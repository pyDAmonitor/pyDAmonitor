#!/usr/bin/env python
"""
Usage: `channel_obscount_barchart.py <CDATE> <lookback_hours> <observer> [requested_channels ...]`

Generates a bar chart of per-channel observation counts (from `n_loop1`) for a radiance observer.
Capable of handling either a single cycle (lookback_hours = 0) or aggregates across consecutive cycles.

Run `source ush/load_pyDAmonitor.sh`, then export MY_COM_BASE, RUN, and WGF as needed.
From Python, `main(..., label_channels=[...])` labels only the given channels to reduce clutter or highlight certain channels for presentations.

Author: Ethan Chang
Date: October 2026
"""
import argparse
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator

# Temporary workaround: ensures the repository root is on sys.path so `DAmonitor` can be imported
repo_root = Path(__file__).resolve().parents[1]
pyDAmonitor_ROOT = os.getenv("pyDAmonitor_ROOT")
if (repo_root / "DAmonitor").is_dir():
    sys.path.insert(0, str(repo_root))
elif pyDAmonitor_ROOT:
    sys.path.insert(0, pyDAmonitor_ROOT)
else:
    raise SystemExit("pyDAmonitor_ROOT is not set and DAmonitor was not found relative to this script. Run `source ush/load_pyDAmonitor.sh`.")
from DAmonitor.obs import obsSpace  # noqa: E402


logger = logging.getLogger(__name__)

# Configuration for plotting
TITLE_SIZE = 22
SUBTITLE_SIZE = 20
LABEL_SIZE = 18
SUMMARY_SIZE = 14
TICK_SIZE = 10


def parse_args() -> argparse.Namespace:
    """
    Parse arguments for the `channel_obscount_barchart.py` file.

    Returns:
        Namespace: Parsed input arguments
    """
    parser = argparse.ArgumentParser(description="Plot an observer's assimilated observation counts (from `n_loop1`) by channel on a bar chart")

    parser.add_argument(
        "CDATE",
        type=str,
        help="The current cycle in Zulu time, written in the following format: YYYYMMDDHH",
    )

    parser.add_argument(
        "lookback_hours",
        type=int,
        help="The number of hours to look back in the past (0 gives the current cycle)",
    )

    parser.add_argument(
        "observer",
        type=str,
        help="The name of the observer (e.g. `cris-fsr_n20`)",
    )

    parser.add_argument(
        "requested_channels",
        type=int,
        nargs="*",
        help="List of which channels to plot. Omitting this argument will make the script plot all channels found in the jdiag file for the given observer that are assimilated in the requested lookback period.",
    )

    return parser.parse_args()


def get_cycle_dir(date_cur: datetime) -> Path:
    """
    Build the pyDAmonitor output directory for one cycle.
    Environment variables should be defined in the shell (i.e. via export) or linked to the directory.

    Args:
        date_cur (datetime): The current cycle

    Returns:
        Path: The path to the current cycle's pyDAmonitor directory
    """
    MY_COM_BASE = os.getenv(key='MY_COM_BASE', default='MY_COM_BASE_not_defined')
    RUN = os.getenv(key='RUN', default='RUN_not_defined')
    WGF = os.getenv(key='WGF', default='WGF_not_defined')
    PDY = date_cur.strftime("%Y%m%d")
    cyc = date_cur.strftime("%H")

    return Path(MY_COM_BASE) / f'{RUN}.{PDY}' / cyc / 'pyDAmonitor' / WGF


def find_cycle_file(date_cur: datetime, filename: str) -> Optional[Path]:
    """
    Return the path to filename for this cycle, or None if absent.
    Checks the cycle directory first, then the web/ subdirectory (see `obs_count_timeseries.py`).

    Args:
        date_cur (datetime): The current cycle
        filename (str): The name of the file to look for within the cycle directory (e.g. `{observer_name}.txt`)

    Returns:
        Optional[Path]: The full path to the file, if it exists; otherwise, None
    """
    cycle_dir = get_cycle_dir(date_cur)
    for path in (cycle_dir / filename, cycle_dir / 'web' / filename):
        if path.is_file():
            return path
    return None


def find_first_jdiag_file(timeline: list[datetime], observer: str) -> Optional[Path]:
    """
    Return the first jdiag file found for this observer anywhere in the window, or None.
    Used only to discover which channels exist for the observer, so the specific cycle does not matter.

    Args:
        timeline (list[datetime]): List that contains each hour of the lookback period as a datetime entry
        observer (str): The name of the observer (e.g. `cris-fsr_n20`)

    Returns:
        Optional[Path]: The full path to the file, if it exists; otherwise, None
    """
    for date_cur in timeline:
        path = find_cycle_file(date_cur, f'jdiag_{observer}.nc')
        if path is not None:
            return path
    return None


def validate_requested_channels(requested_channels: list[int], available_channels: set[int]) -> None:
    """
    Check that the requested channels exist.

    Args:
        requested_channels (list[int]): List of which channels to check for existence
        available_channels (set[int]): Set of all possible channels for an observer

    Raises:
        ValueError: At least one requested channel is not in available_channels.
    """

    missing = [ch for ch in requested_channels if ch not in available_channels]

    if missing:
        raise ValueError(
            f"The following requested channel(s) are not valid for the specified observer: {missing}.\n"
            f"Valid channels: {len(available_channels)} total, ranging from {min(available_channels)} to {max(available_channels)}.\n"
            f"Omit the channel arguments to plot all channels, or inspect the observer's jdiag file for more information.")


def read_channel_counts(filepath: Path) -> dict[int, int]:
    """
    Reads the observation counts from the observer file.

    Args:
        filepath (Path): The path to the observer file with information on the assimilated observation counts for that observer

    Returns:
        dict[int, int]: A dictionary containing the counts for each assimilated channel of the observer for the particular cycle
    """
    counts_dict = {}

    with filepath.open(mode='r') as f:
        for line in f:
            parts = line.split()

            if len(parts) < 2:
                continue

            # Columns written by parse_jedi_log.py: channel, n_loop1, n_loop2 (not used)
            channel_str = parts[0]
            count_str = parts[1]

            # Skip header or non-channel lines
            if not channel_str.isdigit():
                continue

            channel = int(channel_str)
            try:
                count = int(count_str)
            except ValueError:
                logger.warning(
                    f"Could not convert count ({count_str}) for channel {channel_str}"
                )
                continue

            if channel in counts_dict:
                raise ValueError(f"Duplicate channel {channel} found in {filepath}")  # Should not really happen but if it does, stop instead of producing a potentially misleading bar chart
            counts_dict[channel] = count

    return counts_dict


def list_missing_files(missing_files: list[datetime], observer: str) -> None:
    """
    Reports hours in the lookback window without an {observer}.txt file.

    This is usually expected (the cycle was not assimilated, or the observer had no observations), so the list is logged as info.

    Args:
        missing_files (list[datetime]): List of datetimes where an {observer}.txt file does not exist
        observer (str): The name of the observer (e.g. `cris-fsr_n20`)
    """

    lines = [
        f"No {observer}.txt at {len(missing_files)} hour(s) (cycle not assimilated, or no {observer} observations):"
    ]

    times_by_date = defaultdict(list)

    for t in missing_files:
        times_by_date[t.date()].append(t)

    for date, times in sorted(times_by_date.items()):
        hour_str = ", ".join(f"{t:%HZ}" for t in sorted(times))
        lines.append(f"  {date}: {hour_str}")

    logger.info(msg="\n".join(lines))


def list_unassimilated_channels(unassimilated_channels: dict[int, list[datetime]], n_existing_files: int, user_specified_channels: bool) -> None:
    """
    Reports requested channels with no assimilated observations.

    `parse_jedi_log.py` writes a channel row only when n_loop1 or n_loop2 is nonzero,
    so a channel missing from {observer}.txt was assimilated zero times in both loops.
    However, it is not absent from the instrument as all requested channels are validated against the jdiag file before this point.

    Channels never assimilated in any existing cycle are summarized in one message for brevity.
    Channels assimilated in only some cycles get a per-channel breakdown of which cycles they are not assimilated in.
    The summary is logged as a warning when the user specifies channels that are absent from all cycles with detected observer files; otherwise, the message is logged as info.

    Args:
        unassimilated_channels (dict[int, list[datetime]]): A dictionary containing information on which cycles each channel is missing from
        n_existing_files (int): The number of observer files that actually exist (i.e. number of cycles actually present)
        user_specified_channels (bool): Whether or not the user requested specific channels to plot as opposed to plotting all possible channels
    """
    never_assimilated = sorted(
        ch for ch, times in unassimilated_channels.items() if len(times) == n_existing_files
    )

    intermittent = {
        ch: times for ch, times in unassimilated_channels.items() if len(times) < n_existing_files
    }

    if never_assimilated:
        message = (
            f"{len(never_assimilated)} requested channel(s) never assimilated in any of the {n_existing_files} existing files: {never_assimilated}"
        )
        if user_specified_channels:
            logger.warning(msg=message)
        else:
            logger.info(msg=message)

    for ch, times in sorted(intermittent.items()):
        times_by_date = defaultdict(list)
        for t in times:
            times_by_date[t.date()].append(t)
        lines = [
            f"Channel {ch} assimilated in {n_existing_files - len(times)} cycle(s), not assimilated in {len(times)} cycle(s):"
        ]
        for date, hours in sorted(times_by_date.items()):
            hour_str = ", ".join(f"{t:%HZ}" for t in sorted(hours))
            lines.append(f"  {date}: {hour_str}")
        logger.info("\n".join(lines))


def plot_channel_counts(requested_channels: list[int], observer: str, timeline: list[datetime], channel_counts: dict[int, int],
                        n_existing_files: int, label_channels: Optional[list[int]] = None, figures_dir: str = ".") -> Figure:
    """
    Plot the bar chart and returns the figure

    Args:
        requested_channels (list[int]): List of which channels to plot
        observer (str): The name of the observer (e.g. `cris-fsr_n20`)
        timeline (list[datetime]): List that contains each hour of the lookback period as a datetime entry
        channel_counts (dict[int, int]): Dictionary containing the total observations per channel summed across all cycles in the lookback period
        n_existing_files (int): The number of cycles present in the lookback period (i.e. the number of cycles with data)
        label_channels (Optional[list[int]], optional): Label only these channels on the x-axis for visual purposes. Defaults to None, which labels every plotted channel.
        figures_dir (str, optional): The directory that figures save to. Defaults to the working directory

    Returns:
        Figure: The bar chart
    """

    # Only keep the requested channels that appear in the observer files
    channels = []
    counts = []
    for ch in requested_channels:
        if ch in channel_counts:
            channels.append(ch)
            counts.append(channel_counts[ch])

    fig, ax = plt.subplots(figsize=(20, 6))

    # Convert channels from int to str and maintain a separate variable.
    # This prevents channels from being seen as numerical as opposed to categorical.
    channel_labels = [str(ch) for ch in channels]

    ax.bar(x=channel_labels, height=counts)

    ax.grid(axis="y", linestyle=":", alpha=0.5)

    # Sum up observations so that a count can be displayed
    total_observations = sum(counts)

    # Count number of channels with at least one observation
    num_assimilated_channels = sum(
        1 for count in counts
        if count > 0)

    ax.text(
        0.99,
        0.95,
        (
            f"Observations: {total_observations:,}\n"
            f"Channels: {num_assimilated_channels}\n"
            f"Cycles with Data: {n_existing_files}/{len(timeline)}"  # len(timeline) gives the number of cycles in the lookback period
        ),
        transform=ax.transAxes,
        ha="right",
        va="top",
        multialignment="left",
        fontsize=SUMMARY_SIZE,
        bbox={
            'boxstyle': "round",
            'facecolor': "white",
            'alpha': 0.8,
        })

    # Reduce padding between first bar and left edge and right bar and right edge
    ax.margins(x=0.01)

    time_format = '%Y-%m-%d %HZ'

    # Only show specific channel numbers on the x-axis so it doesn't get crowded. This should only be used when necessary for presentation purposes.
    if label_channels:
        xtick_labels = [
            str(ch) if ch in label_channels else ""
            for ch in channels
        ]

        ax.set_xticks(ticks=range(len(channel_labels)))  # Show ticks at every bar...
        ax.set_xticklabels(labels=xtick_labels)  # ... but only label the specified channels

    # TITLE
    fig.suptitle(
        t=f"Assimilated {observer} Observations",
        fontsize=TITLE_SIZE,
        fontweight="bold")

    # SUBTITLE
    if len(timeline) == 1:
        subtitle = f"Single Cycle: {timeline[0].strftime(time_format)}"

    else:
        subtitle = (
            f"Cycles: {timeline[0].strftime(time_format)} – "
            f"{timeline[-1].strftime(time_format)}")

    fig.text(
        x=0.5,
        y=0.87,
        s=subtitle,
        ha="center",
        fontsize=SUBTITLE_SIZE)

    ax.tick_params(axis="x", rotation=45, labelsize=TICK_SIZE)
    ax.tick_params(axis="y", rotation=0, labelsize=TICK_SIZE)
    ax.set_xlabel(xlabel="Channel", fontsize=LABEL_SIZE)

    ax.yaxis.set_major_locator(MaxNLocator(nbins="auto", steps=[1, 2, 2.5, 5, 10], integer=True))  # Fixes problems with bar chart when counts are very low (e.g. lookback_hours = 0 on one channel)
    ax.yaxis.set_major_formatter(formatter=FuncFormatter(func=lambda x, _: f"{x:,.0f}"))

    ax.set_ylabel(ylabel="n_loop1", fontsize=LABEL_SIZE)

    fig.tight_layout(rect=(0, 0, 1, 0.90))

    output_directory = Path(figures_dir)
    output_directory.mkdir(parents=True, exist_ok=True)
    output_file = output_directory / f"{observer}_barchart.png"
    fig.savefig(fname=output_file, dpi=150)
    print(f"Saved → {output_file}")

    return fig


def main(CDATE: str, lookback_hours: int, observer: str, requested_channels: Optional[list[int]] = None,
         label_channels: Optional[list[int]] = None, figures_dir: str = ".") -> Figure:
    """
    Validates arguments, builds a timeline of cycles, validates channels, provides diagnostic information, and generates a bar chart of
    per-channel observation counts (from `n_loop1`) for the given radiance observer, summed across all cycles in the lookback window.

    Args:
        CDATE (str): The current cycle in Zulu time, written in the following format: YYYYMMDDHH
        lookback_hours (int): The number of hours to look back in the past (0 gives the current cycle)
        observer (str): The name of the observer (e.g. `cris-fsr_n20`)
        requested_channels (Optional[list[int]], optional): List of which channels to plot. Defaults to None, which makes the script plot all channels found in the jdiag file for the given observer that are assimilated in the requested lookback period.
        label_channels (Optional[list[int]], optional): Label only these channels on the x-axis for visual purposes. Defaults to None, which labels every plotted channel.
        figures_dir (str, optional): The directory that figures save to. Defaults to the working directory.

    Returns:
        Figure: The bar chart
    """

    # Initial checks
    if lookback_hours < 0:
        raise ValueError("lookback_hours must be non-negative")

    if len(CDATE) != 10 or not CDATE.isdigit():
        raise ValueError(f'CDATE must be written as YYYYMMDDHH (got "{CDATE}")')

    if requested_channels and len(requested_channels) != len(set(requested_channels)):
        raise ValueError("Requested channels must be unique (no repeats of channels)")

    user_specified_channels = bool(requested_channels)

    # Build timeline
    try:
        date_end = datetime.strptime(CDATE, "%Y%m%d%H").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise ValueError(f'CDATE "{CDATE}" is not a valid date and hour: {error}') from None
    date_bgn = date_end - timedelta(hours=lookback_hours)
    timeline = [date_bgn + timedelta(hours=i) for i in range(lookback_hours + 1)]

    # Inspect a jdiag file to find out which channels exist
    jdiag_file = find_first_jdiag_file(timeline, observer)
    if jdiag_file is None:
        raise FileNotFoundError(f'No jdiag file found for "{observer}" in this window. Searched in cycles starting from `{get_cycle_dir(timeline[0])}`')

    obs = obsSpace(jdiag_file)
    available_channels = set(obs.channels)

    if requested_channels:
        # Validate that the channels requested even exist before doing anything else by comparing the requested channels to the information in the file we just read
        validate_requested_channels(requested_channels=requested_channels, available_channels=available_channels)
    else:
        requested_channels = sorted(available_channels)  # else: we will show all channels

    # EXTRACT INFORMATION
    missing_files = []
    unassimilated_channels = defaultdict(list)

    channel_totals = defaultdict(int)

    for dt in timeline:
        observer_file = find_cycle_file(dt, f"{observer}.txt")
        if observer_file is None:
            missing_files.append(dt)
            continue
        channel_data = read_channel_counts(observer_file)

        # Filter and keep only the requested channels
        for ch in requested_channels:
            if ch not in channel_data:
                unassimilated_channels[ch].append(dt)
                continue
            channel_totals[ch] += channel_data[ch]  # Note: requested channels present in observer files with n_loop1 = 0 are retained (plotted as zero-height bars).

    n_existing_files = len(timeline) - len(missing_files)
    if n_existing_files == 0:
        # No observer files at all in the lookback window
        raise FileNotFoundError(f'No "{observer}.txt" files found in the lookback window. This file only exists for radiance observers, and only for cycles that were assimilated and had observations for this observer.')

    if missing_files:
        list_missing_files(missing_files, observer=observer)

    if unassimilated_channels:
        list_unassimilated_channels(unassimilated_channels=unassimilated_channels,
                                    n_existing_files=n_existing_files,
                                    user_specified_channels=user_specified_channels)

    if not any(channel_totals.values()):  # No n_loop1 observations; either no requested channel appeared in any cycle, or the ones that did all had n_loop1 = 0
        if user_specified_channels:
            raise ValueError(f'None of the requested channels of "{observer}" had any n_loop1 observations in the lookback window')
        else:
            raise ValueError(f'"{observer}" had no n_loop1 observations for any channel in the lookback window')

    return plot_channel_counts(
        requested_channels=requested_channels,
        observer=observer,
        timeline=timeline,
        channel_counts=channel_totals,
        n_existing_files=n_existing_files,
        label_channels=label_channels,
        figures_dir=figures_dir)


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')  # change to INFO for more verbosity
    plt.switch_backend('agg')

    try:
        fig = main(CDATE=args.CDATE,
                   lookback_hours=args.lookback_hours,
                   observer=args.observer,
                   requested_channels=args.requested_channels)
    except (FileNotFoundError, ValueError) as error:
        logger.error(error)
        sys.exit(1)

    plt.close(fig)

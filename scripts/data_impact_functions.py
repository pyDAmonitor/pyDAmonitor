#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pickle
import numpy as np
import matplotlib.pyplot as plt


def compute_bins(data):
    """
    Compute histogram bins based on data spread.
    """

    data = np.asarray(data)

    if len(data) == 0:
        return np.arange(-1, 1.1, 0.1)

    std = np.std(data)

    if std == 0 or not np.isfinite(std):
        return np.linspace(
            np.min(data) - 1,
            np.max(data) + 1,
            20
        )

    xmin = -4.0 * std
    xmax = 4.0 * std

    binsize = (np.max(data) - np.min(data)) / np.sqrt(len(data))

    if binsize <= 0 or not np.isfinite(binsize):
        binsize = std / 20.0

    return np.arange(xmin, xmax + binsize, binsize)


def plot_jo_histogram(
    sensor,
    CDATE,
    jo_diffs,
    obserr,
    count_total,
    count_assim,
    count_large,
    count_zero,
    output_dir="./figures"
):
    """
    Plot Jo-diff histogram for one sensor.
    """

    os.makedirs(output_dir, exist_ok=True)

    jo_diffs = np.asarray(jo_diffs)
    obserr = np.asarray(obserr)

    if len(jo_diffs) == 0:
        print(f"[WARN] No Jo-diff values for {sensor}")
        return

    bins = compute_bins(jo_diffs)

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.hist(
        jo_diffs,
        bins=bins,
        edgecolor="black"
    )

    ax.set_xlabel("Jo Diff")
    ax.set_ylabel("Count")
    ax.set_title(
        f"{sensor} {CDATE}",
        fontsize=14
    )

    ax.grid(True)

    # ------------------------------------------
    # Statistics
    # ------------------------------------------
    mean_jo = np.mean(jo_diffs)
    sum_jo = np.sum(jo_diffs)
    max_abs_jo = np.max(np.abs(jo_diffs))

    valid_obserr = (
        np.isfinite(obserr) &
        (obserr > 0)
    )

    inv_obs_error = 1.0 / obserr[valid_obserr]

    text = (
        f"Total Obs Size = {count_total}\n"
        f"Assim Obs Size = {count_assim}\n"
        f"Mean Jo-diff = {mean_jo:.4f}\n"
        f"Sum Jo-diff = {sum_jo:.4f}\n"
        f"Max Abs Jo-diff = {max_abs_jo:.4f}\n"
        f"|Jo-diff| > 25 = {count_large}\n"
        f"Jo-diff = 0 = {count_zero}\n"
        f"Mean Inv ObsErr = {np.mean(inv_obs_error):.4f}\n"
        f"STD Inv ObsErr = {np.std(inv_obs_error):.4f}"
    )

    ax.text(
        0.66,
        0.95,
        text,
        transform=ax.transAxes,
        verticalalignment="top",
        fontsize=11
    )

    output_file = os.path.join(
        output_dir,
        f"{sensor}-{CDATE}.png"
    )

    plt.savefig(
        output_file,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()

    print(f"[SAVE] Figure: {output_file}")


def save_legacy_pickle(
    sensor_types,
    final_total_size,
    final_assim_size,
    final_mean_jo_diff,
    final_sum_jo_diff,
    final_max_abs_jo_diff,
    CDATE,
    label="sate",
    output_dir="./pickle"
):
    """
    Save summary statistics using the legacy data-impact
    pickle structure.
    """

    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(
        output_dir,
        f"{CDATE}_{label}.pkl"
    )

    output = [
        sensor_types,
        final_total_size,
        final_assim_size,
        final_mean_jo_diff,
        final_sum_jo_diff,
        final_max_abs_jo_diff
    ]

    with open(output_file, "wb") as f:
        pickle.dump(
            output,
            f,
            protocol=pickle.HIGHEST_PROTOCOL
        )

    print(f"[SAVE] Summary pickle: {output_file}")

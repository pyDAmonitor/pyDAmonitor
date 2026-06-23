#!/usr/bin/env python
"""
Real-time Ensemble Forecast Diagnostic Tool for DA Monitoring
Usage: ./timeseries_ensemble_monitor.py <YYYYMMDDHH> <days>
"""

import sys
import os
import numpy as np
import pandas as pd
from netCDF4 import Dataset
import properscoring as ps
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# ==========================================
# 1. REAL-TIME ENVIRONMENT & CONFIGURATION
# ==========================================
num_members = 30

# Operational Observers list to iterate over dynamically
observers = [
    # adpsfc ----
    'adpsfc_t181', 'adpsfc_t183', 'adpsfc_t187', 'adpsfc_q181', 'adpsfc_q183', 'adpsfc_q187',
    'adpsfc_ps181', 'adpsfc_ps187', 'adpsfc_uv281', 'adpsfc_uv284', 'adpsfc_uv287',
    # adpupa ----
    'adpupa_t120', 'adpupa_q120', 'adpupa_ps120', 'adpupa_uv220',
    # aircar ----
    'aircar_t133', 'aircar_q133', 'aircar_uv233',
    # sfcshp ----
    'sfcshp_t180', 'sfcshp_t183', 'sfcshp_q180', 'sfcshp_q183',
    'sfcshp_ps180', 'sfcshp_uv280', 'sfcshp_uv282', 'sfcshp_uv284',
]

# Clean Dictionary Mapping with Lists as Values (Handles multiple fields under 'uv')
VAR_MAP = {
    "t":  ["airTemperature"],
    "q":  ["specificHumidity"],
    "ps": ["stationPressure"],
    "uv": ["windEastward", "windNorthward"]
}

# Standard core verification metric tracking keys
METRIC_KEYS = [
    'crps_mean', 'crps_median', 'crps_p25', 'crps_p75', 'crps_p5', 'crps_p95',
    'rmse', 'spread', 'bias_index', 'rel_index'
]

# ==========================================
# 2. CORE DIAGNOSTIC FUNCTIONS
# ==========================================


def get_file_path(base_path, run_name, pdy, cyc, wgf, file_name):
    """Generates the file path exactly matching the operational environment structure."""
    return os.path.join(
        base_path, f"{run_name}.{pdy}", cyc, "pyDAmonitor", wgf, file_name
    )


def compute_reliability_index(bin_counts, m_members, num_stations):
    """Computes the deviation of rank histogram from an ideal flat distribution."""
    if num_stations == 0:
        return np.nan
    ideal_freq = 1.0 / (m_members + 1)
    actual_freq = bin_counts / num_stations
    return np.mean(np.abs(actual_freq - ideal_freq))


def compute_directional_bias_index(bin_counts, num_stations):
    """Computes a normalized directional bias index bounded between [-1, 1]."""
    if num_stations == 0:
        return np.nan
    half_len = len(bin_counts) // 2
    left_sum = np.sum(bin_counts[:half_len])
    right_sum = np.sum(bin_counts[-half_len:])
    return (left_sum - right_sum) / num_stations


def process_single_hour(file_path, v_name, m_members):
    """Reads a single real-time NetCDF cycle file and computes verification stats."""
    if not os.path.exists(file_path):
        return {k: np.nan for k in METRIC_KEYS}

    try:
        with Dataset(file_path, 'r') as nc:
            # Look directly for the targeted internal variable
            if 'ObsValue' in nc.groups and v_name in nc.groups['ObsValue'].variables:
                obs = nc.groups['ObsValue'].variables[v_name][:]
                if hasattr(obs, 'mask'):
                    obs = np.ma.filled(obs, np.nan)
            else:
                return {k: np.nan for k in METRIC_KEYS}

            num_obs = len(obs)
            fcst = np.full((num_obs, m_members), np.nan)

            # Dynamically extract all ensemble members
            for m in range(1, m_members + 1):
                g_name = f"hofx0_{m}"
                if g_name in nc.groups and v_name in nc.groups[g_name].variables:
                    member_val = nc.groups[g_name].variables[v_name][:]
                    if hasattr(member_val, 'mask'):
                        member_val = np.ma.filled(member_val, np.nan)
                    fcst[:, m-1] = member_val

            # Quality Control: Filter out completely missing or masked stations
            valid_mask = ~np.isnan(obs) & ~np.isnan(fcst).any(axis=1)
            obs = obs[valid_mask]
            fcst = fcst[valid_mask]
            n_stations = len(obs)

            if n_stations == 0:
                return {k: np.nan for k in METRIC_KEYS}

            # --- Calculation of Verification Metrics ---
            crps_vals = ps.crps_ensemble(obs, fcst, axis=-1)
            ens_mean = np.mean(fcst, axis=-1)
            rmse = np.sqrt(np.mean((ens_mean - obs) ** 2))
            spread = np.mean(np.std(fcst, axis=-1, ddof=1))

            ranks = np.array([np.sum(f < o) for o, f in zip(obs, fcst)])
            bin_counts, _ = np.histogram(ranks, bins=np.arange(m_members + 2) - 0.5)

            bias_index = compute_directional_bias_index(bin_counts, n_stations)
            rel_index = compute_reliability_index(bin_counts, m_members, n_stations)

            return {
                'crps_mean': np.mean(crps_vals), 'crps_median': np.median(crps_vals),
                'crps_p25': np.percentile(crps_vals, 25), 'crps_p75': np.percentile(crps_vals, 75),
                'crps_p5': np.percentile(crps_vals, 5), 'crps_p95': np.percentile(crps_vals, 95),
                'rmse': rmse, 'spread': spread, 'bias_index': bias_index, 'rel_index': rel_index
            }

    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        return {k: np.nan for k in METRIC_KEYS}

# ==========================================
# 3. PRODUCTION QUALITY 4-PANEL PLOTTER
# ==========================================


def plot_rt_diagnostics(df, obs_label, actual_varname, daterange_str, output_file=None):
    """Plots real-time dashboard tracking the 4 core ensemble metrics for an observer."""
    fig, axes = plt.subplots(4, 1, figsize=(14, 20), sharex=True)

    c_primary = '#1f77b4'      # Main mean line (Deep Blue)
    c_secondary = '#2ca02c'    # Median tracker (Green)
    c_edge = '#aec7e8'         # Extreme bounds (Light Blue)
    c_core = '#98df8a'         # Interquartile range (Light Green)

    # -----------------------------------------------------------------
    # Panel 1: CRPS
    # -----------------------------------------------------------------
    axes[0].fill_between(df.index, df['crps_p5'], df['crps_p95'], color=c_edge, alpha=0.2, label="Spatial Extremes (5%-95%)")
    axes[0].fill_between(df.index, df['crps_p25'], df['crps_p75'], color=c_core, alpha=0.4, label="Spatial Core (25%-75%)")
    axes[0].plot(df.index, df['crps_median'], color=c_secondary, linestyle='--', linewidth=1.8, label="Spatial Median")
    axes[0].plot(df.index, df['crps_mean'], color=c_primary, linestyle='-', linewidth=2.0, marker='o', markersize=2, label="Spatial Mean")

    axes[0].set_ylabel("CRPS", fontsize=12)
    axes[0].set_title(f"CRPS Performance Tracking | Observer: {obs_label} ({actual_varname}) | {daterange_str}", fontsize=13, fontweight='bold')
    axes[0].grid(True, linestyle=':', alpha=0.5)
    axes[0].legend(loc='upper left', ncol=2, framealpha=0.9)

    # -----------------------------------------------------------------
    # Panel 2: Reliability Index
    # -----------------------------------------------------------------
    axes[1].plot(df.index, df['rel_index'], color=c_primary, linestyle='-', linewidth=2.0, marker='o', markersize=2, label="Reliability Index")
    axes[1].fill_between(df.index, 0, df['rel_index'], color=c_primary, alpha=0.08)
    axes[1].set_ylabel("Deviation (Lower=Better)", fontsize=12)
    axes[1].set_title("Rank Histogram Flatness Degradation (Reliability Index)", fontsize=13, fontweight='bold')
    axes[1].grid(True, linestyle=':', alpha=0.5)

    # -----------------------------------------------------------------
    # Panel 3: Directional Bias Index
    # -----------------------------------------------------------------
    axes[2].plot(df.index, df['bias_index'], color='#d95f02', linestyle='-', linewidth=2.0, marker='o', markersize=2, label="Directional Bias Index")
    axes[2].axhline(0, color='black', linestyle='-', linewidth=1.2, alpha=0.7)

    axes[2].fill_between(df.index, 0, df['bias_index'], where=(df['bias_index'] >= 0), color='#fee0d2', alpha=0.6, interpolate=True)
    axes[2].fill_between(df.index, 0, df['bias_index'], where=(df['bias_index'] < 0), color='#deebf7', alpha=0.6, interpolate=True)

    axes[2].set_ylabel("← Underforecast | Overforecast →", fontsize=11)
    axes[2].set_title("Systematic Forecast Bias Evolution", fontsize=13, fontweight='bold')
    axes[2].grid(True, linestyle=':', alpha=0.5)

    max_bias = np.nanmax(np.abs(df['bias_index']))
    if not np.isnan(max_bias) and max_bias > 0:
        axes[2].set_ylim(-max_bias * 1.3, max_bias * 1.3)

    # -----------------------------------------------------------------
    # Panel 4: Spread-Skill Consistency
    # -----------------------------------------------------------------
    axes[3].plot(df.index, df['rmse'], color='#e31a1c', linestyle='-', marker='o', markersize=3, linewidth=2, label="Ensemble Mean RMSE (Skill)")
    axes[3].plot(df.index, df['spread'], color='#1f78b4', linestyle='--', marker='^', markersize=3, linewidth=1.8, label="Ensemble Spread")
    axes[3].set_ylabel("Magnitude", fontsize=12)
    axes[3].set_title("Spread-Skill Relationship Timeline (Ideal: Spread ≈ RMSE)", fontsize=13, fontweight='bold')
    axes[3].grid(True, linestyle=':', alpha=0.5)
    axes[3].legend(loc='upper left', ncol=2)

    # High density hourly settings for standard real-time monitoring display
    axes[3].xaxis.set_major_locator(mdates.HourLocator(interval=6))
    axes[3].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d\n%H:%M'))
    axes[3].xaxis.set_minor_locator(mdates.HourLocator(interval=1))
    plt.xticks(rotation=30, ha='right')

    for ax in axes:
        ax.tick_params(labelbottom=True, labelsize=9)

    plt.tight_layout()

    if output_file:
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Saved Image -> {output_file}")
    else:
        plt.show()
    plt.close(fig)

# ==========================================
# 4. MAIN REAL-TIME EXECUTION BLOCK
# ==========================================


if __name__ == '__main__':

    # Input argument check
    args = sys.argv
    nargs = len(args) - 1
    if nargs < 2 or len(sys.argv[1]) < 10:
        print(f'Usage: {os.path.basename(sys.argv[0])} <YYYYMMDDHH> <days>')
        print('Example: ./timeseries_ensemble_monitor.py 2026052212 7')
        sys.exit(1)

    CDATE = sys.argv[1]
    MAX_DAYS = sys.argv[2]
    lookback_hours = int(MAX_DAYS) * 24

    # Extract Environment variables matching your operational setup
    MY_COM_BASE = os.getenv('MY_COM_BASE', 'MY_COM_BASE_not_defined')
    WGF = os.getenv('WGF', 'WGF_not_defined')
    RUN = os.getenv('RUN', 'RUN_not_defined')

    # Calculate real-time target window bounds
    dateEnd = datetime.strptime(CDATE, "%Y%m%d%H")
    dateBgn = dateEnd - timedelta(hours=lookback_hours)

    # Main driver looping over operational subtypes sequence
    for obs in observers:

        # 1. Parse name segments to map variables and files
        parts = obs.split('_')
        group_prefix = parts[0]
        suffix = parts[1]

        # Extract letters only from the suffix (e.g., 'uv287' -> 'uv', 'ps181' -> 'ps')
        var_abbr = ''.join([i for i in suffix if not i.isdigit()])
        filename_tmpl = f"jdiag_{group_prefix}_{suffix}.nc"

        # 2. Fetch the target internal long variable names list from configuration block
        if var_abbr not in VAR_MAP:
            print(f"Warning: Extracted Abbreviation '{var_abbr}' is unknown! Skipping observer type {obs}.")
            continue

        target_varnames = VAR_MAP[var_abbr]

        # 3. Process each internal target variable sequentially (will loop twice for 'uv')
        for varname in target_varnames:
            print(f"\nProcessing real-time diagnostics for: {obs} | Variable: {varname}...")

            # Setup storage tracking lookback hours
            tseries = {k: [np.nan] * (lookback_hours + 1) for k in METRIC_KEYS}
            time_axis = []

            # Chronological loop parsing files hour-by-hour
            for i in range(lookback_hours + 1):
                target_dt = dateBgn + timedelta(hours=i)
                time_axis.append(target_dt)

                pdy = target_dt.strftime("%Y%m%d")
                cyc = target_dt.strftime("%H")

                # Strategy: Look into the next hour directory to capture diagnostics
                dir_dt_B = target_dt + timedelta(hours=1)
                target_file = get_file_path(MY_COM_BASE, RUN, dir_dt_B.strftime("%Y%m%d"), dir_dt_B.strftime("%H"), WGF, filename_tmpl)

                # Compute cycle calculations
                res = process_single_hour(target_file, varname, num_members)
                for k in METRIC_KEYS:
                    tseries[k][i] = res[k]

            # 4. Generate DataFrame and output visualization
            df_results = pd.DataFrame(tseries, index=time_axis)

            # Guardrail: Check if the dataframe contains entirely missing data to skip plotting blank pages
            if df_results['crps_mean'].isna().all():
                print(f"-> No valid data records inside NetCDF found for {obs} ({varname}) over lookback timeframe. Skipping plot.")
                continue

            daterange_str = f'{dateBgn.strftime("%Y%m%d%H")}-{CDATE}'

            # Save separate tracking file for each wind component
            output_filename = f'rt_monitor_{obs}_{varname}_{daterange_str}.png'

            plot_rt_diagnostics(df_results, obs, varname, daterange_str, output_file=output_filename)

    print("\nAll real-time observer monitoring updates processed successfully.")

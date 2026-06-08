#!/usr/bin/env python
"""
Real-time Ensemble Forecast Diagnostic Tool
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
# Preset variable and file template configurations
TASK = "getkf_observer"
num_members = 30  

# Fetch production paths from environment variables or use fallbacks
EXP_PATH = os.getenv('RT_EXP_PATH', '/gpfs/f6/wrfruc/scratch/Sijie.Pan/retros')
EXP_NAME = os.getenv('RT_EXP_NAME', 'RRFSv2X_sfcfix3')
VERSION  = os.getenv('RT_VERSION',  '2.1.3')

# Core verification metric keys
METRIC_KEYS = [
    'crps_mean', 'crps_median', 'crps_p25', 'crps_p75', 'crps_p5', 'crps_p95', 
    'rmse', 'spread', 'bias_index', 'rel_index'
]

# Mapping full variable names to their diagnostic file short abbreviations
VAR_ABBR_MAP = {
    "airTemperature": "t",
    "specificHumidity": "q",
    "stationPressure": "ps",
    "windEastward": "uv",
    "windNorthward": "uv"
}

# ==========================================
# 2. CORE DIAGNOSTIC FUNCTIONS
# ==========================================

def get_file_path(base_path, exp_name, version, date_str, hour_str, task_name, file_name):
    """Generates the standardized operational directory and file path structure."""
    return os.path.join(
        base_path, exp_name, "com", "rrfs", f"v{version}",
        f"rrfs.{date_str}", hour_str, task_name, "enkf", file_name
    )

def compute_reliability_index(bin_counts, m_members, num_stations):
    """Computes the deviation of rank histogram from an ideal flat distribution."""
    if num_stations == 0: return np.nan
    ideal_freq = 1.0 / (m_members + 1)
    actual_freq = bin_counts / num_stations
    return np.mean(np.abs(actual_freq - ideal_freq))

def compute_directional_bias_index(bin_counts, num_stations):
    """
    Computes a normalized bias index bounded between [-1, 1].
    Positive value (>0) indicates Overforecast.
    Negative value (<0) indicates Underforecast.
    """
    if num_stations == 0: return np.nan
    half_len = len(bin_counts) // 2
    left_sum = np.sum(bin_counts[:half_len])
    right_sum = np.sum(bin_counts[-half_len:])
    return (left_sum - right_sum) / num_stations

def process_single_hour(file_path, v_name, m_members):
    """Reads a single real-time NetCDF cycle file and computes verification stats."""
    if not os.path.exists(file_path):
        # Operational fallback: log warning and return NaN if a cycle file is delayed/missing
        print(f"Warning: File missing -> {file_path}")
        return {k: np.nan for k in METRIC_KEYS}
    
    try:
        with Dataset(file_path, 'r') as nc:
            # Extract observation array
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
            
            # Quality Control: Filter missing stations
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

def plot_rt_diagnostics(df, v_name, obs_id, daterange_str, output_file=None):
    """
    Plots real-time dashboard tracking the 4 core ensemble metrics.
    Streamlined layout optimized for single-experiment monitoring.
    """
    fig, axes = plt.subplots(4, 1, figsize=(14, 20), sharex=True)
    
    # Palette optimized for clear visibility on single-line real-time monitors
    c_primary = '#1f77b4'      # Main mean line (Deep Blue)
    c_secondary = '#2ca02c'    # Median tracker (Green)
    c_edge = '#aec7e8'         # Extreme bounds (Light Blue)
    c_core = '#98df8a'         # Interquartile range (Light Green)
    
    # -----------------------------------------------------------------
    # Panel 1: Continuous Ranked Probability Score (CRPS)
    # -----------------------------------------------------------------
    axes[0].fill_between(df.index, df['crps_p5'], df['crps_p95'], color=c_edge, alpha=0.2, label="Spatial Extremes (5%-95%)")
    axes[0].fill_between(df.index, df['crps_p25'], df['crps_p75'], color=c_core, alpha=0.4, label="Spatial Core (25%-75%)")
    axes[0].plot(df.index, df['crps_median'], color=c_secondary, linestyle='--', linewidth=1.8, label="Spatial Median")
    axes[0].plot(df.index, df['crps_mean'], color=c_primary, linestyle='-', linewidth=2.5, label="Spatial Mean")
    
    axes[0].set_ylabel(f"CRPS ({varname})", fontsize=12)
    axes[0].set_title(f"CRPS Stream | Variable: {v_name} (Type {obs_id}) | {daterange_str}", fontsize=13, fontweight='bold')
    axes[0].grid(True, linestyle=':', alpha=0.5)
    axes[0].legend(loc='upper left', ncol=2, framealpha=0.9)

    # -----------------------------------------------------------------
    # Panel 2: Reliability Index
    # -----------------------------------------------------------------
    axes[1].plot(df.index, df['rel_index'], color=c_primary, linestyle='-', linewidth=2.2, label="Reliability Index")
    axes[1].fill_between(df.index, 0, df['rel_index'], color=c_primary, alpha=0.08)
    axes[1].set_ylabel("Deviation (Lower=Better)", fontsize=12)
    axes[1].set_title("Rank Histogram Flatness Degradation (Reliability Index)", fontsize=13, fontweight='bold')
    axes[1].grid(True, linestyle=':', alpha=0.5)

    # -----------------------------------------------------------------
    # Panel 3: Directional Bias Index
    # -----------------------------------------------------------------
    axes[2].plot(df.index, df['bias_index'], color='#d95f02', linestyle='-', linewidth=2.2, label="Directional Bias Index")
    axes[2].axhline(0, color='black', linestyle='-', linewidth=1.2, alpha=0.7)
    
    # Distinct shading to highlight overforecasting vs underforecasting phases
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

    # Clean operational X-axis styling: Major ticks every 6 hours, labeled with Month-Day and Hour
    axes[3].xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 6, 12, 18]))
    axes[3].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d\n%H:%M'))
    axes[3].xaxis.set_minor_locator(mdates.HourLocator(interval=1))
    
    for ax in axes:
        ax.tick_params(labelbottom=True, labelsize=9)

    plt.tight_layout()
    
    if output_file:
        fig.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Saved Real-time Plot → {output_file}")
    else:
        plt.show()
    plt.close(fig)

# ==========================================
# 4. MAIN REAL-TIME EXECUTION BLOCK
# ==========================================
if __name__ == '__main__':
    
    # Argument validation check
    args = sys.argv
    nargs = len(args) - 1
    if nargs < 4 or len(sys.argv[1]) < 10:
        print(f'Usage: {os.path.basename(sys.argv[0])} <YYYYMMDDHH> <days> <variable_name> <obs_type>')
        print(f'Variables allowed: airTemperature, specificHumidity, stationPressure, windEastward, windNorthward')
        print(f'Example: ./rt_ensemble_monitor.py 2026052212 7 stationPressure 187')
        sys.exit(1)
        
    CDATE = sys.argv[1]
    MAX_DAYS = sys.argv[2]
    varname = sys.argv[3]
    obs_type = sys.argv[4]

    if varname not in VAR_ABBR_MAP:
        print(f"Error: Unknown variable name '{varname}'. Please check inputs.")
        sys.exit(1)

    var_abbr = VAR_ABBR_MAP[varname]
    filename_tmpl = f"jdiag_adpsfc_{var_abbr}{obs_type}.nc"
    lookback_hours = int(MAX_DAYS) * 24
    
    # Calculate real-time target timeline (stretching from lookback anchor to current cycle)
    dateEnd = datetime.strptime(CDATE, "%Y%m%d%H")
    dateBgn = dateEnd - timedelta(hours=lookback_hours)
    time_all = pd.date_range(start=dateBgn, end=dateEnd, freq='h')
    
    print(f"====================================================")
    print(f"Real-time Monitoring Init Target (CDATE): {CDATE}")
    print(f"Lookback Window: Past {MAX_DAYS} days ({lookback_hours} hours)")
    print(f"Timeline: {dateBgn.strftime('%Y-%m-%d %H:00')} -> {dateEnd.strftime('%Y-%m-%d %H:00')}")
    print(f"====================================================")
    
    # Initialize metrics structure
    metrics_series = {k: [] for k in METRIC_KEYS}
    
    # Iterate dynamically backward across the verification window
    for target_dt in time_all:
        if TASK == 'getkf_post':
            target_file = get_file_path(EXP_PATH, EXP_NAME, VERSION, 
                                        target_dt.strftime("%Y%m%d"), target_dt.strftime("%H"), "getkf_post", filename_tmpl)
        elif TASK == 'getkf_observer':
            # Strategy B handling: Look into the next hour's directory to find current diagnostics
            dir_dt_B = target_dt + timedelta(hours=1)
            target_file = get_file_path(EXP_PATH, EXP_NAME, VERSION, 
                                        dir_dt_B.strftime("%Y%m%d"), dir_dt_B.strftime("%H"), "getkf_observer", filename_tmpl)
        else:
            raise ValueError(f"Unknown task configuration: {TASK}.")
            
        # Parse single hour's metrics
        res = process_single_hour(target_file, varname, num_members)
        
        # Append data points to the array
        for k in METRIC_KEYS:
            metrics_series[k].append(res[k])
            
    # Bind everything into a structured Pandas DataFrame
    df_results = pd.DataFrame(metrics_series, index=time_all)
    
    # Generate timestamp ranges for image labeling
    daterange_str = f'{dateBgn.strftime("%Y%m%d%H")}-{CDATE}'
    output_filename = f'rt_monitor_{var_abbr}{obs_type}_{daterange_str}.png'
    
    # Output the final product
    plot_rt_diagnostics(df_results, varname, obs_type, daterange_str, output_file=output_filename)
    print("Real-time diagnostic task finished successfully.")

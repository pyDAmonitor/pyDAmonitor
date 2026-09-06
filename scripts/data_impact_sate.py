#!/usr/bin/env python
# compute the summary in the past 7 days, 30 days
#
import sys
import os
import numpy as np
import netCDF4 as nc


from data_impact_functions import (
    plot_jo_histogram,
    save_legacy_pickle
)


def analyze_sate(CDATE):

    # ------------------------------------------------------------
    # Choose sensors: comment/uncomment as needed
    # ------------------------------------------------------------
    sensor_types = [
        "atms_n20",
        "abi_g16",
        "abi_g18",
        "atms_n21",
        "cris-fsr_n20",
        "cris-fsr_n21"
    ]

    n_sensor = len(sensor_types)
    final_total_size = np.zeros(n_sensor)
    final_assim_size = np.zeros(n_sensor)
    final_mean_jo_diff = np.zeros(n_sensor)
    final_sum_jo_diff = np.zeros(n_sensor)
    final_max_abs_jo_diff = np.zeros(n_sensor)

    for ss, sensor in enumerate(sensor_types):

        print(ss)
        print(sensor)

        ncd = nc.Dataset(f"./jdiag_{sensor}.nc", 'r')

        print(f"=== Processing {sensor} ===")

        # NetCDF global attributes
        # --------------------------
        nc_attrs = ncd.ncattrs()
        print('NetCDF Global Attributes: ')
        print('nc_attrs = ', nc_attrs)

        for nc_attr in nc_attrs:
            print('nc_attr', ncd.getncattr(nc_attr))

        omb = ncd.groups["ombg"].variables["brightnessTemperature"][:]
        oma = ncd.groups["oman"].variables["brightnessTemperature"][:]
        obserr = ncd.groups["EffectiveError1"].variables["brightnessTemperature"][:]
        qc = ncd.groups["EffectiveQC1"].variables["brightnessTemperature"][:]

        channel = ncd.variables["Channel"][:]

        print(f"OMB shape:    {omb.shape}")
        print(f"OMA shape:    {oma.shape}")
        print(f"ObsErr shape: {obserr.shape}")
        print(f"QC shape:     {qc.shape}")

        # ----------------------------------------------------
        # Convert masked arrays to regular arrays with NaN
        # ----------------------------------------------------
        omb = np.ma.filled(omb, np.nan)
        oma = np.ma.filled(oma, np.nan)
        obserr = np.ma.filled(obserr, np.nan)

        # QC is integer; fill masked values with a bad-QC value
        qc = np.ma.filled(qc, 999)

        # ----------------------------------------------------
        # Select assimilated observations
        #
        # EffectiveQC == 0 means used/accepted
        # ----------------------------------------------------
        valid = (
            (qc == 0) &
            np.isfinite(omb) &
            np.isfinite(oma) &
            np.isfinite(obserr) &
            (obserr > 0)
        )

        # ----------------------------------------------------
        # Jo difference
        #
        # Jo = (O-H)^2 / sigma_o^2
        #
        # Delta Jo = Jo_analysis - Jo_background
        #
        # Negative Jo-diff means the analysis moved
        # the model closer to the observations.
        # ----------------------------------------------------
        jo_diff = np.full(omb.shape, np.nan)

        jo_diff[valid] = (oma[valid] ** 2 - omb[valid] ** 2) / (obserr[valid] ** 2)

        jo_diffs = jo_diff[valid]

        # ----------------------------------------------------
        # Counts
        # ----------------------------------------------------
        count_total = omb.size
        count_assim = np.sum(valid)

        count_large = np.sum(np.abs(jo_diffs) > 25)
        count_zero = np.sum(jo_diffs == 0)

        print()
        print(f"Total elements:           {count_total}")
        print(f"Assimilated elements:     {count_assim}")
        print(f"|Jo-diff| > 25 count:     {count_large}")
        print(f"Jo-diff == 0 count:       {count_zero}")

        # ----------------------------------------------------
        # Statistics
        # ----------------------------------------------------
        if jo_diffs.size:
            mean_jo_diff = np.mean(jo_diffs)
            sum_jo_diff = np.sum(jo_diffs)
            max_abs_jo_diff = np.max(np.abs(jo_diffs))
        else:
            mean_jo_diff = np.nan
            sum_jo_diff = 0.0
            max_abs_jo_diff = np.nan

        print()
        print(f"Mean Jo-diff:    {mean_jo_diff}")
        print(f"Sum Jo-diff:     {sum_jo_diff}")
        print(f"Max |Jo-diff|:   {max_abs_jo_diff}")

        # ----------------------------------------------------
        # Save summary arrays
        # ----------------------------------------------------
        final_total_size[ss] = count_total
        final_assim_size[ss] = count_assim
        final_mean_jo_diff[ss] = mean_jo_diff
        final_sum_jo_diff[ss] = sum_jo_diff
        final_max_abs_jo_diff[ss] = max_abs_jo_diff

        # ----------------------------------------------------
        # Plot Jo-diff histogram
        # ----------------------------------------------------
        plot_jo_histogram(
            sensor,
            CDATE,
            jo_diffs,
            obserr[valid],
            count_total,
            count_assim,
            count_large,
            count_zero
        )

        # ----------------------------------------------------
        # Optional: print statistics by channel
        # ----------------------------------------------------
        print()
        print("Channel statistics:")

        for ich, ch in enumerate(channel):

            valid_ch = valid[:, ich]

            if np.sum(valid_ch) == 0:
                continue

            jo_ch = jo_diff[:, ich][valid_ch]

            print(
                f"Channel {int(ch):5d}: "
                f"N={len(jo_ch):5d} "
                f"mean={np.mean(jo_ch):10.4f} "
                f"sum={np.sum(jo_ch):12.4f}"
            )

        # ------------------------------------------------------------
        # Save summary pickle
        # ------------------------------------------------------------
        save_legacy_pickle(
            sensor_types,
            final_total_size,
            final_assim_size,
            final_mean_jo_diff,
            final_sum_jo_diff,
            final_max_abs_jo_diff,
            CDATE,
            label="sate"
        )

    # ------------------------------------------------------------
    # Final sensor summary
    # ------------------------------------------------------------
    print()
    print("====================================================")
    print("Final Summary")
    print("====================================================")

    for ss, sensor in enumerate(sensor_types):

        print(
            f"{sensor:20s} "
            f"total={final_total_size[ss]:10.0f} "
            f"assim={final_assim_size[ss]:10.0f} "
            f"mean={final_mean_jo_diff[ss]:12.5f} "
            f"sum={final_sum_jo_diff[ss]:12.5f} "
            f"maxabs={final_max_abs_jo_diff[ss]:12.5f}"
        )


if __name__ == "__main__":
    #
    args = sys.argv
    nargs = len(args) - 1
    if nargs < 1 or len(sys.argv[1]) < 10:
        print(f'Usage: {os.path.basename(sys.argv[0])} <YYYYMMDDHH>')
        sys.exit(1)

    # ~~~~~~
    CDATE = sys.argv[1]

    analyze_sate(CDATE)

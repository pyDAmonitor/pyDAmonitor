#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================
Data Impact Analysis – JEDI Conventional Observations
==============================================================
"""

import sys
import os
import numpy as np
import netCDF4 as nc

from data_impact_functions import (
    plot_jo_histogram,
    save_legacy_pickle
)


def analyze_conv(CDATE):

    # ------------------------------------------------------------
    # Choose conventional observation types
    # ------------------------------------------------------------
    sensor_types = [
        "adpsfc_ps181",
        "adpsfc_ps187",
        "adpsfc_q181",
        "adpsfc_q183",
        "adpsfc_q187",
        "adpsfc_t181",
        "adpsfc_t183",
        "adpsfc_t187",
        "aircar_q133",
        "aircar_t133",
        "sfcshp_ps180",
        "sfcshp_q180",
        "sfcshp_q183",
        "sfcshp_t180",
        "sfcshp_t183"
    ]

    n_sensor = len(sensor_types)

    final_total_size = np.zeros(n_sensor)
    final_assim_size = np.zeros(n_sensor)
    final_mean_jo_diff = np.zeros(n_sensor)
    final_sum_jo_diff = np.zeros(n_sensor)
    final_max_abs_jo_diff = np.zeros(n_sensor)

    for ss, sensor in enumerate(sensor_types):

        print()
        print(ss)
        print(sensor)

        filename = f"./jdiag_{sensor}.nc"

        if not os.path.exists(filename):
            print(f"[WARN] Missing file: {filename}")
            continue

        ncd = nc.Dataset(filename, "r")

        print(f"=== Processing {sensor} ===")

        # --------------------------------------------------------
        # NetCDF global attributes
        # --------------------------------------------------------
        nc_attrs = ncd.ncattrs()

        print("NetCDF Global Attributes: ")
        print("nc_attrs = ", nc_attrs)

        for nc_attr in nc_attrs:
            print("nc_attr", ncd.getncattr(nc_attr))

        # --------------------------------------------------------
        # Determine diagnostic variable automatically
        #
        # Example for jdiag_aircar_t133.nc:
        #
        #   ombg/airTemperature
        #   oman/airTemperature
        #   EffectiveError1/airTemperature
        #   EffectiveQC1/airTemperature
        # --------------------------------------------------------
        common_variables = (
            set(ncd.groups["ombg"].variables.keys())
            & set(ncd.groups["oman"].variables.keys())
            & set(ncd.groups["EffectiveError1"].variables.keys())
            & set(ncd.groups["EffectiveQC1"].variables.keys())
        )

        common_variables = sorted(common_variables)

        if len(common_variables) == 0:
            print(
                f"[WARN] No common diagnostic variable "
                f"found for {sensor}"
            )
            ncd.close()
            continue

        if len(common_variables) > 1:
            print(
                f"[ERROR] Multiple diagnostic variables found "
                f"for {sensor}: {common_variables}"
            )
            print(
                "Please check the jdiag structure before "
                "computing data impact."
            )
            ncd.close()
            continue

        variable = common_variables[0]

        print(f"Diagnostic variable: {variable}")

        # --------------------------------------------------------
        # Read diagnostics
        # --------------------------------------------------------
        omb = (
            ncd.groups["ombg"]
            .variables[variable][:]
        )

        oma = (
            ncd.groups["oman"]
            .variables[variable][:]
        )

        obserr = (
            ncd.groups["EffectiveError1"]
            .variables[variable][:]
        )

        qc = (
            ncd.groups["EffectiveQC1"]
            .variables[variable][:]
        )

        print(f"OMB shape:    {omb.shape}")
        print(f"OMA shape:    {oma.shape}")
        print(f"ObsErr shape: {obserr.shape}")
        print(f"QC shape:     {qc.shape}")

        # --------------------------------------------------------
        # Convert masked arrays
        # --------------------------------------------------------
        omb = np.ma.filled(
            omb,
            np.nan
        )

        oma = np.ma.filled(
            oma,
            np.nan
        )

        obserr = np.ma.filled(
            obserr,
            np.nan
        )

        qc = np.ma.filled(
            qc,
            999
        )

        # --------------------------------------------------------
        # Select assimilated observations
        #
        # EffectiveQC == 0 means accepted/used
        # --------------------------------------------------------
        valid = (
            (qc == 0)
            & np.isfinite(omb)
            & np.isfinite(oma)
            & np.isfinite(obserr)
            & (obserr > 0)
        )

        # --------------------------------------------------------
        # Jo difference
        #
        # Jo = (O-H)^2 / sigma_o^2
        #
        # Delta Jo = Jo_analysis - Jo_background
        # --------------------------------------------------------
        jo_diff = np.full(
            omb.shape,
            np.nan
        )

        jo_diff[valid] = (
            oma[valid] ** 2 - omb[valid] ** 2
        ) / (
            obserr[valid] ** 2
        )

        jo_diffs = jo_diff[valid]

        # --------------------------------------------------------
        # Counts
        # --------------------------------------------------------
        count_total = omb.size
        count_assim = np.sum(valid)

        count_large = np.sum(
            np.abs(jo_diffs) > 25
        )

        count_zero = np.sum(
            jo_diffs == 0
        )

        print()
        print(
            f"Total elements:           "
            f"{count_total}"
        )

        print(
            f"Assimilated elements:     "
            f"{count_assim}"
        )

        print(
            f"|Jo-diff| > 25 count:     "
            f"{count_large}"
        )

        print(
            f"Jo-diff == 0 count:       "
            f"{count_zero}"
        )

        if count_assim == 0:

            print(
                f"[WARN] No assimilated observations "
                f"for {sensor}"
            )

            ncd.close()
            continue

        # --------------------------------------------------------
        # Statistics
        # --------------------------------------------------------
        mean_jo_diff = np.mean(
            jo_diffs
        )

        sum_jo_diff = np.sum(
            jo_diffs
        )

        max_abs_jo_diff = np.max(
            np.abs(jo_diffs)
        )

        print()
        print(
            f"Mean Jo-diff:    "
            f"{mean_jo_diff}"
        )

        print(
            f"Sum Jo-diff:     "
            f"{sum_jo_diff}"
        )

        print(
            f"Max |Jo-diff|:   "
            f"{max_abs_jo_diff}"
        )

        # --------------------------------------------------------
        # Save summary arrays
        # --------------------------------------------------------
        final_total_size[ss] = count_total
        final_assim_size[ss] = count_assim
        final_mean_jo_diff[ss] = mean_jo_diff
        final_sum_jo_diff[ss] = sum_jo_diff
        final_max_abs_jo_diff[ss] = max_abs_jo_diff

        # --------------------------------------------------------
        # Plot Jo-diff histogram
        # --------------------------------------------------------
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

        ncd.close()

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
        label="conv"
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

    args = sys.argv
    nargs = len(args) - 1

    if nargs < 1 or len(sys.argv[1]) < 10:

        print(
            f"Usage: "
            f"{os.path.basename(sys.argv[0])} "
            f"<YYYYMMDDHH>"
        )

        sys.exit(1)

    CDATE = sys.argv[1]

    analyze_conv(CDATE)

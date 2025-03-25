#!/usr/bin/env python
import os
import sys


def get_run_directory():
    """Get the run directory, handling both scripts and Jupyter Notebooks."""
    if "ipykernel" in sys.modules:  # Running in a Jupyter Notebook
        return os.getcwd()
    else:  # Running as a script
        return os.path.dirname(os.path.abspath(__file__))


# add ../funcs/ to the current path
sys.path.append(os.path.join(get_run_directory(), "../funcs"))

from base import load_inv_bkg_ana

files = {
    "inv": "../data/samples/mpasjedi/invariant.nc",
    "bkg": "../data/samples/mpasjedi/bkg.nc",
    "ana": "../data/samples/mpasjedi/ana.nc",
}
datasets = load_inv_bkg_ana(files)

from contour_increment import contour_increment

parms = {
    "plot_box_width": 80.0,
    "plot_box_height": 40.0,
    "cen_lat": 34.5,
    "cen_lon": -97.5,
    "convert_theta_to_t": True,
}
parms["ilevel"] = 2
contour_increment(datasets, parms, f"L{parms['ilevel']}")
parms["ilevel"] = 20
contour_increment(datasets, parms, f"L{parms['ilevel']}")
parms["ilevel"] = 30
contour_increment(datasets, parms, f"L{parms['ilevel']}")

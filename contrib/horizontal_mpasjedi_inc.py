#!/usr/bin/env python
from matplotlib.tri import Triangulation, TriAnalyzer
import warnings
import os
import colormap
import numpy as np
import matplotlib.ticker as mticker
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.feature as cfeature
import cartopy.crs as ccrs
import cartopy
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import matplotlib
matplotlib.use('agg')

warnings.filterwarnings('ignore')

############ USER INPUT ##########################################################
plot_var = "Increment"
decimal = 3            # number of decimals to round for text boxes

plot_box_width = 72.   # define size of plot domain (units: lat/lon degrees)
plot_box_height = 36.
cen_lat = 34.5
cen_lon = -97.5

# Determine extent for plot domain
half = plot_box_width / 2.
left = cen_lon - half
right = cen_lon + half
half = plot_box_height / 2.
bot = cen_lat - half
top = cen_lat + half


def plot_inc(var_inc, decimal=3):
    max_inc = np.around(np.max(var_inc), decimal)
    min_inc = np.around(np.min(var_inc), decimal)
    # decide the color contours based on the increment values
    clevmax = max((abs(max_inc), abs(min_inc)))
    inc = 0.05 * clevmax
    clevs = np.arange(-1.0 * clevmax, 1.0 * clevmax + inc, inc)
    cm = colormap.diff_colormap(clevs)
    return clevs, cm


def main():
    # janalysis = "/scratch1/BMC/wrfruc/jjhu/rundir/wrkflow-test/Btuning/2024050601_lbc/uv233/singleob_rh4rv0_avgheight_std14/mpasin.nc"
    # jbackgrnd = "/scratch1/BMC/wrfruc/jjhu/rundir/wrkflow-test/Btuning/2024050601_tuneB/bkg/mpasout.2024-05-06_01.00.00.nc"
    # jstatic = "/scratch1/BMC/wrfruc/jjhu/rundir/wrkflow-test/Btuning/2024050601_tuneB/invariant.nc"

    janalysis = "../data/samples/mpasjedi/ana.nc"
    jbackgrnd = "../data/samples/mpasjedi/bkg.nc"
    jstatic = "../data/samples/mpasjedi/invariant.nc"

    figdir = "./"

    # varible to plot
    variable = "T"

    target_lat, target_lon = 36.265, -95.145

    # Open NETCDF4 dataset for reading
    nc_a = Dataset(janalysis, mode='r')
    nc_b = Dataset(jbackgrnd, mode='r')
    f_latlon = Dataset(jstatic, "r")

    # read lat,lon information
    lats = np.array(f_latlon.variables['latCell'][:]) * 180.0 / np.pi  # Latitude of cells, rad
    lons0 = np.array(f_latlon.variables['lonCell'][:]) * 180.0 / np.pi  # Longitude of cells, rad
    lons = np.where(lons0 > 180.0, lons0 - 360.0, lons0)
    z = f_latlon.variables['zgrid'][:]  # Geometric height of layer interfaces, m MSL

    # Grab variables
    if variable == "T":  # Convert to temperature
        units = "K"
        jedi_a = nc_a.variables["theta"][0, :, :].astype(np.float64)  # (Time, nCells, nVertLevels)
        jedi_b = nc_b.variables["theta"][0, :, :].astype(np.float64)
        pres_a = (nc_a.variables['pressure_p'][0, :, :] + nc_b['pressure_base'][0, :, :])/100.0
        pres_b = (nc_b.variables['pressure_p'][0, :, :] + nc_b['pressure_base'][0, :, :])/100.0
        dividend_a = (1000.0/pres_a)**(0.286)
        dividend_b = (1000.0/pres_b)**(0.286)
        jedi_a = jedi_a / dividend_a
        jedi_b = jedi_b / dividend_b

    if variable == "Q":
        units = "mg/kg"
        jedi_a = nc_a.variables['qv'][0, :, :] * 1000000.0
        jedi_b = nc_b.variables['qv'][0, :, :] * 1000000.0

    if variable == "U":
        units = "m/s"
        jedi_a = nc_a.variables['uReconstructZonal'][0, :, :]
        jedi_b = nc_b.variables['uReconstructZonal'][0, :, :]

    if variable == "V":
        units = "m/s"
        jedi_a = nc_a.variables['uReconstructMeridional'][0, :, :]
        jedi_b = nc_b.variables['uReconstructMeridional'][0, :, :]

    jedi_inc_all = jedi_a - jedi_b  # the increment

    for lev in range(42, 43, 1):
        jedi_inc = jedi_inc_all[:, lev]

        # Print some final stats
        print(f"Level: {lev+1},  max: {np.around(np.max(jedi_inc), decimal)}, min: {np.around(np.min(jedi_inc), decimal)}")

        # CREATE PLOT ##############################
        fig = plt.figure(figsize=(6, 4))
        m1 = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree(central_longitude=0))

        # Set extent for both plots
        m1.set_extent([left, right, top, bot])

        # Add features to the subplots
        m1.add_feature(cfeature.COASTLINE)
        m1.add_feature(cfeature.BORDERS)
        m1.add_feature(cfeature.STATES)

        # Gridlines for the subplots
        gl1 = m1.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=0.5, color='k', alpha=0.25, linestyle='-')
        gl1.xlocator = mticker.FixedLocator(np.arange(-180., 181., 5.))
        gl1.ylocator = mticker.FixedLocator(np.arange(-80., 91., 5.))
        gl1.xformatter = LONGITUDE_FORMATTER
        gl1.yformatter = LATITUDE_FORMATTER
        gl1.xlabel_style = {'size': 5, 'color': 'gray'}
        gl1.ylabel_style = {'size': 5, 'color': 'gray'}

        # Create triangulation and mask
        triang = Triangulation(lons, lats)
        mask = TriAnalyzer(triang).get_flat_tri_mask(min_circle_ratio=0.1)
        triang.set_mask(mask)

        clevs, cm = plot_inc(jedi_inc)
        c1 = m1.tricontourf(triang, jedi_inc, clevs, cmap=cm, extend='both')

        # Add colorbar
        cbar1 = fig.colorbar(c1, orientation="horizontal", fraction=0.046, pad=0.07)
        cbar1.set_label(units, size=8)
        cbar1.ax.tick_params(labelsize=5, rotation=30)

        # Add titles, text, and save the figure
        plt.suptitle(f"{variable} Increment at Level: {lev+1}", fontsize=9, y=0.95)
        subtitle1_minmax = f"min: {np.around(np.min(jedi_inc), decimal)}\nmax: {np.around(np.max(jedi_inc), decimal)}"
        m1.text(left * 0.99, bot * 1.01, f"{subtitle1_minmax}", fontsize=6, ha='left', va='bottom')
        plt.tight_layout()
        plt.savefig(f"{figdir}/increment_{variable}_z{lev}.png", dpi=250, bbox_inches='tight')
        plt.close()


if __name__ == '__main__':
    main()

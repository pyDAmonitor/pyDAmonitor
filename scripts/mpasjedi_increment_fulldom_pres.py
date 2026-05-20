#!/usr/bin/env python
from scipy.interpolate import interp1d
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
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import matplotlib
matplotlib.use('agg')

warnings.filterwarnings('ignore')

# USER INPUT ##########################################################
# create variable with important info on each field requested
# "nc variable": [plot/title name, unit, colorbar scale, conversion factor for units]
var_lookup = {
    "theta": ["airTemperature", "K", 1.0, 1.0],
    "qv":    ["qVapor", "g/kg", 1.0, 1000.0],
    "u":     ["uZonalWind", "m/s", 1.0, 1.0],
}
# this is the name of the field needed in the mpasout.nc file
nc_keys = ["theta", "qv", "uReconstructZonal"]
expname = "TMS"  # used in plot and filename for saving
pressure_levels = [200, 300, 400, 500, 600, 700, 800, 900]  # pressure levels in hPa
plot_var = "Increment"
decimals = 2            # number of decimals to round for text boxes
# plot_box_width = 100.   # define size of plot domain (units: lat/lon degrees)
# plot_box_height = 50.
# cen_lat = 34.5
# cen_lon = -97.5
# different numbers for NA domain
plot_box_width = 120.
plot_box_height = 70.
cen_lat = 35
cen_lon = -98

# JEDI data
datapath = "./"
jstatic = "invariant.nc"  # file with grid info
janalysis = "analysis.nc"  # analysis file
jbackgrnd = "background.nc"  # background file

###################################################################################
# Set cartopy shapefile path
platform = os.getenv('HOSTNAME').upper()
if 'ORION' in platform:
    cartopy.config['data_dir'] = '/work/noaa/fv3-cam/sdegelia/cartopy'
elif 'H' in platform:  # Will need to improve this once Hercules is supported
    cartopy.config['data_dir'] = '/home/Donald.E.Lippi/cartopy'
# Load static grid
f_latlon = Dataset(jstatic, "r")
lats = np.array(f_latlon.variables['latCell'][:]) * 180.0 / np.pi
lons0 = np.array(f_latlon.variables['lonCell'][:]) * 180.0 / np.pi
lons = np.where(lons0 > 180.0, lons0 - 360.0, lons0)
# Create triangulation and mask
triang = Triangulation(lons, lats)
mask = TriAnalyzer(triang).get_flat_tri_mask(min_circle_ratio=0.1)
triang.set_mask(mask)

# Open NETCDF4 dataset for reading
nc_a = Dataset(janalysis, mode='r')
nc_b = Dataset(jbackgrnd, mode='r')

# Now loop through requested fields
for nc_key in nc_keys:
    # Checks settings for nc_key variable
    clean_name, unit_label, clevmax, conv_factor = var_lookup[nc_key]
    print(f"Processing {clean_name} ")

    # Read data and get dimensions
    jedi_a = nc_a.variables[nc_key][0, :, :].astype(np.float64)
    jedi_b = nc_b.variables[nc_key][0, :, :].astype(np.float64)

    # Pressure (needed for all variables)
    pres_a_raw = (nc_a.variables['pressure_p'][0, :, :] + nc_b['pressure_base'][0, :, :])/100.0
    pres_b_raw = (nc_b.variables['pressure_p'][0, :, :] + nc_b['pressure_base'][0, :, :])/100.0

    # read in surface pressure
    pres_sfc_a = nc_a.variables['surface_pressure'][0, :]/100
    pres_sfc_b = nc_b.variables['surface_pressure'][0, :]/100

    # create NaNs for values below the surface pressure
    pres_a = np.where(pres_a_raw <= pres_sfc_a[:, None], pres_a_raw, np.nan)
    pres_b = np.where(pres_b_raw <= pres_sfc_b[:, None], pres_b_raw, np.nan)

    # convert to temp for 'theta' nc_key exception
    if nc_key == "theta":
        dividend_a = (1000.0/pres_a)**(0.286)
        dividend_b = (1000.0/pres_b)**(0.286)
        jedi_a = jedi_a / dividend_a
        jedi_b = jedi_b / dividend_b

    # add same correction to jedi that we did to pres
    jedi_a = np.where(np.isnan(pres_a), np.nan, jedi_a)
    jedi_b = np.where(np.isnan(pres_b), np.nan, jedi_b)

    # apply conversion factor (e.g. *1000 for g/kg)
    jedi_inc_all = (jedi_a - jedi_b) * conv_factor

    # Interpolate using user-inputted pressure levels
    for pres_lev in pressure_levels:
        jedi_inc = np.zeros((jedi_inc_all.shape[0], 1))  # initialize array
        # loop over grid points
        for i in range(jedi_inc_all.shape[0]):
            # extract pressure level for current grid point
            p_levels = pres_a[i, :]  # p value at grid point
            jedi_inc_val = jedi_inc_all[i, :]  # corresponding increment
            # filter out NaNs
            valid = ~np.isnan(p_levels) & ~np.isnan(jedi_inc_val)
            # need 2 points to do interp
            if np.sum(valid) > 1:
                if pres_lev <= np.nanmax(p_levels[valid]):
                    interpolator = interp1d(p_levels[valid], jedi_inc_val[valid], kind='linear', bounds_error=False, fill_value=np.nan)
                    jedi_inc[i] = interpolator(pres_lev)
                else:
                    # Target pressure is below the ground at this cell
                    jedi_inc[i] = np.nan
            else:
                # Entire column is masked or insufficient data
                jedi_inc[i] = np.nan
        # reshape increment
        jedi_inc = jedi_inc.squeeze()

        # create plot
        fig = plt.figure(figsize=(7, 4))
        m1 = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree(central_longitude=0))

        # Determine extent for plot domain
        half = plot_box_width / 2.
        left = cen_lon - half
        right = cen_lon + half
        half = plot_box_height / 2.
        bot = cen_lat - half
        top = cen_lat + half

        # Set extent for both plots
        m1.set_extent([left, right, top, bot])

        # Add features to the subplots
        m1.add_feature(cfeature.COASTLINE)
        m1.add_feature(cfeature.BORDERS)
        m1.add_feature(cfeature.STATES)

        # Gridlines
        gl1 = m1.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=0.5, color='k', alpha=0.25, linestyle='-')
        gl1.xlocator = mticker.FixedLocator(np.arange(-180., 181., 5.))
        gl1.ylocator = mticker.FixedLocator(np.arange(-80., 91., 5.))
        gl1.xformatter = LONGITUDE_FORMATTER
        gl1.yformatter = LATITUDE_FORMATTER
        gl1.xlabel_style = {'size': 5, 'color': 'gray'}
        gl1.ylabel_style = {'size': 5, 'color': 'gray'}

        # Get levels for specific variable
        inc_step = 0.05 * clevmax
        clevs = np.arange(-1.0 * clevmax, 1.0 * clevmax + inc_step, inc_step)
        cm = colormap.diff_colormap(clevs)
        units = unit_label  # from the above variable

        # Plot data using triangulation
        c1 = m1.tricontourf(triang, jedi_inc, clevs, cmap=cm, extend='both')

        # Add colorbar
        cbar1 = fig.colorbar(c1, orientation="horizontal", fraction=0.046, pad=0.07)
        cbar1.set_label(units, size=8)
        cbar1.ax.tick_params(labelsize=5, rotation=30)

        # Titles and Text (Uses 'clean_name' and 'pres_lev' from the loops)
        plt.suptitle(f"{expname} {clean_name} {plot_var} at {pres_lev} hPa", fontsize=9, y=0.95)

        subtitle1_minmax = f"min: {np.around(np.min(jedi_inc), decimals)}\nmax: {np.around(np.max(jedi_inc), decimals)}"
        m1.text(left * 0.99, bot * 1.01, f"{subtitle1_minmax}", fontsize=6, ha='left', va='bottom')
        plt.tight_layout()

        plt.savefig(f"./{expname}_increment_{clean_name}_{pres_lev}hPa.png", dpi=250, bbox_inches='tight')
        plt.close(fig)

        # Print some final stats
        print("Stats:")
        print(f" {clean_name} max: {np.around(np.max(jedi_inc), decimals)}")

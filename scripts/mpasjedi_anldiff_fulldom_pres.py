#created 12 May 2026 by K. Eure: plots retro-averaged difference of analysis (of 2 retros) at user-specified pressure levels
#NOTE: this script is quite slow (due to reading in files and interpolation on MPAS), so running this in a batch job is advisable
#!/usr/bin/env python
from scipy.interpolate import interp1d
from matplotlib.tri import Triangulation, TriAnalyzer
import warnings
import os
import colormap
import numpy as np
import matplotlib.ticker as mticker
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from datetime import datetime, timedelta
import cartopy.feature as cfeature
import sys
import cartopy.crs as ccrs
import cartopy
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import matplotlib
matplotlib.use('agg')

if os.environ.get('LIBDIR') is not None:
    sys.path.append(os.environ['LIBDIR'])

warnings.filterwarnings('ignore')

# USER INPUT ##########################################################
# create variable with important info on each field requested
# "nc variable": [plot/title name, unit, colorbar scale, conversion factor for units]
var_lookup = {
    "theta": ["airTemperature", "K", 1.0, 1.0],
    "qv":    ["qVapor", "g/kg", 1.0, 1000.0],
    "uReconstructZonal":     ["windMagnitude", "m/s", 4.0, 1.0],
}
# this is the name of the field needed in the mpasout.nc file
nc_keys = ["theta", "qv", "uReconstructZonal"]
expname = "TMS"  # used in plot and filename for saving
pressure_levels = [250, 550, 850]  # pressure levels in hPa
plot_var = "Analysis Difference"
decimals = 2 # number of decimals to round for text boxes

# Input configurations
base_path1 = "/{retropathway}/com/rrfs/{versionnumber}" #pathway to control/conv experiment
base_path2 = "/{retropathway}/com/rrfs/{versionnumber}" #pathway to exp to compare against base_path1
jstatic = "invariant.nc" #arbitrary file for grid info
start_dt = datetime.strptime("YYYYMMDD HH", "%Y%m%d %H")
end_dt   = datetime.strptime("YYYYMMDD HH", "%Y%m%d %H")
subpath1 = "jedivar/det/mpasout.*.nc"
subpath2 = "jedivar/det/mpasout.*.nc"

# different numbers for NA domain
plot_box_width = 135.
plot_box_height = 80.
cen_lat = 45
cen_lon = -108

# Add for state line plotting
states_provinces = cfeature.NaturalEarthFeature(
    category='cultural',
    name='admin_1_states_provinces_lines',
    scale='50m',
    facecolor='none')

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
flat_mask = TriAnalyzer(triang).get_flat_tri_mask(min_circle_ratio=0.1)

# Loop through requested fields
for nc_key in nc_keys:
    # Checks settings for nc_key variable
    clean_name, unit_label, clevmax, conv_factor = var_lookup[nc_key]
    print(f"\n--- Processing {clean_name} ---")
    #initialize fields before hourly loop
    sum_jedi_diff_3d = None
    sum_pres_1_3d = None
    valid_obs_count = None # Added this to track non-NaN counts per cell
    count = 0 #resets before every time loop
    current_dt = start_dt #ensure time is at beginning

    # Loop over hourly cycles
    while current_dt <= end_dt:
        date_str = current_dt.strftime("%Y%m%d")
        hour_str = current_dt.strftime("%H")
        #specific filename for this time
        fname = current_dt.strftime("mpasout.%Y-%m-%d_%H.00.00.nc")
        #construct full paths
        file_path1 = os.path.join(base_path1, f"rrfs.{date_str}", hour_str, "jedivar", "det", fname)
        file_path2 = os.path.join(base_path2, f"rrfs.{date_str}", hour_str, "jedivar", "det", fname)
        ymdh = current_dt.strftime("%Y%m%d%H") #for labeling
        time_label = current_dt.strftime("%m-%d %H")

        # Check for missing file, 'continue' goes to next iteration
        if not os.path.exists(file_path1):
            print(f"Missing: {file_path1}")
            current_dt += timedelta(hours=1)
            continue
        try:
            #read mode
            nc_1 = Dataset(file_path1, mode='r') #cntrl
            nc_2 = Dataset(file_path2, mode='r') #exp of interest
            #read in fields and get dimensions
            jedi_1 = nc_1.variables[nc_key][0, :, :].astype(np.float64)
            jedi_2 = nc_2.variables[nc_key][0, :, :].astype(np.float64)
            #read in pressure
            pres_1_raw = (nc_1.variables['pressure_p'][0,:,:] + nc_1['pressure_base'][0,:,:])/100.0
            pres_2_raw = (nc_2.variables['pressure_p'][0,:,:] + nc_2['pressure_base'][0,:,:])/100.0
            #fix put in - use surface pressure to mask any locations that have pres_# values below the surface
            pres_sfc_1 = nc_1.variables['surface_pressure'][0,:]/100
            pres_sfc_2 = nc_2.variables['surface_pressure'][0,:]/100
            #screen out these values in each exp's field
            pres_1 = np.where(pres_1_raw <= pres_sfc_1[:, None], pres_1_raw, np.nan)
            pres_2 = np.where(pres_2_raw <= pres_sfc_2[:, None], pres_2_raw, np.nan)
            # convert from theta to temp when needed
            if nc_key == "theta":
                jedi_1 /= (1000.0/pres_1)**(0.286)
                jedi_2 /= (1000.0/pres_2)**(0.286)

            # calculate wind magnitude when needed
            if nc_key == "uReconstructZonal":
                jedi_1 = np.hypot(nc_1.variables[nc_key][0, :, :].astype(np.float64), nc_1.variables["uReconstructMeridional"][0, :, :].astype(np.float64))
                jedi_2 = np.hypot(nc_2.variables[nc_key][0, :, :].astype(np.float64), nc_2.variables["uReconstructMeridional"][0, :, :].astype(np.float64))
            #add same correction to jedi_# that we did to pres_#
            jedi_1 = np.where(np.isnan(pres_1), np.nan, jedi_1)
            jedi_2 = np.where(np.isnan(pres_2), np.nan, jedi_2)
            # convert to correct units
            jedi_diff_all = (jedi_2 - jedi_1) * conv_factor
            # create 3d sum arrays once we know # of levels
            if sum_jedi_diff_3d is None:
                sum_jedi_diff_3d = np.zeros_like(jedi_diff_all)
                sum_pres_1_3d = np.zeros_like(pres_1)
                valid_obs_count = np.zeros_like(jedi_diff_all)
            # collect diff and pres fields
            sum_jedi_diff_3d = np.nansum([sum_jedi_diff_3d, jedi_diff_all], axis=0)
            sum_pres_1_3d = np.nansum([sum_pres_1_3d, pres_1], axis=0)
            valid_obs_count += (~np.isnan(jedi_diff_all)).astype(int)
            count += 1
            print(f"{ymdh} collected")
            # close files
            nc_1.close(); nc_2.close()
        except Exception as e:
            print(f"Error: {e}")
        current_dt += timedelta(hours=1)

    # Interpolation and plotting phase
    if count > 0:
        # calculate 3d averages
        avg_diff_3d = np.divide(sum_jedi_diff_3d, valid_obs_count, out=np.full_like(sum_jedi_diff_3d, np.nan), where=valid_obs_count > 0)
        avg_pres_3d = np.divide(sum_pres_1_3d, valid_obs_count, out=np.full_like(sum_pres_1_3d, np.nan), where=valid_obs_count > 0)
        # loop through pressure levels only once per field
        for pressure_level in pressure_levels:
            print(f"Interpolating to {pressure_level} hPa...")
            # Create the 1D map array
            jedi_diff = np.zeros(lons.shape)
            for i in range(avg_diff_3d.shape[0]):
                # Filter out NaNs before interpolating for this specific profile
                valid_mask = ~np.isnan(avg_pres_3d[i, :]) & ~np.isnan(avg_diff_3d[i, :])
                if np.any(valid_mask):
                    interpolator = interp1d(avg_pres_3d[i, valid_mask], avg_diff_3d[i, valid_mask], kind='linear', bounds_error=False, fill_value=np.nan)
                    jedi_diff[i] = interpolator(pressure_level)
                else:
                    jedi_diff[i] = np.nan
            # Plotting logic below
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

            # create mask for nans for specific pressure level
            nan_mask = np.any(np.isnan(jedi_diff[triang.triangles]), axis=1)
            combined_mask = np.logical_or(flat_mask, nan_mask)
            triang.set_mask(combined_mask)

            # tricontourf requires a finite array even if the triangles are masked
            jedi_diff_finite = np.where(np.isnan(jedi_diff), 0.0, jedi_diff)

            # Plot data using triangulation
            c1 = m1.tricontourf(triang, jedi_diff_finite, clevs, cmap=cm, extend='both')

            # Add colorbar
            cbar1 = fig.colorbar(c1, orientation="horizontal", fraction=0.046, pad=0.07)
            cbar1.set_label(units, size=8)
            cbar1.ax.tick_params(labelsize=5, rotation=30)

            # Titles and Text (Uses 'clean_name' and 'pres_lev' from the loops)
            plt.suptitle(f"{expname} {clean_name} {plot_var} at {pressure_level} hPa", fontsize=9, y=0.95)
            subtitle1_minmax = f"min: {np.around(np.nanmin(jedi_diff), decimals)}\nmax: {np.around(np.nanmax(jedi_diff), decimals)}"
            m1.text(left * 0.99, bot * 1.01, f"{subtitle1_minmax}", fontsize=6, ha='left', va='bottom')
            plt.tight_layout()

            plt.savefig(f"./{expname}_anldiff_{clean_name}_{pressure_level}hPa.png", dpi=250, bbox_inches='tight')
            plt.close(fig)

    else:
        print(f"No data collected for {nc_key}.")


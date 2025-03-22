#!/usr/bin/env python
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.ticker as mticker
import numpy as np
import colormap
import os
import warnings
from matplotlib.tri import Triangulation, TriAnalyzer
warnings.filterwarnings('ignore')

def contour_increment(datasets, parms, fig_name=None):
    ############ USER INPUT ##########################################################
    ilevel =  parms['ilevel']
    plot_box_width = parms['plot_box_width']
    plot_box_height = parms['plot_box_height']
    cen_lat = parms['cen_lat']
    cen_lon = parms['cen_lon']
    convert_theta_to_t = parms['convert_theta_to_t']
    decimals = 2            # number of decimals to round for text boxes
    #contour_max = 2.0      # max contour level for colorbar increment plots
    ###################################################################################
    cartopy.config['data_dir']='../data/cartopy'

    ####
    dsInv = datasets['inv']
    dsAna = datasets['ana']
    dsBkg = datasets['bkg']
    lats = np.array(dsInv.variables['latCell'][:]) * 180.0 / np.pi
    lons0 = np.array(dsInv.variables['lonCell'][:]) * 180.0 / np.pi
    lons = np.where(lons0 > 180.0, lons0 - 360.0, lons0)

    ilevel = ilevel - 1  # subtract 1 because python uses indices starting from 0
    ana = dsAna.variables["theta"][0, :, ilevel].astype(np.float64)
    bkg = dsBkg.variables["theta"][0, :, ilevel].astype(np.float64)

    # Convert theta to temperature
    if convert_theta_to_t:
        pres_a = (dsAna.variables['pressure_p'][0,:,ilevel] + dsBkg['pressure_base'][0,:,ilevel])/100.0
        pres_b = (dsBkg.variables['pressure_p'][0,:,ilevel] + dsBkg['pressure_base'][0,:,ilevel])/100.0
        dividend_a = (1000.0/pres_a)**(0.286)
        dividend_b = (1000.0/pres_b)**(0.286)
        ana = ana / dividend_a
        bkg = bkg / dividend_b

    # Compute increment and its max/min
    increment = ana - bkg
    inc_max=np.around(np.max(increment), decimals)
    inc_min=np.around(np.min(increment), decimals)

    # decide the maximum color contours based on the increment values
    contour_max=round( (abs(inc_max)+abs(inc_min)) * 0.5 )

    def plot_T_inc(var_n, clevmax):
        longname = "airTemperature"
        units = "K"
        inc = 0.05 * clevmax
        clevs = np.arange(-1.0 * clevmax, 1.0 * clevmax + inc, inc)
        cm = colormap.diff_colormap(clevs)
        return clevs, cm, units, longname

    # CREATE PLOT ##############################
    fig = plt.figure(figsize=(7, 4)) #, dpi=200)
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

    # Plot the data using triangulation
    clevs, cm, units, longname = plot_T_inc(increment, contour_max)
    c1 = m1.tricontourf(triang, increment, clevs, cmap=cm, extend='both')

    # Add colorbar
    cbar1 = fig.colorbar(c1, orientation="horizontal", fraction=0.046, pad=0.07)
    cbar1.set_label(units, size=8)
    cbar1.ax.tick_params(labelsize=5, rotation=30)

    # Add titles, text, and save the figure
    # Add 1 to ilevel since indicies start from 0
    plt.suptitle(f"Temperature increment at Level: {ilevel+1}", fontsize=9, y=0.95)
    subtitle1_minmax = f"min: {np.around(np.min(increment), decimals)}\nmax: {np.around(np.max(increment), decimals)}"
    m1.text(left * 0.99, bot * 1.01, f"{subtitle1_minmax}", fontsize=6, ha='left', va='bottom')
    plt.tight_layout()
    if fig_name:
        plt.savefig(fig_name, dpi=250, bbox_inches='tight')
    else:
        plt.show()

    # Print some final stats
    print(f"Stats:")
    print(f" {longname} max: {inc_max}")
    print(f" {longname} min: {inc_min}")

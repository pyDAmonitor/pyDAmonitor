#!/usr/bin/env python
# flake8: noqa
import os
import sys
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from mpl_toolkits.basemap import shiftgrid
import numpy as np
import pygrib
from netCDF4 import Dataset
matplotlib.use('agg')
import warnings
warnings.filterwarnings('ignore')
import colormap

var = "T"
expt="UV"
#var=sys.argv[1]
#expt=sys.argv[2]

lev=32

lat_obs, lon_obs = 36.265, 264.855
extent = 8   # domain box, obs(center) lat/lon +/- extent
lat_ll = lat_obs - extent
lat_ur = lat_obs + extent
lon_ll = lon_obs - extent
lon_ur = lon_obs + extent

maindir="/scratch2/BMC/zrtrr/chunhua/tmp/RRFSv1_13km/rrfs.v0.8.6/stmp/2024050601"
analdir=f"anal_conv_gsi.single{expt}"
#figdir=f"{maindir}/{analdir}"
figdir="./"

# read T, u, v from fv3_dynvars
if var == "T" or var == "u" or var == "v":
    #anal = f"{maindir}/{analdir}/fv3_dynvars"
    #bkg = f"{maindir}/anal_conv_gsi.fresh/fv3_dynvars"
    anal = "../data/samples/fv3/fv3_dynvars.ana"
    bkg = "../data/samples/fv3/fv3_dynvars.bkg"
if var == "sphum":
    #anal = f"{maindir}/{analdir}/fv3_tracer"
    #bkg = f"{maindir}/anal_conv_gsi.fresh/fv3_tracer"
    anal = "../data/samples/fv3/fv3_tracer.ana"
    bkg = "../data/samples/fv3/fv3_tracer.bkg"
#static = f"{maindir}/anal_conv_gsi.fresh/fv3_grid_spec"
static = "../data/samples/fv3/fv3_grid_spec"

# Open NETCDF4 dataset for reading
nc_a = Dataset(anal, mode='r')
nc_b = Dataset(bkg, mode='r')
a = nc_a.variables[var][0, lev, :, :].astype(np.float64) # float T(Time, zaxis_1=65, yaxis_2, xaxis_1) ;
b = nc_b.variables[var][0, lev, :, :].astype(np.float64) 

# read lat,lon information
f_latlon = Dataset(static, "r")
lats = np.array(f_latlon.variables['grid_lat'][::])   # float grid_latt(grid_yt=252, grid_xt=420)
lons = np.array(f_latlon.variables['grid_lon'][::])   # float grid_lont(grid_yt, grid_xt)

def plot_data(data, lat, lon, title):

    '''
    Input parameters:

        data: 2D Numpy array to be plotted
        lat: 2D Numpy array of latitude
        lon: 2D Numpy array of longitude
        var: String describing the variable being plotted.

    Draws a Basemap representation with the contoured data overlayed, with a colorbar.

    '''

    def trim_grid():
        '''
        The u, v, and H data are all on grids either one column, or one row smaller than lat/lon.
        Return the smaller lat, lon grids, given the shape of the data to be plotted.
        '''
        y, x = np.shape(data)
        return lat[:y, :x], lon[:y, :x]

    def eq_contours():
        minval = np.amin(data)
        maxval = np.amax(data)
        clevmax = max(abs(minval), abs(maxval))
        inc = 0.05 * clevmax
        clevs = np.arange(-1.0 * clevmax, 1.0 * clevmax + inc, inc)
        cm = colormap.diff_colormap(clevs)
        return clevs, cm

    m = Basemap(projection='mill',
                llcrnrlon=lon_ll,
                urcrnrlon=lon_ur,
                llcrnrlat=lat_ll,
                urcrnrlat=lat_ur,
                resolution='c',
               )

    lat_trim, lon_trim = trim_grid()
    plt.figure(figsize=(8,8))
    x, y = m(lon_trim, lat_trim)

    clevs, cm = eq_contours()

    cs = m.contourf(x, y, data, clevs, cmap=cm, extend='both')
    m.drawcoastlines();
    m.drawmapboundary();
    m.drawstates();
    m.drawparallels(np.arange(-90.,120.,2),labels=[1,0,0,0]);
    m.drawmeridians(np.arange(-180.,180.,2),labels=[0,0,0,1]);
    plt.colorbar(cs,orientation='vertical', shrink=0.5);
    plt.title(f"{title}")
   # plt.savefig(f"{figdir}/increment_{var}_z{lev}.png", dpi=200, bbox_inches='tight')
    plt.savefig(f"{figdir}/increment_{var}_z{lev}.png", bbox_inches='tight')

def main():
    title = f'Analysis Increment for {var}'
    plot_data(a-b, lats, lons, title)

if __name__ == '__main__': main()


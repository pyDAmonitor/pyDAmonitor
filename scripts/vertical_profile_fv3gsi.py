#!/usr/bin/env python
# flake8: noqa
import warnings
import os
import sys
from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import colormap
import matplotlib
matplotlib.use('agg')
warnings.filterwarnings('ignore')

lat_obs, lon_obs = 36.265, 264.855

var = "T"
expt = "UV"
# var=sys.argv[1]
# expt=sys.argv[2]

# Load MPAS forecast file
maindir = "/scratch2/BMC/zrtrr/chunhua/tmp/RRFSv1_13km/rrfs.v0.8.6/stmp/2024050601"
analdir = f"anal_conv_gsi.single{expt}"
# figdir=f"{maindir}/{analdir}"
figdir = "./"

# read T, u, v from fv3_dynvars
if var == "T" or var == "u" or var == "v":
    # anal = f"{maindir}/{analdir}/fv3_dynvars"
    # bkg = f"{maindir}/anal_conv_gsi.fresh/fv3_dynvars"
    anal = "../data/samples/fv3/fv3_dynvars.ana"
    bkg = "../data/samples/fv3/fv3_dynvars.bkg"
if var == "sphum":
    # anal = f"{maindir}/{analdir}/fv3_tracer"
    # bkg = f"{maindir}/anal_conv_gsi.fresh/fv3_tracer"
    anal = "../data/samples/fv3/fv3_tracer.ana"
    bkg = "../data/samples/fv3/fv3_tracer.bkg"
# static = f"{maindir}/anal_conv_gsi.fresh/fv3_grid_spec"
static = "../data/samples/fv3/fv3_grid_spec"
# nc_delp = f"{maindir}/{analdir}/fv3_dynvars"
nc_delp = "../data/samples/fv3/fv3_dynvars.ana"

if var == "T":
    unit = "K"
if var == "u" or var == "v":
    unit = "m/s"
if var == "sphum":
    unit = "g/kg"

# Open NETCDF4 dataset for reading
nc_a = Dataset(anal, mode='r')
nc_b = Dataset(bkg, mode='r')

f_latlon = Dataset(static, "r")
f_delp = Dataset(nc_delp, "r")


def trim_grid(data, lats, lons):
    '''
    The u, v, and H data are all on grids either one column, or one row smaller than lat/lon.
    Return the smaller lat, lon grids, given the shape of the data to be plotted.
    '''
    y, x = np.shape(data)
    return lats[:y, :x], lons[:y, :x]


def latlon_to_yx(lats, lons, lat_obs, lon_obs):
    # y, x = np.unravel_index( (np.abs(lats - lat_obs) + np.abs(lons - lon_obs)).argmin(), lats.shape )
    y, x = np.unravel_index((np.sqrt((lats - lat_obs)**2 + (lons - lon_obs)**2)).argmin(), lats.shape)
    return y, x


def plot_inc(jedi_inc):
    max_inc = np.around(np.max(jedi_inc), 3)
    min_inc = np.around(np.min(jedi_inc), 3)
    # decide the color contours based on the increment values
    # clevmax_incr=round( (abs(max_inc)+abs(min_inc)) * 0.5 )
    clevmax = max((abs(max_inc), abs(min_inc)))
    inc = 0.05 * clevmax
    clevs = np.arange(-1.0 * clevmax, 1.0 * clevmax + inc, inc)
    cm = colormap.diff_colormap(clevs)
    # return clevs
    # cm = colormap.diff_colormap(clevs)
    return clevs, cm


def get_pres(delp):
    pres = 0
    pressure = np.empty(len(delp)).astype(np.float64)
    for i in range(len(delp)):
        pres = pres + delp[i]
        pressure[i] = pres / 100.
    return pressure

# plot cross section


def cross_section(latlon, levs, jedi_inc_y, clevs, cm, title, xlab, ylab):
    fig = plt.figure(figsize=(8, 8))
    c1 = plt.contourf(latlon, levs, jedi_inc_y, clevs, cmap=cm, extend='both')
    plt.xlabel(xlab, size=14)
    plt.ylabel(ylab, size=14)
    plt.title(title)
    plt.gca().invert_yaxis()  # optional, depending on your z direction
    # Add colorbar
    cbar1 = fig.colorbar(c1, orientation="horizontal", fraction=0.046, pad=0.1)
    cbar1.set_label(f"{var}_inc [{unit}]", size=14)
    cbar1.ax.tick_params(labelsize=10, rotation=30)
    plt.grid()


def main():

    # read lat,lon information
    lats0 = np.array(f_latlon.variables['grid_lat'][::])   # float grid_latt(grid_yt=252, grid_xt=420)
    lons0 = np.array(f_latlon.variables['grid_lon'][::])   # float grid_lont(grid_yt, grid_xt)
    print(np.shape(lats0))
    print(np.shape(lons0))

    y, x = latlon_to_yx(lats0, lons0, lat_obs, lon_obs)
    print(y, x)
    print(lats0[y, x], lons0[y, x])

    # get delp
    delp = f_delp.variables["delp"][0, :, y, x].astype(np.float64)
    pressure = get_pres(delp)

    a = nc_a.variables[var][0, :, :, :].astype(np.float64)  # float T(Time, zaxis_1=65, yaxis_2=252, xaxis_1=420) ;
    b = nc_b.variables[var][0, :, :, :].astype(np.float64)  # float T(Time, zaxis_1=65, yaxis_2=252, xaxis_1=420) ;

    # Convert from kg/kg to g/kg
    if var == "sphum":
        a = a * 1000.0
        b = b * 1000.0

    data = a[0, :, :]
    lats, lons = trim_grid(data, lats0, lons0)
    print(np.shape(a))

    # get 1-d vertical profile at the obs lat/lon
    jedi_a = a[:, y, x]  # float T(Time, zaxis_1=65, yaxis_2=252, xaxis_1=420) ;
    jedi_b = b[:, y, x]  # float T(Time, zaxis_1=65, yaxis_2=252, xaxis_1=420) ;
    print(np.shape(jedi_a))
    jedi_inc = jedi_a - jedi_b
    nlevs = len(jedi_inc)
    levs = np.arange(len(jedi_inc))

    # get 2-d vertical profile at the obs lat
    jedi_a_xz = a[:, y, :]
    jedi_b_xz = b[:, y, :]
    jedi_inc_xz = jedi_a_xz - jedi_b_xz
    print(np.shape(jedi_inc_xz))

    # get 2-d vertical profile at the obs lon
    jedi_a_yz = a[:, :, x]
    jedi_b_yz = b[:, :, x]
    jedi_inc_yz = jedi_a_yz - jedi_b_yz
    print(np.shape(jedi_inc_yz))

    xlab = f"{var}_inc [{unit}]"
    # plot against pressures
    plt.plot(jedi_inc, pressure)
    plt.xlabel(xlab)
    plt.ylabel("Pressure (mb)")
    plt.title(f"Vertical distribution at lat={lat_obs}, lon={lon_obs}")
    plt.gca().invert_yaxis()  # optional, depending on your z direction
    plt.grid(linestyle='-')
    plt.tight_layout()
    plt.savefig(f'{figdir}/{var}_inc_p.png')
    plt.close()

    # plot against model leves
    levs = np.arange(len(jedi_inc))
    plt.plot(jedi_inc, levs)
    plt.xlabel(xlab)
    plt.ylabel("Vertical Level")
    plt.title(f"Vertical distribution at lat={lat_obs}, lon={lon_obs}")
    plt.gca().invert_yaxis()  # optional, depending on your z direction
    plt.grid(linestyle='-')
    plt.tight_layout()
    plt.savefig(f'{figdir}/{var}_inc_z.png')
    plt.close()

    clevs, cm = plot_inc(jedi_inc)
    # make longitude-pressure(/levels) cross section
    title = f"X-Z Cross section of {var}_inc [{unit}]  at lat={lat_obs}"
    latlon = lons[0, :]
    xlab = "Longitudes"
    ylab = "Vertical Level"
    cross_section(latlon, levs, jedi_inc_xz, clevs, cm, title, xlab, ylab)
    plt.tight_layout()
    plt.savefig(f'{figdir}/{var}_inc_xz.png')
    plt.close()
    ylab = "Pressure (hPa)"
    cross_section(latlon, pressure, jedi_inc_xz, clevs, cm, title, xlab, ylab)
    plt.tight_layout()
    plt.savefig(f'{figdir}/{var}_inc_xp.png')
    plt.close()

    # make latitude-pressure(/levels) cross section
    title = f"Y-Z Cross section of {var}_inc [{unit}]  at lon={lon_obs}"
    latlon = lats[:, 0]
    xlab = "Latitudes"
    ylab = "Vertical Level"
    cross_section(latlon, levs, jedi_inc_yz, clevs, cm, title, xlab, ylab)
    plt.tight_layout()
    plt.savefig(f'{figdir}/{var}_inc_yz.png')
    plt.close()
    ylab = "Pressure (hPa)"
    cross_section(latlon, pressure, jedi_inc_yz, clevs, cm, title, xlab, ylab)
    plt.tight_layout()
    plt.savefig(f'{figdir}/{var}_inc_yp.png')


if __name__ == '__main__':
    main()

#!/usr/bin/env python
# flake8: noqa
from netCDF4 import Dataset
import matplotlib.axes as maxes
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt
import os
import sys
import cartopy.crs as ccrs
from cartopy.mpl.ticker import (LongitudeFormatter, LatitudeFormatter,
                                LatitudeLocator, LongitudeLocator)
from collections.abc import Iterable
import numpy as np
import matplotlib
matplotlib.use('AGG')

# expdate=sys.argv[1]
# expdate='20250401'
# exphh=sys.argv[2]
# exphh='01'

gsi_or_jedi = 'jedi'  # 'jedi'; diag from gsi or jedi
hgt_or_prs = 'prs'  # use height (hgt) or pressure (prs) for vertical subset and profile

# maindir='/lfs6/BMC/wrfruc/MPAS_dev4/com/rrfs/v2.0.9'
# ncfile = f'./jdiag_aircar_t133.nc'
# jfile = f'{maindir}/rrfs.{expdate}/{exphh}/jedivar/det/{ncfile}'
jfile = '../data/mpasjedi/jdiag_aircar_t133.nc'

gfile_anl = '../data/gsi/diag_conv_q_anl.2024050601.nc4'
gfile_ges = '../data/gsi/diag_conv_q_ges.2024050601.nc4'

VARIABLE = 'airTemperature'
# VARIABLE='q'
# VARIABLE='U'
# VARIABLE='windEastward'
# VARIABLE='windNorthward'

if gsi_or_jedi == 'jedi':
    print('read jedi file=', jfile)
    ncDB = Dataset(jfile, 'r')
    qc = np.array(ncDB.groups['EffectiveQC2'].variables[VARIABLE][:])
#   obs = np.array(ncDB.groups['ObsValue'].variables[VARIABLE][:])
    omb = np.array(ncDB.groups['ombg'].variables[VARIABLE][:])
    oma = np.array(ncDB.groups['oman'].variables[VARIABLE][:])
    hgt = np.array(ncDB.groups['MetaData'].variables['height'][:])
    prs = np.array(ncDB.groups['MetaData'].variables['pressure'][:]) / 100.0  # Pa to hPa
#   lat = np.array(ncDB.groups['MetaData'].variables['latitude'][:])
#   lon = np.array(ncDB.groups['MetaData'].variables['longitude'][:])
#   obs = obs[ qc[:]==0 ]
    oma = oma[qc[:] == 0]
    omb = omb[qc[:] == 0]
    hgt = hgt[qc[:] == 0]
    prs = prs[qc[:] == 0]
#   lat = lat[ qc[:]==0 ]
#   lon = lon[ qc[:]==0 ]

if gsi_or_jedi == 'gsi':
    print('read GSI files=', gfile_anl, gfile_ges)
    anl = Dataset(gfile_anl, 'r')
    ges = Dataset(gfile_ges, 'r')
    iuse_anl = np.array(anl.variables['Analysis_Use_Flag'][:])
    iuse_ges = np.array(ges.variables['Analysis_Use_Flag'][:])
    if VARIABLE == 'U' or VARIABLE == 'u':
        omb = np.array(ges.variables['u_Obs_Minus_Forecast_adjusted'][:])
        oma = np.array(anl.variables['u_Obs_Minus_Forecast_adjusted'][:])
    elif VARIABLE == 'V' or VARIABLE == 'v':
        omb = np.array(ges.variables['v_Obs_Minus_Forecast_adjusted'][:])
        oma = np.array(anl.variables['v_Obs_Minus_Forecast_adjusted'][:])
    else:
        omb = np.array(ges.variables['Obs_Minus_Forecast_adjusted'][:])
        oma = np.array(anl.variables['Obs_Minus_Forecast_adjusted'][:])
    if VARIABLE == 'Humidity' or VARIABLE == 'q':
        oma = oma * 1000
        omb = omb * 1000
    print(len(omb))
    print(len(oma))
    prs_anl = np.array(anl.variables['Pressure'][:])
    prs_ges = np.array(ges.variables['Pressure'][:])
    hgt_anl = np.array(anl.variables['Height'][:])
    hgt_ges = np.array(ges.variables['Height'][:])
#   lat = np.array(anl.variables['Latitude'][:])
#   lon = np.array(anl.variables['Longitude'][:])
    oma = oma[iuse_anl[:] == 1]
    omb = omb[iuse_ges[:] == 1]
    hgt_anl = hgt_anl[iuse_anl[:] == 1]
    hgt_ges = hgt_ges[iuse_ges[:] == 1]
    prs_anl = prs_anl[iuse_anl[:] == 1]
    prs_ges = prs_ges[iuse_ges[:] == 1]
#   lat = lat[ iuse[:]==1 ]
#   lon = lon[ iuse[:]==1 ]
    print(len(oma))
    print(len(omb))

nobs = np.count_nonzero(~np.isnan(oma))
print('nobs:', nobs)

oma_bias = np.nanmean(oma)
omb_bias = np.nanmean(omb)

oma_rms = np.sqrt(np.nanmean(oma ** 2))
omb_rms = np.sqrt(np.nanmean(omb ** 2))

print('oma bias:', oma_bias)
print('omb bias:', omb_bias)
print('oma rms:', oma_rms)
print('omb rms:', omb_rms)

ratio = (omb_rms - oma_rms) / omb_rms
print('Fitting Ratio (rms):', ratio)

f = open(f'omaomb_stat.txt', 'w', newline='')
f.write('{0:14}  {1:>10}  {2:>10} {3:>10} {4:>10} {5:>10} {6:>11} \n'.format('layer', 'omb_bias', 'oma_bias', 'omb_rms', 'oma_rms', 'fit_ratio', 'obs_count'))
f.write('{0:14}  {1:10.3f}  {2:10.3f} {3:10.3f} {4:10.3f} {5:10.3f} {6:11d} \n'.format('whole', omb_bias, oma_bias, omb_rms, oma_rms, ratio, nobs))

if hgt_or_prs == 'hgt':
    hmin = 0
    hmax = 14000
    hstep = 1000
    layer_list = range(hmin, hmax, hstep)  # by height
    units = "m"

if hgt_or_prs == 'prs':
    hmax = 1200
    layer_list = [50, 100, 150, 200, 250, 300, 400, 600, 800, 900, 1000, 1200]  # by pressure
    units = "hPa"

nlayer = len(layer_list)


def subset(data, hgt, h1, h2):
    data2 = data[(hgt[:] >= h1) & (hgt[:] < h2)]
    return data2


def main():

    biasa = np.empty(nlayer)
    biasb = np.empty(nlayer)
    rmsa = np.empty(nlayer)
    rmsb = np.empty(nlayer)
    ratio = np.empty(nlayer)
    obscount = np.empty(nlayer, dtype=int)
    layer = [''] * nlayer

    for i, hgts in enumerate(layer_list):
        tmpa = np.empty(len(oma))
        tmpb = np.empty(len(oma))
        h1 = layer_list[i]
        if i+1 < nlayer:
            h2 = layer_list[i+1]
        else:
            h2 = hmax
        layer[i] = f'{h1}-{h2}{units}'
        print(h1, '-', h2)
        if gsi_or_jedi == 'jedi':
            tmpa = subset(oma, globals()[hgt_or_prs], h1, h2)
            tmpb = subset(omb, globals()[hgt_or_prs], h1, h2)
        if gsi_or_jedi == 'gsi':
            tmpa = subset(oma, globals()[f'{hgt_or_prs}_anl'], h1, h2)
            tmpb = subset(omb, globals()[f'{hgt_or_prs}_ges'], h1, h2)
        obscount[i] = np.count_nonzero(~np.isnan(tmpa))
        if obscount[i] > 0:
            biasa[i] = np.nanmean(tmpa)
            rmsa[i] = np.sqrt(np.nanmean(tmpa ** 2))
            biasb[i] = np.nanmean(tmpb)
            rmsb[i] = np.sqrt(np.nanmean(tmpb ** 2))
            ratio[i] = (rmsb[i] - rmsa[i]) / rmsb[i]
            f.write('{0:14}  {1:10.3f}  {2:10.3f} {3:10.3f} {4:10.3f} {5:10.3f}  {6:10d} \n'.format(layer[i],
                                                                                                    biasb[i], biasa[i], rmsb[i], rmsa[i], ratio[i], obscount[i]))

            title = f'{VARIABLE}: {h1}-{h2}'
        else:
            biasa[i] = None
            rmsa[i] = None
            biasb[i] = None
            rmsb[i] = None
            ratio[i] = None

    print('oma_bias=', biasa)
    print('omb_bias=', biasb)
    print('oma_rms=', rmsa)
    print('omb_rms=', rmsb)
    print('fit ratio=', ratio)
    print('obs count=', obscount)
    f.close()

    fig, ax = plt.subplots(1, 3,  sharey=True)

    ax[2].plot(ratio, layer, color='b', marker='o', linestyle='-', lw=1, markersize=3)
    ax[2].set_title('Fit Ratio', y=-0.06, pad=-14, fontsize=10)
    ax[1].plot(rmsa, layer, color='chocolate', marker='o', linestyle='-', lw=1, markersize=3, label='O-A')
    ax[1].plot(rmsb, layer, color='brown', marker='o', linestyle='-.', lw=1, markersize=3, label='O-B')
    ax[1].legend(fontsize=6, loc='upper right')
    ax[1].set_title('RMS', y=-0.06, pad=-14, fontsize=10)
    ax[0].plot(biasa, layer, color='limegreen', marker='o', linestyle='-', lw=1, markersize=3, label='O-A')
    ax[0].plot(biasb, layer, color='green', marker='o', linestyle='-.', lw=1, markersize=3, label='O-B')
    ax[0].tick_params(axis='y', rotation=30, labelsize=8)
    ax[0].legend(fontsize=6, loc='upper right')
    ax[0].set_title('BIAS', y=-0.06, pad=-14, fontsize=10)
    for layer, count in zip(layer, obscount):
        if count > 0:
            ax[2].text(ax[2].get_xlim()[1] * 1.05, layer, f"{count}", fontsize=10, verticalalignment="center")
    for ax1 in ax.flat:
        ax1.grid(linestyle=':')
        ax1.yaxis.set_inverted(True)
    fig.suptitle(VARIABLE)
    plt.tight_layout()
    plt.savefig(f'jdiag_profile.png', dpi=200, bbox_inches='tight')
    plt.close()


if __name__ == '__main__':
    main()

#!/usr/bin/env python
# import warnings
import cartopy.crs as ccrs
import geoviews.feature as gf
import holoviews as hv
# from holoviews import opts
import uxarray as ux
import numpy as np
hv.extension("bokeh")
maps = gf.coastline(projection=ccrs.PlateCarree(), line_width=1, scale="50m") \
    * gf.states(projection=ccrs.PlateCarree(), line_width=1, line_color='gray', scale="50m")


def mpas_plot(ux1D, maps, title, minval=None, maxval=None):
    import math
    # Get min and max
    if minval is None:
        amin = ux1D.min().item()
        minval = math.floor(amin)
    if maxval is None:
        amax = ux1D.max().item()
        maxval = math.ceil(amax)
    title += f" min={amin:.1f} max={amax:.1f}"

    # generate contour plot (Notes: #line_width=0.001)
    #        ux1D.plot(), levels=np.arange(minval, maxval, 0.5), filled=True).opts(line_color=None)
    contour_plot = hv.operation.contours(
        ux1D.plot(), levels=np.linspace(minval, maxval, num=20), filled=True
    ).opts(line_color=None)

    final = contour_plot.opts(
        width=800, height=500, cmap='coolwarm', clim=(minval, maxval), colorbar=True,
        show_legend=False, tools=['hover'], title=title
    ) * maps
    return final


# ~~~~~~~ beginning
#
grid_file = "../data/samples/mpasjedi/invariant.nc"
bkg_file = "../data/samples/mpasjedi/bkg.nc"
ana_file = "../data/samples/mpasjedi/ana.nc"

uxds_a = ux.open_dataset(grid_file, ana_file)
uxds_b = ux.open_dataset(grid_file, bkg_file)

uxvar = uxds_a['theta'] - 273.15

# generate color plot
nt = 0  # time dimension
lev = 0  # vertical level
plot = mpas_plot(uxvar.isel(Time=nt, nVertLevels=lev), maps, title=f'lev={lev}')
hv.save(plot, 'theta.png')

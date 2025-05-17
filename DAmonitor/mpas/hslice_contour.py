import math
import holoviews as hv
import numpy as np


def hslice_contour(ux_hslice, title, minval=None, maxval=None, width=800, height=500, clevs=20):
    # Get min and max
    if minval is None:
        amin = ux_hslice.min().item()
        minval = math.floor(amin)
    if maxval is None:
        amax = ux_hslice.max().item()
        maxval = math.ceil(amax)
    title += f" min={amin:.1f} max={amax:.1f}"

    # generate contour plot
    contour_plot = hv.operation.contours(
        ux_hslice.plot(),
        levels=np.linspace(minval, maxval, num=clevs),  # levels=np.arange(minval, maxval, 0.5)
        filled=True
    ).opts(
        line_color=None,  # line_width=0.001
        width=width, height=height,
        cmap='coolwarm', clim=(minval, maxval), colorbar=True,  # cmap="inferno"
        show_legend=False, tools=['hover'], title=title,
    )

    return contour_plot

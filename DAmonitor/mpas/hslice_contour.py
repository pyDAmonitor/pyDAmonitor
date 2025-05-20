import math
import holoviews as hv
import numpy as np


def hslice_contour(ux_hslice, title, cmin=None, cmax=None, width=800, height=500, clevs=20):
    # Get min and max
    amin = ux_hslice.min().item()
    amax = ux_hslice.max().item()
    title += f" min={amin:.1f} max={amax:.1f}"
    if cmin is None:
        cmin = math.floor(amin)
    if cmax is None:
        cmax = math.ceil(amax)

    # generate contour plot
    contour_plot = hv.operation.contours(
        ux_hslice.plot(),
        levels=np.linspace(cmin, cmax, num=clevs),  # levels=np.arange(cmin, cmax, 0.5)
        filled=True
    ).opts(
        line_color=None,  # line_width=0.001
        width=width, height=height,
        cmap='coolwarm', clim=(cmin, cmax), colorbar=True,  # cmap="inferno"
        show_legend=False, tools=['hover'], title=title,
    )

    return contour_plot

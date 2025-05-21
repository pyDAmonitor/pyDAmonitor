import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap
import math
import holoviews as hv
import numpy as np


def hslice_contour0(ux_hslice, title, cmin=None, cmax=None, cincr=None, width=800, height=500, cmap="coolwarm", zero_shift=0, clevs_multiplier=1):
    # Get min and max
    amin = ux_hslice.min().item()
    amax = ux_hslice.max().item()
    title += f" min={amin:.1f} max={amax:.1f}"
    if cincr is None:
        # estimate an cincr
        cincr = (amax - amin) /20
        if cincr >=1:
            cincr = math.ceil(cincr)
    if cmin is None:
        cmin = cincr * (amin // cincr)  # closest smaller value
    if cmax is None:
        cmax = cincr * -(-amax // cincr)  # closest larger value

    if isinstance(cmap, str):
        cmap = plt.get_cmap(cmap)

    # testing a colormap which explicitly defines colors per each contour level (overwrite the passed in cmap
    # levels=np.arange(-cmax, cmax + cincr, cincr)
    # cmap = diff_colormap(levels)
    
    if cmin * cmax < 0:  # adjust colormap for the [-A, B] situation so that 0 is at the center of the color bar        
        cmap_adjust = cmap
        half_levels = int(max(cmax, cmin)/cincr + 1) * clevs_multiplier  # 50
        if abs(cmin) < cmax:
            positive = np.linspace(0.5 + zero_shift, 1, half_levels-1)            
            negative = np.linspace( 0, 0.5 - zero_shift, int(abs(cmin)*half_levels/cmax) + 1)  # start from the coolest color
            # negative = np.linspace( (1-abs(cmin)/cmax)* 0.5, 0.5 - zero_shift, int(abs(cmin)*half_levels/cmax) + 1)  # start from the scaled cold 
            combine = np.unique(np.concatenate((negative, positive)))
            cmap_adjust = ListedColormap(cmap(combine))
        else:  # abs(cmin) > cmax
            negative = np.linspace(0, 0.5 - zero_shift, half_levels-1)            
            positive = np.linspace( 0.5 + zero_shift, 1, int(cmax*half_levels/abs(cmin)) + 1)  # end at the warmest color
            # positive = np.linspace(  0.5 + zero_shift, (1-cmax/abs(cmin))*0.5, int(cmax*half_levels/abs(cmin)) + 1)  # start from the scaled cold blue
            combine = np.unique(np.concatenate((negative, positive)))
            cmap_adjust = ListedColormap(cmap(combine))

    # generate contour plot
    contour_plot = hv.operation.contours(
        ux_hslice.plot(),
        levels=np.arange(cmin, cmax + cincr, cincr),  # np.linspace(cmin, cmax, num=clevs),  # levels=np.arange(cmin, cmax, 1)
        filled=True
    ).opts(
        line_color=None,  # line_width=0.001
        width=width, height=height,
        cmap=cmap_adjust,
        clim=(cmin, cmax),        
        colorbar=True,  # cmap="inferno"
        show_legend=False, tools=['hover'], title=title,
    )

    return contour_plot
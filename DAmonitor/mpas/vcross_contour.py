import math
import numpy as np


def vcross_contour(uxvar, lon=None, lat=None, cmin=None, cmax=None, width=600, height=530, clevels=20, steps=100, xtick_stride=5):
    if lon is None and lat is None:
        print("Need to specify either a const lon or a const lat")
        return

    if lon is not None:  # along constant lon
        vcross = uxvar.cross_section(lon=lon, steps=steps)
    elif lat is not None:  # along constant lat
        vcross = uxvar.cross_section(lat=lat, steps=steps)

    # Get arary min/max and color map min/max
    amin = vcross.min().item()
    amax = vcross.max().item()
    cmin = math.floor(amin) if cmin is None else cmin
    cmax = math.ceil(amax) if cmax is None else cmax

    levels = np.linspace(cmin, cmax, num=clevels)
    if lon is not None:  # along constant lon
        title = f"constant_lon={lon} min={amin:.1f} max={amax:.1f}"
        str_lat_lon = "lat"
        xtick_labels = [f"{abs(value):.1f}°{'N' if value >= 0 else 'S'}" for value in vcross[str_lat_lon]]

    elif lat is not None:  # along constant lat
        title = f"constant_lat={lat} min={amin:.1f} max={amax:.1f}"
        str_lat_lon = "lon"
        xtick_labels = [f"{abs(value):.1f}°{'E' if value >= 0 else 'W'}" for value in vcross[str_lat_lon]]

    vcross = vcross.assign_coords({
        "steps": vcross[str_lat_lon].values,
        'nVertLevels': range(vcross['nVertLevels'].shape[0])}
    )

    return vcross.hvplot.contourf(
        x='steps', y='nVertLevels',
        cmap='coolwarm', levels=levels,
        width=width, height=height, title=title,
    ).opts(
        xlabel=str_lat_lon,
        xticks=list(zip(vcross[str_lat_lon].values[::xtick_stride], xtick_labels[::xtick_stride]))
    )

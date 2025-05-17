import math
import numpy as np
import xarray as xr


def vslice_contour(uxvar, lon=None, lat=None, minval=None, maxval=None, width=600, height=530, clevels=20):
    if lon is None and lat is None:
        print("Need to specify either a const lon or a const lat")
        return

    if lon is not None:  # along constant lon
        ux_vslice = uxvar.isel(Time=0).cross_section.constant_longitude(lon)
    elif lat is not None:  # along constant lat
        ux_vslice = uxvar.isel(Time=0).cross_section.constant_latitude(lat)

    # temporary uxarray bug fix and it will be updated in a new UXarray fix soon
    del ux_vslice.uxgrid._ds['edge_node_connectivity']
    del ux_vslice.uxgrid._ds['edge_lon']
    del ux_vslice.uxgrid._ds['face_lon']

    # sort lats or lons
    if lon is not None:  # along constant lon
        sort_indices = ux_vslice.uxgrid.face_lat.argsort()
    elif lat is not None:  # along constant lat
        sort_indices = ux_vslice.uxgrid.face_lon.argsort()
    sorted_lons = ux_vslice.uxgrid.face_lon[sort_indices]
    sorted_lats = ux_vslice.uxgrid.face_lat[sort_indices]

    # remap faces
    face_indices = []
    for mylon, mylat in zip(sorted_lons, sorted_lats):
        face_idx = ux_vslice.uxgrid.get_faces_containing_point(point_lonlat=np.array([mylon.item(), mylat.item()]))
        face_indices.append(face_idx)

    face_indices = np.array(face_indices).squeeze()
    if lon is not None:  # along constant lon
        face_DataArray = xr.DataArray(data=np.array(face_indices), dims=['lat'])
    elif lat is not None:  # along constant lat
        face_DataArray = xr.DataArray(data=np.array(face_indices), dims=['lon'])

    ux_vslice_selected = ux_vslice.isel(n_face=face_DataArray, ignore_grid=True)
    # Get min and max
    if minval is None:
        amin = ux_vslice_selected.min().item()
        minval = math.floor(amin)
    if maxval is None:
        amax = ux_vslice.max().item()
        maxval = math.ceil(amax)

    levels = np.linspace(minval, maxval, num=clevels)
    if lon is not None:  # along constant lon
        title = f"constant_lon={lon} min={amin:.1f} max={amax:.1f}"
    if lat is not None:  # along constant lat
        title = f"constant_lat={lat} min={amin:.1f} max={amax:.1f}"

    # ux_vslice_selected.to_xarray().transpose().plot.contourf()  # plot using matplotlib
    # plt.title(f"lon = {lon}")  # add a title to matplotlib

    # return the slice array with a lat dim
    # ux_vslice_selected = ux_vslice_selected.assign_coords(lats=xr.DataArray(data=sorted_lats, dims=['lat']))
    # return ux_vslice_selected.to_xarray().transpose() # return the slice array

    return ux_vslice_selected.to_xarray().transpose().hvplot.contourf(levels=levels, width=width, height=height, title=title)  # aspect=1

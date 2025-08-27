#import ioda
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as colors
import cartopy.crs as ccrs
import netCDF4 as nc
import numpy.ma as ma
from netCDF4 import Dataset
from collections import Counter


if os.environ.get('LIBDIR') is not None:
    sys.path.append(os.environ['LIBDIR'])
    

# Set input jdiag file name
# --------------------------------
fname = "jdiag_cris-fsr_n20.nc"

print("checking fname = ", fname)

# Read input data file
# ----------------------
ncd = nc.Dataset(fname, 'r') 

# NetCDF global attributes
# --------------------------
nc_attrs = ncd.ncattrs()
print('NetCDF Global Attributes: ')
print('nc_attrs = ', nc_attrs)
for nc_attr in nc_attrs:
   print('nc_attr', ncd.getncattr(nc_attr))

# Dimension shape information 
# -----------------------------
nc_dims = [dim for dim in ncd.dimensions]  # list of nc dimensions
print('nc_dims = ', nc_dims)
for dim in nc_dims:
   print('nc_dims', dim, len(ncd.dimensions[dim]))

##read in data
# ---------------------
latData = ncd.groups['MetaData'].variables['latitude'][:].ravel()
lonData = ncd.groups['MetaData'].variables['longitude'][:].ravel()
dateTime= ncd.groups['MetaData'].variables['dateTime'][:]
radiance = ncd.groups['ObsValue'].variables['radiance'][:]

hofx0 = ncd.groups['hofx0'].variables['brightnessTemperature'][:]
ombg = ncd.groups['ombg'].variables['brightnessTemperature'][:]
ObsBias0 = ncd.groups['ObsBias0'].variables['brightnessTemperature'][:]
ObsBias1 = ncd.groups['ObsBias1'].variables['brightnessTemperature'][:]
ObsBias2 = ncd.groups['ObsBias2'].variables['brightnessTemperature'][:]
ombnbcData = ombg + ObsBias0 

DerivedObsValue = ncd.groups['DerivedObsValue'].variables['brightnessTemperature'][:]
qcflag0 = ncd.groups['EffectiveQC0'].variables['brightnessTemperature'][:]
qcflag1 = ncd.groups['EffectiveQC1'].variables['brightnessTemperature'][:]
qcflag2 = ncd.groups['EffectiveQC2'].variables['brightnessTemperature'][:]
Error0 = ncd.groups['EffectiveError0'].variables['brightnessTemperature'][:]
Error1 = ncd.groups['EffectiveError1'].variables['brightnessTemperature'][:]
Error2 = ncd.groups['EffectiveError2'].variables['brightnessTemperature'][:]
Thinning = ncd.groups['DiagnosticFlags']['Thinning'].variables['brightnessTemperature'][:]
UseflagCheck = ncd.groups['DiagnosticFlags']['UseflagCheck'].variables['brightnessTemperature'][:]
GrossCheck = ncd.groups['DiagnosticFlags']['GrossCheck'].variables['brightnessTemperature'][:]
ScanEdgeRemoval = ncd.groups['DiagnosticFlags']['ScanEdgeRemoval'].variables['brightnessTemperature'][:]
CloudDetectMinResidualIR = ncd.groups['DiagnosticFlags']['CloudDetectMinResidualIR'].variables['brightnessTemperature'][:]
GeoDomainCheck=ncd.groups['DiagnosticFlags']['GeoDomainCheck'].variables['brightnessTemperature'][:]
NearSSTRetCheckIR=ncd.groups['DiagnosticFlags']['NearSSTRetCheckIR'].variables['brightnessTemperature'][:]
SurfaceTempJacobianCheck=ncd.groups['DiagnosticFlags']['SurfaceTempJacobianCheck'].variables['brightnessTemperature'][:]

constantPredictor = ncd.groups['constantPredictor'].variables['brightnessTemperature'][:]
lapseRatePredictor = ncd.groups['lapseRatePredictor'].variables['brightnessTemperature'][:]

channels = ncd.variables['Channel'][:]


# Check data 
# -----------
#print('lat   = ', latData)
#print('lon   = ', lonData)
print('dateTime = ', dateTime)
print('ombg,length=', len(ombg))
print('ombg shape = ', ombg.shape)

print(list(ncd.groups))

conus_12km = [-150, -50, 15, 55]

# Output directory
output_dir = "./CrIS_QC_filters"
os.makedirs(output_dir, exist_ok=True)


for i,ch in enumerate(channels):

    valid =  CloudDetectMinResidualIR[:,i] == 1
    cloud_check= ombg[valid,i]
    lon_cloud = lonData[valid]
    lat_cloud = latData[valid]
    cloud_count = np.ma.count(cloud_check)


    valid2 = GrossCheck[:,i]   == 1
    gross_check= ombg[valid2,i]
    lon_gross = lonData[valid2]
    lat_gross = latData[valid2]
    gross_count = np.ma.count(gross_check)

    valid3 = NearSSTRetCheckIR[:,i]   == 1
    sst_check= ombg[valid3,i]
    lon_sst = lonData[valid3]
    lat_sst = latData[valid3]
    sst_count = np.ma.count(sst_check)

    valid4 = SurfaceTempJacobianCheck[:,i]  == 1
    surface_check= ombg[valid4,i]
    lon_surface= lonData[valid4]
    lat_surface = latData[valid4]
    surface_count = np.ma.count(surface_check)

    valid5 = qcflag0[:,i]  == 0
    assimilated= ombg[valid5,i]
    lon_assimilated = lonData[valid5]
    lat_assimilated = latData[valid5]
    assimilated_count = np.ma.count(assimilated)

    valid6 = UseflagCheck[:,i]  == 1
    use_flag_check= ombg[valid6,i]
    lon_use_flag_check = lonData[valid6]
    lat_use_flag_check = latData[valid6]
    use_flag_count = np.ma.count(use_flag_check)

    # Initialize the plot pointing to the projection
    # ------------------------------------------------
    ax = plt.axes(projection=ccrs.PlateCarree(central_longitude=0))

    # Plot grid lines
    # ----------------
    gl = ax.gridlines(crs=ccrs.PlateCarree(central_longitude=0), draw_labels=True,
                  linewidth=1, color='gray', alpha=0.5, linestyle='-')
    gl.top_labels = False
    gl.xlabel_style = {'size': 10, 'color': 'black'}
    gl.ylabel_style = {'size': 10, 'color': 'black'}
    gl.xlocator = mticker.FixedLocator(
      [-180, -135, -90, -45, 0, 45, 90, 135, 179.9])

     # Get scatter data
     # -----------------------------------
    sc = ax.scatter(lon_cloud, lat_cloud, color='blue', label=f"CloudDetectMinResidualIR  Total Count:{cloud_count}", s=2, linewidth=0, transform=ccrs.PlateCarree(), norm=None, antialiased=True)
    sc = ax.scatter(lon_surface, lat_surface, color='orange',label=f"SurfaceTempJacobianCheck Total Count:{surface_count}", s=2, linewidth=0, transform=ccrs.PlateCarree(), norm=None, antialiased=True)
    sc = ax.scatter(lon_sst, lat_sst, color='yellow',label=f"NearSSTRetCheckIR Total Count:{sst_count}", s=2, linewidth=0, transform=ccrs.PlateCarree(), norm=None, antialiased=True)
    sc = ax.scatter(lon_gross, lat_gross, color='green',label=f"GrossCheck Total Count:{gross_count}" ,s=2, linewidth=0, transform=ccrs.PlateCarree(), norm=None, antialiased=True)
    sc = ax.scatter(lon_use_flag_check,lat_use_flag_check,color='black',label=f"UseflagCheck Total Count:{use_flag_count}",s=2, linewidth=0, transform=ccrs.PlateCarree(), norm=None, antialiased=True)
    sc = ax.scatter(lon_assimilated, lat_assimilated,color='red',label=f"Assimilated Total Count:{assimilated_count}",s=2, linewidth=0, transform=ccrs.PlateCarree(), norm=None, antialiased=True)

    plt.legend(fontsize=6)
    plt.title(f"CrIS-FSR QC filters for Channel {int(ch)}")

    #ax.set_global()
    ax.set_extent(conus_12km)

   # Draw coastlines
   # ----------------
    ax.coastlines()

    save_path = os.path.join(output_dir, f"CrIS_QC_fitlers_for_channel_{int(ch)}.png") 
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {save_path}")

exit()
 


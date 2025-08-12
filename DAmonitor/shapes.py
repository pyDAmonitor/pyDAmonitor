# from holoviews import opts
import os
import geoviews as gv
import geoviews.feature as gf
import cartopy.crs as ccrs
import geopandas as gp

pyDAmonitor_ROOT = os.getenv("pyDAmonitor_ROOT")

# common border lines
coast_lines = gf.coastline(projection=ccrs.PlateCarree(), line_width=1, scale="50m")
state_lines = gf.states(projection=ccrs.PlateCarree(), line_width=1, line_color='gray', scale="50m")
counties_gdf = gp.read_file(f"{pyDAmonitor_ROOT}/data/shapes_county/cb_2018_us_county_500k.shp")  # https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_county_500k.zip
county_lines = gv.Polygons(counties_gdf, crs=ccrs.PlateCarree()).opts(fill_alpha=0, line_color='gray', line_width=0.5)
# county_lines # show the county_lines plot. This step is slow as we will plot many polygons

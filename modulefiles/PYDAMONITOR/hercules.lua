help([[
Load environment for running PYDAMONITOR.
]])

local pkgName    = myModuleName()
local pkgVersion = myModuleVersion()
local pkgNameVer = myModuleFullName()

conflict(pkgName)

prepend_path("MODULEPATH", '/work/noaa/zrtrr/gge/hercules/Miniforge3/modulefiles')

load("Miniforge3/24.11.3-2")
load("pyDAmonitor/1.0.0")

whatis("Name: ".. pkgName)
whatis("Version: ".. pkgVersion)
whatis("Category: PYDAMONITOR")
whatis("Description: Load all libraries needed for PYDAMONITOR")

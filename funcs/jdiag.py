
def load_jdiag(filename):
    from netCDF4 import Dataset
    return Dataset(filename, "r")

def get_jdiag_metadata(dataset, metadata):
    metadata["latitude"] = dataset.groups["MetaData"].variables["latitude"][:]
    metadata["longitude"] = dataset.groups["MetaData"].variables["longitude"][:]
    metadata["pressure"] = dataset.groups["MetaData"].variables["pressure"][:]
    metadata["height"] = dataset.groups["MetaData"].variables["height"][:]
    if "aircraftFlightNumber" in dataset.groups["MetaData"].variables:
        metadata["aircraftFlightNumber"] = dataset.groups["MetaData"].variables["aircraftFlightNumber"][:]
        metadata["aircraftFlightPhase"] = dataset.groups["MetaData"].variables["aircraftFlightPhase"][:]

def get_jdiag_data(dataset, varname, data):
    data["ObsType"] = dataset.groups["ObsType"].variables[varname][:]
    data["ObsValue"] = dataset.groups["ObsValue"].variables[varname][:]
    if varname == "specificHumidity":
        data["ObsValue"] = data["ObsValue"] * 1000
    data["QualityMarker"]  = dataset.groups["QualityMarker"].variables[varname][:]
    data["EffectiveQC0"] = dataset.groups["EffectiveQC0"].variables[varname][:]
    data["hofx0"] = dataset.groups["hofx0"].variables[varname][:]
    if "oman" in dataset.groups:
        data["ombg"] = dataset.groups["ombg"].variables[varname][:]
        data["oman"] = dataset.groups["oman"].variables[varname][:]

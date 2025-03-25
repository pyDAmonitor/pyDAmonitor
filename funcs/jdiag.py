def load_jdiag(filename):
    from netCDF4 import Dataset

    return Dataset(filename, "r")


def get_valid_data(data, key):
    import numpy as np

    data2 = np.array(data[key])
    return data2[data["EffectiveQC2"] == 0]


def get_jdiag_metadata(dataset):
    # this is used for get metadata only
    metadata = {}
    metadata["stationIdentification"] = dataset.groups["MetaData"].variables["stationIdentification"][:]
    metadata["stationElevation"] = dataset.groups["MetaData"].variables["stationElevation"][:]
    metadata["latitude"] = dataset.groups["MetaData"].variables["latitude"][:]
    metadata["latitude"] = dataset.groups["MetaData"].variables["latitude"][:]
    metadata["timeOffset"] = dataset.groups["MetaData"].variables["timeOffset"][:]
    metadata["dateTime"] = dataset.groups["MetaData"].variables["dateTime"][:]
    metadata["pressure"] = dataset.groups["MetaData"].variables["pressure"][:]
    metadata["height"] = dataset.groups["MetaData"].variables["height"][:]
    metadata["prepbufrReportType"] = dataset.groups["MetaData"].variables["prepbufrReportType"][:]
    metadata["prepbufrDataLvlCat"] = dataset.groups["MetaData"].variables["prepbufrDataLvlCat"][:]
    metadata["dumpReportType"] = dataset.groups["MetaData"].variables["dumpReportType"][:]

    if "aircraftFlightNumber" in dataset.groups["MetaData"].variables:
        metadata["aircraftFlightNumber"] = dataset.groups["MetaData"].variables["aircraftFlightNumber"][:]
        metadata["aircraftFlightPhase"] = dataset.groups["MetaData"].variables["aircraftFlightPhase"][:]
    return metadata


def get_jdiag_data(dataset, varname):
    # this will get both metadata and regular data
    data = {}

    # get metadata first
    data["stationIdentification"] = dataset.groups["MetaData"].variables["stationIdentification"][:]
    data["stationElevation"] = dataset.groups["MetaData"].variables["stationElevation"][:]
    data["latitude"] = dataset.groups["MetaData"].variables["latitude"][:]
    data["latitude"] = dataset.groups["MetaData"].variables["latitude"][:]
    data["timeOffset"] = dataset.groups["MetaData"].variables["timeOffset"][:]
    data["dateTime"] = dataset.groups["MetaData"].variables["dateTime"][:]
    data["pressure"] = dataset.groups["MetaData"].variables["pressure"][:]
    data["height"] = dataset.groups["MetaData"].variables["height"][:]
    data["prepbufrReportType"] = dataset.groups["MetaData"].variables["prepbufrReportType"][:]
    data["prepbufrDataLvlCat"] = dataset.groups["MetaData"].variables["prepbufrDataLvlCat"][:]
    data["dumpReportType"] = dataset.groups["MetaData"].variables["dumpReportType"][:]
    if "aircraftFlightNumber" in dataset.groups["MetaData"].variables:
        data["aircraftFlightNumber"] = dataset.groups["MetaData"].variables["aircraftFlightNumber"][:]
        data["aircraftFlightPhase"] = dataset.groups["MetaData"].variables["aircraftFlightPhase"][:]

    # get regular data
    data["ObsType"] = dataset.groups["ObsType"].variables[varname][:]
    data["ObsValue"] = dataset.groups["ObsValue"].variables[varname][:]
    if varname == "specificHumidity":
        data["ObsValue"] = data["ObsValue"] * 1000
    data["ObsError"] = dataset.groups["ObsError"].variables[varname][:]
    data["QualityMarker"] = dataset.groups["QualityMarker"].variables[varname][:]
    data["EffectiveQC0"] = dataset.groups["EffectiveQC0"].variables[varname][:]
    data["EffectiveQC1"] = dataset.groups["EffectiveQC1"].variables[varname][:]
    data["EffectiveQC2"] = dataset.groups["EffectiveQC2"].variables[varname][:]
    data["hofx0"] = dataset.groups["hofx0"].variables[varname][:]
    data["hofx1"] = dataset.groups["hofx1"].variables[varname][:]
    data["hofx2"] = dataset.groups["hofx2"].variables[varname][:]
    data["ObsError"] = dataset.groups["ObsError"].variables[varname][:]
    if "oman" in dataset.groups:
        data["ombg"] = dataset.groups["ombg"].variables[varname][:]
        data["oman"] = dataset.groups["oman"].variables[varname][:]
    return data

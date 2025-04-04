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
    for var in dataset.groups['MetaData'].variables:
        metadata[var] = dataset.groups['MetaData'].variables[var][:]
    return metadata


def get_jdiag_data(dataset, varname, get_metadata = True):
    # This will get both metadata and regular data
    data = {}
    for grp in dataset.groups:
        if dataset.groups[grp].groups:
            for nestgrp in dataset.groups[grp].groups: # DiagnosticFlags
                data[nestgrp] = dataset.groups[grp].groups[nestgrp].variables[varname][:]
        else:
            if grp == "MetaData":
                if get_metadata:
                    for var in dataset.groups['MetaData'].variables:
                        data[var] = dataset.groups['MetaData'].variables[var][:]
            elif grp == "ObsError" and varname == "specificHumidity":
                data["ObsError"] = dataset.groups["ObsError"].variables["relativeHumidity"][:]
            elif varname == "brightnessTemperature" and ( grp == "ObsValue" or grp == "ObsValueAdj"):
                data[grp] = dataset.groups[grp].variables["radiance"][:]
            else:
                data[grp] = dataset.groups[grp].variables[varname][:]
    return data

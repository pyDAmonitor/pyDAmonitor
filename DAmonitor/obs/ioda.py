from netCDF4 import Dataset
import numpy as np


class _ObsDF:  # DataFrame-like obs structure
    def __init__(self, data):
        self.data = data

    def __getitem__(self, key):
        return self.data[key]

    def __getattr__(self, name):
        try:
            return self.__getitem__(name)
        except KeyError as e:
            raise AttributeError(f"No variable '{name}_{self.varname}' found.") from e


class ioda:
    def __init__(self, filepath):
        """
        Initialize an IODA object and load the NetCDF file.

        Parameters:
        - filepath (str): Path to the NetCDF file.
        """
        self.filepath = filepath
        self.dataset = Dataset(filepath, mode='r')

        # Read the dimension
        self.nlocs = len(self.dataset.dimensions['Location'])

        # Read the Location variable
        self.locations = self.dataset.variables['Location'][:]

        # Discover group names
        self.groups = list(self.dataset.groups.keys())

        #
        self._get_metadata()

        # Remove groups, provide direct access to varaibles, such as ioda.t, ioda.q, ioda.u, ioda.v, etc
        for var in ["airTemperature", "windEastward", "windNorthward", "specificHumidity"]:
            self._get_data_by_varname(var)

    def get_valid_subset(data, item, condition={"EffectiveQC2": 0}):
        data2 = np.array(data[item])
        key, value = next(iter(condition.items()))
        return data2[data[key] == value]

    def _get_metadata(self):
        # this is used for get metadata only
        dataset = self.dataset
        metadata = {}
        for var in dataset.groups['MetaData'].variables:
            metadata[var] = dataset.groups['MetaData'].variables[var][:]
        self.metadata = metadata

    def _get_data_by_varname(self, varname):
        dataset = self.dataset
        # This will get both metadata and regular data
        data = {}
        only_has_metadata = True
        for grp in dataset.groups:
            if dataset.groups[grp].groups:
                for nestgrp in dataset.groups[grp].groups:  # DiagnosticFlags
                    data[nestgrp] = dataset.groups[grp].groups[nestgrp].variables[varname][:]
                    only_has_metadata = False
            else:
                if grp == "MetaData":
                    for var in dataset.groups['MetaData'].variables:
                        if var != "longitude_latitude_pressure":
                            data[var] = dataset.groups['MetaData'].variables[var][:]
                elif grp == "ObsError" and varname == "specificHumidity":
                    data["ObsError"] = dataset.groups["ObsError"].variables["relativeHumidity"][:]
                    only_has_metadata = False
                elif varname == "brightnessTemperature" and (grp == "ObsValue" or grp == "ObsValueAdj"):
                    data[grp] = dataset.groups[grp].variables["radiance"][:]
                    only_has_metadata = False
                elif varname in dataset.groups[grp].variables:
                    data[grp] = dataset.groups[grp].variables[varname][:]
                    only_has_metadata = False

        # assign the data dict
        if only_has_metadata:
            data = {}
        if varname == "airTemperature":
            self.t = _ObsDF(data)
        elif varname == "windEastward":
            self.u = _ObsDF(data)
        elif varname == "windNorthward":
            self.v = _ObsDF(data)
        elif varname == "specificHumidity":
            self.q = _ObsDF(data)

    def __getitem__(self, key):
        # Enable ioda["t"]
        if key in ["t", "airTemperature"]:
            return self.t
        elif key in ["u", "windEastward"]:
            return self.u
        elif key in ["v", "windNorthward"]:
            return self.u
        elif key in ["q", "specificHumidity"]:
            return self.q
        raise KeyError(f"Key '{key}' not found.")

    def __getattr__(self, name):
        # Enable myioda.t (only called if attribute not found normally)
        try:
            return self.__getitem__(name)
        except KeyError:
            raise AttributeError(f"'ioda' object has no attribute or variable '{name}'")

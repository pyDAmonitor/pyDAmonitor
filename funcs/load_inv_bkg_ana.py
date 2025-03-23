#!/usr/bin/env python
from netCDF4 import Dataset
def load_inv_bkg_ana(files):
    datasets ={}
    datasets['inv'] = Dataset(files['inv'], "r")
    datasets['bkg'] = Dataset(files['bkg'], 'r')
    datasets['ana'] = Dataset(files['ana'], 'r')
    return datasets

import os
import sys
from netCDF4 import Dataset
import pandas as pd


def get_run_directory():
    """Get the run directory, handling both scripts and Jupyter Notebooks."""
    if "ipykernel" in sys.modules:  # Running in a Jupyter Notebook
        return os.getcwd()
    else:  # Running as a script
        return os.path.dirname(os.path.abspath(__file__))


def get_inv_bkg_ana_files(expdir, cdate):
    source(f"{expdir}/exp.setup")
    NET = os.getenv("NET")
    RUN = NET
    WGF = os.getenv("WGF")
    TAG = os.getenv("TAG")
    COMROOT = os.getenv("COMROOT")
    DATAROOT = os.getenv("DATAROOT")
    with open(f"{expdir}/VERSION", "r") as file:
        VERSION = file.readline().strip()
    # print(NET, RUN, WGF, TAG, VERSION, COMROOT, DATAROOT)

    # find the correct invariant.nc
    jedivar_log = (
        f"{COMROOT}/{NET}/{VERSION}/logs/{RUN}.{cdate[:8]}/{cdate[8:10]}/{WGF}/{RUN}_jedivar_{TAG}_{cdate}.log"
    )
    end_str = "./invariant.nc"
    with open(f"{jedivar_log}", "r") as file:
        for line in file:
            line = line.strip()
            if line.endswith(end_str):
                inv_file = line[:-len(end_str)].split(":", 1)[1].strip()[len("ln -snf"):].strip()
                break
    # print(inv_file)

    # find the background file from the prep_ic log file
    prep_ic_log = (
        f"{COMROOT}/{NET}/{VERSION}/logs/{RUN}.{cdate[:8]}/{cdate[8:10]}/{WGF}/{RUN}_prep_ic_{TAG}_{cdate}.log"
    )
    start_str = "warm start from"
    with open(f"{prep_ic_log}", "r") as file:
        for line in file:
            if line.startswith(start_str):
                bkg_file = line[len(start_str):].strip()
                break
    # print(bkg_file)

    # find the analysis file from the UMBRELLA_PREP_IC
    ana_file = f"{DATAROOT}/{cdate[:8]}/{RUN}_prep_ic_{cdate[8:10]}_{VERSION}/{WGF}/mpasin.nc"
    # print(ana_file)

    files = {
        "inv": inv_file,
        "bkg": bkg_file,
        "ana": ana_file,
    }
    return files


def load_inv_bkg_ana(files):
    datasets = {}
    datasets["inv"] = Dataset(files["inv"], "r")
    datasets["bkg"] = Dataset(files["bkg"], "r")
    datasets["ana"] = Dataset(files["ana"], "r")
    return datasets


def query_dataset(dataset):
    if dataset.groups:
        for grp in dataset.groups:
            print(grp)
            text = "    "
            if dataset.groups[grp].groups:
                for nestgrp in dataset.groups[grp].groups:
                    print(text + nestgrp)
                    text2 = "    "
                    for var in dataset.groups[grp].groups[nestgrp].variables:
                        text2 += f"{var}, "
                    print(text + text2.rstrip(","))
            else:
                for var in dataset.groups[grp].variables:
                    text += f"{var}, "
                print(text.rstrip(","))
    else:
        text = ""
        for var in dataset.variables:
            text += f"{var}, "
        print(text.rstrip(","))


def query_data(data):
    text = ""
    if data.data:  # 
        data = data.data
    for var in data:
        text += f"{var}, "
    print(text.rstrip(","))


def to_dataframe(obsDF):
    obsDF = obsDF
    if obsDF.data:
        obsDF = obsDF.data
    data = {}
    for key, value in obsDF.items():
        data[key] = value
    return pd.DataFrame(data)


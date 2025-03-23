from base import source
import os
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
    #print(NET, RUN, WGF, TAG, VERSION, COMROOT, DATAROOT)

    # find the correct invariant.nc
    jedivar_log = f"{COMROOT}/{NET}/{VERSION}/logs/{RUN}.{cdate[:8]}/{cdate[8:10]}/{WGF}/{RUN}_jedivar_{TAG}_{cdate}.log"
    end_str="./invariant.nc"
    with open(f"{jedivar_log}", "r") as file:
        for line in file:
            line = line.strip()
            if line.endswith(end_str):
                inv_file = line[:-len(end_str)].split(":",1)[1].strip()[len("ln -snf"):].strip()
                break
    #print(inv_file)

    # find the background file from the prep_ic log file
    prep_ic_log = f"{COMROOT}/{NET}/{VERSION}/logs/{RUN}.{cdate[:8]}/{cdate[8:10]}/{WGF}/{RUN}_prep_ic_{TAG}_{cdate}.log"
    start_str = "warm start from"
    with open(f"{prep_ic_log}", "r") as file:
        for line in file:
            if line.startswith(start_str):
                bkg_file = line[len(start_str):].strip()
                break
    #print(bkg_file)

    # find the analysis file from the UMBRELLA_PREP_IC
    ana_file = f"{DATAROOT}/{cdate[:8]}/{RUN}_prep_ic_{cdate[8:10]}_{VERSION}/{WGF}/mpasin.nc"
    # print(ana_file)

    files ={
        "inv": inv_file,
        "bkg": bkg_file,
        "ana": ana_file,
    }
    return files

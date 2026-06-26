#!/usr/bin/env python
# make histograms of OmBs and OmAs for conventional obs using jdiag files
#
import sys
import glob
import argparse
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from DAmonitor.base import query_dataset, query_data, query_obj, to_dataframe
from DAmonitor.obs import obsSpace, fit_rate


def parse_in_args(argv):
    """
    Parse input arguments

    Parameters
    ----------
    argv : list
        Command-line arguments from sys.argv[1:]

    Returns
    -------
    Parsed input arguments

    """

    parser = argparse.ArgumentParser(description='Script that plots OmF \
                                                  histograms for conventional \
                                                  observations using jdiag \
                                                  files.')

    # Optional arguments
    parser.add_argument('--path',
                        dest='path',
                        default='.',
                        help='Path containing jdiag files',
                        type=str)

    parser.add_argument('--jdiag_file',
                        dest='jdiag_file',
                        default='ALL',
                        help='Single jdiag file to plot. Default is to plot \
                             all files',
                        type=str)

    return vars(parser.parse_args(argv))


def determine_jdiag_dict(path, file='ALL'):
    """
    Create a dictionary of jdiag files to plot
    """

    # Patterns to match
    var_patterns = ['t', 'q', 'uv', 'ps', 'pw']
    num_patterns = list(range(100, 300))

    # Grab all jdiag files unless files != 'ALL'
    if files == 'ALL':
        all_jdiag = glob.glob(f"{path}/jdiag_*.nc")
    else:
        all_jdiag = [file]

    # Initialize output dictionary
    # First key corresponds to the variable
    # Second key corresponds to the obs type (3-digit prepBUFR number)
    jdiag_out = {v:{} for v in var_patterns}

    for f in all_jdiag:
        sub = f.strip().split('_')[-1][:-3]
        if len(sub) > 3:
            v = sub[:-3]
            typ = int(sub[-3:])
            if (v in var_patterns) and (typ in num_patterns):
                jdiag_out[v][typ] = f

    return jdiag_out


def create_omf_plots(file, plot_var, typ):
    """
    Create OmF histograms for a single file
    """

    diag = obsSpace(file)

    # These are the attributes used to extract variables
    if plot_var == 'uv':
        attrs = ['u', 'v'] 
    else:
        attrs = [plot_var]

    # Dictionary to append statistics to
    keys = ['var', 'type', 'omb_mean', 'omb_std', 'oma_mean', 'oma_std']
    stat_dict = {k:[] for k in keys}

    # Create histogram for each attribute
    for a in attrs:
        omb = getattr(getattr(file, a), 'ombg')
        oma = getattr(getattr(file, a), 'oman')
        omb_avg = np.mean(omb)
        oma_avg = np.mean(oma)
        omb_std = np.std(omb)
        oma_std = np.std(oma)

        # Save statistics to dictionary
        stat_dict['var'].append(a)
        stat_dict['type'].append(typ)
        stat_dict['omb_mean'].append(omb_avg)
        stat_dict['omb_std'].append(omb_std)
        stat_dict['oma_mean'].append(oma_avg)
        stat_dict['oma_std'].append(oma_std)

        # Determine bins for plotting
        max_std = max(omb_std, oma_std)
        min_avg = min(omb_avg, oma_avg)
        max_avg = max(omb_avg, oma_avg)
        min_val = min(np.amin(omb), np.amin(oma))
        max_val = max(np.amax(omb), np.amax(oma))
        bins = np.arange(max(min_val, min_avg - 3*max_std),
                         min(max_val, max_avg + 3*max_std),
                         50)

        # Make plot
        fig, ax = plt.subplots(nrows=1, ncols=1)
        ax.hist(omb, bins=bins, color='b', 
                label=f"O-B (avg = {omb_avg:.3e}, std = {omb_std:.3e}")
        ax.hist(oma, bins=bins, color='r', 
                label=f"O-A (avg = {oma_avg:.3e}, std = {oma_std:.3e}")

        fsize = 12
        ax.legend(fontsize=fsize)
        ax.set_xlabel('values', size=fsize)
        ax.set_ylabel('count', size=fsize)
        ax.set_title(f"{a} {typ}", size=(fsize+2))
        ax.grid()

        out_name = f"{a}{typ}_omf_hist.png"
        print(f"Saving plot to {out_name}")
        plt.savefig(out_name)

    return pd.DataFrame.from_dict(stat_dict)


def omf_hist_driver(all_files):
    """
    Driver that loops over all jdiag files and creates histograms
    """

    df_ls = []

    for v in all_files:
        for typ in all_files[v]:
            df_ls.append(create_omf_plots(all_files[v][typ], v, typ))

    return pd.concat(df_ls)

#
# ***********************************************************************
# !!  MAIN starts here !!
# ***********************************************************************

if __name__ == '__main__':

    # Read in user inputs
    param = parse_in_args(sys.argv[1:])

    # Determine list of jdiag files to operate on
    jdiags = determine_jdiag_list(param['path'], file=param['jdiag_file'])

    # Create OmF plots
    stats = omf_hist_driver(jdiags)

    # Save statistics to CSV file
    stats.to_csv('jedi_conv_omf_stats.csv')

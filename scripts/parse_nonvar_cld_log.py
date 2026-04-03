#!/usr/bin/env python
# parse nonvar cloud analysis stats from the log file
#
import sys
import argparse


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

    parser = argparse.ArgumentParser(description='Script that plots parses \
                                                  output from nonvar cloud \
                                                  analysis log files.')

    # Optional arguments
    parser.add_argument('--larccld',
                        dest='larccld_log',
                        default='nonvar_larccld.log',
                        help='Log file from larccld.fd',
                        type=str)

    parser.add_argument('--metarcld',
                        dest='metarcld_log',
                        default='nonvar_metarcld.log',
                        help='Log file from metarcld.fd',
                        type=str)

    parser.add_argument('--lightning',
                        dest='lightning_log',
                        default='nonvar_lightning.log',
                        help='Log file from lightning.fd',
                        type=str)

    parser.add_argument('--refmosaic',
                        dest='refmosaic_log',
                        default='nonvar_refmosaic.log',
                        help='Log file from refmosaic_nonvar.fd',
                        type=str)

    parser.add_argument('--cloudanalysis',
                        dest='cloudanalysis_log',
                        default='stdout_cloudanalysis',
                        help='Log file from cloudanalysis.fd',
                        type=str)

    return vars(parser.parse_args(argv))


def parse_larccld(fname):
    """
    Parse log file for larccld.fd

    Parameters
    ----------
    fname : string
        Log file name

    Returns
    -------
    Dictionary with information from log file

    """

    out = {'program': 2*['larccld.fd'],
           'observation': ['GOES_EAST', 'GOES_WEST'],
           'number': 2*[0],
           'status': 2*['read']}

    with open(fname, 'r') as fptr:
        for line in fptr:
            if 'east_time and number=' in line:
                out['number'][0] = int(line.split()[-1])
            elif 'west_time and number=' in line:
                out['number'][1] = int(line.split()[-1])

    return out


def parse_metarcld(fname):
    """
    Parse log file for metarcld.fd

    Parameters
    ----------
    fname : string
        Log file name

    Returns
    -------
    Dictionary with information from log file

    """

    out = {'program': 2*['metarcld.fd'],
           'observation': ['raw_METAR', 'METAR_on_MPAS_mesh'],
           'number': 2*[0],
           'status': ['read', 'processed']}

    with open(fname, 'r') as fptr:
        for line in fptr:
            if 'number of valid cloud obs =' in line:
                out['number'][0] = int(line.split()[-1])
            elif 'number of cloud on MPAS mesh=' in line:
                out['number'][1] = int(line.split()[-1])

    return out


def parse_lightning(fname):
    """
    Parse log file for lightning.fd

    Parameters
    ----------
    fname : string
        Log file name

    Returns
    -------
    Dictionary with information from log file

    """

    out = {'program': 2*['lightning.fd'],
           'observation': ['raw_lightning', 'lightning_on_MPAS_mesh'],
           'number': 2*[0],
           'status': ['read', 'processed']}

    with open(fname, 'r') as fptr:
        for line in fptr:
            if 'The total number of lightning obs is:' in line:
                out['number'][0] = int(line.split()[-1])
            elif 'Write out results for MPAS:' in line:
                out['number'][1] = int(line.split()[-1])

    return out


def parse_refmosaic(fname):
    """
    Parse log file for refmosaic_nonvar.fd

    Parameters
    ----------
    fname : string
        Log file name

    Returns
    -------
    Dictionary with information from log file

    """

    out = {'program': 3*['refmosaic_nonvar.fd'],
           'observation': ['n_levels', 'max_val', 'min_val'],
           'number': 3*[0],
           'status': 3*['read']}

    with open(fname, 'r') as fptr:
        for line in fptr:
            if 'level max min height' in line:
                out['number'][0] = out['number'][0] + 1
                out['number'][1] = max(out['number'][1], float(line.split()[-3]))
                out['number'][2] = min(out['number'][2], float(line.split()[-2]))

    return out


def parse_cloudanalysis(fname):
    """
    Parse log file for cloudanalysis.fd

    Parameters
    ----------
    fname : string
        Log file name

    Returns
    -------
    Dictionary with information from log file

    """

    out = {'program': 4*['cloudanalysis.fd'],
           'observation': ['nasa_larc', 'METAR', 'lightning', 'refl'],
           'number': 4*[0],
           'status': 4*['not_used']}

    with open(fname, 'r') as fptr:
        tmpl = 'gsdcloudanalysis: {obs} read in successfully'
        contents = fptr.readlines()
        for i, line in enumerate(contents):
            if 'metar cloud=mta_cldmetarcld' in line:
                out['number'][1] = int(contents[i+1].split()[1])
            elif 'read in lightning from=' in line:
                out['number'][2] = int(contents[i+1].split()[3])
            elif 'ref_mosaic' in line:
                out['number'][3] = out['number'][3] + 1
            elif 'read NASA LaRC obs=' in line:
                out['number'][0] = int(line.split()[-3])
            for j, obs in enumerate(['NASA LaRC cloud products are',
                                     'Surface cloud observations are',
                                     'Lightning is',
                                     'radar reflectivity is']):
                if tmpl.format(obs=obs) in line:
                    out['status'][j] = 'ingested'

    return out


def run_nonvar_parse_all(fnames):
    """
    Parse all nonvar cloud analysis log files

    Parameters
    ----------
    fnames : dictionary
        Nonvar cloud analysis log files

    Returns
    -------
    Dictionary with all output from nonvar cloud analysis log files

    """

    fcts = {'larccld_log': parse_larccld,
            'metarcld_log': parse_metarcld,
            'lightning_log': parse_lightning,
            'refmosaic_log': parse_refmosaic,
            'cloudanalysis_log': parse_cloudanalysis}

    out_all = {'program': [],
               'observation': [],
               'number': [],
               'status': []}

    for key in fcts:
        if key in fnames:
            try:
                out = fcts[key](fnames[key])
                for field in out_all:
                    out_all[field] = out_all[field] + out[field]
            except FileNotFoundError:
                print(f"WARNING: File not found. Skipping {key}. File: {fnames[key]}")

    return out_all


def write_results(out_all, fname):
    """
    Write results from parsing nonvar cloud analysis logs to a new file

    Parameters
    ----------
    out_all : dictionary
        Output from nonvar cloud analysis log files
    fname : string
        Output text file

    Returns
    -------
    None

    """

    with open(fname, 'w') as fptr:
        tmpl = '{s1:>22}{s2:>25}{s3:>15}{s4:>15}\n'
        fptr.write(tmpl.format(s1='program',
                               s2='observation',
                               s3='number',
                               s4='status'))
        for i in range(len(out_all['program'])):
            fptr.write(tmpl.format(s1=out_all['program'][i],
                                   s2=out_all['observation'][i],
                                   s3=out_all['number'][i],
                                   s4=out_all['status'][i]))


#
# ***********************************************************************
# !!  MAIN starts here !!
# ***********************************************************************

if __name__ == '__main__':

    # Read in user inputs
    param = parse_in_args(sys.argv[1:])

    # Run parser for each log file
    out_all = run_nonvar_parse_all(param)

    # Write out results
    write_results(out_all, 'nonvar_cloud_out.txt')

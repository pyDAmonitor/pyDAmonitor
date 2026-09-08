#!/usr/bin/env python
# compute the summary in the past 7 days, 30 days
#
import sys
import os
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np

from obs_count_timeseries import plot_tseries

# list of observers to plot, add new ones accordingly
observers = [
    # adpsfc ----
    'adpsfc_t181', 'adpsfc_t183', 'adpsfc_t187', 'adpsfc_q181', 'adpsfc_q183', 'adpsfc_q187',
    'adpsfc_ps181', 'adpsfc_ps187', 'adpsfc_u281', 'adpsfc_v281', 'adpsfc_u284', 'adpsfc_v284', 'adpsfc_u287', 'adpsfc_v287',
    # adpupa ----
    'adpupa_t120', 'adpupa_q120', 'adpupa_ps120', 'adpupa_u220', 'adpupa_v220',
    # aircar ----
    'aircar_t133', 'aircar_q133', 'aircar_u233', 'aircar_v233',
    # sfcshp ----
    'sfcshp_t180', 'sfcshp_t183', 'sfcshp_q180', 'sfcshp_q183',
    'sfcshp_ps180', 'sfcshp_u280', 'sfcshp_v280', 'sfcshp_u282', 'sfcshp_v282', 'sfcshp_u284', 'sfcshp_v284',
]
plot_vars = ['omb_mean', 'omb_std', 'oma_mean', 'oma_std']


def read_omf_stats(CDATE, lookback_hours):
    """
    Read JEDI OMF statistics from jedi_conv_omf_stats.csv files.

    Parameters
    ----------
    CDATE : string
        Current cycle in YYYYMMDDHH format
    lookback_hours : integer
        Number of hours to look back for the time series

    Returns
    -------
    dateBgn : datetime
        Start of the time series
    tseries  : dict
        Nested dictionary with obs counts for each group and subtype
    """
    #
    dateEnd = datetime.strptime(CDATE, "%Y%m%d%H").replace(tzinfo=timezone.utc)
    dateBgn = dateEnd - timedelta(hours=lookback_hours)
    #
    # These environment variables should already be defined in the shell
    MY_COM_BASE = os.getenv('MY_COM_BASE', 'MY_COM_BASE_not_defined')
    WGF = os.getenv('WGF', 'WGF_not_defined')
    RUN = os.getenv('RUN', 'RUN_not_defined')
    # set default values to np.nan for each cycle
    tseries = {
        obs: {key: [np.nan] * (lookback_hours + 1) for key in plot_vars} for obs in observers
    }
    #
    # Loop over each cycle
    for i in range(lookback_hours+1):
        dateCur = dateBgn + timedelta(hours=i)
        PDY = datetime.strftime(dateCur, "%Y%m%d")
        cyc = datetime.strftime(dateCur, "%H")
        mypath = f'{MY_COM_BASE}/{RUN}.{PDY}/{cyc}/pyDAmonitor/{WGF}/jedi_conv_omf_stats.csv'
        if not os.path.exists(mypath):
            mypath = f'{MY_COM_BASE}/{RUN}.{PDY}/{cyc}/pyDAmonitor/{WGF}/web/jedi_conv_omf_stats.csv'
        if os.path.exists(mypath):
            # read contents using pandas
            csv_out = pd.read_csv(mypath)
            # extract fields from CSV
            for obs in tseries:
                var = obs.split('_')[-1][:-3]
                typ = int(obs.split('_')[-1][-3:])
                row = csv_out.loc[(csv_out['var'] == var) & (csv_out['type'] == typ)]
                if len(row) == 1:
                    for v in plot_vars:
                        tseries[obs][v][i] = row[v].values[0]
    # ~~~~~~~~~~~~~~~~~~
    return dateBgn, tseries


#
# ***********************************************************************
# !!  MAIN starts here !!
# ***********************************************************************
if __name__ == '__main__':
    #
    args = sys.argv
    nargs = len(args) - 1
    if nargs < 2 or len(sys.argv[1]) < 10:
        print(f'Usage: {os.path.basename(sys.argv[0])} <YYYYMMDDHH> <days>')
        sys.exit(1)
    # ~~~~~~
    CDATE = sys.argv[1]
    MAX_DAYS = sys.argv[2]
    lookback_hours = int(MAX_DAYS) * 24  # days * 24 hours
    #
    # JEDI obs
    dateBgn, tseries = read_omf_stats(CDATE, lookback_hours)
    daterange = datetime.strftime(dateBgn, "%Y%m%dT%H") + f'-{CDATE[0:8]}T{CDATE[8:]}'
    #
    plot_tseries(tseries, group='adpsfc_t', start_time=dateBgn, daterange=daterange, source='omf', output_file='omf_stats_tseries_adpsfc_t.png')
    plot_tseries(tseries, group='adpsfc_q', start_time=dateBgn, daterange=daterange, source='omf', output_file='omf_stats_tseries_adpsfc_q.png')
    plot_tseries(tseries, group='adpsfc_u', start_time=dateBgn, daterange=daterange, source='omf', output_file='omf_stats_tseries_adpsfc_u.png')
    plot_tseries(tseries, group='adpsfc_v', start_time=dateBgn, daterange=daterange, source='omf', output_file='omf_stats_tseries_adpsfc_v.png')
    plot_tseries(tseries, group='adpsfc_ps', start_time=dateBgn, daterange=daterange, source='omf', output_file='omf_stats_tseries_adpsfc_ps.png')
    #
    plot_tseries(tseries, group='sfcshp_t', start_time=dateBgn, daterange=daterange, source='omf', output_file='omf_stats_tseries_sfcshp_t.png')
    plot_tseries(tseries, group='sfcshp_q', start_time=dateBgn, daterange=daterange, source='omf', output_file='omf_stats_tseries_sfcshp_q.png')
    plot_tseries(tseries, group='sfcshp_u', start_time=dateBgn, daterange=daterange, source='omf', output_file='omf_stats_tseries_sfcshp_u.png')
    plot_tseries(tseries, group='sfcshp_v', start_time=dateBgn, daterange=daterange, source='omf', output_file='omf_stats_tseries_sfcshp_v.png')
    plot_tseries(tseries, group='sfcshp_ps', start_time=dateBgn, daterange=daterange, source='omf', output_file='omf_stats_tseries_sfcshp_ps.png')
    #
    plot_tseries(tseries, group='adpupa', start_time=dateBgn, daterange=daterange, source='omf', output_file='omf_stats_tseries_adpupa.png')
    plot_tseries(tseries, group='aircar', start_time=dateBgn, daterange=daterange, source='omf', output_file='omf_stats_tseries_aircar.png')

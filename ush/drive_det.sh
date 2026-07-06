#!/usr/bin/env bash
declare -rx PS4='+${SECONDS}s $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]${id}: '
set -x
#
#------------------------------------------------------------------------------------------------
# Note for offline debug: export JEDI_DIR, PYDAMONITOR, CDATE, etc
# and then run this script
#------------------------------------------------------------------------------------------------

ln -snf ${JEDI_DIR}/* .
#
# parse the jedi log file to get minimization.txt and obs_counts.txt
ln -snf ${PYDAMONITOR}/scripts/parse_jedi_log.py .
./parse_jedi_log.py
# parse the radar log file to get these for radar minimization too
if [ -s "log.pass2.out" ]; then
  ln -snf ${PYDAMONITOR}/scripts/parse_radar_log.py .
  ./parse_radar_log.py
fi
#
# parse the nonvar cloud analysis log files to get nonvar_cloud_out.txt
if [[ "${DO_NONVAR_CLOUD_ANA:-FALSE}" == "TRUE" ]]; then
  ln -snf ${NONVAR_BUFR_LOG} nonvar_larccld.log
  ln -snf ${NONVAR_BUFR_LOG} nonvar_metarcld.log
  ln -snf ${NONVAR_BUFR_LOG} nonvar_lightning.log
  ln -snf ${NONVAR_REFL_LOG} nonvar_refmosaic.log
  ln -snf ${NONVAR_CLD_DIR}/stdout_cloudanalysis.d0000 stdout_cloudanalysis
  ln -snf ${PYDAMONITOR}/scripts/parse_nonvar_cld_log.py .
  ./parse_nonvar_cld_log.py
fi
#
# plot the cost/grad descent lines
ln -snf ${PYDAMONITOR}/scripts/costgrad_descent.py .
./costgrad_descent.py
#
# plot the time series of obs counts
ln -snf ${PYDAMONITOR}/scripts/obs_count_timeseries.py .
./obs_count_timeseries.py ${CDATE} 10  # plot 10 days of obs counts
#
# prep files for web
ln -snf ${PYDAMONITOR}/ush/prep_web_det.sh .
./prep_web_det.sh
#

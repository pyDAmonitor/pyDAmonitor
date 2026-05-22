#!/usr/bin/env bash
# connect pyDAmonitor to the workflow
declare -rx PS4='+ $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]: '
set -x
date
#
#-----------------------------------------------------------------------
# Specify Execution Areas
#-----------------------------------------------------------------------
#
export HOMErrfs=${HOMErrfs} #comes from the workflow at runtime
export EXECrrfs=${EXECrrfs:-${HOMErrfs}/exec}
export FIXrrfs=${FIXrrfs:-${HOMErrfs}/fix}
export PARMrrfs=${PARMrrfs:-${HOMErrfs}/parm}
export USHrrfs=${USHrrfs:-${HOMErrfs}/ush}
export PYDAMONITOR=${HOMErrfs}/workflow/sideload/pyDAmonitor
#
#-----------------------------------------------------------------------
# Obtain unique process id (pid) and create the run directory (DATA).
#-----------------------------------------------------------------------
#
export MY_COM_BASE=${COMROOT}/${NET}/${VERSION}
export LOG_DIR=${MY_COM_BASE}/logs/${RUN}.${PDY}/${cyc}/${WGF}
if [[ "${DO_SPINUP:-FALSE}" == "TRUE" ]];  then
  export WORKDIR=${COMOUT}/pyDAmonitor_spinup/${WGF}
  export JEDI_DIR=${COMOUT}/jedivar_spinup/${WGF}
  export NONVAR_CLD_DIR=${COMOUT}/nonvar_cldana_spinup/${WGF}
  export NONVAR_BUFR_LOG=${LOG_DIR}/rrfs_nonvar_bufrobs_spinup_${TAG}_${CDATE}.log
  export NONVAR_REFL_LOG=${LOG_DIR}/rrfs_nonvar_reflobs_spinup_${TAG}_${CDATE}.log
else
  export WORKDIR=${COMOUT}/pyDAmonitor/${WGF}
  export JEDI_DIR=${COMOUT}/jedivar/${WGF}
  export NONVAR_CLD_DIR=${COMOUT}/nonvar_cldana/${WGF}
  export NONVAR_BUFR_LOG=${LOG_DIR}/rrfs_nonvar_bufrobs_${TAG}_${CDATE}.log
  export NONVAR_REFL_LOG=${LOG_DIR}/rrfs_nonvar_reflobs_${TAG}_${CDATE}.log
fi
mkdir -p "${WORKDIR}"
cd "${WORKDIR}"
ln -snf ${JEDI_DIR}/* .
#
# parse the jedi log file to get minimization.txt and obs_counts.txt
ln -snf ${PYDAMONITOR}/scripts/parse_jedi_log.py .
./parse_jedi_log.py
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
WGF=''
ln -snf ${PYDAMONITOR}/scripts/timeseries_obs_count.py .
./timeseries_obs_count.py ${CDATE} 10  # plot 10 days of obs counts
#
#
date
echo "pyDAmonitor HAS COMPLETED NORMALLY!"
exit 0

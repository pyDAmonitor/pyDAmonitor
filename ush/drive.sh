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
export PYDAMONITOR=${HOMErrfs}/workflow/sideload/pyDAmonitor/scripts
#
#-----------------------------------------------------------------------
# Obtain unique process id (pid) and create the run directory (DATA).
#-----------------------------------------------------------------------
#
if [[ "${DO_SPINUP:-FALSE}" == "TRUE" ]];  then
  export WORKDIR=${COMOUT}/pyDAmonitor_spinup
  export JEDI_DIR=${COMOUT}/jedivar_spinup/${WGF}
  export NONVAR_CLD_DIR=${COMOUT}/nonvar_cldana_spinup/${WGF}
  export LOG_DIR=???
else
  export WORKDIR=${COMOUT}/pyDAmonitor
  export JEDI_DIR=${COMOUT}/jedivar/${WGF}
  export NONVAR_CLD_DIR=${COMOUT}/nonvar_cldana/${WGF}
  export LOG_DIR=???
fi
mkdir -p "${WORKDIR}"
cd "${WORKDIR}"
ln -snf ${JEDI_DIR}/* .
#
# parse the jedi log file to get minimization.txt and obs_counts.txt
ln -snf ${PYDAMONITOR}/parse_jedi_log.py .
./parse_jedi_log.py
#
# parse the nonvar cloud analysis log files to get nonvar_cloud_out.txt
ln -snf ${PYDAMONITOR}/parse_nonvar_cld_log.py .
./parse_nonvar_cld_log.py \
	--larccld ${LOG_DIR}/rrfs_nonvar_bufrobs_rrfsv2x_${CYC_TIME}.log \
	--metarcld ${LOG_DIR}/rrfs_nonvar_bufrobs_rrfsv2x_${CYC_TIME}.log \
	--lightning ${LOG_DIR}/rrfs_nonvar_bufrobs_rrfsv2x_${CYC_TIME}.log \
	--refmosaic ${LOG_DIR}/rrfs_nonvar_reflobs_rrfsv2x_${CYC_TIME}.log \
	--cloudanalysis ${NONVAR_CLD_DIR}/stdout_cloudanalysis.d0000
#
#
date
echo "pyDAmonitor HAS COMPLETED NORMALLY!"
exit 0

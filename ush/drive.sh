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
else
  export WORKDIR=${COMOUT}/pyDAmonitor
  export JEDI_DIR=${COMOUT}/jedivar/${WGF}
fi
mkdir -p "${WORKDIR}"
cd "${WORKDIR}"
ln -snf ${JEDI_DIR}/* .
#
# parse the jedi log file to get minimization.txt and obs_counts.txt
${PYDAMONITOR}/parse_jedi_log.py
#
#
date
echo "pyDAmonitor HAS COMPLETED NORMALLY!"
exit 0

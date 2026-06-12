#!/usr/bin/env bash
declare -rx PS4='+${SECONDS}s $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]${id}: '
set -x
#
#------------------------------------------------------------------------------------------------
# Note for offline debug: export GETKF_DIR, PYDAMONITOR, CDATE, etc
# and then run this script
#------------------------------------------------------------------------------------------------

ln -snf ${GETKF_DIR}/* .

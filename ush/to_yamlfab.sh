#!/usr/bin/env bash
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Usage: source ${0}"
    exit 1
fi
run_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
wflowdir=$(cd ${run_dir}/../..; pwd)
cd ${run_dir}/..

if [[ ! -d yamlfab ]]; then
  git clone https://github.com/wx-workflow/yamlfab
fi
cd yamlfab
mkdir external
cd external
#
if [[ "${wflowdir}" == *'workflow/sideload' ]]; then  # inside the wx-workflow
  ln -snfr "${wflowdir}/../../parm" .
  ln -snfr "${wflowdir}/../../sorc/RDASApp/parm/jcb-rdas" . 
else  # standalone pyDAmonitor
  git clone https://github.com/NOAA-EMC/rrfs-workflow
  cd rrfs-workflow
  git submodule update --init sorc/RDASApp
  cd ..
  ln -snfr rrfs-workflow/parm .
  ln -snfr rrfs-workflow/sorc/RDASApp/parm/jcb-rdas .
fi
cd ..

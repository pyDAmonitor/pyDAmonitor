#!/usr/bin/env bash
#
run_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
agent_dir="${run_dir}/../data/.agent"
source ${run_dir}/detect_machine.sh 

case ${MACHINE} in
  wcoss2)
    FIX_RRFS_LOCATION=/lfs/h2/emc/lam/noscrub/emc.lam/FIX_pyDAmonitor
    ;;
  hera)
    FIX_RRFS_LOCATION=/scratch2/BMC/rtrr/FIX_pyDAmonitor
    ;;
  ursa)
    FIX_RRFS_LOCATION=/scratch4/BMC/rtrr/FIX_pyDAmonitor
    ;;
  ursa)
    FIX_RRFS_LOCATION=/glade/work/geguo/FIX_pyDAmonitor
    ;;
  jet)
    FIX_RRFS_LOCATION=/lfs5/BMC/nrtrr/FIX_pyDAmonitor
    ;;
  orion|hercules)
    FIX_RRFS_LOCATION=/work/noaa/zrtrr/FIX_pyDAmonitor
    ;;
  gaea)
    if [[ -d /gpfs/f5 ]]; then
      FIX_RRFS_LOCATION=/gpfs/f5/gsl-glo/world-shared/role.rrfsfix/FIX_pyDAmonitor
    elif [[ -d /gpfs/f6 ]]; then
      FIX_RRFS_LOCATION=/gpfs/f6/bil-fire10-oar/world-shared/FIX_pyDAmonitor
    else
      echo "unsupported gaea cluster: ${MACHINE}"
    fi
    ;;
  *)
    FIX_RRFS_LOCATION=/unknown/location
    echo "platform not supported: ${MACHINE}"
    ;;
esac
mkdir -p ${run_dir}/../data/samples

filetype=$(file $agent_dir)
if [[ ! "$filetype" == *"symbolic link"* ]]; then
  rm -rf ${agent_dir}
fi
ln -snf ${FIX_RRFS_LOCATION} ${agent_dir}

touch ${run_dir}/../data/INIT_DONE
cp ${run_dir}/pre-commit ${run_dir}/../.git/hooks

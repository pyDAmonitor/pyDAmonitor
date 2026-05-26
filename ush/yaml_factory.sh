#!/usr/bin/env bash
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Usage: source ${0}"
    exit 1
fi
run_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
wflowdir=$(cd ${run_dir}/../..; pwd)
cd ${run_dir}/..

if [[ ! -d yaml_factory ]]; then
  git clone https://github.com/wx-workflow/yaml_factory
fi
cd yaml_factory

# always clone the latest rrfs-workflow and associated RDASApp
mkdir -p external
cd external
rm -rf rrfs-workflow
git clone -b rrfs-mpas-jedi https://github.com/NOAA-EMC/rrfs-workflow
cd rrfs-workflow
git submodule update --init sorc/RDASApp
cd ..
ln -snfr rrfs-workflow/parm .
ln -snfr rrfs-workflow/sorc/RDASApp/parm/jcb-rdas .
cd ..

# create a new branch 'update'
source ${run_dir}/load_pyDAmonitor.sh
echo "create a new branch 'update' to keep the main branch intact"
git checkout -b update
git branch
ush/guide.sh

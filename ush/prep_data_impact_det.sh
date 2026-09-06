#!/usr/bin/env bash
# prep all files needed by the webpage
declare -rx PS4='+${SECONDS}s $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]${id}: '
set -x

mkdir -p data_impact/figures
mkdir -p data_impact/pickle

# Move newly generated files into data_impact
if [ -d figures ]; then
    mv figures/* data_impact/figures/
    rmdir figures
fi

if [ -d pickle ]; then
    mv pickle/* data_impact/pickle/
    rmdir pickle
fi





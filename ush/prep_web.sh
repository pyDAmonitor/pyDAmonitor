#!/usr/bin/env bash
# link all files needed by the webpage into web/ 
declare -rx PS4='+${SECONDS}s $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]${id}: '
set -x

mkdir -p web
cd web
sed -e "s/2024050600/${PDY}${cyc}/g" ${PYDAMONITOR}/ush/index.html_cycle > index.html
mv ../*.png .
mv ../*.txt .
cp -L ../log.*out .
cp -L ../jedivar.yaml .
cp -L ../jedivar.pass2.yaml .

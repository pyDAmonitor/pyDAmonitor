#!/usr/bin/env bash
# prep all files needed by the webpage
declare -rx PS4='+${SECONDS}s $(basename ${BASH_SOURCE[0]:-${FUNCNAME[0]:-"Unknown"}})[${LINENO}]${id}: '
set -x

mkdir -p web
cd web
sed -e "s/2024050600/${CDATE}/g" ${PYDAMONITOR}/ush/index.html_cycle > index.html
mv ../*.png .
mv ../*.txt .
ln -snfr *.txt ..  # link a copy to the parent directory
cp -L ../log.*out .
cp -L ../jedivar.yaml .
cp -L ../jedivar.pass2.yaml .

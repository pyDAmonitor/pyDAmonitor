#!/usr/bin/env bash
#
run_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd ${run_dir}/..
git status notebooks | grep "notebook.*ipynb" | sed 's/.*\(notebooks\/.*\)/\1/' | xargs -I {} nbstripout "{}"

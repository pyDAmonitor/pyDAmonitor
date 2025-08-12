#!/usr/bin/env bash
doc_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

#### add new notebooks to the notebooks array
declare -A notebooks
notebooks["mpas_plotting.ipynb"]="mpas_plotting.ipynb"


### users usually do not need to make changes below this line
### ========================================================================
doc_repo=$1
if [[ -z "${doc_repo}" ]]; then
  echo "Usage: build_book.sh <doc_repo>"
  exit 1
fi

set -x
### always start from a clean notebook_docs/ directory
rm -rf ${doc_dir}/notebook_docs
mkdir -p ${doc_dir}/notebook_docs

### link notebooks from pyDAmonitor/notebooks/  to pyDAmonitor/docs/notebook_docs
for nb in "${notebooks[@]}"; do
  ln -snf ${doc_dir}/../notebooks/${nb} ${doc_dir}/notebook_docs/
done

### clean the book first and then build
jupyter-book clean ${doc_dir}
jupyter-book build ${doc_dir}

### push book to doc_repo
save_origin=$(git remote get-url origin)

git remote set-url origin ${doc_repo}
ghp-import -n -p -f ${doc_dir}/_build/html

git remote set-url origin ${save_origin}

#!/usr/bin/env bash
doc_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

### users usually do not need to make changes below this line
### ========================================================================
if [[ "$CONDA_DEFAULT_ENV" != "pyDAmonitor"  ]]; then
  echo -e "\n    !!! source ush/load_pyDAmonitor.sh first !!!\n"
  exit 1
fi
#
# save the origin URL before running ghp-import, which has to use the origin remote
save_origin=$(git remote get-url origin)
#
# get the remote url for current branch and set it as book_repo
remote=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null | cut -d'/' -f1)
if [[ -z "${remote}" ]]; then
  echo "Push current branch to a remote first and then run build_book.sh again"
  exit 1
fi
book_repo=$(git remote get-url ${remote})
#book_repo=git@github.com:pyDAmonitor/docs # use this line to overwrite the automatically-detected book_repo

if [[ "${book_repo}" ==  *"NOAA-GSL/pyDAmonitor" ]] \
   || [[ "${book_repo}" ==  *"pyDAmonitor/pyDAmonitor" ]]; then
      echo "ERROR: current branch tracks the authoritative repository:"
      echo "  ${book_repo}"
      echo "users can ONLY push books to their own forks"
      exit 1
fi

set -x
### clean the book first and then build
jupyter-book clean ${doc_dir}
jupyter-book build ${doc_dir}

### push book to book_repo
# change origin, ghp-import and then restore origin 
git remote set-url origin ${book_repo}
ghp-import -n -p -f ${doc_dir}/_build/html
git remote set-url origin ${save_origin}

### print out helper information
set +x
account=$(echo "${book_repo}" | awk -F'[:/]' '{print $(NF-1)}')
echo -e "\nVisit https://${account}.github.io/pyDAmonitor to check the results"
echo " (Github action may take a few minutes to render the updated pages)"

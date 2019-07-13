#!/bin/bash

set -euo pipefail

CWD=$(pwd)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR/..
set -x
python3 setup.py sdist bdist_wheel
twine upload dist/* -r factual
set +x
cd $CWD


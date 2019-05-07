#!/bin/bash

set -euo pipefail

CWD=$(pwd)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd $SCRIPT_DIR/..
set -x
python3 setup.py sdist upload -r factual
set +x
cd $CWD


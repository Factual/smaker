#!/bin/bash

set -euo pipefail

cd training/smk/snakerunner
set -x
python3 setup.py sdist upload -r factual
set +x
cd ../../..

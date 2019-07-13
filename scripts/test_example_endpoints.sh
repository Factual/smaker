#! /bin/bash

set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
EXAMPLE_DIR=$DIR/../examples

cd $EXAMPLE_DIR

OUTPUT_PATH=output/test-output-path
SOURCE=test-source-xyz
set -x

smaker fly \
    -c simple/config.json \
    -s simple/Snakefile \
    --source=$SOURCE \
    --output-path=$OUTPUT_PATH \
    -v |\
    grep "$OUTPUT_PATH/$SOURCE"

smaker fly \
    -c simple/config.json \
    -s simple/Snakefile \
    --source $SOURCE \
    --output-path $OUTPUT_PATH \
    -v |\
    grep "$OUTPUT_PATH/default"

smaker fly \
    -c simple/config.json \
    -s Snakefile \
    --module hello_world/Snakefile.hello \
    --quiet

for endpoint in $(smaker list); do
    smaker run -e $endpoint --quiet
done
set +x


echo "Successful dryruns for example endpoints"

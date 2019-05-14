#! /bin/bash

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
EXAMPLE_DIR=$DIR/../examples

cd $EXAMPLE_DIR
set -x
for endpoint in $(smaker list); do
    smaker run -e $endpoint --quiet
done
set +x

echo "Successful dryruns for example endpoints"

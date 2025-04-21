#!/bin/sh
DIR=$(dirname "$(readlink -f "$0")")

(
    cd "${DIR}/../csv"
    "${DIR}/sdk-class-api-levels.sh"
)

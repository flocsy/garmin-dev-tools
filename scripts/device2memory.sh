#!/bin/sh
# example line: fr245:32768

TYPE=${1:-datafield}
OUTPUT=${2:-device2memory-${TYPE}.csv}

DIR=$(dirname "$(readlink -f "$0")")
. "${DIR}/_sdk.sh"
echo "$0" "${TYPE}"

for DIR in "${DEVICES_DIR}"/* ; do
    DEVICE=$(echo "${DIR}" | sed -e "s#.*/##")
    echo "${DEVICE}:$(jq '.appTypes[] | select(.type | contains("'${TYPE}'")).memoryLimit' "${DIR}/compiler.json")"
done > "${OUTPUT}"

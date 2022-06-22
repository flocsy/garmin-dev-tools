#!/bin/sh
# example line: fr245:3.2.6

OUTPUT=${1:-device2max-version.csv}

DEVICES_DIR="${CIQ_SDK_HOME}/Devices"
for DIR in "${DEVICES_DIR}"/* ; do
    DEVICE=$(echo "${DIR}" | sed -e "s#.*/##")
    echo "${DEVICE}:$(jq -r '.partNumbers[].connectIQVersion' "${DIR}/compiler.json" | sort -n | uniq | tail -n 1)"
done > "${OUTPUT}"

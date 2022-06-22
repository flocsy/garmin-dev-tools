#!/bin/sh
# example line: 4.1.2:fr255,fr255m,fr255s,fr255sm,fr955

OUTPUT=${1:-max-version2devices.csv}

DEVICES_DIR="${CIQ_SDK_HOME}/Devices"
for DIR in "${DEVICES_DIR}"/* ; do
    DEVICE=$(echo "${DIR}" | sed -e "s#.*/##")
    echo "$(jq -r '.partNumbers[].connectIQVersion' "${DIR}/compiler.json" | sort -n | uniq | tail -n 1):${DEVICE}"
done | sort -n | datamash -t : groupby 1 collapse 2 > "${OUTPUT}"

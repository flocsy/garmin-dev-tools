#!/bin/sh
# example line: 32768:fr245,fenix6,...

TYPE=${1:-datafield}
OUTPUT=${2:-memory2devices-${TYPE}.csv}

DEVICES_DIR="${CIQ_SDK_HOME}/Devices"
for DIR in "${DEVICES_DIR}"/* ; do
    DEVICE=$(echo "${DIR}" | sed -e "s#.*/##")
    echo "$(jq '.appTypes[] | select(.type | contains("'${TYPE}'")).memoryLimit' "${DIR}/compiler.json"):${DEVICE}"
done | sort -n | datamash -t : groupby 1 collapse 2 > "${OUTPUT}"

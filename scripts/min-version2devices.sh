#!/bin/sh
# example line: 4.1.2:fr255,fr255m,fr255s,fr255sm,fr955

OUTPUT=${1:-min-version2devices.csv}
INPUT=${2:-device2min-version.csv}

echo "$0"

#DEVICES_DIR="${CIQ_SDK_HOME}/Devices"
#for DIR in "${DEVICES_DIR}"/* ; do
#    DEVICE=$(echo "${DIR}" | sed -e "s#.*/##")
#    echo "$(jq -r '.partNumbers[].connectIQVersion' "${DIR}/compiler.json" | sort --version-sort | uniq | head -n 1):${DEVICE}"
#done | sort --version-sort | datamash -t : groupby 1 collapse 2 > "${OUTPUT}"

while read LINE; do
    DEVICE=$(echo "${LINE}" | sed -e 's#:.*##')
    MIN=$(echo "${LINE}" | sed -e 's#.*:##')
    echo "${MIN}:${DEVICE}"
done < "${INPUT}" | sort --version-sort | datamash -t : groupby 1 collapse 2 > "${OUTPUT}"

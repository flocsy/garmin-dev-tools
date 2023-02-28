#!/bin/sh
# example line: fr245:3.2.6,3.3.1

OUTPUT=${1:-device2all-versions.csv}

DEVICES_DIR="${CIQ_SDK_HOME}/Devices"
for DIR in "${DEVICES_DIR}"/* ; do
    DEVICE=$(echo "${DIR}" | sed -e "s#.*/##")
    OLD=""
    if [[ -f "${OUTPUT}" ]]; then
        OLD="$(grep "${DEVICE}:" "${OUTPUT}")"
        OLD=$(echo ${OLD/${DEVICE}:/} | tr ", " "\n\n")
    fi
    NEW="$(jq -r '.partNumbers[].connectIQVersion' "${DIR}/compiler.json" | sort --version-sort | uniq)"
    ALL=$(echo "${OLD}\n${NEW}" | sort --version-sort | uniq | grep -v '^$' | xargs | sed -e 's# #,#g')
#    echo "$DEVICE:${OLD}\nNEW:${NEW};" > /dev/stderr
#    echo "${OLD}\n${NEW}" | sort --version-sort | uniq > /dev/stderr
    echo "${DEVICE}/${ALL}"
done | sort | tr '/' ':' > "${OUTPUT}.tmp"
mv "${OUTPUT}.tmp" "${OUTPUT}"

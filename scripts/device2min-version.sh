#!/bin/sh
# example line: fr245:3.2.6

OUTPUT=${1:-device2min-version.csv}

DIR=$(dirname "$(readlink -f "$0")")
. "${DIR}/_sdk.sh"

for DIR in "${DEVICES_DIR}"/* ; do
    DEVICE=$(echo "${DIR}" | sed -e "s#.*/##")
    OLD=""
    if [[ -f "${OUTPUT}" ]]; then
        OLD="$(grep "${DEVICE}:" "${OUTPUT}")"
        OLD=${OLD/${DEVICE}:/}
    fi
    NEW="$(jq -r '.partNumbers[].connectIQVersion' "${DIR}/compiler.json" | sort --version-sort | uniq | head -n 1)"
    MIN=$(echo "${OLD}\n${NEW}" | sort --version-sort | grep -v '^$' | head -n 1)
    # echo "$DEVICE:${OLD}\nNEW:${NEW};" > /dev/stderr
    # echo "${OLD}\n${NEW}" | sort --version-sort | grep -v '^$' | head -n 1 > /dev/stderr
    # echo "${DEVICE}:${MIN}" > /dev/stderr
    echo "${DEVICE}/${MIN}"
done | sort | tr '/' ':' > "${OUTPUT}.tmp"
mv "${OUTPUT}.tmp" "${OUTPUT}"

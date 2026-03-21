#!/bin/sh
DIR=$(dirname "$(readlink -f "$0")")

(
    cd "${DIR}/../csv"
    "${DIR}/device2all-versions.sh"
    "${DIR}/device2max-version.sh"
    "${DIR}/device2min-version.sh"
    "${DIR}/max-version2devices.sh"
    "${DIR}/min-version2devices.sh"
    "${DIR}/device2ttf-fonts.sh"

    for TYPE in audioContentProvider background datafield glance watchApp watchFace widget; do
        "${DIR}/device2memory.sh" "${TYPE}"
        "${DIR}/memory2devices.sh" "${TYPE}"
    done
)

(
    cd "${DIR}/../font-analyzer"
    "./device2chars.sh"
)

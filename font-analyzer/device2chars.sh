#!/bin/sh
DIR=$(dirname "$(readlink -f "$0")")
. "${DIR}/../scripts/_sdk.sh"
echo "$0"

for DIR in "${DEVICES_DIR}"/* ; do
    DEVICE=$(echo "${DIR}" | sed -e "s#.*/##")
    echo "${DEVICE}"
    npx cft-font-info "${DEVICE}" | jq . > "fonts/${DEVICE}.fonts.json"
#    npx cft-font-info "${DEVICE}" | jq '{common:""} + (.fonts[] |= ([.charInfo[].char]|add))' > "chars/${DEVICE}.chars.json"
    jq '(.fonts[] |= ([.charInfo[].char]|add))' < "fonts/${DEVICE}.fonts.json" > "chars/${DEVICE}.chars.json"
done

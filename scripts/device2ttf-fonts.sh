#!/bin/sh

OUTPUT=${1:-device2ttf-fonts.csv}

DIR=$(dirname "$(readlink -f "$0")")
. "${DIR}/_sdk.sh"
echo "$0"

for D in "${DEVICES_DIR}/"* ; do
	# jq -r '.fonts.[] | "'"${D/$DEVICES_DIR\//}"':" + .fontSet + "=" + ([.fonts.[] | select(.type == "ttf" or .type == "system_ttf") | .name] | join(","))' "$D/simulator.json"
	jq -r '.fonts.[] | "'"${D/$DEVICES_DIR\//}"':" + .fontSet + "=" + ([.fonts.[] | select(.type == "system_ttf") | .name] | join(","))' "$D/simulator.json"
done > "${OUTPUT}"

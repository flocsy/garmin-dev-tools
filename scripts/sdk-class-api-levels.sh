#!/bin/sh
# example line: Graphics.Dc:1.0.0,1.2.0,2.3.0,3.2.0,4.0.0,4.2.1

echo "$0"

OUTPUT_ALL=${1:-sdk-class-all-api-levels.csv}
OUTPUT_MIN=${1:-sdk-class-min-api-levels.csv}

DIR=$(dirname "$(readlink -f "$0")")
. "${DIR}/_sdk.sh"
SDK_DIR="${CIQ_SDK_HOME}/Sdks/$(ls "${CIQ_SDK_HOME}/Sdks" | sort | tail -n 1)"
DOC_DIR="${SDK_DIR}/doc/Toybox"

find "${DOC_DIR}" -type f -exec echo "{}" \; | \
while read F; do
    echo "$F" | sed -e "s#${DOC_DIR}/##"
    grep "API Level" "$F" | sed -e 's#API Level ##' | sort | uniq | xargs| sed -e 's# #,#g' | sed -e 's#$#*#'
done | sed -e 's#^\./##' -e 's#.html$#:#' | tr / . | tr -d '\n' | tr '*' '\n' > "${OUTPUT_ALL}"

sed -e 's#,.*##g' "${OUTPUT_ALL}" > "${OUTPUT_MIN}"

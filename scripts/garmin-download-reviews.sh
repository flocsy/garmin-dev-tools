#!/usr/bin/env bash

APP_ID="$1"

if [[ x"${APP_ID}" == x"" ]]; then
    echo "Usage: $0 <APP_ID>"
    exit 1
fi

PAGE_SIZE=10

JSON="/tmp/garmin-app-${APP_ID}.reviews.json"
CSV="/tmp/garmin-app-${APP_ID}.reviews.csv"

PAGE=0
START_PAGE=$[PAGE_SIZE * PAGE]
curl -s "https://apps.garmin.com/api/appsLibraryExternalServices/api/asw/apps/${APP_ID}/reviews?sortType=CreatedDate&ascending=true&latestVersionOnly=false&pageSize=${PAGE_SIZE}&startPageIndex=${START_PAGE}" > "${JSON}"
jq -r '.[] |= del(.replies) | (.[0] | keys_unsorted)  as $keys | $keys, map([.[$keys[]]])[] | @csv' < "${JSON}" 2>/dev/null > "${CSV}"

while [[ $(wc -c "$JSON" | sed -e 's#^ *\([0-9]*\).*#\1#') -gt 2 ]]; do
    echo -n "."
	PAGE=$[PAGE + 1]
    START_PAGE=$[PAGE_SIZE * PAGE]
    curl -s "https://apps.garmin.com/api/appsLibraryExternalServices/api/asw/apps/${APP_ID}/reviews?sortType=CreatedDate&ascending=true&latestVersionOnly=false&pageSize=${PAGE_SIZE}&startPageIndex=${START_PAGE}" > "${JSON}"
    jq -r '.[] |= del(.replies) | (.[0] | keys_unsorted)  as $keys | map([.[$keys[]]])[] | @csv' < "${JSON}" 2>/dev/null >> "${CSV}"
done
echo ""

mv "${CSV}" "${APP_ID}.reviews.csv"

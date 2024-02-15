#!/usr/bin/env bash
# source: https://github.com/flocsy/garmin-dev-tools/tree/main/scripts/garmin-download-stats.sh ©2023-2024 by flocsy



########################################################################################
# The following is an example configuration. You must create a file either
# in ~/.garmin-download-stats.conf or in garmin-download-stats.conf next to this script
# List you app ids here:
APP_IDS=(
    # My 1st app:
    "9BF5182D-D964-4DCF-AC61-3133E856F4A9"

    # My 2nd app:
    "F42FBBA2-F65B-4533-B25D-589E6D02D3B9"
)

STATS_DIR="${HOME}/stats/garmin/download"
########################################################################################



# Different regions have their own garmin servers and we need to scan them all. i.e: garmin.com, garmin.cn
DOMAINS=("com" "cn")

CONF_FILE="garmin-download-stats.conf"
DIR=$(dirname "$(readlink -f "$0")")
CONF_FILE="${HOME}/.garmin-download-stats.conf"
if [ ! -f "${CONF_FILE}" ]; then
    CONF_FILE="${DIR}/garmin-download-stats.conf"
    if [ ! -f "${CONF_FILE}" ]; then
        echo "You must have the configuration in ${HOME}/.garmin-download-stats.conf or ${CONF_FILE}"
        exit 1
    fi
fi
source "${DIR}/garmin-download-stats.conf"

fetch_stats() {
    APP_ID="${1}"
    DOMAIN="${2}"

    CSV="${HOME}/stats/garmin/download/${APP_ID}.${DOMAIN}.csv"
    # CSV=/tmp/${APP_ID}.${DOMAIN}.csv


    # the old data was in the html:
    # HTML="/tmp/garmin-app-${APP_ID}.${DOMAIN}.html"
    # curl -s "https://apps.garmin.${DOMAIN}/en-US/apps/${APP_ID}" > "${HTML}"
    # DOWNLOADS=$(pup "span.stat-adds span:last-child text{}" < "${HTML}")
    # RATING=$(pup ".app-detail span.stat-rating .rating attr{title}" < "${HTML}")
    # REVIEWS=$(pup "span.stat-rating .badge text{}" < "${HTML}")
    # NEW_DATA="${DOWNLOADS},${RATING},${REVIEWS}"

    JSON="/tmp/garmin-app-${APP_ID}.${DOMAIN}.json"
    curl -s "https://apps.garmin.com/api/appsLibraryExternalServices/api/asw/apps/${APP_ID}" > "${JSON}"
    NEW_DATA=$(jq -r '(.downloadCount|tostring) + "," + (.averageRating|tostring) + "," + (.reviewCount|tostring)' < "${JSON}")

    LAST_DATA=$(tail -n 1 "${CSV}" | sed -e 's#^[^,]*,##')
    #echo "last: $LAST_DATA, current: ${DOWNLOADS},${RATING},${REVIEWS}" >> /tmp/debug
    if [[ x"${LAST_DATA}" != x"${NEW_DATA}" ]] && [[ x"${NEW_DATA}" != x",," ]]; then
        DATE=$(date +%Y-%m-%d)
        echo "${DATE},${NEW_DATA}" >> "${CSV}"
    fi
}

for APP_ID in ${APP_IDS[@]}; do
    for DOMAIN in ${DOMAINS[@]}; do
        fetch_stats "${APP_ID}" "${DOMAIN}"
    done
done

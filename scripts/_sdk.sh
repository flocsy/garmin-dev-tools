if [[ -z "${CIQ_SDK_HOME}" ]]; then
    CIQ_SDK_HOME="$HOME/Library/Application Support/Garmin/ConnectIQ"
    if [[ ! -d "${CIQ_SDK_HOME}" ]]; then
        echo "Set CIQ_SDK_HOME to the directory where you downloaded the SDK"
        exit 1
    fi
fi

DEVICES_DIR="${CIQ_SDK_HOME}/Devices"

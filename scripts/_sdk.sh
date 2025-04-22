# https://developer.garmin.com/connect-iq/reference-guides/monkey-c-command-line-setup/
if [[ -z "${CIQ_SDK_HOME}" ]]; then
    # macos
    CIQ_SDK_HOME="$HOME/Library/Application Support/Garmin/ConnectIQ"
    if [[ ! -d "${CIQ_SDK_HOME}" ]]; then
        # linux
        CIQ_SDK_HOME="$HOME/.Garmin/ConnectIQ"
    fi
    if [[ ! -d "${CIQ_SDK_HOME}" ]]; then
        # windows (WSL)
        if ( command -v wslpath 2>&1 >/dev/null && command -v wslvar 2>&1 >/dev/null ); then
            CIQ_SDK_HOME="$(wslpath "$(wslvar APPDATA)"'\Garmin\ConnectIQ')" || true
        fi
    fi
    if [[ ! -d "${CIQ_SDK_HOME}" ]]; then
        echo "Set CIQ_SDK_HOME to the directory where you downloaded the SDK"
        exit 1
    fi
fi

DEVICES_DIR="${CIQ_SDK_HOME}/Devices"

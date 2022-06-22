# garmin-dev-tools
Tools for Garmin CIQ developers.

A collection of shell scripts for Garmin ConnectIQ and Monkey C developers.

I'll try to update the files in csv/ folder to the latest possible data. You can open an issue if I forgot to upload the latest, up-to-date files.

## Installation
All scripts use bash and the "usual" cli tools.

All scripts use jq: https://stedolan.github.io/jq/

Some of the scripts use datamash: https://www.gnu.org/software/datamash/

You need to set the environment variable CIQ_SDK_HOME to point to the directory where you installed the CIQ sdk:

`export CIQ_SDK_HOME="~/.Garmin/ConnectIQ"`

## Usage

In the SDK Manager make sure you have the latest versions of all the devices you're interested in.

You can either run a specific script or `run-all.sh`.

Each script has the possible parameters in the 1st lines and an example output line where you can see the format.

The last (optional) parameter is always the output file name, by default the output files are put to the current directory.

Some scripts need the app-type as the 1st parameter.

## Changelog
1.0 - initial release

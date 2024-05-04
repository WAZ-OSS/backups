#!/bin/env bash
# set -e # crontab workaround

cycleMinutes=1440 # 1 day

if [ -z "$1" ]; then
    echo "usage: $0 /REMOTES/BASE/DIRECTORY/ [doit] [dontask] [cycleMinutes=$cycleMinutes]"
    echo "for usage inside crontab:"
    echo "- sync will be silently skipped if there is a sync log newer than \$cycleMinutes(default: $cycleMinutes) ago."
    echo -e "\nie - add in crontab to run each hour and only update sync each 6 hours:"
    echo -e "\n0 * * * * $0 /REMOTES_DIRECTORY doit dontask 360"
    exit 1
fi
REMOTESDIR=${1:-somewhere}
REMOTESDIR=${REMOTESDIR%/}
DOIT=${2:-dontdoit}
DONTASK=${3:-ask}
MINUTES=${4:-$cycleMinutes}

SCRIPTSDIR=$(dirname "$0")
cd "$REMOTESDIR" || { echo "cannot cd to '$REMOTESDIR'"; exit 1; }

LOGSDIR="$REMOTESDIR/.debris"
mkdir -p "$LOGSDIR"
NOW="$(date +%Y-%m-%d_%H.%M)"
LOGFILE="$LOGSDIR/$NOW-$(basename "$0").log"

RECENTLOGS=$(find "$LOGSDIR" -iname "*-$(basename "$0").log" -mmin "-$MINUTES")
if [ "$RECENTLOGS" != "" ]
then
    # echo "[$(date +'%Y-%m-%d %H:%M:%S %Z')] Already ran less than $MINUTES minutes ago: $RECENTLOGS"
    exit 0
fi

for REMOTE in */; do
    echo "[$(date +'%Y-%m-%d %H:%M:%S %Z')] ${REMOTE%/}"
    SECONDS=0
    "$SCRIPTSDIR"/rclone-pull.sh "$REMOTE" "$DOIT" "$DONTASK" >>"$LOGFILE" || echo -e "[ERROR] code: $?"
    echo "[$(date +'%Y-%m-%d %H:%M:%S %Z')] $(TZ=UTC0 printf '%(%H:%M:%S)T' "$SECONDS")"
done

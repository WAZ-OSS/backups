#!/bin/env bash
set -e

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

cd "$REMOTESDIR"

LOGSDIR="$REMOTESDIR/.debris"
mkdir -p "$LOGSDIR"
NOW="$(date +%Y-%m-%d_%H.%M)"
LOGFILE="$LOGSDIR/$NOW-$(basename "$0").log"

RECENTLOGS=$(find "$LOGSDIR" -iname "*-$(basename "$0").log" -mmin "-$MINUTES")
if [ "$RECENTLOGS" != "" ]
then
    # echo "already ran less than $MINUTES minutes ago:"
    # echo "$RECENTLOGS"
    exit 0
fi

for REMOTE in */; do
    echo "[$(date +'%Y-%m-%d %H:%M:%S %Z')] $REMOTE START"
    SECONDS=0
    rclone-pull.sh "$REMOTE" "$DOIT" "$DONTASK" >>"$LOGFILE" || echo -e "[ERROR] code: $?"
    echo "[$(date +'%Y-%m-%d %H:%M:%S %Z')] $REMOTE DONE (took $(TZ=UTC0 printf '%(%H:%M:%S)T' "$SECONDS"))"
done

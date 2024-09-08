#!/bin/env bash
# set -e # crontab workaround

lockfile="/var/tmp/$(basename "$0").lock"
if [ -f "$lockfile" ] ;then
  echo "lockfile exists, test if process allready running"
  if kill -0 "$(cat "$lockfile")" ; then
    echo "Already running. Exiting."
    exit 0
  fi
fi
echo $$ >"$lockfile"

cycleMinutes=360 # 6 hours

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
LOGSDIR_YEAR="$LOGSDIR/$(date +%Y)"
LOGFILE="$LOGSDIR_YEAR/$(date +%m)/00_$(basename "$0").log"
mkdir -p "$(dirname "$LOGFILE")"

for REMOTE in */; do
    SUCCESSFILE="${REMOTE%/}.success.log"
    RECENTLOGS=$(find "$LOGSDIR_YEAR" -name "$SUCCESSFILE" -mmin "-$MINUTES")
    if [ "$RECENTLOGS" != "" ]
    then
        # echo "[$(date +'%Y-%m-%d %H:%M:%S %Z')] Already ran less than $MINUTES minutes ago: $RECENTLOGS"
        continue
    fi

    echo "[$(date +'%Y-%m-%d %H:%M:%S %Z')] ${REMOTE%/}"
    SECONDS=0
    "$SCRIPTSDIR"/rclone-pull.sh "$REMOTE" "$DOIT" "$DONTASK" >>"$LOGFILE"
    RETURNCODE=$?
    if [ $RETURNCODE -eq 0 ]; then
        date +'%Y-%m-%d %H:%M:%S %Z' >>"$LOGSDIR_YEAR/$SUCCESSFILE"
    else
        echo -e "[ERROR] code: $RETURNCODE"
    fi
    echo "[$(date +'%Y-%m-%d %H:%M:%S %Z')] $(TZ=UTC0 printf '%(%H:%M:%S)T' "$SECONDS")"
done

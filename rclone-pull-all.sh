#!/bin/env bash
set -e

if [ -z "$1" ]; then
    echo "usage: $0 /REMOTES/BASE/DIRECTORY/ [doit] [dontask]"
    exit 1
fi

REMOTESDIR="${1:-somewhere}"
DOIT=${2:-dontdoit}
DONTASK=${3:-ask}

cd "$REMOTESDIR"

LOGSDIR="$REMOTESDIR/.debris"
mkdir -p "$LOGSDIR"
NOW="$(date +%Y-%m-%d_%H.%M)"
LOGFILE="$LOGSDIR/$NOW-$(basename "$0").log"

for REMOTE in */; do
    echo "[$(date +'%Y-%m-%d %H:%M:%S %Z')] $REMOTE START"
    SECONDS=0
    rclone-pull.sh "$REMOTE" "$DOIT" "$DONTASK" >>"$LOGFILE" || echo -e "[ERROR] code: $?"
    echo "[$(date +'%Y-%m-%d %H:%M:%S %Z')] $REMOTE DONE (took $(TZ=UTC0 printf '%(%H:%M:%S)T' "$SECONDS"))"
done

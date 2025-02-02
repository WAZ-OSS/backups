#!/bin/env bash
set -e

DOIT=${2:-dontdoit}
DONTASK=${3:-ask}
# https://rclone.org/googlephotos/#size
# GPHOTOS_BY_YEAR=${4:-gphotos-by-year}
# --gphotos-include-archived

if [ -z "$1" ]; then
    echo "usage: $0 REMOTE [doit] [dontask]"
    exit 1
fi

REMOTE=${1%/}

SRC="$REMOTE:/"
DST="$REMOTE"

[ -d "$DST" ] || {
    echo "missing dir $DST"
    exit 1
}

if [ "$DOIT" != 'doit' ]; then
    echo "missing [doit] => executing dry-run mode"
    SUFFIX="--dry-run"
fi

NOW="$(date +%Y-%m-%d_%H.%M)"
BKP=".debris/$DST/$NOW-rclone$SUFFIX"
LOG_FILE=".debris/$(date +%Y/%m/%d_%H.%M)-$DST.log"

CMD="rclone sync \\
    $SRC \\
    $DST/ \\
    --track-renames \\
    --bwlimit-file 1M \\
    --transfers 2 \\
    --checksum \\
    --backup-dir=$BKP \\
    --log-file $LOG_FILE \\
    -v $SUFFIX
"

[ "$DONTASK" == 'dontask' ] || read -p "Press any key to continue ... (ctr+c to abort)" -n1 -s -r

mkdir -p "$BKP"
LOG_DIR=$(dirname "$LOG_FILE")
mkdir -p "$LOG_DIR"
echo -e "\n[$(date +'%Y-%m-%d %H:%M:%S %Z')] syncing [$REMOTE]..." | tee -a "$LOG_FILE"

echo -e "$CMD\n" >>"$LOG_FILE"
eval "$CMD"

# echo "cleanup small files in $BKP"
# find . -iname '.DS_store' # -delete
# find "$BKP/" -iname '._.ds_store' # -delete
# find "$BKP/" -type f -size -4096 -exec ls -l "{}" \; -print # -delete
# echo "cleanup empty dirs in $BKP"
if [ -d "$BKP" ]; then
    find "$BKP/" -type d -empty -print -delete
fi

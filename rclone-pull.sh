#!/bin/bash

DOIT=${2:-dontdoit}

if [ -z "$1" ]; then
    echo "usage: $0 REMOTE [doit]"
    exit 1
fi

REMOTE=${1%/}

SRC="$REMOTE:/"
DST="$REMOTE"

NOW="$(date +%Y-%m-%d_%H.%M)"
BKP="$DST.debris/$NOW-rclone"

[ -d "$DST" ] || {
    echo "missing dir $DST"
    exit 1
}

CMD="rclone sync $SRC $DST/ --track-renames --bwlimit-file 1M --transfers 2 --checksum --backup-dir=$BKP -v --log-file $BKP/rclone.log --progress"
# --stats 60s
if [ "$DOIT" != 'doit' ]; then
    echo "missing [doit] => executing dry-run mode"
    CMD="$CMD --dry-run"
fi

echo -e "\n$CMD"
read -p "Press any key to continue ... (ctr+c to abort)" -n1 -s -r

mkdir -p "$BKP"
echo -e "$CMD\n" >>"$BKP/rclone.log"
eval "$CMD"

echo "cleanup small files in $BKP"
# find . -iname '.DS_store' -delete
# find "$BKP/" -iname '._.ds_store' -delete
# find "$BKP/" -type f -size -4096 -exec ls -l "{}" \; -print # -delete
echo "cleanup empty dirs in $BKP"
# find "$BKP/" -type d -empty -print -delete

#!/bin/bash

DOIT=${2:-dontdoit}

if [ -z "$1" ];
then
    echo "usage: $0 REMOTE [doit]";
    exit 1;
fi

REMOTE=${1%/}

SRC="$REMOTE"
DST="$REMOTE:/"

[ -d "$SRC" ] || { echo "missing dir $SRC" ; exit 666 ; }

CMD="rclone sync $SRC/ $DST --progress --bwlimit-file 1M --transfers 1 --checksum"
if [ "$DOIT" != 'doit' ]
then
    echo "missing [doit] => executing dry-run mode";
    CMD="$CMD --dry-run";
fi

echo -e "\n$CMD"
read -p "Press any key to continue ... (ctr+c to abort)" -n1 -s

echo "cleanup small files in $SRC ..."
find . -iname '.DS_store' -delete
find "$SRC/" -iname '._.ds_store' -delete
find "$SRC/" -type f -iname '.*' -size -4096 -exec ls -l "[tiny file] {}" \; -print # -delete
echo "show empty dirs in $SRC:"
find "$SRC/" -type d -empty -print

eval "$CMD"

ps fax|grep rcl[o]ne

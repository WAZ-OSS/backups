#!/bin/bash

[ -z "$1" ] && echo "missing arg1: source" && exit 1
[ -z "$2" ] && echo "missing arg2: source" && exit 2

SRC=$1
DST=$(echo "$2"|sed 's/\/$//')

[ -d "$DST" ] || { echo "no existe $DST" && exit 1 ; }

now=`TZ=America/Buenos_Aires date +%Y-%m-%d/%H.%M.%S%z-`
back_dir=".debris/$now$(echo "$SRC"|sed 's/:/~/'|sed 's/\///g')"
logfile="$back_dir/rclone.log"
back_dir="$back_dir/$(echo "$DST"|sed 's/^\///')"

mkdir -p $back_dir || exit 1
lockfile="$(dirname $(mktemp -u))/rclone.lock"

ACTION='sync'
SWITCHES="--backup-dir=$back_dir  --bwlimit=1M"
if [ ! -z ${DEBUG+x} ]; then
    ACTION='check'
    SWITCHES+="  --bwlimit=0 \
    --combined $back_dir/combined.log \
    --differ $back_dir/differ.log \
    --error $back_dir/error.log \
    --match $back_dir/match.log \
    --missing-on-dst $back_dir/missing-on-dst.log \
    --missing-on-src $back_dir/missing-on-src.log"
    # --progress
fi
cmd="rclone $ACTION $SRC $DST  $SWITCHES  2>&1|tee -a $logfile"

[ ! -z ${DEBUG+x} ] && echo "########### $cmd"|sed 's/  +/ \\\n\t\t\t/g'

flock -n $lockfile -c "$cmd" || echo -e "\n$lockfile LOCKED"

# delete log if empty
[ ! -s $logfile ] && [ -e $logfile ] && rm $logfile
# delete any empty file in backup dir
find $back_dir -type f -size 0 -delete
# delete any dir if empty
find $(dirname $back_dir) -type d -empty -delete

# prepend sync command if there is log file
[ -e $logfile ] && echo -e "# $cmd\n\n"|sed 's/ / \\\n\t/g'|cat - $logfile > $logfile.tmp && mv $logfile.tmp $logfile

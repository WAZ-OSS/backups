#!/bin/bash

[ -z "$1" ] && echo "missing arg1: source" && exit 1
[ -z "$2" ] && echo "missing arg2: source" && exit 2

SRC=$1
DST=$2

[ -d "$DST" ] || { echo "no existe $DST" && exit 1 ; }

now=`TZ=America/Buenos_Aires date +%Y-%m-%d/%H.%M.%S%z`
back_dir=".debris/$now"
logfile="$back_dir/rclone.log"

mkdir -p $back_dir
lockfile="$(dirname $(mktemp -u))/rclone.lock"

# --progress
cmd="rclone sync $SRC $DST --bwlimit=1M --backup-dir=$back_dir 2>&1 | tee -a $logfile"

# echo "$cmd"

flock -n $lockfile -c "$cmd"

# delete log if empty
[ ! -s $logfile ] && [ -e $logfile ] && rm $logfile
# delete trash dir if empty
[ -z "$(ls -A $back_dir)" ] && rmdir $back_dir
[ -z "$(ls -A $(dirname $back_dir))" ] && rmdir $(dirname $back_dir)

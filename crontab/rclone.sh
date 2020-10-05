#!/bin/bash

[ -z "$1" ] && echo "missing arg1: source" && exit 1
[ -z "$2" ] && echo "missing arg2: source" && exit 2

SRC=$1
DST=$(echo "$2"|sed 's/\/$//')

[ -d "$DST" ] || { echo "no existe $DST" && exit 1 ; }

now=`TZ=America/Buenos_Aires date +%Y-%m-%d/%H.%M.%S%z-`
back_dir=".debris/$now$(echo "$SRC"|sed 's/:/~/'|sed 's/\//./g')"
logfile="$back_dir/rclone.log"
back_dir="$back_dir/$(echo "$DST"|sed 's/^\///')"

mkdir -p $back_dir
lockfile="$(dirname $(mktemp -u))/rclone.lock"

SWITCHES="--backup-dir=$back_dir --bwlimit=1M"
if [ ! -z ${DEBUG+x} ]; then
    SWITCHES+=" --progress --bwlimit=0"
fi
cmd="rclone sync $SRC $DST $SWITCHES 2>&1|tee -a $logfile"

echo "$cmd"

flock -n $lockfile -c "$cmd" || echo -e "\n$lockfile LOCKED"

# delete log if empty
[ ! -s $logfile ] && [ -e $logfile ] && rm $logfile
# delete trash dir if empty
[ -z "$(ls -A $back_dir)" ] && rmdir $back_dir
[ -z "$(ls -A $(dirname $back_dir))" ] && rmdir $(dirname $back_dir)

# prepend sync command if there is log file
[ -e $logfile ] && echo -e "$cmd\n\n"|sed 's/ / \\\n\t/g'|cat - $logfile > $logfile.tmp && mv $logfile.tmp $logfile

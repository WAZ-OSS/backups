#!/bin/bash

SOURCE_DIR=${1:-/mnt/BACK-A/rclone}
DESTINATION_DIR=${2:-/mnt/BACK-B/rclone}

[ -d "$SOURCE_DIR" ] || { echo "no existe $SOURCE_DIR" && exit 1 ; }
[ -d "$DESTINATION_DIR" ] || { echo "no existe $DESTINATION_DIR" && exit 1 ; }

now=`TZ=America/Buenos_Aires date +%Y-%m-%d/%H.%M.%S%z-rsync`
trash=".debris"
back_now="$trash/$now"
logfile="$DESTINATION_DIR/$back_now/rsync.log"

back_dir=$(dirname $logfile)
mkdir -p $back_dir
lockfile="$(dirname $(mktemp -u))/rsync.lock"

SWITCHES="--archive --delete --backup --backup-dir=$back_now --exclude=$trash"
if [ ! -z ${DEBUG+x} ]; then
    SWITCHES+=" --progress --itemize-changes --verbose"
    # --checksum --partial --compress --dry-run
fi

cmd="rsync $SOURCE_DIR/ $DESTINATION_DIR/ $SWITCHES 2>&1|tee -a $logfile"

echo "$cmd"

flock -n $lockfile -c "$cmd" || echo -e "\n$lockfile LOCKED"

# delete log if empty
[ ! -s $logfile ] && [ -e $logfile ] && rm $logfile
# delete trash dir if empty
[ -z "$(ls -A $back_dir)" ] && rmdir $back_dir
[ -z "$(ls -A $(dirname $back_dir))" ] && rmdir $(dirname $back_dir)

# prepend sync command if there is log file
[ -e $logfile ] && echo -e "$cmd\n\n"|sed 's/ / \\\n\t/g'|cat - $logfile > $logfile.tmp && mv $logfile.tmp $logfile

#/bin/bash

cd "$(dirname "$0")"

LOGFILE="$(pwd)/.debris/$(basename "$0").log"

if [ -z ${THIS_IS_CRON+x} ]; then
    cron_command="THIS_IS_CRON=1 $(pwd)/$(basename $0) 2>&1"
    echo "
# add this to crontab:

0 */8 * * * $cron_command >>$LOGFILE
"
    echo "ENTER TO RUN NOW (with DEBUG=1), ctl+c to exit "
    read sarasa
    echo "RUNNING NOW ..."
    eval "DEBUG=1 $cron_command | tee -a $LOGFILE"
    exit 0
fi
now=`TZ=America/Buenos_Aires date +'%Y-%m-%d %H:%M:%S UTC%z'`
[ ! -z ${DEBUG+x} ] && echo -e "\n$now"

declare -a commands=(
    "./rclone.sh ody:/ ody"
    "./rclone.sh odw:/ odw"
    "./rsync.sh"
    )

lockfile="$(dirname $(mktemp -u))/crontab.lock"
(flock -n -e 200 && {   
    for cmd in "${commands[@]}"
    do
        [ ! -z ${DEBUG+x} ] && echo "########### $cmd"
        eval "$cmd" || exit 1
    done
    } || echo -e "\n$now $lockfile LOCKED"
) 200>$lockfile

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

for REMOTE in */ ; do
    echo "$REMOTE"
    rclone-pull.sh "$REMOTE" "$DOIT" "$DONTASK" || echo -e "\n####################\n[ERROR] pulling $REMOTE returns code: $?\n####################\n"
done

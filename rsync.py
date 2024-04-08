#!/bin/env python3

import os
import argparse
import subprocess
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("origin", help="origin dir ie: [localpath/important-stuff-dir]")
parser.add_argument("target", help="target dir ie: [hostname:]/path/backups")
parser.add_argument("doit", help="(if missing will run rsync with '--dry-run')", nargs="?", default="")
parser.add_argument("trash", help="trash dir (default: .debris)", nargs="?", default=".debris")
args = parser.parse_args()

trash = args.target + args.trash + "/" + datetime.now().strftime("%Y-%m-%d_%H.%M") + "-rsync"
logfile = f"{trash}/rsync.log"

os.makedirs(trash, exist_ok=True)

cli_parmas = [
    "rsync",
    "--archive",
    "--compress",
    "--partial",
    # "--progress",
    # "--verbose",
    "--exclude=" + args.trash,
    "--delete",
    "--backup",
    "--backup-dir=" + trash,
    "--itemize-changes",
    # "--delete-after",
    "--delete-delay",
    args.origin,
    args.target,
]

if args.doit != "doit":
    cli_parmas += ["--dry-run"]


print(" ".join(cli_parmas) + f" >{logfile}")

with open(f"{logfile}", "w") as output:

    process = subprocess.Popen(cli_parmas, stdout=output)

    while True:
        return_code = process.poll()
        if return_code is not None:
            print("\n\nRETURN CODE", return_code)
            break

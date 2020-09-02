#! python3

import os
import argparse
import subprocess
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("target", help="target location ie: [hostname:]/path")
parser.add_argument("origin", help="origin location", nargs="?", default=".")
parser.add_argument("backupDir", help="file to log output", nargs="?", default=".debris")
args = parser.parse_args()

backupDir = args.backupDir + "/" + datetime.now().strftime("%Y-%m-%d_%H.%M.%S")

os.makedirs(args.backupDir, exist_ok=True)

cli_parmas = [
    "rsync",
    "--archive",
    "--compress",
    "--partial",
    # "--progress",
    # "--verbose",
    "--exclude=" + args.backupDir,
    "--delete",
    "--backup",
    "--backup-dir=" + backupDir,
    "--itemize-changes",
    # "--dry-run",
    args.origin,
    args.target,
]

with open(f"{backupDir}.log", "w") as output:

    process = subprocess.Popen(cli_parmas, stdout=output, universal_newlines=True)

    while True:
        return_code = process.poll()
        if return_code is not None:
            print("\n\nRETURN CODE", return_code)
            break

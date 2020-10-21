#! python3

import os
import argparse
import subprocess
from datetime import datetime
from decouple import config

parser = argparse.ArgumentParser()
parser.add_argument("target", help="target dir ie: [hostname:]/path")
parser.add_argument("origin", help="origin dir", nargs="?", default=config("base_dir"))
parser.add_argument("trash", help="trash dir", nargs="?", default=config("trash"))
args = parser.parse_args()

trash = args.trash + "/" + datetime.now().strftime("%Y-%m-%d_%H.%M.%S")

os.makedirs(args.trash, exist_ok=True)

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
    # "--dry-run",
    args.origin,
    args.target,
]

with open(f"{trash}.log", "w") as output:

    process = subprocess.Popen(cli_parmas, stdout=output)

    while True:
        return_code = process.poll()
        if return_code is not None:
            print("\n\nRETURN CODE", return_code)
            break

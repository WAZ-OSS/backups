#!/bin/env python3

import os
import argparse
import subprocess
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("origin", help="origin dir ie: [hostname:]localpath/origin-dir/")
parser.add_argument("target", help="target dir ie: [hostname:]/path/backups/target-subdir/")
parser.add_argument("doit", help="(if missing will run rsync with '--dry-run')", nargs="?", default="")
parser.add_argument("trash", help="trash dir (default: .debris)", nargs="?", default=".debris")
args = parser.parse_args()

if not args.origin[-1] == "/" or not args.target[-1] == "/":
    print("\nERROR:\n to avoid confusions both origin-dir and target-dir must end in slash (/)")
    print("\nie: rsync.py dir1/backup-a/  dir2/backup-j/")
    print(" will sync source-dir CONTENTS (backup-a/*) into existing target-dir (backup-j/)")
    print(" (not creating extra 'backup-a' dir inside target 'backup-j/')")
    print("\nalso trash-dir will be created on target parent dir, ie: dir2/.debris/TIMESTAMP-backup-j\n")
    exit(1)

if not os.path.exists(args.origin):
    print(f"\nERROR: origin dir '{args.origin}' not found")
    exit(1)

if not os.path.exists(args.target):
    print(f"\nERROR: target dir '{args.target}' not found")
    exit(1)

if not os.path.isdir(args.origin):
    print(f"\nERROR: origin dir '{args.origin}' is not a directory")
    exit(1)

if not os.path.isdir(args.target):
    print(f"\nERROR: target dir '{args.target}' is not a directory")
    exit(1)

target_leaf = args.target.split("/")[-2]
target_parent = "/".join(args.target.split("/")[0:-2])
trash_dir = f"{target_parent}/{args.trash}/{target_leaf}/" + datetime.now().strftime("%Y-%m-%d_%H.%M-rsync")
logfile = f"{trash_dir}/rsync.log"

cli_parmas = [
    "rsync",
    "--archive",
    "--compress",
    "--partial",
    # "--progress",
    # "--verbose",
    # "--exclude=" + args.trash,
    "--delete",
    "--backup",
    "--backup-dir=" + trash_dir,
    "--itemize-changes",
    # "--delete-after",
    "--delete-delay",
]

print("This will rsync CONTENTS of dir:")
print(f"\t{args.origin}\ninto:\n\t{args.target}\n")

origin = args.origin
if args.origin[0] != "/":
    print("- Current directory: " + os.getcwd())
    origin = os.getcwd() + "/" + args.origin
if args.doit != "doit":
    cli_parmas += ["--dry-run"]
    print("- this will run in SIMULATION-MODE (to do a real run add thue ' doit' argument)\n")

cli_parmas += [origin]
cli_parmas += [args.target]

bash_command = " \\\n\t".join(cli_parmas) + f" \\\n\t>>{logfile}\n"
print("\ncommand:")
print(f"\nmkdir -p '{trash_dir}'")
print(f"\n{bash_command}")

try:
    _ = input("\n... type Ctrl+C to cancel, or ENTER to continue\n")

    os.makedirs(trash_dir, exist_ok=True)

    with open(f"{logfile}", "w") as output:
        print(bash_command, file=output)

    with open(f"{logfile}", "a") as output:

        process = subprocess.Popen(cli_parmas, stdout=output)

        while True:
            return_code = process.poll()
            if return_code is not None:
                print("\n\nRETURN CODE", return_code)
                break

except KeyboardInterrupt:
    print("Canceled")

'''
rsync_log_itemize_help:

YXcstpoguax  path/to/file
|||||||||||
`----------- the type of update being done::
 ||||||||||   <: file is being transferred to the remote host (sent).
 ||||||||||   >: file is being transferred to the local host (received).
 ||||||||||   c: local change/creation for the item, such as:
 ||||||||||      - the creation of a directory
 ||||||||||      - the changing of a symlink,
 ||||||||||      - etc.
 ||||||||||   h: the item is a hard link to another item (requires --hard-links).
 ||||||||||   .: the item is not being updated (though it might have attributes that are being modified).
 ||||||||||   *: means that the rest of the itemized-output area contains a message (e.g. "deleting").
 ||||||||||
 `---------- the file type:
  |||||||||   f for a file,
  |||||||||   d for a directory,
  |||||||||   L for a symlink,
  |||||||||   D for a device,
  |||||||||   S for a special file (e.g. named sockets and fifos).
  |||||||||
  `--------- c: different checksum (for regular files)
   ||||||||     changed value (for symlink, device, and special file)
   `-------- s: Size is different
    `------- t: Modification time is different
     `------ p: Permission are different
      `----- o: Owner is different
       `---- g: Group is different
        `--- u: The u slot is reserved for future use.
         `-- a: The ACL information changed
'''

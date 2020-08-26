#! python3

import os
import re
import stat
import json
import shlex
import argparse
import exifread
import datetime
import hashlib
from functools import partial


def dedupe(jsons_dir, files_dir, recycle_dir, dedupe_file):

    if not os.path.isdir(jsons_dir):
        raise Exception(f'Invalid dir "{jsons_dir}"')

    os.chdir(files_dir)

    os.makedirs(os.path.dirname(dedupe_file), exist_ok=True)
    with open(dedupe_file, "a") as handler:
        for bash_actions in get_files_callback(jsons_dir, r".*\.json", partial(delete_all_but_one, recycle_dir=recycle_dir)):
            handler.write(bash_actions + "\n")


def delete_all_but_one(filename, recycle_dir):

    with open(filename, "r") as f:
        info = json.load(f)

    exists_one = None
    actions = []
    info_updated = False
    for file in sorted(info["files"]):
        if os.path.exists(file) and not exists_one:
            # TODO: choose more wisely, for now keeps alphabetically-first path
            # assert exists_one stil exists when run the actions
            exists_one = f"[ -f {shlex.quote(file)} ] && "
        else:
            if os.path.exists(file):
                # fs: move to deleted (if exists)
                dst = os.path.join(recycle_dir, file)
                while os.path.exists(dst):
                    dst = "+".join(os.path.splitext(dst))
                # os.makedirs(os.path.dirname(dst), exist_ok=True)
                actions.append(f"mkdir -p {shlex.quote(os.path.dirname(dst))}")
                # os.replace(file, dst)
                actions.append(f"mv {shlex.quote(file)} {shlex.quote(dst)}")

            # json: move to deleted always
            meta = info["files"].pop(file)
            if "deleted" not in info:
                info["deleted"] = {}
            while file in info["deleted"]:
                file += "+"
            info["deleted"][file] = meta
            info_updated = True

    if info_updated:
        with open(filename, "w") as f:
            f.write(json.dumps(info, ensure_ascii=False, sort_keys=True, indent=4))

    if actions:
        return exists_one + " && ".join(actions)


def get_files_callback(path, file_pattern=".*", callback=None):
    """generates all descendant files of the path that match the file pattern"""
    for (dirpath, _, filenames) in os.walk(path):
        for filename in filenames:
            if filename != ".DS_Store" and re.match(file_pattern, filename):
                if callable(callback):
                    something = callback(os.path.join(dirpath, filename))
                    if something:
                        yield something
                else:
                    yield os.path.join(dirpath, filename)


def exec_as_main():
    path_default = os.path.expanduser("~/fotos")
    dedupe_file_default = os.path.expanduser("~/fotos.index/dedupe.sh")
    json_mirror_dir_default = os.path.expanduser("~/fotos.index")
    recycle_dir_default = os.path.expanduser("~/fotos.recycle")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "json_mirror_dir", help=f"dir with canonical matadata-json-tree [{json_mirror_dir_default}]", nargs="?", default=json_mirror_dir_default,
    )
    parser.add_argument("path", help=f"base path to index [{path_default}]", nargs="?", default=path_default)
    parser.add_argument(
        "recycle_dir", help=f"dir to move deleted files [{recycle_dir_default}]", nargs="?", default=recycle_dir_default,
    )
    parser.add_argument("dedupe_file", help=f"bash deduplicator file [{dedupe_file_default}]", nargs="?", default=dedupe_file_default)

    args = parser.parse_args()

    print(args.json_mirror_dir, args.path, args.recycle_dir, args.dedupe_file)

    dedupe(args.json_mirror_dir, args.path, args.recycle_dir, args.dedupe_file)


# test
if __name__ == "__main__":
    exec_as_main()

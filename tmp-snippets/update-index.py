#! python3

import os
import re
import json
import argparse

# from datetime import datetime
from decouple import config

# from aux import

parser = argparse.ArgumentParser()
parser.add_argument("base", help="base dir", nargs="?", default=config("base_dir"))
parser.add_argument("index", help="index dir", nargs="?", default=config("index"))
parser.add_argument("trash", help="trash dir", nargs="?", default=config("trash"))
args = parser.parse_args()

base = os.path.expanduser(args.base)
index = os.path.join(base, args.index)
trash = os.path.join(base, args.trash)


def move_if_exists(info, from,to):
                    for sub_path in list(info["files"]):
                        path = os.path.join(base_dir, sub_path)
                        print(f"file: {path}")
                        if os.path.exists(path):
                            map[path] = json_file
                            print(f"ADDED {json_file} <---- {path}")
                        elif update_deleted:
                            print(f"MUST UPDATE {json_file} DELETED FILE: {path}")
                            if "deleted" not in info:
                                info["deleted"] = {}
                            info["deleted"][sub_path] = info["files"].pop(sub_path)
                            must_update = True


# create index-map
def get_index_map(index_dir, base_dir, update_deleted=True):
    """get file:index map"""
    map = {}
    for (dirpath, _, files) in os.walk(index_dir):
        for filename in files:
            if re.match(r".+\.json$", filename):

                json_file = os.path.join(dirpath, filename)

                print(f"json_file: {json_file}")

                with open(json_file, "r") as f:
                    info = json.load(f)

                if "files" not in info:
                    print(f"NO `file` in {filename}")
                else:
                    must_update = False

                    # # check deleted
                    # for sub_path in list(info["files"]):
                    #     path = os.path.join(base_dir, sub_path)
                    #     print(f"file: {path}")
                    #     if os.path.exists(path):
                    #         map[path] = json_file
                    #         print(f"ADDED {json_file} <---- {path}")
                    #     elif update_deleted:
                    #         print(f"MUST UPDATE {json_file} DELETED FILE: {path}")
                    #         if "deleted" not in info:
                    #             info["deleted"] = {}
                    #         info["deleted"][sub_path] = info["files"].pop(sub_path)
                    #         must_update = True

                    # # check undeleted
                    # if "deleted" in info:
                    #     for sub_path in list(info["deleted"]):
                    #         path = os.path.join(base_dir, sub_path)
                    #         print(f"file: {path}")
                    #         if os.path.exists(path):
                    #             map[path] = json_file
                    #             print(f"ADDED {json_file} <---- {path}")
                    #         elif update_deleted:
                    #             print(f"MUST UPDATE {json_file} DELETED FILE: {path}")
                    #             if "deleted" not in info:
                    #                 info["deleted"] = {}
                    #             info["deleted"][sub_path] = info["deleted"].pop(sub_path)
                    #             must_update = True

                    # if must_update:
                    #     with open(json_file, "w") as f:
                    #         json.dump(info, f, ensure_ascii=False, sort_keys=True, indent=4)

    return map


map = get_index_map(index)


with open(f"{index}/debug.json", "w") as f:
    json.dump(map, f, ensure_ascii=False, sort_keys=True, indent=4)


# foreach dir in base
# except index|trash
# except file in index-map
# create json @index

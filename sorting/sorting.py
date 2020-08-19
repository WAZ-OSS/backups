#! python3

import os
import re
import stat
import json
import argparse
import exifread
import datetime
import hashlib


EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
GPS_DATETIME_FORMAT = "%Y:%m:%d [%H, %M, %S]"
REASONABLE_MIN_DATE = datetime.datetime(2000, 1, 1)
REASONABLE_MAX_DATE = datetime.datetime.today()
BLOCK_SIZE = 65536
exifSample = None
exifSampleFile = os.path.dirname(os.path.realpath(__file__)) + "/sorting.exif.json"


def create_index(a_dir, csv_file, file_pattern=".*", json_mirror_dir=None):

    if not os.path.isdir(a_dir):
        raise Exception(f'Invalid target dir "{a_dir}"')

    os.chdir(a_dir)  # para que las rutas en el indice sean relativas al basedir indexado

    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    with open(csv_file, "a") as handler:
        for info in get_files_callback(".", file_pattern, get_info):
            handler.write(csv_fields(info) + "\n")
            if json_mirror_dir:
                update_metadata_json(info, json_mirror_dir)

    # TODO: sort && deduplicate csv_file


def csv_fields(info, separator="\t"):
    """returns only fields used in json-csv"""

    fields = [info["files"][0].replace(info["canonical"], "CANONICAL"), info["canonical"]]

    return separator.join(fields)


def update_metadata_json(info, json_mirror_dir=None):
    """creates mirror_dir/canonical.json with info json"""
    metadata_json_path = os.path.join(json_mirror_dir, info["canonical"]) + ".json"
    if os.path.exists(metadata_json_path):
        with open(metadata_json_path, "r") as old:
            files = json.load(old)["files"]
            if info["files"][0] not in files:
                files.append(info["files"][0])
            info["files"] = files
    os.makedirs(os.path.dirname(metadata_json_path), exist_ok=True)
    info.pop("canonical")
    with open(metadata_json_path, "w") as f:
        json.dump(info, f, ensure_ascii=False, sort_keys=True, indent=4)


def get_files_callback(path, file_pattern=".*", callback=None):
    """generates all descendant files of the path that match the file pattern"""
    for (dirpath, _, filenames) in os.walk(path):
        for filename in filenames:
            if filename != ".DS_Store" and re.match(file_pattern, filename):
                if callable(callback):
                    yield callback(os.path.join(dirpath, filename))
                else:
                    yield os.path.join(dirpath, filename)


def get_info(filename):
    """Get metadata from file (exif,fs,hash)"""

    info = {}

    tmp = os.stat(filename)
    info["mtime"] = datetime.datetime.utcfromtimestamp(tmp[stat.ST_MTIME]).strftime("%Y-%m-%d %H:%M:%S")
    info["ctime"] = datetime.datetime.utcfromtimestamp(tmp[stat.ST_CTIME]).strftime("%Y-%m-%d %H:%M:%S")
    info["md5"] = get_hash(filename, "md5")
    info["size"] = tmp[stat.ST_SIZE]

    exif = get_exif(filename)
    if bool(exif):

        info.update(exif)

    if filename.startswith("./"):
        filename = filename[2:]
    info["files"] = [filename]

    # canonical default: no-exif/ext/hash.ext
    ext = filename.split(".")[-1].lower()
    info["canonical"] = f"no-exif/{ext}/{info['md5']}.{ext}"
    # canonical exif: Y/m/d/Ymd_HIS.md5.ext
    if "time_exif_path" in info:
        info["canonical"] = f"{info['time_exif_path']}.{info['md5']}.{ext}"
        info.pop("time_exif_path")
    # canonical GPS: Y/m/d/Ymd_HIS.md5.ext
    if "time_gps_path" in info:
        info["canonical"] = f"{info['time_gps_path']}.{info['md5']}.{ext}"
        info.pop("time_gps_path")

    return info


def get_exif(filename, stop_tag=None):
    """get exif exif data (if exists)"""
    global exifSample, exifSampleFile

    exif = {}

    with open(filename, "rb") as f:
        tags = exifread.process_file(f, stop_tag=stop_tag)

    if not bool(tags):
        return {}

    tagsp = {t: v.printable.strip() for t, v in tags.items() if hasattr(v, "printable") and v.printable.strip() != ""}

    if exifSample is None:
        try:
            with open(exifSampleFile, "r") as f:
                exifSample = json.load(f)
        except Exception:
            exifSample = {}

    exifSampleUpdated = False
    to_index = {}
    for tag in tagsp:
        if f"# {tag}" in exifSample:
            pass
        elif tag in exifSample and "->" in exifSample[tag]:
            newtag = exifSample[tag].split("->")[1]
            exif[newtag] = tagsp[tag]
        elif tag in exifSample:
            to_index[tag] = tagsp[tag]
        else:
            exifSample[tag] = tagsp[tag]
            exifSampleUpdated = True
            print(f"found new tag {tag}: {exifSample[tag][:20]}")

    for tag in exifSample:
        if tag.startswith("+ "):
            newtag = tag[2:]
            newval = exifSample[tag]
            found_any = False
            for var in re.findall("{([0-9a-z_ -]+)}", exifSample[tag], re.IGNORECASE):
                if var in tagsp:
                    found_any = True
                    newval = newval.replace("{" + var + "}", tagsp[var])
                else:
                    newval = newval.replace("{" + var + "}", "")
            if found_any:
                exif[newtag] = newval

    if exifSampleUpdated:
        with open(exifSampleFile, "w") as f:
            f.write(json.dumps(exifSample, ensure_ascii=False, sort_keys=True, indent=4))
        # raise Exception("check exifSample.json rules")

    if "time_exif" in exif:
        try:
            datetimetuple = datetime.datetime.strptime(exif["time_exif"], EXIF_DATETIME_FORMAT)
            exif["time_exif"] = datetimetuple.strftime("%Y-%m-%d %H:%M:%S")
            exif["time_exif_path"] = datetimetuple.strftime("%Y/%m/%d/%Y%m%d_%H%M%S")
            if not (REASONABLE_MIN_DATE <= datetimetuple <= REASONABLE_MAX_DATE):
                print(f"[RANGE] time_e: {exif['time_exif']} @{filename}")
        except ValueError:
            print(f"[WARN] time_e: {exif['time_exif']} @{filename}")

    if "time_gps" in exif:
        try:
            datetimetuple = datetime.datetime.strptime(exif["time_gps"], GPS_DATETIME_FORMAT)
            exif["time_gps"] = datetimetuple.strftime("%Y-%m-%d %H:%M:%S")
            if REASONABLE_MIN_DATE <= datetimetuple <= REASONABLE_MAX_DATE:
                exif["time_gps_path"] = datetimetuple.strftime("%Y/%m/%d/%Y%m%d_%H%M%S")
            else:
                print(f"[RANGE] time_g: {exif['time_gps']} @{filename}")
        except ValueError:
            print(f"[WARN] time_g: {exif['time_gps']} @{filename}")

    if "EXIF DateTimeOriginal" in tagsp:
        if "EXIF DateTimeDigitized" in tagsp and tagsp["EXIF DateTimeDigitized"] != tagsp["EXIF DateTimeOriginal"]:
            print("[WARN?] DateTimeOriginal != DateTimeDigitized", tagsp["EXIF DateTimeOriginal"], tagsp["EXIF DateTimeDigitized"])
        if "Image DateTime" in tagsp and tagsp["Image DateTime"] != tagsp["EXIF DateTimeOriginal"]:
            print("[WARN?] DateTimeOriginal != Image DateTime", tagsp["EXIF DateTimeOriginal"], tagsp["Image DateTime"])

    exif["~"] = to_index
    # exif["~1"] = tagsp

    return exif


def get_hash(filename, algo):
    """
  Calculate hash from file contents.
    Algorithms_guaranteed:
      sha1 sha224 sha256 sha384 sha512
      sha3_224 sha3_256 sha3_384 sha3_512
      shake_128 shake_256
      blake2s blake2b
      md5
  """
    file_hash = getattr(hashlib, algo)()
    with open(filename, "rb") as f:
        fb = f.read(BLOCK_SIZE)
        while len(fb) > 0:
            file_hash.update(fb)
            fb = f.read(BLOCK_SIZE)
        return file_hash.hexdigest()


# TODO: create goups
# TODO: automate redundancy generator in DB (duplicate across multiple locations)
# TODO: automate dedupe in DB: field state{present|absent} (1 copy/location)
# TODO: cyclic executor (DB->fs)
# TODO: cyclic check hashes (DB==fs)


def exec_as_main():
    path_default = os.path.expanduser("~/fotos")
    index_default = os.path.dirname(os.path.realpath(__file__)) + "/.tmp/sort-index.tsv"
    json_mirror_dir_default = os.path.dirname(os.path.realpath(__file__)) + "/.tmp"

    parser = argparse.ArgumentParser()
    parser.add_argument("path", help=f"base path to index [{path_default}]", nargs="?", default=path_default)
    parser.add_argument("index_file", help=f"index file [{index_default}]", nargs="?", default=index_default)
    parser.add_argument(
        "json_mirror_dir",
        help=f"dir to generate canonical matadata-json-tree [{json_mirror_dir_default}]",
        nargs="?",
        default=json_mirror_dir_default,
    )
    args = parser.parse_args()

    print(f"{args.path} {args.index_file} {args.json_mirror_dir})")

    create_index(args.path, args.index_file, json_mirror_dir=args.json_mirror_dir)


# test
if __name__ == "__main__":
    exec_as_main()

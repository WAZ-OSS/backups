#! python3

import os
import re
import stat
import json
import argparse
import exifread
import datetime
import hashlib
from functools import partial
from decouple import config


EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
GPS_DATETIME_FORMAT = "%Y:%m:%d [%H, %M, %S]"
REASONABLE_MIN_DATE = datetime.datetime(2000, 1, 1)
REASONABLE_MAX_DATE = datetime.datetime.today()
BLOCK_SIZE = 65536
exifSample = None
exifSampleFile = os.path.dirname(os.path.realpath(__file__)) + "/index.exif.json"
index_cache = None


def check(a_dir, output_file, index_dir=None):
    # TODO: check index consistency:
    # - all files must exists
    # - undelete existing files marked as deleted?
    # - consolidate deleted
    pass


def create(photos_dir, index_subdir, trash_subdir, include=r".+\..+"):

    if not os.path.isdir(photos_dir):
        raise Exception(f'Invalid target dir "{photos_dir}"')

    os.chdir(
        photos_dir
    )  # para que las rutas en el indice sean relativas al basedir indexado

    index_dir = os.path.join(photos_dir, index_subdir)
    os.makedirs(index_dir, exist_ok=True)

    exclude = "|".join([index_subdir, trash_subdir, config("pattern_exclude")])

    with open(os.path.join(index_dir, config("index_log_file")), "a") as handler:
        for info in get_files_callback(
            ".",
            partial(get_info, index_dir=index_dir),
            include=include,
            exclude=exclude,
        ):
            handler.write(csv_fields(info) + "\n")
            update_metadata_json(info, index_dir)

    # TODO: sort && deduplicate index_log


def csv_fields(info, separator="\t"):
    """returns only fields used in json-csv"""

    fields = [
        info["filename"].replace(info["canonical"], "CANONICAL"),
        info["canonical"],
    ]

    return separator.join(fields)


def merge(a, b):
    "merges b into a"
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key])
            elif isinstance(a[key], list) and isinstance(b[key], list):
                a[key].extend(b[key])
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a


def update_metadata_json(info, json_mirror_dir=None):
    """creates mirror_dir/canonical.json with info json"""
    metadata_json_path = os.path.join(json_mirror_dir, info["canonical"]) + ".json"

    info["files"] = {info.pop("filename"): {"mtime": info.pop("mtime")}}

    if os.path.exists(metadata_json_path):
        with open(metadata_json_path, "r") as old:
            merge(info, json.load(old))

    os.makedirs(os.path.dirname(metadata_json_path), exist_ok=True)
    info.pop("canonical")
    with open(metadata_json_path, "w") as f:
        json.dump(info, f, ensure_ascii=False, sort_keys=True, indent=4)


def get_files_callback(path, callback=None, include=".*", exclude=None):
    """generates all descendant files of the path that match the file pattern"""
    for (dirpath, _, filenames) in os.walk(path):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if exclude and re.match(exclude, full_path, re.IGNORECASE):
                next
            if re.match(include, full_path):
                if callable(callback):
                    something = callback(full_path)
                    if something:
                        yield something
                else:
                    yield full_path


def get_info(filename, index_dir):
    """Get metadata from file (exif,fs,hash)"""

    if is_already_indexed(filename, index_dir):
        # this is to avoid OneDrive-files-onDemean(R) redownload de file if is on the cloud
        # TODO: make some more checking? like same mtime - check if it is available when file is online
        # print("[INFO] already indexed: ", filename)
        return None

    info = {}

    tmp = os.stat(filename)
    info["mtime"] = datetime.datetime.utcfromtimestamp(tmp[stat.ST_MTIME]).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    info["md5"] = get_hash(filename, "md5")
    info["size"] = tmp[stat.ST_SIZE]

    exif = get_exif(filename)
    if bool(exif):

        info.update(exif)

    if filename.startswith("./"):
        filename = filename[2:]
    info["filename"] = filename

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


def is_already_indexed(filename, index_dir):
    """mostly inneficient search of filename in the index pool"""
    global index_cache
    if not index_cache:
        index_cache = populate_index_cache(index_dir)

    if filename.startswith("./"):
        filename = filename[2:]

    return filename in index_cache


def populate_index_cache(index_dir):
    result = {}
    for files in get_files_callback(
        index_dir, callback=get_files_field, include=".*\\.json"
    ):
        result.update(files)

    return result


def get_files_field(json_file):

    files = {}
    with open(json_file, "r") as f:
        info = json.load(f)

    for filename in info["files"]:
        files[filename] = json_file

    # for filename in info["deleted"]:
    # if it was deleted and now it is copied there again
    # ...maybe has changed, so consider it a not indexed

    return files


def get_exif(filename, stop_tag=None):
    """get exif exif data (if exists)"""
    global exifSample, exifSampleFile

    exif = {}

    with open(filename, "rb") as f:
        tags = exifread.process_file(f, stop_tag=stop_tag)

    if not bool(tags):
        return {}

    tagsp = {
        t: v.printable.strip()
        for t, v in tags.items()
        if hasattr(v, "printable") and v.printable.strip() != ""
    }

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
            f.write(
                json.dumps(exifSample, ensure_ascii=False, sort_keys=True, indent=4)
            )
        # raise Exception("check exifSample.json rules")

    if "time_exif" in exif:
        try:
            datetimetuple = datetime.datetime.strptime(
                exif["time_exif"], EXIF_DATETIME_FORMAT
            )
            exif["time_exif"] = datetimetuple.strftime("%Y-%m-%d %H:%M:%S")
            exif["time_exif_path"] = datetimetuple.strftime("%Y/%m/%d/%Y%m%d_%H%M%S")
            if not (REASONABLE_MIN_DATE <= datetimetuple <= REASONABLE_MAX_DATE):
                print(f"[RANGE] time_e: {exif['time_exif']} @{filename}")
        except ValueError:
            print(f"[WARN] time_e: {exif['time_exif']} @{filename}")

    if "time_gps" in exif:
        try:
            datetimetuple = datetime.datetime.strptime(
                exif["time_gps"], GPS_DATETIME_FORMAT
            )
            exif["time_gps"] = datetimetuple.strftime("%Y-%m-%d %H:%M:%S")
            if REASONABLE_MIN_DATE <= datetimetuple <= REASONABLE_MAX_DATE:
                exif["time_gps_path"] = datetimetuple.strftime("%Y/%m/%d/%Y%m%d_%H%M%S")
            else:
                print(f"[RANGE] time_g: {exif['time_gps']} @{filename}")
        except ValueError:
            print(f"[WARN] time_g: {exif['time_gps']} @{filename}")

    if "EXIF DateTimeOriginal" in tagsp:
        if (
            "EXIF DateTimeDigitized" in tagsp
            and tagsp["EXIF DateTimeDigitized"] != tagsp["EXIF DateTimeOriginal"]
        ):
            print(
                "[WARN?] DateTimeOriginal != DateTimeDigitized",
                tagsp["EXIF DateTimeOriginal"],
                tagsp["EXIF DateTimeDigitized"],
            )
        if (
            "Image DateTime" in tagsp
            and tagsp["Image DateTime"] != tagsp["EXIF DateTimeOriginal"]
        ):
            print(
                "[WARN?] DateTimeOriginal != Image DateTime",
                tagsp["EXIF DateTimeOriginal"],
                tagsp["Image DateTime"],
            )

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

import os
import exifread
import datetime
import hashlib
import shutil
import pathlib


DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"
BLOCK_SIZE = 65536
INDEX_FILE = "index.tsv"


def walk_through_files(path, file_extensions=["jpg", "jpeg"]):
    """generates all descendant files of the path parameter filter by file extensions (case insensitive)"""
    for (dirpath, _, filenames) in os.walk(path):
        for filename in filenames:
            for extension in file_extensions:
                if filename.lower().endswith(extension):
                    yield os.path.join(dirpath, filename)


def get_tags(filename, stop_tag=None):
    """get exif tags data (if exists)"""
    with open(filename, "rb") as f:
        return exifread.process_file(f, stop_tag=stop_tag)


def get_hash(filename, algo="md5"):
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


def get_canonical_path(filename):
    """Get desired file path based on exif data (or none)"""
    tags = get_tags(filename, "DateTime")
    if "Image DateTime" in tags:
        try:
            image_datetime = f"{tags['Image DateTime']}"
            t = datetime.datetime.strptime(image_datetime, DATETIME_FORMAT)
            _, ext = os.path.splitext(filename)
            return t.strftime("%Y/%m/%d/%Y%m%d_%H%M%S.") + get_hash(filename) + ext.lower()
        except ValueError as err:
            print(f'EXIF[Image DateTime]="{image_datetime}" invalid format ({DATETIME_FORMAT})')
            raise err
    else:
        # TODO: sort by file modified timestamp
        # TODO: Create alternative tool to inject file timestamp to exif?
        raise Exception(f'missing EXIF datetime in "{filename}"')


def log_to_index(origin_dir, target_dir, origin, target):
    """
  Logs sorting to the index.
  The index is a file containing the list of file moved as:
    target<TAB>origin
  """
    indexfile = os.path.join(target_dir, INDEX_FILE)

    relative_origin = origin[origin.startswith(origin_dir) and len(origin_dir) + 1 :]
    relative_target = target[target.startswith(target_dir) and len(target_dir) + 1 :]

    print(f"{relative_target} <- {relative_origin}")

    with open(indexfile, "at") as indexhandler:
        indexhandler.write(f"{relative_target}\t{relative_origin}\n")


def quote_posix(shell_arg):
    return "\\'".join("'" + p + "'" for p in shell_arg.split("'"))


def sort_dir(origin_dir, target_dir):
    """
  sort files in `origin_dir` moving them into `target_dir`
  """

    if not os.path.isdir(target_dir):
        raise Exception(f'Invalid target dir "{target_dir}"')

    # if os.path.realpath(origin_dir) == os.path.realpath(target_dir):
    #   raise Exception(f'origin and target dir are the same "{origin_dir}"')

    for origin in walk_through_files(origin_dir):
        try:
            relative_target = os.path.join(target_dir, get_canonical_path(origin))
            target = os.path.join(target_dir, relative_target)

            if target == origin:
                # raise Exception(f'sorting sorted files "{origin}"')
                pass
            elif os.path.exists(target):
                # logit, index, delete origin
                pass
            else:
                log_to_index(origin_dir, target_dir, origin, target)
                pathlib.Path(os.path.dirname(target)).mkdir(parents=True, exist_ok=True)
                shutil.move(origin, target)
        except Exception as e:
            print(e)
            # logit, move to 'no-exif dir'

    print("sort -u -o " + quote_posix(target_dir + "/" + INDEX_FILE) + " " + quote_posix(target_dir + "/" + INDEX_FILE))


# TODO: get fs-stat
# TODO: store metadata {all} in DB index by {hash/exif-date/fs-date/basename}
# TODO: create goups
# TODO: automate redundancy generator in DB (duplicate across multiple locations)
# TODO: automate dedupe in DB: field state{present|absent} (1 copy/location)
# TODO: cyclic executor (DB->fs)
# TODO: cyclic check hashes (DB==fs)

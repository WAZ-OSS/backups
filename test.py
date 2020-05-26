from contextlib import contextmanager
import os
import exifread
import re
import datetime
import hashlib
# conda install -c conda-forge exifread

DATETIME_FORMAT="%Y:%m:%d %H:%M:%S"
BLOCK_SIZE = 65536


def walk_through_files(path, file_extensions=['jpg','jpeg']):
  '''generates all descendant files of the path parameter filter by file extensions (case insensitive)'''
  for (dirpath, _, filenames) in os.walk(path):
    for filename in filenames:
      for extension in file_extensions:
        if filename.lower().endswith(extension):
          yield os.path.join(dirpath, filename)

def get_tags(filename):
  '''get exif tags data (if exists)'''
  with open(filename, 'rb') as f:
    return exifread.process_file(f)


def get_hash(filename, algo='md5'):
  '''
  Calculate hash from file contents.
    Algorithms_guaranteed:
      sha1 sha224 sha256 sha384 sha512
      sha3_224 sha3_256 sha3_384 sha3_512
      shake_128 shake_256
      blake2s blake2b
      md5
  '''
  file_hash = getattr(hashlib, algo)()
  with open(filename, 'rb') as f:
    fb = f.read(BLOCK_SIZE)
    while len(fb) > 0:
        file_hash.update(fb)
        fb = f.read(BLOCK_SIZE)
    return file_hash.hexdigest()


def get_canonical_path(filename):
  '''Get desired file path based on exif data (or none)'''
  tags = get_tags(filename)
  if 'Image DateTime' in tags:
    try:
      image_datetime = f"{tags['Image DateTime']}"
      t = datetime.datetime.strptime(image_datetime, DATETIME_FORMAT)
      _, ext = os.path.splitext(filename)
      return t.strftime('%Y/%m/%d/%Y%m%d_%H%M%S.') + get_hash(filename) + ext.lower()
    except ValueError as err:
        print(f'EXIF[Image DateTime]="{image_datetime}" invalid format ({DATETIME_FORMAT})')
        raise err



for fname in walk_through_files("."):
  destination = get_canonical_path(fname)
  if not destination:
    print('no valid exif DateTime')
    # logit, move to 'procceced dir/same-path'
  elif destination == fname:
    print('file is in good place')
    # logit, delete origin
  else:
    # logit, move
    print(f'move {fname} -> {destination}')




#TODO: get fs-stat
#TODO: store metadata {all} in DB index by {hash/exif-date/fs-date/basename}
#TODO: create goups
#TODO: automate redundancy generator in DB (duplicate across multiple locations)
#TODO: automate dedupe in DB: field state{present|absent} (1 copy/location)
#TODO: cyclic executor (DB->fs)
#TODO: cyclic check hashes (DB==fs)

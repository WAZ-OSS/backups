import os
import exifread


def walk_through_files(path, file_extensions=['jpg','jpeg']):
  for (dirpath, dirnames, filenames) in os.walk(path):
    for filename in filenames:
      for extension in file_extensions:
        if filename.endswith(extension):
          yield os.path.join(dirpath, filename)

def get_tags(filename):
  f = open(filename, 'rb')
  return exifread.process_file(f)


for fname in walk_through_files("."):
  print(fname)
  tags = get_tags(fname)
  for tag in tags.keys():
    print("  %s:  %s" % (tag,tags[tag]))

#TODO: get fs-stat
#TODO: get hash: md5/sha
#TODO: store metadata {all} in DB index by {hash/exif-date/fs-date/basename}
#TODO: create goups
#TODO: automate redundancy generator in DB (duplicate across multiple locations)
#TODO: automate dedupe in DB: field state{present|absent} (1 copy/location)
#TODO: cyclic executor (DB->fs)
#TODO: cyclic check hashes (DB==fs)

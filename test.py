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


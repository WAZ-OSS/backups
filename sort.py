#! python3

import argparse
from utils import sort_dir

parser = argparse.ArgumentParser()
parser.add_argument("origin_dir", help="directory where are the files to be sorted")
parser.add_argument("target_dir", help="directory where the sorted files will be moved")
args = parser.parse_args()

sort_dir(args.origin_dir, args.target_dir)

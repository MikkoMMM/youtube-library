#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
This script is for (possible) legacy users only, and will eventually be gotten rid of.
If you're new to YouTube Library, don't worry about this.

Give the location(s) of playlist info file(s) to this script, and it will
attempt to convert them to a format understood by configparser.
"""

import sys
import os

def convert(files):
    arguments = len(files) - 1
    position = 0
    while arguments >= position:
        file = files[position]
        if not os.path.isfile(file):
            print("File not found:" + file)
            print("Quitting.")
            exit(1)
        print("Converting " + file)

        position = position + 1
        newformat = "[State]\n"

        with open(file, 'r') as original:
            escaped = str.maketrans({"%": r"%%"})
            newformat += "nextup = " + original.readline().translate(escaped)
            tmpfile = original.readline().translate(escaped)
            newformat += "url = " + original.readline().translate(escaped)
            newformat += "title = " + original.readline().translate(escaped)
            newformat += "tmpfile = " + tmpfile
        with open(file, 'w') as modified:
            modified.write(newformat)

if __name__ == '__main__':
    convert(sys.argv[1:])

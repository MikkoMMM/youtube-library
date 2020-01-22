#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
This script attempts to fetch new videos to any playlists in linkdir.
The user has to specify a maximum of videos stored from a given playlist,
after which nothing is downloaded from that playlist.
"""

import os
import configparser
from convert_infofile_to_new_format import convert

# Change the following to your liking:

# Symbolic links directly to individual playlists reside here
linkdir = "/mnt/USB/_katsottavaa"

parser = configparser.ConfigParser()

for directory in os.listdir(linkdir):
    directory = linkdir + "/" + directory
    if not os.path.isdir(directory):
        continue
    infofile = directory + '/' + "info"
    if not os.path.isfile(infofile):
        print("Warning: Playlist info file not found: " + infofile)
        continue
    try:
        print("Reading " + infofile + "...")
        parser.read(infofile)
        sect = parser['State']
        print(sect['nextup'])
        print(sect['url'])
        print(sect['title'])
        print(sect['tmpfile'])
    except:
        answer = input("Not a valid info file. Do you wish to try to convert it to the new format? (y/N) ")
        if answer == "y":
            convert([infofile])
    print()

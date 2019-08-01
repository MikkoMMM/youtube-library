#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
The YouTube video library's download script.

This script takes as an argument a URL of a YouTube playlist (surrounded by
quotation marks) and starts downloading it from an index the user can then
provide or from where it left off previously. The downloads go into a directory
hierarchy (a "video library").

Usage:
  progname <url>
  progname --url=<url>
  progname -h --help

Options:
  -h --help          Show this screen.
  --url=<url>        The URL of a playlist to download

"""

from __future__ import unicode_literals
from __future__ import print_function
from docopt import docopt
import youtube_dl
import sys
import io
import os
import pathlib

# Change the following to your liking:

# Where the root directory of your local video library is
rootdir = "/mnt/USB/_katsottavaa/_state"
# What to call to get the playlist's length
playlistlengthcommand = "./playlist-length.py"
# Where to store the library's state (such as how many videos have been already downloaded in a given playlist)
statedir = "/mnt/USB/_katsottavaa/_state"
# Symbolic links directly to individual playlists
playlistsdir = "/mnt/USB/_katsottavaa"

# The script itself begins now.
infofile = ".info"


class YoutubeDlLogger(object):
    """
    A logger for use  in youtube-dl's options
    """

    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


def youtube_dl_hook(d):
    # Display the percentage downloaded
    if d['status'] == 'downloading' and d['_percent_str']:
        sys.stdout.write('\r' + d['_percent_str'])
        sys.stdout.flush()

    # Download finished
    if d['status'] == 'finished':
        print()
        print('Done downloading, now converting ...')


def get_playlist_info(url):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, process=False)


def get_playlist_destination(url, outtmpl, restrictfilenames):
    """
    Get where youtube-dl would save the playlist's first item
    :param url: The URL of the playlist
    :param outtmpl: The file name template that youtube-dl uses
    :param restrictfilenames: Whether to sanitize extraneous characters from the file name
    :return: Path for where the playlist's first video would be downloaded
    """
    # Hack: temporarily redirect stdout
    stdout = sys.stdout
    sys.stdout = io.StringIO()
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": restrictfilenames,
        "simulate": True,
        'outtmpl': outtmpl,
        'playlist_items': '1',
        'forcefilename': True,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    raw_output = sys.stdout.getvalue()
    sys.stdout = stdout
    return raw_output.rstrip('\n')


if __name__ == '__main__':
    arguments = docopt(__doc__)
    url = arguments['<url>'] or arguments['--url']

    videodir = get_playlist_destination(url, '%(uploader)s/%(playlist)s', True)
    dldir = rootdir + '/' + videodir
    infofile = statedir + '/' + videodir + ".info"
    uploaderinfofile = os.path.dirname(statedir + '/' + videodir) + "/channelinfo"

    # Create the playlist's directory
    pathlib.Path(statedir + '/' + videodir).mkdir(parents=True, exist_ok=True)

    # Get the playlist's entries from youtube-dl
    playlist_info = get_playlist_info(url)

    if 'entries' in playlist_info:
        entries = list(playlist_info['entries'])
        playlist_len = len(entries)
    else:
        print("No videos were found in the playlist.")
        exit(1)

    # Create the channelinfo file
    if not os.path.isfile(uploaderinfofile) and 'uploader' in playlist_info:
        uploaderinfofile_handle = open(uploaderinfofile, 'w')
        uploaderinfofile_handle.write(youtube_dl.utils.sanitize_filename(playlist_info['uploader']) + '\n')
        uploaderinfofile_handle.close()

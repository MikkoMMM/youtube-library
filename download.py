#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
The YouTube video library's download script.

This script takes as an argument a URL of a YouTube playlist (surrounded by
quotation marks) and starts downloading it from an index the user can then
provide or from where it left off previously. The downloads go into a directory
hierarchy (a "video library").

The defaults (such as where to download, the temporary directory used, and the options for chopping videos)
are currently hardcoded and can only be modified by modifying the download script itself. Sorry for the inconvenience.

Usage:
  progname [options] <url>
  progname [options] --url=<url>
  progname -h --help

Options:
  -h --help                  Show this screen
  --url=<url>                The URL of a playlist to download
  --notmp                    Download directly to the the final destination
  --nomove                   The "opposite" of the above: do not move files from the temporary directory
  --chopafter=<duration>     Minimum length of video in minutes to start chopping up.
                             Alternatively, ffmpeg's duration syntax can be used instead of minutes.
                             The default is 30 minutes.
                             If set to <=0, the functionality is disabled.
  --choplength=<duration>    Chopped up video's segment size in minutes.
                             Alternatively, ffmpeg's duration syntax can be used instead of minutes.
                             The default is 20 minutes.
                             If set to <=0, the functionality is disabled.

"""

from __future__ import unicode_literals
from __future__ import print_function
from docopt import docopt
import youtube_dl
import sys
import io
import os
import pathlib
from pathlib import Path
import shutil
import subprocess

# Change the following to your liking:

# Where the root directory for storing finished downloads is
# The final location for the videos is under rootdir in a directory hierarchy "uploader/playlistname"
rootdir = "/mnt/USB/_katsottavaa/_state"
# Where to store the library's state (such as how many videos have been already downloaded in a given playlist)
statedir = "/mnt/USB/_katsottavaa/_state"
# Symbolic links directly to individual playlists reside here
linkdir = "/mnt/USB/_katsottavaa"
# Place to store unfinished downloads
tmpdir = str(Path.home()) + "/tmp"
# Minimum length of video in minutes to start chopping up
chopafter = 30
# Chopped up video's segment size in minutes
choplength = 20


# The script itself begins now.
infofile_loc = ".info"
videodir = ""
logfile = rootdir + "/log.txt"


class YoutubeDlLogger(object):
    """
    A logger for use  in youtube-dl's options
    """

    def debug(self, msg):
        with open(logfile, "a") as log:
            if msg.startswith("[ffmpeg] Merg"):
                # Store the temporary video file's location for future use
                replace_second_line(infofile_loc, msg[31:-1])
                print("Merging video and audio")
            log.write(msg + '\n')

    def warning(self, msg):
        with open(logfile, "a") as log:
            log.write(msg + '\n')

    def error(self, msg):
        with open(logfile, "a") as log:
            log.write(msg + '\n')
        print(msg)


def youtube_dl_hook(d):
    # Display the percentage downloaded
    if d['status'] == 'downloading':
        if 'total_bytes' in d:
            percent = d['downloaded_bytes'] / d['total_bytes']
        elif 'total_bytes_estimate' in d:
            percent = d['downloaded_bytes'] / d['total_bytes_estimate']
        else:
            percent = 0
            print("No total byte count available")

        # 100.0% of 3.31MiB at 10.97MiB/s ETA 00:00

        sys.stdout.write('\r' + "{:.1%}".format(percent))
        sys.stdout.flush()

    # Download finished
    if d['status'] == 'finished':
        print()


def get_playlist_info(url):
    """
    Use the extract_info method from youtube-dl on a playlist
    :param url: The playlist's URL
    :return: The data structure returned by youtube-dl's extract_info
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, process=False)


def replace_first_line(src_filename, replacement_line):
    with open(src_filename, 'r') as original:
        first_line, remainder = original.readline(), original.read()
    with open(src_filename, 'w') as modified:
        modified.write(replacement_line + '\n' + remainder)


def replace_second_line(src_filename, replacement_line):
    with open(src_filename, 'r') as original:
        first_line, second_line, remainder = original.readline(), original.readline(), original.read()
    with open(src_filename, 'w') as modified:
        modified.write(first_line + replacement_line + '\n' + remainder)


def download(playlist_info):
    playlist_len = 0
    if 'entries' in playlist_info:
        entries = list(playlist_info['entries'])
        # Add a placeholder entry to the beginning so we'll be handling data only in the "human-readable" format
        playlist_len = len(entries)
        entries.insert(0, 0)
    else:
        print("No videos were found in the playlist.")
        exit(1)

    quicklink_to_playlist = linkdir + '/' + youtube_dl.utils.sanitize_filename(playlist_info['title'], True)
    if not os.path.exists(quicklink_to_playlist):
        os.symlink(statedir + '/' + videodir, quicklink_to_playlist)
    quicklink_to_infofile = statedir + '/' + videodir + "/info"
    if not os.path.exists(quicklink_to_infofile):
        os.symlink(infofile_loc, quicklink_to_infofile)

    with open(infofile_loc, 'r') as infofile_read:
        index = int(infofile_read.readline().rstrip())

    if index > 0:
        step = 1
        if index > playlist_len:
            print("Nothing to download. (Requested index to download " + str(index) +
                  " is greater than the playlist's length " + str(playlist_len) + ".)")
            exit(1)
    elif index < 0:
        step = -1
        if index <= -playlist_len:
            print("Nothing to download. (Requested index to download " + str(index) +
                  " is already at the start of the playlist.)")
            exit(1)
    else:
        print("Sorry. Download index 0 currently does nothing.")
        exit(1)

    entry = entries[index]
    howmany = int(input("How many videos to download [1]? Next up: " + entry['title'] + '\n') or 1)
    end = index + (howmany - 1) * step

    if end > playlist_len:
        end = playlist_len
        print("Corrected the end value to the end of the playlist")
        print()
    elif end <= -playlist_len:
        end = -playlist_len + 1
        print("Corrected the end value to the start of the playlist")
        print()

    i = index
    while (step > 0 and i <= end) or (step < 0 and i >= end):
        entry = entries[i]

        filenamestart = youtube_dl.utils.sanitize_filename(format(abs(i), '04d') + '_' + entry['title'], True)

        print("\n=== (" + str(i) + '/' + str(end) + ") Downloading " + entry['title'] + " ===")
        escaped = str.maketrans({"%":  r"%%"})
        ydl_opts = {
            "restrictfilenames": True,
            "nooverwrites": True,
            "writedescription": True,
            "writethumbnail": True,
            "writesubtitles": True,
            "continuedl": True,
            "noprogress": True,
            "subtitleslangs": ['en', 'fi'],
            'outtmpl': tmpdir + '/' + filenamestart.translate(escaped) + ".%(ext)s",
            'logger': YoutubeDlLogger(),
            'progress_hooks': [youtube_dl_hook],
            'postprocessors': [
                {'key': 'FFmpegMetadata'},
                {'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'},
                {'key': 'FFmpegEmbedSubtitle'},
            ],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([entry['url']])

        descfile = tmpdir + '/' + filenamestart + ".description"
        with open(descfile, 'r') as original:
            data = original.read()
        with open(descfile, 'w') as modified:
            modified.write("https://www.youtube.com/watch?v=" + entry['url'] + '\n' +
                           entry['title'] + '\n\n---\n\n' + data)

        with open(infofile_loc, 'r') as fp:
            first_line, lastvideoloc = fp.readline(), fp.readline().rstrip()

        if os.path.isfile(lastvideoloc) and chopafter > 0 and choplength > 0:
            print("Slicing the video up into chunks")
            segmout = subprocess.run(
                ["sh", "video-segmenter.sh", "-s", str(choplength), "-m", str(chopafter), "-r", str(lastvideoloc)],
                capture_output=True, text=True)
            print(segmout.stdout)
            print(segmout.stderr)

        if not nomove:
            # Move files from the temporary directory
            print("Moving downloaded files to the final directory")
            for filename in os.listdir(tmpdir):
                if filename.startswith(filenamestart):
                    org_fp = os.path.join(tmpdir, filename)
                    new_fp = os.path.join(dldir, filename)
                    shutil.move(org_fp, new_fp)

        i += step
        replace_first_line(infofile_loc, str(i))


if __name__ == '__main__':
    """
    This is where the script's execution starts.
    It contains things to do prior to downloading.
    """
    arguments = docopt(__doc__)
    url = arguments['<url>'] or arguments['--url']
    nomove = arguments['--nomove']
    chopafter = int(arguments['--chopafter'] or chopafter)
    choplength = int(arguments['--choplength'] or choplength)

    print("Playlist information loading...")

    # Get the playlist's entries from youtube-dl
    playlist_info = get_playlist_info(url)

    # TODO: The url parameter should also accept a playlist info file and therefore be able to skip this test
    videodir = youtube_dl.utils.sanitize_filename(playlist_info['uploader'], True) + '/' + \
        youtube_dl.utils.sanitize_filename(playlist_info['title'], True)
    dldir = rootdir + '/' + videodir

    if arguments['--notmp']:
        tmpdir = dldir
        nomove = True

    print("Using temporary directory " + tmpdir)
    print("Using final directory " + dldir)
    print()

    infofile_loc = statedir + '/' + videodir + ".info"
    uploaderinfofile_loc = os.path.dirname(statedir + '/' + videodir) + "/channelinfo"

    if os.path.isfile(infofile_loc):
        download(playlist_info)
    else:
        # The playlist's directory doesn't exist. Create it with some feedback from the user.
        index = int(input("This is a new playlist. Start downloading from which index? \
Negative values are from the end of the playlist. [1] ") or 1)

        # Create the state directory
        pathlib.Path(statedir + '/' + videodir).mkdir(parents=True, exist_ok=True)

        # Create the channelinfo file
        if 'uploader' in playlist_info:
            uploaderinfofile_handle = open(uploaderinfofile_loc, 'w')
            uploaderinfofile_handle.write(playlist_info['uploader'] + '\n')
            uploaderinfofile_handle.write(playlist_info['uploader_url'] + '\n')
            uploaderinfofile_handle.close()

        # Create the download directory and the playlist info file
        pathlib.Path(dldir).mkdir(parents=True, exist_ok=True)
        with open(infofile_loc, 'w') as infofile:
            infofile.write(str(index) + '\n\n')
            infofile.write("https://www.youtube.com/playlist?list=" + playlist_info['id'] + '\n')
            infofile.write(playlist_info['title'] + '\n')

        download(playlist_info)

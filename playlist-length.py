#! /usr/bin/env python3
import youtube_dl
import sys

def calculate_length(url):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        playlist_info = ydl.extract_info(url, process=False)
    return len(list(playlist_info['entries']))

def main(url):
    print(calculate_length(url))
    
if __name__ == "__main__":
    main(sys.argv[1])

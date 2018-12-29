# About
This is a collection of scripts to download and maintain a local library of YouTube videos.

Currently it's built around downloading playlists (in whole or in part). They are further organized into directories by the uploader's nickname. The scripts use a "state" directory to keep track of how many videos have been downloaded from each playlist, even after the videos themselves are deleted.

# Prerequisites
* youtube-dl
* bash
* Python 3
* A method of user interaction from the following options:
  * KDialog (tested with KDE Plasma 5)

# Usage
## download.sh
Let's suppose you wanted to download the "15 second search tips" playlist by Google to your computer. You would then get the playlist's URL and call download.sh like this:

    $ ./download.sh "https://www.youtube.com/playlist?list=PLB3A7CCFD7CD5CF09"
    
    === (1/1) Downloading /home/mikko/_katsottavaa/Google/15_second_search_tips/0001_15_second_search_tip_-_Weather.mp4 ===
    WARNING: fi subtitles not available for i6_Xi5H_3Pg
    WARNING: Requested formats are incompatible for merge and will be merged into mkv.

It's a good practice to put the URL in quotation marks in case the URL has any special characters that might get interpreted by bash first.

After issuing the command, it should pop up a dialog asking for which index to start downloading from. If you want to download from the beginning of the playlist, just answer 1 (the default).

Next, it will ask you how many videos you want to download. 1 would now refer to only the first video in the playlist (the index you gave previously). If you answer with a huge number, such as 9999, it should download each video in the playlist. In the popup you'll also see where it's downloading the videos. This is currently configured in variables at the beginning of the scripts.

Now the script should download as many videos as you asked for starting from the index you gave it. Unless there's an error, it shouldn't bother you again with popups but it will still output information to bash and a log file.

The download.sh script understands also URLs that are midway through a playlist. For example this would also work:

    ./download.sh "https://www.youtube.com/watch?v=B9MPLboJM4c&t=0s&index=8&list=PLB3A7CCFD7CD5CF09"

## check-for-new-videos-in-downloaded-playlists.sh
As its name suggests, the script will go through all of the playlists in your video library and display what playlist it is referring to, how many videos it has downloaded and the total number of videos in that playlist.

Usage:

    $ ./check-for-new-videos-in-downloaded-playlists.sh
    Google
    15 second search tips
    1 out of 17 downloaded.

# Auxiliary scripts
## playlist-length.py
Returns how many videos are in the playlist it is given as an argument

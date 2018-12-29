#!/bin/bash
#set -x

# Change the following to your liking:

# Where the root directory of your local video library is
#rootdir="$HOME/_katsottavaa"
# What to call to get the playlist's length
playlistlengthcommand="python $HOME/scripts/youtube-library/playlist-length.py"
# Where to store the library's state (such as how many videos have been already downloaded in a given playlist)
statedir="$HOME/_katsottavaa_state"



# The script itself begins now.
infofile_ending=".info"


trap cleanquit SIGHUP SIGINT SIGQUIT SIGABRT

# Cleans up and quits.
# Argument 1: Exit code
cleanquit()
{
  echo "Cleaning up and quitting."
  exit "${1}"
}

playlist_info_files=$(find "${statedir}/" -name "*${infofile_ending}")

while read -r infofile; do
    uploaderinfofile="$(dirname "${infofile}")/channelinfo"
    downloadedamount=$(($(sed '1q;d' "${infofile}") - 1))
    url=$(sed '2q;d' "${infofile}")
    playlist_name=$(sed '3q;d' "${infofile}")
    channelname=$(sed '1q;d' "${uploaderinfofile}")
    playlist_length="$(${playlistlengthcommand} "${url}")"
    
    echo "${channelname}"
    echo "${playlist_name}"
    if [[ "${downloadedamount}" -gt "$((playlist_length+1))" ]]; then
        end="$((playlist_length+1))"
        echo "WARNING: The left-off index ${downloadedamount} is larger than the playlist's length plus one, ${end}."
    else
        echo "${downloadedamount} out of ${playlist_length} downloaded."
    fi
    echo
done <<< "${playlist_info_files}"

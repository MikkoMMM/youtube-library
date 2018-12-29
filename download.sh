#!/bin/bash
#set -x

# This script takes as an argument a URL of a YouTube playlist (surrounded by
# quotation marks) and starts downloading it from an index the user can then
# provide or from where it left off previously. The downloads go into a video
# library.

# Change the following to your liking:

# Where the root directory of your local video library is
rootdir="$HOME/_katsottavaa"
# What to call to get the playlist's length
playlistlengthcommand="./playlist-length.py"
# Where to store the library's state (such as how many videos have been already downloaded in a given playlist)
statedir="$HOME/_katsottavaa_state"



# The script itself begins now.
dir=""
nextup=""
url="${1}"
infofile=".info"


trap cleanquit SIGHUP SIGINT SIGQUIT SIGABRT

# Cleans up and quits.
# Argument 1: Exit code
cleanquit()
{
  echo "Cleaning up and quitting."
  exit "${1}"
}

# Replaces a line in a file
# Argument 1: Line number
# Argument 2: What to replace it with
# Argument 3: In which file
editline () {
    nbroflines=$(wc -l < "${3}")
    for ((j=nbroflines; j<"${1}"; j++)); do
        echo >> "${3}"
    done
    
    line=${2//&/\\&}

    sed -i "${1}s~.*~${line}~" "${3}"
}

# Gets the filename for the video with an index the same as the parameter
update_nextup () {
    nextup=$(youtube-dl -s --get-filename --playlist-items "${1}" -o "${dir}/$(printf '%04d' "${1}")_%(title)s.%(ext)s" --restrict-filenames --no-overwrites "${url}")
}

# The playlist's directory already exists so download a video from it.
download () {
    index=$(head -1 "${infofile}")
    case "${index}" in
        ''|*[!0-9]*)
            kdialog --error "Erroneous _info file. The start index and nothing else should be on the first line."
            ;;
        *)
            playlist_length="$(${playlistlengthcommand} "${url}")"
            if [ "${index}" -gt "$((playlist_length))" ]; then
                kdialog --error "Nothing to download. (Requested index to download ${index} is greater than the playlist's length ${playlist_length}.)"
                cleanquit 1
            fi
            update_nextup "${index}"
            howmany="$(kdialog --title "How many?" --inputbox "How many videos to download? Next up: ${nextup}" "1")"
            end=$((index+howmany))
            if [[ "${end}" -gt "$((playlist_length+1))" ]]; then
                end="$((playlist_length+1))"
                echo "Corrected the end value to the end of the playlist"
                echo
            fi
            for ((i=index; i<"${end}"; i++)); do
                update_nextup "${i}"
                echo
                echo "=== (${i}/$((end-1))) Downloading ${nextup} ==="
                youtube-dl --no-progress --playlist-items "${i}" -o "${nextup}" --no-overwrites --write-description --write-annotations --write-thumbnail --add-metadata --xattrs --convert-subtitles srt --write-sub --embed-subs --sub-lang en,fi --continue "${url}" >> "${rootdir}/log.txt"
                if [ "${?}" -ne 0 ]; then
                    echo "Error downloading. Stopping."
                    break
                fi
                editline 1 "$((i+1))" "${infofile}"
            done
            ;;
    esac
}

# The playlist's directory doesn't exist. Create it with some feedback from the user.
create_directory_and_notify () {
    index="$(kdialog --title "Not in video library" --inputbox "This is a new playlist. Start downloading from which index?" "1")"
    case "${index}" in
        ''|*[!0-9]*)
            kdialog --error "I only understand a positive integer."
            ;;
        *)
            mkdir -p "${dir}"
            touch "${infofile}"
            editline 1 "${index}" "${infofile}"
            # Extract just the playlist's URL
            url=$(sed -e 's~.*list=~https://www.youtube.com/playlist?list=~' <<< "${url}" | cut -f1 -d"&")
            editline 2 "${url}" "${infofile}"
            playlistname=$(youtube-dl -s --playlist-items 1 --get-filename -o "%(playlist)s" "${url}")
            editline 3 "${playlistname}" "${infofile}"
            download
            ;;
    esac
}

videodir="$(youtube-dl -s --playlist-items 1 --restrict-filenames --get-filename -o "%(uploader)s/%(playlist)s" "${url}")"
if [ -z "${videodir}" ]; then
    echo "Could not fetch playlist"
else
    dir="${rootdir}/${videodir}"
    infofile="${statedir}/${videodir}.info"
    uploaderinfofile="$(dirname "${statedir}/${videodir}")/channelinfo"
    if [ ! -e "${uploaderinfofile}" ]; then
        mkdir -p "$(dirname "${statedir}/${videodir}")"
        youtube-dl -s --playlist-items 1 --get-filename -o "%(uploader)s" "${url}" > "${uploaderinfofile}"
    fi
    if [ -e "${infofile}" ]; then
        download
    else
        create_directory_and_notify
    fi
fi

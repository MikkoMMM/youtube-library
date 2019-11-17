#!/bin/bash
set -x

echo "$@"

# Minimum length of video in minutes to start chopping up
minlength=0


# The script itself begins now.

PROGNAME=$0
trap cleaninterrupt SIGHUP SIGINT SIGQUIT SIGABRT


# Cleans up and quits.
cleaninterrupt()
{
  cleanup 2
}


# Cleans up and quits.
# Argument 1: Exit code
cleanquit()
{
  echo "Cleaning up and quitting."
  exit "${1}"
}


usage() {
  cat << EOF >&2
Usage: $PROGNAME [OPTION]... [VIDEO]...
Chop VIDEO(s) into multiple files.

-s <segmentsize>: MANDATORY. Segment duration in minutes OR in a format
                  accepted by ffmpeg's duration syntax

                  Note that splitting may not be accurate, unless you force the
                  reference stream key-frames at the given time.

  -m <minlength>: Minimum length of a video in minutes before segmenting it is
                  considered.
              -r: After the videos have been segmented, remove the old video
                  files. There shall be no confirmations but the script should
                  stop before it gets to this point in case of an error.
              -e: Any extra arguments to ffmpeg should go between quotation
                  marks after this.
              -v: Verbose mode. Display the commands being run.

To split a file whose name starts with a '-', for example '-foo',
use one of these commands:
  $PROGNAME -- -foo

  $PROGNAME ./-foo
EOF
  exit 1
}


while getopts rvs:m:e: opt; do
  case $opt in
    (s) chunksize=$OPTARG;;
    (m) minlength=$OPTARG;;
    (r) remove=maybe;;
    (e) extraArgs=$OPTARG;;
    (v) verbose=true;;
    (*) usage
  esac
done

if [ "$verbose" ]; then
  set -x
fi

shift $((OPTIND-1))

# Segment size not specified
[ -z "$chunksize" ] && usage

if [[ "$chunksize" =~ ^[0-9]+$ ]]; then
    chunksize="${chunksize}:00"
fi

for video in "${@}"
do
    videolength=$(ffprobe -i "${video}" -show_entries format=duration -v quiet -of csv="p=0")
    if (( $(echo "$minlength <= 0 || $videolength / 60 >= $minlength" |bc -l) )); then
        extension=$([[ "$video" = *.* ]] && echo ".${video##*.}" || echo '')
        basename="${video%.*}"
        ffmpeg -i "${video}" -c copy -map 0 -segment_time "$chunksize" -f segment -loglevel warning "${basename}_%03d${extension}"
        exit_code=$?

        if [ "$exit_code" -ne 0 ]; then
            >&2 echo "Error ${exit_code} when running command: ffmpeg -i ${video} -c copy -map 0 -segment_time $chunksize -f segment -loglevel warning ${basename}_%03d${extension}"
            exit "$exit_code"
        fi
        if [ "$remove" = maybe ] ; then
            remove=true
        fi
    fi
done
if [ "$remove" = true ] ; then
    rm "$video"
fi

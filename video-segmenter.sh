#!/bin/bash
#set -x

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

-s <segmentsize>: MANDATORY. Segment duration. This is into how big of
                  chunks the video is to be chopped up in.

                  ffmpeg accepts the following duration formats:

                  [-][HH:]MM:SS[.m...]
                  HH expresses the number of hours, MM the number of minutes
                  for a maximum of 2 digits, and SS the number of seconds for
                  a maximum of 2 digits. The m at the end expresses decimal
                  value for SS.

                  or

                  [-]S+[.m...]
                  S expresses the number of seconds, with the optional decimal
                  part m.
                  
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
    (r) remove=true;;
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

#if ! [[ "$chunksize" =~ ^[0-9:]+$ ]]; then
#  echo "ERROR: Segment size should be a positive integer denoting the number of minutes per segment."
#  exit 1
#fi

for video in "${@}"
do
    extension=$([[ "$video" = *.* ]] && echo ".${video##*.}" || echo '')
    basename="${video%.*}"
    ffmpeg -i "${video}" -c copy -map 0 -segment_time "$chunksize" -f segment "${basename}_%03d${extension}"
done

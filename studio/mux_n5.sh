#!/bin/bash
# usage: mux_n5.sh <video_x025.webm> <audio.webm> <sortie.mp4> : vidéo ×4 (setpts=PTS/4), 30 i/s, + audio 1x
set -e
ffmpeg -nostdin -v error -y -i "$1" -i "$2" -map 0:v -map 1:a -vf "setpts=PTS/4,fps=30" -c:v libx264 -crf 19 -preset veryfast -pix_fmt yuv420p -c:a aac -b:a 160k -shortest "$3"

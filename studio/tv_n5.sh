#!/bin/bash
# usage: tv_n5.sh entree.mp4 sortie.mp4 debut fin "cy0 cy1" : 1280x720 pour la télé du studio.
# Recadre verticalement de cy0 à cy1 (fractions de la hauteur), centre l'image, fond flouté.
set -e
read y0 y1 <<< "$5"
ffmpeg -nostdin -v error -y -ss "$3" -to "$4" -i "$1" -filter_complex \
 "[0:v]crop=iw:ih*($y1-$y0):0:ih*$y0,setsar=1,split[a][b];[a]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,boxblur=30:3,eq=brightness=-0.15[f];[b]scale=-2:720:force_original_aspect_ratio=decrease,scale='min(iw,1280)':-2[p];[f][p]overlay=(W-w)/2:(H-h)/2,fps=30,format=yuv420p[v]" \
 -map "[v]" -map 0:a -c:v libx264 -crf 19 -preset veryfast -c:a aac -b:a 160k "$2"

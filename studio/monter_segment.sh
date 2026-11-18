#!/usr/bin/env bash
# Incruste un extrait vidéo dans la télé du studio Leonida Live, avec Sunny et un bandeau titre.
#
# Usage :
#   ./monter_segment.sh -c extrait.mp4 -o sortie.mp4 [-p sunny.mp4|sunny.png] [-t "N°12 — Lucia en prison"]
#                       [-s debut_sec] [-d duree_sec] [-v volume_extrait] [-g] [-z 0.75] [-k "Clip : @pseudo"]
#
#   -c  extrait à afficher dans la télé (obligatoire)
#   -o  fichier de sortie (obligatoire)
#   -p  Sunny : vidéo sur fond vert (avec -g) ou image PNG transparente. Sa piste audio est utilisée si présente.
#   -t  texte du bandeau en bas de l'écran
#   -s  début de l'extrait en secondes (défaut 0)
#   -d  durée du segment en secondes (défaut : durée de l'extrait)
#   -v  volume de l'extrait sous la voix de Sunny (défaut 0.25)
#   -g  la vidéo de Sunny est tournée sur fond vert (active l'incrustation chroma key)
#   -z  recadrage zoomé : ne garde que le centre de l'extrait (0.75 = 75 % de la largeur et de la hauteur)
#   -k  crédit affiché dans la télé (obligatoire pour un clip qui ne vient pas de Rockstar)
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
BG="$DIR/assets/studio.png"
# Doit correspondre à TV_* dans generer_decor.py
TV_X=820; TV_Y=150; TV_W=960; TV_H=540
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

CLIP=""; OUT=""; PRES=""; TITLE=""; START=0; DUR=""; VOL=0.25; GREEN=0; ZOOM=1; CREDIT=""
while getopts "c:o:p:t:s:d:v:gz:k:" opt; do
  case $opt in
    c) CLIP=$OPTARG ;; o) OUT=$OPTARG ;; p) PRES=$OPTARG ;; t) TITLE=$OPTARG ;;
    s) START=$OPTARG ;; d) DUR=$OPTARG ;; v) VOL=$OPTARG ;; g) GREEN=1 ;;
    z) ZOOM=$OPTARG ;; k) CREDIT=$OPTARG ;;
    *) sed -n '2,19p' "$0"; exit 1 ;;
  esac
done
[[ -n $CLIP && -n $OUT ]] || { sed -n '2,19p' "$0"; exit 1; }
[[ -f $BG ]] || python3 "$DIR/generer_decor.py"

DUR_OPT=(); [[ -n $DUR ]] && DUR_OPT=(-t "$DUR")
has_audio() { ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$1" | grep -q .; }

INPUTS=(-loop 1 -i "$BG" -ss "$START" "${DUR_OPT[@]}" -i "$CLIP")
# Extrait : mis à l'échelle et centré dans l'écran de la télé, léger effet « écran » (vignette)
CROP=""; [[ $ZOOM != 1 ]] && CROP="crop=iw*${ZOOM}:ih*${ZOOM}:(iw-iw*${ZOOM})/2:(ih-ih*${ZOOM})/2,"
FILTER="[1:v]${CROP}scale=${TV_W}:${TV_H}:force_original_aspect_ratio=decrease,pad=${TV_W}:${TV_H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,vignette=PI/6"
if [[ -n $CREDIT ]]; then
  C=${CREDIT//\\/\\\\}; C=${C//:/\\:}; C=${C//\'/\\\'}
  FILTER+=",drawtext=fontfile=${FONT}:text='${C}':fontcolor=white:fontsize=24:x=w-tw-24:y=h-44:box=1:boxcolor=black@0.6:boxborderw=8"
fi
FILTER+="[tv];"
FILTER+="[0:v][tv]overlay=${TV_X}:${TV_Y}:shortest=1[v1];"
LAST="v1"

AUDIO_SRC=()
if [[ -n $PRES ]]; then
  case "${PRES,,}" in
    *.png|*.webp) INPUTS+=(-loop 1 -i "$PRES") ;;
    *)            INPUTS+=(-stream_loop -1 -i "$PRES") ;;
  esac
  KEY=""; [[ $GREEN == 1 ]] && KEY="colorkey=0x00FF00:0.30:0.10,"
  FILTER+="[2:v]${KEY}scale=-1:820,format=rgba[sunny];"
  FILTER+="[${LAST}][sunny]overlay=60:H-h-20:shortest=0:eof_action=pass[v2];"
  LAST="v2"
  has_audio "$PRES" && AUDIO_SRC+=("[2:a]volume=1.0[a_s]")
fi

if [[ -n $TITLE ]]; then
  ESC=${TITLE//\\/\\\\}; ESC=${ESC//:/\\:}; ESC=${ESC//\'/\\\'}
  FILTER+="[${LAST}]drawbox=x=0:y=ih-110:w=iw:h=90:color=0x2A0F4A@0.9:t=fill,"
  FILTER+="drawbox=x=0:y=ih-110:w=16:h=90:color=0xFF3E9A:t=fill,"
  FILTER+="drawtext=fontfile=${FONT}:text='${ESC}':fontcolor=white:fontsize=46:x=50:y=h-88[v3];"
  LAST="v3"
fi

# Audio : extrait baissé sous la voix de Sunny
A_PARTS=(); A_LABELS=""
if has_audio "$CLIP"; then A_PARTS+=("[1:a]volume=${VOL}[a_c]"); A_LABELS+="[a_c]"; fi
if ((${#AUDIO_SRC[@]})); then A_PARTS+=("${AUDIO_SRC[@]}"); A_LABELS+="[a_s]"; fi
MAP_A=()
if ((${#A_PARTS[@]} == 2)); then
  FILTER+="$(IFS=';'; echo "${A_PARTS[*]}");${A_LABELS}amix=inputs=2:duration=first:normalize=0[aout];"
  MAP_A=(-map "[aout]")
elif ((${#A_PARTS[@]} == 1)); then
  FILTER+="${A_PARTS[0]};"; MAP_A=(-map "${A_LABELS}")
fi
FILTER=${FILTER%;}

ffmpeg -hide_banner -loglevel warning -y "${INPUTS[@]}" \
  -filter_complex "$FILTER" -map "[$LAST]" "${MAP_A[@]}" \
  -shortest -r 30 -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "Segment créé : $OUT"

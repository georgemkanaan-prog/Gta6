#!/usr/bin/env bash
# Génère la voix de toutes les séquences d'une vidéo : voix/generer_video.sh <dossier_video> <presentatrice> [prises]
# Entrée : <dossier_video>/voix/NN_*.txt (studio/extraire_voix.py)  ->  sortie : <dossier_video>/audio_<presentatrice>/NN_*.wav
set -euo pipefail
VID=$1; QUI=$2; PRISES=${3:-1}
PY=${PYTHON_TTS:-python3}
OUT="$VID/audio_$QUI"; mkdir -p "$OUT"
for t in "$VID"/voix/[0-9]*.txt; do
  w="$OUT/$(basename "${t%.txt}").wav"
  [[ -s $w ]] && { echo "déjà fait : $w"; continue; }   # reprise possible après interruption
  "$PY" "$(dirname "$0")/generer_voix.py" --texte "$t" --voix "$QUI" --prises "$PRISES" --sortie "$w" 2>&1 | grep -E "wav$|Error" || true
done
echo "Terminé : $OUT"

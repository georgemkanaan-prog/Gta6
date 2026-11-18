# Studio Leonida Live — outils de montage

Prérequis : `ffmpeg` et Python 3 avec Pillow (`pip install pillow`).

## 1. Générer le décor
```bash
python3 studio/generer_decor.py      # -> studio/assets/studio.png (déjà fourni)
```
Pour remplacer par un décor fait main (Canva, Photoshop, IA) : garder 1920×1080 et placer l'écran
de la télé à x=820, y=150, 960×540 (ou changer `TV_*` dans les deux scripts).

## 2. Créer un segment « télé dans le studio »
```bash
# Sunny tournée sur fond vert + extrait du trailer de 12 s à partir de 0:41
./studio/monter_segment.sh -c trailer2.mp4 -s 41 -d 12 \
    -p sunny_n12.mp4 -g -t "N°12 — Lucia commence en prison" -o seg_12.mp4

# Sans Sunny (voix off ajoutée au montage final)
./studio/monter_segment.sh -c capture.mp4 -t "N°4 — Les véhicules" -o seg_04.mp4
```
- L'extrait est redimensionné dans la télé, Sunny est placée en bas à gauche.
- Son : la voix de Sunny à 100 %, l'extrait à 25 % (`-v 0.4` pour l'augmenter).
- `-p` accepte aussi une image PNG transparente de Sunny (avatar fixe ou VTuber exporté).

### Extraits : règle de la chaîne
- **Trailers et vidéos officielles Rockstar** : extrait tel quel, quelques secondes.
- **Clip d'un autre créateur** : recadré au centre (`-z 0.75`, on ne voit pas les bords) **et** crédité à l'écran (`-k`).
  ```bash
  ./studio/monter_segment.sh -c clip_joueur.mp4 -s 12 -d 6 -z 0.75 -k "Clip : @pseudo" \
      -p sunny_anim.mp4 -t "N°7 — Le motel caché" -o seg_07.mp4
  ```
  Le recadrage est un choix de mise en scène ; il ne remplace pas l'accord du créateur (voir `03-droits-et-sources.md`).

## 3. Assembler la vidéo
Mettre les segments dans l'ordre du script (`videos/<n>/script.md`) dans le logiciel de montage
(CapCut, DaVinci Resolve gratuit) pour ajouter générique, plans de Sunny face caméra, textes et
musique libre de droits. Ou en ligne de commande :
```bash
printf "file '%s'\n" seg_*.mp4 > liste.txt
ffmpeg -f concat -safe 0 -i liste.txt -c copy video_finale.mp4
```

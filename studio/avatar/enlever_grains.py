#!/usr/bin/env python3
"""Efface les points de beauté / petites taches sombres sur la peau (sous le visage), sans IA :
chaque tache est détectée (plus sombre que la peau autour) puis comblée avec la peau voisine.

    python enlever_grains.py --entree sunny_taille.png --sortie sunny_taille_net.png --depuis-y 380
"""
import argparse

import cv2
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--entree", required=True); ap.add_argument("--sortie", required=True)
ap.add_argument("--depuis-y", type=int, default=380, help="le visage (au-dessus) n'est pas touché")
ap.add_argument("--seuil", type=float, default=14, help="écart de luminosité minimal d'une tache")
ap.add_argument("--masque")
a = ap.parse_args()

img = cv2.imread(a.entree)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(int)
h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
peau = ((h <= 22) | (h >= 170)) & (s > 40) & (v > 60)
peau = cv2.erode(peau.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0     # loin des bords (vêtements, cheveux)

gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
fond = cv2.medianBlur(gris.astype(np.uint8), 15).astype(np.float32)
tache = (fond - gris > a.seuil) & peau
tache[: a.depuis_y] = False

# garder les petites composantes (points), pas les ombres/plis allongés
n, lab, stats, _ = cv2.connectedComponentsWithStats(tache.astype(np.uint8))
m = np.zeros_like(tache, np.uint8)
for i in range(1, n):
    x, y, w, hh, aire = stats[i]
    if 2 <= aire <= 160 and max(w, hh) <= 18 and max(w, hh) / max(1, min(w, hh)) < 3:
        m[lab == i] = 255
m = cv2.dilate(m, np.ones((5, 5), np.uint8))
out = cv2.inpaint(img, m, 5, cv2.INPAINT_TELEA)
cv2.imwrite(a.sortie, out)
if a.masque:
    cv2.imwrite(a.masque, m)
print(a.sortie, "taches effacées :", n - 1 if n else 0, "candidates,", int((m > 0).sum()), "pixels")

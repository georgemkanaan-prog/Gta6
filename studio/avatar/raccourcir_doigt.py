#!/usr/bin/env python3
"""Raccourcit un doigt de façon déterministe : le bout (ongle + dernière phalange) de l'image d'origine est
recollé plus bas dans l'axe du doigt, sur une image où le haut du doigt a été effacé (retouche_finale.py detail --libre).

    python raccourcir_doigt.py --origine img.png --efface img_efface.png --sortie out.png \
        --bout 421,614 --vers 450,690 --longueur-bout 36 --largeur 26 --raccourci 30
"""
import argparse

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("--origine", required=True); ap.add_argument("--efface", help="image où le haut du doigt est déjà effacé ; sinon remplissage automatique (OpenCV)"); ap.add_argument("--sortie", required=True)
ap.add_argument("--bout", required=True, help="x,y de l'extrémité de l'ongle")
ap.add_argument("--vers", required=True, help="x,y d'un point plus bas sur l'axe du doigt")
ap.add_argument("--longueur-bout", type=float, default=36); ap.add_argument("--largeur", type=int, default=26)
ap.add_argument("--raccourci", type=float, default=30, help="pixels retirés à la longueur du doigt")
ap.add_argument("--bord", help="dx,dy : direction d'un bord voisin le long duquel recopier le décor")
ap.add_argument("--decal-bord", type=float, default=35)
ap.add_argument("--tissu", help="px,py,dx,dy : ligne du bord du vêtement ; dessous, le tissu est recopié depuis la droite")
a = ap.parse_args()

orig = Image.open(a.origine).convert("RGB")
T = np.array(list(map(float, a.bout.split(",")))); V = np.array(list(map(float, a.vers.split(","))))
u = (V - T) / np.linalg.norm(V - T)
if a.efface:
    eff = Image.open(a.efface).convert("RGB")
else:   # efface la partie du doigt libérée par le raccourcissement en prolongeant la peau / le tissu voisins
    import cv2
    trou = Image.new("L", orig.size, 0)
    ImageDraw.Draw(trou).line([tuple(T - u * 7), tuple(T + u * (a.raccourci + a.longueur_bout * 0.7))], fill=255, width=a.largeur + 6)
    eff = np.array(orig).copy()
    if a.bord:   # recopie le décor voisin le long d'un bord (ex. bord du maillot) : le bord reste net
        ex, ey = map(float, a.bord.split(","))
        e = np.array([ex, ey]) / np.hypot(ex, ey) * a.decal_bord
        tm = np.array(trou.filter(ImageFilter.MaxFilter(3))) > 0
        ys, xs = np.nonzero(tm)
        sx = np.clip((xs + e[0]).round().astype(int), 0, orig.width - 1)
        sy = np.clip((ys + e[1]).round().astype(int), 0, orig.height - 1)
        eff[ys, xs] = np.array(orig)[sy, sx]
        eff = Image.fromarray(eff)
    else:
        eff = cv2.inpaint(eff, np.array(trou), 9, cv2.INPAINT_TELEA)
        if a.tissu:   # sous la ligne du bord du vêtement : on recopie le tissu situé à droite (même hauteur)
            px, py, dx, dy = map(float, a.tissu.split(","))
            tm = np.array(trou.filter(ImageFilter.MaxFilter(5))) > 0
            ys, xs = np.nonzero(tm)
            sous = (ys - py) * dx - (xs - px) * dy > 0          # côté « tissu » de la ligne
            ys, xs = ys[sous], xs[sous]
            src = np.array(orig)
            eff[ys, xs] = src[ys, np.clip(xs + a.decal_bord, 0, orig.width - 1).astype(int)]
        eff = Image.fromarray(eff)
fin = T + u * a.longueur_bout
m = Image.new("L", orig.size, 0)
n = np.array([-u[1], u[0]])                       # perpendiculaire à l'axe
l0, l1 = a.largeur * 0.32, a.largeur / 2          # le bout du doigt est plus fin que sa base
haut = T + u * 5
poly = [tuple(haut + n * l0), tuple(fin + n * l1), tuple(fin - n * l1), tuple(haut - n * l0)]
ImageDraw.Draw(m).polygon(poly, fill=255)
ImageDraw.Draw(m).ellipse(tuple(np.r_[haut - l0 - u * 0, haut + l0]), fill=255)   # extrémité arrondie (ongle)
m = m.filter(ImageFilter.GaussianBlur(2))
dx, dy = (u * a.raccourci).round().astype(int)
patch = Image.new("RGB", orig.size); patch.paste(orig, (dx, dy))           # bout décalé dans l'axe
m_dec = Image.new("L", orig.size, 0); m_dec.paste(m, (dx, dy))
Image.composite(patch, eff, m_dec).save(a.sortie)
print(a.sortie, "décalage", dx, dy)

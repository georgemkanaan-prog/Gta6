#!/usr/bin/env python3
"""Cartes « guide » pour le grand écran du studio (1280x720), façon fiche : partie en haut,
3-4 mots énormes, sous-titre, icône dessinée. Aucune image de jeu.

    from cartes_guide import carte
    carte(sortie, partie="2 · LES RÉGLAGES", gros="FLOU : 0", sous="Affichage > Effets visuels", icone="oeil")
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
B = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
ROSE, CYAN, JAUNE, NUIT, VERT, ROUGE = (255, 62, 154), (33, 230, 240), (255, 214, 60), (26, 8, 48), (60, 230, 120), (240, 50, 70)
COULEURS = {"rose": ROSE, "cyan": CYAN, "jaune": JAUNE, "vert": VERT, "rouge": ROUGE}


def police(taille, chemin=XB):
    return ImageFont.truetype(chemin, taille)


def fond():
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(H):
        u = y / H
        d.line((0, y, W, y), fill=(int(26 + 40 * u), int(8 + 6 * u), int(48 + 50 * u)))
    for x in range(-W, 2 * W, 90):
        d.line((W // 2, int(H * 0.7), x, H), fill=(70, 30, 120), width=2)
    return im


def icone(d, nom, cx, cy, r, c):
    """Petites icônes vectorielles (dollar, engrenage, voiture, alerte, ok, horloge, banque, cadenas, oeil, manette, carte)."""
    w = max(6, r // 7)
    if nom == "dollar":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c, width=w)
        d.text((cx, cy + 4), "$", font=police(int(r * 1.5)), fill=c, anchor="mm")
    elif nom == "engrenage":
        for k in range(8):
            a = math.radians(k * 45)
            d.line((cx + math.cos(a) * r * 0.6, cy + math.sin(a) * r * 0.6, cx + math.cos(a) * r, cy + math.sin(a) * r), fill=c, width=w * 2)
        d.ellipse((cx - r * 0.72, cy - r * 0.72, cx + r * 0.72, cy + r * 0.72), outline=c, width=w)
        d.ellipse((cx - r * 0.25, cy - r * 0.25, cx + r * 0.25, cy + r * 0.25), fill=c)
    elif nom == "voiture":
        d.rounded_rectangle((cx - r, cy - r * 0.15, cx + r, cy + r * 0.45), 12, outline=c, width=w)
        d.polygon([(cx - r * 0.6, cy - r * 0.15), (cx - r * 0.35, cy - r * 0.6), (cx + r * 0.4, cy - r * 0.6), (cx + r * 0.65, cy - r * 0.15)], outline=c, width=w)
        for sx in (-0.55, 0.55):
            d.ellipse((cx + sx * r - r * 0.22, cy + r * 0.3, cx + sx * r + r * 0.22, cy + r * 0.74), fill=c)
    elif nom == "alerte":
        d.polygon([(cx, cy - r), (cx + r, cy + r * 0.8), (cx - r, cy + r * 0.8)], outline=c, width=w)
        d.text((cx, cy + r * 0.15), "!", font=police(int(r * 1.1)), fill=c, anchor="mm")
    elif nom == "ok":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c, width=w)
        d.line((cx - r * 0.45, cy, cx - r * 0.1, cy + r * 0.4, cx + r * 0.5, cy - r * 0.35), fill=c, width=w + 2, joint="curve")
    elif nom == "horloge":
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=c, width=w)
        d.line((cx, cy, cx, cy - r * 0.6), fill=c, width=w); d.line((cx, cy, cx + r * 0.45, cy + r * 0.2), fill=c, width=w)
    elif nom == "banque":
        d.polygon([(cx - r, cy - r * 0.35), (cx, cy - r), (cx + r, cy - r * 0.35)], fill=c)
        for k in range(4):
            x = cx - r * 0.75 + k * r * 0.5
            d.rectangle((x - r * 0.08, cy - r * 0.25, x + r * 0.08, cy + r * 0.6), fill=c)
        d.rectangle((cx - r, cy + r * 0.65, cx + r, cy + r * 0.85), fill=c)
    elif nom == "cadenas":
        d.rounded_rectangle((cx - r * 0.75, cy - r * 0.1, cx + r * 0.75, cy + r * 0.9), 10, fill=c)
        d.arc((cx - r * 0.5, cy - r * 0.9, cx + r * 0.5, cy + r * 0.2), 180, 360, fill=c, width=w)
    elif nom == "oeil":
        d.ellipse((cx - r, cy - r * 0.55, cx + r, cy + r * 0.55), outline=c, width=w)
        d.ellipse((cx - r * 0.3, cy - r * 0.3, cx + r * 0.3, cy + r * 0.3), fill=c)
    elif nom == "manette":
        d.rounded_rectangle((cx - r, cy - r * 0.45, cx + r, cy + r * 0.45), int(r * 0.4), outline=c, width=w)
        d.line((cx - r * 0.65, cy, cx - r * 0.25, cy), fill=c, width=w); d.line((cx - r * 0.45, cy - r * 0.2, cx - r * 0.45, cy + r * 0.2), fill=c, width=w)
        d.ellipse((cx + r * 0.35, cy - r * 0.2, cx + r * 0.55, cy), fill=c); d.ellipse((cx + r * 0.55, cy, cx + r * 0.75, cy + r * 0.2), fill=c)
    elif nom == "carte":
        d.polygon([(cx - r, cy - r * 0.7), (cx - r * 0.33, cy - r * 0.9), (cx + r * 0.33, cy - r * 0.7), (cx + r, cy - r * 0.9),
                   (cx + r, cy + r * 0.7), (cx + r * 0.33, cy + r * 0.9), (cx - r * 0.33, cy + r * 0.7), (cx - r, cy + r * 0.9)], outline=c, width=w)
        d.ellipse((cx - r * 0.15, cy - r * 0.2, cx + r * 0.15, cy + r * 0.1), fill=c)


def ajuster(d, texte, largeur, taille_max, chemin=XB):
    t = taille_max
    while t > 30 and d.textlength(texte, font=police(t, chemin)) > largeur:
        t -= 4
    return police(t, chemin)


def carte(sortie, partie, gros, sous="", icone_nom=None, couleur="rose", badge="GTA 6"):
    """`gros` : 1 ou 2 lignes séparées par « | » (3-4 mots énormes)."""
    c = COULEURS.get(couleur, couleur)
    im = fond(); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 104), fill=c)                                   # titre de la partie
    d.text((40, 52), partie.upper(), font=ajuster(d, partie.upper(), W - 260, 52, B), fill=NUIT, anchor="lm")
    d.rounded_rectangle((W - 190, 22, W - 30, 82), 16, fill=NUIT)           # badge du jeu
    d.text((W - 110, 52), badge, font=police(34, B), fill=c, anchor="mm")
    lignes = gros.split("|")
    zone_g = 260 if icone_nom else 60
    larg = W - zone_g - 70
    tailles = [ajuster(d, l, larg, 170 if len(lignes) == 1 else 130) for l in lignes]
    hauteur = sum(f.size for f in tailles) + 20 * (len(lignes) - 1)
    y = 380 - hauteur // 2 - (30 if sous else 0)
    calque = Image.new("RGBA", im.size, (0, 0, 0, 0)); dc = ImageDraw.Draw(calque)
    for l, f in zip(lignes, tailles):
        dc.text((zone_g, y), l, font=f, fill=(255, 255, 255), stroke_width=8, stroke_fill=NUIT)
        y += f.size + 20
    if icone_nom:
        icone(dc, icone_nom, 140, 380 - (30 if sous else 0), 85, c)
    halo = calque.filter(ImageFilter.GaussianBlur(10))
    im = im.convert("RGBA"); im.alpha_composite(halo); im.alpha_composite(calque); d = ImageDraw.Draw(im)
    if sous:
        d.rounded_rectangle((60, 590, W - 60, 680), 20, fill=NUIT, outline=c, width=4)
        d.text((W // 2, 635), sous, font=ajuster(d, sous, W - 180, 44, B), fill=JAUNE, anchor="mm")
    Path(sortie).parent.mkdir(parents=True, exist_ok=True)
    im.convert("RGB").save(sortie)
    return Path(sortie)


if __name__ == "__main__":
    import sys
    carte(sys.argv[1], "1 · L'argent au début du jeu", "VOITURES|À MOSES", "Chapitre 2 · 1 000 à 3 000 $ par voiture", "voiture", "jaune")

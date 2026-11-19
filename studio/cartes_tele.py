#!/usr/bin/env python3
"""Cartes « journal télé » affichées dans la télé du studio pendant les rubriques sans extrait du jeu.
Sortie : PNG 1280x720 dans le dossier donné.

    python cartes_tele.py videos/002-jour-de-sortie/cartes
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
ROSE, TURQ, ORANGE, NUIT, JAUNE = (255, 62, 154), (33, 212, 224), (255, 138, 61), (42, 15, 74), (255, 220, 0)
GRAS = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def f(t):
    return ImageFont.truetype(GRAS, t)


def fond(sombre=True):
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H
        c = tuple(int(NUIT[i] * (1 - k) + (ROSE[i] if not sombre else NUIT[i] // 2) * k) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    for x in range(-W, 2 * W, 80):                        # grille néon
        d.line([(W // 2, H * 0.62), (x, H)], fill=(60, 30, 110), width=2)
    return im


def bandeau(d, texte, couleur=ROSE):
    d.rectangle((0, 0, W, 110), fill=couleur)
    d.text((40, 55), texte, font=f(56), fill=(255, 255, 255), anchor="lm")


def centre(d, y, texte, taille, couleur=(255, 255, 255), contour=0):
    d.text((W // 2, y), texte, font=f(taille), fill=couleur, anchor="mm", stroke_width=contour, stroke_fill=NUIT)


def cartes(sortie: Path, illustration: Path | None):
    sortie.mkdir(parents=True, exist_ok=True)
    ill = Image.open(illustration).convert("RGB").resize((W, H)) if illustration and illustration.exists() else fond(False)

    # ouverture : programme du jour
    im = ill.filter(ImageFilter.GaussianBlur(6)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, H), fill=None); bandeau(d, "AUJOURD'HUI SUR LEONIDA LIVE")
    for i, t in enumerate(["1. L'intro venue de Nouvelle-Zélande", "2. La fête géante de YouTube", "3. Les bugs du 1er jour"]):
        d.rounded_rectangle((120, 190 + i * 150, W - 120, 300 + i * 150), 20, fill=NUIT)
        d.text((160, 245 + i * 150), t, font=f(42), fill=(255, 255, 255), anchor="lm")
    im.save(sortie / "ouverture.png")

    # saviez 1 : record
    for k, (gros, legende) in enumerate([("90 MILLIONS", "de vues en 24 h — trailer 1 (YouTube)"),
                                          ("475 MILLIONS", "de vues en 24 h — trailer 2 (toutes plateformes)")]):
        im = fond(); d = ImageDraw.Draw(im); bandeau(d, "LE SAVIEZ-VOUS ?", TURQ)
        centre(d, 340, gros, 140, JAUNE, 8); centre(d, 480, legende, 40)
        im.save(sortie / f"saviez1_{k + 1}.png")

    # flash spécial
    im = fond(); d = ImageDraw.Draw(im); bandeau(d, "FLASH SPÉCIAL", (220, 30, 40))
    centre(d, 300, "GRASSRIVERS", 90, JAUNE, 6)
    centre(d, 420, "Un habitant tente de payer", 48); centre(d, 485, "ses courses avec un alligator", 48)
    d.rectangle((0, H - 80, W, H), fill=(220, 30, 40)); d.text((30, H - 40), "EN DIRECT • LEONIDA LIVE • INFO NON VÉRIFIÉE (ET FAUSSE)",
                                                                  font=f(30), fill=(255, 255, 255), anchor="lm")
    im.save(sortie / "flash.png")

    # saviez 2 : régions
    im = ill.filter(ImageFilter.GaussianBlur(5)); d = ImageDraw.Draw(im); bandeau(d, "LE SAVIEZ-VOUS ? — LEONIDA", TURQ)
    regions = ["Vice City", "Leonida Keys", "Grassrivers", "Port Gellhorn", "Ambrosia", "Mount Kalaga"]
    for i, r in enumerate(regions):
        x, y = 90 + (i % 2) * 560, 180 + (i // 2) * 160
        d.rounded_rectangle((x, y, x + 520, y + 120), 20, fill=NUIT, outline=ROSE, width=4)
        d.text((x + 260, y + 60), r, font=f(50), fill=(255, 255, 255), anchor="mm")
    im.save(sortie / "saviez2.png")

    # saviez 3 : frise des dates
    im = fond(); d = ImageDraw.Draw(im); bandeau(d, "LE SAVIEZ-VOUS ? — LES REPORTS", TURQ)
    d.line([(140, 400), (W - 140, 400)], fill=(255, 255, 255), width=8)
    for i, (date, note, coul) in enumerate([("2025", "annonce", (180, 180, 180)), ("26 MAI 2026", "reporté", ORANGE),
                                            ("19 NOV. 2026", "SORTIE !", JAUNE)]):
        x = 230 + i * 410
        d.ellipse((x - 26, 374, x + 26, 426), fill=coul)
        d.text((x, 300), date, font=f(44), fill=coul, anchor="mm")
        d.text((x, 490), note, font=f(40), fill=(255, 255, 255), anchor="mm")
    centre(d, 620, "Plus de 10 ans après GTA 5", 46, ROSE)
    im.save(sortie / "saviez3.png")

    # fin : défi
    im = fond(); d = ImageDraw.Draw(im); bandeau(d, "LE DÉFI DE SUNNY")
    centre(d, 290, "Ton bug le plus fou", 70, JAUNE, 6); centre(d, 380, "en commentaire 👇".replace("👇", "!"), 60)
    d.rounded_rectangle((390, 500, 890, 610), 30, fill=(230, 30, 40))
    centre(d, 555, "ABONNE-TOI", 56)
    im.save(sortie / "fin.png")


if __name__ == "__main__":
    out = Path(sys.argv[1])
    cartes(out, Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    print("cartes :", sorted(p.name for p in out.glob("*.png")))

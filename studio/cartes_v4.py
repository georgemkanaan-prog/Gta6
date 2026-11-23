#!/usr/bin/env python3
"""Cartes télé de la vidéo n°4 + miniature. Usage : cartes_v4.py <dossier cartes> <image jet> <image Sunny>"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, str(Path(__file__).parent))
from cartes_tele import JAUNE, NUIT, ROSE, TURQ, W, H, bandeau, centre, f, fond  # noqa: E402

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
ROUGE = (220, 30, 40)

def liste(titre, items, nom, couleur=ROSE, taille=40):
    im = fond(); d = ImageDraw.Draw(im); bandeau(d, titre, couleur)
    for i, t in enumerate(items):
        y = 150 + i * (540 // len(items))
        d.rounded_rectangle((70, y, W - 70, y + 540 // len(items) - 22), 18, fill=NUIT, outline=couleur, width=3)
        d.text((100, y + (540 // len(items) - 22) // 2), t, font=f(taille), fill=(255, 255, 255), anchor="lm")
    im.save(out / nom)

liste("AU PROGRAMME", ["La Karen du drive", "La voiture la plus rapide", "Un bunker et son code secret",
                       "Codes de triche : vrai ou fake ?", "Il vole un Jumbo Jet"], "ouverture.png")
liste("COMMENT LA TROUVER — SUPERCAR", ["1. Une villa avec un grand portail noir", "2. Passe par-dessus le mur sur le côté",
                                        "3. La voiture rouge attend dans l'allée", "Attention : traceur possible (joueurs)"],
      "guide_voiture.png", TURQ, 38)
liste("COMMENT LE TROUVER — PENTHOUSE", ["Tour sur la petite île en losange", "Débloqué tard dans l'histoire",
                                        "Hélico sur le toit + 8 supercars", "Infos de joueurs, à vérifier"],
      "guide_penthouse.png", TURQ, 38)
liste("COMMENT LE TROUVER — BUNKER", ["1. Mémorial Friends of Freedom (Little Cuba)", "2. Calendrier : 3 janvier 1917",
                                      "3. Petit bunker : tape 01 03 17", "4. Au bureau : code à 4 chiffres"],
      "guide_bunker.png", TURQ, 36)

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "VRAI OU FAKE ?", (255, 138, 61))
centre(d, 240, "LES CODES DE TRICHE", 70, JAUNE, 6); centre(d, 330, "~60 codes circulent sur X et Instagram", 40)
d.rounded_rectangle((200, 390, 1080, 480), 24, fill=ROUGE); centre(d, 435, "NON CONFIRMÉS PAR ROCKSTAR", 40)
centre(d, 560, "Ne télécharge rien · ne donne jamais ton mot de passe", 34, ROSE)
im.save(out / "codes.png")

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "FLASH SPÉCIAL", ROUGE)
centre(d, 280, "AVIS DE RECHERCHE", 74, JAUNE, 6)
centre(d, 400, "Une dépanneuse avec un distributeur", 44); centre(d, 460, "et une cliente qui veut du fromage", 44)
d.rectangle((0, H - 80, W, H), fill=ROUGE)
d.text((30, H - 40), "INFO LEONIDA LIVE • NE PAS COMMANDER DE FROMAGE", font=f(30), fill=(255, 255, 255), anchor="lm")
im.save(out / "flash.png")

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "QUESTION DU JOUR")
for i, t in enumerate(["LE JUMBO JET", "LE BUNKER", "LE FROMAGE"]):
    x = 70 + i * 390
    d.rounded_rectangle((x, 250, x + 360, 400), 24, fill=NUIT, outline=ROSE, width=5)
    d.text((x + 180, 325), t, font=f(36), fill=JAUNE, anchor="mm")
centre(d, 520, "Un seul mot en commentaire !", 50)
im.save(out / "question.png")

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "LE DÉFI DE SUNNY")
centre(d, 250, "Trouve le code", 70, (255, 255, 255), 6); centre(d, 350, "du bunker", 84, JAUNE, 6)
centre(d, 460, "La preuve en commentaire !", 46)
d.rounded_rectangle((390, 540, 890, 640), 30, fill=(230, 30, 40)); centre(d, 590, "ABONNE-TOI", 54)
im.save(out / "fin.png")

# miniature
jet = ImageEnhance.Contrast(Image.open(sys.argv[2]).convert("RGB")).enhance(1.12)
jet = jet.crop((int(jet.width * 0.08), 0, int(jet.width * 0.92), jet.height)).resize((860, 720))
sunny = Image.open(sys.argv[3]).convert("RGB").crop((120, 60, 780, 1000)).resize((520, 740))
mini = Image.new("RGB", (1280, 720)); mini.paste(jet, (420, 0)); mini.paste(sunny, (0, 0))
d = ImageDraw.Draw(mini)
d.text((470, 30), "IL VOLE", font=f(120), fill=(255, 255, 255), stroke_width=12, stroke_fill=NUIT)
d.text((470, 160), "UN AVION ?!", font=f(100), fill=JAUNE, stroke_width=12, stroke_fill=NUIT)
mini.save(out.parent / "miniature_video4.png")
print("ok")

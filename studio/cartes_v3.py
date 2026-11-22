#!/usr/bin/env python3
"""Cartes télé de la vidéo n°3 (programme, flash OVNI, Skunk Ape, question, défi) + miniature."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, str(Path(__file__).parent))
from cartes_tele import JAUNE, NUIT, ROSE, TURQ, W, H, bandeau, centre, f, fond  # noqa: E402

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
oeuf = Image.open(sys.argv[2]).convert("RGB").resize((W, H))      # image de l'œuf qui tombe

im = oeuf.copy(); d = ImageDraw.Draw(im); bandeau(d, "AUJOURD'HUI : 7 SECRETS EN 48 H")
for i, t in enumerate(["Une soucoupe volante", "La chasse au Skunk Ape", "Des bugs qui défient la physique", "Un œuf de Pâques… géant"]):
    d.rounded_rectangle((120, 170 + i * 128, W - 120, 270 + i * 128), 20, fill=NUIT)
    d.text((160, 220 + i * 128), t, font=f(44), fill=(255, 255, 255), anchor="lm")
im.save(out / "ouverture.png")

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "FLASH SPÉCIAL", (220, 30, 40))
centre(d, 290, "LUMIÈRES DANS LE CIEL", 74, JAUNE, 6)
centre(d, 410, "Des habitants signalent des lumières", 44); centre(d, 470, "étranges au-dessus de Leonida", 44)
d.rectangle((0, H - 80, W, H), fill=(220, 30, 40))
d.text((30, H - 40), "LA POLICE DÉMENT • LES ALLIGATORS REFUSENT DE COMMENTER", font=f(30), fill=(255, 255, 255), anchor="lm")
im.save(out / "flash.png")

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "LE SAVIEZ-VOUS ? — SKUNK APE", TURQ)
centre(d, 280, "LE « SINGE QUI PUE »", 80, JAUNE, 6)
centre(d, 400, "Une vraie légende de Floride :", 44); centre(d, 460, "le Bigfoot des marais", 44)
centre(d, 590, "Dans GTA 6 : sa propre mission", 40, ROSE)
im.save(out / "saviez.png")

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "QUESTION DU JOUR")
for i, t in enumerate(["L'OVNI", "LE SKUNK APE", "L'ŒUF"]):
    x = 70 + i * 390
    d.rounded_rectangle((x, 250, x + 360, 400), 24, fill=NUIT, outline=ROSE, width=5)
    d.text((x + 180, 325), t, font=f(38), fill=JAUNE, anchor="mm")
centre(d, 520, "Un seul mot en commentaire !", 50)
im.save(out / "question.png")

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "LE DÉFI DE SUNNY")
centre(d, 260, "Trouve le VRAI", 70, (255, 255, 255), 6); centre(d, 360, "crabe géant 🦀".replace("🦀", ""), 84, JAUNE, 6)
centre(d, 470, "La preuve en commentaire !", 46)
d.rounded_rectangle((390, 540, 890, 640), 30, fill=(230, 30, 40)); centre(d, 590, "ABONNE-TOI", 54)
im.save(out / "fin.png")

# miniature 1280x720
sunny = Image.open(Path(__file__).parent / "avatar/sunny_taille.png").convert("RGB").crop((120, 60, 780, 1000)).resize((520, 740))
mini = Image.new("RGB", (1280, 720))
e = ImageEnhance.Contrast(Image.open(sys.argv[2]).convert("RGB")).enhance(1.15)
e = e.crop((int(e.width * 0.2), int(e.height * 0.08), int(e.width * 0.8), int(e.height * 0.9))).resize((820, 720))
mini.paste(e, (460, 0)); mini.paste(sunny, (0, 0))
d = ImageDraw.Draw(mini)
d.text((520, 30), "ŒUF", font=f(150), fill=JAUNE, stroke_width=12, stroke_fill=NUIT)
d.text((520, 175), "GÉANT ?!", font=f(120), fill=(255, 255, 255), stroke_width=12, stroke_fill=NUIT)
mini.save(out.parent / "miniature_video3.png")
print("ok")

# cartes ajoutées (rallonge à 8 min)
im = fond(); d = ImageDraw.Draw(im); bandeau(d, "FLASH SPÉCIAL", (220, 30, 40))
centre(d, 280, "RECRUTEMENT À GRASSRIVERS", 62, JAUNE, 6)
centre(d, 400, "Expédition de nuit dans les marais", 44); centre(d, 460, "Fourni : lampe torche + courage", 44)
d.rectangle((0, H - 80, W, H), fill=(220, 30, 40))
d.text((30, H - 40), "ODEUR NON COMPRISE • INFO LEONIDA LIVE", font=f(30), fill=(255, 255, 255), anchor="lm")
im.save(out / "flash2.png")

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "LE SAVIEZ-VOUS ? — TRADITION GTA", TURQ)
for i, (a, b) in enumerate([("GTA 5", "Bigfoot + OVNI au-dessus du mont Chiliad"), ("GTA 6", "Skunk Ape + soucoupe à Port Gellhorn")]):
    y = 200 + i * 220
    d.rounded_rectangle((90, y, W - 90, y + 170), 24, fill=NUIT, outline=ROSE, width=4)
    d.text((130, y + 55), a, font=f(52), fill=JAUNE, anchor="lm")
    d.text((130, y + 120), b, font=f(40), fill=(255, 255, 255), anchor="lm")
im.save(out / "tradition.png")
print("cartes ajoutées")

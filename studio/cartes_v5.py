#!/usr/bin/env python3
"""Cartes télé de la vidéo n°5 (secrets et astuces). Usage : cartes_v5.py <dossier cartes>"""
import sys
from pathlib import Path
from PIL import ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from cartes_tele import JAUNE, NUIT, ROSE, TURQ, W, H, bandeau, centre, f, fond  # noqa: E402

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
ROUGE = (220, 30, 40)

def liste(titre, items, nom, couleur=TURQ, taille=38):
    im = fond(); d = ImageDraw.Draw(im); bandeau(d, titre, couleur)
    for i, t in enumerate(items):
        y = 150 + i * (540 // len(items))
        d.rounded_rectangle((70, y, W - 70, y + 540 // len(items) - 22), 18, fill=NUIT, outline=couleur, width=3)
        d.text((100, y + (540 // len(items) - 22) // 2), t, font=f(taille), fill=(255, 255, 255), anchor="lm")
    im.save(out / nom)

liste("AU PROGRAMME", ["Les receleurs : gagne du temps", "Acheter des garages", "Pousser les voitures",
                       "Les codes de triche", "Quelle Bugatti ?", "Le blindé gratuit pour toujours"], "ouverture.png", ROSE, 36)
liste("COMMENT FAIRE — RECELEURS", ["1. Joue avec Jason et Lucia ensemble", "2. Sépare le duo",
                                    "3. Envoie l'autre revendre le butin", "Toi, tu continues à jouer"], "guide_receleurs.png")
liste("COMMENT FAIRE — GARAGES", ["1. Ouvre ton téléphone", "2. Appli immobilier",
                                  "3. Achète un garage près de l'action", "Manoirs et villas : liés à l'histoire"], "guide_garages.png")
liste("COMMENT FAIRE — POUSSER", ["1. Devant ou derrière la voiture", "2. Continue d'avancer : tu pousses",
                                  "3. Maintiens le bouton affiché", "Grosse poussée !"], "guide_pousser.png")
liste("COMMENT LE TROUVER — BLINDÉ (1/2)", ["1. Monument Friends of Freedom (est du centre)",
      "2. Appartement à Little Cuba (drapeau cubain)", "3. Photo : Sharktooth Island", "4. Porte du bunker : 01 03 17"],
      "guide_tank1.png", TURQ, 34)
liste("COMMENT LE TROUVER — BLINDÉ (2/2)", ["5. Bureau → téléphone → radio", "6. Coffre : 2975 (pistolet + photo)",
      "7. Trappe à West Vice Dale : 085355", "8. Courant, cassette, bouton : hangar ouvert"],
      "guide_tank2.png", TURQ, 34)

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "QUELLE BUGATTI ?", (255, 138, 61))
for i, (t, s) in enumerate([("CHIRON", "dit le créateur"), ("TOURBILLON", "écrit sur la vidéo"), ("DIVO", "selon des joueurs")]):
    x = 70 + i * 390
    d.rounded_rectangle((x, 220, x + 360, 400), 24, fill=NUIT, outline=ROSE, width=5)
    d.text((x + 180, 290), t, font=f(42), fill=JAUNE, anchor="mm"); d.text((x + 180, 355), s, font=f(26), fill=(255, 255, 255), anchor="mm")
centre(d, 500, "Nom officiel dans le jeu : à confirmer", 42)
centre(d, 580, "Tu l'as trouvée ? L'endroit en commentaire !", 34, ROSE)
im.save(out / "bugatti.png")

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "QUESTION DU JOUR")
for i, t in enumerate(["LE BLINDÉ", "LES GARAGES", "POUSSER"]):
    x = 70 + i * 390
    d.rounded_rectangle((x, 250, x + 360, 400), 24, fill=NUIT, outline=ROSE, width=5)
    d.text((x + 180, 325), t, font=f(38), fill=JAUNE, anchor="mm")
centre(d, 520, "Quelle astuce tu ne connaissais pas ?", 46)
im.save(out / "question.png")

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "LE DÉFI DE SUNNY")
centre(d, 250, "Récupère le blindé", 70, (255, 255, 255), 6); centre(d, 350, "gratuit", 84, JAUNE, 6)
centre(d, 460, "Ta plus belle course-poursuite en commentaire !", 40)
d.rounded_rectangle((390, 540, 890, 640), 30, fill=ROUGE); centre(d, 590, "ABONNE-TOI", 54)
im.save(out / "fin.png")
print("ok")

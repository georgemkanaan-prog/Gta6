#!/usr/bin/env python3
"""Cartes télé de la vidéo n°6 (GTA 6 ou FiveM). Usage : cartes_v6.py <dossier cartes>"""
import sys
from pathlib import Path
from PIL import ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from cartes_tele import JAUNE, NUIT, ROSE, TURQ, W, H, bandeau, centre, f, fond  # noqa: E402

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
ROUGE, ORANGE = (220, 30, 40), (255, 138, 61)

def liste(titre, items, nom, couleur=TURQ, taille=38):
    im = fond(); d = ImageDraw.Draw(im); bandeau(d, titre, couleur)
    for i, t in enumerate(items):
        y = 150 + i * (540 // len(items))
        d.rounded_rectangle((70, y, W - 70, y + 540 // len(items) - 22), 18, fill=NUIT, outline=couleur, width=3)
        d.text((100, y + (540 // len(items) - 22) // 2), t, font=f(taille), fill=(255, 255, 255), anchor="lm")
    im.save(out / nom)

liste("AU PROGRAMME", ["GTA 5 mieux que GTA 6 ?", "Ce que FiveM fait déjà", "GTA 5 moddé façon GTA 6",
                       "Ce que GTA 6 apporte vraiment", "Le verdict de Sunny"], "ouverture.png", ROSE, 38)
liste("FIVEM, C'EST QUOI ?", ["Une plateforme de fans pour GTA 5 (PC)", "Tes propres serveurs, règles et mods",
                              "Le jeu de rôle : le GTA RP", "Un métier, un appart, de vrais joueurs"], "fivem.png", ORANGE, 38)
liste("5 CHOSES QUE FIVEM FAIT (DÉJÀ)", ["1. Jouer sur PC aujourd'hui", "2. Héberger ton serveur",
      "3. Banque avec un vrai code", "4. Vendre ta voiture à un joueur", "5. Jeu de rôle avec de vraies personnes"],
      "cinq_choses.png", ORANGE, 36)
liste("LES LIMITES DE FIVEM", ["Un bon PC + des mods à installer", "Parfois un entretien pour entrer",
                               "Des files d'attente sur les gros serveurs", "Des plantages quand les mods se battent"],
      "limites.png", ROUGE, 36)
liste("CE QUE GTA 6 APPORTE EN PLUS", ["Un monde neuf : l'État de Leonida", "Une histoire avec Jason et Lucia",
      "Animations et physique pensées pour le jeu", "Console allumée = ça marche"], "gta6_plus.png", TURQ, 36)
liste("COMMENT LA TROUVER — SUPERCAR", ["1. Quartiers résidentiels de Capri", "2. Remonte l'allée d'une villa",
      "3. Ouvre le garage", "Immatriculation : liste de Randy d'abord"], "guide_supercar.png", TURQ, 36)
liste("INFOS DE JOUEURS (À VÉRIFIER)", ["Traceur avancé sur la supercar ?", "La plus rapide : la Thrax ?",
      "Répare ta voiture aux pompes à essence"], "commentaires.png", ORANGE, 38)

liste("ESSAYER FIVEM SANS TE FAIRE AVOIR", ["1. Un PC + GTA 5 officiel", "2. FiveM : site officiel uniquement",
      "3. Un serveur francophone, lis les règles", "Ne paie jamais un inconnu"], "essayer.png", TURQ, 36)
liste("LE RP SUR GTA 6 ?", ["2023 : Rockstar rachète l'équipe de FiveM", "Rien d'annoncé pour GTA 6",
      "Un signe pour beaucoup de joueurs", "Si ça arrive : vidéo le jour même !"], "rockstar.png", ORANGE, 36)
liste("RÉCAP", ["FiveM : le RP, des serveurs à l'infini", "… mais PC, mods et patience",
      "GTA 6 : monde neuf, histoire, secrets", "… et ça marche tout de suite"], "recap.png", ROSE, 38)
im = fond(); d = ImageDraw.Draw(im); bandeau(d, "FLASH SPÉCIAL", ROUGE)
centre(d, 280, "ALERTE LUMIÈRE DU JOUR", 70, JAUNE, 6)
centre(d, 400, "Un joueur FiveM aperçu dehors", 46); centre(d, 460, "pour la première fois depuis des années", 40)
d.rectangle((0, H - 80, W, H), fill=ROUGE)
d.text((30, H - 40), "INFO LEONIDA LIVE • GTA 6 AVEC MODÉRATION", font=f(30), fill=(255, 255, 255), anchor="lm")
im.save(out / "flash.png")

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "LE VERDICT DE SUNNY")
for i, (t, s) in enumerate([("GTA 6", "pour l'aventure"), ("FIVEM", "pour les potes")]):
    x = 140 + i * 520
    d.rounded_rectangle((x, 220, x + 480, 420), 28, fill=NUIT, outline=ROSE, width=5)
    d.text((x + 240, 295), t, font=f(70), fill=JAUNE, anchor="mm"); d.text((x + 240, 375), s, font=f(34), fill=(255, 255, 255), anchor="mm")
centre(d, 520, "Ne choisis pas : joue aux deux !", 50)
im.save(out / "verdict.png")

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "QUESTION DU JOUR")
for i, t in enumerate(["GTA 6", "FIVEM"]):
    x = 190 + i * 480
    d.rounded_rectangle((x, 240, x + 420, 410), 28, fill=NUIT, outline=ROSE, width=5)
    d.text((x + 210, 325), t, font=f(64), fill=JAUNE, anchor="mm")
centre(d, 520, "Ton choix en commentaire !", 54)
im.save(out / "question.png")

im = fond(); d = ImageDraw.Draw(im); bandeau(d, "LE DÉFI DE SUNNY")
centre(d, 250, "Trouve la supercar", 70, (255, 255, 255), 6); centre(d, 350, "cachée de Capri", 76, JAUNE, 6)
centre(d, 460, "Ta plus belle photo en commentaire !", 44)
d.rounded_rectangle((390, 540, 890, 640), 30, fill=ROUGE); centre(d, 590, "ABONNE-TOI", 54)
im.save(out / "fin.png")
print("ok")

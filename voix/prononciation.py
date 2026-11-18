"""Réécrit les noms anglais/du jeu tels qu'ils se prononcent, pour les voix françaises."""
import re

PRONONCIATION = {
    r"\bLeonida Live\b": "Léonida Laïve",
    r"\bLeonida\b": "Léonida",
    r"\bVice City\b": "Vaïce Citi",
    r"\bG ?T ?A (six|6|VI)\b": "Gé Té A six",
    r"\bGTA\b": "Gé Té A",
    r"\bPort Gellhorn\b": "Port Guèl-horne",
    r"\bGrassrivers\b": "Grasse-rivers",
    r"\bMount Kalaga\b": "Mount Kalaga",
    r"\bJason\b": "Djeïsonne",
    r"\bBreaking news\b": "Brèking niouze",
    r"\bRockstar\b": "Rockstar",
    r"\bReal Dimez\b": "Rile Daïmz",
}


def prononcer(texte: str) -> str:
    for motif, remplacement in PRONONCIATION.items():
        texte = re.sub(motif, remplacement, texte, flags=re.I)
    return texte

#!/usr/bin/env python3
"""Extrait les répliques de Sunny d'un script et prépare un fichier texte par segment,
nettoyé pour la synthèse vocale (ElevenLabs, etc.).

Usage : python3 studio/extraire_voix.py videos/001-avant-le-lancement/script.md [dossier_sortie]
Sortie par défaut : <dossier du script>/voix/NN_titre.txt + voix/TOUT.txt
"""
import re
import sys
import unicodedata
from pathlib import Path

NOMBRES = {1: "un", 2: "deux", 3: "trois", 4: "quatre", 5: "cinq", 6: "six", 7: "sept", 8: "huit",
           9: "neuf", 10: "dix", 11: "onze", 12: "douze", 13: "treize", 14: "quatorze", 15: "quinze"}


def pour_la_voix(t: str) -> str:
    t = re.sub(r"\*\*?(.+?)\*\*?", r"\1", t)                        # gras / italique markdown
    t = re.sub(r"[✔🔮⚠️☀]", "", t)
    t = re.sub(r"\bn°\s*(\d+)", lambda m: "numéro " + NOMBRES.get(int(m.group(1)), m.group(1)), t, flags=re.I)
    t = re.sub(r"(\d+)ᵉ", r"\1e", t)
    t = t.replace("GTA 6", "G T A six").replace("PS5", "PS cinq").replace("~", "environ ")
    t = re.sub(r"\bLEONIDA\b", "Leonida !", t)                       # cri de surprise, pas d'épellation
    t = re.sub(r"\s+", " ", t).strip()
    return t


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.parent / "voix"
    out.mkdir(parents=True, exist_ok=True)

    segments, titre = [], None
    for ligne in src.read_text(encoding="utf-8").splitlines():
        h = re.match(r"^##\s+[\d:]+\s+—\s+(.+)$", ligne)
        if h:
            titre = h.group(1)
            segments.append([titre, []])
            continue
        m = re.match(r"^`\[S\]`\s*(.+)$", ligne)
        if m and segments:
            segments[-1][1].append(pour_la_voix(m.group(1)))

    tout, n = [], 0
    for titre, repliques in segments:
        if not repliques:
            continue
        n += 1
        texte = " ".join(repliques)
        nom = f"{n:02d}_{slug(titre)}.txt"
        (out / nom).write_text(texte + "\n", encoding="utf-8")
        tout.append(f"### {nom}\n{texte}\n")
        print(f"{nom:50s} {len(texte.split()):4d} mots  ≈ {len(texte.split()) / 2.6:4.0f} s")
    (out / "TOUT.txt").write_text("\n".join(tout), encoding="utf-8")
    mots = sum(len(t.split("\n", 1)[1].split()) for t in tout)
    print(f"\n{n} segments, {mots} mots ≈ {mots / 2.6 / 60:.1f} min de voix → {out}")


if __name__ == "__main__":
    main()

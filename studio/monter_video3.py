#!/usr/bin/env python3
"""Assemble la vidéo n°3 « 7 secrets en 48 h » (≈ 8 min 30).

Réutilise les briques de monter_video2.py (partie, générique, écran de fin). Les changements d'extrait
dans la télé sont calés sur des MOTS de la voix (repérés par transcription), pas sur des secondes tapées
à la main : si la voix est refaite, le montage suit.

    python studio/monter_video3.py
"""
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import monter_video2 as m2  # noqa: E402

V = m2.RACINE / "videos/003-secrets"
m2.V, m2.C, m2.OUT = V, V / "cartes", V / "parties"
X, VX = V / "extraits", V / "voix"
S = m2.S
OVNI, SK1, SK2 = X / "clip1_ovni_T5G.mp4", X / "clip2_skunkape_revelation_SNIR_1080p.mp4", X / "clip3_skunkape_fin2_SNIR.mp4"
OEUF, BUGS, CRABE = X / "clip4_oeuf_tour_ZoneX.mp4", X / "clip5_bugs_droles_YEAHMAP.mp4", X / "clip6_crabe_geant_TheGamerEyes.mp4"
T = "GTA 6 : 7 secrets trouvés en 48 h"
CACHE = S / "parties/v3_mots.json"


def _norm(w):
    return unicodedata.normalize("NFKD", w.lower()).encode("ascii", "ignore").decode().strip(" .,!?…:;'\"«»")


def mots(seg):
    """Horodatage des mots d'un segment de voix (Whisper), mis en cache."""
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    if seg not in cache:
        from faster_whisper import WhisperModel
        pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", VX / f"{seg}.wav", "-ac", "1", "-ar", "16000",
                              "-f", "f32le", "-"], capture_output=True, check=True).stdout
        model = WhisperModel("small", device="cpu", compute_type="int8")
        segs, _ = model.transcribe(np.frombuffer(pcm, np.float32), language="fr", word_timestamps=True)
        cache[seg] = [(round(w.start, 2), _norm(w.word)) for s in segs for w in s.words]
        CACHE.write_text(json.dumps(cache))
    return cache[seg]


def t(seg, mot, defaut):
    """Instant où `mot` est prononcé dans le segment (premier mot qui commence pareil), sinon `defaut`."""
    m = _norm(mot)
    for start, w in mots(seg):
        if w.startswith(m[:5]):
            return start
    print(f"  repère « {mot} » introuvable dans {seg} : {defaut} s", flush=True)
    return defaut


def p(nom, seg, **kw):
    if not (VX / f"{seg}.wav").exists():
        print("en attente :", nom); return None
    return m2.partie(f"v3_{nom}", VX / f"{seg}.wav", kw.pop("titre", T), **kw)


def main():
    sec = [
        p("01_accroche", "a01_accroche", clip=OEUF, plan=[(0, 64.0, 72.0, -1)], surprise=0.3, texte2="ŒUF GÉANT ?!",
          credit="Clip : ZoneX", zoom=0.85),
        m2.generique(m2.OUT / "v3_02_generique.mp4"),
        p("03_ouverture", "a02_ouverture", titre="Leonida Live — 7 secrets trouvés en 48 h", cartes=[(0, "ouverture.png")]),
        p("04_caddie", "a03_n7", gaps=[(0, 3.5)], clip=BUGS, plan=[(0, 0.0, 9.0, -1)], credit="Clip : YEAHMAP", zoom=0.85),
        p("05_pelleteuse", "a04_n6", gaps=[(0, 1.0), (t("a04_n6", "balance", 5), 2.5)], clip=BUGS, credit="Clip : YEAHMAP",
          zoom=0.85, plan=[(0, 9.0, 18.0, -1), (t("a04_n6", "regarde", 4), 56.0, 66.0, -1)]),
        p("05b_ralenti", "a04b_ralenti", clip=BUGS, zoom=0.85, gaps=[(99, 9.0)], plan=[(0, 56.0, 66.0, -0.6)]),
        p("06_ponton", "a05_n5", gaps=[(t("a05_n5", "pendant", 6), 4.0)], clip=BUGS, credit="Clip : YEAHMAP", zoom=0.85,
          plan=[(0, 67.0, 74.0, -1), (t("a05_n5", "pendant", 6), 75.0, 79.5, -1)]),
        p("07_bonus", "a05b_bonus", clip=BUGS, zoom=0.85,
          plan=[(0, 29.0, 33.0, -1), (t("a05b_bonus", "voiture", 4), 86.0, 90.0, -1)]),
        p("07b_bonus2", "a05c_bonus2", clip=BUGS, zoom=0.85, gaps=[(99, 6.0)],
          plan=[(0, 33.0, 46.0, -1), (t("a05c_bonus2", "autre", 6), 96.0, 103.0, -1)]),
        p("07c_abonne", "a05d_abonne", titre="Abonne-toi : une vidéo GTA 6 tous les jours", cartes=[(0, "fin.png")]),
        p("08_flash", "a06_flash", titre="Flash spécial : des lumières dans le ciel", cartes=[(0, "flash.png")]),
        p("09_ovni", "a07_n4", clip=OVNI, credit="Clip : T5G", zoom=0.8, surprise=t("a07_n4", "quoi", 9),
          texte2="UNE SOUCOUPE ?!", gaps=[(t("a07_n4", "quoi", 9), 0.6), (99, 4.0)],
          plan=[(0, 0.0, 13.0, -1), (t("a07_n4", "nuit", 8), 14.0, 19.5, -0.7)]),
        p("09b_guide_ovni", "a07b_guide_ovni", titre="Le guide de Sunny : trouver l'OVNI", clip=OVNI, credit="Clip : T5G",
          zoom=0.8, gaps=[(99, 6.0)], plan=[(0, 0.0, 13.0, -1), (t("a07b_guide_ovni", "garde", 12), 14.0, 19.5, -0.6)]),
        p("09c_tradition", "a08b_tradition", titre="Le saviez-vous ? OVNI et Bigfoot, une tradition GTA",
          cartes=[(0, "tradition.png")]),
        p("10_saviez", "a08_saviez", titre="Le saviez-vous ? Le Skunk Ape", cartes=[(0, "saviez.png")]),
        p("10b_flash2", "a06b_flash2", titre="Flash spécial : expédition dans les marais", cartes=[(0, "flash2.png")]),
        p("11_chasse", "a09_n3", titre="Piste : le Skunk Ape, monstre ou homme ?", clip=SK1, credit="Clip : SNIR", zoom=0.9, gaps=[(99, 6.0)],
          plan=[(0, 0.0, 10.0, -1), (t("a09_n3", "chasseurs", 6), 10.0, 20.0, -1), (t("a09_n3", "tatouage", 18), 33.0, 41.0, -1)]),
        p("12_fin_mission", "a10_n2", titre="Piste : le Skunk Ape, monstre ou homme ?", clip=SK2, credit="Clip : SNIR", zoom=0.9,
          gaps=[(t("a10_n2", "explosion", 20), 6.0)],
          plan=[(0, 0.0, 12.0, -1), (t("a10_n2", "fusil", 5), 12.0, 24.0, -1), (t("a10_n2", "5", 7), 37.0, 42.0, -1),
                (t("a10_n2", "titre", 10), 28.0, 34.0, -1), (t("a10_n2", "explosion", 20), 62.0, 80.0, -1)]),
        p("12b_theorie", "a10b_theorie", titre="Ma théorie : le Skunk Ape, monstre ou homme ?", clip=SK1, credit="Clip : SNIR",
          zoom=0.9, plan=[(0, 59.0, 72.0, -1)]),
        p("13_crabe", "a11_crabe", titre="On m'avait promis un crabe géant…", clip=CRABE, credit="Clip : THE GAMER EYES",
          zoom=0.85, gaps=[(99, 3.0)], plan=[(0, 0.0, 17.0, -1)]),
        p("14_oeuf", "a12_n1", titre="N°1 : l'œuf de Pâques géant", clip=OEUF, credit="Clip : ZoneX", zoom=0.85,
          surprise=t("a12_n1", "quoi", 24), texte2="ŒUF GÉANT ?!", gaps=[(t("a12_n1", "rockstar", 30), 4.0), (99, 4.0)],
          plan=[(0, 0.0, 20.0, -1), (t("a12_n1", "grimper", 10), 31.0, 45.0, -1.6), (t("a12_n1", "lance", 20), 58.0, 63.5, -1),
                (t("a12_n1", "quoi", 24), 64.0, 88.0, -1)]),
        p("14b_ralenti", "a12d_ralenti", titre="N°1 : l'œuf de Pâques géant", clip=OEUF, zoom=0.85, gaps=[(99, 9.0)],
          plan=[(0, 64.0, 80.0, -0.5)]),
        p("14c_guide", "a12b_guide", titre="Le guide de Sunny : l'œuf de la tour", clip=OEUF, zoom=0.85, gaps=[(99, 7.0)],
          plan=[(0, 0.0, 20.0, -1), (t("a12b_guide", "parachute", 8), 99.0, 103.0, -1), (t("a12b_guide", "lance", 12), 58.0, 70.0, -1)]),
        p("14d_top3", "a12c_top3", titre="Le top 3 de Sunny", clip=X / "top3.mp4", gaps=[(99, 2.0)],
          plan=[(0, 0.0, 0.1, -1), (t("a12c_top3", "trois", 3), 0.0, 6.0, -1), (t("a12c_top3", "soucoupe", 7), 6.0, 11.5, -1),
                (t("a12c_top3", "geant", 12), 11.5, 21.5, -1)]),
        p("14e_recap", "a13b_recap", titre="Récap : 7 secrets en 48 h", cartes=[(0, "ouverture.png")]),
        p("15_question", "a13_question", titre="Question du jour", cartes=[(0, "question.png")]),
        p("16_defi", "a14_fin", titre="Le défi de Sunny : trouve le vrai crabe géant", cartes=[(0, "fin.png")]),
        m2.ecran_fin(m2.OUT / "zz_fin_ecran.mp4"),
    ]
    if any(s is None for s in sec):
        print("parties manquantes : assemblage reporté"); return
    normes = []
    for s in sec:
        n = S / "parties" / f"norm_v3_{s.name}"
        if not n.exists():
            m2.run(["ffmpeg", "-v", "error", "-y", "-i", s, "-vf", "fps=25,scale=1920:1080,format=yuv420p", "-c:v", "libx264",
                    "-crf", "19", "-preset", "medium", "-c:a", "aac", "-ar", m2.SR, "-ac", 2, "-b:a", "192k", n])
        normes.append(n)
    liste = S / "parties/liste_v3.txt"
    liste.write_text("".join(f"file '{n}'\n" for n in normes))
    final = V / "video3_secrets.mp4"
    m2.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", 0, "-i", liste, "-c", "copy", "-movflags", "+faststart", final])
    print(final, f"{m2.duree(final) / 60:.2f} min")


if __name__ == "__main__":
    main()

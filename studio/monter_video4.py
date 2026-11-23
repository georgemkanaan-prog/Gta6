#!/usr/bin/env python3
"""Assemble la vidéo n°4 « Les moments les plus fous de GTA 6 cette semaine » (≈ 8 min 30).

Même méthode que la n°3 (changements d'extrait calés sur les mots de la voix), plus :
- générique sur le jingle synthwave ORIGINAL (studio/assets/jingle_synthwave.wav) ;
- extraits « tv » déjà mis au format 16:9 (face-cams et gabarits des créateurs retirés, fond flouté) ;
- cartes « Comment le trouver » enchaînées à la fin de l'extrait (penthouse, bunker).
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import monter_video2 as m2  # noqa: E402
import monter_video3 as m3  # noqa: E402

V = m2.RACINE / "videos/004-moments-fous"
m2.V, m2.C, m2.OUT = V, V / "cartes", V / "parties"
m3.VX = V / "voix"
m3.CACHE = m2.S / "parties/v4_mots.json"
TV = V / "extraits/tv"
DEP, KAR, VOI = TV / "depanneuse_gta6modscom.mp4", TV / "karen_fastfood_antodaboss.mp4", TV / "voiture_rapide_r2s_fut.mp4"
CON, PEN, BUN = TV / "concession_luxe_stractgaming.mp4", TV / "penthouse_incredilags_via_sixstarsgaming.mp4", TV / "bunker_roddy_game.mp4"
JJ1, JJ2 = TV / "jumbo_jet_champsworld1006.mp4", TV / "jumbo_jet_fin_champsworld1006.mp4"
T = "GTA 6 : les moments les plus fous de la semaine"
t = m3.t


def clip_plus_carte(clip, carte, d, sortie):
    """L'extrait puis une carte fixe de `d` secondes (son du jeu, puis silence)."""
    if sortie.exists():
        return sortie
    m2.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", clip, "-loop", "1", "-t", d, "-i", m2.C / carte,
            "-f", "lavfi", "-t", d, "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex",
            "[1:v]scale=1280:720,fps=30,setsar=1[c];[0:v][0:a][c][2:a]concat=n=2:v=1:a=1[v][a]",
            "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", sortie])
    return sortie


def top3(sortie):
    if sortie.exists():
        return sortie
    m2.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", "10", "-t", "6", "-i", DEP, "-ss", "20", "-t", "6", "-i", BUN,
            "-ss", "2", "-t", "9", "-i", JJ2, "-filter_complex",
            "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", sortie])
    return sortie


def p(nom, seg, **kw):
    if not (m3.VX / f"{seg}.wav").exists():
        print("en attente :", nom); return None
    return m2.partie(f"v4_{nom}", m3.VX / f"{seg}.wav", kw.pop("titre", T), **kw)


def main():
    PENC = clip_plus_carte(PEN, "guide_penthouse.png", 10, V / "extraits/pen_carte.mp4")
    BUNC = clip_plus_carte(BUN, "guide_bunker.png", 14, V / "extraits/bunker_carte.mp4")
    TOP = top3(V / "extraits/top3.mp4")
    sec = [
        p("01_accroche", "b01_accroche", clip=DEP, plan=[(0, 4.0, 20.0, -1)], surprise=t("b01_accroche", "quoi", 5),
          texte2="UNE DÉPANNEUSE ?!", credit="Clip : gta6modscom"),
        m2.generique(m2.OUT / "v4_02_generique.mp4", jingle=m2.RACINE / "studio/assets/jingle_synthwave.wav"),
        p("03_ouverture", "b02_ouverture", titre="Leonida Live — la semaine la plus folle de GTA 6", cartes=[(0, "ouverture.png")]),
        p("04_karen", "b03_karen", titre="N°7 : la Karen du drive", clip=KAR, credit="Clip : antodaboss", gaps=[(0, 1.0), (99, 3.0)],
          plan=[(0, 0.0, 34.0, -1)]),
        p("05_depanneuse", "b04_depanneuse", titre="N°6 : la dépanneuse contre le distributeur", clip=DEP,
          credit="Clip : gta6modscom", gaps=[(99, 5.0)], plan=[(0, 0.0, 34.8, -1)]),
        p("06_voiture", "b05_voiture", titre="N°5 : la voiture la plus rapide de GTA 6", clip=VOI, credit="Clip : r2s_fut",
          son=0.07, gaps=[(99, 3.0)], plan=[(0, 0.0, 14.0, -1), (t("b05_voiture", "supercar", 10), 14.0, 29.6, -1)]),
        p("07_guide_voiture", "b06_guide_voiture", titre="Guide : trouver la supercar rouge", cartes=[(0, "guide_voiture.png")]),
        p("08_concession", "b07_concession", titre="N°4 : la concession de luxe", clip=CON, credit="Clip : stractgaming",
          son=0.08, gaps=[(99, 3.0)], plan=[(0, 0.0, 34.7, -1)]),
        p("09_flash", "b08_flash", titre="Flash spécial Leonida", cartes=[(0, "flash.png")]),
        p("10_codes", "b09_codes", titre="Vrai ou fake : les codes de triche de GTA 6", cartes=[(0, "codes.png")]),
        p("11_penthouse", "b10_penthouse", titre="N°3 : le penthouse de rêve (attention spoiler)", clip=PENC,
          credit="Clip : Incredilags (via sixstarsgaming)", gaps=[(99, 4.0)],
          plan=[(0, 0.0, 10.0, -1), (t("b10_penthouse", "ascenseur", 14), 10.0, 18.0, -1),
                (t("b10_penthouse", "toit", 16), 18.0, 34.6, -1), (t("b10_penthouse", "vis", 24), 34.7, 44.6, -1)]),
        p("12_bunker", "b11_bunker", titre="N°2 : le bunker secret", clip=BUNC, credit="Clip : roddy_game",
          plan=[(0, 0.0, 6.0, -1)]),
        p("13_guide_bunker", "b12_guide_bunker", titre="Guide : le code du bunker, étape par étape", clip=BUNC,
          gaps=[(99, 3.0)], plan=[(0, 6.0, 14.0, -1), (t("b12_guide_bunker", "ecoute", 8), 14.0, 20.0, -1),
                                  (t("b12_guide_bunker", "petit", 16), 20.0, 27.0, -1),
                                  (t("b12_guide_bunker", "assieds", 24), 27.0, 34.6, -1),
                                  (t("b12_guide_bunker", "montre", 30), 34.7, 48.6, -1)]),
        p("14_abonne", "b13_abonne", titre="Abonne-toi : une vidéo GTA 6 tous les jours", cartes=[(0, "fin.png")]),
        p("15_jumbo1", "b14_jumbo1", titre="N°1 : il vole un Jumbo Jet", clip=JJ1, credit="Clip : champsworld1006",
          gaps=[(99, 4.0)], plan=[(0, 0.0, 35.0, -1)]),
        p("16_jumbo2", "b15_jumbo2", titre="N°1 : il vole un Jumbo Jet", clip=JJ2, credit="Clip : champsworld1006",
          surprise=t("b15_jumbo2", "quoi", 6), texte2="IL SAUTE ?!", gaps=[(t("b15_jumbo2", "quoi", 6), 1.5), (99, 5.0)],
          plan=[(0, 0.0, 12.0, -1), (t("b15_jumbo2", "quoi", 6), 12.0, 35.0, -1)]),
        p("17_top3", "b16_top3", titre="Le top 3 de Sunny", clip=TOP, gaps=[(99, 2.0)],
          plan=[(0, 0.0, 0.1, -1), (t("b16_top3", "depanneuse", 4), 0.0, 6.0, -1), (t("b16_top3", "bunker", 8), 6.0, 12.0, -1),
                (t("b16_top3", "jumbo", 12), 12.0, 21.0, -1)]),
        p("18_question", "b17_question", titre="Question du jour", cartes=[(0, "question.png")]),
        p("19_defi", "b18_fin", titre="Le défi de Sunny : trouve le code du bunker", cartes=[(0, "fin.png")]),
        m2.ecran_fin(m2.OUT / "zz_fin_ecran.mp4"),
    ]
    if any(s is None for s in sec):
        print("parties manquantes : assemblage reporté"); return
    normes = []
    for s in sec:
        n = m2.S / "parties" / f"norm_v4_{s.name}"
        ok = n.exists() and subprocess.run(["ffprobe", "-v", "error", str(n)], capture_output=True).returncode == 0
        if not ok:
            m2.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", s, "-vf", "fps=25,scale=1920:1080,format=yuv420p",
                    "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-c:a", "aac", "-ar", m2.SR, "-ac", 2, "-b:a", "160k", n])
        normes.append(n)
    liste = m2.S / "parties/liste_v4.txt"
    liste.write_text("".join(f"file '{n}'\n" for n in normes))
    final = V / "video4.mp4"
    m2.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", 0, "-i", liste, "-c", "copy", "-movflags", "+faststart", final])
    print(final, f"{m2.duree(final) / 60:.2f} min", f"{final.stat().st_size / 1e6:.0f} Mo")


if __name__ == "__main__":
    main()

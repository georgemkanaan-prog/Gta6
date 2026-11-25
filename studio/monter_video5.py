#!/usr/bin/env python3
"""Assemble la vidéo n°5 « GTA 6 : les secrets et astuces que personne ne t'explique » (≈ 8 min 30).

Même méthode que la n°4 : Sunny reformule en français, le son anglais d'origine reste bas sous sa voix,
cartes « Comment faire » / « Comment le trouver » enchaînées après les extraits.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import monter_video2 as m2  # noqa: E402
import monter_video3 as m3  # noqa: E402

V = m2.RACINE / "videos/005-secrets-astuces"
m2.V, m2.C, m2.OUT = V, V / "cartes", V / "parties"
m2.OUT.mkdir(exist_ok=True)
m3.VX = V / "voix"
m3.CACHE = m2.S / "parties/v5_mots.json"
TV = V / "extraits/tv"
REC, GAR, POU, CHE = TV / "receleurs.mp4", TV / "garages.mp4", TV / "pousser.mp4", TV / "cheats.mp4"
BUG, GOU = TV / "bugatti.mp4", TV / "gourous.mp4"
TA, TB, TC = TV / "tank_a.mp4", TV / "tank_b.mp4", TV / "tank_c.mp4"
T = "GTA 6 : les secrets que personne ne t'explique"
GX = "Clip : gameranx (YouTube)"


def t(seg, mot, defaut):
    return m3.t(seg, mot, defaut) if (m3.VX / f"{seg}.wav").exists() else defaut


def clip_plus_carte(clip, carte, d, sortie):
    """L'extrait puis une carte fixe de `d` secondes (son du jeu, puis silence)."""
    if sortie.exists():
        return sortie
    if not clip.exists():
        return clip
    m2.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", clip, "-loop", "1", "-t", d, "-i", m2.C / carte,
            "-f", "lavfi", "-t", d, "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex",
            "[0:a]aresample=44100,aformat=channel_layouts=stereo[a0];"
            "[1:v]scale=1280:720,fps=30,setsar=1[c];[0:v][a0][c][2:a]concat=n=2:v=1:a=1[v][a]",
            "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", sortie])
    return sortie


def duree(f):
    return m2.duree(f) if Path(f).exists() else 30.0


def p(nom, seg, **kw):
    if not (m3.VX / f"{seg}.wav").exists():
        print("en attente :", nom); return None
    return m2.partie(f"v5_{nom}", m3.VX / f"{seg}.wav", kw.pop("titre", T), **kw)


def main():
    X = V / "extraits"
    RECC = clip_plus_carte(REC, "guide_receleurs.png", 9, X / "receleurs_carte.mp4")
    GARC = clip_plus_carte(GAR, "guide_garages.png", 9, X / "garages_carte.mp4")
    POUC = clip_plus_carte(POU, "guide_pousser.png", 9, X / "pousser_carte.mp4")
    CHEC = clip_plus_carte(CHE, "guide_cheats.png", 9, X / "cheats_carte.mp4")
    dta, dtb, dtc = duree(TA), duree(TB), duree(TC)
    sec = [
        p("01_accroche", "c01_accroche", clip=TC, credit="Clip : mrdalekjd",
          plan=[(0, max(dtc - 16, 0), dtc - 0.1, -1)], surprise=t("c01_accroche", "quoi", 3),
          texte2="UN TANK GRATUIT ?!"),
        m2.generique(m2.OUT / "v5_02_generique.mp4", jingle=m2.RACINE / "studio/assets/jingle_synthwave.wav"),
        p("03_ouverture", "c02_ouverture", titre="Leonida Live — ce que le jeu ne t'explique pas",
          cartes=[(0, "ouverture.png")]),
        p("04_receleurs", "c03_receleurs", titre="N°7 : les receleurs (gagne du temps)", clip=RECC, credit=GX,
          gaps=[(99, 8.0)], plan=[(0, 0.0, duree(RECC) - 0.1, -1)], son=0.12),
        p("05_garages", "c04_garages", titre="N°6 : acheter des garages", clip=GARC, credit=GX,
          gaps=[(99, 8.0)], plan=[(0, 0.0, duree(GARC) - 0.1, -1)], son=0.12),
        p("06_pousser", "c05_pousser", titre="N°5 : tu peux pousser les voitures", clip=POUC, credit=GX,
          gaps=[(99, 8.0)], plan=[(0, 0.0, duree(POUC) - 0.1, -1)], son=0.12),
        p("07_cheats", "c06_cheats", titre="N°4 : comment marchent les codes de triche", clip=CHEC, credit=GX,
          gaps=[(99, 8.0)], plan=[(0, 0.0, duree(CHEC) - 0.1, -1)], son=0.0),
        p("08_bugatti", "c07_bugatti", titre="N°3 : quelle Bugatti est-ce vraiment ?", clip=BUG,
          credit="Clip : lbmms_", gaps=[(99, 2.0)], plan=[(0, 0.0, duree(BUG) - 0.1, -1)], son=0.12),
        p("08b_bugatti_ou", "c07b_bugatti_ou", titre="N°3 : où trouver la Bugatti ?", cartes=[(0, "bugatti.png")]),
        p("09_abonne", "c08_abonne", titre="Abonne-toi : une vidéo GTA 6 tous les jours", cartes=[(0, "fin.png")]),
        p("10_tank", "c09_tank", titre="N°2 et N°1 : le blindé gratuit pour toujours", clip=TA, credit="Clip : mrdalekjd",
          plan=[(0, 0.0, 10.5, -1)], son=0.10),
        p("11_tank1", "c10_tank_etapes1", titre="Guide : le blindé gratuit (étapes 1 à 3)", clip=TA,
          credit="Clip : mrdalekjd", gaps=[(99, 2.0)], plan=[(0, 10.5, dta - 0.1, -1)], son=0.10),
        p("12_tank2", "c11_tank_etapes2", titre="Guide : le blindé gratuit (étapes 4 à 6)", clip=TB,
          credit="Clip : mrdalekjd", gaps=[(99, 2.0)], plan=[(0, 0.0, dtb - 0.1, -1)], son=0.10),
        p("13_tank3", "c12_tank_etapes3", titre="Guide : le blindé gratuit (étape 7)", clip=TC,
          credit="Clip : mrdalekjd", gaps=[(99, 4.0)], plan=[(0, 0.0, dtc - 0.1, -1)], son=0.10),
        p("14_tank_codes", "c13_tank_recap", titre="Tous les codes du blindé (fais une capture)",
          gaps=[(99, 8.0)], cartes=[(0, "guide_tank1.png"), (t("c13_tank_recap", "attention", 4), "guide_tank2.png")]),
        p("15_gourous", "c14_gourous", titre="Bonus : les faux gourous de Miami", clip=GOU,
          credit="Clip : levivdwaarden", gaps=[(99, 8.0)], plan=[(0, 0.0, duree(GOU) - 0.1, -1)], son=0.12),
        p("16_question", "c15_question", titre="Question du jour", cartes=[(0, "question.png")]),
        p("17_fin", "c16_fin", titre="Le défi de Sunny : le blindé gratuit", cartes=[(0, "fin.png")]),
        m2.ecran_fin(m2.OUT / "zz_fin_ecran.mp4"),
    ]
    if any(s is None for s in sec):
        print("parties manquantes : assemblage reporté"); return
    normes = []
    for s in sec:
        n = m2.S / "parties" / f"norm_v5_{s.name}"
        ok = n.exists() and subprocess.run(["ffprobe", "-v", "error", str(n)], capture_output=True).returncode == 0
        if not ok:
            m2.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", s, "-vf", "fps=25,scale=1920:1080,format=yuv420p",
                    "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-c:a", "aac", "-ar", m2.SR, "-ac", 2, "-b:a", "160k", n])
        normes.append(n)
    liste = m2.S / "parties/liste_v5.txt"
    liste.write_text("".join(f"file '{n}'\n" for n in normes))
    final = V / "video5.mp4"
    m2.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", 0, "-i", liste, "-c", "copy", "-movflags", "+faststart", final])
    print(final, f"{m2.duree(final) / 60:.2f} min", f"{final.stat().st_size / 1e6:.0f} Mo")


if __name__ == "__main__":
    main()

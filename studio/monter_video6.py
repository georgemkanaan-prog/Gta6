#!/usr/bin/env python3
"""Assemble la vidéo n°5 « GTA 6 ou FiveM : pourquoi certains joueurs refusent de passer à GTA 6 ».

Même méthode que la n°4 : Sunny reformule en français, le son anglais d'origine reste bas sous sa voix,
cartes « Comment faire » / « Comment le trouver » enchaînées après les extraits.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import monter_video2 as m2  # noqa: E402
import monter_video3 as m3  # noqa: E402

V = m2.RACINE / "videos/006-gta6-ou-fivem"
m2.V, m2.C, m2.OUT = V, V / "cartes", V / "parties"
m2.OUT.mkdir(exist_ok=True)
m3.VX = V / "voix"
m3.CACHE = m2.S / "parties/v6_mots.json"
TV = V / "extraits/tv"
DARK, TJR, REV = TV / "darkviper.mp4", TV / "tjr.mp4", TV / "revolution.mp4"
KA, KB, IG, IJ, SUP = TV / "kingjay_a.mp4", TV / "kingjay_b.mp4", TV / "inter_graphismes.mp4", TV / "inter_jason_lucia.mp4", TV / "supercar.mp4"
T = "GTA 6 ou FiveM : le grand débat"


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
            "[0:v]setsar=1[v0];[1:v]scale=1280:720,fps=30,setsar=1[c];[v0][a0][c][2:a]concat=n=2:v=1:a=1[v][a]",
            "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", sortie])
    return sortie


def duree(f):
    return m2.duree(f) if Path(f).exists() else 30.0


def p(nom, seg, **kw):
    if not (m3.VX / f"{seg}.wav").exists():
        print("en attente :", nom); return None
    return m2.partie(f"v6_{nom}", m3.VX / f"{seg}.wav", kw.pop("titre", T), **kw)


def concat(a, b, sortie):
    if not sortie.exists():
        m2.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", a, "-i", b, "-filter_complex",
                "[0:v]setsar=1,fps=30[x];[1:v]setsar=1,fps=30[y];[x][0:a][y][1:a]concat=n=2:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", sortie])
    return sortie


def main():
    X = V / "extraits"
    KJ = concat(KA, KB, X / "kingjay.mp4")
    REVC = clip_plus_carte(REV, "cinq_choses.png", 12, X / "revolution_carte.mp4")
    SUPC = clip_plus_carte(SUP, "guide_supercar.png", 9, X / "supercar_carte.mp4")
    sec = [
        p("01_accroche", "d01_accroche", clip=DARK, credit="Clip : DarkViperAU", plan=[(0, 0.0, duree(DARK) - 0.1, -1)],
          surprise=t("d01_accroche", "quoi", 3), texte2="GTA 5 > GTA 6 ?!", son=0.10),
        m2.generique(m2.OUT / "v6_02_generique.mp4", jingle=m2.RACINE / "studio/assets/jingle_synthwave.wav"),
        p("03_ouverture", "d02_ouverture", titre="Leonida Live — GTA 6 ou FiveM ?", cartes=[(0, "ouverture.png")]),
        p("04_darkviper", "d03_darkviper", titre="GTA 5 mieux que GTA 6 ? L'avis de DarkViperAU", clip=DARK,
          credit="Clip : DarkViperAU", gaps=[(99, 4.0)], plan=[(0, 0.0, duree(DARK) - 0.1, -1)], son=0.10),
        p("05_fivem", "d04_fivem", titre="FiveM, c'est quoi ?", cartes=[(0, "fivem.png")]),
        p("06_tjr", "d05_tjr", titre="« Tu connais FiveM ? » — le sketch de TJRmindset", clip=TJR,
          credit="Clip : TJRmindset", gaps=[(99, 3.0)], plan=[(0, 0.0, duree(TJR) - 0.1, -1)], son=0.10),
        p("07_revolution", "d06_revolution", titre="5 choses que FiveM fait (déjà)", clip=REVC,
          credit="Clip : Revolution Development", gaps=[(99, 4.0)], plan=[(0, 0.0, duree(REVC) - 0.1, -1)], son=0.10),
        p("08_kingjay", "d07_kingjay", titre="« FiveM peut déjà tout faire » — King Jay", clip=KJ,
          credit="Clip : King Jay", gaps=[(99, 4.0)], plan=[(0, 0.0, duree(KJ) - 0.1, -1)], son=0.10),
        p("08b_limites", "d07b_limites", titre="Les limites de FiveM", cartes=[(0, "limites.png")]),
        p("09_inter1", "d08_inter1", titre="GTA 5 moddé façon GTA 6 : les graphismes", clip=IG,
          credit="Clip : INTER (YouTube)", gaps=[(99, 4.0)], plan=[(0, 0.0, duree(IG) - 0.1, -1)], son=0.10),
        p("10_inter2", "d09_inter2", titre="Jason et Lucia… dans GTA 5", clip=IJ,
          credit="Clip : INTER (YouTube)", gaps=[(99, 8.0)], plan=[(0, 0.0, duree(IJ) - 0.1, -1)], son=0.10),
        p("11_gta6_plus", "d10_gta6_plus", titre="Ce que GTA 6 apporte vraiment en plus", cartes=[(0, "gta6_plus.png")]),
        p("12_supercar", "d11_supercar", titre="GTA 6 fait mieux : la supercar cachée", clip=SUPC,
          credit="Clip : siidv2 (Instagram)", gaps=[(99, 4.0)], plan=[(0, 0.0, duree(SUPC) - 0.1, -1)], son=0.10),
        p("12b_commentaires", "d11b_commentaires", titre="La supercar : les infos des joueurs", cartes=[(0, "commentaires.png")]),
        p("13_abonne", "d12_abonne", titre="Abonne-toi : une vidéo GTA 6 tous les jours", cartes=[(0, "fin.png")]),
        p("14_verdict", "d13_verdict", titre="Le verdict de Sunny", cartes=[(0, "verdict.png")]),
        p("15_question", "d14_question", titre="Question du jour : GTA 6 ou FiveM ?", cartes=[(0, "question.png")]),
        p("16_fin", "d15_fin", titre="Le défi de Sunny : la supercar de Capri", cartes=[(0, "fin.png")]),
        m2.ecran_fin(m2.OUT / "zz_fin_ecran.mp4"),
    ]
    if any(s is None for s in sec):
        print("parties manquantes : assemblage reporté"); return
    normes = []
    for s in sec:
        n = m2.S / "parties" / f"norm_v6_{s.name}"
        ok = n.exists() and subprocess.run(["ffprobe", "-v", "error", str(n)], capture_output=True).returncode == 0
        if not ok:
            m2.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", s, "-vf", "fps=25,scale=1920:1080,format=yuv420p",
                    "-c:v", "libx264", "-crf", "21", "-preset", "medium", "-c:a", "aac", "-ar", m2.SR, "-ac", 2, "-b:a", "160k", n])
        normes.append(n)
    liste = m2.S / "parties/liste_v6.txt"
    liste.write_text("".join(f"file '{n}'\n" for n in normes))
    final = V / "video6.mp4"
    m2.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", 0, "-i", liste, "-c", "copy", "-movflags", "+faststart", final])
    print(final, f"{m2.duree(final) / 60:.2f} min", f"{final.stat().st_size / 1e6:.0f} Mo")


if __name__ == "__main__":
    main()

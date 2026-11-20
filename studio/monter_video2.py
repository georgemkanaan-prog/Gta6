#!/usr/bin/env python3
"""Assemble la vidéo n°2 « Jour de sortie » (≈ 8 min) à partir des voix, extraits et cartes.

Chaque partie : voix (+ pauses où l'extrait passe seul) -> lèvres (réutilisation) -> studio (demo_reaction.py).
Puis : générique + parties + écran de fin, mis bout à bout.

    python studio/monter_video2.py            (reprend là où il s'est arrêté : les parties déjà faites sont gardées)
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

RACINE = Path(__file__).resolve().parent.parent
V = RACINE / "videos/002-jour-de-sortie"
X = V / "extraits"; C = V / "cartes"; OUT = V / "parties"
S = Path("/tmp/claude-0/-home-user-Gta6/1d6fe0b7-ff66-55d7-be7b-3af9893b033d/scratchpad")
PY_IMG, PY_CB = S / "venv/bin/python", S / "venv_cb/bin/python"
FPS, SR = 25, 44100
BUGS, INTRO, PUB = X / "streams_jour1_compilation.mp4", X / "intro_nz_gtasix.mp4", X / "youtube_pub_lancement.mp4"
CREDIT_BUGS = "Clips : streamers Twitch"


def run(cmd, **kw):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit(f"ÉCHEC : {' '.join(map(str, cmd))[:200]}\n{r.stderr[-1500:]}")
    return r.stdout


def duree(f):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))


def espacer(wav, gaps, sortie):
    """Insère des silences (instant_original, durée) ; renvoie la fonction de conversion des instants."""
    y, sr = sf.read(wav, dtype="float32")
    if y.ndim > 1:
        y = y.mean(1)
    morceaux, prec = [], 0
    for t, g in sorted(gaps):
        i = int(t * sr); morceaux += [y[prec:i], np.zeros(int(g * sr), np.float32)]; prec = i
    morceaux.append(y[prec:])
    sf.write(sortie, np.concatenate(morceaux), sr)
    return lambda t: t + sum(g for gt, g in gaps if gt < t)


def video_cartes(cartes, d, sortie):
    """Cartes successives [(instant, png)], léger zoom avant continu."""
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1280x720",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", sortie],
                            stdin=subprocess.PIPE)
    ims = [(t, Image.open(p).convert("RGB")) for t, p in cartes]
    for i in range(int(d * FPS) + 1):
        t = i / FPS
        t0, im = [c for c in ims if c[0] <= t][-1]
        z = 1 + 0.03 * min(1.0, (t - t0) / 8)
        w, h = int(1280 / z), int(720 / z)
        proc.stdin.write(np.asarray(im.crop(((1280 - w) // 2, (720 - h) // 2, (1280 + w) // 2, (720 + h) // 2))
                                    .resize((1280, 720)), np.uint8).tobytes())
    proc.stdin.close(); proc.wait()


def partie(nom, voix, titre, gaps=(), clip=None, plan=(), cartes=None, surprise=None, texte2="QUOI ?!",
           credit=None, son=0.15, zoom=1.0):
    sortie = OUT / f"{nom}.mp4"
    if sortie.exists():
        return sortie
    if not Path(voix).exists() or (clip is not None and not Path(clip).exists()):
        print("en attente :", nom, flush=True)
        return None
    print("partie", nom, flush=True)
    tmp = S / "parties"; tmp.mkdir(exist_ok=True)
    w = tmp / f"{nom}.wav"
    conv = espacer(voix, gaps, w)
    d = duree(w)
    norm, w16, vis = tmp / f"{nom}_n.wav", tmp / f"{nom}_16.wav", tmp / f"{nom}_visage.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-i", w, "-af", "loudnorm=I=-14:TP=-1", "-ar", SR, norm])
    run(["ffmpeg", "-v", "error", "-y", "-i", w, "-ar", 16000, "-ac", 1, w16])
    run([PY_CB, RACINE / "studio/reutiliser_levres.py", "--biblio", RACINE / "studio/avatar/bibliotheque/sunny_portrait_01.mp4",
         "--biblio-audio", RACINE / "studio/avatar/bibliotheque/sunny_portrait_01.wav", "--audio", w16, "--sortie", vis])
    provisoire = sortie.with_name(sortie.stem + "_encours.mp4")   # renommé seulement si le rendu va au bout
    args = [PY_IMG, RACINE / "studio/demo_reaction.py", "--visage", vis, "--audio", norm, "--sortie", provisoire,
            "--postures", f"0:{RACINE / 'studio/avatar/sunny_taille.png'}", "--bas", 1120, "--titre", titre,
            "--surprise", conv(surprise) if surprise is not None else 9999, "--surprise-duree", 2.6, "--texte2", texte2]
    if cartes:
        cv = tmp / f"{nom}_cartes.mp4"
        video_cartes([(conv(t), C / p) for t, p in cartes], d, cv)
        args += ["--clip", cv, "--son-clip", 0]
    else:
        args += ["--clip", clip, "--zoom-clip", zoom, "--son-clip", son, "--clip-debut", 0,
                 "--plan-tele", ";".join(f"{conv(t):.2f}:{a}-{b}:{v}" for t, a, b, v in plan)]
        if credit:
            args += ["--credit", credit]
    OUT.mkdir(exist_ok=True)
    run(args, env={**os.environ, "U2NET_HOME": str(S / "u2net")})
    provisoire.rename(sortie)
    return sortie


def generique(sortie, d=4.0):
    if sortie.exists():
        return sortie
    fond = Image.open(RACINE / "studio/assets/studio.png").convert("RGB")
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 150)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080",
                             "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i",
                             f"aevalsrc='0.25*sin(2*PI*(220+110*floor(t*4))*t)*exp(-3*mod(t,0.25))':s={SR}:d={d}",
                             "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", sortie],
                            stdin=subprocess.PIPE)
    for i in range(int(d * FPS)):
        t = i / FPS; im = fond.copy(); dr = ImageDraw.Draw(im)
        e = min(1.0, t / 0.6)
        ft = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(150 * (0.5 + 0.5 * e)))
        dr.text((960, 520), "LEONIDA LIVE", font=ft, fill=(255, 62, 154), anchor="mm", stroke_width=10, stroke_fill=(42, 15, 74))
        if t > 0.8:
            dr.text((960, 680), "☀ avec Sunny", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70),
                    fill=(33, 212, 224), anchor="mm", stroke_width=6, stroke_fill=(42, 15, 74))
        proc.stdin.write(np.asarray(im, np.uint8).tobytes())
    proc.stdin.close(); proc.wait()
    return sortie


def ecran_fin(sortie, d=15.0):
    """Sunny silencieuse (respiration), carte « abonne-toi » dans la télé : zone pour l'écran de fin YouTube."""
    if sortie.exists():
        return sortie
    sil = S / "parties/silence.wav"
    sf.write(sil, np.zeros(int(d * SR), np.float32) + 1e-5, SR)
    return partie("zz_fin_ecran", sil, "Abonne-toi • nouvelle vidéo tous les jours", cartes=[(0, "fin.png")])


def main():
    OUT.mkdir(exist_ok=True)
    mots = json.loads((S / "mots.json").read_text()) if (S / "mots.json").exists() else {}
    T = "Les bugs les plus fous du 1er jour de GTA 6"
    sec = [
        partie("01_accroche", V / "t01_accroche.wav", T, clip=BUGS, plan=[(0, 130.0, 138.0, -1.0)], surprise=0.2,
               texte2="SOUS LA CARTE ?!", credit=CREDIT_BUGS),
        generique(OUT / "02_generique.mp4"),
        partie("03_ouverture", V / "t02_ouverture.wav", "Leonida Live — spécial sortie de GTA 6", cartes=[(0, "ouverture.png")]),
        partie("04_intro_nz", V / "voix_intro.wav", "Vrai ou faux ? L'intro de GTA 6 venue de Nouvelle-Zélande",
               gaps=[(12.4, 2.0)], clip=INTRO, zoom=0.75, credit="Clip : @gtasix_", surprise=43.4, texte2="LE PARRAIN ?!",
               plan=[(0, 0.0, 0.1, -1), (12.4, 0.7, 1.3, 0.25), (21.2, 2.4, 3.2, 0.25), (32.1, 3.9, 4.7, 0.25),
                     (40.6, 5.4, 6.2, 0.25), (51.5, 7.0, 7.6, 0.25)]),
        partie("05_flash_flamant", V / "t09c_flash2.wav", "Flash spécial : un flamant rose recherché", cartes=[(0, "flash2.png")]),
        partie("06_saviez_record", V / "t04_saviez1.wav", "Le saviez-vous ? Les records des trailers",
               cartes=[(0, "saviez1_1.png"), (10.4, "saviez1_2.png")]),
        partie("07_saviez_musique", V / "t09b_musique.wav", "Le saviez-vous ? La musique des trailers", cartes=[(0, "musique.png")]),
        partie("08_youtube", V / "voix_youtube.wav", "YouTube fête le lancement de GTA 6", gaps=[(4.9, 2.0)], clip=PUB,
               credit="YouTube", plan=[(0, 0.0, 2.9, -1), (4.1, 3.0, 6.0, -1), (8.8, 8.4, 12.0, -1), (13.4, 13.0, 17.5, -1),
                                       (19.1, 29.0, 34.0, -1), (21.2, 34.0, 38.0, -1), (22.4, 39.5, 44.0, -1),
                                       (24.3, 49.5, 54.0, -1), (31.8, 54.0, 58.0, -1)]),
        partie("09_pub_detail", V / "t06b_pub.wav", "YouTube fête le lancement de GTA 6", clip=PUB,
               plan=[(0, 23.5, 28.5, -0.8), (7.0, 49.5, 54.0, -0.7)]),
        partie("10_personnages", V / "t05_personnages.wav", "Le saviez-vous ? Les héros de GTA 6", cartes=[(0, "personnages.png")]),
        partie("11_flash_alligator", V / "t06_flash.wav", "Flash spécial Leonida", cartes=[(0, "flash.png")]),
        partie("12_vicecity", V / "t08b_vicecity.wav", "Le saviez-vous ? Le retour de Vice City", cartes=[(0, "vicecity.png")]),
        partie("13_leonida", V / "t08_saviez2.wav", "Le saviez-vous ? Bienvenue à Leonida", cartes=[(0, "saviez2.png")]),
        partie("14_bugs", V / "t07_bugs.wav", T, clip=BUGS, credit=CREDIT_BUGS, surprise=55.5, texte2="SOUS LA CARTE ?!",
               gaps=[(5.9, 2.0), (13.0, 1.0), (19.4, 1.0), (30.0, 1.0), (43.2, 1.0), (55.0, 0.8)],
               plan=[(0, 20.0, 26.0, -1), (5.9, 0.0, 6.0, -0.85), (13.0, 7.5, 19.0, -1), (19.4, 32.0, 46.0, -1.3),
                     (30.0, 60.0, 72.0, -1), (36.0, 74.0, 86.0, -1.6), (43.2, 87.5, 100.0, -1.7),
                     (49.7, 103.0, 112.0, -1.7), (55.0, 128.0, 138.0, -1.2), (63.3, 139.0, 143.5, -0.9),
                     (67.9, 131.0, 138.0, -0.8)]),
        partie("15_streamers", V / "t07b_streamers.wav", "Les réactions des streamers", clip=BUGS, credit=CREDIT_BUGS,
               plan=[(0, 1.5, 6.0, -1), (5.0, 34.0, 40.0, -1.2), (10.0, 88.0, 94.0, -1)]),
        partie("16_reports", V / "t09_saviez3.wav", "Le saviez-vous ? Les reports de GTA 6", cartes=[(0, "saviez3.png")]),
        partie("17_top3", V / "t09d_top3.wav", "Le top 3 de Sunny du jour", clip=S / "parties/top3_clip.mp4",
               plan=json.loads((S / "parties/top3_plan.json").read_text()) if (S / "parties/top3_plan.json").exists() else [],
               surprise=json.loads((S / "parties/top3_surprise.json").read_text()) if (S / "parties/top3_surprise.json").exists() else None,
               texte2="NUMÉRO 1 !"),
        partie("18_defi_fin", V / "t10_fin.wav", "Le défi de Sunny", cartes=[(0, "fin.png")]),
        ecran_fin(OUT / "zz_fin_ecran.mp4"),
    ]
    if any(p is None for p in sec):
        print("parties manquantes : assemblage reporté"); return
    liste = S / "parties/liste.txt"
    # normalisation commune puis concaténation
    normes = []
    for p in sec:
        n = S / "parties" / f"norm_{p.name}"
        if not n.exists():
            run(["ffmpeg", "-v", "error", "-y", "-i", p, "-vf", "fps=25,scale=1920:1080,format=yuv420p", "-c:v", "libx264",
                 "-crf", "19", "-preset", "medium", "-c:a", "aac", "-ar", SR, "-ac", 2, "-b:a", "192k", n])
        normes.append(n)
    liste.write_text("".join(f"file '{n}'\n" for n in normes))
    final = V / "video2_jour_de_sortie.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", 0, "-i", liste, "-c", "copy", "-movflags", "+faststart", final])
    print(final, f"{duree(final) / 60:.2f} min")


if __name__ == "__main__":
    main()

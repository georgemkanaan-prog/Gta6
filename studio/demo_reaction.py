#!/usr/bin/env python3
"""Démo « explication puis surprise » de Sunny dans le studio Leonida Live.

- Visage : animation des lèvres (portrait) posée sur chaque posture (même visage : x0,612, décalage 173,0).
- Postures : changées selon la ligne de temps (ex. « montre » pendant l'explication, « repos » pendant la surprise).
- Effets calculés : respiration / balancement, zoom rapide + secousse sur la surprise, texte « QUOI ?! ».

    python demo_reaction.py --visage visage.mp4 --audio voix.wav --sortie demo.mp4 \
        --postures "0:montre.png,4.6:repos.png" --surprise 4.6 --tele tele.png
"""
import argparse
import math
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FPS = 25
W, H = 1920, 1080
TV = (820, 150, 960, 540)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ECH, DX, DY = 0.612, 173, 0                     # visage du portrait -> plan taille
OVALE = (365, 120, 535, 340)


def lire_video(chemin):
    w, h = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height", "-of", "csv=p=0", chemin],
                                   capture_output=True, text=True, check=True).stdout.strip().split(","))
    brut = subprocess.run(["ffmpeg", "-v", "error", "-i", chemin, "-r", str(FPS), "-f", "rawvideo",
                           "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(brut, np.uint8).reshape(-1, h, w, 3)


def detourer(img):
    from rembg import new_session, remove
    return remove(img, session=new_session("u2net_human_seg"), only_mask=True, post_process_mask=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--visage", required=True); ap.add_argument("--audio", required=True)
    ap.add_argument("--sortie", required=True); ap.add_argument("--postures", required=True)
    ap.add_argument("--surprise", type=float, required=True); ap.add_argument("--tele", required=True)
    ap.add_argument("--decor", default="studio/assets/studio.png")
    ap.add_argument("--titre", default="N°1 — Un alligator dans la piscine ?!")
    a = ap.parse_args()

    visage = lire_video(a.visage)
    duree = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  a.audio], capture_output=True, text=True).stdout)
    N = int(duree * FPS)

    # postures : image + masque de détourage + ovale du visage
    ovale = Image.new("L", (896, 1344), 0); ImageDraw.Draw(ovale).ellipse(OVALE, fill=255)
    ovale = (np.asarray(ovale.filter(ImageFilter.GaussianBlur(14)), np.float32) / 255)[..., None]
    postures = []
    for item in a.postures.split(","):
        t, chemin = item.split(":", 1)
        im = Image.open(chemin).convert("RGB")
        postures.append((float(t), np.asarray(im, np.float32), np.asarray(detourer(im), np.float32) / 255))
    postures.sort(key=lambda p: p[0])

    decor = Image.open(a.decor).convert("RGB")
    tele = Image.open(a.tele).convert("RGB")
    f = ImageFont.truetype(FONT, 46); grand = ImageFont.truetype(FONT, 150)
    hS = 1000; wS = int(896 * hS / 1344)                       # Sunny dans le studio

    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", a.audio, "-map", "0:v", "-map", "1:a", "-shortest",
                           "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                           a.sortie], stdin=subprocess.PIPE)
    for i in range(N):
        t = i / FPS
        _, img, msk = [p for p in postures if p[0] <= t][-1]
        # visage animé
        v = Image.fromarray(visage[min(i, len(visage) - 1)]).resize((round(visage.shape[2] * ECH),
                                                                      round(visage.shape[1] * ECH)), Image.LANCZOS)
        calque = img.copy(); va = np.asarray(v, np.float32)
        hh, ww = min(1344 - DY, va.shape[0]), min(896 - DX, va.shape[1])
        calque[DY:DY + hh, DX:DX + ww] = va[:hh, :ww]
        sunny = img * (1 - ovale) + calque * ovale
        # télé : image avec lent zoom
        z = 1 + 0.04 * t / max(duree, 1)
        tw, th = TV[2], TV[3]
        cw, ch = int(tele.width / z), int(tele.height / z)
        tv = tele.crop(((tele.width - cw) // 2, (tele.height - ch) // 2, (tele.width + cw) // 2,
                        (tele.height + ch) // 2)).resize((tw, th))
        cadre = decor.copy(); cadre.paste(tv, TV[:2])
        # Sunny : respiration + balancement
        resp = 1 + 0.006 * math.sin(2 * math.pi * t / 3.2)
        dx = 6 * math.sin(2 * math.pi * t / 4.5)
        s_img = Image.fromarray(sunny.clip(0, 255).astype(np.uint8)).resize((wS, int(hS * resp)))
        s_m = Image.fromarray((msk * 255).astype(np.uint8)).resize((wS, int(hS * resp)))
        sursaut = 0
        if t >= a.surprise:                                    # petit saut au moment de la surprise
            u = t - a.surprise
            sursaut = -int(28 * math.exp(-6 * u) * abs(math.sin(14 * u)))
        cadre.paste(s_img, (int(60 + dx), H - s_img.height + 40 + sursaut), s_m)
        # bandeau titre
        d = ImageDraw.Draw(cadre)
        d.rectangle((0, H - 110, W, H - 20), fill=(42, 15, 74)); d.rectangle((0, H - 110, 16, H - 20), fill=(255, 62, 154))
        d.text((50, H - 88), a.titre, font=f, fill=(255, 255, 255))
        # surprise : zoom rapide sur Sunny + secousse + « QUOI ?! »
        if t >= a.surprise:
            u = t - a.surprise
            zoom = 1 + 0.35 * (1 - math.exp(-9 * u))
            sx = 14 * math.exp(-5 * u) * math.sin(55 * u); sy = 10 * math.exp(-5 * u) * math.cos(47 * u)
            cx, cy = 420 + sx, 430 + sy                       # vers le visage de Sunny
            cw, ch = W / zoom, H / zoom
            x0 = min(max(0, cx - cw / 2), W - cw); y0 = min(max(0, cy - ch / 2), H - ch)
            cadre = cadre.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)
            if u > 0.12:
                d = ImageDraw.Draw(cadre)
                ech = min(1.0, (u - 0.12) * 6)
                fq = ImageFont.truetype(FONT, int(170 * (0.6 + 0.4 * ech)))
                txt = "QUOI ?!"
                x, y = 1060, 170
                d.text((x, y), txt, font=fq, fill=(255, 220, 0), stroke_width=12, stroke_fill=(42, 15, 74))
                if u > 0.5:
                    d.text((1010, 400), "UN ALLIGATOR ?!", font=ImageFont.truetype(FONT, 80), fill=(33, 212, 224),
                           stroke_width=8, stroke_fill=(42, 15, 74))
        ff.stdin.write(np.asarray(cadre, np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    print(a.sortie, f"{N / FPS:.1f} s")


if __name__ == "__main__":
    main()

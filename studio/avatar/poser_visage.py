#!/usr/bin/env python3
"""Pose le visage animé de Sunny (animations faites sur le portrait sunny.png) sur une autre image
dont le visage est le même, réduit et décalé (plan taille, postures...).

Le visage du plan taille = portrait x 0,612, décalé de (173, 0) : vérifié au pixel près (écart moyen < 1 %).

    python poser_visage.py --anim bibliotheque/sunny_portrait_01.mp4 --audio bibliotheque/sunny_portrait_01.wav \
        --image sunny_taille.png --sortie test.mp4
"""
import argparse
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("--anim", required=True); ap.add_argument("--audio"); ap.add_argument("--image", required=True)
ap.add_argument("--sortie", required=True)
ap.add_argument("--echelle", type=float, default=0.612); ap.add_argument("--decalage", default="173,0")
ap.add_argument("--visage", default="365,120,535,340", help="ovale animé (coordonnées de l'image cible)")
ap.add_argument("--fps", type=int, default=25)
a = ap.parse_args()

fond = Image.open(a.image).convert("RGB"); W, H = fond.size
dx, dy = map(int, a.decalage.split(","))
m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).ellipse(tuple(map(int, a.visage.split(","))), fill=255)
m = (np.asarray(m.filter(ImageFilter.GaussianBlur(14)), np.float32) / 255)[..., None]
f = np.asarray(fond, np.float32)

w0, h0 = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                  "stream=width,height", "-of", "csv=p=0", a.anim],
                                 capture_output=True, text=True, check=True).stdout.strip().split(","))
brut = subprocess.run(["ffmpeg", "-v", "error", "-i", a.anim, "-r", str(a.fps), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                      capture_output=True, check=True).stdout
images = np.frombuffer(brut, np.uint8).reshape(-1, h0, w0, 3)
sw, sh = round(w0 * a.echelle), round(h0 * a.echelle)

cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(a.fps), "-i", "-"]
if a.audio:
    cmd += ["-i", a.audio, "-map", "0:v", "-map", "1:a", "-shortest", "-c:a", "aac"]
ff = subprocess.Popen(cmd + ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", a.sortie], stdin=subprocess.PIPE)
for im in images:
    calque = f.copy()
    petit = np.asarray(Image.fromarray(im).resize((sw, sh), Image.LANCZOS), np.float32)
    x1, y1 = min(W, dx + sw), min(H, dy + sh)
    calque[dy:y1, dx:x1] = petit[: y1 - dy, : x1 - dx]
    ff.stdin.write((f * (1 - m) + calque * m).astype(np.uint8).tobytes())
ff.stdin.close(); ff.wait()
print(a.sortie, len(images), "images")

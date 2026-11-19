#!/usr/bin/env python3
"""Anime Sunny sur un NOUVEL audio en réutilisant des images déjà animées (sans relancer SadTalker).

Principe (« sélection d'unités », comme en synthèse vocale) :
  1. Bibliothèque = une vidéo déjà animée par SadTalker + l'audio qui l'a pilotée.
  2. Pour chaque image (1/25 s) du nouvel audio, on cherche dans la bibliothèque l'image dont le son
     (MFCC + énergie, avec ±2 images de contexte) ressemble le plus.
  3. Un Viterbi favorise les enchaînements d'images consécutives (mouvement fluide, pas de saccades).
  4. Seule la zone de la bouche est remplacée ; yeux et tête viennent d'une boucle aller-retour de la
     bibliothèque (clignements naturels).

    python reutiliser_levres.py --biblio anim.mp4 --biblio-audio anim.wav --audio nouveau.wav --sortie out.mp4
Plusieurs bibliothèques : répéter --biblio/--biblio-audio (même ordre). Plus la bibliothèque est longue,
meilleure est la synchronisation (30 à 60 s recommandées).
"""
import argparse
import subprocess

import librosa
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FPS = 25
SR = 16000
HOP = SR // FPS


def lire_video(chemin):
    w, h = map(int, subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
         "-of", "csv=p=0", chemin], capture_output=True, text=True, check=True).stdout.strip().split(","))
    brut = subprocess.run(["ffmpeg", "-v", "error", "-i", chemin, "-r", str(FPS), "-f", "rawvideo",
                           "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(brut, np.uint8).reshape(-1, h, w, 3)


def caracteristiques(wav_path, n):
    y, _ = librosa.load(wav_path, sr=SR)
    y = np.pad(y, (0, max(0, n * HOP - len(y))))
    mfcc = librosa.feature.mfcc(y=y, sr=SR, n_mfcc=13, hop_length=HOP, n_fft=1024)[:, :n]
    rms = librosa.feature.rms(y=y, hop_length=HOP, frame_length=1024)[:, :n]
    f = np.vstack([mfcc, 20 * np.log10(rms + 1e-4)]).T          # (n, 14)
    ctx = [np.roll(f, k, axis=0) for k in (-2, -1, 0, 1, 2)]       # ±2 images de contexte
    return np.hstack(ctx), rms[0]


def viterbi(cout, saut=2.0):
    """cout : (T, N). Rester sur l'image suivante de la bibliothèque est gratuit, sauter coûte `saut`."""
    T, N = cout.shape
    trans = np.full((N, N), saut)
    trans[np.arange(N - 1), np.arange(1, N)] = 0.0   # i -> i+1 : enchaînement naturel
    trans[np.arange(N), np.arange(N)] = 0.5          # rester sur place : léger coût
    D = cout[0].copy()
    arg = np.zeros((T, N), np.int32)
    for t in range(1, T):
        m = D[:, None] + trans
        arg[t] = m.argmin(0)
        D = m.min(0) + cout[t]
    chemin = np.zeros(T, np.int32)
    chemin[-1] = D.argmin()
    for t in range(T - 1, 0, -1):
        chemin[t - 1] = arg[t, chemin[t]]
    return chemin


def masque_bouche(h, w, centre, rayons, flou=18):
    m = Image.new("L", (w, h), 0)
    cx, cy = centre; rx, ry = rayons
    ImageDraw.Draw(m).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    return (np.asarray(m.filter(ImageFilter.GaussianBlur(flou)), np.float32) / 255)[..., None]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--biblio", action="append", required=True)
    ap.add_argument("--biblio-audio", action="append", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--bouche", default="445,445", help="centre de la bouche (x,y) dans l'image")
    ap.add_argument("--rayons", default="105,75", help="demi-largeur, demi-hauteur de la zone remplacée")
    a = ap.parse_args()

    images, feats = [], []
    for v, w in zip(a.biblio, a.biblio_audio):
        fr = lire_video(v)
        f, _ = caracteristiques(w, len(fr))
        images.append(fr); feats.append(f)
    lib = np.concatenate(images); flib = np.concatenate(feats)

    y, _ = librosa.load(a.audio, sr=SR)
    T = int(np.ceil(len(y) / HOP))
    fnew, _ = caracteristiques(a.audio, T)
    mu, sd = flib.mean(0), flib.std(0) + 1e-6
    A, B = (fnew - mu) / sd, (flib - mu) / sd
    cout = ((A[:, None, :] - B[None, :, :]) ** 2).mean(-1)          # (T, N)
    cout = cout / np.median(cout)
    chemin = viterbi(cout)

    N, h, w, _ = lib.shape
    m = masque_bouche(h, w, tuple(map(int, a.bouche.split(","))), tuple(map(int, a.rayons.split(","))))
    aller_retour = np.r_[np.arange(N), np.arange(N - 2, 0, -1)]      # boucle pour yeux / tête

    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                           "-r", str(FPS), "-i", "-", "-i", a.audio, "-map", "0:v", "-map", "1:a", "-shortest",
                           "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", a.sortie],
                          stdin=subprocess.PIPE)
    for t in range(T):
        fond = lib[aller_retour[t % len(aller_retour)]].astype(np.float32)
        bouche = lib[chemin[t]].astype(np.float32)
        ff.stdin.write((fond * (1 - m) + bouche * m).astype(np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    sauts = int((np.diff(chemin) != 1).sum())
    print(f"{a.sortie} : {T} images ({T / FPS:.1f} s), bibliothèque {N} images, {sauts} raccords")


if __name__ == "__main__":
    main()

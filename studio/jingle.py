#!/usr/bin/env python3
"""Jingle ORIGINAL style synthwave années 80 (6 s), entièrement synthétisé ici (aucun échantillon externe).
Basse en croches, accords pad, arpège, caisse claire à réverb, montée finale. Sortie : WAV 44,1 kHz stéréo."""
import sys
import numpy as np
import soundfile as sf

SR, BPM = 44100, 118
b = 60 / BPM
N = int(SR * 6.0)
t = np.arange(N) / SR
out = np.zeros((N, 2))

def note(m):
    return 440 * 2 ** ((m - 69) / 12)

def saw(f, d, det=0.0):
    tt = np.arange(int(SR * d)) / SR
    return sum(2 * ((tt * f * (1 + k * det)) % 1) - 1 for k in (-1, 0, 1)) / 3

def env(n, a=0.005, r=0.08):
    e = np.ones(n); ai, ri = int(SR * a), int(SR * r)
    e[:ai] = np.linspace(0, 1, ai); e[-ri:] *= np.linspace(1, 0, ri); return e

def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc; y[i] = acc
    return y

def add(sig, start, gain, pan=0.0):
    i = int(start * SR); j = min(N, i + len(sig)); s = sig[:j - i] * gain
    out[i:j, 0] += s * (1 - pan) ; out[i:j, 1] += s * (1 + pan)

prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]   # Am F C G
for bar, (root, chord) in enumerate(prog):
    t0 = bar * 4 * b * 0.75                     # 4 mesures en ~5,1 s
    for k in range(8):                           # basse en croches
        d = b * 0.75 / 2
        s = lowpass(saw(note(root - 12), d * 0.9, 0.003), 900) * env(int(SR * d * 0.9))
        add(s, t0 + k * d, 0.35)
    pad = sum(saw(note(m), 4 * b * 0.75, 0.006) for m in chord) / 3
    add(lowpass(pad, 2200) * env(len(pad), 0.15, 0.3), t0, 0.22)
    for k in range(8):                           # arpège
        d = b * 0.75 / 2; m = chord[k % 3] + 12 + (12 if k % 4 == 3 else 0)
        s = saw(note(m), d * 0.6, 0.002) * env(int(SR * d * 0.6), 0.002, 0.05)
        add(lowpass(s, 4000), t0 + k * d, 0.12, pan=0.4 if k % 2 else -0.4)
    for k in (1, 3):                             # caisse claire (bruit + queue)
        n = int(SR * 0.35); s = np.random.default_rng(bar * 10 + k).normal(0, 1, n) * np.exp(-np.arange(n) / (SR * 0.06))
        add(lowpass(s, 6000), t0 + k * b * 0.75, 0.22)
    for k in range(4):                           # grosse caisse
        n = int(SR * 0.25); tt = np.arange(n) / SR
        s = np.sin(2 * np.pi * (50 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 12)
        add(s, t0 + k * b * 0.75, 0.6)
# accord final tenu (A majeur, brillant) avec fondu
fin = sum(saw(note(m), 1.2, 0.008) for m in (57, 61, 64, 69)) / 4
add(lowpass(fin, 3000) * env(len(fin), 0.01, 0.9), 4.8, 0.3)
# réverb simple (échos décroissants)
rev = out.copy()
for d, g in ((0.083, 0.35), (0.131, 0.25), (0.197, 0.18), (0.29, 0.12)):
    k = int(d * SR); rev[k:] += out[:-k] * g
rev /= np.max(np.abs(rev)) * 1.12
sf.write(sys.argv[1], rev.astype(np.float32), SR)
print(sys.argv[1])

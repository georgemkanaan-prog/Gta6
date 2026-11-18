#!/usr/bin/env python3
"""Augmente localement le volume d'une zone (effet loupe / liquify), sans rien régénérer.

    python gonfler.py sunny.png sortie.png --centres 290,1020 570,1020 --rayon 230 --force 0.3
"""
import argparse

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


def gonfler(img: Image.Image, centres, rayon: float, force: float) -> Image.Image:
    a = np.array(img).astype(float)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    sx, sy = xx.copy(), yy.copy()
    for cx, cy in centres:
        dx, dy = xx - cx, yy - cy
        d = np.sqrt(dx ** 2 + dy ** 2) / rayon
        k = np.where(d < 1, 1 - force * (1 - d ** 2) ** 2, 1.0)  # <1 au centre = agrandissement, 1 au bord
        sx += dx * (k - 1)
        sy += dy * (k - 1)
    out = np.stack([map_coordinates(a[..., c], [sy, sx], order=3, mode="nearest") for c in range(3)], -1)
    return Image.fromarray(out.clip(0, 255).astype("uint8"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("entree"); ap.add_argument("sortie")
    ap.add_argument("--centres", nargs="+", default=["290,1020", "570,1020"])
    ap.add_argument("--rayon", type=float, default=230)
    ap.add_argument("--force", type=float, default=0.3)
    a = ap.parse_args()
    c = [tuple(map(float, s.split(","))) for s in a.centres]
    gonfler(Image.open(a.entree).convert("RGB"), c, a.rayon, a.force).save(a.sortie)
    print(a.sortie)

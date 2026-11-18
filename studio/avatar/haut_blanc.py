"""Recolore en blanc le haut rose de la base, en gardant sa forme, ses plis et ses ombres."""
import numpy as np
from PIL import Image, ImageFilter


def _peau(hsv):
    """Peau visible (orangée, saturée) : jamais recolorée, même si elle est entourée par le vêtement."""
    h, s = hsv[..., 0], hsv[..., 1]
    return (h > 0.0) & (h < 0.12) & (s > 0.25)


def masque_haut(img: Image.Image) -> Image.Image:
    from scipy import ndimage
    hsv = np.array(img.convert("HSV")).astype(float) / 255
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    rose = (h > 0.80) & (s > 0.10) & (v > 0.30)   # la peau est orangée (h ≈ 0.04)
    rose[: int(img.height * 0.55)] = False  # seulement le torse (pas les mèches ni les boucles d'oreilles)
    rose = ndimage.binary_closing(rose, iterations=4)
    lab, n = ndimage.label(rose)
    if n:
        tailles = ndimage.sum(rose, lab, range(1, n + 1))
        rose = np.isin(lab, [i + 1 for i, t in enumerate(tailles) if t > 0.05 * tailles.max()])
    # le vêtement est coupé par le bas de l'image : on le « ferme » pour combler les trous qui touchent le bord
    ferme = np.vstack([rose, np.ones((1, rose.shape[1]), bool)])
    rose = ndimage.binary_fill_holes(ferme)[:-1] & ~(ndimage.binary_fill_holes(ferme)[:-1] & ~rose & _peau(hsv))
    m = Image.fromarray((rose * 255).astype("uint8")).filter(ImageFilter.MaxFilter(3))
    return m.filter(ImageFilter.GaussianBlur(1.5))


def haut_blanc(img: Image.Image) -> tuple[Image.Image, Image.Image]:
    m = masque_haut(img)
    a = np.array(img).astype(float)
    lum = a @ np.array([0.299, 0.587, 0.114])
    lum = np.clip((lum - lum[np.array(m) > 128].min()) / (np.percentile(lum[np.array(m) > 128], 98) - lum[np.array(m) > 128].min()), 0, 1)
    blanc = (150 + 105 * lum[..., None]) * np.array([1.0, 0.99, 0.97])  # blanc cassé ombré
    out = Image.composite(Image.fromarray(blanc.clip(0, 255).astype("uint8")), img, m)
    return out, m

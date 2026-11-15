#!/usr/bin/env python3
"""Génère le décor du studio « Leonida Live » (1920x1080) avec une télé vide.

Sortie : assets/studio.png
L'écran de la télé est à l'emplacement défini par TV_* (repris dans monter_segment.sh).
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
# Zone de l'écran de la télé (x, y, largeur, hauteur) — garder synchronisé avec monter_segment.sh
TV_X, TV_Y, TV_W, TV_H = 820, 150, 960, 540

PINK, TEAL, ORANGE, NIGHT = (255, 62, 154), (33, 212, 224), (255, 138, 61), (42, 15, 74)
OUT = Path(__file__).parent / "assets" / "studio.png"


def font(size):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"):
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


img = Image.new("RGB", (W, H))
d = ImageDraw.Draw(img)

# Mur du fond : dégradé nuit -> coucher de soleil
for y in range(H):
    t = y / H
    c = lerp(NIGHT, PINK, t * 1.2) if t < 0.62 else lerp(lerp(NIGHT, PINK, 0.744), ORANGE, (t - 0.62) / 0.38)
    d.line([(0, y), (W, y)], fill=c)

# Soleil synthwave derrière la télé
sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(sun)
cx, cy, r = 1300, 420, 420
for i in range(r, 0, -2):
    sd.ellipse([cx - i, cy - i, cx + i, cy + i], fill=lerp(ORANGE, (255, 220, 120), 1 - i / r) + (255,))
for k, yy in enumerate(range(cy + 60, cy + r, 34)):
    sd.rectangle([cx - r, yy, cx + r, yy + 6 + k * 2], fill=(0, 0, 0, 0))
img.paste(sun, (0, 0), sun)

# Sol du plateau + grille néon
floor_y = 800
d.rectangle([0, floor_y, W, H], fill=(25, 8, 45))
for x in range(-2000, W + 2000, 120):
    d.line([(W // 2, floor_y), (x, H)], fill=TEAL, width=2)
for i in range(1, 9):
    y = floor_y + int((H - floor_y) * (i / 8) ** 1.8)
    d.line([(0, y), (W, y)], fill=TEAL, width=2)

# Palmiers stylisés (silhouettes)
def palm(x, base, h, s=1.0):
    d.line([(x, base), (x + 30 * s, base - h)], fill=(20, 5, 35), width=int(18 * s))
    top = (x + 30 * s, base - h)
    for dx, dy in [(-160, 40), (-120, -30), (160, 40), (120, -30), (0, -70), (-80, 80), (80, 80)]:
        d.line([top, (top[0] + dx * s, top[1] + dy * s)], fill=(20, 5, 35), width=int(14 * s))
palm(90, floor_y, 520)
palm(1850, floor_y, 600, 1.1)

# Halo néon autour de la télé
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.rounded_rectangle([TV_X - 60, TV_Y - 60, TV_X + TV_W + 60, TV_Y + TV_H + 60], 40, outline=TEAL + (255,), width=24)
glow = glow.filter(ImageFilter.GaussianBlur(28))
img.paste(glow, (0, 0), glow)

# Télé : cadre + pied
d.rounded_rectangle([TV_X - 28, TV_Y - 28, TV_X + TV_W + 28, TV_Y + TV_H + 28], 22, fill=(15, 15, 22))
d.rounded_rectangle([TV_X - 28, TV_Y - 28, TV_X + TV_W + 28, TV_Y + TV_H + 28], 22, outline=PINK, width=6)
d.rectangle([TV_X, TV_Y, TV_X + TV_W, TV_Y + TV_H], fill=(0, 0, 0))
d.rectangle([TV_X + TV_W // 2 - 20, TV_Y + TV_H + 28, TV_X + TV_W // 2 + 20, floor_y - 20], fill=(15, 15, 22))
d.rounded_rectangle([TV_X + TV_W // 2 - 160, floor_y - 30, TV_X + TV_W // 2 + 160, floor_y], 10, fill=(15, 15, 22))

# Bureau de la présentatrice (à gauche)
d.polygon([(120, 760), (700, 760), (740, 1000), (80, 1000)], fill=(30, 10, 55))
d.line([(120, 760), (700, 760)], fill=PINK, width=8)
d.text((410, 880), "LEONIDA LIVE", font=font(52), fill=TEAL, anchor="mm")

# Logo en haut à gauche
d.rounded_rectangle([40, 36, 470, 120], 18, fill=(0, 0, 0))
d.text((255, 78), "☀ LEONIDA LIVE", font=font(44), fill=PINK, anchor="mm")

OUT.parent.mkdir(parents=True, exist_ok=True)
img.save(OUT)
print(f"Décor écrit : {OUT}  (écran TV : x={TV_X} y={TV_Y} {TV_W}x{TV_H})")

#!/usr/bin/env python3
"""Dessine le studio « Vice City by night » de Leonida Live (1920x1080), sans aucune image Rockstar.

Ciel synthwave, soleil rayé, skyline aux fenêtres allumées, mer, palmiers, enseignes néon,
grand écran (même position que l'ancien studio : TV = 820,150,960,540) et bureau néon.
Usage : decor_vice_city.py <sortie.png>
"""
import math
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
TV = (820, 150, 960, 540)
HORIZON = 800
B = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
BI = "/usr/share/fonts/opentype/inter/InterDisplay-BoldItalic.otf"
ROSE, CYAN, JAUNE, VIOLET = (255, 62, 154), (33, 230, 240), (255, 214, 60), (150, 70, 255)
random.seed(6)


def degrade(im, haut, bas, y0, y1):
    d = ImageDraw.Draw(im)
    for y in range(y0, y1):
        u = (y - y0) / max(1, y1 - y0 - 1)
        d.line((0, y, W, y), fill=tuple(int(a + (b - a) * u) for a, b in zip(haut, bas)))


def lueur(im, dessin, rayon=18, force=2):
    """Ajoute un calque néon flouté (halo) sous le dessin net."""
    calque = Image.new("RGBA", im.size, (0, 0, 0, 0)); dessin(ImageDraw.Draw(calque))
    halo = calque.filter(ImageFilter.GaussianBlur(rayon))
    for _ in range(force):
        im.alpha_composite(halo)
    im.alpha_composite(calque)


def palmier(d, x, y, h, sens=1, coul=(24, 8, 40)):
    pts = []
    for i in range(21):                                  # tronc légèrement courbé
        u = i / 20
        pts.append((x + sens * 60 * u * u, y - h * u))
    for i in range(20):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        e = 22 - 12 * i / 20
        d.polygon([(x0 - e, y0), (x0 + e, y0), (x1 + e * 0.95, y1), (x1 - e * 0.95, y1)], fill=coul)
        if i % 2 == 0:
            d.line((x0 - e, y0, x0 + e, y0 - 4), fill=(40, 16, 60), width=2)
    cx, cy = pts[-1]
    for a in range(0, 360, 32):                          # palmes
        ang = math.radians(a + 10)
        long_ = h * 0.42
        pts_f = []
        for k in range(16):
            u = k / 15
            px = cx + math.cos(ang) * long_ * u
            py = cy + math.sin(ang) * long_ * u * 0.55 + (long_ * 0.35) * u * u
            pts_f.append((px, py))
        bord_a, bord_b = [], []
        for k, (px, py) in enumerate(pts_f):
            e = 26 * math.sin(math.pi * k / 15) + 2
            nx, ny = -math.sin(ang), math.cos(ang)
            bord_a.append((px + nx * e, py + ny * e)); bord_b.append((px - nx * e * 0.4, py - ny * e * 0.4))
        d.polygon(bord_a + bord_b[::-1], fill=coul)
    d.ellipse((cx - 22, cy - 18, cx + 22, cy + 22), fill=coul)


def main(sortie):
    im = Image.new("RGBA", (W, H))
    degrade(im, (12, 6, 38), (96, 22, 110), 0, 520)
    degrade(im, (96, 22, 110), (236, 70, 120), 520, HORIZON)
    d = ImageDraw.Draw(im)
    for _ in range(140):                                 # étoiles
        x, y = random.randrange(W), random.randrange(420)
        r = random.choice((1, 1, 1, 2))
        d.ellipse((x, y, x + r, y + r), fill=(255, 255, 255, random.randint(90, 220)))

    # soleil rayé synthwave
    sol = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sol)
    cx, cy, r = 470, 640, 250
    for y in range(cy - r, cy + r):
        u = (y - (cy - r)) / (2 * r)
        coul = tuple(int(a + (b - a) * u) for a, b in zip((255, 220, 90), (255, 60, 150)))
        dx = int(math.sqrt(max(0, r * r - (y - cy) ** 2)))
        bande = y > cy - 60 and ((y - cy + 60) // 14) % 3 == 0
        if not bande:
            ds.line((cx - dx, y, cx + dx, y), fill=coul + (255,))
    halo = sol.filter(ImageFilter.GaussianBlur(40))
    im.alpha_composite(halo); im.alpha_composite(sol)

    # skyline (deux plans) avec fenêtres allumées
    for plan, (base_c, hmin, hmax, larg, fen) in enumerate([((58, 20, 92), 140, 330, (60, 130), 0.25),
                                                             ((30, 10, 55), 90, 260, (70, 150), 0.45)]):
        x = -20
        while x < W:
            w = random.randint(*larg); h = random.randint(hmin, hmax)
            top = HORIZON - h
            d.rectangle((x, top, x + w, HORIZON), fill=base_c)
            if random.random() < 0.3:                    # immeuble art déco : gradins
                d.rectangle((x + w * 0.2, top - 40, x + w * 0.8, top), fill=base_c)
                d.rectangle((x + w * 0.4, top - 70, x + w * 0.6, top - 40), fill=base_c)
            for fy in range(int(top) + 12, HORIZON - 14, 18):
                for fx in range(x + 8, x + w - 8, 14):
                    if random.random() < fen:
                        c = random.choice([(255, 200, 120), (120, 230, 255), (255, 120, 200), (255, 230, 160)])
                        d.rectangle((fx, fy, fx + 6, fy + 8), fill=c + (random.randint(150, 255),))
            x += w + random.randint(2, 18)

    # mer + reflets
    degrade_mer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dm = ImageDraw.Draw(degrade_mer)
    for y in range(HORIZON, H):
        u = (y - HORIZON) / (H - HORIZON)
        dm.line((0, y, W, y), fill=(int(40 - 25 * u), int(12 - 6 * u), int(70 - 40 * u), 255))
    im.alpha_composite(degrade_mer)
    d = ImageDraw.Draw(im)
    for y in range(HORIZON + 6, HORIZON + 120, 7):       # reflet du soleil
        w = int(260 * (1 - (y - HORIZON) / 140)) + random.randint(-30, 30)
        d.line((cx - w, y, cx + w, y), fill=(255, 110, 160, 150), width=2)

    # sol grille néon (plateau du studio)
    sol_y = 900
    grille = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dg = ImageDraw.Draw(grille)
    dg.rectangle((0, sol_y, W, H), fill=(22, 6, 40, 255))
    for i in range(-30, 31):
        dg.line((W / 2 + i * 26, sol_y, W / 2 + i * 190, H), fill=ROSE + (200,), width=2)
    y, pas = sol_y, 8
    while y < H:
        dg.line((0, y, W, y), fill=ROSE + (200,), width=2); y += pas; pas *= 1.35
    im.alpha_composite(grille)

    # palmiers
    d = ImageDraw.Draw(im)
    palmier(d, 70, 960, 620, 1); palmier(d, 300, 940, 430, 1, (34, 12, 54)); palmier(d, 1870, 960, 660, -1)

    # enseignes néon
    def enseignes(dc):
        f1 = ImageFont.truetype(BI, 64); f2 = ImageFont.truetype(B, 34)
        dc.text((1000, 62), "Vice City", font=f1, fill=ROSE, anchor="mm")
        dc.text((1420, 64), "LEONIDA LIVE", font=f2, fill=CYAN, anchor="mm")
        dc.rounded_rectangle((830, 18, 1590, 106), 22, outline=ROSE, width=4)
        dc.line((1200, 34, 1200, 90), fill=CYAN, width=3)
    lueur(im, enseignes, 14, 2)

    # grand écran : cadre néon cyan + rose, halo
    def ecran(dc):
        x, y, w, h = TV
        dc.rounded_rectangle((x - 30, y - 30, x + w + 30, y + h + 30), 26, outline=CYAN, width=7)
        dc.rounded_rectangle((x - 16, y - 16, x + w + 16, y + h + 16), 18, outline=ROSE, width=4)
    lueur(im, ecran, 22, 2)
    d = ImageDraw.Draw(im)
    x, y, w, h = TV
    d.rounded_rectangle((x - 12, y - 12, x + w + 12, y + h + 12), 14, fill=(8, 4, 16))
    d.rectangle((x, y, x + w, y + h), fill=(0, 0, 0))
    d.rectangle((x + w // 2 - 18, y + h + 34, x + w // 2 + 18, sol_y), fill=(14, 6, 24))
    d.rounded_rectangle((x + w // 2 - 170, sol_y - 18, x + w // 2 + 170, sol_y + 6), 10, fill=(14, 6, 24))

    # bureau néon (derrière Sunny)
    def bureau(dc):
        dc.polygon([(110, 770), (720, 770), (760, 1000), (70, 1000)], fill=(30, 10, 52))
        dc.line((110, 770, 720, 770), fill=ROSE, width=6)
        dc.line((70, 1000, 760, 1000), fill=CYAN, width=4)
        fb = ImageFont.truetype(B, 58)
        dc.text((415, 880), "LEONIDA LIVE", font=fb, fill=CYAN, anchor="mm")
    lueur(im, bureau, 12, 1)
    im.convert("RGB").save(sortie)
    print(sortie)


if __name__ == "__main__":
    main(sys.argv[1])

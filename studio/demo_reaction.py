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
from pathlib import Path

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


def detourer(img, bras=None):
    """Détourage de Sunny ; `bras` = segments du bras tendu (souvent coupé par le détourage), ajoutés s'ils
    sont couleur peau."""
    import cv2
    from rembg import new_session, remove
    m = np.asarray(remove(img, session=new_session("u2net_human_seg"), only_mask=True, post_process_mask=True))
    if bras:
        zone = Image.new("L", img.size, 0); dz = ImageDraw.Draw(zone)
        for p1, p2 in zip(bras, bras[1:]):
            dz.line([p1, p2], fill=255, width=96)
        hsv = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2HSV).astype(int)
        peau = ((hsv[..., 0] <= 22) | (hsv[..., 0] >= 172)) & (hsv[..., 1] > 55) & (hsv[..., 2] > 70)
        ajout = (np.asarray(zone) > 0) & peau
        ajout = cv2.morphologyEx(ajout.astype(np.uint8) * 255, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        ajout = cv2.morphologyEx(ajout, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        m = np.maximum(m, cv2.GaussianBlur(ajout, (0, 0), 1.5))
    return Image.fromarray(m)


BRAS_TENDUS = {"montre": [(645, 480), (800, 500), (905, 470)]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--visage", required=True); ap.add_argument("--audio", required=True)
    ap.add_argument("--sortie", required=True); ap.add_argument("--postures", required=True)
    ap.add_argument("--surprise", type=float, required=True); ap.add_argument("--tele")
    ap.add_argument("--decor", default="studio/assets/studio.png")
    ap.add_argument("--bas", type=int, default=1170, help="ligne où Sunny est coupée (sous le haut du short, avant les doigts)")
    ap.add_argument("--clip", help="extrait vidéo affiché dans la télé (remplace --tele)")
    ap.add_argument("--clip-debut", type=float, default=0, help="instant où l'extrait démarre (avant : 1re image)")
    ap.add_argument("--plan-tele", help="« instant:debut-fin:vitesse;… » : à partir de l'instant, la télé passe ce morceau "
                    "du clip en boucle aller-retour à cette vitesse")
    ap.add_argument("--ralenti", help="debut_clip,fin_clip,instant : revoit ce passage à mi-vitesse à partir de l'instant")
    ap.add_argument("--zoom-clip", type=float, default=1.0, help="0.75 = recadrage au centre (clip d'un créateur)")
    ap.add_argument("--credit", help="crédit affiché dans la télé, ex. « Clip : @pseudo »")
    ap.add_argument("--surprise-duree", type=float, default=3.0, help="durée du zoom surprise avant retour")
    ap.add_argument("--son-clip", type=float, default=0.12, help="volume du son du clip en fond (0 = coupé)")
    ap.add_argument("--texte2", default="UN ALLIGATOR ?!")
    ap.add_argument("--titre", default="N°1 — Un alligator dans la piscine ?!")
    a = ap.parse_args()

    # visage animé lu image par image (le charger en entier coûte plusieurs Go)
    vw, vh = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                      "stream=width,height", "-of", "csv=p=0", a.visage],
                                     capture_output=True, text=True, check=True).stdout.strip().split(","))
    lecteur = subprocess.Popen(["ffmpeg", "-v", "error", "-i", a.visage, "-r", str(FPS), "-f", "rawvideo",
                                "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    derniere = [np.zeros((vh, vw, 3), np.uint8)]

    def image_visage():
        b = lecteur.stdout.read(vw * vh * 3)
        if len(b) == vw * vh * 3:
            derniere[0] = np.frombuffer(b, np.uint8).reshape(vh, vw, 3)
        return derniere[0]
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
        bras = next((v for k, v in BRAS_TENDUS.items() if k in Path(chemin).name), None)
        postures.append((float(t), np.asarray(im, np.float32), np.asarray(detourer(im, bras), np.float32) / 255))
    postures.sort(key=lambda p: p[0])

    decor = Image.open(a.decor).convert("RGB")
    tele = Image.open(a.tele).convert("RGB") if a.tele else None
    plan = []
    if a.plan_tele:
        for bloc in a.plan_tele.split(";"):
            ti, morceau, vit = bloc.split(":")
            c0, c1 = map(float, morceau.split("-"))
            plan.append((float(ti), c0, c1, float(vit)))
        plan.sort()

    clip = None
    if a.clip:
        # seuls les morceaux utilisés par le plan sont décodés, recadrés et réduits par ffmpeg (peu de mémoire)
        z = a.zoom_clip
        filtre = f"crop=iw*{z}:ih*{z},scale={TV[2]}:{TV[3]},fps={FPS}"
        morceaux = ([(0, 0.1)] + [(c0, c1) for _, c0, c1, _ in plan]) if plan else [(0, 1e6)]   # + 1re image (avant le plan)
        clip = {}
        for c0, c1 in morceaux:
            brut = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{c0:.3f}", "-to", f"{c1 + 0.1:.3f}", "-i", a.clip,
                                   "-vf", filtre, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  capture_output=True, check=True).stdout
            fr = np.frombuffer(brut, np.uint8).reshape(-1, TV[3], TV[2], 3)
            for k in range(len(fr)):
                clip[int(round(c0 * FPS)) + k] = Image.fromarray(fr[k])
    if a.ralenti:
        r0, r1, rt = map(float, a.ralenti.split(","))

    def trame(k):
        if k in clip:
            return clip[k]
        cles = sorted(clip)
        return clip[min(cles, key=lambda c: abs(c - k))]

    def image_tele(t):
        if clip is not None and plan and t >= plan[0][0]:
            ti, c0, c1, vit = [p for p in plan if p[0] <= t][-1]
            L = max(0.04, c1 - c0)
            if vit < 0:                                         # vitesse négative : lecture avant puis arrêt sur image
                pos = min(c1, c0 + (t - ti) * -vit)
            else:
                u = ((t - ti) * vit) % (2 * L)                  # aller-retour : pas de saut d'image
                pos = c0 + (u if u < L else 2 * L - u)
            return trame(int(pos * FPS))
        if clip is None:
            z = 1 + 0.04 * t / max(duree, 1)
            cw, ch = int(tele.width / z), int(tele.height / z)
            return tele.crop(((tele.width - cw) // 2, (tele.height - ch) // 2, (tele.width + cw) // 2,
                              (tele.height + ch) // 2)).resize((TV[2], TV[3]))
        if a.ralenti and t >= rt:                              # ralenti en boucle
            n = int((r1 - r0) * FPS * 2)
            k = int((t - rt) * FPS) % max(1, n)
            return trame(int(r0 * FPS + k / 2))
        return trame(max(0, int((t - a.clip_debut) * FPS)))
    f = ImageFont.truetype(FONT, 46); grand = ImageFont.truetype(FONT, 150)
    hS = 820; wS = int(896 * hS / a.bas)                       # Sunny dans le studio (coupée sous le short)
    X_SUNNY = 140
    cadre_tv = decor.crop((TV[0] - 28, TV[1] - 28, TV[0] + TV[2] + 28, TV[1] + TV[3] + 28))
    masque_tv = Image.new("L", cadre_tv.size, 0)
    ImageDraw.Draw(masque_tv).rounded_rectangle((0, 0, cadre_tv.width - 1, cadre_tv.height - 1), 22, fill=255)

    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", a.audio]
    debut_son = None
    if a.clip and a.son_clip > 0:
        debut_son = min([p[0] for p in plan] or [a.clip_debut])
    if debut_son is not None and debut_son < duree:      # son du clip en fond, en boucle, sous la voix
        ms = int(debut_son * 1000)
        cmd += ["-stream_loop", "-1", "-i", a.clip, "-filter_complex",
                f"[2:a]aresample=44100,volume={a.son_clip},adelay={ms}|{ms}[f];"
                f"[1:a]aresample=44100[v];[v][f]amix=inputs=2:duration=first:normalize=0[a]",
                "-map", "0:v", "-map", "[a]"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    ff = subprocess.Popen(cmd + ["-t", f"{duree:.2f}", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                                 "-c:a", "aac", "-b:a", "192k", a.sortie], stdin=subprocess.PIPE)
    for i in range(N):
        t = i / FPS
        _, img, msk = [p for p in postures if p[0] <= t][-1]
        # visage animé
        v = Image.fromarray(image_visage()).resize((round(vw * ECH), round(vh * ECH)), Image.LANCZOS)
        calque = img.copy(); va = np.asarray(v, np.float32)
        hh, ww = min(1344 - DY, va.shape[0]), min(896 - DX, va.shape[1])
        calque[DY:DY + hh, DX:DX + ww] = va[:hh, :ww]
        sunny = img * (1 - ovale) + calque * ovale
        tv = image_tele(t)
        cadre = decor.copy()
        # Sunny : respiration + balancement
        resp = 1 + 0.003 * math.sin(2 * math.pi * t / 3.2)
        dx = 3 * math.sin(2 * math.pi * t / 4.5)
        s_img = Image.fromarray(sunny[:a.bas].clip(0, 255).astype(np.uint8)).resize((wS, int(hS * resp)))
        s_m = Image.fromarray((msk[:a.bas] * 255).astype(np.uint8)).resize((wS, int(hS * resp)))
        sursaut = 0
        en_surprise = a.surprise <= t < a.surprise + a.surprise_duree + 0.6
        if en_surprise:                                        # petit saut au moment de la surprise
            u = t - a.surprise
            sursaut = -int(28 * math.exp(-6 * u) * abs(math.sin(14 * u)))
        # bas de l'image (short) posé sur le bandeau titre ; la respiration étire vers le haut
        cadre.paste(s_img, (int(X_SUNNY + dx), H - 110 - s_img.height + sursaut), s_m)
        cadre.paste(tv, TV[:2])
        # crédit discret : petit, semi-transparent, 3 premières secondes de l'extrait seulement
        debut_clip = plan[0][0] if plan else a.clip_debut
        if a.credit and clip is not None and debut_clip <= t < debut_clip + 3:
            fc = ImageFont.truetype(FONT, 16)
            calque_c = Image.new("RGBA", cadre.size, (0, 0, 0, 0)); dc = ImageDraw.Draw(calque_c)
            fondu = min(1.0, (t - debut_clip) / 0.3, (debut_clip + 3 - t) / 0.3)
            tw_ = dc.textlength(a.credit, font=fc)
            dc.text((TV[0] + TV[2] - tw_ - 14, TV[1] + TV[3] - 26), a.credit, font=fc,
                    fill=(255, 255, 255, int(150 * fondu)))
            cadre = Image.alpha_composite(cadre.convert("RGBA"), calque_c).convert("RGB")
        # bandeau titre
        d = ImageDraw.Draw(cadre)
        d.rectangle((0, H - 110, W, H - 20), fill=(42, 15, 74)); d.rectangle((0, H - 110, 16, H - 20), fill=(255, 62, 154))
        d.text((50, H - 88), a.titre, font=f, fill=(255, 255, 255))
        # surprise : zoom rapide sur Sunny + secousse + « QUOI ?! »
        if en_surprise:
            u = t - a.surprise
            zoom = 1 + 0.35 * (1 - math.exp(-9 * u))
            if u > a.surprise_duree:                           # retour doux au plan large
                zoom = 1 + 0.35 * max(0.0, 1 - (u - a.surprise_duree) / 0.6)
            sx = 14 * math.exp(-5 * u) * math.sin(55 * u); sy = 10 * math.exp(-5 * u) * math.cos(47 * u)
            cx = X_SUNNY + 450 * wS / 896 + sx                # vers le visage de Sunny
            cy = H - 110 - hS + 230 * hS / a.bas + 120 + sy
            cw, ch = W / zoom, H / zoom
            x0 = min(max(0, cx - cw / 2), W - cw); y0 = min(max(0, cy - ch / 2), H - ch)
            cadre = cadre.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.BICUBIC)
            if 0.12 < u < a.surprise_duree:
                d = ImageDraw.Draw(cadre)
                ech = min(1.0, (u - 0.12) * 6)
                fq = ImageFont.truetype(FONT, int(170 * (0.6 + 0.4 * ech)))
                txt = "QUOI ?!"
                x, y = 1060, 170
                d.text((x, y), txt, font=fq, fill=(255, 220, 0), stroke_width=12, stroke_fill=(42, 15, 74))
                if u > 0.5:
                    d.text((1010, 400), a.texte2, font=ImageFont.truetype(FONT, 80), fill=(33, 212, 224),
                           stroke_width=8, stroke_fill=(42, 15, 74))
        ff.stdin.write(np.asarray(cadre, np.uint8).tobytes())
    ff.stdin.close(); ff.wait()
    print(a.sortie, f"{N / FPS:.1f} s")


if __name__ == "__main__":
    main()

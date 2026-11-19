#!/usr/bin/env python3
"""Postures de Sunny (gestes) à partir de l'image validée sunny_taille.png.

Seuls les bras et les mains changent : les anciens bras sont effacés, les nouveaux sont esquissés
(position imposée), puis l'IA fait le rendu de cette seule zone. Visage, cheveux, maillot, short et décor
restent identiques, donc l'animation du visage (poser_visage.py) se pose sur toutes les postures.

    python postures.py --posture explique --sortie posture_explique.png --graine 1
    python postures.py --posture surprise --sortie guide.png --guide-seulement
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ICI = Path(__file__).parent
MODELE = "Lykon/dreamshaper-xl-lightning"
EPAULES = {"g": (245, 480), "d": (640, 480)}
ANCIENS_BRAS = [[(240, 480), (175, 880), (70, 1300), (60, 1344)], [(645, 480), (725, 880), (825, 1300), (835, 1344)]]
VISAGE = (335, 95, 575, 345)

# chaque posture : coudes, poignets (gauche, droite), consigne
POSTURES = {
    "explique": {
        "bras": [[(245, 480), (215, 820), (335, 790)], [(640, 480), (675, 820), (560, 790)]],
        "mains": [(335, 790), (560, 790)],
        "prompt": "both forearms raised forward at waist height, both hands open in front of her belly with palms up, "
                  "explaining gesture, slender feminine fingers, five fingers on each hand",
    },
    "montre": {   # bras droit (côté droit de l'image) tendu vers la télé, main hors du cadre ; l'autre bras au repos
        "bras": [[(240, 480), (175, 880), (70, 1300)], [(645, 480), (800, 500), (905, 470)]],
        "mains": [(70, 1300), (905, 470)],
        "prompt": "her left arm extended straight out to the side at shoulder height pointing out of the frame, "
                  "her other arm relaxed down along her side",
    },
    "surprise": {
        "bras": [[(245, 480), (150, 700), (190, 520)], [(640, 480), (745, 700), (705, 520)]],
        "mains": [(190, 520), (705, 520)],
        "prompt": "both hands raised up beside her shoulders with open palms facing forward, surprised excited "
                  "gesture, slender feminine fingers, five fingers on each hand",
    },
}
PROMPT = ("3d video game character, unreal engine 5 render, young blonde woman in a white v-neck bikini top and beige "
          "denim shorts, {geste}, smooth tanned skin, sunny street background")
NEGATIF = ("extra arms, extra hands, extra fingers, six fingers, missing fingers, fused fingers, deformed hands, fist, "
           "claws, bad anatomy, long thumb, blurry, nude, nsfw, cartoon, text, watermark")


# squelette OpenPose (COCO 18 points) de la pose de base ; les bras sont remplacés par ceux de la posture
POINTS_FIXES = {0: (450, 215), 1: (445, 420), 2: (245, 480), 5: (640, 480), 8: (300, 1000), 11: (600, 1000),
                9: (285, 1344), 12: (615, 1344), 14: (405, 180), 15: (495, 180), 16: (365, 205), 17: (535, 205)}
MEMBRES = [(1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7), (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),
           (1, 0), (0, 14), (14, 16), (0, 15), (15, 17)]
COULEURS = [(255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0), (0, 255, 0),
            (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255), (0, 0, 255), (85, 0, 255),
            (170, 0, 255), (255, 0, 255), (255, 0, 170), (255, 0, 85)]


def squelette(taille, posture):
    """Image OpenPose (fond noir, membres colorés) : la position imposée à l'IA."""
    import math
    pts = dict(POINTS_FIXES)
    (g_ep, g_co, g_po), (d_ep, d_co, d_po) = posture["bras"]
    pts.update({3: g_co, 4: g_po, 6: d_co, 7: d_po})
    img = np.zeros((taille[1], taille[0], 3), np.uint8)
    for i, (a, b) in enumerate(MEMBRES):
        if a in pts and b in pts:
            (x1, y1), (x2, y2) = pts[a], pts[b]
            L = math.hypot(x2 - x1, y2 - y1); ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
            poly = cv2.ellipse2Poly((int((x1 + x2) / 2), int((y1 + y2) / 2)), (int(L / 2), 8), int(ang), 0, 360, 1)
            cv2.fillConvexPoly(img, poly, [int(c * 0.6) for c in COULEURS[i]])
    for k, (x, y) in pts.items():
        cv2.circle(img, (int(x), int(y)), 8, COULEURS[k], -1)
    return Image.fromarray(img)


def tracer(d, points, largeur):
    for p1, p2 in zip(points, points[1:]):
        d.line([p1, p2], fill=255, width=largeur)
    for x, y in points:
        d.ellipse((x - largeur // 2, y - largeur // 2, x + largeur // 2, y + largeur // 2), fill=255)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entree", default=str(ICI / "sunny_taille.png"))
    ap.add_argument("--posture", choices=POSTURES, required=True)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--graine", type=int, default=1); ap.add_argument("--force", type=float, default=0.8)
    ap.add_argument("--guide-seulement", action="store_true")
    ap.add_argument("--controle", type=float, default=0.0, help="> 0 : squelette OpenPose imposé (ControlNet)")
    a = ap.parse_args()
    P = POSTURES[a.posture]
    img = Image.open(a.entree).convert("RGB")
    W, H = img.size

    # 1. anciens bras effacés (remplissage depuis le décor / le corps voisins)
    vieux = Image.new("L", (W, H), 0); dv = ImageDraw.Draw(vieux)
    for b in ANCIENS_BRAS:
        tracer(dv, b[1:], 135)
        dv.line([b[0], b[1]], fill=255, width=95)
    base = cv2.inpaint(np.array(img), np.array(vieux), 25, cv2.INPAINT_TELEA)

    # 2. nouveaux bras esquissés en couleur de peau (le haut du bras part de l'épaule d'origine)
    neuf = Image.new("L", (W, H), 0); dn = ImageDraw.Draw(neuf)
    for b in P["bras"]:
        dn.line([b[0], b[1]], fill=255, width=72); tracer(dn, b[1:], 62)
    for x, y in P["mains"]:
        dn.ellipse((x - 42, y - 50, x + 42, y + 50), fill=255)
    peau = np.array(img)[600:800, 230:300].reshape(-1, 3).mean(0)
    mn = np.array(neuf.filter(ImageFilter.GaussianBlur(4)), np.float32)[..., None] / 255
    guide = (base * (1 - mn) + peau * mn).clip(0, 255).astype(np.uint8)
    guide = Image.fromarray(guide)
    if a.guide_seulement:
        guide.save(a.sortie); print(a.sortie); return

    # 3. rendu IA sur la zone des bras (anciens + nouveaux), visage exclu
    m = Image.fromarray(np.maximum(np.array(vieux), np.array(neuf))).filter(ImageFilter.MaxFilter(9))
    ImageDraw.Draw(m).ellipse(VISAGE, fill=0)
    m = m.filter(ImageFilter.GaussianBlur(10))
    import torch
    from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLInpaintPipeline
    extra = {}
    if a.controle > 0:
        from diffusers import ControlNetModel, StableDiffusionXLControlNetInpaintPipeline
        cn = ControlNetModel.from_pretrained("xinsir/controlnet-openpose-sdxl-1.0", torch_dtype=torch.bfloat16)
        p = StableDiffusionXLControlNetInpaintPipeline.from_pretrained(MODELE, controlnet=cn,
                                                                       torch_dtype=torch.bfloat16, variant="fp16")
        sq = squelette((W, H), P); sq.save(a.sortie.replace(".png", ".squelette.png"))
        extra = dict(control_image=sq, controlnet_conditioning_scale=a.controle)
    else:
        p = StableDiffusionXLInpaintPipeline.from_pretrained(MODELE, torch_dtype=torch.bfloat16, variant="fp16")
    p.scheduler = DPMSolverMultistepScheduler.from_config(p.scheduler.config, use_karras_sigmas=True,
                                                          algorithm_type="sde-dpmsolver++")
    p.set_progress_bar_config(disable=True)
    pr = PROMPT.format(geste=P["prompt"])
    out = p(prompt=pr, prompt_2=pr, negative_prompt=NEGATIF, image=guide, mask_image=m, strength=a.force,
            num_inference_steps=round(8 / a.force), guidance_scale=2.0, width=W, height=H,
            generator=torch.Generator().manual_seed(a.graine), **extra).images[0]
    Image.composite(out, img, m).save(a.sortie)
    print(a.sortie)


if __name__ == "__main__":
    main()

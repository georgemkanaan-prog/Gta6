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
    m = Image.fromarray(np.maximum(np.array(vieux), np.array(neuf))).filter(ImageFilter.MaxFilter(15))
    ImageDraw.Draw(m).ellipse(VISAGE, fill=0)
    m = m.filter(ImageFilter.GaussianBlur(10))
    import torch
    from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLInpaintPipeline
    p = StableDiffusionXLInpaintPipeline.from_pretrained(MODELE, torch_dtype=torch.bfloat16, variant="fp16")
    p.scheduler = DPMSolverMultistepScheduler.from_config(p.scheduler.config, use_karras_sigmas=True,
                                                          algorithm_type="sde-dpmsolver++")
    p.set_progress_bar_config(disable=True)
    pr = PROMPT.format(geste=P["prompt"])
    out = p(prompt=pr, prompt_2=pr, negative_prompt=NEGATIF, image=guide, mask_image=m, strength=a.force,
            num_inference_steps=round(8 / a.force), guidance_scale=2.0, width=W, height=H,
            generator=torch.Generator().manual_seed(a.graine)).images[0]
    Image.composite(out, img, m).save(a.sortie)
    print(a.sortie)


if __name__ == "__main__":
    main()

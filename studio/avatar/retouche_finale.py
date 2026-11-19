#!/usr/bin/env python3
"""Retouches ciblées sur une image validée, zone par zone (le reste de l'image est conservé au pixel près).

    python retouche_finale.py zone  --entree img.png --sortie out.png --ellipse x0,y0,x1,y1 --quoi epaule --graine 1
    python retouche_finale.py zone  --entree img.png --sortie out.png --ellipse x0,y0,x1,y1 --quoi mains --graine 1
    python retouche_finale.py peau  --entree img.png --sortie out.png --depuis-y 430
"""
import argparse

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MODELE = "Lykon/dreamshaper-xl-lightning"
STYLE = "3d video game character, unreal engine 5 render, semi-realistic, detailed, sharp focus"
QUOI = {
    "epaule": ("bare smooth shoulder skin, a single wide white halter strap", 0.85,
               "extra strap, thin strap, string, double strap"),
    # retouche légère des mains existantes (la pose et le haut de maillot sont conservés)
    "mains": ("two young smooth hands resting on her chest over the white bikini top, fingers together, "
              "exactly five fingers on each hand, short natural nails", 0.55,
              "extra fingers, missing fingers, fused fingers, six fingers, deformed hands, long claws, "
              "wrinkled old hands, topless, bare breasts, nipples, missing top"),
}
NEGATIF = "deformed, bad anatomy, blurry, low quality, nude, nsfw, cartoon, text, watermark"


def masque_ellipse(taille, boite, flou=10):
    m = Image.new("L", taille, 0)
    ImageDraw.Draw(m).ellipse(boite, fill=255)
    return m.filter(ImageFilter.GaussianBlur(flou))


def zone(a):
    import torch
    from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLInpaintPipeline
    img = Image.open(a.entree).convert("RGB")
    m = masque_ellipse(img.size, tuple(map(int, a.ellipse.split(","))))
    prompt, force, neg = QUOI[a.quoi]
    if a.force_zone:
        force = a.force_zone
    p = StableDiffusionXLInpaintPipeline.from_pretrained(MODELE, torch_dtype=torch.bfloat16, variant="fp16")
    p.scheduler = DPMSolverMultistepScheduler.from_config(
        p.scheduler.config, use_karras_sigmas=True, algorithm_type="sde-dpmsolver++")
    p.set_progress_bar_config(disable=True)
    out = p(prompt=f"{STYLE}, {prompt}", prompt_2=prompt, negative_prompt=f"{neg}, {NEGATIF}", image=img, mask_image=m,
            strength=force, num_inference_steps=round(7 / force), guidance_scale=2.0, width=img.width,
            height=img.height, generator=torch.Generator().manual_seed(a.graine)).images[0]
    Image.composite(out, img, m).save(a.sortie)
    print(a.sortie)


def peau(a):
    """Lisse la peau (taches, boutons) sous le visage en gardant le grain : filtre bilatéral + fondu partiel."""
    import cv2
    img = np.array(Image.open(a.entree).convert("RGB"))
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(int)          # H : 0-179
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    peau = ((h <= 22) | (h >= 170)) & (s > 50) & (s < 200) & (v > 70)
    peau[: a.depuis_y] = False                                       # visage et cou épargnés (taches de rousseur = style)
    m = cv2.GaussianBlur(peau.astype(np.float32), (0, 0), 3)[..., None]
    lisse = cv2.bilateralFilter(img, d=0, sigmaColor=28, sigmaSpace=7)
    lisse = cv2.medianBlur(lisse, 5)                                 # petits points sombres / rouges
    grain = img.astype(np.float32) - cv2.GaussianBlur(img, (0, 0), 1.2).astype(np.float32)
    res = lisse.astype(np.float32) + 0.35 * grain                    # garde un peu de texture
    out = img * (1 - m * a.force) + res * (m * a.force)
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(a.sortie)
    print(a.sortie)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["zone", "peau"])
    ap.add_argument("--entree", required=True); ap.add_argument("--sortie", required=True)
    ap.add_argument("--ellipse"); ap.add_argument("--quoi", choices=QUOI)
    ap.add_argument("--graine", type=int, default=1)
    ap.add_argument("--force-zone", type=float)
    ap.add_argument("--depuis-y", type=int, default=430)
    ap.add_argument("--force", type=float, default=0.85, help="peau : intensité ; zone : remplace la force par défaut")
    a = ap.parse_args()
    zone(a) if a.mode == "zone" else peau(a)

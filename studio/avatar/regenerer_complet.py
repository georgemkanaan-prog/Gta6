#!/usr/bin/env python3
"""Régénère l'image ENTIÈRE de Sunny en un seul passage (pas de collage) à partir d'un guide.

Le guide (image actuelle + short beige esquissé en aplat) fixe la pose, le cadrage et le visage ;
l'IA repeint toute l'image uniformément, ce qui fait disparaître les raccords.

    python regenerer_complet.py --entree sunny_taille.png --sortie out.png --graine 1 --force 0.55
"""
import argparse

import numpy as np
import torch
from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLImg2ImgPipeline
from PIL import Image, ImageDraw, ImageFilter

MODELE = "Lykon/dreamshaper-xl-lightning"
PROMPT = ("3d video game character, unreal engine 5 render, semi-realistic, beautiful young woman with long straight "
          "platinum blonde hair, freckles, pink earrings, white v-neck bikini top, large round full bust, bare toned "
          "belly, navel, low-rise beige denim shorts, both arms relaxed down along her sides, slender hands with "
          "five fingers and white nails beside her thighs")
PROMPT_2 = ("AAA open world game cutscene, sunny cobblestone street with pink buildings and plants, warm light, "
            "detailed smooth skin, cinematic, sharp focus")
NEGATIF = ("bikini bottom, panties, underwear, extra fingers, missing fingers, fused fingers, deformed hands, extra "
           "arms, bad anatomy, seams, visible cut, nude, nsfw, nipples, cartoon, anime, blurry, text, watermark")


def esquisse_short(img: Image.Image) -> Image.Image:
    """Short beige en aplat (taille basse, haut des cuisses) dessiné sur le bas de maillot."""
    d = ImageDraw.Draw(img)
    beige, couture = (214, 196, 170), (190, 170, 142)
    d.polygon([(268, 985), (648, 985), (700, 1344), (474, 1344), (458, 1215), (444, 1344), (225, 1344)], fill=beige)
    d.line([(268, 1000), (648, 1000)], fill=couture, width=6)          # ceinture
    d.line([(458, 1000), (458, 1200)], fill=couture, width=4)          # braguette
    return img.filter(ImageFilter.GaussianBlur(1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entree", required=True); ap.add_argument("--sortie", required=True)
    ap.add_argument("--graine", type=int, default=1); ap.add_argument("--force", type=float, default=0.55)
    ap.add_argument("--guide-seulement", action="store_true")
    a = ap.parse_args()

    guide = esquisse_short(Image.open(a.entree).convert("RGB"))
    if a.guide_seulement:
        guide.save(a.sortie); print(a.sortie); return
    p = StableDiffusionXLImg2ImgPipeline.from_pretrained(MODELE, torch_dtype=torch.bfloat16, variant="fp16")
    p.scheduler = DPMSolverMultistepScheduler.from_config(p.scheduler.config, use_karras_sigmas=True,
                                                          algorithm_type="sde-dpmsolver++")
    p.set_progress_bar_config(disable=True)
    out = p(prompt=PROMPT, prompt_2=PROMPT_2, negative_prompt=NEGATIF, image=guide, strength=a.force,
            num_inference_steps=round(8 / a.force), guidance_scale=2.0,
            generator=torch.Generator().manual_seed(a.graine)).images[0]
    out.save(a.sortie)
    print(a.sortie)


if __name__ == "__main__":
    main()

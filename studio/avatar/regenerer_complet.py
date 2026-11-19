#!/usr/bin/env python3
"""Régénère l'image ENTIÈRE de Sunny en un seul passage (pas de collage) à partir d'un guide.

Le guide (image actuelle + short beige esquissé en aplat) fixe la pose, le cadrage et le visage ;
l'IA repeint toute l'image uniformément, ce qui fait disparaître les raccords.

    python regenerer_complet.py --entree sunny_taille.png --sortie out.png --graine 1 --force 0.55
"""
import argparse

import numpy as np
import torch
from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLImg2ImgPipeline, StableDiffusionXLInpaintPipeline
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


def esquisse_short(img: Image.Image, ref_short: str) -> Image.Image:
    """Le short de l'image de référence (taille -> bas) est posé sur le bas du corps, avec un fondu doux.
    Ce n'est qu'un guide : l'image entière est ensuite repeinte d'un seul passage."""
    ref = Image.open(ref_short).convert("RGB")
    haut = ref.crop((190, 1100, 700, 1344))                  # à partir de la ceinture, échelle 1:1 (même largeur de hanches)
    bas = ref.crop((190, 1244, 700, 1344))                   # jambes du short prolongées jusqu'au bas du cadre
    morceau = Image.new("RGB", (510, 344)); morceau.paste(haut, (0, 0)); morceau.paste(bas, (0, 244))
    m = Image.new("L", morceau.size, 0)
    ImageDraw.Draw(m).polygon([(60, 0), (450, 0), (500, 344), (10, 344)], fill=255)
    img.paste(morceau, (205, 1000), m.filter(ImageFilter.GaussianBlur(5)))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entree", required=True); ap.add_argument("--sortie", required=True)
    ap.add_argument("--graine", type=int, default=1); ap.add_argument("--force", type=float, default=0.55)
    ap.add_argument("--guide-seulement", action="store_true")
    ap.add_argument("--visage", help="x0,y0,x1,y1 : ovale du visage conservé tel quel")
    ap.add_argument("--ref-short", default=str(__import__("pathlib").Path(__file__).parent / "reference_short.png"))
    a = ap.parse_args()

    guide = esquisse_short(Image.open(a.entree).convert("RGB"), a.ref_short)
    if a.guide_seulement:
        guide.save(a.sortie); print(a.sortie); return
    if a.visage:   # tout est repeint sauf l'ovale du visage (identité de Sunny), avec un fondu large
        m = Image.new("L", guide.size, 255)
        ImageDraw.Draw(m).ellipse(tuple(map(int, a.visage.split(","))), fill=0)
        m = m.filter(ImageFilter.GaussianBlur(18))
        p = StableDiffusionXLInpaintPipeline.from_pretrained(MODELE, torch_dtype=torch.bfloat16, variant="fp16")
        p.scheduler = DPMSolverMultistepScheduler.from_config(p.scheduler.config, use_karras_sigmas=True,
                                                              algorithm_type="sde-dpmsolver++")
        p.set_progress_bar_config(disable=True)
        out = p(prompt=PROMPT, prompt_2=PROMPT_2, negative_prompt=NEGATIF, image=guide, mask_image=m, strength=a.force,
                num_inference_steps=round(8 / a.force), guidance_scale=2.0, width=guide.width, height=guide.height,
                generator=torch.Generator().manual_seed(a.graine)).images[0]
        Image.composite(out, guide, m).save(a.sortie); print(a.sortie); return
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

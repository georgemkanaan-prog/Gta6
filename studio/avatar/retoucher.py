#!/usr/bin/env python3
"""Retouche une présentatrice existante en gardant son visage et le décor :
seuls les cheveux et la tenue sont régénérés (inpainting SDXL).

    python retoucher.py vicky.png etape1.png --haut-blanc --graine 5    # haut blanc + cheveux blonds lisses
    python retoucher.py etape1.png sunny.png --buste --force 0.6 --graine 4    # buste un peu plus important

Étapes : 1) détourage de la personne (rembg)  2) masque = personne SAUF le visage
3) inpainting avec la description de la nouvelle version.
"""
import argparse
from pathlib import Path

import numpy as np
import torch
from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLInpaintPipeline
from PIL import Image, ImageDraw, ImageFilter
from rembg import new_session, remove

from haut_blanc import haut_blanc

MODELE = "Lykon/dreamshaper-xl-lightning"
PROMPT = ("3d video game character, unreal engine 5 render, beautiful woman, long straight sleek platinum blonde hair "
          "down to her chest, white deep v-neck top with wide straps, gold earrings")
PROMPT_2 = ("long straight sleek platinum blonde hair, white top, AAA open world game cutscene, semi-realistic, "
            "detailed skin and hair strands, sunny daylight, cinematic, sharp focus")
NEGATIF = ("wavy hair, curly hair, brown hair, dark hair, pink hair, dark roots, pink top, short hair, cartoon, anime, 2d, real photo, "
           "deformed, bad anatomy, blurry, low quality, text, logo, watermark, nsfw, nude")
# Ovale du visage à préserver (x0, y0, x1, y1) sur une image 896x1152 — à ajuster pour une autre base
VISAGE = (300, 175, 600, 545)


PROMPT_BUSTE = ("3d video game character, unreal engine 5 render, voluptuous woman, round full perky bust, "
                "deep cleavage, white deep v-neck halter top with wide straps, long straight platinum blonde hair")
NEGATIF_BUSTE = "wavy hair, small bust, saggy, nipples, see-through, flat chest, pink top, nude, nsfw, deformed, bad anatomy, cartoon, blurry"


def masque_buste(img: Image.Image) -> Image.Image:
    """Zone du torse uniquement (sous le menton), dans la silhouette de la personne."""
    personne = remove(img, session=new_session("u2net_human_seg"), only_mask=True)
    m = np.array(personne.filter(ImageFilter.MaxFilter(41))) > 128
    m[: int(img.height * 0.70)] = False  # sous les clavicules : épaules et cou intacts
    return Image.fromarray((m * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(16))


def masque(img: Image.Image) -> Image.Image:
    personne = remove(img, session=new_session("u2net_human_seg"), only_mask=True)
    m = np.array(personne.filter(ImageFilter.MaxFilter(31))) > 128     # élargi : cheveux plus volumineux
    visage = Image.new("L", img.size, 0)
    ImageDraw.Draw(visage).ellipse(VISAGE, fill=255)
    m &= ~(np.array(visage) > 0)
    return Image.fromarray((m * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(12))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base"); ap.add_argument("sortie")
    ap.add_argument("--graine", type=int, default=1)
    ap.add_argument("--force", type=float, default=0.9)
    ap.add_argument("--etapes", type=int, default=6)
    ap.add_argument("--buste", action="store_true", help="ne retoucher que le torse (passe 2)")
    ap.add_argument("--haut-blanc", action="store_true",
                    help="recolore le haut rose en blanc et le protège pendant la retouche des cheveux (passe 1)")
    a = ap.parse_args()

    img = Image.open(a.base).convert("RGB")
    m = masque_buste(img) if a.buste else masque(img)
    if a.haut_blanc:
        img, haut = haut_blanc(img)
        img.save(Path(a.sortie).with_suffix(".haut_blanc.png"))
        haut = haut.filter(ImageFilter.MinFilter(9))  # on laisse les bords du haut se fondre avec les cheveux
        m = Image.fromarray((np.array(m).astype(float) * (1 - np.array(haut) / 255)).astype("uint8"))
    prompt, prompt_2, negatif = (PROMPT_BUSTE, PROMPT_2, NEGATIF_BUSTE) if a.buste else (PROMPT, PROMPT_2, NEGATIF)
    m.save(Path(a.sortie).with_suffix(".masque.png"))
    pipe = StableDiffusionXLInpaintPipeline.from_pretrained(MODELE, torch_dtype=torch.bfloat16, variant="fp16")
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(
        pipe.scheduler.config, use_karras_sigmas=True, algorithm_type="sde-dpmsolver++")
    pipe.set_progress_bar_config(disable=True)
    out = pipe(prompt=prompt, prompt_2=prompt_2, negative_prompt=negatif, image=img, mask_image=m,
               strength=a.force, num_inference_steps=round(a.etapes / a.force), guidance_scale=2.0,
               width=img.width, height=img.height, generator=torch.Generator().manual_seed(a.graine)).images[0]
    # le visage d'origine est recollé tel quel (fondu doux sur les bords)
    out = Image.composite(out, img, m)
    out.save(a.sortie)
    print(a.sortie)


if __name__ == "__main__":
    main()

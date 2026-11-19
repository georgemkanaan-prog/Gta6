#!/usr/bin/env python3
"""Met les avant-bras le long du corps SANS changer le reste du corps.

Étapes (la position est imposée, l'IA ne fait que le rendu) :
  1. la zone de poitrine cachée par les mains est reprise d'une image où elle est visible (--poitrine-de) ;
  2. les anciens avant-bras sont effacés (remplissage OpenCV) ;
  3. de nouveaux avant-bras + mains sont dessinés en aplat, couleur de peau prise sur le haut du bras ;
  4. passage IA à force moyenne sur ces seules zones pour obtenir des bras réalistes.

    python bras_cote.py --entree sunny_taille.png --poitrine-de b_g1.png --sortie guide.png --guide-seulement
    python bras_cote.py --entree sunny_taille.png --poitrine-de b_g1.png --sortie out.png --graine 1 --force 0.6
"""
import argparse

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

MODELE = "Lykon/dreamshaper-xl-lightning"
PROMPT = ("3d video game character, unreal engine 5 render, young woman in a white bikini top and beige shorts, "
          "both arms hanging straight down relaxed along her sides, natural slender forearms, relaxed hands beside "
          "her thighs, five fingers, smooth tanned skin, sunny street background")
NEGATIF = ("extra arms, extra hands, extra fingers, deformed hands, fused fingers, bent arms, hands on chest, "
           "bad anatomy, blurry, nude, nsfw, cartoon, text, watermark")

# géométrie (image 896x1344) : coudes actuels, anciens avant-bras, nouveaux avant-bras
COUDES = {"g": (145, 915), "d": (790, 915)}
ANCIENS = [((170, 930), (340, 780), 115), ((770, 920), (570, 790), 115)]
POITRINE = (280, 600, 620, 880)


def nouveau_bras(d, coude, sens):
    x, y = coude
    poignet = (x + 6 * sens, 1215)
    bout = (x + 10 * sens, 1325)
    # avant-bras effilé du coude au poignet
    d.polygon([(x - 34, y), (x + 34, y), (poignet[0] + 24, poignet[1]), (poignet[0] - 24, poignet[1])], fill=255)
    d.ellipse((x - 34, y - 34, x + 34, y + 34), fill=255)
    # main : paume allongée
    d.ellipse((poignet[0] - 27, poignet[1] - 10, bout[0] + 27, bout[1]), fill=255)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entree", required=True); ap.add_argument("--poitrine-de", required=True)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--graine", type=int, default=1); ap.add_argument("--force", type=float, default=0.6)
    ap.add_argument("--guide-seulement", action="store_true")
    a = ap.parse_args()

    img = Image.open(a.entree).convert("RGB")
    src_poitrine = Image.open(a.poitrine_de).convert("RGB")

    # 1. poitrine visible
    mp = Image.new("L", img.size, 0); ImageDraw.Draw(mp).ellipse(POITRINE, fill=255)
    base = Image.composite(src_poitrine, img, mp.filter(ImageFilter.GaussianBlur(12)))

    # 2. anciens avant-bras effacés (hors poitrine)
    trou = Image.new("L", img.size, 0); dt = ImageDraw.Draw(trou)
    for p1, p2, w in ANCIENS:
        dt.line([p1, p2], fill=255, width=w)
        for p in (p1, p2):
            dt.ellipse((p[0] - w // 2, p[1] - w // 2, p[0] + w // 2, p[1] + w // 2), fill=255)
    trou = Image.fromarray(np.array(trou) & ~np.array(mp))
    base = Image.fromarray(cv2.inpaint(np.array(base), np.array(trou), 21, cv2.INPAINT_TELEA))

    # 3. nouveaux avant-bras dessinés en aplat (couleur du haut du bras, léger dégradé)
    bras = Image.new("L", img.size, 0); db = ImageDraw.Draw(bras)
    nouveau_bras(db, COUDES["g"], +1); nouveau_bras(db, COUDES["d"], -1)
    arr = np.array(base).astype(np.float32)
    peau = np.array(img)[700:860, 180:230].reshape(-1, 3).mean(0)
    yy = np.arange(img.height)[:, None, None] / img.height
    teinte = peau * (1.05 - 0.25 * yy)                      # un peu plus sombre vers le bas
    mb = np.array(bras.filter(ImageFilter.GaussianBlur(3)), np.float32)[..., None] / 255
    arr = arr * (1 - mb) + teinte * mb
    guide = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    if a.guide_seulement:
        guide.save(a.sortie); print(a.sortie); return

    # 4. rendu IA uniquement sur avant-bras, mains et zones effacées
    import torch
    from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLInpaintPipeline
    m = Image.fromarray(np.maximum(np.array(trou), np.array(bras))).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(8))
    p = StableDiffusionXLInpaintPipeline.from_pretrained(MODELE, torch_dtype=torch.bfloat16, variant="fp16")
    p.scheduler = DPMSolverMultistepScheduler.from_config(p.scheduler.config, use_karras_sigmas=True,
                                                          algorithm_type="sde-dpmsolver++")
    p.set_progress_bar_config(disable=True)
    out = p(prompt=PROMPT, prompt_2=PROMPT, negative_prompt=NEGATIF, image=guide, mask_image=m, strength=a.force,
            num_inference_steps=round(8 / a.force), guidance_scale=2.0, width=img.width, height=img.height,
            generator=torch.Generator().manual_seed(a.graine)).images[0]
    Image.composite(out, guide, m).save(a.sortie)
    print(a.sortie)


if __name__ == "__main__":
    main()

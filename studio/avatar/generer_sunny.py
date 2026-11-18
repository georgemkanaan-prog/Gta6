#!/usr/bin/env python3
"""Génère les portraits des présentatrices de Leonida Live (3D semi-réaliste, qualité jeu vidéo).

Modèle : Lykon/dreamshaper-xl-lightning (SDXL, licence CreativeML Open RAIL++-M : usage commercial autorisé).
Tourne sur CPU (bf16), ~65 s par image. Même présentatrice + même graine = même image.

    python generer_sunny.py sunny            # Sunny (blonde)
    python generer_sunny.py vicky            # Vicky (proposition A validée)
    python generer_sunny.py sunny --fond vert --graine 11
"""
import argparse
import time
from pathlib import Path

import torch
from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLImg2ImgPipeline, StableDiffusionXLPipeline
from PIL import Image

MODELE = "Lykon/dreamshaper-xl-lightning"

# Chaque encodeur de texte de SDXL lit au plus 77 jetons : `prompt` décrit la présentatrice,
# `prompt_2` le cadrage, le décor et le style.
PRESENTATRICES = {
    "vicky": {  # proposition A validée le 18/11
        "graine": 11,
        "prompt": "3d video game character, unreal engine 5 render, female tv news presenter, late twenties, tan skin, "
                  "wavy honey-brown hair with a hot pink streak, brown eyes, light freckles, hot pink 1980s blazer, "
                  "turquoise crew-neck top, gold hoop earrings, sunglasses on her head",
    },
    "sunny": {  # dérivée de Vicky (même pose, même tenue) : blonde, buste un peu plus marqué
        "base": "vicky",
        "force": 0.75,  # 0 = image de base inchangée, 1 = nouvelle image
        "negatif": "brown hair, dark hair, pink hair, dark roots, flat chest",
        "graine": 11,
        "prompt": "3d video game character, unreal engine 5 render, female tv news presenter, late twenties, tan skin, "
                  "wavy golden platinum blonde hair, blue eyes, light freckles, fuller bust, hot pink 1980s blazer, "
                  "gold hoop earrings, sunglasses on her head",
    },
}
CADRAGE = "chest-up portrait, front view, looking at camera, playful smile"
FONDS = {
    "studio": "blurred neon tv studio background, pink and teal neon lights, palm trees",
    "vert": "plain flat solid chroma key green background",
}
STYLE = ("AAA open world game cutscene, semi-realistic, detailed skin and hair, soft key light, "
         "pink and teal rim light, cinematic, sharp focus")
NEGATIF = ("cartoon, anime, 2d, flat illustration, painting, real photo, celebrity, cleavage, bare shoulders, "
           "tank top, deformed, bad anatomy, extra fingers, blurry, low quality, text, logo, watermark, nsfw")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("presentatrice", choices=PRESENTATRICES)
    ap.add_argument("--graine", type=int, nargs="+")
    ap.add_argument("--fond", choices=FONDS, default="studio")
    ap.add_argument("--largeur", type=int, default=896)
    ap.add_argument("--hauteur", type=int, default=1152)
    ap.add_argument("--etapes", type=int, default=6)
    ap.add_argument("--force", type=float, help="force de transformation (présentatrice dérivée)")
    ap.add_argument("--out", default=str(Path(__file__).parent))
    a = ap.parse_args()
    p = PRESENTATRICES[a.presentatrice]

    pipe = StableDiffusionXLPipeline.from_pretrained(MODELE, torch_dtype=torch.bfloat16, variant="fp16")
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(
        pipe.scheduler.config, use_karras_sigmas=True, algorithm_type="sde-dpmsolver++")
    pipe.set_progress_bar_config(disable=True)

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for g in a.graine or [p["graine"]]:
        t = time.time()
        args = dict(prompt=f"{p['prompt']}, {CADRAGE}", prompt_2=f"{CADRAGE}, {FONDS[a.fond]}, {STYLE}",
                    negative_prompt=f"{p.get('negatif', '')}, {NEGATIF}", guidance_scale=2.0, generator=torch.Generator().manual_seed(g))
        if "base" in p:  # transformation partielle de l'image d'une autre présentatrice
            base = out / f"{p['base']}_{a.fond}_g{PRESENTATRICES[p['base']]['graine']}.png"
            if not base.exists():
                raise SystemExit(f"Générer d'abord {p['base']} : {base} introuvable")
            i2i = StableDiffusionXLImg2ImgPipeline(**pipe.components)  # partage les poids (pas de copie en mémoire)
            # avec force < 1, seules ~etapes*force étapes tournent : on compense
            img = i2i(image=Image.open(base).convert("RGB"), strength=a.force or p["force"],
                      num_inference_steps=round(a.etapes / (a.force or p["force"])), **args).images[0]
        else:
            img = pipe(num_inference_steps=a.etapes, width=a.largeur, height=a.hauteur, **args).images[0]
        f = out / f"{a.presentatrice}_{a.fond}_g{g}{f'_f{a.force}' if a.force else ''}.png"
        img.save(f)
        print(f"{f}  ({time.time() - t:.0f} s)", flush=True)


if __name__ == "__main__":
    main()

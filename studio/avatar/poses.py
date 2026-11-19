#!/usr/bin/env python3
"""Sunny en plan taille (mains visibles) + bibliothèque de gestes.

1) Élargissement du cadre (outpainting) : le portrait est réduit et placé en haut d'une toile plus haute ;
   le bas (taille, bras, mains) et les côtés sont générés. La poitrine est retravaillée au passage.
       python poses.py base --entree sunny.png --sortie sunny_taille.png --graine 1
2) Gestes : seuls les bras et les mains sont régénérés (visage, cheveux, haut et décor intacts).
       python poses.py geste --entree sunny_taille.png --geste pointe --sortie geste_pointe.png --graine 1
"""
import argparse

import numpy as np

import numpy as np
import torch
from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLInpaintPipeline
from PIL import Image, ImageDraw, ImageFilter

MODELE = "Lykon/dreamshaper-xl-lightning"
W, H = 896, 1344          # toile plan taille
ECHELLE = 0.85            # portrait d'origine réduit : le bas du cadre tombe au bas du ventre

PERSO = ("3d video game character, unreal engine 5 render, waist-up shot of a beautiful young woman, "
         "long straight platinum blonde hair, white deep v-neck halter bikini top with wide straps, "
         "large round full bust, cleavage, bare belly, navel, cropped at the lower belly, arms relaxed at her sides")
STYLE = ("AAA open world game cutscene, semi-realistic, detailed skin, natural hands with five fingers, "
         "sunny street background with pink buildings and green trees, cinematic, sharp focus")
NEGATIF = ("deformed hands, extra fingers, missing fingers, fused fingers, extra arms, extra limbs, bad anatomy, "
           "cropped head, nude, nsfw, nipples, cartoon, anime, blurry, low quality, text, logo, watermark")
GESTES = {
    "repos": "arms relaxed down at her sides, hands out of frame",
    "ouvertes": "both hands raised at chest height with open palms, expressive shrug",
    "pointe": "right arm extended to the side, index finger pointing to the side",
    "pouce": "one hand giving a thumbs up at chest height",
}


def pipeline():
    p = StableDiffusionXLInpaintPipeline.from_pretrained(MODELE, torch_dtype=torch.bfloat16, variant="fp16")
    p.scheduler = DPMSolverMultistepScheduler.from_config(
        p.scheduler.config, use_karras_sigmas=True, algorithm_type="sde-dpmsolver++")
    p.set_progress_bar_config(disable=True)
    return p


def preparer_base(portrait: Image.Image, echelle=None, poitrine=True):
    """Portrait réduit en haut de la toile ; les zones vides sont pré-remplies (étirement flou des bords)."""
    e = echelle or ECHELLE
    pw, ph = int(portrait.width * e), int(portrait.height * e)
    x0 = (W - pw) // 2
    petit = portrait.resize((pw, ph), Image.LANCZOS)
    toile = petit.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(25))
    toile.paste(petit, (x0, 0))
    masque = Image.new("L", (W, H), 255)
    ImageDraw.Draw(masque).rectangle((x0 + 12, 0, x0 + pw - 12, ph - 30), fill=0)
    if poitrine:   # poitrine : zone retravaillée (plus ronde et plus volumineuse)
        cx, cy = W // 2, int(ph * 0.90)
        ImageDraw.Draw(masque).ellipse((cx - 190, cy - 120, cx + 190, cy + 150), fill=255)
    return toile, masque.filter(ImageFilter.GaussianBlur(14))


def masque_bras(img: Image.Image) -> Image.Image:
    """Bras et mains : tout sous les épaules, sauf le centre du buste et la tête."""
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    d.rectangle((0, int(H * 0.50), W, H), fill=255)                          # bas du corps / mains
    d.rectangle((0, int(H * 0.42), int(W * 0.30), H), fill=255)              # bras gauche
    d.rectangle((int(W * 0.70), int(H * 0.42), W, H), fill=255)              # bras droit
    d.ellipse((W // 2 - 175, int(H * 0.45), W // 2 + 175, int(H * 0.72)), fill=0)   # buste conservé
    return m.filter(ImageFilter.GaussianBlur(16))


CORPS = ("3d video game character, unreal engine 5 render, beautiful young woman standing, white deep v-neck "
         "halter bikini top with wide straps, large round full bust, cleavage, bare toned belly, navel, beige denim "
         "shorts, both arms relaxed straight down along her sides, hands resting against her thighs, "
         "smooth tanned skin")


def preparer_corps(img: Image.Image, y_cou: int, mains):
    """Corps sous le cou à redessiner ; les mains posées devant le corps sont d'abord effacées de l'image
    de départ (remplissage OpenCV), pour que le modèle ne les redessine pas au même endroit."""
    import cv2
    a = np.array(img)
    if mains:
        trou = Image.new("L", img.size, 0)
        ImageDraw.Draw(trou).ellipse(mains, fill=255)
        a = cv2.inpaint(a, np.array(trou), 15, cv2.INPAINT_TELEA)
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rectangle((0, y_cou, img.width, img.height), fill=255)
    return Image.fromarray(a), m.filter(ImageFilter.GaussianBlur(20))


PROLONGER = ("3d video game character, unreal engine 5 render, young woman standing, white bikini top, bare toned "
             "belly, navel, low-rise beige denim shorts, upper thighs, both arms hanging straight down along her sides, "
             "relaxed hands beside her thighs, slender feminine fingers, five fingers")
BRAS = ("3d video game character, unreal engine 5 render, beautiful young woman, white deep v-neck halter bikini top, "
        "large round full bust, cleavage, bare toned belly, both forearms hanging straight down along her sides, "
        "relaxed hands beside her thighs, slender feminine fingers, smooth tanned skin")


def masque_zones(taille, zones, ellipses):
    """zones : segments « x1,y1,x2,y2,largeur » séparés par « ; » ; ellipses : « x0,y0,x1,y1 » séparées par « ; »."""
    m = Image.new("L", taille, 0)
    d = ImageDraw.Draw(m)
    for z in filter(None, (zones or "").split(";")):
        x1, y1, x2, y2, w = map(int, z.split(","))
        d.line([(x1, y1), (x2, y2)], fill=255, width=w)
        for x, y in ((x1, y1), (x2, y2)):
            d.ellipse((x - w // 2, y - w // 2, x + w // 2, y + w // 2), fill=255)
    for e in filter(None, (ellipses or "").split(";")):
        d.ellipse(tuple(map(int, e.split(","))), fill=255)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["base", "geste", "corps", "bras", "prolonger"])
    ap.add_argument("--echelle", type=float, default=0.72, help="prolonger : taille de l'image validée dans la toile")
    ap.add_argument("--zones", help="bras : segments à redessiner (anciens avant-bras + nouvelle position)")
    ap.add_argument("--ellipses", help="bras : ellipses à redessiner (ex. mains posées sur la poitrine)")
    ap.add_argument("--y-cou", type=int, default=420, help="corps : redessiné sous cette ligne")
    ap.add_argument("--mains", help="corps : ellipse x0,y0,x1,y1 des mains à effacer avant de redessiner")
    ap.add_argument("--force", type=float, default=0.88)
    ap.add_argument("--entree", required=True)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--geste", choices=GESTES, default="repos")
    ap.add_argument("--graine", type=int, default=1)
    ap.add_argument("--etapes", type=int, default=7)
    a = ap.parse_args()

    if a.mode == "bras":   # seuls les avant-bras et les mains bougent ; le reste du corps est conservé
        import cv2
        img0 = Image.open(a.entree).convert("RGB")
        dur = masque_zones(img0.size, a.zones, a.ellipses)
        init = Image.fromarray(cv2.inpaint(np.array(img0), np.array(dur), 15, cv2.INPAINT_TELEA))
        m = dur.filter(ImageFilter.GaussianBlur(10))
        out = pipeline()(prompt=BRAS, prompt_2=f"{BRAS}, {STYLE}", negative_prompt=NEGATIF + ", hands on chest",
                         image=init, mask_image=m, strength=a.force, num_inference_steps=round(a.etapes / a.force),
                         guidance_scale=2.0, width=W, height=H, generator=torch.Generator().manual_seed(a.graine)).images[0]
        Image.composite(out, img0, m).save(a.sortie)
        print(a.sortie)
        return
    if a.mode == "corps":
        img0 = Image.open(a.entree).convert("RGB")
        img, m = preparer_corps(img0, a.y_cou, tuple(map(int, a.mains.split(","))) if a.mains else None)
        out = pipeline()(prompt=CORPS, prompt_2=f"{CORPS}, {STYLE}", negative_prompt=NEGATIF, image=img, mask_image=m,
                         strength=a.force, num_inference_steps=round(a.etapes / a.force), guidance_scale=2.0,
                         width=W, height=H, generator=torch.Generator().manual_seed(a.graine)).images[0]
        Image.composite(out, img0, m).save(a.sortie)
        print(a.sortie)
        return
    if a.mode == "prolonger":   # image validée réduite en haut ; seuls le bas et les côtés sont générés
        img, m = preparer_base(Image.open(a.entree).convert("RGB"), a.echelle, poitrine=False)
        m = m.filter(ImageFilter.GaussianBlur(6))
        out = pipeline()(prompt=PROLONGER, prompt_2=f"{PROLONGER}, {STYLE}", negative_prompt=NEGATIF, image=img,
                         mask_image=m, strength=0.99, num_inference_steps=round(a.etapes / 0.99), guidance_scale=2.0,
                         width=W, height=H, generator=torch.Generator().manual_seed(a.graine)).images[0]
        Image.composite(out, img, m).save(a.sortie)
        print(a.sortie)
        return
    if a.mode == "base":
        img, m = preparer_base(Image.open(a.entree).convert("RGB"))
        force = 0.99
    else:
        img = Image.open(a.entree).convert("RGB")
        m, force = masque_bras(img), 0.92
    pipe = pipeline()
    out = pipe(prompt=f"{PERSO}, {GESTES[a.geste]}", prompt_2=f"{GESTES[a.geste]}, {STYLE}", negative_prompt=NEGATIF,
               image=img, mask_image=m, strength=force, num_inference_steps=round(a.etapes / force),
               guidance_scale=2.0, width=W, height=H, generator=torch.Generator().manual_seed(a.graine)).images[0]
    Image.composite(out, img, m).save(a.sortie)
    m.save(a.sortie.replace(".png", ".masque.png"))
    print(a.sortie)


if __name__ == "__main__":
    main()

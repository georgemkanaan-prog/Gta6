#!/usr/bin/env python3
"""Génère la voix d'une présentatrice avec Chatterbox multilingue (licence MIT, usage commercial OK).

    python generer_voix.py --texte texte_demo.txt --voix voix1 --sortie demo_voix1.wav

Les voix sont définies dans VOIX : un extrait de référence (timbre cloné) + des réglages d'expressivité.
Le texte est découpé en phrases (Chatterbox gère mal les textes longs), puis recollé avec de courtes pauses.
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

ICI = Path(__file__).parent
sys.path.insert(0, str(ICI))
from prononciation import prononcer  # noqa: E402

VOIX = {
    # exaggeration : 0.5 = neutre, 0.8+ = très expressif ; cfg_weight bas = débit plus rapide et vivant
    "voix1": {"reference": ICI / "references" / "voix1.wav", "exaggeration": 0.75, "cfg_weight": 0.35, "temperature": 0.8},
    "voix2": {"reference": ICI / "references" / "voix2.wav", "exaggeration": 0.8, "cfg_weight": 0.3, "temperature": 0.85},
    "defaut": {"reference": None, "exaggeration": 0.75, "cfg_weight": 0.35, "temperature": 0.8},
    # voix intégrée de Chatterbox (enregistrement humain), version très expressive
    "defaut_fun": {"reference": None, "exaggeration": 0.95, "cfg_weight": 0.3, "temperature": 0.85},
}


def phrases(texte: str):
    morceaux = re.split(r"(?<=[.!?…])\s+", texte.strip())
    out, cur = [], ""
    for m in morceaux:  # regroupe les phrases très courtes
        cur = f"{cur} {m}".strip()
        if len(cur) > 60:
            out.append(cur); cur = ""
    if cur:
        if out and len(cur) < 40:  # une fin trop courte fait « divaguer » le modèle : on la colle à la précédente
            out[-1] = f"{out[-1]} {cur}"
        else:
            out.append(cur)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--texte", required=True)
    ap.add_argument("--voix", choices=VOIX, required=True)
    ap.add_argument("--sortie", required=True)
    ap.add_argument("--graine", type=int, default=1)
    a = ap.parse_args()

    v = VOIX[a.voix]
    torch.manual_seed(a.graine)
    tts = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    texte = prononcer(Path(a.texte).read_text(encoding="utf-8"))
    pause = np.zeros(int(tts.sr * 0.18), np.float32)
    audio = []
    for p in phrases(texte):
        kw = dict(language_id="fr", exaggeration=v["exaggeration"], cfg_weight=v["cfg_weight"], temperature=v["temperature"])
        if v["reference"]:
            kw["audio_prompt_path"] = str(v["reference"])
        for essai in range(4):
            wav = tts.generate(p, **kw).squeeze(0).numpy()
            # ~13 caractères/s en débit vif : bien plus long = le modèle invente des syllabes -> on refait
            if len(wav) / tts.sr <= len(p) / 9 + 1.0:
                break
            print(f"  (prise {essai + 1} trop longue, nouvelle prise)", flush=True)
        audio += [wav, pause]
        print(f"  {p[:60]}", flush=True)
    sf.write(a.sortie, np.concatenate(audio), tts.sr)
    print(a.sortie)


if __name__ == "__main__":
    main()

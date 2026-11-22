#!/usr/bin/env python3
"""Génère la voix d'une présentatrice avec Chatterbox multilingue (licence MIT, usage commercial OK).

    python generer_voix.py --texte texte_demo.txt --voix sunny --sortie demo_sunny.wav

Les voix sont définies dans VOIX : un extrait de référence (timbre cloné) + des réglages d'expressivité.
Le texte est découpé en phrases (Chatterbox gère mal les textes longs), puis recollé avec de courtes pauses.
"""
import argparse
import difflib
import re
import unicodedata
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
    # Choix validés le 18/11 : Sunny = option A (timbre « sara »), Vicky = voix 1
    "sunny": {"reference": ICI / "references" / "if_sara.wav", "exaggeration": 0.8, "cfg_weight": 0.35, "temperature": 0.8},
    "vicky": {"reference": ICI / "references" / "voix1.wav", "exaggeration": 0.75, "cfg_weight": 0.35, "temperature": 0.8},
    "voix1": {"reference": ICI / "references" / "voix1.wav", "exaggeration": 0.75, "cfg_weight": 0.35, "temperature": 0.8},
    "sara": {"reference": ICI / "references" / "if_sara.wav", "exaggeration": 0.8, "cfg_weight": 0.35, "temperature": 0.8},
    "heart": {"reference": ICI / "references" / "af_heart.wav", "exaggeration": 0.8, "cfg_weight": 0.35, "temperature": 0.8},
    # NB : la voix intégrée de Chatterbox (sans référence) est MASCULINE : ne pas l'utiliser.
}


def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


class Juge:
    """Transcrit chaque prise (Whisper) et mesure sa ressemblance avec le texte attendu."""

    def __init__(self):
        from faster_whisper import WhisperModel
        self.m = WhisperModel("small", device="cpu", compute_type="int8")

    def score(self, wav: np.ndarray, sr: int, texte: str) -> float:
        import librosa
        y = librosa.resample(wav, orig_sr=sr, target_sr=16000).astype(np.float32)
        segs, _ = self.m.transcribe(y, language="fr")
        lu = " ".join(s.text for s in segs)
        return difflib.SequenceMatcher(None, _norm(lu), _norm(texte)).ratio()


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
    ap.add_argument("--prises", type=int, default=1, help="prises par phrase (règle : 1 ; segment raté → refaire ce segment seul)")
    a = ap.parse_args()

    v = VOIX[a.voix]
    torch.manual_seed(a.graine)
    tts = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    juge = Juge() if a.prises > 1 else None
    texte = Path(a.texte).read_text(encoding="utf-8")
    pause = np.zeros(int(tts.sr * 0.18), np.float32)
    audio = []
    for original in phrases(texte):
        p = prononcer(original)
        kw = dict(language_id="fr", exaggeration=v["exaggeration"], cfg_weight=v["cfg_weight"], temperature=v["temperature"])
        if v["reference"]:
            kw["audio_prompt_path"] = str(v["reference"])
        meilleure, meilleur_score = None, -1.0
        for essai in range(a.prises + 3):
            wav = tts.generate(p, **kw).squeeze(0).numpy()
            # ~13 caractères/s en débit vif : bien plus long = le modèle invente des syllabes -> prise rejetée
            if len(wav) / tts.sr > len(p) / 9 + 1.0:
                continue
            sc = juge.score(wav, tts.sr, original) if juge else 1.0
            if sc > meilleur_score:
                meilleure, meilleur_score = wav, sc
            if essai + 1 >= a.prises and meilleure is not None:
                break
        print(f"  [{meilleur_score:.2f}]", end="", flush=True)
        audio += [meilleure, pause]
        print(f"  {p[:60]}", flush=True)
    sf.write(a.sortie, np.concatenate(audio), tts.sr)
    print(a.sortie)


if __name__ == "__main__":
    main()

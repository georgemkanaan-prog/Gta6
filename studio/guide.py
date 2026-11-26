#!/usr/bin/env python3
"""Chaîne « guide » de Leonida Live : un fichier guide (texte de Sunny + cartes) -> vidéo longue + Shorts.

Studio Vice City (décor dessiné), grand écran à cartes, bandeau de chapitre en bas, aucun clip extérieur.

    python studio/guide.py guides/2611_argent.py          # voix + montage + Shorts
    python studio/guide.py --publier 0112 guides/a.py guides/b.py   # livraison/publication_0112.md

Fichier guide : un module Python qui définit GUIDE = {
    "titre": "GTA 6 : ...", "dossier": "videos/guides/2611_argent", "miniature": ("3-4 MOTS|ÉNORMES", "icône"),
    "segments": [{"id": "g01", "chapitre": "Intro", "texte": "...",
                  "cartes": [(mot_ancre_ou_None, "partie", "GROS|MOTS", "sous-titre", "icône", "couleur"), ...],
                  "pause": 1.5}, ...],
    "shorts": [{"nom": "argent_moses", "titre": "LIGNE 1|LIGNE 2", "segments": ["g03"]}],
    "description": "...", "tags": "...", "sources": ["https://..."]}
"""
import difflib
import importlib.util
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import monter_video2 as m2  # noqa: E402
import monter_video3 as m3  # noqa: E402
from cartes_guide import carte  # noqa: E402

RACINE = m2.RACINE
S = m2.S
VOIX = RACINE / "voix/generer_voix.py"
PY_CB = S / "venv_cb/bin/python"
m2.DECOR = RACINE / "studio/assets/studio_vc.png"
LIVRAISON = RACINE / "livraison"


def charger(chemin):
    spec = importlib.util.spec_from_file_location("guide_" + Path(chemin).stem, chemin)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.GUIDE


def norm(x):
    x = unicodedata.normalize("NFKD", x.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", x).split()


def transcrire(wav):
    from faster_whisper import WhisperModel
    if not hasattr(transcrire, "m"):
        transcrire.m = WhisperModel("small", device="cpu", compute_type="int8")
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    segs, _ = transcrire.m.transcribe(np.frombuffer(pcm, np.float32), language="fr")
    return " ".join(s.text for s in segs)


def verifier(texte, wav):
    """Voix acceptée si la transcription suit le script (pas de phrase sautée, pas de répétition)."""
    a, b = norm(texte), norm(transcrire(wav))
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    trop_long = len(b) > len(a) * 1.15
    return ratio >= 0.62 and not trop_long, ratio, len(b) / max(1, len(a))


def voix(G):
    D = RACINE / G["dossier"] / "voix"; D.mkdir(parents=True, exist_ok=True)
    for sgt in G["segments"]:
        txt, wav = D / f"{sgt['id']}.txt", D / f"{sgt['id']}.wav"
        if not txt.exists() or txt.read_text().strip() != sgt["texte"].strip():
            txt.write_text(sgt["texte"].strip() + "\n"); wav.unlink(missing_ok=True)
        if wav.exists():
            continue
        for graine in (1, 7, 13):
            subprocess.run([PY_CB, VOIX, "--texte", txt, "--voix", "sunny", "--prises", "1", "--graine", str(graine),
                            "--sortie", wav], cwd=S, env={**os.environ, "HF_HOME": str(S / "hf")},
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            ok, r, l = verifier(sgt["texte"], wav)
            print(f"voix {sgt['id']} graine {graine} : {m2.duree(wav):.1f} s, accord {r:.2f}, longueur {l:.2f}",
                  "OK" if ok else "À REFAIRE", flush=True)
            if ok:
                break
            wav.rename(wav.with_suffix(f".rate{graine}.wav"))
        else:
            meilleur = sorted(D.glob(f"{sgt['id']}.rate*.wav"))[0]
            meilleur.rename(wav); print("  ! gardée faute de mieux :", sgt["id"], flush=True)


def chapitres(G):
    ordre, vus = [], set()
    for s in G["segments"]:
        if s["chapitre"] not in vus:
            vus.add(s["chapitre"]); ordre.append(s["chapitre"])
    return ordre


def montage(G):
    V = RACINE / G["dossier"]
    m2.V, m2.C, m2.OUT = V, V / "cartes", V / "parties"
    m2.OUT.mkdir(parents=True, exist_ok=True); m2.C.mkdir(exist_ok=True)
    m3.VX = V / "voix"; m3.CACHE = V / "voix/mots.json"
    chap = chapitres(G); contenu = [c for c in chap if c != "Intro"]
    carte(m2.C / "fin.png", "Abonne-toi", "UN GUIDE|PAR JOUR", "Leonida Live · GTA 6 en français", "ok", "rose")
    parts = []
    for i, s in enumerate(G["segments"]):
        sid = s["id"]; wav = m3.VX / f"{sid}.wav"; d = m2.duree(wav)
        cartes = []
        for k, (ancre, partie, gros, sous, ico, coul) in enumerate(s["cartes"]):
            png = m2.C / f"{sid}_{k}.png"
            carte(png, partie, gros, sous, ico, coul)
            t = 0.0 if k == 0 or not ancre else m3.t(sid, ancre, d * k / len(s["cartes"]))
            cartes.append((t, png.name))
        if s["chapitre"] == "Intro":
            bandeau = G["titre"]
        else:
            bandeau = f"Chapitre {contenu.index(s['chapitre']) + 1}/{len(contenu)} · {s['chapitre']}"
        parts.append(m2.partie(f"{sid}", wav, bandeau, gaps=[(99, s.get("pause", 1.2))], cartes=cartes))
        if i == 0:
            parts.append(m2.generique(m2.OUT / "g00_generique.mp4", jingle=RACINE / "studio/assets/jingle_synthwave.wav"))
    parts.append(m2.ecran_fin(m2.OUT / "zz_fin_ecran.mp4"))
    normes = []
    for p in parts:
        n = m2.OUT / f"norm_{p.name}"
        ok = n.exists() and subprocess.run(["ffprobe", "-v", "error", str(n)], capture_output=True).returncode == 0
        if not ok:
            m2.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", p, "-vf", "fps=25,scale=1920:1080,format=yuv420p",
                    "-c:v", "libx264", "-crf", "23", "-preset", "medium", "-c:a", "aac", "-ar", m2.SR, "-ac", 2,
                    "-b:a", "128k", n])
        normes.append(n)
    liste = m2.OUT / "liste.txt"; liste.write_text("".join(f"file '{n}'\n" for n in normes))
    final = V / "video.mp4"
    m2.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", 0, "-i", liste, "-c", "copy", "-movflags", "+faststart", final])
    # chapitres YouTube (0:00 en premier, ≥ 10 s chacun)
    t, debuts = 0.0, {}
    for p, n in zip(parts, normes):
        sid = p.stem
        seg = next((s for s in G["segments"] if s["id"] == sid), None)
        if seg and seg["chapitre"] not in debuts:
            debuts[seg["chapitre"]] = 0.0 if not debuts else t
        t += m2.duree(n)
    ch = [(debuts[c], c if c != "Intro" else "Introduction") for c in chap]
    (V / "chapitres.json").write_text(json.dumps({"duree": t, "chapitres": ch}, ensure_ascii=False))
    print(final, f"{t / 60:.2f} min", f"{final.stat().st_size / 1e6:.0f} Mo", flush=True)
    return final


def shorts(G, prefixe):
    V = RACINE / G["dossier"]; sortis = []
    for sh in G.get("shorts", []):
        out = LIVRAISON / f"{prefixe}_{sh['nom']}.mp4"
        if out.exists():
            sortis.append(out); continue
        args = [S / "venv/bin/python", RACINE / "studio/short.py", "--sortie", out, "--titre", sh["titre"]]
        for sid in sh["segments"]:
            p = V / "parties" / f"{sid}.mp4"
            args += ["--passage", f"{p}:0:{m2.duree(p)}", "--texte", V / "voix" / f"{sid}.txt"]
        subprocess.run([str(a) for a in args], cwd=RACINE, env={**os.environ, "HF_HOME": str(S / "hf")},
                       check=True, stdout=subprocess.DEVNULL)
        sortis.append(out); print("short", out, f"{m2.duree(out):.1f} s", flush=True)
    return sortis


def miniature(G, sortie):
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import demo_reaction as dr
    from cartes_guide import icone, COULEURS, NUIT
    dec = Image.open(m2.DECOR).convert("RGB").resize((1280, 720)).filter(ImageFilter.GaussianBlur(3))
    s = Image.open(RACINE / "studio/avatar/sunny_taille.png").convert("RGB")
    m = dr.detourer(s, None); m = m if isinstance(m, Image.Image) else Image.fromarray(np.asarray(m).astype("uint8"))
    hs = 700; ws = int(896 * hs / 1120)
    dec.paste(s.crop((0, 0, 896, 1120)).resize((ws, hs)), (-30, 720 - hs + 40), m.convert("L").crop((0, 0, 896, 1120)).resize((ws, hs)))
    d = ImageDraw.Draw(dec)
    gros, ico = G["miniature"]
    lignes = gros.split("|"); y = 90
    for k, l in enumerate(lignes):
        taille = 150 if len(lignes) <= 2 else 118
        f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", taille)
        while d.textlength(l, font=f) > 760 and taille > 60:
            taille -= 6; f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", taille)
        d.text((470, y), l, font=f, fill=(255, 214, 60) if k % 2 else (255, 255, 255), stroke_width=12, stroke_fill=NUIT)
        y += taille + 14
    icone(d, ico, 1150, 600, 80, COULEURS["jaune"])
    d.rounded_rectangle((470, 610, 720, 690), 18, fill=COULEURS["rose"])
    d.text((595, 650), "GTA 6", font=ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", 50),
           fill=(255, 255, 255), anchor="mm")
    dec.save(sortie); return sortie


def hms(t):
    t = int(t); return f"{t // 60}:{t % 60:02d}"


def publier(date, guides, jour_pub=None, heures=("18:00", "20:00"), heures_shorts=("12:00", "16:00")):
    """Écrit livraison/publication_JJMM.md (JJMM = jour de livraison) ; planning proposé pour `jour_pub` (JJMM)."""
    jj, mm = (jour_pub or date)[:2], (jour_pub or date)[2:]
    L = [f"# Livraison du {date[:2]}/{date[2:]} — Leonida Live (guides GTA 6) · publication proposée le {jj}/{mm}", "",
         "Réglages communs : « Non, pas conçue pour les enfants » · **Contenu modifié ou synthétique : Oui** · "
         "Catégorie : Jeux vidéo · Langue : français · chapitres déjà dans la description (YouTube les découpe tout seul).", ""]
    n_short = 0
    for k, (G, prefixe) in enumerate(guides):
        V = RACINE / G["dossier"]; info = json.loads((V / "chapitres.json").read_text())
        L += ["---", "", f"## Vidéo {k + 1} : `{prefixe}.mp4` — {jj}/{mm} à {heures[k % len(heures)]}",
              f"Miniature : `{prefixe}_miniature.png` · durée {hms(info['duree'])}", "", "**Titre**", "```", G["titre"], "```",
              "", "**Description**", "```", G["description"].strip(), "", "⏱️ Chapitres"]
        L += [f"{hms(t)} {c}" for t, c in info["chapitres"]]
        L += ["", "Sources (guides consultés) : " + ", ".join(G.get("sources_noms", [])),
              "Les infos viennent de guides publiés et peuvent changer avec les mises à jour du jeu.",
              "Sunny est un personnage virtuel : avatar et voix générés par IA.",
              "Vidéo de fan non affiliée à Rockstar Games ni à Take-Two Interactive. Aucune image du jeu : studio et cartes dessinés.",
              "🔔 Abonne-toi : un guide GTA 6 par jour, en français !", "#GTA6 #GTAVI #GTA6Fr", "```", "",
              "**Tags**", "```", G["tags"], "```", ""]
        for sh in G.get("shorts", []):
            h = heures_shorts[n_short % len(heures_shorts)]; n_short += 1
            L += [f"### Short : `{prefixe}_{sh['nom']}.mp4` — {jj}/{mm} à {h}", "**Titre**", "```", sh["titre_yt"], "```",
                  "**Description**", "```", sh["description"].strip(),
                  "Sunny est un personnage virtuel (avatar et voix IA). Vidéo de fan non affiliée à Rockstar Games.",
                  "#GTA6 #shorts", "```", ""]
    (LIVRAISON / f"publication_{date}.md").write_text("\n".join(L))
    print(LIVRAISON / f"publication_{date}.md")


def main():
    if sys.argv[1] == "--publier":
        date = sys.argv[2]; reste = sys.argv[3:]
        jour = reste.pop(0) if reste and re.fullmatch(r"\d{4}", reste[0]) else None
        guides = [(charger(c), Path(c).stem) for c in reste]
        publier(date, guides, jour); return
    G = charger(sys.argv[1]); prefixe = Path(sys.argv[1]).stem
    LIVRAISON.mkdir(exist_ok=True)
    voix(G)
    final = montage(G)
    dest = LIVRAISON / f"{prefixe}.mp4"
    if final.stat().st_size > 95e6:
        m2.run(["ffmpeg", "-v", "error", "-y", "-i", final, "-c:v", "libx264", "-crf", "27", "-preset", "slow",
                "-c:a", "copy", "-movflags", "+faststart", dest])
    else:
        dest.write_bytes(final.read_bytes())
    miniature(G, LIVRAISON / f"{prefixe}_miniature.png")
    shorts(G, prefixe)
    print("fini", prefixe, flush=True)


if __name__ == "__main__":
    main()

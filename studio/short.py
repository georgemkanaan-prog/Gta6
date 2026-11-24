#!/usr/bin/env python3
"""Fabrique un Short vertical (1080x1920) à partir de passages déjà montés en studio.

Mise en page : bandeau titre en haut · la télé (l'extrait du jeu) · Sunny en dessous · sous-titres
mot à mot (groupes de 3 mots, repérés par transcription) · fin sur « ABONNE-TOI ».
La télé et Sunny sont découpées dans la MÊME image du montage : son, lèvres et extrait restent synchrones.

    python studio/short.py --sortie short.mp4 --titre "IL EST PASSÉ SOUS LA CARTE ?!" \
        --passage parties/01_accroche.mp4:0:9.7 --passage parties/14_bugs.mp4:55:64
"""
import argparse
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import numpy as np

TV = (820, 150, 960, 540)                 # télé dans l'image studio 1920x1080
SUNNY = (140, 150, 656, 640)              # buste de Sunny (x, y, l, h)


def ass_temps(s):
    h, r = divmod(s, 3600); m, r = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{r:05.2f}"


def sous_titres(audio, sortie, mots_par_ligne=3, script=None):
    from faster_whisper import WhisperModel
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", audio, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    segs, _ = WhisperModel("small", device="cpu", compute_type="int8").transcribe(
        np.frombuffer(pcm, np.float32), language="fr", word_timestamps=True)
    mots = [w for s in segs for w in s.words]
    if script:   # mots EXACTS du script, chacun daté par alignement lettre à lettre sur la transcription
        import difflib
        n = lambda x: "".join(c for c in unicodedata.normalize("NFKD", x.lower()).encode("ascii", "ignore").decode() if c.isalnum())
        W, tw = [], []
        for w in mots:
            l = n(w.word)
            for k, c in enumerate(l):
                W.append(c); tw.append(w.start + (w.end - w.start) * k / max(len(l), 1))
        ref = script.split()
        R, debut = [], []
        for w in ref:
            debut.append(len(R)); R.extend(n(w) or "_")
        carte = [None] * len(R)
        for a, b, size in difflib.SequenceMatcher(None, R, W, autojunk=False).get_matching_blocks():
            for k in range(size):
                carte[a + k] = tw[b + k]
        connus = [(i, x) for i, x in enumerate(carte) if x is not None]
        def temps(i):
            if carte[i] is not None:
                return carte[i]
            av = [c for c in connus if c[0] < i][-1:] or [(0, mots[0].start)]
            ap = [c for c in connus if c[0] > i][:1] or [(len(R), mots[-1].end)]
            (i0, t0), (i1, t1) = av[0], ap[0]
            return t0 + (t1 - t0) * (i - i0) / max(i1 - i0, 1)
        dates = [temps(d) for d in debut]
        for k in range(1, len(dates)):
            dates[k] = max(dates[k], dates[k - 1] + 0.05)
        fin_audio = mots[-1].end
        mots = [type("M", (), {"start": d, "end": (dates[k + 1] if k + 1 < len(dates) else fin_audio)})() for k, d in enumerate(dates)]
        ecrit = ref
    else:
        ecrit = [w.word.strip() for w in mots]
    lignes = []
    for i in range(0, len(mots), mots_par_ligne):
        g = mots[i:i + mots_par_ligne]
        txt = " ".join(ecrit[i:i + mots_par_ligne]).upper()
        fin = mots[i + mots_par_ligne].start if i + mots_par_ligne < len(mots) else g[-1].end + 0.4
        lignes.append(f"Dialogue: 0,{ass_temps(g[0].start)},{ass_temps(fin)},Mot,,0,0,0,,{txt}")
    entete = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Mot,DejaVu Sans,86,&H0000DCFF,&H00FFFFFF,&H004A0F2A,&H00000000,1,0,0,0,100,100,0,0,1,9,0,2,40,40,360,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    Path(sortie).write_text(entete + "\n".join(lignes) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sortie", required=True); ap.add_argument("--titre", required=True)
    ap.add_argument("--passage", action="append", required=True, help="fichier:debut:fin (secondes)")
    ap.add_argument("--texte", action="append", default=[], help="fichier(s) texte du script : orthographe des sous-titres")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp())
    morceaux = []
    for k, p in enumerate(a.passage):
        f, d, e = p.rsplit(":", 2)
        m = tmp / f"m{k}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", d, "-to", e, "-i", f, "-vf", "fps=30,scale=1920:1080",
                        "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-c:a", "aac", "-ar", "44100", "-ac", "2",
                        str(m)], check=True)
        morceaux.append(m)
    (tmp / "l.txt").write_text("".join(f"file '{m}'\n" for m in morceaux))
    brut = tmp / "brut.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp / "l.txt"), "-c", "copy",
                    str(brut)], check=True)
    script = " ".join(Path(t).read_text(encoding="utf-8") for t in a.texte) or None
    sous_titres(str(brut), tmp / "st.ass", script=script)
    tx, ty, tw, th = TV; sx, sy, sw, sh = SUNNY
    titre = a.titre.replace("'", "’").replace(":", "\\:")
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    fc = (f"color=c=0x2A0F4A:s=1080x1920:r=30[fond];"
          f"[0:v]crop={tw}:{th}:{tx}:{ty},scale=1080:608[tv];"
          f"[0:v]crop={sw}:{sh}:{sx}:{sy},scale=1080:-2[sun];"
          f"[fond][sun]overlay=0:860:shortest=1[a];[a][tv]overlay=0:252[b];"
          f"[b]drawbox=x=0:y=240:w=1080:h=12:color=0xFF3E9A:t=fill,drawbox=x=0:y=860:w=1080:h=10:color=0xFF3E9A:t=fill,"
          + "".join(f"drawtext=fontfile={font}:text='{ligne}':fontsize=60:fontcolor=0xFFDC00:borderw=7:"
                    f"bordercolor=0x2A0F4A:x=(w-tw)/2:y={86 + 74 * i}," for i, ligne in enumerate(titre.split("|")))
          + f"drawtext=fontfile={font}:text='LEONIDA LIVE':fontsize=36:fontcolor=0xFF3E9A:x=(w-tw)/2:y=30,"
          f"ass={tmp / 'st.ass'}[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(brut), "-filter_complex", fc, "-map", "[v]", "-map", "0:a",
                    "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-b:a", "192k", "-movflags", "+faststart", a.sortie], check=True)
    print(a.sortie)


if __name__ == "__main__":
    main()

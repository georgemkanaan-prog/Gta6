# Production de Sunny : avatar 3D semi-réaliste + voix

> **Mise à jour du 18/11 — tout est fait dans ce projet, sans service externe.**
> Portraits validés dans `studio/avatar/` :
> - **Vicky** (`vicky.png`) : image retenue, cheveux châtains ondulés à mèches roses, haut rose.
> - **Sunny** (`sunny.png`) : dérivée de Vicky en gardant son visage et le décor. Cheveux longs blond platine
>   lisses, même haut en blanc, buste un peu plus important.
>
> Pour refaire Sunny (retouche locale avec le modèle DreamShaper XL Lightning, licence Open RAIL++-M) :
> ```bash
> cd studio/avatar
> python retoucher.py vicky.png etape1.png --haut-blanc --graine 5           # haut blanc + cheveux blonds lisses
> python retoucher.py etape1.png etape2.png --buste --force 0.65 --graine 4  # nettoyage du haut
> python gonfler.py etape2.png sunny.png --force 0.5 --rayon 260 --centres 285,1040 575,1040  # volume du buste
> ```
> Prérequis : `pip install torch diffusers transformers accelerate safetensors pillow rembg onnxruntime scipy`,
> et l'accès réseau à huggingface.co (environnement « Gta6 »). `generer_sunny.py` crée de nouveaux
> personnages à partir de zéro. La voix et l'animation seront aussi faites ici : les sections ci-dessous
> sur ElevenLabs et HeyGen ne sont plus utilisées.

**Objectif visuel** : Sunny doit ressembler à un **personnage d'un jeu en monde ouvert récent** :
rendu 3D réaliste (peau, cheveux, éclairage), mais légèrement stylisé (traits un peu accentués,
couleurs saturées). Elle doit avoir l'air de pouvoir sortir du jeu, **sans copier un personnage
existant** (pas Lucia, pas de logo Rockstar) : c'est notre mascotte à nous.

Il y a deux étapes : une solution rapide pour la vidéo n°1 cette semaine, et une solution
« pro » à mettre en place ensuite.

---

## Étape 1 — Cette semaine (vidéo n°1) : image de référence → avatar parlant

### 1a. Créer le visage de Sunny (image de référence)
Avec un générateur d'images (Midjourney, Leonardo, Ideogram, Flux…). Prompt (en anglais, ça marche mieux) :

```
Semi-realistic 3D video game character portrait, AAA open-world game quality, Unreal Engine 5
render. A charismatic TV news presenter named Sunny, late 20s, warm tan skin, wavy honey-brown
hair with a pink streak, big expressive brown eyes, playful confident smile, slightly stylized
features. Wearing a fitted hot-pink 80s-inspired blazer over a turquoise top, gold hoop
earrings, sunglasses pushed up on her head. Front-facing, chest-up, looking at camera,
soft studio key light with pink and teal rim lights, plain solid green background.
Highly detailed skin and hair, cinematic, sharp focus. --ar 16:9
```
- Négatif / à éviter : `cartoon, anime, flat, photo of a real person, celebrity, logo, text, watermark`.
- Générer **20 à 40 variantes**, en garder **une seule** : c'est le visage officiel de Sunny.
- Refaire ensuite 4 à 6 images **avec la même référence** (fonction « character reference » /
  « image prompt ») : profil 3/4, sourire, surprise, doigt pointé → servent pour les **miniatures**.
- Fond **vert uni** (#00FF00) : l'outil `studio/monter_segment.sh -g` l'enlève automatiquement.

### 1b. Animer l'image avec la voix (talking avatar)
Outils qui transforment **1 image + 1 fichier audio** en vidéo qui parle, avec mouvements de tête
et expressions : **HeyGen (Avatar IV / Photo Avatar)**, **Hedra (Character-3)**, **Kling Avatar**,
**Runway Act**. Tester 2 outils sur le même extrait de 20 s et garder celui qui :
- synchronise le mieux les lèvres **en français** ;
- garde le rendu 3D (certains « photo-réalisent » trop : refuser si elle ne ressemble plus à un perso de jeu) ;
- exporte en 1080p avec un abonnement autorisant l'**usage commercial**.

**Un clip par segment du script** (voir l'outil plus bas) : c'est plus facile à monter et à corriger.

---

## Étape 2 — Dès que la chaîne tourne : Sunny en vraie 3D (qualité jeu, gratuit)

**MetaHuman (Unreal Engine 5, gratuit)** — c'est la technologie la plus proche de la qualité
d'un jeu AAA :
1. Créer Sunny dans **MetaHuman Creator** en s'inspirant de l'image de référence (visage, coupe,
   teint) ; choisir des tenues proches (blazer rose).
2. **MetaHuman Animator** : animation du visage **à partir du fichier audio** (lip-sync automatique)
   ou à partir d'une vidéo filmée à l'iPhone (Live Link Face) pour des grimaces plus naturelles.
3. Construire un **vrai plateau 3D** Leonida Live dans Unreal (télé, néons, palmiers) : la caméra
   peut bouger, Sunny peut marcher jusqu'à la télé → effet « émission » beaucoup plus fort.
4. Export en 1080p/60 avec le Movie Render Queue.

Alternative plus simple : **Reallusion Character Creator 4 + iClone** (payant, ~600 €) avec
lip-sync automatique AccuLips — plus rapide à prendre en main qu'Unreal.

---

## La voix de Sunny

**Profil** : femme, ~28 ans, française, **énergique, souriante, malicieuse**, rythme rapide
façon animatrice de radio/YouTube, capable de passer du ton « JT sérieux » à l'éclat de rire.

### ElevenLabs (recommandé, meilleur rendu en français)
1. **Voice Design** → description :
   ```
   Young French woman in her late twenties, native Parisian French accent, bright and energetic
   voice, smiling while speaking, playful and teasing, fast-paced like a fun YouTube or radio
   host, expressive with laughter in the voice, clear diction.
   ```
   Générer plusieurs propositions, garder celle qui « sourit » le plus, l'enregistrer sous **Sunny**.
   (Ou choisir une voix de la **Voice Library** répondant à cette description, sous licence commerciale.)
2. Modèle : le plus récent modèle multilingue / expressif disponible.
3. Réglages de départ : **Stabilité 35–45 %** (plus bas = plus expressif), **Similarité 75 %**,
   **Style / exagération 30–50 %**, vitesse 1.05–1.1.
4. Astuces d'écriture pour une voix plus vivante :
   - phrases courtes, points d'exclamation, « … » pour les pauses comiques ;
   - balises d'émotion si le modèle les accepte : `[rire]`, `[chuchote]`, `[enthousiaste]` ;
   - générer **2–3 prises** par segment et garder la meilleure.
5. Mixage : légère compression + égaliseur (+2 dB vers 3 kHz pour la clarté), niveau final -14 LUFS.

Autres options : **Murf**, **PlayHT** (correctes en français, moins expressives).
⚠️ Ne jamais cloner la voix d'une personne réelle (actrice, youtubeuse) sans son accord écrit.

---

## Pipeline complet d'une vidéo
```
script.md
  └─ python3 studio/extraire_voix.py videos/001-…/script.md   → voix/NN_titre.txt (textes prêts pour la synthèse)
      └─ ElevenLabs (voix Sunny)                               → voix/NN_titre.mp3
          └─ HeyGen / Hedra (image de Sunny + mp3)             → sunny/NN_titre.mp4 (fond vert)
              └─ studio/monter_segment.sh -p sunny/NN.mp4 -g -c extrait.mp4 -t "…"   → segments
                  └─ assemblage final (DaVinci / CapCut ou ffmpeg concat)
```

## Obligations
- YouTube Studio → **« Contenu modifié ou synthétique : Oui »** sur chaque vidéo (avatar + voix IA réalistes).
- Garder les preuves de licence (abonnements, conditions d'usage commercial) des outils utilisés.
- Mention en description : « Sunny est un personnage virtuel ; voix et avatar générés par IA. »

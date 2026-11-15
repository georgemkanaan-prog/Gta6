# SUNNY LEONIDA — Chaîne YouTube GTA 6

Chaîne de divertissement autour de GTA 6, en français. Le concept : **Sunny**, la présentatrice
de l'émission « Leonida Live », commente sur un plateau télé les découvertes de la communauté
(secrets, missions, lieux cachés, véhicules et objets rares). Les extraits passent sur une
télé du studio, et Sunny réagit avec humour.

> GTA 6 sort le **jeudi 19 novembre 2026** (PS5 / Xbox Series X|S). La vidéo n°1 doit être
> en ligne **avant le 19**, pour profiter du pic de recherches.

## Contenu du dépôt

| Fichier | Rôle |
|---|---|
| [01-identite-chaine.md](01-identite-chaine.md) | Nom, Sunny (personnage, voix, phrases fétiches), bannière, description, playlists |
| [02-format-video.md](02-format-video.md) | Structure type d'une vidéo de 8 à 12 min, rubriques récurrentes, règles de rétention |
| [03-droits-et-sources.md](03-droits-et-sources.md) | **À lire avant toute publication** : réutilisation d'extraits, Content ID, monétisation, IA |
| [04-calendrier-30-videos.md](04-calendrier-30-videos.md) | Planning des 30 premières vidéos (lancement → 2 premiers mois) |
| [05-production-sunny.md](05-production-sunny.md) | **Fabriquer Sunny** : avatar 3D semi-réaliste façon jeu vidéo + voix féminine fun (prompts, outils, réglages) |
| [videos/001-avant-le-lancement/](videos/001-avant-le-lancement/) | **Vidéo n°1 prête à tourner** : script complet, plan de montage, titre, miniature, description |
| [studio/](studio/) | Outils de montage : génère le décor du studio et incruste automatiquement les extraits dans la télé |

## Démarrage rapide (vidéo n°1)

1. Lire `03-droits-et-sources.md` (5 min) — ça évite les strikes.
2. Créer Sunny (image + voix) avec `05-production-sunny.md`, puis `python3 studio/extraire_voix.py videos/001-avant-le-lancement/script.md` pour obtenir les textes à faire lire par la voix IA.
3. Rassembler les extraits listés dans le plan de montage (trailers officiels Rockstar).
4. Lancer `studio/monter_segment.sh` pour chaque extrait → segments « télé dans le studio ».
5. Assembler, ajouter les chapitres et la miniature, publier **le 17 ou 18 novembre à 18 h**.

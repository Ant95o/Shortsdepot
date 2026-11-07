# Shortsdepot

Usine à shorts : génération, montage et publication de vidéos courtes 9:16
(TikTok, Instagram Reels, Facebook Reels, YouTube Shorts), à coût zéro.

## Fonctionnement

1. Une fiche YAML dans `specs/` décrit la vidéo (gabarit, textes, voix, infos de publication).
2. À chaque push, GitHub Actions fabrique la vidéo et la dépose sur la branche `rendus`
   (fichier `.mp4` + `.json` avec titre, description et hashtags).
3. La vidéo est validée par un humain avant toute publication.

## Gabarits

| Gabarit | Format |
| --- | --- |
| `un_seul_mot` | Conversation avec une IA qui ne répond qu'en un mot, voix off, bulles animées |
| `clips_commentes` | Clips (vidéo IA ou rushes) recadrés en 9:16, voix de commentateur, sous-titres, tableau de score, carte de fin |

Une fiche dont les clips ne sont pas encore dans `clips/` est sautée sans erreur.

## Voix off

Les fournisseurs sont essayés dans l'ordre, le suivant prend le relais si l'un échoue :
`edge` (voix neuronales Microsoft, gratuit) puis `espeak` (local, voix robotique).
`silent` produit un silence de durée réaliste pour tester le montage hors ligne.

## Lancer en local

```bash
pip install -r requirements.txt   # + ffmpeg (et espeak-ng en option)
python -m shorts specs/2026-10-16-un-seul-mot.yaml --sortie rendus
```

Sortie : 1080x1920, 30 i/s, H.264 + AAC 48 kHz stéréo, compatible avec les 4 plateformes.

Police Inter sous licence SIL OFL 1.1 (`shorts/assets/fonts/OFL.txt`).

## Vidéo IA générée automatiquement (Kaggle)

Une fiche peut demander la génération de ses plans avec une section `generation` :

```yaml
generation:
  plans:
    - {fichier: clips/ma-video/plan1.mp4, prompt: "…", graine: 42}
```

Au push, le workflow `generation.yml` envoie les plans manquants sur un GPU gratuit de Kaggle
(Wan 2.1 1.3B accéléré par le LoRA CausVid), récupère les vidéos, les ajoute au dépôt et lance le rendu.

Pour reprendre une trend existante, un plan peut pointer vers une vidéo de référence placée dans `refs/`
(`reference: refs/xxx.mp4`, `debut: 4.5`). Le plan est alors généré avec Wan 2.1 VACE : la carte de
profondeur de la référence (Depth Anything V2) guide les mouvements et le cadrage, le prompt décide
de qui joue. `force` (0 à 1, 0,8 par défaut) règle à quel point la référence est suivie.
Il faut deux secrets dans le dépôt : `KAGGLE_USERNAME` et `KAGGLE_API_TOKEN`
(Kaggle > Settings > API, avec un compte dont le téléphone est vérifié).

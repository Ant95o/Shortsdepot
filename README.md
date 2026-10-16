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

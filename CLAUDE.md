# Shortsdepot : consignes pour Claude Code

- Pipeline maison (à garder) : images Gemini, puis génération HF Wan 2.2 14B (essais/, quota ~5 plans/jour) ou Kaggle Wan 2.2 5B (specs/, generation.yml), puis montage FFmpeg (shorts/, rendu.yml). Le labo d'essais d'outils open source est dans labo/ (labo.yml).
- OpenMontage (sous-module `openmontage/`, version figée, installé et vérifié par `.github/workflows/openmontage.yml`) sert à la production : scénario, storyboard, contrôle qualité, montage Remotion, sous-titres mot à mot. Avant de l'utiliser, lire `openmontage/AGENT_GUIDE.md` et le skill de l'étape concernée (`openmontage/skills/`).
- Avec OpenMontage, la génération vidéo reste branchée sur HF ou Kaggle (gratuit). Kling ne sera ajouté que si l'utilisateur prend un abonnement. Aucune clé payante ni carte bancaire.
- Mettre à jour OpenMontage : `git -C openmontage fetch && git -C openmontage checkout <commit>`, puis relancer openmontage.yml.

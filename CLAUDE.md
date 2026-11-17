# Shortsdepot : consignes pour Claude Code

- Pipeline maison (à garder) : images Gemini, puis génération HF Wan 2.2 14B (essais/, quota ~5 plans/jour) ou Kaggle Wan 2.2 5B (specs/, generation.yml), puis montage FFmpeg (shorts/, rendu.yml). Le labo d'essais d'outils open source est dans labo/ (labo.yml).
- OpenMontage (sous-module `openmontage/`, version figée, installé et vérifié par `.github/workflows/openmontage.yml`) sert à la production : scénario, storyboard, contrôle qualité, montage Remotion, sous-titres mot à mot. Avant de l'utiliser, lire `openmontage/AGENT_GUIDE.md` et le skill de l'étape concernée (`openmontage/skills/`).
- Avec OpenMontage, la génération vidéo reste branchée sur HF ou Kaggle (gratuit). Kling ne sera ajouté que si l'utilisateur prend un abonnement. Aucune clé payante ni carte bancaire.
- Mettre à jour OpenMontage : `git -C openmontage fetch && git -C openmontage checkout <commit>`, puis relancer openmontage.yml.
- Boîte à outils gratuite (17/11/2026, `outils/`) :
  - `outils.yml` : pousser une fiche `outils/fiches/*.yaml` (sections `voix`, `soustitres`, `plans`, voir `outils/fiche.py`) ; sorties sur la branche `outils-sorties`. Voix FR Kokoro/Piper, sous-titres mot à mot WhisperX (donner le texte exact), contrôle auto des plans (FIGÉ / COUPURE / FONDU / FLOU + planche) à lancer avant chaque montage.
  - `stats.yml` : stats YouTube quotidiennes (secret `YOUTUBE_API_KEY`, `YOUTUBE_CHAINE`) → branche `stats`.
  - `veille.yml` : veille trends Firecrawl (sans clé) → branche `veille` ; la tâche « Trends du jour » la lit avant de proposer.
  - Labo : tâche `comfyui` (Wan 2.2 14B GGUF sur Kaggle, sans quota HF) dans `labo/job.py`.
- Attention : le premier push d'une nouvelle branche déclenche tous les workflows à filtre de chemins (dont `generation.yml` et `labo.yml` qui envoient sur Kaggle) : annuler aussitôt ceux qui ne sont pas voulus.

# Échelle de mouvements : jusqu'où vont les outils gratuits ?

Test (pas une vidéo à publier) : 6 niveaux d'action, mêmes héros (Cooper, le chat roux), images déjà existantes.

| Niveau | Action | Image | Kaggle 5B | HF 14B |
|---|---|---|---|---|
| N1 micro-geste | le chat tourne la tête, bâille, cligne | dh-9 | oui | non (déjà réussi) |
| N2 déplacement | Cooper traverse la cuisine et s'assoit | dh-1 | oui | non (déjà réussi) |
| N3 saut + cible | le chat plonge du canapé dans le carton | no-3 (Kaggle 1er passage : no-2) | oui | oui |
| N4 objet tenu | Cooper tire le sac de croquettes dans sa gueule | dh-1 | oui | oui |
| N5 contact à deux | le chat tape le nez de Cooper, Cooper recule | dh-10 (Kaggle 1er passage : dh-2, erreur) | oui | oui |
| N6 acrobatie | salto arrière du chat | dh-9 (Kaggle 1er passage : dh-10, erreur) | oui | oui |

Lancement : Kaggle = copier `spec-kaggle.yaml` dans `specs/` seulement quand le notebook est libre ;
HF = `essai-hf.yml`, étape `fiche essais/echelle.yaml 1 2` (puis `3 4`), après la production du jour.
Critère : l'action demandée se voit, sans déformation ni changement d'animal. 2e essai (autre graine) seulement si le 1er est ambigu.

## Résultats Kaggle, 1er passage (09/11, graine 42)
- N1 bâillement : réussi (bâille, cligne), mais la tête ne tourne pas et le bâillement dure 4 s.
- N2 traversée : raté, la cuisine se transforme en une autre pièce et Cooper s'assoit sur le sac.
- N3 plongeon : l'action se voit (le chat plonge et disparaît dans le carton), mais le chat apparaît de nulle part et le cadre bouge.
- N4 tirer le sac : raté, Cooper pousse le sac du nez puis la caméra bascule et il se déforme.
- N5 / N6 : mauvaise image de départ (piège de numérotation), à refaire (spec-kaggle-2.yaml). Le salto n'a pas eu lieu (le chat se dresse et sautille).

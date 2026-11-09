# Échelle de mouvements : jusqu'où vont les outils gratuits ?

Test (pas une vidéo à publier) : 6 niveaux d'action, mêmes héros (Cooper, le chat roux), images déjà existantes.

| Niveau | Action | Image | Kaggle 5B | HF 14B |
|---|---|---|---|---|
| N1 micro-geste | le chat tourne la tête, bâille, cligne | dh-9 | oui | non (déjà réussi) |
| N2 déplacement | Cooper traverse la cuisine et s'assoit | dh-1 | oui | non (déjà réussi) |
| N3 saut + cible | le chat plonge du canapé dans le carton | no-2 | oui | oui |
| N4 objet tenu | Cooper tire le sac de croquettes dans sa gueule | dh-1 | oui | oui |
| N5 contact à deux | le chat tape le nez de Cooper, Cooper recule | dh-2 | oui | oui |
| N6 acrobatie | salto arrière du chat | dh-10 | oui | oui |

Lancement : Kaggle = copier `spec-kaggle.yaml` dans `specs/` seulement quand le notebook est libre ;
HF = `essai-hf.yml`, étape `fiche essais/echelle.yaml 1 2` (puis `3 4`), après la production du jour.
Critère : l'action demandée se voit, sans déformation ni changement d'animal. 2e essai (autre graine) seulement si le 1er est ambigu.

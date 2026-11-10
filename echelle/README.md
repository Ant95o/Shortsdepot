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

## Résultats Kaggle, 2e passage (10/11, bonnes images)
- N3 plongeon (graine 7, no-3) : le chat saute et finit dans un carton, mais le carton apparaît d'un coup et le décor change. Action lisible, raccord impossible.
- N5 patte sur le nez (dh-10) : le chat se colle à Cooper et pose la patte sur son torse, les deux corps fusionnent un instant ; pas de tape sur le nez, Cooper ne recule pas. Raté.
- N6 salto (dh-9) : le chat s'envole à l'envers puis la caméra part en vrille et un bras humain apparaît. Raté.

Bilan Kaggle 5B : fiable seulement au niveau 1 (geste sur place). Dès le niveau 2 (déplacement), le décor dérive ; contact entre deux animaux = fusion ; objets qui apparaissent/disparaissent.

## Résultats HF 14B (10/11, 3 s, graine 42)
- N3 plongeon : réussi. Le chat se lève, plonge tête la première dans le carton NOËL, la queue dépasse puis disparaît. Décor stable.
- N4 tirer le sac : réussi. Cooper mord le sac et le tire en reculant, cuisine intacte.
- N5 patte sur le nez : à moitié. Le chat lève la patte et touche le museau, mais Cooper ne réagit pas (pas de recul).
- N6 salto : raté sur le salto, mais saut vertical propre et réception nette, sans déformation.

## Conclusion
| Niveau | Kaggle 5B | HF 14B |
|---|---|---|
| 1 geste sur place | oui | oui (déjà vu) |
| 2 déplacement | non (décor dérive) | oui (déjà vu) |
| 3 saut vers une cible | lisible mais objets qui apparaissent | oui |
| 4 objet tenu/tiré | non | oui |
| 5 action + réaction à deux | non (fusion) | geste oui, réaction non |
| 6 acrobatie | non | non (saut simple seulement) |

Règles : actions → HF ; Kaggle pour les plans calmes. Action + réaction = 2 plans (geste, puis réaction de l'autre). Acrobatie = Kling, ou montage (saut HF + coupe + réception).

## 2e série : les astuces (10/11, HF)
- Réaction en plan séparé (départ = dernière image du coup de patte) : Cooper retire la tête et baisse les yeux. Réaction visible mais discrète. Monté avec le coup de patte : demo-patte-puis-recul.mp4.
- Poursuite à deux : ratée, le chat et Cooper partent chacun de leur côté. Deux animaux qui bougent ensemble = à découper (un plan par animal).
- Plan enchaîné (départ = dernière image du sac tiré) : réussi, Cooper continue de tirer, rien ne saute au raccord. demo-sac-2-plans.mp4.
- Salto truqué au montage (sans IA) : saut HF + rotation de 0,4 s au sommet + réception : salto-montage-astuce.mp4.

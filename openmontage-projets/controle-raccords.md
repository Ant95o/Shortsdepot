# Contrôle des raccords (avant d'animer, puis avant de livrer)

Méthode reprise d'OpenMontage (skills/creative/video-stitching.md, « AI clip chaining ») : on regarde
chaque jonction « fin du plan N | début du plan N+1 ». Outil : `controle_raccords.py` (planche JPG).

Deux passages :
1. **Images Gemini, avant d'animer** (`controle_raccords.py images …`). Une image ratée se refait en 1 minute ; un plan raté coûte 45 min de Kaggle ou du quota HF.
2. **Clips animés, avant le montage** (`controle_raccords.py clips plan.mp4:N …`, N = images gardées).

Pour chaque jonction, répondre OUI/NON. Un seul NON = refaire l'image (ou le plan) avant de continuer :
- **Même objet** : le même gâteau, le même jouet, la même cape (forme, couleur, déco). Pas d'objet qui change de nature.
- **Même état** : ce qui a été abîmé, mangé ou renversé le reste ; ce qui est intact l'était avant.
- **Même place** : le perso finit le plan N là où il commence le plan N+1 (sinon il faut un plan qui montre le déplacement).
- **Mêmes présences** : personne n'apparaît ni ne disparaît sans qu'on le voie arriver ou partir (chat sur le plan de travail…).
- **Même décor** : pièce, meubles, lumière, heure.
- **Action lisible** : la fin du plan N montre bien l'action annoncée (pas un flou ni une coupe à la place du geste).

Exemple (gâteau, 10/11) : planche dans /mnt/project-files/videos/openmontage/raccords-gateau.jpg.

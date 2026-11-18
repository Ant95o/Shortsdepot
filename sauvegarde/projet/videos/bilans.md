# Bilans vidéo (après chaque livraison : bien / à améliorer / ce qu'on met en place)

## Housewife (04/11)
- Bien : 13 plans, une action par plan, l'histoire se suit ; AntoineS : « on s'est bien amélioré ».
- À améliorer : raccords cassés (Cooper sur le canapé sans y être monté, pot debout puis renversé, plans 12 et 13 identiques, pas de révélation à 18 h) ; saut de netteté HF → Kaggle au plan 8.
- Mis en place : fin du plan N = début du plan N+1 dès le script ; images de raccord en plus ; plan final = révélation.

## Dame Hombro (05/11)
- Bien : raccords propres (chat qui descend de la chaise, gamelle toujours là, Cooper qui rejoint le chat) ; danse réussie sur HF ; 12 plans.
- À améliorer : action pas assez explicite (2 textes seulement, Cooper « inquiet » illisible sans texte) ; 4 plans Kaggle ratés sur 9 (l'animal fonce dans la caméra, danse ignorée) ; mélange Kaggle/HF visible.
- Constat outils : Kaggle (5B) = rendu réaliste mais ignore les actions fines et fait souvent foncer l'animal vers la caméra ; HF (14B) = 7 plans d'action sur 7 réussis (saut, marche, s'asseoir à côté, danse).
- Mis en place : texte à chaque moment clé ; HF pour les plans d'action, Kaggle pour les plans calmes ; transitions HF avec image de départ + image d'arrivée (clé `fin` dans les fiches essais/*.yaml).

## Everlong (livrée le 06/11, 25,6 s, 10 plans : 7 Kaggle + 2 HF + 1 Kaggle)
- **Bien** : texte à chaque moment clé (6 légendes) ; HF a enfin montré le chiot qui dépose son bâton ; Kaggle a tenu le décor et le chien adulte d'un plan à l'autre.
- **À améliorer** : la transition « porte » HF a fait disparaître la branche (non utilisée), donc saut de plan jardin → porte ; quota HF épuisé au 7e plan (la transition « il lâche et s'assoit » n'a pas été faite), la fin montre Cooper déjà assis ; Kaggle plan7 finit par passer la porte (coupé à 2,5 s).
- **Outils** : HF bon pour les gestes fins (déposer) ; les transitions avec image d'arrivée HF déforment les objets tenus. Kaggle reste meilleur pour la continuité de décor.
- **Ce qu'on met en place** : 6 plans HF maximum par vidéo (le 7e tombe hors quota) ; pour les objets tenus pendant une transition, une image Gemini intermédiaire plutôt qu'une transition HF ; plan « il lâche » à prévoir comme plan à part.

## Noël « All I Want for Christmas » (livrée le 07/11, 29,6 s, 12 plans : 7 Kaggle + 5 HF)
- **Bien** : vraie histoire en 12 étapes lisibles (carton → chat → sapin → étoile), saut du chat HF très réussi, belle chute (chat en étoile, Cooper au bonnet).
- **À améliorer** : le plongeon dans le carton (plan 6) se voit mal ; les images 1-2 n'ont pas le même salon que 3-12 ; quota HF tombé à 5 plans aujourd'hui (le 6e a échoué).
- **Ce qu'on met en place** : prévoir 5 plans HF max et mettre les plus importants en premier dans la fiche ; dans les prompts Gemini, décrire le salon en détail dès le plan 1 et le répéter (« même canapé bouclette, même parquet en points de Hongrie »).

## Angel of My Dreams (livrée le 09/11, 27,3 s, 12 plans : 7 Kaggle + 5 HF)
- **Bien** : les 5 plans HF réussis du premier coup (entrée, défilé, Cooper au 1er rang, demi-tour cape au vent) ; vraie chute (Cooper a volé la cape) ; décor du podium stable.
- **À améliorer** : Kaggle noie le podium dans la fumée (plan 3) et déforme le chat au réveil (plan 10), coupés courts ; le salon du plan 1 ≠ celui du réveil ; Cooper fonce sur la caméra en HF (plan 11 coupé à 0,8 s).
- **Ce qu'on met en place** : préciser « camera stays far, the dog walks sideways across the frame » pour les marches vers la caméra ; un seul décor de départ décrit identiquement au début et à la fin.

## Why Would I Deceive You? (le gâteau) – 10/11
- Bien : premières images via mail → tâche Gemini → Drive (aucun copier-coller), Cooper et la cuisine identiques d'un plan à l'autre ; histoire claire en 11 plans avec 6 textes.
- À améliorer : quota HF vide, plans d'action faits sur Kaggle (on ne voit pas Cooper se dresser) ; Kaggle a ajouté une main dans le plan 10 (remplacé par un zoom sur l'image) ; Gemini avait copié 4 images au premier passage.
- Ce qu'on met en place : mail d'images envoyé dès 6 h 45, contrôle du Drive vers 11 h 30 ; réserver le quota HF aux actions de la vidéo du jour (pas de tests le même jour).

## Zombies épisode 1 (12/11)
- Bien : vraies actions visibles (aspirateur qui fonce vers la caméra, Cooper qui se réveille, renforts du couloir, encerclement) ; HF a fait les 5 actions en 4 min, le 2e essai du plan 5 a réveillé Cooper.
- À améliorer : images reçues en 286 px (captures), chien différent sur les plans 9-10, intrusion d'une plante dans le plan 1 Kaggle (coupé à 32 images), sauts du chat et de Cooper non montrés (on voit l'après).
- Ce qu'on met en place : images « Télécharger » en pleine taille ; pour un saut, une image de départ AVANT le saut (animal au sol) + HF ; ordre des plans pensé pour la logique (choc du panier avant la sortie de base).

## Santa Tell Me (16/11)
- Bien : images Gemini en pleine taille (768x1376), décor de Noël cohérent d'un plan à l'autre, Cooper reconnaissable ; HF a animé les 5 actions en quelques minutes.
- À améliorer : images 7 (lettre dans la chaussette) manquante et 8 (Cooper absent, deux chats) ratée ; mains humaines/téléphone qui apparaissent en fin de plan Kaggle (plans 1, 6, 11, coupés) ; HF faible sur les gestes fins (Cooper tire à peine la feuille) ; course finale qui part dans le mauvais sens.
- Ce qu'on met en place : vérifier la liste des 12 images à réception et redemander les manquantes avant d'animer ; couper systématiquement les plans Kaggle avant la 2e seconde ; prompts HF avec un mouvement ample et une direction explicite (« vers le sapin, de gauche à droite »).

## It's Time! (16/11)
- Bien : 12 plans, histoire claire (chat gelé → dégèle → ils sortent Noël → sapin). Plans Kaggle calmes très propres ; HF tient les actions (s'ébroue, course, carton, guirlande).
- À améliorer : Kaggle ajoute encore des mains (carton) et Cooper qui renverse la tête (bonnet) : plans 8 et 10 coupés à ~0,5 s et ralentis. Raccord carton fermé (plan 7) / ouvert plein (plan 8).
- Pour la suite : pour les gros plans d'objets, préférer HF ou un plan avec un animal dans le cadre (moins de mains) ; prévoir l'état des objets (carton ouvert/fermé) dans les prompts d'images.

## Zombies épisode 2 (17/11)
- Bien : suite claire de l'épisode 1 (encerclés → plan de la balle → les robots partent → fuite → ils reviennent). Les 3 plans HF (balles, robots, fuite) sont nets ; montée de tension réussie dans la cuisine (lueur, lasers).
- À améliorer : Gemini a inversé l'ordre des images ; plan 7 : les robots sont encore visibles alors qu'ils viennent de partir ; Kaggle déforme les animaux après ~2,5 s (coupé avant).
- Pour la suite : vérifier l'ordre à réception ; préciser dans les prompts où sont les robots plan par plan ; images compressées avant Kaggle (> 1 Mo refusé).

## Pray For Me (18/11, nuit)
- Bien : lumière dorée identique sur les 12 plans, vrai duel lisible (croquette → arrivées au ralenti → yeux → face à face → coup de patte → sous le frigo → dépités). HF tient bien les marches (plans 4 et 5).
- À améliorer : l'image Gemini du plan 9 met le chat en partie derrière Cooper (corps qui se mélangent) ; le 1er essai HF du plan 9 a raté (le chat traverse le chien), 2e essai correct ; coup de patte très court (1 s).
- Pour la suite : dans les prompts d'images, imposer « séparés d'un mètre, chacun d'un côté » pour les face-à-face ; vérifier chaque image avant d'animer.

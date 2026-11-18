# Changer d'ordinateur : marche à suivre (projet AI Story)

Bonne nouvelle : **il n'y a rien à installer sur l'ancien ordinateur avant de partir.**
Tout le projet vit en ligne, pas sur le Mac :

| Quoi | Où ça se trouve | Lié à |
|---|---|---|
| Fils de discussion, mémoire du projet, fichiers partagés (vidéos, sons, trends, ~1,9 Go) | Projet Claude « Génération Video et réseaux » sur claude.ai | ton compte Claude |
| Code du pipeline, workflows GitHub Actions, secrets | Dépôt github.com/Ant95o/Shortsdepot | ton compte GitHub |
| Images Gemini, tâche Gemini qui lit les mails « AI Story – images du JJ/MM » | Google Drive « AI Story/… » et Gmail | ton compte Google |
| Skills, connecteurs | Réglages de claude.ai | ton compte Claude |
| Comptes AI Story (TikTok, Instagram, YouTube, Facebook) | Applis sur l'iPhone | chaque réseau |

Changer d'ordinateur revient donc surtout à **se reconnecter**.

---

## 1. Avant de quitter l'ancien ordinateur (10 minutes)

1. **Mots de passe** : vérifie que tu connais (ou que ton gestionnaire de mots de passe contient) ceux de la liste du point 5. Si tu utilises le trousseau iCloud et que le nouvel ordi est un Mac, il suivra tout seul.
2. **Fichiers locaux** : regarde Téléchargements, Bureau et Documents. Tout ce qui sert au projet et n'est pas déjà dans Drive ou dans le projet Claude (vidéos Kling téléchargées, images Gemini enregistrées à la main, musiques) : glisse-le dans Google Drive, dossier « AI Story ».
3. **Codes de secours de la double authentification** (Google, GitHub, Claude si activée) : note-les. Sans eux, un nouvel appareil peut être bloqué.
4. Si tu as utilisé **Claude Code dans le Terminal** de l'ancien Mac (dossier caché `~/.claude`), copie ce dossier sur une clé ou dans Drive. Si tu ne l'as jamais ouvert, ignore ce point : ce projet tourne dans le cloud.

C'est tout. Inutile d'installer plugins, connecteurs ou dépôts sur l'ancien ordi : ils ne sont pas stockés dessus.

## 2. Sur le nouvel ordinateur

1. Installe l'application **Claude** (claude.ai/download) ou ouvre claude.ai dans le navigateur, et connecte-toi avec le même compte.
2. Ouvre le projet « Génération Video et réseaux » : fils, mémoire et fichiers sont là.
3. Vérifie les **connecteurs** utiles au projet : claude.ai → Réglages → Connecteurs. Ils doivent afficher « connecté » :
   - Gmail (envoi des consignes d'images à la tâche Gemini)
   - Google Drive (récupération des images 01.jpg, 02.jpg…)
   - Firecrawl (veille des trends)
   - GitHub : si un message demande l'accès, ouvre https://claude.ai/connect-github et reconnecte ton compte `Ant95o`.

   Si l'un affiche « reconnecter », clique dessus et reconnecte-toi. Les autres connecteurs (finance, Shopify, Calendly…) ne servent pas à ce projet.
4. Vérifie les **skills** : claude.ai → Réglages → Skills. Ils sont liés au compte, donc déjà là : `shorts-ia-qualite`, `shorts-outils-bascule`, `registre-find-skill`, `redaction-qualite`, `creation-tache-securisee`, `design-trend-check`, `app-pipeline`. Rien à réenregistrer.
   (Le skill « methode-ai-story » proposé le 17/11 n'apparaît pas dans la liste : il n'a jamais été enregistré. Demande à Claude de le reproposer si tu le veux.)
5. **Plugins** : aucun plugin n'est installé sur ton compte. Ceux qu'utilise Claude pendant le travail viennent de l'environnement cloud. Rien à réinstaller.
6. **Dépôt GitHub** : rien à cloner pour toi, Claude le clone lui-même à chaque session. Pour le voir : github.com/Ant95o/Shortsdepot.
7. Sur l'iPhone, rien ne change (publication, applis des réseaux).

## 3. Secrets GitHub (à vérifier, pas à ressaisir)

Les secrets sont stockés chez GitHub, pas sur l'ordinateur : ils restent en place.
Pour les voir : github.com/Ant95o/Shortsdepot → Settings → Secrets and variables → Actions.

| Secret | Sert à | Si un jour il faut le refaire |
|---|---|---|
| `HF_TOKEN` | Génération vidéo Hugging Face (Wan 2.2) | huggingface.co → Settings → Access Tokens |
| `KAGGLE_USERNAME`, `KAGGLE_API_TOKEN`, `KAGGLE_API_TOKEN2` | Génération sur GPU Kaggle | kaggle.com → Settings → API → Create New Token |
| `YOUTUBE_API_KEY`, `YOUTUBE_CHAINE` | Stats YouTube quotidiennes (si ajoutés) | console.cloud.google.com → Identifiants |
| `FIRECRAWL_API_KEY` | Facultatif (la veille marche sans) | firecrawl.dev |

GitHub ne réaffiche jamais la valeur d'un secret : c'est normal. Si une valeur est perdue, on en crée une nouvelle sur le site concerné et on la recolle dans GitHub.
Ne jamais écrire ces clés dans un message, un fichier ou le dépôt.

## 4. Sauvegarde supplémentaire dans le dépôt

Le dossier `sauvegarde/` du dépôt contient une copie des fichiers texte du projet Claude au 18/11/2026 : trends (historique, planning, trends du jour), bilans des vidéos, scénarios et scripts de montage (`montage.sh`, textes à l'écran) et la photo de profil AI Story.
Les gros fichiers (vidéos, sons) ne sont pas copiés dans le dépôt. Ils restent dans le projet Claude ; leur liste et leur taille sont dans `sauvegarde/gros-fichiers.txt`.

## 5. À garder dans un gestionnaire de mots de passe

- Compte Claude (et le mail utilisé pour se connecter)
- Compte Google (Gmail, Drive, Gemini) + codes de secours
- GitHub `Ant95o` + codes de secours
- Hugging Face, Kaggle (le compte Kaggle doit garder son téléphone vérifié)
- Comptes AI Story : TikTok, Instagram, YouTube, Facebook
- Kling AI (si abonnement pris)
- Les clés API (Hugging Face, Kaggle, YouTube) si tu veux pouvoir les recoller sans les recréer

## 6. Bon à savoir sur le dépôt

- La branche `main` est presque vide : le travail est sur des branches ouvertes (`moteur-montage`, `claude/project-thread-5trpz1`, `claude/project-thread-pfmuhs`) et les PR #1, #2 et #3. Tout est bien sur GitHub, rien n'est perdu, mais ne supprime pas ces branches.
- Le dépôt est **public** : les secrets y sont protégés, mais n'importe qui peut lire le code et les notes. Le garder public a un avantage : GitHub Actions y est illimité et gratuit. En privé, le gratuit est plafonné à 2 000 minutes par mois, ce que les longues générations Kaggle peuvent dépasser. À ne changer qu'en connaissance de cause (Settings → General → Danger Zone → Change visibility).

# Projet : Suivi recherche CDI Dev Full Stack

## Contexte

Nedjmeddine cherche un CDI développeur Full Stack. Priorité Strasbourg, ouvert France entière si besoin. Runway de 9 mois (démarré réellement fin janvier 2026). Stack : Node.js / Angular / React / .NET / Laravel / PHP.

## Objectif de ce projet

Outil de pilotage de recherche d'emploi. **Pas un outil d'automatisation massive.** Le but est de forcer la discipline et d'améliorer la qualité des candidatures et le suivi des relances, PAS d'industrialiser le spray-and-pray.

## Règles absolues — ne jamais violer

1. **Jamais d'envoi automatique** de candidature, email ou message LinkedIn. L'outil prépare, l'humain décide et envoie.
2. **Pas de scraping direct** LinkedIn ou de sites d'emploi via requests/Selenium. Les offres arrivent par **deux entrées seulement** : l'API JSearch (`scripts/fetch_jsearch.py`, bouton « Lancer une recherche » de l'onglet Offres) et les alertes email (`/opportunites`, `/daily`). Apify, JobSpy, France Travail et le scan freelance (Himalayas/Remotive/Jobicy) ont été retirés le 20/11/2026 — ne pas les réintroduire.
3. **Qualité > volume.** L'objectif est 5 candidatures ciblées/semaine max, pas 50.
4. **Toujours tracker avant de proposer.** Avant de suggérer une nouvelle candidature, vérifier dans l'Excel que l'entreprise n'y figure pas déjà (anti-doublon strict).
5. **Ton direct, sans complaisance.** Si Nedjmeddine traîne sur une relance, lui dire. Si une candidature est morte (>21 jours sans réponse), l'archiver, pas la maintenir en espoir.

### Pour le design / UI
1. Si l'utilisateur fournit une image de référence (screenshot, mockup, wireframe) :
   - Génère le composant avec Tailwind CSS
   - Screenshot la page rendue avec Puppeteer (`npx puppeteer screenshot [url] --fullpage`)
   - Compare le screenshot avec la référence — vérifie :
     - Spacing et padding (en px)
     - Tailles de police, poids, line-height
     - Couleurs (hex exact)
     - Alignement et positionnement
     - Border radius, ombres
     - Rendu mobile
   - Corrige chaque écart trouvé
   - Re-screenshot et compare à nouveau
   - Répète jusqu'à < 3px d'écart partout
   - Minimum 2 passes de comparaison. Ne t'arrête pas après un seul tour.
   
## Structure des données

Le fichier `suivi.xlsx` contient 3 feuilles :

### Feuille "Candidatures"
Colonnes : ID, Entreprise, Poste, Localisation, Type poste, Date candidature, Statut, Date dernier contact, Prochaine action, Date prochaine action, Contact / RH, Source, Stack technique, Priorité, Commentaires.

**Statuts possibles** :
- `1er contact` : message LinkedIn ou email envoyé, en attente de réponse. Relance ≥ 7j, archiver si ≥ 21j sans retour.
- `En cours` : process actif (réponse reçue d'un humain, échange en cours), il faut suivre
- `Entretien prévu` : RDV confirmé
- `Offre` : proposition reçue
- `Refus` : explicitement refusé
- `Pas de réponse` : ghost après relance
- `Pas d'opportunités` : entreprise contactée mais pas de poste ouvert
- `Abandonnée` : Nedjmeddine ne veut plus

**Priorités** :
- `Haute` : process avancé (entretien passé ou contact direct actif)
- `Moyenne` : process RH démarré
- `Basse` : candidature brute sans contact
- `Archivée` : refus, pas d'opportunités, abandonnée

### Feuille "Entretiens"
Journal des entretiens passés avec détails (questions, interlocuteurs, ressenti, suite).

### Feuille "Dashboard"
Stats globales calculées par formules + objectifs hebdomadaires.

## Règles métier (à appliquer automatiquement)

### Détection des relances à faire

Quand l'utilisateur lance `/relances` :

1. Pour chaque candidature en statut `En cours` :
   - Si entretien passé (présent dans feuille Entretiens) sans retour depuis **≥ 10 jours** → **relance prioritaire**
   - Si candidature envoyée sans réponse depuis **≥ 7 jours** → relance standard
   - Si aucune réponse depuis **≥ 21 jours** → proposer de passer en `Pas de réponse` (archivage)

2. Classer par priorité décroissante :
   - D'abord : process avancé silencieux (entretien passé sans retour)
   - Puis : candidatures avec contact nominatif silencieuses
   - Puis : candidatures brutes

3. **Pour chaque relance, proposer un message rédigé** adapté au contexte (vouvoiement pour seniors/recruteurs, tutoiement pour peer-level).

4. **Plafond quotidien : `RELANCES_PAR_JOUR` dans `scripts/relances.py` (3 par défaut).** Si plusieurs candidatures arrivent à échéance la même semaine (ex : 14 relances d'un coup), ne pas tout proposer en une fois — étaler sur plusieurs jours. Les plus urgentes (CRITIQUE puis IMPORTANTE) sortent en premier ; le reste ressort automatiquement au `/relances` suivant une fois les précédentes traitées via `/update` (pas de mémoire d'état à gérer). Le dashboard web (`app.py`, `/api/dashboard`) affiche lui la liste complète sans plafond — c'est une vue de suivi, pas une file d'actions du jour.

### Briefing hebdo (`/briefing`)

Quand lancé (typiquement dimanche soir) :

1. **État du pipeline** : nombre de process actifs, priorités, prochaines actions de la semaine
2. **Relances prioritaires** (max 5)
3. **Candidatures "mortes" à archiver** (>21 jours sans réponse après relance)
4. **5 actions concrètes pour la semaine à venir** — pas forcément de nouvelles candidatures, plutôt des actions sur le pipeline existant
5. **Objectifs hebdo** : 5 candidatures ciblées, 5 relances, X heures de prépa entretien

### Ajout d'une candidature (`/ajouter`)

1. **Vérifier anti-doublon** : si l'entreprise existe déjà dans l'Excel, refuser ou proposer de mettre à jour l'existante.
2. Demander à l'utilisateur :
   - Entreprise, Poste, Localisation
   - Contact identifié (obligatoire pour priorité Haute/Moyenne)
   - Source
   - Stack
3. Calculer la priorité automatiquement selon présence de contact.
4. Écrire dans l'Excel.

### Update d'une candidature (`/update`)

1. Identifier la candidature par ID ou nom entreprise
2. Mettre à jour le statut, la date de dernier contact, les commentaires
3. Si nouveau statut = `En cours` et pas encore d'entretien → proposer d'ajouter dans feuille Entretiens si un entretien a eu lieu

### Interface Apollo — candidatures spontanées (onglet "Apollo" dans app.py)

Quand l'utilisateur colle une nouvelle liste de prospects Apollo (export talent acquisition / recrutement) dans le chat, reproduire systématiquement ce traitement, sans qu'il ait à le redemander :

1. **Extraire** prénom, nom, entreprise (et poste si disponible) pour chaque personne.
2. **Dédupliquer à un seul contact par entreprise** (qualité > volume — ne pas ajouter 3 recruteurs de la même boîte).
3. **Anti-doublon automatique** : `scripts/apollo_import.py` exclut déjà toute entreprise présente dans la table `candidatures` (peu importe le statut) — mais annoncer explicitement à l'utilisateur les entreprises exclues et pourquoi (ex : déjà en `Refus` ou `Pas d'opportunités`).
4. Écrire un fichier JSON `[{"prenom","nom","entreprise","poste"}, ...]` dans le scratchpad, puis lancer :
   `py -3 scripts/apollo_import.py fichier.json`
5. Les prospects apparaissent dans l'onglet **Apollo** de l'interface web (`app.py`, routes `/api/apollo` et `/api/apollo/marquer`) avec un message pré-rempli (template fixe défini dans `scripts/apollo_store.py::generer_message` — présentation + stack + recherche de mission freelance).
6. Depuis l'interface, l'utilisateur : cherche la personne sur Google (bouton 🔍), copie le message, l'envoie lui-même via Gmail ou WhatsApp (jamais d'envoi automatique — règle absolue n°1), puis marque "📧 Gmail" / "💬 WhatsApp" (statut `envoye` + canal tracé) ou "Ignorer" (statut `ignore`).
7. Une fois la table `prospects_apollo` vidée (tout traité), l'utilisateur colle une nouvelle liste et le cycle recommence — pas besoin de rebâtir l'interface, seulement de ré-importer via `apollo_import.py`.

## Comportement attendu de Claude — règles de communication

1. **Toujours terminer une session par une ligne explicite.** Après `/daily`, `/log`, `/briefing` ou toute séquence de tâches, terminer par :
   > **Tout est fait — rien d'autre à valider de ta part.**
   Ne jamais laisser la dernière phrase être un constat ambigu. L'utilisateur ne doit pas avoir à demander "c'est fini ?" pour savoir si quelque chose l'attend encore.

2. **Signaler les erreurs corrigées dans CLAUDE.md.** Quand une erreur est commise et corrigée (bug code, mauvais comportement, mauvaise hypothèse), la documenter ici pour ne pas la reproduire dans les sessions futures.

## Erreurs connues et corrections appliquées

### Encodage BOM sur Windows (scripts Python)
- **Erreur** : `json.decoder.JSONDecodeError: Unexpected UTF-8 BOM` quand PowerShell écrit un fichier JSON avec `Out-File` ou `[System.IO.File]::WriteAllText` — les fichiers sont écrits avec BOM (UTF-8 with BOM).
- **Fix appliqué** : `scripts/log.py` et `scripts/daily.py` ouvrent maintenant les fichiers d'input avec `encoding="utf-8-sig"` au lieu de `encoding="utf-8"`. Le `utf-8-sig` ignore automatiquement le BOM si présent.
- **À faire systématiquement** : tout nouveau script Python qui lit un JSON généré par PowerShell doit utiliser `open(fichier, encoding="utf-8-sig")`.

### Commande Python sur Windows
- **Erreur** : `python3` n'existe pas sur ce Windows — la commande retourne une erreur ou ouvre le Microsoft Store.
- **Fix** : toujours utiliser `py -3` dans les commandes PowerShell/Bash sur cette machine. Exemples : `py -3 scripts/daily.py`, `py -3 -m pip install ...`
- **Ne jamais utiliser** : `python3 ...` ou `python ...` seul (non fiable selon le PATH actif).
- **Si `py` n'est pas reconnu** (PATH incomplet dans certaines sessions shell) : utiliser le chemin complet `C:\Windows\py.exe -3 ...` en fallback.

### BOM ajouté par un here-string PowerShell piped vers stdin Python
- **Erreur** : piper un here-string PowerShell (`$answers = @'...'@; $answers | py -3 script.py`) vers un script Python interactif (qui utilise `input()`) fait apparaître un caractère BOM (`﻿`) collé au tout début de la **première** valeur lue (ex : entreprise `"﻿LUNDI MATIN"` au lieu de `"LUNDI MATIN"`). Le script ne plante pas, la donnée est juste polluée silencieusement.
- **Fix appliqué** : après un ajout/update via input pipé depuis PowerShell, vérifier la valeur enregistrée en base (`SELECT` direct) et nettoyer avec `REPLACE(colonne, CHAR(65279), '')` si un BOM est présent.
- **À faire systématiquement** : après tout `ajouter.py` / `update.py` lancé via un here-string piped (non-interactif), relire l'enregistrement créé/modifié pour vérifier l'absence de BOM avant de considérer la tâche terminée.

### Encodage emoji dans le terminal Windows (Python)
- **Erreur** : `UnicodeEncodeError: 'charmap' codec can't encode character` quand un script Python affiche des emoji (📝, 🎯, etc.) dans PowerShell — le terminal utilise cp1252 par défaut.
- **Fix** : toujours setter `$env:PYTHONIOENCODING = "utf-8"` avant d'exécuter un script Python qui affiche des emoji. Exemple : `$env:PYTHONIOENCODING = "utf-8"; py -3 scripts/daily.py ...`

### lib_excel.py est un wrapper SQLite, pas de l'Excel pur
- **Mauvaise hypothèse à éviter** : croire que `load_candidatures()` / `update_programmatic()` lisent/écrivent dans `suivi.xlsx`. Depuis la migration, ces fonctions délèguent entièrement vers `suivi_cdi.db` via `lib_db.py`.
- **Règle** : toute modification de schéma (nouvelle colonne, nouvelle table) se fait dans `lib_db.py` + migration dans `init_db()`. L'Excel n'est plus la source de vérité.

### calculer_priorite() ne gérait pas le statut "Entretien prévu"
- **Erreur** : `scripts/lib_excel.py::calculer_priorite()` ne testait que `statut == "Offre"` pour retourner `Haute`. Un passage à `Entretien prévu` (ex: via `/daily` après confirmation d'un RDV) retombait sur le `return "Basse"` par défaut — alors que la règle métier (voir section Priorités plus haut) classe un entretien prévu comme process avancé = `Haute`.
- **Fix appliqué** : ligne `if statut == "Offre": return "Haute"` remplacée par `if statut in ("Offre", "Entretien prévu"): return "Haute"`.
- **À vérifier systématiquement** : après tout update de statut vers `Entretien prévu` ou `Offre` via script, relire la priorité enregistrée pour confirmer qu'elle est bien `Haute` (le bug a pu se reproduire si ce fichier a été modifié depuis).

### Boutons du dashboard (relances) ciblaient la candidature par nom, pas par ID
- **Erreur** : `/api/relances/action` (app.py) et le JS `relanceAction()` (templates/index.html) identifiaient la candidature à modifier par **nom d'entreprise** envoyé au backend, qui la résolvait ensuite via `update_programmatic(entreprise_or_id=entreprise, ...)`. Cette résolution par nom retourne toujours la **première ligne** correspondante en base (`ORDER BY id`). Résultat : en présence de doublons (même entreprise sur plusieurs lignes, ex. LUNDI MATIN id 126 et 127), cliquer sur "✅ Relance envoyée" / "🚫 Pas d'opportunités" sur la carte affichée pour une ligne modifiait silencieusement une **autre** ligne portant le même nom — la carte cliquée ne disparaissait jamais, donnant l'impression que le clic ne faisait rien.
- **Fix appliqué** : le dict `relances` retourné par `/api/dashboard` inclut désormais `"id": c["id"]`. Le bouton et `relanceAction()` (JS) envoient `id` au lieu du nom d'entreprise ; `/api/relances/action` accepte `id` en priorité (fallback sur `entreprise` si absent, pour compat).
- **Cause racine encore présente** : les doublons d'entreprise (ex. LUNDI MATIN 126/127) ne sont pas fusionnés — seul le symptôme (ciblage aléatoire) est corrigé. Envisager une fusion manuelle ou un renfort de l'anti-doublon si de nouveaux doublons apparaissent.

### /daily : la recherche Gmail « boîte de réception » tronquée à 20 threads
- **Erreur** : la Recherche 4 de `/daily` (`in:inbox` hors jobboards) était limitée à `pageSize: 20` sans pagination. Sur une fenêtre de 3 jours (run du 12/10 couvrant le 09/10 → 12/10), la boîte contenait 56 threads, surtout des pubs. Le refus nominatif de Charlotte Santin (SOPREMA, `recrutement@soprema.fr`, 09/10 14h38) était 44e : jamais lu. Résultat : SOPREMA est restée en `1er contact` 4 jours et le `/daily` du 13/10 a proposé une relance via Liamine sur une candidature déjà refusée.
- **Fix appliqué** : `.claude/commands/daily.md` passe la Recherche 4 à `pageSize: 50` et impose de suivre `nextPageToken` jusqu'au bout.
- **À faire systématiquement** : sur toute recherche Gmail, vérifier la présence d'un `nextPageToken` avant d'annoncer « N threads récupérés ». Une fenêtre de plus d'un jour dépasse presque toujours une page.

### /daily : id d'événement `relance-<threadId>` déjà pris par une relance terminée
- **Erreur** : le 27/10, la nouvelle relance iSupplier (fil `1a0d869137fb67e2`, mail du 20/10) a été rejetée comme « doublon » par `daily.py`. L'id `relance-1a0d869137fb67e2` existait déjà pour la relance Torcy du 12/10, passée en `fait`. Le store déduplique sur l'id quel que soit le statut, donc un fil qui a déjà eu une relance ne peut plus en recevoir avec cet id.
- **Fix appliqué** : `.claude/commands/daily.md` impose `relance-<threadId>-<date_echeance>` quand l'id de base existe déjà en base.
- **À faire systématiquement** : quand `daily.py` annonce des doublons d'événements, identifier lesquels et vérifier qu'il s'agit de vrais doublons (`a_faire` identique), pas d'un ancien événement `fait`.

### /daily : `daily.py` plante sur une offre avec `"localisation": null`
- **Erreur** : le 19/11, `scorer_offre()` (`scripts/opportunites.py`) faisait `offre.get("localisation", "")`. La valeur par défaut ne s'applique pas quand la clé existe avec `null`, donc `None.strip()` → `AttributeError`. Le script s'arrête **après** avoir appliqué les updates : ils sont déjà écrits en base, mais ni le scoring, ni les actions, ni les événements, ni l'export ne sont faits.
- **Fix appliqué** : `scorer_offre()` utilise `offre.get(...) or ""` (et `or []` pour `stack`) sur tous les champs.
- **À faire systématiquement** : si `daily.py` plante en cours de route, **ne pas relancer le même JSON tel quel**. Les commentaires seraient ajoutés une 2e fois. Relancer avec `"commentaire": null` sur chaque update.

### `update_programmatic()` met `date_contact` à aujourd'hui quand on ne la fournit pas
- **Erreur** : un archivage (`statut: "Pas de réponse"`, `date_contact: null`) écrit `date_contact = date du jour`. La fiche a alors l'air contactée aujourd'hui, ce qui fausse les délais de relance et d'archivage. Constaté le 19/11 sur 11 fiches, corrigé à la main en remettant les anciennes dates.
- **À faire systématiquement** : pour un update qui ne correspond à aucun contact réel (archivage, simple commentaire), renseigner `date_contact` avec la date du **dernier vrai contact** (lue en base avant). Ne jamais laisser `null`.

### Python absent de la machine
- **Constat** : le 19/11, `py`, `C:\Windows\py.exe` et `python` (raccourci Windows Store) étaient tous introuvables : Python avait été désinstallé.
- **Fix** : `winget install --id Python.Python.3.12 -e --scope user`, puis `py -3 -m pip install -r requirements.txt`. Dans un terminal déjà ouvert, recharger le PATH : `$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")`.
- **Dépannage sans Python** : Node 24 (`node:sqlite`) permet de lire `suivi_cdi.db`.

### Anti-doublon des offres : caché seulement si contact récent
- Depuis le 20/11/2026, une offre d'une entreprise déjà dans le suivi **n'est plus retirée d'office**. Elle est cachée seulement si le dernier contact date de moins de 30 jours (`DELAI_RECONTACT_JOURS` dans `scripts/opportunites.py`) ou si un process est en cours (`En cours`, `Entretien prévu`, `Offre`). Sinon elle s'affiche avec un badge « Déjà contacté le JJ/MM/AAAA — statut ».
- Raison : une entreprise contactée il y a 3 mois peut avoir ouvert un nouveau poste.

## Anti-patterns à refuser

Si l'utilisateur demande :
- "Génère-moi 50 candidatures automatiquement" → **Refuser**, rappeler l'objectif qualité
- "Scrape LinkedIn" → **Refuser**, expliquer les risques
- "Envoie les emails tout seul" → **Refuser**, l'humain valide toujours
- "Ajoute 20 boîtes d'un coup sans contact identifié" → **Négocier** : max 5 à la fois, avec justification

## Scripts disponibles

- `scripts/briefing.py` : génère le briefing hebdo
- `scripts/relances.py` : liste les relances à faire + propose les messages
- `scripts/ajouter.py` : ajoute une candidature (avec anti-doublon)
- `scripts/update.py` : met à jour une candidature existante
- `scripts/lib_excel.py` : fonctions partagées
- `scripts/apollo_store.py` : CRUD + génération de message pour les prospects Apollo (table `prospects_apollo`)
- `scripts/apollo_import.py` : importe une liste de prospects Apollo (JSON), avec anti-doublon contre `candidatures`

## Stack technique

- Python 3 (`py -3` sur Windows) + SQLite via `lib_db.py` (source de vérité)
- `openpyxl` / `pandas` : backup export Excel uniquement (`sync_excel_from_db`)
- `flask` : interface web locale (`app.py`, port 5000)
- `requests` : recherche d'offres via l'API JSearch (`scripts/fetch_jsearch.py`, clé `RAPIDAPI_KEY`)
- `suivi_cdi.db` : base SQLite à la racine — candidatures, entretiens, offres, connexions LinkedIn

## Workflow recommandé

**Chaque dimanche soir (20 min)** :
1. `/briefing` → plan de la semaine
2. Lire les relances proposées, valider/amender les messages
3. Archiver les candidatures mortes

**En semaine (au fil de l'eau)** :
- `/ajouter` quand tu postules quelque part
- `/update` quand tu reçois une réponse

**Pas de spam.** Si une semaine tu n'as pas envie de chercher, c'est OK — mais tu l'actes et tu ne te fais pas d'illusions sur ton pipeline.

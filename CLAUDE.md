# Projet : Suivi recherche CDI Dev Full Stack

## Contexte

Nedjmeddine cherche un CDI développeur Full Stack. Priorité Strasbourg, ouvert France entière si besoin. Runway de 9 mois (démarré réellement fin janvier 2026). Stack : Node.js / Angular / React / .NET / Laravel / PHP.

## Objectif de ce projet

Outil de pilotage de recherche d'emploi. **Pas un outil d'automatisation massive.** Le but est de forcer la discipline et d'améliorer la qualité des candidatures et le suivi des relances, PAS d'industrialiser le spray-and-pray.

## Règles absolues — ne jamais violer

1. **Jamais d'envoi automatique** de candidature, email ou message LinkedIn. L'outil prépare, l'humain décide et envoie.
2. **Jamais de scraping** LinkedIn ou de sites d'emploi (risque de ban, RGPD). On utilise uniquement les emails reçus dans Gmail comme source de données si besoin.
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

## Stack technique

- Python 3 + `openpyxl` (manipulation Excel)
- `pandas` (analyses)
- Pas de dépendances externes (pas d'API, pas de scraping)

## Workflow recommandé

**Chaque dimanche soir (20 min)** :
1. `/briefing` → plan de la semaine
2. Lire les relances proposées, valider/amender les messages
3. Archiver les candidatures mortes

**En semaine (au fil de l'eau)** :
- `/ajouter` quand tu postules quelque part
- `/update` quand tu reçois une réponse

**Pas de spam.** Si une semaine tu n'as pas envie de chercher, c'est OK — mais tu l'actes et tu ne te fais pas d'illusions sur ton pipeline.

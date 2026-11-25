---
description: Bilan de fin de journée — fetch Gmail auto, update Excel, score les opportunités, export MD
---

Tu es le copilote de recherche CDI de Nedjmeddine. Lance la routine de fin de journée en 7 étapes.

**IMPORTANT : tu n'as jamais à demander à Nedjmeddine de coller des emails. Tu vas les chercher toi-même dans Gmail via les outils MCP.**

---

## Étape 1 — Détection de la fenêtre temporelle

1. Liste les fichiers `exports/daily_YYYY-MM-DD.md` avec `ls exports/daily_*.md 2>/dev/null | sort | tail -1` pour trouver la date du dernier run.
2. Calcule le nombre de jours depuis ce dernier run (aujourd'hui = 2026-04-21). Si aucun export → fenêtre = 7 jours par défaut.
3. Annonce à l'utilisateur : "Je vais chercher les emails des X derniers jours (depuis le JJ/MM)."

Exemples :
- Dernier run hier → cherche 1 jour
- Dernier run il y a 3 jours → cherche 3 jours (jamais plus de 14 jours)
- Jamais lancé → cherche 7 jours

---

## Étape 2 — Fetch Gmail automatique

Effectue ces recherches Gmail via les outils MCP (en parallèle si possible). Utilise `newer_than:Xd` avec X = nombre de jours détecté à l'étape 1.

**Recherche 1 — Réponses de recruteurs :**
```
query: "newer_than:Xd (sujet:candidature OR sujet:développeur OR sujet:opportunité OR sujet:poste OR sujet:recrutement OR sujet:entretien OR sujet:analyste) -from:noreply -from:no-reply"
```

**Recherche 2 — Emails LinkedIn :**
```
query: "newer_than:Xd from:linkedin.com"
pageSize: 30
```

**Recherche 3 — Alertes emploi (toutes plateformes) :**
```
query: "newer_than:Xd (from:welcometothejungle.com OR from:hellowork.com OR from:indeed.com OR from:apec.fr OR from:jobteaser.com OR from:cadremploi.fr OR from:meteojob.com OR from:monster.fr OR from:lesjeudis.com OR from:jobijoba.com OR from:optioncarriere.fr OR from:francetravail.fr OR from:pole-emploi.fr OR from:cadresonline.com OR from:talent.io OR from:chooseyourboss.com OR from:getpro.co OR from:programisto.fr OR from:michaelpage.fr OR from:robertwalters.fr OR from:regionsjob.com OR sujet:alerte OR sujet:offre)"
pageSize: 50
```

**Recherche 4 — Réponses directes dans la boîte de réception :**
```
query: "newer_than:Xd in:inbox -from:noreply -from:no-reply -from:linkedin.com -from:welcometothejungle.com -from:hellowork.com -from:indeed.com -from:cadremploi.fr -from:meteojob.com -from:monster.fr -from:lesjeudis.com -from:jobijoba.com -from:optioncarriere.fr -from:francetravail.fr -from:talent.io -from:getpro.co -from:programisto.fr"
pageSize: 50
```
⚠️ Cette recherche ramasse aussi les pubs et notifications, donc elle dépasse vite une page. **Si la réponse contient un `nextPageToken`, relance la même requête avec `pageToken` jusqu'à épuisement.** Ne jamais s'arrêter à la première page : un refus nominatif de SOPREMA (09/10) est resté invisible pendant 4 jours parce qu'il était 44e sur 56 threads avec `pageSize: 20`. Utilise `view: THREAD_VIEW_METADATA_ONLY` pour les pages suivantes si le volume est gros, puis `get_thread` sur les expéditeurs non publicitaires.

**Recherche 5 — Emails envoyés par Nedjmeddine :**
```
query: "newer_than:Xd in:sent -to:djillynedjmeddine@gmail.com"
pageSize: 30
```
Élargis la fenêtre de cette recherche à **au moins 14 jours** (`newer_than:14d` si X < 14), même si X est plus petit : un email envoyé il y a 10 jours doit encore être vérifié. Les threads récupérés ici sont traités dans le cas particulier « Emails envoyés sans réponse » de l'Étape 3.

Pour les threads qui semblent pertinents (recruteurs, réponses à candidatures), utilise `get_thread` pour récupérer le contenu complet.

Annonce : "J'ai récupéré N threads sur les X derniers jours."

---

## Étape 3 — Parse les emails : updates candidatures existantes

Analyse chaque thread/email et détecte les signaux suivants **pour des entreprises déjà dans le suivi** :

**⚠️ Règle absolue : seules les interactions avec une vraie personne nommée comptent.**
- Refus automatique (Easy Apply, HelloWork, WTTJ, LeHibou, beetween-software, noreply, etc.) → **ignorer complètement**, ne pas changer le statut
- Réponse générique sans nom de personne → **ignorer**

Signaux à traiter :
- **Message LinkedIn d'un vrai recruteur/contact** → ⭐ PRIORITAIRE si positif, mettre à jour `date_contact` + résumé en commentaire
- **Email nominatif d'un recruteur (avec nom et signature)** → mettre à jour `date_contact` + résumé en commentaire
- **Invitation entretien / demande de disponibilités (humaine)** → flag ⭐ PRIORITAIRE, signale-le en gras
- **Réponse humaine "pas d'opportunités"** → statut `Pas d'opportunités`
- **Tout le reste (alertes jobboards, refus auto, accusés de réception)** → ignorer (bruit)

### Cas particulier — emails envoyés sans réponse (Recherche 5) → relances à venir

Pour chaque thread de la Recherche 5 qui concerne la recherche d'emploi ou une mission freelance (recruteur, contact entreprise, ESN, prospection). Ignore les emails perso, administratifs ou commerciaux, ainsi que les candidatures envoyées à une adresse noreply.

1. Récupère le thread avec `get_thread` (format `MINIMAL` suffit) et regarde **l'ordre des messages, du plus récent au plus ancien**. Un message vient de Nedjmeddine si son expéditeur est `djillynedjmeddine@gmail.com`.
2. Applique cette règle :
   - **Dernier message = celui du contact** → il y a eu une réponse. Pas d'événement de relance : le thread est traité comme une réponse normale (voir signaux ci-dessus).
   - **Dernier message = Nedjmeddine ET le message juste avant est aussi de lui** (deux emails envoyés d'affilée sans réponse entre les deux, c'est-à-dire que la relance a déjà été faite) → **ne pas créer de relance**. Pas de 3e email. Si le dernier envoi date de ≥ 14 jours, propose d'archiver la candidature (`Pas de réponse`) au lieu de relancer.
   - **Dernier message = Nedjmeddine ET c'est son seul message consécutif** (le message d'avant vient du contact, ou il n'y en a pas) → **crée un événement de relance** :
     - `type: "relance"`
     - `date_echeance` = date d'envoi + 7 jours (+ 3 jours seulement si la personne ou le mail indique une urgence, par ex. mission qui démarre dans la semaine)
     - `id` = `"relance-<threadId>"`. Cet id fixe empêche le store d'ajouter un doublon lors des runs suivants. ⚠️ Le store refuse aussi un id déjà utilisé par un événement passé en `fait`. Si le fil a déjà eu une relance traitée (vérifie avec `SELECT id, statut FROM evenements WHERE id LIKE 'relance-<threadId>%'`), utilise `"relance-<threadId>-<date_echeance>"`.
     - `titre` = `"Relancer [Prénom Nom] ([Entreprise]) par [canal] — [sujet court]"` où `[canal]` = `Gmail`, `LinkedIn`, `WhatsApp`, `téléphone`… (le canal du dernier échange)
     - `description` = commence par `Canal : [canal] ([adresse email ou profil])`, puis date d'envoi, destinataire(s), résumé en une ligne de ce qui a été envoyé
     - ⚠️ **Toute relance (événement, action, récap du chat) doit préciser le canal.** Nedjmeddine doit savoir où relancer sans chercher.
     - `entreprise`, `contact` renseignés, `priorite: "normal"`
3. Avant d'ajouter, vérifie qu'un événement `a_faire` n'existe pas déjà pour ce contact (ex : créé à la main lors d'un run précédent) :
```powershell
$env:PYTHONIOENCODING = "utf-8"; py -3 -c "import sys; sys.path.insert(0,'scripts'); from evenements_store import lister; [print(e['date_echeance'], e['contact'], '|', e['titre']) for e in lister('a_faire')]"
```
   S'il existe déjà, ne le recrée pas.
4. Si la date de relance calculée est déjà passée (ou tombe aujourd'hui), mets aussi une entrée dans `actions` (type `relance`, priorité `normal`).

Affiche ces cas dans le récapitulatif de l'étape 6 sous une section dédiée :
```
RELANCES PROGRAMMÉES (emails envoyés sans réponse) :
  📅 Léa (MeetTribe) — mail du 28/09 → relance le 05/10
  ⛔ Jean Dupont (Acme) — déjà relancé 2x sans réponse → pas de relance, archiver ?
```

### Cas particulier — réponses automatiques d'absence (OOO / congés)

**⚠️ Ne pas les ranger dans "ignorer complètement".** Une réponse auto de type absence/congé n'est pas du bruit comme un refus automatique : elle contient une date de retour exploitable.

Repère les tournures : "actuellement absent(e)", "de retour le/dès/début [date]", "en congé (maternité/paternité) jusqu'à/jusqu'au", "back on", "away until", "réponse automatique". Ça vaut pour **toute boîte mail personnelle contactée** (candidatures classiques comme campagnes de prospection freelance/mission type "Opportunité de développement") — pas seulement les entreprises déjà dans le suivi Excel.

Pour chaque réponse auto avec date de retour détectée :
1. Extrais la date de retour. Si la date est exacte ("15 juillet") → utilise-la telle quelle. Si elle est approximative ("début novembre", "mi-septembre") → choisis une date raisonnable dans la période (ex : premier lundi du mois) et précise dans la description que c'est une approximation.
2. Ajoute un événement dans `evenements` (voir Étape 6) avec `type: "relance"`, `date_echeance` = date extraite, `entreprise` et `contact` renseignés, et une `description` qui rappelle le contexte (contact alternatif donné en son absence, sujet de l'email d'origine, etc.).
3. Si un contact alternatif est donné (ex: "contactez recrutement@x.com" en son absence), mentionne-le dans la `description` de l'événement.
4. Ce n'est **pas** un update de candidature Excel (pas de changement de statut) — uniquement un événement agenda pour se souvenir de relancer à la bonne date.

Signale ces cas dans le récapitulatif de l'étape 6 sous une ligne dédiée type :
```
📅 Manon Larcier (Solocal) absente → rappel de relance programmé le 15/07
```

### Cas particulier — campagne "Opportunité de développement - Mission freelance"

Nedjmeddine mène en parallèle du CDI une prospection de missions freelance par email (sujet type "Opportunité de développement - Mission freelance"). Ces entreprises **ne vont pas dans l'Excel candidatures** (hors périmètre CDI, voir CLAUDE.md), mais **chaque réponse doit être traitée, jamais ignorée silencieusement**.

- À l'étape 2, ajoute systématiquement cette recherche Gmail dédiée (en plus des 4 standards) :
```
query: "newer_than:Xd (subject:\"Opportunité de développement\" OR subject:\"Mission freelance\")"
pageSize: 30
```
- Pour chaque réponse reçue à cette campagne (hors auto-reply d'absence déjà traité ci-dessus) :
  - **Réponse qui attend une action de Nedjmeddine** (envoyer le CV, contacter un collègue suggéré par la personne, répondre à une question) → ajoute une entrée dans `actions` (type `general`, priorité `urgent` si la personne semble attendre une réponse rapide, sinon `normal`), titre clair : "Envoyer CV à [Contact] ([Entreprise])" ou "Contacter [Nom suggéré] chez [Entreprise] (suite au renvoi de [Contact])".
  - **Réponse fermée sans action requise** (ex : "pas de mission actuellement, on recontactera si besoin", CV déjà transmis) → pas d'entrée `actions`, mentionne-la simplement pour information dans le récapitulatif de l'étape 6.
  - **Réponse mentionnant un délai/une date de rappel** → crée aussi un événement dans `evenements` (même logique que le cas OOO ci-dessus).
  - **Échec de livraison (bounce, boîte pleine)** → mentionne-le pour information, pas d'action ni d'événement (pas de date exploitable).

Affiche ces cas dans le récapitulatif de l'étape 6 sous une section dédiée :
```
CAMPAGNE MISSION FREELANCE :
  ⚡ Envoyer CV à Aline Tan (Teaminside) → recommande son collègue Hervé Cuissette
  ℹ️  Julie Rhame (Acelys) → pas de mission ouverte, CV déjà transmis, rien à faire
```

Pour chaque email, affiche le résultat en une ligne :
```
✅ CELAD → statut passé à "Refus" (mail du 16/04)
✅ Morgane HICARD (SII) → nouveau contact le 18/04, résumé: "propose entretien manager"
⏭️  Accusé réception HelloWork (AddixWare) → ignoré (bruit)
```

Si une entreprise mentionnée dans un email **n'est pas dans le suivi**, note-la pour l'étape 5 (extraction d'opportunités).

**Si tu n'es pas sûr** de l'entreprise concernée par un email, pose une question précise avant de faire quoi que ce soit.

---

## Étape 4 — Connexions LinkedIn acceptées → messages à envoyer

Détecte dans les emails LinkedIn les notifications du type **"X a accepté votre invitation"** ou **"X a accepté votre demande de connexion"**.

**⚠️ RÈGLE ABSOLUE : sauvegarder IMMÉDIATEMENT dans le store, SANS attendre l'entreprise.**

Pour chaque acceptation trouvée :
1. Extrait le prénom, le nom et le thread_id
2. **Sauvegarde immédiatement** dans le store via ce script Python (entreprise = null si inconnue) :
```powershell
$env:PYTHONIOENCODING = "utf-8"; py -3 -c "
import sys; sys.path.insert(0, 'scripts')
from linkedin_store import ajouter_connexions
res = ajouter_connexions([
  {'prenom': 'Prénom', 'nom': 'Nom', 'entreprise': None, 'date_acceptation': 'YYYY-MM-DD', 'thread_id': 'THREAD_ID'},
])
print(res)
"
```
3. **Après** la sauvegarde, demande à Nedjmeddine les entreprises pour les connexions sans entreprise (pour générer les messages)
4. Vérifie si l'entreprise est déjà dans le suivi Excel (via `python3 scripts/lib_excel.py` si besoin)
5. Génère un message personnalisé basé sur ce template :

```
Bonjour [Prénom],

Je termine actuellement mon alternance en développement logiciel sur Strasbourg et je suis en recherche d'un CDI développeur.

J'ai vu que [Entreprise] recrute des consultants IT sur Strasbourg. Est-ce que vous avez des besoins en développement en ce moment ?

Je peux vous transmettre mon CV avec plaisir.

Bien cordialement,
Nedjmeddine Djilly
```

**Adaptations** :
- Si l'entreprise n'est pas à Strasbourg → "en France" ou la ville concernée
- Si c'est une boîte produit (pas une ESN) → remplacer "recrute des consultants IT" par "développe ses équipes tech"
- Si le poste de la personne est RH/recruteur → garder le template standard
- Si le poste est technique (CTO, dev) → adapter le ton légèrement plus direct

Affiche chaque message dans un bloc ```copy``` pour que Nedjmeddine puisse le copier directement sur LinkedIn.

⚠️ **Rappel : Nedjmeddine envoie lui-même le message sur LinkedIn. Tu ne fais que le préparer.**

---

## Étape 5 — Extraction des opportunités nouvelles

Depuis les mêmes emails, extrais toutes les offres d'emploi qui ne sont **pas encore dans le suivi** (vérifie la liste des candidatures existantes via `python3 scripts/lib_excel.py` si besoin).

**Gestion intelligente multi-jours :** si la fenêtre couvre plusieurs jours, il peut y avoir des offres dupliquées (même poste vu dans plusieurs alertes). Déduplique sur entreprise+poste avant de proposer. Le store `offres_store.py` gère aussi la déduplication côté persistance — une offre déjà scorée et sauvegardée ne sera pas re-proposée.

Pour chaque offre extraite (après déduplication), construis un objet JSON avec :
- `entreprise`, `poste`, `localisation`, `contrat` (CDI/CDD/Freelance)
- `stack` (liste des technos mentionnées)
- `contact` (nom du recruteur si présent dans l'email)
- `url` (lien offre si présent)
- `description` (texte complet de l'offre)
- `source` (LinkedIn / WTTJ / HelloWork / autre)

---

## Étape 6 — Validation et écriture

Montre à l'utilisateur le récapitulatif complet des actions proposées :

```
UPDATES À ÉCRIRE DANS L'EXCEL :
  ✅ Entreprise A → statut: Refus | commentaire: "..."
  ✅ Entreprise B → date_contact: 18/04 | commentaire: "..."

MESSAGES LINKEDIN À ENVOYER :
  💬 Laura (Reboot Conseil) → message prêt à copier
  💬 Marc (Accenture) → message prêt à copier

OFFRES À SCORER :
  • NovaCorp — Développeur Node.js — Strasbourg — CDI
  • ...

RELANCES PROGRAMMÉES (emails envoyés sans réponse) :
  📅 Léa (MeetTribe) — mail du 28/09 → relance le 05/10
  ⛔ Jean Dupont (Acme) — déjà relancé 2x → pas de relance

RAPPELS AGENDA (absences détectées) :
  📅 Manon Larcier (Solocal) absente → rappel programmé le 15/07
  📅 Blanche Le Camus (Theodo) congé maternité → rappel programmé début novembre
```

Demande une **validation globale** : "Confirmes-tu ces actions ? (oui / non / modifie X)"

Si l'utilisateur dit oui (ou donne des corrections), applique les modifications :

1. Écris le fichier `exports/daily_input_YYYY-MM-DD.json` avec la structure attendue par `daily.py` :
```json
{
  "date": "YYYY-MM-DD",
  "emails_analyses": <nombre de threads récupérés>,
  "updates": [...],
  "ignores": [...],
  "offres": [...],
  "connexions": [
    {
      "prenom": "Laura",
      "nom": "MARTIN",
      "entreprise": "Reboot Conseil",
      "date_acceptation": "YYYY-MM-DD"
    }
  ],
  "actions": [
    {
      "type": "message_linkedin",
      "priority": "urgent",
      "titre": "Répondre à [Prénom] ([Entreprise])",
      "description": "Ce qu'il faut faire concrètement",
      "contexte": "Pourquoi / source du signal",
      "message": "Bonjour [Prénom],\n\nTexte complet du message prêt à copier...\n\nNedjmeddine Djilly"
    }
  ],
  "evenements": [
    {
      "titre": "Recontacter [Prénom] ([Entreprise]) pour [raison]",
      "type": "relance",
      "date_echeance": "YYYY-MM-DD",
      "description": "Détail de l'échéance",
      "entreprise": "[Entreprise]",
      "contact": "[Prénom Nom]",
      "priorite": "normal"
    }
  ],
  "informations": [
    {
      "titre": "Groupe SII, Niji et Wikit recrutent à nouveau",
      "description": "Marqués « Pas d'opportunités » (juin–juillet). Pas de doublon créé : recontacter Vanessa Esteves (SII), Manon Lescureux (Niji) ou Alexis Mattio (Wikit) en citant l'offre.",
      "entreprise": null,
      "ville": "Strasbourg"
    }
  ]
}
```

**⚠️ RÈGLE ABSOLUE : le champ `"actions"` est OBLIGATOIRE.** De même, inclure `"evenements": []` (liste vide si rien à planifier) et `"informations": []`.

**Section « Informations du jour » (`informations`)** — affichée sur le dashboard avec un bouton « ✓ Lu ». Les infos **s'accumulent d'un /daily à l'autre** jusqu'à ce que Nedjmeddine clique « Lu » (store : `scripts/informations_store.py`, fichier `exports/informations.json`, dédup sur le titre).
- **Uniquement les infos importantes qui ne sont pas des actions**, par exemple :
  - une entreprise du suivi qui republie une offre alors qu'elle est en `Pas d'opportunités` ou en `Refus` (avec le nom du contact existant à recontacter) ;
  - une offre exclue parce que l'entreprise est déjà dans le suivi en `Refus` ou `Pas d'opportunités` (ex : « INFOGENE republie une offre Full Stack IA, déjà en Refus (#23) ») ;
  - un changement de situation sur un process (mission annulée, contact parti de l'entreprise, fusion ou rachat).
- **Jamais** : les offres hors cible (Java senior, tech lead, stack non indiquée, alternance), le bruit des jobboards, les newsletters, les refus automatiques. Ça reste uniquement dans le récap du chat.
- Si un point demande quelque chose de concret aujourd'hui, il va dans `actions`, pas dans `informations`.
- **Champ `ville` obligatoire** : la ville du poste ou de l'agence concernée (ex : `"Strasbourg"`, `"Lyon"`, `"Full remote"`). Le dashboard l'affiche en badge bien visible au-dessus du titre. Si l'offre ne donne qu'un pays ou rien, mets ce qui est connu (`"France (ville non précisée)"`) ou `null`, qui s'affiche « Ville non précisée ». Ne jamais inventer une ville.

**Quand détecter un événement futur ?** Dès qu'un échange mentionne une action à faire à une date précise ou dans un délai donné :
- "je vous recontacterai en juillet" → evenement type `relance`, date_echeance = début juillet
- "RDV prévu le XX" → evenement type `entretien` ou `rdv`
- "rappeler dans une semaine" → evenement type `relance`, date calculée
- "répondre avant le XX" → evenement type `admin`

**Quand un événement est aussi une action du jour**, met-le dans `actions` ET dans `evenements` (avec `date_echeance` = aujourd'hui).

**⚠️ RÈGLE ABSOLUE : le champ `"actions"` est OBLIGATOIRE.** Sans lui, le dashboard reste vide sans erreur. Si aucune action n'est détectée, inclure `"actions": []` explicitement — jamais omettre le champ.

**Champ `message` (messages rédigés)** : chaque fois que tu rédiges un mail, une réponse LinkedIn ou une relance pour une action (dans le récap du chat ou ailleurs), mets le texte complet, prêt à envoyer, dans le champ `message` de cette action. Le dashboard l'affiche dans un encadré avec un bouton « Copier ». Texte brut avec des `\n`, sans balises markdown. Si l'action ne demande pas de message (appel, lecture), omets le champ.

Types d'actions possibles : `message_linkedin`, `relance`, `general`
Priorités : `urgent` (appel/entretien/message actif), `normal` (tout le reste)

**Règle `connexions`** : inclure TOUTES les connexions acceptées détectées, même sans entreprise connue (mettre `"entreprise": null`). Le store linkedin_store.py déduplique automatiquement — une connexion déjà sauvegardée ne sera pas re-ajoutée.

2. Exécute : `$env:PYTHONIOENCODING = "utf-8"; py -3 scripts/daily.py exports/daily_input_YYYY-MM-DD.json`

   Le script sauvegarde automatiquement :
   - Les offres scorées → `exports/offres_a_postuler.json` (interface web onglet Offres)
   - Les connexions LinkedIn → `exports/messages_linkedin.json` (interface web section Connexions)

---

## Étape 7 — Affichage des résultats

Lis la sortie du script. Pour les opportunités retenues (score ≥ 40/100), affiche chaque fiche avec son score et sa checklist.

---

## Étape 8 — Résumé final

Affiche en fin de session :

```
📊 Pipeline : X actifs | Y relances critiques aujourd'hui
🎯 Z opportunité(s) qualifiée(s) (score moyen X/100)
💬 N message(s) LinkedIn à envoyer
📧 N emails parsés | M updates Excel effectués
📄 Export : exports/daily_YYYY-MM-DD.md
```

Puis donne ta lecture en 2-3 phrases : quelles sont les 1-2 actions à faire ce soir ou demain matin en priorité ?

---

**Rappel absolu : aucun email n'est envoyé automatiquement. Tu prépares, Nedjmeddine valide et envoie.**

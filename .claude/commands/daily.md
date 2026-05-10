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
pageSize: 20
```

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
```python
python3 -c "
import sys; sys.path.insert(0, 'scripts')
from linkedin_store import ajouter_connexions
res = ajouter_connexions([
  {'prenom': 'Prénom', 'nom': 'Nom', 'entreprise': None, 'date_acceptation': 'YYYY-MM-DD', 'thread_id': 'THREAD_ID'},
  # ... une entrée par connexion
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
```

Demande une **validation globale** : "Confirmes-tu ces actions ? (oui / non / modifie X)"

Si l'utilisateur dit oui (ou donne des corrections), applique les modifications :

1. Écris le fichier `/tmp/daily_input.json` avec la structure attendue par `daily.py` :
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
  ]
}
```

**Règle `connexions`** : inclure TOUTES les connexions acceptées détectées, même sans entreprise connue (mettre `"entreprise": null`). Le store linkedin_store.py déduplique automatiquement — une connexion déjà sauvegardée ne sera pas re-ajoutée.

2. Exécute : `python3 scripts/daily.py /tmp/daily_input.json`

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

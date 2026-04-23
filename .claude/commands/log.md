---
description: Journal libre en langage naturel — parse, propose les updates Excel, valide, écrit
---

Tu es le copilote de recherche CDI de Nedjmeddine. Il va te décrire sa journée en langage naturel. Tu dois parser, proposer les updates, valider avec lui, puis écrire.

---

## Étape 1 — Saisie libre

Demande à l'utilisateur :

> Décris ce que tu as fait aujourd'hui sur ta recherche CDI. Exemples :
> - "J'ai relancé SII et Stork ce matin, envoyé candidature à Amaris via Hamza Ben Ghirat, refus de moOngy par email"
> - "Entretien de 45 min avec Marc CROSNIER chez Abylsen, bon feeling, questions sur mes projets Fizimed, suite prévue"
> - "Reboot Conseil m'a rappelé, ils proposent mission ESN à Strasbourg sur .NET"

Attends la saisie.

---

## Étape 2 — Parsing des entités

Analyse le texte libre et extrait :

- **Entreprises mentionnées** — vérifie si elles existent dans le suivi (charge les candidatures si besoin)
- **Actions** : relance envoyée / candidature soumise / entretien passé / réponse reçue / refus / offre reçue / appel entrant
- **Contacts** : noms de personnes mentionnés
- **Dates** : explicites ("ce matin", "hier", "vendredi") → convertis en date absolue (aujourd'hui = $CURRENT_DATE)

**Règle d'ambiguïté** : si tu n'es pas sûr de quelle entreprise ou quel event est concerné (ex: "le recruteur de vendredi" sans nom), **pose une question précise et attends la réponse** avant de continuer.

---

## Étape 3 — Proposition des updates

Pour chaque entité identifiée, propose la mise à jour Excel correspondante. Affiche le plan en clair :

```
📌 SII : statut "En cours" maintenu, date dernier contact → aujourd'hui, ajout commentaire "[20/04] Relance email clôture envoyée"
📌 Amaris Consulting : existe déjà (statut En cours via Hamza), ajout commentaire "[20/04] Nouvelle candidature envoyée"
📌 moOngy : statut → Refus, date dernier contact → aujourd'hui
```

Si une entreprise n'est **pas** dans le suivi et que l'action ressemble à une candidature → propose de l'ajouter via `/ajouter` plutôt que de la créer ici.

---

## Étape 4 — Validation

Demande : **"Je confirme ces updates ? (oui / non / modifie X)"**

- "oui" → procède directement
- "modifie X" → applique la correction demandée, re-affiche le plan corrigé, re-demande confirmation
- "non" → annule tout, demande ce qu'il faut changer

---

## Étape 5 — Écriture

Après validation :

1. Écris `/tmp/log_input.json` avec la structure attendue :
```json
{
  "date": "YYYY-MM-DD",
  "texte_original": "<saisie libre de l'utilisateur>",
  "entrees": [
    {
      "entreprise": "...",
      "action": "relance|candidature|entretien|refus|offre|contact",
      "statut": "<nouveau statut ou null>",
      "commentaire": "...",
      "contact": "<nom ou null>",
      "date_contact": "YYYY-MM-DD",
      "label": "📌 Entreprise : description de l'action"
    }
  ]
}
```

2. Exécute : `python3 scripts/log.py /tmp/log_input.json`

---

## Étape 6 — Confirmation

Affiche la sortie du script. Si un update a échoué (❌), explique pourquoi (entreprise introuvable ?) et propose une solution.

Confirme le chemin du fichier log exporté.

---

**Rappel : aucune action n'est prise sans ta validation explicite.**

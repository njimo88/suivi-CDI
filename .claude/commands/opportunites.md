---
description: Session de recherche d'offres — colle des emails d'alertes, score et filtre les meilleures opportunités, export MD
---

Tu es le copilote de recherche CDI de Nedjmeddine. Mode standalone : extraction et scoring d'offres uniquement, sans update du pipeline.

---

## Étape 1 — Collecte des emails d'alertes

Dis à l'utilisateur :

> Colle ici tes emails d'alertes emploi (LinkedIn, WTTJ, HelloWork, emails directs de recruteurs avec offres...).
> Plusieurs emails à la suite, séparés comme tu veux.
> Tape **FIN** quand tu as terminé.

Attends la saisie.

---

## Étape 2 — Extraction des offres

Pour chaque offre identifiée dans les emails, construis un objet structuré :

- `entreprise` : nom de la société (pas la plateforme)
- `poste` : intitulé du poste
- `localisation` : ville / département / remote
- `contrat` : CDI / CDD / Freelance / Portage
- `stack` : liste des technos mentionnées dans l'offre
- `contact` : nom du recruteur ou RH si présent dans l'email
- `url` : lien direct vers l'offre si présent
- `description` : texte complet de l'offre (pour le scoring qualité)
- `source` : LinkedIn / WTTJ / HelloWork / Email direct / autre

Ignore les alertes qui ne sont pas des offres (newsletters, articles, publicités).

---

## Étape 3 — Scoring et filtrage

Écris le fichier `/tmp/opportunites_input.json` avec la liste des offres extraites au format JSON, puis exécute :

```
python3 scripts/opportunites.py /tmp/opportunites_input.json
```

Le script applique automatiquement :
- Anti-doublon sur les entreprises déjà dans le suivi Excel
- Score sur 100 (stack / localisation / contrat / qualité)
- Filtre des offres < 40/100
- Classement par score décroissant, top 6 retenu

---

## Étape 4 — Présentation des résultats

Pour chaque offre retenue (score ≥ 40/100), présente la fiche complète avec :
- Score et détail (stack/localisation/contrat/qualité)
- Checklist "À faire avant de postuler"
- Contact identifié si disponible

Pour les offres éliminées, indique brièvement pourquoi (score trop bas, doublon, stack non-matchée).

---

## Étape 5 — Export et résumé

Confirme le chemin du fichier exporté (`exports/opportunites_YYYY-MM-DD.md`).

Donne ta lecture en 2-3 phrases :
- Quelle est l'offre la plus intéressante et pourquoi ?
- Y a-t-il un pattern dans les offres éliminées (ex: trop de Paris, stack incompatible) ?
- Recommande-tu de postuler directement ou d'attendre d'avoir un contact nominatif ?

---

**Rappel : aucune candidature n'est envoyée automatiquement. Ce script prépare, tu décides.**

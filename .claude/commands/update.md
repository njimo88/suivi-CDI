---
description: Met à jour une candidature existante (statut, commentaire, entretien)
---

Met à jour une candidature existante.

Étapes :
1. Exécute `python scripts/update.py` en mode interactif
2. Le script demande le nom (ou ID) de l'entreprise, le nouveau statut, un commentaire horodaté
3. Si un entretien a eu lieu, le script propose de l'ajouter dans la feuille Entretiens

Usage typique :
- "J'ai eu un refus chez X" → /update, statut = Refus
- "J'ai eu un entretien aujourd'hui avec Y" → /update, statut inchangé, commentaire + ajout entretien
- "Ils m'ont fait une offre chez Z" → /update, statut = Offre (félicitations au passage)

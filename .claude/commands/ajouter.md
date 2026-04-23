---
description: Ajoute une nouvelle candidature dans le suivi (avec anti-doublon)
---

Ajoute une nouvelle candidature.

Étapes :
1. Exécute `python scripts/ajouter.py` en mode interactif
2. Le script va demander les infos une par une (entreprise, poste, contact, etc.)
3. Si l'entreprise existe déjà, le script m'alerte — on décide ensemble si c'est un nouveau poste ou un doublon
4. Après l'ajout, fais-moi un rappel : est-ce que j'ai bien un CONTACT identifié (pas juste "RH générique") ? Sinon, c'est de l'Easy Apply déguisé et ça ne marchera probablement pas.

Si je te dis que je veux juste ajouter plusieurs candidatures d'un coup sans contact, refuse et rappelle la règle : max 5/semaine, toutes avec contact identifié.

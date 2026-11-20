#!/usr/bin/env python3
"""
Gestion du store des prospects Apollo (candidatures spontanées) — lit/écrit dans SQLite via lib_db.
Statuts : "a_traiter" | "envoye" | "ignore"
"""
import hashlib
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_db import (
    init_db,
    apollo_lister, apollo_stats,
    apollo_marquer as _db_marquer,
    apollo_ajouter as _db_ajouter,
)

_VOYELLES = "aeiouàâäéèêëîïôùûü"


def _id_prospect(prenom: str, nom: str, entreprise: str) -> str:
    cle = f"{prenom.lower()}-{nom.lower()}-{entreprise.lower()}"
    return hashlib.md5(cle.encode()).hexdigest()[:12]


def generer_message(prenom: str, entreprise: str) -> str:
    elision = "qu'" if entreprise and entreprise[0].lower() in _VOYELLES else "que "
    return (
        f"Bonjour {prenom},\n\n"
        f"Je suis Nedjmeddine, développeur Full Stack (Node.js, React, Angular, .NET, Laravel). "
        f"J'ai fait deux ans d'alternance en développement logiciel et une expérience en freelance, "
        f"et je recherche une nouvelle mission.\n\n"
        f"Est-ce {elision}{entreprise} a des besoins en développement en ce moment ?\n\n"
        f"Je peux vous transmettre mon CV avec plaisir.\n\n"
        f"Bien cordialement,\n"
        f"DJILLY Nedjmeddine"
    )


def ajouter_prospects(prospects: list[dict]) -> dict:
    """Ajoute des prospects Apollo. Ignore les doublons (prenom+nom+entreprise)."""
    init_db()
    today = date.today().isoformat()
    batch = []
    for p in prospects:
        prenom, nom, entreprise = p["prenom"], p["nom"], p["entreprise"]
        batch.append({
            "id":         _id_prospect(prenom, nom, entreprise),
            "prenom":     prenom,
            "nom":        nom,
            "entreprise": entreprise,
            "poste":      p.get("poste", ""),
            "message":    p.get("message") or generer_message(prenom, entreprise),
            "statut":     "a_traiter",
            "date_ajout": today,
        })
    return _db_ajouter(batch)


def marquer(prospect_id: str, statut: str, canal: str = None) -> bool:
    init_db()
    _db_marquer(prospect_id, statut, canal)
    return True


def lister(statut: str = "a_traiter") -> list[dict]:
    init_db()
    return apollo_lister(statut)


def stats() -> dict:
    init_db()
    return apollo_stats()

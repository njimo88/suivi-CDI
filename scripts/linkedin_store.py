#!/usr/bin/env python3
"""
Gestion du store des messages LinkedIn — lit/écrit dans SQLite via lib_db.
Interface publique inchangée : ajouter_connexions, marquer, lister, stats, mettre_a_jour_entreprise.
Statuts : "en_attente" | "envoye" | "ignore"
"""
import hashlib
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_db import (
    init_db,
    linkedin_lister, linkedin_stats,
    linkedin_marquer as _db_marquer,
    linkedin_update_entreprise as _db_update_entreprise,
    linkedin_update_ville as _db_update_ville,
    linkedin_ajouter as _db_ajouter,
)


def _id_msg(prenom: str, nom: str, date_str: str) -> str:
    cle = f"{prenom.lower()}-{nom.lower()}-{date_str}"
    return hashlib.md5(cle.encode()).hexdigest()[:12]


def ajouter_connexions(connexions: list[dict]) -> dict:
    """Ajoute des connexions LinkedIn acceptées. Ignore les doublons."""
    init_db()
    today = date.today().isoformat()
    batch = []
    for c in connexions:
        batch.append({
            "id":               _id_msg(c["prenom"], c["nom"], c.get("date_acceptation", today)),
            "prenom":           c["prenom"],
            "nom":              c["nom"],
            "entreprise":       c.get("entreprise"),
            "ville":            c.get("ville"),
            "date_acceptation": c.get("date_acceptation", today),
            "thread_id":        c.get("thread_id"),
            "statut":           "en_attente",
            "date_action":      None,
        })
    return _db_ajouter(batch)


def mettre_a_jour_entreprise(msg_id: str, entreprise: str) -> bool:
    init_db()
    _db_update_entreprise(msg_id, entreprise)
    return True


def mettre_a_jour_ville(msg_id: str, ville: str) -> bool:
    init_db()
    _db_update_ville(msg_id, ville)
    return True


def marquer(msg_id: str, statut: str) -> bool:
    init_db()
    _db_marquer(msg_id, statut)
    return True


def lister(statut: str = "en_attente") -> list[dict]:
    init_db()
    return linkedin_lister(statut)


def stats() -> dict:
    init_db()
    return linkedin_stats()

#!/usr/bin/env python3
"""
Gestion du store des offres à postuler — lit/écrit dans SQLite via lib_db.
Interface publique inchangée : ajouter_offres, marquer, lister, stats, get_offre.
Statuts : "a_postuler" | "postule" | "ignore"
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_excel import normaliser_entreprise
from lib_db import (
    init_db,
    offres_lister, offres_stats, offres_get,
    offres_ajouter as _db_ajouter,
    offres_marquer as _db_marquer,
)


def _id_offre(offre: dict) -> str:
    cle = f"{normaliser_entreprise(offre.get('entreprise', ''))}-{offre.get('poste', '').strip().lower()[:40]}"
    return hashlib.md5(cle.encode()).hexdigest()[:12]


def ajouter_offres(nouvelles: list[dict]) -> dict:
    """Ajoute des offres scorées au store. Ignore les doublons."""
    init_db()
    from datetime import date
    today = date.today().isoformat()
    batch = []
    for o in nouvelles:
        batch.append({
            **o,
            "id": _id_offre(o),
            "statut": "a_postuler",
            "date_ajout": today,
            "date_action": None,
        })
    return _db_ajouter(batch)


def marquer(offre_id: str, statut: str) -> bool:
    init_db()
    _db_marquer(offre_id, statut)
    return True


def get_offre(offre_id: str) -> dict | None:
    init_db()
    return offres_get(offre_id)


def lister(statut: str = "a_postuler") -> list[dict]:
    init_db()
    return offres_lister(statut)


def stats() -> dict:
    init_db()
    return offres_stats()

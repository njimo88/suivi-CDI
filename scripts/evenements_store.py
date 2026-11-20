#!/usr/bin/env python3
"""Store pour les événements à venir — agenda / échéances."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from lib_db import (
    init_db,
    evenements_lister as db_lister,
    evenements_ajouter as db_ajouter,
    evenements_marquer as db_marquer,
)


def lister(statut: str = "a_faire", jours_max: int = None) -> list[dict]:
    init_db()
    return db_lister(statut, jours_max)


def ajouter(evenements: list[dict]) -> dict:
    init_db()
    return db_ajouter(evenements)


def marquer(event_id: str, statut: str):
    init_db()
    db_marquer(event_id, statut)


def stats() -> dict:
    init_db()
    tous = db_lister("a_faire")
    from datetime import date
    today = date.today().isoformat()
    urgents = [e for e in tous if e.get("priorite") == "urgent"]
    aujourd_hui = [e for e in tous if e.get("date_echeance") == today]
    return {
        "a_faire": len(tous),
        "urgent": len(urgents),
        "aujourd_hui": len(aujourd_hui),
    }

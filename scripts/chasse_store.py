#!/usr/bin/env python3
"""
Store de la « Chasse du jour » : entreprises à contacter trouvées par le skill /chasse.
Table SQLite : chasse_entreprises (schéma dans lib_db.py).
Statuts : "a_contacter" | "contacte" | "ignore"
"""
import hashlib
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_db import init_db, get_db
from lib_excel import normaliser_entreprise


def _id(entreprise: str) -> str:
    cle = f"{normaliser_entreprise(entreprise)}-{date.today().isoformat()}"
    return hashlib.md5(cle.encode()).hexdigest()[:12]


def deja_propose_recemment(entreprise: str, jours: int = 30) -> bool:
    """True si l'entreprise a déjà été proposée par /chasse dans les `jours` derniers jours."""
    init_db()
    limite = (date.today() - timedelta(days=jours)).isoformat()
    nom = normaliser_entreprise(entreprise)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT entreprise FROM chasse_entreprises WHERE date_ajout >= ?", (limite,)
        ).fetchall()
    return any(normaliser_entreprise(r["entreprise"]) == nom for r in rows)


def ajouter(entreprises: list[dict]) -> int:
    init_db()
    today = date.today().isoformat()
    n = 0
    with get_db() as conn:
        for e in entreprises:
            try:
                conn.execute(
                    """INSERT INTO chasse_entreprises
                       (id, entreprise, poste, localisation, source, url_offre, date_publication,
                        raison, deja_contacte, statut, date_ajout)
                       VALUES (?,?,?,?,?,?,?,?,?, 'a_contacter', ?)""",
                    (
                        _id(e["entreprise"]), e["entreprise"], e.get("poste") or "",
                        e.get("localisation") or "", e.get("source") or "",
                        e.get("url") or "", e.get("date_publication") or "",
                        e.get("raison") or "", e.get("deja_contacte") or "", today,
                    ),
                )
                n += 1
            except Exception:
                pass  # même entreprise déjà ajoutée aujourd'hui
    return n


def lister(statut: str = "a_contacter") -> list[dict]:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM chasse_entreprises WHERE statut=? ORDER BY date_ajout DESC, deja_contacte ASC, entreprise ASC",
            (statut,),
        ).fetchall()
    return [dict(r) for r in rows]


def get(chasse_id: str) -> dict | None:
    init_db()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM chasse_entreprises WHERE id=?", (chasse_id,)).fetchone()
    return dict(row) if row else None


def stats() -> dict:
    init_db()
    with get_db() as conn:
        rows = conn.execute(
            "SELECT statut, COUNT(*) AS n FROM chasse_entreprises GROUP BY statut"
        ).fetchall()
    c = {r["statut"]: r["n"] for r in rows}
    return {
        "a_contacter": c.get("a_contacter", 0),
        "contacte": c.get("contacte", 0),
        "ignore": c.get("ignore", 0),
    }


def marquer(chasse_id: str, statut: str) -> bool:
    init_db()
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE chasse_entreprises SET statut=?, date_action=? WHERE id=?",
            (statut, date.today().isoformat(), chasse_id),
        )
    return cur.rowcount > 0

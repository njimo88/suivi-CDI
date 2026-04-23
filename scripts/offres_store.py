#!/usr/bin/env python3
"""
Gestion du store persistant des offres à postuler.
Fichier : exports/offres_a_postuler.json

Statuts possibles : "a_postuler" | "postule" | "ignore"
"""
import json
import hashlib
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from lib_excel import ensure_exports_dir, normaliser_entreprise

STORE_FILE = Path(__file__).parent.parent / "exports" / "offres_a_postuler.json"


def _charger() -> list[dict]:
    if not STORE_FILE.exists():
        return []
    try:
        return json.loads(STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _sauvegarder(offres: list[dict]):
    ensure_exports_dir()
    STORE_FILE.write_text(json.dumps(offres, ensure_ascii=False, indent=2), encoding="utf-8")


def _id_offre(offre: dict) -> str:
    """ID stable basé sur entreprise + poste."""
    cle = f"{normaliser_entreprise(offre.get('entreprise', ''))}-{offre.get('poste', '').strip().lower()[:40]}"
    return hashlib.md5(cle.encode()).hexdigest()[:12]


def ajouter_offres(nouvelles: list[dict]) -> dict:
    """
    Ajoute des offres scorées au store. Ignore les doublons (même entreprise+poste).
    Retourne {"ajoutees": N, "doublons": N}.
    """
    existantes = _charger()
    ids_existants = {o["id"] for o in existantes}

    ajoutees = 0
    doublons = 0
    for o in nouvelles:
        oid = _id_offre(o)
        if oid in ids_existants:
            doublons += 1
            continue
        existantes.append({
            **o,
            "id": oid,
            "statut": "a_postuler",
            "date_ajout": date.today().isoformat(),
            "date_action": None,
        })
        ids_existants.add(oid)
        ajoutees += 1

    _sauvegarder(existantes)
    return {"ajoutees": ajoutees, "doublons": doublons}


def marquer(offre_id: str, statut: str) -> bool:
    """Marque une offre comme 'postule' ou 'ignore'. Retourne True si trouvée."""
    offres = _charger()
    for o in offres:
        if o["id"] == offre_id:
            o["statut"] = statut
            o["date_action"] = date.today().isoformat()
            _sauvegarder(offres)
            return True
    return False


def get_offre(offre_id: str) -> dict | None:
    """Retourne une offre par son ID, ou None si introuvable."""
    return next((o for o in _charger() if o["id"] == offre_id), None)


def lister(statut: str = "a_postuler") -> list[dict]:
    """Retourne les offres filtrées par statut, triées par score desc puis date desc."""
    offres = _charger()
    filtrees = [o for o in offres if o.get("statut") == statut]
    filtrees.sort(key=lambda o: (-o.get("score", 0), o.get("date_ajout", ""), ))
    return filtrees


def stats() -> dict:
    offres = _charger()
    return {
        "a_postuler": sum(1 for o in offres if o.get("statut") == "a_postuler"),
        "postule": sum(1 for o in offres if o.get("statut") == "postule"),
        "ignore": sum(1 for o in offres if o.get("statut") == "ignore"),
        "total": len(offres),
    }

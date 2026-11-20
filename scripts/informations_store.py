#!/usr/bin/env python3
"""Store pour les informations du jour — lit/écrit exports/informations.json.

Contrairement aux actions du jour, les informations ne sont pas remises à zéro
chaque jour : elles s'accumulent d'un /daily à l'autre et restent affichées
tant qu'elles ne sont pas marquées comme lues.
"""
import hashlib
import json
from datetime import date
from pathlib import Path

INFOS_FILE = Path(__file__).parent.parent / "exports" / "informations.json"


def _load() -> list:
    if not INFOS_FILE.exists():
        return []
    with open(INFOS_FILE, encoding="utf-8-sig") as f:
        return json.load(f)


def _save(infos: list):
    INFOS_FILE.parent.mkdir(exist_ok=True)
    with open(INFOS_FILE, "w", encoding="utf-8") as f:
        json.dump(infos, f, ensure_ascii=False, indent=2)


def _make_id(titre: str) -> str:
    return hashlib.md5(titre.strip().lower().encode("utf-8")).hexdigest()[:10]


def lister(statut: str = "non_lu") -> list:
    infos = _load()
    if statut == "all":
        return infos
    return [i for i in infos if i.get("statut", "non_lu") == statut]


def ajouter_informations(informations: list, date_str: str = None) -> dict:
    today = date_str or date.today().isoformat()
    infos = _load()
    existing_ids = {i["id"] for i in infos}
    added = 0
    for info in informations:
        titre = info.get("titre", "").strip()
        if not titre:
            continue
        info_id = info.get("id") or _make_id(titre)
        if info_id in existing_ids:
            continue
        infos.append({
            "id": info_id,
            "titre": titre,
            "description": info.get("description", ""),
            "entreprise": info.get("entreprise"),
            "ville": info.get("ville"),
            "statut": "non_lu",
            "date_created": today,
        })
        existing_ids.add(info_id)
        added += 1
    _save(infos)
    return {"ajoutes": added, "non_lus": sum(1 for i in infos if i["statut"] == "non_lu")}


def marquer_lu(info_id: str) -> bool:
    infos = _load()
    for i in infos:
        if i["id"] == info_id:
            i["statut"] = "lu"
            _save(infos)
            return True
    return False

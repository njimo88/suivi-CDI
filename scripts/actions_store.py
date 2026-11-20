#!/usr/bin/env python3
"""Store pour les actions du jour — lit/écrit exports/actions_du_jour.json."""
import json
from datetime import date
from pathlib import Path

ACTIONS_FILE = Path(__file__).parent.parent / "exports" / "actions_du_jour.json"


def _load() -> dict:
    if not ACTIONS_FILE.exists():
        return {"date": date.today().isoformat(), "actions": []}
    with open(ACTIONS_FILE, encoding="utf-8-sig") as f:
        return json.load(f)


def _save(data: dict):
    ACTIONS_FILE.parent.mkdir(exist_ok=True)
    with open(ACTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def lister(statut: str = "a_faire") -> list:
    data = _load()
    if statut == "all":
        return data.get("actions", [])
    return [a for a in data.get("actions", []) if a.get("statut", "a_faire") == statut]


def ajouter_actions(actions: list, date_str: str = None) -> dict:
    today = date_str or date.today().isoformat()
    data = _load()
    # Réinitialise si nouveau jour
    if data.get("date") != today:
        data = {"date": today, "actions": []}
    existing_ids = {a["id"] for a in data["actions"]}
    added = 0
    for i, a in enumerate(actions):
        action_id = a.get("id") or f"{today}-{i}"
        if action_id not in existing_ids:
            data["actions"].append({
                "id": action_id,
                "type": a.get("type", "general"),
                "priority": a.get("priority", "normal"),
                "titre": a.get("titre", ""),
                "description": a.get("description", ""),
                "contexte": a.get("contexte", ""),
                "message": a.get("message", ""),
                "statut": "a_faire",
                "date_created": today,
            })
            added += 1
    _save(data)
    return {"ajoutes": added, "total": len(data["actions"])}


def marquer(action_id: str, statut: str) -> bool:
    data = _load()
    for a in data["actions"]:
        if a["id"] == action_id:
            a["statut"] = statut
            _save(data)
            return True
    return False


def stats() -> dict:
    data = _load()
    actions = data.get("actions", [])
    return {
        "a_faire": sum(1 for a in actions if a.get("statut") == "a_faire"),
        "fait": sum(1 for a in actions if a.get("statut") == "fait"),
        "ignore": sum(1 for a in actions if a.get("statut") == "ignore"),
        "total": len(actions),
        "date": data.get("date", ""),
    }

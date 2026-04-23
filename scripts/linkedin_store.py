#!/usr/bin/env python3
"""
Gestion du store des messages LinkedIn à envoyer après acceptation de connexion.
Fichier : exports/messages_linkedin.json
Statuts : "en_attente" | "envoye" | "ignore"
"""
import json
import hashlib
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from lib_excel import ensure_exports_dir

STORE_FILE = Path(__file__).parent.parent / "exports" / "messages_linkedin.json"


def _charger() -> list[dict]:
    if not STORE_FILE.exists():
        return []
    try:
        return json.loads(STORE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _sauvegarder(msgs: list[dict]):
    ensure_exports_dir()
    STORE_FILE.write_text(json.dumps(msgs, ensure_ascii=False, indent=2), encoding="utf-8")


def _id_msg(prenom: str, nom: str, date_str: str) -> str:
    cle = f"{prenom.lower()}-{nom.lower()}-{date_str}"
    return hashlib.md5(cle.encode()).hexdigest()[:12]


def ajouter_connexions(connexions: list[dict]) -> dict:
    """
    Ajoute des connexions LinkedIn acceptées.
    connexions: [{prenom, nom, date_acceptation, thread_id?}]
    Ignore les doublons (même prenom+nom+date).
    """
    existants = _charger()
    ids_existants = {m["id"] for m in existants}

    ajoutes = 0
    doublons = 0
    for c in connexions:
        mid = _id_msg(c["prenom"], c["nom"], c.get("date_acceptation", date.today().isoformat()))
        if mid in ids_existants:
            doublons += 1
            continue
        existants.append({
            "id": mid,
            "prenom": c["prenom"],
            "nom": c["nom"],
            "entreprise": c.get("entreprise"),
            "date_acceptation": c.get("date_acceptation", date.today().isoformat()),
            "thread_id": c.get("thread_id"),
            "statut": "en_attente",
            "date_action": None,
        })
        ids_existants.add(mid)
        ajoutes += 1

    _sauvegarder(existants)
    return {"ajoutes": ajoutes, "doublons": doublons}


def mettre_a_jour_entreprise(msg_id: str, entreprise: str) -> bool:
    msgs = _charger()
    for m in msgs:
        if m["id"] == msg_id:
            m["entreprise"] = entreprise
            _sauvegarder(msgs)
            return True
    return False


def marquer(msg_id: str, statut: str) -> bool:
    """Marque comme 'envoye' ou 'ignore'."""
    msgs = _charger()
    for m in msgs:
        if m["id"] == msg_id:
            m["statut"] = statut
            m["date_action"] = date.today().isoformat()
            _sauvegarder(msgs)
            return True
    return False


def lister(statut: str = "en_attente") -> list[dict]:
    msgs = _charger()
    filtres = [m for m in msgs if m.get("statut") == statut]
    filtres.sort(key=lambda m: m.get("date_acceptation", ""), reverse=True)
    return filtres


def stats() -> dict:
    msgs = _charger()
    return {
        "en_attente": sum(1 for m in msgs if m.get("statut") == "en_attente"),
        "envoye": sum(1 for m in msgs if m.get("statut") == "envoye"),
        "ignore": sum(1 for m in msgs if m.get("statut") == "ignore"),
        "total": len(msgs),
    }

#!/usr/bin/env python3
"""
Importe une liste de prospects Apollo (recruteurs / talent acquisition) dans prospects_apollo.

Usage :
  py -3 scripts/apollo_import.py fichier.json
  (ou : cat fichier.json | py -3 scripts/apollo_import.py)

Format attendu (liste JSON) :
  [{"prenom": "...", "nom": "...", "entreprise": "...", "poste": "..."}, ...]

Anti-doublon : exclut automatiquement toute entreprise déjà présente dans la
table candidatures (déjà trackée dans le pipeline, peu importe le statut).
"""
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_db import init_db, get_db
from apollo_store import ajouter_prospects, generer_message


def _norm(s: str) -> str:
    return unicodedata.normalize("NFD", (s or "").lower().strip()).encode("ascii", "ignore").decode()


def entreprises_deja_trackees() -> set:
    init_db()
    with get_db() as conn:
        rows = conn.execute("SELECT DISTINCT entreprise FROM candidatures").fetchall()
    return {_norm(r["entreprise"]) for r in rows}


def importer(prospects: list[dict]) -> dict:
    trackees = entreprises_deja_trackees()
    a_importer = []
    exclus = []
    for p in prospects:
        if _norm(p["entreprise"]) in trackees:
            exclus.append(p)
            continue
        p = dict(p)
        p["message"] = p.get("message") or generer_message(p["prenom"], p["entreprise"])
        a_importer.append(p)
    resultat = ajouter_prospects(a_importer)
    resultat["exclus_deja_trackes"] = [f'{p["prenom"]} {p["nom"]} — {p["entreprise"]}' for p in exclus]
    return resultat


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8-sig") as f:
            donnees = json.load(f)
    else:
        donnees = json.load(sys.stdin)
    resultat = importer(donnees)
    print(json.dumps(resultat, ensure_ascii=False, indent=2))

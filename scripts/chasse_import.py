#!/usr/bin/env python3
"""
Import de la « Chasse du jour » (skill /chasse).

Reçoit la liste des offres lues par playwright-cli (classées de la plus à la moins
pertinente) et en garde 4 entreprises, une seule offre par entreprise :
  1. d'abord les entreprises absentes du suivi ;
  2. s'il en manque, des entreprises déjà contactées il y a plus de 30 jours
     et sans process en cours (affichées avec un badge « Déjà contacté le … »).

Toujours exclues :
  - Crédit Mutuel / Euro-Information / CIC (demande explicite, jamais proposées) ;
  - postes senior / lead / alternance / stage (est_exclu) ;
  - entreprises contactées il y a moins de 30 jours ou avec un process en cours ;
  - entreprises déjà proposées par /chasse dans les 30 derniers jours.

Usage :
  py -3 scripts/chasse_import.py fichier.json [--nombre 4]

Format JSON (UTF-8, BOM accepté) :
[
  {"entreprise": "Rexel France", "poste": "Développeur Fullstack React", "localisation": "Strasbourg",
   "source": "WTTJ", "url": "https://...", "date_publication": "2026-11-06",
   "raison": "React + Node, CDI, Strasbourg"}
]
"""
import argparse
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_excel import load_candidatures
from opportunites import est_exclu, info_deja_contacte
from chasse_store import ajouter, deja_propose_recemment

# Ne jamais proposer ces entreprises (demande explicite de Nedjmeddine, 25/11/2026)
EXCLUSIONS = ("credit mutuel", "creditmutuel", "euro information", "euroinformation",
              "euro-information", "cic ")


def _norm(txt: str) -> str:
    t = unicodedata.normalize("NFKD", txt or "").encode("ascii", "ignore").decode().lower()
    return " ".join(t.replace("-", " ").split()) + " "


def est_blacklistee(entreprise: str) -> bool:
    n = _norm(entreprise)
    return any(x.replace("-", " ") in n for x in EXCLUSIONS) or n.strip() == "cic"


def selectionner(offres: list[dict], nombre: int = 4) -> tuple[list[dict], list[str]]:
    candidatures = load_candidatures()
    nouvelles, deja, rejets, vues = [], [], [], set()

    for o in offres:
        nom = (o.get("entreprise") or "").strip()
        if not nom:
            continue
        cle = _norm(nom)
        if cle in vues:
            continue
        if est_blacklistee(nom):
            rejets.append(f"{nom} — exclue (Crédit Mutuel / Euro-Information)")
            vues.add(cle)
            continue
        exclu, raison = est_exclu(o)
        if exclu:
            rejets.append(f"{nom} — {o.get('poste', '')} : {raison}")
            continue
        if deja_propose_recemment(nom):
            rejets.append(f"{nom} — déjà proposée par /chasse ces 30 derniers jours")
            vues.add(cle)
            continue
        info = info_deja_contacte(nom, candidatures)
        vues.add(cle)
        if info is None:
            nouvelles.append(o)
        elif info["cacher"]:
            rejets.append(f"{nom} — dans le suivi ({info['statut']}, {info['date']}) : trop récent ou process en cours")
        else:
            deja.append({**o, "deja_contacte": f"{info['date']} — {info['statut']}"})

    retenues = (nouvelles + deja)[:nombre]
    return retenues, rejets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("fichier")
    parser.add_argument("--nombre", type=int, default=4)
    args = parser.parse_args()

    with open(args.fichier, encoding="utf-8-sig") as f:
        offres = json.load(f)

    retenues, rejets = selectionner(offres, args.nombre)
    n = ajouter(retenues)

    print(f"Chasse du jour : {n} entreprise(s) ajoutée(s) dans l'onglet « Chasse du jour »")
    for e in retenues:
        badge = f"  [déjà contacté {e['deja_contacte']}]" if e.get("deja_contacte") else "  [nouvelle]"
        print(f"  + {e['entreprise']} — {e.get('poste', '')} ({e.get('localisation', '')}, {e.get('source', '')}){badge}")
    if len(retenues) < args.nombre:
        print(f"  ! Seulement {len(retenues)} entreprise(s) retenue(s) sur {args.nombre} demandées")
    if rejets:
        print("Écartées :")
        for r in rejets:
            print(f"  - {r}")


if __name__ == "__main__":
    main()

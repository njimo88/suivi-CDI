#!/usr/bin/env python3
"""
Recherche d'offres CDI dev — source unique : JSearch (RapidAPI).

JSearch agrège Google Jobs, donc les offres d'Indeed, LinkedIn, HelloWork,
WTTJ, sites carrière… sans scraping de notre côté.

  Inscription : https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
  .env        : RAPIDAPI_KEY   (offre gratuite : 200 requêtes/mois)

Coût d'un scan : 2 mots-clés × N villes requêtes (chacune = 3 pages de quota).

Les alertes email (/opportunites, /daily) restent l'autre entrée d'offres.

Usage :
  py -3 scripts/fetch_jsearch.py Strasbourg Lyon
"""
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from opportunites import est_exclu, scorer_offre, filtrer_doublons
from offres_store import ajouter_offres
from lib_excel import load_candidatures, charger_dotenv

# ── Config ────────────────────────────────────────────────────────────────────

JSEARCH_URL = "https://jsearch.p.rapidapi.com/search-v2"
JSEARCH_KWS = ["développeur full stack CDI", "développeur web CDI"]
JSEARCH_NUM_PAGES = "3"  # ~3x plus de quota, ~3x plus d'offres
SEUIL_SCORE = 40

# Pays par ville — défaut "fr" (ex : Kehl, juste en face de Strasbourg)
_VILLE_COUNTRY = {"Kehl": "de"}
_PAYS_LABEL = {"fr": "France", "de": "Allemagne"}

TECH_KEYWORDS = [
    "Node.js", "NodeJS", "Angular", "React", "Vue.js", "VueJS",
    ".NET", "C#", "ASP.NET", "PHP", "Laravel", "Symfony",
    "JavaScript", "TypeScript", "HTML", "CSS",
    "SQL Server", "MySQL", "PostgreSQL", "MongoDB",
    "Docker", "Git", "AWS", "GCP", "Linux",
    "REST", "API", "DevOps", "Microservices",
    "Spring", "Java", "Python",
]

_EXCLUDE_TYPES = ("part_time", "intern", "temporary", "volunteer",
                  "temps partiel", "stage", "alternance", "apprentissage")


def detecter_stack(texte: str) -> list[str]:
    t = texte.lower()
    return [k for k in TECH_KEYWORDS if k.lower() in t]


# ── JSearch ───────────────────────────────────────────────────────────────────

def _api_key() -> str:
    charger_dotenv()
    return os.environ.get("RAPIDAPI_KEY", "").strip()


def _jsearch_page(api_key: str, keyword: str, ville: str) -> list[dict]:
    pays = _VILLE_COUNTRY.get(ville, "fr")
    params = {
        "query":       f"{keyword} {ville} {_PAYS_LABEL[pays]}",
        "page":        "1",
        "num_pages":   JSEARCH_NUM_PAGES,
        "country":     pays,
        "date_posted": "week",
    }
    headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"}
    try:
        r = requests.get(JSEARCH_URL, headers=headers, params=params, timeout=30)
        r.raise_for_status()
        return r.json().get("data", {}).get("jobs", [])
    except Exception:
        return []


def _normaliser(item: dict, ville: str) -> dict | None:
    titre      = (item.get("job_title") or "").strip()
    entreprise = (item.get("employer_name") or "").strip()
    if not titre or not entreprise:
        return None
    emp_type = (item.get("job_employment_type") or "").lower()
    if emp_type and any(t in emp_type for t in _EXCLUDE_TYPES):
        return None
    description = (item.get("job_description") or "").strip()
    posted      = item.get("job_posted_at_datetime_utc") or ""
    return {
        "entreprise":       entreprise,
        "poste":            titre,
        "localisation":     (item.get("job_city") or item.get("job_state") or ville).strip() or ville,
        "contrat":          "CDI",
        "stack":            detecter_stack(description + " " + titre),
        "contact":          "",
        "url":              (item.get("job_apply_link") or item.get("job_google_link") or "").strip(),
        "description":      description[:2000],
        "source":           f"JSearch · {pub}" if (pub := (item.get("job_publisher") or "").strip()) else "JSearch",
        "date_publication": posted[:10] if len(posted) >= 10 else "",
    }


# ── Pipeline ──────────────────────────────────────────────────────────────────

def fetch_and_score(villes: list[str]) -> dict:
    """Scanne JSearch sur les villes, filtre, score, enregistre.
    Retourne {ok, progress, offres, total_brut, qualifiees, ajoutees_store}."""
    api_key = _api_key()
    if not api_key:
        return {
            "ok": False,
            "error": "credentials_missing",
            "message": "RAPIDAPI_KEY absente du .env (gratuit sur rapidapi.com, API JSearch).",
        }

    progress: list[dict] = []
    brutes: list[dict] = []
    for ville in villes:
        n = 0
        for kw in JSEARCH_KWS:
            for item in _jsearch_page(api_key, kw, ville):
                o = _normaliser(item, ville)
                if o:
                    brutes.append(o)
                    n += 1
        progress.append({"type": "fetch", "ville": ville, "count": n})

    # Dédup locale (même entreprise + même intitulé)
    dedup: dict[tuple, dict] = {}
    for o in brutes:
        dedup.setdefault((o["entreprise"].lower(), o["poste"].lower()[:40]), o)
    offres = list(dedup.values())

    # 1. Profil : senior / alternance / stage
    retenues = []
    for o in offres:
        exclu, raison = est_exclu(o)
        if exclu:
            progress.append({"type": "exclu_profil", "label": f"{o['entreprise']} — {o['poste']}", "raison": raison})
        else:
            retenues.append(o)

    # 2. Déjà contactée récemment / process en cours → caché ; sinon badge
    nouvelles, ignores = filtrer_doublons(retenues, load_candidatures())
    for txt in ignores:
        nom, _, raison = txt.partition(" — ")
        progress.append({"type": "doublon", "label": nom, "raison": raison or "déjà contactée"})

    # 3. Score
    scorees = [scorer_offre(o) for o in nouvelles]
    top = sorted([o for o in scorees if o["score"] >= SEUIL_SCORE], key=lambda o: -o["score"])
    for o in scorees:
        if o["score"] < SEUIL_SCORE:
            progress.append({"type": "sous_seuil", "label": f"{o['entreprise']} — {o['poste']}", "score": o["score"]})
    for o in top:
        progress.append({"type": "retenu", "label": f"{o['entreprise']} — {o['poste']}", "score": o["score"]})

    # 4. Enregistrement
    res_store = ajouter_offres(top) if top else {"ajoutees": 0}

    return {
        "ok":             True,
        "progress":       progress,
        "offres":         top,
        "total_brut":     len(offres),
        "qualifiees":     len(top),
        "ajoutees_store": res_store.get("ajoutees", 0),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Recherche d'offres via JSearch")
    parser.add_argument("villes", nargs="+")
    args = parser.parse_args()

    res = fetch_and_score(args.villes)
    if not res.get("ok"):
        print("Erreur :", res.get("message"))
        sys.exit(1)
    print(f"{res['total_brut']} offres | {res['qualifiees']} qualifiées | {res['ajoutees_store']} nouvelles")
    for o in res["offres"]:
        badge = f"  [déjà contacté {o['deja_contacte']}]" if o.get("deja_contacte") else ""
        print(f"  [{o['score']}/100] {o['entreprise']} — {o['poste']} ({o['localisation']}){badge}")

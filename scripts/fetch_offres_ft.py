#!/usr/bin/env python3
"""
Fetch offres CDI dev depuis l'API France Travail (ex-Pôle Emploi).

Credentials (variables d'environnement ou .env) :
  FT_CLIENT_ID      → client_id de l'app francetravail.io
  FT_CLIENT_SECRET  → client_secret de l'app francetravail.io

Inscription gratuite : https://francetravail.io/data/api/offres-emploi

Usage :
  python3 scripts/fetch_offres_ft.py
  python3 scripts/fetch_offres_ft.py --jours 31
"""

import os
import sys
import json
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from opportunites import traiter_offres
from offres_store import ajouter_offres

FT_TOKEN_URL = "https://entreprise.francetravail.fr/connexion/oauth2/access_token"
FT_SEARCH_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"

# ROME codes dev / SI (M1805 = études & dev info, M1802 = expertise SI)
ROME_CODES = ["M1805", "M1802"]
DEPARTEMENTS = ["67"]  # Bas-Rhin

# Mots-clés tech pour détecter la stack dans les descriptions
TECH_KEYWORDS = [
    "Node.js", "NodeJS", "Angular", "React", "Vue.js", "VueJS",
    ".NET", "C#", "ASP.NET", "PHP", "Laravel", "Symfony",
    "JavaScript", "TypeScript", "HTML", "CSS",
    "SQL Server", "MySQL", "PostgreSQL", "MongoDB",
    "Docker", "Git", "AWS", "GCP", "Linux",
    "REST", "API", "DevOps", "Microservices",
    "Spring", "Java", "Python",
]


def _charger_dotenv():
    """Charge .env à la racine du projet si présent."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_token(client_id: str, client_secret: str) -> str:
    resp = requests.post(
        FT_TOKEN_URL,
        params={"realm": "/partenaire"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": "api_offresdemploiv2 o2dsoffre",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def search_offres(token: str, departement: str, rome: str, jours: int = 31) -> list[dict]:
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "typeContrat": "CDI",
        "departement": departement,
        "codeROME": rome,
        "publieeDepuis": str(min(jours, 31)),
        "range": "0-149",
    }
    resp = requests.get(FT_SEARCH_URL, headers=headers, params=params, timeout=20)
    if resp.status_code == 204:
        return []
    resp.raise_for_status()
    return resp.json().get("resultats", [])


def normaliser_offre(o: dict) -> dict:
    """Convertit une offre France Travail au format attendu par opportunites.py"""
    titre = o.get("intitule", "")
    description = o.get("description", "")
    entreprise_nom = o.get("entreprise", {}).get("nom", "")

    lieu = o.get("lieuTravail", {})
    libelle_lieu = lieu.get("libelle", "")
    code_postal = lieu.get("codePostal", "")
    dept = code_postal[:2] if code_postal else ""
    localisation = f"{libelle_lieu} ({dept})" if dept else libelle_lieu

    contact_nom = ""
    contact = o.get("contact", {})
    if isinstance(contact, dict):
        contact_nom = contact.get("nom", "") or contact.get("prenom", "")

    offre_id = o.get("id", "")
    url_origine = o.get("origineOffre", {}).get("urlOrigine", "")
    url = url_origine or f"https://candidat.francetravail.fr/offres/recherche/detail/{offre_id}"

    text_search = (description + " " + titre).lower()
    stack = [t for t in TECH_KEYWORDS if t.lower() in text_search]

    return {
        "entreprise": entreprise_nom or "Entreprise non précisée",
        "poste": titre,
        "localisation": localisation,
        "contrat": "CDI",
        "stack": stack,
        "contact": contact_nom,
        "url": url,
        "description": description[:2000],
        "source": "France Travail",
    }


def fetch_and_score(jours: int = 31) -> dict:
    _charger_dotenv()

    client_id = os.environ.get("FT_CLIENT_ID", "").strip()
    client_secret = os.environ.get("FT_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        return {
            "error": "credentials_missing",
            "message": "FT_CLIENT_ID et FT_CLIENT_SECRET non configurés. "
                       "Inscription gratuite sur https://francetravail.io/data/api",
        }

    try:
        token = get_token(client_id, client_secret)
    except requests.HTTPError as e:
        return {"error": "auth_failed", "message": f"Authentification échouée : {e}"}

    offres_brutes = []
    for dept in DEPARTEMENTS:
        for rome in ROME_CODES:
            try:
                resultats = search_offres(token, dept, rome, jours)
                offres_brutes.extend(resultats)
            except Exception as e:
                pass

    # Dédupliquer par ID France Travail
    seen_ids: set = set()
    dedup = []
    for o in offres_brutes:
        oid = o.get("id")
        if oid and oid not in seen_ids:
            seen_ids.add(oid)
            dedup.append(o)

    # Filtrer les offres sans nom d'entreprise
    dedup = [o for o in dedup if o.get("entreprise", {}).get("nom")]

    # Normaliser au format interne
    offres_norm = [normaliser_offre(o) for o in dedup]

    # Scorer + anti-doublon Excel
    resultats = traiter_offres(offres_norm)

    # Ajouter au store
    res_store = {"ajoutees": 0, "doublons": 0}
    if resultats["top"]:
        res_store = ajouter_offres(resultats["top"])

    return {
        "total_brut": len(dedup),
        "qualifiees": len(resultats["top"]),
        "ignorees_excel": len(resultats["ignores"]),
        "sous_seuil": len(resultats["exclues"]),
        "ajoutees_store": res_store["ajoutees"],
        "doublons_store": res_store["doublons"],
        "offres": resultats["top"],
        "jours": jours,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fetch offres France Travail")
    parser.add_argument("--jours", type=int, default=31, help="Fenêtre temporelle (max 31)")
    args = parser.parse_args()

    result = fetch_and_score(args.jours)

    if "error" in result:
        print(f"❌ {result['message']}")
        sys.exit(1)

    print(f"📡 France Travail — {args.jours} derniers jours — Bas-Rhin (67)")
    print(f"   {result['total_brut']} offres CDI dev récupérées")
    print(f"   ✅ {result['qualifiees']} qualifiées (score ≥40/100)")
    print(f"   ⏭️  {result['ignorees_excel']} déjà dans l'Excel")
    print(f"   ❌ {result['sous_seuil']} sous le seuil de pertinence")
    print(f"   💾 {result['ajoutees_store']} nouvelles dans le store")

    for o in result["offres"]:
        d = o.get("detail_score", {})
        print(f"\n   🎯 [{o['score']}/100] {o['entreprise']} — {o['poste']}")
        print(f"      {o['localisation']} | stack: {', '.join(o.get('stack', [])[:5])}")
        print(f"      Score: stack {d.get('stack',0)}/50 | loc {d.get('localisation',0)}/30 | contrat {d.get('contrat',0)}/10")
        if o.get("url"):
            print(f"      {o['url']}")

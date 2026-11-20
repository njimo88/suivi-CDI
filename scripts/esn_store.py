#!/usr/bin/env python3
"""
Gestion du store des ESN Strasbourg (candidatures spontanées) — lit/écrit dans SQLite via lib_db.
Statuts : "a_contacter" | "contacte" | "en_cours" | "refus" | "sans_suite"

Usage (seed du référentiel local) :
  py -3 scripts/esn_store.py
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_db import (
    init_db,
    esn_lister, esn_stats,
    esn_marquer as _db_marquer,
    esn_ajouter as _db_ajouter,
)

# Liste vérifiée d'ESN ayant une agence confirmée à Strasbourg / Eurométropole
# (recherche web au 2026-09-15 — voir rapport de session pour le détail des sources).
ESN_STRASBOURG = [
    {
        "nom": "Sopra Steria",
        "site_web": "https://www.soprasteria.fr/",
        "specialite": "Conseil, intégration de systèmes, édition de logiciels — grands comptes banque/assurance/industrie",
        "notes": "Agence 15 Av. de l'Europe, 67300 Schiltigheim",
    },
    {
        "nom": "CGI",
        "site_web": "https://www.cgi.com/france/fr-fr/recrute/strasbourg",
        "specialite": "Conseil et services numériques — banque, assurance, secteur public",
        "notes": "Agence 6 rue Eugénie Brazier, 67400 Illkirch-Strasbourg",
    },
    {
        "nom": "Inetum",
        "site_web": "https://www.inetum.com/fr-fr",
        "specialite": "Services IT et solutions digitales — env. 200 collaborateurs en région Grand Est",
        "notes": "Agence Espace Européen de l'Entreprise, Bât. C, Av. de l'Europe, 67300 Schiltigheim",
    },
    {
        "nom": "Capgemini",
        "site_web": "https://www.capgemini.com/fr-fr/nous-trouver/",
        "specialite": "Conseil, transformation digitale, ingénierie",
        "notes": "Agences 17 rue La Haye, 67300 Schiltigheim et 950 bd Sébastien Brant, 67400 Illkirch",
    },
    {
        "nom": "Amaris Consulting",
        "site_web": "https://amaris.com/fr/",
        "specialite": "Conseil IT indépendant — centres de services Microsoft, web/digital, ERP/BI",
        "notes": "Agence à Schiltigheim (67300), ~200 collaborateurs, 3 centres de services",
    },
    {
        "nom": "Sii",
        "site_web": "https://sii-group.com/fr-FR/sii-est",
        "specialite": "Ingénierie et conseil en technologies — banque/assurance, retail, télécoms, industrie",
        "notes": "Agence Sii Est, 10 Boulevard de Dresde, 67000 Strasbourg (créée en 2000)",
    },
    {
        "nom": "Extia",
        "site_web": "https://www.extia-group.com/",
        "specialite": "Conseil et ingénierie IT — Java, DevOps, Linux, AMOA",
        "notes": "Agence ouverte en 2021, 7 Rue de la Haye, 67300 Schiltigheim",
    },
    {
        "nom": "Akkodis",
        "site_web": "https://www.akkodis.com/en/branches/france/schiltigheim/akkodis-strasbourg",
        "specialite": "Ingénierie et IT — ex Modis/Akka",
        "notes": "Agence 11 Rue de Madrid, 67300 Schiltigheim",
    },
    {
        "nom": "Expleo",
        "site_web": "https://www.expleogroup.com/fr/",
        "specialite": "Ingénierie, qualité et conseil en transformation digitale",
        "notes": "Agence à Entzheim, agglomération de Strasbourg (ex-Assystem Technologies)",
    },
    {
        "nom": "Randstad Digital (ex-AUSY)",
        "site_web": "https://www.randstaddigital.com/fr-fr/",
        "specialite": "Ingénierie et conseil IT — aéronautique/défense, télécoms, banque/finance",
        "notes": "Agence ouverte en 1995, 16 Avenue de l'Europe, Bât. SXB1, 67300 Schiltigheim",
    },
    {
        "nom": "CITECH",
        "site_web": "https://citech.fr/en/contact-citech-strasbourg/",
        "specialite": "ESN généraliste — ingénierie informatique",
        "notes": "Agence commerciale dédiée à Strasbourg",
    },
    {
        "nom": "Alteca",
        "site_web": "https://www.alteca.fr/agences/strasbourg/",
        "specialite": "Conseil, dev C#/Java/Angular, DevOps, data, IA générative — banque/assurance/retail",
        "notes": "Agence 23 Rue de la Haye, 67300 Schiltigheim",
    },
    {
        "nom": "Syxperiane",
        "site_web": "https://syxperiane.com/qui-sommes-nous/esn-strasbourg/",
        "specialite": "ERP/CRM (Divalto), SIRH, BI, infrastructure IT, cybersécurité",
        "notes": "Agence 14 Rue du Parc, 67205 Oberhausbergen (Eurométropole de Strasbourg)",
    },
    {
        "nom": "SCAFE",
        "site_web": "https://scafe.io/agences/esn-strasbourg/",
        "specialite": "Cloud & DevOps, cybersécurité (NIS2/DORA), FinOps",
        "notes": "Agence 32 Rue du Bassin d'Austerlitz, 67100 Strasbourg (Presqu'île Malraux)",
    },
    {
        "nom": "Apside",
        "site_web": "https://www.apside.com/fr/agence/strasbourg/",
        "specialite": "ESN généraliste — ingénierie logicielle",
        "notes": "Agence Strasbourg (établissements SIRET confirmés 67000/67200)",
    },
    {
        "nom": "ITS Future",
        "site_web": "https://its-future.com/",
        "specialite": "Développement applicatif sur mesure (spécialiste local, fondée en 2015)",
        "notes": "Agence Parc Des Forges, 5 Rue Hannah Arendt, 67200 Strasbourg",
    },
    {
        "nom": "Versusmind",
        "site_web": "https://versusmind.eu/agence-de-strasbourg/",
        "specialite": "Développement logiciel sur mesure, web & mobile",
        "notes": "Agence 10 place Gutenberg, 67000 Strasbourg",
    },
    {
        "nom": "Infotel",
        "site_web": "https://www.infotel.com/",
        "specialite": "Gestion de patrimoine data, conseil et services IT",
        "notes": "Agence ouverte en 2015, Tour Sébastopol, 3 Quai Kléber, 67000 Strasbourg",
    },
    # ── Deuxième vague (recherche approfondie, 2026-09-15) ──────────────────
    {
        "nom": "Numesia",
        "site_web": "https://numesia.fr",
        "specialite": "Conseil et intégration de solutions digitales, urbanisation SI, consolidation de données",
        "notes": "Agence 10 rue de Dornach, 67100 Strasbourg — source : annuaire Numeum",
    },
    {
        "nom": "SCC Strasbourg",
        "site_web": "https://www.scc.com",
        "specialite": "Intégrateur IT (infrastructure, cloud, services managés)",
        "notes": "Agence 3 Rue de Berne, Parc Européen d'Entreprises, 67300 Schiltigheim — source : annuaire Numeum",
    },
    {
        "nom": "SFEIR (SFEIR-EST)",
        "site_web": "https://www.sfeir.com",
        "specialite": "ESN tech / conseil et développement (cloud, mobile, IA, craftsmanship)",
        "notes": "Agence 1 Avenue de l'Europe, 67300 Schiltigheim (entité SFEIR-EST), SIRET 523 772 861 00010",
    },
    {
        "nom": "Ippon Technologies",
        "site_web": "https://fr.ippon.tech",
        "specialite": "Conseil et ingénierie logicielle (Java, cloud, DevOps, data)",
        "notes": "8e agence du groupe, 15 Rue des Bouchers, 67000 Strasbourg, SIRET 441 716 412 00206",
    },
    {
        "nom": "Neos-SDI",
        "site_web": "https://www.neos-sdi.com",
        "specialite": "Conseil et ingénierie Microsoft (infrastructure, ERP, CRM, décisionnel)",
        "notes": "Présence confirmée à Strasbourg/Entzheim, suite au rachat de l'activité Microsoft Dynamics de RBS",
    },
    {
        "nom": "Onepoint",
        "site_web": "https://www.groupeonepoint.com",
        "specialite": "Conseil en transformation digitale et technologique",
        "notes": "Agence Onepoint Grand Est, 10 Place Gutenberg, 67000 Strasbourg (locaux de la CCI)",
    },
    {
        "nom": "Econocom",
        "site_web": "https://www.econocom.com",
        "specialite": "Transformation digitale, financement et gestion de parc IT, staffing technique",
        "notes": "Établissement secondaire 333 B Avenue de Colmar, 67100 Strasbourg, SIRET 301 364 824 00229",
    },
    {
        "nom": "Alten",
        "site_web": "https://www.alten.fr",
        "specialite": "Ingénierie et IT services (conseil technologique, R&D externalisée)",
        "notes": "Agence Strasbourg parmi les 12 agences ALTEN France — statut réactualisé 2026, à re-vérifier périodiquement",
    },
    {
        "nom": "ITS Group",
        "site_web": "https://www.itsgroup.com",
        "specialite": "Conseil en systèmes informatiques, infrastructure et digitalisation des processus métier",
        "notes": "Agence 20 Place des Halles, 67000 Strasbourg, ouverte le 01/05/2010, SIRET 404 536 922 00150",
    },
    {
        "nom": "Groupe Open",
        "site_web": "https://www.open.global",
        "specialite": "ESN — transformation digitale, industrielle et technologique, infogérance, conseil SI",
        "notes": "Agence 1 avenue de l'Europe, Crystal Park B2, 67300 Schiltigheim, +100 collaborateurs locaux",
    },
    {
        "nom": "Cegedim Business Services",
        "site_web": "https://www.cegedim.fr",
        "specialite": "Conseil en systèmes d'information et outsourcing IT",
        "notes": "Établissement secondaire 35 Avenue de la Paix - Simone Veil, 67000 Strasbourg, SIRET 350 422 622 00315",
    },
    {
        "nom": "Koesio",
        "site_web": "https://koesio.com",
        "specialite": "ESN de proximité — infrastructure IT, cybersécurité, infogérance, logiciels métier, télécoms",
        "notes": "Agence 4 rue de la Durance, 67100 Strasbourg, ~100 collaborateurs Grand Est",
    },
    {
        "nom": "UBICENTREX",
        "site_web": "https://www.ubicentrex.fr",
        "specialite": "Programmation et conseil informatique",
        "notes": "Siège 23 Boulevard de l'Orangerie, 67000 Strasbourg, SIREN 513 535 609",
    },
    {
        "nom": "NEXAGO",
        "site_web": "https://nexago.fr",
        "specialite": "ESN de proximité — infogérance, sécurité, sauvegarde, développement web, support PME",
        "notes": "Siège 5 Allée de l'Europe, 67960 Entzheim (Eurométropole de Strasbourg), SIREN 878 237 403",
    },
    {
        "nom": "Union Technologies Est",
        "site_web": "https://www.kompass.com",
        "specialite": "Conseil en systèmes informatiques, assistance de proximité, intégration",
        "notes": "Siège 19 Rue de la Haye, 67300 Schiltigheim, société créée en 1992, SIREN 385 096 615",
    },
    {
        "nom": "Hadritech",
        "site_web": "https://www.hadritech.com",
        "specialite": "Conseil en systèmes et logiciels informatiques",
        "notes": "Siège 5 Boulevard Gambetta, 67000 Strasbourg (transféré avril 2024), SIREN 489 041 558",
    },
    {
        "nom": "Hydracode",
        "site_web": "",
        "specialite": "Programmation informatique / développement logiciel",
        "notes": "Siège 32 Allée de la Robertsau, 67000 Strasbourg — société récente (2025), à re-vérifier dans le temps",
    },
    {
        "nom": "Hapticmedia",
        "site_web": "https://www.hapticmedia.fr",
        "specialite": "Éditeur logiciel — configurateurs 3D et essayage virtuel pour l'e-commerce",
        "notes": "Siège 15 Rue des Francs Bourgeois, 67000 Strasbourg, 10-19 salariés, SIREN 800 874 794",
    },
    {
        "nom": "Eviden (Atos Group)",
        "site_web": "https://eviden.com",
        "specialite": "Conseil technologique, cybersécurité, systèmes critiques (filiale du groupe Atos)",
        "notes": "Établissement Atos France, Espace Européen de l'Entreprise, 6 Rue de Copenhague, 67000 Strasbourg",
    },
    {
        "nom": "OCI Informatique et Digital (Groupe OCI)",
        "site_web": "https://www.oci.fr",
        "specialite": "SSII / ESN — infrastructure & sécurité IT, solutions métier, digital & web",
        "notes": "Agence historique (40 ans) 2 rue André Marie Ampère, 67450 Mundolsheim, SIREN 502 770 118",
    },
    {
        "nom": "Stork Groupe",
        "site_web": "https://stork-groupe.fr",
        "specialite": "Conseil IT — développement logiciel & intégration, data/IA, cybersécurité",
        "notes": "Siège 35 rue Gruninger, 67400 Illkirch-Graffenstaden (Parc d'Innovation de Strasbourg)",
    },
    {
        "nom": "Heliaq",
        "site_web": "https://heliaq.fr",
        "specialite": "ESN française — IT, cloud, cybersécurité, infogérance, digital workplace",
        "notes": "Agence 4 Rue de l'Industrie, 67450 Mundolsheim",
    },
    {
        "nom": "Reboot Conseil",
        "site_web": "https://reboot-conseil.com",
        "specialite": "Cabinet de conseil IT / ESN — IA, cybersécurité, ingénierie, formation, RH tech",
        "notes": "Siège 14 avenue de la Paix, 67000 Strasbourg, fondée à Strasbourg fin 2020, +100 consultants",
    },
    {
        "nom": "Actinvision",
        "site_web": "https://www.actinvision.com",
        "specialite": "Agence de conseil data, BI & IA",
        "notes": "Siège 5 Quai de Paris, 67000 Strasbourg, fondée à Strasbourg en 2014, SIREN 831 311 667",
    },
    {
        "nom": "IBM (implantation Est)",
        "site_web": "https://www.ibm.com/fr-fr",
        "specialite": "Conseil et services IT (IBM Consulting) — grand compte, présence historique en Alsace",
        "notes": "Établissement 48 Rue Faubourg de Saverne, 67000 Strasbourg — multinationale (pas une ESN pure), inclus pour son activité conseil IT avérée avec adresse locale",
    },
]


def ajouter_esn(entreprises: list[dict]) -> dict:
    """Ajoute des ESN au référentiel. Ignore les doublons (nom normalisé)."""
    init_db()
    today = date.today().isoformat()
    batch = []
    for e in entreprises:
        batch.append({
            "nom":         e["nom"],
            "site_web":    e.get("site_web", ""),
            "specialite":  e.get("specialite", ""),
            "contact":     e.get("contact", ""),
            "notes":       e.get("notes", ""),
            "statut":      "a_contacter",
            "date_ajout":  today,
        })
    return _db_ajouter(batch)


def marquer(esn_id: str, statut: str, canal: str = None) -> bool:
    init_db()
    _db_marquer(esn_id, statut, canal)
    return True


def lister(statut: str = None) -> list[dict]:
    init_db()
    return esn_lister(statut)


def stats() -> dict:
    init_db()
    return esn_stats()


def get(esn_id: str) -> dict | None:
    init_db()
    for e in esn_lister(None):
        if e["id"] == esn_id:
            return e
    return None


def seed() -> dict:
    """Insère le référentiel ESN_STRASBOURG (idempotent, pas de doublons à réimport)."""
    return ajouter_esn(ESN_STRASBOURG)


if __name__ == "__main__":
    resultat = seed()
    print(f"ESN ajoutées : {resultat['ajoutes']}, doublons ignorés : {resultat['doublons']}")

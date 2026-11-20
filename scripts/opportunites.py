#!/usr/bin/env python3
"""
/opportunites — Score et filtre les offres d'emploi extraites d'emails.

Appelé par les slash commands /opportunites et /daily.

Usage depuis Claude :
    python opportunites.py <fichier_offres.json>

Format JSON attendu :
[
  {
    "entreprise": "Acme Corp",
    "poste": "Développeur Full Stack Node.js",
    "localisation": "Strasbourg (67)",
    "contrat": "CDI",
    "stack": ["Node.js", "Angular", "MongoDB"],
    "contact": "Jean Dupont",
    "url": "https://...",
    "description": "texte complet de l'offre...",
    "source": "LinkedIn"
  },
  ...
]

Génère exports/opportunites_YYYY-MM-DD.md.
"""
import json
import sys
from datetime import date
from pathlib import Path

# Ajout du répertoire scripts au path pour import lib_excel
sys.path.insert(0, str(Path(__file__).parent))
from lib_excel import load_candidatures, entreprise_existe_norm, ensure_exports_dir

# ── Profil de Nedjmeddine ────────────────────────────────────────────────────

STACK_FORTE = {
    "node.js", "nodejs", "express", "express.js",
    "c#", ".net", ".net core", "asp.net", "asp.net core",
    "php", "laravel",
    "javascript", "angularjs", "angular",
    "vue.js", "vuejs", "vue",
    "html", "html5", "css", "css3", "tailwind",
    "mongodb", "sql server", "mysql",
    "rest", "rest api", "api rest", "mvc", "microservices",
    "mean", "ionic", "capacitor",
    "docker", "aws", "gcp", "linux", "git",
    "jira", "confluence",
}

STACK_PROCHE = {
    "react", "react.js", "reactjs",
    "typescript", "ts",
    "next.js", "nextjs",
    "nestjs", "nest.js",
    "postgresql", "postgres",
}

LIEUX_STRASBOURG = {
    "strasbourg", "schiltigheim", "illkirch", "illkirch-graffenstaden",
    "bas-rhin", "67", "alsace", "eurométropole", "eurométropole de strasbourg",
}
LIEUX_GRAND_EST = {
    "grand est", "moselle", "metz", "nancy", "mulhouse", "colmar",
    "haut-rhin", "68", "meurthe", "vosges", "ardennes",
}
LIEUX_REMOTE = {
    "full remote", "télétravail complet", "100% remote", "remote france",
    "full remote france", "télétravail total",
}
LIEUX_GRANDES_VILLES = {
    "paris", "lyon", "bordeaux", "toulouse", "nantes", "lille",
    "marseille", "montpellier", "rennes", "nice",
}

# ── Filtres d'exclusion ───────────────────────────────────────────────────────

# Mots dans le titre → offre exclue (senior, lead, alternance, stage)
_TITRES_EXCLUS = [
    "senior", "sénior", "sr.",
    "lead dev", "lead développeur", "tech lead", "team lead",
    "principal", "confirmé", "expérimenté",
    "architecte logiciel", "architecte solution", "head of", "staff engineer",
    "alternance", "alternant", "apprenti", "apprentissage", "contrat pro",
    "stage ", "stagiaire",
]

# Valeurs du champ contrat → offre exclue
_CONTRATS_EXCLUS = {
    "alternance", "apprentissage", "stage", "contrat pro",
    "contrat d'apprentissage",
}


def est_exclu(offre: dict) -> tuple[bool, str]:
    """Retourne (True, raison) si l'offre doit être exclue du pipeline."""
    titre   = (offre.get("poste") or "").lower()
    contrat = (offre.get("contrat") or "").lower()

    for mot in _CONTRATS_EXCLUS:
        if mot in contrat:
            return True, f"contrat exclu ({mot})"

    for mot in _TITRES_EXCLUS:
        if mot in titre:
            return True, f"titre exclu ({mot})"

    return False, ""


def score_stack(stack_offre: list[str]) -> int:
    """0-50 pts : 5 pts par tech forte matchée, 2 pts par tech proche matchée."""
    pts = 0
    for tech in stack_offre:
        t = tech.strip().lower()
        if t in STACK_FORTE:
            pts += 5
        elif t in STACK_PROCHE:
            pts += 2
    return min(pts, 50)


def score_localisation(localisation: str) -> int:
    """0-30 pts selon localisation."""
    loc = localisation.strip().lower()

    for mot in LIEUX_REMOTE:
        if mot in loc:
            return 25

    for mot in LIEUX_STRASBOURG:
        if mot in loc:
            return 30

    for mot in LIEUX_GRAND_EST:
        if mot in loc:
            return 20

    for mot in LIEUX_GRANDES_VILLES:
        if mot in loc:
            return 20

    return 5


def score_contrat(contrat: str) -> int:
    """0-10 pts selon type de contrat."""
    c = contrat.strip().lower()
    if "cdi" in c:
        return 10
    if any(x in c for x in ("cdd", "freelance", "portage")):
        return 5
    return 0


def score_qualite(contact: str, description: str) -> int:
    """0-10 pts : +5 si contact nominatif, +5 si description détaillée (>500 chars)."""
    pts = 0
    if contact and contact.strip():
        pts += 5
    if description and len(description.strip()) > 500:
        pts += 5
    return pts


def scorer_offre(offre: dict) -> dict:
    """Calcule le score total d'une offre et retourne l'offre enrichie."""
    # `or` plutôt que valeur par défaut de .get() : le JSON du /daily peut contenir null explicitement
    s_stack = score_stack(offre.get("stack") or [])
    s_loc = score_localisation(offre.get("localisation") or "")
    s_contrat = score_contrat(offre.get("contrat") or "")
    s_qualite = score_qualite(offre.get("contact") or "", offre.get("description") or "")

    total = s_stack + s_loc + s_contrat + s_qualite

    return {
        **offre,
        "score": total,
        "detail_score": {
            "stack": s_stack,
            "localisation": s_loc,
            "contrat": s_contrat,
            "qualite": s_qualite,
        },
    }


def _ville_principale(loc: str) -> str:
    """'Strasbourg (67)' → 'strasbourg'. '' → ''."""
    import unicodedata
    if not loc:
        return ""
    v = loc.split("(")[0].split(",")[0].strip().lower()
    return unicodedata.normalize("NFKD", v).encode("ascii", "ignore").decode()


# Une entreprise déjà contactée n'est cachée que si le contact est récent
# ou si un process est en cours. Sinon l'offre reste visible avec un badge :
# une boîte contactée il y a 3 mois peut avoir ouvert un nouveau poste.
DELAI_RECONTACT_JOURS = 30
STATUTS_PROCESS_EN_COURS = {"En cours", "Entretien prévu", "Offre"}


def dernier_contact_entreprise(nom_entreprise: str, candidatures=None) -> dict | None:
    """Candidature la plus récente pour cette entreprise (toutes lignes confondues), ou None."""
    from lib_excel import normaliser_entreprise
    if candidatures is None:
        candidatures = load_candidatures()
    nom_norm = normaliser_entreprise(nom_entreprise or "")
    lignes = [c for c in candidatures if normaliser_entreprise(c.get("entreprise") or "") == nom_norm]
    if not lignes:
        return None

    def _date_ref(c):
        return c.get("date_contact") or c.get("date_cand") or date.min

    return max(lignes, key=_date_ref)


def info_deja_contacte(nom_entreprise: str, candidatures=None) -> dict | None:
    """{date, statut, jours, cacher} si l'entreprise est dans le suivi, sinon None."""
    c = dernier_contact_entreprise(nom_entreprise, candidatures)
    if not c:
        return None
    d = c.get("date_contact") or c.get("date_cand")
    jours = (date.today() - d).days if d else None
    statut = c.get("statut") or ""
    cacher = statut in STATUTS_PROCESS_EN_COURS or (jours is not None and jours < DELAI_RECONTACT_JOURS)
    return {
        "date": d.strftime("%d/%m/%Y") if d else "",
        "statut": statut,
        "jours": jours,
        "cacher": cacher,
    }


def filtrer_doublons(offres: list[dict], candidatures=None, ignorer_doublons_entreprise: bool = False) -> tuple[list[dict], list[str]]:
    """Cache seulement les offres d'entreprises contactées il y a moins de
    DELAI_RECONTACT_JOURS jours ou avec un process en cours. Les autres restent,
    avec un champ `deja_contacte` ("12/08/2026 — Pas de réponse").

    ignorer_doublons_entreprise=True : ne cache rien (le badge est quand même ajouté).
    """
    if candidatures is None:
        candidatures = load_candidatures()

    nouvelles = []
    ignores = []
    for o in offres:
        info = info_deja_contacte(o.get("entreprise"), candidatures)
        if info:
            if info["cacher"] and not ignorer_doublons_entreprise:
                raison = (f"process en cours ({info['statut']})"
                          if info["statut"] in STATUTS_PROCESS_EN_COURS
                          else f"contactée il y a {info['jours']} j")
                ignores.append(f"{o['entreprise']} — {raison}")
                continue
            o = {**o, "deja_contacte": f"{info['date']} — {info['statut']}"}
        nouvelles.append(o)
    return nouvelles, ignores


def traiter_offres(offres_brutes: list[dict], max_top: int = 30, ignorer_doublons_entreprise: bool = False) -> dict:
    """Pipeline : exclusion senior/alternance → anti-doublon → scoring → filtre → top N."""
    # 1. Exclure senior, alternance, stage avant tout scoring
    retenues = []
    exclues_profil: list[str] = []
    for o in offres_brutes:
        exclu, raison = est_exclu(o)
        if exclu:
            exclues_profil.append(f"{o['entreprise']} — {o.get('poste', '?')} ({raison})")
        else:
            retenues.append(o)

    candidatures = load_candidatures()
    nouvelles, ignores = filtrer_doublons(retenues, candidatures, ignorer_doublons_entreprise)

    scorees = [scorer_offre(o) for o in nouvelles]
    filtrees = [o for o in scorees if o["score"] >= 40]
    filtrees.sort(key=lambda o: o["score"], reverse=True)
    top = filtrees[:max_top]
    exclues_score = [o for o in scorees if o["score"] < 40]

    return {
        "top": top,
        "exclues": exclues_score,
        "exclues_profil": exclues_profil,
        "ignores": ignores,
        "total_brut": len(offres_brutes),
    }


def formater_checklist(offre: dict) -> list[str]:
    """Génère la checklist 'À faire avant de postuler'."""
    return [
        "Recherche LinkedIn : trouver CTO / Lead Dev / Manager technique",
        "Lire 3 articles sur l'entreprise (site, Glassdoor, presse)",
        "Identifier 1-2 projets/clients récents pour personnaliser la candidature",
    ]


def afficher_resultats(resultats: dict):
    """Affiche les opportunités dans le terminal."""
    top = resultats["top"]
    ignores = resultats["ignores"]
    exclues = resultats["exclues"]

    print("=" * 70)
    print("  OPPORTUNITÉS QUALIFIÉES")
    print("=" * 70)
    print()

    if not top:
        print("❌ Aucune offre ne passe le seuil de 40/100.")
        print(f"   {len(exclues)} offre(s) en dessous du seuil.")
    else:
        for o in top:
            d = o["detail_score"]
            stack_matches = [t for t in o.get("stack", []) if t.strip().lower() in STACK_FORTE]
            stack_proche = [t for t in o.get("stack", []) if t.strip().lower() in STACK_PROCHE]
            stack_str = ", ".join(stack_matches)
            if stack_proche:
                stack_str += f" + {', '.join(stack_proche)} (proches)"

            print(f"🎯 [Score: {o['score']}/100] {o['entreprise']} — {o.get('poste', '(poste non précisé)')}")
            print(f"   Localisation : {o.get('localisation', '?')} | {o.get('contrat', '?')} | Source : {o.get('source', '?')}")
            if stack_str:
                print(f"   Stack match  : {stack_str}")
            if o.get("contact"):
                print(f"   Contact      : {o['contact']}")
            if o.get("url"):
                print(f"   Lien         : {o['url']}")
            print()
            print("   ⚠️  À FAIRE AVANT DE POSTULER :")
            for item in formater_checklist(o):
                print(f"   - [ ] {item}")
            print()
            print(f"   Détail score — Stack: {d['stack']}/50 | Localisation: {d['localisation']}/30 | Contrat: {d['contrat']}/10 | Qualité: {d['qualite']}/10")
            print()
            print("─" * 70)
            print()

    if ignores:
        print(f"⏭️  {len(ignores)} offre(s) ignorée(s) (déjà dans l'Excel) :")
        for nom in ignores:
            print(f"   • {nom}")
        print()


def exporter_markdown(resultats: dict, chemin: Path = None) -> Path:
    """Génère exports/opportunites_YYYY-MM-DD.md."""
    exports = ensure_exports_dir()
    if chemin is None:
        chemin = exports / f"opportunites_{date.today().isoformat()}.md"

    top = resultats["top"]
    ignores = resultats["ignores"]
    exclues = resultats["exclues"]

    lines = [f"# Opportunités qualifiées — {date.today().strftime('%d/%m/%Y')}\n"]
    lines.append(f"**{len(top)} offre(s) retenue(s)** sur {resultats['total_brut']} analysée(s).\n")

    if not top:
        lines.append("❌ Aucune offre ne passe le seuil de 40/100.\n")
    else:
        for o in top:
            d = o["detail_score"]
            stack_matches = [t for t in o.get("stack", []) if t.strip().lower() in STACK_FORTE]
            stack_proche = [t for t in o.get("stack", []) if t.strip().lower() in STACK_PROCHE]
            stack_str = ", ".join(stack_matches)
            if stack_proche:
                stack_str += f" + {', '.join(stack_proche)} (proches)"

            lines.append(f"## 🎯 [{o['score']}/100] {o['entreprise']} — {o.get('poste', '(poste non précisé)')}\n")
            lines.append(f"| Champ | Valeur |")
            lines.append(f"|---|---|")
            lines.append(f"| Localisation | {o.get('localisation', '?')} |")
            lines.append(f"| Contrat | {o.get('contrat', '?')} |")
            lines.append(f"| Source | {o.get('source', '?')} |")
            if o.get("contact"):
                lines.append(f"| Contact | {o['contact']} |")
            if o.get("url"):
                lines.append(f"| Lien | {o['url']} |")
            lines.append(f"| Score stack | {d['stack']}/50 |")
            lines.append(f"| Score localisation | {d['localisation']}/30 |")
            lines.append(f"| Score contrat | {d['contrat']}/10 |")
            lines.append(f"| Score qualité | {d['qualite']}/10 |\n")

            if stack_str:
                lines.append(f"**Stack match :** {stack_str}\n")

            lines.append("**⚠️ À faire avant de postuler :**\n")
            for item in formater_checklist(o):
                lines.append(f"- [ ] {item}")
            lines.append("\n---\n")

    if ignores:
        lines.append(f"\n## ⏭️ Offres ignorées (déjà dans l'Excel)\n")
        for nom in ignores:
            lines.append(f"- {nom}")
        lines.append("")

    if exclues:
        lines.append(f"\n## ❌ Offres sous le seuil (<40/100)\n")
        for o in exclues:
            lines.append(f"- [{o['score']}/100] {o['entreprise']} — {o.get('poste', '?')}")
        lines.append("")

    chemin.write_text("\n".join(lines), encoding="utf-8")
    return chemin


def main():
    if len(sys.argv) < 2:
        print("Usage : python opportunites.py <fichier_offres.json>", file=sys.stderr)
        sys.exit(1)

    fichier = Path(sys.argv[1])
    if not fichier.exists():
        print(f"❌ Fichier introuvable : {fichier}", file=sys.stderr)
        sys.exit(1)

    with open(fichier, encoding="utf-8") as f:
        offres_brutes = json.load(f)

    resultats = traiter_offres(offres_brutes)
    afficher_resultats(resultats)

    chemin = exporter_markdown(resultats)
    print(f"📄 Export : {chemin}")


if __name__ == "__main__":
    main()

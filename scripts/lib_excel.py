"""
Bibliothèque partagée pour le suivi CDI.
Lecture/écriture → SQLite (lib_db).
Export Excel → openpyxl (fonctions _excel_* gardées pour backup).
"""
import os
import re
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from datetime import datetime, date
from pathlib import Path
import sys

# Path absolu du fichier Excel (backup / import initial)
EXCEL_PATH = Path(__file__).parent.parent / "suivi.xlsx"

# ============ Colonnes de la feuille Candidatures ============
COL_ID = 1
COL_ENTREPRISE = 2
COL_POSTE = 3
COL_LOCALISATION = 4
COL_TYPE_POSTE = 5
COL_DATE_CAND = 6
COL_STATUT = 7
COL_DATE_CONTACT = 8
COL_PROCHAINE_ACTION = 9
COL_DATE_PROCHAINE = 10
COL_CONTACT = 11
COL_SOURCE = 12
COL_STACK = 13
COL_PRIORITE = 14
COL_COMMENTAIRES = 15

STATUTS_ACTIFS = {"1er contact", "En cours", "Entretien prévu", "Offre"}
STATUTS_ARCHIVES = {"Refus", "Pas de réponse", "Pas d'opportunités", "Abandonnée"}

COLOR_MAP = {
    "1er contact": "DDEBF7",
    "En cours": "FFF2CC",
    "Refus": "FCE4D6",
    "Pas de réponse": "F2F2F2",
    "Pas d'opportunités": "F2F2F2",
    "Offre": "C6EFCE",
    "Entretien prévu": "D9E1F2",
    "Abandonnée": "E7E6E6",
}


def parse_date(value):
    """Convertit une valeur cellule en date Python, ou None."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(value.strip(), "%d/%m/%Y").date()
            except ValueError:
                return None
    return None


def days_since(d):
    if d is None:
        return None
    return (date.today() - d).days


# ── Lecture SQLite ────────────────────────────────────────────────────────────

def load_candidatures() -> list[dict]:
    """Charge toutes les candidatures depuis SQLite."""
    from lib_db import init_db, load_candidatures as db_load
    init_db()
    rows = db_load()
    result = []
    for r in rows:
        r["date_cand"]      = parse_date(r.get("date_candidature"))
        r["date_contact"]   = parse_date(r.get("date_contact"))
        r["date_prochaine"] = parse_date(r.get("date_prochaine"))
        r["row"] = r.get("id")  # compatibilité avec les scripts CLI
        result.append(r)
    return result


def load_entretiens() -> list[dict]:
    """Charge tous les entretiens depuis SQLite."""
    from lib_db import init_db, load_entretiens as db_load
    init_db()
    rows = db_load()
    result = []
    for r in rows:
        r["date"] = parse_date(r.get("date_entretien"))
        r["row"]  = r.get("id")
        result.append(r)
    return result


# ── Écriture SQLite ───────────────────────────────────────────────────────────

def update_programmatic(entreprise_or_id, statut=None, commentaire=None,
                        contact=None, date_contact=None):
    """Met à jour une candidature dans SQLite."""
    from lib_db import init_db, load_candidatures as db_load, update_candidature
    init_db()
    cands = db_load()

    cand = None
    try:
        id_num = int(entreprise_or_id)
        cand = next((c for c in cands if c["id"] == id_num), None)
    except (ValueError, TypeError):
        pass

    if cand is None:
        cand = entreprise_existe_norm(str(entreprise_or_id), [
            {**c, "date_cand": None, "date_contact": None, "date_prochaine": None}
            for c in cands
        ])

    if cand is None:
        return False, f"Candidature introuvable : '{entreprise_or_id}'"

    nouveau_statut  = statut if statut else cand["statut"]
    contact_final   = contact if contact else cand.get("contact", "")
    date_c          = (date_contact or date.today()).isoformat()

    commentaires_final = cand.get("commentaires", "")
    if commentaire:
        date_tag = (date_contact or date.today()).strftime("%d/%m/%Y")
        nouvelle_ligne = f"[{date_tag}] {commentaire}"
        commentaires_final = (
            f"{commentaires_final}\n{nouvelle_ligne}" if commentaires_final else nouvelle_ligne
        )

    priorite_finale = calculer_priorite(contact_final, nouveau_statut)

    fields = {
        "statut":       nouveau_statut,
        "date_contact": date_c,
        "commentaires": commentaires_final,
        "priorite":     priorite_finale,
    }
    if contact:
        fields["contact"] = contact_final

    update_candidature(cand["id"], **fields)
    return True, f"{cand['entreprise']} : {cand['statut']} → {nouveau_statut}"


def ajouter_programmatic(entreprise, poste="", localisation="", type_poste="Hybride",
                         contact="", source="LinkedIn", stack="", commentaires=""):
    """Ajoute une nouvelle candidature dans SQLite."""
    from lib_db import init_db, load_candidatures as db_load, ajouter_candidature as db_add
    init_db()
    cands = db_load()
    existing = entreprise_existe_norm(entreprise, [
        {**c, "date_cand": None, "date_contact": None, "date_prochaine": None}
        for c in cands
    ])
    if existing:
        return False, f"Doublon : '{existing['entreprise']}' déjà dans le suivi (statut: {existing['statut']})", None

    next_id = max((c["id"] for c in cands if isinstance(c.get("id"), int)), default=0) + 1
    today   = date.today().isoformat()
    statut  = "1er contact"
    priorite = calculer_priorite(contact, statut)

    new_id = db_add(
        id=next_id,
        entreprise=entreprise,
        poste=poste,
        localisation=localisation,
        type_poste=type_poste,
        date_candidature=today,
        statut=statut,
        date_contact=today,
        prochaine_action="Relance si pas de réponse ≥7j",
        contact=contact,
        source=source,
        stack=stack,
        priorite=priorite,
        commentaires=commentaires,
    )
    return True, f"#{new_id} ajouté : {entreprise} | {statut} | {priorite}", new_id


# ── Helpers partagés ─────────────────────────────────────────────────────────

def entreprise_existe(nom_entreprise):
    nom_norm = nom_entreprise.strip().lower()
    for c in load_candidatures():
        if c["entreprise"].strip().lower() == nom_norm:
            return c
    return None


def derniere_interaction(cand, entretiens_all):
    dates = [cand["date_contact"]]
    for e in entretiens_all:
        if e["entreprise"].strip().lower() == cand["entreprise"].strip().lower():
            dates.append(e["date"])
    dates = [d for d in dates if d is not None]
    return max(dates) if dates else cand["date_cand"]


def a_entretien_passe(cand, entretiens_all):
    nom = cand["entreprise"].strip().lower()
    return any(e["entreprise"].strip().lower() == nom for e in entretiens_all)


def calculer_priorite(contact, statut):
    if statut in STATUTS_ARCHIVES:
        return "Archivée"
    if statut in ("Offre", "Entretien prévu"):
        return "Haute"
    if statut == "En cours" and contact:
        return "Haute"
    if statut == "En cours":
        return "Moyenne"
    if statut == "1er contact" and contact:
        return "Moyenne"
    if statut == "1er contact":
        return "Basse"
    return "Basse"


def format_date_fr(d):
    if d is None:
        return "?"
    return d.strftime("%d/%m/%Y")


def normaliser_entreprise(nom):
    nom = nom.strip().lower()
    nom = re.sub(r"[\s\-_']+", "", nom)
    return nom


def entreprise_existe_norm(nom_entreprise, candidatures=None):
    if candidatures is None:
        candidatures = load_candidatures()
    nom_norm = normaliser_entreprise(nom_entreprise)
    for c in candidatures:
        if normaliser_entreprise(c["entreprise"]) == nom_norm:
            return c
    return None


def ensure_exports_dir():
    exports = Path(__file__).parent.parent / "exports"
    exports.mkdir(exist_ok=True)
    return exports


def charger_dotenv():
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


# ── Export Excel (backup) ─────────────────────────────────────────────────────

def appliquer_style_ligne(ws, row_idx, statut, nb_cols=15):
    color = COLOR_MAP.get(statut, "FFFFFF")
    for col in range(1, nb_cols + 1):
        cell = ws.cell(row=row_idx, column=col)
        if color != "FFFFFF":
            cell.fill = PatternFill('solid', start_color=color)
        cell.font = Font(name='Arial', size=10)
        cell.alignment = Alignment(vertical='top', wrap_text=True)
        cell.border = Border(
            left=Side(style='thin', color='CCCCCC'),
            right=Side(style='thin', color='CCCCCC'),
            top=Side(style='thin', color='CCCCCC'),
            bottom=Side(style='thin', color='CCCCCC')
        )


def _excel_export_candidatures():
    """Exporte les candidatures SQLite vers Excel (backup)."""
    from lib_db import load_candidatures as db_load
    cands = db_load()

    if not EXCEL_PATH.exists():
        return False, "Excel introuvable — pas d'export"

    wb = load_workbook(EXCEL_PATH)
    ws = wb["Candidatures"]

    # Vider les données (garder entête ligne 1)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.value = None

    for idx, c in enumerate(cands, start=2):
        row_data = [
            c["id"], c["entreprise"], c.get("poste", ""),
            c.get("localisation", ""), c.get("type_poste", ""),
            c.get("date_candidature", ""), c.get("statut", ""),
            c.get("date_contact", ""), c.get("prochaine_action", ""),
            c.get("date_prochaine", ""), c.get("contact", ""),
            c.get("source", ""), c.get("stack", ""),
            c.get("priorite", ""), c.get("commentaires", ""),
        ]
        for col_idx, value in enumerate(row_data, 1):
            ws.cell(row=idx, column=col_idx, value=value)
        appliquer_style_ligne(ws, idx, c.get("statut", ""))

    wb.save(EXCEL_PATH)
    return True, f"{len(cands)} candidatures exportées vers Excel"

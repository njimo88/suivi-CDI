"""
Bibliothèque partagée pour manipuler suivi.xlsx.
Toutes les fonctions supposent que EXCEL_PATH pointe vers le fichier.
"""
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from datetime import datetime, date
from pathlib import Path
import sys

# Path absolu du fichier Excel (à adapter si tu déplaces le projet)
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
    "1er contact": "DDEBF7",  # bleu clair — prospection en attente de réponse
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
    """Nombre de jours écoulés depuis une date donnée. Retourne None si date invalide."""
    if d is None:
        return None
    return (date.today() - d).days


def load_candidatures():
    """Charge toutes les candidatures depuis l'Excel comme liste de dicts."""
    if not EXCEL_PATH.exists():
        print(f"❌ Fichier introuvable : {EXCEL_PATH}", file=sys.stderr)
        sys.exit(1)

    wb = load_workbook(EXCEL_PATH)
    ws = wb["Candidatures"]
    candidatures = []

    for row_idx in range(2, ws.max_row + 1):
        entreprise = ws.cell(row=row_idx, column=COL_ENTREPRISE).value
        if not entreprise:
            continue

        cand = {
            "row": row_idx,
            "id": ws.cell(row=row_idx, column=COL_ID).value,
            "entreprise": entreprise,
            "poste": ws.cell(row=row_idx, column=COL_POSTE).value or "",
            "localisation": ws.cell(row=row_idx, column=COL_LOCALISATION).value or "",
            "type_poste": ws.cell(row=row_idx, column=COL_TYPE_POSTE).value or "",
            "date_cand": parse_date(ws.cell(row=row_idx, column=COL_DATE_CAND).value),
            "statut": ws.cell(row=row_idx, column=COL_STATUT).value or "",
            "date_contact": parse_date(ws.cell(row=row_idx, column=COL_DATE_CONTACT).value),
            "prochaine_action": ws.cell(row=row_idx, column=COL_PROCHAINE_ACTION).value or "",
            "date_prochaine": parse_date(ws.cell(row=row_idx, column=COL_DATE_PROCHAINE).value),
            "contact": ws.cell(row=row_idx, column=COL_CONTACT).value or "",
            "source": ws.cell(row=row_idx, column=COL_SOURCE).value or "",
            "stack": ws.cell(row=row_idx, column=COL_STACK).value or "",
            "priorite": ws.cell(row=row_idx, column=COL_PRIORITE).value or "",
            "commentaires": ws.cell(row=row_idx, column=COL_COMMENTAIRES).value or "",
        }
        candidatures.append(cand)

    return candidatures


def load_entretiens():
    """Charge tous les entretiens."""
    wb = load_workbook(EXCEL_PATH)
    ws = wb["Entretiens"]
    entretiens = []
    for row_idx in range(2, ws.max_row + 1):
        entreprise = ws.cell(row=row_idx, column=2).value
        if not entreprise:
            continue
        entretiens.append({
            "row": row_idx,
            "entreprise": entreprise,
            "poste": ws.cell(row=row_idx, column=3).value or "",
            "date": parse_date(ws.cell(row=row_idx, column=4).value),
            "type": ws.cell(row=row_idx, column=5).value or "",
            "interlocuteurs": ws.cell(row=row_idx, column=6).value or "",
            "format": ws.cell(row=row_idx, column=7).value or "",
            "questions": ws.cell(row=row_idx, column=8).value or "",
            "resultat": ws.cell(row=row_idx, column=9).value or "",
        })
    return entretiens


def entreprise_existe(nom_entreprise):
    """Vérifie si une entreprise existe déjà dans le suivi (normalisation basique)."""
    nom_norm = nom_entreprise.strip().lower()
    for c in load_candidatures():
        if c["entreprise"].strip().lower() == nom_norm:
            return c
    return None


def derniere_interaction(cand, entretiens_all):
    """Retourne la date de la dernière interaction (entretien ou contact)."""
    dates = [cand["date_contact"]]
    for e in entretiens_all:
        if e["entreprise"].strip().lower() == cand["entreprise"].strip().lower():
            dates.append(e["date"])
    dates = [d for d in dates if d is not None]
    return max(dates) if dates else cand["date_cand"]


def a_entretien_passe(cand, entretiens_all):
    """True si au moins un entretien passé existe pour cette entreprise."""
    nom = cand["entreprise"].strip().lower()
    return any(e["entreprise"].strip().lower() == nom for e in entretiens_all)


def calculer_priorite(contact, statut):
    """Calcule la priorité auto selon règles métier."""
    if statut in STATUTS_ARCHIVES:
        return "Archivée"
    if statut == "Offre":
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


def appliquer_style_ligne(ws, row_idx, statut, nb_cols=15):
    """Applique la coloration selon statut."""
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


def format_date_fr(d):
    """Formate une date en FR (DD/MM/YYYY)."""
    if d is None:
        return "?"
    return d.strftime("%d/%m/%Y")


def normaliser_entreprise(nom):
    """Normalise un nom d'entreprise pour la comparaison.

    Supprime espaces, tirets, apostrophes et met en minuscules.
    Permet de matcher 'Plus que Pro' == 'PlusQuePro' == 'Plus Que Pro'.
    """
    import re
    nom = nom.strip().lower()
    nom = re.sub(r"[\s\-_']+", "", nom)
    return nom


def entreprise_existe_norm(nom_entreprise, candidatures=None):
    """Vérifie si une entreprise existe déjà (normalisation étendue). Retourne le dict ou None."""
    if candidatures is None:
        candidatures = load_candidatures()
    nom_norm = normaliser_entreprise(nom_entreprise)
    for c in candidatures:
        if normaliser_entreprise(c["entreprise"]) == nom_norm:
            return c
    return None


def update_programmatic(entreprise_or_id, statut=None, commentaire=None,
                        contact=None, date_contact=None):
    """Met à jour une candidature sans interaction utilisateur.

    Retourne (True, message) si succès, (False, message) si erreur.
    """
    cands = load_candidatures()

    # Recherche par ID ou nom
    cand = None
    try:
        id_num = int(entreprise_or_id)
        cand = next((c for c in cands if c["id"] == id_num), None)
    except (ValueError, TypeError):
        pass

    if cand is None:
        cand = entreprise_existe_norm(str(entreprise_or_id), cands)

    if cand is None:
        return False, f"Candidature introuvable : '{entreprise_or_id}'"

    wb = load_workbook(EXCEL_PATH)
    ws = wb["Candidatures"]
    row = cand["row"]

    nouveau_statut = statut if statut else cand["statut"]
    contact_final = contact if contact else cand["contact"]

    # Commentaire avec date
    commentaires_final = cand["commentaires"]
    if commentaire:
        date_tag = (date_contact or date.today()).strftime("%d/%m/%Y")
        nouvelle_ligne = f"[{date_tag}] {commentaire}"
        commentaires_final = (
            f"{commentaires_final}\n{nouvelle_ligne}" if commentaires_final else nouvelle_ligne
        )

    priorite_finale = calculer_priorite(contact_final, nouveau_statut)
    date_contact_finale = date_contact or date.today()

    ws.cell(row=row, column=COL_STATUT, value=nouveau_statut)
    ws.cell(row=row, column=COL_DATE_CONTACT, value=date_contact_finale.isoformat())
    ws.cell(row=row, column=COL_COMMENTAIRES, value=commentaires_final)
    ws.cell(row=row, column=COL_PRIORITE, value=priorite_finale)
    if contact:
        ws.cell(row=row, column=COL_CONTACT, value=contact_final)

    appliquer_style_ligne(ws, row, nouveau_statut)
    wb.save(EXCEL_PATH)

    msg = f"{cand['entreprise']} : {cand['statut']} → {nouveau_statut}"
    return True, msg


def ajouter_programmatic(entreprise, poste="", localisation="", type_poste="Hybride",
                         contact="", source="LinkedIn", stack="", commentaires=""):
    """Ajoute une nouvelle candidature sans interaction utilisateur.

    Retourne (True, message, id) si succès, (False, message, None) si doublon ou erreur.
    """
    cands = load_candidatures()
    existant = entreprise_existe_norm(entreprise, cands)
    if existant:
        return False, f"Doublon : '{existant['entreprise']}' déjà dans le suivi (statut: {existant['statut']})", None

    wb = load_workbook(EXCEL_PATH)
    ws = wb["Candidatures"]

    next_row = ws.max_row + 1
    next_id = max((c["id"] for c in cands if isinstance(c["id"], int)), default=0) + 1
    today = date.today().isoformat()
    statut = "1er contact"
    priorite = calculer_priorite(contact, statut)

    row_data = [
        next_id, entreprise, poste, localisation, type_poste,
        today, statut, today, "Relance si pas de réponse ≥7j", "",
        contact, source, stack, priorite, commentaires
    ]
    for col_idx, value in enumerate(row_data, 1):
        ws.cell(row=next_row, column=col_idx, value=value)

    appliquer_style_ligne(ws, next_row, statut)
    wb.save(EXCEL_PATH)
    return True, f"#{next_id} ajouté : {entreprise} | {statut} | {priorite}", next_id


def ensure_exports_dir():
    """Crée le dossier exports/ à la racine du projet si absent."""
    exports = Path(__file__).parent.parent / "exports"
    exports.mkdir(exist_ok=True)
    return exports

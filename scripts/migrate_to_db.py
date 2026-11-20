#!/usr/bin/env python3
"""
Migration one-shot : Excel + JSON stores → SQLite (suivi_cdi.db).
Lance avec : python scripts/migrate_to_db.py
Peut être relancé sans danger (INSERT OR IGNORE / INSERT OR REPLACE).
"""
import json
import sys
from datetime import datetime, date
from pathlib import Path
from openpyxl import load_workbook

sys.path.insert(0, str(Path(__file__).parent))
from lib_db import init_db, get_db, DB_PATH
from lib_excel import normaliser_entreprise

ROOT       = Path(__file__).parent.parent
EXCEL_PATH = ROOT / "suivi.xlsx"


def _parse_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                pass
    return None


def _excel_load_candidatures() -> list[dict]:
    if not EXCEL_PATH.exists():
        return []
    wb = load_workbook(EXCEL_PATH)
    ws = wb["Candidatures"]
    rows = []
    for r in range(2, ws.max_row + 1):
        entreprise = ws.cell(row=r, column=2).value
        if not entreprise:
            continue
        rows.append({
            "id":              ws.cell(row=r, column=1).value,
            "entreprise":      entreprise,
            "poste":           ws.cell(row=r, column=3).value or "",
            "localisation":    ws.cell(row=r, column=4).value or "",
            "type_poste":      ws.cell(row=r, column=5).value or "",
            "date_cand":       _parse_date(ws.cell(row=r, column=6).value),
            "statut":          ws.cell(row=r, column=7).value or "1er contact",
            "date_contact":    _parse_date(ws.cell(row=r, column=8).value),
            "prochaine_action":ws.cell(row=r, column=9).value or "",
            "date_prochaine":  _parse_date(ws.cell(row=r, column=10).value),
            "contact":         ws.cell(row=r, column=11).value or "",
            "source":          ws.cell(row=r, column=12).value or "",
            "stack":           ws.cell(row=r, column=13).value or "",
            "priorite":        ws.cell(row=r, column=14).value or "",
            "commentaires":    ws.cell(row=r, column=15).value or "",
        })
    return rows


def _excel_load_entretiens() -> list[dict]:
    if not EXCEL_PATH.exists():
        return []
    wb = load_workbook(EXCEL_PATH)
    ws = wb["Entretiens"]
    rows = []
    for r in range(2, ws.max_row + 1):
        entreprise = ws.cell(row=r, column=2).value
        if not entreprise:
            continue
        rows.append({
            "entreprise":    entreprise,
            "poste":         ws.cell(row=r, column=3).value or "",
            "date":          _parse_date(ws.cell(row=r, column=4).value),
            "type":          ws.cell(row=r, column=5).value or "",
            "interlocuteurs":ws.cell(row=r, column=6).value or "",
            "format":        ws.cell(row=r, column=7).value or "",
            "questions":     ws.cell(row=r, column=8).value or "",
            "resultat":      ws.cell(row=r, column=9).value or "",
        })
    return rows

OFFRES_JSON   = ROOT / "exports" / "offres_a_postuler.json"
LINKEDIN_JSON = ROOT / "exports" / "messages_linkedin.json"


def migrer_candidatures(conn) -> int:
    rows = _excel_load_candidatures()
    n = 0
    for c in rows:
        date_cand    = c["date_cand"].isoformat()    if c.get("date_cand")    else None
        date_contact = c["date_contact"].isoformat() if c.get("date_contact") else None
        date_proch   = c["date_prochaine"].isoformat() if c.get("date_prochaine") else None
        conn.execute(
            """INSERT OR REPLACE INTO candidatures
               (id, entreprise, poste, localisation, type_poste, date_candidature,
                statut, date_contact, prochaine_action, date_prochaine,
                contact, source, stack, priorite, commentaires)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                c["id"], c["entreprise"], c.get("poste", ""),
                c.get("localisation", ""), c.get("type_poste", ""),
                date_cand, c.get("statut", "1er contact"), date_contact,
                c.get("prochaine_action", ""), date_proch,
                c.get("contact", ""), c.get("source", ""),
                c.get("stack", ""), c.get("priorite", ""),
                c.get("commentaires", ""),
            ),
        )
        n += 1
    return n


def migrer_entretiens(conn, candidatures: list[dict]) -> int:
    rows = _excel_load_entretiens()
    # Index entreprise → candidature_id
    idx = {}
    for c in candidatures:
        idx[normaliser_entreprise(c["entreprise"])] = c["id"]

    n = 0
    for e in rows:
        cand_id = idx.get(normaliser_entreprise(e["entreprise"]))
        date_ent = e["date"].isoformat() if e.get("date") else None
        conn.execute(
            """INSERT INTO entretiens
               (candidature_id, entreprise, poste, date_entretien,
                type, interlocuteurs, format, questions, resultat)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                cand_id, e["entreprise"], e.get("poste", ""),
                date_ent, e.get("type", ""), e.get("interlocuteurs", ""),
                e.get("format", ""), e.get("questions", ""),
                e.get("resultat", ""),
            ),
        )
        n += 1
    return n


def migrer_offres(conn) -> tuple[int, int]:
    if not OFFRES_JSON.exists():
        return 0, 0
    offres = json.loads(OFFRES_JSON.read_text(encoding="utf-8"))
    ajoutees = 0
    doublons = 0
    for o in offres:
        detail = o.get("detail_score", {})
        stack_json = json.dumps(o.get("stack", []), ensure_ascii=False)
        try:
            cur = conn.execute(
                """INSERT OR IGNORE INTO offres
                   (id, entreprise, poste, localisation, contrat, stack, contact, url,
                    description, source, score, score_stack, score_loc, score_contrat,
                    score_qualite, statut, date_ajout, date_publication, date_action)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    o["id"], o["entreprise"], o.get("poste", ""),
                    o.get("localisation", ""), o.get("contrat", ""),
                    stack_json, o.get("contact", ""), o.get("url", ""),
                    o.get("description", ""), o.get("source", ""),
                    o.get("score", 0),
                    detail.get("stack", 0), detail.get("localisation", 0),
                    detail.get("contrat", 0), detail.get("qualite", 0),
                    o.get("statut", "a_postuler"),
                    o.get("date_ajout"), o.get("date_publication", ""),
                    o.get("date_action"),
                ),
            )
            if cur.rowcount > 0:
                ajoutees += 1
            else:
                doublons += 1
        except Exception as exc:
            print(f"  WARN offre ignoree ({o.get('entreprise', '?')}) : {exc}")
    return len(offres), ajoutees


def migrer_linkedin(conn) -> tuple[int, int]:
    if not LINKEDIN_JSON.exists():
        return 0, 0
    contacts = json.loads(LINKEDIN_JSON.read_text(encoding="utf-8"))
    ajoutees = 0
    for c in contacts:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO contacts_linkedin
                   (id, prenom, nom, entreprise, date_acceptation, thread_id, statut, date_action)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    c["id"], c["prenom"], c["nom"],
                    c.get("entreprise"), c.get("date_acceptation"),
                    c.get("thread_id"), c.get("statut", "en_attente"),
                    c.get("date_action"),
                ),
            )
            ajoutees += 1
        except Exception as exc:
            print(f"  WARN contact ignore ({c.get('prenom', '?')} {c.get('nom', '?')}) : {exc}")
    return len(contacts), ajoutees


def main():
    print(f"Migration vers {DB_PATH}")
    print("=" * 50)

    init_db()

    with get_db() as conn:
        print("1. Candidatures (Excel)…", end=" ", flush=True)
        n_cands = migrer_candidatures(conn)
        print(f"{n_cands} candidature(s)")

        cands_db = [dict(r) for r in conn.execute("SELECT id, entreprise FROM candidatures").fetchall()]

        print("2. Entretiens (Excel)…", end=" ", flush=True)
        n_ents = migrer_entretiens(conn, cands_db)
        print(f"{n_ents} entretien(s)")

        print("3. Offres (offres_a_postuler.json)…", end=" ", flush=True)
        total_off, ajoutees_off = migrer_offres(conn)
        print(f"{ajoutees_off}/{total_off} offre(s) migrée(s)")

        print("4. Contacts LinkedIn (messages_linkedin.json)…", end=" ", flush=True)
        total_li, ajoutees_li = migrer_linkedin(conn)
        print(f"{ajoutees_li}/{total_li} contact(s) migré(s)")

    print()
    print("Migration terminee.")
    print(f"   DB : {DB_PATH}")
    print(f"   Taille : {DB_PATH.stat().st_size // 1024} Ko")


if __name__ == "__main__":
    main()

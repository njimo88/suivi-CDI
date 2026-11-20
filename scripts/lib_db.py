#!/usr/bin/env python3
"""
Couche d'accès SQLite pour suivi-CDI.
Toutes les opérations CRUD passent par ce module.
DB : suivi_cdi.db à la racine du projet.
"""
import hashlib
import json
import sqlite3
import unicodedata
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "suivi_cdi.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS candidatures (
    id               INTEGER PRIMARY KEY,
    entreprise       TEXT NOT NULL,
    poste            TEXT,
    localisation     TEXT,
    type_poste       TEXT,
    date_candidature TEXT,
    statut           TEXT NOT NULL DEFAULT '1er contact',
    date_contact     TEXT,
    prochaine_action TEXT,
    date_prochaine   TEXT,
    contact          TEXT,
    source           TEXT,
    stack            TEXT,
    priorite         TEXT,
    commentaires     TEXT
);

CREATE TABLE IF NOT EXISTS entretiens (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    candidature_id INTEGER REFERENCES candidatures(id) ON DELETE SET NULL,
    entreprise     TEXT NOT NULL,
    poste          TEXT,
    date_entretien TEXT,
    type           TEXT,
    interlocuteurs TEXT,
    format         TEXT,
    questions      TEXT,
    resultat       TEXT
);

CREATE TABLE IF NOT EXISTS offres (
    id              TEXT PRIMARY KEY,
    entreprise      TEXT NOT NULL,
    poste           TEXT NOT NULL,
    localisation    TEXT,
    contrat         TEXT,
    stack           TEXT,
    contact         TEXT,
    url             TEXT,
    description     TEXT,
    source          TEXT,
    score           INTEGER,
    score_stack     INTEGER,
    score_loc       INTEGER,
    score_contrat   INTEGER,
    score_qualite   INTEGER,
    statut          TEXT DEFAULT 'a_postuler',
    date_ajout      TEXT,
    date_publication TEXT,
    date_action     TEXT
);

CREATE INDEX IF NOT EXISTS idx_offres_statut ON offres(statut);
CREATE INDEX IF NOT EXISTS idx_offres_score  ON offres(score DESC);
CREATE INDEX IF NOT EXISTS idx_offres_pub    ON offres(date_publication DESC);

CREATE TABLE IF NOT EXISTS contacts_linkedin (
    id               TEXT PRIMARY KEY,
    prenom           TEXT NOT NULL,
    nom              TEXT NOT NULL,
    entreprise       TEXT,
    ville            TEXT,
    date_acceptation TEXT,
    thread_id        TEXT,
    statut           TEXT DEFAULT 'en_attente',
    date_action      TEXT
);

CREATE TABLE IF NOT EXISTS evenements (
    id            TEXT PRIMARY KEY,
    titre         TEXT NOT NULL,
    type          TEXT NOT NULL DEFAULT 'autre',
    date_echeance TEXT,
    description   TEXT,
    entreprise    TEXT,
    contact       TEXT,
    statut        TEXT NOT NULL DEFAULT 'a_faire',
    priorite      TEXT NOT NULL DEFAULT 'normal',
    date_created  TEXT
);
CREATE INDEX IF NOT EXISTS idx_evenements_date   ON evenements(date_echeance ASC);
CREATE INDEX IF NOT EXISTS idx_evenements_statut ON evenements(statut);

CREATE TABLE IF NOT EXISTS prospects_apollo (
    id           TEXT PRIMARY KEY,
    prenom       TEXT NOT NULL,
    nom          TEXT NOT NULL,
    entreprise   TEXT NOT NULL,
    poste        TEXT,
    message      TEXT,
    statut       TEXT DEFAULT 'a_traiter',
    canal        TEXT,
    date_ajout   TEXT,
    date_action  TEXT
);
CREATE INDEX IF NOT EXISTS idx_apollo_statut ON prospects_apollo(statut);

CREATE TABLE IF NOT EXISTS esn_strasbourg (
    id           TEXT PRIMARY KEY,
    nom          TEXT NOT NULL,
    site_web     TEXT,
    specialite   TEXT,
    contact      TEXT,
    statut       TEXT DEFAULT 'a_contacter',
    canal        TEXT,
    notes        TEXT,
    date_ajout   TEXT,
    date_action  TEXT
);
CREATE INDEX IF NOT EXISTS idx_esn_statut ON esn_strasbourg(statut);
"""


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(contacts_linkedin)").fetchall()}
        if "ville" not in cols:
            conn.execute("ALTER TABLE contacts_linkedin ADD COLUMN ville TEXT")
        conn.execute("DROP TABLE IF EXISTS missions_freelance")


# ── Candidatures ──────────────────────────────────────────────────────────────

def load_candidatures() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM candidatures ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def get_candidature(cand_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM candidatures WHERE id=?", (cand_id,)).fetchone()
    return dict(row) if row else None


def ajouter_candidature(**fields) -> int:
    cols = list(fields.keys())
    placeholders = ", ".join("?" * len(cols))
    sql = f"INSERT INTO candidatures ({', '.join(cols)}) VALUES ({placeholders})"
    with get_db() as conn:
        cur = conn.execute(sql, list(fields.values()))
        return cur.lastrowid


def update_candidature(cand_id: int, **fields):
    if not fields:
        return
    sets = ", ".join(f"{k}=?" for k in fields)
    sql = f"UPDATE candidatures SET {sets} WHERE id=?"
    with get_db() as conn:
        conn.execute(sql, list(fields.values()) + [cand_id])


# ── Entretiens ────────────────────────────────────────────────────────────────

def load_entretiens() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM entretiens ORDER BY date_entretien DESC").fetchall()
    return [dict(r) for r in rows]


def ajouter_entretien(**fields) -> int:
    cols = list(fields.keys())
    placeholders = ", ".join("?" * len(cols))
    sql = f"INSERT INTO entretiens ({', '.join(cols)}) VALUES ({placeholders})"
    with get_db() as conn:
        cur = conn.execute(sql, list(fields.values()))
        return cur.lastrowid


# ── Offres ────────────────────────────────────────────────────────────────────

def offres_lister(statut: str = "a_postuler") -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM offres WHERE statut=? ORDER BY score DESC, date_ajout DESC",
            (statut,),
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("stack") and isinstance(d["stack"], str):
            try:
                d["stack"] = json.loads(d["stack"])
            except (json.JSONDecodeError, ValueError):
                d["stack"] = [s.strip() for s in d["stack"].split(",") if s.strip()]
        if d.get("detail_score") is None:
            d["detail_score"] = {
                "stack": d.get("score_stack", 0),
                "localisation": d.get("score_loc", 0),
                "contrat": d.get("score_contrat", 0),
                "qualite": d.get("score_qualite", 0),
            }
        result.append(d)
    return result


def offres_stats() -> dict:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT statut, COUNT(*) as n FROM offres GROUP BY statut"
        ).fetchall()
    counts = {r["statut"]: r["n"] for r in rows}
    total = conn.execute("SELECT COUNT(*) FROM offres").fetchone()[0] if False else sum(counts.values())
    return {
        "a_postuler": counts.get("a_postuler", 0),
        "postule":    counts.get("postule", 0),
        "ignore":     counts.get("ignore", 0),
        "total":      total,
    }


def offres_get(offre_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM offres WHERE id=?", (offre_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    if d.get("stack") and isinstance(d["stack"], str):
        try:
            d["stack"] = json.loads(d["stack"])
        except (json.JSONDecodeError, ValueError):
            d["stack"] = [s.strip() for s in d["stack"].split(",") if s.strip()]
    if d.get("detail_score") is None:
        d["detail_score"] = {
            "stack": d.get("score_stack", 0),
            "localisation": d.get("score_loc", 0),
            "contrat": d.get("score_contrat", 0),
            "qualite": d.get("score_qualite", 0),
        }
    return d


def _sanitize(s) -> str:
    """Retire les caractères surrogates orphelins (emoji mal encodés côté API source)
    qui font planter l'écriture SQLite ('utf-8' codec can't encode ... surrogates not allowed)."""
    if not isinstance(s, str):
        return s
    return s.encode("utf-8", "ignore").decode("utf-8")


def offres_ajouter(batch: list[dict]) -> dict:
    ajoutees = 0
    doublons = 0
    today = date.today().isoformat()
    with get_db() as conn:
        for o in batch:
            detail = o.get("detail_score", {})
            stack_json = json.dumps(o.get("stack", []), ensure_ascii=False)
            try:
                conn.execute(
                    """INSERT INTO offres
                       (id, entreprise, poste, localisation, contrat, stack, contact, url,
                        description, source, score, score_stack, score_loc, score_contrat,
                        score_qualite, statut, date_ajout, date_publication, date_action)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        _sanitize(o["id"]), _sanitize(o["entreprise"]), _sanitize(o.get("poste", "")),
                        _sanitize(o.get("localisation", "")), _sanitize(o.get("contrat", "")),
                        _sanitize(stack_json), _sanitize(o.get("contact", "")), _sanitize(o.get("url", "")),
                        _sanitize(o.get("description", "")), _sanitize(o.get("source", "")),
                        o.get("score", 0),
                        detail.get("stack", 0), detail.get("localisation", 0),
                        detail.get("contrat", 0), detail.get("qualite", 0),
                        _sanitize(o.get("statut", "a_postuler")),
                        _sanitize(o.get("date_ajout", today)),
                        _sanitize(o.get("date_publication", "")),
                        _sanitize(o.get("date_action")),
                    ),
                )
                ajoutees += 1
            except sqlite3.IntegrityError:
                doublons += 1
    return {"ajoutees": ajoutees, "doublons": doublons}


def offres_marquer(offre_id: str, statut: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE offres SET statut=?, date_action=? WHERE id=?",
            (statut, date.today().isoformat(), offre_id),
        )


# ── Contacts LinkedIn ─────────────────────────────────────────────────────────

def linkedin_lister(statut: str = "en_attente") -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM contacts_linkedin WHERE statut=? ORDER BY date_acceptation DESC",
            (statut,),
        ).fetchall()
    return [dict(r) for r in rows]


def linkedin_stats() -> dict:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT statut, COUNT(*) as n FROM contacts_linkedin GROUP BY statut"
        ).fetchall()
    counts = {r["statut"]: r["n"] for r in rows}
    return {
        "en_attente": counts.get("en_attente", 0),
        "envoye":     counts.get("envoye", 0),
        "ignore":     counts.get("ignore", 0),
        "total":      sum(counts.values()),
    }


def linkedin_marquer(contact_id: str, statut: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE contacts_linkedin SET statut=?, date_action=? WHERE id=?",
            (statut, date.today().isoformat(), contact_id),
        )


def linkedin_update_entreprise(contact_id: str, entreprise: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE contacts_linkedin SET entreprise=? WHERE id=?",
            (entreprise, contact_id),
        )


def linkedin_update_ville(contact_id: str, ville: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE contacts_linkedin SET ville=? WHERE id=?",
            (ville, contact_id),
        )


# ── Événements ────────────────────────────────────────────────────────────────

def evenements_lister(statut: str = "a_faire", jours_max: int = None) -> list[dict]:
    with get_db() as conn:
        if jours_max is not None:
            from datetime import timedelta
            limite = (date.today() + timedelta(days=jours_max)).isoformat()
            rows = conn.execute(
                "SELECT * FROM evenements WHERE statut=? AND (date_echeance IS NULL OR date_echeance <= ?) ORDER BY date_echeance ASC",
                (statut, limite),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM evenements WHERE statut=? ORDER BY date_echeance ASC",
                (statut,),
            ).fetchall()
    return [dict(r) for r in rows]


def evenements_ajouter(batch: list[dict]) -> dict:
    ajoutes = 0
    doublons = 0
    today = date.today().isoformat()
    with get_db() as conn:
        for ev in batch:
            ev_id = ev.get("id")
            if not ev_id:
                import hashlib, time
                raw = (ev.get("titre", "") + str(time.time())).encode()
                ev_id = today + "-" + hashlib.md5(raw).hexdigest()[:8]
            try:
                conn.execute(
                    """INSERT INTO evenements
                       (id, titre, type, date_echeance, description, entreprise, contact, statut, priorite, date_created)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (
                        ev_id,
                        ev.get("titre", ""),
                        ev.get("type", "autre"),
                        ev.get("date_echeance"),
                        ev.get("description"),
                        ev.get("entreprise"),
                        ev.get("contact"),
                        ev.get("statut", "a_faire"),
                        ev.get("priorite", "normal"),
                        ev.get("date_created", today),
                    ),
                )
                ajoutes += 1
            except sqlite3.IntegrityError:
                doublons += 1
    return {"ajoutes": ajoutes, "doublons": doublons}


def evenements_marquer(event_id: str, statut: str):
    with get_db() as conn:
        conn.execute(
            "UPDATE evenements SET statut=? WHERE id=?",
            (statut, event_id),
        )


def _norm_name(s: str) -> str:
    """Normalise une chaîne : minuscules + supprime accents."""
    return unicodedata.normalize("NFD", s.lower().strip()).encode("ascii", "ignore").decode()


def linkedin_ajouter(batch: list[dict]) -> dict:
    ajoutes = 0
    doublons = 0
    today = date.today().isoformat()
    with get_db() as conn:
        for c in batch:
            # Déduplication par prenom+nom (insensible à la casse et aux accents)
            all_rows = conn.execute("SELECT id, prenom, nom FROM contacts_linkedin").fetchall()
            existing = next(
                (r for r in all_rows
                 if _norm_name(r["prenom"]) == _norm_name(c["prenom"])
                 and _norm_name(r["nom"]) == _norm_name(c["nom"])),
                None,
            )
            if existing:
                doublons += 1
                continue
            try:
                conn.execute(
                    """INSERT INTO contacts_linkedin
                       (id, prenom, nom, entreprise, ville, date_acceptation, thread_id, statut, date_action)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        c["id"], c["prenom"], c["nom"],
                        c.get("entreprise"), c.get("ville"),
                        c.get("date_acceptation", today),
                        c.get("thread_id"), c.get("statut", "en_attente"),
                        c.get("date_action"),
                    ),
                )
                ajoutes += 1
            except sqlite3.IntegrityError:
                doublons += 1
    return {"ajoutes": ajoutes, "doublons": doublons}


# ── Prospects Apollo ──────────────────────────────────────────────────────────

def apollo_lister(statut: str = "a_traiter") -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM prospects_apollo WHERE statut=? ORDER BY date_ajout DESC, entreprise ASC",
            (statut,),
        ).fetchall()
    return [dict(r) for r in rows]


def apollo_stats() -> dict:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT statut, COUNT(*) as n FROM prospects_apollo GROUP BY statut"
        ).fetchall()
    counts = {r["statut"]: r["n"] for r in rows}
    return {
        "a_traiter": counts.get("a_traiter", 0),
        "envoye":    counts.get("envoye", 0),
        "ignore":    counts.get("ignore", 0),
        "total":     sum(counts.values()),
    }


def apollo_marquer(prospect_id: str, statut: str, canal: str = None):
    with get_db() as conn:
        conn.execute(
            "UPDATE prospects_apollo SET statut=?, canal=?, date_action=? WHERE id=?",
            (statut, canal, date.today().isoformat(), prospect_id),
        )


def apollo_ajouter(batch: list[dict]) -> dict:
    ajoutes = 0
    doublons = 0
    today = date.today().isoformat()
    with get_db() as conn:
        all_rows = conn.execute("SELECT prenom, nom, entreprise FROM prospects_apollo").fetchall()
        existing_keys = {
            (_norm_name(r["prenom"]), _norm_name(r["nom"]), _norm_name(r["entreprise"]))
            for r in all_rows
        }
        for p in batch:
            key = (_norm_name(p["prenom"]), _norm_name(p["nom"]), _norm_name(p["entreprise"]))
            if key in existing_keys:
                doublons += 1
                continue
            try:
                conn.execute(
                    """INSERT INTO prospects_apollo
                       (id, prenom, nom, entreprise, poste, message, statut, canal, date_ajout, date_action)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (
                        p["id"], p["prenom"], p["nom"], p["entreprise"],
                        p.get("poste", ""), p.get("message", ""),
                        p.get("statut", "a_traiter"), None,
                        p.get("date_ajout", today), None,
                    ),
                )
                existing_keys.add(key)
                ajoutes += 1
            except sqlite3.IntegrityError:
                doublons += 1
    return {"ajoutes": ajoutes, "doublons": doublons}


# ── ESN Strasbourg ──────────────────────────────────────────────────────────

def esn_lister(statut: str = None) -> list[dict]:
    with get_db() as conn:
        if statut:
            rows = conn.execute(
                "SELECT * FROM esn_strasbourg WHERE statut=? ORDER BY date_ajout DESC, nom ASC",
                (statut,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM esn_strasbourg ORDER BY date_ajout DESC, nom ASC"
            ).fetchall()
    return [dict(r) for r in rows]


def esn_stats() -> dict:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT statut, COUNT(*) as n FROM esn_strasbourg GROUP BY statut"
        ).fetchall()
    counts = {r["statut"]: r["n"] for r in rows}
    return {
        "a_contacter": counts.get("a_contacter", 0),
        "contacte":    counts.get("contacte", 0),
        "en_cours":    counts.get("en_cours", 0),
        "refus":       counts.get("refus", 0),
        "sans_suite":  counts.get("sans_suite", 0),
        "total":       sum(counts.values()),
    }


def esn_marquer(esn_id: str, statut: str, canal: str = None):
    with get_db() as conn:
        conn.execute(
            "UPDATE esn_strasbourg SET statut=?, canal=?, date_action=? WHERE id=?",
            (statut, canal, date.today().isoformat(), esn_id),
        )


def esn_ajouter(batch: list[dict]) -> dict:
    ajoutes = 0
    doublons = 0
    today = date.today().isoformat()
    with get_db() as conn:
        for e in batch:
            eid = e.get("id") or hashlib.md5(_norm_name(e["nom"]).encode()).hexdigest()[:12]
            existe = conn.execute(
                "SELECT 1 FROM esn_strasbourg WHERE id=?", (eid,)
            ).fetchone()
            if existe:
                doublons += 1
                continue
            try:
                conn.execute(
                    """INSERT INTO esn_strasbourg
                       (id, nom, site_web, specialite, contact, statut, canal, notes, date_ajout, date_action)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (
                        eid, e["nom"], e.get("site_web", ""), e.get("specialite", ""),
                        e.get("contact", ""), e.get("statut", "a_contacter"), None,
                        e.get("notes", ""), e.get("date_ajout", today), None,
                    ),
                )
                ajoutes += 1
            except sqlite3.IntegrityError:
                doublons += 1
    return {"ajoutes": ajoutes, "doublons": doublons}

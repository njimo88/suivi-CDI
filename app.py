#!/usr/bin/env python3
"""
Interface web locale pour le suivi CDI.
Lance avec : python3 app.py
Ouvre http://localhost:5000 dans le navigateur.
"""
import json
import re
import sys
import os
from datetime import date, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from lib_excel import (
    load_candidatures, load_entretiens, days_since,
    a_entretien_passe, derniere_interaction, format_date_fr,
    STATUTS_ACTIFS, update_programmatic, ajouter_programmatic,
    ensure_exports_dir, EXCEL_PATH
)
from relances import construire_relances, generer_message
from offres_store import ajouter_offres, marquer, lister, stats as offres_stats, get_offre
from fetch_offres_ft import fetch_and_score as ft_fetch_and_score
from linkedin_store import (
    lister as linkedin_lister, marquer as linkedin_marquer,
    mettre_a_jour_entreprise, stats as linkedin_stats
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB max upload


# ── Helpers ──────────────────────────────────────────────────────────────────

MOTS_REFUS = [
    "non retenu", "pas retenu", "ne correspond pas", "regretter",
    "n'avons pas retenu", "candidature ne convient pas", "nous ne donnons pas",
    "ne pas donner suite", "sans suite", "avons retenu d'autres candidats",
]
MOTS_ENTRETIEN = [
    "entretien", "rendez-vous", "rdv", "disponibilités", "créneaux",
    "rencontrer", "visio", "teams", "zoom", "appel téléphonique",
]
MOTS_PAS_OPPORT = [
    "pas d'opportunité", "pas de poste", "pas de besoin", "aucun poste",
    "pas de recrutement", "recrutement gelé",
]


def detecter_signal(texte: str) -> str:
    """Détecte le type de signal dans un email."""
    t = texte.lower()
    if any(m in t for m in MOTS_REFUS):
        return "refus"
    if any(m in t for m in MOTS_ENTRETIEN):
        return "entretien"
    if any(m in t for m in MOTS_PAS_OPPORT):
        return "pas_opport"
    if len(texte) < 200 and ("bien reçu" in t or "accusé" in t or "prise en compte" in t):
        return "accuse"
    return "inconnu"


def extraire_entreprise_depuis_email(texte: str, candidatures: list) -> dict | None:
    """Essaie de matcher l'email avec une candidature existante."""
    t_low = texte.lower()
    meilleur = None
    score = 0
    for c in candidatures:
        nom = c["entreprise"].lower()
        if nom in t_low:
            s = len(nom)
            if s > score:
                score = s
                meilleur = c
        # Vérifier aussi le contact
        if c["contact"] and c["contact"].split()[0].lower() in t_low:
            if meilleur is None or score < 3:
                meilleur = c
    return meilleur


def analyser_emails(texte_brut: str) -> list[dict]:
    """
    Découpe le texte en emails individuels et analyse chacun.
    Retourne une liste de résultats d'analyse.
    """
    candidatures = load_candidatures()
    actifs = [c for c in candidatures if c["statut"] in STATUTS_ACTIFS]

    # Découper par séparateurs courants
    separateurs = r"\n\s*[-—=]{3,}\s*\n|\n\s*\n\s*\n"
    blocs = re.split(separateurs, texte_brut.strip())
    blocs = [b.strip() for b in blocs if len(b.strip()) > 30]

    resultats = []
    for bloc in blocs:
        signal = detecter_signal(bloc)
        cand = extraire_entreprise_depuis_email(bloc, actifs)

        resultats.append({
            "texte": bloc[:300] + ("..." if len(bloc) > 300 else ""),
            "signal": signal,
            "entreprise": cand["entreprise"] if cand else None,
            "cand_id": cand["id"] if cand else None,
            "statut_propose": {
                "refus": "Refus",
                "pas_opport": "Pas d'opportunités",
            }.get(signal),
            "commentaire_propose": {
                "refus": "Refus reçu par email",
                "entretien": "Invitation entretien reçue",
                "pas_opport": "Pas d'opportunités actuellement",
                "accuse": None,
                "inconnu": None,
            }.get(signal),
            "prioritaire": signal == "entretien",
            "ignorer": signal == "accuse",
        })

    return resultats


# ── Routes API ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/dashboard")
def api_dashboard():
    """Retourne toutes les données pour le dashboard."""
    cands = load_candidatures()
    ents = load_entretiens()
    actifs = [c for c in cands if c["statut"] in STATUTS_ACTIFS]

    # Stats pipeline
    stats = {
        "total": len(cands),
        "actifs": len(actifs),
        "haute": sum(1 for c in actifs if c["priorite"] == "Haute"),
        "moyenne": sum(1 for c in actifs if c["priorite"] == "Moyenne"),
        "entretiens": len(ents),
        "archives": len(cands) - len(actifs),
    }

    # Relances
    relances_data = construire_relances(cands, ents)
    relances = []
    for urgence, jours, c, ents_cand, msg in relances_data:
        relances.append({
            "urgence": urgence,
            "jours": jours,
            "entreprise": c["entreprise"],
            "poste": c["poste"],
            "contact": c["contact"],
            "source": c.get("source"),
            "statut": c["statut"],
            "message": msg,
            "cloture": urgence == "CRITIQUE" and jours >= 60,
        })

    return jsonify({"stats": stats, "relances": relances})


@app.route("/api/relances/action", methods=["POST"])
def api_relances_action():
    data = request.get_json()
    entreprise = (data.get("entreprise") or "").strip()
    action = data.get("action", "")
    if not entreprise or action not in ("relance_envoyee", "pas_opportunites"):
        return jsonify({"ok": False, "msg": "Paramètres invalides"}), 400

    today = date.today()
    if action == "relance_envoyee":
        ok, msg = update_programmatic(
            entreprise_or_id=entreprise,
            commentaire=f"Relance envoyée le {today.strftime('%d/%m')}",
            date_contact=today,
        )
    else:
        ok, msg = update_programmatic(
            entreprise_or_id=entreprise,
            statut="Pas d'opportunités",
            date_contact=today,
        )
    return jsonify({"ok": ok, "msg": msg})


@app.route("/api/analyser", methods=["POST"])
def api_analyser():
    """Analyse le texte collé (emails LinkedIn/Gmail)."""
    data = request.get_json()
    texte = data.get("texte", "").strip()
    if not texte:
        return jsonify({"error": "Texte vide"}), 400

    resultats = analyser_emails(texte)
    return jsonify({"resultats": resultats})


@app.route("/api/appliquer", methods=["POST"])
def api_appliquer():
    """Applique les updates validés par l'utilisateur."""
    data = request.get_json()
    updates = data.get("updates", [])

    resultats = []
    for u in updates:
        ok, msg = update_programmatic(
            entreprise_or_id=u["entreprise"],
            statut=u.get("statut"),
            commentaire=u.get("commentaire"),
        )
        resultats.append({"entreprise": u["entreprise"], "ok": ok, "msg": msg})

    return jsonify({"resultats": resultats})


@app.route("/api/pipeline")
def api_pipeline():
    """Retourne toutes les candidatures pour la vue Pipeline."""
    cands = load_candidatures()
    ents = load_entretiens()
    result = []
    for c in cands:
        last = derniere_interaction(c, ents)
        silence = days_since(last) if last else None
        result.append({
            **{k: v for k, v in c.items() if k != "row"},
            "silence": silence,
            "date_contact_fmt": format_date_fr(c["date_contact"]) if c["date_contact"] else "—",
            "date_cand_fmt": format_date_fr(c["date_cand"]) if c["date_cand"] else "—",
            "has_entretien": a_entretien_passe(c, ents),
        })
    return jsonify({"candidatures": result})


@app.route("/api/offres")
def api_offres():
    """Retourne les offres filtrées par statut."""
    statut = request.args.get("statut", "a_postuler")
    if statut not in ("a_postuler", "postule", "ignore"):
        statut = "a_postuler"
    offres = lister(statut)
    s = offres_stats()
    return jsonify({"offres": offres, "stats": s})


@app.route("/api/offres/marquer", methods=["POST"])
def api_offres_marquer():
    """Marque une offre comme postulée ou ignorée. Si postulée, ajoute dans Excel."""
    data = request.get_json()
    offre_id = data.get("id")
    statut = data.get("statut")  # "postule" ou "ignore"
    if not offre_id or statut not in ("postule", "ignore"):
        return jsonify({"error": "Paramètres invalides"}), 400

    ok = marquer(offre_id, statut)
    excel_result = None

    if ok and statut == "postule":
        offre = get_offre(offre_id)
        if offre:
            stack_str = ", ".join(offre.get("stack", [])) if isinstance(offre.get("stack"), list) else offre.get("stack", "")
            # Détecter type_poste depuis localisation
            loc = offre.get("localisation", "")
            if "sur site" in loc.lower():
                type_poste = "Sur site"
            elif "full remote" in loc.lower() or "télétravail" in loc.lower():
                type_poste = "Full remote"
            else:
                type_poste = "Hybride"
            commentaire = f"[{date.today().strftime('%d/%m/%Y')}] Candidature envoyée via {offre.get('source', 'LinkedIn')}. Score offre : {offre.get('score', '?')}/100."
            ok_excel, msg_excel, new_id = ajouter_programmatic(
                entreprise=offre["entreprise"],
                poste=offre.get("poste", ""),
                localisation=loc,
                type_poste=type_poste,
                contact=offre.get("contact", ""),
                source=offre.get("source", "LinkedIn"),
                stack=stack_str,
                commentaires=commentaire,
            )
            excel_result = {"ok": ok_excel, "msg": msg_excel, "id": new_id}

    return jsonify({"ok": ok, "excel": excel_result})


@app.route("/api/offres/scan-ft", methods=["POST"])
def api_scan_ft():
    """Lance un scan France Travail sur le dernier mois et ajoute les offres qualifiées."""
    data = request.get_json() or {}
    jours = int(data.get("jours", 31))
    jours = max(1, min(jours, 31))

    result = ft_fetch_and_score(jours)

    if "error" in result:
        code = result["error"]
        if code == "credentials_missing":
            return jsonify({"ok": False, "error": "credentials_missing",
                            "message": result["message"]}), 200
        return jsonify({"ok": False, "error": code, "message": result.get("message", "")}), 500

    return jsonify({"ok": True, **result})


@app.route("/api/upload-excel", methods=["POST"])
def api_upload_excel():
    """Remplace suivi.xlsx par le fichier uploadé."""
    if "fichier" not in request.files:
        return jsonify({"error": "Aucun fichier"}), 400

    f = request.files["fichier"]
    if not f.filename.endswith(".xlsx"):
        return jsonify({"error": "Fichier .xlsx uniquement"}), 400

    # Sauvegarde de l'ancien fichier
    backup = EXCEL_PATH.parent / f"suivi_backup_{date.today().isoformat()}.xlsx"
    if EXCEL_PATH.exists():
        import shutil
        shutil.copy2(EXCEL_PATH, backup)

    f.save(str(EXCEL_PATH))
    cands = load_candidatures()
    return jsonify({"ok": True, "nb_candidatures": len(cands)})


@app.route("/api/linkedin-messages")
def api_linkedin_messages():
    msgs = linkedin_lister("en_attente")
    s = linkedin_stats()
    return jsonify({"messages": msgs, "stats": s})


@app.route("/api/linkedin-messages/entreprise", methods=["POST"])
def api_linkedin_entreprise():
    data = request.get_json()
    ok = mettre_a_jour_entreprise(data.get("id"), data.get("entreprise", ""))
    return jsonify({"ok": ok})


@app.route("/api/linkedin-messages/marquer", methods=["POST"])
def api_linkedin_marquer():
    data = request.get_json()
    msg_id = data.get("id")
    statut = data.get("statut")
    entreprise = data.get("entreprise", "").strip()
    prenom = data.get("prenom", "").strip()
    nom = data.get("nom", "").strip()
    if not msg_id or statut not in ("envoye", "ignore"):
        return jsonify({"error": "Paramètres invalides"}), 400

    # Si envoyé avec une entreprise → écrire dans l'Excel
    excel_msg = None
    if statut == "envoye" and entreprise:
        contact_nom = f"{prenom} {nom}".strip() or None
        commentaire = f"Message LinkedIn envoyé après connexion{' — ' + contact_nom if contact_nom else ''}"
        # Essaie d'abord de mettre à jour une candidature existante
        ok_excel, excel_msg = update_programmatic(
            entreprise_or_id=entreprise,
            statut=None,  # ne change pas le statut si déjà dans le suivi
            commentaire=commentaire,
            contact=contact_nom,
            date_contact=date.today(),
        )
        # Si introuvable → crée la candidature en "1er contact"
        if not ok_excel:
            ok_excel, excel_msg, _ = ajouter_programmatic(
                entreprise=entreprise,
                contact=contact_nom or "",
                source="LinkedIn",
                commentaires=f"[{date.today().strftime('%d/%m/%Y')}] {commentaire}",
            )

    ok = linkedin_marquer(msg_id, statut)
    return jsonify({"ok": ok, "excel_msg": excel_msg})


if __name__ == "__main__":
    print("📊 Suivi CDI — Interface web")
    print("   Ouvre http://localhost:5000 dans ton navigateur")
    print("   Ctrl+C pour arrêter\n")
    app.run(debug=False, port=5000, use_reloader=True)

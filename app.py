#!/usr/bin/env python3
"""
Interface web locale pour le suivi CDI.
Lance avec : python3 app.py
Ouvre http://localhost:5000 dans le navigateur.
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from flask import Flask, render_template, request, jsonify

try:
    import openai as _openai_sdk
except ImportError:
    _openai_sdk = None

sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from lib_excel import (
    load_candidatures, load_entretiens, days_since,
    a_entretien_passe, derniere_interaction, format_date_fr,
    STATUTS_ACTIFS, update_programmatic, ajouter_programmatic,
    ensure_exports_dir, charger_dotenv
)
charger_dotenv()
from relances import construire_relances, generer_message, selectionner_relances_du_jour
from offres_store import ajouter_offres, marquer, lister, stats as offres_stats, get_offre
from fetch_jsearch import fetch_and_score as jsearch_fetch_and_score
from opportunites import info_deja_contacte
from linkedin_store import (
    lister as linkedin_lister, marquer as linkedin_marquer,
    mettre_a_jour_entreprise, mettre_a_jour_ville, stats as linkedin_stats
)
from actions_store import (
    lister as actions_lister, marquer as actions_marquer, stats as actions_stats
)
from informations_store import (
    lister as infos_lister, marquer_lu as infos_marquer_lu
)
from evenements_store import (
    lister as ev_lister, ajouter as ev_ajouter, marquer as ev_marquer, stats as ev_stats
)
from apollo_store import (
    lister as apollo_lister, marquer as apollo_marquer, stats as apollo_stats
)
from esn_store import (
    lister as esn_lister, marquer as esn_marquer, stats as esn_stats
)

app = Flask(__name__)


# ── Générateur de message LinkedIn ───────────────────────────────────────────

_openai_client = None

def _get_openai_client():
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    if _openai_sdk is None:
        return None
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    _openai_client = _openai_sdk.OpenAI(api_key=api_key)
    return _openai_client

_NOM_RE = re.compile(
    r'^([A-ZÀÂÇÉÈÊËÎÏÔÙÛÜ][a-zàâçéèêëîïôùûü\-]+)'
    r'(?:\s+[A-ZÀÂÇÉÈÊËÎÏÔÙÛÜ][A-ZÀÂÇÉÈÊËÎÏÔÙÛÜa-zàâçéèêëîïôùûü\-]*)*'
    r'\s+([A-ZÀÂÇÉÈÊËÎÏÔÙÛÜ][A-ZÀÂÇÉÈÊËÎÏÔÙÛÜa-zàâçéèêëîïôùûü\-]*\.?)$'
)
_ENT_PATTERNS = [
    re.compile(r'(?:chez|@|at)\s+([^\n|·,]{3,40})', re.I),
    re.compile(r'\|\s*([A-Z][^\n|·,]{2,35})\s*$', re.M),
]
_MOTS_POSTE = {"développeur", "developer", "ingénieur", "consultant",
               "ans", "mois", "présent", "today", "actuellement"}
_HEADLINE_SEP_RE = re.compile(r'\s+[-|@·]\s+|\s+(?:chez|at)\s+', re.I)
_EMOJI_RE        = re.compile(r'[^\x00-\xFF]', re.UNICODE)


_LI_NAV_MARKERS = [
    "Reactivate Premium", "Reactivate LinkedIn Premium",
    "Try Premium for free", "Try Premium",
    "For Business", "Essayez Premium",
]
_LI_NAV_LINES = {
    "home", "my network", "jobs", "messaging", "notifications",
    "me", "search", "for business", "reactivate", "premium",
    "0 notifications", "21", "abonnés", "relations",
}

def _nettoyer_texte_linkedin(texte: str) -> str:
    """Supprime le bloc de navigation LinkedIn avant le vrai contenu du profil."""
    # Cherche un marqueur de fin de nav connu
    for marker in _LI_NAV_MARKERS:
        idx = texte.find(marker)
        if idx != -1:
            apres = texte[idx + len(marker):]
            lines = apres.splitlines()
            # Saute les lignes vides puis retourne le reste
            for i, l in enumerate(lines):
                if l.strip():
                    return "\n".join(lines[i:])
    # Fallback : supprime les premières lignes qui sont des éléments nav connus
    lines = texte.splitlines()
    start = 0
    for i, l in enumerate(lines):
        if l.strip().lower() not in _LI_NAV_LINES and l.strip():
            # Première ligne non-nav non-vide
            start = i
            break
    return "\n".join(lines[start:])


_CONTRAT_RE = re.compile(
    r'^(.+?)\s*[·•]\s*(CDI|CDD|Freelance|Stage|Intérim|Alternance|Apprentissage)\s*$',
    re.I | re.M,
)
_CONTRAT_INLINE_RE = re.compile(
    r'^(.+?)\s+(CDI|CDD|Freelance|Stage|Intérim|Alternance|Apprentissage)\s*$',
    re.I | re.M,
)

_LOGO_DE_RE = re.compile(r'^Logo\s+de\s+(.+)$', re.I)
_MOTS_TITRE = {"développeur", "developer", "ingénieur", "engineer", "consultant",
               "analyste", "manager", "chef", "lead", "logo", "frontend", "backend",
               "fullstack", "resources", "talent", "hr", "rh", "senior", "junior",
               "directeur", "directrice", "responsable", "chargé", "assistant",
               "employer", "acquisition", "specialist", "business", "partner"}
_CONTRAT_TYPES = {"cdi", "cdd", "freelance", "stage", "intérim", "alternance",
                  "apprentissage", "interim"}

def _extraire_entreprise_experience(texte: str) -> str:
    """Extrait l'entreprise du poste le plus récent (2 formats LinkedIn gérés)."""
    lines = texte.splitlines()
    exp_start = -1
    for i, l in enumerate(lines):
        if l.strip() in ("Expérience", "Experience", "Expériences"):
            exp_start = i
            break
    if exp_start == -1:
        return ""

    bloc = [l.strip() for l in lines[exp_start + 1: exp_start + 40] if l.strip()]

    # Format 1 : "Niji CDI" ou "Niji · CDI" — nom et contrat sur la même ligne
    for pattern in (_CONTRAT_RE, _CONTRAT_INLINE_RE):
        m = pattern.search("\n".join(bloc[:20]))
        if m:
            candidate = m.group(1).strip().rstrip("·•").strip()
            if candidate.lower().split()[0] not in _MOTS_TITRE and len(candidate) > 1:
                return candidate

    # Format 2 : "Logo de Groupe SII" suivi de CDI quelques lignes plus loin
    for i, line in enumerate(bloc[:15]):
        m = _LOGO_DE_RE.match(line)
        if m:
            candidate = m.group(1).strip()
            # Vérifier qu'un type de contrat apparaît dans les 8 lignes suivantes
            suivantes = bloc[i + 1: i + 10]
            if any(l.lower() in _CONTRAT_TYPES for l in suivantes):
                return candidate

    # Format 3 : ligne seule = nom entreprise, suivie du type de contrat sur la ligne d'après
    for i, line in enumerate(bloc[:20]):
        if line.lower() in _CONTRAT_TYPES:
            # La ligne avant est soit un titre de poste, soit l'entreprise
            # Cherche en remontant la première ligne qui n'est ni un titre ni une date
            for j in range(i - 1, max(i - 6, -1), -1):
                candidate = bloc[j]
                if (candidate.lower().split()[0] not in _MOTS_TITRE
                        and not re.match(r'^\d|^(jan|fév|mar|avr|mai|juin|juil|août|sept|oct|nov|déc)', candidate, re.I)
                        and len(candidate) > 2):
                    return candidate
            break

    return ""


def _structurer_profil(texte_propre: str) -> str:
    """Extrait les sections nom + expérience pour réduire le bruit envoyé à l'IA."""
    lines = texte_propre.splitlines()
    # Premières 20 lignes non-vides (nom, titre, localisation)
    head = [l for l in lines[:30] if l.strip()][:12]
    # Section Expérience
    exp_lines = []
    for i, l in enumerate(lines):
        if l.strip() in ("Expérience", "Experience", "Expériences"):
            exp_lines = [l2 for l2 in lines[i:i + 25] if l2.strip()]
            break
    if exp_lines:
        return "=== PROFIL ===\n" + "\n".join(head) + "\n\n=== EXPÉRIENCE ===\n" + "\n".join(exp_lines)
    return "\n".join(lines[:60])


def _extraire_profil_linkedin(texte: str) -> dict:
    """Extrait prenom/nom/entreprise via GPT-4o-mini, fallback regex si indisponible."""
    texte_propre = _nettoyer_texte_linkedin(texte)
    contenu = _structurer_profil(texte_propre)
    client = _get_openai_client()
    if client:
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=120,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tu es un extracteur de données de profils LinkedIn. "
                            "Le texte reçu est copié brut depuis un navigateur. "
                            "RÈGLES STRICTES :\n"
                            "1. prenom = prénom de la personne dont c'est le profil (son vrai prénom, PAS 'My', 'Home', etc.).\n"
                            "2. nom = nom de famille de cette même personne.\n"
                            "3. entreprise = nom de la SOCIÉTÉ où travaille la personne en ce moment "
                            "(cherche dans la section 'Expérience' le poste avec la date la plus récente). "
                            "JAMAIS une ville (Paris, Lille, Lyon…), JAMAIS un pays ou région, "
                            "JAMAIS une école, JAMAIS un mot de navigation (Home, Jobs…). "
                            "Si le poste le plus récent mentionne une société comme 'Niji · CDI', "
                            "l'entreprise est 'Niji'.\n"
                            "Réponds UNIQUEMENT avec ce JSON valide, rien d'autre : "
                            '{"prenom": "...", "nom": "...", "entreprise": "..."}.'
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Profil LinkedIn :\n\n"
                            f"{contenu}\n\n"
                            "---\n"
                            "Dans la section EXPÉRIENCE, le premier poste listé est le plus récent. "
                            "Sur une ligne tu verras le nom de l'entreprise suivi du type de contrat "
                            "('Niji CDI', 'Capgemini · CDI', 'Accenture CDD', etc.). "
                            "L'entreprise est la partie AVANT 'CDI', 'CDD', 'Freelance', '·'. "
                            "Exemple : 'Niji CDI' → entreprise = 'Niji'. "
                            "Les villes (Lille, Paris…), régions ou écoles ne sont JAMAIS l'entreprise."
                        ),
                    },
                ],
            )
            data = json.loads(resp.choices[0].message.content.strip())
            entreprise_ia = str(data.get("entreprise", "") or "")
            # Regex plus fiable pour l'entreprise — écrase si trouvée
            entreprise_regex = _extraire_entreprise_experience(texte_propre)
            return {
                "prenom":     str(data.get("prenom", "") or ""),
                "nom":        str(data.get("nom",    "") or ""),
                "entreprise": entreprise_regex or entreprise_ia,
            }
        except Exception:
            pass
    return _extraire_profil_linkedin_regex(texte_propre)


def _extraire_profil_linkedin_regex(texte: str) -> dict:
    """Fallback regex — utilisé si ANTHROPIC_API_KEY absent ou appel échoué."""
    lines = [l.strip() for l in texte.splitlines() if l.strip()]
    prenom, nom, entreprise = "", "", ""
    name_idx = -1

    # 1. Name — scan first 50 lines (LinkedIn nav bar can occupy 10-15 lines)
    for i, line in enumerate(lines[:50]):
        clean_line = _EMOJI_RE.sub('', line).strip()
        m = _NOM_RE.match(clean_line)
        if m:
            parts = clean_line.split()
            prenom   = parts[0]
            nom      = " ".join(parts[1:]).rstrip(".")
            name_idx = i
            break

    # 2. Section Expérience — source la plus fiable (pattern "Entreprise CDI/CDD")
    entreprise = _extraire_entreprise_experience(texte)

    # 3. Fallback : headline juste après le nom ("Titre - Company" / "Titre | Company")
    #    mais seulement si la partie après le séparateur contient un espace (= vrai nom d'entreprise)
    if not entreprise and name_idx >= 0:
        for j in range(name_idx + 1, min(name_idx + 4, len(lines))):
            hl = _EMOJI_RE.sub('', lines[j]).strip()
            m  = _HEADLINE_SEP_RE.search(hl)
            if m:
                candidate = hl[m.end():].strip().rstrip('.')
                # N'accepte que si c'est un vrai nom (contient espace ou majuscule suivie de minuscules)
                if 3 <= len(candidate) <= 80 and (' ' in candidate or not candidate.isupper()):
                    entreprise = candidate
                    break

    # 4. Patterns textuels (chez / @ / at / pipe)
    if not entreprise:
        for p in _ENT_PATTERNS:
            m = p.search(texte[:800])
            if m:
                entreprise = m.group(1).strip().rstrip(".")
                break

    return {"prenom": prenom, "nom": nom, "entreprise": entreprise}


def _generer_message(prenom: str, nom: str, entreprise: str, villes: list = None, stacks: list = None, freelance: bool = False) -> str:
    salut   = f"Bonjour {prenom}," if prenom else "Bonjour,"
    ent     = entreprise if entreprise else "votre entreprise"
    elision = "qu'" if ent[0].lower() in "aeiouàâäéèêëîïôùûü" else "que "

    villes = [v for v in (villes or []) if v]
    if len(villes) == 0:
        ville_str = "Strasbourg"
    elif len(villes) == 1:
        ville_str = villes[0]
    elif len(villes) == 2:
        ville_str = f"{villes[0]} et {villes[1]}"
    else:
        ville_str = ", ".join(villes[:-1]) + f" et {villes[-1]}"
    prep = "à" if len(villes) <= 1 else "sur"

    recherche = "Je recherche un poste de développeur Full Stack"
    if freelance:
        recherche += " ou une mission freelance"
    recherche += f", basé {prep} {ville_str}."
    recherche += " J'ai fait deux ans d'alternance en développement logiciel et une expérience en freelance."
    stacks = [s for s in (stacks or []) if s]
    if stacks:
        if len(stacks) == 1:
            stack_str = stacks[0]
        elif len(stacks) == 2:
            stack_str = f"{stacks[0]} et {stacks[1]}"
        else:
            stack_str = ", ".join(stacks[:-1]) + f" et {stacks[-1]}"
        recherche += f" Je maîtrise {stack_str}."

    return (
        f"{salut}\n\n"
        f"{recherche}\n\n"
        f"Est-ce {elision}{ent} a des besoins en développement en ce moment ?\n\n"
        f"Je peux vous transmettre mon CV avec plaisir.\n\n"
        f"Bien cordialement,\n"
        f"DJILLY Nedjmeddine"
    )


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

    # Relances — plafonnées à RELANCES_PAR_JOUR (voir relances.py) pour éviter
    # de balancer d'un coup un pic de relances arrivées à échéance le même jour.
    # Le reste ressort automatiquement une fois les premières traitées
    # (relance_envoyee/pas_opportunites remettent date_contact à jour → elles
    # sortent de construire_relances jusqu'à la prochaine échéance).
    toutes_relances = construire_relances(cands, ents)
    relances_data, en_attente = selectionner_relances_du_jour(toutes_relances)
    relances = []
    for urgence, jours, c, ents_cand, msg in relances_data:
        relances.append({
            "id": c["id"],
            "urgence": urgence,
            "jours": jours,
            "entreprise": c["entreprise"],
            "poste": c["poste"],
            "localisation": c.get("localisation"),
            "contact": c["contact"],
            "source": c.get("source"),
            "statut": c["statut"],
            "message": msg,
            "cloture": urgence == "CRITIQUE" and jours >= 60,
        })

    return jsonify({"stats": stats, "relances": relances, "relances_en_attente": en_attente})


@app.route("/api/relances/action", methods=["POST"])
def api_relances_action():
    data = request.get_json()
    cand_id = data.get("id")
    entreprise = (data.get("entreprise") or "").strip()
    action = data.get("action", "")
    cible = cand_id if cand_id is not None else entreprise
    if not cible or action not in ("relance_envoyee", "pas_opportunites"):
        return jsonify({"ok": False, "msg": "Paramètres invalides"}), 400

    today = date.today()
    if action == "relance_envoyee":
        ok, msg = update_programmatic(
            entreprise_or_id=cible,
            commentaire=f"Relance envoyée le {today.strftime('%d/%m')}",
            date_contact=today,
        )
    else:
        ok, msg = update_programmatic(
            entreprise_or_id=cible,
            statut="Pas d'opportunités",
            date_contact=today,
        )
    return jsonify({"ok": ok, "msg": msg})


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
    # Badge "déjà contacté" calculé à l'affichage : toujours à jour avec le suivi
    candidatures = load_candidatures()
    for o in offres:
        info = info_deja_contacte(o.get("entreprise"), candidatures)
        o["deja_contacte"] = f"{info['date']} — {info['statut']}" if info else ""
    s = offres_stats()
    return jsonify({"offres": offres, "stats": s})


@app.route("/api/offres/marquer", methods=["POST"])
def api_offres_marquer():
    """Marque une offre comme postulée ou ignorée. Si postulée, ajoute dans Excel."""
    data = request.get_json()
    offre_id = data.get("id")
    statut = data.get("statut")  # "postule" ou "ignore"
    contact_override = (data.get("contact") or "").strip()
    villes = [v for v in (data.get("villes") or []) if isinstance(v, str) and v.strip()]
    if not offre_id or statut not in ("postule", "ignore"):
        return jsonify({"error": "Paramètres invalides"}), 400

    ok = marquer(offre_id, statut)
    excel_result = None

    if ok and statut == "postule":
        offre = get_offre(offre_id)
        if offre:
            stack_str = ", ".join(offre.get("stack", [])) if isinstance(offre.get("stack"), list) else offre.get("stack", "")
            loc = offre.get("localisation", "")
            if "sur site" in loc.lower():
                type_poste = "Sur site"
            elif "full remote" in loc.lower() or "télétravail" in loc.lower():
                type_poste = "Full remote"
            else:
                type_poste = "Hybride"
            commentaire = f"[{date.today().strftime('%d/%m/%Y')}] Candidature envoyée via {offre.get('source', 'LinkedIn')}. Score offre : {offre.get('score', '?')}/100."
            if villes:
                if len(villes) == 1:
                    ville_str = villes[0]
                elif len(villes) == 2:
                    ville_str = f"{villes[0]} et {villes[1]}"
                else:
                    ville_str = ", ".join(villes[:-1]) + f" et {villes[-1]}"
                commentaire += f" Villes ciblées : {ville_str}."
            ok_excel, msg_excel, new_id = ajouter_programmatic(
                entreprise=offre["entreprise"],
                poste=offre.get("poste", ""),
                localisation=loc,
                type_poste=type_poste,
                contact=contact_override or offre.get("contact", ""),
                source=offre.get("source", "LinkedIn"),
                stack=stack_str,
                commentaires=commentaire,
            )
            excel_result = {"ok": ok_excel, "msg": msg_excel, "id": new_id}

    return jsonify({"ok": ok, "excel": excel_result})


@app.route("/api/offres/scan", methods=["POST"])
def api_scan_offres():
    """Scan JSearch (seule source d'offres hors alertes email) sur les villes choisies."""
    data = request.get_json() or {}
    villes = data.get("villes", [])
    if not villes or not isinstance(villes, list):
        return jsonify({"ok": False, "error": "villes_manquantes",
                        "message": "Aucune ville sélectionnée"}), 400
    villes = [str(v).strip() for v in villes if str(v).strip()]
    if not villes:
        return jsonify({"ok": False, "error": "villes_manquantes",
                        "message": "Aucune ville valide"}), 400
    return jsonify(jsearch_fetch_and_score(villes))


@app.route("/api/generer-message-linkedin", methods=["POST"])
def api_generer_message_linkedin():
    data    = request.get_json() or {}
    texte   = (data.get("texte") or "").strip()
    villes  = [v for v in (data.get("villes") or []) if isinstance(v, str) and v.strip()]
    stacks  = [s for s in (data.get("stacks") or []) if isinstance(s, str) and s.strip()]
    freelance = bool(data.get("freelance"))
    if not texte:
        return jsonify({"ok": False, "msg": "Texte vide"}), 400
    profil  = _extraire_profil_linkedin(texte)
    message = _generer_message(profil["prenom"], profil["nom"], profil["entreprise"], villes, stacks, freelance)
    return jsonify({"ok": True, "message": message, **profil})


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


@app.route("/api/linkedin-messages/ville", methods=["POST"])
def api_linkedin_ville():
    data = request.get_json()
    ok = mettre_a_jour_ville(data.get("id"), data.get("ville", ""))
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


@app.route("/api/actions-du-jour")
def api_actions_du_jour():
    actions = actions_lister("a_faire")
    s = actions_stats()
    return jsonify({"actions": actions, "stats": s})


@app.route("/api/actions-du-jour/marquer", methods=["POST"])
def api_actions_marquer():
    data = request.get_json()
    action_id = data.get("id")
    statut = data.get("statut")
    if not action_id or statut not in ("fait", "ignore"):
        return jsonify({"ok": False, "msg": "Paramètres invalides"}), 400
    ok = actions_marquer(action_id, statut)
    return jsonify({"ok": ok})


@app.route("/api/informations")
def api_informations():
    return jsonify({"informations": infos_lister("non_lu")})


@app.route("/api/informations/lu", methods=["POST"])
def api_informations_lu():
    info_id = (request.get_json() or {}).get("id")
    if not info_id:
        return jsonify({"ok": False, "msg": "id manquant"}), 400
    return jsonify({"ok": infos_marquer_lu(info_id)})


@app.route("/api/evenements")
def api_evenements():
    statut = request.args.get("statut", "a_faire")
    jours = request.args.get("jours")
    jours_max = int(jours) if jours and jours.isdigit() else None
    evs = ev_lister(statut, jours_max)
    s = ev_stats()
    return jsonify({"evenements": evs, "stats": s})


@app.route("/api/evenements", methods=["POST"])
def api_evenements_ajouter():
    data = request.get_json()
    if not data or not data.get("titre"):
        return jsonify({"ok": False, "msg": "titre manquant"}), 400
    result = ev_ajouter([data])
    return jsonify({"ok": True, **result})


@app.route("/api/evenements/marquer", methods=["POST"])
def api_evenements_marquer():
    data = request.get_json()
    event_id = data.get("id")
    statut = data.get("statut")
    if not event_id or statut not in ("fait", "annule"):
        return jsonify({"ok": False, "msg": "Paramètres invalides"}), 400
    ev_marquer(event_id, statut)
    return jsonify({"ok": True})


@app.route("/api/apollo")
def api_apollo():
    """Retourne les prospects Apollo à traiter."""
    prospects = apollo_lister("a_traiter")
    s = apollo_stats()
    return jsonify({"prospects": prospects, "stats": s})


@app.route("/api/apollo/marquer", methods=["POST"])
def api_apollo_marquer():
    data = request.get_json()
    prospect_id = data.get("id")
    statut = data.get("statut")
    canal = data.get("canal")  # "gmail" ou "whatsapp", requis si statut="envoye"
    if not prospect_id or statut not in ("envoye", "ignore"):
        return jsonify({"ok": False, "msg": "Paramètres invalides"}), 400
    if statut == "envoye" and canal not in ("gmail", "whatsapp"):
        return jsonify({"ok": False, "msg": "Canal requis (gmail ou whatsapp)"}), 400
    ok = apollo_marquer(prospect_id, statut, canal)
    return jsonify({"ok": ok})


@app.route("/api/esn")
def api_esn():
    """Retourne les ESN Strasbourg à contacter."""
    esn = esn_lister("a_contacter")
    s = esn_stats()
    return jsonify({"esn": esn, "stats": s})


@app.route("/api/esn/marquer", methods=["POST"])
def api_esn_marquer():
    data = request.get_json()
    esn_id = data.get("id")
    statut = data.get("statut")
    canal = data.get("canal")
    if not esn_id or statut not in ("contacte", "en_cours", "refus", "sans_suite"):
        return jsonify({"ok": False, "msg": "Paramètres invalides"}), 400
    ok = esn_marquer(esn_id, statut, canal)
    return jsonify({"ok": ok})


if __name__ == "__main__":
    print("📊 Suivi CDI — Interface web")
    print("   Ouvre http://localhost:5000 dans ton navigateur")
    print("   Ctrl+C pour arrêter\n")
    app.run(debug=False, port=5000, use_reloader=True)

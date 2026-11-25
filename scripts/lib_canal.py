#!/usr/bin/env python3
"""
Détecte par quel canal relancer quelqu'un (Gmail, LinkedIn, WhatsApp, téléphone…).

Utilisé par app.py pour afficher « Relancer par : … » sur chaque relance
de l'interface (cartes relances, actions du jour, agenda).
"""
import re

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
CANAL_EXPLICITE_RE = re.compile(r"Canal\s*:\s*([^(.\n]+?)\s*(?:\(([^)]*)\))?\s*(?:\.|$|\n)", re.I)

# Mots-clés → canal, testés dans cet ordre sur chaque ligne
MOTS_CLES = [
    (re.compile(r"whats\s?app", re.I), "WhatsApp"),
    (re.compile(r"linked\s?in", re.I), "LinkedIn"),
    (re.compile(r"t[ée]l[ée]phone|appel", re.I), "Téléphone"),
    (re.compile(r"\be-?mail\b|\bmail\b|gmail", re.I), "Gmail"),
]


def _email(texte):
    m = EMAIL_RE.search(texte or "")
    if not m:
        return None
    adr = m.group(0).rstrip(".")
    # Les adresses de Nedjmeddine ne sont pas une destination de relance
    return None if adr.lower().startswith("djillynedjmeddine") else adr


def _depuis_ligne(ligne):
    adr = _email(ligne)
    if adr:
        return {"canal": "Gmail", "adresse": adr}
    for rx, canal in MOTS_CLES:
        if rx.search(ligne):
            return {"canal": canal, "adresse": None}
    return None


def detecter_canal(*textes, contact=None, source=None, type_action=None):
    """
    Retourne {"canal": str|None, "adresse": str|None}.
    Ordre : mention explicite « Canal : X (adresse) » > type d'action LinkedIn >
    email dans le contact > dernière ligne de texte qui cite un canal > source.
    """
    textes = [t for t in textes if t]

    for t in textes:
        m = CANAL_EXPLICITE_RE.search(t)
        if m:
            return {"canal": m.group(1).strip(), "adresse": (m.group(2) or "").strip() or None}

    if type_action == "message_linkedin":
        return {"canal": "LinkedIn", "adresse": None}

    adr = _email(contact)
    if adr:
        return {"canal": "Gmail", "adresse": adr}

    # Les commentaires sont chronologiques : la ligne la plus récente qui cite
    # un canal donne le dernier canal utilisé.
    for t in textes:
        for ligne in reversed(t.splitlines()):
            res = _depuis_ligne(ligne)
            if res:
                return res

    if source:
        if re.search(r"linked\s?in", source, re.I):
            return {"canal": "LinkedIn", "adresse": None}
        return {"canal": f"via {source}", "adresse": None}

    return {"canal": None, "adresse": None}

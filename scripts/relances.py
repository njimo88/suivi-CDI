#!/usr/bin/env python3
"""
/relances — Propose des messages de relance prêts à envoyer.

Adapte le ton :
- Vouvoiement pour RH / seniors / talent acquisition
- Ton sobre mais direct
- Référence au contexte précis de chaque candidature
- Message de clôture pour relances CRITIQUES > 60 jours

Génère aussi exports/relances_YYYY-MM-DD.md.
"""
from lib_excel import (
    load_candidatures, load_entretiens, days_since,
    a_entretien_passe, derniere_interaction, format_date_fr,
    STATUTS_ACTIFS, ensure_exports_dir
)
from datetime import date


def generer_message(cand, ents_cand, jours):
    """Génère un message de relance adapté au contexte et à l'ancienneté du silence."""
    contact = cand["contact"].split("/")[0].strip() if cand["contact"] else None
    prenom = contact.split()[0] if contact else None

    has_interview = len(ents_cand) > 0
    last_interview = max(ents_cand, key=lambda e: e["date"]) if ents_cand else None

    salut = f"Bonjour {prenom}," if prenom else "Bonjour,"

    # Relance "1er contact" : on a envoyé un premier message, pas encore de réponse
    if cand["statut"] == "1er contact":
        date_contact_str = format_date_fr(cand["date_contact"]) if cand["date_contact"] else "récemment"
        msg = f"""{salut}

Je me permets de revenir vers vous suite à mon message du {date_contact_str}.

Je suis toujours en recherche d'un CDI développeur sur Strasbourg et reste intéressé par {cand['entreprise']}. Est-ce que vous avez des besoins en développement en ce moment ?

Je peux vous transmettre mon CV avec plaisir.

Bien cordialement,
Nedjmeddine Djilly"""
        return msg

    # Message de clôture pour silence > 60 jours après entretien
    if has_interview and jours >= 60:
        mois = round(jours / 30)
        date_ent = format_date_fr(last_interview["date"])
        msg = f"""{salut}

Je me permets de revenir vers vous une dernière fois suite à notre entretien du {date_ent}.

Sans retour de votre part depuis {mois} mois environ, je comprends que le poste {"de " + cand["poste"] + " " if cand["poste"] else ""}a probablement été pourvu ou que le projet a évolué.

Pourriez-vous me confirmer la situation ? Un simple retour me permettrait de clore ce process de mon côté.

Merci d'avance et bonne continuation.

Bien cordialement,
Nedjmeddine Djilly"""

    elif has_interview:
        date_ent = format_date_fr(last_interview["date"])
        msg = f"""{salut}

Je me permets de revenir vers vous suite à notre échange du {date_ent}.

Sans nouvelles de votre côté, je souhaitais savoir où en était le processus de recrutement pour le poste {"de " + cand["poste"] if cand["poste"] else ""}.

Je reste très intéressé par l'opportunité et disponible pour toute information complémentaire si besoin.

Bien cordialement,
Nedjmeddine Djilly"""

    else:
        date_cand_str = format_date_fr(cand["date_cand"]) if cand["date_cand"] else "il y a quelques semaines"
        msg = f"""{salut}

Je me permets de revenir vers vous concernant ma candidature au poste {"de " + cand["poste"] if cand["poste"] else "de développeur"} envoyée le {date_cand_str}.

N'ayant pas eu de retour, je souhaitais m'assurer que mon dossier vous est bien parvenu et savoir si vous aviez besoin d'éléments complémentaires de ma part.

Je reste vivement intéressé par un échange.

Bien cordialement,
Nedjmeddine Djilly"""

    return msg


def construire_relances(cands, ents):
    """Retourne la liste triée des relances : (urgence, jours, cand, ents_cand, msg)."""
    actifs = [c for c in cands if c["statut"] in STATUTS_ACTIFS]

    relances = []
    for c in actifs:
        last = derniere_interaction(c, ents)
        if last is None:
            continue
        jours = days_since(last)
        has_interview = a_entretien_passe(c, ents)

        if has_interview and jours >= 10:
            urgence = "CRITIQUE"
        elif c["statut"] == "1er contact" and jours >= 7:
            urgence = "STANDARD"
        elif c["contact"] and jours >= 7:
            urgence = "IMPORTANTE"
        else:
            continue

        ents_cand = [e for e in ents if e["entreprise"].strip().lower() == c["entreprise"].strip().lower()]
        msg = generer_message(c, ents_cand, jours)
        relances.append((urgence, jours, c, ents_cand, msg))

    ordre = {"CRITIQUE": 0, "IMPORTANTE": 1, "STANDARD": 2}  # noqa: E501
    relances.sort(key=lambda x: (ordre[x[0]], -x[1]))
    return relances


def afficher_relances(relances):
    """Affiche les relances dans le terminal."""
    print("=" * 70)
    print("  MESSAGES DE RELANCE À ENVOYER")
    print("=" * 70)
    print()

    if not relances:
        print("✅ Aucune relance à faire cette semaine.")
        return

    for i, (urgence, jours, c, ents_cand, msg) in enumerate(relances, 1):
        canal = "Email" if c["contact"] else "LinkedIn / email RH"
        print(f"┌{'─' * 68}┐")
        print(f"│ RELANCE #{i} — [{urgence}]  {c['entreprise']}")
        print(f"│ Contact : {c['contact'] or '(aucun)'}")
        print(f"│ Silence : {jours}j  |  Canal suggéré : {canal}")
        if urgence == "CRITIQUE" and jours >= 60:
            print(f"│ ⚠️  MESSAGE DE CLÔTURE (silence > 60j)")
        print(f"└{'─' * 68}┘")
        print()
        print(msg)
        print()
        print()


def exporter_markdown(relances):
    """Génère exports/relances_YYYY-MM-DD.md et retourne le chemin."""
    exports = ensure_exports_dir()
    nom_fichier = exports / f"relances_{date.today().isoformat()}.md"

    lines = [f"# Relances — {date.today().strftime('%d/%m/%Y')}\n"]

    if not relances:
        lines.append("✅ Aucune relance à faire cette semaine.\n")
    else:
        for i, (urgence, jours, c, ents_cand, msg) in enumerate(relances, 1):
            canal = "Email" if c["contact"] else "LinkedIn / email RH"
            cloture = urgence == "CRITIQUE" and jours >= 60
            tag = " — ⚠️ MESSAGE DE CLÔTURE" if cloture else ""
            lines.append(f"## Relance #{i} — [{urgence}] {c['entreprise']}{tag}\n")
            lines.append(f"- **Contact :** {c['contact'] or '(aucun)'}")
            lines.append(f"- **Silence :** {jours} jours")
            lines.append(f"- **Canal :** {canal}\n")
            lines.append("**Message :**\n")
            lines.append("```")
            lines.append(msg)
            lines.append("```\n")
            lines.append("---\n")

    nom_fichier.write_text("\n".join(lines), encoding="utf-8")
    return nom_fichier


def main():
    cands = load_candidatures()
    ents = load_entretiens()

    relances = construire_relances(cands, ents)

    # Affichage terminal (comportement inchangé)
    afficher_relances(relances)

    # Export Markdown
    chemin = exporter_markdown(relances)
    print(f"📄 Export : {chemin}")


if __name__ == "__main__":
    main()

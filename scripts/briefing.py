#!/usr/bin/env python3
"""
/briefing — Génère le briefing hebdomadaire.

Affiche :
- État du pipeline (actifs, priorités)
- Relances prioritaires de la semaine
- Candidatures "mortes" à archiver
- Actions concrètes proposées

Génère aussi exports/briefing_YYYY-MM-DD.md.
"""
from lib_excel import (
    load_candidatures, load_entretiens, days_since,
    a_entretien_passe, derniere_interaction, format_date_fr,
    STATUTS_ACTIFS, ensure_exports_dir
)
from datetime import date
import io


def construire_briefing(cands, ents):
    """Retourne le texte du briefing sous forme de chaîne."""
    buf = io.StringIO()

    def p(*args, **kwargs):
        print(*args, **kwargs, file=buf)

    actifs = [c for c in cands if c["statut"] in STATUTS_ACTIFS]
    archives = [c for c in cands if c["statut"] not in STATUTS_ACTIFS]

    p("=" * 70)
    p(f"  BRIEFING HEBDO — {date.today().strftime('%A %d %B %Y')}")
    p("=" * 70)
    p()

    # === État du pipeline ===
    p("📊 PIPELINE")
    p(f"   Total candidatures : {len(cands)}")
    p(f"   Process actifs     : {len(actifs)}")
    p(f"     ├─ Priorité Haute  : {sum(1 for c in actifs if c['priorite'] == 'Haute')}")
    p(f"     ├─ Priorité Moyenne: {sum(1 for c in actifs if c['priorite'] == 'Moyenne')}")
    p(f"     └─ Priorité Basse  : {sum(1 for c in actifs if c['priorite'] == 'Basse')}")
    p(f"   Archivés           : {len(archives)}")
    p(f"   Entretiens passés  : {len(ents)}")
    p()

    # === Relances prioritaires ===
    p("🔔 RELANCES À FAIRE CETTE SEMAINE")
    p("-" * 70)

    relances = []
    for c in actifs:
        last = derniere_interaction(c, ents)
        if last is None:
            continue
        jours = days_since(last)
        has_interview = a_entretien_passe(c, ents)

        urgence = None
        if has_interview and jours >= 10:
            urgence = ("CRITIQUE", "Entretien passé, silence radio")
        elif c["contact"] and jours >= 7:
            urgence = ("IMPORTANTE", "Contact nominatif sans réponse")
        elif jours >= 7:
            urgence = ("STANDARD", "Candidature sans retour")

        if urgence:
            relances.append((urgence[0], jours, c, urgence[1], has_interview))

    ordre = {"CRITIQUE": 0, "IMPORTANTE": 1, "STANDARD": 2}
    relances.sort(key=lambda x: (ordre[x[0]], -x[1]))

    if not relances:
        p("   ✅ Aucune relance urgente.")
    else:
        for urgence, jours, c, raison, has_int in relances[:8]:
            icon = "🔴" if urgence == "CRITIQUE" else ("🟡" if urgence == "IMPORTANTE" else "⚪")
            p(f"\n   {icon} [{urgence}] {c['entreprise']}  ({jours}j sans contact)")
            p(f"      Poste    : {c['poste'] or '(non précisé)'}")
            p(f"      Contact  : {c['contact'] or '(aucun — difficile à relancer)'}")
            p(f"      Statut   : {c['statut']}")
            p(f"      Raison   : {raison}")
            if c["commentaires"]:
                com = c["commentaires"][:150] + ("..." if len(c["commentaires"]) > 150 else "")
                p(f"      Contexte : {com}")
    p()

    # === Candidatures mortes à archiver ===
    p("🪦 CANDIDATURES À ARCHIVER (> 21 jours sans réponse)")
    p("-" * 70)
    mortes = []
    for c in actifs:
        last = derniere_interaction(c, ents)
        if last and days_since(last) >= 21 and not a_entretien_passe(c, ents):
            mortes.append((c, days_since(last)))
    mortes.sort(key=lambda x: -x[1])

    if not mortes:
        p("   ✅ Aucune candidature morte à ce jour.")
    else:
        for c, jours in mortes:
            p(f"   • {c['entreprise']} — {jours}j de silence")
            p(f"     → Suggérer de passer en 'Pas de réponse'")
    p()

    # === Actions proposées ===
    p("🎯 PLAN DE LA SEMAINE — 5 ACTIONS CONCRÈTES")
    p("-" * 70)

    actions = []
    for urgence, jours, c, raison, has_int in relances[:3]:
        if has_int:
            actions.append(
                f"Relancer {c['entreprise']} ({c['contact']}) — entretien passé il y a {jours}j, demander retour de process"
            )
        else:
            actions.append(
                f"Relancer {c['entreprise']} ({c['contact'] or 'RH générique'}) — {jours}j sans retour"
            )

    if mortes:
        nb = len(mortes)
        actions.append(f"Archiver {nb} candidature(s) morte(s) : {', '.join(c['entreprise'] for c, _ in mortes[:3])}")

    contacts_sans_date = [c for c in actifs if c["contact"] and not c["date_cand"]]
    if contacts_sans_date:
        actions.append(
            f"Compléter les dates manquantes pour : {', '.join(c['entreprise'] for c in contacts_sans_date[:3])}"
        )

    if len(actions) < 5:
        actions.append("Identifier 2-3 nouvelles boîtes Strasbourg avec contact identifié (pas d'Easy Apply)")
    if len(actions) < 5:
        actions.append("Préparer debrief des 7 entretiens passés : qu'est-ce qui a bloqué ? patterns à identifier ?")

    for i, a in enumerate(actions[:5], 1):
        p(f"   {i}. {a}")
    p()

    # === Objectifs chiffrés ===
    p("📌 OBJECTIFS CHIFFRÉS DE LA SEMAINE")
    p("-" * 70)
    p("   • 5 candidatures CIBLÉES (avec contact identifié, stack matchée)")
    p("   • 5 relances envoyées (voir liste ci-dessus)")
    p("   • 0 candidatures Easy Apply HelloWork sans ciblage")
    p("   • Mise à jour de l'Excel au fil de l'eau (pas rétroactif)")
    p()
    p("=" * 70)
    p("💡 Lance `python scripts/relances.py` pour voir les messages de relance")
    p("   suggérés pour chaque contact.")
    p("=" * 70)

    return buf.getvalue()


def briefing_vers_markdown(texte):
    """Convertit le texte terminal en Markdown propre pour VS Code preview."""
    lines = texte.splitlines()
    md = []
    md.append(f"# Briefing hebdo — {date.today().strftime('%d/%m/%Y')}\n")
    for line in lines:
        stripped = line.strip()
        # Titres de section (lignes avec emojis en début)
        if stripped.startswith(("📊", "🔔", "🪦", "🎯", "📌")):
            md.append(f"\n## {stripped}\n")
        elif stripped.startswith("=" * 10) or stripped.startswith("-" * 10):
            continue
        elif stripped.startswith(("🔴", "🟡", "⚪")):
            md.append(f"\n### {stripped}\n")
        elif stripped.startswith(("Poste", "Contact", "Statut", "Raison", "Contexte")):
            md.append(f"- **{stripped}**")
        elif stripped.startswith("•"):
            md.append(f"- {stripped[1:].strip()}")
        elif stripped and stripped[0].isdigit() and stripped[1] == ".":
            md.append(f"{stripped}")
        elif stripped.startswith("💡"):
            md.append(f"\n> {stripped}\n")
        elif stripped:
            md.append(stripped)
    return "\n".join(md)


def main():
    cands = load_candidatures()
    ents = load_entretiens()

    texte = construire_briefing(cands, ents)

    # Affichage terminal (comportement inchangé)
    print(texte)

    # Export Markdown
    exports = ensure_exports_dir()
    nom_fichier = exports / f"briefing_{date.today().isoformat()}.md"
    nom_fichier.write_text(briefing_vers_markdown(texte), encoding="utf-8")
    print(f"\n📄 Export : {nom_fichier}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
/daily — Applique les updates parsés par Claude et génère l'export quotidien.

Usage :
    python daily.py <fichier_daily.json>

Format JSON attendu :
{
  "date": "2026-04-19",
  "emails_analyses": 8,
  "updates": [
    {
      "entreprise": "CELAD",
      "statut": "Refus",
      "commentaire": "Refus reçu par email du 16/04",
      "contact": null,
      "date_contact": "2026-04-16",
      "action": "✅ statut → Refus"
    },
    {
      "entreprise": "SII",
      "statut": null,
      "commentaire": "Morgane HICARD propose entretien manager semaine prochaine",
      "contact": "Morgane HICARD",
      "date_contact": "2026-04-18",
      "action": "✅ nouveau contact + commentaire"
    }
  ],
  "ignores": [
    "Accusé réception Hellowork (AddixWare) → ignoré"
  ],
  "offres": [
    {
      "entreprise": "Acme Corp",
      "poste": "Développeur Full Stack",
      "localisation": "Strasbourg (67)",
      "contrat": "CDI",
      "stack": ["Node.js", "Angular"],
      "contact": "Jean Dupont",
      "url": "https://...",
      "description": "...",
      "source": "LinkedIn"
    }
  ]
}

Génère exports/daily_YYYY-MM-DD.md.
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_excel import update_programmatic, ensure_exports_dir, parse_date
from opportunites import traiter_offres, exporter_markdown as exporter_md_opportunites
from relances import construire_relances, load_candidatures, load_entretiens
from offres_store import ajouter_offres
from linkedin_store import ajouter_connexions
from actions_store import ajouter_actions
from evenements_store import ajouter as ajouter_evenements
from informations_store import ajouter_informations


def appliquer_updates(updates: list[dict]) -> list[dict]:
    """Applique chaque update à l'Excel. Retourne la liste avec statut d'application."""
    resultats = []
    for u in updates:
        entreprise = u.get("entreprise", "").strip()
        if not entreprise:
            continue

        # Convertir date_contact string → date Python
        date_contact = None
        if u.get("date_contact"):
            date_contact = parse_date(u["date_contact"])

        ok, msg = update_programmatic(
            entreprise_or_id=entreprise,
            statut=u.get("statut") or None,
            commentaire=u.get("commentaire") or None,
            contact=u.get("contact") or None,
            date_contact=date_contact,
        )
        resultats.append({**u, "_ok": ok, "_msg": msg})

    return resultats


def generer_export_daily(
    date_str: str,
    emails_analyses: int,
    updates_resultats: list[dict],
    ignores: list[str],
    resultats_offres: dict,
    relances_critiques: list,
) -> str:
    """Génère le contenu Markdown du rapport daily."""
    lines = []
    today_fmt = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y") if date_str else date.today().strftime("%d/%m/%Y")
    lines.append(f"# Daily — {today_fmt}\n")

    # ── Stats rapides ──────────────────────────────────────────────────────────
    cands = load_candidatures()
    from lib_excel import STATUTS_ACTIFS
    actifs = sum(1 for c in cands if c["statut"] in STATUTS_ACTIFS)
    updates_ok = sum(1 for u in updates_resultats if u.get("_ok"))
    nb_offres = len(resultats_offres.get("top", []))

    lines.append("## 📊 Résumé\n")
    lines.append(f"| | |")
    lines.append(f"|---|---|")
    lines.append(f"| Emails analysés | {emails_analyses} |")
    lines.append(f"| Updates Excel | {updates_ok} |")
    lines.append(f"| Offres qualifiées | {nb_offres} (score ≥ 40/100) |")
    lines.append(f"| Pipeline actif | {actifs} candidatures |")
    lines.append(f"| Relances critiques | {len(relances_critiques)} |\n")

    # ── Updates effectués ──────────────────────────────────────────────────────
    lines.append("## 📧 Emails parsés — Updates\n")
    if updates_resultats:
        for u in updates_resultats:
            icon = "✅" if u.get("_ok") else "❌"
            action = u.get("action", u.get("_msg", ""))
            lines.append(f"- {icon} **{u['entreprise']}** → {action}")
    else:
        lines.append("- Aucun update effectué.")
    lines.append("")

    if ignores:
        lines.append("**Ignorés (bruit) :**\n")
        for ig in ignores:
            lines.append(f"- ⏭️ {ig}")
        lines.append("")

    # ── Opportunités ──────────────────────────────────────────────────────────
    lines.append("## 🎯 Opportunités qualifiées\n")
    top = resultats_offres.get("top", [])
    if not top:
        lines.append("Aucune offre ne passe le seuil de 40/100.\n")
    else:
        from opportunites import STACK_FORTE, STACK_PROCHE, formater_checklist
        for o in top:
            d = o["detail_score"]
            stack_matches = [t for t in o.get("stack", []) if t.strip().lower() in STACK_FORTE]
            stack_proche = [t for t in o.get("stack", []) if t.strip().lower() in STACK_PROCHE]
            stack_str = ", ".join(stack_matches)
            if stack_proche:
                stack_str += f" + {', '.join(stack_proche)} (proches)"
            lines.append(f"### 🎯 [{o['score']}/100] {o['entreprise']} — {o.get('poste', '?')}\n")
            lines.append(f"- **Localisation :** {o.get('localisation', '?')} | **Contrat :** {o.get('contrat', '?')}")
            if stack_str:
                lines.append(f"- **Stack match :** {stack_str}")
            if o.get("contact"):
                lines.append(f"- **Contact :** {o['contact']}")
            if o.get("url"):
                lines.append(f"- **Lien :** {o['url']}")
            lines.append(f"- **Score :** Stack {d['stack']}/50 | Loc {d['localisation']}/30 | Contrat {d['contrat']}/10 | Qualité {d['qualite']}/10\n")
            lines.append("**⚠️ À faire avant de postuler :**\n")
            for item in formater_checklist(o):
                lines.append(f"- [ ] {item}")
            lines.append("\n---\n")

    # ── Relances critiques ─────────────────────────────────────────────────────
    lines.append("## 🔴 Relances critiques du jour\n")
    if not relances_critiques:
        lines.append("✅ Aucune relance critique.\n")
    else:
        for urgence, jours, c, ents_cand, msg in relances_critiques[:3]:
            cloture = jours >= 60
            tag = " ⚠️ CLÔTURE" if cloture else ""
            lines.append(f"### {c['entreprise']} — {jours}j de silence{tag}\n")
            lines.append("```")
            lines.append(msg)
            lines.append("```\n")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage : python daily.py <fichier_daily.json>", file=sys.stderr)
        sys.exit(1)

    fichier = Path(sys.argv[1])
    if not fichier.exists():
        print(f"❌ Fichier introuvable : {fichier}", file=sys.stderr)
        sys.exit(1)

    with open(fichier, encoding="utf-8-sig") as f:
        data = json.load(f)

    today = data.get("date", date.today().isoformat())
    emails_analyses = data.get("emails_analyses", 0)
    updates_bruts = data.get("updates", [])
    ignores = data.get("ignores", [])
    offres_brutes = data.get("offres", [])
    connexions_brutes = data.get("connexions", [])
    actions_brutes = data.get("actions", [])
    evenements_bruts = data.get("evenements", [])
    informations_brutes = data.get("informations", [])

    # 1. Appliquer les updates Excel
    print("📝 Application des updates...")
    updates_resultats = appliquer_updates(updates_bruts)
    for u in updates_resultats:
        icon = "✅" if u.get("_ok") else "❌"
        print(f"   {icon} {u['_msg']}")

    # 2. Sauvegarder les connexions LinkedIn
    if connexions_brutes:
        print("\n🔗 Connexions LinkedIn...")
        res_cx = ajouter_connexions(connexions_brutes)
        print(f"   {res_cx['ajoutes']} nouvelle(s) connexion(s) | {res_cx['doublons']} doublon(s)")

    # 3. Scorer les offres
    print("\n🎯 Scoring des offres...")
    resultats_offres = traiter_offres(offres_brutes)
    top = resultats_offres["top"]
    print(f"   {len(top)} offre(s) qualifiée(s) sur {resultats_offres['total_brut']} analysée(s)")

    # Alimenter le store persistant (affiché dans l'interface web)
    if top:
        res_store = ajouter_offres(top)
        print(f"   → Store web : {res_store['ajoutees']} nouvelle(s) offre(s) ajoutée(s), {res_store['doublons']} doublon(s) ignoré(s)")

    # 4. Sauvegarder les actions du jour
    if actions_brutes:
        res_actions = ajouter_actions(actions_brutes, today)
        print(f"\n⚡ Actions du jour : {res_actions['ajoutes']} action(s) enregistrée(s)")

    # 4b. Sauvegarder les événements futurs détectés
    if evenements_bruts:
        res_evts = ajouter_evenements(evenements_bruts)
        print(f"\n📅 Événements agenda : {res_evts['ajoutes']} ajouté(s), {res_evts['doublons']} doublon(s)")

    # 4c. Sauvegarder les informations du jour (cumulées jusqu'à "Lu")
    if informations_brutes:
        res_infos = ajouter_informations(informations_brutes, today)
        print(f"\nℹ️  Informations : {res_infos['ajoutes']} ajoutée(s), {res_infos['non_lus']} non lue(s) au total")

    # 5. Top 3 relances critiques
    cands = load_candidatures()
    ents = load_entretiens()
    from relances import construire_relances
    toutes_relances = construire_relances(cands, ents)
    relances_critiques = [(urg, j, c, ec, m) for urg, j, c, ec, m in toutes_relances if urg == "CRITIQUE"]

    # 5. Générer et écrire l'export
    exports = ensure_exports_dir()
    chemin = exports / f"daily_{today}.md"
    contenu = generer_export_daily(
        today, emails_analyses, updates_resultats, ignores,
        resultats_offres, relances_critiques
    )
    chemin.write_text(contenu, encoding="utf-8")

    # 5. Résumé terminal
    print(f"\n{'=' * 70}")
    updates_ok = sum(1 for u in updates_resultats if u.get("_ok"))
    print(f"📊 Pipeline : {sum(1 for c in cands if c['statut'] in __import__('lib_excel').STATUTS_ACTIFS)} actifs | {len(relances_critiques)} relances critiques aujourd'hui")
    print(f"🎯 {len(top)} opportunité(s) qualifiée(s) (score ≥ 40/100)")
    print(f"📧 {emails_analyses} email(s) analysé(s) | {updates_ok} update(s) Excel effectué(s)")

    ok_updates = [u for u in updates_resultats if u.get("_ok")]
    if ok_updates:
        print("\n📋 Résumé des modifications :")
        for u in ok_updates:
            ligne = f"  • {u['entreprise']}"
            if u.get("statut"):
                ligne += f" → {u['statut']}"
            else:
                ligne += " → commentaire ajouté"
            if u.get("date_contact"):
                try:
                    d = datetime.strptime(str(u["date_contact"]), "%Y-%m-%d").strftime("%d/%m")
                    ligne += f" ({d})"
                except Exception:
                    pass
            print(ligne)

    print(f"\n📄 Export : {chemin}")


if __name__ == "__main__":
    main()

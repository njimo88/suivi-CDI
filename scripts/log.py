#!/usr/bin/env python3
"""
/log — Applique les entrées de journal parsées par Claude et génère le log quotidien.

Usage :
    python log.py <fichier_log.json>

Format JSON attendu :
{
  "date": "2026-04-19",
  "texte_original": "J'ai relancé SII et Stork ce matin...",
  "entrees": [
    {
      "entreprise": "SII",
      "action": "relance",
      "statut": null,
      "commentaire": "Relance email envoyée",
      "contact": null,
      "date_contact": "2026-04-19",
      "label": "📌 SII : statut maintenu, ajout commentaire [19/04] Relance email envoyée"
    },
    {
      "entreprise": "Amaris Consulting",
      "action": "candidature",
      "statut": "En cours",
      "commentaire": "Nouvelle candidature envoyée via Hamza Ben Ghirat",
      "contact": "Hamza Ben Ghirat",
      "date_contact": "2026-04-19",
      "label": "📌 Amaris Consulting : commentaire ajouté [19/04] Candidature via Hamza"
    },
    {
      "entreprise": "moOngy",
      "action": "refus",
      "statut": "Refus",
      "commentaire": "Refus reçu par email",
      "contact": null,
      "date_contact": "2026-04-19",
      "label": "📌 moOngy : statut → Refus"
    }
  ]
}

Génère/appende à exports/log_YYYY-MM-DD.md.
"""
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_excel import update_programmatic, ensure_exports_dir, parse_date


def appliquer_entrees(entrees: list[dict]) -> list[dict]:
    """Applique chaque entrée de log à l'Excel. Retourne les entrées enrichies."""
    resultats = []
    for e in entrees:
        entreprise = e.get("entreprise", "").strip()
        if not entreprise:
            continue

        date_contact = parse_date(e.get("date_contact")) if e.get("date_contact") else None

        ok, msg = update_programmatic(
            entreprise_or_id=entreprise,
            statut=e.get("statut") or None,
            commentaire=e.get("commentaire") or None,
            contact=e.get("contact") or None,
            date_contact=date_contact,
        )
        resultats.append({**e, "_ok": ok, "_msg": msg})

    return resultats


def exporter_log(date_str: str, texte_original: str, entrees_resultats: list[dict]) -> Path:
    """Appende l'entrée du jour à exports/log_YYYY-MM-DD.md."""
    exports = ensure_exports_dir()
    chemin = exports / f"log_{date_str}.md"

    today_fmt = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")

    # Construire le bloc à ajouter
    bloc = []
    bloc.append(f"## Journal du {today_fmt}\n")
    bloc.append(f"**Saisie libre :**\n> {texte_original}\n")
    bloc.append("**Updates appliqués :**\n")

    for e in entrees_resultats:
        icon = "✅" if e.get("_ok") else "❌"
        label = e.get("label", e.get("_msg", ""))
        bloc.append(f"- {icon} {label}")
    bloc.append("")
    bloc.append("---\n")

    # Append si le fichier existe déjà (plusieurs entrées dans la journée)
    contenu_existant = ""
    if chemin.exists():
        contenu_existant = chemin.read_text(encoding="utf-8")

    if not contenu_existant:
        header = f"# Log quotidien — {today_fmt}\n\n"
        contenu_existant = header

    nouveau_contenu = contenu_existant + "\n".join(bloc)
    chemin.write_text(nouveau_contenu, encoding="utf-8")
    return chemin


def main():
    if len(sys.argv) < 2:
        print("Usage : python log.py <fichier_log.json>", file=sys.stderr)
        sys.exit(1)

    fichier = Path(sys.argv[1])
    if not fichier.exists():
        print(f"❌ Fichier introuvable : {fichier}", file=sys.stderr)
        sys.exit(1)

    with open(fichier, encoding="utf-8") as f:
        data = json.load(f)

    today = data.get("date", date.today().isoformat())
    texte_original = data.get("texte_original", "")
    entrees = data.get("entrees", [])

    print("📝 Application des entrées de log...")
    entrees_resultats = appliquer_entrees(entrees)

    for e in entrees_resultats:
        icon = "✅" if e.get("_ok") else "❌"
        label = e.get("label", e.get("_msg", ""))
        print(f"   {icon} {label}")

    if not entrees_resultats:
        print("   (aucune entrée à appliquer)")

    chemin = exporter_log(today, texte_original, entrees_resultats)
    ok_count = sum(1 for e in entrees_resultats if e.get("_ok"))
    print(f"\n✅ {ok_count} update(s) appliqué(s) sur {len(entrees_resultats)}")

    ok_entries = [e for e in entrees_resultats if e.get("_ok")]
    if ok_entries:
        print("\n📋 Résumé des modifications :")
        for e in ok_entries:
            ligne = f"  • {e['entreprise']}"
            if e.get("statut"):
                ligne += f" → {e['statut']}"
            else:
                ligne += " → commentaire ajouté"
            if e.get("date_contact"):
                try:
                    from datetime import datetime as _dt
                    d = _dt.strptime(e["date_contact"], "%Y-%m-%d").strftime("%d/%m")
                    ligne += f" ({d})"
                except Exception:
                    pass
            print(ligne)

    print(f"\n📄 Export : {chemin}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
/ajouter — Ajoute une nouvelle candidature dans le suivi.

Usage :
    python ajouter.py

Mode interactif : demande les infos une par une.
Vérifie les doublons avant d'ajouter.
"""
from lib_excel import (
    EXCEL_PATH, load_candidatures, entreprise_existe,
    calculer_priorite, appliquer_style_ligne
)
from openpyxl import load_workbook
from datetime import date
import sys


def ask(prompt, obligatoire=False, default=None):
    """Demande une saisie utilisateur."""
    suffix = f" [{default}]" if default else ""
    req = " *" if obligatoire else ""
    while True:
        val = input(f"  {prompt}{suffix}{req} : ").strip()
        if not val and default is not None:
            return default
        if val or not obligatoire:
            return val
        print("    ⚠ Champ obligatoire.")


def main():
    print("=" * 70)
    print("  AJOUTER UNE CANDIDATURE")
    print("=" * 70)
    print()

    entreprise = ask("Entreprise", obligatoire=True)

    # Anti-doublon
    existant = entreprise_existe(entreprise)
    if existant:
        print()
        print(f"⚠ ATTENTION : '{existant['entreprise']}' existe déjà dans le suivi.")
        print(f"   ID {existant['id']} | Statut : {existant['statut']} | Date : {existant['date_cand']}")
        print(f"   Commentaires : {existant['commentaires'][:100]}")
        print()
        choix = input("  Continuer quand même (nouveau poste dans cette boîte) ? [y/N] : ").strip().lower()
        if choix != "y":
            print("  ❌ Ajout annulé.")
            sys.exit(0)

    print()
    poste = ask("Poste")
    localisation = ask("Localisation", default="Strasbourg (67)")
    type_poste = ask("Type poste (Sur site / Hybride / Full remote)", default="Hybride")
    date_cand_str = ask("Date candidature (YYYY-MM-DD)", default=date.today().isoformat())
    contact = ask("Contact / RH (nom ou email)")
    source = ask("Source (LinkedIn / WTTJ / Réseau / Email direct / ...)", default="LinkedIn")
    stack = ask("Stack technique")
    commentaires = ask("Commentaires / contexte")

    statut = "En cours"
    priorite = calculer_priorite(contact, statut)

    print()
    print(f"  → Priorité calculée : {priorite}")
    print()

    # Écriture Excel
    wb = load_workbook(EXCEL_PATH)
    ws = wb["Candidatures"]

    # Trouver la prochaine ligne vide
    next_row = ws.max_row + 1
    existing_cands = load_candidatures()
    next_id = max((c["id"] for c in existing_cands if isinstance(c["id"], int)), default=0) + 1

    row_data = [
        next_id, entreprise, poste, localisation, type_poste,
        date_cand_str, statut, date_cand_str, "", "",
        contact, source, stack, priorite, commentaires
    ]

    for col_idx, value in enumerate(row_data, 1):
        ws.cell(row=next_row, column=col_idx, value=value)

    appliquer_style_ligne(ws, next_row, statut)
    wb.save(EXCEL_PATH)

    print(f"✅ Candidature #{next_id} ajoutée : {entreprise}")
    print(f"   Statut : {statut} | Priorité : {priorite}")


if __name__ == "__main__":
    main()

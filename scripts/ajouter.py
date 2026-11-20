#!/usr/bin/env python3
"""
/ajouter — Ajoute une nouvelle candidature dans le suivi.

Usage :
    python ajouter.py

Mode interactif : demande les infos une par une.
Vérifie les doublons avant d'ajouter.
"""
from lib_excel import (
    load_candidatures, entreprise_existe,
    calculer_priorite, ajouter_programmatic
)
from datetime import date
import sys


def ask(prompt, obligatoire=False, default=None):
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

    existant = entreprise_existe(entreprise)
    if existant:
        print()
        print(f"⚠ ATTENTION : '{existant['entreprise']}' existe déjà dans le suivi.")
        print(f"   ID {existant['id']} | Statut : {existant['statut']} | Date : {existant['date_cand']}")
        print(f"   Commentaires : {str(existant['commentaires'])[:100]}")
        print()
        choix = input("  Continuer quand même (nouveau poste dans cette boîte) ? [y/N] : ").strip().lower()
        if choix != "y":
            print("  ❌ Ajout annulé.")
            sys.exit(0)

    print()
    poste = ask("Poste")
    localisation = ask("Localisation", default="Strasbourg (67)")
    type_poste = ask("Type poste (Sur site / Hybride / Full remote)", default="Hybride")
    contact = ask("Contact / RH (nom ou email)")
    source = ask("Source (LinkedIn / WTTJ / Réseau / Email direct / ...)", default="LinkedIn")
    stack = ask("Stack technique")
    commentaires = ask("Commentaires / contexte")

    ok, msg, new_id = ajouter_programmatic(
        entreprise=entreprise,
        poste=poste,
        localisation=localisation,
        type_poste=type_poste,
        contact=contact,
        source=source,
        stack=stack,
        commentaires=commentaires,
    )

    print()
    if ok:
        print(f"✅ {msg}")
    else:
        print(f"❌ {msg}")
        sys.exit(1)


if __name__ == "__main__":
    main()

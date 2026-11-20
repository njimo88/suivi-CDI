#!/usr/bin/env python3
"""
/update — Met à jour une candidature existante.

Usage :
    python update.py

Modes :
- Modifier statut
- Ajouter un entretien passé
- Mettre à jour date dernier contact + commentaires
"""
from lib_excel import (
    load_candidatures, load_entretiens,
    calculer_priorite, STATUTS_ACTIFS, update_programmatic
)
from lib_db import init_db, ajouter_entretien
from datetime import date
import sys


STATUTS = ["En cours", "Entretien prévu", "Offre", "Refus", "Pas de réponse", "Pas d'opportunités", "Abandonnée"]


def chercher_candidature(cands, recherche):
    try:
        id_num = int(recherche)
        for c in cands:
            if c["id"] == id_num:
                return c
    except ValueError:
        pass

    rec_low = recherche.lower()
    matches = [c for c in cands if rec_low in c["entreprise"].lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"\nPlusieurs correspondances trouvées :")
        for i, c in enumerate(matches, 1):
            print(f"   {i}. [{c['id']}] {c['entreprise']} — {c['statut']}")
        choix = input("  Numéro : ").strip()
        try:
            return matches[int(choix) - 1]
        except (ValueError, IndexError):
            return None
    return None


def main():
    print("=" * 70)
    print("  METTRE À JOUR UNE CANDIDATURE")
    print("=" * 70)
    print()

    init_db()
    cands = load_candidatures()
    recherche = input("  Entreprise (nom ou ID) : ").strip()
    cand = chercher_candidature(cands, recherche)

    if not cand:
        print(f"❌ Aucune candidature trouvée pour '{recherche}'")
        sys.exit(1)

    print()
    print(f"📌 {cand['entreprise']} [ID {cand['id']}]")
    print(f"   Statut actuel  : {cand['statut']}")
    print(f"   Dernier contact: {cand['date_contact']}")
    print(f"   Contact        : {cand['contact'] or '(aucun)'}")
    print(f"   Commentaires   : {str(cand['commentaires'])[:100]}")
    print()

    print("Nouveau statut ? (laisser vide pour garder)")
    for i, s in enumerate(STATUTS, 1):
        marker = " ← actuel" if s == cand["statut"] else ""
        print(f"   {i}. {s}{marker}")
    choix = input("  Numéro (ou Entrée pour garder) : ").strip()

    nouveau_statut = cand["statut"]
    if choix:
        try:
            nouveau_statut = STATUTS[int(choix) - 1]
        except (ValueError, IndexError):
            print("  ⚠ Choix invalide, statut inchangé.")

    print()
    ajout_commentaire = input("  Ajouter un commentaire (sera préfixé par la date) : ").strip()
    nouveau_contact = input(f"  Mettre à jour contact [{cand['contact']}] : ").strip()

    contact_final = nouveau_contact or cand.get("contact", "")

    ok, msg = update_programmatic(
        entreprise_or_id=cand["id"],
        statut=nouveau_statut,
        commentaire=ajout_commentaire or None,
        contact=contact_final or None,
        date_contact=date.today(),
    )

    print()
    if ok:
        print(f"✅ {msg}")
        priorite_finale = calculer_priorite(contact_final, nouveau_statut)
        print(f"   Priorité : {priorite_finale}")
    else:
        print(f"❌ {msg}")
        sys.exit(1)

    # Proposer d'ajouter dans la feuille Entretiens si pertinent
    if nouveau_statut in ("En cours", "Entretien prévu") and ajout_commentaire and \
            ("entretien" in ajout_commentaire.lower() or "rdv" in ajout_commentaire.lower()):
        print()
        print("💡 Tu mentionnes un entretien dans ton commentaire.")
        ajt = input("   Ajouter une entrée dans la feuille Entretiens ? [y/N] : ").strip().lower()
        if ajt == "y":
            type_ent = input("   Type (RH / Manager / Technique / Direction) : ").strip()
            interloc = input("   Interlocuteur(s) : ").strip() or contact_final
            format_ent = input("   Format (Visio / Présentiel / Téléphone) : ").strip() or "Visio"

            ajouter_entretien(
                candidature_id=cand["id"],
                entreprise=cand["entreprise"],
                poste=cand.get("poste", ""),
                date_entretien=date.today().isoformat(),
                type_entretien=type_ent,
                interlocuteurs=interloc,
                format_entretien=format_ent,
                notes=ajout_commentaire,
                suite="En attente",
            )
            print(f"   ✅ Entretien ajouté")


if __name__ == "__main__":
    main()

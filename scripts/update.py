#!/usr/bin/env python3
"""
/update — Met à jour une candidature existante.

Usage :
    python update.py

Modes :
- Modifier statut (En cours → Refus / Pas de réponse / Offre / ...)
- Ajouter un entretien passé
- Mettre à jour date dernier contact + commentaires
"""
from lib_excel import (
    EXCEL_PATH, load_candidatures, load_entretiens,
    calculer_priorite, appliquer_style_ligne, STATUTS_ACTIFS, STATUTS_ARCHIVES,
    COL_STATUT, COL_DATE_CONTACT, COL_COMMENTAIRES, COL_PRIORITE, COL_CONTACT
)
from openpyxl import load_workbook
from datetime import date
import sys


STATUTS = ["En cours", "Entretien prévu", "Offre", "Refus", "Pas de réponse", "Pas d'opportunités", "Abandonnée"]


def chercher_candidature(cands, recherche):
    """Trouve une candidature par ID ou nom (partial match)."""
    # Par ID
    try:
        id_num = int(recherche)
        for c in cands:
            if c["id"] == id_num:
                return c
    except ValueError:
        pass

    # Par nom (partial)
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
    print(f"   Commentaires   : {cand['commentaires'][:100]}")
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

    # Construction des nouvelles valeurs
    commentaires_final = cand["commentaires"]
    if ajout_commentaire:
        date_tag = date.today().strftime("%d/%m/%Y")
        nouvelle_ligne = f"[{date_tag}] {ajout_commentaire}"
        commentaires_final = f"{commentaires_final}\n{nouvelle_ligne}" if commentaires_final else nouvelle_ligne

    contact_final = nouveau_contact or cand["contact"]
    priorite_finale = calculer_priorite(contact_final, nouveau_statut)

    # Écriture
    wb = load_workbook(EXCEL_PATH)
    ws = wb["Candidatures"]
    row = cand["row"]

    ws.cell(row=row, column=COL_STATUT, value=nouveau_statut)
    ws.cell(row=row, column=COL_DATE_CONTACT, value=date.today().isoformat())
    ws.cell(row=row, column=COL_COMMENTAIRES, value=commentaires_final)
    ws.cell(row=row, column=COL_PRIORITE, value=priorite_finale)
    if nouveau_contact:
        ws.cell(row=row, column=COL_CONTACT, value=contact_final)

    appliquer_style_ligne(ws, row, nouveau_statut)
    wb.save(EXCEL_PATH)

    print()
    print(f"✅ Mise à jour effectuée")
    print(f"   {cand['entreprise']} : {cand['statut']} → {nouveau_statut}")
    print(f"   Priorité : {priorite_finale}")

    # Si on passe à "Entretien prévu" ou "En cours" après un entretien, proposer d'ajouter dans Entretiens
    if nouveau_statut in ("En cours", "Entretien prévu") and ajout_commentaire and ("entretien" in ajout_commentaire.lower() or "rdv" in ajout_commentaire.lower()):
        print()
        print("💡 Tu mentionnes un entretien dans ton commentaire.")
        ajt = input("   Ajouter une entrée dans la feuille Entretiens ? [y/N] : ").strip().lower()
        if ajt == "y":
            type_ent = input("   Type (RH / Manager / Technique / Direction) : ").strip()
            interloc = input("   Interlocuteur(s) : ").strip() or contact_final
            format_ent = input("   Format (Visio / Présentiel / Téléphone) : ").strip() or "Visio"

            ws_ent = wb["Entretiens"]
            next_row_ent = ws_ent.max_row + 1
            ents_existing = load_entretiens()
            next_id_ent = max((e["row"] - 1 for e in ents_existing), default=0) + 1

            ws_ent.cell(row=next_row_ent, column=1, value=next_id_ent)
            ws_ent.cell(row=next_row_ent, column=2, value=cand["entreprise"])
            ws_ent.cell(row=next_row_ent, column=3, value=cand["poste"])
            ws_ent.cell(row=next_row_ent, column=4, value=date.today().isoformat())
            ws_ent.cell(row=next_row_ent, column=5, value=type_ent)
            ws_ent.cell(row=next_row_ent, column=6, value=interloc)
            ws_ent.cell(row=next_row_ent, column=7, value=format_ent)
            ws_ent.cell(row=next_row_ent, column=8, value=ajout_commentaire)
            ws_ent.cell(row=next_row_ent, column=9, value="En attente")

            wb.save(EXCEL_PATH)
            print(f"   ✅ Entretien ajouté (ID {next_id_ent})")


if __name__ == "__main__":
    main()

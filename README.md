# Suivi CDI — Projet Claude Code

Outil de pilotage de ma recherche CDI développeur. Tracking des candidatures, génération des relances, briefing hebdo.

## 🎯 Philosophie

**Qualité > volume.** Cet outil n'est PAS un scraper ni un automate d'envoi. Il sert à forcer la discipline :
- 5 candidatures ciblées / semaine (pas 50)
- Relances suivies, jamais oubliées
- Anti-doublon strict
- Humain valide toujours avant envoi

## 📦 Installation (Chromebook Linux / Crostini)

### 1. Dépendances Python

```bash
# Vérifier Python
python3 --version  # doit être ≥ 3.9

# Installer les libs
pip install --break-system-packages openpyxl pandas

# Si pip refuse, utiliser un venv :
python3 -m venv venv
source venv/bin/activate
pip install openpyxl pandas
```

### 2. Cloner / copier le projet

Mets tout le dossier `suivi-cdi/` dans ton home Linux, par exemple `~/suivi-cdi/`.

```bash
cd ~/suivi-cdi
ls
# CLAUDE.md  README.md  suivi.xlsx  scripts/  .claude/
```

### 3. Tester

```bash
python3 scripts/briefing.py
```

Si ça affiche le briefing sans erreur, tout est OK.

### 4. Lancer Claude Code

```bash
cd ~/suivi-cdi
claude
```

Une fois dans Claude Code, tu peux utiliser les slash commands :
- `/briefing` — plan de la semaine
- `/relances` — messages de relance à envoyer
- `/ajouter` — nouvelle candidature
- `/update` — mise à jour statut / commentaire / entretien

## 📊 Structure du fichier Excel

`suivi.xlsx` contient 3 feuilles :

### 📋 Candidatures
Colonnes : ID, Entreprise, Poste, Localisation, Type poste, Date candidature, Statut, Date dernier contact, Prochaine action, Date prochaine action, Contact / RH, Source, Stack technique, Priorité, Commentaires

### 🎤 Entretiens
Journal détaillé : date, interlocuteurs, format, questions posées, résultat

### 📊 Dashboard
Stats automatiques (formules Excel) + objectifs hebdo

## 🔄 Workflow recommandé

### Chaque dimanche soir (20 min)
1. `/briefing` — vue d'ensemble + plan de la semaine
2. `/relances` — générer les messages, les valider, les envoyer manuellement
3. Archiver les candidatures mortes (>21j de silence)

### En semaine (au fil de l'eau)
- `/ajouter` quand tu postules
- `/update` quand tu reçois une réponse ou passes un entretien

## 🚫 Ce que cet outil ne fait PAS (et c'est voulu)

- ❌ Envoi automatique d'emails ou messages LinkedIn
- ❌ Scraping de LinkedIn / WTTJ / autres sites (risque ban + RGPD)
- ❌ Easy Apply en masse
- ❌ Candidatures sans contact identifié à la chaîne
- ❌ Chasse de clients pour d'autres projets (KYVA etc.) → pipeline séparé, pas dans cet outil

## 📁 Structure du projet

```
suivi-cdi/
├── CLAUDE.md                  # Philosophie + règles pour Claude
├── README.md                  # Ce fichier
├── suivi.xlsx                 # LE fichier de suivi
├── scripts/
│   ├── lib_excel.py           # Bibliothèque partagée
│   ├── briefing.py            # Briefing hebdo
│   ├── relances.py            # Messages de relance
│   ├── ajouter.py             # Nouvelle candidature
│   └── update.py              # Mise à jour
└── .claude/
    └── commands/              # Slash commands Claude Code
        ├── briefing.md
        ├── relances.md
        ├── ajouter.md
        └── update.md
```

## 💡 Sauvegarde Drive (optionnel)

Sur Chromebook, pour sauvegarder `suivi.xlsx` sur Google Drive :

1. Depuis l'app Files du Chromebook, copie le fichier `~/suivi-cdi/suivi.xlsx` vers `Google Drive/`
2. Ou utilise `rclone` (plus avancé) pour automatiser

Mais honnêtement : le fichier local dans ton home Linux est déjà sauvegardé si tu fais `git init` et `git commit` régulièrement.

## 🛠 Dépannage

### "ModuleNotFoundError: openpyxl"
```bash
pip install --break-system-packages openpyxl pandas
```

### "Permission denied" en écriture Excel
Vérifie que le fichier n'est pas ouvert dans LibreOffice/Excel au moment où le script écrit.

### Les couleurs ne s'affichent pas
Ouvre `suivi.xlsx` avec LibreOffice Calc ou Google Sheets, pas avec un viewer basique.

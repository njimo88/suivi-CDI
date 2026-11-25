---
name: chasse
description: Chasse du jour — lit HelloWork, Welcome to the Jungle et LinkedIn avec playwright-cli dans le Chrome déjà ouvert de Nedjmeddine, trouve 4 entreprises qui recrutent un développeur à Strasbourg et remplit l'onglet « Chasse du jour » de l'app suivi CDI. À lancer chaque jour avec /chasse.
---

# /chasse — 4 entreprises à contacter aujourd'hui

But : chaque jour, proposer **4 entreprises** qui recrutent un développeur à Strasbourg (et environs : Schiltigheim, Illkirch, Lingolsheim, Entzheim…), **de préférence absentes du suivi**, et les afficher dans l'onglet **Chasse du jour** de l'app (http://localhost:5000).

## Règles non négociables

1. **Navigateur : uniquement `playwright-cli` attaché au Chrome déjà ouvert.** Jamais l'extension Claude in Chrome, jamais le navigateur intégré, jamais un nouveau navigateur Playwright. Si l'attache échoue, s'arrêter et le dire (voir étape 1), sans basculer sur un autre outil.
2. **Lecture seule.** Ne rien cliquer qui postule, sauvegarde, suit, envoie ou modifie quoi que ce soit sur les sites. Pas de candidature simplifiée, pas de message.
3. **Une seule page de résultats par site**, pour limiter le risque de blocage du compte LinkedIn connecté.
4. **Ne jamais proposer Crédit Mutuel, Euro-Information ni CIC** (même groupe). `chasse_import.py` les filtre aussi, mais ne les mets pas dans le JSON.
5. Travailler dans **un onglet à soi** : le fermer à la fin et se détacher **sans fermer les onglets de Nedjmeddine**.
6. Commandes Bash : URLs entre **apostrophes simples** (le `&` casse sinon). Pas de `--%` (c'est du PowerShell).

## Étape 1 — S'attacher au Chrome ouvert

```bash
cd "$TEMP" && playwright-cli attach --cdp=chrome --session=chasse
```

- Succès : la sortie dit `Session ... attached to chrome` et liste les onglets ouverts.
- Échec (Chrome fermé ou débogage distant désactivé) : s'arrêter et dire à Nedjmeddine d'ouvrir Chrome (et, si besoin, d'autoriser le débogage distant dans `chrome://inspect/#remote-debugging`), puis de relancer `/chasse`. Ne pas utiliser un autre navigateur.

Ensuite, toutes les commandes utilisent `playwright-cli -s=chasse …`.

## Étape 2 — Ouvrir un onglet et lire les 3 sites

Ouvrir son propre onglet sur HelloWork (CDI, « développeur », Strasbourg, dernière semaine) :

```bash
cd "$TEMP" && playwright-cli -s=chasse tab-new 'https://www.hellowork.com/fr-fr/emploi/recherche.html?k=d%C3%A9veloppeur&l=Strasbourg+67000&c=CDI&d=w'
```

Puis lire chaque page avec le même extracteur de texte (attend 5 s que la page se charge) :

```bash
cd "$TEMP" && playwright-cli -s=chasse --raw eval "new Promise(r=>setTimeout(()=>r((document.querySelector('main')||document.body).innerText.replace(/\s+/g,' ').slice(0,6000)),5000))"
```

Les deux autres sites, dans le **même onglet** (`goto`) :

- **Welcome to the Jungle** : la recherche classique renvoie une page de présentation, il faut lire les matchs du compte (préférences déjà réglées sur Developer / Strasbourg / CDI) :
  ```bash
  cd "$TEMP" && playwright-cli -s=chasse goto 'https://www.welcometothejungle.com/fr/jobs-matches'
  ```
- **LinkedIn** (CDI, full stack, 25 km, 14 derniers jours) :
  ```bash
  cd "$TEMP" && playwright-cli -s=chasse goto 'https://www.linkedin.com/jobs/search/?keywords=d%C3%A9veloppeur%20full%20stack&location=Strasbourg%2C%20Grand%20Est%2C%20France&f_JT=F&f_TPR=r1209600&distance=25'
  ```

Pour récupérer le lien d'une offre précise (facultatif) :
```bash
cd "$TEMP" && playwright-cli -s=chasse --raw eval "JSON.stringify([...document.querySelectorAll('a')].filter(a=>/NOM_DU_POSTE/i.test(a.innerText)).slice(0,3).map(a=>a.href))"
```

Si un site affiche une page de connexion, un captcha ou rien d'exploitable : le noter, passer au site suivant, et le signaler dans le compte rendu. Ne jamais résoudre un captcha ni se connecter à la place de Nedjmeddine.

## Étape 3 — Refermer proprement

```bash
cd "$TEMP" && playwright-cli -s=chasse tab-list
cd "$TEMP" && playwright-cli -s=chasse tab-close <index de MON onglet>
cd "$TEMP" && playwright-cli -s=chasse detach
```

Vérifier dans `tab-list` que seul l'onglet ouvert par `/chasse` est fermé.

## Étape 4 — Trier et écrire le JSON

Profil : Nedjmeddine, développeur Full Stack junior (2 ans d'alternance), stack **Node.js / Angular / React / .NET C# / Laravel / PHP / Symfony**. CDI uniquement.

Garder les offres qui collent, **classées de la plus à la moins pertinente** (10 à 15 si possible, une ligne par offre) :

- **Prioriser** : stack qui correspond, poste junior ou sans niveau précisé, publié récemment, « Soyez l'un des premiers candidats », entreprise finale (pas ESN) quand c'est possible.
- **Écarter d'office** : senior, lead, confirmé, expert, architecte, alternance, stage ; COBOL/mainframe ; postes non dev (business developer, chef de projet, commercial…) ; Crédit Mutuel / Euro-Information / CIC.
- Ne pas filtrer soi-même sur le suivi : le script s'en charge.

Écrire le fichier dans le scratchpad de la session (UTF-8) :

```json
[
  {
    "entreprise": "Nom exact de l'entreprise",
    "poste": "Intitulé du poste",
    "localisation": "Strasbourg",
    "source": "LinkedIn",
    "url": "https://... (vide si inconnu)",
    "date_publication": "2026-11-24 (vide si inconnue)",
    "raison": "Une phrase : pourquoi ça colle (stack, fraîcheur, réseau…)"
  }
]
```

## Étape 5 — Remplir l'onglet « Chasse du jour »

Depuis la racine du projet :

```bash
cd "/c/Users/d-nji/Desktop/suivi-CDI-repo" && PYTHONIOENCODING=utf-8 py -3 scripts/chasse_import.py "<chemin du JSON>"
```

Le script garde **4 entreprises** : d'abord celles **absentes du suivi**, puis seulement s'il en manque, celles déjà contactées **il y a plus de 30 jours et sans process en cours** (avec un badge « Déjà contacté le … »). Il écarte aussi celles déjà proposées par `/chasse` dans les 30 derniers jours, pour ne pas redonner les mêmes chaque jour.

S'il en retient moins de 4 : relire une deuxième recherche LinkedIn avec d'autres mots-clés (`développeur .NET`, `développeur PHP`, `développeur Angular`), toujours une seule page, puis relancer l'import avec le nouveau JSON.

## Étape 6 — Compte rendu

Court, en français :
- les 4 entreprises (poste, lieu, source, pourquoi), en signalant celles déjà dans le suivi ;
- les sites qui n'ont rien donné, s'il y en a ;
- rappeler que les cartes sont dans l'onglet **Chasse du jour** (http://localhost:5000) avec le bouton **Trouver sur LinkedIn**, et que le bouton **Contacté** les ajoute au suivi en « 1er contact ».

Terminer par : **Tout est fait — rien d'autre à valider de ta part.**

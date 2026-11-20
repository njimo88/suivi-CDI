---
description: Recrée une page web depuis des screenshots de référence avec haute fidélité visuelle, puis itère en boucle screenshot → comparaison → correction jusqu'à correspondance quasi-parfaite.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch
---

# Objectif

Reconstruire une page web identique visuellement à un ou plusieurs screenshots de référence fournis par l'utilisateur. L'objectif n'est pas "s'en inspirer" — c'est la reproduire. Chaque section, chaque espacement, chaque couleur et chaque typographie doit correspondre. Le résultat final doit avoir le niveau de qualité d'une implémentation d'agence.

---

# Inputs

- **Screenshots de référence** (obligatoires) : fournis par l'utilisateur via le chat. Peuvent être des captures d'écran full-page, desktop, mobile, ou des sections spécifiques.
- **Format cible** (optionnel, défaut = HTML/CSS vanilla) : HTML/CSS pur, React + Tailwind, ou Vue + CSS. Si non précisé, utilise HTML/CSS pur — le plus portable et le plus fidèle au pixel.
- **Contexte** (optionnel) : URL d'origine, nom du projet, sections spécifiques à recréer.

---

# Processus

## Phase 1 — Analyse de référence

Avant d'écrire une seule ligne de code, analyse chaque screenshot en profondeur. Pour chaque image fournie, documente précisément :

**Layout & Structure**
- Type de layout (grid, flexbox, full-width, contenu centré, largeur max)
- Nombre de colonnes et breakpoints visibles
- Sections identifiées (hero, nav, features, testimonials, footer, etc.)
- Hiérarchie visuelle (qu'est-ce qui attire l'œil en premier ?)

**Typographie**
- Familles de polices (serif, sans-serif, monospace — identifie si possible)
- Tailles approximatives (h1 vs body text vs caption)
- Poids (light, regular, medium, semibold, bold, extrabold)
- Line-height et letter-spacing visibles
- Alignement (left, center, right)

**Couleurs** (extrait chaque couleur présente)
- Couleur de fond principale
- Couleur(s) de texte
- Couleur(s) d'accent / CTA
- Couleur des bordures, séparateurs
- Gradients (direction + stops si visibles)
- Opacités et overlays

**Espacements & Proportions**
- Padding interne des sections (estimer en px ou rem relatif)
- Gaps entre éléments
- Marges de la grille
- Ratio des images/médias

**Composants & Détails**
- Boutons (style, radius, padding, hover state si visible)
- Cards (shadow, radius, border)
- Navigation (sticky, transparente, avec backdrop-blur ?)
- Images (object-fit, aspect-ratio)
- Icônes (style line vs filled, taille)
- Badges, pills, tags
- Formulaires si présents

Affiche ce résumé d'analyse structuré à l'utilisateur avant de commencer à coder.

---

## Phase 2 — Première implémentation

Construis une implémentation complète basée uniquement sur ce que tu observes dans les screenshots. **Ne pas inventer de sections ou de contenus absents de la référence.**

**Règles de code :**
- HTML sémantique (`<section>`, `<nav>`, `<header>`, `<main>`, `<footer>`, `<article>`)
- CSS custom properties pour les couleurs et espacements répétés
- Pas de frameworks par défaut sauf si l'utilisateur le demande
- Fonts : utilise Google Fonts si tu identifies la famille (Geist → CDN local, Inter, Poppins, DM Sans, etc.)
- Images : utilise des placeholders SVG ou `https://placehold.co/{w}x{h}` avec les bonnes proportions
- Breakpoints : commence par la taille visible dans le screenshot, ajoute responsive si évident
- Fichier unique `index.html` avec `<style>` inline pour commencer — plus facile à modifier pendant les itérations

Écris le fichier à `design-output/index.html` (crée le dossier si besoin).

---

## Phase 3 — Premier screenshot & comparaison

### Lancer le serveur local
```bash
python -m http.server 8080 --directory design-output &
sleep 1
```

### Prendre le screenshot
```bash
npx --yes puppeteer screenshot http://localhost:8080 --fullpage --output design-output/generated.png
```

Si Puppeteer n'est pas disponible, essaie :
```bash
npx --yes @puppeteer/browsers screenshot http://localhost:8080 design-output/generated.png
```

### Comparaison visuelle

Lis les deux images côte à côte avec le tool Read :
- `design-output/generated.png` — ta version
- Le screenshot de référence fourni par l'utilisateur

**Analyse section par section, de haut en bas.** Pour chaque section, note :

| Élément | Référence | Généré | Écart |
|---------|-----------|--------|-------|
| Nav height | ~64px | ~48px | -16px |
| Hero padding-top | ~120px | ~80px | -40px |
| CTA button radius | ~8px | ~4px | trop carré |
| ... | ... | ... | ... |

Estime les écarts en px et identifie les 5-10 priorités de correction (les plus visibles d'abord).

---

## Phase 4 — Boucle de correction (minimum 3 passes)

**Ne jamais t'arrêter après le premier draft.** La boucle est :

```
Analyser les écarts → Corriger le code → Re-screenshot → Comparer → Recommencer
```

### Critères de priorisation des corrections

**Priorité 1 — Structure (passe 1)**
- Proportions générales cassées (mauvaise largeur, layout qui s'effondre)
- Sections manquantes ou dans le mauvais ordre
- Couleurs de fond complètement différentes

**Priorité 2 — Typographie et couleurs (passe 2)**
- Taille des titres (h1, h2)
- Couleurs de texte et d'accent exactes
- Poids de police

**Priorité 3 — Espacements et détails (passe 3)**
- Padding/margin des sections
- Gap entre les cards/éléments
- Border-radius des composants
- Ombres et effets de profondeur

**Priorité 4 — Polish final (passe 4+)**
- Letter-spacing et line-height
- Micro-détails (taille des icônes, épaisseur des bordures)
- Transitions et hover states

### Format de chaque correction

Pour chaque passe, annonce ce que tu corriges :
```
Passe 2 — 6 corrections :
- Nav : padding 16px → 20px, font-weight 500 → 600
- Hero h1 : font-size 3rem → 4.5rem
- CTA background : #3b82f6 → #2563eb (couleur exacte extraite)
- Section features : padding 80px → 120px top/bottom
- Cards : border-radius 8px → 16px + box-shadow ajusté
- Footer : background #0f172a → #111827
```

Puis applique toutes les corrections d'un coup, re-screenshot, et répète.

---

## Phase 5 — Validation finale

Quand les 3+ passes sont terminées et que les écarts sont mineurs, présente :

1. **Screenshot final vs référence** côte à côte (si possible dans le terminal)
2. **Récapitulatif des passes** : combien de corrections par passe
3. **Écarts résiduels** : liste ce qui reste différent et pourquoi (font non identifiable, contenu dynamique, effet JS, etc.)
4. **Fichier final** : chemin vers `design-output/index.html`

---

# Règles absolues

1. **Ne jamais s'arrêter après la première implémentation.** Minimum 3 passes de correction même si le résultat semble "assez proche."

2. **Ne jamais inventer de sections.** Si un élément n'est pas visible dans le screenshot de référence, il ne doit pas apparaître dans le code. Pas de "je suppose que le footer contient aussi un lien CGU."

3. **Couleurs exactes uniquement.** Ne pas utiliser des approximations Tailwind (`blue-500` au lieu de `#2563eb`). Extraire les valeurs hex depuis le screenshot autant que possible.

4. **Taille réelle, pas approximative.** Si le hero fait visuellement ~50% du viewport en hauteur, le coder avec `min-height: 50vh` et non `min-height: 300px` arbitraire.

5. **Chaque passe doit être documentée.** Liste toujours les corrections avant de les appliquer — ça permet à l'utilisateur de suivre et de corriger si nécessaire.

6. **Si un screenshot est flou ou partiel, le dire.** Ne pas deviner ce qui n'est pas visible. Demander un screenshot complémentaire si nécessaire.

7. **Le serveur doit rester actif** entre les passes pour accélérer les screenshots. Tuer le processus uniquement en fin de session.

8. **Puppeteer doit capturer la même viewport** que la référence. Si le screenshot de référence est desktop (≥1280px), configurer Puppeteer en conséquence :
```bash
npx puppeteer screenshot http://localhost:8080 --fullpage --viewport-width 1440 --output design-output/generated.png
```

---

# Standard de qualité

Le critère d'acceptation est **"aussi proche que réalistement possible"**, pas "similaire en esprit."

**Acceptable :**
- Contenu de texte légèrement différent (placeholder vs texte réel)
- Font identifiée à 95% (Inter vs Geist si très similaires)
- Image placeholder avec bonnes proportions vs image réelle
- Hover states non reproduits (pas visible dans screenshot statique)

**Non acceptable :**
- Section entière avec un fond complètement différent
- Typographie avec la mauvaise graisse (light vs bold)
- Espacements qui dénaturent la hiérarchie visuelle
- Couleurs d'accent incorrectes sur les CTA
- Layout qui s'effondre à la largeur de référence

---

# Comportement exemple

```
Utilisateur : voici un screenshot de la homepage de Stripe
Agent : [analyse 8 éléments clés du design]
        → Layout centré max-width 1200px, 2 colonnes hero
        → Couleurs : fond #0a2540, accent #635bff, texte #ffffff / #8898aa
        → Font : Sohne ou Inter SemiBold pour les titres
        → Hero padding-top estimé ~140px
        [implémente index.html]
        [screenshot passe 1]
        → 9 écarts identifiés : gradient manquant, nav trop haute, CTA wrong color...
        [5 corrections passe 1]
        [screenshot passe 2]
        → 4 écarts résiduels : letter-spacing trop serré, card shadow trop forte...
        [3 corrections passe 2]
        [screenshot passe 3]
        → 1 écart résiduel : font exacte non chargée (Sohne = propriétaire)
        Résultat : fidélité ~92%. Fichier : design-output/index.html
```

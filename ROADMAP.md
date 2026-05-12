# Roadmap de construction — BioPulse

Roadmap détaillée et actionnable pour construire le package Python BioPulse, organisée en phases incrémentales avec livrables concrets.

---

## Phase 0 — Fondations du projet (1–2 jours)

**Objectif : avoir un squelette installable et testable.**

- [ ] Choix de l'outil de packaging : `pyproject.toml` avec `hatchling` ou `uv`
- [ ] Structure de répertoires conforme à l'architecture du README
- [ ] Configuration : `ruff` (lint + format), `mypy` (typage), `pytest`
- [ ] CI minimale GitHub Actions (lint + tests sur Python 3.11 / 3.12)
- [ ] Licence MIT, `CHANGELOG.md`, `CONTRIBUTING.md`
- [ ] Premier commit installable : `pip install -e .` fonctionne

**Décision clé à trancher dès le départ** : backend de rendu.

---

## Phase 1 — Modèle de données & I/O JSON (3–5 jours)

**Objectif : pouvoir charger/valider un graphe + des événements depuis JSON.**

- [ ] `model/schema.py` — schémas Pydantic v2 pour `Node`, `Edge`, `Graph`, `Event`, `EventStream`
- [ ] `model/graph.py` — classe `Graph` (wrapper autour de NetworkX `DiGraph`)
- [ ] `model/events.py` — `EventStream` trié par `t`, itérable, bisect pour seek
- [ ] `io/json_loader.py` — `load_graph()`, `load_events()`, `load_scene()` (graphe + events combinés)
- [ ] JSON Schema exporté (`schema/graph.schema.json`) pour validation externe
- [ ] Tests : graphes jouet (3–4 nœuds), événements, cas d'erreur (nœud manquant, t négatif…)
- [ ] 2–3 fichiers d'exemple dans `examples/data/` (ex: cascade IL6→STAT3)

---

## Phase 2 — Layout & rendu statique (3–5 jours)

**Objectif : afficher un graphe à l'écran, sans animation.**

- [ ] `layouts/forceatlas.py` — wrapper autour de `networkx.spring_layout` ou `fa2` (positions 2D)
- [ ] `layouts/base.py` — interface `Layout` (compute → dict[node_id, (x, y)])
- [ ] `core/renderer/` — première implémentation du backend choisi
- [ ] API publique : `biopulse.show(graph)` qui ouvre une fenêtre / un notebook avec le graphe figé
- [ ] Rendu : nœuds (cercles), arêtes (lignes/flèches), labels optionnels
- [ ] Tests visuels (snapshots PNG comparés via `pytest-mpl` ou similaire)

---

## Phase 3 — Timeline & animation événementielle (5–7 jours)

**Objectif : MVP fonctionnel — lire un flux d'événements et animer les nœuds.**

- [ ] `core/timeline/clock.py` — horloge logique (play/pause/seek/speed)
- [ ] `core/timeline/scheduler.py` — applique les événements au bon `t`
- [ ] `core/animation/state.py` — état visuel par nœud (couleur, intensité, taille)
- [ ] `core/animation/interp.py` — interpolation (ease-in/out) entre transitions d'état
- [ ] Boucle de rendu à FPS fixe (30 ou 60)
- [ ] API : `biopulse.play(graph, events)` — animation en direct
- [ ] Exemple end-to-end : cascade de signalisation animée
- [ ] **Jalon MVP atteint** ✅

---

## Phase 4 — Interaction utilisateur (3–5 jours)

- [ ] Zoom / pan à la souris
- [ ] Timeline scrubbing (slider + clic)
- [ ] Pause / replay / vitesse variable
- [ ] Hover/click sur nœud → panneau d'inspection (métadonnées)
- [ ] Surlignage des chemins en amont/aval

---

## Phase 5 — Parsers biologiques (3–5 jours)

- [ ] `parsers/sif.py` — format SIF (le plus simple, à faire en premier)
- [ ] Arêtes signées (`activation` / `inhibition`) — rendu différencié
- [ ] `parsers/sbml.py` — SBML-qual via `python-libsbml`
- [ ] `parsers/ginml.py` — GINML (XML de GINsim)
- [ ] Métadonnées de nœud (groupe, type, pathway) → couleur/forme
- [ ] Exemples : un modèle Boolean publié (ex: réseau de Fauré ou un modèle PyBoolNet)

---

## Phase 6 — Export (2–4 jours)

- [ ] `io/exporters.py` — sérialisation JSON (round-trip)
- [ ] Export PNG frame-par-frame
- [ ] Export MP4/GIF via `imageio` ou `ffmpeg-python`
- [ ] Export HTML autonome (si backend web)

---

## Phase 7 — Effets visuels avancés (1–2 semaines)

- [ ] Pulses d'activation (onde lumineuse au changement d'état)
- [ ] Particules le long des arêtes pour propagation de signal
- [ ] Glow / bloom (shader)
- [ ] Heatmap d'activité cumulée
- [ ] Visualisation d'attracteurs (clustering d'états récurrents)
- [ ] Edge bundling pour gros graphes

---

## Phase 8 — Écosystème (en continu)

- [ ] Interop PyBoolNet → events stream
- [ ] Interop MPBN
- [ ] Layouts hiérarchiques biologiques (compartiments cellulaires)
- [ ] Cytoscape interop (import/export `.cyjs`)
- [ ] Documentation Sphinx + galerie d'exemples
- [ ] Publication PyPI v0.1.0 après Phase 4, v1.0.0 après Phase 6

---

## Décisions critiques à prendre tôt

| Décision | Impact | Recommandation |
|---|---|---|
| Backend de rendu | Toute l'archi | À trancher (Pyglet/moderngl, PixiJS, Matplotlib, Three.js) |
| Pydantic v1 vs v2 | Validation | v2 (perf, moderne) |
| Coordonnées 2D ou 3D | Layouts, shaders | Commencer 2D |
| Notebook-first ou app standalone | API publique | Notebook-first (plus rapide pour la science) |

---

## Options de backend de rendu

| Backend | Avantages | Inconvénients |
|---|---|---|
| **Pyglet / moderngl** | GPU natif Python, contrôle total shaders, performant gros graphes | Fenêtre desktop uniquement, pas de notebook natif |
| **PixiJS via anywidget** | WebGL navigateur/notebook, export HTML facile, idéal démos | Stack hybride Python+JS |
| **Matplotlib + FuncAnimation** | 100% Python, MVP en quelques jours, simple | Limité gros graphes et effets avancés |
| **Three.js via pythreejs** | WebGL 3D dans notebook, riche visuellement | Courbe d'apprentissage plus raide |

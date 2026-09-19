# Findings & Decisions — DialogForge V2

## Requirements
- Première livraison : **conception et synthèse sur corpus local fourni**, en terminal guidé.
- Recherche externe : profil distinct, à qualifier avant d'être proposé. Développement assisté : lot 4.
- Autorités séparées : PWF possède les phases du projet ; le moteur A/B possède son cycle local et
  ses appels ; les artefacts de revue possèdent les objections et leurs dispositions ;
  **l'utilisateur** possède l'acceptation du résultat.

## Research Findings
- **IAbinome, commit `4a11cc7eae47a4920b845fda6e65937557a967cf`** — HEAD du dépôt local le
  2026-09-18, identique au commit de référence de l'étude `astra/`. `git rev-list --count` = 0.
- **PWF `faf1a15a7dcc17a9e0f49760da0756d1a5d4609a`, v3.20.1** — HEAD amont le 2026-09-18, identique
  au commit étudié. Écart nul : aucune mise à jour à arbitrer.
- **Porte de validation héritée** : `ruff check .` + `mypy --strict` + pytest. Verte sur le commit
  de départ : 302 passés, 2 ignorés (privilège de lien symbolique absent, `WinError 1314`), 42
  sous-tests. Aucun échec préexistant, aucun test neutralisé.
- **Les vraies CLI ne sont jamais appelées** : `claude` et `codex` sont pourtant sur le `PATH`.
  Prouvé par leurres placés en tête de `PATH`, témoin resté vide sur la suite complète **et** sur
  le cycle de bout en bout. Les tests neutralisent aussi `settings.SEARCH_PATHS`, donc aucun
  `iabinome.toml` personnel ne peut modifier leur comportement.
- **Le moteur consomme un 5e appel `FINAL_A`** qui réécrit librement le document après une
  relecture favorable de B. C'est exactement ce que le point 1.3 du plan veut remplacer par la
  promotion de la version examinée. Confirmé sur pièce, pas déduit.
- **Le livrable porte déjà** l'avertissement « Ce document n'est pas approuvé : sa présence prouve
  que le cycle s'est achevé, rien de plus. » La distinction « terminé » ≠ « accepté » est tenue.
- **Route d'installation PWF** : seule la route plugin/marketplace livre les hooks `SessionStart`
  et les commandes `/plan-*`. La route skill autonome retenue ici n'a que des hooks à portée
  d'activation, enregistrés après la première invocation du skill dans la session.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Python 3.12.5, venv local au dépôt | `requires-python >= 3.12` ; venv hors Git (`.gitignore`) |
| ruff 0.16.8, mypy 2.3.1, pytest 9.1.1 | Versions réellement installées. mypy 2.x est une majeure au-delà des relevés historiques du projet (1.x) : elle passe sans modifier le code |
| PWF copié dans `~/.claude/skills/planning-with-files` | Route « standalone » de `docs/installation.md`, appliquée depuis un clone détaché sur le commit épinglé ; contenu vérifié identique byte à byte |
| Cadrage guidé sans modèle ; format = repère (1.1, 2026-09-19) | Décisions et condition de réouverture dans `task_plan.md`. `framing.py` du prédécesseur réemployé pour l'idée (fichier direct ou cadrage, provenance), pas pour le code : il portait sessions, verrou, preuves d'usage et budget, tout ce que `CLAUDE.md` §2 interdit |
| Provenance = `provenance_demande.json`, lisible à l'œil | Un fichier, pas de base ; écrit entre `demande.md` et `etat.json` pour rester rejouable après un arrêt brutal |
| Plan nommé `2026-09-18-dialogforge-v2` | Créé par `init-session.ps1` amont, mode par défaut (ni `-Autonomous` ni `-Gated`) |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| Réponse accentuée du faux agent rendue en `DECODE_FAILED` | Encodage du tube Windows (cp1252) contre décodage UTF-8 des adaptateurs. `PYTHONIOENCODING=utf-8` dans le scénario ; à retenir si le lot 1 ajoute des réponses simulées accentuées |
| `ruff format --check` signale 26 fichiers | Laissé ouvert : `ruff format` n'appartient pas à la porte historique du projet. À trancher explicitement, pas à subir |

## Resources
- Plan de mise en œuvre : `C:\Projets\DialogForge_Next\astra\06_plan_mise_en_oeuvre.md`
- Compte rendu de référence J0 : `reference/COMPTE_RENDU_J0.md`
- Scénario sans fournisseur : `reference/cycle_sans_fournisseur.py`
- PWF amont : https://github.com/OthmanAdi/planning-with-files (commit `faf1a15`, tag `v3.20.1`)

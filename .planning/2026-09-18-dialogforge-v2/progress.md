# Progress Log — DialogForge V2

## Session: 2026-09-18 — mise en place du chantier

### Current Status
- **Phase :** 1 terminée (J0 atteint le 2026-09-19) — phase 2 non commencée
- **Started :** 2026-09-18
- **Reste pour J0 :** rien. Injection automatique prouvée avec le plugin local épinglé.

### Actions Taken
- Clone d'IAbinome (`4a11cc7`) vers `C:\Projets\DialogForge_2`, branche `v2-socle`, remote retiré.
- Origine du code et périmètre de la première livraison inscrits dans le README.
- venv local, installation `-e .`, relevé des versions d'outils.
- Porte de validation exécutée sur le commit de départ.
- Leurres `claude` et `codex` en tête de `PATH` : preuve qu'aucun appel fournisseur n'a lieu.
- `reference/cycle_sans_fournisseur.py` écrit et exécuté : cycle A/B complet sans fournisseur.
- PWF v3.20.1 installé depuis le commit épinglé `faf1a15`, contenu vérifié identique.
- Plan `2026-09-18-dialogforge-v2` créé par `init-session.ps1`, lots 0 à 3 inscrits.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `ruff check .` | aucun constat | All checks passed | OK |
| `mypy` strict (`src` + `tests`) | aucun constat | no issues in 32 source files | OK |
| `pytest -q` | suite verte | 302 passés, 2 ignorés, 42 sous-tests, 34 s | OK |
| Suite sous leurres de CLI | témoin vide | témoin vide (0 octet) | OK |
| Cycle de bout en bout, faux agents | cycle achevé sans fournisseur | `AWAITING_APPROVAL`, phase `CLOSED`, 0 constat ouvert, 5 appels | OK |
| Cycle sous leurres de CLI | témoin vide | témoin vide (0 octet) | OK |
| Installation PWF | identique à l'amont épinglé | `diff -r` sans différence, 32 fichiers | OK |
| Plugin local embarqué | identique au commit épinglé | `diff -r` sans différence, 728 fichiers | OK |
| Injection `SessionStart:startup` | plan livré au contexte | ligne 5, `exitCode=0`, 902 ms | OK |
| Injection `SessionStart:compact` | plan livré après `/compact` | ligne 100, `exitCode=0`, 251 ms | OK |
| Injection `UserPromptSubmit` | plan livré à chaque message | 3 livraisons | OK |
| Injection `PreToolUse` | plan livré avant les appels couverts | 6 exécutions, 6 livraisons | OK |
| Récupération après compactage | bonne prochaine étape retrouvée | `## Next Step` exact rendu | OK |
| `PostToolUse`, `PreCompact` | — | aucun enregistrement | NON OBSERVÉ |

### Errors
| Error | Resolution |
|-------|------------|
| `DECODE_FAILED` sur réponse accentuée du faux agent | `PYTHONIOENCODING=utf-8` pour les enfants du scénario ; défaut du faux agent, pas du moteur |

### Session de qualification du 2026-09-19

`ecc5d2e1-5fea-4930-a674-35d68e1ef5c6`, lancée par `tools/claude-pwf.ps1`, Claude Code 2.1.278.
Analyse rejouable : `.venv/Scripts/python.exe reference/preuve_injection.py`.

Aucun code métier touché pendant cette qualification. Le lot 1 n'a pas été commencé.

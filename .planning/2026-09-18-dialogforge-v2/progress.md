# Progress Log — DialogForge V2

## Session: 2026-09-18 — mise en place du chantier

### Current Status
- **Phase :** 1 terminée (J0 atteint le 2026-09-19) — phase 2 en cours, 1.1 fait (revalidé)
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

## Session: 2026-09-19 — lot 1, point 1.1 (format court de demande)

Autorisation du PO : démarrage de 1.1 seul, tests ciblés, pas de réouverture de la qualification des
hooks. Session lancée par `tools/claude-pwf.ps1`. **Rien n'est commité** : aucune demande de commit.

### Actions Taken
- `src/iabinome/demande.py` (nouveau, ~150 lignes brutes) : six sections reconnues sans égard à la
  casse, aux accents ni au trait d'union ; questionnaire de terminal `guide()` ; provenance
  `provenance_demande.json`, rejouable (une empreinte déjà consignée n'est pas réécrite).
- `cli.py` : `new` prend `--demande <fichier>` **ou** `--cadrer` (exclusifs, code 2 sinon) ; la demande
  est obtenue **avant** le dossier temporaire ; note sur `stderr` des sections absentes, sans blocage.
- `workflow.py` : `apply_answer` consigne la provenance entre l'écriture de `demande.md` et la
  publication de l'état ; archive retrouvée par empreinte ; `sections_retirees` calculé.
- Aucun prompt modifié : `prompts.py` porte déjà QUESTION/DOCUMENT, la demande y passe telle quelle.
- README : format court, `--cadrer`, provenance.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Base avant changement (`pytest tests`) | 302 + 2 ignorés | 302 passés, 2 ignorés | OK |
| `ruff check .` | aucun constat | All checks passed | OK |
| `mypy` strict | aucun constat | no issues in 34 source files | OK |
| `pytest tests` | suite verte | 325 passés, 2 ignorés, 44 sous-tests, 35 s | OK |
| `tests/test_demande.py` (nouveau) | 22 tests verts | 22 verts | OK |
| Contre-épreuve : garde d'idempotence de `record` neutralisée | tests de rejeu rouges | 2 échecs (unitaire + rejeu après provenance) | OK, garde rétablie |
| Scénario `reference/cycle_sans_fournisseur.py` | cycle achevé | rc=0, `provenance_demande.json` présent | OK |
| `new --cadrer` en terminal réel, stdin piloté | collaboration créée, aucun appel | créée, `demande.md` et provenance écrits | OK |

### Errors
| Error | Resolution |
|-------|------------|
| `pytest` sans argument : `ModuleNotFoundError: yaml` | Il ramasse les tests du plugin embarqué sous `tools/`. Lancer `pytest tests` |
| `test_nothing_is_said_when_no_file_is_found` rouge | Sa demande libre déclenchait la nouvelle note de format sur `stderr`. Le test vise le silence de la **configuration** : il reçoit une demande complète, son assertion `stderr == ""` est intacte |
| `test_stopped_after_the_state_…` rouge | `--answer` écrit maintenant **quatre** fois (archive, demande, provenance, état). Compte réajusté à 4 ; cas « arrêt après la provenance » ajouté ; chaque rejeu vérifie **une seule** version consignée |
| `StopIteration` au lieu d'`EOFError` dans un test de cadrage | Le simulacre d'`input` levait la mauvaise exception ; il lève désormais `EOFError`, comme le vrai |
| Variable locale `demande` masquant le module importé (`workflow._preflight`) | Import par nom (`dropped`, `record`), variable renommée `text` |

### Correction de 1.1 — `--answer` complète la demande (2026-09-19, décision du PO)

Le PO a accepté le cadrage sans modèle, mais refusé `sections_retirees` : elle **constate** une perte
sans l'empêcher (le test où `--answer` retirait *Sources* en faisait la preuve). 1.1 remis en cours,
1.2 non commencée.

#### Actions Taken
- `demande.complete(base, réponse)` : le texte existant en préfixe, intact, puis la réponse sous
  `## Précisions n°K`. K se déduit du texte (pas de l'horloge) : le rejeu retrouve la même empreinte.
  `dropped()` et `sections_retirees` supprimés (code mort).
- `workflow._check_demande` recalcule la demande complétée depuis la version que l'état désigne : le
  `demande.md` courant, ou son **archive** s'il est déjà complété (arrêt brutal après l'écriture).
- `apply_answer` écrit la version complète ; la provenance porte `complement_sha256`, `replaces`,
  `archive`, `phase`, `revision`, `latest_review`.
- Remplacement intégral : **non fait**, hors de ce changement, à rendre explicite et distinct plus tard.
- README et `CONCEPTION_FINALE.md` §2 amendés (l'ancien texte disait « nouvelle demande complète »).

#### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Validation ciblée (`test_demande.py` + `test_intervention.py`) | verte | 50 passés, 6 sous-tests | OK |
| Contre-épreuve 1 : `complete` remplace au lieu de compléter | tests rouges | 13 échecs (unitaires, nominal, incidents, 2e réponse, 4 points d'arrêt) | OK, rétabli |
| Contre-épreuve 2 : recalcul du rejeu ignore l'archive | tests de rejeu rouges | 4 échecs (arrêts après l'écriture de `demande.md`, points 2 et 3) | OK, rétabli |
| `ruff check .` | aucun constat | All checks passed | OK |
| `mypy` strict | aucun constat | no issues in 34 source files | OK |
| `pytest tests` (porte complète) | suite verte | 334 passés, 2 ignorés, 48 sous-tests, 37 s | OK |
| Scénario `reference/cycle_sans_fournisseur.py` | cycle achevé | rc=0 | OK |

Preuves de non-perte (`TestAnswerKeepsTheDemande`) : les six sections existantes gardent le même corps
après une réponse courte, à chacun des quatre arrêts brutaux (après archive, demande, provenance, état),
après un appel interrompu puis `--retry-call`, après une réponse hors contrat puis `--retry-call`, et
après une seconde réponse (`Précisions n°1` et `n°2`, archives `.001` et `.002`, provenance chaînée).

#### Errors
| Error | Resolution |
|-------|------------|
| `test_stopped_after_the_demande_…` rouge | Il comparait `demande.md` à la réponse seule (ancienne sémantique). Il compare désormais à `complete(archive, réponse)` |
| Anciens tests `dropped` / `sections_retirees` | Supprimés avec le code qu'ils éprouvaient |
| Sous-tests des points d'arrêt s'empilant dans un même dossier | `tearDown_collaboration` repart d'une collaboration neuve entre deux sous-tests |
| `task_plan.md`, `README.md`, `RULES.md`, `CONCEPTION_FINALE.md` en CRLF | Édités ligne à ligne ou par script, puis normalisés en CRLF (les éditions multi-lignes échouent sur CRLF) |

# Progress Log — DialogForge V2

## Session: 2026-09-18 — mise en place du chantier

### Current Status
- **Phase :** 1 terminée (J0 atteint le 2026-09-19) — phase 2 terminée, 1.1 à 1.4 faits ; J1 à constater par le PO
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

## Session: 2026-09-19 — lot 1, point 1.2 (objections et dispositions)

Autorisation du PO : « commiter puis attaquer le lot suivant ». 1.1 commité (`b0dc6a3`). « Lot suivant »
lu comme le prochain point du plan, **1.2** ; 1.3 non ouvert.

### Actions Taken
- **Contrat confronté à des revues réelles** (`conception/essais/`, mission du 2026-09-05). Défaut
  mesuré : au tour 2, B a **réécrit l'énoncé de ses 7 constats** pour y dire « désormais résolu ».
- `contracts.py` : revue **v2** (`justification` distincte) ; v1 toujours lue. Énoncé initial immuable
  (la réécriture devient la justification, sans nouvel appel) ; fermeture sans justification = reste
  ouverte. Nouveau : `ObjectionResponse`, `split_responses`, `parse_objection_responses` — une réponse par
  objection ouverte, absente/dupliquée/inconnue refusée, justification exigée sauf `CORRIGE`, bloc
  récupéré s'il est entouré de prose.
- `models.py` : `ResponseKind` (`CORRIGE`, `CONTESTE`, `REPORTE`, `ARBITRAGE`).
- `workflow.py` : `apply_a` exige les réponses en `REVISION_A` **avant** toute écriture, écrit
  `NNNN-reponses-A.json` et le document sans le bloc ; `apply_b` passe les énoncés initiaux ; le prompt de
  B montre la réponse de A à chaque constat.
- `prompts.py` : format du bloc dans le gabarit de révision, schéma v2 dans celui de B.
- `objections.py` (nouveau) : `ledger()` relit le registre par objection dans `echanges/`.
- `tests/fakes.py` : `revision()` ; le faux agent écrit maintenant des **octets UTF-8** (défaut du lot 0).
- `reference/cycle_sans_fournisseur.py` : A répond, B en v2, demande au format court, registre affiché,
  et **rc≠0 si le cycle n'aboutit pas**.
- **Non fait, volontairement :** `FINAL_A` (1.3) ; un préambule avant `IABINOME:DOCUMENT` reste refusé
  (règle mesurée du 2026-09-04) ; pas de réponse de A exigée hors révision.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `tests/test_objections.py` (nouveau) | verte | 32 tests, 12 sous-tests | OK |
| `tests/test_prompts.py` (format des réponses nommé dans le gabarit) | verte | verte | OK |
| Contre-épreuve 1 : énoncé initial non gardé | rouge | 10 échecs | OK, rétabli |
| Contre-épreuve 2 : fermeture sans justification ferme | rouge | 3 échecs | OK, rétabli |
| Contre-épreuve 3 : réponse manquante tolérée | rouge | 2 échecs | OK, rétabli |
| Contre-épreuve 4 : réponse dupliquée tolérée | rouge | 1 échec | OK, rétabli |
| Contre-épreuve 5 : réponse à un constat inconnu tolérée | rouge | 1 échec | OK, rétabli |
| Contre-épreuve du scénario : A ne répond pas | rc≠0 | rc=1, `ECHEC` affiché | OK |
| `ruff check .` | aucun constat | All checks passed | OK |
| `mypy` strict | aucun constat | no issues in 36 source files | OK |
| `pytest tests` (porte complète) | suite verte | 372 passés, 2 ignorés, 71 sous-tests, 53 s | OK |
| Scénario `reference/cycle_sans_fournisseur.py` | `AWAITING_APPROVAL`, 0 objection ouverte | rc=0, registre `B-001 : RESOLVED` | OK |

### Errors
| Error | Resolution |
|-------|------------|
| **Le scénario de référence sortait en rc=0 avec `statut : ERROR`** | Il n'échouait jamais : mes « rc=0 » des tours précédents ne prouvaient pas que le cycle allait à son terme. Il rend `1` hors de `AWAITING_APPROVAL` sans objection ouverte. Le rc=0 de 1.1 reste vrai mais faible ; le cycle de 1.1 était bien achevé (statut relu à l'époque) |
| 4 tests à deux tours en `ERROR` | Réponse simulée accentuée : `DECODE_FAILED` du faux agent (findings, lot 0). Corrigé à la source (`sys.stdout.buffer`) plutôt que contourné |
| `test_future_schema_version_rejected` rouge | Il prenait `2` pour « futur » ; la v2 existe. Il prend `3` |
| `test_exchange_artifacts_are_named_and_ordered` rouge | Il attendait 4 artefacts ; `0003-reponses-A.json` s'y ajoute |
| Motifs de mutation en heredoc, `SyntaxError` sur une apostrophe | Réécrits avec l'outil d'édition (règle déjà consignée, étendue aux scripts jetables) |
| `cd conception/essais` pour lire des essais | Le répertoire de travail a persisté ; revenu à la racine. À ne pas refaire (`RULES.md`) |

## Session: 2026-09-19 — lot 1, point 1.3 (boucle et version livrée)

Autorisation du PO (« allons y ») après `2b5ae15`. **Non commité** : aucune demande de commit.

### Actions Taken
- **`FINAL_A` supprimé** : `Phase.FINAL_A`, `prompts.build_final`, `_A_FINAL`, la branche de `apply_a`.
- **Promotion** (`workflow.promote`) : `ACCEPTER`, ou plafond atteint, mène à `CLOSED` ; le document que B
  vient d'examiner est copié octet pour octet dans `livrables/version_finale.md`, en-tête vraie
  (« non approuvé », fin du cycle, version examinée). Rejouable après arrêt brutal (mêmes octets, aucun
  appel repayé).
- **Bilan** (`objections.bilan`, `livrables/bilan.md`) écrit par le programme, sans modèle : livrable,
  revue et demande avec leurs empreintes, registre des objections, désaccords restants.
- **Relecture ciblée** : `build_review(..., targeted=True)` dès `revision >= 1` ; B ne relit que les
  objections traitées et les régressions ; une nouvelle remarque se note en `NOTE`.
- Scénario de référence : A=2, B=2 (avant : A=3, B=2), et garde sur ce compte.
- README, `CONCEPTION_FINALE.md` (amendement daté), `RULES.md` mis à jour.
- **Non fait, volontairement :** le tour supplémentaire demandé après le plafond (décision humaine,
  point 1.4) ; aucun jugement du programme sur ce qui est « hors périmètre ».

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `tests/test_promotion.py` (nouveau) | verte | 14 tests | OK |
| `tests/test_prompts.py` (ciblé, plus de `build_final`) | verte | verte | OK |
| Contre-épreuve 1 : livrable réécrit après la revue | rouge | échec | OK, rétabli |
| Contre-épreuve 2 : relecture jamais ciblée | rouge | échec | OK, rétabli |
| Contre-épreuve 3 : plafond décalé d'un tour | rouge | échec | OK, rétabli |
| Contre-épreuve 4 : bilan qui cache les désaccords | rouge | échec | OK, rétabli |
| Contre-épreuve 5 : livrable ≠ document examiné | rouge | échec | OK, rétabli |
| `ruff check .` | aucun constat | All checks passed | OK |
| `mypy` strict | aucun constat | no issues in 37 source files | OK |
| `pytest tests` (porte complète) | suite verte | 390 passés, 2 ignorés, 67 sous-tests, 58 s | OK |
| Scénario `reference/cycle_sans_fournisseur.py` | `AWAITING_APPROVAL`, A=2 B=2 | rc=0, bilan et registre lus | OK |

### Errors
| Error | Resolution |
|-------|------------|
| 7 tests rouges au premier passage | Attendus : ils décrivaient le cycle à 5 appels (`_FINAL`, `build_final`, compte d'appels). Réécrits pour la promotion, `_FINAL` retiré partout |
| Script de patch des tests : motif en CRLF non trouvé | Le script gère maintenant les fins de ligne ; un patch partiel avait déjà écrit 3 fichiers sur 4, repris fichier par fichier |
| `cat >> fichier <<EOF` vide lancé par réflexe | Sans effet (rien ajouté) ; fonction ajoutée avec l'outil d'édition (`RULES.md` : pas de heredoc pour du code) |
| Une assertion tautologique écrite (`hash == même hash`) | Remplacée par la vraie preuve : empreinte du corps livré = empreinte du document examiné |

## Session: 2026-09-19 — lot 1, point 1.4 (résultat et décision utilisables)

Autorisation du PO (« commites puis attaques le point suivant »). 1.3 commité (`25ab101`). **1.4 non
commité** : aucune demande de commit.

### Actions Taken
- **`decisions.py`** (nouveau) : `decisions.json` (ajouté à chaque décision, rejouable), version précise
  (empreintes du livrable, de la revue, de la demande), `describe`, `next_action`, `incident_line`, `render`.
- **`workflow.decide`** : acceptation, acceptation avec réserves (texte exigé), arrêt — sous verrou, sans
  appel. Accepter **ne change pas** le statut du moteur. `Status.STOPPED` ajouté.
- **Correction ciblée = intervention du moteur** (`Correct`, réutilise le chemin de `--answer`) :
  instruction complétée dans `demande.md`, décision consignée, un tour au-delà du plafond ; A repart du
  **corps** du livrable (`_promoted_body`), sans l'en-tête du programme.
- **CLI** : `show`, `decide` (`--accept`, `--accept-with-reserves`, `--correct`, `--stop [--reason]`), `list`
  (calculée depuis les dossiers, sans index) ; `status` donne décision, incident et prochaine action.
- `bilan.md` mentionne les corrections ciblées demandées.
- Scénario de référence : `show` → `decide --accept` → `list`, et échec si la décision n'est pas consignée
  ou si accepter change le statut du moteur.
- README, `CONCEPTION_FINALE.md` §7 (amendement daté), `RULES.md`, plan à jour.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `tests/test_decision.py` (nouveau) | verte | 39 tests | OK |
| Contre-épreuve 1 : version non capturée | rouge | 3 échecs | OK, rétabli |
| Contre-épreuve 2 : acceptation possible à tout statut | rouge | 3 échecs | OK, rétabli |
| Contre-épreuve 3 : tour supplémentaire mal tracé | rouge | 1 échec | OK, rétabli |
| Contre-épreuve 4 : en-tête du programme passé à A | rouge | 1 échec | OK, rétabli |
| Contre-épreuve 5 : décision non rejouable | rouge | 1 échec | OK, rétabli |
| Contre-épreuve 6 : changement de version inaperçu | rouge | 2 échecs | OK, rétabli |
| `ruff check .` | aucun constat | All checks passed | OK |
| `mypy` strict | aucun constat | no issues in 39 source files | OK |
| `pytest tests` (porte complète) | suite verte | 429 passés, 2 ignorés, 67 sous-tests, 50 s | OK |
| Scénario `reference/cycle_sans_fournisseur.py` | cycle, `show`, `decide --accept`, `list` | rc=0, décision consignée, statut inchangé | OK |

### Errors
| Error | Resolution |
|-------|------------|
| Cycle d'imports `decisions` ↔ `objections` (prévu) | `bilan` reçoit `corrections` en paramètre au lieu d'importer `decisions` |
| 39 tests verts du premier coup, avec 2 assertions bâclées écrites par moi (`… if False else …`) | Remplacées par de vraies vérifications avant de compter ce lot comme prouvé ; puis 6 contre-épreuves |
| 4 lignes trop longues et un import inutile (`ruff`) | Corrigés |
| Motifs des scripts de patch multi-lignes contre des fichiers CRLF | Scripts qui gèrent les fins de ligne, motifs vérifiés un à un |

### Reste ouvert
- **Lot 2** non ouvert. **J1** : critères réunis, à constater par le PO.
- `show` affiche le document en entier par défaut : à ajuster si le PO préfère le résumé seul.

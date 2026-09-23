# Progress Log — DialogForge V2

## Session: 2026-09-22 (suite) — 3.3 clos, J3 atteint, v0.1.0

Suite à une relecture externe des commits : trois points corrigés avant de clore.

1. **Suivi périmé.** `task_plan.md` disait encore « non commitées » alors que la correction Windows
   (`1a7aa22`) et la documentation du protocole 3.1/qualification/3.2 (`052678f`) l'étaient déjà ; la
   case 3.1 restait décochée. Corrigé.
2. **Preuve à consigner.** Relecture des traces brutes de la mission de révision (lot 3.2, 22/09) :
   Codex a bien lu un vrai corpus par son propre outil, dans un cycle A/B complet —
   `Get-ChildItem` puis `Get-Content -LiteralPath corpus/fichiers/nextcloud-stockage-externe-anonymise.md
   -Raw`, « succeeded in 917ms », contenu exact retourné, dans le dossier jetable du produit
   (`appels/0001-A-…/stderr.txt`, lignes 79-87). Corrobore la qualification du 21 sur un second
   scénario indépendant (pas de témoin isolé cette fois, un vrai corpus dans un cycle complet) ; ne
   teste pas la lecture d'un chemin hors du corpus. Reporté dans `docs/LIMITES.md` §2, `findings.md`,
   `task_plan.md`. La formulation antérieure du bilan 3.2 (« n'infirme ni ne confirme ») était imprécise
   au vu de cette preuve : corrigée. Commité `5cd91e9`.
3. **Lot 3.3 terminé** :
   - `docs/LIMITES.md` : tableau §2 mis à jour (lecture du corpus par Codex), section « Correction
     ciblée » complétée par le paragraphe de corroboration du 22, section 4 augmentée du bilan des
     trois missions 3.2. En-tête daté au 2026-09-22.
   - **Validation complète sur `5cd91e9`** : `ruff check .` → *All checks passed*. `mypy --strict` →
     *no issues found in 48 source files*. `pytest tests` (Git Bash dans le `PATH` de la commande,
     nécessaire aux tests PWF, cf. règle du 19/09) → **576 passed, 2 skipped** (privilège de lien
     symbolique absent, connu), 220 sous-tests. `reference/cycle_sans_fournisseur.py` → rc=0.
     `git diff --check` → aucune erreur.
   - **Installation en environnement propre** : venv neuf hors dépôt, `pip install -e .` sans aucune
     dépendance tierce (conforme à la stack stdlib), `python -m iabinome --help` et le scénario de
     référence exécutés depuis ce venv, rc=0 dans les deux cas. Venv temporaire supprimé après
     vérification ; `git status` resté propre pendant tout l'essai.
   - **Version marquée** : tag annoté `v0.1.0` sur `5cd91e9`, message résumant les lots 0 à 3 et la
     porte de validation. `pyproject.toml` était à `0.1.0` depuis le lot 0, jamais tagué jusqu'ici.
   - Plan mis à jour : 3.1/3.2/3.3 cochés, Phase 4 « complete », **jalon J3 atteint le 2026-09-22**.

**J3 atteint : première livraison utilisable, `v0.1.0`.** Aucun `push` (le clone n'a pas de remote,
par choix du lot 0). Suite éventuelle : lot 4 (développement assisté), sur décision du PO — non
engagée par cette session.

## Session: 2026-09-18 — mise en place du chantier

### Current Status
- **Phase :** 1 terminée (J0 atteint le 2026-09-19) — phase 2 terminée (J1 validé), lot 2 ouvert : 2.1 fait
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

## Session: 2026-09-19 — lot 2 ouvert, point 2.1 (appels, interruptions, récupération)

J1 validé par le PO (« je valide J1, et nous ouvrons le lot 2 »). 1.4 commité (`6cf7aa4`). **2.1 non
commité** : aucune demande de commit.

### Actions Taken
- **Mesuré avant de coder** : le moteur hérité distinguait déjà `LAUNCH_FAILED` (échec de `Popen`
  observé), `CALL_POSSIBLY_PAID`, `CLI_FAILED`, `TIMEOUT`, `INTERRUPTED_BY_USER`, `CONTRACT_ERROR`,
  `DECODE_FAILED`, `INTEGRITY_MISMATCH` — mais **rien ne les expliquait** à l'humain, et sur
  `CONTRACT_ERROR`/`DECODE_FAILED` la seule sortie était un **nouvel appel payant**.
- **`incidents.py`** (nouveau) : catalogue « payé ? » (non / peut-être / inconnu / oui), sens, action ;
  pour `CLI_FAILED`, le message de l'outil cité **tel quel**, sans coût ni heure de reprise déduits.
  `decisions.next_action`/`render` et `status` s'en servent.
- **`resume --reprocess <uuid> --reason-file`** (`workflow.Reprocess`) : retraitement **local** d'une
  réponse brute conservée, sans appel ; motif exigé ; trace `retraitements.jsonl` ; données brutes
  intactes ; même table fermée que la relance ; un échec reste `ERROR`.
- **Pause à la frontière d'appel** : `workflow.run(pause=…)`, consultée entre deux appels seulement ;
  **Ctrl+C à deux temps** dans la CLI (`_PauseSwitch`) : pause (code de sortie 6), puis arrêt immédiat
  (`INTERRUPTED_BY_USER`). Les conséquences sont affichées, puis la prochaine action après chaque commande.
- Verrou : inchangé (déjà exclusif, jamais effacé quand ambigu) ; tests ajoutés au niveau CLI.
- README, `CONCEPTION_FINALE.md` §7 (amendement daté), `RULES.md` (2 règles), plan à jour.
- **Non fait, volontairement** : « appel non lancé » **prouvé après crash** est impossible (`pid.txt`
  s'écrit après `Popen`) ; seul `LAUNCH_FAILED` l'est. Aucune heure de reprise ni coût affichés.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `tests/test_incidents.py` (nouveau) | verte | 28 tests, 4 sous-tests | OK |
| Contre-épreuve 1 : retraitement non tracé | rouge | 2 échecs | OK, rétabli |
| Contre-épreuve 2 : retraiter un appel qui n'est pas en erreur | rouge | 1 échec | OK, rétabli |
| Contre-épreuve 3 : pause jamais consultée | rouge | 3 échecs | OK, rétabli |
| Contre-épreuve 4 : « payé ? » toujours « inconnu » | rouge | 3 échecs | OK, rétabli |
| Contre-épreuve 5 : message de l'outil caché | rouge | 1 échec | OK, rétabli |
| Contre-épreuve 6 : le second Ctrl+C n'arrête rien | rouge | 2 échecs | OK, rétabli |
| Contre-épreuve 7 : la pause rend le code 0 | rouge | 1 échec | OK, rétabli |
| `ruff check .` | aucun constat | All checks passed | OK |
| `mypy` strict | aucun constat | no issues in 41 source files | OK |
| `pytest tests` (porte complète) | suite verte | 457 passés, 2 ignorés, 71 sous-tests, 54 s | OK |
| Scénario `reference/cycle_sans_fournisseur.py` | rc=0, prochaine action affichée | rc=0 | OK |

### Errors
| Error | Resolution |
|-------|------------|
| Test CLI du retraitement en `ERROR` (code 4 au lieu de 0) | Mon test : B « révisait », donc A devait ensuite répondre à une objection. B accepte ; le moteur était juste |
| 4 constats `ruff` sur les nouveaux tests (lignes longues, variable inutilisée) | Corrigés |
| Un motif de patch de test trouvé plusieurs fois, script abandonné sans rien écrire | Motif rendu unique, script rejoué |

### Reste ouvert
- **2.2** (séparation des rôles) et **2.3** (liaison PWF) non ouverts.
- Le double Ctrl+C est testé avec `_thread.interrupt_main` (ce que fait le signal) : le vrai clavier
  Windows n'est pas simulé.

## Session: 2026-09-19 — lot 2, point 2.2 (séparation des rôles)

2.1 commité (`4e9a3cd`). « oui commites et continues » : 2.2 ouvert. **2.2 non commité** : aucune
demande de commit.

### Actions Taken
- **Mesuré avant de coder** : A et B tournaient avec `cwd` = dossier de collaboration (le reviewer
  atteignait `appels/`, `echanges/`, les anciennes demandes) ; `transport.run` héritait de
  l'environnement complet du parent (identifiants de session, jeton de messagerie, racine de plan) ;
  Claude ne restreignait ses outils qu'en `CONTEXT_ONLY`.
- **`isolation.py`** (nouveau) : `neutral_workdir` (dossier jetable, **copie** de `corpus/fichiers/`
  seule, supprimé après l'appel), `clean_env` (liste de refus **nominative**, insensible à la casse,
  `PWF_*`), `refused_names` (noms seuls, tracés dans `intention.json`).
- **`transport.run(env=)`** ; `workflow.new_call` lance dans le dossier neutre avec l'environnement filtré.
- **`Capabilities.enforces_read_only` / `fresh_session`** ; prévol `_require_separation` : un adaptateur
  qui ne les déclare pas est refusé avant tout appel, sans mutation, pour A comme pour B.
- **Adaptateurs** : Claude `--restricted --strict-mcp-config --no-session-persistence
  --disable-slash-commands --tools "Read,Grep,Glob"` (`""` en `CONTEXT_ONLY`) ; Codex `--sandbox
  read-only --ephemeral --ignore-user-config --ignore-rules`. Formes lues dans `--help`, **non éprouvées**.
- **`SOURCES_MODIFIED`** : contrôle complet du corpus après l'appel, avant toute lecture de la
  réponse ; réponse non retenue, `INTERRUPTED`, jamais relancé seul ; catalogué dans `incidents.py`.
- `reference/FRONTIERE_ROLES.md`, README, `CONCEPTION_FINALE.md` §8, `RULES.md` (2 règles).
- **Non fait, volontairement** : aucun confinement du système d'exploitation ; aucun essai avec une
  CLI réelle (lot 3) ; `demande.md`/`etat.json` non contrôlés *pendant* l'appel.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `tests/test_isolation.py` (nouveau) + `test_adapters.py` | verts | 40 tests | OK |
| 13 contre-épreuves (cwd = collaboration, env non filtré, liens durs, pas de contrôle post-appel, prévol neutralisé, Claude sans `--restricted` / sans `--no-session-persistence` / CONSULT tous outils, Codex sans `--ephemeral` / `--ignore-user-config`, filtre sensible à la casse, `PWF_` oublié, noms non tracés) | rouges | 13 rouges, chacune rétablie | OK |
| `ruff check .` | aucun constat | All checks passed | OK |
| `mypy` strict | aucun constat | no issues in 43 source files | OK |
| `pytest tests` (porte complète) | suite verte | 479 passés, 2 ignorés, 71 sous-tests, 58 s | OK |
| Scénario `reference/cycle_sans_fournisseur.py` | rc=0 | rc=0 | OK |

### Errors
| Error | Resolution |
|-------|------------|
| `pytest` lancé avec le Python global : `iabinome` résolu vers l'ancien projet (`C:\Projets\IAbinome`) | Toujours `.venv/Scripts/python.exe -m pytest tests` |
| Faux agent `status_marker` relisait `etat.json` en relatif : cassé par le dossier neutre | Chemin absolu `state_file` |
| E501 (docstring) et 3 erreurs mypy (`**dict[str, bool]`) | Corrigés |
| Une assertion vacue (`{"PATH","SYSTEMROOT"} & names or "PATH" in names`) | Remplacée par `assertIn("PATH", names)` |

### Reste ouvert
- **2.3** (liaison PWF facultative) non ouvert : attendre l'autorisation du PO.
- Toutes les protections sont **à mesurer avec de vraies CLI au lot 3** (liste dans `FRONTIERE_ROLES.md`).

### Correction de 2.2 — fuite Codex trouvée par la validation du PO (2026-09-19)
2.2 est **rouvert** : un agent lancé depuis un hôte Codex héritait de `CODEX_SESSION_ID`,
`CODEX_THREAD_ID` et `CODEX_PERMISSION_PROFILE`, que `clean_env` ne filtrait pas (la liste ne
couvrait que Claude, `PLAN_ID`, `PWF_*`). Ma liste venait du seul environnement de **cette**
session (un hôte Claude) : elle ne pouvait pas connaître l'autre hôte.
- **Corrigé** : les trois noms ajoutés à la liste **nominative** ; **aucun** refus global `CODEX_*`.
- **Examiné séparément, conservé** (`isolation.KEPT_ON_PURPOSE`, raison par variable) : `CODEX_HOME`
  (authentification, même sous `--ignore-user-config`), `CODEX_MANAGED_PACKAGE_ROOT` (réécrite par le
  lanceur npm — `bin/codex.js` lu ; garder ou retirer est sans effet, gardée par prudence),
  `CLAUDE_CODE_OAUTH_TOKEN`, `CLAUDE_CODE_GIT_BASH_PATH`.
- **Non observé directement** : cette session n'a aucune variable `CODEX_*` ; les noms viennent du
  signalement du PO. Dit dans `FRONTIERE_ROLES.md`.
- **Tests** : hôte Codex simulé dans `_HOST_ENV` (absence dans le processus agent, noms — jamais
  valeurs — dans `intention.json`), conservation explicite des variables d'authentification et de
  lancement, pas de refus global, insensibilité à la casse. 9 contre-épreuves rouges (chacun des
  trois noms retiré, refus global `CODEX_*`, `CODEX_HOME` refusé, `CODEX_MANAGED_PACKAGE_ROOT`
  refusé, casse, noms non tracés, valeurs tracées), chacune rétablie.
- **Résultats** : `test_isolation.py` + `test_adapters.py` 43 passés ; 9 contre-épreuves rouges ;
  `ruff` OK ; `mypy` strict OK (43 fichiers) ; `pytest tests` 483 passés, 2 ignorés, 71 sous-tests,
  57 s ; scénario de référence rc=0. **2.2 reste en cours** jusqu'à re-validation par le PO.

## Session: 2026-09-19 — lot 2, point 2.3 (liaison facultative à un plan PWF)

« on continue avec le point suivant » : 2.3 ouvert (2.2 pris comme re-validé, voir `task_plan.md`).
**2.3 non commité** : aucune demande de commit.

### Actions Taken
- **Mesuré avant de coder** le vrai `resolve-plan-dir.sh` sur des projets jetables : il rend
  **toujours 0** ; identifiant inexistant, mal formé (`../x`), ambigu (deux plans, sans épinglage),
  racine invalide → **sortie vide**. Un identifiant épinglé **sans `task_plan.md`** est rendu tel
  quel. `--check-ambiguity` imprime `PWF_PLAN_AMBIGUOUS_V1`. Hors racine explicite (`PWF_PLAN_ROOT`
  absolu) il ne résout rien sous un dossier quelconque.
- **`planlink.py`** (nouveau) : `resolve` (épingle `PLAN_ID` et `PWF_PLAN_ROOT`, sortie vide = refus,
  autre plan que demandé = refus, `task_plan.md` exigé), `link` (résout **avant** d'écrire),
  `unlink`, `read`, `summary`.
- **Commande `plan <dossier> [--link ID [--plan-root DIR] | --unlink]`** ; sans option, le résumé à
  reporter **à la main** (statut, décision, prochaine action, chemins). Lisible sans liaison.
- **Amendement du plan validé** (PO, 2026-09-19 ; d'abord signalé ici comme écart) : la liaison est
  dans `plan.json`, **pas** dans `configuration.json` — schéma à clés exactes dont dépend le cycle ;
  un fichier à part se supprime sans toucher à rien. Le cycle ne lit jamais `plan.json`. **Il n'existe
  plus d'écart ouvert sur 2.3.**
- **Environnement par rôle** : déjà couvert par 2.2 (`clean_env` retire `PLAN_ID`/`PWF_*` pour A **et**
  B) ; test ajouté pour B. Plus strict que « selon le rôle » : aucun rôle n'a besoin du plan.
- README, `CONCEPTION_FINALE.md` §7, `RULES.md` (2 règles), `FRONTIERE_ROLES.md`.
- **Non fait, volontairement** : aucune écriture dans un plan ; aucune synchronisation d'état ;
  `--check-ambiguity` non utilisé (l'identifiant est toujours épinglé, l'ambiguïté n'a pas lieu d'être).

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `tests/test_planlink.py` (nouveau) | verts | 33 tests, dont 6 sur le **vrai** script | OK |
| 10 contre-épreuves (sortie vide acceptée, `PLAN_ID` / `PWF_PLAN_ROOT` non épinglés, autre plan accepté, `task_plan.md` non exigé, code de retour ignoré, liaison écrite avant résolution, résumé bloqué par une liaison morte, `unlink` qui touche l'état, résumé sans dossier) | rouges | 10 rouges, chacune rétablie | OK |
| `ruff check .` | aucun constat | All checks passed | OK |
| `mypy` strict | aucun constat | no issues in 45 source files | OK |
| `pytest tests` (porte complète) | suite verte | 517 passés, 2 ignorés, 71 sous-tests, 62 s | OK |
| Scénario `reference/cycle_sans_fournisseur.py` | rc=0 | rc=0 | OK |

### Commits
Sur demande du PO (« fais les commites »), **deux commits** : `feat: ... (2.2)` (code, tests,
docs de 2.2) puis `feat: ... (2.3)` (code, tests, docs de 2.3, plan PWF). Les docs partagés
(README, `CONCEPTION_FINALE.md`, `RULES.md`, `FRONTIERE_ROLES.md`) ont été réduits à la part 2.2
pour le premier commit. **Le commit 2.2 seul a passé la porte complète** dans un worktree jetable :
ruff OK, mypy OK (43 fichiers), 484 tests passés, 2 ignorés, scénario rc=0. Le plan PWF (les trois
fichiers) est dans le second commit.

### Errors
| Error | Resolution |
|-------|------------|
| Ma première sonde du résolveur donnait « vide, code 0 » partout | Mon montage : sans `PWF_PLAN_ROOT` absolu, rien à résoudre hors du projet ; refait avec la racine explicite |
| Script Python passé en heredoc : `\n` devenu vrai saut de ligne, `é` mal décodé (cp1252) | Encore la règle RULES « pas de heredoc pour du code » : Edit/Write |
| Contre-épreuve « résumé sans dossier » **verte** | Un autre ligne (« Document : <dossier>/… ») satisfaisait l'assertion : test resserré sur la ligne exacte, redevenue rouge |
| Une « contre-épreuve » rouge par **erreur de collecte** (fichier de test cassé par mon heredoc) | Non comptée ; refaite après réparation |
| Patch des tests abandonné (motif absent) | Cause : décodage du heredoc ; refait par fichier |

## Session: 2026-09-19 — amendement du plan de mise en œuvre, point 2.3 (documentaire)

Décision du PO : la liaison PWF dans `plan.json` est **validée** et remplace l'exigence initiale qui
parlait de `configuration.json`. **Aucune modification de code ni de la liaison.**

### Actions Taken
- `C:\Projets\DialogForge_Next\astra\06_plan_mise_en_oeuvre.md`, point 2.3 : premier point de
  « Travail » remplacé par une liaison facultative dans un fichier indépendant `plan.json`, jamais
  requise ni lue par le cycle ; note datée du 2026-09-19 (validée par le PO), avec sa justification.
  Ce dossier n'est pas un dépôt Git : l'ancien texte est gardé hors dépôt pour le diff présenté.
- `task_plan.md` et ce compte rendu : « écart à faire valider » remplacé par « amendement validé » ;
  plus d'écart ouvert sur 2.3 ; « trancher l'écart » retiré de l'étape suivante.
- `findings.md` : la ligne correspondante ne parle plus d'un écart à faire valider.
- **Non fait, volontairement** : la liaison reste dans `plan.json` ; `configuration.json` et le code
  fonctionnel sont inchangés. **Commité** sur feu vert du PO (`docs: ...`, voir `git log`).
- Sur indication du PO : la case du plan PWF s'intitule désormais « Liaison facultative à un plan PWF
  via les scripts publics ; sortie vide traitée », et « J2 à constater » devient **« J2 atteint et validé
  par le PO le 2026-09-19 »** (`task_plan.md` : Next Step, Current Phase, statut et jalon de la phase 3).
  Le lot 3 reste à n'ouvrir que sur autorisation explicite du PO.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `rg` des mentions résiduelles de l'écart (`écart au plan`, `à faire valider`, `trancher l'écart`, `écart ouvert`) dans le plan PWF, le README, `RULES.md`, `CONCEPTION_FINALE.md`, `reference/` et le plan de mise en œuvre | aucune réserve obsolète | seules restent des négations (« plus d'écart ouvert sur 2.3 ») et la description de cette session | OK |
| `git diff --check` (dépôt DialogForge_2) | aucune erreur d'espaces | rc=0 (un avertissement LF→CRLF sur `findings.md`, sans effet) | OK |

## Session: 2026-09-19 — lot 3, point 3.1 (essais réels des adaptateurs) — EN COURS

Autorisation du PO (« peux-tu me guider pour lancer ces tests du lot 3.1 »). **Les appels ont été lancés
par le PO** avec ses accès (Claude Code 2.1.278, Codex CLI 0.155.0) ; l'assistant n'a lancé aucun appel
fournisseur (essais de diagnostic avec un nom de modèle inexistant, sans coût). Dossiers d'essai hors dépôt :
`C:\Projets\essais-3-1\collab` (A=codex `gpt-5.6-terra`, B=claude `sonnet`) et `collab-inverse` (A=claude
`sonnet`, B=codex `gpt-5.6-terra`), même demande, `max_revisions = 1`, `consult`. **3.1 n'est pas marqué fait.**

### Constatés en réel (les deux permutations, dans les deux rôles)
- **Cycles complets, aucun incident** : 4 appels chacun, tous rc=0 ; `AWAITING_APPROVAL`, B a accepté la
  version examinée. Durées d'appel : 305 s (Codex en A) et 402 s (Claude en A).
- **Drapeaux acceptés** : Claude `--restricted --strict-mcp-config --no-session-persistence
  --disable-slash-commands --tools Read,Grep,Glob` ; Codex `--sandbox read-only --skip-git-repo-check
  --ephemeral --ignore-user-config --ignore-rules`. Authentification conservée avec l'environnement filtré
  (Claude par `CLAUDE_CONFIG_DIR`, Codex avec `--ignore-user-config`). Le modèle passé par `-m` est appliqué.
- **Extraction** : prompt par stdin, réponse lue sur stdout, dans les deux sens ; contrat v2 respecté par
  les deux outils en producteur (bloc `IABINOME:REPONSES`) et en reviewer.
- **Dossier neutre** : la bannière Codex montre un dossier sous `%TEMP%` ; aucun `iabinome-*` restant après ;
  `workdir=neutre` inscrit dans chaque `intention.json`.
- **Contexte du reviewer** : le prompt de B (14,6 Ko et 19,9 Ko) contient la demande et la version examinée,
  aucune mention de `appels/`, `echanges/`, `etat.json`, `configuration.json`, `prompt.txt`.
- **Bac à sable Codex** : une commande PowerShell tentée par A a été rejetée (`exec_command failed … Rejected`).

### Non éprouvé (ne pas le déclarer acquis)
- Le **filtre d'environnement en conditions réelles** : `env_removed` vide, le terminal d'essai n'ayant aucune
  variable d'hôte. Les points 4 et 5 de `FRONTIERE_ROLES.md` restent ouverts.
- **Accès aux sources et `SOURCES_MODIFIED`** : aucun corpus dans ces essais.
- **Affichage des incidents** : aucun incident survenu.
- **Lecture par chemin absolu** par un agent en `--restricted` (point 2 de `FRONTIERE_ROLES.md`).

### Constats à trancher par le PO (rien de corrigé)
| Constat | Détail |
|---|---|
| Codex fait des **recherches web** en A | 6 recherches par appel de A (`web search:` dans le stderr), non désactivées par `--sandbox read-only`. Claude, avec `--tools Read,Grep,Glob`, n'en a pas : les deux permutations ne sont pas comparables en qualité. Contredit le choix de conception qui écarte les sources externes en V0.1 (§12.1) — à accepter ou à désactiver par un réglage explicite |
| Codex tourne en `reasoning effort: none` | `--ignore-user-config` retire `model_reasoning_effort = "medium"` du `config.toml` du PO. Options : ne rien changer, en faire un paramètre configurable, ou retirer le drapeau |
| `CLAUDE_CONFIG_DIR` choisit le compte Claude | Elle passe le filtre parce qu'elle n'est pas refusée, mais n'est pas dans `KEPT_ON_PURPOSE` : une extension du filtre pourrait la retirer sans qu'un test le voie. Petite correction proposée |
| Observation de protocole | `B-outils-003` (MAJOR) : A répond `REPORTE` (« sans accès web »), B le clôt `RESOLVED` parce que le guide qualifie désormais ces données de non établies. Le protocole a fonctionné comme conçu |

### Hors produit (environnement du PO)
- Sa fonction PowerShell `claude` (profil) ne transmet pas stdin à `claude.exe` : le tube échouait. Le moteur,
  lui, lance `claude.exe` directement. `model_a = "terra"` dans son `iabinome.toml` n'est pas un nom valide :
  `gpt-5.6-terra` (erreur 400 côté serveur, sans coût).

### Décisions du PO sur les constats (2026-09-19) et corrections faites — **commitées** (voir `git log`)
Les premières décisions (« web ouvert pour les deux ») ont été **remplacées** par les suivantes.
1. **Accès web facultatif et fermé par défaut** : réglage booléen `web_access`, **un seul pour A et B**, figé à
   `new` (`Configuration.web_access`, clé écrite seulement si vraie ; une collaboration sans clé vaut faux).
   Sans lui : Claude `--tools Read,Grep,Glob`, Codex **explicitement** `-c web_search=disabled`. Avec lui :
   Claude `+WebSearch,WebFetch` et `--allowedTools`, Codex `-c web_search=live`. `CONTEXT_ONLY` : aucun outil
   Claude, `disabled` côté Codex quoi qu'il arrive. `--web-access` / `--no-web-access`, clé `web_access` du
   fichier (booléen strict). `Capabilities.controls_web_access` exigée au prévol pour les deux rôles.
2. **Effort** : conservé, facultatif, aucun effort explicite par défaut ; **validé contre l'adaptateur** —
   Claude `low, medium, high, xhigh, max`, Codex `minimal, low, medium, high, xhigh` (`Capabilities.effort_levels`).
   Une valeur incompatible est refusée **à `new`** et **au prévol** de `run`, sans mutation ni quota.
3. **Filtrage d'environnement par adaptateur** : chaque adaptateur déclare une `EnvPolicy` (préfixes possédés,
   sessions d'hôte, variables gardées avec leur raison). Claude garde `CLAUDE_CONFIG_DIR`,
   `CLAUDE_CODE_OAUTH_TOKEN`, `CLAUDE_CODE_GIT_BASH_PATH`, `ANTHROPIC_API_KEY` et ne reçoit rien de Codex ;
   Codex garde `CODEX_HOME`, `CODEX_MANAGED_PACKAGE_ROOT`, `OPENAI_API_KEY` et ne reçoit rien de Claude ;
   `PLAN_ID`, `PWF_*` et les sessions d'hôte sont retirés à tous ; `intention.json` : noms seuls. **Effet
   de bord voulu** : `isolation.py` ne nomme plus aucun fournisseur (`CLAUDE.md` §6, non respecté en 2.2).
- **Tests** : `test_web_access.py` et `test_effort.py` (nouveaux), `test_adapters.py` et `test_isolation.py`
  réécrits en partie. **26 contre-épreuves : 25 rouges, chacune rétablie ; 1 mutant équivalent** (compter
  l'adaptateur lui-même parmi les « autres » ne change rien : sa règle de possession passe avant).
- Docs : `iabinome.toml.exemple`, README, `FRONTIERE_ROLES.md` (frontière réseau, séparation des secrets,
  points 7 à 10 à vérifier), `CONCEPTION_FINALE.md` §12.1, `RULES.md` (3 règles).
- **Aucun nouvel appel fournisseur** pendant ce travail. Les clés `web_search`, `--allowedTools` et les
  niveaux d'effort ne sont **pas éprouvés en réel**.

### Validation par Codex (2026-09-20), relayée par le PO — et suite
Codex a rejoué les vérifications de façon indépendante : 93 tests ciblés verts, suite complète 566 réussis et
2 ignorés (les 6 tests PWF réels rejoués avec Git Bash), Ruff, mypy strict (47 fichiers), scénario rc=0,
`git diff --check` ; README : 27 lignes ajoutées, aucune section supprimée. Il juge les trois décisions
correctement traduites, la liste Codex conforme à la configuration officielle OpenAI, et les points non
éprouvés correctement présentés comme des réserves d'exécution réelle. **Aucun défaut bloquant.**
- **Le hash du commit de ce lot est la référence des prochains essais réels** (voir `git log`, et la ligne
  ajoutée en fin de cette section par le commit qui suit).
- **3.1 ne sera complètement fermé qu'après le petit protocole fournisseur** couvrant les points 7 à 10 de
  `reference/FRONTIERE_ROLES.md` : `web_search=disabled|live` chez Codex (et coupure effective), `WebSearch` /
  `WebFetch` + `--allowedTools` chez Claude sous `--restricted`, niveaux d'effort acceptés, authentification de
  chaque outil sans les variables de l'autre. **Il n'est pas nécessaire de refaire les deux cycles éditoriaux
  sur la peinture.** Ce protocole consomme du quota : à lancer par le PO, sur son autorisation.
- Restent aussi, hors de ce protocole : un éventuel essai avec un petit corpus (accès aux sources,
  `SOURCES_MODIFIED`) et un essai depuis une session outillée pour éprouver le filtre d'environnement.
- **Commit de référence des prochains essais réels : `dda7a54`** (`feat: acces web facultatif, effort valide par
  adaptateur, environnement par fournisseur (3.1)`), 566 tests, 2026-09-20.

## Session: 2026-09-20 — protocole fournisseur du 3.1 (rédigé, pas lancé)

`reference/PROTOCOLE_FOURNISSEUR_3_1.md` (version 2) et `reference/lire_flux_claude.ps1` — **commités** (voir
`git log`). Version 1 rédigée à la demande du PO, puis **corrigée sur cinq points de la revue de Codex** :
1. **corpus et canari obligatoires** dans le mini-cycle (marqueur `CORPUS-3-1-OK`, fichier hors corpus
   `CANARY-HORS-CORPUS-3-1`, demande explicite de les restituer) — le canari est une **observation**, pas un
   verdict ;
2. **Claude : la preuve est le flux** `--output-format stream-json --verbose` (outils annoncés, appels,
   résultats), pas la phrase-témoin (contrôle secondaire) ;
3. **chemins complets** (`codex.cmd`, `claude.exe`) et modèle Claude précis (`claude-sonnet-5`) ;
4. **variables d'environnement sauvegardées et restaurées** (`try/finally`), dans un PowerShell jetable ;
5. **coût ramené à environ six appels** : plus d'appels dédiés à l'effort, porté par le mini-cycle
   (`--effort-a medium --effort-b high`) ; l'étape 4b reformulée (diagnostic d'un échec, pas preuve générale).
- **Éprouvé sans quota** : `new` du mini-cycle avec corpus et efforts (configuration écrite avec `effort`) ;
  création du matériel ; lecteur de flux sur un fichier synthétique ; commandes de lecture rejouées sur le
  premier essai ; motif de restauration de l'environnement — **qui a révélé un défaut de ma première version**
  (`SetEnvironmentVariable(nom, $null)` laisse une variable **vide** au lieu de la supprimer) ; corrigé, retesté.
- **Non vérifié** : le format réel du flux `stream-json` (le lecteur a été éprouvé sur un fichier synthétique).
- **Zéro quota, déjà constaté** : `claude --effort minimal` est ignoré avec un avertissement (Claude n'échoue pas).

## Session: 2026-09-20 (suite) — documentation utilisateur, 3.3 partiel — commitée (`5542ee8`)

Demande du PO : rédiger la documentation à l'usage de l'utilisateur. Proposition soumise, **quatre décisions du PO** :
ouvrir 3.3 dans ces termes ; renommage en DialogForge **à la fin du développement V2** ; README allégé (historique et
origine retirés) ; test de cohérence retenu. **Le PO n'a pas lancé le protocole 3.1** (dit dans la session).

**Livré** (aucun appel fournisseur de ma part ; sorties citées produites par `reference/cycle_sans_fournisseur.py`) :
- `README.md` : 350 → ~90 lignes, porte d'entrée. L'historique et l'origine du code passent dans `docs/DEVELOPPEMENT.md`.
- `docs/PRISE_EN_MAIN.md`, `COMMANDES.md` (8 commandes, statuts, codes, catalogue des incidents), `CONFIGURATION.md`,
  `LIMITES.md` (trois niveaux de preuve, **daté de `dda7a54`**), `DEVELOPPEMENT.md`.
- `exemples/` : demande de conception, demande de recherche, mini-corpus fictif de deux notes, `corpus.txt`.
- `src/iabinome/cli.py` : `help=` sur **toutes** les commandes et options, description et épilogue (codes de sortie) ;
  docstring corrigée (huit commandes, pas sept). Seul code touché.
- `tests/test_docs.py` (8 tests, 142 sous-tests) : chaque commande a sa section ; chaque option est nommée **dans la
  section de sa commande** ; chaque clé de réglage est dans `CONFIGURATION.md` et dans `iabinome.toml.exemple` ; chaque
  option a un texte d'aide ; les exemples passent par `new` (recherche : manifeste = les deux fichiers attendus) ; liens
  relatifs et ancres résolus.

**Vérifié** : suite complète **574 passés, 2 ignorés** (566 + 8 nouveaux), `ruff check .`, `mypy` strict (48 fichiers),
scénario rc=0, `git diff --check` propre (avertissement LF→CRLF sur `README.md`, sans effet).
**Contre-épreuves du test** : 10 mutations, **10 détectées**, chacune annulée ensuite (option retirée de `COMMANDES.md` ;
`help=` retiré ; lien cassé ; ancre cassée ; section retirée d'un exemple ; corpus pointant un fichier absent ; clé
absente de `CONFIGURATION.md` ; clé inconnue dans le `.toml` d'exemple ; commande sans section ; **option retirée de la
seule section `decide`**). **Cette dernière a montré une faiblesse de ma première version** : le test cherchait l'option
n'importe où dans `COMMANDES.md`, donc `--timeout` documenté pour `run` masquait son oubli dans `decide` ; rendu strict
par section.

**Erreur rectifiée en cours de route** : mon premier `LIMITES.md` écrivait « aucun appel réel n'a encore prouvé » pour les
options d'isolation, d'après `FRONTIERE_ROLES.md` (écrit **avant** les essais). Le journal du 2026-09-19 (plus haut)
montre qu'elles ont été **acceptées** par les deux outils en réel, avec authentification conservée ; seul leur **effet**
n'est pas mesuré. Corrigé : `LIMITES.md` distingue « accepté » de « appliqué », et cite les durées d'appel mesurées
(305 s Codex, 402 s Claude).

**Écart non corrigé, à décider par le PO** : `reference/FRONTIERE_ROLES.md` dit encore « jamais éprouvé » pour ces drapeaux
(section « Ce que le programme demande à la CLI »). À mettre à jour, ou à laisser daté.
**Protocole 3.1 : le PO décide de le lancer (2026-09-20).** Avant lancement, défaut trouvé dans le **précontrôle du
protocole** : `git diff --quiet dda7a54 HEAD -- src …` compare des commits, donc rendait `0` (« code inchangé ») alors que
l'arbre de travail portait des modifications non commitées de `cli.py` (textes d'aide) — et le mini-cycle de l'étape 5 tourne
sur l'arbre de travail. Mesuré : `HEAD` → rc 0, arbre de travail → rc 1. Corrigé : il compare l'arbre de travail, `cli.py`
exclu (aide seule, suite verte), et `git status --short` est demandé. Le hash noté par `git rev-parse` ne désigne le code
lancé que si la documentation est commitée avant.

### Protocole 3.1 exécuté par le PO (2026-09-20, soir) — résultats lus par l'assistant dans `essais-3-1\protocole`
Détail et verdicts : tableau « Résultats » de `reference/PROTOCOLE_FOURNISSEUR_3_1.md`. Aucun appel fournisseur de ma part.
- **Point 7 (Codex)** : `web_search=disabled` → 0 recherche ; `live` → 4 lignes `web search:` ; même prompt. ✅
- **Point 8 (Claude)** : fermé → outils `Glob,Grep,Read`, aucun appel ; ouvert → `WebSearch` annoncé, appelé, résultats
  réels, `permission_denials=[]`. `--allowedTools` suffit : l'étape 4b n'a pas lieu d'être. Le lecteur de flux est éprouvé
  sur un vrai flux. ✅
- **Point 9 (effort)** : Codex `reasoning effort: medium` (contre `none`), Claude `--effort high` accepté sans avertissement. ✅
- **Point 10 (secrets)** : `env_removed` conforme des deux côtés, aucune erreur d'authentification, `CLAUDE_CONFIG_DIR` gardé
  chez Claude et retiré chez Codex. ✅ (ce qui est retiré, pas ce que l'outil voit).
- **Canari** : Claude refuse (`--restricted confines the file tools to the working directory`) ; Codex refuse aussi mais pour
  la raison générale ci-dessous : **non concluant**.
- **DÉFAUT RÉEL : Codex ne lit pas le corpus.** Trois tentatives de lecture rejetées (`pwsh … Get-Content`, `rg --files`),
  chaque fois « rejected: blocked by policy ». B (Claude) a lu le corpus, constaté l'échec de A et ouvert `B-marqueur-001`
  (MAJEUR). Le contrôle préalable de l'adaptateur n'a pas détecté l'incapacité de lecture ; le workflow l'a détectée ensuite grâce au reviewer B. Causes non départagées (`--ignore-rules` ? bac à sable `read-only` sous
  Windows avec `approval: never` ?).
- **Erreur de ma part, rectifiée** : j'ai attribué à des fichiers du PO un message « Shell cwd was reset to … » qui était
  ajouté par **mon propre outil** à mes sorties (les `.err` de Claude font 0 octet). Retiré du protocole (erratum inscrit),
  et j'ai demandé au PO de chercher l'origine d'un phénomène inexistant. **Leçon : vérifier qu'une ligne est bien dans le
  fichier avant de l'attribuer** (un `grep -c` l'a montré immédiatement).
- Aide de `codex exec` (sans quota) : `--ignore-rules` = « Do not load user or project execpolicy `.rules` files ».

### Préparation de la reprise (2026-09-21) — aucune modification de code, aucun appel fournisseur
Le PO a soumis un prompt pour corriger « Codex ne lit pas le corpus » ; **six ajustements validés** avant lancement :
(1) qualifier d'abord la **couche** qui rejette — politique d'exécution (`--ignore-rules` + `approval: never`) plutôt que
système de fichiers — avec un **point d'arrêt** si un profil borné ne lève pas le rejet, car une règle `allow` peut
s'exécuter hors du bac à sable, ce qui ferait du **repli** (injection du corpus) la vraie solution ; (2) prévol au `run`,
pas au `new`, via un point d'accroche **générique** ; (3) suite de tests sans aucun `codex`, lanceur injecté ; (4) témoins
créés par le produit, jetables ; (5) estimation de taille annoncée avant d'implémenter ; (6) les contrôles sans quota du PO
sont **à refaire** (non vus par l'assistant). La correction de formulation passe en étape 0 (indépendante du prototype).
Bloc REPRISE de `task_plan.md` réécrit en conséquence. Missions Nextcloud/UrBackup **en attente**.

**Reste pour fermer 3.3** : mettre `LIMITES.md` à jour après 3.1/3.2 ; le renommage DialogForge (fin de V2, fichiers listés
dans `docs/DEVELOPPEMENT.md`) ; relire `docs/` contre les sorties **réelles** quand un cycle réel les aura produites (les
extraits cités viennent du faux agent).

## Session: 2026-09-21 — 3.1, qualification sans quota du défaut de lecture du corpus par Codex

Scope du PO : qualification seulement — **ni code de production, ni appel fournisseur, ni commit**. Session lancée depuis
`C:\Projets\DialogForge_2`. Plan résolu (`PLAN_ID=2026-09-18-dialogforge-v2`). Arbre de travail et huit fichiers modifiés
**conservés**. Aucun `codex exec`, `claude -p`, cycle ou mini-cycle ; aucune règle personnelle chargée par un appel du produit.

### Actions Taken
- **Étape 0 (documentaire)** : formulation « le cycle l'a détecté, le produit non » remplacée par « Le contrôle préalable de
  l'adaptateur n'a pas détecté l'incapacité de lecture ; le workflow l'a détectée ensuite grâce au reviewer B. » dans le
  protocole, `progress.md` et `docs/LIMITES.md` (le plan la portait déjà). Mentions « pas encore lancé » corrigées :
  `task_plan.md` (paragraphe de la phase 3) et en-tête du protocole. **L'historique n'est pas réécrit** (le titre de la session du
  2026-09-20 « rédigé, pas lancé » décrit l'état de cette session-là). `tests/test_docs.py` : 8 passés.
- **Qualification locale** avec `codex --help`, `codex sandbox`, `codex execpolicy check` seulement, dans un dossier jetable
  du scratchpad de session, supprimé ensuite. `CODEX_HOME` vide pour les essais qui n'ont pas besoin du backend élevé ;
  vrai `CODEX_HOME` (lu, jamais copié) pour les essais du backend élevé, dont les secrets (`.sandbox-secrets`) ne se copient pas.
- Aide de `codex exec` : **pas d'option `--permission-profile`** (seulement `-p` = couche de configuration sous `CODEX_HOME`) ;
  un profil se définit donc par `-c permissions.<nom>.…` + `default_permissions`. `codex sandbox`, lui, a `-P` et **pas** `--sandbox`.

### Résultats mesurés (Codex 0.155.0, Windows 11)
| # | Mécanisme | Essai | Résultat |
|---|---|---|---|
| 1 | Politique d'exécution | `execpolicy check --rules ~/.codex/rules/default.rules -- pwsh.exe -Command "Get-Content …"` (et `rg --files`) | `allow` par le préfixe `["…\\pwsh.exe","-Command"]` — préfixe très large. `cmd.exe /c type` : aucune règle |
| 2 | Politique d'exécution | mêmes commandes, fichier de règles vide | `{"matchedRules":[]}` : **aucune décision**. C'est la situation sous `--ignore-rules` ; ce que l'outil en fait ensuite (repli, `approval: never`) **n'est pas observable sans `codex exec`** |
| 3 | Fichiers | `sandbox -P :read-only`, `CODEX_HOME` vide, dossier neutre + canari voisin | corpus **lu**, canari **lu**, écriture **refusée** (`Access … is denied`, rien créé). Constat du PO **reproduit sans config personnelle** |
| 4 | Fichiers | profil `:root=none, :minimal=read, :project_roots={.=read}` (réseau coupé), backend par défaut | échec : **« Restricted read-only access requires the elevated Windows sandbox backend »** (valeurs `none` et `deny` équivalentes) |
| 5 | Fichiers | même profil, `-c windows.sandbox='elevated'` | échec : **« elevated Windows sandbox requires effective `:root` read access »** — les deux exigences se contredisent : une lecture bornée est impossible sur cette version |
| 6 | Fichiers | `:root=read` seul (élevé) | corpus lu, canari lu, écriture refusée : identique à `:read-only` |
| 7 | Fichiers | `:root=read` + refus du dossier du canari | canari **refusé**, corpus lu — **liste noire** : marche pour un chemin qu'on connaît, ne borne rien |
| 8 | Fichiers | `:root=read` + refus du scratchpad + lecture du dossier neutre (fils) | **échec du lancement** : `CreateProcessWithLogonW failed: 267` — refuser un ancêtre interdit d'atteindre le fils, l'autorisation plus précise n'est pas honorée |
| 9 | Fichiers | `icacls` après l'essai 7/8 | les refus sont des **ACL `DENY` persistantes** pour le groupe local `CodexSandboxUsers` (explicites sur le dossier refusé, héritées par les enfants), **elles survivent à la commande** |
| 10 | Approbations | `approval: never` | bannière de l'appel réel du 2026-09-20 ; **non observable localement** ; la documentation consultée ne dit rien du repli sur commande sans règle |
| 11 | `--sandbox` vs profils | — | **non confirmé** : `codex sandbox` n'a pas `--sandbox` ; la doc consultée dit seulement de ne pas les combiner, **sans préciser la priorité**. L'affirmation « `--sandbox` l'emporte », donnée comme documentée dans le prompt de reprise, **n'a pas été retrouvée** |
| 12 | Web | — | hors périmètre : clé séparée (`web_search`), déjà mesurée en réel (2026-09-20) |
| 13 | Réseau | écouteur local, `network.enabled=false` puis `true` | **non concluant** (bouclage `127.0.0.1` : `false` connecte, `true` refuse sans message). Coupure réseau **non caractérisée** |

- **Config personnelle** : `[windows] sandbox = "elevated"` y figure ; `--ignore-user-config` **l'ignore** — le backend qu'un `codex exec`
  du produit utilise n'est donc pas celui de la config du PO (non mesuré : nécessite `exec`). Le profil borné échoue de toute façon
  avec les deux backends.
- **Part de la config personnelle dans mes essais** : `codex sandbox` n'a **aucune** option pour l'ignorer ; pour les essais 5 à 9
  (backend élevé, seul disponible dans le vrai `CODEX_HOME`) elle était donc chargée, et j'ai forcé par `-c` le backend, le profil
  et le réseau. L'échec de l'essai 4 vient d'un `CODEX_HOME` **vide** : lui est indépendant de toute config. Pour les essais 5 à 9,
  l'indépendance est **argumentée** (tout ce qui compte est passé par `-c`), pas prouvée.
- **Intégrité** : empreintes SHA-256 (sans affichage) de `config.toml`, `auth.json`, `rules/`, `.sandbox-secrets/`, `sandbox*.log`
  avant/après : **73 fichiers, aucune différence**. Aucun secret copié, déplacé ni journalisé.
- **Cause la mieux étayée du rejet initial** : couche **politique d'exécution**. (a) `:read-only` lit le corpus : le système de
  fichiers n'est pas en cause ; (b) l'erreur est `Rejected(…) rejected: blocked by policy`, levée dans `CreateProcess` *avant* qu'un
  processus existe — un refus du bac à sable donnerait `Access … denied` (essai 3) ; (c) **toutes** les commandes shell observées
  sous ces drapeaux ont été rejetées (au moins 6, sur trois appels réels, y compris `Get-Content` seul), aucune n'a réussi ;
  (d) les règles du PO les autoriseraient, et `--ignore-rules` les retire. Sous-hypothèses **non départageables sans quota** :
  pas de règle `allow` sous `approval: never` ; heuristique Windows sur `pwsh -Command`.

### Conclusion (étape 6 du scope : les trois preuves ne sont pas obtenables)
Corpus lisible : oui. Canari illisible **sans le connaître d'avance** : non. Écriture impossible : oui. Le profil borné exigé
(`:root` refusé) est **refusé par les deux backends**, et même s'il passait il ne lèverait pas le rejet, qui vient d'une autre
couche. **Le prototype n'a donc pas été « testé » au sens des trois preuves** : il a été arrêté par l'échec de construction
(essais 4 et 5). Repli présenté au PO, **non implémenté**.

### Ce que les essais prouvent et ne prouvent pas
- **Prouvent** : le refus de lecture initial ne vient pas du système de fichiers ; un profil borné n'est pas constructible sur
  Codex 0.155.0 / Windows (deux messages d'erreur exacts) ; les refus de chemin sont des ACL persistantes ; les règles du PO
  autorisent les commandes rejetées ; `CODEX_HOME` du PO intact.
- **Ne prouvent pas** : le comportement d'un `codex exec` (approbations, repli sur commande sans règle, priorité de `--sandbox`,
  backend sous `--ignore-user-config`) ; la coupure réseau ; que l'échec soit le même sur une autre version de Codex ou un autre OS.

### Options soumises au PO (rien n'est implémenté) — estimations à ±30 %, sur ~4 560 lignes de `src/iabinome`
**Option 1 — repli : injecter le corpus dans le prompt de Codex (recommandée).** L'adaptateur déclare que son outil ne lit pas
le corpus par outil ; le prompt porte alors le corpus (manifeste chemin/taille/sha256, contenus délimités, plafond de taille,
non-UTF-8 refusé avant l'appel) et l'outil shell de Codex est fermé (`-c features.shell_tool=false`, déjà utilisé pour
`CONTEXT_ONLY`). Claude continue de lire par outil.
- **Production ≈ 90–120 lignes** : rendu et plafond dans `corpus.py` ≈ 40 ; bloc et phrase du prompt dans `prompts.py` ≈ 20 ;
  capacité + argv dans `adapters/base.py` et `codex.py` ≈ 10 ; passage du bloc et refus avant appel dans `workflow.py` ≈ 25 ;
  plafond réglable ≈ 10. **Tests ≈ 120–160 lignes** (rendu, plafond, binaire, argv A et B, prompt, empreintes, rejeu).
- **Risques** : coût en tokens à chaque appel (A et B, chaque révision) ; asymétrie de méthode (Claude lit à la demande, Codex
  reçoit tout) ; plafond arbitraire, un gros corpus (Nextcloud, UrBackup ?) peut être refusé ; `prompt.txt` duplique le corpus
  dans chaque dossier d'appel ; un contenu de corpus qui ressemble à des consignes (déjà vrai avec la lecture par outil).
- **Limites** : que `shell_tool=false` ferme tout n'est mesuré que pour l'équivalence avec `--disable shell_tool` ; le confinement
  « ne lit pas ailleurs » vient de l'**absence d'outil**, pas d'un bac à sable — à confirmer par l'appel unique ci-dessous.
- **En échange (POURQUOI.md, règle 2)** : le prévol au `run`, le point d'accroche générique, le lanceur injecté et les témoins
  proposés dans l'ancien bloc REPRISE (**estimés 250–400 lignes de production, plus leurs tests**) n'ont plus d'objet ; le
  contournement « confiez à Claude le rôle qui lit » et le paragraphe de `LIMITES.md` s'effacent. **Aucun code existant n'est
  retiré** : le solde reste **+100 à +120 lignes** de production.

**Option 2 — intégrer un profil de permissions (non recommandée : ne tient pas les exigences).** Variante la plus proche
constructible : `:root=read`, `windows.sandbox=elevated`, refus explicites, réseau coupé.
- **Production ≈ 30–40 lignes, tests ≈ 50–70** ; plus un prévol pour détecter l'absence d'élévation (≈ 250–400 lignes, déjà
  citées).
- **Risques/limites** : ne borne rien (liste noire) ; exige le backend élevé, installé par un administrateur — état propre à la
  machine, donc contraire à « indépendant de la machine » ; **modifie les ACL du disque de l'utilisateur** de façon persistante ;
  **ne lève pas le rejet de politique** — l'appel intégré échouerait vraisemblablement encore ; corriger cela impose de rétablir
  des règles `allow`, donc de retirer `--ignore-rules` (interdit). **Rien à retirer en échange.**

**Commande proposée pour l'unique appel Codex (à lancer par le PO après autorisation ; analysée pour la syntaxe, jamais
exécutée)**. Elle fournit le corpus dans le prompt, ferme l'outil shell et redemande le canari, avec les drapeaux du produit
(`--sandbox read-only --ephemeral --ignore-user-config --ignore-rules`). Attendu : ligne 1 = marqueur, ligne 2 = `ILLISIBLE`,
0 appel d'outil, 0 recherche web. Ce que l'appel **ne prouvera pas** : que la fermeture soit la même pour B, ni le
comportement du produit intégré ; `ILLISIBLE` seul ne dit pas *pourquoi* (lire `injection.err`).

```powershell
$codex = "C:\Users\schne\AppData\Roaming\npm\codex.cmd"
$p     = "C:\Projets\essais-3-1\protocole"
$w     = Join-Path $env:TEMP ("df-injection-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
$m     = (Get-Content "$p\corpus-source\marqueur.txt" -Raw).Trim()
$h     = (Get-FileHash "$p\corpus-source\marqueur.txt" -Algorithm SHA256).Hash.ToLower()
$prompt = @"
Reponds par exactement deux lignes, sans rien d'autre.
Ligne 1 : le marqueur du corpus, tel qu'il figure dans le bloc CORPUS ci-dessous.
Ligne 2 : le contenu du fichier $p\hors-corpus\canari.txt si tu peux le lire, sinon ILLISIBLE.

CORPUS (1 fichier, contenu fourni ici : tu n'as aucun outil pour le lire)
=== corpus/fichiers/marqueur.txt sha256=$h ===
$m
=== fin de corpus/fichiers/marqueur.txt ===
"@
try {
  New-Item -ItemType Directory $w | Out-Null
  Push-Location $w
  $prompt | & $codex exec -m gpt-5.6-terra --sandbox read-only --skip-git-repo-check --ephemeral --ignore-user-config --ignore-rules -c features.shell_tool=false -c web_search=disabled -c model_reasoning_effort=medium - 2> "$p\injection.err" > "$p\injection.out"
} finally {
  Pop-Location
  if (Test-Path $w) { [System.IO.Directory]::Delete($w, $true) }
}
Get-Content "$p\injection.out"
"appels d'outil (attendu 0) : " + @(Select-String -Path "$p\injection.err" -Pattern 'exec_command|blocked by policy').Count
"recherches web (attendu 0) : " + @(Select-String -Path "$p\injection.err" -Pattern '^web search:').Count
```

### Erreurs / effets de bord
| Erreur | Suite |
|---|---|
| **Mes essais 7/8 ont laissé des ACL `DENY` sur le dossier temporaire de la session** (le backend élevé les pose et ne les retire pas) ; l'essai suivant a échoué en 267 alors qu'il avait marché | Trouvé par `icacls` ; retiré avec `icacls … /remove:d` sur mon seul dossier temporaire, arbre supprimé, **0 refus résiduel** vérifié. Aucun chemin du PO n'a jamais été visé par un refus. Règle ajoutée dans `RULES.md` |
| L'outil de l'assistant a refusé deux scripts contenant `Remove-Item` à côté d'un chemin avec espace (faux positif) | Suppression par `[System.IO.Directory]::Delete`, restauration de variable d'environnement par `SetEnvironmentVariable` |
| Essai réseau (13) sur boucle locale : résultat incohérent | Consigné **non concluant**, pas interprété |
| Le prompt de reprise disait « confirmé par la documentation » pour la priorité de `--sandbox` | Non retrouvé dans la documentation consultée : écrit comme **non confirmé** (11) |
| Le bloc REPRISE disait « décisions d'architecture validées par le PO » | Faux : le PO ne les a pas validées ; corrigé, ce sont des **propositions** |

### Non fait, volontairement
Aucun `codex exec` (donc ni approbations, ni priorité de `--sandbox`, ni backend réel sous `--ignore-user-config` observés) ;
aucun `codex debug prompt-input` (hors de la liste des essais autorisés — **candidat** pour le PO, sans quota probable, à
confirmer) ; aucun point d'accroche, prévol ni incident ; `LIMITES.md` et `FRONTIERE_ROLES.md` non réécrits (après décision).

### Test Results
| Test | Expected | Actual | Status |
|---|---|---|---|
| `pytest tests/test_docs.py` | verte | 8 passés, 143 sous-tests | OK |
| `git status` | code de production inchangé | seuls les huit fichiers de départ + le non suivi, plus les docs éditées ici | OK |
| Empreintes de `CODEX_HOME` avant/après | identiques | 73/73 identiques | OK |

## Session: 2026-09-22 (suite) — 3.2, troisième tâche : révision d'un document existant, 3.2 clos

Sujet choisi par le PO sur ma suggestion : la note technique réelle `Aides\NextCloud\nextcloud_mise_en_place_dun_stockage_externe_local_derriere_apache_docker.md`
(241 lignes, mise en place d'un stockage externe local Nextcloud 32 derrière Apache/Docker), écartée
au profit d'une **copie anonymisée** avant tout usage — IP réelles, domaine réel
(`cloud.meteo-poelley50.fr`) et identifiant système remplacés par des exemples génériques, vérifié par
grep avant utilisation (aucune trace résiduelle). Deux autres documents disponibles écartés : un
audit trop vide de contenu concret, une checklist de sécurité réseau domestique jugée trop sensible
même anonymisée (posture pare-feu/exposition réelle).

**Collaboration** : `C:\Projets\essais-3-1\revision-nextcloud\collab`, corpus à un seul fichier
(`--source-root`/`--source-list`), `--kind conception` (le corpus sert de matière à réviser, pas de
synthèse externe), **web fermé** — premier essai réel de ce réglage par défaut sur 3.2, les deux
tâches précédentes ayant utilisé le web ouvert.

**Résultat** : cycle complet, 4 appels (A 78 s, B 153 s, A-révision 85 s, B-relecture 59 s ≈ 6 min 15 s).
**B a accepté dès le premier tour, zéro désaccord.** 6 objections soulevées et toutes résolues par la
révision d'A : diagnostics de cause requalifiés en hypothèses non étayées (boucle d'authentification,
erreur 500), `auth.confirmation.enabled=false` retiré (masquait le symptôme sans traiter la cause),
`172.16.0.0/12` retiré de l'exemple `trusted_proxies` (portée non justifiée), et surtout **le
diagnostic de permissions lui-même corrigé** : le mode affiché donnait déjà `r-x` à « other », donc ne
prouvait rien — le test doit s'exécuter sous `www-data`, pas sous l'utilisateur admin. Document passé
de 241 à 317 lignes, section finale « Ce qui a changé et pourquoi » traçant chaque changement à un
problème précis, sans reformulation générale (conforme à la contrainte posée dans la demande).

**Décision humaine** : `ACCEPTE` le 2026-09-22T15:22:18Z (`decisions.json`). Premier essai enregistré
avec un faux départ (commande composée mais Entrée non pressée) : aucun effet, `decisions.json` absent,
état intact — reconduit sans incident.

**Mesure 3.2 (3 des 3 tâches représentatives — 3.2 clos)** : résultat jugé utilisable, accepté sans
réserve dès le premier tour. Aucun transfert manuel au-delà de la préparation (anonymisation avant
dépôt dans le corpus). Vue d'ensemble des trois tâches : Nextcloud clients (4 appels, web ouvert),
pièges à souris (8 appels sur 3 tours, web ouvert, 1 correction + 1 complément après acceptation),
révision stockage externe (4 appels, web fermé, acceptée d'emblée) — 16 appels au total sur les trois
tâches, aucun défaut reproductible de perte de réponse, de version ou de reprise (seuls incidents :
deux erreurs humaines de chemin/frappe, sans effet sur l'état).

## Session: 2026-09-22 (suite) — 3.2, deuxième tâche : conception courte, avec correction ciblée

Sujet initial du PO (« application pour enregistrer les emplacements de pièges à souris avec un
schéma de zone ») recadré en séance : IAbinome produit un document, pas une application (`CLAUDE.md`
§2) — reformulé en guide de décision (solutions existantes) avec, seulement si un manque réel est
constaté, un cahier des charges borné à ce manque, explicitement hors réalisation (lot 4, après J3).
Web ouvert, par choix du PO, avant rédaction de la demande.

**Collaboration** : `C:\Projets\essais-3-1\pieges-souris` (hors dépôt, mêmes réglages que la tâche
Nextcloud : `--kind conception`, `--web-access`, `--max-revisions 1`, agents par défaut de
`iabinome.toml`).

**Premier tour** : 4 appels (A 105 s, B 107 s, A-révision 87 s, B-relecture 78 s ≈ 6 min 17 s).
Résultat : recommandation QField + QGIS (local, gratuit, historique relationnel), alternative Avenza
Maps Plus ; partie 2 activée (manque réel constaté : aucune solution ne combine plan non géoréférencé
annotable au téléphone et historique structuré). B a soulevé 8 objections dont 4 `MAJOR`/`MINOR`
résolues par la révision d'A et 4 restées ouvertes (2 `MINOR`, 2 `NOTE`) — dont une contradiction
interne réelle introduite par la révision elle-même (coût d'ArcGIS Field Maps affirmé « plus coûteux »
tout en disant son coût « non vérifié »).

**Décision humaine** : le PO a demandé Sol (`gpt-5.6-sol`) pour la correction ; refusé par construction
— `configuration.json` est écrit une fois à `new` et n'est jamais reconfiguré sur une collaboration
ouverte, `decide --correct`/`resume` n'ont pas d'option de modèle. Deux voies proposées (nouvelle
collaboration sœur avec Sol, ou `--correct` sur celle-ci avec Terra) ; le PO a choisi `--correct` avec
Terra.

**Correction ciblée** (`decide --correct`, 1 tour au-delà du plafond, `decisions.json` séquence 1,
`CORRECTION_CIBLEE`) : fichier de correction nommant les 4 objections ouvertes. 2 appels (A 70 s,
B 93 s ≈ 2 min 43 s). 3 des 4 levées — Trap.NZ (application spécialisée réelle) nommée et écartée pour
une raison sourcée, contradiction de coût ArcGIS levée sans montant non vérifié, source dédiée au
positionnement GNSS hors ligne de QField ajoutée. La 4e (`B-format-001`, longueur) s'est aggravée : en
corrigeant les trois autres, le document est passé de 4 à 5 solutions comparées et de 7 à 13 sources —
compromis fond contre forme, pas un défaut de contenu.

**Décision finale** : `ACCEPTE` le 2026-09-22T14:03:53Z (`decisions.json` séquence 2), dépassement de
longueur assumé explicitement par le PO (« pas un problème »).

**Troisième tour, après acceptation** : le PO a demandé un complément de recherche (pas une
correction) sur une version déjà `ACCEPTE` — question ajoutée, indépendante des objections closes :
quelle solution comparée est compatible avec un récepteur GPS externe centimétrique (RTK/NTRIP), et
non le seul GPS interne du téléphone. **Constat d'usage** : `decide --correct` n'est pas fermé par une
acceptation antérieure — `apply_correction` ne vérifie que `AWAITING_APPROVAL`, jamais l'absence d'une
décision `ACCEPTE` déjà consignée (`workflow.py`, `decisions.json` garde l'historique complet des deux
`ACCEPTE` et des deux `CORRECTION_CIBLEE`, dans l'ordre). Comportement voulu par la conception (« le
statut ne change pas à l'acceptation »), confirmé en réel pour la première fois ici.

2 appels (A 62 s, B 69 s ≈ 2 min 11 s). Réponse sourcée par solution : QField, Mergin Maps et ArcGIS
Field Maps documentent un récepteur externe et une précision centimétrique (RTK/NTRIP) ; Avenza
documente un GPS externe mais pas le centimétrique ; Trap.NZ ne documente ni l'un ni l'autre. **B a
accepté directement, sans nouvelle objection** — `B-format-001` (longueur) close : B distingue
explicitement l'allongement dû à la colonne demandée d'une régression du resserrement déjà validé.

**Décision finale** : `ACCEPTE` le 2026-09-22T14:24:17Z (`decisions.json` séquence 4), sans réserve.

**Mesure 3.2 (2 des 3 tâches représentatives)** : résultat jugé utilisable ; **8 appels au total sur
3 tours** (4 initiaux + 2 correction + 2 complément) ≈ 11 min de calcul fournisseur ; aucun transfert
manuel de fichier ; interventions humaines hors cycle : recadrage du sujet avant lancement (document,
pas application), refus du choix de modèle en cours de collaboration expliqué, arbitrage sur la
longueur, une question de recherche ajoutée après acceptation. Reste pour clore 3.2 : une révision
d'un document existant avec objections à traiter.

## Session: 2026-09-22 — 3.2, premier cycle réel avec la correction Windows

Reprise sans réouverture de la qualification. Demande initiale (Nextcloud, corpus PDF fourni) écartée
en séance : le web ouvert convient mieux à une question sur documentation officielle, et reconstruire
un corpus déjà accessible en ligne n'aurait rien apporté. Recadrée par le PO en séance sur un sujet
plus précis : déploiement du client de bureau Nextcloud, serveur en version 33, montée vers 34 prévue
sous peu — la version cible a été vérifiée sur disque avant rédaction (seule trace : audit local de
janvier, `32.0.3.2` — écart avec la version réelle 33 relevé par le PO, corrigé dans la demande).

**Collaboration** : `C:\Projets\essais-3-1\nextcloud-clients` (hors dépôt, `--kind conception`,
`--web-access`, `--max-revisions 1`, `agent_a`/`agent_b` par défaut de `iabinome.toml` : Codex
`gpt-5.6-terra` / Claude `sonnet`).

**Résultat** : cycle complet sans incident, 4 appels (A 110 s, B 140 s, A-révision 70 s, B-relecture
55 s — total ≈ 6 min 15 s). Plafond d'1 révision atteint normalement. B a soulevé 6 objections ; 4
résolues par la révision d'A (citation non sourcée corrigée, écart 33/34 étayé par comparaison directe
des deux pages officielles, mention AppImage non fondée retirée, source de paramètres requalifiée) ;
2 `NOTE` restent ouvertes, aucune `BLOCKING` (désaccord de forme sur des rubriques ajoutées ; désaccord
sur l'attribution d'une préconisation de stratégie de groupe à la documentation officielle).

**Décision humaine** : `ACCEPTE` le 2026-09-22T11:23:11Z (`decisions.json`), sur la version examinée
par B, sans réécriture. Les deux désaccords `NOTE` restent tels quels dans le livrable accepté — non
un défaut du moteur, l'arbitrage humain a tranché de les laisser en l'état.

**Incident d'usage, sans conséquence** : premier essai de `decide` avec un chemin relatif
(`essais-3-1\nextcloud-clients`) lancé depuis `DialogForge_2` → `[Errno 2] No such file or directory`
sur `verrou.json`. Cause : la collaboration est sous `C:\Projets\essais-3-1`, pas sous
`C:\Projets\DialogForge_2\essais-3-1` — chemin relatif erroné donné par l'assistant, pas un défaut de
`decide`. Résolu avec le chemin absolu. État de la collaboration inchangé entre les deux essais.

**Mesure 3.2 (1 des 3 tâches représentatives)** : résultat jugé utilisable par le PO (`ACCEPTE`) ;
temps d'appel mesuré ci-dessus ; aucun transfert manuel de fichier (web ouvert, aucun corpus local
chargé) ; deux interventions humaines hors cycle (recadrage du sujet avant lancement, correction du
chemin après). Reste à faire pour clore 3.2 : une conception courte et une révision avec objections.

### Qualification unique Windows du 2026-09-21 — correction ciblée approuvée

- **Code** : `CodexAdapter` ajoute uniquement sous Windows `-c windows.sandbox=elevated`; les protections existantes restent : `read-only`, `--ephemeral`, `--ignore-user-config`, `--ignore-rules`, environnement filtré et `web_search=disabled`. Modèle par défaut inchangé : `gpt-5.6-sol`.
- **Tests ciblés** : `pytest tests/test_adapters.py -q` → **31 passed** ; mocks Windows et non-Windows, avec conservation explicite de l'ordre des options `-c`.
- **Appel autorisé, unique** : `transport.run` (stdin, 60 s, environnement `clean_env`) a lancé Codex 0.155.0 dans un dossier jetable. Résultat `COMPLETED`, rc=0, 19.187 s. L'outil a lu le marqueur aléatoire et la tentative `Set-Content` du témoin a été refusée (`Access ... is denied`, rc=1). Les empreintes du marqueur et du témoin sont inchangées ; `web_search=disabled` était dans l'argv. Preuve normalisée, sans valeur d'environnement ni identifiant de session : `C:\Projets\essais-3-1\qualification-elevated-2026-09-21\preuve.txt`.
- **Limite** : cette réussite qualifie ce scénario Windows ; elle ne prouve ni confinement général de la lecture du disque ni fermeture générale du réseau. Aucun second appel n'est lancé.

- **Revue indépendante** : l'assistant principal a lu le script `C:\Projets\DialogForge_qualification\qualification.py` et le stderr original sous `call/` : `Get-Content` réussit (rc=0), `Set-Content` est refusé (rc=1). Fichiers témoins à la racine du dossier, et non un cycle A/B avec copie dans `corpus/fichiers/`. Le script utilise bien `CodexAdapter.command`, `clean_env` et `transport.run`. Les traces sont conservées à cet emplacement ; le nettoyage demandé par Terra n'a pas abouti, aucun nouvel essai n'a été lancé.
- **Validation finale** : Ruff vert ; mypy strict vert sur 48 fichiers après correction des mocks de plateforme ; pytest complet : 570 réussis, 8 ignorés (6 faute de `sh` dans le PATH de la session, 2 liens symboliques sans privilège). Relance locale de `test_planlink.py` et `test_docs.py` avec `C:\Program Files\Git\bin` ajouté au PATH de la commande uniquement : 41 réussis, aucun ignoré. Scénario `reference/cycle_sans_fournisseur.py` : rc=0. `git diff --check` sans erreur, avertissements LF/CRLF seulement. Aucun appel fournisseur supplémentaire, aucun commit.

## Session: 2026-09-22 (apres J3) — revue de documentation contre le code

**Scope demande par le PO** : confronter la documentation a l'etat reel du programme, proposer les
corrections, ou conclure qu'elle suffit. Verdict rendu : documentation utilisateur juste sur la
surface CLI, mais sept affirmations fausses hors `docs/` et une page derivee en journal.

**Confronte au code** (aucun appel fournisseur) : `COMMANDES.md` vs `cli.py` (8 commandes, toutes les
options, codes 0-6 identiques a `_EXIT_CODE` et a l'epilogue) ; statuts vs `decisions.next_action` ;
cles de `CONFIGURATION.md` vs `settings._SPEC` ; modeles et niveaux d'effort vs les adaptateurs ;
exemple de `show` vs la sortie reelle du scenario sans fournisseur (identique) ; arborescence de
`PRISE_EN_MAIN.md` §6 vs le dossier produit.

**Corrige** :
- `CLAUDE.md` §1 : le schema montrait encore `A finalise`, supprime en 1.3 (promotion). Meme erreur
  dans `iabinome.toml.exemple` (`max_revisions = 0`).
- **Taille** : ~1 500 lignes annonce dans `CLAUDE.md` §1 et §3 et `DEVELOPPEMENT.md`. Mesure :
  **3 253 lignes de code dans `src/`** (4 891 avec commentaires et docstrings), 2 968 au commit de
  depart `4a11cc7`, 7 555 en tests. **Le PO assume le depassement** (2026-09-22) : chiffre corrige
  partout, note datee ajoutee sous la regle 1 de `POURQUOI.md` (texte d'origine conserve), amendement
  inscrit dans `RULES.md`. La metrique de garde (rapport au projet servi) reste, et reste tenue.
- `iabinome.toml.exemple` : `timeout` vaut aussi pour `decide --correct`.
- Durees d'appel : `PRISE_EN_MAIN.md` §3 et `LIMITES.md` §4 ne citaient que le 19/09 (5-7 min).
  Ajout des mesures du 22 (appels de 55 s a 153 s, cycle de 4 appels ~6 min) : fourchette 1 a 7 min.
- `LIMITES.md` §4 : « Claude ignore un effort `minimal` avec un avertissement » — le programme le
  refuse desormais avant tout appel ; la phrase devient le motif de ce refus.
- `LIMITES.md` : en-tete et §2 condenses (deux paragraphes de recit du 21 et du 22 → un paragraphe
  operationnel) ; le recit d'enquete descend dans `reference/FRONTIERE_ROLES.md`. L'essai de B en
  consultation sous le backend `elevated` passe explicitement en « non mesure ».
- `PRISE_EN_MAIN.md` §6 : `provenance_demande.json` et `plan.json` manquaient ; `echanges/` contient
  aussi les reponses de A.
- `README.md` : paragraphe « il ne pretend pas savoir ce qu'il ignore » ramene a l'essentiel, le
  detail du backend Windows reste dans `PRISE_EN_MAIN.md` et `LIMITES.md`.
- `DEVELOPPEMENT.md` : « recherche externe hors perimetre » precise — l'outil n'en conduit aucune,
  les agents gardent celle de leur CLI (`web_access`, exercee en 3.2).
- **Commentaires de code perimes** : `adapters/claude.py` (x2), `adapters/codex.py` (x2) et
  `adapters/base.py` disaient encore « non eprouve en reel, lot 3 » apres les mesures des 19, 20 et 22.

**Validation** : ruff vert ; mypy strict vert (48 fichiers) ; pytest complet **576 reussis, 2 ignores**
(privilege de lien symbolique) ; `tests/test_docs.py` vert avant et apres ; scenario sans fournisseur
rc=0. Aucun appel fournisseur, aucun commit (arbre sale, en attente de decision du PO).

**Regle nouvelle** (`RULES.md`, Conduite de projet) : `test_docs.py` garantit la forme, jamais la
verite — une documentation se confronte au code et aux mesures, et les commentaires du code
vieillissent avec elle.

## Session: 2026-09-22 (suite) — la surface exposee passe a DialogForge

**Recadrage du PO** : la question n'etait pas « renommer iabinome » mais « IAbinome ne doit pas etre
expose frontalement a l'utilisateur ». Consequence : **le paquet n'est pas renomme**. Seul change ce
que l'utilisateur tape, ecrit ou lit. PyCharm n'a servi a rien : aucun import touche, aucun
`Maj+F6` (l'option etait de renommer `src/iabinome` et 25 fichiers de tests, pour un gain nul).

**Fait** :
- `pyproject.toml` : `name = "dialogforge"` et `[project.scripts] dialogforge = "iabinome.cli:main"`.
  `python -m iabinome` reste fonctionnel, volontairement absent de la documentation.
- `cli.py` : `prog="dialogforge"`, aide de `--config` reecrite.
- `settings.py` : recherche `./dialogforge.toml`, puis `~/.dialogforge/reglages.toml`, puis les deux
  anciens noms **en dernier recours**. Un ancien nom est **lu et signale** (`legacy_note`, affiche
  sur stderr avant la ligne `configuration : …`). Un seul attribut `SEARCH_PATHS` a neutraliser dans
  les tests, comme avant. Decision du PO sur les deux points (emplacement, transition).
- `isolation.py` : dossier jetable `dialogforge-…` (visible dans Temp et dans les traces relues).
- `iabinome.toml.exemple` → `dialogforge.toml.exemple` (`git mv`), en-tete reecrit ; `.gitignore`
  couvre les deux noms.
- Documentation : `README.md`, `PRISE_EN_MAIN.md`, `COMMANDES.md`, `CONFIGURATION.md` passent a
  `dialogforge` ; **les deux encadres « le package s'appelle encore iabinome » sont supprimes** ;
  `CONFIGURATION.md` gagne le motif du nom (collision dans le dossier courant + cle inconnue =
  refus) et la note sur les anciens noms ; `DEVELOPPEMENT.md` §« Nom du package » entierement
  reecrit : ce qui est expose, ce qui ne l'est pas, et pourquoi le renommage du paquet n'a plus
  d'urgence.
- Tests : 4 ajoutes (`test_settings.py`) — ordre de recherche, ancien nom lu et signale, nom courant
  silencieux, annonce sur stderr au niveau CLI. `test_docs.py` suit le nouveau nom d'exemple.

**Laisse en place, a decider separement** : les balises `IABINOME:DOCUMENT` / `QUESTION` /
`REPONSES`, visibles dans `echanges/`. Les renommer casserait `resume --reprocess` sur les
collaborations de `C:\Projets\essais-3-1` et les revues reelles rejouees par `test_objections.py` :
changement de contrat (phase a deux balises), pas un renommage.

**Validation** : ruff vert ; mypy strict vert (48 fichiers) ; pytest **580 reussis, 2 ignores** ;
scenario sans fournisseur rc=0 ; `pip uninstall iabinome` puis `pip install -e .` dans le venv, et
`dialogforge --help` verifie. Verification live de la transition : le `iabinome.toml` reel du depot
est toujours lu, avec le message « ancien nom de fichier … renommez-le en dialogforge.toml ».
Aucun appel fournisseur.

**Regles nouvelles** (`RULES.md`, Conduite de projet) : « ce qui se renomme, c'est la surface
exposee, pas le code » ; « un nom d'usage qui change laisse l'ancien lisible, et le dit ».

## 2026-09-23 — Phase 5 ouverte (GUI V1), lot 1 fait

**Demande du PO** : « passer a la mise en place de ce plan » —
`C:\Projets\essais-3-1\gui-v1\collab\livrables\version_finale.md` (conception GUI V1, cycle clos,
B `ACCEPTER`, 3 `NOTE` ouvertes, **pas de `decisions.json`** : non acceptee formellement).
Constat avant tout code : la GUI est un des cinq interdits de `CLAUDE.md` §2. Question posee au PO,
reponses : **j'ecris la decision** (il accepte lui-meme le livrable par `decide`) ; **perimetre :
plan + lot 1**.

**Decision ecrite** : `CLAUDE.md` §2 (ligne de l'interdit), `project/RULES.md` § Perimetre (regle
« la GUI V1 est une surface de plus sur le meme moteur »), `task_plan.md` (phase 5, table des
decisions, dispositions des trois `NOTE`). Conception copiee octet pour octet dans
`conception/GUI_V1.md` (sha256 `8c87908893697198dbd77e6d68a0acd61a78405233d95118ec8fa780c143ea39`).

**Lot 1** :
- Reference verte avant tout changement : 580 passes, 2 ignores.
- `tests/test_actions.py` ecrit **d'abord** : phrases de `next_action` relevees sur `ba5c0a4` pour
  12 situations (READY neuf / en pause, RUNNING, question, BLOQUANT accepte, TIMEOUT,
  LAUNCH_FAILED, CONTRACT_ERROR, AWAITING_APPROVAL, accepte, accepte puis livrable modifie,
  STOPPED), vert sur l'ancien code. Piege rencontre : deux collaborations sous la meme racine de
  test partagent la numerotation des echanges (`0002-question-A.md` au lieu de `0001`) — un
  dossier par situation.
- `decisions.py` : `ActionId`, `AllowedAction(id, may_call, local_step, primary, inputs, call_id)`,
  `accepted()`, `allowed_actions()` ; `next_action` choisit sa phrase **d'apres les actions
  permises**, plus d'apres le statut ; la phrase d'incident (ex-`incidents.action`) y est deplacee.
  Pas de `ActionId.NONE` : « aucune action principale » le dit.
- Retraits : `incidents.action`, `incidents.received` (aucun appelant), `workflow._WAY_OUT`,
  `workflow._RELAUNCHABLE` + `_Engine.relaunchable` (regle unique `incidents.relaunchable`),
  doublon « deja accepte » de `workflow.decide`.
- **Texte change, un seul** : le refus de la porte d'etat nomme desormais sa sortie via
  `next_action`. En `AWAITING_APPROVAL` : « sortie : lire `livrables/bilan.md` puis decider : … »
  au lieu de « aucune, le cycle est alle a son terme ; decision humaine : … ». En `ERROR` il
  propose aussi `--reprocess` (l'ancienne table ne nommait que `--retry-call`). Assertion de
  `test_intervention.py` adaptee (« terme » → la sortie `decide <dossier> --accept`).
- Delai : `settings.resolve_timeout(explicit, override, base)` → `Timeout(seconds, origin,
  settings)` ; `settings.load(explicit, base)` ; `cli._merge_settings` s'en sert pour
  `run`/`resume`/`decide` (sortie stderr identique). `_FALLBACK["timeout"]` supprime, aide
  derivee de `settings.DEFAULT_TIMEOUT`. 7 tests (`TestTheTimeoutOfALaunch`).
- `docs/COMMANDES.md` : ligne `resume` du tableau corrigee (`B-reprocess-012`).
- **Contre-epreuves** (mutation de `decisions.py`, script hors depot) : READY offrant ACCEPT,
  STOPPED offrant STOP, phrase d'incident sans `--stop`, RETRY principal en ERROR, correction sans
  etape locale — **5 vues sur 5**, fichier restaure.

**Validation** : ruff vert ; mypy strict vert (49 fichiers) ; pytest **595 passes, 2 ignores** ;
scenario sans fournisseur rc=0 ; `git diff --check` propre. **Taille** : 3 282 → 3 365 lignes de
code effectif dans `src/` (+83 ; compteur tokenize sans docstrings, le meme sur `HEAD` et l'arbre —
il donne 3 282 pour `HEAD` la ou le releve de J3 disait 3 253 avant `9a9824c` : comparer les
deltas, pas les absolus). Aucun appel fournisseur. **Non commite.**

**Commit du lot 1** (demande du PO « commites puis continues ») : `38abbca` (code, tests,
`COMMANDES.md`) et `12b4b8e` (decision, conception, plan).

## 2026-09-23 — Lot 2 GUI : `ExecutionControl`

- `transport.ExecutionControl` : `pause_requested`, `interrupt_requested` (`threading.Event`),
  `stopping()`. `transport.run(control=…)` : `_wait` teste l'interruption a chaque tour, comme le
  delai → `_terminate_tree`, `INTERRUPTED_BY_USER`. Le `except KeyboardInterrupt` reste, en filet.
- `workflow.run(control=…)` remplace `pause: Callable` ; frontiere d'appel : `control.stopping()`
  → `READY`. `_Engine.control` ; `new_call` leve `workflow.Stopped` si l'interruption est deja
  posee, **avant toute ecriture de l'appel** (verrou rendu, `etat.json` intact).
- `cli._CtrlC` remplace `_PauseSwitch` : 1er signal = pause (message inchange), 2e = interruption ;
  plus aucune exception depuis le gestionnaire. `_drive` attrape `workflow.Stopped` au lieu de
  `KeyboardInterrupt` (meme message, code 6).
- Tests : `tests/test_control.py` (7) — transport interrompu depuis un autre fil ; pause ignoree
  par le transport ; moteur **dans un fil secondaire** : pause pendant l'appel de A (A applique,
  `READY`, 1 seul appel lance), interruption pendant l'appel (`INTERRUPTED_BY_USER`), interruption
  avant l'appel (`Stopped`, 0 appel, etat intact, verrou rendu), interruption entre deux appels
  (`READY`) ; CLI : arret demande avant tout appel = code 6, 0 appel. Tests existants adaptes
  (`test_incidents.py` pause et Ctrl+C, `test_actions.py`). Le test reel « deux `interrupt_main` »
  passe inchange.
- Erreur de test corrigee : ma premiere condition « entre deux appels » (`launched_calls >= 1`)
  etait vraie **pendant** l'appel de A — le transport l'interrompait. Remplacee par la phase
  publiee.
- **Contre-epreuves** (script hors depot, sources restaurees) : transport sans test
  d'interruption, moteur sans test de frontiere, `new_call` sans test d'interruption, second
  Ctrl+C inoperant — **4 vues sur 4**.

**Validation** : ruff vert ; mypy strict vert (50 fichiers) ; pytest **602 passes, 2 ignores** ;
scenario sans fournisseur rc=0 ; `git diff --check` propre. **Taille** : 3 365 → 3 379 (+14 ; +97
depuis le debut de la phase 5). Aucun appel fournisseur. **Non commite.**

**Commit du lot 2** (demande du PO) : `6c77953`. Reprise preparee dans `task_plan.md` § Next Step :
references du lot 3, briques deja disponibles, deux questions a poser au PO (point d'entree de la
GUI, emplacement des recents). Mesure : Tkinter 8.6 present dans le `.venv`, `Tk()` masquee
utilisable sous Windows.

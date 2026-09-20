# Progress Log — DialogForge V2

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

## Session: 2026-09-20 (suite) — documentation utilisateur, 3.3 partiel — **NON COMMITÉE**

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

**Reste pour fermer 3.3** : mettre `LIMITES.md` à jour après 3.1/3.2 ; le renommage DialogForge (fin de V2, fichiers listés
dans `docs/DEVELOPPEMENT.md`) ; relire `docs/` contre les sorties **réelles** quand un cycle réel les aura produites (les
extraits cités viennent du faux agent).

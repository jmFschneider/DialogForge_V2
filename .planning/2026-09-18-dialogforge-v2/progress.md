# Progress Log — DialogForge V2

## Session 2026-10-04 — Runner agent unique, R2 (mandat entier, ligne finale, boucle commune)

- R1 commité (`0436bb7`). `core.run_agent` devient la boucle unique de la CLI, du pont et de la GUI : prompt = consigne du §4 (dont « travaille seul », la ligne finale, et l'écart du « passage de relais » de l'export) + export entier + validations ; `RESTE` → nouvel appel, `CANDIDAT` → validations, `INTERVENTION`/ligne illisible → `Paused`, `TIMEOUT` d'appel ou durée écoulée → `Paused`. `ValidationFailed` couvre aussi espace non propre et absence de commit, et son message (avec l'extrait de sortie) devient le « Défaut du candidat à corriger » du prompt suivant. Les validations prennent `min(délai, temps restant)`.
- **Export inchangé, volontairement** : modifier son texte aurait rendu méconnaissables `export-001` de Mastermind et sa référence d'exécution (R1 n'aurait plus trouvé le paquet).
- Retirés : `MAX_AGENT_CALLS`, `RunnerRequest.max_calls`, `_run_calls` (GUI), option `--lot` et paramètre `lot` de `prepare` ; une exécution avec `input/lot.md` est refusée pour tout nouvel appel (consultable). Pont : code `pause` pour `Paused` (au lieu de `validation_failed`). `inspect_run` rend `verdict` (ligne finale du dernier appel réussi), `lot`, et le bilan pris en fin de sortie. `CLAUDE_TOOLS` nommé, sans outil de délégation.
- Session GUI : un paquet est aussitôt remis dans `code/` (`delivery.deliver` dans le fil de la session) ; étapes « Prêt à essayer », « En pause », « Arrêté » ; un refus de remise garde le paquet et l'explique.
- Tests au faux A (modes `reste`, `toujours-reste`, `intervention`, `puis-intervention`, `illisible` ajoutés ; ligne finale dans tous les modes) : RESTE puis candidat, intervention et ligne illisible sans validation ni relance, durée bornante, exécution `lot.md` refusée, outils sans délégation, échec de validation renvoyé à A puis pause, modification utilisateur dans `code/` conservée, dossier `revues/` jamais créé. `FlowCase` fait désormais une vraie remise (`runner_support.local_delivery`). Contre-épreuve : `RESTE` neutralisé → 2 tests échouent ; restauré.
- Mesure : `src/` 9 117 → 9 143 (+26 ; `core.py` +45 dont la consigne, `runner_session.py` −16) ; façade + GUI **2 685 / 2 700**.

## Session 2026-10-04 — Runner agent unique, R1 (remise et acceptation)

- PO : découpage R1 remise → R2 continuation → R3 écran validé, « n'attends pas mon accord » ; un commit par lot. Travail antérieur commité d'abord : `4365598` (lots 3, correctif, 4), `0814ec1` (conception et analyses).
- `delivery.py` réécrit autour de la remise : `deliver` (paquet copié sous `paquets/NNN`, bundle sous `candidats/`, branche `dialogforge/candidat-NNN` extraite dans `code/` ; copie d'essai distincte pour un dépôt existant ; arrêt sans écrasement si l'espace d'essai est modifié), `current` (version remise relue sur Git et le paquet, sans état copié), `accept` (commit essayé seulement, fast-forward depuis la base ou une version acceptée, divergence = humain, reçu `integrations/`). Retirés : `create_review`, `review_for`, `_link_review`, `review_context`, `integration_preview`, `can_integrate`, `integrate_candidate` et le bouton « Intégrer ce candidat » du suivi.
- `core.bundle_candidate` : le bundle désigne la tête du paquet par `refs/dialogforge/<id>` ; il n'exige plus que le clone soit encore à cette tête ni le stade « paquet » (une trace 401 ultérieure bloquait Mastermind). `executions` : clé facultative `projet.branche` (branche cible notée à la première remise), anciennes références lues telles quelles.
- Écran Runner : « Remettre dans code/ » et « Accepter cette version » (confirmation), statut « Prêt à essayer » avec dossier, branche, commit et environnement vérifié.
- Mastermind **sur copie** (mission copiée dans le scratchpad, dossier Runner copié sous `/tmp` d'Ubuntu, référence de la copie réécrite) : `inspect` réel par le pont WSL (`paquet`, 8 appels, 7 collectes), remise de `dde9eaa` sur `dialogforge/candidat-001`, `node --test` sous Windows depuis `code/` : 23/23 ; acceptation sur une seconde copie : `master` → `dde9eaa`, reçu écrit. Mission réelle et son dossier Runner non modifiés ; aucun agent appelé.
- Tests : `test_delivery.py` réécrit sur le vrai parcours (`FlowCase`, faux agent) — remise, idempotence, modifications utilisateur conservées, commit essayé seul acceptable, correction après acceptation (avance depuis la version acceptée, ancienne branche conservée), divergence, dépôt existant (copie d'essai, dépôt utilisateur avancé seulement à l'acceptation). Fichiers Runner/GUI ciblés : 109 passés.
- Mesure (`tools/measure_development.py`) : `src/` 9 136 → 9 114 (**−22**, dont −3 d'artefact `modeles.toml`) ; façade + GUI **2 700 / 2 700** ; plus grande vue `creation.py` 385.

## Session 2026-10-04 — conception Runner recentrée sur la simplicité

- À la demande du PO, rédaction de `conception/RUNNER_AGENT_UNIQUE.md` : A seul réalise et contrôle toute la conception acceptée ; validations existantes, remise locale puis essai et acceptation humaine. Aucune sélection de lot partiel dans ce parcours.
- Retirés de la cible précédente : mesure de progression, registre supplémentaire de candidats, reprise générale et contrat JSON de fin d'appel. Une ligne finale à trois issues suffit ; le bilan reste libre. Réemploi des exports, clones, traces, paquets, bundles et références actuels.
- Règle de travail précisée : une suggestion de revue ne devient pas une exigence sans besoin démontré ; plusieurs analyses servent à choisir, pas à cumuler leurs précautions. Analyse finale annotée comme historique ; plan et règles orientés vers la nouvelle proposition.
- Contrôles documentaires : liens locaux, blocs Markdown, absence d'espaces en fin de ligne et cohérence avec le périmètre A seul. Aucun code, test d'implémentation, appel fournisseur ou mission réelle modifié/exécuté.

## Session 2026-10-04 — révision impérative : Runner avec A seul

- Le PO confirme la source Astra V2 et impose un seul agent pour la réalisation et le contrôle du code : A. Aucun B, agent de revue facultatif ou sous-agent délégué. Cette décision remplace la recommandation de la synthèse précédente, conservée ci-dessous comme historique.
- `schema_dialogforge_analyseFinale.md` révisé dans son ensemble : parcours, mandat, contrôle par A, continuation, authentification, preuves, lots et recette Mastermind. Les validations locales ne sont pas des appels agent ; plusieurs appels au même A restent possibles pour poursuivre ou corriger.
- Décision consignée dans `task_plan.md` et `project/RULES.md`. Les étapes documentaires amont ne sont pas redéfinies ; aucun code ni mission réelle modifié.
- Vérification documentaire : recherche des références résiduelles à B et des appels de revue, contrôle des liens et blocs Markdown ; aucun appel fournisseur ni test d'implémentation.

## Session 2026-10-04 — synthèse finale des propositions Runner

- Document demandé : `schema_dialogforge_analyseFinale.md`, rédigé après lecture intégrale d'Opus V2 et d'Astra V2. `schema_dialogforge_analyseFable_V2.md` absent du dépôt ; hypothèse de correspondance explicitée, sans renommer les sources.
- Arbitrage recommandé : revue B directe dans la cible complète, accès aux candidats historiques dès le premier lot, résultat de fin d'appel minimal, durée commune CLI/GUI, remise puis acceptation du commit essayé. Les recommandations ne sont pas enregistrées comme décisions du PO.
- Vérification documentaire : liens locaux présents, blocs Markdown équilibrés, UTF-8 et espaces de fin de ligne contrôlés ; `git diff --check` sans erreur. Lecture ciblée du code courant ; aucun code modifié, test d'implémentation ou appel fournisseur exécuté, aucune mission réelle touchée.
- Plan : prochain examen de la proposition signalé ; statuts des lots de développement inchangés. Aucune règle nouvelle ajoutée à `project/RULES.md` avant acceptation.

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

## 2026-09-23 — Lot 3 GUI : accueil, récents, ouverture, suivi en lecture seule

**Scope de session déclaré** : ouvrir le lot 3 (5.3), tel que préparé dans `task_plan.md` § Next
Step. Les deux questions laissées ouvertes par la conception ont été posées et tranchées par le PO
avant tout code : point d'entrée = sous-commande `dialogforge gui` (pas de script séparé) ;
fichier des récents = `~/.dialogforge/recents.json` (la proposition de la conception).

**Fait** :
- `src/iabinome/facade.py` (nouveau) — façade commune CLI/GUI (§10.1) : `inspect_collaboration(path,
  *, owned_by_this_gui=False, runner_alive=None) -> CollaborationSnapshot`. Relit intégralement
  `configuration.json`/`etat.json` à chaque appel (§3.3, jamais de cache) ; `InspectionError` nomme
  un dossier illisible sans le réparer (§5.1). L'instantané (§10.3) porte : la décision courante et
  si elle s'applique encore à la version sur disque (réutilise `decisions.applies_to_current`), le
  texte d'incident (`incidents.explain`), le délai résolu contre le **parent** du dossier de
  collaboration (§6.4), l'observation d'exécution (jamais d'activité animée sans preuve qu'*une*
  fenêtre possède l'exécution — §7.2, paramètres fournis par l'appelant, absents en lot 3), et une
  présentation : labels de statut/phase/activité, `allowed_actions` repris tel quel de
  `decisions.allowed_actions` (aucune règle dupliquée), documents lisibles qui existent réellement
  sur disque, `phase_steps` (barre de progression §7.1 : ✓ current ● à venir ○ arrêté ! sans objet
  —, calculée en dehors de Tkinter pour rester testable sans Tk — §15.1), et `next_action_text`
  (`decisions.next_action`, la même phrase que la CLI).
- `src/iabinome/gui/` (nouveau paquet, ~470 lignes effectives) :
  - `recents.py` — préférences non métier : chemins absolus et date d'ouverture seulement, jamais
    de statut ni de phase en cache (§5.2) ; écriture atomique ; une lecture corrompue rend une
    liste vide plutôt que lever (AC-05 : le fichier se supprime sans effet sur les collaborations).
  - `controller.py` — navigation dans une seule fenêtre (§4) ; pas de fil moteur ni
    d'`ExecutionControl` : rien ne les consomme avant le lot 5 (façade construite avec son
    consommateur, comme au lot 1). `open_collaboration` est strictement en lecture (AC-02) :
    inspecte avant de naviguer, montre un message d'erreur et reste sur l'accueil si le dossier est
    invalide, sans jamais l'écrire.
  - `views/accueil.py`, `views/suivi.py`, `views/stub.py` — l'écran de suivi est **en lecture
    seule** : aucune des actions de `allowed_actions` n'est câblée à `workflow.run` ; seul le texte
    de la prochaine action est affiché (§8.6-8.8 restent au lot 5). Le bouton « Nouvelle
    collaboration » ouvre `StubView`, qui se nomme honnêtement plutôt que de ne rien faire — le
    formulaire réel est le lot 4.
  - `app.py` — point d'entrée `run()` (fenêtre, taille minimale, `mainloop`).
- `cli.py` — sous-commande `gui` (`cmd_gui`), `tkinter` importé seulement dans la fonction : la CLI
  n'en dépend pas pour ses huit autres commandes. Docstring de module mis à jour (neuf commandes).
- `docs/COMMANDES.md` — section `## gui`, ligne de tableau, compte de commandes mis à jour.

**Tests** :
- `tests/test_facade.py` — sans Tk (§15.1), en réutilisant les situations de `tests/test_actions.py`
  (READY neuf/en pause, RUNNING, question, incidents, accepté, accepté-puis-modifié, arrêté) :
  `allowed_actions` de l'instantané est **identique** à `decisions.allowed_actions` pour chaque
  situation ; l'activité d'un `RUNNING` non possédé par cette fenêtre reste honnête ; le sous-état
  « Version acceptée » apparaît seulement si la décision porte sur la version courante ; les
  documents lisibles n'incluent que ce qui existe réellement ; un dossier absent lève
  `InspectionError`. `phase_steps` testé séparément : une acceptation immédiate marque « Révision A »
  `—` (jamais eu lieu), une révision qui a tourné se marque `✓` une fois close, la phase courante se
  marque `●` (ou `!` sous `WAITING_HUMAN`).
- `tests/test_gui_recents.py` — sans Tk : enregistrement, remontée en tête sans doublon, liste
  bornée, suppression du fichier sans effet sur une collaboration réelle, lecture tolérante à un
  fichier corrompu ou de forme inattendue.
- `tests/test_gui_views.py` — racine `Tk()` masquée, partagée par le module (mesuré fonctionnel
  sous Windows). Boutons trouvés par leur texte et invoqués par `.invoke()` (un vrai événement Tk,
  pas un appel direct de méthode) : ouverture d'un récent, ouverture par sélecteur de dossier
  (`filedialog.askdirectory` moqué — jamais de vraie boîte de dialogue dans la suite), dossier
  invalide nommé sans navigation, bouton « Nouvelle collaboration » vers le repère du lot 4, lecture
  d'un document dans le visualiseur (`state="disabled"`), `Actualiser` sans écriture, retour à
  l'accueil.
- **Vérifié en réel, hors suite de tests** : la collaboration produite par `reference/cycle_sans_
  fournisseur.py` (faux agents, `decide --accept`) s'ouvre dans le contrôleur GUI et affiche bien
  « Version acceptée », avec les bons documents listés — la compatibilité CLI→GUI du §15.4 tenue en
  pratique, pas seulement en test unitaire.

**Validation** : ruff vert ; mypy strict vert (62 fichiers, y compris `tests/`) ; pytest complet
**637 passés, 2 ignorés** (+35 depuis le lot 2) ; scénario sans fournisseur rc=0 ; `dialogforge
--help` liste `gui`. **Taille** : 474 lignes effectives ajoutées (`facade.py` + `gui/`), 3 379 →
3 851 dans `src/` (plafond §11 : +900 pour l'ensemble de la GUI, lots 3 à 6 compris — large marge
restante). Aucun appel fournisseur. **Non commité** : aucune demande de commit reçue cette session.

**Non fait, volontairement** : `create_collaboration` (lot 4) ; toute intervention qui mute le
cycle — répondre, relancer, retraiter, corriger, décider, démarrer (lot 5) ; suppression d'un
récent (§5.1 ne demande que « Ouvrir » et « Afficher dans le dossier »).

**Commité dans la même session, après un premier essai manuel du PO** : `223c04a` (code, tests,
`COMMANDES.md`) et `89ba64b` (plan, `RULES.md`).

## 2026-09-23 (suite) — Lot 4 GUI : création, premier fil moteur

Enchaînement demandé par le PO (« on continue ») après le commit du lot 3. Scope du lot 5.4 —
formulaire de création, provenance compatible, configuration/lancement séparés, créer seul, créer et
démarrer — repris tel que préparé dans `task_plan.md` § Next Step.

**Fait** :
- `iabinome/registry.py` (nouveau) : `ADAPTERS`, une seule instanciation partagée. `cli.py` et
  `iabinome/gui/` l'importent tous deux ; `mock.patch("iabinome.gui.controller.ADAPTERS", …)` reste
  le point de substitution côté tests, comme `cli.ADAPTERS` déjà.
- `facade.py` : `create_collaboration(request: CreationRequest, *, adapters) -> CreationResult`,
  `DemandeSource`, `CreationError`. Reprend **exactement** les vérifications et l'écriture de
  l'ancien `cli._build_new` (existence du dossier, corpus racine/liste ensemble, recherche sans
  corpus, effort par adaptateur, `Configuration`/`State`, tmp + renommage atomique) — `cli.cmd_new`
  délègue désormais à cette fonction ; `_build_new`, `cli._write_json`, `cli._now` supprimés, devenus
  sans appelant. `corpus.CorpusError` retiré de `cli._BORDER_ERRORS` : absorbé par la façade, plus
  jamais visible depuis la CLI.
  **Contre-épreuve de non-régression** : suite complète rejouée après le refactor avant d'ajouter le
  moindre test neuf — 637 passés, identique au chiffre d'avant (`tests/test_cli.py`,
  `tests/test_effort.py` inchangés, verts).
- `iabinome/gui/views/creation.py` (nouveau, remplace `views/stub.py`, supprimé) : dossier (texte +
  sélecteur), demande (saisir/importer, la source affichée change avec la provenance §6.2), type
  (bascule le bloc corpus, AC-08), agents (combobox sur `registry.ADAPTERS`), révisions, corpus
  (recherche seulement), réglages avancés repliables (modèle/effort par rôle, accès web, accès du
  critique — §6.3) et réglages du prochain lancement repliables (fichier explicite, surcharge de
  délai, bouton « Résoudre » qui affiche délai effectif + origine sans rien créer — §6.4, AC-10) ;
  validation locale (dossier/demande/révisions) puis autoritaire via la façade, refus affiché en
  place, formulaire intact (AC-12).
- `iabinome/gui/dialogs.py` (nouveau) : `confirm()`, modale bloquante à boutons nommés — jamais un
  `messagebox.askyesno` générique (§3.5). Utilisée par « Créer et démarrer » (agent, phase
  « proposition initiale », délai effectif, origine — AC-11) et prête pour les confirmations du
  lot 5.
- `iabinome/gui/controller.py` : **premier fil moteur côté GUI**. `start_run(path,
  timeout_seconds=…)` lance `workflow.run` dans un `threading.Thread` daemon avec un
  `ExecutionControl` propre ; `is_running`, `run_error` (ce que le fil a rapporté s'il s'est arrêté
  **avant tout appel** — adaptateur absent, effort refusé) ; `has_active_run`,
  `interrupt_active_run` pour la fermeture. Un seul fil à la fois : un second `start_run` sur le même
  dossier pendant qu'un premier tourne est un no-op (§3.1, mesuré par contre-épreuve).
- `views/suivi.py` : `_refresh` passe `owned_by_this_gui=controller.is_running(path)` à la façade,
  se reprogramme via `self.after(500, self._refresh)` tant que le fil tourne, s'arrête d'elle-même à
  la fin ; le message d'un lancement resté sans appel (`run_error`) s'affiche dans le bloc activité.
  `destroy()` annule le rappel programmé — jamais un `after()` sur un widget disparu.
- `app.py` : `WM_DELETE_WINDOW` → `_on_close`. Sans exécution active, ferme tout de suite. Avec une
  exécution active : `dialogs.confirm` propose seulement **continuer à suivre** (annuler) ou
  **interrompre et fermer** — la troisième branche du §9.3 (pause puis fermeture différée) demande
  d'attendre le fil sans geler Tk, repoussée au lot 5.

**Tests** :
- `tests/test_facade_creation.py` — sans Tk : chaque refus de `test_cli.py`/`test_effort.py` rejoué
  directement sur `create_collaboration` (dossier existant, corpus mal apparié, recherche sans/avec
  corpus vide, adaptateur inconnu, effort refusé), plus l'atomicité (rien ne reste sur un refus, y
  compris un fichier de corpus introuvable en cours de copie) et la provenance (`fichier` vs
  `cadrage`, `missing_sections`).
- `tests/test_gui_creation.py` — racine Tk masquée : la demande reste visible saisie ou importée
  (AC-06), un import modifié repasse en `cadrage` (AC-07), le bloc corpus n'apparaît qu'en recherche
  (AC-08), créer seulement produit `READY` à zéro appel (AC-13) ou refuse sans rien laisser (AC-12),
  créer et démarrer distingue la création locale du lancement (AC-14), annule sans rien créer si la
  confirmation est refusée, nomme agent/phase/délai/origine dans cette confirmation (AC-11), et
  n'écrit jamais le délai dans `configuration.json` (AC-10). Boutons trouvés par leur texte et
  invoqués par `.invoke()`, comme au lot 3.
- `tests/test_gui_execution.py` — le moteur tourne **dans un vrai fil**, comme `test_control.py`
  côté CLI (un `FakeAdapter` reste un vrai sous-processus) : un cycle complet atteint
  `AWAITING_APPROVAL`, un second `start_run` concurrent n'ouvre pas de second fil, un refus de
  prévol (aucun adaptateur) se rapporte sans toucher `etat.json`, une interruption en cours d'appel
  passe par `INTERRUPTED`, `has_active_run` suit fidèlement le fil, l'écran de suivi cesse de se
  reprogrammer une fois le fil terminé. La garde de fermeture (`app._on_close`) testée aux trois cas
  (rien à fermer, annulation, confirmation) avec des doublures — pas de vraie fenêtre nécessaire.
- **Vérifié en réel, hors suite de tests** (script jetable, faux agents, jamais de vrai fournisseur) :
  formulaire rempli → « Créer et démarrer » → confirmation → dossier créé → écran de suivi →
  2 appels lancés dans le fil secondaire → « Cycle terminé — décision requise » affiché après la fin
  du fil. La même preuve que le lot 3 avait faite pour l'ouverture, faite ici pour la création.

**Validation** : ruff vert ; mypy strict vert (67 fichiers) ; pytest complet **672 passés, 2
ignorés** (+35 depuis le lot 3) ; scénario sans fournisseur rc=0. Aucun appel fournisseur. **Non
commité au moment d'écrire ceci** — voir plus bas.

**Trouvé, non corrigé** : `corpus.build()` avec une liste source vide ne crée jamais le dossier
`corpus/` avant d'y écrire `manifeste.json` — `FileNotFoundError`, jamais le
`ValueError("corpus vide pour une mission de recherche")` qui semblait accessible juste après.
Branche morte préexistante au lot 4 (le refus reste correct : rien n'est créé, code 1) ; repéré en
écrivant une contre-épreuve qui vérifiait le message exact plutôt que le seul résultat. Signalé dans
`task_plan.md` (Errors Encountered) pour décision séparée — corriger `corpus.py` est hors du
périmètre de ce lot.

**Mesure de taille et décision du PO** : compteur cohérent (hors commentaires/docstrings) rejoué à
chaque frontière de lot depuis `ba5c0a4` (juste avant la phase 5, 3 274 lignes) jusqu'à l'état
courant (4 320 lignes) : lot 1 +83, lot 2 +14, lot 3 +480, lot 4 +469 — total +1 046, contre le
plafond de +900 fixé par `conception/GUI_V1.md` §11. Signalé au PO avant toute autre action (« un
dépassement n'est pas accepté silencieusement »). **Décision du PO (2026-09-23)** : le plafond de
croissance nette dans `src/` est porté à **2 500 lignes** — le chiffre initial était trop bas, pas le
lot 4 trop large. Amendement daté écrit dans `conception/GUI_V1.md` §11 et `project/RULES.md`
(texte d'origine conservé, note ajoutée). Le plafond de 1 200 lignes logiques (façade + `gui/`) reste
inchangé, non approché (~1 000 lignes).

**Non fait, volontairement** : toute intervention qui mute un cycle en cours — répondre, relancer,
retraiter, corriger, accepter, arrêter (lot 5) ; la branche « pause puis fermeture » du §9.3 (lot 5).

**Commité dans la même session, sur demande du PO (« fais le commit, puis continues avec les
suivants »)** : `78399c0` (code, tests) et `414bc95` (plan, conception amendée, `RULES.md`).

## 2026-09-23 (suite) — Lots 5 et 6 GUI : interventions, décisions, recette

Enchaînement demandé par le PO après le commit du lot 4 (« continues avec les suivants »). Les deux
derniers lots de la phase 5 sont faits dans la même session : le lot 5 (interventions et décisions,
5.5) puis le lot 6 (recette, 5.6), sans repasser par le PO entre les deux — la demande couvrait
explicitement « les suivants ».

### Lot 5 — interventions et décisions (§8)

**Fait** :
- `iabinome/gui/dialogs.py` : `prompt_text(parent, title, label) -> str | None` (invite
  **multiligne**, `ScrolledText` — une réponse ou un motif ne tiennent pas sur une ligne, contre
  `tkinter.simpledialog.askstring`) ; `choose(parent, title, body, options) -> str | None` (plus de
  deux issues, pour la fermeture à trois branches).
- `iabinome/gui/views/intervention.py` (nouveau) : `run(parent, controller, path, action)` — invite
  le texte requis par `action.inputs` s'il y en a un, confirme (§3.5) si `action.may_call`, sinon une
  confirmation simple pour `STOP` seul (décision définitive) ; puis applique. `ACCEPT`/
  `ACCEPT_WITH_RESERVES`/`STOP` appellent `workflow.decide` **directement** (local, sous verrou,
  synchrone — jamais de fil, `may_call=False` le dit déjà) ; `ANSWER_AND_RESUME`/`RETRY_CALL`/
  `REPROCESS_AND_RESUME`/`CORRECT` écrivent le texte dans un fichier jetable (`tempfile.mkstemp`,
  jamais dans la collaboration) puis appellent `Controller.start_run(path, intervention=…)`.
- `iabinome.gui.controller.Controller.start_run` étendu d'un paramètre `intervention` optionnel —
  le même fil que « créer et démarrer » (lot 4), sans reconstruction ; `workflow.Stopped` n'est plus
  confondu avec un échec (`except workflow.Stopped: pass` avant le `except Exception` générique).
- `views/suivi.py` : une rangée de boutons, un par `AllowedAction` de
  `snapshot.presentation.allowed_actions`, étiqueté par `intervention.label(action.id)` — aucune
  seconde table, la même que la façade rend déjà.
- `app.py` : troisième branche de fermeture (§9.3) — « terminer l'appel courant, mettre en pause,
  puis fermer » pose `pause_active_run()` puis attend `has_active_run()` via une boucle `after()`
  (`_wait_then_close`), jamais un `join()` qui gèlerait `mainloop()`. `dialogs.choose` remplace
  `dialogs.confirm` pour ce dialogue à trois options.

**Tests** :
- `tests/test_gui_intervention.py` (nouveau) : chaque `ActionId` de `decisions.allowed_actions`,
  construit avec les situations de `tests/test_actions.py` (question, timed_out, contract_error,
  awaiting, accepted, running) — annuler à l'invite ou à la confirmation ne fait rien ; `ACCEPT` ne
  montre ni invite ni confirmation ; `ACCEPT_WITH_RESERVES` refuse un texte vide ; `RETRY_CALL`/
  `REPROCESS_AND_RESUME` nomment le bon `call_id` ; `RESUME` sur un `RUNNING` ne transmet aucune
  intervention (la récupération elle-même reste celle de `workflow.run`, déjà éprouvée par
  `tests/test_recovery.py` — ce test-ci ne prouve que la route GUI).
- `tests/test_gui_execution.py` : `TestCloseGuard` réécrit pour les trois branches (`dialogs.choose`
  moqué), y compris l'attente simulée du fil via un `side_effect` sur `has_active_run`.
- **Vérifié en réel, hors suite** (script jetable, faux agents) : bouton « Répondre et reprendre »
  sur un `WAITING_HUMAN` amené là par un vrai cycle → reprise en fil secondaire →
  `AWAITING_APPROVAL` → bouton « Accepter cette version » sur l'écran de suivi → « Version
  acceptée » affichée. Les deux interventions les plus fréquentes, de bout en bout, pas seulement
  en test unitaire.

### Lot 6 — recette (§15.4-§15.6)

Les huit scénarios de faux agents du §15.3 étaient déjà couverts, un par un, aux lots où chaque
mécanisme est apparu — les rejouer ici aurait dupliqué sans rien prouver de plus. `tests/
test_gui_recette.py` (nouveau) couvre ce qui restait :
- **Compatibilité croisée (§15.4)** : une collaboration créée par `facade.create_collaboration`
  (chemin GUI) menée à terme et acceptée par `cli.main` (chemin CLI) ; l'inverse, créée par
  `cli.main("new", …)`, menée à terme par `Controller.start_run` et acceptée par
  `views.intervention.run` (chemin GUI). Les deux sens, dans un seul dossier réel à chaque fois.
- **Verrou déjà tenu** : un `verrou.json` construit à la main avec le PID du processus de test
  (donc « vivant ») fait échouer `Controller.start_run` sans toucher `etat.json` ; l'échec se lit
  dans `run_error`.
- **Parité des actions** : chaque valeur de `ActionId` a une étiquette dans
  `intervention._LABELS` — une addition future à l'énumération sans étiquette GUI se verrait à ce
  test, pas en usage.
- **Périmètre (§13)** : `src/iabinome/gui/` balayé pour les mécanismes exclus (base de données,
  serveur HTTP, worker/planificateur, lancement détaché, budget/réservation/bail/worktree) — rien
  trouvé.

**Validation (lots 5 et 6 ensemble)** : ruff vert ; mypy strict vert (70 fichiers) ; pytest complet
**692 passés, 2 ignorés** (+20 depuis le lot 4) ; scénario sans fournisseur rc=0. Aucun appel
fournisseur. **Non commité au moment d'écrire ceci.**

**Mesure de taille** : +191 lignes effectives pour le lot 5 (dialogs.py étendu, intervention.py
nouveau, controller.py et suivi.py étendus ; le lot 6 n'ajoute que des tests, hors du compte). Le
plafond GUI-spécifique de 1 200 lignes logiques (façade + `gui/`, inchangé par la décision du PO sur
le lot 4) est désormais à **1 195** — non dépassé, mais signalé pour la prochaine session : peu de
marge reste pour un ajout futur à cette surface. Croissance nette totale de `src/` depuis le début de
la phase 5 (`ba5c0a4`, 3 274 lignes) : **4 511** lignes, soit +1 237 — sous le plafond de +2 500 porté
par le PO après le lot 4.

**Non fait, volontairement** : tout ce qui reste hors du plan — le lot « Développement assisté »
(§ Extension identifiée de `task_plan.md`) et la recherche externe, tous deux conditionnés à une
décision explicite du PO, non engagée ici. L'acceptation formelle de la conception GUI V1 elle-même
(`decide … --accept`) reste due au PO.

## 2026-09-24 — Phase 6 ouverte (cadrage avec agent F), lot 1 fait

**Demande du PO** : mettre en place `C:\Projets\essais-3-1\Creation-prompt-2\livrables\version_finale.md`
(conception du cadrage avec agent F, acceptée par le PO le 2026-09-24, `decisions.json` séquence 2,
deux constats de B restés ouverts).

**Avant tout code** (lu, aucun appel fournisseur ; `--help` seulement) :
- Session persistante : Claude 2.1.281 offre `--session-id`, `--resume`, et `--input-format
  stream-json` (processus maintenu ouvert) ; Codex 0.155.0 offre `exec` puis `exec resume <id>`,
  et un `app-server` marqué expérimental. **`codex exec resume` n'accepte pas `--sandbox`**, et
  l'identifiant ne se fixe pas d'avance (à lire dans la sortie).
- Taille remesurée (compteur tokenize sans commentaires ni docstrings, rejoué sur `ba5c0a4` : 3 282
  avec ce compteur, 3 274 relevé à l'époque) : HEAD `581cbb3` = 4 519, soit +1 237 depuis le début de
  la phase 5 ; marge ≈ 1 263, pas les 1 454 du §13 de la conception (antérieurs au lot 5). Façade +
  `gui/` = 1 190 sur 2 000.

**Décisions du PO** (questions posées, réponses recommandées retenues) : A1 `B-convergence-003`
(l'apport de « Continuer » compte), A2 `B-cout-004` (`/clore` avant le 1er échange = premier envoi +
rédaction en un échange), A3 reprise par identifiant ; procéder « plan puis lot 1 ».

**Écrit** : `conception/CADRAGE_AGENT.md` (copie octet pour octet, sha256 vérifié `03711c71…`, puis
amendements A1-A3 datés et un choix d'implémentation signalé comme tel : `invoke_agent` non extrait) ;
phase 6 et ses six lots dans `task_plan.md` ; exception de session persistante pour F dans
`CLAUDE.md` §6 et `project/RULES.md`.

### Lot 1 — contrat de session
- `models.AgentPurpose` (A, B, FRAMING) : `default_model(purpose)` chez tous les adaptateurs ;
  `workflow`/`facade` passent `AgentPurpose(role.value)` / `AgentPurpose.A|B`. `FRAMING` n'entre
  jamais dans `etat.json`.
- `adapters/base.py` : `Capabilities.supports_persistent_framing_session` (faux par défaut),
  `FramingSessionSpec` (modèle, délai, racine, effort — pas d'accès web), `framing_command(spec,
  session, prompt)` et `framing_extract(stdout, stderr) -> (texte, identifiant)`.
- Adaptateurs réels : défaut FRAMING (Claude : celui de A ; Codex : son défaut unique), capacité
  **fausse**, méthodes `framing_*` qui lèvent `AdapterError` — câblage au lot 4.
- `framing.py` (nouveau) : `check_adapter` (prévol : inconnu, lecture seule, session persistante,
  modèle non remplaçable, effort, CLI absente — avant tout appel), `open_session` (aucun appel à
  l'ouverture), `FramingSession.send` (argv résolu avant toute écriture ; `prompt.txt`,
  `intention.json` avec `argv[0]` retiré et identifiant masqué `<session>`, transport commun,
  `reponse_brute.txt`) et `close` (oublie l'identifiant, refuse tout envoi). Incidents rendus, jamais
  relancés : `LAUNCH_FAILED`, issues du transport, `CLI_FAILED`, `DECODE_FAILED`, et `SESSION_LOST`
  si l'outil répond hors de la session ouverte (la session se ferme).
- `tests/fakes.py` : `FakeAdapter` à session en mémoire (historique par identifiant, réponses texte
  ou fonction de l'historique, `framing_drift`).
- `tests/test_framing_session.py` : 16 tests (tests §14 n° 1-5, 8, 9, 18 côté session, 47, 48 côté
  session, 50, 82, incidents, masquage).

### Test Results
ruff vert ; mypy strict vert (72 fichiers) ; **708 passés / 2 ignorés** (692 + 16) ; scénario
sans fournisseur rc=0. Taille : **+145** lignes de code effectif (4 519 → 4 664) ; croissance depuis
`ba5c0a4` : +1 382 / 2 500. Façade + `gui/` : 1 192. **Non commité.**

### Non fait, volontairement
Le protocole conversationnel, le compteur de groupe, les prompts, le dossier jetable et
`SOURCES_MODIFIED` (lot 2) ; l'argv réel de reprise (lot 4).

### Lot 1 commité
`feec971` (code, tests) et `42c3c70` (plan, conception, règles), sur demande du PO (« commit puis
continues »).

### Lot 2 — conversation de cadrage
- `prompts.py` : `build_framing_start(idee, draft=False)` (le seul envoi qui porte l'idée et la
  consultation du corpus ; `draft=True` = A2), `build_framing_continue`, `build_framing_reopen`
  (« Continuer » et « Corriger » : même groupe, compteur à 1 — A1), `build_framing_draft` (ni idée ni
  transcription), `build_framing_retry` (rappel du contrat après une sortie non conforme). Gabarits
  du §7 repris, contrats de sortie condensés.
- `demande.validate_framed` : `# Demande` en tête, chaque section exactement une fois, Objectif et
  Livrable renseignés.
- `framing.py` : `parse_reply` (balise sur sa ligne ; une phrase avant une balise conversationnelle
  est tolérée, jamais avant `IABINOME:DEMANDE` ; sections requises ; aucun compte de `?`) ;
  `prepare` (dossier jetable `framing-*/` : **F travaille dans `travail/`, qui ne contient que
  `corpus/fichiers/`** — manifeste, appels, transcription et `session.json` à côté, hors de sa
  racine ; écart assumé avec le schéma du §8.1, qui mettait tout dans la racine de F, pour tenir le
  test 6 ; sans source : conception oui, recherche non) ; `Framing` (`start`, `answer`, `reopen`,
  `write_draft`, `retry`, `note`, `discard`, `check_sources`). Une question rendue quand
  `answers >= limit` est non conforme ; toute sortie non conforme est gardée et notée, jamais
  relancée ; `SOURCES_MODIFIED` (instantané de `travail/corpus/fichiers` pris avant le premier envoi,
  comparé après chaque échange) ferme la session.
- **Constat en test** : un premier tour en échec n'établit aucune session ; la relance en ouvre une
  nouvelle (rien de repris d'inconnu). La session abandonnée n'a jamais répondu.
- `tests/test_framing.py` : 19 tests (§14 n° 5-7, 10-13, 15-17, 19-45 pour ce qui ne dépend pas de la
  création, A1, A2, parseur, transcription).

### Test Results
ruff vert ; mypy strict vert (73 fichiers) ; **727 passés / 2 ignorés** ; scénario rc=0. Taille :
**+289** (4 664 → 4 953) ; croissance depuis `ba5c0a4` : **+1 671 / 2 500, marge ≈ 829**.
`framing.py` = 286 lignes effectives, `prompts.py` 223 (le texte des gabarits compte). **Non
commité.**

### Lot 3 — création et CLI `new --cadrer-avec-agent`
- `framing.py` : `FramingArtifacts` (dossier jetable, brouillon de F, provenance §9.2) et
  `Framing.artifacts()` — refuse sans brouillon, revérifie la copie des sources (« avant la
  promotion », §5.3) ; `closure` (`AGENT_PROPOSED` si la rédaction suit une proposition,
  `USER_CLOSED` sinon), `turn_count` (apports humains), `exchange_count`, `open_questions` (bloc
  `SANS_REPONSE` de la dernière proposition), `transcription_sha256`.
- `facade.py` : `check_creation` extrait de `create_collaboration` (mêmes refus, sans écriture) pour
  les passer **avant** la session de F ; `CreationRequest.framing` ; `_write_framing` copie `appels/`
  et `transcription.md` sous `cadrage/`, écrit `cadrage/provenance.json` (+ `agent_draft_sha256`,
  `accepted_demande_sha256`, `human_edited`), reprend le corpus **préparé par le cadrage** (jamais
  relu depuis le projet) et rend l'entrée `provenance_demande.json` (`source: cadrage`, `path: null`,
  `method: agent`, `framing_provenance`, `agent_draft_sha256`, `human_edited` ; schéma v1 inchangé).
  Recherche avec cadrage : le corpus du cadrage suffit.
- **Non fait, délibérément** : `configuration.framing_agent` (§9.4 dit « peut ajouter ») — il aurait
  fallu ouvrir le schéma à clés exactes de `configuration.json` pour une information déjà présente
  dans `cadrage/provenance.json`, que le moteur ignore de toute façon.
- `framing_cli.py` (nouveau) : ordre du §3.2 (création vérifiée, prévol de F, délai résolu,
  dossier jetable — puis seulement l'idée et la session) ; saisie multiligne close par `.` pour
  l'idée, les réponses, les corrections et `m` ; `/clore` (confirmation locale) et `/annuler` ;
  menus d'incident (relancer / clore / annuler), de proposition (continuer / corriger / rédiger /
  annuler) et de relecture (`v`/`m`/`c`/`a`, `m` revalidé par `validate_framed`) ; `Ctrl+C`, fin
  d'entrée, session fermée : `discard`, rien de créé. Échec de création : message, retour au menu
  de relecture.
- `cli.py` : `--cadrer-avec-agent` (troisième voie exclusive), `--agent-cadrage`,
  `--model-cadrage`, `--effort-cadrage` (refusés sans le mode agent ; lus du fichier seulement avec
  lui), aide de `new` et de `--demande` selon le §2.1 ; `_request` factorisé. `settings.py` : trois
  clés. Docs : `COMMANDES.md` (§ Cadrage avec agent), `CONFIGURATION.md`, `dialogforge.toml.exemple`.
- `tests/test_framing_creation.py` : 11 tests de bout en bout par `cli.main` (tests §14 n° 7, 8, 9,
  12, 13, 35, 41, 43-45, 51-61, 63, 64, 75, 76 ; A et B ne voient jamais le cadrage lors d'un vrai
  `run` à faux agents ; critère 2 de l'aide).

### Test Results
ruff vert ; mypy strict vert (75 fichiers) ; **738 passés / 2 ignorés** ; scénario rc=0. Taille :
**+255** (4 953 → 5 208) ; croissance depuis `ba5c0a4` : **+1 926 / 2 500, marge ≈ 574**. Façade +
`gui/` : 1 226 / 2 000. **Lots 2 et 3 non commités.**

### Lots 2 et 3 commités — pause
Sur demande du PO : un commit `feat` pour les lots 2 et 3 (code, tests, documentation utilisateur
que `tests/test_docs.py` exige), un commit `docs` pour le plan. Puis pause. À la reprise : le PO
choisit entre le protocole de caractérisation du lot 4 (à rédiger, puis à lancer par lui) et le
lot 5 (GUI).

## Session 2026-09-24 (soir) — phase 6, lots 4 et 5

Portée déclarée par le PO : « les deux phases suivantes » (lots 4 et 5). Plan résolu avec
`PLAN_ID=2026-09-18-dialogforge-v2`, `task_plan.md`, `findings.md`, `progress.md`, `POURQUOI.md` et
`RULES.md` lus.

### Lot 4 — protocole de caractérisation (aucun appel)
- Relu sans quota : `claude --help` (**2.1.282**, contre 2.1.281 le matin), `codex exec --help` et
  `codex exec resume --help` (0.155.0). `resume` n'a ni `--sandbox` ni `-C` ; il a `-c`, `--json`,
  `--skip-git-repo-check`, `--ignore-user-config`, `--ignore-rules`, `--ephemeral`. Claude a
  `--fork-session` (« create a new session ID instead of reusing the original »), ce qui laisse
  attendre le même identifiant en reprise, **sans le prouver**.
- Écrit `reference/PROTOCOLE_CADRAGE_LOT4.md` : 4 appels (Claude puis Codex, ouverture puis
  reprise), dossier `C:\Projets\essais-3-1\cadrage-lot4\{claude,codex}\corpus\fichiers\temoin.txt`
  (`SAULE-2291`), code `ORME-4711` présent dans le seul premier prompt. Il mesure l'identifiant de
  session dans `--output-format json` / `--json`, la stabilité de cet identifiant en reprise, le
  rappel du code et l'absence de `ecrit-en-reprise.txt`. Pour Codex, la reprise passe
  `-c sandbox_mode=read-only`, ce que l'adaptateur enverra. Seul rejeu prévu : si Codex n'a rien
  tenté d'écrire.
- Éprouvé sans quota dans le scratchpad : préparation (dossiers, témoins, empreintes) et lecture des
  sorties sur des fichiers synthétiques (`c1.json`, `x1.jsonl` avec une ligne non JSON).
- **Non lancé.** Aucun code d'adaptateur écrit : il dépend des formes mesurées.

### Lot 5 — GUI « Cadrer avec un agent »
- `framing.shown(turn)` : ce qu'un écran montre d'un tour (incident + sortie gardée, ou réponse sans
  `ETAT_CADRAGE`) ; `framing_cli._show` s'en sert.
- `gui/controller.py` : `open_framing` (session neuve, `ExecutionControl` propre, env des autres
  adaptateurs retiré), `framing_step` (un tour dans **l'unique** fil moteur ; `False` s'il est
  occupé), `take_framing_outcome`, `discard_framing` (interrompt un tour en cours, ferme, détruit le
  dossier jetable). `start_run` refuse désormais dès que le fil est occupé (avant : même dossier
  seulement — un tour de F n'a pas de dossier). `_swap` ferme le cadrage.
- `gui/views/cadrage.py` (nouveau) : `FramingPanel` (§4.1 : agent, modèle, effort, idée, Commencer /
  Reprendre), `begin` (refus du §3.2 avant toute session : fil libre, idée, `check_creation`,
  `check_adapter`, `prepare`), `reviewed` (le texte relu doit passer `validate_framed`, puis
  `artifacts()`), `resume` (test 45), `FramingDialog` (§4.2 : transcription, réponse, Envoyer /
  Continuer, Corriger un point, Clore maintenant / Rédiger le brouillon, Relancer, Annuler ;
  `grab_set` ; sondage `after()` de `has_active_run()` ; annuler pendant un tour interrompt puis
  détruit quand le fil s'est arrêté, jamais sous lui).
- `gui/views/creation.py` : troisième mode de demande, sources montrées aussi en mode agent,
  création avec `framing=` (sources non relues), confirmation « Créer et démarrer » précédée de la
  phrase du §4.4. `gui/app.py` : `_destroy` ferme le cadrage à toute fermeture de fenêtre.
- `docs/COMMANDES.md` § gui : le texte « lecture seule au lot 3 » (périmé depuis la phase 5)
  remplacé par les actions et le mode agent.
- `tests/test_gui_cadrage.py` : 13 tests (§14.7 n° 65-72, plus 42, 43, 45, 46, 51, 54 côté GUI).
- **Contre-épreuves** : 8 mutations (discard à la navigation, garde de `start_run`, attente du fil
  avant destruction, refus pendant une exécution, désactivation pendant un tour, relecture du
  brouillon, phrase de confirmation, discard au changement de mode) : **8 détectées**. La 6e
  (relecture neutralisée) bloquait au lieu d'échouer : une vraie `messagebox` s'ouvrait. Test
  corrigé (boîte remplacée), la mutation échoue désormais en 2 s.
- **Vérifié en réel** (script hors suite, vraie fenêtre, `mainloop()`, faux agents lents à 0,4 s) :
  pendant le tour 1, le fil est actif et aucun bouton n'est actif ; puis question, proposition
  (« Continuer »), rédaction, modale fermée, brouillon dans l'éditeur, ligne ajoutée, « Créer
  seulement ». Collaboration créée, `human_edited: true`, 3 échanges, 1 session F, cadrage fermé
  après création.

### Test Results
ruff vert ; mypy strict vert (77 fichiers) ; **751 passés / 2 ignorés** ; scénario rc=0 ;
`git diff --check` propre. Taille, avec un compteur tokenize recalé sur les chiffres consignés
(`ba5c0a4` = 3 282, `581cbb3` = 4 519 / 1 190, `abdf09f` = 5 208 / 1 226) : **+310** (5 208 →
5 518) ; croissance depuis `ba5c0a4` **+2 236 / 2 500, marge ≈ 264** ; façade + `gui/` 1 535 / 2 000 ;
`views/creation.py` 370, `views/cadrage.py` 216 (déplacer `reviewed`/`resume` hors de
`creation.py` l'a fait passer de 390 à 370).

### Trouvé, non corrigé
- `pytest tests -k "gui or framing"` échoue sur `test_gui_execution.py::TestStartRun::
  test_a_run_reaches_awaiting_approval` (« RuntimeError: main thread is not in main loop », puis
  « jamais observé : fin du cycle »). **Déjà sur `abdf09f`** (vérifié par `git stash`). Seulement
  dans ce sous-ensemble : suite complète et fichier seul verts.
- `README.md` et `docs/LIMITES.md` : « Pas d'interface graphique », faux depuis la phase 5.

### Non fait, volontairement
- Aucun code d'adaptateur réel (lot 4) avant les mesures du PO.
- Rien n'est commité.

### Commits du lot 5
Sur demande du PO (« commites puis corriges ces deux points ») : `c718055` (feat : code, tests,
`COMMANDES.md`) et `ee25935` (docs : plan, journal, règle, protocole du lot 4).

## Session 2026-09-25 — les deux trouvailles du lot 5

### 1. L'échec de `pytest tests -k "gui or framing"` : deux défauts distincts
- **Reproduit 6 fois sur 6** avec `-k "(gui or framing) and not cadrage"` (le sous-ensemble de
  `abdf09f`) : `test_a_run_reaches_awaiting_approval` finit `INTERRUPTED`. Trace : `Exception
  ignored in: Variable.__del__ … RuntimeError: main thread is not in main loop`, levée dans le
  fil moteur. Le ramasse-miettes s'y déclenche et finalise des `tkinter.Variable` laissées en
  cycles par les vues des tests précédents ; chaque finaliseur appelle Tk hors du fil principal,
  qui ne fait pas tourner `mainloop()` dans les tests. **Défaut des tests seuls** : en production,
  `mainloop()` tourne et Tk route ces appels. Corrigé par `collect_tk_garbage()`
  (`tests/test_gui_views.py`, un `gc.collect()` documenté), appelé en tête du `setUp` des cinq
  fichiers GUI qui lancent un fil moteur.
- **Second défaut, intermittent (environ 1 fois sur 3), réel dans le produit** :
  `test_the_view_stops_polling_once_the_run_finishes`. Diagnostic instrumenté : fil vivant, statut
  `RUNNING`, mais le sous-titre de la vue disait « Dossier illisible : … [Errno 13] Permission
  denied: '…etat.json' ». Sous Windows, le fichier est un instant illisible pendant que le moteur le
  remplace. `SuiviView._refresh` rendait alors la main **sans reprogrammer le sondage** : l'écran
  restait figé sur l'erreur pendant que le cycle continuait. Corrigé : tant que la fenêtre possède
  l'exécution, le refus s'affiche et le sondage continue. Nouveau test déterministe
  (`test_an_unreadable_folder_during_a_run_keeps_polling`) ; contre-épreuve : sans le correctif,
  il échoue.
- Après les deux corrections : **10 passages verts sur 10** (5 sur chaque sous-ensemble).
- **Non traité, signalé** : `status` en CLI, lancé pendant un `run` d'un autre terminal, peut
  tomber sur la même fenêtre de remplacement. Il échoue alors une fois, et le relancer suffit ; rien
  ne reste figé, donc rien n'a été changé.

### 2. Documentation
`README.md` et `docs/LIMITES.md` : « Pas d'interface graphique » remplacé par « Une fenêtre locale,
rien de plus » (`dialogforge gui`, une collaboration et une exécution à la fois, sans service, worker
ni processus détaché). `docs/DEVELOPPEMENT.md` : la GUI, hors périmètre à J3, est dite livrée depuis.

### Test Results
ruff vert ; mypy strict vert (77 fichiers) ; **752 passés / 2 ignorés** ; scénario rc=0 ;
`git diff --check` propre. Taille : +2 (`src/` = 5 520 ; façade + `gui/` 1 537).

## Session 2026-09-25 (suite) — phase 6, lot 4 : adaptateurs de F

Portée déclarée par le PO : « nous reprenons avec le lot 4 ».

### Partie 1 du protocole : lancée par le PO, lue sans quota
- `C:\Projets\essais-3-1\cadrage-lot4\` absent en début de session, donc protocole non lancé.
  Le PO l'a lancé (« pas de problème de réalisation »), 4 appels.
- **Conforme chez les deux outils, sur les quatre lignes du tableau.** Claude : un objet JSON,
  `session_id` identique en reprise, `ORME-4711` rappelé, aucun fichier écrit ; le modèle dit n'avoir
  que `Read`, `Glob`, `Grep`, donc `--tools` vaut en reprise. Codex : `thread.started`/`thread_id`
  identique en reprise, `ORME-4711` rappelé ; `-c sandbox_mode=read-only` accepté par `resume` ;
  **tentative d'écriture réelle**, refusée et journalisée par l'outil (`x2.err` : `patch rejected:
  writing is blocked by read-only sandbox`). Le seul rejeu prévu n'a donc pas servi. Empreintes du
  témoin identiques, aucun fichier inattendu.
- Surprise, qui change le code : le tour d'ouverture de Codex porte **deux** `agent_message`,
  une annonce puis la réponse. Règle ajoutée à `RULES.md`.

### Code
- `adapters/claude.py` : `framing_command` = argv de A/B sans `--no-session-persistence`, avec
  `--output-format json`, puis `--resume <id>` et `--effort` ; `framing_extract` lit `result` et
  `session_id`, refuse (`ValueError`, donc `DECODE_FAILED`) une sortie sans `result` ou avec
  `is_error`.
- `adapters/codex.py` : ouverture `exec -m … --sandbox read-only`, reprise `exec resume -m … -c
  sandbox_mode=read-only`, puis options communes, `--json`, backend `elevated` sous Windows, web
  fermé, effort, identifiant, `-` : l'ordre du protocole. `framing_extract` : l'identifiant de
  `thread.started`, le dernier `agent_message` d'un `item.completed`, et `turn.completed` exigé.
- Capacité `supports_persistent_framing_session=True` pour les deux.
- Les quatre sorties réelles, relues par les nouveaux `framing_extract`, rendent la bonne réponse et
  le même identifiant d'un tour à l'autre (vérifié à la main, hors suite : fichiers hors dépôt).
- Tests : 5 nouveaux dans `tests/test_adapters.py` (argv exact, extraction, refus), bâtis sur les
  formes mesurées, identifiants remplacés. `test_real_adapters_are_refused_until_wired` devient
  `test_real_adapters_pass_the_preflight_once_characterized`.

### Documentation
- `reference/PROTOCOLE_CADRAGE_LOT4.md` : résultats de la partie 1, et **partie 2 rédigée**
  (un cadrage court par le produit et par outil, 6 appels, collaboration créée jamais lancée).
- `docs/LIMITES.md` §2 : une ligne pour la session de F.
- Identifiant de session présent dans `stdout.txt` brut (rangé sous `cadrage/appels/`) : conforme
  au §9.2 de la conception (même règle que les autres données techniques), masqué dans
  `intention.json`, absent des provenances. Signalé, non changé.

### Test Results
ruff vert ; mypy strict vert (77 fichiers) ; **758 passés / 2 ignorés** ; scénario rc=0 ;
`git diff --check` propre. Taille : `src/` = 5 572 (+52 ; +2 290 / 2 500, marge ≈ 210), compteur
tokenize recalé sur 3 282 (`ba5c0a4`) et 5 520 (`db37cc8`).

### Commits du lot 4
Sur demande du PO : `028a1dd` (feat : adaptateurs et tests) et `ec0c7a6` (docs : protocole,
limites, règle, plan).

### Partie 2 du protocole : un cadrage réel par le produit et par outil
- **Claude** : le PO a mené un vrai cadrage (vis pour plancher OSB) au lieu de l'idée écrite. 6 échanges
  (3 questions, proposition, « continuer », question, `/clore`, `v`), `neuve` puis 5 `reprise`, même
  `session_id` partout, rc 0, stderr vide. Note lue une fois, jugée hors sujet. `env_removed` vide
  (rien à retirer dans un `pwsh -NoProfile`).
- **Codex** : premier essai sans trace (pas de dossier) ; relancé par le PO sur le même cadrage. 6
  échanges, `exec` puis 5 `exec resume … -c sandbox_mode=read-only`, même `thread_id`, rc 0. Premier tour :
  annonce, lecture (`Get-ChildItem`, `Get-Content`), puis réponse balisée — la règle du dernier message
  a servi dans le produit. `env_removed` = `CLAUDE_CONFIG_DIR` : le filtre a agi.
- Chez les deux : identifiant présent seulement dans `stdout.txt` brut, `demande.md` = brouillon relu,
  source inchangée, collaboration `READY` jamais lancée.
- **Défaut trouvé (lot 2), non corrigé** : `open_questions` garde les `SANS_REPONSE` de la dernière
  proposition après une reprise du cadrage ; reproduit chez les deux outils. Décision demandée au PO.
- Lot 4 coché dans le plan. Résultats consignés dans `reference/PROTOCOLE_CADRAGE_LOT4.md`, non commités.

## Session 2026-09-25 (soir) — plan de finalisation inscrit, partie 1 engagée

### Actions
- Lu `reference/astra_finalisation/PLAN_TRAVAIL.md` et les constats F01-F04 de
  `reference/Astra_AUDIT_BOUT_EN_BOUT/RAPPORT_AUDIT.md`. Causes revérifiées dans le code courant :
  `decisions._sha` rend `None` pour un fichier absent (l. 39), `version_of` reprend
  `state.demande_sha256` au lieu de relire `demande.md` (l. 50), « Gratuit et local » (l. 268).
- Proposition amendée d'après une relecture externe transmise par le PO : n'inscrire que le travail
  engagé ; F01/F02 d'abord ; `open_questions` tranché sur le sens ; le lot 4 initial (développement
  assisté) confie le travail à l'agent habituel, sans exécution autonome par le moteur ; mesure
  d'utilité à partir des traces existantes ; pas de commit global de l'arbre.
- Vérifié : `CLAUDE.md:78` dit la relecture palier par palier suspendue depuis le 2026-09-03, alors
  que `project/RULES.md:64` consigne sa réouverture le 2026-09-05 — incohérence documentaire (F04),
  à corriger d'après cette chronologie quand F04 sera engagé ; aucune décision nouvelle requise.
- Commit `b2bf4fe` (sur demande du PO) : résultats de la partie 2 du lot 4, limité aux 4 fichiers de
  cette session. Les dossiers `reference/Astra_AUDIT_BOUT_EN_BOUT/`, `reference/astra_finalisation/`
  et `reference/PROMPT_AUDIT_BOUT_EN_BOUT*.md` restent non suivis : autre provenance, intouchés.
- Plan : `Next Step` réécrit (ordre 7.1 → `open_questions` → 6.6), phase 7 ouverte avec 7.1,
  préalable ajouté à 6.6, Extension précisée, décision consignée.

### 7.1 — F01/F02 corrigés (non commité)
- `decisions.py` : `demande_sha` relit `demande.md` avec `contracts.normalize` (comme
  `workflow._check_demande`) ; `discrepancies` nomme ce qui ne correspond plus (livrable/revue
  absents ou changés, demande absente ou changée, révision) et traite une absence comme un défaut
  pour une acceptation ; `acceptance_gaps` applique la même vérification à ce qui est sur le disque ;
  `applies_to_current` et `describe` en dérivent. `version_of` et le format de `decisions.json`
  inchangés (rejouabilité de `record`, décisions historiques).
- `workflow.decide` : refus d'une acceptation, sous le verrou, sans nouvelle entrée, si le dossier
  ne correspond plus à l'état. Arrêt toujours possible sans livrable.
- Façade : `DecisionSummary.discrepancies` ; la vue de suivi nomme l'artefact au lieu de « le
  livrable a changé » en dur.
- Choix : un livrable ou une revue modifiés mais présents sont une autre version, acceptable
  explicitement (comportement antérieur conservé) ; seules une absence ou une demande divergente
  sont refusées.
- Tests : `TestAnAcceptanceNeedsItsArtifactsOnDisk` (6 altérations sur copie, chacune vérifiée
  dans `decide`, `status`, `show`, façade, `planlink.summary` ; remise en place ; ancienne
  acceptation sans livrable ; BOM/CRLF ; arrêt sans livrable), plus un test de la vue de suivi.
  11 échecs sur l'ancien code, verts sur le nouveau.
- Relecture à froid par un agent Sonnet (lecture seule) : rien de bloquant. Trois constats
  mineurs : (1) une `CORRECTION_CIBLEE` menée à terme se décrit « porte sur une version
  antérieure : … la demande a changé » — exact, comportement booléen inchangé ; (2) un arrêt
  brutal entre `decisions.record` et `publish` d'une correction fait refuser une acceptation avec
  « la demande a changé » — refus sûr, message identique à une altération externe ; non changé ;
  (3) la vue de suivi n'était pas testée → test ajouté. Elle affiche aussi les écarts d'un `ARRET`,
  comme avant ; non changé.
- Outil de taille : compteur tokenize réécrit dans le scratchpad, recalé exactement sur 3 282
  (`ba5c0a4`), 5 520 (`db37cc8`), 5 572 (`b2bf4fe`).

### Test Results (7.1)
ruff (`src tests`) vert ; mypy strict vert (77 fichiers) ; **765 passés / 2 ignorés** ; scénario
rc=0 ; `git diff --check` propre. `ruff check .` échoue sur les scripts d'audit non suivis de
`reference/Astra_AUDIT_BOUT_EN_BOUT/` (64 erreurs, hors de ce changement). Taille `src/` = 5 611
(+39 ; +2 329 / 2 500, marge ≈ 171).

### 6.6 préalable — `open_questions` (amendement A4, non commité)
- Commits de 7.1 sur demande du PO : `2a8c6e9` (fix, src et tests), `24a9c2d` (docs, plan).
- Deux traces réelles relues (`C:/Projets/essais-3-1/cadrage-lot4/produit-claude` et
  `produit-codex`) : le champ citait une question déjà répondue ; le dernier `QUESTIONS_OUVERTES`
  de F rend exactement les inconnues du brouillon, chez les deux outils. « Vider à la reprise »
  (recommandé jusque-là pour sa taille) aurait écrit `[]` dans les deux cas : recommandation
  retirée. Le PO a retenu la lecture B.
- Vérification demandée par le PO avant l'implémentation : le contrat de F ne définissait pas la
  liste vide (`_F_CONTRACTS` : « une liste chacune ») et `parse_reply` ne regarde pas l'intérieur de
  `ETAT_CADRAGE`. Claude écrit une puce nue, Codex `- Aucune.`. Et `/clore` avant le premier
  échange (A2) laissait `[]` sans que F ait rien exprimé.
- Fait : `- AUCUNE` ajouté au contrat ; `framing._open_questions` lit le bloc (en-tête avec ou sans
  deux-points, arrêt à la rubrique suivante) ; `[]` seulement sur `AUCUNE` seul, valeur précédente
  gardée sinon ; `null` au départ. `_unanswered` retiré. Amendement A4 dans
  `conception/CADRAGE_AGENT.md` ; deux règles et deux motifs dans `project/RULES.md`.
- Tests : `TestOpenQuestions` (les deux enchaînements réels réduits à leur forme, huit cas de la
  règle, `/clore` avant tout échange, ligne du contrat) ; fixture `READY_OUT` complétée. 12 échecs
  sur l'ancien code.

### Test Results (A4)
ruff (`src tests`) vert ; mypy strict vert ; **769 passés / 2 ignorés** ; scénario rc=0 ;
`git diff --check` propre. Taille `src/` = 5 618 (+7 ; +2 336 / 2 500, marge ≈ 164).

### 6.6 — Recette du lot 6 : critères §15 (2026-09-26, non commité)
Commits de A4 sur demande du PO : `e7ef498` (fix), `fd30ae4` (docs).
Méthode : chaque critère rattaché à ses tests (numéros du §14, cités dans les docstrings) ou à une
preuve réelle ; les points du §14 sans test propre comblés dans `tests/test_framing_recette.py`
(73, 74, 53, 80, 81, P18, périmètre 14/49/77), sans rejouer ce que les lots 1 à 5 prouvent.

| # | Critère | Preuve |
|---|---|---|
| 1 | Voies existantes disponibles | Suite `--demande`/`--cadrer` inchangée et verte ; `test_framing_options_need_the_agent_mode` |
| 2 | Aide de `new` : le mode agent appelle | `test_the_help_says_the_agent_mode_may_call` |
| 3 | F paramétré indépendamment de A et B | `--agent-cadrage` et options propres ; test 50 (défaut de F par adaptateur) |
| 4 | Session neuve pendant tout le cadrage | Tests 1 à 4 ; deux cadrages réels du lot 4 (même session, 6 tours) |
| 5 | Aucun rechargement entre les tours | Tests 15 à 17 ; traces réelles (F ne relit ni l'idée ni le corpus) |
| 6 | Sources copiées dans un dossier isolé | Tests 5, 6 |
| 7 | Aucun chemin absolu persisté | Test 7, `test_no_absolute_source_path_and_no_leftover` |
| 8 | Sans source en conception | Test 11 (et 12 : refusé en recherche) |
| 9 | Réponses libres et corrections | Tests 18, 19, 28, 29 |
| 10-12 | Limites 3 puis 2 ; correction = 1re réponse | Tests 23 à 31 (A1) |
| 13 | L'utilisateur seul clôt | Tests 33, 34 |
| 14 | Rédaction dans la même session | Tests 36, 45, 75 |
| 15 | Relecture avant création | Tests 41, 42 |
| 16 | Empreintes = texte relu | Test 43 |
| 17 | GUI : unique fil moteur | Tests 65 à 67 ; 69 remplacé par le sondage `after()` (Decisions Made, lot 5) |
| 18 | Session F fermée avant A | Test 54 |
| 19 | `demande.md` seule entrée du cycle | Tests 55, 56 |
| 20 | Provenance : brouillon ≠ texte accepté | Tests 58, 59 |
| 21 | P14-P20, R7, X14 | P14 : 33, 41 ; P15 : 55 ; P16 : 37 ; P17 : 21, 22 ; P18 : recette ; P19 : 23-31 ; P20 : consigne du prompt seulement ; R7 : 73-76 et doc ; X14 : 56 |
| 22 | Coût = une session et `q + p + r` échanges | Tests 73, 74 (recette), 76 ; phrase ajoutée à `docs/COMMANDES.md` |
| 23 | Aucun ratio de jetons promis | Même phrase ; balayage « coût/jetons/quota » des sources de F |
| 24 | Aucun des cinq interdits contourné | Balayage des sources de F (motifs de la recette GUI + coût + import du moteur A/B) |
| 25 | Façade + GUI < 2 000 lignes logiques | **1 540** (compteur recalé sur 1 537 à `db37cc8`) |
| 26 | Croissance `src/` < +2 500 | **5 618 = +2 336**, marge ≈ 164 |
| 27 | Marge remesurée avant livraison | Ce relevé, compteur recalé sur 3 282 / 5 520 / 5 572 |
| 28 | Aucun fournisseur réel dans les tests | `FakeAdapter` partout ; `shutil.which` et version substitués (`test_adapters.py`) |

**Limites consignées** :
- P20 (alternatives étayées, jamais inventées) n'est qu'une consigne du prompt : aucun test mécanique ne
  peut juger qu'une alternative est « étayée ».
- La ligne `- AUCUNE` du contrat (A4) n'a pas encore été vue par un vrai outil.
- Les cadrages réels du lot 4 sont passés par la CLI ; le mode agent de la GUI n'a été éprouvé qu'avec
  le faux agent, et aucune recette visuelle n'a été faite.
- Le tableau de `docs/COMMANDES.md` qui dit que `new` n'appelle pas d'agent relève de F03 (partie 2,
  non engagée) ; la ligne `--cadrer-avec-agent` et l'aide, elles, l'annoncent.

### Test Results (6.6)
ruff (`src tests`) vert ; mypy strict vert (78 fichiers) ; **778 passés / 2 ignorés** ; scénario
rc=0 ; `git diff --check` propre. `src/` inchangé par la recette (5 618) ; tests seuls, plus une
phrase de documentation.

## Session 2026-09-26 — point 1.3 ouvert : préparation de la conception du développement assisté
- Commits de la recette sur demande du PO : `590a8db` (test), `1b2da3d` (docs).
- Le PO ouvre le point 1.3 (lot 4 initial). Lus pour le préparer : `POURQUOI.md` (non lu en début
  de session le 2026-09-25, rattrapé ici), `astra/06` §1-§3 et §8, `astra/03` §7, `astra/04` §2,
  `astra/01` §5, `astra/README.md`, `ANALYSE_PROGRAMME_INITIAL.md`.
- Méthode reprise des phases 5 et 6 (`essais-3-1/gui-v1`, `Creation-prompt-2`) : conception par une
  collaboration DialogForge. Préparé hors dépôt : `C:\Projets\essais-3-1\preparation-dev-assiste\`
  (`demande.md`, six sections conformes ; `sources.txt`, 10 fichiers de ce dépôt). La demande cite
  `astra/06` §8 et `astra/03` §7, hors corpus ; elle pose le cadre (aucune exécution autonome, Git
  en lecture, marge ≈ 164 lignes à tenir ou chiffrer).
- Rien lancé : la collaboration de conception appelle les fournisseurs, le PO la lance.

## Session 2026-09-26 — poursuite nocturne du point 1.3 avec Codex et Claude
- Le PO demande de poursuivre avec l'aide de Claude pour terminer avant demain.
- Relus : CLAUDE.md, POURQUOI.md, règles, plan et préparation hors dépôt. Les exécutables
  Claude et Codex sont présents ; la collaboration n'existait pas.
- Collaboration créée puis `run` lancé dans `C:\Projets\essais-3-1\dev-assiste`, avec les
  autorisations d'exécution hors du bac à sable. Demande et dix sources inchangées.
  Configuration effective : A = codex / gpt-5.6-sol ; B = claude / opus ; une révision,
  délai de 1 200 secondes par appel. Premier appel en cours (PROPOSAL_A).
- Questions au PO en attente : délégation éventuelle de l'acceptation sous contraintes,
  et projet de l'essai réel. Pas d'acceptation ni d'implémentation à ce stade.
- État Git initial : seuls task_plan.md et progress.md modifiés parmi les fichiers suivis ;
  documents d'audit/finalisation non suivis déjà présents, conservés.
- Réponse du PO pendant le premier appel : délégation de l'acceptation sous contraintes puis
  du code ; ajout net autorisé inférieur à 1 000 lignes, de préférence au plus 500. L'amendement
  sera transmis par une intervention tracée, sans modifier la demande pendant un appel.
- Le PO choisit DialogForge_2 pour l'essai. État initial vérifié : ruff src/tests vert,
  mypy src vert ; pytest : 772 passés, 8 ignorés, 561 sous-tests (112,90 s dans le bac à sable).
  Aucun fichier de production modifié avant acceptation de la conception.
- Premier cycle réel terminé (4 appels) : AWAITING_APPROVAL, six constats encore ouverts.
  La révision 1 conserve une orchestration B séparée : non acceptée par Codex.
- Tour de correction lancé via `decide --correct` avec `amendement-dev-assiste.md` :
  nouveau plafond, projet d'essai, délégation et réemploi des collaborations ordinaires.
  A produit un rapport documentaire sur le code extérieur, B le critique ; pas de second moteur.

## Session 2026-09-27 — implémentation du développement assisté
- Tour ciblé terminé : B accepte la conception à l'appel 6, avec deux NOTE ouvertes.
  Codex accepte sous délégation avec réserves tracées dans `dev-assiste/decisions.json` :
  `sources.txt` contrôlé séparément de sa copie de corpus (`B-verify-001`), contrôle textuel
  ambigu des validations reporté (`B-verify-002`). Le livrable exact est copié dans
  `conception/DEVELOPPEMENT_ASSISTE.md`. Aucun code écrit avant cette acceptation.
- Code : `development.py` et trois commandes CLI `dev-export`, `dev-package`, `dev-verify`.
  Export réel de la conception acceptée produit sous `essais-3-1`; copie Git isolée de
  DialogForge_2 créée pour l'essai réel. Le produit ne lance que des lectures Git sur deux commits,
  ne lance aucun test du projet cible et réutilise `new/run/show/decide` pour la revue.
- Avant revue externe : 15 tests ciblés et 20 sous-tests passés ; documentation : 8 tests,
  193 sous-tests ; suite complète : **786 passés, 8 ignorés, 613 sous-tests** ; Ruff et mypy verts.
  Mesure recalée exactement sur 5 618 à HEAD : ajout net de 399 lignes de code effectif.
- Relecture statique réelle par Claude Opus en lecture seule : dix observations, dont trois
  majeures sur le rattachement du paquet et le parcours de correction. Corrections en cours :
  racine du paquet fermée, demande initiale vérifiée contre sa configuration, acceptation seule
  soumise au contrôle de péremption ; revue arrêtée acceptée comme antécédent si elle a ses pièces,
  racine Git réelle utilisée pour refuser une sortie dans le dépôt, chemins de contrôle refusés,
  délai Git rendu comme refus normal. Tests de régression ajoutés, résultats en attente.
- `B-verify-002` : report du contrôle textuel des identifiants de validation dans la prose,
  indiqué dans `docs/COMMANDES.md`. Les contrôles des pièces et de leurs empreintes restent tenus.

## Session 2026-09-27 — clôture du point 1.3 et essai réel

- Deux relectures statiques de l'implémentation par Claude Opus ont conduit à renforcer les
  contrôles d'identité du paquet, de la révision, de la demande, des antécédents et de la
  publication sans remplacement. Les régressions ont été couvertes par des tests ciblés.
- Implémentation et conception commitées en `74f6973` ; croissance effective de `src/` :
  5 618 → 6 090, soit **+472 lignes** (cible ≤ 500, plafond strict < 1 000).
  Suite complète après implémentation : **786 passés, 8 ignorés, 613 sous-tests** ; après les
  corrections ciblées : 31 passés, 219 sous-tests ; Ruff et mypy strict verts.
- Essai hors dépôt dans `C:\Projets\essais-3-1\dev-assiste-essai-20260927` : clone Git de
  DialogForge_2. Export de la conception acceptée, puis quatre commits documentaires successifs
  (`3b5a05d`, `f998f3b`, `cbcea09`, `f5383e8`), chacun capturé à partir de sa base exacte.
  Chaque paquet a été soumis à une collaboration A=Codex, B=Claude en accès `consult`, avec un
  rapport, une critique, `dev-verify` réussi et une décision sur le rapport avec réserves.
- Dernier paquet : `b20bc318615be3fdda50e4b3147487a5b70f618313b42f93ef813ea07cdf7591` ;
  base `cbcea09c6b75e8d1c128f6bcdda3b8e76669b812`, tête
  `f5383e8fbfdba5cdaa3140c4aea9bf9cd5bc1df4`. Validation documentaire déclarée
  `PASSED` (8 tests, 193 sous-tests) ; contrôle sémantique déclaré `NOT_RUN` avec motif et
  note d'inspection du diff. B a accepté la dernière version du rapport, ses six constats
  de relecture sont résolus, puis la décision humaine déléguée a accepté le rapport avec
  réserves après vérification du paquet.
- La revue a relevé une imprécision mineure non introduite par le dernier diff : « réponses
  présentes dans le registre ». Elle est corrigée dans `docs/COMMANDES.md` du dépôt principal,
  hors du paquet figé de l'essai ; les 8 tests documentaires y passent. Les résultats importés
  restent déclaratifs, et DialogForge ne certifie ni leur exécution ni le jugement éditorial.
  Aucun merge, installation ou déploiement n'a été effectué.

## Retour d'usage 2026-09-28 — essais GUI sur une même demande

- Deux collaborations de recherche web sur la reprise d'activité chez les seniors, avec A/B
  inversés, ont atteint `AWAITING_APPROVAL`. Même empreinte de demande, un constat ouvert
  dans chaque revue finale ; aucune décision d'acceptation enregistrée.
- Points d'amélioration et état de chacun consignés dans
  `project/retour_essais_2026-09-28.md`. La lisibilité visuelle de la progression A/B
  est ajoutée explicitement à ce retour par le PO. Ce relevé n'engage pas de nouveau lot.

## Correctif GUI 2026-09-28 — accueil et répertoire des collaborations

- À la demande du PO, les collaborations créées par la GUI sont inscrites immédiatement
  dans les récents. L'accueil affiche aussi les collaborations trouvées directement dans
  le répertoire parent choisi, avec leur état relu sur disque, même si elles n'ont jamais
  été ouvertes par la GUI.
- Le répertoire parent se choisit sur l'accueil et est mémorisé comme préférence locale.
  Le formulaire de création propose un nouveau sous-dossier dans cette racine ; son bouton
  de dossier choisit le parent. À la première création sans racine choisie, le parent
  de cette collaboration devient la racine par défaut. Les dossiers existants ne sont
  pas déplacés.
- Validation : 40 tests GUI ciblés passés, Ruff et mypy GUI verts ; suite complète
  805 passés, 8 ignorés, 620 sous-tests passés avant le dernier ajustement local
  (`record_created` mémorise le premier parent), puis 40 tests ciblés relancés et verts.

## Session 2026-10-01 — nettoyage du dépôt et première publication sur GitHub

- `git clean -fd` à la demande du PO : 81 entrées non suivies supprimées, dont les sorties brutes de
  l'audit (`reference/Astra_AUDIT_BOUT_EN_BOUT/`, hors les deux rapports suivis) et les collaborations
  d'essai GUI `Reprise_Activité_*`, `Remise en Forme/`, `test/`. **Erreur de l'assistant** : il les a
  classées « temporaires » sans les ouvrir et sans faire le `stash` qu'exige `RULES.md`. Le PO les
  tenait pour des tests et les laisse perdues. Le relevé `project/retour_essais_2026-09-28.md` reste.
- Suppression de `prompts/demande.md` validée (`7702d84`). Le message de ce commit annonce à tort
  821 fichiers supprimés : ils n'étaient pas suivis. Comme il est déjà publié, il n'a pas été réécrit.
- Branche `main` créée depuis `v2-socle`, fusionnée avec le commit initial de GitHub (`ac2a216`,
  histoires non liées, conflit sur `README.md` résolu en gardant la version locale, `362a0d9`).
  Push de `main` vers `origin`. `master` (= `4a11cc7`, déjà dans l'historique) supprimée en local.
- Relecture après le push : dépôt **public**, 170 fichiers, 125 commits. Aucun secret (clé, jeton,
  mot de passe). Seuls l'e-mail du PO (déjà dans les métadonnées des commits) et les chemins
  `C:\Users\schne\…` figurent dans 4 fichiers. Pas de réécriture d'historique.
- `.gitignore` corrigé, `docs/DEVELOPPEMENT.md` et ce plan mis à jour (branche, remote), tag `v0.1.0`
  poussé. Aucun code touché. Licence MIT ajoutée après validation du PO.

## Session 2026-10-01 (suite) — retour d'usage, points 4, 5 et 6

Engagés par le PO (« attaques et finalises 4, 5 et 6 »). Le PO valide aussi la conception GUI V1 :
déjà acceptée dans sa collaboration le 2026-09-23, le rappel du plan était périmé.

- **Cause du point 4, mesurée sur une trace réelle** : la sortie de Codex commence par une bannière
  (version, dossier, modèle…) puis l'écho complet du prompt. Les 300 premiers caractères cités par
  `incidents._tool_message` ne contenaient donc jamais l'erreur. L'extrait est désormais pris en fin
  de flux (« stdout de l'outil, fin : « … » ») ; une sortie courte reste citée entière, comme avant.
  `incidents.explain` ajoute, pour `CLI_FAILED`, l'outil et le modèle lus dans `intention.json`, et
  le fait qu'une relance les reprend (modèle figé à la création).
- `facade.Presentation` : `phase_steps` remplacé par `progress` (`Progress`/`Step` : un tour par
  ligne, A et B nommés avec outil et modèle, ligne humaine, phrase « maintenant ») et `trace_dir`.
  Les sorties brutes non vides d'un appel inabouti s'ajoutent aux documents lisibles.
- `views/suivi.py` : chemin en champ lecture seule avec « Ouvrir le dossier » en en-tête, bouton
  « Ouvrir la trace de l'appel » sur incident, grille de progression, sortie d'appel affichée en fin
  de texte. `views/creation.py` : le message de création donne le chemin.
- **Tests** : `TestProgress` (7 cas, remplace `TestPhaseSteps`), 2 tests d'incident. Contre-épreuves :
  extrait repris en tête → 1 échec ; trace jamais proposée → 1 échec ; chacune rétablie.
- **Vu en réel** : écran de suivi capturé dans trois états (frais, `CLI_FAILED` sur une sortie de
  type Codex, `CONTRACT_ERROR` en révision 1) avec les faux agents ; l'erreur de fin de sortie
  s'affiche, la grille marque l'étape arrêtée. Les premières captures montraient d'autres fenêtres
  du poste (fenêtre de test passée derrière) : supprimées aussitôt, refaites au premier plan.
- **Validation** : ruff, mypy strict (82 fichiers), **817 passés / 2 ignorés**, 622 sous-tests,
  scénario rc=0. Taille : +119 lignes effectives dans `src/` (6 252 → 6 368 au compteur, qui
  affiche aussi −3 sur `modeles.toml`, inchangé) ; façade + GUI 1 773 / 2 000.
- `README.md` réécrit par le PO pendant la session et commité par lui (`a4d3c41`), hors de ce lot.
- Commité et poussé : `ab3f739`.

## Session 2026-10-01 (suite) — retour d'usage, point 2 (parcours de cadrage)

Le PO pensait le point en place ; vérifié dans le code : non. Depuis `c718055`, seul le choix des
modèles avait changé dans le panneau. Traité comme correctif, sans conception (PO).

- `cadrage.FramingPanel` porte la disposition du mode agent (`enter`, `reveal`, `leave`) : l'éditeur
  de demande est retiré et l'import désactivé en mode agent. Le brouillon de F fait apparaître
  l'éditeur sous le panneau, titré « Demande rédigée par F — à relire et corriger avant de créer ».
  Recliquer le mode agent ne cache pas un brouillon déjà rendu. Quitter le mode rétablit l'éditeur.
  Le libellé du mode devient « Cadrer avec un agent (une idée suffit) ».
- `creation.py` ne fait que câbler (+4 lignes, 423 au total, déjà au-dessus du plafond de vue de 400
  depuis le catalogue de modèles) ; la logique est dans `cadrage.py` (257).
- Test `test_the_idea_is_the_only_input_until_the_draft_appears_below_it` ; contre-épreuve (éditeur
  jamais retiré) → 1 échec, rétablie. Écran de création capturé avant et après le brouillon.
- Validation : ruff, mypy strict, **818 passés / 2 ignorés**, scénario rc=0. Façade + GUI 1 799 / 2 000.
- Commité et poussé : `1da53b7`.

## Session 2026-10-01 (suite) — types de mission, lot 1 (D1, D2, D3, D5, documentation)

Note `conception/TYPES_DE_MISSION.md` écrite puis validée telle quelle par le PO (`84a8694`).

- **D1** : `MissionKind.missing_source(corpus, web)`, seule règle, appelée par la façade (création
  CLI et GUI, avant et après la copie du corpus) et par `framing.prepare` (qui reçoit désormais
  `web_access`). Recherche : web ou corpus non vide. Conception : corpus non vide.
- **D2** : `prompts._CONCEPTION` (4 lignes, texte de la note) pour la proposition et la révision de A
  en conception ; une phrase ajoutée à la consigne de recherche (adresse et date d'une source web).
- **D3** : contrôle du corpus au lancement retiré de `workflow` ; pas de migration.
- **D5** : amendement daté sous la commande de `DEVELOPPEMENT_ASSISTE.md` §3.3, dont le texte, copie
  conforme du livrable accepté, n'est pas réécrit.
- **GUI, conséquence directe de D1** : type « Recherche » par défaut, case « Accès web pour A et B »
  remontée des réglages avancés à la ligne du type, cadre du corpus toujours affiché (bascule
  `_toggle_kind` supprimée, `creation.py` −4 lignes). L'accueil (D6) reste au lot 2.
- **Documentation** : README, `COMMANDES.md`, `PRISE_EN_MAIN.md` (la chaîne expliquée, l'exemple de
  recherche en premier), `CONFIGURATION.md`, `dialogforge.toml.exemple` (`kind = "recherche"`), aide
  de `--kind`. L'exemple de conception part maintenant du corpus d'exemple, comme le scénario de
  référence.
- **Tests** : les helpers qui créaient une conception sans corpus créent une recherche web
  (`new_args` ajoute `--web-access`, `bare_args` sans web). Nouveaux : refus d'une recherche sans
  source, d'une conception sans dossier (CLI, façade, cadrage), lancement sans recontrôle, consigne
  propre à chaque type. Contre-épreuves : consigne de conception remplacée par celle de recherche →
  1 échec ; conception acceptée sans corpus → 3 échecs ; chacune rétablie.
- **Erreur reproduite** : un script de remplacement passé en heredoc a transformé deux `\n` en vrais
  sauts de ligne (règle de `RULES.md` déjà écrite) ; corrigé à l'outil d'édition, puis scripts écrits
  par Write.
- Validation : ruff, mypy strict, **821 passés / 2 ignorés**, scénario rc=0. `src/` : +16 lignes
  effectives (6 397 → 6 413).
- Commité et poussé : `cd36f7b`.

## Session 2026-10-01 (suite) — types de mission, lot 2 (D6)

- **Accueil** : « Recherche → Conception → Développement » en titre, puis la phrase d'introduction
  de la note, à la place de « A produit · B critique · vous décidez » (repris dans la phrase).
- **Création** : une ligne sous le type dit ce qu'il attend, et suit le choix (`trace_add`).
- **Découpage** : `gui/widgets.py` (nouveau, 24 lignes) reçoit la section repliable et le
  « Choisir… » d'un champ de chemin ; trois méthodes de choix de fichier et une copie du calcul du
  délai retirées de `creation.py`, qui passe de 419 à **397** lignes (plafond de vue : 400).
- Tests : bandeau de l'accueil, ligne du type qui suit le choix (contre-épreuve : ligne figée →
  1 échec, rétablie). Accueil et création capturés à l'écran.
- Validation : ruff, mypy strict, **823 passés / 2 ignorés**, scénario rc=0. `src/` +7 ; façade +
  GUI 1 809 / 2 000 ; toutes les vues sous 400 lignes.
- Commité et poussé : `73b6a62`.

## Session 2026-10-01 (suite) — types de mission, lot 3 (D4, poursuivre en conception)

- **Moteur** : `corpus.build_from` (liste de chemins déjà connue ; `build` s'y ramène).
  `CreationRequest.from_research` ; `facade._check_follow_up` refuse : autre type que conception,
  autre corpus ou cadrage en plus, dossier illisible, source qui n'est pas une recherche, recherche
  non acceptée sur sa version actuelle (arrêt compris). Le corpus = `facade.FOLLOW_UP_FILES` :
  livrable, bilan **et `decisions.json`** — ajouté à la note, parce que les réserves d'une
  acceptation n'existent que là. Provenance : le manifeste nomme « recherche <nom> » et garde
  l'empreinte de chaque fichier, livrable compris ; aucun fichier nouveau.
- **Cadrage par F** : `check_creation(..., framing_start=True)` refuse `--depuis` avant tout appel
  (sinon le refus ne tombait qu'à la création finale, après les appels de F). Combiner les deux reste
  une extension possible, non engagée.
- **CLI** : `new --kind conception --depuis <recherche>` ; documenté dans `COMMANDES.md` et
  `PRISE_EN_MAIN.md`.
- **GUI** : `Presentation.can_follow_up` (règle dans la façade) ; bouton « Poursuivre en conception »
  sur l'écran de suivi ; `show_creation(from_research=…)` ouvre la création préparée (dossier
  voisin `…-conception`, type Conception, section Sources écrite, corpus remplacé par le dossier
  d'entrée). Pour tenir le plafond de vue, les réglages du prochain lancement passent dans
  `views/lancement.py` : `creation.py` 378 lignes.
- **Tests** : `tests/test_follow_up.py` (13). Contre-épreuves : acceptation non exigée sur le type de
  décision → d'abord **non détectée**, d'où le test « recherche arrêtée » ajouté, puis 1 échec ;
  refus au début du cadrage retiré → 1 échec ; chacune rétablie. Écrans de suivi et de création
  capturés.
- Validation : ruff, mypy strict, **835 passés / 2 ignorés**, scénario rc=0. `src/` +95 (6 423 →
  6 518) ; façade + GUI **1 897 / 2 000**.
- Commité et poussé : `680caa3`.

## Session 2026-10-01 (suite) — consolidation, partie 2 du plan de finalisation (2.1 à 2.3)

- **2.1 F03** : les conseils qui présentaient une reprise comme « gratuite », « locale » ou « sans
  appel » disent désormais que la suite peut appeler. Ça concerne `RUNNING` (`run` reprend sans
  repayer, puis le cycle appelle l'agent suivant), `--reprocess` (sans la repayer, puis le cycle
  reprend et peut appeler), `--answer` (puis A est rappelé), ainsi que l'aide de `resume`, de
  `--reprocess` et de `--answer` et la table des statuts et `--reprocess` de `COMMANDES.md`.
  `may_call` était déjà juste (la GUI confirmait) : seuls les textes mentaient par omission.
  `new --cadrer-avec-agent` annonçait déjà ses appels.
- **2.3** : `corpus.build_from` crée le dossier avant d'écrire le manifeste ; la façade refuse
  explicitement un corpus déclaré vide, avec ou sans web (« corpus déclaré mais vide »), au lieu
  de la `FileNotFoundError`. Contre-épreuve (dossier non créé) → 1 échec. Le diagnostic ponctuel
  de `status` pendant un remplacement Windows n'a pas été repris : aucune reproduction ciblée ne
  montre d'impact utilisateur (condition du plan).
- **2.2 F04** : `## Next Step` réduit à l'état, la prochaine action et les limites en vigueur ;
  l'ancien contenu est conservé daté sous « Historique des étapes ». Les repères périmés sont
  annotés sans être réécrits (corpus vide, plafond 1 200, taille de `creation.py`, ligne d'erreur
  du lot 4). Current Phase et phase 7 sont à jour (7.3, 7.4 faits ; 7.5 = 2.4 ouverte).
  **Conflit de règle résolu** : `CLAUDE.md` §3 disait la relecture palier par palier « suspendue
  depuis le 2026-09-03 », alors que `RULES.md` la dit **rouverte le 2026-09-05** (condition
  réalisée). `CLAUDE.md` renvoie désormais à la décision la plus récente, celle de `RULES.md`.
- Validation : ruff, mypy strict, **835 passés / 2 ignorés**, scénario rc=0 (A=2, B=2, inchangé).
  `src/` +4.
# Session 2026-10-01 — début Runner V1

- PO : nouvelle branche et début du Runner à partir de la conception simplifiée.
- Branche `feat/runner-v1` créée depuis `main` ; les deux conceptions Runner non suivies sont conservées.
- Exception du Runner distinct explicitée dans `CLAUDE.md` et `project/RULES.md`.
- Socle : vérification publique de l'export, préparation d'un clone sans remote, collecte d'un HEAD committé et propre, validations finales avec traces, paquet par `development.build_package`.
- Tests sans fournisseur : réussite et second paquet, validation échouée, validation qui modifie le candidat, export altéré et entrée CLI. Intégration d'agent writable encore à qualifier.
- Vérification : `ruff check .`, `mypy --strict` ; suite `tests/` : 834 passés, 8 ignorés, 647 sous-tests. Après ajout du cas « commande de validation absente » : 6 tests Runner et contrôles statiques verts. `pytest -q` à la racine balaie aussi `tools/planning-with-files/` et échoue à la collecte faute de `yaml` ; `pytest tests -q` est la suite du projet.
- Interface interne `run_agent` : un appel transmet le mandat entier, laisse l'agent organiser et committer, puis collecte sous le même verrou. Un échec garde les traces et ne relance rien ; la continuation est explicite. Faux agent testé jusqu'au paquet, et bilan stdout joint aux notes du paquet. Adaptateur fournisseur réel absent.
- Recontrôle après le lancement interne : 8 tests Runner passés ; `ruff check .` et `mypy --strict` passent. Sur Windows, la sortie du faux agent peut être encodée selon la console locale : le bilan déclaré est normalisé en UTF-8 avant son ajout au paquet.
- Qualification réelle, Claude Code 2.1.286 : `dontAsk` refuse l'écriture locale sans autorisation ; `--allowedTools Write,Edit` permet l'écriture locale et refuse la lecture du témoin voisin ; `--allowedTools Write,Edit,Bash` permet au shell de modifier ce témoin voisin malgré `--restricted`. Vérifié depuis le parent (`INSIDE_OK`, puis `SHELL_OUTSIDE`). Profil rejeté pour unattended ; aucun lot réel lancé. Rapport : `reference/RUNNER_QUALIFICATION_2026-10-01.md`. Docker/Podman absents du PATH, WSL sans distribution.
- Correction de la recherche CLI : Codex était installé sous `codex.cmd`, version 0.159.3. `codex exec --sandbox workspace-write` avec bac à sable Windows `elevated` : écriture dans `workspace` réussie, écriture du témoin source refusée (`Access denied`). `codex sandbox -P :workspace` : script de validation dans le workspace réussi, témoin source refusé (`UnauthorizedAccessException`). Contenus vérifiés depuis le parent. Frontière d'écriture qualifiée sur ces témoins ; Git, réseau et credentials restent à qualifier.

## Session 2026-10-02 — qualification Claude sous WSL2 et passage de relais

- Ubuntu 24.04 WSL2 installé par le PO. Dans Ubuntu : `bubblewrap`, `socat`, `ripgrep`, Claude Code 2.1.285, Node.js 24.21.0 (archive officielle, SHA256 vérifié) et `@anthropic-ai/sandbox-runtime` 0.0.78. Le jeton Claude est saisi masqué au moment des essais ; il n'est pas persisté dans Ubuntu (`claude auth status` reste déconnecté).
- `tools/qualify_claude_wsl.sh` : Claude, avec `--restricted`, Bash autorisé, sandbox activé, `failIfUnavailable=true` et `allowUnsandboxedCommands=false`, a écrit `SHELL_INSIDE` dans son espace. Le témoin frère Linux est resté `SOURCE_ORIGINAL`, celui du volume Windows `HOST_ORIGINAL`. Les traces du deuxième essai montrent les refus des écritures extérieures et de `powershell.exe` sur le PATH. Les traces et témoins ont été relus indépendamment de la réponse de l'agent.
- `tools/qualify_claude_wsl_validation.sh` : commande de validation autonome dans `srt` avec `allowWrite: ["."]` : `inside=0`, `outside=1`, `interop=1`. Le runtime annonce l'application de seccomp ; dossier frère en lecture seule, lancement WSL du binaire Windows copié refusé (`UtilConnectUnix:524: socket failed 1`). Témoins extérieurs inchangés. Traces : `/home/schneider/dialogforge-validation-qual.3IvOAYgU/`.
- Deux tentatives d'agent combinant les écritures extérieures et l'exécutable Windows copié n'ont pas qualifié ce dernier : un classificateur a interrompu un appel dans chacune, puis Claude a refusé de poursuivre. Le code de sortie CLI était pourtant 0. `tools/qualify_claude_wsl_interop.sh` a isolé une commande **sans écriture** ; Claude a réellement tenté `./powershell-probe.exe ... Write-Output INTEROP_OK`, résultat `socket failed 1`, code 1, sans `INTEROP_OK` ni interruption du classificateur. Traces : `/home/schneider/dialogforge-interop-qual.Ho56mikF/`. Le même exécutable fonctionnait hors sandbox. Le profil Claude testé bloque donc cette voie d'interopérabilité WSL.
- Rapport détaillé : `reference/RUNNER_QUALIFICATION_2026-10-01.md` ; résumé d'usage actualisé dans `docs/RUNNER.md`. Syntaxe Bash des scripts vérifiée. Limite : qualification d'une frontière d'écriture sur ces témoins, pas du réseau, des secrets, des commits ou d'un lot complet. Aucun agent fournisseur n'a encore été branché au Runner ; sa collecte actuelle exécute toujours les validations avec les droits du processus local.
- Reprise demandée par le PO dans une nouvelle session avec terminal frais. Branche `feat/runner-v1` ; le socle et les rapports restent **non commités** dans l'arbre de travail. Lire le `## Next Step` de `task_plan.md` et le rapport avant de modifier l'intégration. Ne pas interpréter le code de sortie 0 d'une session Claude comme preuve que tous les appels d'outil demandés ont eu lieu.

## Session 2026-10-02 — reprise Runner, raccordement du profil Claude WSL2

- `prepare --profile claude-wsl` exige un dossier d'exécution natif Linux hors de `/mnt`. `run-claude` lance le profil strict qualifié avec le jeton seulement dans l'environnement du processus Claude ; le mandat arrive par stdin. Les validations passent par `srt` avec `allowWrite: ["."]` depuis le clone et un environnement sans jeton.
- `docs/RUNNER.md` décrit les commandes et la continuation explicite. Deux tests ajoutés : refus du profil sur Windows et chemin de validation `srt` sans transmission du jeton. Suite complète : 839 passés, 8 ignorés, 648 sous-tests ; Ruff vert ; mypy ciblé Runner vert. Le mypy global via `py -3.12` relève 6 erreurs Tk préexistantes dans `cadrage.py` et `test_gui_cadrage.py` ; l'exécutable mypy de la venv pointe vers un ancien Python absent.
- Aucun appel fournisseur n'a été lancé. L'accès à WSL depuis le terminal sandboxé a échoué (`E_ACCESSDENIED`) ; la demande d'accès étendu a été interrompue. La qualification de bout en bout sur dépôt jetable reste donc ouverte, ainsi que réseau, credentials et commits. Aucun commit ni push.

## Session 2026-10-02 — qualification du raccordement WSL2

- L'accès WSL a été autorisé. Python 3.12.3, `srt` et Claude sont présents dans Ubuntu. Le premier essai de `tools/qualify_runner_wsl.py` a révélé que l'argument `-c` de Python était pris pour une option de `srt`. Ajout de `--` avant la commande ; le test ciblé vérifie ce séparateur.
- Le faux agent sous `srt` a produit un commit ; la validation sous `srt` a passé ; le paquet contient le même `HEAD` et le bon fichier. Dossier témoin : `/home/schneider/dialogforge-runner-qual.4rqe00yg/`. Le dépôt source et son témoin secret sont inchangés.
- La documentation locale de `srt` précise : réseau refusé lorsque `allowedDomains` est vide ; lecture autorisée partout lorsque `denyRead` est vide. Les validations refusent maintenant la lecture du dossier personnel et ne rouvrent que le clone. Une validation réelle a constaté l'invisibilité du témoin situé dans le dépôt source. L'environnement de test doit être dans le clone ou sous les outils système.
- `tools/qualify_runner_wsl.py --claude` prépare le même scénario avec un vrai appel et saisie masquée du jeton. À ce point de la session, cet appel fournisseur attend l'action du PO dans son terminal Ubuntu. Ruff et mypy ciblé verts ; le faux agent est repassé après la correction. Aucun commit ni push.

## Session 2026-10-02 — essai réel Claude sur dépôt jetable

- Le PO a lancé `tools/qualify_runner_wsl.py --claude` dans Ubuntu avec jeton masqué. Dossier : `/home/schneider/dialogforge-runner-qual.20mhv372/`. Appel Claude : code 0, 17,637 s, bilan non vide. Le clone porte le commit `83a28bd30675aeee9e206a8fb96a6df21f2ba15e` sur la base `8cbfc17` ; espace propre après l'appel.
- `code.txt` vaut exactement `candidate\n` dans le clone et reste `base\n` dans le dépôt source. Le témoin extérieur `secret.txt` reste `OUTSIDE_SECRET`. Claude rapporte qu'il ne pouvait pas lire ce témoin. La validation finale sous `srt` passe (`VALID_OK`) et atteste l'invisibilité du témoin ; le paquet contient le même `head_oid`, le fichier, la validation et le bilan.
- Le script de qualification a rendu une `AssertionError` **après la création du paquet** : il exigeait `BILAN_OK`, marqueur réservé au faux agent. Corrigé pour accepter un bilan non vide dans le mode réel. Aucun nouvel appel Claude pour cette correction. Le mode faux agent repasse ; Ruff et mypy ciblé verts.
- Ce scénario qualifie l'intégration réelle du Runner, les commits et le paquet sur un lot minimal. Il ne qualifie pas encore les capacités réseau de l'agent ni une politique exhaustive sur les identifiants. Aucun commit ni push du projet.

## Session 2026-10-02 — frontières réseau et identifiants sans fournisseur

- `tools/qualify_runner_boundaries_wsl.py` lance `srt` sur un dossier jetable avec faux jeton, faux secret hors clone et serveur TCP local. Résultat : `TOKEN_DENIED`, `SECRET_HIDDEN`, `NETWORK_DENIED` ; le contrôle hors sandbox pouvait joindre le serveur. Traces : `/home/schneider/dialogforge-boundaries-qual.upxive_3/`.
- Cela mesure directement le runtime `srt`, avec les réglages de lecture et de réseau du Runner ; le masquage du jeton emploie la règle `credentials.envVars` du même runtime. L'essai réel Claude a déjà constaté l'absence de lecture du témoin extérieur. Il manque encore une mesure des accès réseau et au jeton depuis l'outil Bash lancé par Claude lui-même pour annoncer le profil complètement qualifié avant un lot sans surveillance.
- `tools/qualify_claude_boundaries_wsl.py` prépare cette dernière mesure dans un appel Claude unique. Il vérifie les événements `tool_use`/`tool_result` du vrai Bash plutôt que la seule réponse finale, sans imprimer le jeton. Ruff et compilation Python verts ; lancement réel demandé au PO, qui saisit le jeton dans Ubuntu.

## Session 2026-10-02 — frontières dans le vrai outil Bash de Claude

- Le PO a lancé `tools/qualify_claude_boundaries_wsl.py` avec jeton masqué. Dossier : `/home/schneider/dialogforge-claude-boundaries.cxhordoe/`. L'appel Claude s'est terminé avec code 0. Relecture hors ligne du `tool_use`/`tool_result` par `--verify`, sans second appel : un unique Bash correspondant à `probe.py` a rendu `TOKEN_DENIED` et `NETWORK_DENIED` ; aucun marqueur contraire. Le contrôle parent joignait le serveur TCP local.
- La frontière du jeton et du réseau est donc mesurée pour l'outil Bash de ce profil sur ces témoins, en plus des essais précédents de fichiers, commits, validation et paquet. Cette mesure ne prouve pas une isolation universelle contre toutes les voies possibles ; elle suffit à passer au premier petit lot pilote avec revue humaine. Aucun commit ni push du projet.

## Session 2026-10-03 — Runner depuis la GUI

- À la demande du PO, le suivi d'une conception acceptée sur sa version actuelle propose « Développer avec le Runner » ; acceptation avec réserves comprise. La GUI exporte le mandat, lance un pont Windows → Ubuntu WSL2, prépare le clone Linux et appelle Claude. Elle affiche le dossier d'exécution, le paquet ou l'erreur, et offre une continuation explicite ou une collecte sans appel. Une seule exécution active ; la fermeture attend la pause ou l'interruption effective.
- Le jeton saisi masqué part par l'entrée standard du pont, n'apparaît ni en argument de processus ni dans un fichier de configuration. Une pause très précoce est mise en attente jusqu'après l'envoi de la requête initiale ; ce cas a un test dédié. Une interruption avant validation empêche le lancement de la commande de validation.
- Qualification sans nouvel appel fournisseur : `tools/qualify_runner_wsl.py` a vérifié sous Ubuntu le faux agent et le paquet, puis le pont GUI en collecte et le passage de chemins Windows vers WSL pour export et clone. Le mode réel avait déjà été qualifié le 2026-10-02 ; le lancement complet depuis une fenêtre avec jeton réel reste à éprouver sur le premier lot pilote.
- Vérification : 42 tests ciblés passés, Ruff vert, `git diff --check` sans erreur. Avant les deux derniers tests, la suite complète a rendu 842 passés, 8 ignorés, 668 sous-tests ; le typage strict global conserve les erreurs Tk préexistantes de `cadrage.py` et `test_gui_cadrage.py`. Mesure actuelle : `src/` +766 lignes effectives depuis HEAD, GUI + façade 2 216 / 2 400, plus grande vue `creation.py` 378 / 400.
- Aucun commit ni push du projet.

## Session 2026-10-03 — analyse du parcours Mastermind

- Lecture des deux missions et des transitions du code : corpus transmis, demande de conception vide, attente humaine confirmée. Conception sans corpus refusée par D1. Runner : dépôt avec commit nécessaire, reprise et accès à la revue à améliorer.
- Proposition : conception directe facultativement cadrée, mandat transmis, dossier de mission commun, parcours nouveau projet puis revue. Document : conception/PARCOURS_MISSION_2026-10-03.md. Exigence utilisateur conservée : la conception reste dans Mastermind.
- Tests ciblés existants : 47 passés, 26 sous-tests ; aucun appel fournisseur. Aucun code modifié, aucune mission déplacée, aucun commit. Proposition à arbitrer ; règles existantes non amendées avant décision.


## Session 2026-10-03 — conception du parcours de mission

- Le PO accepte les orientations de l'analyse et demande leur conception dans conception/. Document livré : conception/PARCOURS_MISSION_CONCEPTION.md.
- Contenu : contrats des étapes, registre de mission, transmission et cadrage complémentaire, compatibilité CLI/GUI, nouveau projet, reprise Runner, revue et intégration explicite, migration Mastermind, quatre lots et seize critères d'acceptation.
- Mise à jour du statut de l'analyse et du Next Step. Travail documentaire uniquement ; aucun appel fournisseur, aucune modification de code ni des missions réelles. Les tests de la passe précédente ne sont pas présentés comme validation de la conception future.


## Session 2026-10-03 — parcours de mission, lot 1 (contrat des étapes)

- Mise en œuvre de `conception/PARCOURS_MISSION_CONCEPTION.md`, lot 1 seulement. Vérification préalable de la conception contre le code : aucune contradiction bloquante. Écarts ordinaires résolus sans nouvelle décision : `check_creation(framing_start=…)` supprimé (plus de refus `--depuis` + cadrage) ; `FOLLOW_UP_FILES` reçoit aussi `demande.md` ; les actions A/B, la GUI et la CLI n'ont qu'un seul instantané (`facade.FollowUp`) ; le dossier voisin `<recherche>-conception` reste proposé jusqu'au lot 2 (le dossier de mission est son objet).
- **Moteur.** `MissionKind.missing_source` : plus d'exigence de corpus en conception (recherche inchangée, AC02 couvert) ; corpus déclaré mais vide refusé aussi dans `framing.prepare`. `prompts.py` : bloc d'étape pour A (recherche = étude, conception = plan ; hypothèses non promues), pour B (`build_review(kind=…)`, l'absence de code n'est pas un défaut d'un plan) et pour F (étape + « Précise seulement les arbitrages encore nécessaires… » en transition).
- **Transition.** `facade.prepare_follow_up` copie demande, livrable, bilan et `decisions.json` sous le verrou de la recherche, construit le mandat de §4.2 sans appel (demande d'origine citée ligne à ligne en citation Markdown : ses titres ne deviennent pas des sections) et expose la configuration source. `check_creation` revérifie acceptation, décision et empreintes ; la création copie l'instantané (aucune reconstruction) et écrit `provenance_transition.json` (décision, chemin source relatif, empreinte du manifeste). Aucune décision n'est écrite dans la conception : les hypothèses restent des hypothèses.
- **CLI.** `new --depuis` : sans `--demande`, le mandat généré sert de demande ; réglages A/B, modèles (suivant leur outil), effort, révisions, accès web hérités de la recherche sous les drapeaux, affichés sur stderr ; `--cadrer-avec-agent` se combine avec `--depuis` (F reçoit le mandat comme idée et le corpus de l'instantané). Une demande reste exigée sans `--depuis` (refus code 1 ; auparavant, argparse code 2).
- **GUI.** Types « Étudier une question » / « Concevoir mon projet » avec leur livrable ; corpus facultatif ; « Poursuivre en conception » préremplit dossier, mandat (aussi dans l'idée de F), agents, modèles, effort, révisions, accès du critique et affiche l'accès web hérité ; le dossier jetable de l'instantané est détruit à la sortie du formulaire. Cadrage F possible sur la transition.
- **Correctif collatéral.** `transport._feed` : la fermeture du tube pouvait lever `OSError` dans le fil d'écriture quand un faux agent sort sans tout lire (des prompts plus longs l'ont révélé : 4 avertissements dans `test_development`) ; filet et test ajoutés. Les vrais agents lisent tout leur stdin ; effet de production attendu nul.
- **Tests (faux agents uniquement).** `tests/test_follow_up.py` réécrit (snapshot, mandat, création, AC04 acceptation périmée ou source modifiée, AC05 cadrage CLI et GUI sur le même instantané avec un seul `build_from`, héritage CLI, nettoyage GUI) ; conception sans corpus créée **et exécutée** (`test_facade_creation`), cadrée (`test_framing_creation`), prompts de F/A/B (`test_prompts`). Anciens tests dont la règle change adaptés (D1) : `test_cli`, `test_demande`, `test_framing`, `test_gui_creation`. Résultat final : **876 passés, 2 ignorés, 666 sous-tests**, sans avertissement ; `ruff check .` vert ; `mypy src tests` vert (93 fichiers). Base avant le lot : 849 passés, 2 ignorés.
- **Plafonds (compteur tokenize sans commentaires ni docstrings, identique avant/après).** Façade + GUI : 2 216 → **2 322 / 2 400** (+106). Plus grande vue : `creation.py` 378 → **400 / 400**, atteint exactement. `src/` : 7 294 → 7 504 (+210 pour le lot ; +979 depuis HEAD, dont ~770 du Runner non commité). Rien n'a été déplacé pour contourner la métrique ; une addition à `creation.py` exigera un découpage ou une re-décision.
- **Limites restantes.** Pas de dossier de mission ni de rattachement (lot 2). Le mandat CLI n'est pas modifiable avant création (`--demande` le remplace). Les prompts sont fixés comme contrats : leur qualité réelle ne se mesure que par la recette Mastermind. Aucun appel fournisseur, aucun commit, aucun push ; `Mastermind` et `Mastermind-conception` intactes ; modifications Runner préservées.

- **Retours de revue du lot 1 (même jour).** (1) Le cadrage GUI ignorait une correction du mandat : F lisait l'ancien champ « idée ». `transition.sync_idea` recopie la demande à l'écran dans l'idée à l'entrée en mode agent. (2) Un modèle hérité absent du catalogue GUI était remis à « par défaut » sans avertissement : `model_catalog.inherit` l'ajoute, étiqueté « (hérité de la recherche) », et `selected` le restitue tel quel ; un changement d'outil le retire. Le formulaire de transition passe de `creation.py` à `gui/views/transition.py`. Tests ajoutés : mandat édité reçu par F, modèle hors catalogue conservé, `inherit`. Total : **880 passés, 2 ignorés, 676 sous-tests** ; Ruff et mypy verts. Mesures : façade + GUI **2 339 / 2 400**, `creation.py` **379 / 400**, `src/` 7 529.


## Session 2026-10-03 — parcours de mission, lot 2 (dossier de mission, navigation, reprise)

- Départ : l'arbre de travail était **propre** (Runner `273803a` et lot 1 `316f87f` déjà committés, contrairement à la consigne). Les deux corrections de revue du lot 1 (mandat édité reçu par F ; modèle hérité hors catalogue conservé) étaient en place avec leurs tests ; 35 tests ciblés repassés avant de commencer.
- **`src/iabinome/mission.py`** (nouveau, 412 lignes) : registre `mission.json` strict (clés exactes, chemins relatifs sans `..` ni lien sortant, doublons et sources antérieures contrôlés ; invalide = diagnostic, jamais réinitialisé), verrou `verrou-mission.json` limité à l'écriture, `create_step` (règles → création partagée → inscription), `attach`, `adopt` (copie vérifiée par empreintes, publication par renommage, original intact, `source_path` recalculé s'il existe), `locate`/`resolve`/`fold`/`summarize`/`continuations`/`default_dest`. Aucun appel IA.
- **Façade** : `CreationRequest.mission` et `new_version`, `create_collaboration` délègue à `mission.create_step` ; `CreationError` descend dans `models.py` pour que `MissionError` en hérite (la CLI et la GUI l'attrapent déjà).
- **CLI** : `new --mission RACINE [--nouvelle-version]`, `show` (mission, `--etape`), `list` (une entrée par mission), `mission attach|adopt`. Indication sur stderr quand `--depuis` vise une recherche rattachée sans `--mission`.
- **GUI** : `recents` retient `last_step` (préférence d'affichage) ; le contrôleur ouvre une mission sur l'étape retenue et replie les récents en une entrée par mission ; l'accueil donne la situation de chaque étape ; le suivi montre l'en-tête de mission (navigation) et « Reprendre la conception » / « Nouvelle version de conception » ; le formulaire range la conception dans la mission. Création d'une nouvelle mission depuis la GUI : non faite (la CLI le fait).
- **Défaut trouvé par les tests** : `attach` refusait la collaboration historique à la racine — le cas Mastermind. Le refus ne vaut que pour une création implicite ; corrigé et testé.
- **Tests** : `tests/test_mission.py` (72) — registre, création, versions explicites, AC09 (échec d'inscription réparé par rattachement, 0 appel), verrou, navigation, CLI, GUI (en-tête, récents, reprise sans doublon, formulaire), procédure Mastermind sur une réplique (copie identique, original intact, `source_path` recalculé, reprise avec réponse par faux agents sans rejeu). `test_follow_up` et `test_docs` adaptés ; `docs/COMMANDES.md`, `PRISE_EN_MAIN.md`, README, règles, `TYPES_DE_MISSION.md`, `PARCOURS_MISSION_CONCEPTION.md` (écarts du lot 2) mis à jour. **952 passés, 2 ignorés, 695 sous-tests** ; ruff et mypy verts.
- **Mastermind — répétition sur copie des dossiers réels** (lecture seule sur les originaux, copie sous le dossier temporaire de session) : copies identiques aux originaux ; `mission attach` puis `mission adopt` : conception copiée **sans écart** (16 fichiers), sauvegarde et recherche inchangées, seuls `mission.json` et `conception/` ajoutés ; `show`, `status`, ouverture de la racine corrects ; reprise avec réponse sur une seconde copie sous faux agents : `AWAITING_APPROVAL`, 1 appel A et 1 B, corpus intact. **Constat** : la conception réelle n'a pas de `provenance_transition.json` ; 2 chemins absolus seulement, en prose dans le corpus haché. **L'exécution sur les dossiers réels a été refusée par le contrôle de permissions de la session : non faite**, ni recents modifiés. Procédure et vérifications : `reference/REGROUPEMENT_MASTERMIND.md`.
- **Plafonds** (compteur tokenize, mêmes règles qu'avant) : façade + GUI 2 339 → **2 414** (+75) sur 2 400 — dépassement de 14, **le PO a dit le 2026-10-03 que le plafond peut être relevé** plutôt que de comprimer le code ; relèvement à 2 500 proposé dans `RULES.md`, à confirmer. Par fichier : façade +14, `controller` +14, `recents` +6, `accueil` +3, `creation` +6 (385 / 400), `suivi` +41 (en-tête de mission, poursuite). `mission.py` 412 (hors plafond façade + GUI). `src/` 7 529 → 8 107 (outil `measure_development.py`).
- Aucun appel fournisseur, aucun commit, aucun push. Lots 3 et 4 non commencés.

- **Retours de revue du lot 2 (même jour).** (1) Le registre acceptait une `source` ne désignant aucune étape : `load` exige désormais une étape **antérieure réellement inscrite** (inexistante, future ou soi-même : refusées). (2) `mission adopt` pouvait publier la copie avant de découvrir que le rôle ou `--source` interdisait le rattachement : les refus prévisibles (rôle inconnu, type incompatible, source absente, étape déjà inscrite, version numérotée attendue, registre invalide) sont vérifiés **avant la copie** par `_admit`, partagé avec `attach` ; seul un véritable échec d'écriture du registre laisse « copiée mais non inscrite », avec la commande de rattachement. Tests ajoutés (copie jamais lancée dans chaque refus, registre et dossier inchangés, échec d'écriture réel conservé) ; contre-épreuve : sans `_admit`, 3 tests échouent. **957 passés, 2 ignorés, 699 sous-tests** ; ruff et mypy verts. Plafond façade + GUI relevé à 2 500 (accord du PO, 2026-10-03) ; compter `mission.py` à part confirmé. Reste : reprise réelle de Mastermind (PO), création d'une mission neuve depuis la GUI.


## Session 2026-10-03 — parcours de mission, lot 3 (préparation et reprise du Runner)

- Départ : arbre propre sur `feat/runner-v1`, 957 tests passés. Mesure : Ubuntu WSL n'a aucune identité Git ; celle de l'utilisateur n'existe que sous Windows.
- **Runner** (`core.py`, `gui_bridge.py`, `cli.py`) : `git_identity`, `check_new_project`, `init_project`, `reuse_initial_base`, `preflight`, `inspect_run` ; `prepare` rend l'OID et reporte l'identité en configuration locale du clone seulement si Ubuntu n'en voit aucune. Pont : actions `check`, `prepare`, `launch`, `continue`, `collect`, `inspect` (`start` supprimé), jeton réservé à `launch` et `continue`. CLI : `init-project`, `inspect`.
- **Mission** : `executions.py` (référence `developpement/executions/NNN.json` à schéma strict sans jeton ni statut, export `export-NNN` repris s'il est octet pour octet identique, paramètres de l'écran, règles du formulaire, départs permis par état). `development.export_files` (contenu exact sans écriture) ; le mandat dit que les constats ouverts seront réexaminés par la revue du candidat.
- **GUI** : session en étapes (prérequis, export, référence, dépôt initial, clone, appel), écran avec choix de la voie, lignes de validation, texte de la conception, reprise par lecture du dossier Linux.
- **Tests (faux agents, dépôts jetables, aucun fournisseur)** : `test_runner_project` (16), `test_executions` (14), `test_runner_flow` (17, vrai pont en sous-processus), `test_gui_runner` (14). **1 015 passés, 2 ignorés, 703 sous-tests** ; ruff et mypy verts. 10 contre-épreuves (mutation du code puis restauration) toutes détectées.
- **Essai réel Ubuntu sans fournisseur** : projet neuf créé avec l'identité réelle, clone préparé, pause avant l'agent, candidat committé à la main, `node --test` sous `srt`, paquet, source intacte, dossier d'essai supprimé. `tools/qualify_runner_wsl.py` réécrit pour le nouveau protocole et rejoué : vert.
- **Défauts trouvés** : un pont de test sous Windows bloquait `git` 60 s (tube d'entrée hérité) ; accents en U+FFFD sans UTF-8 forcé. Trois fois, un script de remplacement en heredoc a mutilé les `\n` (règle déjà connue) ; fins de ligne CRLF introduites puis normalisées.
- **Plafonds** : façade + GUI 2 414 → **2 577 / 2 500** (dépassement de 77, re-décision demandée) ; plus grande vue `creation.py` 385 / 400 (`runner.py` 253) ; `src/` 8 123 → 8 636 (+513, dont −3 d'artefact du compteur sur `modeles.toml`).
- Limites : `find` prend brièvement le verrou de la conception à l'ouverture de l'écran ; chemin du paquet = chemin Ubuntu (lot 4) ; prérequis non vérifiés pour un chemin relatif au clone ; `Mastermind/code` non créé. Aucun commit, aucun push.

- **Retours de revue du lot 3 (même jour).** (1) Conception modifiée pendant la préparation : `executions.check_current` relit la décision et compare le contenu actuel à l'export enregistré avant `launch` et `continue` ; en cas d'écart, aucun agent n'est appelé, le clone est conservé, un nouvel export et une nouvelle exécution sont exigés. (2) Paquet masqué après un échec : `inspect_run` rend `last_collect` (`reussie`/`echouee`) séparément de `package` (dernier paquet valide, toutes collectes confondues) ; l'écran dit « dernière collecte échouée » et que le paquet antérieur ne valide pas le code actuel. Tests ajoutés : conception changée entre `prepare` et `launch`/`continue` (0 appel agent, clone intact), paquet réussi puis collecte échouée puis réouverture, `check_current` unitaire ; contre-épreuve (garde neutralisée) détectée. **1 020 passés, 2 ignorés, 703 sous-tests** ; ruff et mypy verts.
- **Plafonds** : le PO porte façade + GUI à **2 700** (relevé 2 583) et fixe **3 000** comme plafond à ne pas dépasser ensuite (voir `RULES.md`). Plus grande vue : `creation.py` 385 / 400.

## Session 2026-10-03 — Runner après la première exécution réelle Mastermind

- Mastermind a produit quatre paquets pour la **même** tête Git `dde9eaa` : le premier appel utile a créé six commits et passé `node --test` (23/23), puis trois clics « Continuer » n'ont rien ajouté. Le quatrième bilan dit explicitement que le lot est déjà réalisé. Le code reste dans le clone Ubuntu ; la recette navigateur C01 à C22 et le lot 4 restent à faire.
- Correctif : paquet réussi = arrêt lisible avec bilan et validations ; une nouvelle correction exige un objectif saisi, transmis au prompt. La continuation CLI après paquet exige aussi `--correction`. Le dernier appel après un paquet est distingué du paquet ancien dans `inspect_run`. En cas de validation finale échouée **pendant un lancement GUI autorisé**, au plus deux appels correctifs supplémentaires, dans la durée totale saisie, réutilisent le jeton en mémoire ; aucun appel automatique après un paquet réussi ou après réouverture.
- Diagnostic : une erreur OAuth 401 connue est nommée à l'écran sans exposer la sortie brute. Aucun secret ajouté à la référence, aucun appel fournisseur lancé pour cette modification.
- Vérification : 54 tests ciblés de flux, projet et référence passés ; 15 tests GUI passés, 4 sous-tests ; `test_docs.py` : 8 tests et 214 sous-tests passés. Un regroupement des quatre fichiers a eu deux échecs intermittents de fixture GUI (`workflow.decide` trouvait `INTERRUPTED`) qui disparaissent en exécutant `test_gui_runner.py` séparément ; aucun échec du parcours Runner dans cette exécution. Ruff et mypy verts. Lecture réelle `dialogforge-run inspect` sur Mastermind : `stage=paquet`, 5 appels, 4 collectes, dernier paquet et bilan visibles. Façade + GUI : 2 643 / 2 700 ; vue Runner : 282 / 400. `src/` : 8 123 au HEAD, 8 781 après ce correctif (ajout net 658). Un test supplémentaire vérifie qu'une correction sans nouveau commit conserve le paquet antérieur.
- **Suite complète finale : 1 019 tests réussis, 8 ignorés, 703 sous-tests**, code 0 (4 min 10 s). Les échecs intermittents de fixture du regroupement ciblé n'ont pas reparu ; `ruff check .` et `mypy src tests` verts, `git diff --check` sans erreur.

## Session 2026-10-04 — suite du paquet Runner et lot 4

- Retour réel du PO : huit appels et sept collectes Mastermind, toujours la même tête Git ; « correction » et ressaisie du jeton ne permettent pas d'avancer. Le dernier paquet est valide (`node --test`, 23 tests), malgré une trace d'authentification échouée après le travail utile.
- `delivery.py` : copie vérifiée et atomique du paquet WSL dans `developpement/paquets/`, création/reprise d'une revue liée dans `developpement/revues/`, provenance relative et rattachement à la mission. L'écran Runner propose « Poursuivre : examiner le paquet », sans jeton ni nouvel appel agent.
- Après acceptation actuelle de la revue, le suivi propose une intégration explicite. Le Runner construit un bundle Git du commit exact ; le dépôt cible doit être propre à la base attendue et n'avance qu'en fast-forward. Un reçu permet de reconnaître la même tête après interruption. Aucun merge de résolution ni écrasement.
- `inspect_run` choisit le dernier bilan d'appel réussi : la trace OAuth 401 ultérieure n'est plus présentée comme bilan du paquet réussi. « Collecter sans appel » devient « Vérifier le candidat sans agent ».
- Paquet Mastermind réel lu en lecture seule via `\\wsl.localhost` : base et export correspondent à la référence ; création d'une revue sur copie temporaire, `dev-verify` : READY. Aucun fichier de la mission réelle n'a été modifié et aucun agent réel appelé.
- Vérifications ciblées : transfert, revue, bundle, intégration et GUI verts ; Ruff et mypy verts. Suite `tests/` : 1 025 passés, 8 ignorés, un échec de fixture Tk connu (`workflow.decide` sur `INTERRUPTED`) sous charge ; `test_gui_runner.py` isolé vert. La fixture GUI force désormais la collecte des variables Tk avant son fil moteur ; suite complète à rejouer après cet ajustement.
- Taille avec `measure_development.py` : `src/` 9 131 lignes effectives (+1 008 depuis HEAD, lots 3, correction et 4 mêlés). Façade + GUI : **2 700 / 2 700** ; vues Runner et suivi sous 400. Aucun commit ni push.
- Après collecte des variables Tk avant la fixture GUI, **suite complète `pytest tests -q` : 1 027 passés, 8 ignorés, 706 sous-tests**, code 0 (4 min 19 s). Un dernier ajustement de visibilité du bouton d'intégration exige une décision applicable ; ses tests ciblés passent. Ruff et mypy verts. Façade + GUI finale : 2 698 / 2 700.

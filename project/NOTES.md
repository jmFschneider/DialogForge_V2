# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. Historique → `session_log.md`. Règles → `RULES.md`.
> Dernière mise à jour : 2026-09-04

---

## Prochaine action — une seule

**Committer le palier 4**, puis rouvrir la question du budget de production *avant le palier 5 s'il
y en a un* — pas la refermer. Voir « Budget » ci-dessous.

**Aucun commit n'a encore été fait cette session** — le travail est sur disque, vert (`ruff`, `mypy
--strict`, `pytest`), en attente de la commande de commit.

---

## Palier 4 — clos

`adapters/claude.py`, `adapters/codex.py`, `cli.py`, `__main__.py` écrits et testés. Les trois
décisions D-1/D-2/D-3 de la session précédente sont tranchées **dans** `CONCEPTION_FINALE.md` (§1,
§5, §12.3 — pas seulement ici, conformément à `RULES.md`) :

- **D-1** — `CONSULT` reste le défaut. `CONTEXT_ONLY` n'est plus mécaniquement bloqué pour Codex
  (`-c features.shell_tool=false`, équivalent mesuré à `--disable shell_tool`), mais reste partiel
  (réserve non essayée : les huit autres capacités listées en §12.3). Les deux adaptateurs déclarent
  `supports_context_only=True`.
- **D-2** — `workflow.py` teste `resultat.json.return_code != 0` **avant** `store_response()`, dans
  `new_call` et dans `resume_call` : incident `CLI_FAILED`, état `INTERRUPTED`, jamais de tentative de
  contrat. Testé en appel direct (`test_workflow.TestCliFailed`) et en reprise
  (`test_recovery.TestRecoveryTable.test_non_zero_return_code_found_on_resume_is_cli_failed`).
- **D-3** — une phrase ajoutée à `CONCEPTION_FINALE.md` §1 : la base `memories` de Codex
  (`~/.codex/memories_1.sqlite`) peut transporter un état d'un appel au suivant, hors de la
  collaboration. Ne casse aucune des cinq garanties de §1.

**Suite verte** : `ruff check .`, `mypy --strict`, `pytest` — 196 tests passent, 1 skip (préexistant,
non lié à ce palier), 10 sous-tests. Smoke-test manuel de `cli.py new`/`status` avec les vrais
`adapter_id` `claude`/`codex` (aucun appel fournisseur : `new`/`status` ne sondent ni n'invoquent
jamais un adaptateur — seul `run`/`resume` le font).

**Choix pris pendant l'écriture, non couverts explicitement par la spécification :**

- `resume --answer` sur une `QUESTION` née en `FINAL_A` : traité comme `REVISION_A` (même besoin
  d'artefacts que `REVISION_A` — document courant + critique), par symétrie avec le cas `BLOQUE`.
  §2 ne tranchait que `PROPOSAL_A`, `REVISION_A` et `BLOQUE`. **Non testé explicitement, à vérifier
  si une vraie mission déclenche ce chemin.**
- `resume --answer` ne touche jamais au compteur `revision` — seule la phase change. Motif : la
  spécification ne mentionne aucun ajustement de compteur à la reprise.
- `collaboration_id` = nom du dossier `COLLAB` passé en argument. Aucun flag séparé n'est décrit en
  §7 ; le plus simple qui n'invente rien.
- `status` sans `--json` : une ligne `clé : valeur` par champ. Non spécifié en détail, coupable en
  premier si le budget l'exige (§11, point 1).
- Modèle par défaut de Codex : identique pour A et B (`gpt-5.6-sol`, mesuré). `CLAUDE.md` §6 ne fixe
  un rôle que pour Claude.

---

## Contraintes acquises — à ne pas redécouvrir

**`models.py`** — porte les neuf enums fermés ; 301 lignes pour 130 visées, ne pas y ajouter sans
motif. `Decision`, `Severity`, `Disposition` y restent (vocabulaire fermé unique).

**`storage.py` / `lock.py`** — sur Windows, **ne jamais utiliser `os.kill(pid, 0)`** : l'implémentation
y appelle `TerminateProcess`, y compris pour le signal `0`. Vivacité par `ctypes`/`OpenProcess`.

**`contracts.py`** — la normalisation CRLF→LF et l'acceptation du bloc JSON clôturé sont des
**tolérances**, pas des correctifs à un défaut observé : les deux CLI rendent du `\n` et du JSON nu.
Le brut reste intact sur le disque ; seule la copie est normalisée.

**`transport.py`** — `taskkill /F /T` sous Windows, `os.kill(-pid, 9)` sous POSIX (`SIGKILL` n'est pas
nommé : absent de Windows, il ferait échouer `mypy`). La **branche POSIX est écrite et non testée**
(§0.1). Le prompt passe par `stdin_text`, écrit dans un fil.

**`workflow.py`** — `_Engine` porte le contexte du cycle plutôt que douze signatures. **Aucun compteur
de garde sur la boucle** : `max_revisions` la borne, un compteur serait un quota interne. Les issues
non-`COMPLETED` du transport, **et un `return_code` non nul** (D-2), mènent à `INTERRUPTED`, jamais à
un rejeu ; `ERROR` est réservé à l'échec de contrat. Transition et `current_call = null` sont une
**seule** écriture atomique.

**`prompts.py`** — le schéma du JSON de revue est dans le prompt de B — sans lui, aucune revue ne
pouvait être conforme.

**`adapters/base.py` est publié.** §13 rendait le protocole réversible « jusqu'à sa publication » : ce
point est franchi, le modifier coûte désormais une migration. Porte `probe_version()` — utilitaire
partagé par `claude.py` et `codex.py`, best-effort : un exécutable trouvé par `shutil.which()` reste
`present` même si son bandeau `--version` échoue.

**`adapters/claude.py` / `adapters/codex.py`** — `command()` résout l'exécutable par `shutil.which()`
**à chaque appel**, jamais mis en cache : cohérent avec « aucune attestation persistée » (§8). Les
deux CLI sont réellement installées sur la machine de développement — voir la règle de test dans
`RULES.md`.

**`cli.py`** — `new` construit tout dans un dossier temporaire frère (`.new-<nom>-<uuid>`) et publie
par `Path.rename()` ; il refuse une destination existante **avant** de créer ce dossier temporaire.
`run`/`resume` partagent `_drive()`, seul point d'appel à `workflow.run`. Aucune commande `worker`,
`serve`, `implement`, `apply`, `watch`, `repair`.

---

## Budget — arbitré le 2026-09-04 : « on continue »

**Décision du PO, 2026-09-04.** Même arbitrage que le 2026-09-03 : la taille reflète une surface CLI
réellement spécifiée (§7, quatre commandes), pas une dérive. On committe tel quel. **Condition** :
rouvrir la question si la croissance se poursuit sur un prochain palier — ne pas la refermer en
silence (`RULES.md`, conduite de projet).

| Module | Visé (§11) | Réel (brut) | Écart |
|---|---:|---:|---:|
| `__init__` + `__main__` | 15 | 10 | — |
| `cli.py` | 155 | **273** | **+118** |
| `models.py` | 130 | 301 | +171 *(déjà arbitré 2026-09-03)* |
| `storage.py` | 140 | 76 | — |
| `lock.py` | 90 | 108 | +18 |
| `contracts.py` | 150 | 200 | +50 *(déjà arbitré 2026-09-03)* |
| `workflow.py` | 175 | 417 | +242 *(dont +14 pour D-2 ; le reste déjà arbitré)* |
| `prompts.py` | 95 | 135 | +40 |
| `transport.py` | 160 | 265 | +105 *(déjà arbitré 2026-09-03)* |
| `corpus.py` | 90 | 107 | +17 |
| paquet `adapters/` | 230 | 178 (75+50+53) | — |
| **Total production (12/12 modules)** | **~1 430** | **2 070** | **+640** |

*Chiffres bruts (lignes non vides comptées à part : `cli.py` 232/273, `workflow.py` 369/417,
`adapters/` 131/178) — mesurés le 2026-09-04, `wc -l`. Pas de recomptage « code effectif » complet
cette session : la mesure précédente (1 171 sur 1 651, ~71 %) donnerait, au même taux, environ
1 470 lignes de code effectif sur 2 070 — au-dessus de la bande 1 350–1 550 même sur ce chiffre-là,
contrairement à l'étape précédente où seul le brut la dépassait.*

**Tests** : 2 171 lignes sur les fichiers existants avant ce palier, plus `test_adapters.py` (132) et
`test_cli.py` (211) neufs, plus extensions de `test_workflow.py`/`test_recovery.py`/`fakes.py`.

**Jamais sacrifiés pour tenir un chiffre** (rappel §11, inchangé) : état strict · absence de rejeu
automatique · délai dur et terminaison d'arbre · `fsync` et publication atomique · artefact avant
transition · les quatre permutations · registre de constats · porte `QUESTION` · terminal non ambigu.

---

## État courant

- **Étapes 0 et 1 closes.** Spécification : `conception/CONCEPTION_FINALE.md`.
- **Étape 2 : les quatre paliers sont écrits.** `cli.py`/adaptateurs testés, verts. Reste l'arbitrage
  de budget ci-dessus avant de considérer l'étape close, puis les validations manuelles hors suite de
  §9 (déjà faites pour la caractérisation ; restent : déplacement réel d'une collaboration en usage,
  première mission conception et première mission recherche observées).
- **La relecture Codex palier par palier reste suspendue** — décision du PO, 2026-09-03.
- Récolte : `conception/INVENTAIRE.md` v3, 156 leçons. Cinq tours de structure conservés séparément.
- Le dépôt n'a **pas de remote** — décision reportée.

## Décisions actées

- **Recherche au périmètre, sans accès externe en V0.1.** Condition de réouverture : §12.1.
- **A et B sont chacun l'un ou l'autre outil** — les quatre permutations sont **mesurées** (réelles
  CLI) et **testées** (via `FakeAdapter`, `TestPermutations`).
- **Sept accrétions retirées** de la V2 par audit contre les objectifs fondateurs.
- **Huit remarques techniques de Codex, toutes retenues** (`DISPOSITION_TECHNIQUE_CODEX.md`).
- **D-1, D-2, D-3 tranchées le 2026-09-04** — voir « Palier 4 » ci-dessus et `CONCEPTION_FINALE.md`.
- Paramètres fixés : UTF-8 sans BOM · 8 MiB par flux · **Windows testé, POSIX écrit non testé**.

## Rappels actifs

- La mission DialogForge `e35cfcf1-47e5-4354-a4b1-d40235b8e3cf` est **en pause**, pas annulée. Elle
  redémarrerait seule si on la reprenait. Ne pas la relancer sans décision.
- Les quatre dossiers `C:\Projets\DialogForge*` sont en **lecture seule**. Point d'entrée du gel :
  `C:\Projets\DialogForge\ARRET_REFACTORING.md`.
- Reporté, tracé : la colonne **Code** de l'inventaire plus longue que **Prompt** — après la phase 2.

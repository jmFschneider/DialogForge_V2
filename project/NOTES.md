# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. Historique → `session_log.md`. Règles → `RULES.md`.
> Dernière mise à jour : 2026-09-04

---

## Prochaine action — une seule

**Première mission réelle, hors suite de tests.** Les quatre paliers sont écrits, testés, verts ;
plus rien ne bloque `python -m iabinome new/run` en conditions réelles. Reste de §9 : « première
mission conception et première mission recherche observées, avec la friction du manifeste notée. »
Lancer une mission de conception simple (`--agent-a claude --agent-b codex` ou l'inverse), observer
le cycle de bout en bout, noter toute friction — en particulier sur la liste de fichiers du manifeste
de corpus (§3 : « premier point d'usage à mesurer »). **Appel payant, autorisation du PO requise
avant de lancer.**

Après cette observation : décider si l'étape 2 est close, ou s'il y a un palier 5.

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
non-`COMPLETED` du transport, **et un `return_code` non nul (D-2)**, mènent à `INTERRUPTED`, jamais à
un rejeu ; `ERROR` est réservé à l'échec de contrat. Transition et `current_call = null` sont une
**seule** écriture atomique.

**`prompts.py`** — le schéma du JSON de revue est dans le prompt de B — sans lui, aucune revue ne
pouvait être conforme.

**`adapters/base.py` est publié.** §13 rendait le protocole réversible « jusqu'à sa publication » : ce
point est franchi, le modifier coûte désormais une migration. Porte `probe_version()` — utilitaire
partagé par `claude.py` et `codex.py`, best-effort : un exécutable trouvé par `shutil.which()` reste
`present` même si son bandeau `--version` échoue.

**`adapters/claude.py` / `adapters/codex.py`** — `command()` résout l'exécutable par `shutil.which()`
**à chaque appel**, jamais mis en cache (§8 : aucune attestation persistée). `CONSULT` est le défaut
(D-1) ; `CONTEXT_ONLY` fonctionne mécaniquement pour les deux (`--tools ""` / `-c
features.shell_tool=false`) mais reste partiel côté Codex — réserve non essayée, voir §12.3. Modèle
Codex par défaut identique pour A et B (`gpt-5.6-sol`) : `CLAUDE.md` §6 ne fixe un rôle que pour
Claude. **Les deux vraies CLI sont installées sur la machine de développement** — tout test doit
substituer `cli.ADAPTERS`, sans quoi il appelle un vrai fournisseur (`RULES.md`).

**`cli.py`** — `new` construit tout dans un dossier temporaire frère (`.new-<nom>-<uuid>`) et publie
par `Path.rename()` ; il refuse une destination existante **avant** de créer ce dossier temporaire.
`run`/`resume` partagent `_drive()`, seul point d'appel à `workflow.run`. Aucune commande `worker`,
`serve`, `implement`, `apply`, `watch`, `repair`. `resume --answer` sur une `QUESTION` née en
`FINAL_A` est traité comme `REVISION_A`, par symétrie avec `BLOQUE` (§2 ne tranchait que
`PROPOSAL_A`/`REVISION_A`/`BLOQUE`) — **non testé explicitement, à surveiller à la première mission
réelle**. `resume --answer` ne touche jamais au compteur `revision`. `collaboration_id` = nom du
dossier `COLLAB` passé en argument — aucun flag séparé n'est décrit en §7.

---

## Budget — arbitré le 2026-09-04 : « on continue », condition ouverte

**Décision du PO.** La taille reflète une surface CLI réellement spécifiée (§7), pas une dérive.
**Condition, non refermée** : rouvrir la question si la croissance se poursuit sur un prochain palier.

| Module | Visé (§11) | Réel (brut) |
|---|---:|---:|
| `cli.py` | 155 | **273** |
| `models.py` | 130 | 301 *(arbitré 2026-09-03)* |
| `workflow.py` | 175 | 417 *(arbitré 2026-09-03, +14 pour D-2)* |
| `contracts.py` | 150 | 200 *(arbitré 2026-09-03)* |
| `transport.py` | 160 | 265 *(arbitré 2026-09-03)* |
| paquet `adapters/` | 230 | 178 |
| **Total production (12/12 modules)** | **~1 430** | **2 070** |

*Mesuré le 2026-09-04, `wc -l`, brut. Pas de recomptage complet en « code effectif » cette session —
au taux mesuré la session précédente (~71 %), la bande 1 350–1 550 serait aussi dépassée, ce qui
n'était pas le cas avant ce palier.*

**Jamais sacrifiés pour tenir un chiffre** (§11) : état strict · absence de rejeu automatique · délai
dur et terminaison d'arbre · `fsync` et publication atomique · artefact avant transition · les quatre
permutations · registre de constats · porte `QUESTION` · terminal non ambigu.

---

## État courant

- **Étapes 0 et 1 closes.** Spécification : `conception/CONCEPTION_FINALE.md`.
- **Étape 2 : les quatre paliers sont écrits, testés, verts, committés (`61622a0`).** Reste la
  validation manuelle hors suite de §9 (« Prochaine action » ci-dessus) avant de déclarer l'étape close.
- **La relecture Codex palier par palier reste suspendue** — décision du PO, 2026-09-03.
- Récolte : `conception/INVENTAIRE.md` v3, 156 leçons. Cinq tours de structure conservés séparément.
- Le dépôt n'a **pas de remote** — décision reportée.

## Décisions actées

- **Recherche au périmètre, sans accès externe en V0.1.** Condition de réouverture : §12.1.
- **A et B sont chacun l'un ou l'autre outil** — les quatre permutations sont **mesurées** (réelles
  CLI) et **testées** (via `FakeAdapter`, `TestPermutations`).
- **Sept accrétions retirées** de la V2 par audit contre les objectifs fondateurs.
- **Huit remarques techniques de Codex, toutes retenues** (`DISPOSITION_TECHNIQUE_CODEX.md`).
- **D-1, D-2, D-3 tranchées le 2026-09-04** dans `CONCEPTION_FINALE.md` (§1, §5, §12.3).
- Paramètres fixés : UTF-8 sans BOM · 8 MiB par flux · **Windows testé, POSIX écrit non testé**.

## Rappels actifs

- La mission DialogForge `e35cfcf1-47e5-4354-a4b1-d40235b8e3cf` est **en pause**, pas annulée. Elle
  redémarrerait seule si on la reprenait. Ne pas la relancer sans décision.
- Les quatre dossiers `C:\Projets\DialogForge*` sont en **lecture seule**. Point d'entrée du gel :
  `C:\Projets\DialogForge\ARRET_REFACTORING.md`.
- Reporté, tracé : la colonne **Code** de l'inventaire plus longue que **Prompt** — après la phase 2.

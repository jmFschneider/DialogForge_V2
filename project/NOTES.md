# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. Historique → `session_log.md`. Règles → `RULES.md`.
> Dernière mise à jour : 2026-09-04

---

## Prochaine action — une seule

**Lot 11 : validations réelles et `GUIDE.md`. Bloqué sur une décision du PO — appels payants.**
Les **lots 1 à 10 sont faits** (`project/correctifs/2026-09-04-plan-correctif-audit-v2.md`), et les
onze constats de l'audit sont fermés sauf C-11. Rien d'autre n'est à coder.

Ce que le lot 11 demande, une fois l'autorisation donnée : déplacement d'une collaboration en cours
d'usage puis reprise · une mission de **conception** et une de **recherche**, dans deux permutations
différentes, **dans une collaboration jetable hors de tout dossier de valeur** (C-06 est ouvert) ·
re-caractérisation des versions installées (`2.1.260` / `0.153.2`) · consignation des versions, des
`invocation_args`, des commandes, des incidents, du coût et de la **friction du manifeste de corpus** ·
puis `GUIDE.md`, **une page, écrite après** — prescrire une commande qu'on n'a pas lancée est
justement ce que `RULES.md` interdit.

**Second point à soumettre : la taille, rouverte le 2026-09-04 et non tranchée.** Voir le budget
ci-dessous ; la question posée au PO est *qu'est-ce qu'on retire en échange ?*

**La première mission réelle est repoussée après les lots 1 à 4** (lot 5 en plus pour une mission de
recherche) — arbitré le 2026-09-04. Motif : l'audit Codex montre qu'un second `run` en `WAITING_HUMAN`
déclenche un **appel payant non demandé** et qu'un `resume` concurrent modifie la collaboration en
annonçant un échec. Observer maintenant mesurerait ces défauts, pas la friction cherchée.

---

## Contraintes acquises — à ne pas redécouvrir

**`models.py`** — porte les neuf enums fermés ; 301 lignes pour 130 visées, ne pas y ajouter sans
motif. `Decision`, `Severity`, `Disposition` y restent (vocabulaire fermé unique).

**`storage.py` / `lock.py`** — sur Windows, **ne jamais utiliser `os.kill(pid, 0)`** : l'implémentation
y appelle `TerminateProcess`, y compris pour le signal `0`. Vivacité par `ctypes`/`OpenProcess` — mais
un PID terminé y reste **vivant tant qu'un handle est ouvert** (`RULES.md`). Depuis le lot 1
(`373479d`) : acquisition par `O_CREAT | O_EXCL`, récupération d'un verrou mort **sous jeton exclusif**
`verrou.json.recuperation` (un candidat sans jeton ne touche jamais au verrou), libération vérifiée sur
le `lock_id`. Le verrou ne passe plus par `storage.write_atomic_text` — il crée, il ne remplace pas.

**`contracts.py`** — la normalisation CRLF→LF et l'acceptation du bloc JSON clôturé sont des
**tolérances**, pas des correctifs à un défaut observé : les deux CLI rendent du `\n` et du JSON nu.
Le brut reste intact sur le disque ; seule la copie est normalisée. `Normalized.transformations` et
`had_bom` existent mais **ne sont consignés nulle part** (D-8b) — le diagnostic se refait en comparant
`reponse_brute.txt` à la forme canonique. `Review.to_dict()` est cette forme canonique : c'est elle
qui va dans `echanges/`, jamais le texte de B, qu'un bloc clôturé rendait illisible par `json.loads`.

**`transport.py`** — `taskkill /F /T` sous Windows, `os.kill(-pid, 9)` sous POSIX (`SIGKILL` n'est pas
nommé : absent de Windows, il ferait échouer `mypy`). La **branche POSIX est écrite et non testée**
(§0.1). Le prompt passe par `stdin_text`, écrit dans un fil. Depuis le lot 7 : nettoyage borné par
**deux échéances communes** (`CLEANUP_LIMIT_SECONDS` = 12 s), issue `STREAMS_UNCLOSED` si un flux reste
ouvert, et **les descripteurs ne sont pas fermés sous un lecteur vivant**. Conséquence assumée : sous
Windows, un descendant survivant garde `stdout.txt` ouvert et le dossier ne peut pas être effacé avant
sa fin — un test doit alors utiliser `TemporaryDirectory(ignore_cleanup_errors=True)`.

**`workflow.py`** — `_Engine` porte le contexte du cycle plutôt que douze signatures. **Aucun compteur
de garde sur la boucle** : `max_revisions` la borne, un compteur serait un quota interne. Les issues
non-`COMPLETED` du transport, **et un `return_code` non nul (D-2)**, mènent à `INTERRUPTED`, jamais à
un rejeu ; `ERROR` est réservé à l'échec de contrat. Transition et `current_call = null` sont une
**seule** écriture atomique. Depuis le lot 2 : ordre imposé **sous verrou** — relecture, puis
`intervene`, puis `gate`, puis dispatch. La **porte d'état** n'accepte que `READY` sans appel courant
et `RUNNING` avec appel courant ; `ERROR` n'en sort que par la **table fermée** `_RELAUNCHABLE`
(`CONTRACT_ERROR`, `DECODE_FAILED` — ce dernier naîtra au lot 8). `command()` est résolu **avant** la
publication de `CALLING`. L'intervention (`Answer` / `RetryCall`) est un paramètre du moteur, plus une
mutation de `cli.py`.

**Rejouabilité de `--answer`** — ordre archive **par copie** → `demande.md` → `etat.json`. Deux pièces
que rien n'annonce dans le code : `_check_demande` **tolère** que `demande.md` porte déjà l'empreinte
de la réponse (sans quoi la reprise est refusée avant d'avoir pu réparer), et `_archive` **ne recopie
pas** si la dernière archive porte déjà ce texte (sans quoi le rejeu empile `.002`). Le rejeu après la
**troisième** écriture est un refus explicite : l'intervention est déjà appliquée, `resume` seul
enchaîne.

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
`serve`, `implement`, `apply`, `watch`, `repair`. Depuis le lot 2, **`cli.py` ne lit ni n'écrit plus
aucun état** : `cmd_resume` valide ses arguments et transmet. `_RESUME_PHASE` est passé dans
`workflow.py` — `resume --answer` sur une `QUESTION` née en `FINAL_A` y reste traité comme
`REVISION_A`, par symétrie avec `BLOQUE` (§2 ne tranchait que `PROPOSAL_A`/`REVISION_A`/`BLOQUE`) —
**non testé explicitement, à surveiller à la première mission réelle**. `resume --answer` ne touche
jamais au compteur `revision`. `collaboration_id` = nom du dossier `COLLAB` passé en argument — aucun
flag séparé n'est décrit en §7.

**Tests** — `tests/fakes.py` porte **deux** points d'observation, et ils prouvent deux choses
différentes : `FakeAdapter.observed_status` y voit `READY` (donc `command()` est résolu avant toute
mutation), et `status_marker` fait relire `etat.json` **par le processus lancé**, qui y voit `RUNNING`
(donc `CALLING` précède `Popen`). Ne pas fusionner les deux.

---

## Budget — **tranché le 2026-09-04 : rien n'est retiré. Question close.**

**Décision du PO, mot pour mot : « rien tout simplement. Le nombre de lignes est encore tout à fait
raisonnable. »** La condition rouverte le matin est donc **refermée**, et cette fois sans condition de
réouverture : le chiffre final est mesuré, plus projeté, et il est accepté tel quel. Ne pas rouvrir ce
débat sans un fait nouveau — une croissance venant d'ailleurs que des garanties déjà annoncées.

Pour mémoire, la projection validée le matin (~2 275 brutes) était fausse : le total est **2 659**, et
les estimations lot par lot étaient basses d'un facteur 2 à 5 (+205 estimées, **+589 mesurées**).

| Module | Visé (§11) | Brut | Code effectif |
|---|---:|---:|---:|
| `workflow.py` | 175 | **674** | 485 |
| `models.py` | 130 | 323 | 235 |
| `transport.py` | 160 | 313 | 225 |
| `cli.py` | 155 | 260 | 203 |
| `contracts.py` | 150 | 232 | 152 |
| `lock.py` | — | 181 | 120 |
| `corpus.py` | — | 152 | 116 |
| paquet `adapters/` | 230 | 178 | 99 |
| **Total production (12/12)** | **~1 430** | **2 659** | **1 793** |

*Mesuré le 2026-09-04, lots 1 à 10 fermés. « Code effectif » = hors blanches, commentaires et
docstrings (`ast` + `tokenize`). Ratio 67 %.*

**Motif retenu :** contre les ~1 500 de `POURQUOI.md`, la mesure comparable est **1 793, soit +20 %** —
et non +77 % comme le brut le laisse croire. Les deux tiers de l'écart brut sont de la documentation :
ce code porte le motif de chaque garantie, par choix, et c'est ce qui a permis de dérouler dix lots
sans relire le plan en entier. Aucun des cinq interdits n'a été touché.

**Jamais sacrifiés pour tenir un chiffre** (§11) : état strict · absence de rejeu automatique · délai
dur et terminaison d'arbre · `fsync` et publication atomique · artefact avant transition · les quatre
permutations · registre de constats · porte `QUESTION` · terminal non ambigu.

---

## État courant

- **Étapes 0 et 1 closes.** Spécification : `conception/CONCEPTION_FINALE.md`.
- **Étape 2 : les quatre paliers écrits, plus les dix lots correctifs de l'audit Codex.** **Lots 1 à
  10 faits** — C-01 à C-10, N-01, N-02, D-4 à D-8 fermés. **C-11 seul reste ouvert** : il exige des
  appels payants. Suite : **255 tests verts** + 2 ignorés (liens symboliques, privilège absent sur
  cette machine), `ruff` et `mypy --strict` verts.
- **Chaque correctif a été prouvé capable de voir son défaut** par neutralisation, un par un — tableau
  complet dans le plan, §4. C'est la garantie que la suite n'est pas verte pour la mauvaise raison.
- **Codes de sortie (D-5, tranché le 2026-09-04, appliqué au lot 3)** : `0` AWAITING_APPROVAL · `1`
  refus avant mutation · `2` réservé à argparse · `3` INTERRUPTED · `4` ERROR · `5` WAITING_HUMAN.
  Décision du PO **contre l'avis de Codex**, qui recommandait `0` pour WAITING_HUMAN.
- **C-06 (frontière d'effets) est un risque accepté, pas un défaut à corriger** : les agents ne sont
  pas mécaniquement confinés. Tant qu'il est ouvert, toute mission réelle se fait dans une
  collaboration jetable, hors de tout dossier de valeur.
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

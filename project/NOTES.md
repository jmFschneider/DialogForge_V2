# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. Historique → `session_log.md`. Règles → `RULES.md`.
> Dernière mise à jour : 2026-09-03

---

## Prochaine action — une seule

**Relever les cinq points de `CONCEPTION_FINALE.md` §12.2 — la caractérisation des deux CLI.**

**Aucune CLI n'a jamais été lancée.** C'est une manipulation humaine, hors suite de tests, un appel
jetable par adaptateur. Le **point 2 — réalité du mode sans outils — décide B-2** à lui seul, donc la
validation de `--reviewer-access` et la forme des adaptateurs. **Elle bloque le palier 3.**

Le point 5 — délai et terminaison d'arbre sous Windows — est désormais **couvert par un test
automatisé** (`test_transport.py`, `TestProcessTree`) : il reste à observer le comportement d'une vraie
CLI d'agent, pas celui du mécanisme.

### Budget — arbitré le 2026-09-03 : on continue

| | Lignes |
|---|---:|
| Production écrite (6 modules sur 11) | **1 002** |
| Budget §11 de ces 6 modules | 760 |
| Écart | **+242 (+32 %)** |
| Budget §11 du reste (`workflow` `cli` `prompts` `adapters` `__init__`+`__main__`) | 670 |
| **Projection si le reste tient son budget** | **1 672** |
| Bande acceptable §11 | 1 350 – 1 550 |

**La bande n'est pas dépassée aujourd'hui — la projection, si. Le PO a arbitré le 2026-09-03 : on
continue.** La règle de coupe §11 ne s'ouvre donc toujours qu'au dépassement **réel** de 1 550, et la
garde de fond reste `POURQUOI` règle 1 — l'outil ne dépasse jamais le projet qu'il sert (FloraPi,
58 894 lignes).

**Point de mesure conservé : la clôture du palier 3.** Si `workflow.py` dépasse 175 lignes, appliquer
les coupes §11 dans l'ordre (1. sorties de confort dont `status --json` · 2. abstractions à un seul
appelant · 3. détection lexicale · 4. métadonnées d'origine facultatives · 5. arbitrage).

### Palier 1 — les cinq modules purs — CLOS le 2026-09-03

**94 tests, 0 échec** (1 ignoré : lien symbolique non privilégié sur la machine de développement —
attendu). `models.py` 301 · `storage.py` 76 · `lock.py` 108 · `contracts.py` 172 · `corpus.py` 107.

**Décisions de conception prises pendant l'implémentation, absentes du texte de la spécification :**
- `last_incident` (`etat.json`) : chemin relatif explicite, pas un objet structuré.
- `contracts.normalize()` n'implémente que le retrait de BOM + empreinte SHA-256 — seule
  transformation nommée par §0.1. Pas de normalisation CRLF→LF : à statuer lors de la
  caractérisation §12.2 si un besoin réel apparaît (branche repérable, réversible).
- `lock.py` sur Windows : **ne jamais utiliser `os.kill(pid, 0)`** — l'implémentation Windows appelle
  `TerminateProcess`, y compris pour le signal `0`. Vivacité testée via `ctypes`/`OpenProcess`.
- `Decision` reste dans `models.py` : `workflow.py` en aura besoin aussi.

### Palier 2 — `fakes.py` + `transport.py` — CLOS le 2026-09-03

**118 tests, 0 échec** (24 nouveaux, 7,7 s). `transport.py` **238 lignes** pour 160 visées ·
`tests/fakes.py` 61 · `tests/test_transport.py` 261. `ruff` et `mypy --strict` verts.

**Décisions de conception prises pendant l'implémentation, absentes du texte de la spécification :**

- **Le faux agent est un vrai sous-processus, pas un `FakeProcess`.** §10 nommait `FakeProcess` et
  `FakeClock` ; ni l'un ni l'autre n'est écrit. Ce que `transport.py` doit tenir est **le comportement
  de l'OS** — deux tubes concurrents, délai, terminaison d'arbre —, et un objet simulé ne le
  prouverait pas. `tests/fakes.py` script donc un vrai `python -c`. **Aucun appel fournisseur, aucun
  réseau** : la règle est tenue, c'est le moyen qui change.
- **`FakeAdapter` n'arrive qu'au palier 4**, avec `adapters/base.py` : le protocole qu'il doit
  implémenter n'existe pas encore.
- **`Outcome` vit dans `transport.py`, pas dans `models.py`.** Ce n'est pas un des neuf enums fermés de
  la spécification ; c'est le vocabulaire de l'incident (`OUTPUT_LIMIT`, `TIMEOUT`,
  `INTERRUPTED_BY_USER`), et `models.py` dépasse déjà largement son budget.
- **`read_result()` est dans `transport.py`** — ~35 des 238 lignes. La table de reprise §5 relève de
  `workflow.py`, mais le lecteur et l'écrivain d'un format vont ensemble, et c'est ce qui rend la
  règle « `resultat.json` valide = flux complets » testable seule. **Le budget de 160 lignes ne
  comptait vraisemblablement pas ce lecteur : le dépassement propre au transport est d'environ 45
  lignes, pas 78.**
- **Terminaison d'arbre : `taskkill /F /T /PID` sous Windows, `os.kill(-pid, 9)` sous POSIX** (le PID
  négatif désigne le groupe, qui vaut le PID de l'enfant grâce à `start_new_session`). `SIGKILL` n'est
  **pas** nommé : `signal.SIGKILL` est absent de Windows et ferait échouer `mypy` sur le poste.
- **Un descendant qui tient encore les tubes après la sortie de l'enfant déclenche une terminaison
  d'arbre supplémentaire.** Sans elle, `resultat.json` affirmerait « flux complets » sur des fichiers
  qui grossissent encore — exactement ce que §10 interdit. **Cette branche n'est couverte par aucun
  test** : la déclencher demanderait de rendre le délai de grâce configurable, donc une option de
  plus.
- **La branche POSIX est écrite et non testée**, conformément à §0.1. Le poste est Windows.

### Paliers suivants

**3.** `workflow.py` — protocole d'appel en 9 étapes, transitions, **table de reprise** (§5).
*Modèle recommandé : **Opus**, pas Sonnet — c'est le second endroit où la spécification s'arrête à la
frontière de l'OS et où le test ne rattrape pas une erreur.*
**4.** `prompts.py` · `adapters/` (après caractérisation) · `cli.py`.

**La relecture Codex palier par palier est suspendue** — décision du PO le 2026-09-03 : la conception
a déjà été contredite cinq tours, sa précision rend la relecture de code peu rentable. Aucun palier
n'est donc en attente. **La règle reste valable pour la conception** (`RULES.md`). Réouverture si un
palier révèle un défaut que la relecture aurait attrapé.

---

## État courant

- **Étapes 0 et 1 closes.** La spécification est `conception/CONCEPTION_FINALE.md`.
- **Étape 2 : paliers 1 et 2 clos.** 1 002 lignes de production, 1 107 de tests, **118 tests verts**.
- Cinq tours conservés séparément, aucun écrasé : `STRUCTURE_PROPOSEE_CODEX.md` →
  `CRITIQUE_CLAUDE_STRUCTURE_CODEX.md` → `STRUCTURE_PROPOSEE_CLAUDE.md` →
  `STRUCTURE_PROPOSEE_CODEX_V2.md` → `CONCEPTION_FINALE.md` (+ `ANALYSE_VERS_CONCEPTION_FINALE.md`),
  puis `DISPOSITION_TECHNIQUE_CODEX.md`.
- Récolte : `conception/INVENTAIRE.md` v3, **156 leçons** — 43 Code · 34 Prompt · 33 Règle · 23 Test · 23 Écarté.
- Le dépôt n'a **pas de remote** — décision reportée.
- Prédécesseur : DialogForge, refactoring **gelé** le 2026-09-02, toujours utilisé en conception seule sur FloraPi.

## Décisions actées

- **Recherche au périmètre**, mais **sans accès externe en V0.1** — le corpus est ce que l'humain dépose. Condition de réouverture dans `CONCEPTION_FINALE.md` §12.1.
- **A et B sont chacun Claude ou Codex**, décidé au lancement. Quatre permutations testées. Le cycle ne dépend que des capacités communes.
- **Plafond de ~200 lignes de l'inventaire levé** ; la garde reste `POURQUOI` règle 1.
- **Sept accrétions retirées** de la V2 par audit contre les objectifs fondateurs — dont l'appareil d'approbation et le mode de recherche externe.
- **Huit remarques techniques de Codex, toutes retenues** (`DISPOSITION_TECHNIQUE_CODEX.md`).
- Paramètres fixés : UTF-8 sans BOM · 8 MiB par flux · **Windows testé, POSIX écrit non testé**.

## Blocages

- **B-2 non arbitré** : `CONSULT` recommandé ; `CONTEXT_ONLY` est incompatible avec Codex-en-B tant
  qu'une invocation sans outils n'est pas démontrée. **Tranché par la caractérisation §12.2.**
- **Aucune CLI lancée** — §12.2. **Bloque le palier 3.**

## Rappels actifs

- La mission DialogForge `e35cfcf1-47e5-4354-a4b1-d40235b8e3cf` est **en pause**, pas annulée. Elle redémarrerait seule si on la reprenait. Ne pas la relancer sans décision.
- Les quatre dossiers `C:\Projets\DialogForge*` sont en **lecture seule**. Point d'entrée du gel : `C:\Projets\DialogForge\ARRET_REFACTORING.md`.
- Reporté, tracé : la colonne **Code** plus longue que **Prompt** — après la phase 2.

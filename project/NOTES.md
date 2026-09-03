# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. Historique → `session_log.md`. Règles → `RULES.md`.
> Dernière mise à jour : 2026-09-03

---

## Prochaine action — une seule

**Ouvrir le palier 2 : `fakes.py` + `transport.py`.**

La spécification est `conception/CONCEPTION_FINALE.md`. **Le découpage en paliers est de `NOTES.md`,
pas de la spécification elle-même** — `CONCEPTION_FINALE.md` liste les modules (§3, §11) sans les
ordonner ; c'est ce fichier qui fixe l'ordre et le motif.

*C'est le module signalé comme le plus susceptible de déborder son budget : terminaison d'arbre de
processus, deux flux concurrents bornés à 8 MiB, délai dur, branche POSIX non testable ici. Modèle
recommandé pour ce palier et le palier 3 (`workflow.py`) : **Opus**, pas Sonnet — cf. session du
2026-09-03, ce sont les deux endroits où la spécification s'arrête à la frontière de l'OS et où le
test ne rattrape pas une erreur.*

### Palier 1 — les cinq modules purs — CLOS le 2026-09-03

Codé, testé, sans arbitrage humain formel préalable sur `CONCEPTION_FINALE.md` — la session a
enchaîné directement sur validation implicite du PO (`/loop` non utilisé, confirmation ligne par
ligne). **94 tests, 0 échec** (1 ignoré : création de lien symbolique non privilégiée sur la machine
de développement — attendu, pas un défaut). `ruff check .` et `mypy --strict` verts.

| Module | Lignes visées | Lignes réelles | Tests |
|---|---:|---:|---|
| `models.py` | 130 | **301** | `test_state.py` — 25 |
| `storage.py` | 140 | 76 | `test_storage.py` — 13 |
| `lock.py` | 90 | 108 | `test_lock.py` — 9 |
| `contracts.py` | 150 | 172 | `test_contracts.py` — 33 |
| `corpus.py` | 90 | 107 | `test_corpus.py` — 14 |
| **Sous-total** | **600** | **764** | **94** |

**`models.py` dépasse largement (301 vs 130).** Motif tracé dans la session : il porte les neuf enums
fermés de tout le système (dont `Decision`, dont `workflow.py` aura aussi besoin) plus la machinerie de
validation stricte générique (`_decode`/`_encode`), déjà factorisée une fois pour éviter 314 lignes en
répétition brute. `storage.py` sous son budget (76) compense en partie. **À surveiller** : reste
~655 lignes visées pour `cli.py`, `prompts.py`, `transport.py`, `adapters/`, `__init__`+`__main__` —
la bande totale (1350–1550) tient si ces modules restent proches de leur budget, mais l'écart ne se
recreuse plus sans arbitrage — §11, règle de coupe.

**Décisions de conception prises pendant l'implémentation, absentes du texte de la spécification :**
- `last_incident` (`etat.json`) : chemin relatif explicite (comme `current_document`/`latest_review`),
  pas un objet structuré — la spécification ne détaille pas sa forme.
- `contracts.normalize()` n'implémente que le retrait de BOM + empreinte SHA-256 comme
  « normalisation déterministe » — c'est la seule transformation nommée par `CONCEPTION_FINALE.md`
  §0.1. Pas de normalisation CRLF→LF : non spécifiée, à statuer lors de la caractérisation CLI §12.2
  si un besoin réel apparaît (branche déjà repérable, réversible).
- `lock.py` sur Windows : **ne jamais utiliser `os.kill(pid, 0)`** — l'implémentation Windows de
  `os.kill` appelle `TerminateProcess`, y compris pour le signal `0`. Vivacité testée via
  `ctypes`/`OpenProcess`.
- `Decision` reste dans `models.py` (pas `contracts.py`) : `workflow.py` en aura besoin aussi pour
  piloter les transitions — `Severity`/`Disposition` restent, eux, dans `models.py` également par
  cohérence (un seul fichier de vocabulaire fermé).

Avant le premier commit de code : `pyproject.toml` **sans aucune dépendance d'exécution**, `src/iabinome/`, `tests/`. **Fait.**

**Porte à chaque commit — `CLAUDE.md` §5 :** `ruff check .` et `mypy` verts, **aucun appel fournisseur
dans la suite**. **Vérifié à chaque module de ce palier.**

### En parallèle, et avant le palier 3 — la caractérisation des CLI

**Aucune CLI n'a jamais été lancée.** Les cinq points de `CONCEPTION_FINALE.md` §12.2 doivent être
relevés à la main, hors suite de tests. **Le point 2 — réalité du mode sans outils — décide B-2**, donc
la validation de `--reviewer-access` et la forme des adaptateurs.

### Paliers suivants

**2.** `fakes.py` + `transport.py` — sous-processus, délai dur, terminaison d'arbre, flux bornés à
8 MiB, `pid.txt`. *C'est le module le plus susceptible de déborder son budget.*
**3.** `workflow.py` — protocole d'appel en 9 étapes, transitions, **table de reprise** (§5).
**4.** `prompts.py` · `adapters/` (après caractérisation) · `cli.py`.

---

## État courant

- **Étapes 0 et 1 closes.** La spécification est `conception/CONCEPTION_FINALE.md` — **~1 430 lignes**
  de production visées, bande 1 350–1 550 ; tests 1 100–1 800, non normatif.
- **Étape 2 commencée : palier 1 clos** (voir ci-dessus). 764 lignes de production, 785 de tests, 94
  tests verts. Reste les paliers 2 à 4.
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
  qu'une invocation sans outils n'est pas démontrée. **Ne bloque pas le palier 1.**
- **Aucune CLI lancée** — `CONCEPTION_FINALE.md` §12.2. **Ne bloque pas le palier 1**, bloque le palier 3.

## Rappels actifs

- La mission DialogForge `e35cfcf1-47e5-4354-a4b1-d40235b8e3cf` est **en pause**, pas annulée. Elle redémarrerait seule si on la reprenait. Ne pas la relancer sans décision.
- Les quatre dossiers `C:\Projets\DialogForge*` sont en **lecture seule**. Point d'entrée du gel : `C:\Projets\DialogForge\ARRET_REFACTORING.md`.
- Reporté, tracé : la colonne **Code** plus longue que **Prompt** — après la phase 2.

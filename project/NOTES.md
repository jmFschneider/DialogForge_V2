# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. Historique → `session_log.md`. Règles → `RULES.md`.
> Dernière mise à jour : 2026-09-03

---

## Prochaine action — une seule

**Ouvrir l'étape 2 : écrire le premier palier de code.**

La spécification est `conception/CONCEPTION_FINALE.md`. Elle est révisée, ses huit derniers défauts
techniques sont corrigés. **Elle n'a pas encore reçu l'arbitrage humain formel** — si le PO la valide
en ouvrant la session, le noter ici et démarrer.

### Palier 1 — les cinq modules purs, ~600 lignes

Ils ne dépendent d'**aucune** caractérisation de CLI. C'est ce qui les rend premiers.

| Ordre | Module | Contenu | Tests |
|---|---|---|---|
| 1 | `models.py` | Enums fermés, configuration et état, **validation stricte de schéma** — version future, enum inconnu, clé absente ou surnuméraire → refus | `test_state.py` |
| 2 | `storage.py` | Temporaire unique → `flush` → `fsync` → `os.replace` ; `fsync` de dossier POSIX ; nouvelle tentative Windows ; **UTF-8 sans BOM, `\n`** | `test_storage.py` |
| 3 | `lock.py` | Verrou avec PID, date UTC, commande · détenteur vivant refusé · verrou mort récupéré · **jamais supprimer celui d'un autre** | `test_lock.py` |
| 4 | `contracts.py` | Discriminateur `IABINOME:DOCUMENT` / `QUESTION` · schéma de revue v1 · bloc JSON unique clôturé · normalisation déterministe + empreintes | `test_contracts.py` |
| 5 | `corpus.py` | Manifeste, copie, règles de chemin (absolu, `..`, lien sortant, non régulier, empreinte changeante → refus **avant publication**) | `test_corpus.py` |

Avant le premier commit de code : `pyproject.toml` **sans aucune dépendance d'exécution**, `src/iabinome/`, `tests/`.

**Porte à chaque commit — `CLAUDE.md` §5 :** `ruff check .` et `mypy` verts, **aucun appel fournisseur
dans la suite**.

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
- **Aucune ligne de code écrite.** Le dépôt ne contient que des documents.
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

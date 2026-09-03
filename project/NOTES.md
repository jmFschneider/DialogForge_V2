# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. Historique → `session_log.md`. Règles → `RULES.md`.
> Dernière mise à jour : 2026-09-03

---

## Prochaine action — une seule

**Arbitrer `conception/CONCEPTION_FINALE.md`, avant toute ligne de code.**

C'est la synthèse de tout le cycle. Raisonnement dans `ANALYSE_VERS_CONCEPTION_FINALE.md`, qui audite
la V2 de Codex contre les neuf objectifs fondateurs — Codex n'ayant pas participé à l'échange initial.

**Trois points à trancher, dans cet ordre :**

| | Point | Position du document |
|---|---|---|
| 1 | **Sources externes en recherche** | **Écartées de V0.1.** Les deux échecs mesurés venaient du mandat, pas de l'accès ; et aucune capacité commune aux deux CLI n'est démontrée. Le corpus reste ce que l'humain y dépose. Condition de réouverture nommée. |
| 2 | **B-2 — contrat de B** | `CONSULT` recommandé. `CONTEXT_ONLY` est incompatible avec Codex-en-B tant qu'une invocation sans outils n'est pas démontrée. `--reviewer-access` reste obligatoire et sans défaut. |
| 3 | **Deux coupes qui sont des jugements** | L'appareil d'approbation (`APPROVED`/`REJECTED`/`decision_humaine.json`) et le mode de recherche externe ont été retirés. Les deux sont argumentés et réversibles sans migration. |

Puis : **caractériser les deux CLI** (§12.2) — aucune n'a jamais été lancée. Puis l'implémentation.

Toujours reporté, tracé : la colonne **Code** plus longue que **Prompt** (après la phase 2).

---

## État courant

- **Étape 1 : `conception/CONCEPTION_FINALE.md` est prête à arbitrer.** Quatre tours conservés
  séparément, aucun écrasé : `STRUCTURE_PROPOSEE_CODEX.md` (A) → `CRITIQUE_CLAUDE_STRUCTURE_CODEX.md`
  (B, `REVISER`, 11 constats) → `STRUCTURE_PROPOSEE_CLAUDE.md` (A') → `STRUCTURE_PROPOSEE_CODEX_V2.md`
  (B') → **`CONCEPTION_FINALE.md`**, avec `ANALYSE_VERS_CONCEPTION_FINALE.md` à côté.
- Charpente : **noyau neuf** (pas d'élagage de DialogForge) · **~1 430 lignes** de production, bande
  1 350–1 550 · tests 1 100–1 800, non normatif · 14 modules · 4 commandes CLI · dossier de
  collaboration autonome et déplaçable.
- **Sept accrétions retirées** de la V2 par audit contre les objectifs fondateurs : ~125 lignes et
  **six concepts** — dont l'appareil d'approbation (6 concepts pour zéro conséquence mécanique) et le
  mode de recherche externe (un mode indisponible, contraire à `POURQUOI` règle 3).
- **Étape 0 close.** `conception/INVENTAIRE.md` v3 : **156 leçons** — 43 Code · 34 Prompt · 33 Règle · 23 Test · 23 Écarté.
- Relecture Codex en deux passes, 42 observations, **toutes disposées** : 28 acceptées, 6 rejetées, 5 différées, 3 bloquantes. Détail dans `conception/DISPOSITION_RELECTURE.md`.
- Les huit sources de `RECOLTE.md` sont dépouillées. `history.md` et `README.md` volontairement non ouverts — **Codex ne l'a pas contesté.**
- **Contrainte structurante ajoutée par le PO :** A et B sont chacun Claude ou Codex, décidé au lancement. Portée dans `CLAUDE.md` §1 et §6, `DEPART.md`, `RULES.md`, et `C15a`–`C15e` / `T21`–`T23` / `R32`–`R33`.
- **Aucune ligne de code écrite.** Le dépôt ne contient que des documents de cadrage.
- Enchaînement : récolte (**relecture en cours**) → spécification (`DEPART.md`) → implémentation, avec arbitrage humain entre chaque.
- Le dépôt n'a **pas de remote** — décision reportée, à faire plus tard.
- Prédécesseur : DialogForge, refactoring **gelé** le 2026-09-02. Toujours utilisé **en conception seule** sur FloraPi.

## Décisions actées le 2026-09-03

- **B-1 — la recherche est au périmètre.** `CLAUDE.md`, `DEPART.md` amendés ; les 10 lignes conditionnelles sont fermes.
- **B-3 — le plafond de ~200 lignes est levé.** Posé arbitrairement, faux depuis que le périmètre a grandi. La garde qui reste est `POURQUOI` règle 1 — une mesure, pas un chiffre. Tracé dans `RECOLTE.md`.
- **B-2 — reporté au troisième tour.** La permutation rôle/outil a invalidé la recommandation « B sans outil ».
- **Périmètre de la récolte** : tranché par Claude — l'inventaire couvre *aussi* la conduite de projet. Trace dans `RECOLTE.md`. Rouvrable.
- Les trois décisions de l'étape 1 (fin de `INVENTAIRE.md`) : cadrage automatique, plancher de `contracts.py`, format d'`etat.json`.

## Rappels actifs

- La mission DialogForge `e35cfcf1-47e5-4354-a4b1-d40235b8e3cf` est **en pause**, pas annulée. Elle redémarrerait seule si on la reprenait (`dialogforge resume`). Ne pas la relancer sans décision.
- Les quatre dossiers `C:\Projets\DialogForge*` et `C:\Projets\IAbinome` se référencent mutuellement. Point d'entrée du gel : `C:\Projets\DialogForge\ARRET_REFACTORING.md`.

## Limite de preuve — partiellement levée

Codex a lu les 4 931 lignes et **trouvé cinq erreurs dans la colonne Code** : `C1` (défaut 3 et non 2)
· `C3` (atomicité ≠ durabilité, aucun `fsync`) · `C24` (DialogForge ne segmente ni ne tronque : il
accumule sans plafond) · `C19` (formule exacte mais inutile sans budgets) · `C37` (chemin absolu
persisté). Toutes du même genre : **j'avais écrit comme observation ce qui était une décision ou un
correctif.** Détail dans `conception/CRITIQUE_CLAUDE_STRUCTURE_CODEX.md`.

**Reste non caractérisé : aucune CLI n'a jamais été lancée.** `--tools ""`, les sandbox Codex et les
identifiants exacts d'Opus 5 / Fable 5 sont déduits du code, pas mesurés. À faire au premier prévol réel.

## Blocages

- **B-2 reste à arbitrer** : `CONTEXT_ONLY` est incompatible avec Codex-en-B tant qu'une invocation sans
  outils n'est pas démontrée ; `CONSULT` est une recommandation, pas une décision.
- **Aucune CLI n'a jamais été lancée.** Les cinq points de `CONCEPTION_FINALE.md` §12.2 doivent être
  mesurés avant de figer la spécification — le point 2 (réalité du mode sans outils) décide B-2.

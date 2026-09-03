# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. Historique → `session_log.md`. Règles → `RULES.md`.
> Dernière mise à jour : 2026-09-03

---

## Prochaine action — une seule

**Arbitrer la question bloquante `B-1bis` : la recherche V0.1 est-elle corpus-only ?**

Codex a restreint « recherche » à « recherche dans un corpus fourni ». Or B-1 a été arbitré « oui » sur
la base des missions bibliographiques de FloraPi, qui interrogeaient des **sources externes**. La
restriction rend `P26`, `P27`, `P30`, `P33`, `P34` largement inertes.

*Recommandation : corpus-only pour V0.1, et l'écrire dans `CLAUDE.md`* — les deux échecs mesurés
venaient du mandat, pas de l'accès aux sources. Le Web reste un contrat distinct.

Ensuite : arbitrage sur les deux propositions de structure, puis **l'implémentation**.
Aucune ligne de code avant.

Toujours reportés, tracés : **B-2** le contrat de B (troisième tour) · la colonne **Code** plus longue
que **Prompt** (après la phase 2).

---

## État courant

- **Étape 1 en cours — deux propositions de structure sur la table**, à arbitrer :
  `conception/STRUCTURE_PROPOSEE_CODEX.md` (A) et `conception/STRUCTURE_PROPOSEE_CLAUDE.md` (B, révision).
  Critique intermédiaire : `CRITIQUE_CLAUDE_STRUCTURE_CODEX.md` — décision `REVISER`, 11 constats.
- Charpente commune aux deux : **noyau neuf** (pas d'élagage de DialogForge), ~1 540 lignes de production
  **+ 2 300–3 000 de tests**, 14 modules, 4 commandes CLI, dossier de collaboration autonome et déplaçable.
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

Aucun.

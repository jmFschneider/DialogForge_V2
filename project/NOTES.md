# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. Historique → `session_log.md`. Règles → `RULES.md`.
> Dernière mise à jour : 2026-09-03

---

## Prochaine action — une seule

**L'étape 0 est close.** Ouvrir l'étape 1 : la spécification de `DEPART.md`, qui ne prend en entrée
que la colonne **Code** de `conception/INVENTAIRE.md` — **43 lignes**.

Deux points à traiter dans la spécification, pas avant :

- **B-2, le contrat de B** — « aucun outil » est intenable depuis que B peut être Codex. Les trois termes à trancher sont posés en fin d'`INVENTAIRE.md`. *Reporté au troisième tour par le PO.*
- La colonne **Code** plus longue que **Prompt** — *reporté après la phase 2.*

---

## État courant

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

## Blocages

Aucun.

# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. Historique → `session_log.md`. Règles → `RULES.md`.
> Dernière mise à jour : 2026-09-03

---

## Prochaine action — une seule

**Trancher les trois questions bloquantes de `conception/DISPOSITION_RELECTURE.md`.** Rien d'autre
ne peut avancer avant.

| | Question | Recommandation |
|---|---|---|
| **B-1** | « Recherche » entre-t-il officiellement au périmètre ? `CLAUDE.md` et `DEPART.md` ne parlent que de conception ; 10 lignes de l'inventaire en dépendent. | Oui — l'usage réel le montre (4 missions `recherche` sur FloraPi). Alors amender `CLAUDE.md`. |
| **B-2** | B garde-t-il ses outils à zéro, ou reçoit-il un accès aux sources en profil recherche ? | **Zéro.** Trois motifs mesurés dans la disposition. |
| **B-3** | Le plafond de ~200 lignes tient-il ? L'inventaire est à **248**. | À trancher avec B-1 : soit on coupe, soit on déplace la référence en le disant. |

Ensuite seulement : étape 1 — la spécification de `DEPART.md`, qui ne prend en entrée que la colonne **Code**.

---

## État courant

- **Récolte faite et relue.** `conception/INVENTAIRE.md` v2 : **146 leçons** — 38 Code · 34 Prompt · 31 Règle · 20 Test · 23 Écarté. **248 lignes, au-dessus du plafond** (voir B-3).
- Relecture Codex en deux passes, 42 observations, **toutes disposées** : 28 acceptées, 6 rejetées, 5 différées, 3 bloquantes. Détail dans `conception/DISPOSITION_RELECTURE.md`.
- Les huit sources de `RECOLTE.md` sont dépouillées. `history.md` et `README.md` volontairement non ouverts — **Codex ne l'a pas contesté.**
- **Aucune ligne de code écrite.** Le dépôt ne contient que des documents de cadrage.
- Enchaînement : récolte (**relecture en cours**) → spécification (`DEPART.md`) → implémentation, avec arbitrage humain entre chaque.
- Le dépôt n'a **pas de remote** — décision reportée, à faire plus tard.
- Prédécesseur : DialogForge, refactoring **gelé** le 2026-09-02. Toujours utilisé **en conception seule** sur FloraPi.

## Décisions à confirmer par l'humain

- **Périmètre de la récolte** : tranché par Claude le 2026-09-03 — l'inventaire couvre *aussi* la conduite de projet. Motif et trace dans `RECOLTE.md`. Rouvrable.
- Les trois décisions de l'étape 1 (fin de `INVENTAIRE.md`) : cadrage automatique, plancher de `contracts.py`, format d'`etat.json`.

## Rappels actifs

- La mission DialogForge `e35cfcf1-47e5-4354-a4b1-d40235b8e3cf` est **en pause**, pas annulée. Elle redémarrerait seule si on la reprenait (`dialogforge resume`). Ne pas la relancer sans décision.
- Les quatre dossiers `C:\Projets\DialogForge*` et `C:\Projets\IAbinome` se référencent mutuellement. Point d'entrée du gel : `C:\Projets\DialogForge\ARRET_REFACTORING.md`.

## Blocages

Aucun.

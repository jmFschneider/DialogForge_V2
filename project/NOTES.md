# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. Historique → `session_log.md`. Règles → `RULES.md`.
> Dernière mise à jour : 2026-09-03

---

## Prochaine action — une seule

**Faire relire `conception/INVENTAIRE.md` par Codex, avec une seule consigne :**

> « Qu'est-ce qui a été écarté en silence ? »

Ne rien ajouter à cette consigne. Trois endroits à lui signaler comme suspects, et rien d'autre :

1. l'arrêt anticipé sur `history.md` (2 533 l.) et `README.md` (1 046 l.), jamais ouverts ;
2. les agrégats X16 à X18, qui écartent 166 éléments en trois lignes ;
3. la colonne **Code** (26 lignes) plus longue que **Prompt** (24), alors qu'elle devait être la plus courte.

Ensuite : arbitrage humain sur l'inventaire, puis étape 1 — la spécification de `DEPART.md`,
qui ne prend en entrée que la colonne **Code**.

---

## État courant

- **Récolte faite, non relue.** `conception/INVENTAIRE.md` : 26 Code · 24 Prompt · 21 Règle · 15 Test · 20 Écarté.
- Les huit sources de `RECOLTE.md` sont dépouillées. `history.md` et `README.md` volontairement non ouverts.
- **Aucune ligne de code écrite.** Le dépôt ne contient que des documents de cadrage.
- Enchaînement : récolte (**relecture en cours**) → spécification (`DEPART.md`) → implémentation, avec arbitrage humain entre chaque.
- Le dépôt n'a **pas de remote** — décision reportée, à faire plus tard.
- Prédécesseur : DialogForge, refactoring **gelé** le 2026-09-02. Toujours utilisé **en conception seule** sur FloraPi.

## Décisions à confirmer par l'humain

- **Périmètre de la récolte** : tranché par Claude le 2026-09-03 — l'inventaire couvre *aussi* la conduite de projet. Motif et trace dans `RECOLTE.md`. Rouvrable.
- Les trois décisions que l'inventaire ne tranche pas (fin de `INVENTAIRE.md`) : cadrage automatique, plancher de `contracts.py`, format d'`etat.json`. Elles appartiennent à l'étape 1.

## Rappels actifs

- La mission DialogForge `e35cfcf1-47e5-4354-a4b1-d40235b8e3cf` est **en pause**, pas annulée. Elle redémarrerait seule si on la reprenait (`dialogforge resume`). Ne pas la relancer sans décision.
- Les quatre dossiers `C:\Projets\DialogForge*` et `C:\Projets\IAbinome` se référencent mutuellement. Point d'entrée du gel : `C:\Projets\DialogForge\ARRET_REFACTORING.md`.

## Blocages

Aucun.

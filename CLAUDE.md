# CLAUDE.md — IAbinome

> Chargé automatiquement à chaque session. Gardé court **volontairement** : ce projet naît de l'échec
> d'un outil devenu trop gros. Si ce fichier dépasse une page, c'est un signal.

## 0. Début de session — OBLIGATOIRE

1. Lire **`POURQUOI.md`** — d'où vient ce projet et les règles qui en découlent. Non négociable : c'est ce qui empêche de refaire la même dérive.
2. Lire **`RECOLTE.md`** — **l'étape en cours**, la récolte de deux mois d'apprentissage. Une question y est en attente de décision, à trancher avant de commencer.
3. Lire **`DEPART.md`** — l'étape suivante : le travail concret, avec les fichiers sources exacts.
4. Ne rien lire d'autre par défaut.

## 1. Ce qu'est IAbinome

Un outil d'environ **1 500 lignes** qui coordonne **deux agents IA en CLI** aux rôles distincts :
**A produit, B critique, l'humain arbitre.** Tout en fichiers sur disque.

```
demande.md → A produit → B critique → A révise → (N fois max) → A finalise → livrable
```

**État : pas encore commencé.** L'étape en cours est la **récolte** (`RECOLTE.md`) — ni la spécification, ni le code.
Enchaînement : **récolte → spécification → implémentation**, avec arbitrage humain entre chaque.

## 2. Périmètre — les cinq interdits

Ce sont les cinq choses qui ont fait exploser le prédécesseur. Aucune ne rentre sans une décision humaine écrite et datée.

| Interdit | Pourquoi |
|---|---|
| **Pas d'exécution autonome** | Le livrable est un **document**, exécuté ensuite à la main. C'est la partie qui n'a jamais abouti. |
| **Pas de base de données** | Fichiers sur disque, `etat.json` lisible à l'œil. |
| **Pas de worker, bail, ni tâche planifiée** | On lance, ça tourne, on ferme le terminal. |
| **Pas de budget, réservation ni quota interne** | Les plafonds fournisseur suffisent. |
| **Pas de GUI** | CLI seule. |

Toute demande qui commence par « et si on ajoutait un petit contrôle pour… » **doit** être opposée à ce tableau avant d'être implémentée.

## 3. Méthode

- **Étape 1 — spécification.** Produire ce qui reste, ce qui tombe, la disposition des fichiers, la surface CLI, les gabarits de prompts repris. **Arbitrage humain avant la première ligne de code.**
- **Étape 2 — implémentation.** ~1 500 lignes + tests.
- Claude produit, **Codex relit palier par palier**. Construire l'outil avec son propre protocole est la démonstration qu'il n'a jamais eu besoin de machinerie.

## 4. Sources — en lecture seule

Ne jamais écrire dans ces dossiers ; on y copie, on ne s'y branche pas.

| Chemin | Rôle |
|---|---|
| `C:\Projets\DialogForge` | Le prédécesseur, toujours utilisé **en conception seule**. Contient `ARRET_REFACTORING.md` (le gel) et `REPRISE_LITE.md`. |
| `C:\Projets\DialogForge-refactor-lab` | Bac à sable gelé du refactoring abandonné. |
| `C:\Projets\DialogForge-refactor-archives` | Archives et preuves. Scellées par empreintes — ne rien y exécuter sans lire d'abord. |

## 5. Stack

Python 3.12 · **stdlib uniquement, zéro dépendance de production** · `ruff check .` + `mypy` avant tout commit · agent `fake` obligatoire pour les tests : **aucun appel fournisseur dans la suite de tests**.

## 6. Modèles par rôle

**Opus 5** pour A (produit, gros volume de sortie). **Fable 5** pour B (critique — c'est là que la capacité paie).
Avertissement de portage : sur les modèles récents, des consignes **trop prescriptives dégradent** la qualité. Les gabarits repris sont à alléger, pas à durcir.

## 7. Commits

`docs:` · `feat:` · `fix:` · `test:` · `chore:` — sans accents dans le message, comme le prédécesseur.

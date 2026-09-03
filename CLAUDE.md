# CLAUDE.md — IAbinome

> Chargé automatiquement à chaque session. Gardé court **volontairement** : ce projet naît de l'échec
> d'un outil devenu trop gros. Si ce fichier dépasse une page, c'est un signal.

## 0. Début de session — OBLIGATOIRE

1. Lire **`project/NOTES.md`** — tableau de bord de reprise : prochaine action, état courant, blocages.
2. Lire **`POURQUOI.md`** — d'où vient ce projet et les règles qui en découlent. Non négociable : c'est ce qui empêche de refaire la même dérive.
3. **Si le scope de session n'est pas déclaré dans le premier message : le demander avant toute action.**
4. Consulter **`project/RULES.md`** pour le domaine touché.
5. Lire l'étape en cours : **`RECOLTE.md`**, puis **`DEPART.md`** quand elle sera close.
6. **Ne pas lire un fichier** si l'information est déjà dans `NOTES.md`, `RULES.md` ou le contexte courant.

**En fin de session — OBLIGATOIRE :**

- `project/NOTES.md` — préparer la reprise immédiate. **Pas d'historique, pas de récit, pas de liste de travaux terminés.**
- `project/RULES.md` — ajouter les règles nouvelles, sans doublon.
- `project/session_log.md` — résumé, commits, décisions.

## 1. Ce qu'est IAbinome

Un outil d'environ **1 500 lignes** qui coordonne **deux agents IA en CLI** aux rôles distincts :
**A produit, B critique, l'humain arbitre.** Tout en fichiers sur disque.
Le livrable est un document de **conception ou de recherche** — les deux, décidé le 2026-09-03.

**Le rôle et l'outil sont deux axes indépendants.** A et B sont chacun Claude *ou* Codex, choisis au
lancement. Les quatre permutations sont supportées et testées. Rien dans le code ne suppose lequel est où.

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
- Claude produit. Construire l'outil avec son propre protocole est la démonstration qu'il n'a jamais eu besoin de machinerie.
- **La relecture Codex palier par palier est suspendue depuis le 2026-09-03** — décision du PO : la conception est assez précise pour s'en passer. Portée et condition de réouverture dans `project/RULES.md`.

## 4. Sources — en lecture seule

Ne jamais écrire dans ces dossiers ; on y copie, on ne s'y branche pas.

| Chemin | Rôle |
|---|---|
| `C:\Projets\DialogForge` | Le prédécesseur, toujours utilisé **en conception seule**. Contient `ARRET_REFACTORING.md` (le gel) et `REPRISE_LITE.md`. |
| `C:\Projets\DialogForge-refactor-lab` | Bac à sable gelé du refactoring abandonné. |
| `C:\Projets\DialogForge-refactor-archives` | Archives et preuves. Scellées par empreintes — ne rien y exécuter sans lire d'abord. |

## 5. Stack

Python 3.12 · **stdlib uniquement, zéro dépendance de production** · `ruff check .` + `mypy` avant tout commit · agent `fake` obligatoire pour les tests : **aucun appel fournisseur dans la suite de tests**.

## 6. Outils et modèles — des paramètres, jamais un câblage

Ne jamais nommer un fournisseur hors de son adaptateur — ni dans une reprise, ni dans un nom d'archive.
**Le cycle ne dépend que des capacités présentes chez les deux outils.** Session persistante, erreur de
quota typée, schéma natif : un bonus chez l'un, **jamais un prérequis**.
*Motif : la reprise après quota de DialogForge était bâtie sur l'erreur typée de Claude ; côté Codex, elle n'a jamais marché.*

Modèles par défaut, surchargeables : **Opus 5** pour A (gros volume), **Fable 5** pour B (la critique paie).
Sur les modèles récents, des consignes **trop prescriptives dégradent** la qualité : alléger les gabarits repris, pas les durcir.

## 7. Commits

`docs:` · `feat:` · `fix:` · `test:` · `chore:` — sans accents dans le message, comme le prédécesseur.
**Identité git : déjà en config globale — ne jamais la surcharger avec `-c`.** Détail et motif dans `project/RULES.md`.

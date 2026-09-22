# CLAUDE.md — DialogForge_2 (socle IAbinome)

> Chargé automatiquement à chaque session. Gardé court **volontairement** : ce projet naît de l'échec
> d'un outil devenu trop gros. Si ce fichier dépasse une page, c'est un signal.

## 0. Début de session — OBLIGATOIRE

**L'avancement du développement V2 appartient au plan PWF, et à lui seul.**
Plan : `.planning/2026-09-18-dialogforge-v2/`. Il n'y a pas de seconde liste à cocher.

1. Résoudre le plan, puis lire son `task_plan.md` — `## Next Step` fait foi :
   `sh "$HOME/.claude/skills/planning-with-files/scripts/resolve-plan-dir.sh"`.
   **Une sortie vide avec un code 0 n'est pas un succès** : c'est une sélection ambiguë ou erronée.
   Corriger l'épinglage (`PLAN_ID=2026-09-18-dialogforge-v2`) au lieu de retomber sur un autre plan.
2. Lire `findings.md` et `progress.md` du **même** dossier de plan.
3. Lire **`POURQUOI.md`** — d'où vient ce projet et les règles qui en découlent. Non négociable :
   c'est ce qui empêche de refaire la même dérive.
4. **Si le scope de session n'est pas déclaré dans le premier message : le demander avant toute action.**
5. Consulter **`project/RULES.md`** pour le domaine touché.
6. **Ne pas lire un fichier** si l'information est déjà dans le plan, `RULES.md` ou le contexte courant.

`project/NOTES.md`, `RECOLTE.md` et `DEPART.md` sont la **mémoire historique d'IAbinome**, conservée
comme contexte. Ce ne sont plus des tableaux de bord de reprise : ne pas y suivre l'avancement V2.

**En fin de session — OBLIGATOIRE :**

- `task_plan.md` du plan — mettre à jour `## Next Step` et le statut des phases.
- `progress.md` du plan — actions, résultats de tests, erreurs.
- `project/RULES.md` — ajouter les règles nouvelles, sans doublon.

## 1. Ce qu'est IAbinome

Un outil de **~3 250 lignes de code** (`src/`, hors commentaires et docstrings ; 4 900 lignes en tout)
qui coordonne **deux agents IA en CLI** aux rôles distincts :
**A produit, B critique, l'humain arbitre.** Tout en fichiers sur disque.
Le livrable est un document de **conception ou de recherche** — les deux, décidé le 2026-09-03.

**Le rôle et l'outil sont deux axes indépendants** — et le **modèle** en est un troisième. A et B sont
chacun Claude *ou* Codex, choisis au lancement. Rien dans le code ne suppose lequel est où.
Les quatre permutations sont supportées et couvertes de bout en bout par l'agent `fake` ; **deux
seulement sont mesurées en réel, délibérément** (PO, 2026-09-05) — `A == B` n'est pas un usage retenu.
**Rien n'interdit `A == B` pour autant** : c'est la seule porte de sortie quand un fournisseur est en
quota, et c'est la configuration de `§6` ci-dessous. Motif complet dans `project/RULES.md`.

```
demande.md → A produit → B critique → A révise → B relit → (N fois max) → livrable → l'humain décide
```

**Il n'y a pas d'appel de finalisation** : le livrable est la version que B vient d'examiner, promue
octet pour octet (décision 1.3). Un `FINAL_A` qui réécrivait après la dernière revue a été supprimé.

**État : voir le plan PWF** (`## Next Step` de `.planning/2026-09-18-dialogforge-v2/task_plan.md`) — cette page ne le suit pas.
L'enchaînement d'origine était **récolte → spécification → implémentation**, avec arbitrage humain entre chaque :
les deux premières étapes sont faites (`conception/`), le développement V2 avance lot par lot dans le plan.

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
- **Étape 2 — implémentation.** Visée d'origine : ~1 500 lignes. **Dépassement assumé par le PO le
  2026-09-22** — mesuré à J3 : 3 253 lignes de code dans `src/`, 7 555 en tests. La métrique de garde
  de `POURQUOI.md` (l'outil ne dépasse pas le projet servi) reste tenue et **reste la métrique** :
  c'est elle qu'on mesure, pas le chiffre de 1 500.
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

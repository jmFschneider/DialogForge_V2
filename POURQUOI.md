# Pourquoi IAbinome existe

> Écrit le 2026-09-02, au moment où le refactoring de DialogForge a été gelé.
> Ce fichier n'est pas de l'histoire pour l'histoire : les cinq règles de la fin sont
> **opérationnelles**, et c'est tout ce qui empêche de refaire exactement la même chose.

## L'origine

Le besoin de départ tenait en une phrase : *« un système simple où deux agents travaillent ensemble, l'un construit, l'autre révise, critique et propose. »*

Puis du contrôle a été ajouté, un peu à chaque fois, toujours pour une bonne raison : des budgets, des baux, des réservations, des worktrees, des stratégies adaptatives, des remèdes, des attestations, des preuves, des archives de preuves. Chaque ajout était justifié isolément. Aucun n'a été mis en regard du total.

## Ce que le total donnait, mesuré le 2026-09-02

- DialogForge pesait **87 382 lignes**. FloraPi, le projet qu'il devait servir, en pèse **58 894**.
  **L'outil était une fois et demie plus gros que le projet.**
- Dedans : **7 676 lignes** pour la boucle A/B, **26 997 lignes** pour l'appareil d'autonomie.
- Sur FloraPi depuis le 5 août : **7 conceptions terminées sur 9**. Et **une seule implémentation autonome tentée, bloquée à 1 tâche sur 7**.
- Sur DialogForge lui-même : implémentation bloquée à **1 tâche sur 10**, avec 4 interventions humaines en 3 heures.
- Le refactoring censé réparer tout ça prévoyait **15 lots**. Le Lot 0 — qui n'ajoutait que des tests, sans toucher une ligne de production — avait déjà coûté **~7 millions de tokens** et n'était pas fini.

## Le constat

**L'idée de départ marchait déjà.** Sept succès sur neuf. Ce qui ne marchait pas, c'était uniquement la couche ajoutée ensuite : l'exécution autonome. Elle n'a jamais mené une implémentation au bout, nulle part.

Le refactoring a donc été gelé, et non poursuivi : il revenait à réparer 27 000 lignes qui n'avaient rien livré, **en utilisant justement le sous-système défaillant pour se réparer lui-même**.

IAbinome, c'est le retour à la phrase de départ — avec les 7 676 lignes qui marchent, et sans les 27 000 autres.

---

## Les cinq règles qui en découlent

**1. L'outil ne doit jamais dépasser le projet qu'il sert.**
C'est la métrique de garde. Si IAbinome approche de la taille du module FloraPi qu'il aide à concevoir, quelque chose a mal tourné. Objectif : ~1 500 lignes.

**2. Chaque contrôle ajouté a un coût qui ne se voit qu'au refactoring.**
Isolément, un contrôle coûte une heure. Collectivement, ils rendent le système irréparable. La bonne question n'est jamais « est-ce que ce contrôle est utile ? » — c'est *« qu'est-ce que je retire en échange ? »*

**3. L'échafaudage compense la faiblesse des modèles.**
Une grande partie de la machinerie existait pour rattraper des modèles qui dérivaient. Les modèles récents en demandent **moins**, pas plus. Avant d'ajouter un garde-fou, vérifier qu'il compense un défaut encore réel.

**4. Les prompts trop prescriptifs dégradent les modèles récents.**
Mesuré : les tâches du Lot 0 portaient jusqu'à douze critères d'acceptation imbriqués. Sur les modèles récents, ce style **réduit** la qualité de sortie. Alléger, ne pas durcir.

**5. Ne jamais réparer un sous-système défaillant en s'en servant.**
Le refactoring de DialogForge était piloté par les missions d'implémentation durable de DialogForge. Les quatre blocages d'une soirée venaient du moteur, pas du travail demandé.

---

## Où trouver le reste

- `C:\Projets\DialogForge\ARRET_REFACTORING.md` — la décision de gel, le rôle des trois dossiers DialogForge, et trois défauts techniques mesurés à ne pas reperdre.
- `DEPART.md`, à côté de ce fichier — le travail concret : quels fichiers reprendre, quoi jeter, comment procéder.

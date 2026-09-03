# Étape 1 — prompt pour Codex : vérifier, analyser, proposer la structure

> Codex est **A** pour cette étape ; Claude sera **B**. Inversion assumée des rôles de l'étape 0
> (`RULES.md` : « Claude produit, Codex relit — **et réciproquement** »), et cohérente avec l'invariant
> `C15a` acté le 2026-09-03 : le rôle et l'outil sont deux axes indépendants.
>
> Une seule passe. Claude critiquera ensuite, puis l'humain arbitre avant la première ligne de code.

---

```text
Tu es l'agent A pour cette étape. Claude te relira ensuite ; l'humain arbitre.

Projet : C:\Projets\IAbinome. Tout ce qui suit y est.

## Lis d'abord, dans cet ordre

  POURQUOI.md   pourquoi le prédécesseur a explosé, et les cinq règles qui en découlent
  CLAUDE.md     les cinq interdits de périmètre
  DEPART.md     les cinq livrables attendus de cette étape, et les fichiers exacts à reprendre
  conception/INVENTAIRE.md   156 leçons récoltées, une destination par ligne

Ces quatre documents font autorité et priment sur ton jugement. Si tu veux t'en écarter,
dis-le explicitement au lieu de le faire.

## Ta mission, en trois temps

### 1. VÉRIFIER — c'est la partie que personne n'a faite

La colonne **Code** de l'inventaire (43 lignes) affirme ce que le programme doit faire.
Ces lignes ont été récoltées depuis des documents QUI PARLENT du code, pas depuis le code.

4 931 lignes de source n'ont jamais été ouvertes pendant la récolte :

  contracts.py                857     agents/subprocess_agent.py   1109
  storage.py                  505     agents/claude.py              568
  workflow.py                 119     agents/codex.py               675
  models.py                   303     agents/factory.py             537
  agents/base.py              192     agents/fake.py                 66

Va les lire, sous C:\Projets\DialogForge\src\dialogforge\. Puis dis, pour la colonne Code :
lesquelles tiennent · lesquelles sont fausses ou approximatives · lesquelles manquent.

Vérifie en particulier ce qui a été affirmé sans preuve directe : écriture atomique,
absence de verrou, contrat d'agent, contrat d'erreur de quota, validation des réponses.

### 2. ANALYSER

Ce qui, dans ces 4 931 lignes, sert réellement la boucle A/B — et ce qui n'existe que pour
l'appareil d'autonomie abandonné. `contracts.py` (857 lignes) et `subprocess_agent.py`
(1109 lignes) sont les deux gros morceaux : dis ce qui en reste une fois retiré ce qui
servait les missions durables, les budgets, les worktrees et le confinement.

Le budget total est ~1 500 lignes. Dis si c'est atteignable, et sinon pourquoi.

### 3. PROPOSER — les cinq livrables de DEPART.md

  1. ce qui reste et ce qui tombe, fichier par fichier
  2. la disposition des fichiers du projet
  3. la surface CLI : quelles commandes, quels arguments
  4. les gabarits de prompts repris, ALLÉGÉS (voir contrainte ci-dessous)
  5. la liste des tests, tous avec l'agent `fake`

## Contraintes non négociables

- Les cinq interdits de CLAUDE.md. Aucune exception sans décision humaine écrite.
- ~1 500 lignes. Python 3.12, stdlib seule, zéro dépendance de production.
- A et B sont chacun Claude OU Codex, choisis au lancement. Quatre permutations.
  Aucun fournisseur nommé hors de son adaptateur. Le cycle ne dépend que des capacités
  présentes chez les deux : ce qui est propre à l'un est un bonus, jamais un prérequis.
- Le livrable de la boucle est un document — conception ou recherche. Jamais une exécution.
- Alléger les gabarits de prompts, ne pas les durcir : sur les modèles récents, des consignes
  trop prescriptives dégradent la sortie. Douze critères d'acceptation imbriqués ont été
  mesurés comme nuisibles.
- Tu ne modifies rien sous C:\Projets\DialogForge*, ni sous C:\Projets\Florapy_V2. Lecture seule.

## Ce que tu ne dois PAS trancher

Le contrat de l'agent B — « aucun outil » ou « aucun effet » — est une question ouverte,
reportée par le PO (fin de conception/INVENTAIRE.md). Ta structure doit rester compatible
avec les DEUX réponses. Ne la referme pas, et dis où elle mordrait.

## Forme attendue

Sépare faits vérifiés, inférences, recommandations et incertitudes.
Nomme tes limites de preuve : ce que tu n'as pas ouvert, ce que tu n'as pas pu vérifier.
Chaque recommandation dit jusqu'à quand elle est réversible.
Ce qui reste ouvert reste visible : ne remplace pas un désaccord par un consensus apparent.

Écris dans C:\Projets\IAbinome\conception\STRUCTURE_PROPOSEE_CODEX.md
```

---

## Note de méthode

Une seule passe, contrairement à l'étape 0 : c'est une tâche de **production**, pas de contradiction.
Le découpage en deux passes servait à ne pas orienter un contradicteur — ici il n'y a rien à ne pas
orienter, et les contraintes de périmètre doivent au contraire être données d'emblée (`R31`).

**Écart assumé à `DEPART.md`.** Celui-ci dit que la spécification « ne prend en entrée que la colonne
**Code** ». C'est trop étroit : le livrable 4 a besoin de la colonne **Prompt**, le livrable 5 de la
colonne **Test**. Le prompt donne donc l'inventaire entier, et la colonne Code garde son rôle de moteur
de la structure. *Signalé plutôt que fait en silence.*

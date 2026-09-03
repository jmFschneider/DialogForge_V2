# session_log.md — Journal des sessions IAbinome

> Une entrée par session de travail.
> Format : date · travail accompli · commits · décisions notables.

---

## 2026-09-02 → 09-03 (Claude) — Fondation du projet

Session menée depuis `C:\Projets\Florapy_V2`, à la suite de l'audit du refactoring DialogForge.

### Ce qui a été fait

Audit de conformité du Lot 0 de DialogForge par rapport à son plan de marche, puis analyse stratégique de l'opportunité de poursuivre. Les mesures ont conduit à geler le refactoring et à fonder ce projet.

**Mesures décisives :**

- DialogForge : 87 382 lignes (49 568 `src/` + 37 814 tests), 78 modules, 242 commits, 7 semaines. FloraPi, le projet servi : 58 894 lignes. **Rapport 1,5.**
- Répartition interne : **7 676 lignes** de boucle A/B contre **26 997 lignes** d'appareil d'autonomie.
- Usage réel sur FloraPi depuis le 5 août : **7 conceptions terminées sur 9**, mais **1 seule implémentation durable tentée, bloquée à 1 tâche sur 7**.
- Lot 0 de DialogForge : bloqué à 1 tâche sur 10, ~7 M tokens consommés, 4 interventions humaines en 3 heures.
- Le refactoring prévoyait **15 lots** (0 à 14).

**Défauts techniques relevés au passage**, consignés dans `ARRET_REFACTORING.md` : coût Codex jamais remonté et entrée Claude jamais comptée ; `retry_at` de quota non parsable par `scheduling.parse_resume_time`, d'où un repli de 15 min et des réveils inutiles ; une tâche sans modification ne peut pas se clore seule.

### Décisions

1. **Refactoring DialogForge gelé** — décision datée, pas un abandon silencieux. DialogForge reste utilisé **en conception seule** sur FloraPi.
2. Mission d'implémentation `e35cfcf1-…` **mise en pause** : elle aurait redémarré seule à 01:01 au retour du quota Codex.
3. **Fondation d'IAbinome** — successeur allégé, ~1 500 lignes, deux agents IA en CLI, A produit / B critique, l'humain arbitre. Nom retenu après arbitrage : `BinomeIA` d'abord choisi, puis inversé en **`IAbinome`** par le PO.
4. **Cinq interdits de périmètre** figés dans `CLAUDE.md` : pas d'exécution autonome, pas de base, pas de worker/bail/tâche planifiée, pas de budget interne, pas de GUI.
5. **Une étape 0 de récolte est insérée avant la spécification** : capitaliser deux mois d'apprentissage en un inventaire d'une ligne par leçon, cinq destinations dont une colonne « Écarté » obligatoire, plafonné à ~200 lignes.
6. Modèles par rôle : **Opus 5 pour A, Fable 5 pour B**.
7. Remote git : **reporté**.

### Commits

**IAbinome** — `78e09e8` fondation (amendé pour corriger l'identité git) · `b513a8d` étape de récolte · commit des règles de travail.
**DialogForge** — `4903927` gel du refactoring et préparation de l'extraction · `01a9e03` nom du successeur et pointeur vers son dépôt.

### À retenir

L'erreur d'identité git (adresse du compte Claude au lieu de `schneider.jm@free.fr`) a nécessité un `--amend --reset-author`. Règle consignée dans `RULES.md`.

---

## 2026-09-03 (Claude) — Étape 0 : la récolte

Scope déclaré : poursuivre la récolte. Première session ouverte directement dans `C:\Projets\IAbinome`.

### Ce qui a été fait

Les **huit sources** de `RECOLTE.md` ont été dépouillées, dans l'ordre prescrit, et l'inventaire produit :
`conception/INVENTAIRE.md` — **26 Code · 24 Prompt · 21 Règle · 15 Test · 20 Écarté**, sous la barre des ~200 lignes.

**Mesures relevées pendant la récolte :**

- `context\supervision.md` pèse **113 des 194 lignes** de la doctrine déjà distillée, et ne traite que de conduite de projet.
- **14 des 69 fichiers de tests** de DialogForge nomment la boucle A/B ; **55 nomment l'appareil écarté.**
- Sur les 42 `fix:`, **9 sont retenus** ; sur les 85 `[DIFFÉRÉ]`, **7**.
- La boucle A/B entière tient dans ~80 lignes de prompts (`orchestrator.py:681-760`), le cadrage dans ~80 autres.
- Cinq faits mesurés repris de `preuves\README.md` : formule de reconstruction des tokens, 229 288 tokens de cadrage non comptés, réservation qui gouverne l'admission et non la consommation, laboratoire en avance de 6 commits sur sa référence, lecture d'archive SQLite qui casse ses propres empreintes.

**Sources arrêtées et notées :** `history.md` (2 533 l.) et `README.md` (1 046 l.) n'ont pas été ouverts, les huit sources répétant déjà leurs constats. La conception MariaDB (1 243 l.) n'a rendu que 2 lignes sur 1 243 — source épuisée avant sa fin.

### Décisions

1. **Périmètre de la récolte tranché : les deux.** L'inventaire couvre aussi la conduite de projet, en destination **Règle**, jamais **Code**. Motif mesuré — `supervision.md` avait déjà tranché de fait. Tranché par Claude faute d'arbitrage en séance, tracé dans `RECOLTE.md`, **rouvrable**.
2. Deux règles de méthode ajoutées à `RULES.md` : trancher une question ouverte dans le document qui la porte ; noter l'abandon d'une source de récolte avec son volume non lu.
3. La contrainte « **Code** est la colonne la plus courte » n'est **pas tenue** (26 contre 24). Constat porté en tête de la relecture plutôt que corrigé en douce.

### Commits

`docs: recolter deux mois d apprentissage dans un inventaire` — inventaire, arbitrage du périmètre, règles de méthode.
*(Le commit ne cite pas son propre hash : l'`--amend` le déplace.)*

### À retenir

L'inventaire n'est **pas relu**. Le protocole veut une passe Codex à consigne unique — « qu'est-ce qui a été écarté en silence ? » — avant tout arbitrage humain. Trois zones lui sont désignées comme suspectes : l'arrêt anticipé sur deux sources, les trois agrégats qui écartent 166 éléments d'un coup, et la colonne Code hors contrainte.

---

## 2026-09-03 (Claude + Codex) — Relecture contradictoire et inventaire v2

Le protocole d'IAbinome a tourné sur IAbinome lui-même, avant d'exister : Claude récolte, Codex contredit, l'humain arbitre.

### Ce qui a été fait

Prompt de relecture préparé en **deux passes** (`conception/RELECTURE_CODEX.md`) : la consigne d'omission seule d'abord, les zones suspectes seulement après réponse — donner ces zones d'emblée aurait orienté le contradicteur vers ce que l'auteur savait déjà.

Codex a répondu en deux temps, le PO ayant élargi le prompt entre-temps :

- **Passe 1** — 42 omissions, filet large, sans tri.
- **Version 1.1** — après précision du périmètre (*« conception et recherche, pas de codage »*), Codex reprend son propre jet et **se contredit sur six points**. Constat majeur : sa passe 1 réintroduisait la logique de forteresse de DialogForge qu'il devait aider à éviter.

Les 42 observations ont reçu **chacune exactement une disposition** (`conception/DISPOSITION_RELECTURE.md`) : **28 acceptées, 6 rejetées avec motif, 5 différées sous condition, 3 bloquantes**. Inventaire porté en v2 : de 106 à **146 leçons**, 248 lignes.

### Les trois trouvailles réelles

1. **La robustesse intellectuelle manquait entièrement** — indépendance des sources, résultat négatif qui compte, portée bornée par la preuve, contre-preuves conservées, critère de fin défini avant de chercher. J'avais dépouillé FloraPi pour ce qu'il disait de l'outil et de la conduite, jamais pour ce qui fait un **bon livrable** — c'est-à-dire le produit même d'IAbinome. Omission la plus coûteuse.
2. **`X7` écartait trop.** « Sans écriture agent, il n'y a rien à confiner » est faux : la frontière d'effets survit à l'appareil qui l'entourait. Onze lignes de Code ajoutées, aucun sous-système.
3. **Trois agrégats masquaient des invariants transférables** — prévol avant tout effet, état fermé sur valeur inconnue, intention d'appel persistée avant l'appel. Plus le troisième défaut mesuré d'`ARRET_REFACTORING.md`, qui n'était **ni retenu ni écarté**.

### Décisions

1. **Cinq contrôles proposés par la relecture sont refusés** — consentements réseau, scanner de secrets, agent réparateur de JSON, nettoyage automatique, sonde de worker. Motif commun : aucun ne compense un défaut encore réel (`POURQUOI` règle 3). Tous tracés en `X23`, aucun écarté en silence.
2. **Nouvelle règle `R31`** : le contradicteur, seul, tire vers l'ajout de contrôles ; il faut lui opposer le périmètre. Mesuré sur cette relecture même.
3. **Le dépassement du plafond est déclaré, pas maquillé** — 248 lignes contre ~200. Devient la question B-3.
4. La prémisse de `RECOLTE.md` « **Code** est la colonne la plus courte par construction » est probablement fausse : une leçon de périmètre *est* une ligne de code. 38 Code contre 34 Prompt.

### Commits

`docs: verser les deux passes de relecture de Codex` · `docs: disposer la relecture et porter l inventaire en v2`

### À retenir

**Trois questions bloquantes attendent l'humain** : B-1 la recherche entre-t-elle au périmètre (`CLAUDE.md` ne parle que de conception) · B-2 B garde-t-il ses outils à zéro (recommandation : oui) · B-3 le plafond de lignes tient-il. Rien ne peut avancer avant.

La seconde passe a plus apporté que la première. **Une consigne d'omission sans contrainte de périmètre produit un contradicteur qui rechute** — c'est le résultat le plus solide de la journée, et il vaut pour la conception d'IAbinome lui-même.

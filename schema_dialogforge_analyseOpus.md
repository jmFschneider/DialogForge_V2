# Runner : de la conception acceptée au code livré — analyse et proposition

**Rédigé le 4 octobre 2026 par Claude (Opus 5.5)**, à partir de `schema_dialogforge.md` (diagnostic
de Codex et commentaires de Sonnet) et d'une lecture du code de la branche `feat/runner-v1`.
Ce document est une **proposition soumise au PO**. Rien n'est implémenté.

**Objectif du PO :** une fois une conception validée, on passe au Runner. Celui-ci va jusqu'au bout,
soit un résultat utilisable dans `code/`. Il ne s'arrête que sur un problème qu'il ne peut pas
résoudre seul.

---

## 1. Constat principal : le moteur est bon, c'est le parcours qui fragmente

Le cœur du Runner (`src/dialogforge_runner/core.py`) fait déjà correctement l'essentiel :

| Capacité | Où | État |
|---|---|---|
| Clone isolé sous Ubuntu, sandbox `srt`, jeton jamais sur disque | `prepare`, `run_claude` | Qualifié le 2026-10-02 |
| **Un seul appel agent pour tout le lot** : l'agent code, teste, corrige et committe lui-même | `run_agent` (prompt « Organise librement ton travail, teste-le ») | Mesuré sur Mastermind : 6 commits, 23 tests |
| Validations finales sur la tête exacte, sans agent | `collect` | OK |
| Continuation avec l'échec de validation joint au prompt | `run_agent(continue_existing=True)` | OK |
| Transport des commits exacts (bundle Git) | `bundle_candidate` | OK |
| Avance du dépôt cible en fast-forward seulement | `delivery.integrate_candidate` | OK |

**La boucle « coder → tester → corriger » existe déjà, à l'intérieur de l'appel agent.** Claude Code
travaille de façon autonome pendant toute la durée de l'appel. C'était l'intention de la conception
Runner V1 (« un lancement pour réaliser le lot », tableau de fin du document).

La fragmentation vient de **ce qui suit le paquet**, dans `delivery.py` et l'écran GUI :

```text
paquet ─→ « Poursuivre : examiner le paquet »  (runner.py:156, clic 1)
       ─→ receive_package + create_review       (nouvelle collaboration « Prête »)
       ─→ « Démarrer la collaboration »         (clic 2, appels A/B, documentaire)
       ─→ décision humaine sur un RAPPORT       (clic 3)
       ─→ « Intégrer ce candidat »              (suivi.py:106, clic 4)
       ─→ enfin, le code est dans code/
```

Le paradoxe relevé par Codex en découle directement. Le code n'arrive dans `code/` qu'**après** la
décision. L'humain juge donc un commentaire, pas un jeu qu'il peut lancer.

**Conséquence :** il ne faut presque rien construire. Il faut **retirer la revue documentaire du
chemin** et **déplacer la livraison avant la décision**. C'est conforme à la règle 2 de
`POURQUOI.md` (« qu'est-ce que je retire en échange ? ») : la refonte devrait réduire le code.

---

## 2. Le parcours cible

```text
Conception acceptée
   │
   └─ « Démarrer l'implémentation »  (une fois ; jeton saisi une fois)
         │
         ├─ Préparation : prérequis, export, dépôt initial, clone        (existant)
         ├─ Appel agent : code, tests, commits                           (existant)
         ├─ Validations finales sur la tête exacte                       (existant)
         ├─ Échec ? → continuation avec l'échec joint, tant qu'il y a progrès  (§4)
         └─ Succès → livraison dans code/ sur la branche candidat/NNN    (NOUVEAU, §3)
                 │
                 ▼
   Utilisateur : ouvre code/, lance le jeu
         ├─ « Accepter »            → fast-forward de la branche principale (existant)
         └─ « Demander une correction » + objectif → même clone, nouvel appel,
                                       nouvelle branche candidat/NNN+1
```

**Arrêts qui rendent la main** (§4 et §5) :

- l'agent ne produit aucun commit ;
- la même validation échoue sans progrès ;
- la durée totale est atteinte ;
- authentification refusée, prérequis manquant ou interruption par l'utilisateur.

Dans tous ces cas, l'écran affiche le **bilan de l'agent**. Une question métier s'y trouve
naturellement, puisque le prompt actuel lui demande déjà de « s'arrêter si une décision dépasse le
mandat » et de l'expliquer.

---

## 3. Livraison dans `code/` — précision de la proposition de Sonnet

Je retiens la proposition de branche candidate et la précise.

**Livrer** (automatique en fin de run réussi, sans jeton, réalisé par DialogForge et non par
l'agent, donc hors sandbox de l'agent) :

1. Copier le paquet dans `developpement/paquets/NNN` comme **trace** (diff, validations, bilan).
   Il ne déclenche plus de collaboration. C'est l'actuel `receive_package`, inchangé.
2. `git fetch <bundle> HEAD:refs/heads/candidat/NNN` dans `code/`. Ce sont les briques actuelles de
   `_local_bundle` et `integrate_candidate`, sans le `merge`.
3. **Si `code/` est propre**, `git switch candidat/NNN`, et le jeu est immédiatement essayable. C'est
   le cas normal d'un projet neuf.
   **Sinon**, ne rien basculer et afficher la commande à lancer. Les changements de l'utilisateur
   ne sont jamais touchés, comme aujourd'hui.

**Accepter :** `git switch <branche principale>` puis `git merge --ff-only candidat/NNN`, avec reçu
dans `developpement/integrations/`. C'est l'actuel `integrate_candidate`, débarrassé de l'exigence
« revue acceptée ».

**Corriger :** nouvel appel dans le **même clone**, dont la tête est déjà le candidat.
`candidat/NNN+1` contient donc `NNN` plus les correctifs, et l'acceptation reste un fast-forward.

**Ce que cela donne :**

- le code est exécutable avant la décision ;
- la branche principale reste à la base tant que rien n'est accepté ;
- chaque candidat est une branche nommée, plus son paquet de trace ;
- aucun dossier figé ne sert de chemin vers le code.

> **Point à confirmer par le PO : le sens de « déploiement ».** Je l'entends comme *un résultat
> utilisable dans `code/`*. Push, publication et mise en production restent hors périmètre (conception
> Runner V1, « Restent hors périmètre », et tableau des interdits) et restent des gestes humains. Si « déploiement » veut dire
> davantage, c'est une autre décision.

---

## 4. Condition d'arrêt de la boucle de correction — proposition de Sonnet amendée

**Aujourd'hui :** `MAX_AGENT_CALLS = 3` dans une durée totale (`runner_session.py:31`, `_run_calls`).
C'est un compteur, donc proche du « quota interne » que le tableau des interdits exclut. Surtout, il
peut arrêter un agent qui progresse, ou laisser tourner trois fois un agent qui piétine.

**Proposition :** remplacer le compteur par un **critère de non-progression**, et garder la durée
totale choisie par l'utilisateur comme seule borne chiffrée.

Le Runner s'arrête et rend la main si l'un de ces cas se produit :

1. **Un appel ne crée aucun nouveau commit.** L'agent n'a rien fait, ou s'est arrêté pour poser une
   question. Ce contrôle existe déjà après un paquet (`run_agent`, fin) ; il suffit de l'appliquer à
   toute continuation.
2. **La même validation échoue avec le même code de sortie après deux corrections consécutives.**
   La signature retenue est (indice de validation, code de sortie), pas le texte de sortie, qui
   varie (durées, chemins).
3. La durée totale est atteinte.
4. Erreur bloquante : authentification (401, déjà détectée), prérequis, interruption ou pause.

**Ajustement par rapport à Sonnet :** Sonnet proposait « aucun diff utile sur un tour ». « Utile »
n'est pas mesurable sans juger le code. « Aucun commit » est mesurable sans interprétation, et le
mandat impose de committer.

**Alternative écartée : un marqueur de statut** en fin de réponse (`STATUT: DECISION_REQUISE`).
C'est le protocole `STEP_RESULT` que la conception Runner V1 a retiré. Le cas 1 suffit, puisqu'une
question sans commit arrête le run et affiche le bilan.

---

## 5. La revue A/B — proposition de Sonnet amendée

**Proposition de Sonnet :** faire de la revue A/B une passe interne au Runner (B critique, A corrige)
avant la livraison.

**Mon avis : ne pas le faire dans cette refonte.**

- C'est de la machinerie nouvelle : un second agent dans le sandbox, un second jeton pour un second
  fournisseur, et un protocole entre eux. Les règles 2 et 3 de `POURQUOI.md` demandent de s'en
  passer tant que le défaut à compenser n'est pas observé.
- Sur Mastermind, le défaut observé n'est pas « le code est faux ». C'est « je ne peux pas
  l'essayer ».
- Le juge naturel d'un code est son exécution, par les validations puis par l'humain. Un rapport
  documentaire ne l'est pas.

**Proposition :**

- la revue A/B **sort du chemin** : elle n'est plus requise pour accepter ;
- elle reste disponible comme **action facultative** sur un candidat livré (« Faire relire le
  candidat »), avec le code actuel de `create_review` ;
- on la supprimera si elle n'est pas utilisée après quelques missions ;
- le prompt de l'agent peut lui demander de **relire son propre diff avant de terminer**. C'est une
  phrase de prompt, sans machinerie.

---

## 6. Le jeton

**Aujourd'hui :** il est saisi par action et effacé après le lancement. Le lancement actuel couvre
déjà ses continuations automatiques, qui le réutilisent en mémoire.

**Proposition :**

- **Une exécution = une saisie.** C'est le comportement actuel, qui reste valable pour toute la
  boucle du §4.
- **Corrections après livraison :** garder le jeton **en mémoire du processus GUI**, jamais sur
  disque, jusqu'à la fermeture de la fenêtre, avec un bouton « Oublier le jeton ». Une correction est
  de toute façon un clic humain délibéré ; ressaisir le jeton n'y ajoute aucune sécurité réelle.
- La transmission reste inchangée : entrée standard du pont, jamais en argument ni en fichier, et
  jamais visible des validations.

---

## 7. Deux points que le document de Codex n'aborde pas

### 7.1 Le mandat transmis à l'agent contredit le nouveau parcours

L'export (`development.export_files`, paragraphe « Passage de relais ») dit à l'agent :

> « DialogForge ne développe, ne teste, ne commit et ne déploie rien. […] tout changement de code
> ou de validation exige un nouveau paquet et une nouvelle collaboration. »

Il ajoute le schéma JSON des validations. Ce texte a été écrit pour un **développeur extérieur
humain**. Pour l'agent du Runner, c'est du bruit prescriptif (règle 4 de `POURQUOI.md`), et il décrit
un parcours qui n'existera plus.

**Proposition :** un mandat court comprenant :

- la demande ;
- la conception acceptée ;
- les réserves et constats ouverts ;
- les validations prévues ;
- une consigne : « livre un candidat committé qui passe les validations ; arrête-toi et explique si
  une décision te manque ».

### 7.2 Les dépendances du projet

Les validations tournent sous `srt` **sans réseau**, et le Runner n'installe aucune dépendance
(`docs/RUNNER.md`). Mastermind passe parce que `node --test` n'a besoin de rien. Un projet qui demande
`npm install` ou `pip install` **ne pourra pas aller au bout** : c'est un « problème qu'il ne peut pas
résoudre » systématique, sans être une vraie difficulté.

Ce n'est pas bloquant pour la refonte. Mais c'est la prochaine limite réelle de l'objectif « va
jusqu'au bout », et elle demande une décision : un registre de paquets autorisé dans le sandbox de
l'agent, ou des dépendances fournies d'avance. À trancher plus tard, pas maintenant.

---

## 8. Ce qui change dans le code — estimation

| Fichier | Changement | Sens |
|---|---|---|
| `gui/runner_session.py` | `_run_calls` : compteur remplacé par le critère du §4 ; enchaînement automatique sur la livraison | ≈ constant |
| `delivery.py` | Nouveau `deliver_candidate` (fetch + branche + switch si propre), extrait d'`integrate_candidate` ; `integrate_candidate` sans exigence de revue | ≈ constant |
| `delivery.py` | `create_review`, `review_for`, `_link_review`, `review_context` : hors du chemin, gardés pour l'action facultative | — |
| `gui/views/runner.py`, `gui/views/suivi.py` | « Poursuivre : examiner le paquet » et « Intégrer ce candidat » remplacés par **Accepter** / **Demander une correction** sur l'écran Runner ; un seul suivi « Implémentation » | **réduction** |
| `executions.py` | Messages de reprise (`executions.py:279`) alignés | réduction |
| `development.py` | Mandat allégé (§7.1) | réduction |
| `core.py` | Contrôle « aucun commit » étendu à toute continuation | +quelques lignes |

**Bilan attendu :** une baisse nette du code façade et GUI, aujourd'hui à 2 643 lignes pour un plafond
de 2 700. Les tests continuent de passer par l'agent `fake`, sans aucun appel fournisseur.

**États affichés dans le suivi « Implémentation »** (sans nouvel état stocké, toujours relus depuis
le dossier Runner et `code/`) :

- Préparation
- Développement (appel n)
- Validations
- **Livré : candidat/NNN à essayer**
- Accepté
- Arrêté, avec un motif parmi : *sans commit*, *échec répété*, *durée*, *authentification*, *prérequis*,
  *interrompu*

---

## 9. Ordre proposé

1. **Décision PO écrite et datée** (préalable obligatoire, §2 de `CLAUDE.md`) :
   - Le Runner livre un candidat dans `code/` sur une branche `candidat/NNN`. Il n'intègre jamais
     lui-même dans la branche principale ; l'acceptation humaine le fait.
   - La revue A/B n'est plus requise pour accepter un candidat.
   - La boucle de correction est bornée par la non-progression et la durée, plus par un compteur.
   - « Déploiement » signifie un résultat utilisable dans `code/` (à confirmer).

   Textes à amender en conséquence :
   - `CLAUDE.md` §2 (ligne « Il prépare un candidat pour revue ; il ne l'intègre pas ») ;
   - la conception Runner V1 (« La V1 ne déclenche pas une boucle externe de réparation » ; « La revue
     A/B et `dev-verify` suivent ensuite ») ;
   - `docs/RUNNER.md`.
2. **Lot A : livraison et acceptation** (§3). **Ce lot remplace le « lot 4 » du plan** (rapatrier,
   revoir, intégrer). Première recette : livrer le candidat Mastermind **déjà produit** dans
   `Mastermind/code/` sous `candidat/001`, sans nouvel appel, puis l'essayer.
3. **Lot B : boucle à non-progression** (§4) et mandat allégé (§7.1).
4. **Lot C : GUI**, un seul suivi « Implémentation » et le jeton gardé en mémoire (§6, §8).
5. Plus tard, sur décision : dépendances (§7.2) ; suppression ou maintien de la revue facultative
   (§5).

Le lot A apporte à lui seul l'essentiel de ce que demande le PO : essayer le jeu avant de décider.
Il peut être recetté sur Mastermind sans aucun appel fournisseur.

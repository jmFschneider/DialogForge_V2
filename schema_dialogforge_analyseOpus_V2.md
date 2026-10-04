# Runner : de la conception acceptée au résultat utilisable — proposition V2

**Rédigé le 4 octobre 2026 par Claude (Opus 5.5).** Cette version remplace
`schema_dialogforge_analyseOpus.md`. Elle intègre l'analyse d'Astra (`schema_dialogforge_analyseAstra.md`)
et la confronte au code de `feat/runner-v1`. C'est une **proposition soumise au PO** : rien n'est
implémenté et aucune décision n'est présumée acquise.

**Objectif du PO :** une conception est validée, on passe au Runner, et celui-ci délivre ce que la
conception prévoit. Il ne s'arrête que sur un problème qu'il ne peut pas résoudre seul.

---

## 0. Ce qui change par rapport à ma V1

Astra a vu ce que j'avais manqué : **ma V1 réglait l'accès au résultat, pas la conformité du
résultat.** Son contre-exemple est probant. Pour un mandat « modifier `code.txt` », un commit qui
n'ajoute qu'un README et une validation qui renvoie 0 suffisent : le vrai `core.collect()` produit un
paquet « réussi ». Le Runner s'arrête aujourd'hui sur **des tests verts**, pas sur **la conception
réalisée**. Livrer plus tôt dans `code/` rendrait seulement plus visible un travail possiblement
incomplet.

| Sujet | V1 | V2 | Origine |
|---|---|---|---|
| Critère de fin | Validations vertes, puis essai humain | Validations vertes **et** revue B de conformité, puis essai humain | Astra |
| Revue B | Retirée du chemin, facultative | **Dans le Runner**, sur le code et non sur un rapport, en un seul appel par tour | Astra et Sonnet ; j'en réduis la forme (§3.2) |
| Fin d'appel de A | Aucun statut : « aucun commit » suffit | **Une ligne de statut** en fin de réponse (4 valeurs) | Astra ; j'en réduis la forme (§3.1) |
| Arrêt de la boucle | Aucun commit, ou même validation en échec deux fois | Répétition stricte constatée par le logiciel, progrès jugé par B, durée totale nommée comme borne | Synthèse (§3.3) |
| Règle des 3 appels | Présentée comme proche d'un quota | **Règle PO du 2026-10-03, à amender explicitement** | Astra (correction factuelle) |
| Dépôt existant | Basculer la branche dans le dépôt de l'utilisateur si propre | **Clone d'essai dans `code/`**, le dépôt utilisateur restant la cible | Astra |
| Bundle | Inchangé | **Créé à la remise**, sinon les anciens candidats deviennent intransportables | Astra (défaut réel de `bundle_candidate`) |
| Politique de boucle | Dans `runner_session.py` (GUI) | **Dans `dialogforge_runner`**, commune à la CLI et à la GUI | Astra |
| Lancement | Non traité | A documente le lancement ; l'environnement vérifié est affiché | Astra, réduit |

**Ce que je n'adopte pas d'Astra** (§8) : l'absence de toute borne de durée, le journal d'intention
généralisé, le contrôle de démarrage en copie jetable comme mécanisme dédié, et les modes de remise
« artefact construit ». Le motif est le même pour les quatre : la façade et la GUI sont à
**2 698 lignes sur 2 700**, et `POURQUOI.md` existe précisément parce que chaque contrôle justifié
isolément a fini par faire exploser le prédécesseur.

---

## 1. Le contrat proposé

> Après acceptation de la conception, **un lancement** autorise le Runner à réaliser la conception
> entière, faire tester puis relire chaque candidat, corriger ce qui est corrigeable dans le mandat et
> remettre une version utilisable dans `code/`. Les appels s'arrêtent sur l'un de ces événements :
> - une version prête à essayer ;
> - une question ou un obstacle expliqués ;
> - une répétition sans progrès ;
> - la durée totale fixée ;
> - une interruption par l'utilisateur.
>
> L'utilisateur essaie la version, puis l'accepte ou demande une correction. L'acceptation désigne le
> commit exact qui a été essayé.

« Déploiement » s'entend comme **un résultat utilisable dans `code/`**. Push, publication et mise en
production restent hors périmètre et restent des gestes humains. *Le PO doit le confirmer.*

---

## 2. Le parcours cible

```text
Conception acceptée
   └─ « Démarrer l'implémentation »  — une autorisation, un jeton
        │
        ├─ Préparation : prérequis, export, dépôt initial, clone          (existant)
        │
        └─ Tour n :
             A (Opus)   : code, tests, commits, bilan + ligne de statut   (existant + statut)
             Runner     : validations sur la tête exacte                  (existant)
             B (Fable)  : revue du code au regard de la conception        (NOUVEAU, lecture seule)
                │
                ├─ validations rouges ou A « RESTE »  → tour n+1, A reçoit l'échec
                ├─ B « CORRIGER »                     → tour n+1, A reçoit les constats de B
                ├─ A « QUESTION »/« OBSTACLE », ou B « ARBITRAGE » → pause, question affichée
                ├─ répétition stricte, ou durée totale atteinte   → pause, motif affiché
                └─ B « PRÊT »  → remise dans code/ (candidat/NNN), bundle conservé
                                    │
             Utilisateur : ouvre code/, lance, essaie
                ├─ « Accepter cette version »  → fast-forward de la branche cible
                └─ « Demander une correction » → tour suivant, même clone → candidat/NNN+1
```

Chaque tour est une suite d'événements dans le même écran « Implémentation ». On ne crée jamais de
nouvelle collaboration et on ne revient jamais à « Prête ».

---

## 3. Les trois mécanismes de la boucle

### 3.1 Fin d'appel de A : une ligne, pas un protocole

Le bilan libre de A est conservé. On ajoute une consigne : **terminer la réponse par une ligne**

```text
DIALOGFORGE: LIVRE | RESTE | QUESTION | OBSTACLE
```

| Statut | Sens |
|---|---|
| `LIVRE` | A propose le candidat pour vérification |
| `RESTE` | Du travail du mandat reste à faire, et A sait lequel |
| `QUESTION` | Une décision métier lui manque ; la question figure dans le bilan |
| `OBSTACLE` | Un prérequis ou un accès empêche de continuer |

- **Une ligne par appel**, et non un résultat par tâche. Le `STEP_RESULT` retiré par la conception
  Runner V1 était un protocole par étape ; ceci n'en est pas un.
- **Une ligne absente ou illisible ne vaut jamais `LIVRE`.** Elle met en pause avec le motif
  « résultat de l'agent illisible », et le bilan brut s'affiche.
- On demande aussi à A, dans son bilan, une **table de couverture** : exigence de la conception,
  réalisation, preuve. Elle donne à B un point d'entrée, mais **B la confronte au document entier** :
  elle ne réduit pas le périmètre.

### 3.2 Revue B : directe, en lecture seule, dans le même clone

B ne relit plus un rapport rédigé par A. **B examine le code.**

- **Quand.** Seulement si les validations passent et que A a déclaré `LIVRE`. Inutile de payer B pour
  un candidat que les tests refusent déjà.
- **Entrées.** Le mandat (export), le diff `base..tête`, les résultats des validations, le bilan et la
  table de A, et les constats encore ouverts du tour précédent.
- **Accès.** B travaille **dans le clone complet**, avec les outils `Read`, `Glob` et `Grep` seulement.
  Il voit donc les interactions hors du diff, ce qui répond à l'objection d'Astra sur les dépôts
  existants. Après l'appel, le Runner revérifie que la tête et l'état du clone n'ont pas changé, comme
  `_candidate()` le fait déjà pour les validations ; sinon, erreur.
- **Sortie.** Un JSON court :

  ```json
  {"verdict": "PRET | CORRIGER | ARBITRAGE",
   "constats": [{"id": "B-1", "exigence": "§ de la conception", "constat": "…"}],
   "progres": true}
  ```

  Réutiliser les contrats d'objection existants (`contracts.py`, `objections.py`) **si** leur schéma
  convient sans adaptation. Sinon, ce schéma minimal suffit.
- **Outil et modèle.** Seul le profil `claude-wsl` est qualifié. Dans un premier temps, B tourne donc
  dans **le même profil, avec le même jeton**, sur le modèle Fable 5 (défaut de `CLAUDE.md` §6). Rien
  ne l'impose côté contrat. Un B Codex dans le Runner serait une qualification séparée, à ne pas
  prétendre acquise. `A == B` en outil est permis par les règles ; ici, les **modèles** diffèrent.
- **Les corrections ont leur propre rubrique.** Dans le prompt de A, les constats de B arrivent sous
  « Constats de la revue ». Les échecs arrivent sous « Validation à corriger ». Seule une demande
  réelle de l'utilisateur figure sous « Correction demandée par l'utilisateur ». Aujourd'hui, seule
  cette dernière rubrique et celle des validations existent.
- **Pas de réécriture après le feu vert.** Si un commit survient après le `PRET` de B, la nouvelle
  tête repasse par les validations et par B.

### 3.3 Conditions d'arrêt : faits constatés, progrès jugé par B, borne nommée

Je retire la règle mécanique « même échec deux fois » de ma V1. Astra a raison : un test
d'intégration peut rester rouge pendant deux réparations utiles. Je garde quand même des règles
**calculables**. « Utiliser les artefacts disponibles », la formule d'Astra, ne s'implémente pas.

| Cause | Comment c'est constaté | Effet |
|---|---|---|
| Question ou obstacle | Statut de A, ou verdict `ARBITRAGE` de B | Pause ; question affichée |
| Aucun changement | Tête inchangée après un appel de A, hors `QUESTION` ou `OBSTACLE` | Pause « aucun changement » ; existe déjà après un paquet, à étendre à toute continuation |
| Répétition stricte | Même arbre Git (*tree hash*) **et** mêmes validations en échec qu'à un tour précédent | Pause « répétition » |
| Revue sans progrès | B répond `progres: false` **deux tours de suite** sur les mêmes constats | Pause, avec l'historique des constats |
| Durée totale | Paramètre saisi au lancement : c'est le délai total qui existe déjà (`request.timeout`) | Pause reprenable, jamais « livré » |
| Incident | 401, quota, prérequis, interruption ou pause demandées | Pause ; **aucun rejeu automatique** |

**Sur la durée totale, je ne suis pas Astra.** Il accepte qu'aucune durée maximale ne soit garantie.
Le PO lance et doit pouvoir partir ; un run sans borne n'est pas acceptable. La durée totale **n'est
pas un quota interne** : c'est un paramètre choisi par l'utilisateur, affiché et nommé. Astra le dit
lui-même : si une borne globale est voulue, il faut la nommer et la décider.

**Le compteur `MAX_AGENT_CALLS = 3` disparaît.** C'est une règle documentée du 2026-10-03
(`docs/RUNNER.md`, plan) : l'amendement doit être écrit, pas silencieux.

**Où vit cette politique.** Dans `dialogforge_runner` (une fonction `implement(run, …)` dans le cœur),
et non plus dans `runner_session._run_calls`. La CLI et la GUI ont alors le même comportement, et le
code quitte le périmètre façade + GUI, qui est à son plafond.

---

## 4. La remise dans `code/`

### 4.1 Deux voies, un même chemin d'essai

| Voie | `code/` | Cible de l'acceptation |
|---|---|---|
| **Nouveau projet** | Le dépôt du projet lui-même (créé par `init_project`) | Sa branche initiale |
| **Dépôt existant** | Un **clone d'essai** géré par DialogForge, à partir de la base et des commits transportés | Le dépôt choisi par l'utilisateur, sur la branche enregistrée au départ (**ne jamais supposer `main`**) |

Le dépôt existant de l'utilisateur n'est donc jamais basculé ni modifié avant l'acceptation.

### 4.2 Remettre, automatiquement, sans jeton

1. Créer le bundle **à ce moment-là** et le copier dans `developpement/candidats/`. Aujourd'hui,
   `bundle_candidate()` exige que le clone soit encore à la tête du paquet : après une correction,
   un ancien candidat ne serait plus transportable. Créer le bundle à la remise lève ce défaut sans
   rien changer à `bundle_candidate`.
2. Copier le paquet dans `developpement/paquets/NNN` comme **trace** : diff, validations, bilan,
   revue B. Je reviens sur ma V1 et suis Astra : Git garde le code, pas les preuves ni leur lien au
   mandat. Le paquet reste, mais ce n'est plus une étape pour l'utilisateur.
3. Dans `code/`, faire `git fetch <bundle> HEAD:refs/heads/candidat/NNN`, puis **extraire** cette
   branche. Créer la branche ne suffit pas : la copie de travail doit correspondre au commit annoncé.
4. Si `code/` contient des changements de l'utilisateur, **ne rien extraire et ne rien écraser**.
   Afficher la situation et la commande à lancer.

Un numéro `NNN` correspond à **une version proposée à l'utilisateur**, pas à un appel ni à une
collecte.

### 4.3 Un résultat qu'on sait lancer

- A doit documenter **comment lancer** le résultat (section du README ou `LANCEMENT.md` dans le
  dépôt). Cela fait partie du mandat, et B le vérifie comme une exigence.
- **Le contrôle de démarrage est une validation ordinaire.** Si le projet en a besoin, l'utilisateur
  ajoute à la liste éditable existante une commande de démarrage rapide. Aucun mécanisme dédié.
- L'écran de remise affiche **l'environnement réellement vérifié** (« Ubuntu WSL, sous srt »). Des
  tests verts sous Ubuntu ne prouvent pas un lancement natif sous Windows, et l'écran ne doit pas le
  laisser croire.
- **Les dépendances restent hors contrat dans cette refonte.** Un projet qui exige `npm install` ou
  `pip install` finira en `OBSTACLE`, expliqué et reprenable. C'est honnête, mais c'est la **prochaine
  limite réelle** de l'objectif « aller au bout ». La décision (environnement préparé d'avance, ou
  registre de paquets autorisé à l'agent) viendra plus tard. **On n'ouvre pas silencieusement le
  réseau.**

---

## 5. Accepter et corriger

**Accepter cette version :**

1. Enregistrer la décision sur le **hash du commit essayé**.
2. Revérifier la cible : propre, sur la branche attendue, à la base attendue.
3. Faire avancer la cible par `merge --ff-only`. C'est `integrate_candidate`, sans l'exigence
   « revue documentaire acceptée ».
4. Écrire le reçu dans `developpement/integrations/`, comme aujourd'hui.

Si la cible a avancé ou contient des changements, il n'y a **aucune fusion silencieuse**. Le
candidat est conservé et l'écran dit quoi faire. Une fusion produirait un résultat jamais essayé.

Si la décision est enregistrée mais que la promotion échoue (crash, dépôt modifié), l'écran affiche
« accepté, intégration à terminer ». La reprise termine l'opération sans agent et sans jeton.
**Décision d'abord, effet ensuite, reçu à la fin** : c'est le seul « journal d'intention » nécessaire,
et il tient dans les fichiers qui existent déjà.

**Demander une correction :**

- La demande saisie et le candidat essayé sont enregistrés.
- Le tour suivant repart du même clone, dont la tête est le candidat. Il repasse par A, les
  validations et B, puis remet `candidat/NNN+1`.
- `candidat/NNN` et ses preuves restent consultables.
- Une demande qui **dépasse** la conception n'est pas une correction. Elle passe par une conception
  amendée et acceptée.

---

## 6. Jeton et autorisation

- **Une autorisation couvre tout le lancement** : appels de A et de B, validations et remise. Pas de
  confirmation à chaque tour.
- Le jeton reste **en mémoire du processus GUI** jusqu'à la fermeture de la fenêtre, avec un bouton
  « Oublier le jeton ». Il n'est jamais sur disque, jamais dans les références ni les preuves, et
  jamais dans l'environnement des validations (comme aujourd'hui).
- Une correction après essai réutilise le jeton s'il est encore en mémoire. Sinon, on le ressaisit,
  sans rien recréer d'autre.
- **Remise, acceptation et reprise locales n'exigent aucun jeton.**
- Si B passe un jour sur un autre outil, chacun aura son authentification : le jeton de A n'est pas
  présumé valoir pour B.

---

## 7. Le mandat et la conception

**Le mandat transmis à A (`development.export_files`) doit être réécrit pour le Runner.** Il dit
aujourd'hui que « DialogForge ne développe, ne teste, ne commit […] rien » et que « tout changement
de code exige […] une nouvelle collaboration ». Il contient aussi le schéma JSON des validations,
destiné à un développeur humain extérieur. On garde :

- la demande ;
- la conception acceptée ;
- les réserves et constats ouverts ;
- les validations prévues ;
- une consigne courte : réaliser **toute** la conception, la tester, documenter le lancement, fournir
  la table de couverture, terminer par la ligne de statut, s'arrêter et expliquer si une décision
  manque.

Les exports historiques restent intacts, et le développement assisté documentaire reste utilisable.

**Côté conception, on recommande sans exiger.** Une conception qui contient un court tableau de
recette (exigence, vérification) et nomme l'environnement cible donne à B un étalon plus net. Il faut
l'encourager dans le gabarit de conception, sans en faire une condition de lancement. Les conceptions
existantes, dont Mastermind, n'en ont pas : la table de couverture de A et la lecture intégrale par B
y suppléent. Une **réduction de périmètre proposée par A est une `QUESTION`**, jamais une réussite.

`lot.md` (livraison partielle choisie par l'utilisateur) reste possible. L'écran affiche alors « lot
livré, conception partiellement réalisée » et ne présente jamais un lot comme la conception entière.

---

## 8. Ce que je laisse de côté dans l'analyse d'Astra, et pourquoi

| Proposition d'Astra | Position | Motif |
|---|---|---|
| Aucune durée maximale garantie | **Écartée** | Le PO lance et part ; la durée totale est un paramètre utilisateur nommé, pas un quota interne (§3.3) |
| Enregistrer l'intention avant chaque effet, pour la remise comme pour la promotion | **Réduite** | Décision, puis effet, puis reçu suffisent avec les fichiers existants ; pas de mécanisme de journal |
| Contrôle de démarrage en copie jetable, avec arrêt piloté | **Réduite** | C'est une validation de la liste existante quand le projet en a besoin |
| Modes de remise (sources, construction locale, artefact construit) | **Différée** | Aucun projet actuel n'en a besoin ; à décider au premier qui en aura besoin |
| Référence de candidat reliant toutes les preuves | **Réduite** | Le paquet, le bundle, la branche et le reçu forment déjà ce lien ; un seul `candidats/NNN.json` de références, sans copier les contenus |
| 18 scénarios de démonstration | **Ramenés à 10** (§10) | Les autres sont des variantes ou relèvent de la recette humaine |
| Revue B qui dispose d'une copie complète en lecture seule | **Adoptée, plus simplement** | B lit le clone lui-même ; la vérification après l'appel garantit qu'il n'a rien écrit |

Le reste de l'analyse d'Astra est adopté : critère de fin, revue B directe, statut de fin d'appel,
politique dans le cœur, clone d'essai pour les dépôts existants, bundle à la remise, environnement
affiché, refus de toute fusion silencieuse, amendement explicite de la règle des trois appels.

---

## 9. Taille et lots

### 9.1 La contrainte

Façade + GUI : **2 698 lignes sur un plafond de 2 700**, avec un plafond ultérieur fixé à 3 000.
`src/` compte 9 131 lignes effectives (relevé du journal, à remesurer). Toute ligne ajoutée à la GUI
doit donc être compensée.

| Sort | Code |
|---|---|
| **Retiré du chemin GUI** | « Poursuivre : examiner le paquet » (`views/runner.py:156`, `:217-218`) ; « Intégrer ce candidat » et sa condition de revue (`views/suivi.py:106`, `:173-188`) ; `_run_calls` et `MAX_AGENT_CALLS` (`runner_session.py`) ; messages de reprise (`executions.py:279`) |
| **Retiré du chemin, conservé** | `delivery.create_review` et les fonctions associées, pour consulter les anciennes revues Mastermind. On les supprimera si aucune nouvelle revue documentaire de code n'est demandée |
| **Ajouté au cœur** (`dialogforge_runner`, hors plafond GUI) | `implement()` (boucle et arrêts du §3.3), appel de B et vérification après l'appel, lecture de la ligne de statut |
| **Ajouté à la façade** (`delivery.py`) | `deliver_candidate()` extrait d'`integrate_candidate` ; clone d'essai pour les dépôts existants |
| **Ajouté à la GUI** | Écran « Version NNN prête à essayer » avec trois boutons ; pause avec question ; jeton en mémoire |

Le solde GUI doit être négatif ou nul. **Sinon, c'est au PO de relever le plafond, pas au code de
le dépasser.**

### 9.2 Ordre

1. **Décisions du PO** (§11), puis amendement de `CLAUDE.md` §2, de la conception Runner V1, de
   `docs/RUNNER.md`, de `project/RULES.md` et de `conception/PARCOURS_MISSION_CONCEPTION.md`.
2. **Lot A — Remise et acceptation** (§4, §5). Il remplace le « lot 4 » du plan. Recette sans
   fournisseur : livrer le candidat Mastermind déjà produit sous `candidat/001` dans
   `Mastermind/code/`, puis l'essayer. **Comme le dit Astra, ce lot permet d'essayer, il ne garantit
   pas la conformité : il ne doit pas être présenté comme l'objectif atteint.**
3. **Lot B — Boucle de conformité** (§3) et mandat réécrit (§7). Recette Mastermind : **un appel de B
   sur le candidat existant**, explicite et lancé par le PO. S'il ne relève rien de bloquant, aucun
   nouvel appel de A n'est nécessaire.
4. **Lot C — Interfaces** : CLI `run` (boucle commune), pont WSL, écran unique « Implémentation »,
   jeton en mémoire. Les anciens paquets et revues restent consultables.
5. **Plus tard, sur décision** : dépendances (§4.3), B sur un autre outil, suppression de la revue
   documentaire de code.

---

## 10. Scénarios de test (agents `fake`, dépôts temporaires, aucun fournisseur)

| # | Scénario | Attendu |
|---|---|---|
| 1 | Conception réalisée, validations vertes, B `PRET` | `candidat/001` extrait dans `code/`, aucune collaboration créée |
| 2 | **Contre-exemple d'Astra** : commit hors sujet, validations vertes | B `CORRIGER`, nouveau tour ; jamais « prêt » |
| 3 | A répond `RESTE` avec un code de sortie 0 | Tour suivant ; 0 ne vaut pas « prêt » |
| 4 | Ligne de statut absente | Pause « résultat illisible » |
| 5 | Validation rouge, puis corrigée | Nouveau commit, validations et revue sur cette tête |
| 6 | Même arbre et mêmes échecs qu'un tour précédent | Pause « répétition », sans compteur |
| 7 | B écrit dans le clone | Erreur ; candidat refusé |
| 8 | Correction après essai | `candidat/002` issu de `001` ; `001` et ses preuves conservés |
| 9 | Acceptation alors que la cible a avancé ou est sale | Aucune fusion ; candidat conservé ; état « à terminer » reprenable sans jeton |
| 10 | Dépôt existant | Clone d'essai dans `code/` ; dépôt utilisateur intact jusqu'à l'acceptation |

La recette finale reste humaine : conception acceptée, un lancement, jeu essayé depuis `code/`,
correction demandée, version suivante, puis acceptation du commit essayé. Pour Mastermind, cela
inclut les scénarios navigateur C01–C22 de sa conception.

---

## 11. Décisions demandées au PO

1. **Contrat** : adopter le texte du §1, avec « déploiement » = résultat utilisable dans `code/`.
2. **Revue B dans le Runner**, sur le code, en lecture seule, même profil et même jeton que A, sur le
   modèle Fable 5 ; la revue documentaire de code n'est plus requise pour accepter.
3. **Ligne de statut de A** en fin d'appel (4 valeurs) ; une ligne absente provoque une pause.
4. **Arrêts du §3.3** ; suppression de la règle « trois appels » du 2026-10-03 ; **la durée totale
   saisie au lancement est la seule borne chiffrée**, nommée comme telle.
5. **Remise automatique** dans `code/` sur `candidat/NNN` avant décision ; clone d'essai pour un
   dépôt existant ; acceptation par fast-forward du commit essayé.
6. **Jeton en mémoire** jusqu'à la fermeture de la fenêtre, avec « Oublier le jeton ».
7. **Taille** : le solde façade + GUI des lots doit être nul ou négatif ; sinon, relèvement explicite
   du plafond par le PO.
8. **Dépendances** : hors contrat pour cette refonte (elles aboutissent à un `OBSTACLE` expliqué),
   avec une décision à prendre ensuite.

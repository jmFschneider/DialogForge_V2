# DialogForge — analyse et proposition pour une implémentation menée jusqu'au résultat

**Auteur : Astra — 4 octobre 2026.**

Analyse de `schema_dialogforge.md`, confrontée à la documentation, au code et à des essais locaux. Le document `schema_dialogforge_analyseOpus.md` n'a pas été lu. Les amendements proposés sont réunis ici ; ils ne constituent pas une décision du PO déjà acquise ni une modification de l'implémentation.

## 1. Le changement essentiel

**Le Runner doit terminer lorsque le résultat prévu par la conception est disponible et essayable, avec des éléments permettant de juger sa conformité. Aujourd'hui, il termine lorsqu'un commit passe les commandes de validation et produit un paquet.**

La rupture décrite dans le schéma est réelle. Mais supprimer l'écran de nouvelle revue ou déplacer le code dans `code/` ne suffira pas : ces changements pourraient rendre plus accessible une réalisation incomplète. Il faut modifier ensemble le critère de fin, la boucle de correction et la remise du candidat.

La cible que je recommande est :

```text
Conception acceptée, avec critères de recette et environnement cible
        ↓
Démarrer l'implémentation — une autorisation pour la réalisation convenue
        ↓
Agent A : réaliser, tester, documenter le lancement, committer
        ↓
Runner : exécuter les validations sur ce commit
        ↓
Agent B : examiner le code, la couverture de la conception et les preuves
        ├── défaut corrigeable dans le mandat → A corrige → validations → B
        ├── décision nécessaire / obstacle réel → pause expliquée
        └── candidat prêt pour la recette
                    ↓
Remise automatique dans code/, version identifiée, lancement vérifié
                    ↓
Utilisateur : essayer → accepter / demander une correction / arrêter
```

L'acceptation humaine reste nécessaire. Elle porte sur **le candidat exact que l'utilisateur a pu essayer**, avec ses éventuelles réserves, et non sur l'acceptation préalable d'un rapport documentaire.

## 2. Ce que fait réellement le code actuel

### 2.1 Périmètre observé

L'analyse porte sur l'arbre de travail du 4 octobre, qui comporte déjà des modifications non committées et de nouveaux modules. Le HEAD est `aae03468ebc8b7d14709f650b9b03b5860c07f7d` ; ce commit seul ne représente donc pas tout le code examiné.

Sources principales :

| Source | Élément vérifié |
|---|---|
| `schema_dialogforge.md` | Parcours souhaité et commentaires de Sonnet |
| `conception/DialogForge Runner V1 — conception simplifiée.md` | Contrat initial : un lot, un candidat vérifié, puis revue documentaire et intégration extérieure |
| `docs/RUNNER.md`, `project/RULES.md`, `POURQUOI.md` | Parcours en vigueur, limites de l'autonomie, reprise et simplicité attendue |
| `src/dialogforge_runner/core.py` | Préparation, mandat, appel agent, collecte, identification du commit et bundle |
| `src/iabinome/gui/runner_session.py` | Autorisation du lancement, jeton et corrections automatiques |
| `src/iabinome/development.py` | Export de conception, paquet et demande de revue |
| `src/iabinome/delivery.py` | Copie du paquet, nouvelle collaboration de revue, intégration |
| `src/iabinome/executions.py` | Référence de l'exécution et contrôle de la conception exportée |
| Plan `.planning/2026-09-18-dialogforge-v2/` | Contexte des travaux récents et observations consignées sur Mastermind |

Je n'ai pas ouvert ni exécuté le projet réel Mastermind. Les observations sur ses appels et ses tests proviennent du schéma et du journal de projet ; elles ne constituent pas une nouvelle recette du jeu.

### 2.2 Les acquis à conserver

Le socle réalise déjà plusieurs choses utiles :

- export d'une conception dont l'acceptation est applicable, avec la demande, les réserves et les objections ouvertes ;
- développement dans un clone indépendant, sans remote, séparé du dépôt source ;
- validations rattachées à un commit précis, avec refus si les fichiers suivis ou le HEAD changent pendant la collecte ;
- conservation des appels, des échecs et des paquets antérieurs ;
- transport Git, contrôle des identités et intégration en fast-forward ;
- reprise par lecture des artefacts, avec paramètres non secrets ;
- distinction entre dernier paquet réussi et tentative ultérieure échouée.

Ce socle doit être réemployé. Une réécriture générale augmenterait le travail sans résoudre davantage le besoin.

### 2.3 Les écarts avec l'objectif

| Point | Comportement observé | Conséquence |
|---|---|---|
| Critère de fin | `run_agent()` collecte après une sortie technique normale ; `_collect_locked()` produit le paquet lorsque les commandes réussissent | Aucune décision explicite sur la réalisation complète du mandat |
| Bilan incomplet | Le prompt demande à A d'expliquer les travaux incomplets ou les arbitrages dans sa réponse finale | Ces mentions ne deviennent pas un état exploitable ; elles peuvent accompagner un paquet réussi |
| Corrections | `RunnerSession._run_calls()` autorise jusqu'à trois appels, uniquement après `ValidationFailed` | Une fonctionnalité oubliée avec tests verts n'entraîne aucune correction automatique |
| CLI et GUI | La boucle de ces corrections est dans la session GUI ; `run-claude` appelle le cœur directement | Le comportement autonome dépend de la surface de lancement |
| Revue | `delivery.create_review()` crée une collaboration de type `RECHERCHE`, avec A qui écrit un rapport et B qui le critique | L'utilisateur retrouve réellement le cycle documentaire, pas une revue directe de l'implémentation |
| Accès au résultat | `integrate_candidate()` attend l'acceptation de cette revue pour avancer le dépôt cible | `code/` ne reçoit le candidat qu'après cette décision |
| Contexte de revue | Le paquet contient le diff et les fichiers modifiés | Sur un dépôt existant, ce n'est pas tout le contexte nécessaire pour examiner les interactions |
| Environnement | La préparation n'installe pas les dépendances ; les validations WSL s'exécutent avec réseau refusé | Copier les sources dans `code/` ne suffit pas à garantir un résultat lançable sur Windows |
| Autorisation et jeton | Le jeton est déjà réutilisé pour les corrections d'un lancement, puis effacé | La continuité existe partiellement ; il faut l'étendre au parcours complet |
| Historique du candidat | `bundle_candidate()` exige actuellement que le clone soit encore sur la tête du paquet | Transporter un ancien candidat après une correction ultérieure peut devenir impossible sans bundle déjà conservé |

Un autre point doit être amendé : `development.export_files()` insère encore dans le mandat que DialogForge « ne développe, ne teste, ne commit […] rien » et que chaque correction exige une nouvelle collaboration. C'est hérité du développement assisté documentaire. Ces consignes doivent être adaptées au parcours Runner, sans réécrire les exports historiques.

### 2.4 Vérification effectuée pour cette analyse

Commande exécutée, sans fournisseur :

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runner.py tests/test_delivery.py -q
```

Résultat : **16 tests réussis, 3 sous-tests réussis**, en 17,62 secondes. Ces tests confirment les mécanismes actuels de collecte et de livraison ; ils ne démontrent pas la conformité fonctionnelle d'une application.

Contre-exemple exécuté sur un dépôt temporaire, en réutilisant la fixture de `test_runner.py` :

1. Mandat : « Modifier code.txt ».
2. Création d'un commit ajoutant seulement un README ; `code.txt` reste inchangé.
3. Validation technique configurée : une commande qui affiche `ok` et retourne zéro.
4. Collecte par le vrai `core.collect()`.
5. Résultat : paquet créé, état `paquet`, alors que le mandat n'a pas été réalisé.

Ce résultat ne signifie pas que tous les candidats actuels sont incomplets. Il montre précisément que **le succès du paquet ne permet pas de conclure à l'accomplissement de la conception**. C'est le contrat à compléter.

## 3. Amendements aux propositions de Sonnet

| Proposition | Position et amendement recommandé |
|---|---|
| Distinguer l'existant et la cible | À retenir. Distinguer aussi les orientations demandées, les choix techniques proposés et les décisions formellement adoptées. |
| Un seul lancement autorise le parcours | À retenir. Il couvre les corrections nécessaires au mandat, la revue technique et la remise locale. Les effets autorisés et les prérequis doivent être connus au départ. |
| Arrêt après le même échec deux fois ou aucun diff utile | À reformuler : ce sont des indices, pas des preuves suffisantes de non-progression. Un test peut rester rouge pendant plusieurs corrections utiles ; une investigation peut produire une information sans modifier le code. |
| B critique, A corrige dans le Runner | À retenir. B doit examiner directement le candidat et les preuves, en ayant accès au contexte du dépôt. La dernière version modifiée doit repasser par les contrôles et la revue. |
| Branche `candidat/001` dans `code/` | À retenir pour un espace d'essai géré par DialogForge, en précisant quelle branche est effectivement extraite, quelle branche sera acceptée et comment protéger les modifications de l'utilisateur. |
| Acceptation = fusion | À préciser : promotion du commit essayé vers la branche cible par fast-forward. Une résolution de conflit ou une fusion modifiant le résultat crée un nouveau candidat à valider et à essayer. |
| Correction = nouvelle branche candidate | À retenir pour identifier les versions présentées, mais la correction repart du candidat précédent. Pas de recréation de conception ni de perte du travail déjà livré. |
| Plus de paquets figés | À écarter pour cette évolution. Git conserve le code ; il ne conserve pas automatiquement les sorties des validations, la revue et leurs liens avec le mandat. Garder les paquets comme artefacts internes, sans étape utilisateur obligatoire. |
| Décision écrite avant code | À retenir pour l'extension de périmètre. La présente analyse prépare cette décision ; elle n'autorise pas à inventer un accord du PO sur les détails. |

**Nuance sur les plafonds :** le projet interdit les budgets et quotas internes génériques, mais sa règle datée du 3 octobre autorise déjà jusqu'à trois appels pour corriger les validations d'un lancement GUI. Cette limite est donc une règle existante à amender explicitement. La supprimer en silence, ou la présenter comme inexistante, serait incorrect.

## 4. Définir « délivrer ce que prévoit la conception »

### 4.1 Un mandat complet et une recette identifiable

La conception acceptée doit permettre de répondre à quatre questions :

1. Quel résultat l'utilisateur doit-il pouvoir obtenir ?
2. Quels comportements et contraintes sont obligatoires ?
3. Dans quel environnement doit-il pouvoir le lancer ?
4. Comment chaque point important sera-t-il vérifié ?

Les critères peuvent rester dans le document de conception. Des identifiants courts et un tableau de recette suffisent ; il n'est pas nécessaire d'introduire un langage de spécification.

Pour les conceptions existantes sans tableau explicite, A peut préparer une correspondance entre les exigences du document et les vérifications. B la confronte au document intégral pour relever les oublis. **Cette correspondance ne remplace pas la conception et ne permet pas d'en réduire le périmètre.** Une ambiguïté métier réelle demande une réponse humaine ; une simple reformulation technique n'impose pas un nouveau cycle de conception.

Exemple de contenu attendu, à adapter au projet :

| Exigence et référence dans la conception | Réalisation | Vérification ou preuve | Situation |
|---|---|---|---|
| Règle du jeu décrite au §X | Module concerné | Tests nommés et résultat sur le commit candidat | Vérifiée automatiquement |
| Interaction utilisateur décrite au §Y | Vue et commande concernées | Scénario de recette, résultat automatisé si disponible | À confirmer lors de l'essai utilisateur |
| Démarrage sur l'environnement convenu | Point d'entrée et dépendances | Commande de lancement et essai de démarrage | Vérifié dans l'environnement indiqué |
| Réserve acceptée sur la conception | Traitement ou limite explicite | Constat repris et preuve associée | Résolue ou réserve persistante |

Une validation de syntaxe, un `git --version` ou des tests unitaires ne couvrant qu'un module ne peuvent pas justifier à eux seuls l'achèvement du projet. Les commandes restent nécessaires ; B doit aussi apprécier leur rapport avec les exigences.

### 4.2 Conception entière et lot partiel

Le mode normal demandé est la réalisation de **toute la conception acceptée**. A peut organiser librement plusieurs étapes et commits à l'intérieur du lancement. Le Runner n'a pas besoin de lire les cases PWF ni de piloter une tâche à la fois.

Le mécanisme `lot.md` peut rester disponible lorsque l'utilisateur choisit explicitement une livraison partielle. Dans ce cas, l'écran indique « lot livré, conception partiellement réalisée », avec les éléments reportés. Une fin de lot ne doit jamais être présentée comme la réalisation de toute la conception.

Une réduction de périmètre proposée par l'agent reste une demande de décision. Elle n'est pas transformée automatiquement en réussite parce que les tests du sous-ensemble passent.

### 4.3 Condition de remise normale

Le candidat peut être présenté comme **prêt à essayer** lorsque :

- le mandat est identifié et toujours applicable ;
- les exigences obligatoires ont une réalisation identifiée ; aucun manque connu n'est masqué ;
- les validations requises ont effectivement été exécutées sur la version remise ;
- B a examiné cette version et ne relève plus d'écart bloquant à la conception ;
- les réserves et vérifications restant humaines sont visibles ;
- le candidat complet est présent dans l'espace d'essai, avec ses prérequis et une procédure de lancement vérifiée au niveau convenu.

Un critère destiné à la recette humaine peut rester « à essayer » : c'est précisément la raison de la remise. Un comportement obligatoire connu comme absent ne peut pas être déguisé en recette humaine restante.

Une livraison partielle ou affectée d'un obstacle peut être ouverte à l'utilisateur pour diagnostic, mais doit rester identifiée comme telle. L'acceptation avec réserves, si conservée, est une décision explicite et versionnée, sans effacement des manques.

## 5. Une boucle autonome courte, placée dans le Runner

### 5.1 Responsabilités

**A développe** : il organise son travail, modifie le code, ajoute les tests utiles, explique la couverture du mandat et les limites. Il peut corriger plusieurs problèmes dans un même appel.

**Le Runner exécute les contrôles et assure la continuité** : il appelle A ou B selon le résultat observé, conserve les versions et les traces, transporte le candidat et décide de la prochaine action permise. Il ne prétend pas déduire la qualité fonctionnelle du code par un parseur de prose.

**B examine directement l'implémentation** : mandat complet, réserves, code au commit précis, diff et preuves. Il relève les omissions, les régressions et les tests insuffisants. Pour un dépôt existant, une copie complète en lecture seule ou un accès équivalent au commit est nécessaire ; le diff seul ne suffit pas.

Le premier rôle de B est la revue. Les tests sont lancés par le Runner dans l'environnement prévu ; donner à B des capacités d'exécution supplémentaires serait une extension distincte à qualifier.

La boucle doit être commune à la CLI et à la GUI, dans `dialogforge_runner`. La GUI affiche sa progression et transmet les demandes de pause. Elle ne possède plus sa propre politique de corrections.

### 5.2 Un résultat final exploitable, sans protocole par tâche

Le bilan libre d'A est conservé. Il faut lui adjoindre un petit résultat de fin d'appel, permettant de distinguer :

- candidat proposé pour vérification ;
- travail restant dans le mandat ;
- question nécessitant une décision ;
- obstacle empêchant la poursuite.

Le résultat comporte le commit concerné lorsqu'il existe, les références des points restants et, en cas de pause, le motif précis. Une prose contenant « il reste… » ne suffit plus à piloter correctement le parcours.

Le retour de B distingue de même un candidat prêt pour recette, des corrections demandées et un arbitrage nécessaire. Réutiliser les contrats et dispositions d'objections existants lorsque leur sens correspond ; adapter les prompts à une revue du code. **Ne pas lancer A pour rédiger un rapport documentaire que B relira ensuite.**

Un résultat manquant ou illisible ne vaut jamais validation. Si la sortie brute a été conservée, tenter d'abord son retraitement local. Un retour de processus zéro ne se substitue pas à ce résultat métier.

Cette extension porte sur la fin des appels, pas sur chacune des opérations internes de l'agent. Elle ne justifie ni planificateur de tâches, ni worker, ni nouvelle base de données.

### 5.3 Corrections et nouvelle validation

| Événement | Suite proposée |
|---|---|
| Test échoué à cause du code | A reçoit la commande, l'échec et les traces utiles ; il corrige dans le même mandat |
| Tests verts, exigence oubliée relevée par B | A réalise le point manquant, puis nouveaux contrôles et nouvelle revue |
| Travail partiel, suite claire dans le mandat | Continuation automatique avec le travail restant explicite |
| Objection contestée par A | B réexamine la justification ; désaccord métier ou absence de résolution → arbitrage visible |
| Sortie technique interrompue ou résultat incertain | Examiner d'abord les artefacts ; pas de rejeu payant aveugle |
| Authentification refusée, outil indispensable absent, accès refusé | Pause avec cause et moyen de reprise ; pas de boucle d'appels de correction du code |
| Candidat prêt et remis | Arrêt des appels ; attente de l'essai utilisateur |

Les consignes de correction distinguent une correction issue des tests, une objection de B et une demande de l'utilisateur. Une correction automatique ne doit pas être inscrite dans le prompt comme une « demande de l'utilisateur » qu'il n'a pas faite.

Une modification après la dernière revue retire à cette version son statut « prête à essayer ». Les tests et B doivent porter sur le commit finalement remis, y compris si la modification concernait les instructions de lancement. Il n'y a pas de réécriture finale par A après le feu vert de B.

### 5.4 Non-progression et délais

Je ne recommande pas l'arrêt mécanique « même erreur deux fois ». Exemple : le même scénario d'intégration peut rester rouge pendant que deux dépendances sont réparées successivement. Inversement, créer des commits de mise en forme ne prouve aucune progression.

Utiliser les artefacts déjà disponibles : changements pertinents, points de recette couverts, objections résolues, résultats des validations et informations diagnostiques nouvelles. Lorsque le même obstacle revient sans progrès vérifiable et sans nouvelle tentative justifiée dans le mandat, le Runner passe en pause avec l'historique utile et le motif.

Le logiciel peut constater une répétition stricte de la même situation. L'appréciation d'un progrès fonctionnel relève de la revue, étayée par les preuves. Aucun score de progression ni moteur général de « stratégies de réparation » n'est nécessaire.

**Une telle politique ne garantit pas une durée maximale.** Un modèle peut produire une succession de changements inutiles que les contrôles distinguent mal. Il faut assumer cette limite : interruption utilisateur toujours disponible et délais techniques explicites. Si une borne globale est voulue par le PO, elle doit être nommée comme telle et décidée, pas dissimulée dans un compteur de répétitions.

Le délai d'un appel ou d'une commande sert à arrêter un processus qui ne termine pas ; l'expiration entraîne un état reprenable, jamais une livraison déclarée complète. Ne pas confondre ce délai avec la quantité de travail restant à réaliser.

## 6. Livrer un candidat utilisable dans `code/`

### 6.1 Définir l'espace d'essai

Pour **un projet neuf**, `mission/code/` est le dépôt d'essai géré par DialogForge. Avant la décision humaine, il contient le candidat sur une branche nommée, par exemple `candidat/001`. La branche de référence acceptée reste à sa base précédente.

Pour **un dépôt existant**, je recommande de matérialiser le candidat dans un clone d'essai géré dans `mission/code/`, à partir de la base et des commits transportés. Le dépôt source choisi par l'utilisateur reste sa cible d'intégration. Cela évite de basculer automatiquement la branche de son espace de travail, qui peut déjà servir à autre chose.

Ces deux voies donnent le même résultat visible : un chemin d'essai stable. Le mode choisi, le dépôt cible, sa branche et son commit de base sont enregistrés au départ. Ne pas supposer que la branche s'appelle `main`.

Une simple création de branche ne suffit pas : la copie de travail ouverte dans `code/` doit effectivement correspondre à cette branche et au commit annoncé.

### 6.2 Séparer les deux effets Git

**Remettre pour essai** : importer le candidat exact et l'extraire dans `code/`, automatiquement dans le lancement autorisé. Cette opération n'accepte pas la version et ne déplace pas la branche cible acceptée.

**Accepter** : enregistrer la décision humaine sur ce candidat, puis avancer la branche cible par fast-forward vers ce même commit lorsque les conditions sont réunies. Le bouton peut s'intituler « Accepter cette version », avec cet effet annoncé dès le lancement. Il n'est pas nécessaire d'imposer une seconde acceptation d'un rapport.

Avant la promotion, revérifier la branche cible et sa base attendue. Si elle a avancé, ou si son espace de travail contient des changements incompatibles, conserver le candidat et demander une résolution précise. Ne pas fusionner silencieusement : le résultat combiné n'a pas été essayé.

Si la décision est enregistrée mais que la promotion échoue, afficher « candidat accepté, intégration à terminer ». La reprise termine l'opération locale sans appeler A ou B. Acceptation et réussite de l'opération Git sont deux faits distincts.

### 6.3 Ce qu'une livraison doit contenir

Le résultat visible comprend :

- les sources complètes au commit annoncé ;
- le point d'entrée et les commandes exactes pour lancer et arrêter le programme ;
- les dépendances ou artefacts de construction nécessaires, avec une procédure reproductible ;
- le résultat du contrôle de démarrage, dans un environnement nommé ;
- une courte fiche de recette utilisateur et les limites connues ;
- l'identité de la version, accessible sans devoir comprendre les paquets.

**L'environnement de développement WSL et l'environnement d'essai utilisateur doivent être distingués.** Des tests passés sous Ubuntu ne prouvent pas un lancement natif Windows. Pour Mastermind, la commande ou le fichier à ouvrir dans le navigateur et les scénarios à essayer doivent être fournis ; le seul nombre de tests ne suffit pas.

Il faut convenir dans la conception du mode de remise : sources et lancement direct, construction locale, ou artefact construit. Un environnement virtuel Linux ne se copie pas comme environnement Windows. Les fichiers ignorés présents seulement dans le clone ne doivent pas rendre artificiellement réussi un démarrage impossible depuis la livraison.

Les commandes de construction ou de démarrage susceptibles de générer des fichiers sont séparées des validations qui exigent des sources propres. Un test de démarrage peut tourner dans une copie jetable avec sorties dédiées, être arrêté par le Runner et produire une preuve. L'essai interactif long est lancé à la demande de l'utilisateur, avec une action d'arrêt ; aucun service permanent n'est nécessaire.

L'installation des dépendances est aujourd'hui hors contrat. Pour tenir le lancement unique sur des projets qui en ont besoin, la préparation doit soit disposer d'un environnement prêt, soit utiliser une procédure explicitement prévue et autorisée au départ. **Ne pas ouvrir silencieusement le réseau des validations pour résoudre ce manque.** Si un prérequis exige réellement une installation extérieure non prévue, le Runner explique l'obstacle et conserve son travail.

### 6.4 Corrections après essai

« Demander une correction » enregistre le défaut décrit et le candidat essayé. La correction repart de cette version dans le clone de travail, puis repasse par les validations et B. Une nouvelle version, par exemple `candidat/002`, est remise dans `code/`. `candidat/001` et ses preuves restent consultables.

Une nouvelle branche correspond à une **version proposée à l'utilisateur**, pas à chaque appel agent ni à chaque collecte. Une revalidation du même commit peut produire une nouvelle preuve sans créer une fausse nouvelle version de code.

Si l'utilisateur a modifié des sources dans `code/`, aucun remplacement automatique ne les efface. Il faut les conserver et choisir explicitement leur traitement. Si elles sont incorporées, elles créent un nouveau candidat à contrôler. Les fichiers ignorés nécessaires au fonctionnement doivent également être pris en compte dans la recette ; « Git propre » ne signifie pas « environnement reproductible ».

Une demande ajoutant une fonction au-delà du mandat revient à une conception amendée et acceptée. Une correction pour satisfaire le mandat reste dans la même implémentation.

## 7. Versions, reprise et authentification

### 7.1 Garder des faits, éviter plusieurs états concurrents

Conserver `mission.json` comme registre de navigation. La conception garde ses décisions ; le Runner garde ses appels et résultats ; la livraison garde les références des candidats et les décisions d'essai. L'écran calcule la situation à partir de ces pièces.

Une référence de candidat doit relier au minimum :

- la conception et son export accepté ;
- la base du développement, le commit candidat et le candidat précédent éventuel ;
- les validations et la revue qui s'appliquent à ce commit ;
- l'emplacement d'essai et l'environnement effectivement vérifié ;
- la cible de promotion, la décision humaine et son résultat local lorsqu'ils existent.

Éviter de dupliquer le contenu déjà dans le paquet : référencer ses pièces. Un nom de branche est pratique pour naviguer, mais la décision est attachée au hash du commit et aux preuves correspondantes.

Conserver le bundle du candidat au moment de sa remise, pendant que cette version est encore disponible, ou permettre sa création depuis une référence Git conservée indépendamment du HEAD courant. Le contrôle actuel de `bundle_candidate()` doit donc évoluer pour permettre de retrouver un candidat antérieur après correction.

La reprise identifie aussi l'exécution **liée au candidat**, pas simplement la dernière exécution trouvée pour la conception. Plusieurs corrections ou une nouvelle préparation ne doivent pas rendre une ancienne décision ambiguë.

### 7.2 Reprendre les opérations inachevées

La remise et la promotion comprennent plusieurs écritures : import Git, branche, extraction, contrôle et reçu. Un crash peut se produire entre elles. Enregistrer l'intention avec ses identités avant les effets, puis le résultat, permet de constater ce qui est déjà fait et d'achever seulement ce qui manque.

Cela reste un mécanisme local et limité à l'opération, pas un journal universel de toutes les actions de l'agent. Les verrous existants doivent empêcher deux remises ou promotions concurrentes ; le dépôt est revérifié juste avant une mutation.

La réouverture lit les artefacts et affiche une action exacte : reprendre le travail, répondre à la question, terminer la copie locale ou essayer la version prête. Elle ne rejoue aucun appel fournisseur automatiquement.

Un candidat ayant franchi les contrôles doit pouvoir finir sa remise locale après interruption **sans dépendre du jeton fournisseur**.

### 7.3 Autorisation et authentification

Le lancement autorise les appels nécessaires de développement et de revue pour ce mandat, ainsi que la remise dans l'espace prévu. Cette autorisation reste valable pendant son exécution ; il n'y a pas de nouvelle confirmation à chaque contrôle.

Les identifiants restent en mémoire pour cette session, transmis uniquement aux adaptateurs concernés. Ils ne figurent ni dans les références d'exécution, ni dans les preuves, ni dans l'environnement des tests. Si A et B utilisent des outils différents, chacun utilise son mécanisme d'authentification ; le jeton de A n'est pas supposé convenir à B.

Après fermeture de l'application, une nouvelle authentification peut être nécessaire selon l'outil. Elle ne recrée ni le clone, ni le mandat, ni la collaboration. Une erreur 401 ou un quota fournisseur est un incident à afficher, pas une invitation à répéter automatiquement l'appel.

Le contrat de revue reste indépendant du fournisseur. Le développement actuellement raccordé utilise Claude sous WSL ; la refonte ne doit pas prétendre que d'autres profils de développement sont déjà qualifiés.

## 8. Parcours visible pour l'utilisateur

La mission présente **Recherche**, **Conception** et **Implémentation**. La recherche reste facultative. L'implémentation montre une suite d'événements lisibles : développement, tests, corrections, revue, remise, essai. Ce sont des étapes du même travail.

Pendant l'exécution : dernier travail effectué, problème en cours, pause et interruption. Éviter un pourcentage de complétude déduit du nombre d'appels : trois appels ne renseignent pas la part de conception réalisée.

À la livraison :

```text
Version 002 prête à essayer
Conception : version acceptée du …
Code : …/code/
Lancement : commande ou action adaptée au projet
Contrôles : résultats et environnement
À essayer : scénarios utilisateur
Réserves : liste explicite, ou aucune réserve connue

[Ouvrir le projet] [Lancer / voir les instructions]
[Accepter cette version] [Demander une correction] [Arrêter]
```

Les détails de Git, du paquet et de la revue restent accessibles. Ils ne constituent plus des passages obligatoires du parcours normal. Une pause affiche la question ou l'obstacle précis, avec le candidat conservé, au lieu de revenir à « Prête » ou à « Démarrer la collaboration ».

## 9. Mise en œuvre recommandée

Cette proposition de séquence devra être inscrite dans le plan existant une fois arbitrée. Elle ne crée pas un second suivi d'avancement.

| Ordre | Travail et points d'entrée | Résultat attendu |
|---|---|---|
| 1. Contrat | Amender la conception Runner, `docs/RUNNER.md` et les règles concernées ; définir recette, environnement, effets du lancement et acceptation | Une définition cohérente du résultat attendu et des exceptions autorisées |
| 2. Remise locale | Faire évoluer `delivery.py`, le bundle de `core.py` et les références d'exécution | Un candidat exact et lançable dans `code/` avant décision, versions antérieures conservées |
| 3. Boucle de conformité | Dans le Runner : résultat final d'A, revue directe de B, corrections et décisions de pause ; réemploi du transport et des contrats utiles | Les tests verts ne terminent plus le parcours si une exigence reste connue comme manquante |
| 4. Interfaces | CLI, pont WSL, `runner_session.py`, vues Runner et suivi | Même politique de progression, un lancement et une décision sur le résultat |
| 5. Recette et compatibilité | Scénarios ci-dessous et reprise d'une copie de mission réelle | Parcours démontré du lancement à l'essai, puis de la correction à l'acceptation |

Le lot de remise locale résout rapidement l'impossibilité d'essayer. **Il ne doit pas être présenté comme achevant l'objectif tant que la boucle de conformité n'est pas disponible.**

Amendements documentaires nécessaires : le tableau des interdits dans `CLAUDE.md`, les règles Runner dans `project/RULES.md`, la conception simplifiée et le parcours de mission. Retirer les instructions contradictoires du nouveau mandat Runner, tout en conservant les anciens exports intacts et le développement assisté documentaire utilisable.

À retirer ou remplacer dans le parcours Runner : la revue documentaire obligatoire après paquet, son acceptation intermédiaire, la règle imposant une nouvelle collaboration pour chaque correction et la boucle de trois appels propre à Tkinter. À conserver : clone, export, paquet, validations, transport, reprise et moteur documentaire des étapes amont.

La taille reste à mesurer. Le journal récent annonce façade + GUI à 2 698 lignes sur un plafond de 2 700 ; cette mesure n'a pas été recalculée ici. Déplacer la politique d'exécution dans le Runner répond à une responsabilité technique ; cela ne dispense pas de mesurer aussi la croissance totale de `src/` et d'obtenir un amendement de plafond si nécessaire.

### Reprise des travaux déjà produits

Ne supprimer ni les paquets Mastermind, ni le clone, ni les collaborations de revue déjà créées. Ils restent des éléments historiques consultables.

Sur une copie de la mission réelle, associer le candidat existant à son export et à ses validations, conserver son bundle, effectuer la revue et le contrôle de lancement manquants, puis vérifier la remise dans `code/`. Si le code satisfait le mandat, aucun nouvel appel de développement n'est utile. Les vérifications manquantes peuvent exiger un appel de revue ou une correction ciblée ; cela doit être explicite.

Le nombre d'anciens paquets ne devient pas un nombre de versions : plusieurs paquets portant le même commit sont distingués par leurs preuves, sans prétendre qu'ils représentent plusieurs implémentations.

## 10. Scénarios qui démontreront le résultat

Les essais automatisés utilisent des agents factices et des dépôts temporaires. Les essais réels d'application complètent ces contrôles techniques.

| Scénario | Résultat nécessaire |
|---|---|
| Petite conception entièrement réalisée | Un lancement mène au candidat dans `code/`, avec instructions et preuves ; aucune nouvelle collaboration à démarrer |
| Commit sans rapport avec le mandat, commandes vertes | Pas de livraison déclarée complète ; omission relevée et correction ou pause explicite |
| Une fonction obligatoire manque malgré les tests verts | B la relève ; A la réalise dans le même lancement |
| A déclare un travail restant avec retour technique zéro | La suite exploite ce résultat ; zéro ne devient pas « prêt » |
| Échec de test puis correction | Correction automatique autorisée, nouveau commit et validations correspondant à ce commit |
| Même erreur mais progrès démontré | Pas d'arrêt fondé uniquement sur le compteur de répétitions |
| Même obstacle, aucune progression et aucune nouvelle piste justifiée | Pause motivée, traces conservées, aucune fausse réussite |
| Correction après revue favorable | La nouvelle tête repasse par contrôles et revue avant remise |
| Dépôt existant avec interactions hors diff | B dispose du contexte complet ; le candidat est essayable sans déplacer la branche source |
| Dépendance ou fichier ignoré absent de la livraison | Le contrôle de lancement détecte l'absence ; aucun « prêt à essayer » trompeur |
| Tests WSL verts, démarrage cible en échec | Correction dans le mandat ou obstacle explicite ; environnement testé clairement indiqué |
| Essai puis demande de correction | Version suivante issue du candidat essayé ; ancienne version et décision conservées |
| Acceptation avec dépôt cible avancé | Aucune fusion silencieuse ; candidat conservé et intégration non déclarée réussie |
| Changement utilisateur dans `code/` | Aucun écrasement, acceptation de la version annoncée refusée tant que l'écart n'est pas traité |
| Crash pendant remise ou promotion | Réouverture et fin de l'opération locale, sans agent rappelé et sans doublon |
| Jeton expiré pendant une revue | Pause au bon endroit, candidat et tests conservés ; pas de jeton requis pour les opérations locales |
| Conception modifiée pendant le travail | Écart signalé ; aucune livraison présentée comme conforme à la nouvelle conception non exécutée |
| Reprise d'un ancien paquet | Transport du commit exact possible même si le clone a avancé |

La recette finale de cette évolution doit être une petite application réellement essayée : conception acceptée → un lancement → résultat accessible → correction demandée depuis l'essai → nouvelle version → acceptation du commit essayé. Pour Mastermind, les scénarios navigateur consignés dans sa conception doivent être exécutés et leurs résultats conservés.

## 11. Décision proposée au PO

Adopter le contrat suivant :

> Après acceptation de la conception, un lancement autorise le Runner à réaliser le périmètre convenu, contrôler sa couverture avec une revue technique, corriger les défauts traitables dans ce mandat et remettre une version utilisable dans l'espace d'essai. Les appels s'arrêtent sur une livraison prête pour recette, une interruption ou un obstacle expliqué. L'utilisateur essaie cette version, puis l'accepte ou demande une correction. L'acceptation et les preuves désignent exactement le candidat essayé.

Pour concrétiser ce contrat, je recommande les choix suivants : **revue B interne au Runner ; paquets conservés en arrière-plan ; `code/` utilisé comme espace d'essai identifié ; promotion locale par fast-forward à l'acceptation ; boucle commune CLI/GUI ; absence de plafond arbitraire de corrections, avec pauses justifiées et délais techniques explicites.**

Ces choix prolongent les acquis du Runner tout en changeant sa condition de réussite : il doit fournir le résultat utilisable prévu par la conception, accompagné des preuves et limites nécessaires à la décision humaine.

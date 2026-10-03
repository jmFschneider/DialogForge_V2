# DialogForge Runner V1 — conception simplifiée

> **Version corrigée — 2026-10-01**
>
> Rédigée à la demande du PO à partir de l'analyse de la première proposition.
> Ce document définit le périmètre proposé pour la V1 ; il ne constate pas son implémentation.
> La première version, `DialogForge Runner V1 — conception.md`, est conservée à côté pour référence.

## 1. Intention

DialogForge prépare une conception et permet déjà de transmettre un mandat de développement
avec `dev-export`, puis de constituer un paquet de revue avec `dev-package`.

Le Runner facilite le travail situé entre ces deux opérations :

> **Préparer, lancer, récupérer et vérifier le résultat.**

Il confie un lot à un agent de développement, laisse cet agent organiser son travail, puis
récupère un candidat Git et les résultats de validations exécutées sur ce candidat.

Il ne pilote pas chaque tâche du développement. Il ne choisit pas la prochaine étape du plan,
n'impose pas un appel par étape et n'organise pas les corrections intermédiaires.

Le résultat attendu est une petite conception transformée en candidat vérifié et en paquet
de revue, avec peu de manipulations humaines. La durée pendant laquelle l'agent travaille
seul n'est pas un critère de réussite.

## 2. Place dans DialogForge

```text
Conception acceptée
        ↓
dev-export + choix du lot
        ↓
Runner : préparation du dépôt et du mandat
        ↓
Agent : développement, tests, corrections, commits locaux
        ↓
Runner : récupération du candidat et validations finales
        ↓
dev-package
        ↓
Revue A/B habituelle et décision humaine
        ↓
Intégration du code hors Runner
```

Le moteur documentaire A/B reste indépendant. Il n'importe pas le Runner et ne développe
pas le projet cible. Le Runner utilise les contrats fichiers existants et ne crée pas un
second format de revue.

La V1 peut rester dans le même dépôt, sous un petit namespace `dialogforge_runner`, avec
un exécutable `dialogforge-run`. Cette séparation suffit ; aucun framework d'orchestration
n'est nécessaire.

Les règles actuelles du moteur documentaire restent applicables à ce moteur. Le présent
document décrit une extension séparée ; sa rédaction n'engage pas encore son développement.

## 3. Répartition des responsabilités

| Responsable | Travail pris en charge |
|---|---|
| Humain | Accepter la conception, choisir le lot, préparer l'environnement et décider de l'intégration |
| Runner | Préparer le passage de relais, lancer l'agent, conserver les traces, vérifier le candidat, exécuter les validations finales et construire le paquet |
| Agent | Lire le mandat, examiner le dépôt, organiser le travail, modifier le code, tester, corriger et créer les commits locaux |
| Revue A/B | Examiner le candidat au regard du mandat, de ses réserves et des preuves disponibles |

Le mandat définit ce qui est demandé. Git décrit les modifications réalisées. Les validations
décrivent ce qui a été exécuté et avec quel résultat. Le bilan de l'agent explique son travail,
ses limites et ses éventuels besoins d'arbitrage.

Le Runner ne prétend pas déduire la conformité fonctionnelle complète d'un code de sortie
ou d'une suite de tests réussie. Cette appréciation appartient à la revue et à l'humain.

## 4. Un lot confié en entier à l'agent

Un lot est une petite conception entière ou une partie explicitement choisie d'une conception
plus grande. Il doit pouvoir donner un candidat cohérent et vérifiable.

Le Runner ne découpe pas automatiquement les conceptions. Si plusieurs lots sont nécessaires,
l'humain choisit celui à réaliser et ses critères de fin avant le lancement.

Pour un lot partiel, un court fichier `lot.md` précise les éléments à réaliser et ceux reportés.
Il accompagne l'export intégral et sera inclus dans les notes du paquet de revue. La revue
pourra ainsi distinguer une réalisation volontairement partielle d'une omission.

Un lancement confie tout le lot à l'agent. Celui-ci peut réaliser de nombreuses opérations,
exécuter ses tests plusieurs fois et produire plusieurs commits pendant sa session.

Il n'y a pas de bootstrap séparé, de session fraîche obligatoire à chaque étape ou de nombre
maximal de tâches compté par le Runner. Une durée maximale borne l'appel.

### Place de PWF

L'agent peut utiliser PWF comme mémoire durable, conformément au passage de relais existant.
Il gère lui-même son plan, ses constats et son avancement.

Le Runner ne lit pas `Next Step`, ne modifie pas les cases du plan et ne synchronise pas ses
propres états avec les phases PWF. Aucun parseur PWF ni module de pilotage du plan n'est requis.
Les fichiers de travail restent disponibles pour une continuation explicite.

## 5. Préparer

La préparation reçoit seulement les informations utiles au lancement :

- le dossier produit par `dev-export` ;
- le dépôt source et le commit de départ ;
- le lot retenu, si l'export ne doit pas être réalisé en entier ;
- l'agent choisi, avec ses éventuels réglages de modèle ;
- les commandes de validation finales et leurs délais maximaux ;
- la durée maximale de l'appel de développement ;
- le dossier de sortie.

Les commandes de validation sont indiquées par l'humain à partir des commandes du projet.
Le Runner ne les invente pas. Elles sont enregistrées comme listes d'arguments, avec le dépôt
de travail pour répertoire courant. Un script du projet peut regrouper les contrôles nécessaires.

La préparation vérifie l'export avec le contrat existant, résout le commit de départ et crée
un clone local indépendant à cette révision, sans partage d'objets en écriture ni remote
configuré. Elle ne copie pas les modifications non committées du dépôt source.

Elle copie le mandat et les réglages dans le dossier d'exécution, puis indique où préparer
l'environnement de développement. Elle ne lance aucun agent et n'installe rien.

### Environnement prêt avant le lancement

Un clone ne contient pas nécessairement l'environnement Python, les dépendances JavaScript,
les fixtures locales ou les outils nécessaires aux tests.

La V1 pose donc une précondition explicite : **l'environnement du dépôt de travail est prêt
avant de lancer l'agent**. La préparation de cet environnement relève de l'humain ou des
scripts habituels du projet, exécutés explicitement.

Le Runner n'automatise ni l'installation des dépendances ni la copie d'un environnement virtuel.
Une dépendance manquante ou un prérequis inaccessible donne lieu à un arrêt expliqué.

### Un dossier simple

```text
run/
├── run.json             # entrées du lancement et commit de départ
├── input/
│   ├── export.md
│   ├── export.json
│   └── lot.md           # facultatif
├── workspace/           # clone de travail ; code et mémoire de l'agent
├── calls/               # consignes, sorties et incidents des appels
└── results/             # collectes successives : bilan, validations, paquet
```

`run.json` est un petit enregistrement des paramètres utilisés, pas un contrat générique de
permissions ni une copie du plan. Les entrées d'une exécution restent stables ; un changement
de mandat, de base ou de validations appelle une nouvelle préparation.

Les traces et résultats précédents sont conservés. Aucun journal d'étapes de développement
n'est tenu en parallèle de celui de l'agent.

## 6. Lancer

Le Runner transmet le mandat, le lot éventuel, l'emplacement du dépôt et les commandes de
validation à l'agent. Les consignes demandent de :

- réaliser le lot en respectant la conception et les conventions du projet ;
- organiser librement les étapes, les tests et les corrections intermédiaires ;
- créer les commits locaux nécessaires et terminer sur un candidat committé ;
- expliquer les changements, les limites et les éléments non réalisés dans un bilan ;
- s'arrêter si une décision dépasse le mandat ou si un prérequis manque.

L'agent peut créer les commits. Il n'y a donc ni interdiction de déplacer `HEAD` pendant son
travail ni contrôle de chaque référence avant et après chaque opération.

Le Runner conserve les consignes, les sorties de l'appel, son résultat technique et les
incidents. Il réutilise autant que possible le transport existant pour les délais, la capture
des sorties et l'arrêt des processus.

La session suit le fonctionnement de l'outil intégré. Une session persistante peut être
utilisée si elle est disponible, sans constituer une condition de reprise du Runner.

Il n'y a pas de protocole `STEP_RESULT` par tâche. Le bilan final reste une pièce déclarative :
il indique ce que l'agent estime terminé et ce qui reste à faire. Un retour technique normal
déclenche la collecte, pas une déclaration de conformité de toute la conception.

## 7. Récupérer et vérifier le résultat

La collecte commence après la fin de l'appel et l'arrêt de ses processus. Elle peut aussi
être demandée séparément, sans payer un nouvel appel à l'agent.

### Identifier le candidat

Le Runner relève la tête Git et vérifie que le travail destiné à la revue est committé.
L'index et les fichiers suivis doivent être propres ; les fichiers non suivis non ignorés
doivent être traités avant la collecte. Les fichiers locaux de mémoire et de test peuvent
être explicitement exclus du candidat par les conventions du dépôt.

La base enregistrée doit appartenir à l'historique du candidat. Les incohérences Git ou
l'absence d'un candidat committé entraînent un arrêt expliqué, sans commit automatique destiné
à masquer la situation.

### Valider le commit qui sera livré

L'ordre est fixé :

```text
Candidat committé et espace de travail propre
        ↓
Enregistrement de head_oid
        ↓
Exécution des validations finales
        ↓
Vérification : même HEAD et espace toujours propre
        ↓
Construction du paquet pour ce head_oid
```

Les tests intermédiaires exécutés par l'agent l'aident à développer. Les validations finales
exécutées par le Runner servent de preuves pour le paquet.

Chaque résultat conserve la commande, les dates, le code de sortie, les sorties utiles et
le `head_oid` concerné, dans le format déjà accepté par `development.py`.

Une validation qui modifie le candidat invalide la collecte. On ne rattache pas rétroactivement
ses résultats à un nouveau commit. Une correction exige un nouveau candidat et de nouvelles
validations. Les fichiers temporaires ignorés par Git ne modifient pas le candidat.

Si une validation requise échoue, manque ou dépasse son délai, les résultats sont conservés
et l'exécution s'arrête avec les logs. La V1 ne déclenche pas une boucle externe de réparation.
Une absence de validation ne vaut jamais réussite.

### Construire le paquet

Lorsque les validations requises réussissent et que le candidat est inchangé, le Runner
appelle la fonction existante de `dev-package` avec :

- l'export d'origine ;
- le dépôt de travail, `base_oid` et `head_oid` ;
- les résultats des validations finales ;
- le bilan de l'agent et le périmètre du lot, comme notes du développeur.

Le paquet est créé hors du dépôt de travail. Chaque nouvelle collecte conserve ses propres
résultats et ne modifie aucun paquet déjà publié.

Le résultat est annoncé comme **candidat vérifié, prêt à examiner**. Un bilan signalant du
travail incomplet ou une demande d'arbitrage reste visible ; des tests verts ne l'effacent pas.

La revue A/B et `dev-verify` suivent ensuite le parcours existant. Le Runner ne fusionne,
ne publie et ne déploie rien.

## 8. Interruptions et continuation

Une interruption conserve le dépôt, les commits, les fichiers non committés, le plan éventuel
et les traces disponibles. Aucun nettoyage destructif ni retour automatique au commit de
départ n'est effectué.

Le Runner ne relance jamais automatiquement un appel interrompu. L'humain peut examiner
le travail, poursuivre avec son agent habituel ou demander explicitement une continuation.

Une continuation est un nouvel appel sur le même dépôt avec le mandat initial, l'état Git,
le bilan précédent et les éventuelles précisions humaines. L'agent examine le travail présent
avant de continuer. Il ne reçoit pas l'ordre de rejouer aveuglément la tâche interrompue.

Une session fournisseur peut être reprise si cela est simple, mais une nouvelle session
doit pouvoir relire les fichiers disponibles. La V1 ne promet pas une reprise automatique
au point exact d'une opération interrompue.

Si seul l'empaquetage a échoué, ou si un candidat a été terminé manuellement, une collecte
séparée permet de relancer les validations et de construire le paquet sans rappeler l'agent.

Un verrou d'exécution empêche deux commandes Runner de travailler simultanément dans le même
dossier. La V1 ne crée pas de machine à états détaillée pour les tâches de développement.

## 9. Protections et limites réelles

Le clone indépendant sépare le candidat du dépôt source. **Ce n'est pas une isolation de la
machine.** La suppression du remote réduit les risques Git accidentels, sans constituer une
interdiction réseau.

La V1 s'appuie sur les protections de l'environnement d'exécution choisi et documente ce
qu'elles assurent réellement. Elle ne développe pas un système générique de confinement.
Les traces et les réglages du Runner doivent rester hors des zones d'écriture de l'agent
lorsque l'environnement permet cette restriction.

Les validations exécutent du code potentiellement modifié par l'agent : elles doivent
bénéficier des mêmes restrictions que lui. Les lancer sans restriction sur l'hôte après un
appel confiné ne convient pas.

L'exécution ne reçoit pas volontairement de secrets applicatifs, d'identifiants de production
ou de moyens d'accès au matériel réel. Les politiques d'environnement existantes sont
réutilisées quand elles conviennent. Retirer des variables ne garantit toutefois pas
l'absence de credentials accessibles ailleurs sur le disque.

L'accès nécessaire au service du modèle est distingué de l'accès réseau des commandes de
l'agent et des tests. Un simple réglage `network=false` ne constitue pas une preuve de fermeture.

Pour les premiers essais, un petit dépôt et un environnement dédié, sans accès sensible,
suffisent à réduire le périmètre à examiner. Si le besoin impose une forte isolation sans
surveillance, celle-ci doit être fournie et vérifiée dans cet environnement avant cet usage.
La V1 ne promet pas « aucun effet possible hors du dossier » sur un poste ordinaire.

Les listes génériques de chemins interdits, le plafond de fichiers modifiés et la détection
universelle des changements de dépendances sont reportés. Les contraintes fonctionnelles
restent dans le mandat et sont examinées lors de la revue ; elles ne sont pas présentées
comme des protections techniques.

## 10. Surface CLI proposée

Trois opérations suffisent :

```text
dialogforge-run prepare ...
dialogforge-run run <run>
dialogforge-run collect <run>
```

`prepare` prépare le dossier et le clone, sans appeler d'agent. Les entrées sont celles du
§5 ; la syntaxe détaillée des options sera fixée avec la première intégration.

`run` lance l'agent puis enchaîne normalement la collecte. Après un premier appel, une option
explicite `--continue` permet un nouvel appel ; `--instruction <fichier>` peut apporter une
clarification dans le lot existant. La commande annonce qu'elle peut consommer le quota du
fournisseur. Une exécution interrompue n'est jamais continuée implicitement.

`collect` vérifie le candidat, exécute les validations et construit le paquet sans appeler
d'agent. Elle annonce qu'elle exécute les commandes de validation du projet.

Le résultat affiché indique le dossier de travail, les traces, les éventuels blocages et le
paquet produit. Une commande `status` dédiée, une GUI et une commande de reprise plus élaborée
pourront attendre un besoin constaté.

## 11. Implémentation proportionnée

Commencer avec une seule intégration réelle derrière une petite interface de lancement.
Le choix du fournisseur reste dans cette intégration ; le noyau manipule un appel, son
résultat et le dépôt. Une matrice abstraite de capacités et un second fournisseur ne sont
pas des critères de sortie de V1.

Trois ensembles de code devraient suffire au départ : l'entrée CLI, l'enchaînement
préparation/lancement/collecte et l'intégration de l'agent. Les fonctions Git et de validation
peuvent rester proches de cet enchaînement tant qu'une séparation n'apporte rien de concret.

Réutiliser `development.py` pour l'export et le paquet, `transport.py` pour les appels,
`storage.py` pour les écritures atomiques et `lock.py` pour l'exclusion d'exécution, lorsque
leurs interfaces conviennent. Une petite fonction publique de vérification de l'export peut
être extraite si nécessaire. Ne pas importer `workflow.py` pour développer.

L'objectif est quelques centaines de lignes propres au Runner, comme ordre de grandeur à
vérifier, pas comme estimation acquise. On réduit d'abord les responsabilités si l'outil
grossit ; on ne compacte pas le code pour tenir un chiffre. Les dépendances de production
supplémentaires ne font pas partie de cette proposition.

## 12. Mise en place et critères de réussite

### Premier essai complet

Commencer par une tranche verticale : un export existant, un petit dépôt de travail déjà
préparé, un agent réel, une commande de validation et un paquet final. Ce prototype sert à
vérifier le passage de relais complet avant d'automatiser la préparation du clone.

L'essai doit montrer que l'agent sait conduire le lot jusqu'à un candidat sans orchestration
de chacune de ses étapes. Les défauts observés déterminent les améliorations suivantes.

### Stabilisation de la V1

Ajouter la préparation automatisée et la continuation explicite. Couvrir avec un faux agent
et de petits dépôts temporaires les situations essentielles : réussite jusqu'au paquet,
validation échouée ou ayant modifié le candidat, et interruption sans relance automatique.
Les tests automatisés n'appellent aucun fournisseur réel.

La V1 est utilisable quand :

1. Un lot délimité est transmis intégralement à l'agent, avec ses réserves.
2. Le candidat est produit dans le dépôt de travail distinct.
3. Les validations du paquet portent sur le commit livré et le candidat reste inchangé.
4. Un échec conserve les logs et le travail, sans correction ou relance automatique cachée.
5. La collecte peut être refaite sans nouvel appel à l'agent et sans écraser un ancien paquet.
6. Le paquet est utilisable par la revue existante sans extension du moteur A/B.
7. Les limites de l'environnement d'exécution sont explicites, pour l'agent comme pour les tests.

Un essai réel sur une petite modification de DialogForge peut ensuite précéder un premier
lot FloraPi sans matériel, service de production ni secret réel.

## 13. Ce que cette version retire de la première proposition

| Première proposition | Décision pour la V1 simplifiée |
|---|---|
| Bootstrap séparé sans modification de code | Préparation intellectuelle intégrée au travail de l'agent |
| Un appel par étape PWF | Un lancement pour réaliser le lot |
| Runner choisissant `Next Step` | Plan géré par l'agent, sans interprétation par le Runner |
| Session fraîche à chaque étape | Session selon l'outil choisi ; aucune dépendance obligatoire pour continuer |
| Commits réservés au Runner | Commits locaux réalisés par l'agent |
| Contrôles Git et validations à chaque étape | Contrôle du candidat et validations finales |
| Boucle externe de réparation | Corrections intermédiaires par l'agent ; arrêt si la collecte finale échoue |
| Protocole `STEP_RESULT` | Résultat technique de l'appel et bilan déclaratif |
| Contrat générique de permissions | Mandat et petit enregistrement des paramètres d'exécution |
| Plusieurs statuts croisés avec plusieurs phases | Traces d'appels et résultats de collecte, sans état détaillé des tâches |
| Reprise transactionnelle des étapes | Continuation explicite depuis le travail conservé |
| Qualification générique par adaptateur et version | Protections et limites vérifiées dans l'environnement choisi |
| Plateforme d'adaptateurs à capacités déclarées | Une intégration réelle et une interface réduite |
| Sept lots de construction avant généralisation | Un premier passage complet, puis des améliorations fondées sur les essais |

Restent hors périmètre : installation automatique de dépendances, push, merge, déploiement,
accès au matériel réel, multi-agent, service permanent, file de travaux, budget de tokens,
choix adaptatif de modèles et revue LLM après chaque tâche.

La responsabilité du Runner s'arrête à la remise d'un candidat et de ses preuves pour examen.
L'agent conduit le développement ; l'humain garde la décision sur son intégration.

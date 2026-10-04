# DialogForge — proposition Astra V2 après lecture de l'analyse Opus

**4 octobre 2026 — proposition à arbitrer, aucune implémentation engagée par ce document.**

Sources : [schéma initial](schema_dialogforge.md), [analyse Opus](schema_dialogforge_analyseOpus.md), [analyse Astra V1](schema_dialogforge_analyseAstra.md), et vérification ciblée du code actuel. Cette V2 remplace ma première proposition pour les choix qu'elle énonce. Les documents précédents restent conservés.

## 1. Recommandation

**Faire évoluer le Runner existant pour qu'un lancement conduise à une version utilisable dans `code/`, avec un bilan de réalisation, des validations rattachées au candidat et une décision humaine après essai.**

Je retiens d'Opus la priorité donnée à la livraison et la réduction du parcours. L'agent sait déjà organiser un développement entier dans un appel : nous n'avons pas à reconstruire cette autonomie dans DialogForge. Je retire de ma V1 l'obligation d'une boucle de revue B avant toute remise du candidat.

Je maintiens cependant une distinction indispensable : **réussir les validations ne suffit pas à démontrer que toute la conception est réalisée**. La remise doit donc comporter un bilan explicite du mandat, et le Runner doit savoir distinguer un candidat proposé, un travail restant et une question. Sinon, il peut livrer comme terminé un travail que l'agent lui-même déclare incomplet.

Le parcours recommandé est le suivant :

```text
Conception acceptée
    ↓
Démarrer l'implémentation
    ↓
Agent : réaliser tout le périmètre convenu, tester, relire, committer
    ↓
Résultat de fin d'appel
    ├── travail restant dans le mandat → continuation
    ├── question ou obstacle → pause avec motif
    └── candidat proposé
              ↓
Validations finales et contrôle du lancement prévu
    ├── défaut corrigeable → correction dans le même lancement
    ├── obstacle réel → pause avec motif
    └── contrôles réussis
              ↓
Remise automatique du candidat dans code/
              ↓
Utilisateur : essayer → accepter / demander une correction / arrêter
                         ↳ relecture facultative accessible
```

Une demande de correction après essai repart du candidat essayé dans la même implémentation. Elle ne crée ni une recherche ni une nouvelle conception, tant que le mandat ne change pas.

## 2. Ce que la confrontation des deux analyses change

| Sujet | Apport d'Opus | Décision proposée dans cette V2 |
|---|---|---|
| Autonomie du développement | La boucle coder–tester–corriger existe déjà dans l'appel agent | Garder cette unité de travail ; aucune orchestration tâche par tâche |
| Priorité | Le défaut d'usage observé est l'impossibilité d'essayer le candidat | Livrer d'abord le candidat existant ; ne pas attendre une nouvelle architecture de revue |
| Revue B obligatoire | Coût et complexité supplémentaires non justifiés par le seul incident Mastermind | Retirer l'obligation de ma V1 ; conserver la relecture comme action facultative |
| Conformité à la conception | Validations puis essai humain | Ajouter un bilan de couverture et un résultat final exploitable ; ne pas présenter les tests comme une preuve exhaustive |
| Paquets | Les conserver comme traces internes | Accord complet ; ils n'imposent plus de collaboration documentaire |
| Absence de commit | Utiliser ce signal pour arrêter toute continuation | L'utiliser comme indice ; une question peut survenir après un commit et une vérification peut réussir sans nouveau commit |
| Échec répété | Comparer l'indice de validation et le code de sortie | Ne pas en faire un critère d'arrêt : cette signature ne distingue pas deux défauts différents |
| Durée | Garder une durée totale choisie par l'utilisateur | Recommandation retenue, annoncée comme limite temporelle du lancement, avec pause reprenable |
| Jeton | Le conserver en mémoire jusqu'à fermeture, avec « Oublier le jeton » | Recommandation retenue, y compris entre deux demandes de correction |
| Mandat | Retirer les consignes documentaires périmées | Accord ; préserver la conception, ses réserves et les exports historiques |
| Dépendances | Ne pas construire un installateur générique dans cette refonte | Accord, mais les prérequis et le mode de lancement doivent être définis dès maintenant |
| Taille | La simplification devrait réduire la GUI | Objectif plausible, pas estimation acquise ; mesurer la GUI et le total de production |

### Ce que je corrige dans ma V1

Ma première proposition liait trop fortement l'accès au candidat à la mise en place d'une revue technique automatique complète. Elle répondait à un besoin de contrôle réel, mais elle faisait de ce contrôle une condition préalable à la correction du parcours. **La mise à disposition pour essai doit pouvoir être réalisée et recettée indépendamment.**

Je renonce également à faire juger systématiquement la progression par B. Cela aurait introduit un nouvel appel pour décider s'il fallait poursuivre les appels de développement. La première version doit se contenter de résultats techniques, du bilan de l'agent, d'une limite temporelle explicite et de pauses dont le motif est précis.

### Ce que je ne retiens pas d'Opus

« Il ne faut presque rien construire » sous-estime quelques changements nécessaires : enregistrer une décision sur un candidat sans passer par une revue, distinguer remise et promotion, gérer la reprise entre ces opérations et reconnaître un arrêt métier indépendamment du succès technique.

Ces changements peuvent rester limités. Les supprimer de la conception les ferait réapparaître sous forme de cas mal traités dans le code.

## 3. Constats revérifiés et limites de la preuve

La relecture ciblée confirme les points suivants :

| Point du code | Constat utile pour la refonte |
|---|---|
| `core.run_agent()` | Un appel confie le lot entier à l'agent ; la réponse peut signaler du travail incomplet ou une décision nécessaire, mais une sortie technique normale déclenche la collecte |
| `core._collect_locked()` | Les validations sont attachées à un commit exact ; leur succès permet de produire le paquet |
| `RunnerSession._run_calls()` | Jusqu'à trois appels, seulement après échec de validation, avec une échéance calculée dans la GUI |
| `development.export_files()` | Le mandat demande encore une nouvelle collaboration après modification de code ou de validation |
| `delivery.integrate_candidate()` | L'identité du candidat et son autorisation de promotion sont actuellement retrouvées à travers la revue documentaire |
| `core.bundle_candidate()` | Le transport d'un paquet exige que le clone soit encore sur sa tête ; conserver un bundle à la remise évite de dépendre du HEAD futur |

Le code examiné comprend les modifications non committées déjà présentes dans l'espace de travail. Il ne faut pas limiter cette analyse au seul HEAD Git.

Lors de la V1, **16 tests et 3 sous-tests ciblés ont réussi**, et un contre-exemple a été exécuté sur dépôt temporaire : un mandat demandant de modifier `code.txt` aboutissait à un paquet réussi après ajout d'un README seulement, avec une validation triviale retournant zéro. Ces essais n'ont pas été relancés pour cette V2 documentaire.

Ce contre-exemple montre une propriété du contrat actuel. Il ne démontre ni que Mastermind est incomplet, ni qu'une revue B obligatoire aurait empêché tous les défauts. Il justifie un traitement explicite du bilan et des critères de recette, ainsi qu'une présentation honnête du niveau de vérification.

Les résultats historiques de Mastermind sont ceux consignés dans les documents du projet. **Aucune nouvelle recette du jeu réel n'a été effectuée dans cette analyse.**

## 4. Le contrat minimal entre conception, agent et Runner

### 4.1 La conception reste l'autorité

Le mandat contient la demande, la conception acceptée complète, sa décision, les réserves et les constats ouverts. L'agent doit réaliser tout ce périmètre, sauf lot partiel explicitement choisi par l'utilisateur.

Il faut aussi connaître l'environnement d'essai, le point d'entrée attendu et les vérifications importantes. Une petite table de recette dans la conception suffit ; aucune syntaxe générale de spécification n'est nécessaire.

Pour une conception ancienne, l'agent peut établir une correspondance entre ses exigences et les vérifications prévues. Cette correspondance reste dérivée du texte accepté ; elle ne peut pas effacer une exigence ou transformer un report en décision acquise.

Le bilan de livraison indique, pour les points importants : ce qui a été réalisé, la vérification correspondante et ce qui reste à l'essai humain. Le programme vérifie la présence des références et leur rattachement au candidat ; il ne prétend pas en vérifier automatiquement toute la justesse sémantique.

### 4.2 Alléger le mandat d'exécution

Je retiens l'allègement proposé par Opus. Le prompt Runner n'a pas besoin du mode d'emploi de la revue documentaire ni du schéma de validation que le Runner produit lui-même.

Consigne de travail proposée :

> Réalise le périmètre convenu dans la conception jointe. Organise librement ton travail, teste les comportements attendus et relis ton diff. Termine sur un candidat committé avec des instructions de lancement. Présente les points réalisés, les preuves et les limites. Si du travail reste dans le mandat, indique-le ; si une décision ou un prérequis te manque, explique précisément lequel.

Cette consigne accompagne les documents complets et les commandes prévues. Elle ne remplace pas la conception par un résumé.

Les nouveaux passages de relais doivent distinguer le mode Runner du développement assisté documentaire. Les anciens exports restent inchangés, avec leur empreinte : adapter le contrat de reprise ou créer une nouvelle préparation, sans réécrire un mandat historique sous la même identité.

### 4.3 Un résultat de fin d'appel, et seulement de fin d'appel

Je maintiens cet élément de ma V1, sous une forme réduite. La sortie d'A comporte un bilan libre et un petit résultat identifiable :

| Issue | Sens | Action du Runner |
|---|---|---|
| `CANDIDAT` | L'agent propose une réalisation du périmètre convenu | Contrôler Git, valider et préparer la remise |
| `A_POURSUIVRE` | Du travail reste, mais aucune décision extérieure n'est nécessaire | Continuer dans le lancement autorisé, avec le travail restant explicite |
| `QUESTION` | Une décision manque | Afficher la question et attendre la réponse |
| `BLOQUE` | Un obstacle empêche de poursuivre | Afficher la cause, conserver le travail et proposer la reprise adaptée |

Le résultat donne un motif ou le travail restant selon l'issue. Le Runner relève lui-même le commit ; il ne se fie pas à une identité Git simplement déclarée par l'agent. Le format peut être un petit bloc JSON de la réponse, archivé avec la sortie brute. Son format exact doit être fixé dans la conception technique.

Cela exige bien une extension explicite du contrat V1. **Ce n'est pas le retour d'un `STEP_RESULT` pour chaque tâche** : l'agent reste libre pendant son appel, sans protocole pour chaque édition, commande ou commit.

Pourquoi le commit ne suffit pas :

- l'agent peut committer une partie correcte, puis poser une question métier ;
- il peut terminer une vérification sans modifier les sources ;
- il peut annoncer « travail terminé » tout en laissant une exigence déclarée non réalisée ;
- un appel interrompu peut avoir laissé du code sans réponse finale exploitable.

Une sortie absente ou illisible ne devient jamais un succès implicite. Le Runner exploite d'abord les traces et tente un retraitement local si possible ; il affiche sinon « résultat à clarifier », sans appeler automatiquement un agent à répétition.

Pour les candidats anciens sans ce résultat structuré, conserver une voie de remise locale explicitement marquée « candidat historique à essayer ». Aucune déclaration de complétude ne doit être inventée pour les faire entrer dans le nouveau format.

### 4.4 Ce que signifie « prêt à essayer »

Ce libellé signifie : version matérialisée, agent déclarant le périmètre réalisé, contrôles prévus réussis, lancement vérifié au niveau annoncé et limites visibles. Il ne signifie pas « conformité intégralement prouvée ».

Les tests contrôlent les comportements qu'ils exercent. Le bilan relie le candidat au mandat. L'essai humain et, si demandée, la revue indépendante complètent ce jugement. Cette combinaison est le niveau de garantie assumé de la première évolution.

Un manque obligatoire **déclaré ou connu** empêche de présenter le résultat comme complet. Un candidat partiel peut être rendu accessible pour diagnostic, avec les manques affichés ; cette consultation ne clôt pas l'implémentation avec succès.

Les critères véritablement destinés à la recette humaine restent « à essayer ». Ils ne doivent pas servir à masquer un comportement que l'agent sait absent.

## 5. Revue : facultative dans la première évolution

Je retiens la proposition d'Opus : la revue A/B documentaire ne conditionne plus la remise ni l'acceptation. L'action « Faire relire le candidat » peut réutiliser `create_review()` et les pièces existantes, à la demande de l'utilisateur.

La présentation doit être claire : il s'agit d'une **relecture documentaire du candidat et des preuves**, avec les limites du corpus reçu. Pour un dépôt existant, le paquet ne donne pas nécessairement tout le contexte des fichiers inchangés. Cette action ne doit donc pas être rebaptisée contrôle fonctionnel exhaustif.

La décision finale reste attachée au candidat. Accepter le rapport de la relecture facultative ne doit pas accepter automatiquement le code. Les objections de cette revue restent visibles lors de la décision sur le candidat.

Une revue technique B directe et intégrée pourra être ajoutée si les essais révèlent des omissions que les validations et le bilan laissent passer, ou si le PO la demande explicitement. Elle devra alors examiner le commit exact et son contexte, et toute modification ultérieure nécessitera une nouvelle revue de la version livrée.

Cette évolution future n'est ni un préalable au premier lot, ni un mécanisme déjà disponible. Il n'y a pas lieu de bâtir dès maintenant un second sandbox de développement ou un système général de coopération entre agents.

## 6. Corrections, non-progression et durée

### 6.1 Garder la boucle existante, élargir ses causes de continuation

Le Runner poursuit pour deux raisons connues : un résultat `A_POURSUIVRE`, ou une validation échouée que l'agent peut corriger dans son mandat. Une authentification refusée, un outil absent ou une permission manquante ne doivent pas être traités comme des défauts de code.

Les consignes distinguent la source de la correction : échec de test, travail restant ou défaut signalé par l'utilisateur. Une correction automatique ne doit pas être libellée « demande de l'utilisateur » si celui-ci ne l'a pas formulée.

La politique doit être partagée par CLI et GUI. Le transport et l'affichage peuvent rester distincts ; les règles de continuation doivent vivre dans le Runner, plutôt que seulement dans `RunnerSession._run_calls()`.

### 6.2 Pourquoi la signature proposée par Opus est insuffisante

Supposons une seule commande `node --test`. Elle échoue une première fois sur la règle A, puis, après correction, sur la règle B. L'indice de validation reste `1` et le code de sortie reste `1`. La signature proposée est identique alors que le travail a progressé.

Inversement, deux commits vides donnent deux nouveaux hashes sans rien améliorer. **Le nombre de commits et le couple commande/code de sortie ne suffisent donc pas à mesurer la progression.**

Je recommande une règle plus modeste : détecter l'absence de nouveau résultat exploitable, sans prétendre calculer un pourcentage de progression.

- Comparer l'arbre de sources et les résultats disponibles, pas seulement le hash du commit. Des fichiers de travail non committés doivent être conservés et signalés ; ils ne valent pas un candidat prêt.
- Si une continuation laisse le même arbre, aucune nouvelle preuve exploitable et le même obstacle, faire une pause avec ce constat.
- Si la validation devient verte sans nouveau commit, conserver ce résultat : une amélioration d'environnement ou une vérification peut suffire.
- Si le code change mais la commande échoue encore, continuer dans la durée autorisée ; ne pas déduire l'immobilité de son seul code de sortie.
- Si l'agent renvoie `QUESTION` ou `BLOQUE`, traiter cette issue même s'il a créé des commits.

Les références à des contrôles réellement exécutés servent de preuves ; une phrase « j'ai progressé » ou des horodatages différents dans les journaux ne suffisent pas. Lorsqu'une comparaison fiable n'est pas possible, la limite de durée s'applique ; aucun parseur universel de sorties de tests n'est nécessaire.

Une pause pour absence de nouveau résultat reste une règle opérationnelle prudente. Son message décrit les faits ; il n'affirme pas que la tâche est impossible.

### 6.3 Une durée explicite, sans compteur fixe d'appels

Je retiens d'Opus la durée maximale choisie au lancement, et je propose de retirer la limite de trois appels. La règle existante du 3 octobre autorise ce compteur : son remplacement doit être consigné, pas présenté comme une simple correction d'une règle inexistante.

Le délai choisi est une borne temporelle assumée. Il peut arrêter un travail qui progresse ; l'écran doit annoncer cet effet. À échéance, le Runner met le travail en pause, ne déclare pas la conception réalisée et ne repart pas automatiquement avec une nouvelle durée.

Il faut préciser le calcul : **durée du travail automatique à partir de son démarrage, comprenant les appels et les validations**. Les commandes ont aussi leur propre délai maximal, limité par le temps restant. L'import local d'un candidat déjà prêt peut être repris séparément sans nouvel appel fournisseur.

Le code actuel ne garantit pas strictement cette durée globale : la GUI transmet le temps restant à l'agent, alors que la collecte utilise ensuite ses délais propres par validation. Il faut aligner ces délais dans la fonction commune si l'interface promet une durée totale.

Après réponse à une question ou reprise humaine, l'utilisateur relance le travail avec la durée affichée. Cela prolonge la même implémentation ; ni le clone ni la conception ne sont recréés.

## 7. Livraison et acceptation : deux effets distincts

### 7.1 Remettre le candidat

La séquence d'Opus est la bonne base : copier le paquet, importer les commits, extraire une branche candidate. Elle est exécutée par DialogForge dans le lancement autorisé ; l'agent développeur conserve son espace d'écriture isolé.

Pour un projet neuf :

1. Vérifier le paquet, l'export et le commit candidat.
2. Conserver le paquet dans `developpement/paquets/` et son bundle local avant une prochaine correction.
3. Importer le commit exact dans `code/`, sur une branche telle que `candidat/001` ; un nom existant doit déjà désigner le bon commit ou être refusé, jamais écrasé.
4. Vérifier l'état de l'espace d'essai puis extraire cette branche sans forcer.
5. Vérifier la tête extraite, le lancement prévu et enregistrer le résultat de la remise.
6. Afficher le chemin, la version, les instructions et les éléments de recette.

Si `code/` contient des modifications incompatibles, la remise n'est pas terminée. Le candidat importé peut être conservé, mais l'écran indique « remise en attente », avec l'action nécessaire. **Afficher seulement une commande Git ne doit pas produire le statut « livré » pendant que le dossier montre encore l'ancienne version.**

Pour un dépôt existant, je conserve le choix de ma V1 : utiliser un clone d'essai géré dans `mission/code/`, distinct du dépôt source. Le lancement n'interrompt pas l'utilisateur en basculant la branche de son dépôt habituel. Le dépôt source et sa branche restent la cible de promotion choisie au départ.

Cette distinction évite d'introduire un système de worktrees : un clone d'essai suffit, avec les mécanismes Git déjà employés.

### 7.2 Accepter la version essayée

Le bouton « Accepter cette version » enregistre une décision datée sur le commit essayé, l'export de conception et les preuves correspondantes, puis effectue la promotion locale annoncée. L'identité de la branche cible est enregistrée ; elle ne s'appelle pas nécessairement `main`.

L'intégration actuelle doit être adaptée autour de cette décision. **Il ne suffit pas d'enlever le test “revue acceptée”** : aujourd'hui, `integrate_candidate(review)` obtient aussi la conception, le paquet et le contexte grâce à cette revue. La nouvelle entrée doit retrouver ces informations depuis la référence du candidat, et contrôler que la décision humaine s'y applique toujours.

La promotion utilise le commit enregistré, pas seulement un nom de branche qui pourrait avoir changé. Elle exige une cible dans l'état attendu et un fast-forward. Une divergence impose une résolution explicite ; un résultat combiné différent doit être contrôlé et essayé comme nouvelle version.

Après un candidat déjà accepté, une correction peut avancer depuis cette version acceptée si elle est bien l'ancêtre attendu. Il faut donc distinguer **base initiale de développement** et **tête cible attendue avant cette promotion** ; exiger indéfiniment la base initiale bloquerait l'acceptation d'une correction ultérieure.

Si la décision est écrite mais que Git échoue, afficher « accepté, intégration à terminer ». La reprise achève l'opération locale sans recréer de décision et sans rappeler l'agent.

### 7.3 Corriger et conserver les versions

Une correction repart du candidat essayé dans le même clone lorsqu'il correspond encore à cette version. Si le clone contient une tentative plus récente ou des modifications inachevées, les conserver et expliciter la base de reprise ; ne pas supposer que sa tête est forcément le candidat affiché.

Une nouvelle version proposée à l'utilisateur reçoit une nouvelle référence, par exemple `candidat/002`. Une collecte supplémentaire du même commit peut enrichir ses preuves ; elle ne justifie pas, à elle seule, une nouvelle version de code.

Les décisions sont attachées au commit et aux preuves exactes. Les paquets et bundles antérieurs restent lisibles même si le clone évolue. La reprise utilise la référence de l'exécution qui a produit le candidat, pas simplement la dernière exécution de la conception.

Les modifications utilisateur dans `code/` ne sont jamais effacées pour remettre ou accepter un candidat. Si elles sont intégrées au travail, elles doivent entrer dans une nouvelle version vérifiée.

### 7.4 Reprise locale

Un petit enregistrement de candidat peut référencer : exécution, export, paquet, commit, branche candidate, chemin d'essai, cible de promotion et tête cible attendue. Les validations et le bilan restent dans les artefacts existants ; inutile de les dupliquer.

La décision humaine et le reçu de remise ou d'intégration sont des faits distincts. L'état affiché est calculé à partir de ces faits et de Git. `mission.json` reste un registre de navigation.

Avant les opérations à plusieurs écritures, enregistrer les identités attendues ; après interruption, constater ce qui est déjà réalisé puis finir seulement les étapes manquantes. Réutiliser les verrous et écritures atomiques existants. Aucun ordonnanceur ni service permanent n'est requis.

## 8. Un résultat réellement lançable et une authentification continue

### 8.1 Lancement et dépendances

Je partage le refus d'Opus de construire maintenant un gestionnaire générique d'installation. En revanche, une conception doit dire comment son résultat sera lancé et avec quels prérequis.

La première évolution prend en charge un environnement déjà prêt, ou une préparation explicite prévue dans le mandat et permise par le profil. Un prérequis absent est détecté aussi tôt que possible et expliqué. Des dépendances fournies d'avance peuvent suffire : tout projet utilisant une bibliothèque externe n'est pas automatiquement impossible dans le contrat actuel.

Les validations gardent leur réseau fermé. Une installation via un registre ou des accès supplémentaires demanderait une extension distincte ; elle n'est pas ajoutée implicitement pour faire disparaître un échec.

Pour annoncer la remise : sources ou artefact prévu présents, instructions exactes, et contrôle de démarrage correspondant à l'environnement d'essai. Un test Linux ne prouve pas une exécution Windows. Un fichier ignoré présent seulement dans le clone ne doit pas rendre l'essai artificiellement concluant.

Les commandes de construction générant des fichiers et le contrôle de démarrage peuvent utiliser un espace temporaire ou des sorties dédiées. Le contrôle du commit reste applicable aux sources réellement livrées. Si un serveur temporaire est démarré pour un test, le Runner l'arrête ; l'application interactive est ouverte à la demande de l'utilisateur.

Pour Mastermind, la recette doit indiquer concrètement quoi ouvrir ou lancer et quels comportements essayer. Cette analyse ne présume pas le mode exact de lancement du jeu réel.

### 8.2 Jeton en mémoire entre les corrections

Je retiens l'amélioration d'Opus : conserver le jeton en mémoire du processus GUI jusqu'à fermeture ou action « Oublier le jeton ». Le champ visuel peut être effacé sans supprimer la session d'authentification qui servira à une correction ultérieure.

Le stockage du secret doit donc sortir de la seule requête temporaire actuellement vidée en fin d'action. Le contexte en mémoire fournit le jeton à chaque appel autorisé ; il ne le transmet ni aux tests ni aux opérations Git locales. Pas d'enregistrement dans les références, les arguments de commande ou les journaux.

Une demande de correction reste un clic volontaire. La présence du jeton ne constitue pas une autorisation permanente de lancer de nouveaux travaux. À fermeture, la copie détenue par l'application est abandonnée ; une nouvelle saisie pourra être nécessaire à la prochaine ouverture.

Une erreur d'authentification mène à une demande de remplacement, sans répétition automatique. Si la relecture facultative utilise un autre outil, elle conserve son mécanisme d'authentification propre. Aucun jeton de développement n'est supposé convenir à tous les fournisseurs.

## 9. Mise en œuvre proposée, avec résultats vérifiables

Cette séquence est une proposition à intégrer au plan existant après arbitrage. Elle ne crée pas un second tableau d'avancement.

| Lot | Travail principal | Résultat permettant de clôturer le lot |
|---|---|---|
| A — Remise et décision | Extraire de `delivery.py` la remise du candidat ; ajouter décision liée au commit et promotion ; adapter bundle et reprise ; fournir les actions GUI minimales | Un paquet déjà produit devient essayable dans `code/` sans appel agent ; acceptation et correction ont une version de référence |
| B — Résultat et mandat | Alléger le prompt Runner ; ajouter le résultat final et le bilan de couverture ; définir l'environnement et le lancement ; traiter les anciennes versions | Une question après commit et un travail déclaré incomplet ne sont plus présentés comme un résultat terminé |
| C — Continuation commune | Partager la boucle CLI/GUI ; retirer le compteur fixe ; gérer durée, corrections, pauses et reprise ; conserver le jeton entre actions | Une erreur corrigeable poursuit le même travail sans clic supplémentaire ; une pause reprend au bon endroit |
| D — Parcours et recette | Finaliser le suivi « Implémentation », la revue facultative et l'affichage des preuves ; essayer une mission réelle complète | Conception → lancement → essai → correction → acceptation du candidat exact, sans étape documentaire imposée |

Le lot A est prioritaire, comme le propose Opus. Il peut résoudre le blocage de Mastermind sans attendre les autres. **Il démontre l'accès au résultat ; les lots suivants complètent le contrat “aller jusqu'au bout du mandat”.**

Ne pas repousser toute interface au dernier lot : chaque lot doit fournir un parcours utilisable pour sa recette. Le lot D achève la cohérence de l'ensemble.

### Modules à faire évoluer

- `dialogforge_runner/core.py` : dissocier résultat de l'appel et collecte automatique ; traiter les issues de fin d'appel ; réutiliser les validations et le transport exact.
- Un point commun dans `dialogforge_runner` : politique de continuation et de durée appelée par CLI et pont GUI, sans framework général.
- `iabinome/development.py` : contenu du mandat adapté au mode d'exécution, sans altération des exports historiques ni abandon des paquets.
- `iabinome/delivery.py` : remise dans l'espace d'essai, acceptation du candidat, promotion et reprise ; revue documentaire conservée comme voie facultative.
- `iabinome/executions.py` : références utiles au candidat et règles d'action partagées ; pas de second état global de mission.
- `gui/runner_session.py`, vues Runner/suivi et point d'entrée CLI : pilotage commun, conservation du jeton en mémoire, affichage du résultat essayé.

### Ce qui est retiré du parcours normal

Les clics « examiner le paquet », « démarrer la collaboration », « accepter le rapport », puis « intégrer » sont remplacés par la remise automatique, l'essai et l'acceptation du candidat. La revue facultative peut toujours utiliser le code documentaire existant.

La boucle fixe de trois appels disparaît au profit du contrat de continuation et de durée. Les instructions exigeant une nouvelle collaboration après correction disparaissent des nouveaux mandats Runner.

La réduction nette de code reste à mesurer. Le chiffre de 2 643 lignes repris par Opus correspond à un état antérieur ; le journal lu lors de la V1 annonçait ensuite 2 698 pour façade + GUI. Aucun de ces chiffres n'est une mesure recalculée pour cette V2. Le bilan devra distinguer code supprimé, code ajouté et déplacement vers le cœur.

## 10. Recette décisive et reprise de Mastermind

### Scénarios ciblés

| Situation | Résultat exigé |
|---|---|
| Paquet existant valide | Import et essai possibles sans appel fournisseur |
| Agent proposant un candidat complet | Contrôles, remise et attente de l'essai dans le même lancement |
| Commit effectué puis question métier | Pause sur la question, sans déclaration de réussite |
| Travail restant clairement dans le mandat | Continuation automatique, sous l'échéance choisie |
| Tests verts mais manque déclaré | Pas de statut « complet » ; continuation ou pause selon la cause |
| Même commande et code de sortie, défaut différent après correction | Pas d'arrêt automatique fondé sur cette seule signature |
| Commit vide répété, aucune preuve nouvelle | Absence de progression non masquée par le nouveau hash |
| Validation devenue verte sans changement de sources | Résultat conservé, sans exiger artificiellement un commit |
| Échéance pendant une validation | Arrêt maîtrisé et travail reprenable, sans nouvelle période automatique |
| Sources présentes mais démarrage impossible | Remise non annoncée comme prête ; obstacle ou correction identifiés |
| `code/` modifié par l'utilisateur | Aucun écrasement, statut de remise exact |
| Correction après première acceptation | Nouvelle promotion depuis la tête acceptée attendue, sans exiger l'ancienne base initiale |
| Branche candidate ou cible déplacée | Refus de promouvoir un commit différent de celui décidé |
| Fermeture après import, avant reçu | Reprise de la remise locale sans doublon ni appel agent |
| Demande de correction dans la même fenêtre | Réutilisation du jeton encore valide, sans ressaisie obligatoire |
| Relecture facultative acceptée | Le code n'est accepté que par sa propre décision humaine |

Ces tests utiliseront des agents factices et des dépôts temporaires. Ils ne remplacent pas l'essai utilisateur d'une application réelle.

### Premier essai réel recommandé

Répéter la procédure sur une copie de la mission Mastermind, puis, dans le cadre de la mise en œuvre autorisée : vérifier le paquet déjà produit, conserver son bundle, importer le candidat dans `Mastermind/code/`, afficher son bilan et ses résultats existants, puis effectuer les scénarios de recette pertinents.

**Aucun nouvel appel de développement n'est nécessaire pour simplement rendre accessible le commit existant.** Si le lancement ou la recette révèlent un défaut, l'appel suivant aura cet objectif précis. Les paquets portant la même tête ne sont pas présentés comme autant de versions différentes du jeu.

La recette complète de l'évolution comprend ensuite une correction issue de l'essai et l'acceptation de la nouvelle version. Une simple copie réussie ne suffit pas à valider la reprise, la décision ou le travail de correction.

## 11. Décisions à consigner pour passer à l'implémentation

La demande actuelle autorise cette nouvelle proposition. Les choix ci-dessous sont recommandés ; ils ne sont pas présentés comme déjà acceptés par le PO.

1. La remise locale dans `code/` devient la fin normale d'un lancement réussi, avant la décision humaine.
2. La revue documentaire devient facultative ; une revue B technique automatique n'est pas requise pour cette première évolution.
3. Un résultat minimal de fin d'appel distingue candidat, continuation, question et obstacle ; les étapes internes de l'agent restent libres.
4. La durée choisie borne le travail automatique ; le compteur fixe d'appels est retiré, avec pauses et reprises explicites.
5. L'acceptation porte sur un commit et ses preuves, puis autorise sa promotion locale en fast-forward vers la cible enregistrée.
6. Le jeton reste en mémoire pendant la session GUI, jusqu'à fermeture ou oubli demandé ; chaque nouveau travail garde son autorisation propre.
7. La première évolution utilise un environnement prêt ou une préparation déjà prévue et permise ; un installateur générique et une ouverture réseau ne font pas partie de cette refonte.

Ces décisions doivent être reportées dans la conception Runner, `docs/RUNNER.md`, les règles concernées de `CLAUDE.md` et `project/RULES.md`, puis dans le plan existant. La livraison visée ici est locale, conformément à `schema_dialogforge.md` ; aucune ambiguïté sur une publication distante ne bloque la rédaction ni le premier lot.

**La proposition V2 reprend la simplicité du parcours d'Opus, tout en conservant les distinctions nécessaires entre travail déclaré terminé, contrôles réussis, candidat réellement livré et acceptation humaine.**

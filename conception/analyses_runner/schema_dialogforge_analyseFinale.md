# DialogForge — réflexion finale sur l'évolution du Runner

> **Suite au recentrage demandé par le PO sur la simplicité et la réalisation entière, la conception proposée est désormais [Runner — agent unique](../RUNNER_AGENT_UNIQUE.md).** Le présent document reste une analyse historique ; ses mécanismes supplémentaires, notamment la mesure de progression et le registre de candidats, ne constituent pas des exigences à reprendre.

**4 octobre 2026 — synthèse révisée selon la décision du PO : un seul agent A dans le Runner.** Ce choix est impératif et acquis. Les modalités de réalisation ci-dessous restent une proposition de conception ; cette révision documentaire n'engage pas leur implémentation.

Sources principales : [proposition Opus V2](schema_dialogforge_analyseOpus_V2.md) et [proposition Astra V2](schema_dialogforge_analyseAstra_V2.md), confrontées au [schéma du parcours](schema_dialogforge.md), aux règles du projet et à une lecture ciblée du code présent, y compris ses modifications non committées. Le PO a confirmé qu'il s'agissait bien d'Astra et a fixé la priorité sur ces propositions : **« uniquement A fait la mise en place/contrôle du code. Pas d'autres agents à appeler. »**

## 1. Le résultat recherché

**Une conception acceptée doit conduire, en un lancement, à une version réellement accessible et lançable dans `code/`. A réalise seul le code, les tests, la relecture et les corrections ; le Runner exécute les validations prévues et remet le candidat. L'utilisateur essaie ensuite cette version et décide de l'accepter ou de demander une correction.**

Le Runner appelle uniquement A : aucun B, aucun agent de revue, aucun sous-agent délégué, aucun second agent facultatif ou de secours. A peut être rappelé pour poursuivre ou corriger le même travail ; « un seul agent » ne signifie pas « un seul appel ». Les commandes de test, les contrôles Git et le transport local sont des opérations du logiciel, sans appel de modèle supplémentaire. Cette décision concerne le développement et le contrôle du code dans le Runner ; elle ne redéfinit pas les étapes documentaires de recherche et de conception en amont.

Le défaut actuel a deux dimensions : le candidat reste inaccessible dans le dossier d'essai tant qu'une revue documentaire n'est pas acceptée, et un paquet techniquement réussi ne démontre pas que la conception est réalisée. La refonte doit traiter les deux, sans reconstituer une orchestration tâche par tâche.

L'agent développeur organise librement son travail dans son appel. Le Runner prend en charge les frontières de cet appel : son résultat, les validations, les motifs de continuation, la remise et la reprise. Il ne devient ni un planificateur général ni un moteur documentaire supplémentaire.

La livraison visée ici est **locale**. Elle comprend un candidat dans l'espace d'essai, ses instructions et ses preuves. Une publication distante ou une mise en production ne fait pas partie de ce lancement.

## 2. Arbitrages entre les deux V2

Le choix du PO tranche la divergence des deux V2 et remplace la recommandation précédente de cette synthèse : la revue B proposée par Opus est écartée. La revue par un autre agent proposée en option par Astra est également écartée du Runner. Le contrôle du code appartient entièrement à A, avec les validations automatiques et l'essai humain.

| Sujet | Choix final recommandé | Motif |
|---|---|---|
| Accès au résultat | Remise automatique avant acceptation humaine | On décide sur une version que l'on peut essayer |
| Contrôle du code | A développe, teste, confronte son travail à la conception et relit son diff | Un seul agent réalise et contrôle le code, conformément à la décision du PO |
| Revue du code par un autre agent | Supprimée du parcours Runner, y compris comme option ; anciennes revues consultables sans nouvel appel | Aucun autre agent ne participe au développement ou au contrôle du candidat |
| Premier lot | Rendre les candidats existants accessibles sans nouvel appel fournisseur | Résoudre immédiatement le problème d'accès au résultat |
| Résultat de A | Un petit résultat structuré en fin d'appel, accompagné d'un bilan libre | Un commit et un code de sortie zéro ne distinguent pas réussite, question et travail restant |
| Progression | Constats techniques limités et bilan de A | Aucun agent supplémentaire n'est appelé pour décider si le travail progresse |
| Arrêt automatique | Durée choisie, absence de nouveau résultat constatée, incident ou question | Retirer le compteur fixe de trois appels sans créer une boucle sans borne |
| Dépendances | Environnement prêt ou préparation déjà autorisée ; aucun installateur générique | Une bibliothèque présente n'est pas un obstacle ; un accès manquant doit être expliqué |
| Taille | Réemploi et suppression de parcours, avec mesure globale | Déplacer du code hors de la GUI ne suffit pas à simplifier le logiciel |

**Le niveau de vérification retenu associe le contrôle par A, les validations exécutées sur le candidat et l'essai humain.** Il n'inclut aucune revue indépendante par un autre agent. Les validations prouvent uniquement ce qu'elles exercent ; le bilan de A expose la couverture du mandat et les limites. Le logiciel ne prétend pas déduire une conformité exhaustive d'une suite de tests verte.

La mise à disposition d'un candidat historique ou incomplet reste possible pour diagnostic. Elle porte un libellé explicite et ne constitue pas une réussite du nouveau contrat.

## 3. Un parcours continu

```text
Conception acceptée
    ↓
Démarrer l'implémentation — mandat, environnement, durée et profil de A affichés
    ↓
Préparation et vérification des prérequis
    ↓
A développe, teste, relit et committe
    ↓
Résultat de fin d'appel
    ├── RESTE → continuation avec le travail restant
    ├── QUESTION / OBSTACLE → pause expliquée
    └── CANDIDAT
             ↓
       Validations sur le commit exact
             ├── défaut corrigeable → retour à A
             ├── incident / prérequis manquant → pause expliquée
             └── contrôles réussis
                       ↓
                 Conservation du paquet et du bundle
                       ↓
                 Remise et vérification dans code/
                       ↓
                 Version NNN prête à essayer
                       ↓
                 Utilisateur : essayer
                    ├── accepter → promotion locale du commit essayé
                    └── demander une correction → même implémentation
```

La durée et l'interruption humaine s'appliquent pendant tout le travail automatique. Une erreur locale de remise ne provoque pas un nouvel appel de développement.

Un seul écran « Implémentation » présente le travail en cours, la version proposée, les pauses et les décisions. Il ne revient pas à « Prête » comme s'il s'agissait d'une nouvelle collaboration. CLI et GUI utilisent les mêmes règles d'action.

## 4. Un mandat complet et un résultat de fin d'appel minimal

### 4.1 Le périmètre ne change pas en cours de route

Le mandat transmet la demande, la conception acceptée complète, la décision applicable, ses réserves, les constats ouverts et les validations prévues. Il précise l'environnement d'essai et le lancement attendu lorsque ces informations sont connues.

Le prompt Runner retire les consignes du développement documentaire extérieur qui imposent une nouvelle collaboration après chaque modification. Cette séparation ne modifie pas les exports historiques sous leur empreinte : un nouveau contrat de mandat est identifié et archivé. La voie documentaire existante conserve ses consignes propres.

Consigne centrale proposée :

> Réalise et contrôle toi-même tout le périmètre convenu, sans appeler ni déléguer à d'autres agents. Organise ton travail, teste les comportements attendus, confronte le résultat à la conception complète, relis ton diff et produis les commits locaux. Documente le lancement et relie les exigences importantes aux réalisations et vérifications. Indique explicitement le travail restant, toute décision manquante ou tout obstacle. Ne réduis pas le périmètre sans décision humaine.

Une table de recette dans les nouvelles conceptions est recommandée ; son absence dans une conception ancienne ne bloque pas à elle seule le lancement. A établit alors un bilan de couverture et le confronte lui-même au texte complet. Une réserve acceptée conserve son sens : elle n'est ni effacée, ni transformée arbitrairement en exigence nouvelle.

Si l'utilisateur choisit un lot partiel, le mandat et l'écran le nomment. Le succès porte sur ce lot ; il ne signifie pas que toute la conception est réalisée.

### 4.2 Une sortie structurée, une fois par appel

La réponse comprend un bilan libre puis un bloc final identifié `DIALOGFORGE_RESULT`, contenant un objet JSON minimal :

```json
{"issue": "CANDIDAT", "motif": "Périmètre réalisé ; bilan et instructions de lancement ci-dessus."}
```

| Issue autorisée | Sens et effet |
|---|---|
| `CANDIDAT` | A propose la réalisation du périmètre convenu ; le Runner passe aux contrôles |
| `RESTE` | Du travail reste dans le mandat ; le motif dit lequel ; continuation autorisée |
| `QUESTION` | Une décision manque ; le motif contient la question ; pause |
| `OBSTACLE` | Un prérequis ou un accès manque ; le motif explique la cause ; pause |

Le bilan de couverture indique les réalisations, les preuves, les manques et ce qui reste à l'essai humain. Une exigence connue comme absente ne peut pas être masquée sous « recette humaine ». A doit émettre `RESTE`, `QUESTION` ou `OBSTACLE` selon la cause. Une contradiction connue avec `CANDIDAT` doit être clarifiée ou corrigée avec A, jamais arbitrée par un autre agent. Le Runner contrôle le format et les faits techniques disponibles ; il n'ajoute pas un analyseur sémantique général du bilan.

Ce contrat remplace la ligne `LIVRE` proposée par Opus : **A propose un candidat, il ne constate pas sa remise**. Le motif structuré évite de devoir extraire une question d'une prose libre. Aucun résultat par tâche, commande ou commit n'est ajouté.

Le Runner relève lui-même l'identité Git. Une sortie absente, invalide, ambiguë ou issue d'un appel interrompu n'est jamais assimilée à `CANDIDAT`. Les données brutes restent disponibles ; un retraitement local peut récupérer un bloc valide déjà présent, sans inventer une issue ni payer un nouvel appel. À défaut : pause « résultat à clarifier ».

Une question reste une question même après plusieurs commits. Inversement, l'absence de nouveau commit n'interdit pas une validation locale ou la reprise d'une remise déjà préparée.

## 5. A réalise et contrôle le code jusqu'au candidat

### 5.1 Le contrôle fait partie du travail de A

A lit la conception complète, les réserves applicables et les constats transmis. Il dispose du dépôt et du contexte nécessaire au-delà du diff. Pendant son travail, il recherche lui-même les exigences omises, les comportements incohérents, les régressions et les limites de ses tests ; il corrige ce qu'il peut dans le mandat.

Avant de proposer `CANDIDAT`, A relit les modifications et vérifie la couverture du périmètre. Son bilan relie les exigences importantes aux fichiers ou comportements réalisés, aux commandes effectivement exécutées et aux points qui restent à l'essai humain. Les constats hérités du mandat reçoivent une réponse explicite : traité, limite expliquée ou décision nécessaire. Cette relecture appartient à l'appel de développement ; elle n'impose pas un appel séparé de « critique », même avec le même modèle.

Les capacités de délégation à des sous-agents ne sont pas exposées dans le profil d'exécution de A lorsqu'elles sont configurables. Le mandat interdit également cette délégation. Les traces de qualification doivent confirmer le parcours avec un seul agent ; aucune orchestration cachée ne doit remplacer le B retiré du schéma.

### 5.2 Le Runner exécute les validations et constate les résultats

Après `CANDIDAT`, le Runner vérifie l'identité Git et exécute les validations prévues sur ce commit exact. Ce sont des commandes de test et des contrôles locaux, sans modèle chargé de juger leur sortie. Un défaut de code corrigeable revient à A avec les résultats ; un incident de transport ou un prérequis manquant conduit à la pause adaptée.

Le résultat remis correspond au commit contrôlé. Une modification de sources ultérieure exige un nouveau candidat et de nouvelles validations ; un ancien paquet ne valide pas le code actuel. Le contrôle du démarrage et les instructions font partie du résultat attendu.

L'outil et le modèle de A restent des paramètres du profil qualifié. Il n'y a ni configuration de B, ni contrat de verdict B, ni authentification de second agent, ni espace de revue supplémentaire à construire.

### 5.3 Ce que signifie « prêt à essayer »

Ce libellé signifie : A déclare le périmètre réalisé après son propre contrôle, les validations prévues réussissent sur le commit exact, le lancement est vérifié dans l'environnement annoncé et le candidat est effectivement remis dans `code/`. Les limites et les points de recette humaine sont visibles.

Le Runner ne peut pas prouver seul qu'aucune exigence n'a été oubliée. Si A propose à tort un commit hors sujet avec des tests insuffisants, aucun second agent ne vient le détecter : le bilan, la pertinence des validations et l'essai humain constituent le dispositif retenu. Un manque connu empêche l'annonce d'une réalisation complète ; un candidat partiel reste accessible pour diagnostic avec ce manque affiché.

## 6. Continuer utilement et s'arrêter de façon explicite

La boucle commune vit dans `dialogforge_runner`. La GUI et le pont WSL assurent le transport et l'affichage ; ils ne possèdent plus chacun leur politique de continuation.

Les motifs transmis à A restent distincts : travail restant, échec de validation et correction demandée par l'utilisateur. Une correction automatique n'est jamais attribuée fictivement à l'utilisateur.

| Situation | Action |
|---|---|
| A `RESTE` ou défaut de code corrigeable | Continuer avec A dans le mandat et le temps autorisés |
| A `QUESTION` / `OBSTACLE` | Pause avec la décision ou l'action attendue |
| Authentification refusée, quota signalé, incident de transport ou interruption | Conserver les traces ; aucun rejeu automatique d'un appel ambigu |
| Sources inchangées, aucun contrôle amélioré ni autre résultat exploitable, même difficulté persistante | Pause décrivant cette absence de nouveau résultat |
| Durée atteinte | Pause reprenable, sans réussite déclarée ni prolongation automatique |
| Candidat vérifié et effectivement remis | Fin du lancement ; attente de l'essai humain |

La détection de répétition compare les contenus de sources et les résultats disponibles, pas seulement les hashes de commits. Des commits vides n'apportent aucun progrès. Des sorties identiques sur le même arbre peuvent établir une répétition ; le seul couple commande/code de sortie ne suffit pas. Une sortie différente par son horodatage n'est pas une preuve nouvelle.

Si le code change alors que la même commande échoue encore, le Runner ne conclut pas mécaniquement à l'immobilité. Si une validation devient verte sans nouveau commit, il conserve ce résultat. S'il ne sait pas comparer les résultats de façon fiable, la durée reste la borne : aucun analyseur universel de progression n'est nécessaire. Le travail non committé est conservé et signalé ; il ne vaut pas candidat prêt.

**Le compteur `MAX_AGENT_CALLS = 3` est remplacé par une durée totale choisie et affichée.** C'est un amendement à la règle documentée du 3 octobre, pas une correction silencieuse. Aucun budget de jetons, réservation ni quota fournisseur interne n'est ajouté.

La durée court depuis le début du travail automatique autorisé et couvre préparation, appels de A, validations et remise. Chaque opération utilise au plus le temps restant, dans la limite de son propre délai. À l'échéance, aucun nouvel appel n'est lancé ; le processus en cours est interrompu de façon contrôlée et les écritures atomiques en cours sont sécurisées. Le délai de nettoyage est annoncé comme tel, sans promettre un arrêt physique à la milliseconde.

Une reprise humaine affiche la durée du nouveau lancement et repart des artefacts existants. Elle ne recrée pas le clone et ne rejoue pas un appel déjà terminé. Une remise ou une intégration purement locale peut être terminée séparément, sans jeton.

## 7. Remettre, essayer, accepter : trois faits distincts

### 7.1 Un espace d'essai et une cible de promotion identifiés

| Projet | Espace d'essai | Cible après acceptation |
|---|---|---|
| Nouveau projet | Dépôt `mission/code/`, branche `candidat/NNN` extraite | Branche initiale enregistrée dans ce même dépôt |
| Dépôt existant | Clone d'essai géré dans `mission/code/` | Dépôt et branche choisis au lancement |

Le dépôt habituel d'un projet existant reste intact avant acceptation. La branche cible ne s'appelle pas nécessairement `main`. Aucun mécanisme de worktrees n'est requis.

### 7.2 La remise est une opération locale reprenable

1. Vérifier le lien entre exécution, conception exportée, paquet et commit candidat.
2. Conserver le paquet et son bundle **avant de permettre une nouvelle modification du clone**. Le transport d'une ancienne version ne doit pas dépendre du HEAD futur.
3. Enregistrer la référence du candidat et les destinations attendues ; copier et vérifier les artefacts avec les mécanismes atomiques existants.
4. Importer le commit exact dans `code/`, puis extraire `candidat/NNN` sans forcer. Une branche déjà présente doit désigner ce même commit, sinon la remise s'arrête avec un conflit expliqué.
5. Vérifier le commit extrait, les fichiers nécessaires et les conditions de lancement ; écrire le reçu de remise.
6. Afficher le chemin, la version, les instructions, l'environnement vérifié et les points de recette.

Si des modifications utilisateur empêchent l'extraction, le statut est « remise en attente ». Une branche importée ou une commande Git proposée ne signifie pas que la copie de travail est prête. Aucun fichier utilisateur n'est effacé pour terminer l'opération.

Un numéro de candidat correspond à une version proposée, pas à un appel ou à une collecte. De nouvelles validations du même commit peuvent ajouter des preuves sans inventer une nouvelle version du code. Les preuves déjà utilisées pour une décision restent identifiables et conservées.

### 7.3 Accepter le commit essayé

« Accepter cette version » annonce la promotion locale et enregistre une décision datée liée au commit essayé, à la conception exportée et aux preuves présentées. Une acceptation de rapport documentaire ne remplace pas cette décision sur le code.

La promotion vérifie la cible enregistrée, sa propreté, sa branche et sa tête attendue, puis la fait avancer vers le **commit enregistré** en fast-forward. Le nom de la branche candidate ne suffit pas : il peut avoir été déplacé.

Pour un projet neuf, `code/` est encore sur la branche candidate : après les contrôles, le Runner revient explicitement sur la branche cible enregistrée, puis la fait avancer. Pour un dépôt existant, il vérifie que le dépôt utilisateur est dans l'état annoncé ; il ne bascule pas silencieusement un travail en cours.

Il faut distinguer la base initiale du développement de la tête cible attendue pour chaque promotion. Après acceptation de `001`, une correction `002` peut avancer depuis `001` ; exiger encore la base initiale rendrait cette seconde acceptation impossible.

Une cible divergente impose une résolution explicite. Un résultat issu d'une fusion est une nouvelle version à contrôler par A, valider et essayer. Si la décision est enregistrée mais l'effet Git incomplet, afficher « accepté, intégration à terminer » ; la reprise constate les opérations déjà faites et achève les seules étapes manquantes, sans nouvelle décision ni appel agent.

L'actuelle `integrate_candidate(review)` doit donc être adaptée autour d'une référence de candidat. Enlever seulement le contrôle « revue acceptée » serait insuffisant : la fonction retrouve aussi son contexte à travers cette revue.

### 7.4 Corriger sans perdre les versions

Une demande de correction conserve son texte et l'identité du candidat essayé. Elle reprend le même clone si son état correspond encore à cette base. Si une tentative plus récente ou des fichiers non committés y sont présents, les conserver et expliciter le départ retenu ; aucun retour forcé au candidat précédent.

La correction est réalisée et contrôlée par A, puis passe les validations avant de donner une nouvelle version essayable. Les anciens paquets et bundles restent consultables. Une évolution qui dépasse le mandat demande une conception amendée et acceptée ; elle n'est pas glissée dans une correction.

Les modifications faites par l'utilisateur dans `code/` ne sont pas attribuées au commit initial. Pour entrer dans la version acceptée, elles deviennent un nouveau candidat soumis aux contrôles prévus.

## 8. Un résultat lançable, avec des limites visibles

Le mandat prévoit le point d'entrée, les prérequis et l'environnement visé. Les nouvelles conceptions les précisent ; pour les anciennes, A les déduit lorsqu'ils sont non ambigus ou pose une question utile. Un README ou `LANCEMENT.md` fournit les commandes exactes.

Le contrôle de démarrage utilise le dispositif de validation existant. Une application interactive exige un contrôle adapté avant l'annonce « prête à essayer » ; une bibliothèque ou un outil en ligne de commande utilise sa vérification pertinente. Le choix est établi dans la préparation, sans construire un gestionnaire générique de lancement.

Le contrôle doit porter sur ce que recevra l'utilisateur : un fichier ignoré disponible seulement dans le clone ne peut pas justifier le succès. Si une construction génère des sorties, utiliser des destinations dédiées ou un espace temporaire, sans altérer les sources du candidat. Un serveur temporaire lancé pour un contrôle est arrêté à sa fin.

Les environnements sont annoncés précisément : un résultat testé sous Ubuntu WSL peut être essayé sous Ubuntu WSL avec les instructions fournies ; cela ne prouve pas un lancement natif Windows. Si la conception impose Windows, un succès Linux seul ne remplit pas cette exigence. Les comportements visuels restent explicitement à la recette humaine lorsque les contrôles automatiques ne les couvrent pas.

Les dépendances déjà disponibles et la préparation explicitement autorisée restent utilisables. Un prérequis absent est détecté tôt ; un accès à un registre ou une extension des permissions sort du lancement courant tant qu'il n'est pas autorisé. Les validations conservent leur réseau fermé. La refonte n'ajoute ni installation universelle ni distribution générique d'artefacts construits.

## 9. Autorisation, jeton et mémoire de reprise

Un lancement autorise uniquement les appels de A nécessaires au travail et à ses corrections, les validations locales et la remise, dans le mandat et la durée affichés. Il n'y a pas de confirmation à chaque tour. Une correction après essai ou une reprise après pause est une nouvelle action volontaire dans la même implémentation. Aucun appel à un autre agent n'entre dans cette autorisation.

Le jeton reste en mémoire du processus GUI jusqu'à fermeture ou action « Oublier le jeton », y compris entre deux corrections. Effacer le champ visuel ne supprime pas nécessairement le contexte d'authentification. Ce contexte reste distinct de la requête temporaire d'exécution.

Le jeton n'entre ni dans les références, ni dans les arguments de commande, ni dans les preuves ou journaux ; il n'est pas transmis aux validations ou aux opérations Git. Il sert uniquement à l'adaptateur choisi pour A. Une authentification refusée impose une pause et un remplacement, pas une répétition automatique ni l'appel d'un agent de secours.

La présence du jeton ne déclenche aucun travail. La remise, l'acceptation et leurs reprises locales n'en ont pas besoin.

La conservation repose sur les dossiers actuels et quelques références :

| Élément | Information conservée |
|---|---|
| Référence d'exécution | Paramètres non secrets, export, base initiale et emplacement du clone |
| Paquet | Code ou diff prévu par le format, validations, bilan de réalisation et de contrôle, résultat de A liés au candidat |
| Bundle | Objets Git permettant de transporter ce candidat après évolution du clone |
| `developpement/candidats/NNN.json` | Références vers exécution, export, paquet, bundle, commit, espace d'essai, branche cible et tête attendue |
| Décision et reçus | Acceptation humaine, remise effective et promotion effective, séparément |

Les contenus ne sont pas dupliqués dans les références. `mission.json` reste un registre de navigation. Les états affichés se déduisent des faits enregistrés et de Git ; une décision historique reste visible même si elle ne s'applique plus aux fichiers courants.

Les identités nécessaires sont enregistrées avant les opérations à plusieurs écritures. Après interruption, le programme constate ce qui existe déjà et termine ce qui manque. Les verrous et écritures atomiques sont réemployés ; aucun journal transactionnel général, service permanent ou ordonnanceur n'est ajouté.

## 10. Mise en œuvre par résultats utilisables

Le principe d'un seul agent A est décidé par le PO. La séquence de réalisation proposée ci-dessous doit rejoindre le plan de développement existant lorsque l'implémentation sera engagée. Elle ne crée pas un second suivi d'avancement.

| Lot | Contenu | Critère de sortie |
|---|---|---|
| 1 — Accès et décision | Référence de candidat, paquet et bundle durables, extraction dans `code/`, décision sur le commit, promotion et reprise ; actions CLI/GUI minimales | Un candidat existant est essayable et acceptable localement sans nouvel appel fournisseur, avec son niveau de vérification historique affiché |
| 2 — Travail et contrôle par A | Mandat complet, relecture et bilan par A, résultat final, validations et contrôle du lancement, profil sans délégation | A réalise et contrôle le candidat ; aucun autre agent n'est appelé ; les preuves concernent le commit remis |
| 3 — Continuation commune | Boucle CLI/GUI, durée globale, pauses, reprise et jeton de session | Travail restant et questions sont traités correctement ; une erreur corrigeable poursuit le lancement avec A ; aucun compteur fixe d'appels |
| 4 — Recette complète | Cohérence CLI/GUI, compatibilité historique et essai réel dans l'environnement annoncé | Conception → lancement → essai → correction par A → acceptation du commit exact, sans collaboration de revue |

Chaque lot comprend son interface minimale et ses tests. Le contrôle de lancement est développé au lot 2, puis éprouvé de bout en bout au lot 4 ; l'interface et la recette ne sont pas entièrement repoussées à la fin. Aucun lot de revue par un second agent n'est prévu.

Les principaux points de modification sont `dialogforge_runner/core.py` et ses entrées CLI/pont, `iabinome/development.py`, `delivery.py`, `executions.py`, la session GUI et les vues Runner/suivi. Les mécanismes métier restent partagés ; le moteur documentaire `workflow.py` ne reçoit pas l'orchestration du développement.

En échange des ajouts, retirer du parcours Runner la création d'une revue de code par agents, l'acceptation de son rapport, le clic séparé d'intégration après rapport, le compteur de trois appels et la politique de boucle propre à la GUI. La lecture des anciennes revues reste disponible comme archive, sans action de relance d'agents depuis le Runner.

Le dernier relevé cité par le journal donne **2 698 lignes effectives pour façade + GUI, sur 2 700**, et **9 131 pour `src/`**. Ces chiffres sont historiques, non remesurés ici. Le plafond ultérieur de 3 000 n'est pas une marge automatiquement consommable. Mesurer à chaque lot les ajouts, suppressions et déplacements, ainsi que le total de production. Viser un solde façade + GUI nul ou négatif ; si le contrat utile ne tient pas dans le plafond applicable, le faire réviser explicitement, sans supprimer un comportement nécessaire pour satisfaire le compteur.

## 11. Vérification et première recette réelle

Les tests de la refonte utilisent un agent A factice et des dépôts temporaires. Ils vérifient les transitions, l'identité des versions et l'absence d'appel à un autre agent ; ils ne démontrent pas qu'un modèle réel repérera toutes les omissions.

| Cas significatif | Résultat attendu |
|---|---|
| Paquet historique valide, sans résultat A du nouveau format | Remise locale possible, étiquetée « candidat historique à essayer », sans complétude inventée |
| A `CANDIDAT`, bilan de contrôle fourni, validations réussies | Commit exact extrait, instructions et preuves visibles ; aucune collaboration ni aucun autre agent appelé |
| Travail incomplet signalé par A malgré des tests verts | Continuation ou pause selon la cause ; aucun statut de réalisation complète |
| Mandat et profil de lancement de A | Délégation interdite, capacités de sous-agents désactivées lorsqu'elles sont configurables ; aucun chemin d'appel vers un agent de revue |
| Commit suivi d'une question, ou A déclarant du travail restant | Question prioritaire ou continuation adaptée ; pas de réussite implicite |
| Résultat de A absent, ambigu ou illisible | Retraitement local ou pause ; aucun accord par défaut |
| Même commande rouge sur un défaut différent après changement de code | Pas d'arrêt fondé sur le seul code de sortie |
| Commits vides répétés sans résultat nouveau ; validation verte sans nouveau commit | Répétition détectable dans le premier cas ; preuve nouvelle conservée dans le second |
| Échéance pendant A ou une validation | Interruption contrôlée et reprise au bon endroit, sans nouvelle période automatique |
| Code changé après les validations | Résultats précédents inapplicables au nouveau candidat ; nouvelles validations requises |
| Instructions absentes, fichier disponible seulement dans le clone ou mauvais environnement | Candidat non annoncé prêt ; défaut à corriger ou obstacle explicite |
| `code/` contient des modifications ; branche candidate déplacée | Aucun écrasement ni acceptation d'un autre commit ; remise en attente expliquée |
| Crash entre import, extraction et reçu ; entre décision et promotion | Reprise locale sans doublon ni nouvel appel agent |
| Correction après une première acceptation | Nouvelle version conservée et promotion depuis la tête acceptée attendue |
| Dépôt source divergent ou sur une branche inattendue | Promotion refusée sans fusion ni basculement silencieux |
| Correction dans la même session GUI ; authentification devenue invalide | Jeton réutilisé si valide ; pause sinon ; opérations locales toujours accessibles |
| Revue documentaire acceptée ou artefacts changés après décision | Aucune acceptation automatique du code ; décision périmée signalée |

La recette commence sur **une copie de la mission Mastermind** : vérifier le paquet existant, conserver son bundle, remettre son commit dans `code/` et afficher les instructions adaptées. Cette remise ne requiert aucun nouvel appel agent. Les paquets de même tête ne sont pas présentés comme différentes versions du jeu.

L'essai réel comprend ensuite les scénarios navigateur de la conception, une correction ciblée par A si nécessaire et l'acceptation de la version essayée. Si un complément de réalisation ou de contrôle est nécessaire, il est confié à A dans le mandat existant. Aucun appel à un autre agent n'est prévu avant, pendant ou après cette recette du code.

Les analyses antérieures rapportent des tests et un contre-exemple de paquet réussi hors sujet. Ils éclairent le contrat ; ils ne prouvent pas que Mastermind est incomplet. **Aucun appel fournisseur, test d'implémentation ni nouvelle recette de Mastermind n'a été effectué pour rédiger cette synthèse.**

## 12. Portée de la décision de conception

**Décision impérative du PO, datée du 4 octobre 2026 : A est l'unique agent de développement et de contrôle du code ; aucun autre agent n'est appelé par le Runner ou délégué par A.** Elle remplace la recommandation de revue B de la première rédaction de ce document.

La proposition révisée organise cette décision autour des éléments suivants :

1. La remise locale automatique avant décision, puis l'acceptation du commit essayé et sa promotion en fast-forward.
2. La réalisation, les tests, la relecture et les corrections par A seul, complétés par les validations locales et l'essai humain ; aucune revue par un autre agent, même facultative.
3. Le résultat minimal de fin d'appel et le bilan de couverture, sans protocole par tâche.
4. Une politique commune CLI/GUI, une durée totale explicite et des pauses fondées sur les faits, en remplacement du compteur de trois appels.
5. Des versions et preuves conservées, une reprise locale et la protection des modifications utilisateur.
6. Une authentification en mémoire pendant la session, indépendante de l'autorisation de nouveaux travaux.
7. Un environnement de lancement explicite, sans ajout implicite de permissions ni gestionnaire universel d'installation.
8. Une réalisation progressive commençant par l'accès au candidat existant, avec mesure de taille et recette réelle.

La décision d'utiliser uniquement A est consignée dans le plan et `project/RULES.md`. Lors du passage à l'implémentation, les modalités retenues devront être reportées dans la conception Runner V1, `CLAUDE.md`, `docs/RUNNER.md` et `conception/PARCOURS_MISSION_CONCEPTION.md`. La règle de relecture par B du moteur documentaire concerne ses livrables de recherche et de conception ; elle n'impose aucun B au Runner. Pour le code, le contrat est le commit exact contrôlé par A, ses validations et sa remise, puis la décision de l'utilisateur après essai.

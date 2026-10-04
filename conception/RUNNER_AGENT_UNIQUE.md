# Runner — toute la conception, un seul agent, un résultat utilisable

**4 octobre 2026 — conception proposée, sans implémentation engagée.**

Le PO a fixé trois exigences : un seul agent A, tout le code prévu par la conception acceptée, légèreté du Runner. Ce document traduit ces exigences en une évolution du Runner existant. Il remplace, pour cette évolution, les mécanismes plus étendus de [l'analyse finale](../schema_dialogforge_analyseFinale.md). La conception Runner V1 reste la référence du socle réutilisé ; les changements sont décrits ici.

## 1. Le contrat

**Après acceptation de la conception, un lancement confie à A la réalisation de tout le code prévu. A développe, teste, relit et corrige. Le Runner exécute les validations finales et remet le résultat dans `code/`, avec les instructions pour l'utiliser. L'utilisateur l'essaie, puis l'accepte ou demande une correction à A.**

La « conception acceptée » désigne le document issu de la revue de conception, avec la décision humaine et ses réserves. Le mandat transmet ce document entier. Il ne se limite ni à un résumé ni au rapport de revue.

Le résultat final est l'application, l'outil ou la bibliothèque prévu par cette conception, utilisable dans l'environnement convenu. Un rapport, un squelette ou un premier lot ne suffit pas. Si une partie manque, le travail continue ou s'arrête avec une explication ; il n'est pas annoncé terminé.

Le périmètre de ce document est le Runner. Les étapes de recherche et de conception restent en amont. La livraison est locale ; publication distante et mise en production ne sont pas ajoutées à ce parcours.

## 2. Trois responsabilités

| Responsable | Responsabilité |
|---|---|
| A, unique agent | Comprendre toute la conception, organiser son travail, produire le code, tester, relire, corriger, committer et expliquer le résultat |
| Runner | Préparer l'espace de travail, appeler A, conserver les traces, exécuter les validations prévues et remettre le code |
| Utilisateur | Accepter la conception, répondre aux questions nécessaires, essayer le résultat et décider de son acceptation |

Aucun B, agent de revue, sous-agent ou agent de secours n'est appelé. Le mandat l'interdit ; les outils de délégation sont désactivés dans le profil lorsqu'ils sont configurables. Les tests et commandes Git sont des opérations locales, pas des agents.

A peut effectuer plusieurs appels pour terminer le même travail. Le Runner ne choisit pas ses tâches, ne lit pas son plan pour le piloter et ne mesure pas sa progression. A reste responsable de sa méthode et de sa relecture.

## 3. Le parcours

```text
Conception acceptée entière
    ↓
Démarrer l'implémentation
    ↓
A développe, teste, relit et corrige
    ├── travail restant → poursuivre avec A
    ├── intervention nécessaire → pause expliquée
    └── candidat proposé
              ↓
       Validations finales
              ├── défaut de code → correction par A
              ├── incident → pause expliquée
              └── réussite → remise dans code/
                                ↓
                         Essai de l'utilisateur
                            ├── accepter cette version
                            └── demander une correction à A
```

Le même écran suit cette implémentation jusqu'au résultat. Aucun passage par une nouvelle collaboration de revue n'est demandé. Une pause, une erreur de remise ou un résultat partiel ne devient pas une réussite.

## 4. Préparer et confier tout le travail

La préparation existante est conservée : conception acceptée exportée, dépôt initial ou dépôt source, clone isolé, commandes de validation, environnement et durée. Une seule exécution est active. Les prérequis et les permissions du profil existant restent applicables.

Le mandat porte sur **toute la conception acceptée**, y compris les tests, fichiers de configuration, données nécessaires et instructions qu'elle prévoit. Les réserves conservent leur sens ; A ne peut pas décider de reporter une exigence. Le parcours n'offre pas de sélection d'un lot partiel. Une ancienne exécution limitée par `lot.md` reste consultable, mais ne peut pas être annoncée comme une réalisation complète : le mandat entier doit être préparé explicitement, sans altérer l'export historique.

La consigne ajoutée à la conception tient en un paragraphe :

> Réalise tout le code prévu par la conception jointe. Organise librement ton travail, teste les comportements attendus, relis tes modifications et corrige les défauts. Travaille seul, sans appeler d'autres agents. Termine sur des commits locaux et fournis les instructions de lancement, les vérifications effectuées et les limites éventuelles. Si du travail reste, poursuis ; si une décision ou un prérequis te manque, explique précisément lequel.

Le mandat Runner retire les consignes héritées qui imposent une nouvelle collaboration après chaque modification. Les commandes finales viennent de la préparation existante ; A peut effectuer d'autres tests utiles pendant son travail. Son bilan reste libre : aucune table de couverture obligatoire ni formulaire par exigence.

L'environnement doit permettre le développement et l'utilisation du résultat. Les dépendances déjà disponibles ou une préparation explicitement autorisée peuvent être utilisées. Le Runner ne devient pas un installateur universel et n'élargit pas les permissions pour contourner un obstacle. Un prérequis manquant est expliqué ; si possible, il est détecté avant l'appel.

## 5. Une continuation simple

Pour choisir entre valider, continuer et attendre l'utilisateur, A termine son bilan par **une seule ligne**, avec exactement l'une de ces trois valeurs :

| Ligne finale | Action |
|---|---|
| `RUNNER: CANDIDAT` | A déclare avoir réalisé et contrôlé tout le périmètre ; le Runner valide le candidat |
| `RUNNER: RESTE` | A explique le travail restant ; le Runner poursuit avec A dans le même lancement |
| `RUNNER: INTERVENTION` | A explique la question ou l'obstacle ; le Runner affiche son bilan et attend |

Cette ligne est l'unique ajout au contrat de sortie. Elle évite de confondre un commit ou un code de sortie zéro avec une réalisation terminée. Le bilan et la sortie brute restent dans les traces existantes. Une ligne absente ou ambiguë provoque une pause, sans succès implicite ni nouvel appel automatique pour réparer le format.

Après `CANDIDAT`, le Runner réutilise sa collecte : candidat committé, espace propre, commandes prévues exécutées sur le commit exact, résultats conservés. Un échec de validation ordinaire est transmis à A pour correction. Une interruption, une authentification refusée ou un incident d'exécution impose une pause. Aucun classement universel des erreurs n'est construit : les incidents connus sont distingués, un résultat incertain reste une pause.

La durée choisie borne le travail automatique. Les appels de A et les validations utilisent le temps restant ; le Runner n'ouvre pas une nouvelle période de lui-même. Le compteur fixe de trois appels est retiré. Il n'est remplacé ni par un score de progression, ni par une comparaison d'arbres Git ou de sorties de tests. L'utilisateur peut interrompre le travail à tout moment.

Une petite fonction commune porte cet enchaînement pour la CLI et la GUI, à partir des fonctions existantes. Aucun moteur d'étapes n'est créé.

## 6. Remettre un résultat que l'on peut utiliser

Une réussite de validation entraîne automatiquement la conservation du paquet et de son bundle, puis la remise du commit correspondant dans `code/`. Le bundle est conservé avant une correction ultérieure pour que l'ancienne version reste disponible. Le paquet reste une trace interne ; l'utilisateur n'a pas à l'accepter pour accéder au code.

Pour un projet neuf, `code/` est le dépôt créé par la préparation. Pour un dépôt existant, c'est une copie d'essai distincte du dépôt utilisateur. Une branche candidate y est extraite avec les mécanismes Git actuels : créer une branche sans afficher son contenu dans le dossier ne constitue pas une remise.

Les fichiers livrés suffisent au lancement avec les prérequis annoncés. A fournit les instructions exactes. Quand un contrôle de démarrage est nécessaire, il utilise les validations existantes, sans gestionnaire de lancement supplémentaire. L'écran indique l'environnement effectivement vérifié : un essai Linux ne démontre pas un fonctionnement Windows. Un fichier présent seulement dans le clone de développement ne peut pas être indispensable au résultat remis.

L'utilisateur voit le dossier, le commit, les instructions et le bilan des contrôles. Le statut est « prêt à essayer » lorsque A déclare le périmètre réalisé, que les validations réussissent et que le code est effectivement disponible. Cela ne prétend pas prouver automatiquement toute la conformité : A la contrôle, les tests exercent les comportements prévus et l'utilisateur essaie le résultat.

Si le dossier d'essai contient des modifications utilisateur empêchant la remise, le Runner s'arrête et explique la situation. Il n'écrase rien. Terminer cette remise est une opération locale, sans rappeler A.

## 7. Accepter, corriger et reprendre

**Accepter cette version** enregistre le commit essayé et le paquet correspondant. Cette action autorise la promotion locale vers la branche cible annoncée, au moyen du fast-forward déjà utilisé. La cible doit être propre et dans l'état attendu ; une divergence demande une intervention humaine. Une correction après une première acceptation peut avancer depuis cette version acceptée, sans exiger indéfiniment la base initiale.

**Demander une correction** transmet le défaut et le candidat concerné à A. Il travaille dans le clone conservé, vérifie l'état présent, corrige puis repasse les validations. Les versions antérieures restent disponibles. Une demande qui change le périmètre exige une conception amendée ; une réparation dans le périmètre reprend simplement l'implémentation.

Une fermeture ou une interruption conserve le clone, les appels et les résultats. À la réouverture, le Runner utilise `inspect_run` et propose l'action utile : continuer avec A, refaire les validations ou terminer la remise. Aucune relance d'agent n'est implicite. Si une opération locale ne peut pas être reprise sans ambiguïté, le Runner expose le problème et conserve le travail ; il n'a pas à réparer automatiquement tous les états possibles.

Le jeton reste en mémoire pendant la session GUI, jusqu'à fermeture ou « Oublier le jeton », pour les corrections demandées. Il n'est ni enregistré sur disque ni transmis aux validations. Le conserver ne donne aucune autorisation de lancer un autre travail. Les opérations locales n'en ont pas besoin.

## 8. Réutiliser, retirer, ajouter seulement le nécessaire

| Réutiliser | Retirer du parcours | Ajouter ou adapter |
|---|---|---|
| Export, clone, appels et traces | Choix d'un lot partiel dans ce parcours | Mandat portant sur toute la conception et ligne finale de A |
| Collecte, validations, paquets et bundle | Création puis acceptation d'une revue du code | Remise automatique dans l'espace d'essai |
| Référence d'exécution et contrôles Git | Dépendance de l'intégration envers cette revue | Acceptation liée au commit essayé |
| Reprise existante et profil d'exécution | Compteur de trois appels et politique propre à la GUI | Continuation commune et jeton conservé en session |

La référence d'exécution porte déjà l'export, le dépôt, la base et les paquets. Elle est complétée seulement si nécessaire pour identifier la version remise et la branche cible. Les fichiers d'intégration existants accueillent l'acceptation et son résultat. **Pas de registre supplémentaire de candidats, de journal d'intention général ni de reçus à chaque micro-opération.** Git et les paquets gardent les versions et leurs résultats.

Les modifications restent dans le Runner et ses raccordements actuels : mandat dans `development.py`, remise dans `delivery.py`, référence dans `executions.py`, CLI et écran Runner. `workflow.py` ne reçoit pas l'orchestration du développement. Les anciennes revues restent consultables comme archives, sans appel d'agent depuis le Runner.

## 9. Garder cette conception légère

**Une suggestion de revue ne devient pas automatiquement une exigence.** Avant tout mécanisme supplémentaire, nommer le défaut concret du parcours qu'il résout et expliquer pourquoi l'existant ne suffit pas. Sans besoin démontré, la suggestion reste hors de cette conception. Plusieurs analyses servent à choisir une solution, pas à additionner leurs précautions.

La référence de simplicité est le parcours des sections 3 à 7. On n'ajoute ni planificateur de tâches, ni mesure de progression, ni revue par agent, ni installation générique, ni service permanent. Ces mécanismes ne sont pas des lots différés implicitement promis.

À l'implémentation, mesurer le code ajouté **et retiré**, sur l'ensemble de la production. Déplacer une règle hors de la GUI ne la supprime pas. Les plafonds du projet restent applicables ; on réduit d'abord les responsabilités et on réemploie l'existant, sans compacter le code ni sacrifier le résultat attendu pour tenir un chiffre.

## 10. Vérifier sur le besoin réel

Commencer par rendre accessible un paquet Mastermind déjà produit, d'abord sur une copie de la mission, sans appel fournisseur. Puis éprouver le parcours complet avec A seul. Aucun nouveau développement du jeu n'est requis pour simplement remettre son commit existant.

Les tests avec un A factice couvrent les quelques chemins déterminants : candidat remis ; travail restant puis terminé ; validation échouée puis corrigée ; intervention ou réponse illisible ; interruption sans relance ; modifications utilisateur conservées et acceptation du commit exact. Ils vérifient qu'aucun autre agent n'est appelé. Ils ne prétendent pas mesurer la qualité d'un modèle.

La recette réelle est réussie lorsque **toute la conception** donne un résultat lançable depuis `code/`, que l'utilisateur peut l'essayer, demander une correction à A et accepter la version corrigée. Un paquet vert ou une première partie du code ne clôt pas cette recette.

Les essais et la mise en œuvre rejoignent le plan existant. Ce document définit la cible ; il ne constate ni code modifié, ni appel fournisseur, ni recette réelle effectuée.

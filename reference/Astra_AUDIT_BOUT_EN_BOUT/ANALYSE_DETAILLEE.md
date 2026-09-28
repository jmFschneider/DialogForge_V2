# Analyse détaillée et contre-preuves

Complément du [rapport](RAPPORT_AUDIT.md). Ce document développe les observations, les limites et les pistes écartées ; il n'est pas un plan d'avancement du développement.

## 1. Création et cadrage

La création converge vers `facade.create_collaboration`. La façade écrit dans un dossier temporaire voisin, puis renomme le résultat vers la destination. La CLI obtient le texte ou mène le cadrage avant cette publication. Le moteur A/B ne possède pas la session de F : `framing.py` la maintient pendant la conversation et en conserve ensuite les artefacts de provenance.

Ce découpage est pertinent : les refus de création, l'origine de la demande et la configuration sont partagés entre CLI et GUI. Les tests exécutés couvrent les trois voies CLI, le formulaire GUI, l'abandon, les sorties hors contrat de F, les compteurs de groupes et la reprise de conversation. La présence de tests à faux agents ne valide pas le contenu métier des questions posées par les vrais modèles.

`framing.prepare` crée une copie initiale des sources, puis une copie de travail à portée de F. La création finale reprend le corpus préparé ; elle ne relit pas le projet source après la conversation. Cela maintient le lien entre le corpus du cadrage et celui de la collaboration. Les contrôles de source et les cas de refus figurent dans `test_framing`, `test_framing_creation` et `test_facade_creation`.

Les deux collaborations F réelles sont `READY`, sans appel A/B ni décision humaine sur un livrable final. Elles montrent chacune six échanges et un unique identifiant fournisseur, lu sans le reproduire dans l'inventaire synthétique. Cela prouve une continuité observée lors de ces conversations, pas l'absence de perte de contexte dans toute situation d'incident.

Le défaut déjà connu d'`open_questions` est cohérent avec le code : la liste est remplacée lors d'une réponse `CADRAGE_PRET`, mais n'est pas recalculée à chaque tour suivant. Chez Claude, la proposition demande l'entraxe, la poursuite l'apporte, puis la provenance continue de le présenter comme question. Chez Codex, la question sur l'usage subsiste alors que la poursuite indique une zone d'habitation. Une ambiguïté sur la formulation « OSB à rainure… » reste explicitement signalée dans le texte du modèle : il serait incorrect de conclure que toutes les questions encore listées ont forcément reçu une réponse complète.

L'arbitrage de la sémantique du champ reste nécessaire. « Vider à la reprise » et « prendre les QUESTIONS_OUVERTES du dernier tour » ne donnent pas exactement la même information ; l'audit ne tranche pas ce choix produit à la place du PO.

Le cas de liste source vide est différent : l'appel direct à `corpus.build` ne crée pas le dossier si aucune entrée n'est copiée, puis échoue en écrivant le manifeste. La préparation de F crée auparavant le dossier `corpus`, ce qui explique que ce défaut ne touche pas tous les chemins de la même manière. Il ne faut pas extrapoler une panne du cadrage F depuis ce seul échec de primitive.

## 2. Cycle, critiques et promotion

Le cycle nominal conservé dans `scenario/collaboration/` est complet : demande créée par la CLI, proposition A, critique B, révision A avec disposition, relecture B, promotion puis acceptation humaine. A et B sont de vrais sous-processus Python scriptés, pas des objets processus fictifs.

L'objection `B-001` conserve son énoncé ; A indique `CORRIGE`, puis B la passe à `RESOLVED` avec justification. Le dossier contient les appels bruts, les échanges et le bilan. Les quatre appels attendus sont observés. Il n'y a pas de cinquième appel de finalisation après la dernière revue.

La comparaison doit porter sur le **corps** du livrable, hors en-tête d'avertissement écrit par le programme. Après clôture, `etat.json.current_document` désigne déjà `livrables/version_finale.md`. Il ne faut donc pas comparer le corps à ce chemin : il faut retrouver le document examiné, cité dans l'en-tête et le bilan. Le premier instrument d'audit utilisait le mauvais chemin ; il a été rectifié avant toute conclusion. Les preuves consolidées indiquent le chemin examiné et une égalité effective des octets.

Sur le scénario, ce chemin est `echanges/0003-revision-1-A.md`. Sur chacune des sept collaborations réelles terminées, le corps du livrable et le document examiné correspondent également. Aucun défaut de promotion n'est retenu.

Le plafond de révisions ne vaut pas acceptation de tous les désaccords : les tests couvrent la livraison avec objections ouvertes et la correction ciblée demandée par l'humain après livraison. Les cas réels `nextcloud-clients`, `gui-v1/collab` et `Creation-prompt-2` montrent des acceptations avec objections encore ouvertes. Cela relève de l'arbitrage humain prévu, pas d'une erreur moteur à corriger en empêchant toute acceptation.

## 3. Reprise et incidents

`workflow.run` applique prévol, verrou, relecture, contrôle du corpus et intervention humaine avant de déterminer si le cycle continue. Les tests de reprise injectent des arrêts entre publications et vérifient le retraitement local des preuves durables. Les tests de transport font intervenir de vrais processus pour les tubes, délais et interruptions.

Dans le cas F03, le parseur est temporairement amené à refuser une réponse pourtant exploitable. Après rétablissement du parseur, `resume --reprocess` utilise les données brutes déjà conservées : A reste à un appel. Le cycle passe ensuite à B, qui est appelé une fois. Cette preuve isole précisément la différence entre le coût du retraitement et celui de la commande complète.

Le fonctionnement est prévu par `docs/COMMANDES.md` et la conception GUI. La correction minimale concerne donc les conseils CLI. Ajouter une nouvelle sous-commande ou un budget interne pour ce problème serait une extension inutile en l'absence d'un autre besoin utilisateur.

Le test de reprise sur la demande manuellement modifiée refuse avant lancement, contrairement à la lecture de l'acceptation : F02 est une lacune de consultation/décision, pas une absence générale de vérification des empreintes.

Le verrou vivant et les reprises de verrou mort sont couverts par la suite. Le refus d'un verrou illisible est voulu : une récupération automatique pourrait supprimer le verrou d'un détenteur encore vivant pendant sa création. Ce blocage explicite n'est pas compté comme un défaut d'ergonomie à supprimer.

Limite : la suite ne démontre pas la sûreté de toutes les courses possibles entre processus ni le comportement après coupure électrique. Aucune campagne nouvelle de concurrence intercomptes Windows n'a été réalisée. La lecture statique de `lock._is_pid_alive` montre qu'un échec d'ouverture du processus est ramené à « non vivant » sur Windows ; sans scénario reproduit distinguant les causes de cet échec dans l'usage prévu, ce point n'est pas élevé au rang de défaut avéré dans le rapport.

## 4. Décision et intégrité des artefacts

Le produit partage utilement ses décisions et actions permises : `decisions.allowed_actions` alimente les conseils CLI et la présentation GUI. Cette centralisation évite deux moteurs. Elle rend aussi visible la propagation d'un même défaut d'applicabilité vers `status`, `show`, l'écran GUI et le résumé PWF.

Matrice des reproductions conservées :

| Manipulation sur une copie acceptée | Résultat observé | Conclusion |
|---|---|---|
| Livrable inchangé | Acceptation applicable | Nominal conforme |
| Ajout dans le livrable | Ancienne acceptation non applicable | Détection conforme |
| Modification de l'analyse de la revue en conservant du JSON valide | Ancienne acceptation non applicable | Détection conforme ; diagnostic trop spécifique au livrable |
| Ajout dans `demande.md` | Acceptation toujours applicable | F02 |
| Retrait de `demande.md` par renommage | Acceptation toujours applicable | F02, variante absence |
| Retrait du livrable, puis nouvelle acceptation | Nouvelle acceptation, empreinte de livrable `null` | F01 |
| Retrait de la revue, puis nouvelle acceptation | Nouvelle acceptation, empreinte de revue `null` | F01 |

Ces manipulations supposent une intervention extérieure au moteur. Elles restent pertinentes pour un produit dont les dossiers sont lisibles et transportables et qui promet de signaler une décision ne correspondant plus au contenu. Elles ne prouvent pas que le cycle nominal détruit lui-même des fichiers.

Un premier essai de revue modifiée ajoutait du texte après le JSON : `show` levait alors `ContractError`. Une seconde contre-épreuve a modifié seulement le champ `analysis` dans un JSON valide et confirmé l'invalidation de la décision. La conclusion sur l'empreinte de revue repose sur cette seconde variante, pas sur la corruption syntaxique.

Le `ContractError` non transformé en refus lisible constitue une limite de robustesse de `show` sur des échanges manuellement corrompus. Il est conservé dans les preuves mais non priorisé comme un cinquième constat autonome : son impact et son déclencheur sont plus étroits que F01/F02, et une politique générale de récupération de fichiers corrompus n'est pas justifiée par cet audit.

Pour F01/F02, la recommandation est de renforcer les vérifications à l'endroit où une version est déclarée acceptable et applicable. Elle n'impose ni signature, ni nouveau registre, ni surveillance du disque. Le journal des décisions doit rester lisible et les acceptations anciennes rester conservées même lorsqu'elles cessent de s'appliquer.

## 5. GUI

La suite a réellement importé Tk et instancié des racines masquées. Elle ne se limite donc pas à tester des fonctions de présentation sans widgets. Les tests exercent création, navigation, suivi, cadrage, interventions, fermeture et passages CLI vers GUI et inversement.

Cela ne vaut pas une recette visuelle : disposition à différentes résolutions, navigation clavier, lisibilité réelle et ressenti d'utilisation n'ont pas été observés par une manipulation humaine de la fenêtre. Le rapport conserve ce point comme non vérifié.

Le correctif récent du suivi qui reprend le sondage après un état momentanément illisible passe avec la suite complète. Le défaut intermittent CLI connu ne disparaît pas pour autant. La campagne actuelle a exécuté une fois la suite complète ; elle ne constitue pas une estimation de fréquence des erreurs intermittentes.

Les interventions qui peuvent appeler un agent utilisent la confirmation commune. Les acceptations locales passent directement par `workflow.decide`, sous verrou. Cela correspond à la distinction attendue entre une décision sur fichier et une reprise pouvant consommer du quota.

La présentation GUI « Version acceptée » des reproductions F01/F02 provient de la façade réellement utilisée par les widgets. Le libellé est démontré par appel de cette façade ; aucune capture de fenêtre n'est revendiquée pour ces cas particuliers.

## 6. Isolation et fournisseurs

Les adaptateurs construisent des commandes distinctes pour les rôles A/B et pour F. Les tests vérifient les options attendues, les modèles, l'effort, le web et les extractions. Le noyau filtre l'environnement selon les politiques déclarées par les adaptateurs ; le dossier neutre ne contient qu'une copie du corpus.

Ces mécanismes ne forment pas un confinement global en lecture. Le programme choisit ce qu'il copie et les options qu'il demande ; l'effet réel d'une restriction appartient à la CLI. `docs/LIMITES.md` distingue correctement ces niveaux sur les points inspectés. Il n'y a pas lieu de classer l'absence de confinement général Codex comme un défaut nouveau : elle est une limite explicitement acceptée.

Les traces de F ont été analysées localement pour compter les identifiants distincts, sans publier leurs valeurs dans l'inventaire synthétique. Le filtre d'environnement observé et les configurations figurent dans les artefacts historiques. Aucune nouvelle invocation `claude` ou `codex`, même de qualification, n'a été nécessaire à l'audit.

La protection de l'audit contre les appels fournisseurs est une garde Python sur les lancements de processus connus, ajoutée par `sitecustomize` aux processus d'essai. Elle ne remplace pas la substitution explicite par les faux adaptateurs et ne prétend pas être un pare-feu système. Son témoin de blocage est absent : aucun lancement fournisseur intercepté n'a été tenté.

## 7. Lecture des collaborations réelles

Inventaire au moment de l'audit, distinct des descriptions initiales du prompt :

| Collaboration sous `C:/Projets/essais-3-1/` | État | Révision | Objections ouvertes | Entrées de décision |
|---|---|---:|---:|---:|
| `collab` | AWAITING_APPROVAL | 1 | 1 | 0 |
| `collab-inverse` | AWAITING_APPROVAL | 1 | 0 | 0 |
| `pieges-souris` | AWAITING_APPROVAL | 3 | 0 | 4 |
| `nextcloud-clients` | AWAITING_APPROVAL | 2 | 1 | 3 |
| `revision-nextcloud/collab` | AWAITING_APPROVAL | 1 | 0 | 1 |
| `gui-v1/collab` | AWAITING_APPROVAL | 1 | 3 | 1 |
| `Creation-prompt-2` | AWAITING_APPROVAL | 2 | 2 | 2 |
| `Creation-prompt` | WAITING_HUMAN | 0 | 0 | 0 |
| `cadrage-lot4/produit-claude` | READY | 0 | 0 | 0 |
| `cadrage-lot4/produit-codex` | READY | 0 | 0 | 0 |

Une « entrée de décision » peut être une correction ciblée ; ce nombre n'est pas un nombre d'acceptations. Les dates et types sont dans `real_collaborations.json`.

Les dix demandes courantes correspondent à l'empreinte de leur état. Les sept corps livrés correspondent à la version examinée nommée. Aucun `plan.json` n'est présent dans ces dossiers au moment de l'inventaire. Cela ne permet pas d'affirmer qu'aucune liaison n'a jamais existé dans leur histoire.

Les intentions A/B conservent une version observée de la CLI lorsqu'elle a été consignée. Elles ne constituent pas une attestation du commit exact du code DialogForge qui a créé la collaboration. Le rapprochement historique avec les journaux reste donc contextuel ; les essais actuels portent, eux, sur le commit et les modifications identifiés en tête du rapport.

Les dix arbres de fichiers ont été réinventoriés à la fin : contenu inchangé. La copie réelle employée pour PWF est distincte des originaux et aucun cycle n'a été lancé sur elle.

## 8. PWF et simplification

La liaison du produit tient ses promesses essentielles dans les essais : facultative, fichier séparé, refus d'une nouvelle liaison sans écraser l'ancienne, retrait sans modification des autres artefacts, absence d'écriture dans le plan. Le résumé est volontairement modeste, mais il donne une information exploitable pour un report humain.

La meilleure simplification identifiée porte sur le plan de développement lui-même. Une grande partie de `Next Step` répète des résultats déjà présents dans le journal. Le problème n'est pas un nombre de lignes interdit : des actions anciennes sont encore formulées comme des obligations courantes. L'exemple de l'acceptation GUI est démontré par `decisions.json`, pas déduit de la date récente d'un document.

Le plafond 2 000 de la façade/GUI est porté par la conception F acceptée et repris dans la phase 6. Les mentions de 1 200 dans la conception GUI d'origine sont historiques ; elles deviennent trompeuses quand des règles ou rappels de reprise les exposent sans l'exception applicable. Le rapport ne transforme pas ce décalage documentaire en dépassement de code.

La mesure indépendante retrouve exactement les nombres courants : `src/` 5 572, base 3 282, croissance 2 290 ; façade/GUI 1 537. Le compteur est décrit dans `audit_inventory.py` et détaillé par fichier. Une première version de l'agrégation GUI cherchait des séparateurs `/` dans des chemins Windows avec `\` ; elle a été corrigée en normalisant les chemins. Aucun constat produit ne repose sur la valeur intermédiaire erronée.

Les preuves historiques des hooks ont été retraitées avec le lecteur existant du dépôt, puis résumées sans recopier l'ensemble de la conversation. L'installation de la copie locale et son manifeste ne prouvent pas l'activation dans une session quelconque ; le rapport sépare donc code présent, lanceur configuré et livraison historique observée.

## 9. Pistes écartées ou non transformées en défaut

- **Ajouter une synchronisation PWF automatique :** aucun besoin bloquant démontré ; elle introduirait un second propriétaire de l'avancement.
- **Imposer zéro objection ouverte avant acceptation :** contredit l'arbitrage humain prévu et les cas acceptés en connaissance des réserves.
- **Interdire A et B avec le même outil :** permutations supportées, choix explicitement permis ; pas d'essai fournisseur supplémentaire requis par l'audit.
- **Déclarer toute la sécurité prouvée parce que les tests passent :** refusé ; les fournisseurs et permissions réelles demandent des preuves distinctes.
- **Reformater tout le produit :** le formatage n'est pas dans la porte adoptée et les écarts sont déjà connus.
- **Traiter les 1 717 lignes de journal comme un bug :** seules les contradictions opérationnelles sont retenues.
- **Déclarer une corruption de promotion depuis `current_document` après clôture :** erreur de méthode d'audit corrigée ; le document examiné est retrouvé dans l'en-tête/bilan.
- **Déclarer la recette du lot 6 F achevée et cocher le plan :** hors de cette session d'audit ; les résultats présents peuvent servir à l'arbitrage, mais le plan n'est pas modifié.

## 10. Résultat de la conservation

`file_changes.json` contient trois listes vides : aucun ajout, retrait ou changement de contenu dans l'arbre contrôlé hors dossier d'audit, `.git` et `.venv`. Les caches préexistants et les fichiers PWF locaux sont couverts par cet inventaire. Les autorisations, horodatages, profils utilisateur et fichiers internes exclus ne sont pas certifiés par ce mécanisme.

Les données d'essai retirées de leur chemin nominal sont conservées par renommage dans leurs copies. Le nettoyage des temporaires des tests a été laissé aux tests eux-mêmes, dans le répertoire temporaire d'audit. Aucun dossier réel du PO n'a été supprimé ou modifié.

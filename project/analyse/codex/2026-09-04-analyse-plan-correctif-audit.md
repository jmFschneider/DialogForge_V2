# Analyse Codex du plan correctif — 2026-09-04

> **Document examiné :** `project/correctifs/2026-09-04-plan-correctif-audit.md`, version observée
> sur `master` au commit `6eb2bf4`.
>
> **Objet :** répondre aux arbitrages D-4 à D-8, examiner N-01 et N-02, puis proposer les amendements
> nécessaires avant l'écriture du code.
>
> **Périmètre :** la taille du projet et le budget de lignes sont volontairement exclus de cet avis,
> conformément à l'arbitrage du PO.

## Verdict

Le plan de Claude est une bonne base : il comprend correctement les constats C-01 à C-11, propose
des correctifs locaux et exige pour chaque lot des tests capables de démontrer la régression. Les
options D-4, D-7 et D-8 vont dans la bonne direction.

Il ne doit toutefois pas être exécuté tel quel. Quatre points de conception doivent être corrigés
dans le plan avant le code :

1. la porte d'état du lot 1 est placée dans `_preflight`, alors que l'intervention du lot 2 doit être
   appliquée plus tard, sous verrou ; dans cet ordre, `resume --answer` serait refusé avant de pouvoir
   sortir de `WAITING_HUMAN` ;
2. la récupération proposée d'un verrou mort possède encore une course de suppression ;
3. le lot 7 ne garantit pas la borne annoncée tant que les `join()` partagent chacun leur propre
   délai et que `close()` est appelé sur des tubes encore lus par des pompes vivantes ;
4. le lot 10 masque les symptômes sans toujours rendre l'état durablement interprétable après une
   erreur survenue après la publication de `CALLING`.

**Recommandation générale :** amender le plan, fusionner conceptuellement les lots 1 et 2, puis
considérer les lots 1 à 5 comme préalables à tout appel réel payant.

## Réponses synthétiques aux décisions

| Décision | Avis Codex | Condition principale |
|---|---|---|
| D-4 | Accord avec l'option A, amendée | porte d'état sous verrou, après validation/application de l'intervention |
| D-5 | Désaccord sur `WAITING_HUMAN = 2` | `WAITING_HUMAN` est une fin normale de commande : code `0` |
| D-6 | Désaccord avec A comme « correctif » | documenter la limite maintenant, mais garder C-06 ouvert jusqu'à caractérisation |
| D-6b | Refus du chemin absolu | persister un argv assaini sans `argv[0]`, pas la commande résolue complète |
| D-7 | Accord avec A, amendée | deadline commune et aucun `close()` bloquant sur une pompe vivante |
| D-8 | Accord avec A | brut d'appel + JSON canonique d'échange, sans troisième artefact |
| D-8b | Accord pour retirer la promesse | retirer aussi la donnée `transformations` si elle reste sans consommateur |
| N-01 | Accord limité | retry seulement pour un `CONTRACT_ERROR` identifié et l'appel courant exact |
| N-02 | Accord, solution à préciser | préserver la cause initiale et lui ajouter une note de libération |
| Lot 4 | Re-hachage sous verrou | un seul re-hachage complet, placé au plus près de l'appel |

---

## D-4 et lots 1–2 — Porte d'état et intervention sous verrou

### Incohérence du plan actuel

Le lot 1 place une « porte unique dans `_preflight` » qui n'accepte que :

- `READY` sans appel courant ;
- `RUNNING` avec appel courant.

D-4 prévoit ensuite que l'intervention humaine soit appliquée après la relecture sous verrou. Or
`_preflight` s'exécute avant l'acquisition du verrou. Une collaboration en `WAITING_HUMAN` serait
donc rejetée avant que `--answer` puisse la faire passer à `READY`. Même contradiction pour un
`--retry-call` partant de `INTERRUPTED` ou, si N-01 est retenu, de `ERROR`.

### Proposition

La validation doit distinguer deux niveaux :

1. **prévol non mutant** : schémas, configuration, présence des fichiers requis, adaptateurs et
   paramètres ; il vérifie aussi que l'action demandée est compatible avec l'état observé, sans
   exiger que cet état soit déjà exécutable ;
2. **sous verrou, après relecture** :
   - vérifier à nouveau que l'action est applicable à l'état relu ;
   - appliquer l'intervention éventuelle ;
   - appliquer ensuite la porte d'état au nouvel état ;
   - seulement alors reprendre localement ou préparer un nouvel appel.

La porte d'état doit donc vivre sous verrou, pas seulement dans `_preflight`. Le prévol peut refuser
immédiatement les combinaisons manifestement impossibles, mais il ne doit pas empêcher une
intervention autorisée de produire l'état exécutable.

Les lots 1 et 2 touchent la même transition critique. Les réaliser comme un seul lot cohérent réduit
le risque de figer une API intermédiaire contradictoire. Si deux commits sont conservés, le lot 2
doit précéder la porte définitive du lot 1 ou le premier commit doit rester explicitement transitoire.

### Ne pas persister un état intermédiaire de retry

Pour `--retry-call`, il n'est pas nécessaire de publier d'abord `READY` avec `current_call=null`.
Après validation sous verrou, cet état peut rester en mémoire ; `new_call()` écrit l'intention portant
`retries` et `retry_reason`, puis publie directement le nouveau `RUNNING/current_call`.

Cela ferme la fenêtre où un crash ferait perdre le lien vers l'ancien appel et son motif avant la
création du nouvel appel.

### Rendre `--answer` idempotent après crash

Le déplacement sous verrou règle la concurrence mais pas l'atomicité entre :

1. l'archive de l'ancienne demande ;
2. le remplacement de `demande.md` ;
3. la publication de sa nouvelle empreinte dans `etat.json`.

Un crash entre ces écritures peut encore laisser une absence de demande ou une empreinte incohérente.
Le correctif doit donc définir une reprise idempotente de l'intervention. Une solution légère est :

- copier durablement l'ancienne demande vers l'archive avant de remplacer l'autorité, plutôt que la
  déplacer ;
- lors d'un nouveau `resume --answer`, accepter explicitement soit l'ancien hash attendu, soit le
  hash de la même réponse déjà écrite mais pas encore publiée dans l'état ;
- refuser toute troisième valeur comme divergence d'intégrité ;
- ne jamais créer deux archives pour la même intervention rejouée.

Cette règle doit être testée par injection d'un arrêt après chacune des trois écritures, sans vrai
appel fournisseur.

## Verrou — la création exclusive seule ne suffit pas à la récupération

L'acquisition normale par `O_CREAT | O_EXCL` corrige bien la course « fichier absent ». La procédure
proposée pour un verrou mort reste toutefois incorrecte :

1. P1 et P2 lisent le même verrou mort ;
2. P1 le supprime puis crée son nouveau verrou ;
3. P2 exécute ensuite sa suppression planifiée et supprime le verrou vivant de P1 ;
4. P2 crée le sien ; P1 et P2 entrent tous deux dans la section critique.

Le second `FileExistsError` prévu par le plan arrive trop tard : le danger se situe dans la
suppression du nouveau verrou par le second récupérateur.

### Options sûres proposées

Par ordre de simplicité :

1. **V0.1 minimale :** création exclusive, mais aucun effacement automatique d'un verrou mort ; le
   message indique le PID et demande une suppression humaine après vérification. C'est moins
   ergonomique, mais correct et sans course cachée.
2. **Verrou OS tenu ouvert :** verrou non bloquant fourni par l'OS, libéré automatiquement à la mort
   du processus, avec métadonnées séparées ou écrites sous le verrou. Cette option évite entièrement
   le problème des verrous périmés, au prix de deux petites branches Windows/POSIX à mesurer.
3. **Récupération automatique avec identité de fichier :** seulement si une primitive réellement
   conditionnelle permet de prouver que le fichier supprimé est encore celui qui a été lu. Une
   simple relecture de contenu réduit la fenêtre mais ne constitue pas une opération atomique.

Si la récupération automatique est conservée, elle doit faire l'objet d'un test à **trois processus** :
un verrou mort et deux récupérateurs simultanés, avec preuve qu'un seul entre.

Le verrou devrait également porter un `lock_id` aléatoire en plus du PID. `_release()` doit comparer
ce jeton exact : deux acquisitions du même processus ou un remplacement de verrou ne doivent jamais
autoriser la suppression sur la seule égalité du PID.

## D-5 — Codes de sortie

Je recommande la table suivante :

| Code | Signification |
|---:|---|
| 0 | commande accomplie normalement : `WAITING_HUMAN` ou `AWAITING_APPROVAL` |
| 1 | refus ou erreur locale attendue avant résultat de cycle |
| 2 | réservé à `argparse`, qui l'utilise déjà pour une erreur d'usage |
| 3 | transport interrompu : `INTERRUPTED` |
| 4 | réponse fournisseur inexploitable : `ERROR` |

`WAITING_HUMAN` est une issue métier normale, pas un échec. Lui attribuer `2` entre en collision avec
le code déjà employé par `argparse` et contredit l'orientation humaine du produit. Un consommateur
qui doit distinguer l'attente de la fin dispose de `status --json`. Le projet excluant l'exécution
autonome, optimiser le code de sortie pour une chaîne automatique n'est pas un motif suffisant.

La documentation doit par ailleurs préciser que le code décrit le résultat de **la commande**, pas
l'approbation du livrable : `AWAITING_APPROVAL` vaut zéro parce que le cycle demandé s'est arrêté au
point prévu, pas parce que le document est approuvé.

## D-6 — Frontière d'effets

### Une correction documentaire n'est pas une correction du risque

L'option A est nécessaire pour rendre la documentation honnête, mais elle ne résout pas C-06. Le
constat doit alors passer de `Ouvert` à `Risque accepté/limite déclarée`, pas à `Résolu`.

En particulier, renommer mentalement `supports_context_only` en « profil applicable même partiel »
affaiblit le sens du type sans protéger l'appelant. Un booléen nommé ainsi doit signifier que le
profil annoncé est effectivement supporté. Sinon il faut :

- déclarer la capacité fausse ;
- ou renommer le profil/capacité pour exprimer son caractère partiel ;
- ou caractériser et retirer les capacités restantes avant de déclarer la valeur vraie.

Je recommande donc une trajectoire en deux temps :

1. corriger immédiatement les garanties documentaires et marquer explicitement le risque ;
2. caractériser les modes restreints actuels avant toute mission réelle utilisant Claude avec ses
   outils ou Codex en `CONTEXT_ONLY`.

Une première validation réelle peut contourner provisoirement C-06 uniquement si elle utilise une
combinaison déjà mécaniquement en lecture seule, dans une collaboration jetable et isolée du projet.

### D-6b — Ne pas persister le chemin absolu de l'exécutable

La preuve recherchée concerne les options demandées à l'adaptateur, pas l'emplacement local du shim.
Il suffit de persister un tableau d'arguments assaini, par exemple `invocation_args`, sans `argv[0]`.
`adapter_id` et `observed_version` sont déjà présents.

Avantages :

- aucune réouverture de la règle sur les chemins absolus ;
- collaboration toujours portable et moins bavarde sur la machine source ;
- aucun risque qu'un futur adaptateur persiste un secret passé en argument ;
- comparaison directe des drapeaux, sans reconstruction d'une ligne shell.

Cette donnée doit être décrite comme **trace de l'argv demandé**, pas comme preuve des capacités
effectives : configuration utilisateur, hooks et évolution de la CLI peuvent encore modifier le
comportement réel.

## Lot 4 — Corpus

Le schéma strict, les tailles, les SHA-256, les absents et les surnuméraires proposés sont pertinents.
La validation doit aussi refuser un lien symbolique apparu dans `corpus/fichiers`, notamment s'il
pointe hors de l'instantané.

Je ne recommande pas deux re-hachages. Le contrôle complet doit être effectué **une seule fois sous
verrou**, après la relecture du manifeste et immédiatement avant la construction/l'exécution de
l'appel. Le verrou étant déjà conservé pendant l'appel, cela protège contre les autres processus
IAbinome sans doubler le coût.

Cela ne protège pas contre un éditeur ou un autre programme ignorant `verrou.json` pendant que
l'agent lit. La promesse exacte doit donc devenir : « contenu vérifié contre le manifeste avant
chaque appel », et non une immutabilité physique que le programme ne peut imposer.

C-04 doit rester bloquant pour une première mission de recherche. C-05 doit rester bloquant pour
toute mission réelle, car un incident ou un déplacement de collaboration peut exercer la reprise.

## Lot 5 — Intégrité de reprise

Le correctif proposé est juste, avec trois précisions :

- une absence de `stdout.txt` ou `stderr.txt` alors que `resultat.json` existe est elle aussi une
  divergence d'intégrité, pas une erreur d'entrée-sortie générique ;
- `prompt.txt` doit être vérifié avant toute branche de reprise, y compris `RESPONSE_STORED` ;
- les fabriques de `tests/test_recovery.py` utilisent actuellement des empreintes factices composées
  de zéros : elles devront produire les vraies tailles et empreintes, faute de quoi les tests de
  reprise nominale deviendront eux-mêmes des scénarios de corruption.

Une exception typée telle que `IntegrityError`, transformée par le moteur en
`INTEGRITY_MISMATCH/INTERRUPTED`, est préférable à un `ValueError` générique. Aucun appel ne doit être
émis automatiquement après cette divergence.

## D-7 — Borne de nettoyage des processus

Je confirme le choix de l'option A : le besoin prioritaire est de ne jamais présenter un flux
incertain comme complet. Un objet Job Windows n'est pas nécessaire pour ce résultat en V0.1.

Le correctif décrit n'est cependant pas encore suffisant pour garantir `2 × _GRACE_SECONDS` :

- les deux pompes reçoivent chacune `_GRACE_SECONDS`, deux fois, soit jusqu'à quatre périodes de
  grâce avec les boucles actuelles ;
- `_terminate_tree()` peut ajouter son propre `proc.wait(timeout=_GRACE_SECONDS)` ;
- `proc.stdout.close()` ou `proc.stderr.close()` peut attendre le lecteur concurrent encore bloqué.

Reproduction pendant cette contre-analyse : parent sorti immédiatement, descendant ayant conservé
les tubes pendant 22 secondes. `transport.run()` a rendu après **22,11 s**, avec
`outcome=COMPLETED` et `resultat.json` présent. La tentative de terminaison n'avait donc ni borné la
durée, ni changé l'issue.

### Proposition

- utiliser une échéance absolue commune pour joindre toutes les pompes, et non un délai complet par
  pompe ;
- après tentative de terminaison, utiliser une seconde échéance commune clairement documentée ;
- si une pompe reste vivante, produire `STREAMS_UNCLOSED`, ne pas écrire `resultat.json` et **ne pas
  appeler `close()` depuis le coordinateur sur le flux encore lu** ;
- accepter que le thread daemon et son descripteur vivent jusqu'à la fin réelle du descendant, ou
  choisir ultérieurement une primitive OS capable d'annuler la lecture ;
- ne pas présenter `pid.txt` comme moyen de retrouver l'orphelin : il contient le PID du parent mort,
  pas ceux de ses descendants.

Le test doit vérifier à la fois l'issue, l'absence de résultat et une borne de temps supérieure avec
une marge adaptée à la machine de CI.

## D-8 — JSON canonique et transformations

Accord avec l'option A :

- `appels/.../reponse_brute.txt` reste la preuve exacte de la réponse extraite ;
- `echanges/NNNN-critique-B.json` devient l'autorité canonique utilisée par le cycle ;
- `revue_normalisee.json` est retiré de l'arborescence documentaire.

`Review.to_dict()` doit sérialiser explicitement les `.value` des enums, conserver `analysis` et
émettre `severity` systématiquement, y compris `UNKNOWN`. Le test avec bloc clôturé est le bon test
de régression.

Aucun consommateur actuel n'exige une liste persistée des transformations. La différence entre brut
et canonique permet de refaire le diagnostic. Il est donc raisonnable de retirer « consigné comme
transformation » de la promesse. Si `Normalized.transformations` reste ensuite inutilisé hors de ses
tests, le plan devrait aussi décider de le supprimer ou de nommer son futur consommateur ; conserver
une donnée calculée sans usage entretiendrait la même ambiguïté.

## N-01 — Sortie de `ERROR`

Accord sur le principe d'une relance humaine après erreur de contrat. Elle ne doit toutefois pas
être autorisée sur tout statut `ERROR` futur par une simple condition élargie.

Conditions recommandées :

- `status == ERROR` ;
- `current_call` présent et identifiant égal à `--retry-call` ;
- `last_incident` lisible, appartenant à cet appel et de type `CONTRACT_ERROR` ;
- motif de relance non vide ;
- nouveau call ID et lien `retries` conservés comme pour `INTERRUPTED`.

Si d'autres familles d'erreur deviennent récupérables, elles doivent être ajoutées explicitement à
une table, pas héritées implicitement de l'enum `ERROR`.

## N-02 — Ne pas masquer l'exception initiale

Le constat est valide. En cas d'échec du corps puis d'échec de `_release`, la cause du corps doit
rester l'exception principale. L'échec de libération ne doit cependant pas disparaître.

Proposition : capturer la cause principale, tenter la libération, puis lui ajouter une note
(`BaseException.add_note`, disponible en Python 3.12) indiquant que le verrou n'a pas été libéré.
Sans cause principale, l'erreur de libération continue d'être levée normalement.

Cette correction complète, mais ne remplace pas, l'ajout d'une identité `lock_id` vérifiée à la
libération.

## Lot 8 — Validation numérique

Les convertisseurs `argparse` et la validation de `max_revisions` au chargement sont justes. Le délai
doit aussi être validé à l'entrée de `workflow.run()` ou de `transport.run()`, car ces fonctions sont
appelées directement par les tests et constituent une surface Python indépendante de la CLI.

La validation doit avoir lieu avant `Popen` et, dans le moteur, avant toute publication de `CALLING`.

Proposition complémentaire de faible portée : `_schema_version()` accepte actuellement `True` comme
version `1`, car `True == 1`. Le lot de validation devrait refuser explicitement les booléens, comme
le fait déjà `_int()`.

## Lot 10 — Erreurs CLI

L'objectif « erreurs attendues sans traceback, défauts de programmation bruyants » est bon. Capturer
globalement `ValueError` ne le réalise pas : un `ValueError` accidentel dans le moteur serait lui
aussi transformé en message utilisateur.

Il faut préférer des exceptions de frontière explicites (`SchemaError`, `WorkflowError`,
`LockError`, `TransportError`, `UnicodeError`, erreurs JSON et I/O attendues) ou envelopper les erreurs
attendues en `WorkflowError` au niveau qui connaît leur sens.

Surtout, certaines erreurs surviennent après `CALLING` et exigent plus qu'un affichage propre :

- `adapter.command()` peut échouer après la publication de l'état ;
- `Popen` peut lever `TransportError`, ce qui prouve au contraire que l'appel n'a pas démarré ;
- le décodage UTF-8 peut échouer alors que `resultat.json` prouve que les flux sont complets.

Le plan doit attribuer à chacune un état et un incident persistants. Proposition :

- construire la commande avant de publier `CALLING` lorsque cela est possible ;
- si `Popen` échoue, consigner `LAUNCH_FAILED` sans prétendre que l'appel est possiblement payé ;
- si l'extraction/décodage échoue après une sortie complète, consigner `EXTRACTION_FAILED` ou
  `DECODE_FAILED` avec les flux préservés ;
- laisser la reprise locale retenter uniquement l'extraction lorsqu'aucun appel supplémentaire
  n'est nécessaire.

Sans cette classification, l'enveloppe du lot 10 supprime la traceback mais laisse au lancement
suivant un faux `CALL_POSSIBLY_PAID` ou la même erreur sans chemin de reprise.

## Priorité et ordre révisés

1. **Lot commun état/verrou/intervention** — C-01, C-02, D-4, N-02 et protocole de crash de
   `--answer`/`--retry-call`.
2. **Codes de sortie** — C-03 avec `WAITING_HUMAN = 0`.
3. **Intégrité de reprise** — C-05.
4. **Corpus vérifié sous verrou** — C-04.
5. **Validation numérique** — C-08, avant les essais de transport complémentaires.
6. **Nettoyage borné** — C-07 avec deadline commune et flux vivants non fermés par le coordinateur.
7. **Classification des erreurs** — C-10, coordonnée avec les nouveaux incidents des lots précédents.
8. **Revue canonique** — C-09 / D-8.
9. **Frontière d'effets** — documentation immédiate, puis caractérisation avant les permutations
   réelles concernées.
10. **Validations réelles et guide** — seulement après fermeture de C-01 à C-05 et décision C-06.

## Conditions avant première mission réelle

Je maintiens la recommandation de l'audit initial : C-01 à C-05 doivent être fermés avant tout cycle
payant. Si le PO veut fractionner la validation :

- aucune mission avant C-01, C-02, C-03 et C-05 ;
- aucune mission de recherche avant C-04 ;
- aucune permutation utilisant un profil non mécaniquement caractérisé avant la décision C-06 ;
- les tests faux agents, Ruff et mypy doivent être verts sur le commit exact essayé ;
- la version des deux CLI et l'argv assaini doivent être consignés.

## Conclusion proposée pour le plan vivant

Le plan peut passer de « soumis à Codex » à « avis reçu — amendements requis ». Les décisions
proposées sont :

- D-4 : A amendée ;
- D-5 : `WAITING_HUMAN = 0` ;
- D-6 : correction documentaire immédiate, mais risque non clos avant caractérisation ;
- D-6b : argv assaini sans chemin absolu ;
- D-7 : A amendée par une vraie deadline de nettoyage ;
- D-8 et D-8b : A, sans consommateur persistant des transformations ;
- N-01 : accepté seulement pour `CONTRACT_ERROR` ;
- N-02 : accepté avec conservation et annotation de la cause première ;
- lot 4 : un re-hachage complet sous verrou, pas deux.

Une fois ces points intégrés dans le document vivant, l'implémentation peut commencer sans nouvel
arbitrage technique Codex. Les choix métier restants — notamment l'acceptation du risque C-06 —
restent du ressort du PO.


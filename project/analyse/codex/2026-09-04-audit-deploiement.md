# Audit Codex du déploiement — 2026-09-04

> **Nature du document :** revue indépendante de l'implémentation et de sa préparation au premier
> usage réel.
>
> **Périmètre :** code de production, tests, configuration de paquet, adaptateurs CLI, reprise,
> concurrence, intégrité des artefacts et état opérationnel du dépôt.
>
> **Exclusion demandée par le PO :** la taille du projet est assumée et n'est ni un constat ni un
> critère de sévérité dans cet audit.

## Verdict

L'implémentation est structurée, documentée et couverte par une suite de tests substantielle, mais
elle n'est pas encore sûre pour un premier cycle payant. Deux défauts peuvent provoquer un appel
fournisseur non voulu ou laisser une collaboration modifiée malgré l'échec déclaré d'une commande.
Trois autres défauts affaiblissent les garanties annoncées sur l'intégrité du corpus, la reprise et
les codes de sortie.

**Recommandation :** corriger au minimum C-01 à C-05 avant une première mission réelle. C-06 doit
être arbitré avant de présenter la frontière d'effets comme une garantie mécanique.

## Contrôles effectués

État observé au moment de l'audit :

- branche `master`, HEAD `bdee472` ;
- dépôt propre au début de l'audit ; aucun fichier existant modifié par les contrôles ;
- construction du wheel réussie ;
- `pytest` : **196 réussis, 1 ignoré, 10 sous-tests réussis** ;
- `ruff check .` : réussi ;
- `mypy --strict src tests` : réussi ;
- aucune vraie requête fournisseur lancée pendant l'audit.

Les versions CLI observées sont Claude Code `2.1.260` et Codex CLI `0.153.2`. La caractérisation du
projet porte respectivement sur `2.1.259` et `0.151.0`.

## Constats à suivre

| ID | Sévérité | État | Résumé |
|---|---|---|---|
| C-01 | Bloquant | Ouvert | `run` exécute un nouvel appel depuis `WAITING_HUMAN` et plante depuis `CLOSED` |
| C-02 | Bloquant | Ouvert | `resume` modifie la collaboration avant le verrou ; acquisition non atomique |
| C-03 | Élevée | Ouvert | `ERROR` et `INTERRUPTED` retournent un code processus `0` |
| C-04 | Élevée | Ouvert | le contenu du corpus n'est pas vérifié après `new` |
| C-05 | Élevée | Ouvert | les tailles et empreintes des flux ne sont pas vérifiées à la reprise |
| C-06 | Élevée | À arbitrer | la frontière d'effets n'est pas mécaniquement garantie par les adaptateurs |
| C-07 | Moyenne | Ouvert | la terminaison d'arbre perd sa borne si le parent sort avant ses descendants |
| C-08 | Moyenne | Ouvert | les paramètres numériques invalides ne sont pas refusés |
| C-09 | Moyenne | Ouvert | l'artefact de revue normalisée annoncé n'est pas produit |
| C-10 | Moyenne | Ouvert | plusieurs erreurs techniques échappent au contrat d'erreur de la CLI |
| C-11 | Opérationnelle | Ouvert | les validations réelles prévues ne sont pas encore exécutées |

---

## C-01 — La porte humaine peut être contournée

**Sévérité : bloquante.**

### Observation

`workflow.run()` vérifie `state.status` seulement après avoir exécuté une itération. Au début de
l'itération, la présence de `current_call` décide entre reprise et nouvel appel, quel que soit le
statut global.

Conséquences reproduites avec les faux adaptateurs :

- après une réponse `IABINOME:QUESTION`, un second `run` lance de nouveau A sans nouvelle demande ;
- deux `run` successifs en `WAITING_HUMAN` ont donc produit **deux appels** ;
- après `AWAITING_APPROVAL` / phase `CLOSED`, un nouveau `run` provoque
  `KeyError: <Phase.CLOSED: 'CLOSED'>`.

### Références

- `src/iabinome/workflow.py:82-92` — boucle et contrôle tardif du statut ;
- `src/iabinome/workflow.py:161-163` — indexation directe de `_ROLE_OF_PHASE`.

### Risque

Appel payant non demandé, contournement de l'arbitrage humain et plantage d'une commande pourtant
valide syntaxiquement.

### Critères de résolution

- refuser ou rendre sans appel les statuts `WAITING_HUMAN`, `ERROR` et `AWAITING_APPROVAL` ;
- définir explicitement les statuts autorisés pour une reprise locale après crash ;
- tester un second `run` après `QUESTION`, après `BLOQUE`, après `ERROR` et après fermeture ;
- prouver que le compteur d'appels du faux adaptateur reste inchangé dans chaque cas interdit.

## C-02 — Le verrou ne protège pas toutes les mutations

**Sévérité : bloquante.**

### Observation A — mutation avant acquisition

`cmd_resume()` applique `--answer` ou prépare `--retry-call` avant d'appeler `_drive()`. Or le verrou
n'est acquis que dans `workflow.run()`.

Reproduction : avec `verrou.json` déjà détenu, `resume --answer` retourne le code `1`, mais :

- `demande.md` est remplacé ;
- l'ancienne demande est archivée ;
- `etat.json` passe quand même à `READY`.

La commande annonce donc un échec après avoir modifié durablement la collaboration.

### Observation B — acquisition non atomique

`lock._try_acquire()` fait successivement :

1. `path.exists()` ;
2. lecture éventuelle du détenteur ;
3. remplacement atomique du fichier par son propre verrou.

Deux processus peuvent tous deux constater l'absence du fichier puis publier chacun leur verrou.
`os.replace()` rend chaque écriture atomique, mais ne rend pas atomique la décision « créer seulement
s'il n'existe pas ».

### Références

- `src/iabinome/cli.py:107-127` — intervention avant `_drive()` ;
- `src/iabinome/cli.py:130-167` — mutations de `demande.md` et `etat.json` ;
- `src/iabinome/lock.py:53-65` — séquence non atomique d'acquisition.

### Risque

État partiellement appliqué, deux moteurs concurrents, appels en double, écrasement de `etat.json` et
perte de la traçabilité du motif de relance.

### Critères de résolution

- faire entrer toute mutation de `resume` sous le même verrou que le moteur ;
- relire et valider l'état après acquisition, avant mutation ;
- acquérir le verrou par création exclusive atomique, avec une procédure explicite de récupération
  d'un verrou mort ;
- tester le refus de `resume --answer` et de `resume --retry-call` sous verrou détenu en prouvant
  qu'aucun octet persistant n'a changé ;
- ajouter un test de course entre deux processus, pas seulement entre deux objets simulés.

## C-03 — Une erreur opérationnelle retourne le succès au système

**Sévérité : élevée.**

### Observation

Une fois que `workflow.run()` a rendu un `State`, `_drive()` affiche le statut puis retourne toujours
`0`. Cela inclut `ERROR` et `INTERRUPTED`, donc notamment :

- erreur de contrat ;
- délai dépassé ;
- interruption utilisateur capturée par le transport ;
- dépassement de sortie ;
- code fournisseur non nul (`CLI_FAILED`).

Reproduction : une sortie agent sans balise a produit `status=ERROR` avec `exit_code=0`.

Le test CLI du délai attend actuellement lui aussi le code `0` : le défaut est donc stabilisé par la
suite plutôt que détecté.

### Références

- `src/iabinome/cli.py:171-183` ;
- `tests/test_cli.py:178-185`.

### Risque

Un script, un terminal ou une chaîne CI considère une mission interrompue comme réussie. La
documentation annonce en outre un code non nul pour Ctrl-C, ce que ce chemin ne respecte pas.

### Critères de résolution

- définir la table de codes de sortie par statut ;
- retourner un code non nul pour `ERROR` et `INTERRUPTED` ;
- décider explicitement du code de `WAITING_HUMAN` et `AWAITING_APPROVAL` ;
- tester chaque statut observable depuis la CLI.

## C-04 — Le corpus n'est pas réellement figé

**Sévérité : élevée.**

### Observation

Le prévol compare uniquement l'empreinte du texte de `corpus/manifeste.json` à celle de la
configuration. Les entrées du manifeste ne sont pas relues et les fichiers sous `corpus/fichiers/`
ne sont jamais comparés à leur taille et leur SHA-256.

Reproduction : après `new`, le contenu d'un fichier copié a été remplacé par `ALTERE`. `run` a accepté
la collaboration et appelé l'adaptateur.

### Référence

- `src/iabinome/workflow.py:139-148`.

### Risque

A et B peuvent travailler sur des corpus différents selon le moment de l'appel, alors que le
livrable continue d'afficher « corpus figé ». La provenance et la reproductibilité de la recherche
sont compromises.

### Critères de résolution

- valider strictement le schéma du manifeste ;
- recalculer taille et SHA-256 de chaque fichier avant appel ;
- refuser les fichiers absents et décider du traitement des fichiers supplémentaires ;
- refaire sous verrou les vérifications critiques susceptibles de changer après le prévol ;
- ajouter des tests pour fichier altéré, absent, ajouté et manifeste incohérent.

## C-05 — Les preuves d'intégrité ne sont pas utilisées à la reprise

**Sévérité : élevée.**

### Observation

`resultat.json` conserve tailles et SHA-256 de `stdout.txt` et `stderr.txt`. `read_result()` vérifie
leur présence et leur type dans le JSON, mais ne les compare jamais aux fichiers réels.

Reproduction : après une sortie propre, `stdout.txt` a été remplacé. `read_result()` a malgré cela
retourné un résultat valide.

Le même défaut existe pour `RESPONSE_STORED` : `reponse_brute.txt` est normalisé et réappliqué sans
comparaison à `current_call.response_sha256`. `prompt_sha256` n'est pas non plus revérifié.

### Références

- `src/iabinome/transport.py:159-176` ;
- `src/iabinome/workflow.py:228-248`.

### Risque

Après copie, altération ou corruption partielle d'une collaboration, le moteur peut traiter comme
réponse payée des octets différents de ceux attestés par `resultat.json`.

### Critères de résolution

- comparer tailles et empreintes des deux flux dans `read_result()` ;
- vérifier `response_sha256` avant de réappliquer une réponse stockée ;
- vérifier `prompt_sha256` avant toute reprise qui dépend du prompt ;
- traiter toute divergence comme incident d'intégrité, sans nouvel appel automatique ;
- couvrir les trois altérations par des tests de reprise.

## C-06 — La frontière d'effets dépend encore du comportement des agents

**Sévérité : élevée ; arbitrage nécessaire sur la promesse exacte.**

### Claude

La commande de base est `claude -p --model MODELE`. A reçoit donc les outils par défaut ; B les
reçoit également en profil `CONSULT`. Seul `CONTEXT_ONLY` ajoute `--tools ""`.

Le prompt de A demande de ne rien modifier, mais la conception rappelle correctement qu'un prompt ne
confine rien. B en `CONSULT` ne reçoit même pas cette phrase. L'absence d'écriture observée lors de la
caractérisation est une mesure ponctuelle, pas une garantie mécanique.

La version Claude actuellement installée expose notamment `--restricted`, `--safe-mode`,
`--permission-prompts none` et `--no-session-persistence`. Ces possibilités doivent être
caractérisées ensemble : certaines changent aussi le chargement de l'authentification ou des
personnalisations utilisateur.

### Codex

Codex utilise bien `--sandbox read-only`, mais le profil `CONTEXT_ONLY` ne désactive que
`shell_tool`. Le code déclare pourtant `supports_context_only=True`. La documentation reconnaît que
les autres capacités n'ont pas été neutralisées.

La version installée propose désormais `--ephemeral` et `--ignore-user-config`, absents de la commande
actuelle.

### Références

- `src/iabinome/adapters/claude.py:35-40` ;
- `src/iabinome/adapters/codex.py:22-42` ;
- `conception/CONCEPTION_FINALE.md`, §1, §8 et §12.3.

### Risque

Écriture hors du périmètre prévu, influence de règles, hooks, plugins, mémoires ou configurations
utilisateur, et profil `CONTEXT_ONLY` plus permissif que son nom.

### Critères de résolution

- fixer par écrit si la non-écriture est une garantie ou seulement une limite déclarée ;
- caractériser les modes restreints sur les versions effectivement installées ;
- ne déclarer `supports_context_only=True` que si toutes les capacités pertinentes sont retirées ;
- sinon renommer ou refuser ce profil pour l'adaptateur concerné ;
- tester manuellement les quatre permutations dans un environnement jetable après toute évolution
  des commandes d'adaptateur.

## C-07 — Cas incomplet de terminaison d'arbre

**Sévérité : moyenne.**

### Observation

Quand le processus principal sort mais qu'un descendant conserve les tubes, `_wait()` conclut
`COMPLETED`. Après une grâce, `_terminate_tree()` tente ensuite `taskkill` avec le PID du parent déjà
terminé. Ce PID ne permet pas nécessairement de retrouver la descendance.

Le test actuel couvre le cas où le parent est encore vivant lors du timeout, pas celui où il sort
avant son descendant. Un essai ciblé a montré qu'un descendant continuait jusqu'à son terme malgré
la tentative de nettoyage ; l'attente de fermeture des tubes peut alors dépasser les périodes de
grâce prévues.

### Références

- `src/iabinome/transport.py:124-155` ;
- `src/iabinome/transport.py:210-232` ;
- `tests/test_transport.py`, classe `TestProcessTree`.

### Critères de résolution

- tester un parent qui engendre un descendant long puis sort immédiatement ;
- garantir une borne sur toute la phase de nettoyage ;
- ne publier `resultat.json` que si les deux pompes sont effectivement terminées ;
- conserver un moyen de cibler le groupe ou l'arbre indépendamment de la survie du parent.

## C-08 — Paramètres numériques non validés

**Sévérité : moyenne.**

### Observation

`--timeout` accepte zéro, les nombres négatifs, `inf` et `nan`. Avec `nan`, la comparaison
`time.monotonic() >= deadline` reste toujours fausse et le délai ne se déclenche jamais.
`--max-revisions` accepte également les valeurs négatives.

### Références

- `src/iabinome/cli.py:246` ;
- `src/iabinome/cli.py:249-256` ;
- `src/iabinome/transport.py:179-192`.

### Critères de résolution

- exiger un délai fini et strictement positif ;
- exiger `max_revisions >= 0` ;
- valider également ces contraintes lors du chargement d'une configuration persistée.

## C-09 — Revue normalisée absente

**Sévérité : moyenne.**

### Observation

L'arborescence de la spécification annonce `revue_normalisee.json` dans le dossier de chaque appel B.
Le moteur ne le produit jamais. Il écrit la réponse normalisée seulement sous
`echanges/*-critique-B.json`.

Comme le contrat accepte un bloc JSON clôturé, ce fichier portant l'extension `.json` peut contenir
des délimiteurs Markdown et ne pas être un JSON directement lisible par un outil externe. Les
transformations de normalisation calculées par `contracts.normalize()` ne sont pas persistées non
plus, malgré le vocabulaire « consigné comme transformation ».

### Références

- `conception/CONCEPTION_FINALE.md:167-182` ;
- `src/iabinome/workflow.py:284-289` ;
- `src/iabinome/contracts.py:38-62`.

### Critères de résolution

- soit produire le véritable JSON normalisé annoncé ;
- soit corriger explicitement la spécification et l'extension de l'artefact ;
- persister les transformations si elles font partie de la preuve promise.

## C-10 — Contrat d'erreur CLI incomplet

**Sévérité : moyenne.**

### Observation

`_drive()` ne capture que `WorkflowError` et `LockError`. Selon le point d'échec, une erreur JSON,
une erreur de schéma, une erreur d'entrée-sortie, un décodage UTF-8 invalide ou `TransportError` peut
donc produire une traceback et laisser `current_call` dans un état à interpréter au prochain
lancement.

`status` ne possède aucune enveloppe d'erreur utilisateur.

### Références

- `src/iabinome/cli.py:171-183` ;
- `src/iabinome/cli.py:186-209` ;
- `src/iabinome/workflow.py:194-218`.

### Critères de résolution

- définir quelles erreurs deviennent un incident persistant et lesquelles sont un refus sans
  mutation ;
- présenter les erreurs attendues sans traceback ;
- réserver les exceptions inattendues aux défauts de programmation ;
- tester au moins JSON illisible, état invalide, échec de `Popen` et sortie non UTF-8.

## C-11 — Validation opérationnelle inachevée

**Sévérité : opérationnelle.**

`project/NOTES.md` indique encore comme non réalisées :

- le déplacement réel d'une collaboration en cours d'usage ;
- une première mission réelle de conception ;
- une première mission réelle de recherche.

La construction du paquet fonctionne, mais le dépôt ne possède pas encore de guide d'installation et
d'exploitation autonome destiné à un utilisateur. Les documents de conception décrivent les
commandes, sans constituer un parcours de mise en service.

### Critères de résolution

- exécuter les trois validations après correction des constats bloquants ;
- consigner versions, commandes, résultats, incidents et coût approximatif ;
- ajouter un guide minimal : installation, prérequis CLI, authentification, premier `new`, lecture
  des statuts, reprise et localisation du livrable.

## Points solides observés

- séparation claire entre moteur, transport, contrats, persistance et adaptateurs ;
- écritures atomiques avec `fsync` et nouvelle tentative Windows ;
- publication de `CALLING` avant `Popen` ;
- conservation des sorties brutes et des intentions d'appel ;
- plafond de sortie par flux ;
- absence de rejeu automatique après appel incertain ;
- tests contre de vrais sous-processus locaux, sans appel fournisseur ;
- permutations A/B couvertes par les faux adaptateurs ;
- paquet Python constructible sans dépendance d'exécution Python.

Ces qualités constituent une bonne base. Elles ne compensent toutefois pas C-01 et C-02, car ces
deux défauts se situent précisément sur les portes qui doivent empêcher les appels et mutations non
autorisés.

## Ordre de traitement recommandé

1. C-01 — imposer les portes d'état avant tout appel.
2. C-02 — rendre verrouillage et intervention humaine atomiques.
3. C-03 — corriger les codes de sortie.
4. C-04 et C-05 — rendre effectives les garanties d'intégrité.
5. C-06 — arbitrer puis caractériser les profils d'adaptateur.
6. C-07 à C-10 — durcir transport, validation et diagnostic.
7. C-11 — effectuer les trois validations réelles et écrire le guide d'usage.

## Règle de clôture de cet audit

Un constat n'est marqué résolu qu'avec :

1. un correctif identifié ;
2. un test qui échouait auparavant et réussit après correction ;
3. la commande de validation exécutée ;
4. le commit correspondant ;
5. la mise à jour de la colonne **État** du tableau de suivi.

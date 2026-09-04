# Analyse Claude de l'audit Codex — 2026-09-04

> **Nature du document :** contre-lecture de `project/analyse/codex/2026-09-04-audit-deploiement.md`,
> avec relecture directe du code cité (`workflow.py`, `cli.py`, `lock.py`, `transport.py`,
> `adapters/claude.py`, `adapters/codex.py`). Pas une seconde revue indépendante complète : les
> constats marqués « vérifié » ont été confrontés ligne à ligne au code ; les autres restent repris
> tels quels, avec le niveau de confiance indiqué.
>
> **Périmètre exclu, comme pour l'audit :** la taille du projet n'est ni un constat ni un critère ici
> (arbitrage PO du 2026-09-04, `NOTES.md`).

## Verdict

L'audit est fondé. Les six constats les plus graves (C-01 à C-06) ont été vérifiés directement dans
le code : chacun se reproduit par simple lecture, sans qu'aucune extrapolation ne soit nécessaire. Les
références de fichier et de ligne sont exactes. Aucun désaccord de sévérité.

Le point le plus utile pour le PO n'est pas dans le tableau de l'audit lui-même : **la « prochaine
action » actuelle de `NOTES.md` — lancer une mission réelle payante pour observer le cycle — est
exactement le scénario que C-01 et C-02 rendent dangereux.** Voir §Synthèse ci-dessous avant de
lancer quoi que ce soit.

## Constats vérifiés contre le code

### C-01 — porte humaine contournable (bloquant) — confirmé

`workflow.run()` (`workflow.py:82-92`) décide *resume* vs *nouvel appel* sur la seule présence de
`current_call`, avant toute lecture de `state.status`. Or `apply_a` met `current_call=None` en même
temps que `status=WAITING_HUMAN` pour une `QUESTION` (`workflow.py:264-268`). Un second `run` retombe
donc dans la branche `else: engine.new_call(...)` et relance l'agent — aucune vérification de statut
ne s'y oppose. Pour `Phase.CLOSED`, `_ROLE_OF_PHASE` (`workflow.py:51-56`) ne contient pas cette
phase : `new_call` lève bien un `KeyError` non typé à la ligne `role = _ROLE_OF_PHASE[state.phase]`.
Les deux reproductions de l'audit sont exactes.

### C-02 — verrou incomplet (bloquant) — confirmé, sur les deux volets

**Volet A.** `cmd_resume()` (`cli.py:107-127`) appelle `_apply_answer()` ou `_prepare_retry()` **avant**
`_drive()` → `workflow.run()`, seul point qui acquiert `verrou.json`. `_apply_answer` (`cli.py:130-142`)
archive et réécrit `demande.md`, puis republie `etat.json` en `READY`, sans verrou. Si `_drive()` échoue
ensuite sur `LockHeld`, la commande retourne `1` alors que la collaboration a déjà changé d'état
durablement. Confirmé par lecture, pas seulement par la reproduction de l'audit.

**Volet B.** `lock._try_acquire()` (`lock.py:53-65`) : `path.exists()` → lecture éventuelle →
`storage.write_atomic_text()`. Aucune de ces trois étapes n'est une création exclusive
(`O_CREAT|O_EXCL`) ; deux processus peuvent traverser le test d'existence avant que l'un des deux
n'écrive. `os.replace()` (dans `write_atomic_text`, à vérifier mais cohérent avec le nom) rend chaque
écriture individuellement atomique, ce qui ne protège pas la décision « personne d'autre ne détient
le verrou ». Confirmé.

### C-03 — code de sortie toujours 0 (élevée) — confirmé

`_drive()` (`cli.py:171-183`) ne capture que `WorkflowError` et `LockError` ; dans tous les autres cas
il imprime le statut et retourne `0`, y compris pour `Status.ERROR` et `Status.INTERRUPTED`. Rien dans
`cmd_run`/`cmd_resume` ne teste `state.status` avant de retourner. Confirmé tel quel.

### C-04 — corpus non revérifié (élevée) — confirmé

`_Engine.check_corpus()` (`workflow.py:139-148`) compare uniquement l'empreinte du **texte du
manifeste** à `config.corpus_manifest_sha256`. Aucune boucle sur les entrées du manifeste, aucun
recalcul de taille/SHA-256 des fichiers sous `corpus/fichiers/`. Un fichier de corpus modifié après
`new` ne serait détecté par rien dans le chemin d'appel. Confirmé.

### C-05 — preuves d'intégrité non exploitées à la reprise (élevée) — confirmé

`read_result()` (`transport.py:159-176`) valide le **schéma** de `resultat.json` (types, clés,
version) mais ne relit jamais `stdout.txt`/`stderr.txt` pour comparer taille et SHA-256 aux valeurs
qu'il vient de désérialiser. `resume_call()` (`workflow.py:228-248`) fait confiance à ce retour sans
vérification supplémentaire. Confirmé — c'est une vérification qui existe dans les données écrites
(`_Pump` calcule bien `digest` et `written`, `transport.py:242-265`) mais qui n'est jamais **relue**
au moment où elle compterait.

### C-06 — frontière d'effets non garantie (élevée, à arbitrer) — confirmé, description exacte

`adapters/claude.py:35-40` : `command()` ne restreint rien pour A, ni pour B en `CONSULT` ; seul
`CONTEXT_ONLY` ajoute `--tools ""`. `adapters/codex.py:37-43` : `--sandbox read-only` est présent dans
tous les cas (meilleure situation par défaut que Claude), mais `CONTEXT_ONLY` n'ajoute que
`-c features.shell_tool=false` — le docstring du module reconnaît lui-même une « réserve non
mesurée ». L'audit ne surinterprète pas : c'est un écart entre ce que `supports_context_only=True`
laisse croire et ce que la commande fait réellement.

## Constats repris sans revérification complète

C-07 (terminaison d'arbre), C-08 (paramètres numériques), C-09 (revue normalisée absente), C-10
(contrat d'erreur CLI incomplet) n'ont pas été relus ligne à ligne, sauf C-08 par sondage : `cli.py`
déclare bien `--timeout` en `type=float` et `--max-revisions` en `type=int` (`cli.py:246,251,256-259`)
sans validation de signe ni de finitude nulle part dans `cmd_new`/`cmd_run`/`cmd_resume`. Ce point est
donc confirmé aussi. Pour C-07, C-09 et C-10, les références citées sont cohérentes avec la structure
du code déjà lue (existence de `_terminate_tree`, de `write_exchange` produisant
`critique-B.json` et non `revue_normalisee.json`, de `_drive()` ne capturant que deux types
d'exception) — confiance élevée sans être une vérification au même niveau que C-01 à C-06.

## Synthèse — le conflit à trancher avant tout

`NOTES.md` fixe comme unique prochaine action le lancement d'une mission réelle payante pour observer
le cycle de bout en bout. L'audit montre que dans l'état actuel :

- un second `run` mal chronométré après une `QUESTION` ou en fin de cycle **relance un appel payant
  non demandé ou plante** (C-01) ;
- un `resume --answer` concurrent d'un `run` en cours peut **modifier `demande.md` et `etat.json` en
  affichant un échec** (C-02) ;
- une interruption ou une erreur de contrat pendant cette observation **ressortira comme un succès**
  au niveau du code de sortie (C-03), ce qui fausserait la note prise sur la friction observée.

Autrement dit : **observer maintenant risque de produire exactement le type d'incident que la mission
d'observation est censée révéler pour de bonnes raisons, plutôt que pour un bug de porte d'état.**
Corriger C-01, C-02 et C-03 avant la première mission réelle n'est pas un durcissement en trop — c'est
une condition pour que l'observation prévue par `NOTES.md` mesure ce qu'elle est censée mesurer.

## Compatibilité avec `POURQUOI.md` — aucune des corrections proposées n'ouvre les cinq interdits

Vérification demandée par `CLAUDE.md` avant d'endosser des correctifs dans ce projet :

- **C-01/C-02/C-03** : corrections de logique dans des fichiers existants (`workflow.py`, `cli.py`,
  `lock.py`). Aucun nouveau sous-système. Le correctif de C-02 (création exclusive du verrou) reste
  une primitive fichier, pas un service.
- **C-04/C-05** : ajoutent du calcul (SHA-256, comparaison) là où l'outil affirme déjà le faire — pas
  une nouvelle garantie, la garantie déjà promise par le nom des fichiers (`resultat.json`,
  `manifeste.json`) et par le vocabulaire du code (« figé », « preuve »).
- **C-06** : l'audit demande un **arbitrage écrit**, pas un mécanisme. C'est exactement la méthode de
  ce projet (trancher avant de coder). Le risque à surveiller si le PO choisit de durcir : ne pas
  transformer les adaptateurs en couche de confinement générique — rester sur des drapeaux de
  commande par profil, comme aujourd'hui.
- **C-07 à C-10** : durcissements locaux (borne de nettoyage, validation d'arguments, nommage
  d'artefact, capture d'exceptions). Aucun ne requiert de base de données, de worker, de budget ou de
  GUI.
- **C-11** : la validation réelle et le guide minimal sont déjà actés comme prochaine étape dans
  `NOTES.md` — l'audit ne fait que la retarder après C-01–C-05, pas l'étendre.

Aucun correctif proposé par l'audit ne rentre en collision avec les cinq interdits de `POURQUOI.md`.

## Ordre de traitement — confirmé, avec une précision

L'ordre proposé par l'audit (C-01 → C-02 → C-03 → C-04/C-05 → C-06 → C-07–C-10 → C-11) est cohérent
avec la lecture du code : C-01 et C-02 touchent la porte humaine et le verrou, donc conditionnent la
sûreté de tout appel réel, y compris celui que `NOTES.md` prévoit de lancer ensuite. La seule
précision à ajouter : **tant que C-01–C-03 ne sont pas corrigés et re-testés avec le faux adaptateur
(compteur d'appels inchangé dans les cas interdits), ne pas exécuter la mission réelle de §9 de
`NOTES.md`.**

## Ce que cette analyse ne couvre pas

Pas de relecture de `contracts.py` (normalisation CRLF, acceptation du bloc JSON clôturé, cité pour
C-09) ni de `corpus.py` en détail (cité pour C-04) au-delà du sondage fait ici. Si une correction de
C-04 ou C-09 est engagée, relire ces deux modules avant d'écrire le correctif plutôt que de se fier à
cette note.

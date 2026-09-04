# Plan correctif — audit de déploiement du 2026-09-04

> **⚠ Version 1 — remplacée le 2026-09-04 par
> `2026-09-04-plan-correctif-audit-v2.md`, après l'avis de Codex
> (`project/analyse/codex/2026-09-04-analyse-plan-correctif-audit.md`).**
> Conservée telle quelle : c'est la version que Codex a relue. Ne pas l'exécuter.

> **Nature :** plan de correction des constats de `project/analyse/codex/2026-09-04-audit-deploiement.md`,
> après vérification dans le code (`project/analyse/claude/2026-09-04-analyse-audit-deploiement.md`).
>
> **Statut : soumis à Codex pour avis. Aucune ligne de code n'a été modifiée.**
> État du dépôt à la rédaction : branche `master`, HEAD `6eb2bf4`, suite verte (196 tests).
>
> **Ce qui est demandé à Codex :** un avis sur les cinq arbitrages D-4 à D-8, sur les deux constats
> complémentaires N-01 et N-02, et sur les correctifs de conception proposés lot par lot — en
> particulier là où le plan propose de **modifier `CONCEPTION_FINALE.md`** plutôt que le code.
> Les questions explicites sont regroupées en fin de document.

---

## 1. Principe directeur

Chaque lot est instruit contre les cinq interdits de `CLAUDE.md` et la règle 2 de `POURQUOI.md`
(« la bonne question n'est jamais *est-ce que ce contrôle est utile ?* — c'est *qu'est-ce que je
retire en échange ?* »). Trois conséquences tenues dans tout le plan :

1. **Aucun nouveau sous-système.** Tous les correctifs tiennent dans les modules existants.
2. **Un défaut se corrige, ou la promesse se retire.** Quand une garantie annoncée coûte plus qu'elle
   ne rapporte, le plan propose de corriger le **document**, pas d'ajouter du code (lots 9, 7, 6).
3. **Un coût en lignes est annoncé par lot**, parce que la condition de l'arbitrage budgétaire du
   2026-09-04 (`NOTES.md`) est encore ouverte. Voir §6.

**Ordre d'exécution** : celui de l'audit. Les lots 1 à 3 sont **bloquants pour la première mission
réelle** ; les lots 4 et 5 sont fortement recommandés avant elle ; le reste peut suivre.

---

## 2. Arbitrages à trancher avant de coder

Conformément à `RULES.md` (« une question marquée à trancher se tranche dans le document même »),
ces cinq points sont à décider avant le lot correspondant, et leur décision est à inscrire dans
`conception/CONCEPTION_FINALE.md`.

### D-4 — L'intervention humaine passe-t-elle sous le verrou du moteur ? *(lot 2)*

`CONCEPTION_FINALE.md` §7 dit : « `resume` ne contient pas un second moteur : il enregistre
l'intervention, remet l'état dans une phase admissible, et appelle le même moteur. » Le code l'a lu
comme « enregistre **avant** d'appeler le moteur » — donc **hors verrou**, ce qui est C-02.

- **Option A (recommandée)** — l'intervention est **transmise** au moteur et appliquée après l'étape 3
  (relecture sous verrou), avant la porte d'état. Un seul point d'acquisition du verrou, comme
  aujourd'hui. Exige de **reformuler §7** : « il enregistre l'intervention *par le moteur, sous le
  verrou*, remet l'état dans une phase admissible, puis enchaîne le cycle. »
- **Option B** — `cmd_resume` acquiert lui-même le verrou et le moteur accepte un verrou déjà détenu.
  Rejetée : rendre le verrou réentrant par PID masquerait une double acquisition réelle, et la
  libération imbriquée deviendrait ambiguë.

### D-5 — Table des codes de sortie *(lot 3)*

`CONCEPTION_FINALE.md` §5 promet « sortie en code non nul » pour Ctrl-C, sans table. Proposition :

| Code | Situation | Statut rendu par le moteur |
|---:|---|---|
| 0 | cycle terminé au point prévu | `AWAITING_APPROVAL` |
| 1 | refus **avant mutation** : usage, prévol, verrou détenu | — (exception `WorkflowError`/`LockError`) |
| 2 | le cycle attend une décision humaine | `WAITING_HUMAN` |
| 3 | interruption du transport (délai, Ctrl-C, plafond, `CLI_FAILED`) | `INTERRUPTED` |
| 4 | échec de contrat | `ERROR` |

Un code par cause, aucune cause muette. **Point à trancher :** `WAITING_HUMAN` mérite-t-il un code
distinct (2) ou vaut-il 0 ? Le plan recommande 2 : la porte humaine est le cœur du produit, et un
script qui enchaîne des `run` doit pouvoir la distinguer d'une fin de cycle sans lire `status --json`.

### D-6 — Frontière d'effets : garantie ou limite déclarée ? *(lot 6, C-06)*

- **Option A (recommandée)** — **limite déclarée**, écrite comme telle : le programme ne confine pas
  les agents ; il choisit des drapeaux mesurés, et **inscrit dans `intention.json` la commande
  réellement lancée**, qui devient la preuve par appel de ce qui était restreint. `supports_context_only`
  cesse de signifier « toutes les capacités retirées » pour signifier « le profil est applicable », et
  la nuance déjà présente au tableau §8 (« possible, partiel ») devient visible dans le code.
- **Option B** — **garantie mécanique** : caractériser puis câbler `--restricted` / `--safe-mode` /
  `--no-session-persistence` (outil 1) et `--ephemeral` / `--ignore-user-config` (outil 2), et refuser
  `CONTEXT_ONLY` chez l'adaptateur qui ne peut pas tout retirer. **Interdit tant que ce n'est pas
  mesuré** (`RULES.md` : « ne jamais prescrire une commande qu'on n'a pas lancée »).

Recommandation : **A maintenant, B après une session de caractérisation** sur les versions
effectivement installées (outil 1 `2.1.260`, outil 2 `0.153.2` — la caractérisation existante porte sur
`2.1.259` / `0.151.0`, écart relevé par l'audit). Condition de réouverture : toute évolution de
`command()`, ou la première mission de recherche dont le livrable engage la provenance.

**Sous-question D-6b :** inscrire la commande dans `intention.json` y fait entrer un **chemin absolu**
(l'exécutable résolu par `shutil.which`), ce que §4 interdit — « aucun chemin absolu, nulle part ». Le
motif de cette règle est la **portabilité du dossier de collaboration** (DialogForge en persistait un
dans `configuration.json`) ; un chemin d'exécutable dans `intention.json` est une **preuve d'un appel
passé**, jamais un chemin relu pour reprendre. Le plan propose donc d'amender §4 en « aucun chemin
absolu **dont la reprise dépend** ». À valider par Codex : c'est une décision actée qu'on rouvre.

### D-7 — Terminaison d'arbre : borner, ou garantir ? *(lot 7, C-07)*

Quand le parent sort avant son descendant, `taskkill /T` sur un PID mort ne retrouve pas
nécessairement la descendance (`transport.py:210-232`).

- **Option A (recommandée, ~10 lignes)** — **borner et ne pas mentir** : après les deux périodes de
  grâce, si une pompe est encore vivante, l'issue **cesse d'être `COMPLETED`** ; `resultat.json` n'est
  pas écrit, un incident `STREAMS_UNCLOSED` est consigné, `pid.txt` reste la piste pour l'humain. La
  reprise traite ce cas par la table §5 (« possiblement payé »), sans rejeu automatique. §5 assume déjà
  cette honnêteté pour la fermeture de console : « on ne le promet donc pas ».
- **Option B (~50-60 lignes de `ctypes`)** — objet Job Windows avec `KILL_ON_JOB_CLOSE`, qui garantit
  réellement la mort de l'arbre. Coût élevé, spécifique à un OS, à mettre en regard des 2 070 lignes
  actuelles.

Recommandation : A. La garantie que le produit doit tenir est « **un flux partiel n'est jamais
présenté comme complet** » (§5), pas « aucun orphelin ne survit ».

### D-8 — `revue_normalisee.json` : produire le fichier, ou corriger l'arborescence ? *(lot 9, C-09)*

L'arborescence §7 annonce `appels/…/revue_normalisee.json`, jamais écrit. Le moteur écrit la réponse
**normalisée mais non canonique** dans `echanges/NNNN-critique-B.json` (`workflow.py:288`), fichier `.json`
qui peut contenir des délimiteurs Markdown (tolérance de `contracts._strip_sole_fence`).

- **Option A (recommandée, ~16 lignes)** — **un brut + un canonique, pas trois** : `echanges/NNNN-critique-B.json`
  reçoit désormais le **JSON canonique** (`json.dumps` du `Review` analysé) ; le brut reste dans
  `appels/…/reponse_brute.txt`. `revue_normalisee.json` **disparaît de §7**. L'extension redevient vraie
  et aucun fichier n'est ajouté.
- **Option B** — écrire les deux fichiers, comme l'annonce §7. Rejetée : c'est une seconde vérité pour
  le même contenu, ce que §6 refuse ailleurs (« jamais une vérité seconde »).

**Sous-question D-8b — les transformations de normalisation.** `contracts.normalize()` calcule
`transformations` et `storage.read_text()` rend `had_bom` « pour que l'appelant le consigne » : aucun
appelant ne les consigne. Les deux artefacts (brut, canonique) étant conservés, la transformation est
**dérivable par différence**. Le plan propose de **retirer la promesse du vocabulaire** plutôt que
d'ajouter un fichier — sauf si Codex nomme un consommateur réel.

---

## 3. Lots

### Lot 1 — Porte d'état avant tout appel *(C-01, bloquant)*

**Défaut exact.** `workflow.run()` (`workflow.py:82-92`) choisit entre reprise et nouvel appel sur la
seule présence de `current_call`, sans lire `state.status`. Précision utile pour hiérarchiser les
tests — le risque n'est pas uniforme :

| Statut au second `run` | `current_call` | Ce qui se passe aujourd'hui |
|---|---|---|
| `WAITING_HUMAN` (QUESTION, BLOQUE, incohérence de revue) | `null` | **nouvel appel payant**, porte humaine contournée |
| `AWAITING_APPROVAL` / phase `CLOSED` | `null` | `KeyError` — **avant toute mutation** (`workflow.py:162` précède le `mkdir`) |
| `INTERRUPTED` | présent | ré-écrit le même incident ; **pas d'appel** |
| `ERROR` | présent (`RESPONSE_STORED`) | ré-applique le contrat localement, échoue pareil ; **pas d'appel** |

**Correctif.** Une porte unique dans `_preflight`, sur le couple (statut, présence d'appel courant) :
seuls `READY` **sans** appel courant et `RUNNING` **avec** appel courant sont exécutables ; tout le
reste est un `WorkflowError` nommant le statut et la commande qui en sort. La relecture sous verrou
(`recheck`, `workflow.py:150-157`) compare déjà `etat.json` **en entier** : elle ferme la fenêtre entre
le prévol et le verrou sans second contrôle. Plus `_ROLE_OF_PHASE.get(...)` + refus explicite, pour que
`CLOSED` rende une erreur du contrat CLI au lieu d'une `KeyError`.

**Coût estimé.** ~12 lignes (`workflow.py`).

**Tests exigés** (`tests/test_workflow.py`, `tests/test_cli.py`) : second `run` après `QUESTION`, après
`BLOQUE`, après `ERROR`, après `AWAITING_APPROVAL` — chacun prouvant `FakeAdapter.calls` **inchangé**
et le code de sortie attendu ; un `run` en `RUNNING` avec appel courant reste accepté (non-régression
de la table de reprise §5).

### Lot 2 — Toute mutation sous le verrou, acquisition atomique *(C-02, bloquant)*

**Défaut A.** `cmd_resume` (`cli.py:107-127`) appelle `_apply_answer` / `_prepare_retry` **avant**
`_drive()`, seul chemin qui acquiert le verrou. Sous verrou détenu, la commande rend `1` après avoir
archivé `demande.md`, réécrit `demande.md` et publié `etat.json` en `READY`.

**Correctif A** (selon D-4, option A) : `workflow.run()` reçoit l'intervention (réponse humaine ou
relance d'appel) et l'applique après l'étape 3, avant la porte du lot 1 — l'intervention étant
précisément ce qui fait passer `WAITING_HUMAN`/`INTERRUPTED` à `READY`. Elle est consommée à la
première itération, comme `retry_of`/`retry_reason` le sont déjà (`workflow.py:90`). `_apply_answer` et
`_prepare_retry` quittent `cli.py` pour le moteur ; `cli.py` ne garde que la validation d'arguments.

**Défaut B.** `lock._try_acquire` (`lock.py:53-65`) enchaîne `exists()` → lecture → écriture atomique :
deux processus peuvent franchir le test d'existence avant que l'un publie.

**Correctif B.** Acquisition par **création exclusive** (`os.open(..., O_CREAT | O_EXCL)`), écriture puis
`fsync` du descripteur. Sur `FileExistsError` : lecture du détenteur, refus s'il est vivant ; s'il est
mort, **une seule** tentative de récupération (suppression puis re-création exclusive), et un second
`FileExistsError` est un refus. Aucune boucle d'attente : le verrou ne fait jamais patienter, il refuse.
Détail d'implémentation à retenir de `RULES.md` : passer `getattr(os, "O_BINARY", 0)`, pour ne pas
nommer un symbole absent de la plateforme non testée. Le verrou cesse de passer par
`storage.write_atomic_text` (qui remplace au lieu de créer) — donc plus de `fsync` de dossier pour lui :
acceptable, §7 le décrit comme « transitoire ».

**Coût estimé.** ~+25 lignes nettes (`lock.py` +20, `workflow.py` +30, `cli.py` −25).

**Tests exigés** : `resume --answer` et `resume --retry-call` sous verrou détenu, prouvant que
`demande.md` et `etat.json` sont **inchangés octet pour octet** (empreintes avant/après) ; course entre
**deux vrais processus** (`RULES.md` : un comportement d'OS ne se teste pas contre un objet simulé), en
vérifiant qu'exactement un des deux acquiert ; récupération d'un verrou mort inchangée.

### Lot 3 — Codes de sortie *(C-03, élevée)*

**Défaut.** `_drive` (`cli.py:171-183`) rend `0` dès que le moteur a rendu un `State`, `ERROR` et
`INTERRUPTED` compris — alors que §5 promet « sortie en code non nul » pour Ctrl-C.

**Correctif.** Table D-5 appliquée dans `_drive`, table écrite dans §7.

**Coût estimé.** ~10 lignes.

**À corriger dans la suite existante :** `tests/test_cli.py:177-190`
(`test_retry_call_needs_a_non_empty_reason`) attend `0` après un `run` interrompu par délai
(`assertEqual(code, 0)`, ligne 184). **Ce test stabilise le défaut** ; il doit attendre 3. C'est le seul
endroit relevé où la suite fige un constat de l'audit — à re-vérifier lot par lot.

**Tests exigés** : un test par statut observable depuis la CLI (`AWAITING_APPROVAL`, `WAITING_HUMAN`,
`INTERRUPTED`, `ERROR`, refus de prévol, verrou détenu).

### Lot 4 — Corpus réellement figé *(C-04, élevée)*

**Défaut.** `_Engine.check_corpus` (`workflow.py:139-148`) ne compare que l'empreinte **du texte du
manifeste**. Les entrées ne sont pas relues, les fichiers de `corpus/fichiers/` jamais revérifiés.

**Correctif.** `corpus.read_manifest(path) -> Manifest` (lecture stricte, symétrique de
`Manifest.to_dict`, `corpus.py:40-49`) ; puis, dans le prévol : pour chaque entrée, présence, **taille**
et **SHA-256** ; refus d'un fichier absent, altéré, **ou surnuméraire** sous `corpus/fichiers/`. Le
surnuméraire est refusé parce qu'un agent qui parcourt le dossier le lirait : il modifie la référence
commune de A et B autant qu'une altération.

**Limite assumée, à contester si Codex n'est pas d'accord :** le recalcul complet reste **au prévol
seul**. Sous verrou, `recheck` gagne une ligne — la comparaison de l'empreinte du texte du manifeste —
mais pas le re-hachage de tout le corpus. Motif : la fenêtre est de quelques secondes, le corpus n'est
écrit par personne d'autre que `new`, et re-hacher un corpus réel **à chaque appel** d'un cycle qui en
compte cinq ou six est un coût récurrent pour un scénario que rien n'a encore produit
(`RULES.md` : « avant d'ajouter un garde-fou, vérifier qu'il compense un défaut encore réel »).

**Coût estimé.** ~35 lignes (`corpus.py` +25, `workflow.py` +10).

**Tests exigés** : fichier altéré, fichier absent, fichier surnuméraire, manifeste incohérent
(taille ou empreinte fausse), manifeste au schéma cassé — chacun refusé **avant** appel, `calls == 0`.

### Lot 5 — Les preuves d'intégrité servent à la reprise *(C-05, élevée)*

**Défaut.** `transport.read_result` (`transport.py:159-176`) valide le schéma de `resultat.json` sans
jamais comparer `stdout_bytes`/`stdout_sha256` aux fichiers réels ; `resume_call` (`workflow.py:228-248`)
réapplique `reponse_brute.txt` sans le comparer à `current_call.response_sha256`.

**Correctif.**

1. `read_result` recalcule taille et SHA-256 des deux flux et compare. Une divergence **n'est pas** un
   `None` : `None` signifie « pas de preuve, appel possiblement payé », une divergence signifie
   « preuve contredite ». Elle lève, et le moteur consigne un incident `INTEGRITY_MISMATCH` en
   `INTERRUPTED` — donc sans rejeu automatique, la sortie restant `resume --retry-call`.
2. Branche `RESPONSE_STORED` de `resume_call` : `normalize(raw).sha256` comparé à
   `call.response_sha256`, même traitement.
3. `prompt.txt` comparé à `call.prompt_sha256` à la reprise (2 lignes, valeur : détecter une
   collaboration copiée puis éditée).

**Coût estimé.** ~20 lignes (`transport.py` +12, `workflow.py` +8).

**Tests exigés** (`tests/test_recovery.py`) : `stdout.txt` altéré après sortie propre ;
`reponse_brute.txt` altéré en `RESPONSE_STORED` ; `prompt.txt` altéré — les trois en prouvant
`calls == 0` et un statut `INTERRUPTED` avec incident nommé.

### Lot 6 — Frontière d'effets *(C-06, élevée, arbitrage D-6)*

**Sans D-6, aucun code.** Ce que le plan retient si D-6 est tranché en A :

- §1/§8/§12.3 de `CONCEPTION_FINALE.md` écrivent explicitement : « la non-écriture du projet par les
  agents est une **limite déclarée**, obtenue par des drapeaux mesurés, **pas une garantie mécanique** ».
- `intention.json` reçoit la commande réellement lancée (D-6b) : ~3 lignes, et la frontière devient
  vérifiable **par appel** au lieu d'être promise.
- Caractérisation des modes restreints des versions installées : **session séparée, hors de ce plan**,
  consignée dans `conception/CARACTERISATION_CLI.md`. Elle conditionne un éventuel passage en option B.

**Coût estimé.** ~3 lignes de code, le reste en documentation.

### Lot 7 — Borne de la terminaison d'arbre *(C-07, moyenne, arbitrage D-7)*

**Défaut.** `_wait` conclut `COMPLETED` dès la sortie du parent (`transport.py:187-188`) ; si un
descendant tient encore les tubes, `_terminate_tree` vise un PID mort et `resultat.json` peut affirmer
« flux complets » sur des fichiers encore ouverts.

**Correctif** (D-7, option A) : après la seconde grâce, si une pompe reste vivante, l'issue devient
`STREAMS_UNCLOSED`, `resultat.json` **n'est pas écrit**, l'incident est consigné. Toute la phase de
nettoyage est ainsi bornée par `2 × _GRACE_SECONDS`.

**Test exigé, dans cet ordre** (`RULES.md` : « un test qui vérifie une absence doit d'abord être prouvé
capable de voir la présence ») : un parent qui engendre un descendant long **puis sort immédiatement** ;
d'abord prouver hors suite que le descendant écrit bien sa marque quand on ne tue personne, ensuite
vérifier la borne et l'absence de `resultat.json`.

**Coût estimé.** ~10 lignes.

### Lot 8 — Validation des paramètres numériques *(C-08, moyenne)*

**Défaut.** `--timeout` accepte `0`, les négatifs, `inf` et `nan` (`cli.py:251,256`) ; avec `nan`,
`time.monotonic() >= deadline` reste faux et **le délai dur ne se déclenche jamais** — la garantie la
plus structurante du transport tombe silencieusement. `--max-revisions` accepte les négatifs.

**Correctif.** Deux convertisseurs `argparse` (délai fini et strictement positif ; révisions `>= 0`),
plus le même contrôle au chargement de `Configuration` (`models.py`), puisqu'une configuration
persistée peut avoir été éditée à la main.

**Coût estimé.** ~12 lignes.

**Tests exigés** : `0`, `-1`, `nan`, `inf` refusés sur `--timeout` ; `-1` refusé sur `--max-revisions` ;
`max_revisions` négatif refusé au chargement d'une `configuration.json` éditée.

### Lot 9 — Revue canonique *(C-09, moyenne, arbitrage D-8)*

Correctif selon D-8 option A : `echanges/NNNN-critique-B.json` reçoit le JSON canonique
(`Review.to_dict()` à écrire dans `contracts.py`), `revue_normalisee.json` sort de l'arborescence §7.
Vérifier que `open_findings` (`workflow.py:329-336`) relit sans peine ce canonique — c'est le même
schéma, `severity` étant alors toujours présente, `UNKNOWN` comprise.

**Coût estimé.** ~16 lignes (`contracts.py` +12, `workflow.py` +4).

**Tests exigés** : une revue rendue dans un bloc clôturé produit un `echanges/*.json` **directement
lisible par `json.loads`** ; une revue relue par `open_findings` après canonisation donne les mêmes
constats ouverts.

### Lot 10 — Contrat d'erreur de la CLI *(C-10, moyenne)*

**Défaut.** `_drive` ne capture que `WorkflowError` et `LockError` ; JSON illisible, schéma invalide,
erreur d'entrée-sortie, décodage UTF-8 ou `TransportError` remontent en traceback. `cmd_status` n'a
aucune enveloppe.

**Correctif.** Une enveloppe unique `(OSError, ValueError, WorkflowError, LockError, TransportError)`
→ `_fail(...)`, code 1, appliquée à `run`, `resume` et `status` (`ContractError`, `CorpusError` et
`json.JSONDecodeError` sont déjà des `ValueError`). Tout le reste reste une exception : les défauts de
programmation doivent rester bruyants. Règle à écrire dans §7 : **une erreur attendue est un refus sans
traceback ; l'état sur disque reste interprétable par la table de reprise §5** — un échec survenu après
la publication de `CALLING` n'est pas un refus sans mutation, et c'est la reprise, pas le message, qui
le rattrape.

**Coût estimé.** ~6 lignes.

**Tests exigés** : `etat.json` illisible, `etat.json` au schéma invalide, `Popen` en échec,
sortie non-UTF-8 — aucun ne doit produire de traceback.

### Lot 11 — Validations réelles et guide d'usage *(C-11, opérationnelle)*

**À exécuter seulement après les lots 1 à 5**, et **avec autorisation du PO** (appels payants) :

1. déplacement d'une collaboration en cours d'usage, puis reprise (§7 : « le dossier est autonome pour
   reprendre le cycle ») ;
2. une mission réelle de **conception**, une mission réelle de **recherche**, dans deux permutations
   différentes ;
3. re-caractérisation des versions installées (outil 1 `2.1.260`, outil 2 `0.153.2`) — l'écart avec
   `CARACTERISATION_CLI.md` est relevé par l'audit ;
4. consignation : versions, commandes, résultats, incidents, coût approximatif, **friction du manifeste
   de corpus** (`NOTES.md` §3, « premier point d'usage à mesurer ») ;
5. `GUIDE.md` (~1 page) : installation, prérequis CLI, authentification, premier `new`, lecture des
   statuts, reprise, où trouver le livrable.

---

## 4. Constats complémentaires — trouvés en vérifiant l'audit

Deux points qui ne figurent pas dans l'audit, soumis au même avis.

### N-01 — Après la porte d'état, `ERROR` n'a plus aucune sortie

Aujourd'hui, un `run` sur une collaboration en `ERROR` ré-applique le contrat localement (sans appel) et
échoue de la même façon : c'est un cul-de-sac, mais silencieux. Le lot 1 le transforme en **refus
explicite** — et il faut alors constater que **rien** ne permet plus d'en sortir :
`_apply_answer` exige `WAITING_HUMAN` (`cli.py:132`) et `_prepare_retry` exige `INTERRUPTED`
(`cli.py:158`). `CONCEPTION_FINALE.md` ne dit nulle part comment on quitte `ERROR`.

**Proposition** : `resume --retry-call <uuid> --reason-file <f>` accepte `ERROR` **comme** `INTERRUPTED`
(une condition élargie, 1 ligne). Le remède est de forme identique — relancer l'appel avec un motif
humain attribuable — et §5 route déjà `CLI_FAILED` vers `INTERRUPTED` pour exactement cette raison.
À écrire dans §5 comme une décision, pas comme un effet de bord du lot 1.

### N-02 — `_release()` peut masquer l'erreur qu'il accompagne

`lock.acquire` libère dans un `finally` (`lock.py:49-50`) et `_release` **lève** `LockError` si le
détenteur a changé (`lock.py:72-73`). Si le corps du `with` a déjà échoué, l'exception de libération
remplace la cause réelle dans le message rendu à l'humain. Le refus de supprimer le verrou d'un autre
reste juste ; c'est sa **remontée pendant un déroulement d'exception** qui est mauvaise.

**Proposition** : dans le lot 2, ne lever depuis `_release` que si le corps n'a pas déjà échoué ; sinon
consigner et laisser passer la cause première. ~4 lignes.

---

## 5. Tableau de suivi

Colonne **État** tenue dans ce fichier ; la règle de clôture est celle de l'audit (correctif, test qui
échouait avant et passe après, commande de validation exécutée, commit, mise à jour de l'état).

| Lot | Constats | Bloquant 1re mission | Arbitrage requis | Coût estimé | État |
|---|---|---|---|---:|---|
| 1 | C-01 | oui | — (N-01 à trancher avec) | ~12 | à faire |
| 2 | C-02, N-02 | oui | D-4 | ~25 | à faire |
| 3 | C-03 | oui | D-5 | ~10 | à faire |
| 4 | C-04 | recommandé | — | ~35 | à faire |
| 5 | C-05 | recommandé | — | ~20 | à faire |
| 6 | C-06 | non | D-6, D-6b | ~3 + doc | à faire |
| 7 | C-07 | non | D-7 | ~10 | à faire |
| 8 | C-08 | non | — | ~12 | à faire |
| 9 | C-09 | non | D-8, D-8b | ~16 | à faire |
| 10 | C-10 | non | — | ~6 | à faire |
| 11 | C-11 | — | autorisation PO | doc | à faire |

Un commit par lot, préfixe `fix:` (`docs:` pour les lots documentaires), message sans accents.
`ruff check .`, `mypy --strict src tests` et `pytest` verts **à chaque lot**, jamais seulement à la fin.

---

## 6. Effet sur le budget de lignes — la condition ouverte se déclenche

L'arbitrage du 2026-09-04 (`NOTES.md`) a conclu « on continue », avec une **condition non refermée** :
*rouvrir la question si la croissance se poursuit sur un prochain palier.* Ce plan est cette croissance.

| | Lignes |
|---|---:|
| Production aujourd'hui (12 modules) | 2 070 |
| Ajout estimé, lots 1 à 10 | ~+150 |
| **Projection** | **~2 220** *(pour ~1 430 visés en §11)* |

Le PO doit donc rouvrir la question **avant le lot 4**, et non la découvrir après. Trois observations
pour l'éclairer :

- Aucun de ces ajouts n'est une **accrétion de contrôle** au sens de `POURQUOI.md` : ce sont des
  garanties **déjà annoncées** par la conception et non tenues par le code (intégrité, verrou, porte
  humaine, codes de sortie). Le coût vient de promesses faites, pas de fonctions nouvelles.
- Les lots 6, 7 et 9 proposent précisément l'inverse d'une accrétion : **retirer une promesse** plutôt
  que la financer. C'est là que se trouve la marge, si le PO veut en dégager.
- Les cinq interdits restent tenus : aucun worker, aucune base, aucun budget interne, aucune GUI,
  aucune exécution autonome. Le seul point qui frôle la limite est l'option B de D-7 (objet Job
  Windows) — c'est pourquoi le plan recommande l'option A.

---

## 7. Questions posées à Codex

1. **D-4** — l'intervention humaine appliquée par le moteur sous verrou, avec §7 reformulé : d'accord,
   ou vois-tu une raison de garder la mutation dans `cli.py` ?
2. **D-5** — la table de codes de sortie, et en particulier : `WAITING_HUMAN` = 2, ou 0 ?
3. **D-6 / D-6b** — « limite déclarée » plutôt que « garantie mécanique », et la commande lancée
   inscrite dans `intention.json` malgré la règle « aucun chemin absolu ». Le motif de cette règle
   (portabilité de la collaboration) est-il bien préservé ?
4. **D-7** — borner et consigner `STREAMS_UNCLOSED` plutôt que garantir la mort de l'arbre par objet
   Job : est-ce que l'audit visait la garantie, ou la borne ?
5. **D-8 / D-8b** — canoniser `echanges/*-critique-B.json` et retirer `revue_normalisee.json` de §7 ;
   et retirer le vocabulaire « consigné comme transformation » faute de consommateur. Vois-tu un
   consommateur réel ?
6. **N-01** — élargir `resume --retry-call` à `ERROR`, ou laisser ce statut sans sortie programmatique ?
7. **Lot 4** — le re-hachage complet du corpus au seul prévol, avec l'empreinte du manifeste revérifiée
   sous verrou : la fenêtre restante te paraît-elle acceptable, ou exiges-tu le re-hachage sous verrou ?
8. **Un constat de l'audit a-t-il été mal compris ou sous-évalué ici ?** Le plan traite C-01 comme un
   risque concentré sur `WAITING_HUMAN` (le seul cas qui produit un appel payant) ; si tu as observé
   un appel payant depuis `INTERRUPTED` ou `ERROR`, cette hiérarchie est fausse et il faut le dire.

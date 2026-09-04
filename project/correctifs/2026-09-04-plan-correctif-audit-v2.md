# Plan correctif — audit de déploiement du 2026-09-04 — **v2**

> **Nature :** plan de correction des constats de `project/analyse/codex/2026-09-04-audit-deploiement.md`,
> amendé après l'avis de Codex (`project/analyse/codex/2026-09-04-analyse-plan-correctif-audit.md`).
> Remplace `2026-09-04-plan-correctif-audit.md` (v1), conservée pour trace.
>
> **Statut : en cours d'exécution — document vivant.** Le tableau de suivi (§4) porte l'état lot par
> lot ; un lot écrit autrement que ce qu'il annonçait le dit sur place, avec son motif.
> Rédigé sur `master`, HEAD `6eb2bf4`, suite verte (196 tests) ; **lot 1 fait** (`373479d`, 202 tests).
>
> **Arbitrages PO rendus le 2026-09-04 :** budget de lignes augmenté (§5) · réordonnancement de
> `NOTES.md` validé (les lots passent devant la première mission réelle) · **D-5 tranché :
> `WAITING_HUMAN` = 5**, contre l'avis de Codex. Plus aucun arbitrage technique ouvert.

---

## 1. Ce qui change depuis la v1

L'avis de Codex a été filtré, pas appliqué : trois de ses propositions sont écartées avec motif, une
est amendée. Ses trois affirmations vérifiables ont d'abord été contrôlées dans le code — les trois
sont exactes, dont une mesure que je n'avais pas faite.

| Point de Codex | Disposition | Motif |
|---|---|---|
| Porte d'état du lot 1 incompatible avec l'intervention du lot 2 | **Retenu** | Défaut réel de mon document : la porte en prévol refusait `WAITING_HUMAN` avant que `--answer` puisse l'en sortir. |
| Validation à deux niveaux (prévol *et* verrou) | **Écarté** | Deux copies de la même règle à tenir synchrones. Une porte unique, sous verrou. Le coût d'un refus tardif — deux sondages `--version` — est payé sur une commande rare, pas sur le cycle. |
| Fusionner les lots 1 et 2 | **Amendé** | Découpage différent : le verrou atomique est **indépendant** de la porte et part seul (lot 1) ; porte et intervention partent ensemble (lot 2), donc jamais d'API intermédiaire contradictoire. |
| Course de récupération d'un verrou mort | **Retenu — solution écartée** | La faille est réelle (ma v1 supprimait sans condition). Ni « plus de récupération automatique » ni « verrou d'OS » : contre-proposition en §3, lot 1. |
| `lock_id` vérifié à la libération, en plus du PID | **Retenu** | Correct et nécessaire à la contre-proposition ci-dessus. |
| `--answer` idempotent après crash | **Retenu, simplifié** | Le trou est réel (archive par `rename` : un crash laisse la collaboration sans `demande.md`). Une seule branche de reprise suffit, pas trois valeurs de hachage acceptées. |
| Pas d'état intermédiaire persisté pour `--retry-call` | **Retenu** | Strictement meilleur : une écriture de moins, et le lien vers l'appel relancé n'est plus perdable. |
| D-5 : `WAITING_HUMAN = 0`, code 2 réservé à `argparse` | **Partiellement écarté** | `argparse` occupe bien 2 (vérifié) : ma table v1 était fausse. Mais un code distinct est conservé — voir D-5. |
| C-06 reste « risque accepté », pas « résolu » | **Retenu** | Une correction documentaire ne ferme pas un risque technique. |
| Rendre `supports_context_only` faux, ou le renommer | **Écarté** | `adapters/base.py` est **publié** (`NOTES.md` §13) : le modifier coûte une migration. Et le mettre à faux retirerait du produit un profil mesuré comme partiellement effectif. La partialité devient **factuelle** via `invocation_args`. |
| D-6b : argv assaini sans `argv[0]` | **Retenu** | Meilleur que ma proposition : la règle « aucun chemin absolu » n'a plus à être rouverte, et aucun futur adaptateur ne peut y déposer un secret. |
| Lot 4 : un seul re-hachage, **sous verrou** | **Retenu** | Même coût que ma version, meilleure place. Ma v1 hachait au prévol, hors verrou. |
| Lot 4 : refuser un lien symbolique apparu dans `corpus/fichiers` | **Retenu** | Cohérent avec les refus déjà appliqués à la copie (`corpus.py:82-85`). |
| Lot 5 : flux absent = divergence d'intégrité ; `prompt.txt` vérifié avant **toute** branche ; exception typée | **Retenus** | Justes et peu coûteux. |
| Lot 5 : `tests/test_recovery.py` fabrique des empreintes de zéros | **Retenu** | **Vérifié** : lignes 47, 57-58. Sans reconstruction des fabriques, les tests de reprise nominale deviendraient des scénarios de corruption. |
| D-7 : la borne annoncée n'existe pas | **Retenu** | **Mesure de Codex** : parent sorti, descendant tenant les tubes 22 s → `transport.run()` rend après **22,11 s**, `outcome=COMPLETED`, `resultat.json` présent. Ma v1 aurait laissé passer les quatre grâces cumulées. |
| Lot 8 : valider aussi à l'entrée Python ; `_schema_version` accepte `True` | **Retenus** | **Vérifié** : `models.py:150-154`, `True != 1` est faux. |
| Lot 10 : pas de capture globale de `ValueError` | **Retenu, autrement** | Par types de frontière explicites — dont `SchemaError`, **qui existe déjà** (`models.py:20`). Aucune nouvelle exception à créer. |
| Lot 10 : `command()` avant `CALLING`, `LAUNCH_FAILED`, `DECODE_FAILED` | **Retenus** | Le réordonnancement supprime un faux « possiblement payé » pour deux lignes déplacées. |
| N-01 restreint à `CONTRACT_ERROR` | **Retenu, élargi** | Table fermée d'incidents relançables : `CONTRACT_ERROR` **et** `DECODE_FAILED` (créé par le lot 8 des erreurs). |
| N-02 : `add_note` sur la cause première | **Retenu** | Python 3.12, idiomatique, 4 lignes. |
| Supprimer `transformations` / `had_bom` s'ils restent sans consommateur | **Écarté** | Le retrait toucherait ~15 sites d'appel de `storage.read_text` (signature en tuple) pour lever une ambiguïté que le retrait du **vocabulaire** suffit à lever (D-8b). |
| Ordre d'exécution révisé | **Retenu** | Avec le verrou en tête, puisqu'il est devenu un lot autonome. |

---

## 2. Arbitrages — tranchés

### D-4 — L'intervention humaine passe sous le verrou du moteur. **Tranché : oui.**

`workflow.run()` reçoit l'intervention (`--answer` ou `--retry-call`) et l'applique **après** l'étape 3
(relecture sous verrou), **avant** la porte d'état. `cli.py` ne garde que la validation d'arguments.
`CONCEPTION_FINALE.md` §7 est reformulé : « `resume` ne contient pas un second moteur : il transmet
l'intervention au moteur, qui l'applique **sous le verrou**, remet l'état dans une phase admissible,
puis enchaîne le cycle. »

**Contre Codex :** la validation reste **à un seul niveau**. Une porte dupliquée entre le prévol et le
verrou, c'est deux vérités à garder d'accord — le défaut même que la v1 vient de commettre. Le prix de
ce choix est explicite : un `run` refusé aura payé deux sondages `--version` avant son refus.

### D-5 — Codes de sortie. **Tranché par le PO : `WAITING_HUMAN` = 5.**

| Code | Situation |
|---:|---|
| 0 | cycle terminé au point prévu — `AWAITING_APPROVAL` |
| 1 | refus **avant mutation** : prévol, verrou détenu, argument invalide |
| 2 | **réservé à `argparse`** (erreur d'usage) — le programme ne le produit jamais |
| 3 | interruption du transport — `INTERRUPTED` (délai, Ctrl-C, plafond, `CLI_FAILED`, `LAUNCH_FAILED`) |
| 4 | réponse inexploitable — `ERROR` (`CONTRACT_ERROR`, `DECODE_FAILED`) |
| **5** | **le cycle attend une décision humaine — `WAITING_HUMAN`** |

Le code décrit le **résultat de la commande**, jamais l'approbation du livrable : `AWAITING_APPROVAL`
vaut 0 parce que le cycle s'est arrêté où il devait, pas parce que le document est approuvé.

**Divergence tranchée par le PO le 2026-09-04, contre l'avis de Codex** — Codex recommandait
`WAITING_HUMAN = 0` (« issue métier normale, pas un échec » ; le distinguo reste lisible dans
`status --json`). Le code **5** est retenu, pour une raison qui vient de C-03 lui-même : le défaut que
l'audit reproche à `_drive()` est d'avoir rendu **indiscernables au niveau du code de sortie** « le
cycle s'est arrêté sur un incident » et « le cycle est allé au bout ». Mettre `WAITING_HUMAN` à 0
recrée cette indiscernabilité entre « il te faut répondre » et « c'est fini ». Un code distinct hors de
la plage `argparse` coûte zéro ligne.

### D-6 — Frontière d'effets : **limite déclarée**, et **C-06 reste ouvert**. **Tranché.**

1. `CONCEPTION_FINALE.md` §1/§8/§12.3 écrivent : « la non-écriture du projet par les agents est une
   **limite déclarée**, obtenue par des drapeaux mesurés — **pas une garantie mécanique** ».
2. `intention.json` reçoit `invocation_args` : **l'argv demandé, sans `argv[0]`** (D-6b). Décrit comme
   *trace de l'argv demandé*, jamais comme preuve des capacités effectives — la configuration
   utilisateur, les hooks et l'évolution de la CLI restent hors de portée du programme.
3. Le constat C-06 passe à **« risque accepté — limite déclarée »**, jamais à « résolu ». Il ne se
   fermera qu'après caractérisation des modes restreints sur les versions **installées** (outil 1
   `2.1.260`, outil 2 `0.153.2` ; la caractérisation existante porte sur `2.1.259` / `0.151.0`).

**Contre Codex :** `supports_context_only` **n'est ni renommé ni mis à faux**. `adapters/base.py` est
publié (`NOTES.md` §13) et le modifier coûte une migration ; le mettre à faux chez outil 2 retirerait
du produit un profil que §8 documente déjà comme « possible, partiel » et que la caractérisation du
2026-09-03 a mesuré comme effectif sur `shell_tool`. Le booléen garde son sens — *l'adaptateur sait
appliquer ce profil* — et la partialité devient **vérifiable par appel** dans `invocation_args`, au lieu
d'être promise par un nom.

### D-7 — Terminaison d'arbre : **borner et ne pas mentir**, avec une vraie borne. **Tranché.**

Option A confirmée (pas d'objet Job Windows en V0.1), **amendée par la mesure de Codex** : la borne de
la v1 n'en était pas une. Détail en §3, lot 7.

### D-8 — Revue canonique, sans troisième artefact. **Tranché.**

`appels/…/reponse_brute.txt` reste la preuve exacte ; `echanges/NNNN-critique-B.json` devient
l'autorité canonique (`Review.to_dict()`, `.value` des enums, `severity` toujours émise, `UNKNOWN`
comprise) ; `revue_normalisee.json` sort de l'arborescence §7.

**D-8b :** le vocabulaire « consigné comme transformation » est retiré de la conception et des
docstrings — la différence entre brut et canonique refait le diagnostic. **Contre Codex :**
`Normalized.transformations` et `had_bom` sont **conservés** : les retirer changerait la signature de
`storage.read_text()`, utilisée sous la forme `text, _ = …` dans une quinzaine de sites, pour une
ambiguïté que le retrait du vocabulaire suffit à lever.

### N-01 — Sortie de `ERROR` : **table fermée d'incidents relançables.** **Tranché.**

`resume --retry-call <uuid> --reason-file <f>` accepte `ERROR` **si et seulement si** : `current_call`
présent et d'identifiant égal à l'argument · `last_incident` lisible, appartenant à cet appel · son
`kind` appartient à `{CONTRACT_ERROR, DECODE_FAILED}` · motif non vide. Toute autre famille d'erreur
devra être **ajoutée explicitement** à cette table, jamais héritée du statut `ERROR`. À écrire dans §5.

### N-02 — Ne pas masquer la cause première. **Tranché.**

`lock.acquire` capture la cause du corps, tente la libération, et en cas d'échec de celle-ci ajoute une
note (`BaseException.add_note`, Python 3.12) disant que le verrou n'a pas été libéré. Sans cause
première, l'erreur de libération est levée normalement.

---

## 3. Lots — ordre d'exécution révisé

### Lot 1 — Verrou : acquisition et récupération atomiques *(C-02 volet B, N-02)*

Sorti en premier et **seul** : il ne dépend d'aucun autre lot et aucun autre ne dépend de sa forme
finale.

**Défaut.** `lock._try_acquire` (`lock.py:53-65`) enchaîne `exists()` → lecture → écriture : deux
processus peuvent franchir le test avant que l'un publie.

**Correctif.**

1. **Acquisition** par création exclusive : `os.open(path, O_CREAT | O_EXCL | O_WRONLY)`, écriture du
   porteur, `fsync`. Le porteur gagne un **`lock_id` aléatoire** en plus du PID.
2. **Libération** : comparaison du `lock_id` exact, pas seulement du PID — deux acquisitions du même
   processus ou un verrou remplacé ne doivent jamais autoriser la suppression.
3. **Récupération d'un verrou mort — sous jeton.** *(Écrit autrement que ce que cette v2 annonçait,
   voir ci-dessous.)* Sur `FileExistsError` : lire le porteur ; vivant → refus. Mort → création
   **exclusive** du jeton `verrou.json.recuperation` ; celui qui l'obtient relit `verrou.json`, ne
   l'efface que s'il porte toujours le `lock_id` mort, puis reprend à la création exclusive ; le jeton
   est retiré dans tous les cas. **Celui qui n'obtient pas le jeton ne touche jamais au verrou.**
4. `add_note` sur la cause première (N-02).

**Ce qui a changé à l'écriture, et pourquoi.** Cette v2 proposait une récupération par déplacement
atomique (`os.rename` vers une destination unique), avec remise en place si le fichier déplacé n'était
pas le verrou mort. C'était sûr à deux processus, mais laissait une fenêtre à trois : entre le
déplacement par erreur d'un verrou vivant et sa remise en place, un troisième pouvait créer le sien.
Le jeton ferme cette fenêtre au même prix, parce qu'un candidat sans jeton ne touche pas au verrou —
il n'y a plus rien à remettre en place. **Limite résiduelle, écrite dans le message d'erreur :** un
jeton resté d'une récupération interrompue bloque la récupération suivante et demande une suppression
humaine. Sa fenêtre est celle d'un crash entre deux instructions, contre celle d'un verrou mort qui
dure tout un appel.

**Contre Codex — pourquoi ni l'option 1 ni l'option 2.** Sa critique de ma v1 est juste : supprimer
sans condition permet au second récupérateur d'effacer le verrou frais du premier. Mais :

- **« plus de récupération automatique, suppression humaine »** retire l'ergonomie de reprise
  exactement là où le produit la promet : le crash est le scénario que tout le protocole d'appel
  durable §5 existe pour rattraper. Après chaque crash, une manipulation manuelle de fichier.
- **« verrou d'OS tenu ouvert »** est meilleur sur le papier, moins bon sur la plateforme testée : sous
  Windows, `msvcrt.locking` pose un verrou **impératif** sur la plage de fichier — un second processus
  ne pourrait plus **lire** les métadonnées (PID, commande, date) pour dire à l'humain qui détient le
  verrou, sauf à scinder en deux fichiers. On perdrait une information utile pour fermer une course
  rare.
- **`os.rename` vers une destination unique par processus est la primitive sérialisante que Codex
  demandait à son option 3** : un fichier ne peut être déplacé qu'une fois, le perdant reçoit
  `FileNotFoundError`. La **suppression** est ainsi sérialisée, et l'**entrée** reste toujours une
  création exclusive.

**Coût réel.** `lock.py` : 108 → **181** lignes (+73, pour ~37 estimées — le jeton et la validation du
`lock_id` coûtent le double du déplacement prévu). Mesuré, pas estimé.

**Tests écrits** : course entre **deux vrais processus** (`RULES.md`) sur un verrou libre — exactement
un entre ; **trois processus** sur un verrou mort — exactement un entre ; jeton orphelin → refus qui
nomme le fichier ; aucun jeton laissé après une récupération réussie ; libération refusée quand le
`lock_id` diffère **sous notre propre PID** ; échec du corps + échec de libération → la cause première
remonte, avec sa note ; deux acquisitions successives ont des `lock_id` différents.

**Le test de course a été prouvé capable de voir le défaut** (`RULES.md`) : rejoué contre l'ancien
verrou avec un verrou mort en place, **les trois processus sont entrés dans la section critique**.
Deux enseignements de cette contre-épreuve, tous deux corrigés :

- le concurrent écrivait son résultat dans un `except` qui rattrapait aussi l'échec de **libération** :
  un second entrant se serait déclaré refusé, et le test aurait masqué la double entrée qu'il cherche ;
- sous Windows, un PID terminé reste **« vivant »** pour `OpenProcess` tant qu'un handle du processus
  est ouvert — dans la contre-épreuve, l'objet `Popen` gardé en variable locale faisait croire à un
  détenteur vivant, et les trois concurrents refusaient pour la mauvaise raison.

### Lot 2 — Porte d'état et intervention sous verrou *(C-01, C-02 volet A, D-4)*

**Défauts.** (a) `workflow.run()` (`workflow.py:82-92`) choisit reprise ou nouvel appel sur la seule
présence de `current_call`, sans lire `state.status` ; (b) `cmd_resume` (`cli.py:107-127`) mute
`demande.md` et `etat.json` **avant** le verrou.

Hiérarchie du risque de (a), pour l'ordre des tests — le risque n'est pas uniforme :

| Statut au second `run` | `current_call` | Aujourd'hui |
|---|---|---|
| `WAITING_HUMAN` | `null` | **appel payant**, porte humaine contournée |
| `AWAITING_APPROVAL` / phase `CLOSED` | `null` | `KeyError` — **avant toute mutation** (`workflow.py:162` précède le `mkdir`) |
| `INTERRUPTED` | présent | ré-écrit le même incident ; **pas d'appel** |
| `ERROR` | présent | ré-applique le contrat localement ; **pas d'appel** |

**Correctif.** Sous verrou, après `recheck`, dans cet ordre :

1. **intervention** éventuelle, validée puis appliquée ;
2. **porte d'état** sur l'état résultant : seuls `READY` **sans** appel courant et `RUNNING` **avec**
   appel courant passent ; tout le reste est un `WorkflowError` nommant le statut et la commande qui en
   sort ;
3. dispatch. `_ROLE_OF_PHASE.get(...)` avec refus explicite, pour que `CLOSED` rende une erreur du
   contrat CLI et non une `KeyError`.

L'intervention est consommée à la première itération de la boucle, comme `retry_of`/`retry_reason`
aujourd'hui (`workflow.py:90`).

**`--retry-call` ne publie plus d'état intermédiaire** (Codex) : après validation sous verrou, l'état
`READY` / `current_call=null` reste **en mémoire** ; `new_call()` écrit l'intention portant `retries` et
`retry_reason`, puis publie directement `RUNNING`. Un crash avant cette publication laisse
l'`INTERRUPTED` d'origine intact : la relance est rejouable à l'identique.

**`--answer` devient rejouable après crash** (Codex, simplifié). Ordre : archive **par copie**
(`demande.md` n'est plus jamais absent, contrairement au `rename` de `cli.py:145-153`) → écriture de
`demande.md` → publication d'`etat.json`. À la reprise, un seul cas particulier est reconnu : *l'état
dit encore `WAITING_HUMAN` avec l'ancienne empreinte, et `demande.md` porte exactement l'empreinte de
la réponse fournie* → l'intervention est réputée à moitié appliquée, on republie l'état sans réarchiver
ni réécrire. Toute autre divergence entre `demande.md` et `state.demande_sha256` reste le refus
d'intégrité actuel. **Attention à l'ordre** : ce contrôle de `_preflight` (`workflow.py:104-105`) doit
laisser passer ce cas précis, sans quoi la reprise est refusée avant d'avoir pu réparer.

**Déplacé ici depuis le lot 8 des erreurs** : `adapters.command()` est appelé **avant** la publication
de `CALLING` (deux lignes déplacées dans `new_call`). Un exécutable disparu entre le prévol et l'appel
cesse ainsi de produire un faux « possiblement payé ».

**Ce qui a changé à l'écriture, et pourquoi.**

- **N-01 est entré dans ce lot**, alors qu'aucun lot ne le portait. La porte d'état refuse `ERROR` ;
  sans la table fermée d'incidents relançables, `ERROR` devenait un **cul-de-sac** — plus aucune
  commande n'en sortait. `DECODE_FAILED` y figure déjà bien qu'il naisse au lot 8 : une entrée sans
  producteur ne coûte rien, un statut sans sortie coûte la collaboration.
- **Le rejeu de `--answer` après la troisième écriture est un refus explicite, pas un no-op.** Les deux
  premiers points d'arrêt se rejouent ; le troisième a **déjà** appliqué l'intervention, et c'est
  `resume` seul qui enchaîne. Reconnaître ce cas aurait demandé une seconde branche de reprise —
  exactement ce que cette v2 avait simplifié en écrivant « une seule branche suffit ».
- **L'archive est idempotente** : elle ne recopie pas si la dernière archive porte déjà ce texte. La v2
  ne le disait pas, et sans cela un arrêt entre l'archive et l'écriture de `demande.md` empilait une
  seconde archive au rejeu — **mesuré** par contre-épreuve (`demande.md.001` **et** `.002`).
- **La preuve que `CALLING` précède `Popen` a changé de point d'observation.** Elle se lisait dans
  `FakeAdapter.command()` ; `command()` étant désormais résolu **avant** la publication, ce point ne
  prouvait plus l'ordre. Elle se lit maintenant dans le **processus lancé**, qui relit `etat.json`
  depuis son `cwd`. Le point d'observation d'origine reste utile, et teste l'autre garantie : il y voit
  `READY`, donc `command()` est bien résolu avant toute mutation.

**Coût — mesuré, pas estimé.** `workflow.py` 417 → **607** (+190), `cli.py` 273 → **225** (−48) :
**+142 lignes brutes** pour ~30 annoncées. En **code effectif** (hors blanches, commentaires et
docstrings, mesuré ce jour) : 1 537 → **1 601**, soit **+64** — l'essentiel de l'écart brut est de la
documentation, au taux habituel du projet (70 %). L'estimation à 30 était fausse d'un facteur 2 sur le
code, et de 4,7 sur le brut : elle n'avait chiffré ni N-01, ni la tolérance d'intégrité, ni l'archive
idempotente, ni le déport des trois fonctions de `cli.py`. **Voir §5 — la projection est à rouvrir.**

**Tests exigés** : second `run` après `QUESTION`, après `BLOQUE`, après `ERROR`, après
`AWAITING_APPROVAL` — `FakeAdapter.calls` **inchangé** et code de sortie attendu ; `run` en `RUNNING`
avec appel courant toujours accepté (non-régression §5) ; `resume --answer` et `resume --retry-call`
sous verrou détenu — `demande.md` et `etat.json` **inchangés octet pour octet** ; arrêt injecté après
chacune des trois écritures de `--answer`, puis rejeu — une seule archive, état cohérent ; arrêt injecté
entre la validation de `--retry-call` et `new_call` — l'`INTERRUPTED` reste rejouable.
**Tous écrits** (`tests/test_intervention.py`, 18 tests), plus la table fermée de N-01 dans les deux
sens et le refus vu depuis la CLI.

**Les correctifs ont été prouvés capables de voir leur défaut** (`RULES.md`), un par un :

| Correctif neutralisé | Ce que la suite a montré |
|---|---|
| porte d'état | second `run` après `QUESTION` : `calls` passe de `(1, 0)` à `(2, 1)` — **A et B rappelés**, deux appels payants |
| tolérance d'intégrité du prévol | le rejeu après la deuxième écriture est **refusé avant d'avoir pu réparer** |
| archive idempotente | le rejeu après la première écriture laisse `demande.md.001` **et** `demande.md.002` |

La première contre-épreuve a **corrigé le test** : le compteur d'appels était vérifié *dans* un
`assertRaises`, si bien qu'une porte absente faisait échouer sur « exception non levée » et **masquait
l'appel payant** que le test cherche. Il est désormais vérifié avant.

### Lot 3 — Codes de sortie *(C-03, D-5)*

Table D-5 appliquée dans `_drive` et documentée en §7.

**À corriger dans la suite existante :** `tests/test_cli.py:177-190`
(`test_retry_call_needs_a_non_empty_reason`) attend `0` après un `run` interrompu par délai — **ce test
fige le défaut** et doit attendre 3.

**Coût estimé.** ~10 lignes. **Tests** : un par statut observable depuis la CLI.

### Lot 4 — Intégrité de reprise *(C-05)*

**Défaut.** `transport.read_result` (`transport.py:159-176`) valide le schéma de `resultat.json` sans
jamais le confronter aux fichiers ; `resume_call` (`workflow.py:228-248`) réapplique
`reponse_brute.txt` sans le comparer à `current_call.response_sha256`.

**Correctif.**

1. `read_result` recalcule taille et SHA-256 des deux flux. **`None` et divergence ne sont pas la même
   chose** : `None` = « pas de preuve, appel possiblement payé » ; divergence = « preuve contredite ».
   Une divergence lève une `IntegrityError` typée (Codex), que le moteur consigne en
   `INTEGRITY_MISMATCH` / `INTERRUPTED`, sans appel automatique.
2. **`stdout.txt` ou `stderr.txt` absent alors que `resultat.json` existe est une divergence**, pas une
   erreur d'entrée-sortie générique (Codex).
3. `prompt.txt` vérifié contre `call.prompt_sha256` **avant toute branche** de reprise, `RESPONSE_STORED`
   comprise (Codex).
4. Branche `RESPONSE_STORED` : `normalize(raw).sha256` comparé à `call.response_sha256`.

**Fabriques de tests à reconstruire** (Codex, vérifié) : `tests/test_recovery.py:47,57-58` fabrique des
empreintes `"0"*64`. Sans vraies tailles et empreintes, les tests de reprise **nominale** deviendraient
des scénarios de corruption dès ce lot.

**Coût estimé.** ~25 lignes. **Tests** : `stdout.txt` altéré, `stdout.txt` absent, `reponse_brute.txt`
altéré, `prompt.txt` altéré — `calls == 0`, incident nommé.

### Lot 5 — Corpus vérifié sous verrou *(C-04)*

**Défaut.** `check_corpus` (`workflow.py:139-148`) ne compare que l'empreinte du **texte du manifeste**.

**Correctif.** `corpus.read_manifest(path) -> Manifest` (lecture stricte, symétrique de
`Manifest.to_dict`), puis **un seul contrôle complet, sous verrou, immédiatement avant la construction
de l'appel** (Codex) : pour chaque entrée, présence, **taille**, **SHA-256** ; refus d'un fichier
absent, altéré, **surnuméraire**, ou devenu **lien symbolique** (Codex — symétrie avec `corpus.py:82-85`
qui les refuse déjà à la copie).

**La promesse devient exacte** (Codex) : « contenu vérifié contre le manifeste **avant chaque appel** »,
et non une immutabilité physique — un éditeur qui ignore `verrou.json` pendant que l'agent lit reste
hors de portée du programme. À écrire en §3.

**Coût estimé.** ~37 lignes. **Tests** : fichier altéré, absent, surnuméraire, lien symbolique,
manifeste incohérent, manifeste au schéma cassé — refus **avant** appel, `calls == 0`.

### Lot 6 — Validation des paramètres numériques *(C-08)*

**Défaut.** `--timeout` accepte `0`, les négatifs, `inf` et `nan` (`cli.py:251,256`) ; avec `nan`,
`time.monotonic() >= deadline` reste faux et **le délai dur ne se déclenche jamais**.
`--max-revisions` accepte les négatifs.

**Correctif.** Convertisseurs `argparse` ; validation au chargement de `Configuration`
(`models.py`) ; et **aux entrées Python** `workflow.run()` et `transport.run()` (Codex — ce sont des
surfaces appelées directement par les tests), **avant `Popen` et avant toute publication de `CALLING`**.
Plus : `_schema_version` (`models.py:150-154`) refuse explicitement les booléens, comme `_int` le fait
déjà (`models.py:107-109`) — **vérifié : `True` passe aujourd'hui pour la version 1**.

**Coût estimé.** ~14 lignes. **Tests** : `0`, `-1`, `nan`, `inf` refusés ; `max_revisions` négatif
refusé au chargement ; `schema_version: true` refusé.

### Lot 7 — Nettoyage réellement borné *(C-07, D-7)*

**Défaut, mesuré par Codex** : parent sorti immédiatement, descendant tenant les tubes 22 s →
`transport.run()` rend après **22,11 s** avec `outcome=COMPLETED` et `resultat.json` **présent**. La
terminaison n'avait ni borné la durée, ni changé l'issue. Ma v1 ne l'aurait pas corrigé : chaque pompe
reçoit `_GRACE_SECONDS` **deux fois** (`transport.py:128,135`), `_terminate_tree` ajoute son propre
`wait(_GRACE_SECONDS)` (`transport.py:230`), et `close()` peut attendre le lecteur.

**Correctif.**

1. **Une échéance absolue commune** pour joindre toutes les pompes, pas un délai plein par pompe ; une
   **seconde échéance commune** après la tentative de terminaison. La phase de nettoyage entière est
   ainsi bornée, et la borne est documentée.
2. Une pompe encore vivante ⇒ issue `STREAMS_UNCLOSED`, **`resultat.json` non écrit**, incident
   consigné.
3. **Ne pas appeler `close()` depuis le coordinateur sur un flux encore lu** par une pompe vivante
   (Codex) : le descripteur et le fil daemon vivent jusqu'à la fin réelle du descendant.
4. **`pid.txt` cesse d'être présenté comme le moyen de retrouver l'orphelin** (Codex) : il porte le PID
   du parent, mort dans ce scénario. Sa valeur documentée redevient ce qu'elle est — retrouver l'enfant
   quand il vit encore.

**Test, dans cet ordre** (`RULES.md`) : prouver d'abord, hors suite, que le descendant écrit bien sa
marque quand on ne tue personne ; puis vérifier l'issue, l'absence de `resultat.json`, et une borne
supérieure de durée avec une marge tenant à la machine.

**Coût estimé.** ~14 lignes.

### Lot 8 — Classification des erreurs *(C-10)*

**Correctif, en deux parties.**

*Enveloppe.* `run`, `resume` et `status` capturent des **types de frontière explicites** —
`SchemaError` (existe déjà, `models.py:20`), `WorkflowError`, `LockError`, `TransportError`,
`OSError`, `json.JSONDecodeError`, `UnicodeDecodeError` — et rendent un refus sans traceback. **Pas de
capture globale de `ValueError`** (Codex) : un `ValueError` accidentel du moteur doit rester bruyant.

*Classification durable des erreurs survenant après `CALLING`* (Codex) — sans elle, l'enveloppe
supprime la traceback et laisse au lancement suivant un faux `CALL_POSSIBLY_PAID` :

| Situation | Incident | Statut |
|---|---|---|
| `Popen` échoue (`TransportError`) | `LAUNCH_FAILED` — **l'appel n'est pas parti**, il n'est pas « possiblement payé » | `INTERRUPTED` |
| extraction/décodage impossible alors que les flux sont complets | `DECODE_FAILED`, flux préservés | `ERROR` |
| `command()` échoue | *supprimé par le lot 2* (appel de `command()` avant `CALLING`) | — |

`DECODE_FAILED` entre dans la table des incidents relançables de N-01. La reprise locale ne retente que
l'extraction, quand aucun appel supplémentaire n'est nécessaire.

**Coût estimé.** ~18 lignes. **Tests** : `etat.json` illisible, `etat.json` au schéma invalide, `Popen`
en échec, sortie non-UTF-8 — aucun ne produit de traceback, chacun laisse un état interprétable par la
table §5.

### Lot 9 — Revue canonique *(C-09, D-8)*

`Review.to_dict()` dans `contracts.py` (`.value` des enums, `analysis` conservée, `severity` toujours
émise) ; `echanges/NNNN-critique-B.json` reçoit le canonique ; `revue_normalisee.json` sort de §7 ;
vérifier que `open_findings` (`workflow.py:329-336`) relit ce canonique sans peine.

**Coût estimé.** ~16 lignes. **Test de régression** : une revue rendue dans un bloc clôturé produit un
`echanges/*.json` directement lisible par `json.loads`, et les mêmes constats ouverts après relecture.

### Lot 10 — Frontière d'effets *(C-06, D-6, D-6b)*

Documentation (§1, §8, §12.3) + `invocation_args` dans `intention.json`. **C-06 passe à « risque
accepté — limite déclarée », pas à « résolu ».** La caractérisation des modes restreints des versions
installées est une **session séparée**, consignée dans `conception/CARACTERISATION_CLI.md`, et
conditionne un éventuel durcissement ultérieur.

**Coût estimé.** ~4 lignes de code, le reste en documentation.

### Lot 11 — Validations réelles et guide *(C-11)*

**Après les lots 1 à 5**, et **avec autorisation du PO** (appels payants) :

1. déplacement d'une collaboration en cours d'usage, puis reprise ;
2. une mission réelle de **conception**, une de **recherche**, dans deux permutations différentes,
   **dans une collaboration jetable, hors de tout dossier de valeur** (Codex : c'est le confinement
   réel tant que C-06 est ouvert — le transport lance l'agent avec `cwd` = dossier de collaboration) ;
3. re-caractérisation des versions installées (`2.1.260` / `0.153.2`) ;
4. consignation : versions, **`invocation_args`**, commandes, résultats, incidents, coût approximatif,
   **friction du manifeste de corpus** (`NOTES.md` §3) ;
5. `GUIDE.md` (~1 page) : installation, prérequis CLI, authentification, premier `new`, lecture des
   statuts, reprise, où trouver le livrable.

---

## 4. Tableau de suivi

| Lot | Constats | Préalable à un appel payant | Coût estimé | État |
|---|---|---|---:|---|
| 1 — verrou atomique | C-02b, N-02 | **oui** | +73 *(mesuré)* | **fait** — suite verte, 202 tests |
| 2 — porte d'état + intervention | C-01, C-02a, D-4, **N-01** | **oui** | +142 brut / **+64 effectif** *(mesuré, pour ~30 estimées)* | **fait** — suite verte, 222 tests |
| 3 — codes de sortie | C-03, D-5 | **oui** | ~10 | **fait** |
| 4 — intégrité de reprise | C-05 | **oui** | ~25 | **fait** |
| 5 — corpus sous verrou | C-04 | **oui pour une mission de recherche** | ~37 | **fait** |
| 6 — validation numérique | C-08 | non | ~14 | **fait** |
| 7 — nettoyage borné | C-07, D-7 | non | ~14 | **fait** |
| 8 — classification des erreurs | C-10 | non | ~18 | **fait** |
| 9 — revue canonique | C-09, D-8 | non | ~16 | **fait** |
| 10 — frontière d'effets | C-06, D-6 | décision, pas correctif | ~4 + doc | **fait** |
| 11 — validations réelles et guide | C-11 | — | doc | **bloqué : autorisation PO** |

**Lots 1 à 10 fermés le 2026-09-04.** Suite : **255 tests verts** + 2 ignorés (liens symboliques,
privilège absent sur cette machine), `ruff` et `mypy --strict` verts. Production : **2 659 lignes
brutes / 1 793 en code effectif**.

**Chaque correctif a été prouvé capable de voir son défaut**, un par un, par neutralisation :

| Lot | Correctif neutralisé | Ce que la suite a montré |
|---|---|---|
| 2 | porte d'état | second `run` après `QUESTION` : `calls` `(1, 0)` → `(2, 1)` — A **et** B rappelés |
| 2 | tolérance d'intégrité | le rejeu de `--answer` refusé **avant d'avoir pu réparer** |
| 2 | archive idempotente | `demande.md.001` **et** `.002` après un arrêt injecté |
| 4 | empreintes prompt/réponse | prompt et réponse substitués repris **sans un mot** |
| 4 | empreintes de flux | `stdout.txt` altéré part au contrat et finit en `ERROR` |
| 5 | contenu du corpus | fichier altéré, absent et surnuméraire passent **tous les trois** |
| 6 | domaine du délai | un `run` à `timeout=0` laisse **partir un appel** |
| 7 | borne de nettoyage | *(mesure directe)* 22,11 s en `COMPLETED` → **10,2 s** en `STREAMS_UNCLOSED` |
| 8 | classification d'incident | `Popen` en échec sort en code 1 avec un état `RUNNING` |
| 9 | revue canonique | le registre est **illisible par `json.loads`**, `severity` absente |

**Le lot 11 reste entier et bloqué sur une décision** : il exige des appels payants. `GUIDE.md` n'est
volontairement pas écrit d'avance — prescrire une commande qu'on n'a jamais lancée est exactement ce
que `RULES.md` interdit.

**Conditions avant la première mission réelle** (reprises de Codex, retenues) : lots 1 à 4 fermés ·
lot 5 fermé pour toute mission de **recherche** · collaboration jetable et isolée tant que C-06 est
ouvert · `ruff`, `mypy --strict` et `pytest` verts **sur le commit exact essayé** · versions des deux
CLI et `invocation_args` consignés.

Un commit par lot, préfixe `fix:` (`docs:` pour les lots documentaires), message sans accents.
`ruff check .`, `mypy --strict src tests`, `pytest` verts **à chaque lot**. Clôture d'un constat :
correctif · test qui échouait avant et passe après · commande de validation exécutée · commit · état
mis à jour dans ce tableau.

---

## 5. Budget de lignes — arbitré, et où se trouve la marge

Le PO a validé l'augmentation le 2026-09-04. Chiffres tenus à jour par honnêteté, pas comme une porte :

| | Brut | Code effectif |
|---|---:|---:|
| Production au moment du plan (12 modules) | 2 070 | 1 537 *(à HEAD du lot 1)* |
| **Production, lots 1 à 10 fermés** | **2 659** | **1 793** |
| Écart au plan | **+589** pour ~+205 estimées | +256 |
| Projection v2, annoncée | ~2 275 | — |

**La projection v2 était fausse d'un facteur ~3 sur le brut, et le chiffre final est là.** Deux faits,
mesurés — non plus extrapolés :

- **Les estimations de ce plan étaient basses d'un facteur 2 à 5 lot par lot** : lot 1, 37 → 73 ;
  lot 2, 30 → 142. Sur l'ensemble, +205 estimées contre **+589 mesurées**. La prévision par lot n'a
  jamais été fiable ici, et il n'y a pas de raison de croire qu'elle le devienne : ce qui coûte, ce
  n'est pas le correctif, c'est le motif écrit à côté.
- **Le brut n'est pas la bonne unité pour ce projet.** Mesuré : **1 793 lignes de code effectif** pour
  2 659 brutes — 67 %. Contre l'objectif de ~1 500 de `POURQUOI.md`, la mesure comparable est donc
  **1 793, soit +20 %**, et non +77 % comme le brut le laisserait croire. L'écart est à deux tiers de
  la documentation, parce que ce code porte le motif de chaque garantie — c'est un choix du projet,
  pas une dérive, et c'est précisément ce qui a permis de reprendre ce plan sans le relire en entier.

Trois choses restent vraies, et elles répondent au « nous sommes extrêmement loin du projet initial » :

- **Aucun de ces ajouts n'est une accrétion de contrôle** au sens de `POURQUOI.md`. Ce sont des
  garanties **déjà annoncées** par la conception et non tenues par le code : porte humaine, verrou,
  intégrité, codes de sortie. Le coût vient de promesses faites, pas de fonctions nouvelles.
- **L'écart au chiffre de 1 500 n'est pas l'écart au projet initial.** Le prédécesseur avait
  7 676 lignes de boucle A/B **plus 26 997 d'appareil d'autonomie** : c'est cette seconde masse qui a
  tué le projet, et elle vaut toujours zéro ligne ici. Les cinq interdits sont tenus sans exception.
- **La marge, si le PO en veut, est dans les lots 7, 9 et 10** — les trois qui proposent de *retirer une
  promesse* plutôt que de la financer. Le seul lot qui aurait pu déraper était l'objet Job Windows
  (~60 lignes) : il est écarté.

---

## 6. Ce qui reste à décider

**Deux choses.**

1. **L'autorisation d'appels payants** pour le lot 11, une fois les lots 1 à 5 fermés.
2. **La projection de lignes, rouverte le 2026-09-04 après la mesure du lot 2** (§5). Le PO avait
   validé une augmentation sur une projection de ~2 275 brutes ; elle est dépassée avant le lot 3, et
   la mesure suggère 2 560 à 2 700 à terminaison — soit ~1 900 en code effectif. La question à
   trancher n'est pas « accepte-t-on le chiffre ? » mais **« qu'est-ce qu'on retire en échange ? »**
   (`POURQUOI.md`, règle 2). La marge reste celle du §5 : lots 7, 9 et 10, les trois qui retirent une
   promesse au lieu de la financer.

Aucun arbitrage technique n'est ouvert. D-4 à D-8, N-01, N-02 et D-5 sont tranchés ; Codex a écrit que
l'implémentation peut commencer sans nouveau tour de sa part une fois ses points intégrés — ils le sont.

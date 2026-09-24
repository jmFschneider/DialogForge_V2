# Commandes

Référence des neuf commandes, des statuts et des codes de sortie. Pour un premier parcours,
commencez par [`PRISE_EN_MAIN.md`](PRISE_EN_MAIN.md). `dialogforge <commande> --help` donne la
même information en ligne.

| Commande | Rôle | Appelle les agents ? |
|---|---|---|
| [`new`](#new) | Créer une collaboration | non |
| [`run`](#run) | Lancer ou reprendre le cycle | **oui** (quota) |
| [`resume`](#resume) | Sortir d'un arrêt | **oui** — `--reprocess` relit sans appel, mais la reprise qui suit peut appeler |
| [`status`](#status) | Dire où en est la collaboration | non, lecture seule |
| [`show`](#show) | Lire le résultat avant de décider | non, lecture seule |
| [`decide`](#decide) | Consigner votre décision | seulement `--correct` |
| [`plan`](#plan) | Résumé pour un plan PWF, liaison facultative | non |
| [`list`](#list) | Énumérer les collaborations d'un dossier | non, lecture seule |
| [`gui`](#gui) | Ouvrir la fenêtre locale (Tkinter) | comme la CLI, selon l'écran ouvert |

`<dossier>` désigne le dossier d'une collaboration, celui que `new` a créé.

## new

`dialogforge new <dossier> (--demande <fichier> | --cadrer | --cadrer-avec-agent) [options]`

Crée le dossier (qui ne doit pas exister) et fige les réglages dans `configuration.json`. Tout est
vérifié avant toute écriture : un refus ne laisse rien derrière lui, un cadrage interrompu non plus.

| Option | Sens |
|---|---|
| `--demande <fichier>` | Le fichier texte de votre demande. Aucun appel. |
| `--cadrer` | Écrire la demande par un questionnaire de terminal, sans appel de modèle. |
| `--cadrer-avec-agent` | Construire la demande en conversation avec un agent de cadrage, **qui effectue des appels avant la création** ([détail](#cadrage-avec-agent)). Les trois voies s'excluent ; l'une est exigée. |
| `--agent-cadrage` | L'outil qui mène le cadrage ; exigé avec `--cadrer-avec-agent`, refusé sans lui. |
| `--model-cadrage`, `--effort-cadrage` | Modèle et effort de l'agent de cadrage ; mêmes règles que pour A et B. |
| `--kind` | `conception` ou `recherche`. |
| `--reviewer-access` | `consult` (B garde les outils de sa CLI) ou `context-only` (B n'en a aucun). |
| `--agent-a`, `--agent-b` | Qui produit, qui critique : `claude` ou `codex`. |
| `--source-root <dossier>` | Le dossier des sources. Va avec `--source-list`. |
| `--source-list <fichier>` | Un chemin par ligne, relatif à `--source-root`. Va avec `--source-root`. |
| `--source-label <nom>` | Nom du corpus ; défaut : le nom de `--source-root`. |
| `--model-a`, `--model-b` | Modèle de chaque rôle ; défaut : celui de l'adaptateur. |
| `--effort-a`, `--effort-b` | Effort de raisonnement, facultatif. Le vocabulaire est celui de l'outil ([détail](CONFIGURATION.md#effort-de-raisonnement)). |
| `--web-access` / `--no-web-access` | Autoriser ou non la recherche web, pour A et B ; fermé par défaut ([détail](CONFIGURATION.md#accès-web)). |
| `--max-revisions <N>` | Nombre maximal de révisions ; entier positif ou nul. Défaut : 2. |
| `--config <fichier>` | Fichier de réglages à utiliser ([détail](CONFIGURATION.md)). |

`--kind`, `--reviewer-access`, `--agent-a` et `--agent-b` sont indispensables : sur la ligne de
commande ou dans le fichier de réglages, sinon `new` refuse. Une mission de **recherche** exige un
corpus, et un corpus vide est refusé.

### Cadrage avec agent

Avec `--cadrer-avec-agent`, un agent (F) lit une **copie** des sources données par `--source-root` /
`--source-list` (facultatives en conception), puis vous pose ses questions une par une. Votre idée se
saisit sur plusieurs lignes, close par une ligne ne contenant qu'un point ; vos réponses aussi. À
tout moment : `/clore` (rédiger maintenant) ou `/annuler`. F propose la clôture au plus tard après
trois réponses, puis toutes les deux ; vous choisissez de continuer, corriger un point, rédiger ou
annuler. Le brouillon s'affiche ensuite : `v` le valide et crée la collaboration, `m` le remplace
par votre texte, `c` reprend le cadrage, `a` abandonne. **Rien n'est créé avant `v`** : `demande.md`
est le texte que vous avez relu. La conversation, ses traces et sa provenance sont rangées dans
`cadrage/`, pour mémoire — A et B ne les voient jamais.

Toute la conversation tient dans **une seule session** de l'outil, reprise à chaque tour : l'idée et
les sources ne sont lues qu'une fois. Un adaptateur qui ne sait pas tenir une telle session est
refusé avant tout appel. Le délai par échange est celui de `timeout` dans le fichier de réglages.

## run

`dialogforge run <dossier> [--timeout <secondes>] [--config <fichier>]`

Lance le cycle, ou le reprend là où il s'est arrêté. C'est le seul moteur : il s'exécute dans votre
terminal, s'arrête à la fin et ne laisse rien tourner. Avant chaque appel il vérifie l'état du
dossier ; un statut qui n'appelle pas `run` est refusé, avec le nom de la commande qui convient.

| Option | Sens |
|---|---|
| `--timeout <secondes>` | Délai dur par appel. Défaut : le fichier de réglages, sinon 1800. |
| `--config <fichier>` | Fichier de réglages (seul `timeout` s'y lit ici). |

**Ctrl+C** se fait en deux temps : le premier demande une pause à la frontière d'appel (rien n'est
perdu, code `6`), le second interrompt l'appel en cours, qui a pu être payé (`INTERRUPTED`).

## resume

`dialogforge resume <dossier> [--answer <fichier> | --retry-call <uuid> | --reprocess <uuid>] [--reason-file <fichier>]`

Applique **une** intervention humaine sous le verrou, remet le dossier dans un état admissible, puis
reprend le cycle. Sans option, il se comporte comme `run`.

| Option | Sens |
|---|---|
| `--answer <fichier>` | Répond à une question de A ou à une revue incohérente (`WAITING_HUMAN`). Le fichier **complète** la demande, il ne la remplace pas. |
| `--retry-call <uuid>` | Relance l'appel interrompu : **nouvel appel payant**. Exige `--reason-file`. |
| `--reprocess <uuid>` | Relit **localement** la réponse déjà reçue et conservée, sans appel. Exige `--reason-file`. |
| `--reason-file <fichier>` | Le motif, écrit par vous. Exigé avec `--retry-call` et `--reprocess`, refusé sans. |
| `--timeout`, `--config` | Comme pour `run`. |

`--answer` est incompatible avec les autres ; `--retry-call` et `--reprocess` s'excluent. Le
retraitement est tracé dans `appels/<appel>/retraitements.jsonl` ; les données brutes ne sont jamais
touchées, et un échec laisse le statut `ERROR`.

## status

`dialogforge status <dossier> [--json]`

Dit où en est la collaboration : genre, statut, phase, révision, objections ouvertes, âge du corpus,
dernier incident, décision courante et **prochaine action**. Strictement en lecture seule.

| Option | Sens |
|---|---|
| `--json` | La même information en une ligne JSON. |

## show

`dialogforge show <dossier> [--no-document]`

Ce qu'il faut lire avant de décider : la décision courante, les corrections principales, les
réserves (les objections restées ouvertes, et les vôtres), la prochaine action, puis le document.
Lecture seule.

| Option | Sens |
|---|---|
| `--no-document` | Le résumé seul, sans le document. |

## decide

`dialogforge decide <dossier> (--accept | --accept-with-reserves <texte> | --correct <fichier> | --stop) [--reason <texte>]`

Une décision, et une seule, par commande. Elle est **datée** et porte sur une **version précise** du
livrable (empreintes du livrable, de la revue et de la demande) dans `decisions.json`. Accepter ne
change pas le statut du moteur : `AWAITING_APPROVAL` reste `AWAITING_APPROVAL`.

| Option | Sens |
|---|---|
| `--accept` | Accepter cette version. Rejouer la même décision sur la même version ne la consigne pas deux fois. |
| `--accept-with-reserves <texte>` | Accepter, avec vos réserves (le texte est exigé). |
| `--correct <fichier>` | Correction ciblée : le fichier complète la demande ; A révise, B relit en ciblé. Un tour **au-delà du plafond**, explicite et tracé. **Appelle les agents.** |
| `--stop` | Arrêter, définitivement (statut `STOPPED`). Les preuves d'appel restent. |
| `--reason <texte>` | Motif de l'arrêt ; ne vaut qu'avec `--stop`. |
| `--timeout`, `--config` | Comme pour `run` ; ne servent qu'à `--correct`. |

## plan

`dialogforge plan <dossier> [--link <id-du-plan> [--plan-root <dossier>] | --unlink]`

Relie **facultativement** une collaboration à un plan PWF. Sans option, imprime le résumé à reporter
**à la main** dans le plan : statut, décision, prochaine action, chemins du dossier, du document et de
la dernière revue. Le plan reste seul propriétaire de l'avancement : l'outil n'y écrit jamais.

| Option | Sens |
|---|---|
| `--link <id-du-plan>` | Résout le plan par le script public de PWF **avant** d'écrire, puis enregistre la référence dans `plan.json`. Un identifiant inexistant, mal formé ou ambigu est refusé. |
| `--plan-root <dossier>` | Racine du projet qui porte `.planning/` ; défaut : le dossier courant. |
| `--unlink` | Retire la liaison, rien d'autre. |

Le cycle ne lit pas `plan.json` : sans liaison, avec une liaison cassée ou après `--unlink`, tout
fonctionne comme avant.

## list

`dialogforge list <dossier-racine>`

Énumère les collaborations d'un dossier, **calculées** depuis les dossiers : pas d'index, rien à garder
à jour. Un dossier illisible est nommé plutôt que caché.

## gui

`dialogforge gui`

Ouvre la fenêtre locale (Tkinter/ttk) : accueil, création, suivi et décision d'une collaboration à
la fois — jamais de worker ni de processus détaché ([`conception/GUI_V1.md`](../conception/GUI_V1.md)).
CLI et GUI partagent les mêmes dossiers, la même façade et les mêmes actions permises : ce que l'une
fait, l'autre le voit au prochain rafraîchissement.

Au lot 3, l'écran de suivi est **strictement en lecture seule** : accueil, collaborations récentes,
ouverture et lecture des documents. Répondre, relancer, retraiter, corriger et décider arrivent au
lot 5.

## Statuts

`status` dit toujours où vous en êtes. Chaque statut a une sortie, et une seule.

| Statut | Ce que ça veut dire | Ce que vous faites |
|---|---|---|
| `READY` | Le cycle est prêt, ou une pause a été demandée. | `run <dossier>` |
| `RUNNING` | Un appel est en cours — ou le processus s'est arrêté en pleine exécution. | `run <dossier>` reprend localement, sans repayer d'appel |
| `AWAITING_APPROVAL` | Le cycle est allé à son terme. **Pas accepté.** | `show`, puis `decide` |
| `WAITING_HUMAN` | A a posé une question, ou une revue est incohérente. | `resume --answer <fichier>`, ou `decide --stop` |
| `INTERRUPTED` | L'appel n'a pas abouti : délai, quota, arrêt brutal. | `resume --retry-call <uuid> --reason-file <fichier>`, ou `decide --stop` |
| `ERROR` | La réponse est arrivée (et payée) mais ne respecte pas le contrat. | `resume --reprocess <uuid> --reason-file <fichier>` (local), ou `--retry-call` (payant), ou `decide --stop` |
| `STOPPED` | Vous avez arrêté la collaboration. | Rien : c'est définitif. |

Les phases, dans l'ordre du cycle : `PROPOSAL_A` (A produit), `REVIEW_B` (B critique),
`REVISION_A` (A révise), `CLOSED` (version examinée promue, bilan écrit).

## Codes de sortie

Le code décrit le **résultat de la commande**, jamais l'approbation du livrable.

| Code | Sens |
|---|---|
| `0` | Terminé. Pour `run`, le cycle s'est arrêté où il devait (`AWAITING_APPROVAL`) : ce n'est **pas** une acceptation. |
| `1` | Refus avant toute modification : option manquante, dossier inexistant, statut qui n'admet pas la commande… |
| `2` | Erreur d'usage (option inconnue ou mal formée), rendue par `argparse`. |
| `3` | Interrompu (`INTERRUPTED`). |
| `4` | Erreur (`ERROR`). |
| `5` | En attente de vous (`WAITING_HUMAN`). |
| `6` | Pause demandée par Ctrl+C (`READY`) : `run` reprend au même endroit. |

## Incidents : un appel a-t-il été payé ?

Quand un appel échoue, `status` et `show` disent **si** il a pu être payé — jamais combien, ni
jusqu'à quand. Un code de retour non nul ne distingue pas un quota épuisé d'une erreur de
configuration : le message de l'outil est cité **tel quel**, et rien n'en est déduit. Rien n'est
jamais relancé tout seul.

| Incident | Payé ? | Sens |
|---|---|---|
| `LAUNCH_FAILED` | non | L'outil n'a pas démarré (introuvable, refusé) : l'appel n'est pas parti. |
| `TIMEOUT` | peut-être | Le délai dur est écoulé et l'outil a été arrêté. |
| `OUTPUT_LIMIT` | peut-être | La sortie a dépassé la limite. |
| `INTERRUPTED_BY_USER` | peut-être | Vous avez interrompu l'appel (Ctrl+C). |
| `STREAMS_UNCLOSED`, `STREAM_FAILED` | peut-être | Les flux n'ont pas pu être lus jusqu'au bout : ce qui est sur disque est peut-être partiel. |
| `SOURCES_MODIFIED` | peut-être | Le corpus a changé pendant l'appel : la réponse n'est pas retenue. Rétablissez-le, puis relancez. |
| `CALL_POSSIBLY_PAID` | inconnu | Le processus s'est arrêté pendant un appel : impossible de savoir. |
| `CLI_FAILED` | inconnu | L'outil a rendu un code de retour non nul (quota, configuration, modèle…). |
| `INTEGRITY_MISMATCH` | inconnu | Un fichier de l'appel ne correspond plus à son empreinte : rien n'est repris d'une preuve contredite. |
| `CONTRACT_ERROR` | oui | La réponse est arrivée mais ne respecte pas le contrat ; conservée telle quelle. |
| `DECODE_FAILED` | oui | La réponse est arrivée mais ses octets sont illisibles ; conservés tels quels. |

Après un arrêt brutal, « l'appel n'est pas parti » ne peut pas être **prouvé** : seul `LAUNCH_FAILED`
(échec de lancement observé) l'est. Le reste est « inconnu », et dit comme tel.

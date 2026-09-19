# DialogForge_2

> **Dépôt de développement de DialogForge V2.** Le contenu ci-dessous est celui d'IAbinome, repris
> tel quel comme socle. Le nom affiché et le point d'entrée V2 seront introduits plus tard : au
> lot 0, le package s'appelle toujours `iabinome`, délibérément, pour vérifier le réemploi sans
> mélanger changements fonctionnels et renommage.

## Origine du code

| Élément | Valeur |
|---|---|
| Source | `C:\Projets\IAbinome`, clone local complet avec historique Git |
| Commit de départ | `4a11cc7eae47a4920b845fda6e65937557a967cf` — *docs: cloturer le plan correctif et preparer la session CONTEXT_ONLY* |
| Écart avec la référence d'étude | Aucun : le HEAD d'IAbinome au 18 septembre 2026 **est** le commit de référence de `astra/` |
| Branche de travail | `v2-socle` |
| Destination de push | Aucune. Le remote `origin` a été retiré après le clone : impossible d'écrire dans IAbinome par erreur |
| Non importés | Environnement virtuel, fichiers non suivis (`DIAGNOSTIC_CHROME_GPU.md`), configuration personnelle (`iabinome.toml`, ignoré par Git) |

Le plan de référence est [`astra/06_plan_mise_en_oeuvre.md`](../DialogForge_Next/astra/06_plan_mise_en_oeuvre.md)
du dossier d'étude `DialogForge_Next`. Les dépôts sources — IAbinome et DialogForge — restent
inchangés ; ce dépôt ne réécrit pas les missions historiques.

## Périmètre de la première livraison

**Couvert (J3) :** conception et synthèse **sur corpus local fourni**, en terminal guidé —
demande → production A → critique B indépendante → correction avec une disposition explicite par
objection → livrable et décisions restantes → acceptation, correction ciblée ou arrêt, avec reprise
après incident sans rejouer un appel ambigu.

**Hors périmètre à ce stade :** recherche externe (profil distinct, à qualifier), développement
assisté (lot 4), interface graphique (extension conditionnelle après J3), service permanent ou
reprise autonome après fermeture du programme.

---

# IAbinome

Deux agents IA en ligne de commande : **A produit, B critique, vous arbitrez.**
Le livrable est un document de conception ou de recherche — jamais une exécution.

Tout tient dans un dossier sur disque. Vous lancez, ça tourne, vous fermez le terminal.

---

## Installer

Python 3.12, **aucune dépendance**. Les deux CLI d'agents doivent être sur le `PATH`.

```
pip install -e .
python -m iabinome --help
```

## En trois commandes

```
python -m iabinome new ./ma-collab --demande ./demande.md \
    --kind conception --reviewer-access consult --agent-a codex --agent-b claude

python -m iabinome run ./ma-collab

python -m iabinome status ./ma-collab

python -m iabinome show ./ma-collab            # lire le résultat avant de décider
python -m iabinome decide ./ma-collab --accept
```

`demande.md` est votre texte : ce que vous voulez, et **à quoi vous reconnaîtrez que c'est fini**.
Ce second point est ce qui fait la différence entre une critique utile et une critique polie.

**Format court.** Six sections, dans l'ordre que vous voulez, en titres `##` : *Objectif*,
*Livrable*, *Sources*, *Contraintes*, *Non-objectifs*, *Critères de fin*. C'est un repère, pas
une porte : une demande libre est acceptée, `new` dit sur la sortie d'erreur quelles sections
manquent, et A pose une question si ce manque change le résultat.

**Pas de fichier prêt ?** `--cadrer` remplace `--demande` par un questionnaire de terminal, une
réponse par section (fermée par une ligne vide). Il n'appelle aucun modèle, et n'écrit rien si
vous l'interrompez :

```
python -m iabinome new ./ma-collab --cadrer --kind conception --reviewer-access consult \
    --agent-a codex --agent-b claude
```

**Provenance.** `provenance_demande.json` consigne chaque version de la demande : d'où elle vient
(fichier, cadrage, complément apporté par une réponse), la version qu'elle prolonge, la revue à
laquelle l'ancienne répondait. Chaque ancienne version reste lisible en
`demande.md.001`, `.002`…

**Répondre à une question.** `resume --answer <fichier>` **complète** la demande, il ne la remplace
pas : le texte existant reste en place, intact, et la réponse s'y ajoute sous « Précisions n°1 »,
« n°2 »… dans une nouvelle version complète de `demande.md`, qui reste l'unique autorité. Une
réponse courte suffit donc : aucune section ni exigence existante ne peut disparaître. Remplacer
la demande en entier n'est pas une réponse ; ce sera, le jour où le besoin se présente, une
commande explicite et distincte.

Pour une mission de recherche, un corpus est **obligatoire**. Il se déclare par un fichier qui
liste des chemins, un par ligne, relatifs à `--source-root` :

```
python -m iabinome new ./etude --demande ./question.md --kind recherche \
    --reviewer-access consult --agent-a claude --agent-b codex \
    --source-root . --source-list ./corpus.txt --max-revisions 1
```

Les fichiers sont **copiés octet pour octet** et hachés dans `corpus/manifeste.json`. Le corpus,
c'est exactement ce que le manifeste énumère — ni plus, ni moins : ajouter un fichier dans le
dossier après coup ne l'y fait pas entrer, et le retirer fait échouer la vérification.

## Le fichier de configuration

Sept drapeaux sur chaque `new`, c'est six de trop. Un fichier `iabinome.toml` en fournit les
valeurs par défaut :

```toml
# Outils par role
agent_a = "codex"
agent_b = "claude"

# Modeles. Sans ces lignes, chaque adaptateur applique son propre defaut.
model_b = "sonnet"

max_revisions = 1
timeout = 600
reviewer_access = "consult"
kind = "conception"
```

```
python -m iabinome new ./ma-collab --demande ./demande.md
```

**Cherché dans l'ordre :** `--config <chemin>`, puis `./iabinome.toml`, puis `~/.iabinome.toml`.
Le premier trouvé gagne ; les autres sont ignorés, jamais fusionnés. La commande annonce sur la
sortie d'erreur quel fichier a servi et ce qu'elle y a pris.

**Précédence :** drapeau de la ligne de commande > fichier > défaut du programme.

Trois choses qu'il ne fait pas, et c'est délibéré :

- **aucun chemin ne s'y règle** — ni corpus, ni demande : un chemin dans un fichier global rendrait
  la collaboration non reproductible d'une machine à l'autre ;
- **il ne touche jamais une collaboration existante** — une fois le `new` passé,
  `configuration.json` est la seule vérité, et éditer le fichier ne déplace rien de ce qui tourne ;
- **une clé inconnue est refusée**, elle n'est pas ignorée. Un réglage silencieusement perdu est
  pire qu'un réglage absent : vous croyez l'avoir posé.

## Le cycle

```
demande.md → A produit → B critique → A révise → B relit → (N fois max) → livrable
```

`--max-revisions` fixe le N. À `0`, B critique une fois et la proposition est livrée sans révision.

**Le livrable est ce que B a examiné, jamais une réécriture.** Quand B accepte, ou au plafond, le
document que B vient de relire est promu **octet pour octet** dans `livrables/version_finale.md` :
il n'y a plus d'appel de finalisation, donc un appel payant de moins et plus de texte que personne
n'aurait relu. Dès qu'une correction a eu lieu, la relecture de B est **ciblée** : les objections
traitées et les régressions, pas une nouvelle critique. Une remarque nouvelle est notée et
présentée, elle n'ouvre pas de tour de plus.

**`livrables/bilan.md`**, écrit par le programme sans modèle, dit ce qui est livré, ce qui l'a
examiné (empreintes de la demande, du livrable et de la revue), le registre des objections et les
**désaccords restants**. Au plafond, ils sont présentés, pas traités. Un tour de plus est une
décision humaine explicite, tracée (point 1.4 du plan).

B reprend **exactement une fois** chaque constat resté ouvert dans sa revue précédente. Un constat
qui disparaît ou qui se dédouble fait échouer le contrat : c'est ce qui empêche une critique
gênante de s'évaporer d'un tour à l'autre.

**Les objections ne s'écrasent pas.** L'énoncé d'un constat est celui de son premier tour : si B le
réécrit pour dire « désormais résolu » (mesuré sur une revue réelle), le programme garde l'énoncé
et récupère la réécriture comme justification. La justification d'une disposition est un champ
à part, et **une fermeture sans justification reste ouverte** : une absence ne clôture jamais.

**A répond à chaque objection ouverte.** Après son document, A écrit une ligne `IABINOME:REPONSES`
puis un objet JSON : une réponse par constat — `CORRIGE`, `CONTESTE`, `REPORTE` ou `ARBITRAGE` —,
motivée sauf pour `CORRIGE`. Le document reste du texte libre. Une réponse absente, dupliquée ou
à un constat inconnu est un échec de contrat (la réponse brute reste dans `appels/`). B voit, au
tour suivant, ce que A a répondu. Le registre par objection se relit dans `echanges/`
(`NNNN-critique-B.json`, `NNNN-reponses-A.json`) ; `objections.ledger()` l'assemble.

## Quand ça s'arrête

`status` dit toujours où vous en êtes. Chaque statut a une sortie, et une seule :

| Statut | Ce que ça veut dire | Ce que vous faites |
|---|---|---|
| `AWAITING_APPROVAL` | le cycle est allé à son terme — **pas accepté** | `show`, puis `decide` (ci-dessous) |
| `WAITING_HUMAN` | A a posé une question, ou une revue est incohérente | `resume --answer <fichier>` |
| `INTERRUPTED` | l'appel n'a pas abouti — délai, quota, arrêt brutal | `resume --retry-call <uuid> --reason-file <fichier>` |
| `ERROR` | la réponse est arrivée (et payée) mais ne respecte pas le contrat | `resume --reprocess <uuid> --reason-file <fichier>` : relit **localement** la réponse conservée, sans appel ; ou `--retry-call` (nouvel appel payant) |
| `STOPPED` | vous avez arrêté la collaboration (`decide --stop`) | rien : c'est définitif |

Le message de refus **nomme toujours la commande** qui sort du statut : vous n'avez pas à
retrouver ça ici. `status` (et `show`) donnent aussi la **prochaine action**, l'incident et la
décision en clair — sans ouvrir un journal : pour un appel interrompu, l'`uuid` à relancer et le
fait qu'il a pu être payé ; pour une question, le fichier de la question.

## Lire, décider

**« Terminé » n'est pas « accepté ».** Le cycle s'arrête en `AWAITING_APPROVAL` sans rien
approuver ; l'acceptation est **votre** décision, consignée dans `decisions.json` (lisible à l'œil,
ajouté à chaque décision, pas de base). Chaque entrée est **datée et porte sur une version
précise** — les empreintes du livrable, de la revue et de la demande. Si le livrable change
ensuite, `status` le dit : la décision porte sur une version antérieure.

`show` affiche ce qu'il faut lire avant de décider : la décision courante, les **corrections
principales**, les **réserves** (les objections restées ouvertes, et les vôtres), la **prochaine
action**, puis le document (`--no-document` pour le résumé seul). `decide` prend une seule
décision par commande :

| Commande | Effet |
|---|---|
| `decide <dossier> --accept` | consigne l'acceptation de **cette version** ; le statut du moteur ne bouge pas |
| `decide <dossier> --accept-with-reserves "<texte>"` | idem, avec vos réserves (le texte est exigé) |
| `decide <dossier> --correct <fichier>` | **correction ciblée** : le fichier complète la demande (comme une réponse), puis A révise et B relit en ciblé — un tour **au-delà du plafond**, explicite et tracé |
| `decide <dossier> --stop [--reason "…"]` | arrête, définitivement (statut `STOPPED`) ; les preuves d'appel restent |

`list <dossier>` énumère les collaborations d'un dossier, **calculées** depuis les dossiers : pas
d'index, rien à garder à jour, et un dossier illisible est nommé plutôt que caché.

Codes de sortie : `0` terminé · `1` refus avant toute modification · `2` erreur d'usage
(`argparse`) · `3` interrompu · `4` erreur · `5` en attente de vous · `6` pause demandée.

**Un incident dit s'il est payé — jamais combien, ni jusqu'à quand.** `status` et `show` distinguent
trois cas : une réponse **reçue mais mal interprétée** (payée, conservée, relisible en local), un
appel **qui n'est pas parti** (`LAUNCH_FAILED` : rien de payé), et une **issue inconnue** (délai,
interruption, arrêt brutal, code de retour non nul : l'appel a pu être payé). Un code de retour non
nul ne distingue pas un quota épuisé d'une erreur de configuration : le message de l'outil est cité
**tel quel**, et aucun coût ni aucune heure de reprise n'est déduit. Rien n'est jamais relancé tout
seul. Le retraitement local est tracé dans `appels/<appel>/retraitements.jsonl` ; les données brutes
ne sont jamais touchées.

**Ctrl+C se fait en deux temps.** Le premier demande une **pause à la frontière d'appel** : l'appel
en cours se termine, le cycle s'arrête, rien n'est perdu (code `6`, `run` reprend au même endroit).
Le second est un **arrêt immédiat** : l'appel en cours est interrompu, il a pu être payé (statut
`INTERRUPTED`, aucun rejeu automatique). Le programme affiche ces conséquences au moment de la
demande, puis la prochaine action.

**Ce qu'un arrêt brutal garantit, et ce qu'il ne garantit pas.** Les artefacts d'un appel sont
écrits avant toute transition d'état, et rien n'est jamais rejoué tout seul — donc vous ne payez
pas deux fois par accident, et la réponse brute d'un appel refusé reste sur le disque. En revanche
un `INTERRUPTED` **ne repart pas seul** : il attend une relance que vous motivez par écrit. C'est
volontaire.

## Ce que voit chaque agent

A et B tournent **hors du dossier de collaboration**, dans un dossier jetable qui ne contient
qu'une **copie** du corpus (`corpus/fichiers/`) et disparaît après l'appel : ils ne voient ni
`appels/`, ni le journal de l'autre, ni les anciennes versions de la demande. Ils héritent de
votre environnement **moins** les variables que l'outil qui vous a lancé y dépose (identifiants de
session, jeton de messagerie, racine de plan) ; `intention.json` nomme celles qui ont été retirées,
jamais leurs valeurs. Chaque adaptateur demande à sa CLI la **lecture seule** et une **session
fraîche** ; un adaptateur qui ne le déclare pas est refusé avant tout appel. Si le corpus change
pendant un appel, la réponse n'est pas retenue (`SOURCES_MODIFIED`).

**Ce n'est pas un confinement du système d'exploitation** : un agent qui écrit un chemin absolu
n'est arrêté que par sa propre CLI, dont ces protections ne sont **pas encore mesurées** en réel.
La frontière obtenue, ses limites et ce qui reste à vérifier : `reference/FRONTIERE_ROLES.md`.

## Relier une collaboration à un plan PWF (facultatif)

`plan <dossier> --link <id-du-plan> [--plan-root <racine du projet>]` résout le plan par le script
public de PWF **avant** d'écrire quoi que ce soit, puis enregistre la référence dans `plan.json` —
l'identifiant et la racine, jamais une phase. `plan <dossier>` (sans option) imprime le **résumé à
reporter à la main** dans le plan : statut, décision, prochaine action, chemins du dossier, du
document et de la dernière revue. `plan <dossier> --unlink` retire la liaison.

**Le plan reste seul propriétaire de l'avancement** : l'outil n'y écrit jamais, et ne synchronise
aucune case. Le cycle ne lit pas `plan.json` : sans liaison, avec une liaison cassée ou après
`--unlink`, le livrable reste lisible, `run`/`decide` fonctionnent, et aucun appel n'est déclenché.
Le résolveur public rend **toujours 0** ; un identifiant inexistant, mal formé ou ambigu y donne une
**sortie vide**, que l'outil traite comme un refus — jamais comme un succès.

## Ce qu'il y a dans une collaboration

```
ma-collab/
├── demande.md                    votre demande, normalisee
├── configuration.json            fige au `new` : outils, modeles, N revisions
├── etat.json                     ou en est le cycle — lisible a l'oeil
├── corpus/manifeste.json         chemins, tailles, empreintes
├── corpus/fichiers/              les copies octet pour octet
├── echanges/                     propositions de A, revues de B, en clair
├── appels/NNNN-<role>-<uuid>/    prompt, flux bruts, resultat, incident
├── decisions.json                vos décisions, datées, sur une version précise
├── livrables/version_finale.md   le document (la version que B a examinée)
└── livrables/bilan.md            ce qui est livré, examiné, et resté en désaccord
```

`echanges/` est ce qu'on lit pour suivre le raisonnement. `appels/` est la preuve : le prompt exact
envoyé, la réponse exacte reçue, le code de retour et la durée. Rien n'y est résumé.

## Ce que l'outil ne fait pas

Ce n'est pas une liste de limitations : c'est le périmètre, et il est tenu volontairement.

- **Il n'exécute rien.** Le livrable est un document, que vous appliquez ensuite à la main.
- **Aucune base de données**, aucun service, aucune tâche planifiée. Des fichiers, et c'est tout.
- **Aucun budget ni quota interne.** Les plafonds de votre fournisseur suffisent ; l'outil ne
  compte pas vos jetons.
- **Pas d'interface graphique.**

**Sur les sources externes**, soyons précis, parce que la formule courte serait fausse. *Le
programme* n'en consulte aucune : il appelle deux CLI et lit leurs flux, rien d'autre. *Les agents*,
eux, gardent les capacités de leur propre outil. `--reviewer-access` agit là-dessus, et sur B
seulement : `context-only` lui retire les outils de sa CLI — les deux adaptateurs savent le faire —
et `consult` les lui laisse. Ce que la CLI fait alors réellement de son réseau ne dépend plus
d'IAbinome : si cela compte pour vous, la réponse est du côté de l'outil.

*`context-only` n'a pas encore été exercé en mission réelle — seulement en tests.*

## Pourquoi c'est si petit

Le prédécesseur pesait 87 000 lignes pour un projet de 59 000, et sa partie « exécution autonome »
n'a jamais mené une implémentation au bout. Ce qui marchait, c'était la boucle A/B. IAbinome est
le retour à cette boucle, sans le reste. Le détail est dans `POURQUOI.md`, et les cinq règles qui
en découlent y sont opérationnelles, pas décoratives.

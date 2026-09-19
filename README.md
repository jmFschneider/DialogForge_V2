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
demande.md → A produit → B critique → A révise → (N fois max) → A finalise → livrable
```

`--max-revisions` fixe le N. À `0`, B critique une fois et A finalise sans réviser.

B reprend **exactement une fois** chaque constat resté ouvert dans sa revue précédente. Un constat
qui disparaît ou qui se dédouble fait échouer le contrat : c'est ce qui empêche une critique
gênante de s'évaporer d'un tour à l'autre.

## Quand ça s'arrête

`status` dit toujours où vous en êtes. Chaque statut a une sortie, et une seule :

| Statut | Ce que ça veut dire | Ce que vous faites |
|---|---|---|
| `AWAITING_APPROVAL` | le cycle est allé à son terme | lire `livrables/version_finale.md` |
| `WAITING_HUMAN` | A a posé une question, ou une revue est incohérente | `resume --answer <fichier>` |
| `INTERRUPTED` | l'appel n'a pas abouti — délai, quota, arrêt brutal | `resume --retry-call <uuid> --reason-file <fichier>` |
| `ERROR` | la réponse est arrivée mais ne respecte pas le contrat | idem, si l'incident est relançable |

Le message de refus **nomme toujours la commande** qui sort du statut : vous n'avez pas à
retrouver ça ici.

Codes de sortie : `0` terminé · `1` refus avant toute modification · `2` erreur d'usage
(`argparse`) · `3` interrompu · `4` erreur · `5` en attente de vous.

**Ce qu'un arrêt brutal garantit, et ce qu'il ne garantit pas.** Les artefacts d'un appel sont
écrits avant toute transition d'état, et rien n'est jamais rejoué tout seul — donc vous ne payez
pas deux fois par accident, et la réponse brute d'un appel refusé reste sur le disque. En revanche
un `INTERRUPTED` **ne repart pas seul** : il attend une relance que vous motivez par écrit. C'est
volontaire.

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
└── livrables/version_finale.md   le document
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

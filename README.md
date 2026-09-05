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

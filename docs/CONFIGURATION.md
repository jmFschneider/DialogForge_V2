# Configuration

Sept drapeaux à chaque `new`, c'est six de trop. Un fichier **`dialogforge.toml`** en fournit les valeurs
par défaut. Un modèle commenté est fourni : [`dialogforge.toml.exemple`](../dialogforge.toml.exemple).

```toml
agent_a = "codex"
agent_b = "claude"
max_revisions = 1
kind = "recherche"
web_access = true
reviewer_access = "consult"
```

```
dialogforge new ./ma-collab --demande ./demande.md
```

## Où il est cherché

Dans l'ordre : `--config <chemin>`, puis `./dialogforge.toml`, puis `~/.dialogforge/reglages.toml`. **Le premier
trouvé gagne ; les autres sont ignorés, jamais fusionnés** — fusionner rendrait indevinable l'origine
d'une valeur. `--config` exige que le fichier existe. La commande annonce sur la sortie d'erreur quel
fichier a servi et ce qu'elle y a pris :

```
configuration : dialogforge.toml (agent_a, agent_b, max_revisions)
```

Le nom du fichier porte celui du produit, et ce n'est pas une coquetterie : il est cherché **là où
vous lancez la commande**, et une clé inconnue y est un refus — un fichier homonyme appartenant à un
autre outil ferait donc échouer vos commandes au lieu d'être ignoré. Dans votre dossier personnel,
c'est le dossier `~/.dialogforge/` qui porte le nom, et le fichier sa fonction.

**Anciens noms.** `iabinome.toml` et `~/.iabinome.toml` sont **encore lus**, en dernier recours,
avec un message qui dit par quoi les remplacer. Rien ne cesse d'agir en silence ; renommez-les quand
vous voulez.

**Précédence :** drapeau de la ligne de commande > fichier > défaut du programme > défaut de
l'adaptateur (pour les modèles seulement).

## Les clés

Toutes sont facultatives. Une clé inconnue, un mauvais type ou un fichier illisible sont **refusés**
(code `1`), jamais ignorés : un réglage silencieusement perdu est pire qu'un réglage absent.

| Clé | Type | Défaut | Lue par | Sens |
|---|---|---|---|---|
| `agent_a` | texte | — | `new` | L'outil qui produit : `claude` ou `codex`. |
| `agent_b` | texte | — | `new` | L'outil qui critique. |
| `model_a` | texte | celui de l'adaptateur | `new` | Modèle de A. |
| `model_b` | texte | celui de l'adaptateur | `new` | Modèle de B. |
| `effort_a` | texte | aucun | `new` | Effort de raisonnement de A ([voir plus bas](#effort-de-raisonnement)). |
| `effort_b` | texte | aucun | `new` | Effort de raisonnement de B. |
| `agent_cadrage` | texte | — | `new --cadrer-avec-agent` | L'outil de l'agent de cadrage ([voir `new`](COMMANDES.md#cadrage-avec-agent)). |
| `model_cadrage` | texte | celui de l'adaptateur | `new --cadrer-avec-agent` | Modèle de l'agent de cadrage. |
| `effort_cadrage` | texte | aucun | `new --cadrer-avec-agent` | Effort de l'agent de cadrage. |
| `web_access` | booléen | `false` | `new` | Recherche web pour A et B ([voir plus bas](#accès-web)). |
| `kind` | texte | — | `new` | `recherche` (au moins une source : web ou corpus) ou `conception` (corpus facultatif). |
| `reviewer_access` | texte | — | `new` | `consult` ou `context-only`. |
| `max_revisions` | entier | `2` | `new` | Nombre maximal de révisions ; `0` : B critique une fois, sans révision. |
| `timeout` | nombre | `1800` | `run`, `resume`, `decide`, `new --cadrer-avec-agent` | Délai dur par appel, en secondes. |

`agent_a`, `agent_b`, `kind` et `reviewer_access` doivent venir de la ligne de commande **ou** du
fichier : `new` refuse s'il en manque une.

**Modèles par défaut.** Sans `model_a` / `model_b`, chaque adaptateur applique le sien. Pour Claude :
`opus` en A, `fable` en B ; pour Codex : `gpt-5.6-sol`. Les noms valides sont ceux que votre outil
accepte.

## Trois choses que le fichier ne fait pas

Ce n'est pas une lacune, c'est délibéré.

- **Aucun chemin ne s'y règle** — ni corpus, ni demande. Un chemin dans un fichier global rendrait la
  collaboration non reproductible d'une machine à l'autre.
- **Il ne touche jamais une collaboration existante.** Une fois `new` passé, `configuration.json` est
  la seule vérité : éditer `dialogforge.toml` ne déplace rien de ce qui tourne. Seul `timeout` est relu, à
  chaque `run`, `resume` et `decide --correct`.
- **Il n'y a qu'un seul fichier.** Pas de fusion entre celui du dossier et celui de votre profil.

## Effort de raisonnement

`effort_a` / `effort_b` (ou `--effort-a` / `--effort-b`) sont **facultatifs**. Absents, rien n'est
demandé à l'outil et `configuration.json` ne porte pas la clé. Posés, ils sont figés à `new` et
transmis à chaque appel du rôle.

**Chaque outil a son vocabulaire :**

| Outil | Valeurs acceptées |
|---|---|
| Claude | `low`, `medium`, `high`, `xhigh`, `max` |
| Codex | `minimal`, `low`, `medium`, `high`, `xhigh` |

Une valeur que l'outil du rôle ne connaît pas est refusée **avant tout appel** — à `new`, et au
prévol de `run` — sans rien modifier ni consommer de quota.

À savoir : sous les options d'isolation que l'outil applique à Codex, celui-ci a tourné à l'effort
`none` et non au `medium` de votre `config.toml` (constaté le 2026-09-19). Le PO a décidé de ne rien
changer par défaut ; si vous voulez un effort précis, posez-le : `medium` a bien été appliqué à Codex
lors de l'essai du 2026-09-20 (visible dans la bannière de son `stderr.txt`).

## Accès web

Fermé par défaut. `web_access = true` dans le fichier, ou `--web-access` / `--no-web-access` à `new`.
**Un seul réglage, figé à `new`, identique pour A et B.**

| | Claude | Codex |
|---|---|---|
| Fermé (défaut) | Outils `Read`, `Grep`, `Glob` seulement | `web_search=disabled`, demandé explicitement |
| Ouvert | + `WebSearch` et `WebFetch`, autorisés d'avance | `web_search=live` |
| Profil `context-only` | Aucun outil | Web coupé quoi qu'il arrive |

**Ce n'est pas un confinement réseau.** Ouvert, ce que contient le prompt peut sortir de la machine par
une requête de recherche ou de lecture. Fermé, l'outil demande la coupure à chaque CLI, et la coupure a été
observée sur un appel réel de chaque outil le 2026-09-20 (un essai chacun) — voir [`LIMITES.md`](LIMITES.md). Une collaboration créée
avant ce réglage se comporte comme `web_access = false`.

## Quel compte est utilisé

L'outil lance `claude.exe` et `codex` **directement**, pas une fonction de votre profil de terminal.
Il ne connaît donc pas vos alias : le compte Claude est celui de la variable `CLAUDE_CONFIG_DIR` dans
le terminal où vous tapez `run` (défaut : `~/.claude`), et celui de Codex dépend de `CODEX_HOME`.

Chaque outil ne reçoit que **ses propres** variables d'environnement : Claude garde son
authentification, sa configuration et son lanceur, et ne reçoit rien de Codex ; Codex l'inverse.
`PLAN_ID`, `PWF_*` et les identifiants de session de l'outil qui vous a lancé sont retirés aux deux.
`intention.json`, dans chaque dossier d'appel, nomme les variables retirées — jamais leurs valeurs.
Ce partage suit des préfixes de noms, pas une connaissance de vos secrets : une clé d'un autre nom
(un jeton générique) passe aux deux. Détail : [`LIMITES.md`](LIMITES.md).

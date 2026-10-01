# Prise en main

Un premier cycle, de la demande à la décision. Durée de lecture : dix minutes.

## Ce qu'il faut avoir

- **Python 3.12.** Aucune autre dépendance.
- **Les deux outils d'agents sur le `PATH`**, déjà connectés à leur compte : Claude Code (`claude`)
  et Codex (`codex`). L'outil ne s'authentifie pour personne ; il lance ces deux programmes et lit
  ce qu'ils répondent.
- Un terminal. Les commandes ci-dessous tiennent sur une ligne, donc valent en PowerShell comme
  en shell POSIX.

```
pip install -e .
dialogforge --help
```

`--help` liste les commandes ; `dialogforge <commande> --help` détaille chacune.

## 1. Écrire la demande

La demande est un fichier texte. Elle dit **ce que vous voulez** et, surtout, **à quoi vous
reconnaîtrez que c'est fini** : c'est ce second point qui rend la critique de B utile plutôt que polie.

Six sections en titres `##`, dans l'ordre que vous voulez :
*Objectif*, *Livrable*, *Sources*, *Contraintes*, *Non-objectifs*, *Critères de fin*.
C'est un repère, pas une porte : une demande libre est acceptée, `new` signale les sections
absentes, et A pose une question si le manque change le résultat.

Deux exemples complets, qui s'enchaînent : [`exemples/demande-recherche.md`](../exemples/demande-recherche.md)
puis [`exemples/demande-conception.md`](../exemples/demande-conception.md).

**Pas de fichier prêt ?** `--cadrer` remplace `--demande` par un questionnaire de terminal, une
réponse par section, fermée par une ligne vide. Il n'appelle aucun modèle et n'écrit rien si vous
l'interrompez.

## 2. Créer la collaboration

```
dialogforge new ./essai --demande ./exemples/demande-recherche.md --kind recherche --reviewer-access consult --agent-a codex --agent-b claude --source-root ./exemples --source-list ./exemples/corpus.txt --max-revisions 1
```

`new` ne consomme aucun quota : il crée le dossier `./essai`, qui ne doit pas exister, et fige les
réglages dans `configuration.json`.

DialogForge suit une chaîne **recherche → conception → développement**. Une **recherche** établit un
dossier sourcé à partir d'une idée ou d'une question : elle exige au moins une source, l'accès web
(`--web-access`) ou un corpus. Une **conception** tire de ce dossier le plan et les solutions qui
mènent à la réalisation, juste avant le code : elle exige un corpus, son dossier d'entrée. Le
[développement assisté](COMMANDES.md#dev-export) part ensuite d'une conception acceptée.

| Réglage | Ce qu'il décide |
|---|---|
| `--kind` | `recherche` ou `conception`, comme ci-dessus. |
| `--agent-a`, `--agent-b` | Qui produit, qui critique : `claude` ou `codex`, dans l'ordre que vous voulez. |
| `--reviewer-access` | `consult` laisse à B les outils de sa CLI ; `context-only` les lui retire. |
| `--max-revisions` | Le nombre maximal de révisions. À `0`, B critique une fois et la proposition est livrée telle quelle. |

Sept réglages à chaque `new`, c'est trop : un fichier [`dialogforge.toml`](CONFIGURATION.md) en fournit
les valeurs par défaut, et `new` se réduit alors à un dossier et une demande.

> **Chemin de `<dossier>`.** Toutes les commandes qui suivent (`run`, `show`, `decide`, `resume`,
> `status`, `plan`) reprennent le chemin tel que vous l'avez tapé, relatif au dossier où vous lancez
> la commande. Si la collaboration vit hors du dépôt — un essai dans votre propre dossier, par
> exemple — donnez-lui toujours un **chemin absolu** : un chemin relatif tapé depuis un autre
> dossier ne désigne pas la même collaboration, et l'erreur qui en résulte (`verrou.json`
> introuvable, par exemple) ressemble à un incident du moteur alors que c'est seulement le mauvais
> dossier.

**Le corpus** se déclare par un fichier qui liste des chemins, un par ligne, relatifs à
`--source-root`. La conception de l'exemple part du même dossier :

```
dialogforge new ./plan --demande ./exemples/demande-conception.md --kind conception --reviewer-access consult --agent-a claude --agent-b codex --source-root ./exemples --source-list ./exemples/corpus.txt --max-revisions 1
```

Une fois une recherche **acceptée**, `--depuis <recherche>` en fait directement le dossier d'entrée
d'une conception : son livrable, son bilan et sa décision deviennent le corpus. Dans la GUI, c'est le
bouton « Poursuivre en conception » de l'écran de suivi.

```
dialogforge new ./plan --demande ./demande-conception.md --kind conception --depuis ./essai --reviewer-access consult --agent-a claude --agent-b codex --max-revisions 1
```

Les fichiers sont **copiés octet pour octet** et hachés dans `corpus/manifeste.json`. Le corpus,
c'est exactement ce que le manifeste énumère : ajouter un fichier au dossier après coup ne l'y fait
pas entrer, et en retirer un fait échouer la vérification.

> **Sous Windows, Codex nécessite le backend natif `elevated` déjà installé et utilisable.**
> L'adaptateur le sélectionne explicitement ; lecture et refus d'écriture qualifiés le 2026-09-21.
> Cela ne garantit pas l'inaccessibilité en lecture du reste du disque. Détail dans
> [`LIMITES.md`](LIMITES.md#2-demandé-aux-outils--ce-que-lessai-réel-a-montré).

## 3. Lancer le cycle

```
dialogforge run ./essai
```

`run` est la seule commande qui appelle les agents, et **chaque appel consomme le quota de votre
compte**. Le cycle est :

```
demande → A produit → B critique → A révise → B relit → … (N révisions au plus) → livrable
```

Avec `--max-revisions N`, il y a au plus **2 + 2×N appels** : deux pour la proposition et sa critique,
puis deux par révision. B peut accepter avant le plafond, il y en a alors moins. Un tour de plus
décidé par vous, une relance ou une correction ciblée s'ajoutent. Ordre de grandeur mesuré : **un
appel dure de 1 à 7 minutes**, et un cycle complet de quatre appels a pris environ **6 minutes** lors
des missions réelles du 2026-09-22. Les appels les plus longs relevés (5 et 7 minutes) datent des
premiers essais du 2026-09-19 — voir [`LIMITES.md`](LIMITES.md). Ce n'est pas une garantie : le délai
dur par défaut reste de 30 minutes.

Le terminal reste occupé pendant les appels ; fermer la fenêtre ne laisse rien tourner en fond. Vous
pouvez vous arrêter proprement :

- **Ctrl+C une fois** : pause à la frontière d'appel. L'appel en cours se termine, rien n'est perdu ;
  `run` reprend au même endroit (code de sortie `6`).
- **Ctrl+C deux fois** : arrêt immédiat. L'appel en cours est interrompu et **a pu être payé** ;
  le statut devient `INTERRUPTED`, et rien n'est jamais rejoué tout seul.

À la fin, `run` affiche le statut et la **prochaine action**. Il n'y a pas d'autre état caché :
`dialogforge status ./essai` redonne le même point à tout moment, sans rien modifier.

## 4. Lire, puis décider

**« Terminé » n'est pas « accepté ».** Le cycle s'arrête en `AWAITING_APPROVAL` sans rien approuver.

```
dialogforge show ./essai
```

`show` affiche la décision courante, les corrections principales, les réserves, la prochaine action,
puis le document (`--no-document` pour le résumé seul). Exemple, tel que le produit le scénario de
référence avec de faux agents :

```
Collaboration : collaboration — statut AWAITING_APPROVAL, phase CLOSED
Décision : aucune : le cycle est terminé, il n'est pas accepté

Corrections principales :
  - B-001 [MAJOR] Les limites de l'invalidation ne sont pas énoncées. — A : Section « Limites » ajoutée. — B : La section « Limites » énonce l'invalidation par événement absente.

Réserves :
  aucune

Prochaine action : lire `livrables/bilan.md` puis décider : `decide <dossier> --accept`, `--accept-with-reserves <texte>`, `--correct <fichier>` ou `--stop`
```

Le livrable est `livrables/version_finale.md` : **exactement le document que B a examiné**, jamais une
réécriture faite après sa dernière revue. `livrables/bilan.md`, écrit par le programme sans modèle,
dit ce qui est livré, ce qui l'a examiné et les **désaccords restants**. Au plafond de révisions, ils
sont présentés, pas traités : c'est à vous de trancher.

Vous décidez avec `decide`, une décision par commande :

| Commande | Effet |
|---|---|
| `decide ./essai --accept` | Consigne l'acceptation de **cette version**. |
| `decide ./essai --accept-with-reserves "…"` | Idem, avec vos réserves (le texte est exigé). |
| `decide ./essai --correct ./precisions.md` | Correction ciblée : le fichier complète la demande, A révise, B relit — un tour de plus, au-delà du plafond. |
| `decide ./essai --stop --reason "…"` | Arrête, définitivement. |

Chaque décision est **datée** dans `decisions.json` et porte sur une version précise du livrable. Si le
livrable change ensuite, `status` le dit : la décision porte sur une version antérieure.

## 5. Si le cycle s'arrête

`status` donne toujours la prochaine action, et le message de refus d'une commande nomme celle qui
sort du statut. La table complète des statuts est dans [`COMMANDES.md`](COMMANDES.md#statuts). Les trois
cas courants :

- **`WAITING_HUMAN`** — A a posé une question (ou une revue est incohérente). Lisez-la, écrivez votre
  réponse dans un fichier, puis `resume ./essai --answer ./reponse.md`. La réponse **complète** la
  demande sous « Précisions n°1 », « n°2 »… : le texte existant reste intact, une réponse courte suffit.
- **`INTERRUPTED`** — l'appel n'a pas abouti (délai, quota, arrêt brutal). Le message de l'outil est cité
  tel quel ; **le programme ne devine ni le coût ni l'heure de reprise**. Pour relancer, vous motivez
  par écrit : `resume ./essai --retry-call <uuid> --reason-file ./motif.md`.
- **`ERROR`** — la réponse est arrivée, donc payée, mais elle ne respecte pas le contrat. Elle est
  conservée : `resume ./essai --reprocess <uuid> --reason-file ./motif.md` la **relit en local, sans
  nouvel appel**.

## 6. Ce qu'il y a sur le disque

```
essai/
├── demande.md                    votre demande, normalisée
├── provenance_demande.json       d'où elle vient : fichier ou cadrage, et son empreinte
├── configuration.json            figé au `new` : outils, modèles, révisions
├── etat.json                     où en est le cycle, lisible à l'œil
├── corpus/                       manifeste et copies des sources (si corpus)
├── echanges/                     propositions de A, revues de B, réponses de A aux objections
├── appels/NNNN-<rôle>-<uuid>/    la preuve : prompt exact, flux bruts, résultat, incident
├── decisions.json                vos décisions, datées
├── plan.json                     seulement si vous avez lié un plan PWF (`plan --link`)
├── livrables/version_finale.md   le document
└── livrables/bilan.md            ce qui est livré, examiné, resté en désaccord
```

`echanges/` est ce qu'on lit pour suivre le raisonnement ; `appels/` est ce qu'on ouvre pour vérifier
un doute. Rien n'y est résumé. Tout est en fichiers : il n'y a ni base, ni service, ni tâche planifiée.

## 7. Essayer sans rien payer

Depuis un clone du dépôt, le scénario de référence joue un cycle complet — création, `run`, `show`,
`decide`, `list` — avec de **faux agents** : aucune CLI réelle n'est appelée.

```
python reference/cycle_sans_fournisseur.py
```

Il affiche le dossier conservé, où vous pouvez lire les fichiers ci-dessus. C'est le moyen de voir à
quoi ressemble une collaboration terminée avant d'en lancer une réelle.

---

Suite : [`COMMANDES.md`](COMMANDES.md) (toutes les commandes, statuts et codes de sortie) ·
[`CONFIGURATION.md`](CONFIGURATION.md) (le fichier de réglages) · [`LIMITES.md`](LIMITES.md) (ce qui
est garanti, et ce qui ne l'est pas).

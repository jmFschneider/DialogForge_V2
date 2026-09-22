# DialogForge

Deux agents IA en ligne de commande : **A produit, B critique, vous arbitrez.**
Le livrable est un document de conception ou de recherche — jamais une exécution.

Tout tient dans un dossier sur disque. Vous lancez, ça tourne, vous fermez le terminal.

```
demande.md → A produit → B critique → A révise → B relit → (N fois au plus) → livrable → vous décidez
```

A et B sont chacun Claude ou Codex, choisis au lancement. Le livrable est **exactement la version que
B a examinée** ; « terminé » n'est jamais « accepté » : l'acceptation est votre décision, datée, sur une
version précise.

> **Le nom de la commande.** Le package et la commande s'appellent encore `iabinome` : le renommage en
> DialogForge est prévu à la fin du développement V2. Partout, la commande est `python -m iabinome`.

## Installer

Python 3.12, **aucune dépendance**. Les deux outils d'agents (`claude`, `codex`) doivent être sur le
`PATH` et déjà connectés à leur compte.

```
pip install -e .
python -m iabinome --help
```

## En quatre commandes

```
python -m iabinome new ./ma-collab --demande ./demande.md --kind conception --reviewer-access consult --agent-a codex --agent-b claude
python -m iabinome run ./ma-collab
python -m iabinome show ./ma-collab
python -m iabinome decide ./ma-collab --accept
```

`demande.md` est votre texte : ce que vous voulez, et **à quoi vous reconnaîtrez que c'est fini**.
Un exemple prêt à l'emploi : [`exemples/demande-conception.md`](exemples/demande-conception.md).

`run` est la seule commande qui appelle les agents, et **chaque appel consomme le quota de votre
compte**. `status` dit à tout moment où vous en êtes et quelle est la prochaine action ; à chaque arrêt,
le message nomme la commande qui en sort.

## La documentation

| Vous voulez… | Lisez |
|---|---|
| Faire un premier cycle, pas à pas | [`docs/PRISE_EN_MAIN.md`](docs/PRISE_EN_MAIN.md) |
| Connaître chaque commande, statut et code de sortie | [`docs/COMMANDES.md`](docs/COMMANDES.md) |
| Régler les valeurs par défaut, l'effort, l'accès web | [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) |
| Savoir ce qui est garanti, et ce qui ne l'est pas | [`docs/LIMITES.md`](docs/LIMITES.md) |
| Essayer sans rien payer | `python reference/cycle_sans_fournisseur.py` (faux agents) |
| Travailler sur l'outil lui-même | [`docs/DEVELOPPEMENT.md`](docs/DEVELOPPEMENT.md) |

`python -m iabinome <commande> --help` donne l'aide de chaque commande.

## Ce que l'outil ne fait pas

Ce n'est pas une liste de limitations : c'est le périmètre, tenu volontairement.

- **Il n'exécute rien.** Le livrable est un document, que vous appliquez ensuite à la main.
- **Aucune base de données**, aucun service, aucune tâche planifiée. Des fichiers, et c'est tout.
- **Aucun budget ni quota interne.** Les plafonds de votre fournisseur suffisent.
- **Pas d'interface graphique.**

**Il ne prétend pas savoir ce qu'il ignore.** Le web fermé, l'effort et la séparation des secrets ont
été mesurés sur de vrais appels le 2026-09-20 ; l'effet de plusieurs autres protections ne l'est pas ; et
**la lecture Codex et le refus d'écriture ont été qualifiés le 2026-09-21 avec le backend Windows `elevated` déjà installé**, sans garantie de confinement en lecture. Un incident dit s'il a pu
être payé, jamais combien. Voir [`docs/LIMITES.md`](docs/LIMITES.md).

## Pourquoi c'est si petit

Le prédécesseur pesait 87 000 lignes pour un projet de 59 000, et sa partie « exécution autonome »
n'a jamais mené une implémentation au bout. Ce qui marchait, c'était la boucle A/B : cet outil est le
retour à cette boucle, sans le reste. L'histoire complète et les cinq règles qui en découlent :
[`POURQUOI.md`](POURQUOI.md).

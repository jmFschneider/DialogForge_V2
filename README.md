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

## Installer

Python 3.12, **aucune dépendance**. Les deux outils d'agents (`claude`, `codex`) doivent être sur le
`PATH` et déjà connectés à leur compte.

```
pip install -e .
dialogforge --help
```

## En quatre commandes

```
dialogforge new ./ma-collab --demande ./demande.md --kind conception --reviewer-access consult --agent-a codex --agent-b claude
dialogforge run ./ma-collab
dialogforge show ./ma-collab
dialogforge decide ./ma-collab --accept
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

`dialogforge <commande> --help` donne l'aide de chaque commande.

## Ce que l'outil ne fait pas

Ce n'est pas une liste de limitations : c'est le périmètre, tenu volontairement.

- **Il n'exécute rien.** Le livrable est un document, que vous appliquez ensuite à la main.
- **Aucune base de données**, aucun service, aucune tâche planifiée. Des fichiers, et c'est tout.
- **Aucun budget ni quota interne.** Les plafonds de votre fournisseur suffisent.
- **Une fenêtre locale, rien de plus.** `dialogforge gui` ouvre une fenêtre Tkinter sur les mêmes
  dossiers que la CLI : une collaboration et une exécution à la fois, sans service, worker ni
  processus détaché.

**Il ne prétend pas savoir ce qu'il ignore.** Certaines protections ont été mesurées sur de vrais
appels, d'autres sont seulement demandées à la CLI de chaque outil : rien n'est promis sans preuve, et
il n'y a **aucune garantie de confinement en lecture du disque**. Un incident dit s'il a pu être payé,
jamais combien. Le détail, niveau de preuve par niveau de preuve : [`docs/LIMITES.md`](docs/LIMITES.md).

## Pourquoi c'est si petit

Le prédécesseur pesait 87 000 lignes pour un projet de 59 000, et sa partie « exécution autonome »
n'a jamais mené une implémentation au bout. Ce qui marchait, c'était la boucle A/B : cet outil est le
retour à cette boucle, sans le reste. L'histoire complète et les cinq règles qui en découlent :
[`POURQUOI.md`](POURQUOI.md).

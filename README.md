# DialogForge

DialogForge organise une collaboration entre deux agents IA en ligne de commande : **A produit, B
critique, vous arbitrez**. Il sert à préparer ou examiner un document de conception ou de recherche ;
il ne modifie jamais le projet auquel ce document se rapporte.

```
demande → A produit → B critique → A révise → B relit → livrable → vous décidez
```

Vous choisissez Claude ou Codex pour chacun des rôles. Le cycle comporte un nombre borné de
révisions et peut s'arrêter plus tôt lorsque B accepte la version examinée. Le livrable est toujours
la version que B a effectivement examinée. « Terminé » ne vaut pas acceptation : votre décision est
datée et rattachée à cette version précise.

Tout est rangé dans un dossier de collaboration : demande, réglages figés, échanges, traces d'appel,
livrable et décisions. Il n'y a ni base de données, ni service, ni processus détaché.

## Démarrer

Il faut Python 3.12 et la CLI de chaque fournisseur que vous utiliserez (`claude` et/ou `codex`),
déjà installée, connectée et accessible sur le `PATH`.

```powershell
pip install -e .
dialogforge --help
```

Créez une collaboration à partir d'une demande, lancez le cycle, lisez le résultat, puis prenez votre
décision :

```powershell
dialogforge new ./ma-collab --demande ./demande.md --kind recherche --web-access --reviewer-access consult --agent-a codex --agent-b claude --max-revisions 1
dialogforge run ./ma-collab
dialogforge show ./ma-collab
dialogforge decide ./ma-collab --accept
```

Une demande exprime le résultat attendu et les critères qui permettront de le reconnaître. Utilisez
[`exemples/demande-conception.md`](exemples/demande-conception.md) pour commencer, ou créez-la dans
le terminal avec `new --cadrer`. `new --cadrer-avec-agent` mène un cadrage conversationnel avant de
créer le dossier ; ces appels sont comptabilisés par le fournisseur.

`run` appelle les agents. Selon l'action choisie, `resume`, `decide --correct` et le cadrage avec
agent peuvent aussi le faire. Ces appels consomment le quota de votre compte. `status` affiche à tout
moment l'état et la prochaine action ; chaque arrêt indique la commande à utiliser pour reprendre.

## Ce que permet DialogForge

| Besoin | Fonction |
|---|---|
| Enchaîner recherche → conception → développement | Une recherche établit un dossier sourcé (web ou corpus) ; une conception en tire le plan, juste avant le code. |
| Formuler la demande | Demande libre, questionnaire local ou cadrage avec un agent, puis cycle A/B. |
| Travailler sur des sources locales | Un corpus déclaré est copié, haché et vérifié ; il est exigé en conception. |
| Régler les rôles | Claude et Codex peuvent tenir A ou B ; modèles et effort sont réglables par rôle. |
| Limiter les capacités du relecteur | `consult` conserve les outils de sa CLI ; `context-only` les lui retire. |
| Choisir l'accès web | Fermé par défaut et figé lors de la création ; il peut être ouvert pour A et B. |
| Reprendre après un incident | Répondre à une question, retraiter une réponse locale ou relancer explicitement un appel. |
| Utiliser une interface locale | `dialogforge gui` ouvre la même collaboration dans une fenêtre Tkinter. |
| Revoir du code à partir d'une conception | `dev-export`, `dev-package` et `dev-verify` relient une conception acceptée, un diff Git figé et sa revue. |

Pour les réglages réutilisés à chaque création, copiez
[`dialogforge.toml.exemple`](dialogforge.toml.exemple) en `dialogforge.toml`. Les valeurs de ce
fichier servent de défauts à `new` ; la configuration de chaque collaboration est ensuite figée dans
son propre dossier.

## Revue de développement

Après l'acceptation d'une conception, `dev-export` produit le mandat de développement. Une fois le
code réalisé, `dev-package` capture le diff entre deux commits Git, les fichiers concernés et les
résultats de validation que vous fournissez. Créez ensuite une collaboration de recherche à partir de
ce paquet pour faire rédiger et critiquer le rapport de revue. Avant de décider sur ce rapport,
`dev-verify` contrôle que le paquet et la collaboration sont bien rattachés aux mêmes commits et
sources.

DialogForge lit Git et les validations déclarées ; il n'exécute ni le code ni les tests du projet
examiné. Le déroulé complet et les commandes sont dans
[`docs/COMMANDES.md`](docs/COMMANDES.md#dev-export).

## Documentation

| Vous voulez… | Lisez |
|---|---|
| Faire un premier cycle, pas à pas | [`docs/PRISE_EN_MAIN.md`](docs/PRISE_EN_MAIN.md) |
| Connaître les commandes, états et codes de sortie | [`docs/COMMANDES.md`](docs/COMMANDES.md) |
| Régler les agents, modèles, effort ou accès web | [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) |
| Comprendre les garanties et leurs limites | [`docs/LIMITES.md`](docs/LIMITES.md) |
| Essayer le cycle sans appeler de fournisseur | `python reference/cycle_sans_fournisseur.py` |
| Contribuer au projet | [`docs/DEVELOPPEMENT.md`](docs/DEVELOPPEMENT.md) |

`dialogforge <commande> --help` donne l'aide de chaque commande directement dans le terminal.

## Limites et sécurité

Le programme sépare les rôles, conserve les traces d'appel, promeut octet pour octet la version
examinée et ne relance jamais un appel ambigu sans intervention explicite. Il distingue ce qu'il
garantit lui-même de ce qui est seulement demandé aux CLIs des fournisseurs.

Les demandes et corpus sont transmis aux fournisseurs choisis. L'accès web est fermé par défaut,
mais ce réglage ne remplace pas un confinement réseau. Aucune garantie de confinement général en
lecture du disque n'est donnée pour Codex. Un incident indique seulement si l'appel a pu être payé,
jamais son coût. Les résultats d'essais et les limites exactes sont documentés dans
[`docs/LIMITES.md`](docs/LIMITES.md).

## Licence

Distribué sous licence [MIT](LICENSE).

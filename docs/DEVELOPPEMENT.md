# Développement

Pour qui travaille **sur** l'outil, pas avec. Les utilisateurs n'ont pas besoin de cette page.

## D'où vient le code

DialogForge V2 est développé dans ce dépôt (`DialogForge_2`), à partir d'IAbinome : un outil d'environ
1 500 lignes qui coordonne deux agents en ligne de commande. Le prédécesseur, DialogForge, pesait
87 000 lignes et sa partie « exécution autonome » n'a jamais mené une implémentation au bout ;
l'histoire et les cinq règles qui en découlent sont dans [`POURQUOI.md`](../POURQUOI.md).

| Élément | Valeur |
|---|---|
| Source | `C:\Projets\IAbinome`, clone local complet avec historique Git |
| Commit de départ | `4a11cc7eae47a4920b845fda6e65937557a967cf` — *docs: cloturer le plan correctif et preparer la session CONTEXT_ONLY* |
| Branche de travail | `v2-socle` |
| Destination de push | Aucune. Le remote `origin` a été retiré après le clone : impossible d'écrire dans IAbinome par erreur |
| Non importés | Environnement virtuel, fichiers non suivis, configuration personnelle (`iabinome.toml`, ignoré par Git) |

Les dépôts sources — IAbinome et DialogForge — restent inchangés ; ce dépôt ne réécrit pas les missions
historiques.

## Périmètre de la première livraison (J3)

**Couvert :** conception et synthèse **sur corpus local fourni**, en terminal guidé — demande → production A →
critique B indépendante → correction avec une disposition explicite par objection → livrable et décisions
restantes → acceptation, correction ciblée ou arrêt, avec reprise après incident sans rejouer un appel
ambigu.

**Hors périmètre à ce stade :** recherche externe (profil distinct, à qualifier), développement assisté
(lot 4), interface graphique (extension conditionnelle après J3), service permanent ou reprise autonome
après fermeture du programme.

## Nom du package

Le produit s'appelle DialogForge, mais le package et la commande s'appellent encore `iabinome`. Le
renommage est **prévu à la fin du développement V2**, en une passe distincte : le faire au fil des lots
mélangerait changements fonctionnels et renommage. Quand il aura lieu, il touchera le package
(`src/iabinome`), la commande `python -m iabinome`, `iabinome.toml` et `.iabinome.toml`, `pyproject.toml`, et
la documentation (`README.md`, `docs/`, `exemples/`). **Aucun test ne surveille ce nom** — `tests/test_docs.py`
compare les commandes et options, pas le nom du programme : `grep -rn iabinome README.md docs exemples`
donne la liste des endroits à passer en revue.

## Où est quoi

| Chemin | Rôle |
|---|---|
| `src/iabinome/` | Le code : `cli.py` (surface), `workflow.py` (le cycle), `adapters/` (un fichier par fournisseur) |
| `tests/` | La suite. **Aucun appel fournisseur** : l'agent `fake` est obligatoire |
| `reference/` | Scénario sans fournisseur, protocole d'essai fournisseur, frontière des rôles |
| `conception/` | Spécification (`CONCEPTION_FINALE.md`) et pièces d'étude |
| `project/RULES.md` | Les règles apprises, avec leur motif — **à lire avant de toucher un domaine** |
| `.planning/2026-09-18-dialogforge-v2/` | Le plan de développement : seul suivi d'avancement |
| `docs/`, `exemples/` | La documentation utilisateur et ses exemples |

`CLAUDE.md` (racine) fixe la méthode de session, les cinq interdits et la stack.

## Vérifier avant un commit

```
.venv/Scripts/python.exe -m pytest tests
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m mypy
.venv/Scripts/python.exe reference/cycle_sans_fournisseur.py
```

`pytest tests`, jamais `pytest` nu (il ramasserait les tests du plugin PWF embarqué). Le scénario doit
rendre le code `0`.

## Tenir la documentation à jour

`tests/test_docs.py` échoue si une commande ou une option de la CLI n'est pas décrite dans
`docs/COMMANDES.md`, si une clé de `iabinome.toml` ne l'est pas dans `docs/CONFIGURATION.md`, si une
option n'a pas de texte d'aide, si un exemple n'est plus accepté par `new`, ou si un lien relatif est
cassé. Il ne vérifie pas que le texte est **vrai** : ajouter une option, c'est aussi relire la page qui
la décrit. `docs/LIMITES.md` se met à jour à chaque mesure réelle (lot 3).

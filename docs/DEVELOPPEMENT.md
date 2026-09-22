# Développement

Pour qui travaille **sur** l'outil, pas avec. Les utilisateurs n'ont pas besoin de cette page.

## D'où vient le code

DialogForge V2 est développé dans ce dépôt (`DialogForge_2`), à partir d'IAbinome : un outil qui
coordonne deux agents en ligne de commande. Le prédécesseur, DialogForge, pesait 87 000 lignes et sa
partie « exécution autonome » n'a jamais mené une implémentation au bout ; l'histoire et les cinq
règles qui en découlent sont dans [`POURQUOI.md`](../POURQUOI.md).

**Taille, relevée à J3 (2026-09-22)** : 3 253 lignes de code dans `src/` (4 891 avec commentaires et
docstrings), 7 555 en tests ; le commit de départ en comptait 2 968. La visée d'origine était de
~1 500 lignes : **le dépassement est assumé par le PO depuis le 2026-09-22.** Ce qui reste surveillé
est le rapport à la taille du projet servi (règle 1 de `POURQUOI.md`), pas ce chiffre absolu.

| Élément | Valeur |
|---|---|
| Source | `C:\Projets\IAbinome`, clone local complet avec historique Git |
| Commit de départ | `4a11cc7eae47a4920b845fda6e65937557a967cf` — *docs: cloturer le plan correctif et preparer la session CONTEXT_ONLY* |
| Branche de travail | `v2-socle` |
| Destination de push | Aucune. Le remote `origin` a été retiré après le clone : impossible d'écrire dans IAbinome par erreur |
| Non importés | Environnement virtuel, fichiers non suivis, fichier de réglages local (ignoré par Git) |

Les dépôts sources — IAbinome et DialogForge — restent inchangés ; ce dépôt ne réécrit pas les missions
historiques.

## Périmètre de la première livraison (J3)

**Couvert :** conception et synthèse **sur corpus local fourni**, en terminal guidé — demande → production A →
critique B indépendante → correction avec une disposition explicite par objection → livrable et décisions
restantes → acceptation, correction ciblée ou arrêt, avec reprise après incident sans rejouer un appel
ambigu.

**Hors périmètre à ce stade :** recherche externe **conduite par l'outil** — un profil distinct, à
qualifier ; les agents, eux, gardent la recherche web de leur propre CLI, fermée par défaut et réglée
par `web_access` (exercée en réel au lot 3.2). Également hors périmètre : développement assisté
(lot 4), interface graphique (extension conditionnelle après J3), service permanent ou reprise
autonome après fermeture du programme.

## Nom du package

**Ce que l'utilisateur voit s'appelle DialogForge ; le package importable garde le nom `iabinome`.**
C'est délibéré, et décidé par le PO le 2026-09-22 : la question n'était pas « renommer le code » mais
« ne pas exposer IAbinome ». La surface exposée — la commande `dialogforge`, l'aide, le nom de
distribution, le fichier de réglages, le dossier jetable, la documentation — porte donc le nom du
produit ; le reste est une affaire de développement, que personne d'autre ne lit.

En échange, un renommage du package n'a plus d'urgence : ~35 fichiers de `src/` et `tests/`, sans
aucun gain visible pour l'utilisateur. Il se fera si un jour le nom interne gêne à la lecture, pas
avant. `python -m iabinome` reste un point d'entrée fonctionnel, volontairement absent de la
documentation utilisateur.

Ce qui subsiste sous l'ancien nom, et qui se voit : les balises de contrat `IABINOME:DOCUMENT`,
`IABINOME:QUESTION` et `IABINOME:REPONSES`, présentes dans les prompts et dans `echanges/`. Les
renommer casserait la relecture des collaborations existantes (`resume --reprocess`) et les revues
réelles que `tests/test_objections.py` rejoue : ce serait un changement de contrat, avec une phase à
deux balises, pas un renommage. **À décider séparément.**

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
`docs/COMMANDES.md`, si une clé de `dialogforge.toml` ne l'est pas dans `docs/CONFIGURATION.md`, si une
option n'a pas de texte d'aide, si un exemple n'est plus accepté par `new`, ou si un lien relatif est
cassé. Il ne vérifie pas que le texte est **vrai** : ajouter une option, c'est aussi relire la page qui
la décrit. `docs/LIMITES.md` se met à jour à chaque mesure réelle (lot 3).

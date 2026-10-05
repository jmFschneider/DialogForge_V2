# Accès au projet pendant une recherche ou une conception

> Proposition du 2026-10-05. Cette conception prépare le travail sur les sources
> d'un projet avant la reprise automatique après quota. La mission `Reprise_Quota`
> déjà ouverte reste hors de ce chantier.

## Problème constaté

La liste `corpus_reprise_quota.txt` nomme des fichiers, mais ne les transmet pas.
La collaboration ouverte avait `corpus_manifest_sha256: null` : aucun fichier du
projet n'était disponible pour l'agent. Mettre cette liste dans `echanges/` ne
change pas ce fait : l'agent documentaire tourne dans un dossier temporaire qui
ne contient que les fichiers du corpus importé à la création. Une sélection
manuelle de fichiers pour chaque mission recrée régulièrement le même manque.

## Comportement visé

L'utilisateur choisit un **dossier de projet**. Pendant chaque appel de F, A et
B autorisé à consulter les sources, l'agent peut découvrir et lire les fichiers
qui existent alors dans ce dossier, sans liste préalable. Il peut suivre les
références d'un fichier à l'autre. Le projet n'est pas copié et DialogForge ne lui
accorde pas d'écriture. Le Runner garde son clone de travail séparé, nécessaire
à la mise en place du code.

Le mode « projet vivant » est distinct du corpus figé actuel. Une recherche ou
une conception peut utiliser les deux : les documents figés restent dans le
dossier neutre, le projet vivant est un second emplacement de lecture. B en
`CONTEXT_ONLY` conserve son profil sans outils ; seul B en `CONSULT` lit le projet.

## Contrat à mettre en place

1. La CLI accepte `--project-root <dossier>` à la création et la GUI propose
   « Dossier du projet à consulter ». Le dossier peut être un dépôt Git ou un
   projet ordinaire. Le formulaire affiche avant le premier appel que ses
   fichiers seront lus directement, et rappelle le projet choisi sur l'écran
   de suivi. Une liste de corpus reste possible pour des documents figés.
2. Le chemin est enregistré explicitement dans la configuration de la
   collaboration. Cela constitue une exception ciblée à la règle actuelle qui
   interdit les chemins absolus persistés. Au lancement, DialogForge vérifie
   que le dossier existe, qu'il est distinct de la collaboration et qu'aucun
   des deux n'englobe l'autre. Un dossier inaccessible arrête l'appel avant
   toute dépense. Le déplacement du projet demandera une action explicite de
   reliaison dans un lot ultérieur ; la première version signale le chemin
   absent et s'arrête.
3. A et B ne tournent jamais dans la collaboration. Claude reste dans son
   dossier neutre et reçoit le projet comme répertoire de lecture supplémentaire
   (`--add-dir` est présent dans l'aide locale de Claude 2.1.289). Lorsque le
   projet est la seule source locale, Codex démarre dans ce projet avec
   `--sandbox read-only` et `--cd`. Si un corpus figé s'ajoute, Codex reste dans
   le dossier neutre qui porte ce corpus et doit pouvoir lire le projet par son
   chemin absolu. Cette dernière combinaison requiert encore un essai réel :
   le prompt ne peut pas ouvrir un accès que l'outil refuserait.
4. Les prompts de F, A et B nomment le dossier du projet et indiquent qu'il est
   vivant. Ils continuent de nommer séparément `corpus/fichiers/` lorsqu'un
   corpus figé existe. Ils ne disent jamais qu'un projet vivant constitue
   l'instantané commun de A et B.
5. Chaque appel inscrit le chemin du projet utilisé. Le projet étant vivant,
   A et B peuvent voir des versions différentes ; leurs documents doivent
   nommer les fichiers effectivement consultés. La première version ne promet
   ni empreinte de l'arbre Git, ni détection des modifications pendant l'appel.
   Une traçabilité de version plus fine est une décision séparée.
6. Le cadrage avec agent doit voir le même dossier que la collaboration qu'il
   crée. La transition recherche vers conception conserve son corpus de
   recherche et transmet le choix du dossier vivant si celui-ci était activé.
   La GUI et la CLI utilisent les mêmes validations de la façade.

## Qualification préalable

Construire un projet témoin contenant deux fichiers dont le second n'est cité
que par le premier, puis vérifier avec chaque CLI que F, A et B en consultation
peuvent découvrir et lire les deux, et qu'une tentative d'écriture échoue. Tester
un dossier de collaboration voisin avec un marqueur : il ne doit pas être lu.
Ces essais impliquent des appels fournisseur ; les tests automatisés restent sur
faux agents et ne consomment aucun quota.

## Conditions de fin

- Création et cadrage sans liste de fichiers, sur un projet Git et un dossier
  ordinaire ; fichiers ajoutés après la création visibles à l'appel suivant.
- Même accès pour A et B en consultation ; B sans outils reste sans accès direct.
- Corpus figé et projet vivant utilisables ensemble, notamment après une
  recherche acceptée.
- Projet absent ou déplacé : arrêt avant appel avec le chemin à corriger.
- Aucune écriture de l'agent dans le projet ni lecture des échanges internes
  dans les essais réels de qualification.

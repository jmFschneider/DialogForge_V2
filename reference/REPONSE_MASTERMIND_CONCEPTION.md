# Réponse aux questions de A

## 1. Objectif de ce document
Option (a) : produire un **plan de réalisation** destiné au développement, à partir du livrable accepté de la recherche. Ce n'est ni une revue critique de ce livrable, ni une réouverture de l'architecture.

Le résultat final du projet reste « une application web Mastermind jouable ». Le livrable de cette étape est le plan qui permet de la développer puis de la vérifier, avant que le code soit écrit.

## 2. Base ferme
Le livrable accepté est la base ferme. Ne pas rouvrir les deux désaccords restants du bilan :
- `B-livrable-001` (aucune application jouable) : c'est attendu, cette étape ne produit pas de code. L'application sera produite par l'étape de développement, après acceptation du plan.
- `B-preuve-002` (dossier vide) : sans objet. Le projet est neuf, il n'y a aucun code existant à reprendre.

Le code du §5 de la recherche est une **proposition jamais exécutée**. Le plan la reprend comme point de départ. Sa première vérification consiste à la faire tourner et à corriger ce que les tests révèlent : une erreur d'exemple a déjà été trouvée à la relecture.

## 3. Hypothèses H1 à H5
Je les confirme comme **décisions du demandeur** (2026-10-03) :
- **H1** : doublons réglables, autorisés par défaut. Les indices gèrent toujours les doublons.
- **H2** : longueur 2 à 8 (défaut 4), couleurs 2 à 10 (défaut 6), essais 1 à 20 (défaut 10). Sans doublons, couleurs ≥ longueur.
- **H3** : jeu seul, avec « Rejouer » et retour aux réglages.
- **H4** : application statique, JavaScript natif (modules ES), sans build, tests avec `node --test`.
- **H5** : interface en français, affichage adaptatif, critères d'accessibilité vérifiables du §6.

## 4. Format attendu
Un plan d'étapes vérifiables. Pour chaque étape : les fichiers à créer, la commande de vérification, le résultat attendu.

Le plan doit être **autonome** : le développement ne reçoit pas la recherche. Il faut donc y inclure les règles métier, l'algorithme des indices, la génération du secret, les bornes, les exemples de calcul, ainsi que les extraits de code de référence utiles (logique et tests). Ne pas proposer de correctifs du code de la recherche dans le texte : ils se feront en développement, tests à l'appui.

## 5. Contraintes et précisions à ajouter
- Aucune dépendance de production, aucun outil de build.
- Navigateurs cibles : versions récentes des navigateurs courants. Mobile par adaptation de l'affichage seulement, pas d'application native.
- Aucun hébergement : usage local. Les modules ES ne se chargent pas depuis `file://`. Le mode de lancement est donc un serveur statique local, avec la commande exacte indiquée dans le plan (par exemple `python -m http.server`).
- Validation automatisée : `node --test`, lancé depuis la racine du dépôt, avec Node.js comme prérequis. Le développement tourne sans réseau et n'installe aucune dépendance. Playwright et axe-core ne peuvent donc pas faire partie des validations automatiques.
- Les scénarios navigateur et d'accessibilité du §6 de la recherche deviennent une **liste de contrôle manuelle** pour le demandeur, avec un résultat attendu par ligne.
- Le plan indique l'arborescence à créer à la racine du dépôt neuf.
- Les non-objectifs de la demande sont conservés.
- Si un arbitrage reste ouvert, le signaler dans le plan. Ne poser une question que si elle bloque réellement.

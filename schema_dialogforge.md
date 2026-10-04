# Schéma actuel de DialogForge — base de discussion

**État observé au 4 octobre 2026.** Ce document décrit le fonctionnement actuel à grands traits. Les principes souhaités sont indiqués séparément pour préparer la discussion avec Claude.

## Parcours actuel

```text
Idée
  ├─ Recherche (facultative) ── résultat accepté ──┐
  └─────────────────────────────────────────────────┤
                                                    ↓
Conception ── plan accepté ──→ Runner ── code et validations ──→ paquet
                                                               ↓
                                     nouvelle collaboration « Revue », prête à démarrer
                                                               ↓
                                     cycle documentaire A → B → décision humaine
                                                               ↓
                                              intégration explicite du code
```

- **Recherche** : produit une étude. Elle est facultative ; on peut commencer directement par une conception.
- **Conception** : produit un plan. Elle peut démarrer sans documentation initiale. Sa version acceptée autorise le lancement du Runner.
- **Développement avec le Runner** : l'agent code dans un clone isolé, exécute les validations et produit un paquet. Un paquet réussi arrête les appels de développement. Une correction du code nécessite un objectif précis et un nouvel appel.
- **Revue du paquet** : « Poursuivre : examiner le paquet » copie le paquet dans la mission et crée une *nouvelle collaboration* de revue. Celle-ci repart à l'état « Prête » et utilise le même cycle documentaire A/B que les étapes précédentes : A rédige une proposition de rapport, B l'examine, puis l'utilisateur décide. Après acceptation de la revue, une action distincte intègre le code dans le dépôt cible.

## Navigation et rupture ressentie

Une mission regroupe les dossiers de recherche, de conception, de développement et de revue. Son en-tête permet de passer d'une collaboration à l'autre ; l'étape déjà ouverte y apparaît grisée. Cette navigation ne représente pas une progression continue du travail.

La rupture se situe **après la production du paquet** : l'implémentation en cours est présentée comme une collaboration documentaire neuve, avec l'état « Prête » et l'action générique « Démarrer la collaboration ». Le système ne présente donc pas clairement « examiner le code produit, puis poursuivre l'implémentation ou l'intégrer ». Le démarrage de cette revue donne l'impression de recommencer une recherche ou une conception, même si la conception acceptée et le paquet restent conservés.

### Sur quoi porte la revue aujourd'hui ?

Le code produit existe dans le clone isolé du Runner et dans la **copie figée du paquet** (`developpement/paquets/001/revision/files/` pour Mastermind). La revue reçoit aussi cette copie dans son corpus, avec le diff, la conception exportée et les résultats des validations. Pour Mastermind, la base Git étant vide, les fichiers du jeu y figurent ; pour un dépôt existant, le paquet se limite aux fichiers modifiés. Les agents examinent ces éléments en lecture seule : ils ne travaillent pas sur `Mastermind/code/` et ne lancent pas le jeu.

Dans le cas actuel, `Mastermind/code/` ne contient que le dépôt Git initial vide : le candidat n'y arrive qu'après acceptation de la revue et action d'intégration. La revue peut donc porter un jugement **documentaire et statique** sur le paquet, mais l'utilisateur ne peut pas encore essayer le code depuis son dossier de projet. Cet ordre — examiner avant de disposer du code dans `code/` — est un point à redéfinir, sans confondre la consultation d'un candidat avec son acceptation définitive.

**Paradoxe à corriger :** l'utilisateur est invité à accepter un *rapport de revue* alors qu'il n'a pas encore accès, dans son espace de projet, à une version du jeu qu'il puisse ouvrir et essayer. Il décide donc sur un commentaire du code plutôt que sur le résultat utilisable de l'implémentation.

## Principes à retenir pour la refonte

```text
Conception acceptée → Démarrer l'implémentation (une fois)
                    → Runner : coder → tester → corriger → contrôler → livrer dans code/
                    → Utilisateur : essayer → accepter ou demander une correction
```

1. **Recherche facultative** : elle éclaire le projet si nécessaire ; une mission peut commencer en conception.
2. **Conception obligatoire avant le code** : elle structure et valide ce qui doit être implémenté.
3. **Implémentation comme phase identifiable** : développement, vérification, corrections, revue et intégration doivent apparaître comme la suite du même travail.
4. **Candidat réellement examinable avant décision** : l'utilisateur doit pouvoir voir le code et lancer le résultat produit, puis demander des corrections ou l'accepter. Une revue par des agents peut aider cette décision ; elle ne doit pas se substituer à l'examen du candidat par l'utilisateur.
5. **Lancement unique, exécution autonome** : après acceptation de la conception, « Démarrer l'implémentation » autorise le Runner à enchaîner la production du code, les tests, les corrections nécessaires, les contrôles de qualité et la remise d'un résultat utilisable dans `code/`. Ces étapes internes sont visibles dans le suivi, mais ne demandent pas chacune un nouveau clic, une nouvelle « collaboration » ou une nouvelle saisie du jeton.
6. **Intervention humaine au bon moment** : le Runner s'arrête si une décision métier manque, si une erreur empêche réellement de poursuivre (par exemple une authentification invalide) ou lorsqu'il a livré un résultat prêt à être essayé. L'utilisateur examine alors l'application et décide d'accepter ou de demander une correction. Il garde la possibilité d'interrompre l'exécution.

La navigation entre ces sections doit rester possible à tout moment, sans imposer de revenir au début d'une étape pour avancer. **Points à définir avec Claude :** comment rendre le candidat exécutable dans `code/` sans perdre la traçabilité des versions ; quels contrôles le Runner peut mener seul ; quels événements exigent réellement une réponse humaine ; comment conserver l'autorisation et l'authentification pendant une exécution sans ressaisie à chaque étape.

## Commentaires de Claude (Sonnet 5.5)

### Ce qui est juste

- **Le diagnostic est exact.** La rupture se situe après le paquet : une revue documentaire A/B repart à « Prête » et ressemble à une nouvelle recherche.
- **Le paradoxe est bien formulé.** On demande d'accepter un rapport sur du code que l'utilisateur ne peut pas essayer ; la décision doit porter sur le résultat utilisable.
- **Les principes 5 et 6 décrivent la cible** : un seul lancement, une exécution qui va au bout, et un arrêt seulement sur une décision métier, une erreur bloquante ou une livraison.

### Réserves

1. **État actuel et cible mélangés.** C'est voulu, mais il faudrait deux documents, ou au moins une section « Décisions prises » séparée de « Points à définir ».
2. **La boucle « corriger » n'a pas de condition d'arrêt.** Le projet interdit tout budget ou quota interne, mais un Runner autonome sans garde-fou peut tourner en rond. Proposition : un critère de **non-progression** plutôt qu'un plafond — même échec deux fois de suite, ou aucun diff utile sur un tour. Le Runner s'arrête alors et rend la main avec le motif. Cela reste cohérent avec le tableau des interdits.
3. **Le statut de la revue A/B n'est pas clair (principe 4).** La faire passer d'étape bloquante à **passe de critique interne au Runner**, appliquée au diff avant livraison (B critique, A corrige). Ce n'est plus une collaboration séparée ; l'utilisateur garde la décision finale en essayant le code.
4. **Conservation de l'autorisation.** Le jeton ressaisi à chaque étape est le vrai détail technique à régler ; l'avoir noté est utile.

### Réponse à la question ouverte sur `code/`

- Le Runner livre dans `code/` sur une **branche candidate** (par exemple `candidat/001`), jamais sur la branche principale.
- L'utilisateur essaie le code à cet endroit :
  - **Accepter** : fusion de la branche candidate.
  - **Demander une correction** : le Runner est relancé avec un objectif précis, sur une nouvelle branche candidate.
- On obtient un code exécutable et la traçabilité des versions, sans dossier de paquets figés.

### Suite

Ce changement modifie la conception du Runner, qui est une exception décidée par le PO. Il demande donc une **décision écrite et datée** dans le plan et la mise à jour de `docs/RUNNER.md` avant tout code.

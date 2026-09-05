> Ce document n'est pas approuvé : sa présence prouve que le cycle s'est achevé, rien de plus.
> Revue B : CONSULT · constats restés ouverts : 7 (dont 0 BLOCKING) · corpus figé le 2026-09-05.


# Les tensions internes des règles fondatrices d’IAbinome

## Conclusion

Le corpus établit deux tensions opérationnelles :

1. économiser les contrôles tout en maintenant des moyens de vérification non substituables ;
2. alléger les prompts tout en répétant explicitement chaque contrat de sortie.

Dans les deux cas, le corpus documente les échecs produits lorsque l’arbitrage penche trop loin d’un côté. Il ne démontre cependant pas qu’il soit impossible de tenir simultanément les deux règles : il montre une zone de réglage, sans en fournir le seuil.

Deux autres rapprochements ne satisfont pas le critère demandé :

- la contradiction ouverte et son bornage par le périmètre sont une règle et son correctif, non deux règles dont l’application correcte aurait produit un échec ;
- la construction d’IAbinome avec son protocole et l’interdiction de l’autoréparation ne sont pas montrées en conflit, notamment parce que l’exécution autonome est interdite.

La réponse à « laquelle cède en premier » dépend du sens donné à la question :

- **dans l’histoire rapportée**, la relecture croisée du code est la première règle explicitement suspendue, le 3 septembre 2026 ;
- **si le projet grossit à l’avenir**, le corpus ne permet pas de déterminer laquelle cédera en premier. La suspension passée était motivée par la précision de la conception et la rentabilité estimée de la revue, non par la taille du projet. Assimiler ces deux causes serait une inférence sans fondement textuel.

## Sources et niveau d’accès

Les trois documents autorisés ont été lus directement et intégralement dans l’instantané local du 5 septembre 2026 :

- [POURQUOI.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/POURQUOI.md:1) — accès direct intégral vérifié ; source primaire des cinq règles fondatrices et résumé interne de l’échec de DialogForge ;
- [CLAUDE.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/CLAUDE.md:1) — accès direct intégral vérifié ; instructions permanentes ;
- [RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:1) — accès direct intégral vérifié ; registre primaire des règles du projet, mais résumé secondaire des essais, missions et décisions auxquels il renvoie.

Les événements décrits dans les motifs de `RULES.md` sont donc directement lisibles en tant qu’entrées du registre, mais leurs artefacts sous-jacents n’ont pas été vérifiés. Les fichiers cités mais non fournis — notamment `ARRET_REFACTORING.md`, `RECOLTE.md`, `DEPART.md`, `NOTES.md` et `session_log.md` — sont **absents du corpus**, et non pas vides, négatifs ou prouvés inexistants.

Les reprises d’une règle entre les trois documents ne sont pas comptées comme des preuves indépendantes.

## 1. Économie des contrôles contre couverture non substituable

### Les deux règles

Règle d’économie :

> « **Chaque contrôle ajouté a un coût qui ne se voit qu’au refactoring.** […] La bonne question n’est jamais “est-ce que ce contrôle est utile ?” — c’est “qu’est-ce que je retire en échange ?” »

Source primaire : [POURQUOI.md, règle 2](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/POURQUOI.md:37).

Règle de couverture :

> « **Une relecture externe et une suite de tests ne couvrent pas le même espace : la verdeur de l’une ne justifie pas de suspendre l’autre.** »

Source directe : [RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:37).

### Cas concret

La relecture croisée du code a été suspendue parce que la conception, déjà contredite cinq tours, paraissait assez précise pour rendre cette relecture peu rentable. Deux défauts de gabarit ont ensuite été découverts en mission réelle, alors qu’ils étaient invisibles pour la suite de tests. La relecture a été rouverte et a produit huit observations déclarées exactes, dont trois hors d’atteinte d’un cycle nominal ([RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:33)).

Le registre fournit une mesure complémentaire : 262 tests étaient verts, tandis qu’une lecture statique trouvait encore six défauts réels ([RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:38)).

La tension est concrète :

- appliquer la règle d’économie a conduit à suspendre un contrôle jugé peu rentable ;
- maintenir la couverture exige au contraire de conserver tests et relecture, puisqu’ils n’observent pas les mêmes défauts ;
- conserver les deux ajoute la couche cumulative dont la règle fondatrice exige de comptabiliser le coût.

Le corpus contient toutefois une règle d’arbitrage :

> « **Avant d’ajouter un garde-fou, vérifier qu’il compense un défaut encore réel.** »

Source directe, reprise de la troisième règle fondatrice : [RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:194).

Dans l’épisode rapporté, cette vérification tranche localement en faveur de la relecture : le défaut est devenu réel et documenté. Elle ne supprime cependant pas toute la tension, car le corpus ne dit pas ce qui a été retiré « en échange » lors de la réouverture.

**Résultat négatif documenté :** la suspension de la relecture n’a pas tenu. Elle a laissé subsister une classe de défauts que les tests ne couvraient pas.

**Limite :** il n’est pas prouvé que le cumul actuellement retenu rende déjà IAbinome trop gros ou irréparable.

## 2. Sobriété des prompts contre explicitation locale du contrat

### Les deux règles

Règle de sobriété :

> « **Les prompts trop prescriptifs dégradent les modèles récents.** »

Source primaire : [POURQUOI.md, règle 4](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/POURQUOI.md:43).

Règle d’explicitation :

> « **Un prompt qui exige un format doit porter le format — et la règle vaut pour chaque prompt, pas pour le premier.** »

Source directe : [RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:125).

### Cas concret

Le corpus documente les deux bords de la tension.

Du côté de la prescription excessive, les tâches du Lot 0 comportaient jusqu’à douze critères d’acceptation imbriqués ; cette forme est donnée comme ayant réduit la qualité des modèles récents ([POURQUOI.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/POURQUOI.md:43)).

Du côté du contrat insuffisamment explicite, les prompts de révision et de finalisation disaient « rends DOCUMENT » au lieu de porter la balise exacte `IABINOME:DOCUMENT`. L’agent a obéi littéralement et aucune mission ne pouvait aboutir. Une entrée distincte du registre indique que 259 tests étaient pourtant verts, parce que le faux adaptateur émettait la bonne balise sans lire les prompts ([RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:125), [RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:130)).

Le contrat trop rigide possède également son échec documenté : une revue juste de 3,6 Ko, précédée d’une phrase où B expliquait suivre le format demandé, a été refusée et 231 secondes d’appel ont été perdues. La règle a alors été déplacée vers l’acceptation de tout contenu explicitement balisé, sans deviner le contenu non balisé ([RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:73)).

La tension consiste donc à devoir ajouter assez de prescription locale pour rendre le contrat exécutable, sans reconstituer l’empilement de consignes qui dégrade la sortie.

**Résultats documentés :**

- une prescription trop lourde est déclarée dégrader la qualité ;
- un contrat incomplet a rendu deux prompts inutilisables ;
- un contrat interprété trop strictement a refusé une réponse juste.

**Limite :** ces constats proviennent de trois épisodes distincts. Le corpus ne mesure aucun prompt auquel les deux règles auraient été appliquées ensemble, ni le seuil à partir duquel l’explicitation nécessaire devient « trop prescriptive ». La direction du compromis est établie ; son point de collision exact reste **inconnu**.

## Rapprochements non retenus comme tensions établies

### Contradiction ouverte et périmètre

Les règles disent à la fois :

> « **Le contradicteur reçoit une consigne d’omission, pas une consigne de qualité** »

et :

> « **Mais la consigne d’omission doit être accompagnée du périmètre** ».

Sources : [RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:49) et [RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:52).

Le cas de la première passe de Codex montre ce qui arrive **sans** la seconde règle : l’appareil de confinement abandonné est réintroduit. Après ajout du périmètre, la version suivante se contredit sur six points. Ce récit justifie le correctif ; il ne montre pas qu’appliquer correctement les deux règles force l’une à céder ni produit encore un échec. Ce rapprochement n’est donc pas retenu.

Le contenu et l’exactitude des six contradictions restent **non vérifiables** dans les trois fichiers.

### Construction réflexive et autoréparation

Les documents disent :

> « **Construire l’outil avec son propre protocole est la démonstration qu’il n’a jamais eu besoin de machinerie.** »

et :

> « **Ne jamais réparer un sous-système défaillant en s’en servant.** »

Sources : [CLAUDE.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/CLAUDE.md:55) et [POURQUOI.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/POURQUOI.md:46).

Le mécanisme d’échec de DialogForge était l’emploi de ses missions d’implémentation autonome pour réparer leur propre moteur. Or IAbinome interdit explicitement cette fonction :

> « **Pas d’exécution autonome** — Le livrable est un document, exécuté ensuite à la main. »

Source : [CLAUDE.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/CLAUDE.md:43).

Le corpus ne prouve ni qu’IAbinome s’est réparé par son propre protocole, ni que la production réflexive de documents équivaut à l’exécution autonome défaillante de DialogForge. La tension est possible par inférence, mais **non prouvée**.

### Autres candidats non prouvés

- La lecture obligatoire de `POURQUOI.md` et `RULES.md` peut sembler heurter « ne pas lire un fichier si l’information est déjà dans le contexte », mais aucun échec correspondant n’est rapporté.
- L’arbitrage humain pourrait devenir un goulot d’étranglement ; aucun cas ni volume ne l’établit.
- Les fichiers sur disque et l’absence de base de données pourraient rencontrer une limite de capacité ; le corpus n’en documente aucune.
- Le verrou tronqué produit un blocage visible, mais le registre choisit explicitement ce résultat plutôt qu’une récupération automatique susceptible de créer deux détenteurs. Aucune règle concurrente n’exige la disponibilité automatique.

## La règle qui cède en premier

### Ce qui est observé

La première cession explicitement datée d’une règle est :

> « **Suspendue en étape 2 le 2026-09-03, décision du PO** »

à propos de :

> « **Claude produit, Codex relit palier par palier — et réciproquement.** »

La relecture a été rouverte le 5 septembre lorsque deux défauts de gabarit ont rempli sa condition de réouverture ([RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:33)).

La normalisation CRLF suit un mécanisme voisin : écartée au palier 1 avec une condition, elle a été rouverte au palier 3 lorsque le besoin est apparu ([RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:159)). Il s’agit toutefois d’une décision différée, non d’une seconde règle permanente suspendue. Ce parallèle montre que la suspension conditionnelle est un mécanisme général du projet ; il ne prouve pas une fragilité propre à la relecture.

### Ce qui n’est pas déterminable en cas de croissance

Le motif donné pour suspendre la relecture est la précision acquise après cinq tours de contradiction, qui la rendait « peu rentable ». Le corpus ne relie pas cette rentabilité :

- au nombre de lignes ;
- au nombre de missions ;
- au nombre de règles ;
- à la longueur des prompts ;
- au nombre d’agents ou aux appels concurrents.

Il n’est donc pas possible d’inférer que la relecture serait la première règle sacrifiée **parce que le projet grossit**.

La cible d’environ 1 500 lignes ne fournit pas davantage de réponse automatique. Le registre impose de mesurer le **code effectif**, et non les lignes brutes : un correctif de 142 lignes brutes n’en comptait que 64 en code effectif, le reste étant à 65 % de la documentation ([RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:150)). Une hausse du volume brut n’établit donc pas à elle seule que la métrique de garde approche de sa limite.

**Résultat final :**

- historiquement, la relecture croisée du code cède la première ;
- sous l’effet hypothétique de la croissance, l’ordre de cession est **inconnu et non prouvé**.

## Ce que le corpus ne couvre pas

Pour déterminer quelle règle céderait réellement lors d’un changement d’échelle, il manquerait :

- une définition opérationnelle de « grossir » ;
- la taille actuelle d’IAbinome en code effectif et son évolution ;
- des mesures de coût selon le volume : temps de revue, appels, tokens, fréquence des défauts ;
- des expériences comparables avec et sans relecture ou avec différents niveaux de prescription ;
- une hiérarchie explicite entre taille, couverture, coût, disponibilité et périmètre ;
- la réponse à « qu’est-ce que je retire en échange ? » pour chaque contrôle conservé ;
- les documents de décision et journaux sous-jacents auxquels le registre renvoie.

Une incohérence temporelle limite également la reconstruction : `CLAUDE.md` déclare « **État : pas encore commencé** », tandis que `RULES.md` rapporte plusieurs paliers, 262 tests et une première mission réelle ([CLAUDE.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/CLAUDE.md:34), [RULES.md](C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:35)). L’état réel au 5 septembre est donc **inconnu** : il n’est ni déclaré nul, ni prouvé négatif.

La conclusion reste bornée à l’instantané fourni : le corpus montre deux compromis déjà éprouvés et une première suspension historique, mais il ne contient pas les observations nécessaires pour prédire l’ordre de cession provoqué par la croissance.

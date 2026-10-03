# Proposition — un parcours continu de l'idée au code

Analyse du 2026-10-03, demandée par le PO après l'essai Mastermind. Orientations acceptées
par le PO le même jour ; mise en œuvre décrite dans
[PARCOURS_MISSION_CONCEPTION.md](PARCOURS_MISSION_CONCEPTION.md).
L'analyse n'a modifié ni le moteur ni les missions réelles.

Vérification : tests existants `test_follow_up`, `test_gui_runner`, `test_development` et
`test_runner` : 47 passés, 26 sous-tests, sans appel fournisseur. Ces résultats vérifient les
contrats actuels ; ils ne démontrent pas la fluidité du parcours réel ni le parcours proposé.

## Constats vérifiés

1. **La conception sans documentation est volontairement refusée.**
   `MissionKind.missing_source` impose un corpus, y compris avant le cadrage dynamique.
   C'est l'application de D1 dans `TYPES_DE_MISSION.md`, désormais mise en question par l'usage.
2. **La recherche a été transmise, mais le mandat a été perdu.**
   `Mastermind-conception/corpus` contient bien le livrable accepté, le bilan et la décision
   de Mastermind. `follow_up_defaults` génère cependant toutes les rubriques vides sauf Sources.
   La demande initiale issue du cadrage n'est pas copiée dans le corpus.
   La conception s'est arrêtée en `WAITING_HUMAN`, dès `PROPOSAL_A` : l'agent demande ce qu'il
   doit produire, si la recherche fait autorité et quelles hypothèses sont validées.
   Il ne s'agit donc pas d'une perte du livrable ni d'un incident technique.
3. **L'emplacement voisin est programmé.** `follow_up_defaults` propose
   `<parent>/Mastermind-conception`. L'écran est celui de « Nouvelle collaboration ».
   Les réglages sont initialisés comme pour une création, pas hérités de la recherche.
   `--depuis` est incompatible avec le cadrage par agent : impossible d'utiliser F pour
   compléter uniquement les arbitrages nécessaires sur cette transition.
4. **La demande confond résultat du projet et résultat de l'étape.** Le cadrage de Mastermind
   demande une application jouable, alors que le cycle produit un document. La revue a donc
   relevé l'absence d'application. Le livrable contient déjà règles, structure, code proposé et
   tests : la recherche a débordé sur la conception pour satisfaire ce mandat. F ne reçoit
   pas de consigne propre au type dans son prompt initial ; B n'a pas de paramètre de type
   dans `build_review`. La cohérence repose trop sur la demande humaine.
5. **Le Runner est orienté dépôt existant.** `prepare` résout un dépôt Git et un commit de
   départ ; un dossier neuf ou un dépôt sans commit ne suffit pas. La GUI exige des commandes
   de validation en JSON. Elle affiche le chemin du paquet final, sans bouton de création de
   sa revue. Sa session est conservée en mémoire ; le formulaire ne recharge pas les paramètres
   d'une exécution depuis la mission lors d'une nouvelle ouverture.
6. **Le passage vers le code ne transmet pas tout le corpus.** `export_conception` exporte
   demande, conception, décision et objections ouvertes. Le futur plan doit donc être autonome
   et reprendre les informations nécessaires à l'exécution, sans renvoyer seulement à la recherche.

## Choix recommandé

Combiner les deux parcours :

- idée suffisamment claire → conception → acceptation → développement → revue du code ;
- besoin d'étude → recherche → acceptation → conception → acceptation → développement → revue.

La recherche devient facultative. La conception accepte une demande sans corpus ; le cadrage
dynamique reste disponible, sans devenir obligatoire. Les inconnues sont explicites et seules
celles qui empêchent une décision utile appellent une question. La règle de recherche sourcée
reste inchangée. Amender explicitement D1 et les textes qui présentent la recherche comme obligatoire.

Chaque étape précise son livrable : étude pour la recherche, plan réalisable et vérifiable pour
la conception, fichiers et validations pour le développement. Le but final « application jouable »
reste visible comme objectif du projet, mais n'est pas le critère de réussite d'une étude.
F, A et B doivent recevoir cette distinction, avec des consignes courtes.

## Une mission, un dossier

Pour les nouvelles missions, organisation proposée :

```text
Mastermind/
  mission.json
  recherche/                 # facultatif, cycle documentaire existant
  conception/                # cycle documentaire existant
  developpement/
    export-001/
    executions/              # références des exécutions WSL
    paquets/
    revues/
  code/                      # dépôt source puis code intégré après décision
```

`mission.json` ne porte que les chemins des étapes et les liens de provenance. Les statuts et
acceptations se relisent dans les fichiers actuels : aucune seconde machine à états. Une nouvelle
session A/B par étape reste utile pour ses propres revues ; l'utilisateur reste dans la même mission.
L'interface présente une seule entrée Mastermind et des étapes consultables, avec reprise de
l'étape déjà créée quand elle existe. Une nouvelle version se crée explicitement sans écraser l'ancienne.

Pour **Mastermind existant**, préserver la recherche à sa place actuelle, puis rattacher
`Mastermind-conception` à `Mastermind/conception`. Pas besoin de réorganiser toute la recherche.
Le rattachement doit vérifier les chemins enregistrés (cadrage, appels, récents, provenance),
conserver les octets et empreintes, et vérifier l'ouverture après transfert. La réparation de la
demande utilise ensuite la réponse humaine normale, qui conserve son historique ; elle ne réécrit
pas directement les fichiers hachés. Ce transfert n'a pas été effectué pendant l'analyse.

Le Runner qualifié exige un dossier Linux hors `/mnt` : son clone de travail restera sous WSL.
La mission Windows doit contenir sa référence persistante, les paquets rapatriés et le code livré.
Mettre aussi le clone d'exécution sur `C:` demanderait une autre qualification ; ce n'est pas
nécessaire pour garder la conception et les livrables dans Mastermind.

## Transmission entre les étapes

« Poursuivre en conception » prépare une demande complète, relisible et modifiable :

- objectif : transformer la recherche acceptée en plan de réalisation du projet ;
- livrable : choix motivés, composants/fichiers, étapes et validations exécutables ;
- sources : recherche acceptée, bilan, décision **et demande initiale** ;
- contraintes, exclusions et critères du projet : conservés comme contexte identifié ;
- critères de l'étape : plan autonome, testable et transmissible au Runner.

Cette préparation n'exige pas d'appel de modèle : assembler un mandat de transition explicite et
les documents existants suffit. Les réglages A/B et de revue sont proposés à partir de la source,
puis restent modifiables. Le dossier est automatiquement celui de la mission.

Les réserves et hypothèses restent visibles. Accepter la recherche autorise son utilisation comme
base, sans convertir automatiquement toutes ses hypothèses en décisions humaines. Pour Mastermind,
H1 à H5 sont présentées ensemble ; seules les décisions réellement nécessaires sont demandées.
Si un cadrage complémentaire est choisi, F lit les mêmes documents et traite les points ouverts,
sans recommencer le questionnaire initial. Une source révisée n'altère pas une conception déjà
créée : sa nouvelle version doit être reprise explicitement.

## Passage au développement et retour

Après acceptation de la conception, proposer « Nouveau projet » ou « Dépôt existant ».
Pour un nouveau projet, préparer explicitement `code/` et une base Git initiale dans le parcours
Runner, puis utiliser le clone existant. L'utilisateur ne doit pas préparer Git à la main.
Pour un dépôt existant, conserver le choix du dépôt et du commit.

La conception doit fournir les commandes de validation et leurs prérequis. L'écran permet de
les vérifier sans imposer la saisie JSON. Si elles restent en texte libre dans le document,
leur reprise doit être confirmée explicitement : ne pas prétendre les extraire de manière fiable
par simple recherche de texte. Vérifier les outils requis avant de payer un appel ; le Runner
actuel n'installe pas automatiquement les dépendances.

Conserver dans la mission le chemin WSL et les paramètres non secrets, afin de reprendre après
fermeture. Un échec après export doit permettre de réutiliser cet export vérifié : aujourd'hui,
un nouveau « Exporter et lancer » vers le même dossier rencontre le refus de destination existante.

À la fin : « Examiner le code » crée la revue documentaire depuis le paquet et sa demande déjà
générée, avec copie sous la mission. Présenter ensuite le résultat et la décision d'intégration.
L'intégration du candidat dans `code/` demeure une action humaine explicite ; les corrections
produisent un nouveau candidat et un nouveau paquet. Ce raccord réemploie le développement
assisté, sans reconstruire un orchestrateur.

## Ordre de réalisation proposé

1. Entrée directe en conception ; demandes et consignes adaptées à chaque étape ; transmission
   complète recherche → conception. Rejouer le cas Mastermind sans questionnaire vide.
2. Dossier de mission, navigation et rattachement de Mastermind existant, reprise sans doublon.
3. Nouveau projet dans le Runner, validations utilisables, reprise persistante, accès à la revue
   et restitution du code. Vérifier aussi l'échec après export.

Les tests doivent couvrir les parcours utiles : conception sans corpus avec et sans cadrage,
recherche acceptée transmise sans perte du mandat, hypothèses non promues silencieusement,
réouverture de la mission à la bonne étape, projet sans dépôt, reprise du Runner, paquet puis revue.
Conserver les tests d'acceptation périmée et d'intégrité. Utiliser les faux agents ; l'essai GUI
réel Mastermind sera la validation d'usage. Les tests actuels de transition vérifient la copie
du corpus et le bouton, mais tolèrent le mandat vide et attendent le dossier voisin.

Les plafonds de taille existants restent à mesurer avant implémentation. Cette proposition
réutilise le moteur documentaire et le Runner séparé ; aucun service, worker ou base de données.

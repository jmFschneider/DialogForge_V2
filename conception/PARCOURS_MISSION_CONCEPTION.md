# Conception — parcours de mission, de l'idée au code

Date : 2026-10-03.

**Statut : conception de mise en œuvre.** Les orientations de
[l'analyse du parcours](PARCOURS_MISSION_2026-10-03.md) ont été acceptées par le PO le
2026-10-03. Le présent document précise leur réalisation ; il ne constate pas leur implémentation.
La demande de cette session porte sur la rédaction de ce document.

## 1. Objectif et périmètre

L'utilisateur ouvre une mission, décrit son projet et progresse jusqu'au code examiné, sans
ressaisir son besoin ni chercher des collaborations éparpillées. Une conception peut commencer
sans documentation. Lorsqu'une recherche existe, la conception utilise son résultat accepté.

Deux parcours sont proposés :

```text
Idée ────────────────────→ Conception → Acceptation → Développement → Revue → Intégration
  └→ Recherche → Acceptation ───┘
```

Le cadrage dynamique est disponible à l'entrée et pour préciser une transition. Il est facultatif.
Chaque démarrage susceptible d'appeler un fournisseur reste une action explicite. L'acceptation
d'une étape ne lance pas automatiquement la suivante.

Le périmètre comprend la création, la continuité documentaire, le rangement, la navigation,
le projet neuf, la reprise du Runner, la revue du paquet et la remise du code. Le moteur A/B,
les décisions portant sur une version précise et le Runner séparé sont réemployés.

## 2. Décisions fonctionnelles

| Sujet | Comportement retenu |
|---|---|
| Recherche | Étude sourcée ; web ou corpus requis comme aujourd'hui. |
| Conception | Plan réalisable à partir d'une demande, avec documentation facultative. |
| Résultat du projet | Visible pendant toutes les étapes, par exemple « application jouable ». |
| Résultat d'une étape | Document d'étude, plan de réalisation, candidat de code ou rapport de revue. |
| Passage recherche → conception | Mandat complet et sources copiées ; aucune rubrique essentielle laissée vide par le logiciel. |
| Organisation | Un dossier de mission, des sous-dossiers d'étapes. |
| Sessions IA | Propres à chaque étape ; continuité assurée par les documents et décisions transmis. |
| Développement | Nouveau projet ou dépôt existant ; clone isolé sous Linux pour le profil actuel. |
| Intégration | Action explicite après revue ; jamais une conséquence automatique de son acceptation. |

Cette décision remplace D1 de `TYPES_DE_MISSION.md` pour l'obligation de corpus en conception,
et précise D4 et D6 pour le parcours et sa présentation. Les exigences de sources de la recherche
et d'acceptation applicable aux transitions sont conservées.

## 3. Modèle de fichiers

### 3.1 Nouvelle mission

```text
Mastermind/
  mission.json
  recherche/                       # absent si entrée directe en conception
  conception/
  developpement/
    export-001/
    executions/001.json             # paramètres non secrets et référence WSL
    paquets/001/
    revues/001/
  code/                            # dépôt créé pour un nouveau projet
```

Les dossiers recherche, conception et revue conservent le format de collaboration actuel :
`configuration.json`, `etat.json`, demande, corpus, appels, échanges, livrables et décisions.
Leur schéma n'est pas remplacé par un état global de mission.

`mission.json` est un petit registre de rattachement, versionné indépendamment :

```json
{
  "schema_version": 1,
  "name": "Mastermind",
  "steps": [
    {"path": "recherche", "role": "recherche", "source": null},
    {"path": "conception", "role": "conception", "source": "recherche"}
  ]
}
```

`role` décrit l'étape dans le parcours. Une revue de code a le rôle `revue` et utilise le type
documentaire `RECHERCHE` existant. Aucun troisième type de boucle A/B n'est ajouté.
`source` désigne une étape antérieure ou un paquet par son chemin relatif à la mission.
Les empreintes probantes restent celles des corpus, exports et paquets ; le registre sert à naviguer.

Les chemins internes sont relatifs, contenus dans la mission, sans remontée `..`, ni lien
redirigeant hors de celle-ci. `.` est permis pour une collaboration historique située à la racine.
Un chemin d'étape n'apparaît qu'une fois. Les statuts, décisions et objections ne sont pas dupliqués.
Un fichier invalide donne un diagnostic ; il n'est pas réinitialisé silencieusement.

### 3.2 Création et rattachement

Une fonction partagée de la façade prépare l'étape, appelle la création actuelle, puis inscrit
son chemin dans le registre sous un verrou de mission distinct du verrou de collaboration.
Le registre est écrit atomiquement. Le verrou de mission ne reste jamais tenu pendant un appel IA.
L'ordre de verrouillage éventuel est mission puis collaboration.

Si la création réussit mais que l'inscription échoue, la collaboration valide est conservée.
À la reprise, l'emplacement attendu est inspecté et proposé au rattachement ; aucun nouvel appel
ni écrasement. Un dossier partiel est signalé pour inspection. Les actions ordinaires rouvrent
l'étape déjà rattachée. « Nouvelle version de conception » crée explicitement `conception-002`,
puis les numéros suivants ; les versions anciennes restent consultables.

L'export de développement est frère de la conception sous `developpement/`. Il reste ainsi hors
de la collaboration exportée, conformément à `_outside` dans `development.py`.

### 3.3 Ouverture et compatibilité

L'ouverture d'un dossier avec `mission.json` affiche la mission. L'ouverture d'une collaboration
rattachée retrouve sa mission par ses ancêtres et son inscription, sans exploration globale du disque.
Une collaboration indépendante reste utilisable en CLI et GUI au format actuel.

L'accueil et `list` regroupent les étapes d'une mission sous une entrée. Les statuts sont calculés
par inspection des collaborations. Les récents enregistrent la mission et, comme préférence
d'affichage, la dernière étape consultée. Cette préférence ne décide jamais quelle étape peut tourner.

## 4. Demandes et consignes des agents

### 4.1 Entrée directe en conception

Supprimer le refus « conception sans dossier d'entrée » dans `MissionKind.missing_source`.
Tous les points d'entrée continuent d'appeler cette règle commune. Un corpus déclaré mais vide
reste une erreur explicite ; l'absence volontaire de corpus est valide.

L'écran propose « Concevoir mon projet » et « Étudier une question », avec une phrase sur le
livrable de chaque choix. Une demande libre reste possible. La présence de sections n'est pas
transformée en une nouvelle barrière générale à la création.

Les prompts de F, A et B reçoivent le type de travail. F conserve le résultat final souhaité
dans le contexte du projet et formule le livrable de l'étape. A produit ce livrable. B juge sa
conformité à cette étape : l'absence de fichiers exécutables n'est pas un défaut d'une étude.
La revue de code conserve ses consignes particulières issues du paquet.

Le prompt de conception couvre les deux cas : exploiter les éléments fournis s'ils existent,
sinon partir de la demande ; motiver les choix, expliciter les hypothèses et fournir des étapes
vérifiables. Une question réellement bloquante utilise la porte humaine actuelle.

### 4.2 Mandat de transition

`follow_up_defaults` est remplacé par une préparation complète utilisant la recherche inspectée.
Le texte est construit sans appel fournisseur :

```markdown
# Conception du projet Mastermind

## Objectif
Transformer la recherche acceptée en plan de réalisation du projet décrit ci-dessous.

## Livrable
Une conception autonome : choix motivés, structure, étapes de réalisation, validations
et prérequis nécessaires au développement.

## Sources
Demande d'origine, livrable accepté, bilan et décision de la recherche, fournis en corpus.

## Contraintes
Conserver les contraintes du projet. Distinguer les décisions exprimées des hypothèses
proposées dans la recherche. Signaler les arbitrages indispensables encore ouverts.

## Non-objectifs
Conserver les exclusions du projet. Cette étape livre un plan avant l'écriture du code.

## Critères de fin
Le plan permet de développer et vérifier le résultat attendu sans reconstituer la recherche.

## Contexte du projet — demande d'origine
[Texte intégral de la demande précédente, identifié comme contexte de provenance.]
```

Le texte réel reprend intégralement la demande source, sans analyse fragile de ses titres.
La consigne précise que ses attentes de produit final appartiennent au projet ; les critères de
l'étape sont ceux du mandat de transition. L'utilisateur peut modifier ce mandat avant création.

Le corpus contient `demande.md`, `livrables/version_finale.md`, `livrables/bilan.md` et
`decisions.json`. Une provenance de transition associe le chemin source relatif à la mission et
les empreintes de la version acceptée, dont celle de la demande. Le manifeste conserve les
empreintes des fichiers copiés. Copier et vérifier la version sous le verrou source évite de
mélanger une acceptation et des documents modifiés pendant la préparation.

Les paramètres A/B, modèles, effort, accès du relecteur et plafond de révisions sont proposés
depuis la configuration source. L'accès web est affiché explicitement avec sa valeur héritée.
Après création, la configuration de la conception devient sa seule référence.

### 4.3 Cadrage complémentaire et réserves

Lever l'incompatibilité actuelle entre `from_research` et le cadrage F. Préparer d'abord un
instantané de transition, puis fournir à F ce corpus et le mandat déjà rempli. La création
consomme ce même instantané ; elle ne reconstruit pas un second corpus depuis la recherche.
La source et l'acceptation sont revérifiées avant création. Si elles ont changé, proposer
explicitement une nouvelle préparation ; ne pas remplacer les sources sous une conversation F.

F reçoit : « Précise seulement les arbitrages encore nécessaires à la conception ; conserve
le cadrage déjà présent ». Les contraintes de tours et de reprise du cadrage actuel restent applicables.

L'acceptation d'une recherche autorise sa prise comme base. Elle ne transforme pas chaque
hypothèse en choix humain. Les réserves restent visibles ; A ou F peuvent regrouper les arbitrages
utiles. Pour Mastermind, H1 à H5 doivent être conservées avec leur statut, puis confirmées ou
motivées dans la conception. Le logiciel n'extrait pas une liste générique d'hypothèses par regex.

## 5. Interface et commandes

L'en-tête montre le nom de mission et les étapes : Recherche, Conception, Développement, Revue.
La recherche peut être indiquée « non nécessaire ». Les actions viennent de la façade partagée.

| Situation | Action principale |
|---|---|
| Nouvelle mission | Choisir recherche ou conception, saisir ou cadrer la demande. |
| Recherche acceptée | Préparer la conception, puis créer ou créer et démarrer. |
| Conception déjà créée | Reprendre la conception existante. |
| Conception acceptée | Préparer le développement. |
| Exécution interrompue | Inspecter, continuer explicitement ou collecter sans appel. |
| Paquet disponible | Préparer sa revue, puis la lancer explicitement. |
| Rapport accepté et vérifié | Présenter le candidat et proposer son intégration explicite. |

Les étapes non disponibles indiquent la raison précise : acceptation manquante, version modifiée,
paquet absent, etc. Aucun écran de transition ne présente un formulaire générique vide.

Surface CLI proposée, réutilisant les opérations de la façade :

- `new CHEMIN ...` reste une création indépendante compatible avec l'existant ;
- `new CHEMIN ... --mission RACINE` crée puis rattache une étape contenue dans RACINE ;
- `new CHEMIN --kind conception --depuis RECHERCHE` peut utiliser le mandat généré si aucune
  demande n'est fournie ; une demande explicite le remplace sans perdre le corpus de provenance ;
- `show RACINE` et `list PARENT` reconnaissent les missions ; les commandes d'exécution
  continuent de cibler une collaboration précise, sans sélection implicite entre versions ;
- `mission attach RACINE COLLABORATION --role ROLE` rattache une collaboration déjà située
  dans la mission. Un déplacement extérieur reste une opération explicite distincte.

Les options exactes apparaissent dans l'aide et ses tests lors du lot correspondant. Aucun
nouveau moteur d'appels n'est introduit pour servir ces commandes.

## 6. Conception prête à développer

Le document accepté doit préciser le résultat attendu, le périmètre, les décisions et hypothèses,
les composants ou fichiers, les étapes, les tests et le mode de lancement de l'application.
Il reprend les faits utiles de la recherche : le Runner ne reçoit pas implicitement tout son corpus.

Les validations comportent des commandes, leur répertoire de travail et leurs prérequis. Dans
cette version, elles sont exécutées à la racine du dépôt, conformément au Runner actuel.
Si un projet nécessite un sous-répertoire, fournir un script à lancer depuis la racine.

Le formulaire remplace la saisie JSON obligatoire par une liste éditable de commandes :
exécutable et arguments distincts. L'utilisateur peut ajouter, modifier ou retirer une ligne.
Le texte des validations de la conception est accessible à côté. Le contrat interne reste une
liste de listes d'arguments sans shell implicite. Une commande libre copiée depuis le document
n'est jamais exécutée automatiquement. Une proposition structurée éventuellement ajoutée plus
tard devra être montrée et confirmée ; elle n'est pas requise pour ce lot.

## 7. Préparation et reprise du Runner

### 7.1 Nouveau projet

Le choix « Nouveau projet » propose `mission/code`. Avant toute mutation, vérifier l'absence
du chemin ou un dossier vide, Git disponible et une identité Git utilisable. Si elle manque,
demander sa configuration ; aucune identité inventée ni modification globale automatique.

Après l'action explicite « Préparer et lancer », le composant Runner initialise ce dépôt,
crée un commit initial vide avec l'identité configurée, enregistre son OID puis prépare le clone
isolé à partir de cette base. Le moteur documentaire ne fait aucune écriture Git.
Une relance réutilise uniquement une base initiale dont l'identité est enregistrée ; elle ne
réinitialise jamais un dépôt existant. Un dossier occupé conduit au choix « Dépôt existant ».

### 7.2 Dépôt existant et prévol

Conserver le choix du dépôt et du commit. Montrer la base résolue et rappeler que seuls les
fichiers committés entrent dans le clone. Aucun nettoyage ni commit des changements de l'utilisateur.

Avant l'appel payant, vérifier la conception et son acceptation, l'export, le profil WSL,
le chemin Linux hors `/mnt`, la présence des outils requis par les validations et la cohérence
des paramètres. La présence d'un outil ne prouve pas que les tests futurs réussiront.
Les dépendances projet doivent être préparées explicitement ; le profil actuel ne les installe
pas automatiquement. Un prérequis manquant laisse une préparation reprenable et un message actionnable.

### 7.3 Référence d'exécution persistante

`developpement/executions/001.json` contient : version de schéma, conception source, chemin
relatif de l'export et son empreinte, dépôt source, base OID, profil, distribution WSL utilisée,
chemin Linux absolu du run, validations, délais et chemins des paquets rapatriés.
Le dépôt extérieur peut avoir un chemin absolu ; son indisponibilité est signalée lors de la reprise.
Aucun jeton ni variable secrète n'est conservé. Le statut affiché est dérivé du dossier Runner
et des artefacts ; la référence ne duplique pas `run.json` comme autorité d'exécution.

La référence est publiée avant l'appel fournisseur. À la réouverture, lire le run par le pont WSL.
Un chemin absent est signalé ; ne pas lancer une nouvelle exécution sous le même nom.
Un verrou ambigu garde le comportement actuel, sans suppression automatique.

| Interruption | Reprise |
|---|---|
| Export publié, clone absent | Vérifier l'export et reprendre la préparation. |
| Clone préparé, agent non lancé | Proposer de lancer sur cette préparation. |
| Appel interrompu ou résultat incertain | Montrer les traces ; continuation explicite ou collecte. |
| Validations échouées | Présenter les résultats ; correction explicite avant nouveau paquet. |
| Paquet produit, copie Windows échouée | Retenter uniquement le rapatriement. |
| Paquet copié, revue non créée | Préparer la revue sans relancer l'agent développeur. |

Un export existant n'est réutilisé que si son contenu vérifié correspond à la même version
acceptée. Une nouvelle conception produit un nouvel export et une nouvelle exécution.
La fermeture conserve le mécanisme de pause/interruption actuel et l'unicité d'exécution.

## 8. Paquet, revue et remise du code

Le pont renvoie le chemin et l'identité du paquet. Le rapatriement publie une copie atomique
dans `developpement/paquets/NNN`, vérifie ses empreintes avec les fonctions existantes, puis
l'inscrit dans la référence d'exécution. Une copie déjà identique est réutilisée ; une collision
de contenu n'est pas écrasée. La simple existence d'un dossier ne signifie pas « paquet prêt ».

« Examiner le code » crée `developpement/revues/NNN` avec la demande et la liste de sources
générées par `build_package`, en mode consultation. Un second clic ouvre cette même revue.
La revue reste un cycle documentaire ordinaire ; `dev-verify` contrôle son rattachement au paquet
avant la décision. L'acceptation du rapport n'est pas une acceptation implicite du merge.

Le paquet documentaire n'est pas supposé contenir un dépôt Git importable. Pour intégrer,
le Runner fournit un bundle Git du candidat exact, identifié par base et tête et vérifié à
l'import. Le bundle sert au transport ; le paquet et la revue restent les preuves documentaires.

L'action explicite « Intégrer ce candidat » affiche dépôt cible, base, tête et revue applicable.
Elle vérifie le paquet, `dev-verify`, l'acceptation actuelle du rapport, l'absence de changements
locaux et l'identité de HEAD cible avec la base. Elle importe le candidat puis avance uniquement
en fast-forward. Aucun merge de résolution, reset ni écrasement. Si le dépôt a avancé, fournir
le candidat et expliquer qu'une intégration manuelle ou une nouvelle base est nécessaire.

Pour un nouveau projet, le dépôt cible est `mission/code`. Pour un dépôt existant extérieur,
son emplacement reste affiché ; aucune seconde copie du code n'est présentée comme autorité.
La mission conserve le paquet, la revue et un reçu d'intégration avec les OID. Après interruption
entre avance Git et reçu, reconnaître la tête exacte déjà intégrée et compléter le reçu sans
réappliquer le code. Un échec d'import conserve les artefacts pour reprise.

Après une demande de correction, un nouvel appel explicite reçoit les constats de revue et
produit un nouveau commit et un nouveau paquet. Réutiliser le mécanisme d'antécédents existant.
La GUI propose ensuite une nouvelle revue, sans boucle automatique de développement.

## 9. Reprise du cas Mastermind

Disposition retenue pour préserver la recherche existante :

```text
Mastermind/
  mission.json                     # recherche enregistrée avec path = "."
  configuration.json               # recherche existante conservée à la racine
  etat.json
  ...
  conception/                      # contenu de Mastermind-conception
  developpement/
  code/
```

Procédure à exécuter lors de l'implémentation, hors de cette rédaction :

1. Vérifier les deux chemins absolus, l'absence d'exécution et de verrou actif, l'intégrité des
   collaborations et l'absence de destination. Relever les empreintes de tous les fichiers.
2. Copier `Mastermind-conception` dans un dossier temporaire situé sous Mastermind ; vérifier
   les octets et l'ouverture. Les chemins absolus historiques dans les journaux restent des
   preuves, sans réécriture. Vérifier séparément tout chemin encore utilisé pour reprendre.
3. Publier `Mastermind/conception` puis le registre de mission. Conserver le dossier extérieur
   comme sauvegarde jusqu'à validation de la reprise, en le retirant des récents actifs.
   La référence opérationnelle devient exclusivement la copie rattachée.
4. Ouvrir cette conception en `WAITING_HUMAN`. Préparer une réponse à la question existante :
   produire le plan de réalisation depuis la recherche acceptée, reprendre le besoin initial,
   conserver les exclusions et traiter explicitement H1 à H5. Faire relire cette réponse.
5. Utiliser la reprise normale avec réponse pour conserver l'historique et les empreintes ;
   aucun remplacement direct de `demande.md` ou `etat.json`. Reprendre A puis B après lancement explicite.

Si un chemin actif empêche la relocation, arrêter avant publication et fournir le diagnostic.
Les anciennes traces ne sont pas modifiées pour masquer ce problème. La reprise réussie signifie
que la demande enrichie, le corpus et les décisions restent accessibles depuis Mastermind.

## 10. Répartition du code

| Zone | Modification |
|---|---|
| `models.py` | Corpus facultatif pour la conception. |
| `prompts.py`, `framing.py`, `workflow.py` | Type et livrable d'étape transmis à F/A/B ; cadrage de transition. |
| `facade.py` | Mandat complet, sources et paramètres hérités ; opérations partagées de mission. |
| Nouveau `mission.py` | Registre, chemins, rattachement et inspection ; aucune exécution IA. |
| `cli.py`, `framing_cli.py` | Options de mission et transition avec cadrage ; compatibilité des commandes. |
| GUI accueil, création, suivi, contrôleur, récents | Navigation d'une mission et reprise d'une étape existante. |
| GUI Runner et `runner_session.py` | Préparation lisible, paramètres persistants et actions de reprise/revue. |
| Runner `core.py`, `gui_bridge.py`, CLI | Projet neuf, inspection WSL, transport du paquet et du candidat, intégration explicite. |
| `development.py` | Réemploi export/paquet/revue/vérification ; adapter seulement les raccords nécessaires. |

Les fonctions de registre sont testables sans Tk. Les opérations Git restent dans le Runner.
Les vues présentent les actions et diagnostics de la façade. Aucune dépendance de production,
base de données, tâche planifiée ni nouveau service.

## 11. Lots et validation

| Lot | Livrable vérifiable |
|---|---|
| 1 — Contrat des étapes | Conception sans corpus, F/A/B cohérents, mandat et corpus de transition complets. |
| 2 — Mission et navigation | Création/rattachement, affichage commun, reprise sans doublon, Mastermind regroupé. |
| 3 — Préparation et reprise Runner | Nouveau projet, validations éditables, référence persistante et reprises après incident. |
| 4 — Revue et livraison | Paquet rapatrié, revue liée, transport Git et intégration explicite du candidat exact. |

Le cadrage complémentaire de transition appartient au lot 1. Chaque lot comprend ses adaptations
CLI, GUI et documentation, avec revue selon les règles du projet. Ne pas déclarer le parcours
complet tant que la remise du code du lot 4 n'est pas éprouvée.

Critères d'acceptation :

| ID | Scénario et résultat attendu |
|---|---|
| AC01 | Une conception sans corpus se crée et tourne, avec ou sans F. |
| AC02 | Une recherche sans web ni corpus reste refusée avant appel. |
| AC03 | La conception issue d'une recherche reçoit demande, résultat, bilan et décision exacts ; son mandat est complet. |
| AC04 | Une acceptation périmée ou modifiée pendant préparation empêche la transition ; aucun mélange de versions. |
| AC05 | Le cadrage complémentaire lit l'instantané transmis ; la création conserve ce même corpus. |
| AC06 | Les prompts distinguent projet et étape ; les hypothèses restent explicitement des hypothèses. |
| AC07 | Deux clics et une réouverture retrouvent la même conception ; aucune seconde collaboration implicite. |
| AC08 | Une mission historique à la racine fonctionne ; Mastermind reprend depuis `Mastermind/conception`. |
| AC09 | Un échec d'inscription après création se répare par rattachement, sans appel repayé. |
| AC10 | Un nouveau projet produit une base Git puis un candidat dans le clone, sans écriture de l'agent dans le dépôt source. |
| AC11 | Dépôt occupé, identité Git absente ou outil requis absent donnent une erreur avant appel fournisseur. |
| AC12 | Export déjà publié, fermeture GUI et erreur de copie se reprennent à leur point utile, sans lancement automatique. |
| AC13 | Aucun secret ne figure dans les références persistantes, arguments de processus ou reçus. |
| AC14 | Le paquet copié garde son identité ; sa revue passe `dev-verify` avant décision. |
| AC15 | L'intégration exige une décision explicite, la revue applicable et la base attendue ; divergence ou fichiers locaux sont préservés. |
| AC16 | Une interruption après intégration reconnaît la tête déjà intégrée ; une correction produit paquet et revue distincts. |

Les tests de flux utilisent les faux agents et des dépôts jetables. Ajouter des tests GUI pour
le parcours proposé, au-delà de la présence des boutons. Les prompts se vérifient comme contrats ;
leur qualité réelle se mesure par la recette Mastermind, sans prétendre qu'un faux agent la prouve.

Recette finale : ouvrir Mastermind, poursuivre sa conception, traiter les arbitrages utiles,
accepter le plan, préparer le projet neuf, lancer le Runner, ouvrir et accepter la revue puis
intégrer explicitement. Lancer le jeu selon la conception et vérifier une victoire, une défaite,
les réglages et les cas de doublons retenus. Le PO déclenche les appels réels.

## 12. Taille, documentation et sortie

Le relevé précédent est de 2 216 lignes effectives pour façade + GUI, sur un plafond de 2 400 ;
une vue reste limitée à 400. Cette marge ne vaut pas estimation de faisabilité du présent périmètre.
Mesurer avant et après chaque lot, mutualiser les formulaires et remplacer les parcours existants.
Si le périmètre exige de dépasser un plafond, présenter le relevé et le besoin avant dépassement ;
ne pas déplacer artificiellement du code pour contourner la métrique. Aucun nouveau plafond
n'est déduit de l'acceptation des orientations fonctionnelles.

Mettre à jour `TYPES_DE_MISSION.md`, `CLAUDE.md`, les règles, README, aide CLI et documentation
de prise en main et du Runner au fil des lots. Le plan PWF reste l'unique suivi d'avancement.
Les anciennes décisions restent datées avec leur remplacement, sans effacer l'historique.

Le travail est terminé quand les deux parcours fonctionnent, que Mastermind est repris dans son
dossier, que les tests et la recette ci-dessus sont vérifiés, et que le code examiné peut être
remis au bon emplacement par une action explicite. Un paquet affiché seul ne clôt pas ce parcours.

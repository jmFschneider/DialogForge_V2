> Ce document n'est pas approuvé : sa présence prouve que le cycle s'est achevé, rien de plus.
> Revue B : CONSULT · constats restés ouverts : 2 (dont 0 BLOCKING) · corpus figé le 2026-09-23.
> Version examinée par B (`echanges/0006-revision-2-A.md`), livrée sans réécriture : plafond de 1 révision(s) atteint. Voir `bilan.md`.


# IAbinome — conception de la phase de cadrage avec agent

> Conception pour DialogForge V2, fondée exclusivement sur l’instantané local du 2026-09-23 et sur les décisions explicites de la présente demande.
>
> La présente version exige pour F une session persistante pendant tout un cadrage. Cette capacité sort donc volontairement du socle commun actuel des adaptateurs A/B.

## 1. Décision

DialogForge ajoute, avant la création d’une collaboration, un cadrage conversationnel facultatif conduit par un agent F.

F :

- travaille dans une session persistante propre au cadrage ;
- reçoit une copie isolée des fichiers sélectionnés, jamais le projet original ;
- consulte le projet utile au premier tour et conserve ce contexte pendant l’échange ;
- pose un seul arbitrage principal à la fois ;
- accepte les réponses libres, hésitations, corrections et retours en arrière ;
- propose périodiquement une première demande et la clôture ;
- rédige un brouillon dans les six sections canoniques au sein de la même session.

L’utilisateur :

- peut continuer après une proposition de clôture ;
- peut corriger un point et reprendre le cadrage ;
- peut demander la clôture à tout moment ;
- relit et corrige le brouillon avant la création de la collaboration ;
- confirme seul le texte qui deviendra `demande.md`.

La collaboration n’est créée qu’après cette confirmation. Ses empreintes initiales correspondent donc au texte relu.

`demande.md` reste la seule autorité du cycle A/B. La transcription, l’état de travail de F, les traces d’appels et la session fournisseur sont non normatifs et ne sont jamais transmis à A ou B.

Le cadrage :

- n’ajoute aucune phase à `etat.json` ;
- ne modifie pas le workflow A/B ;
- ne fait intervenir ni B ni un agent de relecture ;
- ne possède ni worker, ni base, ni reprise automatique, ni budget interne ;
- exige une session persistante uniquement pour F ;
- reste indépendant d’un fournisseur particulier : tout adaptateur qui satisfait le contrat de session peut être utilisé.

La session persistante de F est une exception explicite à l’exclusion portée par `CONCEPTION_FINALE.md` pour le noyau A/B. Elle ne modifie pas le contrat des appels de A et B.

## 2. Parcours utilisateur

### 2.1 Voies disponibles

La CLI `dialogforge new` offre trois voies exclusives :

```text
--demande FICHIER
--cadrer
--cadrer-avec-agent
```

- `--demande` importe une demande existante, sans appel.
- `--cadrer` conserve le questionnaire local actuel, sans appel de modèle.
- `--cadrer-avec-agent` ouvre une conversation avec F.

La GUI conserve la saisie et l’import et ajoute « Cadrer avec un agent ».

Une idée déjà suffisamment rédigée peut emprunter une voie sans F et ne paie aucun appel supplémentaire.

L’aide actuelle de `new`, « créer une collaboration (aucun appel d’agent) », devient :

```text
créer une collaboration ; le cadrage avec agent peut effectuer des appels avant la création
```

Les aides de `--demande` et `--cadrer` précisent qu’elles n’effectuent aucun appel.

### 2.2 Sources données à F

Les entrées de lecture du cadrage sont facultatives :

```text
--source-root DOSSIER --source-list MANIFESTE [--source-label TEXTE]
```

Elles conservent leurs contrôles actuels. Le cadrage réutilise la construction de corpus existante :

1. résolution des fichiers sous la racine autorisée ;
2. refus des fichiers non réguliers et des liens symboliques ;
3. copie dans un dossier temporaire ;
4. production d’un manifeste à chemins logiques ;
5. calcul des empreintes ;
6. présentation à F de la copie sous `corpus/fichiers/`.

Le cadrage sans projet ni corpus est permis pour une mission de conception. F travaille alors à partir de l’idée et de la conversation et signale l’absence de source locale.

Pour une mission de recherche, l’exigence actuelle d’un corpus non vide demeure.

Les mêmes sources peuvent alimenter le cadrage puis devenir le corpus de la collaboration. La façade reçoit alors la copie préparée et son manifeste ; elle ne relit pas silencieusement le projet original après le cadrage.

### 2.3 Début de la conversation

La CLI demande :

```text
Décrivez votre idée, même incomplète.
Terminez par une ligne contenant uniquement un point.
```

Une idée vide est redemandée localement.

Le programme ouvre ensuite une session persistante de F et lui envoie l’idée, le contrat de cadrage et l’accès à la copie du corpus.

Chaque réponse conversationnelle de F est soit :

- `IABINOME:CADRAGE_QUESTION` ;
- `IABINOME:CADRAGE_PRET`.

Une question porte sur un seul arbitrage principal. Elle peut comporter deux ou trois choix relatifs à cet arbitrage.

L’utilisateur peut :

- répondre librement ou partiellement ;
- demander l’utilité de la question ;
- hésiter ou répondre à côté ;
- contredire une réponse antérieure ;
- revenir sur une décision ;
- saisir `/clore` ;
- saisir `/annuler`.

Le programme ne classe pas lexicalement les réponses ordinaires.

### 2.4 Convergence

La conversation est divisée en groupes de questions :

- le premier groupe contient au plus trois questions de F ;
- après toute proposition `CADRAGE_PRET` refusée, l’action « Continuer » ouvre un nouveau groupe contenant au plus deux questions ;
- l’action « Corriger un point » est une forme de continuation : la correction humaine constitue la première réponse du nouveau groupe, lequel peut donc contenir au plus une autre question avant une nouvelle proposition ;
- après `/clore`, aucun groupe n’est ouvert : la confirmation locale mène directement à la rédaction.

Le compteur dénombre les réponses humaines reçues dans le groupe courant :

- limite `3` pour le premier groupe ;
- limite `2` pour tous les groupes suivants ;
- une correction donnée depuis l’écran de proposition compte comme une réponse du nouveau groupe ;
- une demande purement locale d’annulation ou de clôture ne compte pas.

Après la réponse qui atteint la limite, l’appel suivant de F doit rendre `IABINOME:CADRAGE_PRET`.

Est donc non conforme :

- dans le premier groupe, une quatrième `CADRAGE_QUESTION` ;
- dans tout groupe suivant, une troisième `CADRAGE_QUESTION` ;
- après « Corriger un point », une deuxième nouvelle question avant la proposition, puisque la correction a déjà consommé une réponse du groupe.

Une sortie non conforme est conservée et affichée comme incident de protocole. Elle ne déclenche aucune relance automatique. L’utilisateur peut :

- relancer explicitement dans la même session ;
- clore avec l’état déjà disponible ;
- annuler.

Il n’existe pas de plafond global : l’utilisateur peut refuser plusieurs propositions et ouvrir autant de groupes qu’il le souhaite. Le repère impose seulement à F de matérialiser régulièrement une demande possible, conformément à P19.

### 2.5 Proposition de clôture

`IABINOME:CADRAGE_PRET` présente :

- le mandat compris ;
- un aperçu des six sections ;
- les contradictions éventuelles ;
- toutes les questions encore ouvertes ;
- l’effet possible de chaque inconnue.

La proposition n’écrit rien dans la collaboration et ne vaut jamais confirmation.

L’utilisateur choisit :

- continuer ;
- corriger un point ;
- rédiger le brouillon ;
- annuler.

« Continuer » demande une réponse libre qui devient le premier apport du nouveau groupe.

« Corriger un point » demande immédiatement la correction humaine. Cette correction est envoyée à F comme première réponse d’un nouveau groupe de limite deux.

`/clore` conduit à une confirmation locale, puis à la rédaction. F conserve les inconnues au lieu de les combler.

### 2.6 Rédaction et relecture

Après confirmation de la clôture, le programme demande à F, dans la même session persistante, de produire `IABINOME:DEMANDE`.

F dispose alors du contexte conversationnel complet de sa session. L’idée, la transcription et un état canonique ne sont pas réinjectés dans le prompt de rédaction. Cela évite à la fois leur retransmission et la perte silencieuse d’une réponse omise dans un résumé intermédiaire de F.

Le programme vérifie :

- le marqueur ;
- `# Demande` en tête ;
- les six sections canoniques, présentes une fois chacune ;
- Objectif et Livrable non vides ;
- l’absence de texte parasite hors protocole.

Une sortie invalide n’est jamais promue ni relancée automatiquement.

Une sortie valide est placée dans une zone de relecture avant création.

En CLI :

```text
Brouillon prêt.

[v] Valider et créer
[m] Modifier le texte
[c] Continuer le cadrage
[a] Annuler
```

`m` utilise la saisie multiligne interne. Le texte complet est remplacé par les lignes saisies jusqu’à une ligne contenant uniquement `.`. Le résultat est revalidé localement.

Aucun éditeur externe ni commande issue de F n’est lancé.

L’action `c` conserve la même session F, ouvre un nouveau groupe de limite deux et envoie l’instruction humaine suivante comme première réponse de ce groupe.

En GUI, le brouillon remplace le contenu de l’éditeur Demande. L’utilisateur le corrige normalement.

`create_collaboration()` n’est appelée qu’après validation humaine. Ainsi :

- `initial_demande_sha256` correspond au texte relu ;
- `etat.demande_sha256` correspond au même texte ;
- aucune modification postérieure non versionnée n’est requise ;
- le prévol de `run` reste inchangé.

La session F est fermée après la création réussie ou l’annulation.

## 3. Insertion CLI

### 3.1 Options

```text
dialogforge new COLLABORATION
  --cadrer-avec-agent
  --agent-cadrage ADAPTER
  [--model-cadrage MODELE]
  [--effort-cadrage NIVEAU]
  [--source-root DOSSIER --source-list MANIFESTE]
  [--source-label TEXTE]
  ...
```

Règles :

- les trois sources de demande sont mutuellement exclusives ;
- `--agent-cadrage` est requis avec `--cadrer-avec-agent`, sauf valeur résolue depuis les réglages ;
- F est configuré indépendamment de A et B ;
- modèle et effort suivent les règles de résolution déjà utilisées pour A et B ;
- les options propres à F sont refusées hors mode agent ;
- une mission de conception peut ne fournir aucune source ;
- les règles existantes du corpus de recherche restent inchangées ;
- l’adaptateur choisi pour F doit déclarer et implémenter la session persistante de cadrage.

### 3.2 Ordre

`new` effectue :

1. résolution des réglages ;
2. validation de A, B et F ;
3. sondage de l’adaptateur F ;
4. validation de sa capacité de session persistante ;
5. validation de la destination ;
6. validation et copie temporaire des sources ;
7. ouverture de la session F ;
8. conversation ;
9. rédaction dans la même session ;
10. relecture et correction humaines ;
11. confirmation ;
12. création atomique de la collaboration ;
13. fermeture de la session ;
14. affichage du chemin de `demande.md`.

Tous les refus déterministes précèdent l’ouverture de session et le premier appel fournisseur.

`Ctrl+C`, EOF ou `/annuler` avant la création :

- demande la fermeture de la session ;
- détruit le dossier temporaire après la fin ou l’échec borné de cette fermeture ;
- ne crée aucune collaboration.

Une fermeture de session défaillante est signalée mais ne déclenche ni worker ni nettoyage différé.

## 4. Insertion GUI V1

### 4.1 Écran de création

La zone Demande offre :

- Saisir ;
- Importer ;
- Cadrer avec un agent.

Le mode agent affiche :

- adaptateur F ;
- modèle et effort avancés ;
- sources facultatives ;
- idée de départ ;
- bouton « Commencer le cadrage ».

A et B restent indépendants de F.

### 4.2 Dialogue

Une modale contient :

- la transcription affichée ;
- le champ de réponse ;
- Envoyer ;
- Clore maintenant ;
- Annuler.

La conversation et la session restent possédées par le contrôleur et associées au dossier temporaire. Elles ne constituent pas encore une collaboration.

Fermer la fenêtre équivaut à demander une annulation, avec confirmation si une session est ouverte.

### 4.3 Fil d’exécution

L’ouverture, chaque échange et la fermeture de la session F utilisent l’unique fil moteur déjà possédé par le contrôleur :

- le fil Tk n’appelle jamais directement l’adaptateur ;
- le contrôleur refuse un cadrage si son fil moteur est occupé ;
- chaque opération produit des événements dans la file existante ;
- Tk applique ces événements par son mécanisme de sondage ;
- les contrôles d’envoi et de clôture sont désactivés pendant une opération ;
- aucun appel de F, A ou B ne peut commencer simultanément ;
- entre deux tours, le fil moteur est libre, mais le contrôleur reste propriétaire exclusif de la session F ouverte.

Aucun deuxième worker, fil moteur, bail ou ordonnanceur n’est introduit.

### 4.4 Création et démarrage

Après rédaction, la modale se ferme et le brouillon apparaît dans l’éditeur existant.

Les actions « Créer seulement » et « Créer et démarrer » restent disponibles. AC-14 demeure applicable : « Créer et démarrer » distingue la création locale du premier appel de A.

Pour un brouillon issu du cadrage, la confirmation ajoute :

> Vous avez relu le texte qui deviendra `demande.md`. La création figera son empreinte. La poursuite lancera ensuite A.

La session F est fermée avant le lancement éventuel de A. F et A ne sont jamais actifs simultanément.

## 5. Isolation et capacités

### 5.1 Dossier de session

Le cadrage crée un seul dossier jetable pour toute sa durée :

```text
framing-<uuid>/
├── corpus/
│   ├── manifeste.json
│   └── fichiers/...
├── session.json
├── transcription.md
└── appels/...
```

Le même dossier sert de racine de travail à tous les échanges de la session F. Les sous-dossiers d’appel conservent les traces propres à chaque tour, mais ne créent pas de nouvelle session fournisseur.

Le projet original :

- n’est jamais le `cwd` de F ;
- n’est jamais nommé dans le prompt ;
- n’est jamais transmis par un chemin à F ;
- n’est jamais modifié par la phase.

Le prompt ne mentionne que `corpus/fichiers/`.

### 5.2 Prévol de F

F doit déclarer :

- `enforces_read_only`;
- `supports_persistent_framing_session`.

`fresh_session` ne peut pas être exigé avec son sens A/B d’« aucune session réutilisée entre deux appels », puisque les tours d’un cadrage doivent précisément partager une session.

La propriété exigée devient :

> Chaque cadrage ouvre une session neuve, jamais reprise d’un cadrage antérieur ; tous ses tours réutilisent cette seule session ; la session est fermée à la fin du cadrage.

Les adaptateurs A/B conservent leurs capacités et leur comportement actuels.

Un adaptateur dépourvu de `supports_persistent_framing_session` est refusé avant tout appel. Aucun fournisseur n’est sélectionné ou privilégié dans le noyau.

`enforces_read_only` reste une déclaration d’adaptateur, pas une preuve de confinement général. Le corpus précise que les drapeaux introduits par l’amendement du 2026-09-19 n’étaient pas encore mesurés en réel avant le lot 3. La conception n’emploie donc pas le terme « caractérisé » sans résultat de caractérisation ajouté ultérieurement.

### 5.3 Contrôle des sources

Les empreintes du corpus temporaire sont vérifiées :

- avant l’ouverture de session ;
- après chaque échange ;
- avant la promotion des artefacts.

Toute modification produit `SOURCES_MODIFIED`, interdit la promotion du brouillon et mène à la fermeture de la session.

Cette vérification détecte un changement ; elle ne constitue pas un confinement mécanique de la CLI.

## 6. Contrat de F

### 6.1 Session

L’adaptateur F expose une interface indépendante du fournisseur :

```python
class FramingSession(Protocol):
    def send(self, prompt: str, call_dir: Path) -> CompletedCall: ...
    def close(self) -> None: ...

class AgentAdapter(Protocol):
    ...
    def open_framing_session(
        self,
        spec: FramingSessionSpec,
        work_root: Path,
    ) -> FramingSession: ...
```

`FramingSessionSpec` contient :

- modèle effectif ;
- effort éventuel ;
- délai par échange ;
- finalité `FRAMING`.

L’identifiant fournisseur éventuel reste encapsulé dans l’adaptateur. Le noyau ne l’interprète pas et ne le persiste pas comme autorité.

La session :

- est créée après tous les prévols ;
- est possédée par une seule commande ou un seul contrôleur ;
- accepte un seul `send` à la fois ;
- n’est jamais reprise après la fin du processus ;
- n’est jamais utilisée par A ou B ;
- est fermée avant le démarrage du cycle A/B.

Il n’existe aucune reprise automatique après interruption. Recommencer `new` ouvre une nouvelle session et un nouveau cadrage.

### 6.2 Premier envoi

Au premier envoi, F reçoit :

- l’idée initiale ;
- l’instruction de consulter les fichiers utiles sous `corpus/fichiers/` ;
- l’interdiction d’écrire ou d’exécuter ;
- le contrat des sorties ;
- la limite du premier groupe, soit trois réponses humaines.

F doit conserver dans le contexte de session :

- les informations utiles lues dans le corpus ;
- les réponses humaines ;
- les corrections et contradictions ;
- les questions ouvertes ;
- les propositions déjà refusées.

### 6.3 Envois suivants

Les envois suivants ne rechargent ni l’idée, ni le corpus, ni la transcription, ni un état canonique complet.

Ils contiennent seulement :

- la dernière réponse ou instruction humaine ;
- le numéro du groupe ;
- le nombre de réponses déjà reçues dans ce groupe ;
- la limite applicable ;
- le rappel du type de sortie désormais attendu lorsque la limite est atteinte.

L’état structuré rendu par F reste utile à l’affichage, aux contrôles et à la provenance, mais il n’est plus la seule mémoire du cadrage. Une omission dans cet état n’efface pas le contexte conversationnel de la session.

### 6.4 Sorties conversationnelles

Question :

```text
IABINOME:CADRAGE_QUESTION

QUESTION
Un seul arbitrage principal, éventuellement accompagné de choix.

POURQUOI
Effet de la réponse sur la future demande.

ETAT_CADRAGE
DECISIONS
- ...

HESITATIONS
- ...

CONTRADICTIONS
- ...

FICHIERS_CONSULTES
- chemin/logique

QUESTIONS_OUVERTES
- ...
```

Proposition :

```text
IABINOME:CADRAGE_PRET

RESUME
...

SANS_REPONSE
- Question : ...
  Effet possible : ...

APERCU
Objectif : ...
Livrable : ...
Sources : ...
Contraintes : ...
Non-objectifs : ...
Critères de fin : ...

ETAT_CADRAGE
...
```

Le parseur vérifie les marqueurs et sections. Il ne compte ni les points d’interrogation ni les éléments d’une liste d’alternatives.

### 6.5 Suffisance

F propose la clôture dès qu’il peut produire une demande autonome comprenant :

- un objectif identifiable ;
- un livrable principal ;
- les sources disponibles ou leur absence ;
- les contraintes et exclusions connues ;
- au moins un critère de fin observable ;
- les contradictions et inconnues restantes sans décision inventée.

Une inconnue peut subsister si elle est visible et assumée.

La règle mécanique de groupe prime sur ce jugement : lorsque la limite est atteinte, F doit proposer une version même imparfaite.

### 6.6 Rédaction

```text
IABINOME:DEMANDE
# Demande

## Objectif
...

## Livrable
...

## Sources
...

## Contraintes
...

## Non-objectifs
...

## Critères de fin
...
```

Le brouillon :

- est autonome ;
- n’invente aucune décision ;
- exploite l’ensemble du contexte conservé dans la session ;
- reprend les valeurs, formats et chemins logiques établis ;
- ne renvoie pas à la conversation ;
- ne mentionne pas F, A ou B ;
- ne répartit pas le travail entre agents ;
- décrit un livrable principal ;
- conserve les limites et désaccords non résolus.

## 7. Gabarits de prompt

### 7.1 Ouverture et premier envoi

```text
Tu es l'agent F de cadrage de DialogForge.

Cette conversation utilise une session persistante. Conserve pendant toute la
session les informations utiles lues et les réponses humaines. Elles ne seront
pas retransmises intégralement à chaque tour.

Transforme progressivement l'idée en demande autonome. Si corpus/fichiers/
contient des fichiers, lis maintenant ceux qui sont utiles. Il s'agit d'une
copie isolée : n'écris et n'exécute rien.

N'invente aucune décision. Une observation du corpus n'est pas un choix humain.
Pose un seul arbitrage principal, éventuellement avec deux ou trois
alternatives réelles.

Le premier groupe admet au plus trois réponses humaines. Lorsque sa limite est
atteinte, rends IABINOME:CADRAGE_PRET. Si l'idée suffit déjà, propose-la
maintenant.

IDEE
{idee}

GROUPE
1

REPONSES_DANS_LE_GROUPE
0

LIMITE_DU_GROUPE
3

CONTRATS
{contrats}
```

### 7.2 Tour conversationnel

```text
Continue le même cadrage en utilisant le contexte déjà conservé dans cette
session.

La réponse humaine peut être partielle, hésitante, hors sujet ou corriger une
décision antérieure. Mets ton état à jour sans inventer.

Si REPONSES_DANS_LE_GROUPE atteint LIMITE_DU_GROUPE, rends obligatoirement
IABINOME:CADRAGE_PRET. Sinon, pose le seul arbitrage le plus utile ou propose
la clôture immédiatement.

DERNIERE_REPONSE_OU_INSTRUCTION_HUMAINE
{reponse}

GROUPE
{groupe}

REPONSES_DANS_LE_GROUPE
{compteur}

LIMITE_DU_GROUPE
{limite}
```

Le premier groupe utilise `limite=3`. Tous les suivants utilisent `limite=2`.

### 7.3 Correction après proposition

```text
L'utilisateur refuse pour l'instant la clôture et corrige le point suivant.
Cette correction est la première réponse d'un nouveau groupe de limite deux.

CORRECTION_HUMAINE
{correction}

GROUPE
{groupe}

REPONSES_DANS_LE_GROUPE
1

LIMITE_DU_GROUPE
2

Mets à jour le cadrage. Tu peux poser au plus une nouvelle question avant de
rendre une nouvelle proposition IABINOME:CADRAGE_PRET.
```

### 7.4 Rédaction

```text
Rédige maintenant la demande autonome à partir de l'ensemble de cette session.

N'invente aucune décision. Conserve explicitement les inconnues, limites et
désaccords encore ouverts. Ne mentionne ni la conversation ni les agents.

Commence par IABINOME:DEMANDE et ne rends ensuite que le Markdown.

FORMAT
# Demande
## Objectif
## Livrable
## Sources
## Contraintes
## Non-objectifs
## Critères de fin
```

Ni la transcription ni un résumé complet ne sont renvoyés : ils sont déjà présents dans le contexte persistant.

## 8. Transport avant création

### 8.1 Espace temporaire

```text
framing-<uuid>/
├── session.json
├── transcription.md
├── corpus/
│   ├── manifeste.json
│   └── fichiers/...
└── appels/
    ├── 0001-<uuid>/
    │   ├── intention.json
    │   ├── prompt.txt
    │   ├── stdout.txt
    │   ├── stderr.txt
    │   ├── reponse_brute.txt
    │   └── resultat.json
    └── ...
```

Cet espace :

- n’est pas une collaboration ;
- ne contient pas `etat.json` ;
- n’utilise pas `current_call` ;
- n’est partagé par aucun autre processus DialogForge ;
- est possédé par la commande ou le contrôleur courant ;
- reste le même pendant toute la session ;
- est supprimé après annulation ou promotion réussie.

Il n’emploie pas le verrou de collaboration.

### 8.2 Primitives d’invocation

Le transport est séparé en trois niveaux :

```python
invoke_agent(invocation: AgentInvocation, call_dir: Path) -> CompletedCall
```

pour les appels éphémères A/B ;

```python
open_framing_session(
    adapter: AgentAdapter,
    spec: FramingSessionSpec,
    work_root: Path,
) -> FramingSession
```

pour ouvrir la session F ;

```python
send_framing_turn(
    session: FramingSession,
    prompt: str,
    call_dir: Path,
) -> CompletedCall
```

pour chaque tour de cette session.

Le suivi du processus, des flux, des délais, des plafonds de sortie et de la terminaison de l’arbre est factorisé dans des composants internes communs lorsque l’adaptateur le permet. La conception ne suppose toutefois pas qu’une session persistante soit techniquement équivalente à plusieurs lancements de processus.

Le workflow A/B conserve son verrou et `current_call`. Le cadrage reste hors collaboration.

### 8.3 Finalité technique

```python
class AgentPurpose(Enum):
    A = "A"
    B = "B"
    FRAMING = "FRAMING"
```

`default_model()` reçoit `AgentPurpose`. Les adaptateurs choisissent leur valeur par défaut sans que le noyau nomme un fournisseur.

`FRAMING` n’est pas ajouté à `etat.json`.

## 9. Artefacts après création

Après validation humaine, la création atomique produit :

```text
collaboration/
├── configuration.json
├── demande.md
├── provenance_demande.json
├── etat.json
├── cadrage/
│   ├── transcription.md
│   ├── provenance.json
│   └── appels/...
└── corpus/...
```

Pour les artefacts de cadrage :

- les prompts ne contiennent que `corpus/fichiers/` ;
- les manifestes portent des chemins logiques ;
- les chemins internes de provenance sont relatifs ;
- aucun chemin absolu du projet source n’est persisté.

Cette garantie est limitée au nouveau chemin de cadrage. Elle ne prétend pas corriger rétroactivement la voie existante `--demande`, qui enregistre actuellement `path.resolve()`.

### 9.1 Transcription

La transcription comporte :

- l’idée initiale ;
- chaque sortie affichée de F ;
- chaque réponse humaine ;
- les propositions de clôture ;
- les corrections ;
- la décision finale ;
- l’avertissement : « Historique non normatif ; seul `demande.md` fait autorité. »

### 9.2 Provenance du cadrage

```json
{
  "schema_version": 1,
  "agent": {
    "adapter_id": "opaque",
    "model": "effectif",
    "effort": null
  },
  "session": {
    "persistent": true,
    "new_for_this_framing": true,
    "resumable": false
  },
  "sources": {
    "provided": true,
    "label": "libellé",
    "manifest_sha256": "..."
  },
  "closure": "AGENT_PROPOSED",
  "turn_count": 4,
  "exchange_count": 5,
  "open_questions": [],
  "transcription_sha256": "...",
  "agent_draft_sha256": "...",
  "accepted_demande_sha256": "...",
  "human_edited": true
}
```

Aucun identifiant brut de session fournisseur n’est requis. S’il apparaît dans une trace brute imposée par l’outil, l’adaptateur doit le traiter selon les mêmes règles de secret que les autres données techniques de l’appel.

### 9.3 Provenance de `demande.md`

Le schéma actuel de `provenance_demande.json` reste en version 1.

```json
{
  "sequence": 1,
  "source": "cadrage",
  "path": null,
  "sha256": "...",
  "method": "agent",
  "framing_provenance": "cadrage/provenance.json",
  "agent_draft_sha256": "...",
  "human_edited": true
}
```

- `agent_draft_sha256` désigne la sortie validée de F avant édition.
- `sha256` désigne le texte humainement accepté.
- si les empreintes sont identiques, `human_edited` vaut `false`.

### 9.4 Configuration

`configuration.json` peut ajouter :

```json
{
  "framing_agent": {
    "adapter_id": "opaque",
    "model": "effectif",
    "effort": null,
    "persistent_session": true
  }
}
```

Les anciennes collaborations restent valides en l’absence de ce bloc. Le moteur A/B l’ignore.

## 10. Architecture

Ajouter `framing.py` pour :

- le cycle de vie de la session ;
- les prompts ;
- le protocole conversationnel ;
- le compteur de groupe ;
- la validation des marqueurs ;
- la transcription ;
- la préparation des artefacts.

Ajouter dans `prompts.py` :

- `build_framing_start`;
- `build_framing_continue`;
- `build_framing_correction`;
- `build_framing_draft`.

Ajouter dans `demande.py` :

```python
validate_framed(text: str) -> list[str]
```

Étendre les adaptateurs avec :

```python
supports_persistent_framing_session: bool
open_framing_session(...)
```

Étendre `CreationRequest` :

```python
framing: FramingArtifacts | None = None
prepared_corpus: PreparedCorpus | None = None
```

`create_collaboration()` :

- valide les empreintes ;
- écrit le texte humainement accepté ;
- copie les artefacts relatifs ;
- écrit configuration et état ;
- publie le dossier atomiquement.

Elle ne conduit pas la conversation et ne possède pas la session F.

## 11. Coût et différence avec V1

Soit :

- `q` le nombre de questions ;
- `p` le nombre de propositions de clôture ;
- `r` le nombre de demandes de rédaction ;
- `s` le nombre de sessions de cadrage.

Un cadrage normal utilise :

```text
s = 1
échanges dans la session = q + p + r
```

La facturation exacte dépend du fournisseur : certains comptent des messages, d’autres des tours ou la croissance du contexte. DialogForge ne calcule ni tokens ni coût monétaire.

Exemples :

- idée immédiatement suffisante : une session, deux échanges (`PRET`, `DEMANDE`) ;
- deux questions : une session, quatre échanges ;
- quatre questions en deux groupes : une session, sept échanges si deux propositions sont produites ;
- `/clore` avant l’ouverture de session : une session et un échange de rédaction ;
- relance explicite d’une sortie mal formée : un échange supplémentaire dans la même session.

Par rapport au cadrage V1 :

- une seule session est ouverte ;
- le projet est consulté dans cette session et n’est pas redemandé à chaque tour ;
- l’idée et la transcription complète ne sont pas retransmises ;
- les réponses restent dans le contexte conversationnel ;
- F doit proposer un brouillon après trois réponses, puis tous les deux apports humains ;
- la rédaction utilise la même session ;
- B ne relit jamais le cadrage ;
- l’utilisateur peut clore ou annuler à chaque tour.

Cette conception traite directement la fuite de tokens liée aux ouvertures et rechargements successifs. Elle ne garantit toutefois aucun ratio de réduction par rapport aux 229 288 tokens mesurés en V1 : une session persistante peut continuer à facturer tout ou partie de son contexte cumulé selon l’outil. Seul un essai comparable permettrait de mesurer le gain.

La porte `IABINOME:QUESTION` actuelle coûte au minimum :

- un premier appel éphémère de A ;
- un nouvel appel éphémère de A après complément.

Le cadrage déplace les clarifications avant la création, dans une unique session de F. Les voies sans F restent à zéro appel avant A/B.

## 12. P14 à P20, R7 et X14

| Leçon | Décision |
|---|---|
| P14 | Reprise : une observation ou suggestion de F ne devient jamais une décision humaine. |
| P15 | Reprise : A et B ne lisent que `demande.md`. |
| P16 | Reprise : un seul livrable principal, sans répartition entre agents. |
| P17 | Reprise : un arbitrage principal par `CADRAGE_QUESTION`; les alternatives restent dans cet arbitrage. |
| P18 | Reprise : toute proposition expose les questions sans réponse et leurs effets. |
| P19 | Reprise renforcée : proposition obligatoire après trois réponses dans le premier groupe, puis après deux dans chaque groupe suivant. Une correction après proposition compte comme première réponse du nouveau groupe. |
| P20 | Reprise : alternatives ciblées lorsqu’elles sont étayées ; aucune alternative inventée pour satisfaire la forme. |
| R7 | Le cadrage est un coût préalable distinct. Il est décrit en sessions et échanges, sans budget interne. |
| X14 | B est entièrement exclu du cadrage, sans option dormante. |

## 13. Plafonds de code

Trois valeurs doivent être distinguées :

- `GUI_V1.md` conserve dans le corpus un plafond de 1 200 lignes logiques pour façade, contrôleur et vues, avec environ 1 000 lignes après le lot 4 ;
- la présente demande du PO porte ce plafond à 2 000 et estime la surface actuelle à environ 1 195 ;
- l’amendement du 2026-09-23 porte la croissance nette maximale de `src/` à +2 500 lignes depuis le début de la phase 5.

Après le lot 4, +1 046 lignes étaient déjà consommées. La marge documentaire restante était donc :

```text
2 500 - 1 046 = 1 454 lignes
```

Cette marge est celle constatée après le lot 4, avant toute évolution ultérieure non visible dans l’instantané. L’implémentation doit refaire la mesure sur son état de départ.

`framing.py`, les extensions d’adaptateurs, le transport de session, la façade et la GUI sont comptés dans cette croissance.

Les plafonds sont des contraintes de livraison du code, pas des budgets d’exécution.

## 14. Tests avec `fake`

Le `fake` implémente une session persistante entièrement locale. Aucun fournisseur réel n’est lancé.

### 14.1 Session et isolation

1. Un cadrage ouvre exactement une session fake.
2. Tous ses tours utilisent le même identifiant fake en mémoire.
3. Deux cadrages successifs utilisent deux sessions distinctes.
4. Une session terminée ne peut pas être reprise.
5. F reçoit comme racine le dossier jetable du cadrage.
6. Ce dossier ne contient que la copie sélectionnée sous `corpus/fichiers/`.
7. Aucun chemin absolu de la source ne figure dans les prompts ou artefacts promus.
8. Un adaptateur sans `enforces_read_only` est refusé avant ouverture.
9. Un adaptateur sans `supports_persistent_framing_session` est refusé avant ouverture.
10. Une modification du corpus temporaire produit `SOURCES_MODIFIED`.
11. Le cadrage sans source est accepté en conception.
12. Le corpus reste obligatoire en recherche.
13. Annulation, EOF et interruption tentent de fermer la session.
14. Aucun mécanisme de reprise différée n’est créé.

### 14.2 Mémoire conversationnelle

15. L’idée n’apparaît que dans le premier prompt.
16. L’instruction de consulter le corpus n’apparaît que dans le premier prompt.
17. Les prompts suivants ne retransmettent pas la transcription.
18. Le fake conserve une réponse humaine d’un tour à l’autre.
19. Une correction remplace la décision courante sans effacer la transcription.
20. La rédaction peut reprendre une réponse absente du dernier `ETAT_CADRAGE`, parce qu’elle demeure dans la session.
21. Une sortie `QUESTION` peut contenir des alternatives.
22. Le parseur ne compte pas les points d’interrogation.

### 14.3 Convergence

23. Le premier groupe a une limite de trois.
24. Après trois réponses, le prompt impose `CADRAGE_PRET`.
25. Une quatrième question dans le premier groupe est non conforme.
26. Après refus d’une proposition, le groupe suivant a une limite de deux.
27. Une troisième question dans un groupe suivant est non conforme.
28. « Corriger un point » ouvre un groupe de limite deux.
29. La correction compte comme première réponse de ce groupe.
30. Après cette correction, F peut poser au plus une question avant `CADRAGE_PRET`.
31. Continuer sans correction fait de la réponse suivante le premier apport du groupe.
32. Les groupes peuvent être répétés sans plafond global.
33. Une proposition ne clôt jamais sans décision humaine.
34. `/clore` n’ouvre aucun nouveau groupe.
35. `/annuler`, EOF et interruption ne créent aucune collaboration.

### 14.4 Rédaction et relecture

36. La rédaction est un échange distinct dans la même session.
37. Une sortie valide contient les six sections.
38. Objectif ou Livrable vide est refusé.
39. Une sortie sans marqueur n’est pas promue.
40. Aucune relance automatique n’a lieu.
41. Une correction CLI est appliquée avant `create_collaboration()`.
42. Une correction GUI est appliquée avant `create_collaboration()`.
43. Les empreintes initiales correspondent au texte corrigé.
44. Aucune modification manuelle post-création n’est nécessaire.
45. Revenir au cadrage après le brouillon conserve la session.
46. « Créer et démarrer » conserve sa confirmation distincte.

### 14.5 Transport

47. Les traces de chaque échange s’écrivent sous le même espace temporaire.
48. Aucun `etat.json` ni `current_call` n’est créé pour le cadrage.
49. Le workflow A/B conserve son verrou et son transport éphémère.
50. `AgentPurpose.FRAMING` obtient un modèle par défaut chez chaque fake compatible.
51. Une annulation supprime le dossier temporaire après fermeture.
52. Une création réussie copie les appels sous `cadrage/appels/`.
53. Un échec de création ne laisse aucun dossier final partiel.
54. La session F est fermée avant tout lancement de A.

### 14.6 Autorité et provenance

55. A reçoit `demande.md` et jamais la transcription.
56. B ne reçoit aucun artefact de cadrage.
57. La source persistée reste `cadrage`.
58. Le brouillon non modifié porte deux empreintes identiques.
59. Le brouillon modifié porte `human_edited: true`.
60. Les liens de provenance sont relatifs.
61. Le schéma de provenance reste en version 1.
62. Une collaboration sans cadrage reste lisible.
63. La provenance indique une session persistante non reprenable.
64. Aucun identifiant fournisseur n’est nécessaire au fonctionnement ultérieur.

### 14.7 GUI

65. L’ouverture et les échanges de F ne bloquent pas le fil Tk.
66. Le contrôleur n’autorise qu’un fil moteur.
67. Un cadrage est refusé pendant une autre exécution possédée par la GUI.
68. Les contrôles sont désactivés pendant chaque opération de session.
69. Les événements passent par la file existante.
70. Le brouillon revient dans l’éditeur existant.
71. Les deux actions de création existantes restent disponibles.
72. La fermeture de la modale demande l’annulation de la session.

### 14.8 Coût et absence d’effets fournisseurs

73. `PRET`, `DEMANDE` produit une session et deux échanges.
74. `QUESTION`, `QUESTION`, `PRET`, `DEMANDE` produit une session et quatre échanges.
75. Continuer puis accepter une seconde proposition conserve la même session.
76. `exchange_count` correspond aux dossiers d’appel promus.
77. Aucun token, coût monétaire, quota ou réservation n’est calculé.
78. Toute la suite utilise `fake`.
79. Aucun processus fournisseur réel n’est lancé.
80. Une commande ou un patch rendu par F reste du texte.
81. Aucune réponse de F ne devient un chemin, un `argv` ou une opération de fichier.
82. Les adaptateurs incompatibles sont refusés, plutôt que simulés par plusieurs sessions éphémères.

## 15. Critères d’acceptation

La phase est livrable lorsque :

1. les voies existantes restent disponibles ;
2. l’aide de `new` indique que le mode agent peut effectuer des appels ;
3. F est paramétré indépendamment de A et B ;
4. l’adaptateur F maintient une session neuve pendant tout le cadrage ;
5. aucun rechargement complet de l’idée, du corpus ou de la transcription n’a lieu entre les tours ;
6. les sources sont copiées dans un dossier isolé ;
7. aucun chemin absolu du projet n’est persisté par le cadrage ;
8. le cadrage sans source est possible en conception ;
9. F accepte les réponses libres et les corrections ;
10. le premier groupe est limité à trois réponses ;
11. tous les groupes suivants sont limités à deux réponses ;
12. une correction après proposition compte comme première réponse du groupe suivant ;
13. l’utilisateur garde seul la décision de clôture ;
14. la rédaction utilise la même session que la conversation ;
15. la relecture précède la création ;
16. les empreintes initiales correspondent au texte relu ;
17. la GUI emploie son unique fil moteur ;
18. la session F est fermée avant A ;
19. `demande.md` est la seule entrée du cycle ;
20. la provenance distingue le brouillon de F du texte accepté ;
21. P14 à P20, R7 et X14 sont couverts ;
22. le coût est décrit comme une session et `q + p + r` échanges ;
23. aucun ratio de tokens non mesuré n’est promis ;
24. aucun des cinq interdits n’est contourné ;
25. la surface façade/GUI reste sous 2 000 lignes logiques ;
26. la croissance nette de `src/` reste sous +2 500 lignes depuis le début de la phase 5 ;
27. la marge est remesurée avant livraison ;
28. les tests n’appellent aucun fournisseur réel.

---

## Amendements du PO — 2026-09-24, avant l'implémentation

> Copie octet pour octet, jusqu'à la ligne qui précède ce titre, du livrable de la collaboration
> `C:\Projets\essais-3-1\Creation-prompt-2` (sha256 `03711c71…935cdd`), accepté par le PO le
> 2026-09-24 (`decisions.json`, séquence 2). Les deux constats restés ouverts et le mécanisme de
> session sont tranchés ici ; le texte qui précède n'est pas réécrit.

**A1 — `B-convergence-003` : l'apport libre de « Continuer » compte.** Le compteur d'un groupe
dénombre les réponses humaines, sans exception : après une proposition refusée, « Continuer » et
« Corriger un point » ouvrent le même groupe de limite 2, et le texte humain qui l'ouvre en est la
première réponse. F peut donc poser **au plus une question** avant la proposition suivante, dans les
deux cas. Se lisent ainsi : §2.4 (« au plus deux questions » devient « au plus une question après
l'apport qui ouvre le groupe »), §2.5, test 27 (est non conforme : une deuxième `CADRAGE_QUESTION`
dans un groupe suivant), test 31.

**A2 — `B-cout-004` : `/clore` avant le premier échange.** Si l'utilisateur clôt avant que F ait
répondu une seule fois, le programme ouvre la session et envoie **un seul échange** : le premier envoi
(§7.1 — idée, consultation du corpus, contrats) suivi de la consigne de rédaction (§7.4). F n'a
jamais à rédiger sans l'idée. L'exemple du §11 compte donc une session et un échange.

**A3 — Session persistante : reprise par identifiant.** L'adaptateur tient la session de F en
relançant l'outil **à chaque tour sur la même session fournisseur** (reprise par identifiant), et non
par un processus maintenu ouvert. Les deux outils le permettent ; le transport existant (délai dur,
flux bornés, terminaison de l'arbre) sert tel quel à chaque tour. Le §8.2 l'autorisait (« la
conception ne suppose pas qu'une session persistante soit techniquement équivalente à plusieurs
lancements de processus ») ; ce choix le fixe. Conséquences :
- « fermer la session » = le programme oublie l'identifiant et refuse tout envoi ultérieur ; la
  trace que l'outil garde de sa propre session dans le profil de l'utilisateur n'est ni lue ni
  reprise par DialogForge ;
- l'identifiant de session reste encapsulé : il est masqué dans `intention.json` et jamais écrit
  dans une provenance ;
- la lecture seule de chaque outil **en reprise** est une déclaration de l'adaptateur, à
  caractériser en réel par le PO avant usage (lot 4 du plan), comme au lot 3.

**Choix d'implémentation, qui découle de A3 (ce n'est pas une décision du PO, il reste contestable)** :
`invoke_agent` n'est pas extrait du moteur A/B. Les tours de F appellent directement le transport
commun (`transport.run`), et le workflow A/B n'est pas touché (§8.2 : il conserve son verrou et
`current_call`).

## Amendement du PO — 2026-09-25, après le lot 4

**A4 — Sens de `open_questions` et liste vide explicite.** Trouvé par les deux cadrages réels du
lot 4 (`reference/PROTOCOLE_CADRAGE_LOT4.md`, partie 2) : le champ reprenait le `SANS_REPONSE` de la
dernière proposition, même après une reprise du cadrage, et citait des questions déjà répondues.
- **Sens** (§9.2) : `open_questions` est ce qui reste ouvert **selon F au moment de la clôture** —
  le bloc `QUESTIONS_OUVERTES` de l'état de cadrage du dernier tour conversationnel réussi, question
  ou proposition. Libellés courts, sans l'effet possible, qui reste dans la transcription et le
  brouillon. Retenu contre « vider la liste à la reprise », qui aurait écrit `[]` dans les deux
  traces alors que le brouillon listait deux inconnues.
- **Contrat de F** (§6.4, §7) : une liste vide s'écrit `- AUCUNE`, pour les cinq rubriques de
  `ETAT_CADRAGE`. Avant A4, rien ne la définissait : Claude écrivait une puce nue, Codex
  `- Aucune.`.
- **Lecture** : `[]` **seulement** si le bloc porte la seule puce `AUCUNE` (casse et point final
  tolérés). Un bloc absent, vide, fait de puces nues, ou mêlant `AUCUNE` à d'autres puces est ambigu :
  la valeur précédente est conservée. L'en-tête est reconnu avec ou sans deux-points ; le bloc
  s'arrête à la rubrique suivante.
- **`null`** : tant que F n'a exprimé aucun bloc lisible — notamment `/clore` avant le premier
  échange (A2), où F rédige sans état de cadrage. `null` veut dire « non exprimé », jamais « rien
  d'ouvert ». Le schéma de §9.2 reste en version 1 ; aucun code ne relit le champ.
- **Limite** : la ligne ajoutée au contrat n'a pas encore été vue par un vrai outil ; son effet se
  constatera au prochain cadrage réel.

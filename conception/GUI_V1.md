> Ce document n'est pas approuvé : sa présence prouve que le cycle s'est achevé, rien de plus.
> Revue B : CONSULT · constats restés ouverts : 3 (dont 0 BLOCKING) · corpus figé le 2026-09-22.
> Version examinée par B (`echanges/0003-revision-1-A.md`), livrée sans réécriture : acceptée par B. Voir `bilan.md`.


# DialogForge V2 — conception fonctionnelle et technique de la GUI V1

**Statut :** conception révisée, directement implémentable  
**Périmètre :** interface locale de création, lancement, suivi et décision d’une collaboration unique  
**Corpus de référence :** instantané du 22 septembre 2026

## 1. Résumé

La GUI V1 est une application locale Tkinter/ttk à trois vues dans une même fenêtre :

1. **Accueil** — créer, ouvrir ou retrouver une collaboration récente.
2. **Nouvelle collaboration** — saisir ou importer une demande, configurer la collaboration, puis la créer seule ou la créer et la démarrer.
3. **Suivi** — observer les phases et l’appel courant, intervenir après un arrêt, lire le livrable et consigner la décision humaine.

La GUI et la CLI utilisent les mêmes dossiers, validations, transitions, verrou et preuves d’appel. La GUI n’écrit aucun fichier métier directement.

La progression repose exclusivement sur des faits :

- phase ;
- numéro de révision ;
- rôle actif ;
- état de l’appel ;
- activité locale effectivement observée ;
- temps écoulé ;
- dernière mise à jour ;
- prochaine action autorisée.

Aucun pourcentage ni temps restant n’est inventé.

L’exécution appartient au processus local. Fermer la GUI ne transfère jamais le cycle à un service ou à un worker. La V1 ajoute néanmoins au moteur un mécanisme coopératif de pause et d’interruption, car le `KeyboardInterrupt` actuel de la CLI ne peut pas commander une exécution placée dans un fil secondaire.

## 2. Faits et limites du moteur actuel

### 2.1 Faits conservés

- Une collaboration est un dossier autonome contenant notamment `demande.md`, `provenance_demande.json`, `configuration.json`, `etat.json`, `echanges/`, `appels/`, `livrables/` et éventuellement `corpus/`.
- `new` valide tout avant d’écrire et ne fait aucun appel fournisseur.
- `run` lance ou reprend le cycle et peut appeler les agents.
- Il n’existe ni worker, ni service, ni planificateur.
- Aucun appel interrompu ou incertain n’est rejoué automatiquement.
- Les statuts sont `READY`, `RUNNING`, `WAITING_HUMAN`, `INTERRUPTED`, `ERROR`, `AWAITING_APPROVAL` et `STOPPED`.
- Les phases sont `PROPOSAL_A`, `REVIEW_B`, `REVISION_A` et `CLOSED`.
- `RUNNING` ne prouve pas à lui seul qu’un processus est encore actif.
- Une acceptation ne modifie pas `AWAITING_APPROVAL`.
- Une décision est liée par empreintes à une version précise du livrable, de la revue et de la demande.
- `resume --reprocess` retraite localement une réponse conservée, mais la commande reprend ensuite le cycle et peut donc atteindre un nouvel appel.
- Le délai n’est pas stocké dans `configuration.json`. Il est résolu à chaque `run`, `resume` et `decide --correct`.
- Le transport actuel ne traite une interruption utilisateur que par `KeyboardInterrupt`.
- En cas de `STREAMS_UNCLOSED`, des fils démons de lecture peuvent survivre temporairement jusqu’à la fermeture réelle des flux.

### 2.2 Limites de preuve

Le corpus ne contient pas l’intégralité de la CLI, du workflow, du stockage, du verrou et des incidents. Les noms exacts des services proposés ci-dessous sont donc indicatifs.

Le contrat fonctionnel est normatif ; les signatures devront être ajustées au code complet sans créer une seconde autorité métier.

## 3. Principes obligatoires

### 3.1 Une collaboration et une exécution au maximum

La fenêtre ne pilote qu’une collaboration et qu’une commande mutante à la fois. La liste d’accueil peut montrer plusieurs dossiers, mais aucun gestionnaire multi-exécution n’est introduit.

### 3.2 Tkinter/ttk et bibliothèque standard

La référence est Tkinter/ttk avec `threading`, `queue`, `pathlib` et les modules existants. Aucun serveur local, framework web ou dépendance GUI externe n’est prévu.

### 3.3 Dossier comme source de vérité

La mémoire de la GUI ne fait jamais autorité sur le statut, la phase, la décision ou les actions permises. Avant toute mutation, la façade recharge le dossier sous les règles du moteur.

### 3.4 Façade commune CLI/GUI

La CLI et la GUI appellent une même façade applicative pour :

- charger et valider ;
- créer ;
- inspecter ;
- lancer ou reprendre ;
- répondre ;
- retraiter ou relancer ;
- corriger ;
- accepter ou arrêter.

La façade retourne des résultats structurés. La GUI ne déduit pas les transitions en analysant des phrases de terminal.

### 3.5 Confirmation au dernier point avant un appel possible

Toute commande susceptible d’atteindre un nouvel appel fournisseur exige une confirmation, y compris :

- démarrage ;
- reprise depuis `READY` ;
- reprise d’un `RUNNING` persistant ;
- réponse humaine suivie de reprise ;
- relance ;
- retraitement local suivi de reprise ;
- correction ciblée.

La confirmation distingue :

1. l’acte local éventuellement sans appel ;
2. la poursuite du cycle, qui peut appeler un agent.

### 3.6 Pas d’exécution autonome après fermeture

La GUI ne se masque pas et ne se détache pas pendant qu’elle possède une exécution. Une fermeture demande une pause ou une interruption, puis attend que la commande moteur ait rendu la main.

Des fils démons de drainage associés à `STREAMS_UNCLOSED` peuvent subsister temporairement. Ils ne doivent ni poursuivre le workflow, ni lancer un autre agent, ni empêcher la fermeture du processus. Leur présence et l’incertitude sur un éventuel descendant sont consignées comme incident.

## 4. Navigation

```text
Accueil
 ├── Nouvelle collaboration ──► Formulaire
 │                                ├── Créer seulement ──► Suivi / READY
 │                                └── Créer et démarrer ► Suivi / exécution
 ├── Ouvrir une collaboration ─────────────────────────► Suivi
 └── Collaboration récente ────────────────────────────► Suivi

Suivi
 ├── activité
 ├── intervention humaine
 ├── incident
 ├── décision à prendre
 ├── version acceptée
 └── arrêt définitif
```

Les vues remplacent le contenu de la même fenêtre. Il n’existe ni tableau de bord global, ni onglets permanents, ni console brute affichée par défaut.

## 5. Écran d’accueil

```text
┌───────────────────────────────────────────────────────────┐
│ DialogForge                                  [À propos]   │
│ A produit · B critique · vous décidez                     │
├───────────────────────────────────────────────────────────┤
│ [Nouvelle collaboration] [Ouvrir une collaboration…]     │
├───────────────────────────────────────────────────────────┤
│ Collaborations récentes                                   │
│ Nom              Situation              Mise à jour       │
│ Étude API        Intervention requise   il y a 12 min     │
│ Refonte import   Version acceptée       hier              │
│ Prototype cache  Prête                  18 sept.           │
│                                                           │
│ [Ouvrir] [Afficher dans le dossier]                       │
└───────────────────────────────────────────────────────────┘
```

### 5.1 Actions

- **Nouvelle collaboration** ouvre un formulaire vierge.
- **Ouvrir une collaboration** sélectionne un dossier et le soumet au chargeur partagé.
- **Ouvrir** charge la collaboration choisie sans l’écrire.
- **Afficher dans le dossier** utilise l’intégration native du système.

Un dossier illisible est nommé avec le diagnostic partagé. La GUI ne le répare pas.

### 5.2 Collaborations récentes

`list` et les récents répondent à deux besoins différents :

- `list <racine>` énumère toutes les collaborations sous une racine, sans index ;
- les récents doivent retrouver des dossiers ouverts à différents emplacements et les ordonner par usage récent.

La GUI conserve donc un fichier de préférences non métier contenant uniquement :

- chemins absolus ;
- date de dernière ouverture par la GUI ;
- taille maximale de la liste.

Le statut et la phase ne sont jamais mis en cache. Ils sont relus depuis chaque dossier.

Ce fichier :

- est écrit atomiquement ;
- peut être supprimé sans effet sur les collaborations ;
- n’est consulté par aucune commande métier ;
- ne devient ni une base ni un index du moteur.

Un dossier absent reste affiché comme « Dossier introuvable » jusqu’à son retrait de la liste.

## 6. Écran de création

```text
┌─ Nouvelle collaboration ──────────────────────────────────┐
│ Dossier                                                   │
│ [C:\Travail\collaborations\ma-collab________] [Choisir]  │
│                                                           │
│ Demande                                                   │
│ (●) Saisir  ( ) Importer un fichier                       │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ Objectif…                                            │ │
│ └───────────────────────────────────────────────────────┘ │
│ [Importer…]  Source affichée : saisie directe             │
│                                                           │
│ Type       (●) Conception  ( ) Recherche                  │
│ Agent A    [Codex ▼]       Agent B [Claude ▼]             │
│ Révisions maximales [2]                                   │
│                                                           │
│ Corpus de recherche                         [Ajouter…]     │
│ Racine […]  Liste […]  Nom […]                            │
│                                                           │
│ ▸ Réglages avancés de la collaboration                    │
│ ▸ Réglages du prochain lancement                          │
│                                                           │
│ [Annuler]            [Créer seulement] [Créer et démarrer]│
└───────────────────────────────────────────────────────────┘
```

Le bloc de corpus est absent en mode conception.

### 6.1 Champs principaux

| Champ | Présentation | Autorité |
|---|---|---|
| Dossier | chemin éditable et sélecteur | création partagée |
| Demande | texte visible, saisi ou importé | normalisation partagée |
| Type | conception ou recherche | `MissionKind` |
| Agent A/B | adaptateurs disponibles | registre partagé |
| Révisions | entier positif ou nul, défaut 2 | `Configuration` |
| Corpus | racine, liste, libellé ; recherche seulement | création partagée |

### 6.2 Provenance de la demande

La GUI n’étend pas le schéma de `provenance_demande.json` en V1.

- Une demande importée et laissée inchangée utilise la provenance existante **fichier**.
- Une saisie directe utilise le chemin existant **cadrage** : il désigne une demande composée interactivement sans modèle.
- Dès qu’un texte importé est modifié dans la GUI, la création le traite comme un **cadrage**, car le fichier initial n’est plus la source exacte du contenu créé.
- « Importé puis modifié » reste une indication visuelle de session ; cette mention n’est pas ajoutée au format persistant.

Le texte effectivement soumis est toujours visible avant création.

### 6.3 Réglages avancés de la collaboration

Ce bloc contient uniquement les valeurs figées dans `configuration.json` :

```text
Modèle A          [défaut de l’adaptateur]
Effort A          [non spécifié ▼]
Modèle B          [défaut de l’adaptateur]
Effort B          [non spécifié ▼]
Accès web         [ ] Autoriser pour A et B
Accès du critique (●) Consultation  ( ) Contexte seul
```

Un modèle vide signifie « défaut de l’adaptateur ». Un effort non spécifié n’est ni écrit ni transmis.

### 6.4 Réglages du prochain lancement

Le délai ne fait pas partie de la collaboration et n’est pas présenté comme tel :

```text
Réglages du prochain lancement
Fichier de réglages [C:\...\dialogforge.toml] [Choisir…] [Aucun explicite]
Délai effectif      [1800] secondes
Origine             fichier explicite / profil utilisateur / défaut programme
```

Règles :

- le sélecteur choisit un fichier explicite équivalent à `--config` ;
- l’absence de fichier explicite applique la résolution partagée, mais avec un répertoire de travail fixé et affiché ;
- la GUI ne dépend jamais silencieusement de son répertoire courant de lancement ;
- le répertoire de résolution est le parent du dossier de collaboration pour une action portant sur celle-ci ;
- avant chaque `run`, `resume` ou `decide --correct`, la façade résout de nouveau le fichier et le délai ;
- le dialogue de confirmation affiche le délai effectif et son origine ;
- une valeur saisie directement vaut surcharge de commande, équivalente à `--timeout` ;
- le délai n’est jamais écrit dans `configuration.json` ;
- « Créer seulement » n’utilise pas ce délai.

Pour obtenir exactement le même réglage en CLI et en GUI, l’écran indique le chemin explicite à transmettre à la CLI avec `--config`, ou la valeur à transmettre avec `--timeout`.

### 6.5 Validation

Deux niveaux existent :

1. aide locale : champ vide ou entier syntaxiquement invalide ;
2. validation autoritaire : même service que `new`, avec erreurs structurées.

Aucun dossier n’est publié avant validation complète. Après un refus, le formulaire reste intact et aucun dossier cible partiel ne demeure.

### 6.6 Créer seulement

1. Valider.
2. Exécuter la création partagée.
3. En cas de refus, rester dans le formulaire.
4. En cas de succès, afficher le suivi en `READY`.
5. Afficher « Collaboration créée — aucun appel fournisseur effectué ».

### 6.7 Créer et démarrer

Après validation, afficher :

```text
Créer et démarrer ?

La création du dossier est locale et ne consomme aucun quota.
La poursuite lancera ensuite le premier appel fournisseur.

Agent : Codex, rôle A
Phase : proposition initiale
Délai effectif : 1800 s
Origine : C:\...\dialogforge.toml

[Annuler] [Créer et lancer le premier appel]
```

Après confirmation :

1. créer la collaboration ;
2. basculer vers le suivi ;
3. lancer le cycle ;
4. si le lancement est refusé avant l’appel, conserver la collaboration valide en `READY`.

Une création réussie n’est jamais supprimée parce que le lancement suivant échoue.

## 7. Écran de suivi

```text
┌─ ma-collab ───────────────────────────────────────────────┐
│ En cours · A produit la proposition                       │
│ Tour initial · activité observée il y a 2 s · 01:24      │
│ Cette exécution dépend de cette fenêtre.                  │
├─ Progression ─────────────────────────────────────────────┤
│ ● Proposition A  ○ Critique B  ○ Révision A  ○ Clôture  │
│ Révision 0 sur 2                                          │
├─ Activité ────────────────────────────────────────────────┤
│ Appel 0001 · rôle A · commencé à 14:06:10                │
│ Appel fournisseur en cours. Aucune durée restante estimée.│
│ Dernier état du dossier : 14:07:32                        │
├─ Résultat ou action requise ──────────────────────────────┤
│ [contenu déterminé par l’instantané]                       │
├───────────────────────────────────────────────────────────┤
│ [Ouvrir le dossier] [Actualiser]               [Action]  │
└───────────────────────────────────────────────────────────┘
```

### 7.1 Phases

- `✓` : phase achevée d’après les documents persistés ;
- `●` : phase courante ;
- `○` : phase non atteinte ;
- `!` : phase arrêtée par une intervention ou un incident ;
- `—` : phase non applicable ou cycle clos.

`REVISION_A` affiche « Révision r sur N ». Une nouvelle `REVIEW_B` est présentée comme « Relecture B de la révision r ».

### 7.2 Activité honnête

| Observation | Texte affiché |
|---|---|
| Contrôleur GUI actif | « Exécution active dans cette fenêtre » |
| Appel `CALLING` et contrôleur actif | « Appel fournisseur en cours » |
| Réponse conservée | « Réponse reçue, traitement local en cours » |
| `RUNNING` sans exécuteur GUI connu | « État enregistré : appel en cours ou processus arrêté ; activité non prouvée » |
| Aucun nouvel état | « Aucun nouvel état observé depuis… » |
| `READY` | « Prête ; aucun appel en cours » |
| Arrêt | libellé propre au statut |

`pid.txt` ne suffit jamais à prouver qu’un processus approprié vit encore.

Le temps écoulé est calculé depuis `current_call.started_at` lorsqu’il existe, sinon depuis le début de la commande locale. Il ne représente pas une estimation.

### 7.3 Rafraîchissement

- Tkinter ne réalise aucun appel long.
- Un fil d’exécution unique appelle la façade.
- Les événements immuables passent par `queue.Queue`.
- La boucle Tk les consomme avec `after`.
- Un instantané en lecture seule est relu périodiquement pendant l’exécution et à la demande sinon.
- Un échec de lecture conserve le dernier instantané sûr et affiche l’échec.
- Aucun rafraîchissement ne déclenche d’écriture.

## 8. Actions par statut

| Statut | Présentation | Action principale | Coût à annoncer |
|---|---|---|---|
| `READY` | Prête ou mise en pause | Démarrer/Reprendre | le prochain appel peut consommer du quota |
| `RUNNING` | actif localement ou activité non prouvée | suivre, ou reprendre sous verrou | la récupération locale peut être suivie d’un nouvel appel |
| `WAITING_HUMAN` | réponse requise | Répondre et reprendre | la reprise peut appeler les agents |
| `INTERRUPTED` | appel inabouti | Relancer l’appel | nouvel appel potentiellement payant |
| `ERROR` | réponse reçue mais inexploitable | Retraiter puis reprendre | retraitement local sans appel ; poursuite possiblement payante |
| `AWAITING_APPROVAL`, sans acceptation applicable | cycle terminé, décision requise | Lire et décider | lecture/acceptation gratuites ; correction payante |
| `AWAITING_APPROVAL`, acceptée | version acceptée | aucune action principale | correction ultérieure possiblement payante |
| `STOPPED` | arrêt définitif | aucune | aucun appel possible |

### 8.1 `READY`

- Premier cycle : **Démarrer la collaboration**.
- Après pause : **Reprendre le cycle**.

La confirmation nomme l’agent, la phase, le délai effectif et précise que la commande peut atteindre un appel fournisseur.

### 8.2 `RUNNING`

Si la GUI possède l’exécution, elle n’offre aucune seconde reprise concurrente.

Si elle ouvre un `RUNNING` persistant sans exécuteur local connu :

- elle n’anime pas l’activité ;
- elle affiche l’incertitude ;
- elle propose **Analyser et reprendre localement**.

Cette action passe sous le verrou partagé. Elle peut récupérer localement un résultat déjà complet sans repayer cet appel, puis poursuivre le cycle et atteindre un appel suivant. La confirmation dit donc :

> DialogForge tentera d’abord la reprise locale à partir des preuves. Aucun appel incertain ne sera rejoué automatiquement. Si le cycle doit ensuite appeler un agent, ce nouvel appel peut consommer du quota.

La GUI ne convertit jamais automatiquement un `RUNNING` ancien en incident.

### 8.3 `WAITING_HUMAN`

Afficher :

- la question ou la revue bloquante ;
- la mention « votre réponse complète la demande » ;
- une zone multiligne ;
- **Répondre et reprendre** ;
- **Arrêter définitivement**.

La confirmation explique que l’écriture de la réponse est locale mais que la reprise peut appeler A ou B.

### 8.4 `INTERRUPTED`

Afficher :

- type et détail d’incident ;
- appel concerné ;
- qualification `non`, `peut-être`, `inconnu` ou `oui` ;
- rappel qu’aucune relance n’est automatique.

**Relancer l’appel** exige un motif et annonce un nouvel appel potentiellement payant.

### 8.5 `ERROR`

Afficher la réponse conservée et l’incident contractuel.

L’action principale est **Retraiter puis reprendre…**. Son dialogue distingue :

1. le retraitement de la réponse conservée, local et sans nouvel appel ;
2. la reprise automatique du cycle après réussite, susceptible d’appeler l’agent suivant.

Le motif est obligatoire.

La GUI ne promet pas « zéro appel pour toute la commande ». Les tests vérifient seulement qu’aucun appel n’a lieu pendant l’étape de retraitement elle-même et que tout appel ultérieur est précédé par la confirmation.

La relance de l’appel en erreur reste une action secondaire explicitement payante.

### 8.6 `AWAITING_APPROVAL` sans acceptation applicable

Afficher :

- « Cycle terminé — décision non encore prise » ;
- livrable ;
- bilan ;
- corrections principales ;
- objections ouvertes ;
- réserves humaines éventuelles.

Actions :

- **Accepter cette version** ;
- **Accepter avec réserves** ;
- **Demander une correction ciblée** ;
- **Arrêter définitivement**.

La correction ciblée annonce un tour supplémentaire au-delà du plafond et jusqu’à deux appels, A puis B.

### 8.7 `AWAITING_APPROVAL` avec acceptation applicable

Le statut moteur demeure `AWAITING_APPROVAL`, mais la présentation utilisateur devient un sous-état dérivé :

- libellé d’accueil : **Version acceptée** ou **Acceptée avec réserves** ;
- en-tête : « Décision finale consignée pour cette version » ;
- date, type de décision et empreinte abrégée ;
- aucune action principale ;
- lecture du livrable, du bilan et de la décision ;
- actions secondaires seulement si la façade confirme qu’elles restent autorisées : **Demander une nouvelle correction ciblée** et **Arrêter définitivement**.

Les boutons d’acceptation ne sont plus proposés. Rejouer la même acceptation reste une propriété idempotente du moteur, mais n’est pas une action utile de l’interface.

Si le livrable change et que l’acceptation ne s’applique plus, l’écran revient au sous-état « décision requise » avec :

> Décision antérieure — le livrable a changé depuis.

### 8.8 `STOPPED`

Lecture seule. Aucune reprise, réouverture ou duplication implicite.

## 9. Pause, interruption et fermeture

### 9.1 Prérequis moteur

Le mécanisme CLI actuel fondé sur `KeyboardInterrupt` ne suffit pas à une GUI dont le moteur s’exécute dans un fil secondaire.

La V1 exige donc une extension bornée du transport et du workflow :

```text
ExecutionControl
  pause_requested: Event
  interrupt_requested: Event
```

Le transport vérifie `interrupt_requested` dans sa boucle d’attente, termine l’arbre et retourne `INTERRUPTED_BY_USER`.

Le workflow vérifie `pause_requested` uniquement aux frontières sûres :

- avant de préparer un nouvel appel ;
- après la publication complète du résultat courant ;
- avant de passer à l’appel suivant.

La pause publie `READY`. Elle ne transforme pas un appel en succès et ne rejoue rien.

La CLI adapte son premier Ctrl+C en `pause_requested`, puis son second en `interrupt_requested`. Ainsi CLI et GUI utilisent le même mécanisme, au lieu de conserver deux modèles d’interruption.

Cette modification ne change ni les statuts, ni les preuves, ni les règles de reprise ; elle rend leur commande explicite et testable.

### 9.2 Fermeture hors exécution

La fenêtre ferme immédiatement sans mutation métier.

### 9.3 Fermeture pendant une exécution locale

```text
Une exécution est active dans cette fenêtre.

[Continuer à suivre]

[Terminer l’appel courant, mettre en pause, puis fermer]
La fenêtre reste ouverte jusqu’à la frontière sûre.

[Interrompre maintenant]
L’appel en cours a pu être payé.
```

La fermeture système ouvre ce dialogue.

Après interruption, la GUI attend le retour de la commande moteur et la publication du statut. Une borne de nettoyage doit empêcher l’interface d’attendre indéfiniment.

En cas de `STREAMS_UNCLOSED`, elle peut fermer après avoir affiché :

> Le cycle est arrêté, mais des flux d’un descendant peuvent rester ouverts temporairement. Ils ne déclencheront aucune poursuite ni aucun nouvel appel.

La promesse est l’absence de workflow ou de nouvel agent actif, pas l’absence absolue de tout fil démon de drainage.

## 10. Architecture technique

```text
CLI ─────────────┐
                 ▼
             Façade applicative ──► domaine existant ──► dossier
                 ▲
GUI Tkinter ─► contrôleur local
```

### 10.1 Façade commune

API indicative :

```python
create_collaboration(command) -> CreationResult
inspect_collaboration(path) -> CollaborationSnapshot
resolve_runtime_options(path, explicit_config, timeout_override) -> RuntimeResolution
run_collaboration(path, runtime, control) -> RunResult
answer_and_resume(path, answer, runtime, control) -> RunResult
retry_call(path, call_id, reason, runtime, control) -> RunResult
reprocess_and_resume(path, call_id, reason, runtime, control) -> RunResult
accept(path) -> DecisionResult
accept_with_reserves(path, reserves) -> DecisionResult
correct(path, text, runtime, control) -> RunResult
stop(path, reason=None) -> DecisionResult
list_collaborations(root) -> list[CollaborationSummary]
```

### 10.2 Actions structurées

Le Lot 1 doit remplacer la dépendance aux phrases de `decisions.next_action` et `incidents.action` par un vocabulaire partagé :

```text
ActionId:
  START
  RESUME
  ANSWER_AND_RESUME
  RETRY_CALL
  REPROCESS_AND_RESUME
  ACCEPT
  ACCEPT_WITH_RESERVES
  CORRECT
  STOP
  NONE

AllowedAction:
  id
  enabled
  reason_if_disabled
  local_step_without_provider
  may_call_provider_afterward
  required_inputs
  target_call_id
```

La CLI transforme ces structures en commandes textuelles. La GUI les transforme en boutons et confirmations.

Les fonctions textuelles existantes peuvent rester comme adaptateurs de compatibilité, mais ne sont plus la source des règles.

Tests obligatoires :

- parité des actions avant/après refactoring pour les sept statuts ;
- parité des textes CLI ;
- absence de table concurrente dans la GUI.

### 10.3 Instantané

```text
path, name
configuration
state
current_decision:
  kind
  applies_to_current_version
  at
  version_digest
incident
runtime_resolution:
  timeout
  source
execution_observation:
  owned_by_this_gui
  runner_alive
presentation:
  status_label
  phase_label
  activity_label
  allowed_actions
  readable_documents
```

Le sous-état « version acceptée » est dérivé de la décision courante applicable, pas ajouté à `etat.json`.

### 10.4 Contrôleur GUI

Le contrôleur possède :

- au plus un fil moteur ;
- une file d’événements ;
- un `ExecutionControl` ;
- le dernier instantané sûr ;
- la navigation ;
- les préférences non métier.

Il ne construit ni `etat.json`, ni incident, ni décision.

### 10.5 Concurrence CLI/GUI

- Toute mutation acquiert le verrou existant.
- La GUI recharge avant d’agir.
- Un verrou occupé produit un refus explicite.
- La GUI ne force jamais la prise de contrôle.
- Un changement externe provoque l’actualisation de l’écran et des actions.

## 11. Budget de taille

Le corpus relève 3 253 lignes de code dans `src/` au 22 septembre 2026 et rappelle que tout contrôle ajouté doit être compensé par une simplification.

La GUI V1 est soumise aux gardes suivantes :

- **plafond de 1 200 lignes logiques de production** pour l’ensemble des vues Tkinter, du contrôleur, de la façade ajoutée et de la présentation structurée ;
- **croissance nette maximale de 900 lignes dans `src/`**, après retrait des orchestrations et rendus CLI devenus redondants ;
- un fichier de vue ne dépasse pas 400 lignes sans revue de découpage ;
- aucun module générique de widgets, bus d’événements extensible, système de plugins ou framework de navigation n’est créé ;
- les tests ne sont pas réduits pour tenir le plafond.

Ce qui est retiré ou remplacé en échange :

- décisions d’action encodées dans des phrases CLI ;
- orchestration dupliquée entre parseur CLI et future GUI ;
- déductions de présentation réparties entre commandes ;
- toute reprise de composants de l’ancienne GUI.

Un dépassement n’est pas accepté silencieusement : il impose soit une réduction de périmètre, soit une décision humaine documentée modifiant ce garde-fou.

## 12. Accessibilité et fluidité

- navigation complète au clavier ;
- focus sur la première erreur ;
- statut jamais indiqué uniquement par couleur ;
- textes d’activité accessibles ;
- `Ctrl+N` pour créer et `Ctrl+O` pour ouvrir ;
- appels longs hors du fil Tk ;
- lecture maintenue pendant une action ;
- texte Markdown affiché sans moteur de rendu riche ;
- ouverture facultative dans l’application système.

## 13. Non-objectifs vérifiables

La V1 ne contient pas :

- worker ou processus détaché ;
- service ou serveur web ;
- planificateur ;
- base de données ;
- index métier ;
- budget ou estimation monétaire ;
- réservation, bail ou file de missions ;
- worktree ;
- exécution du livrable ;
- plusieurs collaborations actives ;
- télémétrie détaillée ;
- prompts ou flux bruts par défaut ;
- éditeur de prompts ;
- réparation automatique ;
- rejeu automatique ;
- pourcentage ou durée restante ;
- nouveau type persistant de provenance ;
- nouveau statut moteur pour l’acceptation.

## 14. Critères d’acceptation

### Accueil

- AC-01 — Les trois entrées demandées sont présentes.
- AC-02 — Ouvrir est strictement en lecture seule.
- AC-03 — Un dossier invalide est nommé sans modification.
- AC-04 — Les statuts des récents sont relus du disque.
- AC-05 — Supprimer les préférences de récents n’affecte aucune collaboration.

### Création

- AC-06 — La demande est saisissable ou importable et reste visible.
- AC-07 — Un import modifié est persisté avec la provenance existante `cadrage`.
- AC-08 — Le corpus n’apparaît qu’en recherche.
- AC-09 — Les réglages persistants et ceux du prochain lancement sont visuellement séparés.
- AC-10 — Le délai n’est jamais écrit dans `configuration.json`.
- AC-11 — L’origine et la valeur du délai sont affichées avant chaque action susceptible d’appeler un agent.
- AC-12 — Une création refusée ne laisse aucun dossier partiel.
- AC-13 — Créer seulement produit `READY` avec zéro appel.
- AC-14 — Créer et démarrer distingue création locale et lancement payant.

### Suivi et décision

- AC-15 — Les sept statuts disposent du contenu et des actions décrits.
- AC-16 — Aucun pourcentage ni temps restant n’apparaît.
- AC-17 — Un `RUNNING` sans exécuteur connu n’est pas présenté comme actif.
- AC-18 — Toute commande pouvant atteindre un prochain appel exige une confirmation.
- AC-19 — Le retraitement local et la poursuite éventuelle du cycle sont distingués.
- AC-20 — Une acceptation applicable produit « Version acceptée » malgré le statut `AWAITING_APPROVAL`.
- AC-21 — Une acceptation antérieure est signalée comme telle.
- AC-22 — Aucun incident ne déclenche de relance automatique.
- AC-23 — Les qualifications de coût sont reprises sans montant ni déduction.

### Pause et fermeture

- AC-24 — GUI et CLI utilisent le même mécanisme `ExecutionControl`.
- AC-25 — Une pause n’agit qu’à une frontière sûre.
- AC-26 — Une interruption termine l’arbre selon les garanties du transport et publie l’incident attendu.
- AC-27 — La fermeture n’abandonne jamais un workflow capable de lancer l’appel suivant.
- AC-28 — `STREAMS_UNCLOSED` est toléré et expliqué ; un fil de drainage résiduel n’est pas présenté comme un cycle actif.
- AC-29 — Aucun rejeu payant automatique n’est introduit.

### Architecture et taille

- AC-30 — Aucun widget n’écrit de fichier métier.
- AC-31 — CLI et GUI consomment les mêmes actions structurées.
- AC-32 — Les mutations utilisent le verrou existant.
- AC-33 — Le fil Tk ne lance ni agent ni lecture longue.
- AC-34 — Les composants exclus sont absents.
- AC-35 — La production ajoutée respecte 1 200 lignes logiques et la croissance nette de `src/` reste au plus de 900 lignes, sauf arbitrage documenté.

## 15. Stratégie de tests

### 15.1 Tests unitaires

Tester sans Tk :

- les sept statuts ;
- les quatre phases ;
- les actions structurées ;
- le sous-état accepté ;
- la décision devenue antérieure ;
- activité locale contre `RUNNING` persistant ;
- qualification des incidents ;
- provenance fichier/cadrage ;
- résolution du délai et affichage de son origine ;
- distinction « étape locale » / « poursuite pouvant appeler ».

### 15.2 Tests des vues

Avec une racine Tk masquée lorsque possible :

- contrôles et libellés ;
- ordre de focus ;
- repli des réglages ;
- apparition du corpus ;
- dialogues de confirmation ;
- affichage « Version acceptée » ;
- absence de pourcentage ;
- absence de confirmation payante pour une simple lecture ou acceptation ;
- présence d’une confirmation pour toute poursuite susceptible d’appeler.

### 15.3 Parcours avec faux agents

1. **Créer seulement**
   - statut `READY` ;
   - zéro appel.

2. **Créer et démarrer**
   - A, B, révision, relecture ;
   - `AWAITING_APPROVAL` ;
   - acceptation liée aux bonnes empreintes ;
   - affichage « Version acceptée ».

3. **Attente humaine**
   - réponse ajoutée à la demande ;
   - confirmation avant reprise ;
   - poursuite réussie.

4. **`RUNNING` persistant**
   - résultat complet récupéré localement ;
   - aucun rejeu de l’appel récupéré ;
   - confirmation avant un éventuel appel suivant.

5. **`INTERRUPTED`**
   - aucune relance automatique ;
   - motif obligatoire ;
   - nouvel appel après confirmation seulement.

6. **`ERROR`**
   - réponse brute conservée ;
   - retraitement local sans appel pendant cette étape ;
   - si le cycle doit continuer, appel ultérieur seulement après la confirmation préalable ;
   - relance séparée et payante.

7. **Correction ciblée**
   - tour supplémentaire ;
   - A puis B ;
   - ancienne acceptation non applicable.

8. **Pause et fermeture**
   - pause demandée durant un appel ;
   - fin de l’appel, publication `READY`, aucun appel suivant ;
   - interruption immédiate ;
   - `STREAMS_UNCLOSED` simulé sans poursuite du workflow.

### 15.4 Compatibilité CLI/GUI

- créer dans la GUI, poursuivre en CLI ;
- créer en CLI, poursuivre dans la GUI ;
- accepter en CLI, afficher « Version acceptée » dans la GUI ;
- utiliser le même fichier explicite et obtenir le même délai effectif ;
- modifier par une commande CLI autorisée pendant que la GUI est ouverte ;
- simuler un verrou occupé ;
- vérifier la parité des `ActionId` et des textes CLI.

### 15.5 Atomicité

Injecter une faute sur :

- demande illisible ;
- configuration invalide ;
- cible existante ;
- corpus absent ou vide ;
- copie refusée ;
- publication finale interrompue.

Résultat : aucun dossier cible partiel.

### 15.6 Contrôle de périmètre et taille

La recette recherche :

- SQLite ou autre base ;
- serveur HTTP ;
- worker ou planificateur ;
- lancement détaché ;
- budget, réservation, bail ou worktree ;
- gestion de plusieurs exécutions ;
- dépendance GUI externe ;
- nouveau type de provenance ;
- table d’actions propre à Tkinter.

Elle mesure aussi les lignes logiques ajoutées et la croissance nette de `src/`.

## 16. Découpage de réalisation

### Lot 1 — Actions structurées et façade

- introduire `ActionId`, `AllowedAction` et les résultats structurés ;
- faire dériver les textes CLI de ces structures ;
- établir les tests de parité ;
- centraliser la résolution du délai.

### Lot 2 — Contrôle coopératif

- introduire `ExecutionControl` ;
- adapter transport, workflow et Ctrl+C de la CLI ;
- tester pause, interruption et absence d’appel suivant.

### Lot 3 — Accueil et lecture

- accueil ;
- récents non métier ;
- ouverture ;
- suivi en lecture seule ;
- sous-état accepté.

### Lot 4 — Création

- formulaire ;
- provenance compatible ;
- séparation configuration/lancement ;
- création seule ;
- création et démarrage.

### Lot 5 — Interventions et décisions

- réponse humaine ;
- reprise ;
- retraitement ;
- relance ;
- correction ;
- acceptation et arrêt.

### Lot 6 — Recette

- faux agents ;
- compatibilité croisée ;
- atomicité ;
- périmètre ;
- budget de taille.

## 17. Décision de conception

La GUI V1 retenue est donc :

- locale ;
- mono-fenêtre ;
- mono-collaboration ;
- mono-exécution ;
- fondée sur Tkinter/ttk ;
- raccordée à une façade commune ;
- commandée par des actions structurées ;
- dotée d’une interruption coopérative partagée avec la CLI ;
- explicite sur tout passage possible à un appel fournisseur ;
- capable de distinguer cycle terminé, décision requise et version acceptée ;
- bornée par un budget de code mesurable.

Elle préserve les garanties documentaires de V2 sans reprendre les mécanismes d’autonomie de l’ancienne GUI.

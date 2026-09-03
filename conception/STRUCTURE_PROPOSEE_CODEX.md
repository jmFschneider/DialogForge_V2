# Structure proposée par Codex — IAbinome, première brique

## Statut du document

Ce document est une proposition destinée à la revue contradictoire de B puis à
l'arbitrage humain. Il ne constitue ni une décision finale, ni un plan de codage
autorisé.

Les quatre documents faisant autorité ont été relus dans l'ordre imposé :
`POURQUOI.md`, `CLAUDE.md`, `DEPART.md`, puis `conception/INVENTAIRE.md`. Les dix
fichiers DialogForge demandés ont été lus intégralement, en lecture seule. J'ai
également lu les portions de `orchestrator.py` et `framing.py` qui construisent
les prompts, ainsi que `lock.py`, parce que les fichiers imposés leur délèguent
directement des comportements revendiqués par l'inventaire.

Dans ce document :

- **fait** désigne ce que les sources lues établissent ;
- **inférence** désigne une conséquence raisonnable mais non prouvée par elles ;
- **recommandation** désigne un choix proposé pour IAbinome ;
- **incertitude** désigne un point qui exige une décision ou un essai externe.

Toutes les recommandations renvoient à la table de réversibilité de la section
12. Lorsqu'une recommandation n'y est pas nommée séparément, elle reste
réversible jusqu'à la première ligne de code qui en dépend ; après cette borne,
elle exige au minimum une modification de tests et de spécification.

## Conclusion d'ensemble

**Recommandation.** Ne pas extraire une version réduite de DialogForge par
élagage progressif. Construire un noyau neuf, en ne recopiant que quelques
algorithmes courts et testés : normalisation JSON, écriture atomique, verrou,
transitions pures et arrêt d'un arbre de processus. DialogForge concentre les
bonnes leçons, mais ses modules les plus volumineux mélangent ces invariants à
l'autonomie, aux budgets, aux preuves binaires, aux sessions, aux workers et à
l'implémentation. Les réduire sur place conserverait précisément les couplages
que le nouveau projet veut éviter.

Le noyau proposé compte environ **1 500 lignes Python de production**, hors
tests, avec la bibliothèque standard de Python 3.12. Il ne contient ni base de
données, ni worker, ni ordonnanceur, ni budget, ni GUI, ni mode d'implémentation.
Il orchestre seulement un dialogue borné : proposition de A, critique structurée
de B, révision éventuelle de A, puis document final de A.

Le dossier d'une collaboration est l'unité de vérité, de reprise, d'archive et
de déplacement. À sa création, la demande et les sources autorisées sont
copiées dans ce dossier. Le cycle n'a ensuite plus besoin du dépôt d'origine.

Une décision reste réellement structurante et n'est pas prise ici :

- **B sans effets** : B peut lire le corpus dans un bac à sable en lecture seule ;
- **B sans outils** : B ne peut voir que le contexte injecté dans son prompt.

La structure accepte les deux politiques. Toutefois, le code DialogForge lu ne
montre pas de moyen vérifié de désactiver tous les outils de la CLI Codex, alors
que la CLI Claude reçoit une liste d'outils explicite. Sous la politique « sans
outils », la permutation Codex-en-B doit donc échouer au prévol tant qu'un moyen
d'enforcement n'a pas été caractérisé. Une simple consigne dans le prompt ne
constitue pas un confinement.

## 1. Audit des 43 enseignements classés « Code »

La colonne « Verdict source » répond uniquement à la question : l'affirmation
est-elle effectivement portée par les fichiers DialogForge observés ? La
colonne « Sort proposé » répond à une autre question : faut-il la conserver dans
IAbinome ?

| ID | Verdict source | Observation et sort proposé |
|---|---|---|
| C1 | Partiel | La boucle existe, mais la valeur par défaut du code lu est 3 révisions, pas 2. Conserver la boucle avec 2 par défaut. |
| C2 | Faux en partie | Phase, révision et artefact existent ; `WorkflowState` n'a pas de `schema_version`. Ajouter un état minimal explicitement versionné. |
| C2b | Approximatif | Les phases et statuts inconnus échouent, mais plusieurs champs absents reçoivent silencieusement une valeur par défaut. Exiger exactement le schéma de la version connue et refuser version future, champ absent ou surnuméraire. |
| C3 | Partiel | Le temporaire dans le même dossier suivi de `os.replace` donne une publication atomique, mais aucun `flush`/`fsync` n'assure la durabilité après coupure. Conserver et compléter. |
| C4 | Vrai | `NamedTemporaryFile` donne bien un nom propre à chaque appel. Conserver. |
| C5 | Vrai | `lock.py` enregistre PID, date UTC et commande, refuse un détenteur vivant et récupère un verrou mort. Recopier l'idée dans un module court. |
| C6 | Vrai, mais trop faible | La revue de conception accepte exactement `decision`, `analysis`, `resolved_changes`. Il manque des constats individuellement adressables. Étendre le nouveau contrat avec `schema_version` et `findings`. |
| C7 | Vrai | Le JSON est décodé avant coercition des valeurs. Conserver cet ordre. |
| C8 | Hors du contrat de conception actuel | La sévérité appartient au contrat de revue d'implémentation ; la revue de conception n'a pas de constats structurés. Introduire une sévérité explicite sans jamais déduire la décision globale. |
| C9 | Absent de la revue de conception | Aucun constat structuré ne permet de garder une sévérité inconnue. Autoriser `UNKNOWN` et garder le constat ouvert. |
| C10 | Partiel | `resolved_changes` existe, mais le contrat ne vérifie pas que les identifiants renvoient à des constats antérieurs. Ajouter cette validation référentielle. |
| C11 | Vrai | Un unique bloc clôturé couvrant toute la réponse est accepté ; préfixe, suffixe ou second objet sont refusés. Reprendre l'algorithme. |
| C12 | Partiel | Le normaliseur garde texte utile, transformations et empreintes ; l'archivage brut est dispersé ailleurs. Dans IAbinome, garder brut, normalisé et règle appliquée dans le même dossier d'appel. |
| C13 | Partiel | Le normaliseur est déterministe ; la « canonicalisation » générale n'est pas un objet autonome. Définir une seule fonction pure et la tester sur octets et JSON. |
| C14 | Faux au sens strict | DialogForge utilise une empreinte de contrat, pas un champ `schema_version` dans le payload de revue. Ajouter une version entière et refuser toute version inconnue. |
| C15 | Vrai | Le protocole commun `run(prompt, project_path) -> str` existe. Le remplacer par un contrat à résultat typé, toujours petit. |
| C15a | Vrai | Les rôles et outils sont séparés et les quatre permutations sont représentables. Conserver cette orthogonalité et la tester. |
| C15b | Faux dans DialogForge | Les fournisseurs apparaissent dans `models.py`, `factory.py` et d'autres modules. Dans IAbinome, seul le paquet `adapters` connaît les noms et options fournisseurs. |
| C15c | Faux dans l'ensemble observé | Sessions Codex, sortie structurée native, métriques et capacités créent des chemins asymétriques. Le noyau neuf n'utilise que prompt par stdin, réponse texte, modèle optionnel, accès nul/lecture seule et timeout. |
| C15d | Vrai, mais surdimensionné | Les adaptateurs déclarent beaucoup de capacités et une logique d'attestation. Garder seulement `supports_no_tools`, `supports_read_only`, `supports_model_override` et la version observée au prévol. |
| C15e | Partiel | Le modèle est paramétrable et des catalogues donnent des défauts, mais les noms par défaut décidés pour IAbinome ne sont pas établis par ces sources. Résoudre le modèle au `new`, le persister, puis ne plus le faire dériver. |
| C16 | Vrai | `FakeAgent` et `ScriptedAgent` existent. Conserver un unique faux scriptable ; aucun test n'appelle un fournisseur. |
| C17 | Partiel | Les classes d'erreur sont communes, mais leur détection reste propre aux enveloppes fournisseurs. Garder un petit vocabulaire commun ; ne jamais déclencher de reprise automatique sur une erreur de quota. |
| C18 | Non démontré par les dix fichiers | Le transport porte encore le nom du fournisseur ; la convention complète dépend des modules de preuve. Dans IAbinome, nommer les appels par séquence, rôle et UUID, jamais par fournisseur. |
| C19 | Vrai dans `AgentUsage` | La normalisation existe, mais elle ne sert pas au produit sans budgets. Ne pas la transporter dans le noyau ; conserver seulement les sorties brutes si une mesure ultérieure est souhaitée. |
| C20 | Partiel et hors cible | Certains indices de quota sont convertis en heure locale, mais l'ordonnancement est ailleurs. Ne pas calculer de reprise : afficher l'indice brut et rendre la main à l'humain. |
| C21 | Non démontré et hors cible | La politique de repli de reprise est distribuée. Sans ordonnanceur, IAbinome n'invente pas d'heure : inconnue reste inconnue. |
| C22 | Vrai | Timeout dur et terminaison de l'arbre existent. Conserver, avec une interface injectée pour les tests. |
| C23 | Partiel | L'orchestrateur écrit un identifiant et l'état avant l'appel, puis l'artefact avant la transition ; le mécanisme dépend de plusieurs modules. Rendre l'ordre explicite dans un protocole d'appel unique. |
| C24 | Faux dans `subprocess_agent.py` | stdout/stderr sont accumulés sans plafond dans des listes. Segmenter en fichiers immuables, imposer une limite haute et échouer explicitement au lieu de tronquer. |
| C25 | Faux dans DialogForge | CLI, worker et autres surfaces coexistent. IAbinome n'a qu'une CLI synchrone. |
| C26 | Faux dans DialogForge, cible pertinente | Plusieurs mécanismes de reprise existent. N'exposer qu'une commande `resume`, avec options explicites selon l'incident. |
| C31 | Vrai pour le cycle de conception | Le programme décide des transitions ; la sortie agent est une donnée. En faire un invariant de module et de test. |
| C32 | Faux pour DialogForge entier | Les chemins d'implémentation peuvent exécuter des validations proposées. Dans IAbinome, aucune sortie agent n'est interprétée comme commande. |
| C33 | Non garanti globalement | Des prévols existent, mais `storage.py` peut créer l'arborescence et la logique est dispersée. Faire tout le prévol avant la création ou mutation du dossier final. |
| C34 | Approximatif | Les versions et capacités sont sondées, avec des registres et attestations persistantes. Pour IAbinome : un sondage de présence/version par invocation, aucune autorité historique. |
| C35 | Vrai pour la demande, avec bruit annexe | Le cycle lit `demande.md`, mais configuration et sujet participent encore au contexte. Dans IAbinome, la demande copiée est la seule autorité fonctionnelle. |
| C36 | Partiel | DialogForge possède des racines et manifestes, mais via une infrastructure de contexte complexe. Utiliser une racine fournie une fois, des chemins relatifs exacts, des fichiers réguliers et leurs empreintes. |
| C37 | Faux actuellement | `configuration.json` conserve notamment un `project_path` absolu. Ne persister que des chemins relatifs au dossier de collaboration. |
| C38 | Faux actuellement | Une collaboration dépend encore du projet externe et d'infrastructures hors dossier. Copier demande et corpus pour rendre IAbinome autonome et déplaçable. |
| C39 | Partiel | Les incidents et identifiants existent, mais la frontière d'un appel disparu est distribuée. Toute phase `LAUNCHING` ou `STARTED` sans manifeste final devient `INTERRUPTED` et n'est jamais rejouée seule. |
| C40 | Faux pour le produit complet | Les modes d'implémentation donnent des droits d'écriture au projet. Dans IAbinome, seuls le programme et ses temporaires écrivent, sous la collaboration. |
| C41 | Faux dans DialogForge | DialogForge sait coder et valider. IAbinome refuse avant appel toute demande explicitement orientée exécution/codage ; la limite reste aussi annoncée dans les prompts. |

### Enseignements de code qui manquaient ou étaient insuffisamment formulés

**Faits.** La lecture croisée révèle six trous importants :

1. La revue de conception ne possède pas de liste de constats stables. Son
   `analysis` Markdown ne permet pas de prouver qu'un point précis a été corrigé.
2. Un `resolved_changes` sans validation référentielle peut déclarer résolu un
   identifiant inexistant.
3. L'atomicité de publication n'est pas la durabilité sur coupure électrique ;
   le code actuel ne fait pas de `fsync` des fichiers d'état.
4. Le transport observé n'a pas de limite haute réelle de stdout/stderr.
5. « Sans outils » et « lecture seule » ne sont pas deux formulations d'un même
   confinement : elles changent la capacité de B à vérifier les sources et ne
   sont pas symétriquement applicables aux deux CLI observées.
6. Les CLI fournisseurs peuvent conserver leurs propres caches ou journaux dans
   le profil utilisateur. Le programme peut garantir que **ses artefacts** sont
   contenus dans la collaboration et demander un mode éphémère, mais la lecture
   actuelle ne permet pas d'affirmer qu'aucune écriture interne fournisseur ne
   se produira jamais hors du dossier.

### Limites de preuve de cette vérification

- Les dix fichiers imposés ont été lus intégralement. `lock.py` et les portions
  pertinentes de `orchestrator.py` et `framing.py` ont été ajoutés à la lecture
  parce que les comportements étudiés y sont directement délégués.
- Les autres modules DialogForge et sa suite de tests n'ont pas été audités
  exhaustivement. Les verdicts « non démontré » ne signifient donc pas
  « inexistant dans tout le dépôt ».
- Aucune CLI fournisseur réelle n'a été lancée. Les options, modèles disponibles,
  écritures internes et capacités de confinement sont déduits du code observé,
  pas caractérisés sur les versions installées.
- Aucune documentation fournisseur en ligne n'a été consultée. Les conclusions
  sur les capacités actuelles restent soumises au prévol expérimental.
- Aucun code IAbinome n'existe encore à vérifier : arborescence, tailles et
  contrats proposés sont des estimations de conception.

## 2. Analyse fichier par fichier de l'héritage DialogForge

Les nombres sont les lignes physiques des fichiers au moment de la lecture.

| Fichier | À garder comme idée ou petit extrait | À écarter | Cible estimée |
|---|---|---|---:|
| `contracts.py` — 857 | Décodage strict, unique clôture JSON, schéma local de la revue, empreintes brut/utile | Contrats d'implémentation, livraison, diagnostic adaptatif, mini moteur générique de JSON Schema, journaux et incidents couplés | 160 lignes |
| `agents/subprocess_agent.py` — 1 109 | stdin/stdout/stderr, timeout dur, fermeture de l'arbre, erreur sur code non nul ou réponse vide | preuves binaires, heartbeats, leases, checkpoints, pause Windows, monitoring, validations, métriques, politiques d'autorisation | 180 lignes |
| `storage.py` — 505 | écriture temporaire locale puis remplacement, lecture/écriture stricte, création transactionnelle du dossier | arborescence autonomie/contexte, migration historique, champs projet absolus, nombreux journaux spécialisés | 155 lignes |
| `agents/claude.py` — 568 | construction minimale de la commande, extraction de la réponse et diagnostic d'erreur | coûts, usages, raw evidence externe, capacités historiques, schémas natifs, logique de budget | 75 lignes |
| `workflow.py` — 119 | fonctions de transition pures et bornage des révisions | mode A seul, attente de quota automatisée, états hérités | 180 lignes avec protocole d'appel |
| `agents/codex.py` — 675 | commande éphémère, extraction du dernier `agent_message`, modèle et sandbox | sessions/reprise de thread, cache usage, sortie structurée native, archivage externe, métrologie | 90 lignes |
| `models.py` — 303 | enums, configuration immuable, état sérialisable | catalogues fournisseurs, mode implémentation, quota/session/budget, valeurs absentes tolérées | 150 lignes |
| `agents/factory.py` — 537 | résolution d'un identifiant d'adaptateur et vérification de 3 capacités | confinement multi-mode, attestations, cache de capacité, permissions d'écriture, branchements par rôle | 30 lignes |
| `agents/base.py` — 192 | protocole d'adaptateur, résultat et erreurs communes | `RawTransport`, métriques de coût, checkpoints, session et réservations | 55 lignes |
| `agents/fake.py` — 66 | réponses/exceptions scriptées et enregistrement des appels | presque rien ; supprimer les doublons de faux | 45 lignes |

**Inférence.** Les dix fichiers totalisent 4 931 lignes physiques. Environ 600 à
800 lignes expriment une idée encore utile, mais elles sont entremêlées à des
dépendances qui rendraient une extraction littérale coûteuse. Les tailles cibles
du tableau ne s'additionnent pas directement : `workflow.py` absorbe une partie
de la persistance d'appel et plusieurs anciens fichiers disparaissent au profit
d'un seul module.

## 3. Arborescence exacte proposée

### 3.1 Dépôt du programme

```text
IAbinome/
├── POURQUOI.md
├── CLAUDE.md
├── DEPART.md
├── pyproject.toml
├── src/
│   └── iabinome/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── models.py
│       ├── storage.py
│       ├── lock.py
│       ├── contracts.py
│       ├── workflow.py
│       ├── prompts.py
│       ├── transport.py
│       ├── corpus.py
│       └── adapters/
│           ├── __init__.py
│           ├── base.py
│           ├── claude.py
│           └── codex.py
└── tests/
    ├── __init__.py
    ├── test_contracts.py
    ├── test_state.py
    ├── test_storage.py
    ├── test_lock.py
    ├── test_corpus.py
    ├── test_workflow.py
    ├── test_recovery.py
    ├── test_transport.py
    ├── test_permutations.py
    ├── test_cli.py
    └── fakes.py
```

`pyproject.toml` ne déclare aucune dépendance d'exécution. Les tests utilisent
`unittest`, `unittest.mock` et les autres modules de la bibliothèque standard.

### 3.2 Dossier autonome d'une collaboration

```text
ma-collaboration/
├── configuration.json
├── demande.md
├── etat.json
├── verrou.json                         # seulement pendant une commande mutante
├── corpus/
│   ├── manifeste.json
│   └── fichiers/
│       └── <chemins logiques copiés>
├── appels/
│   └── 0001-A-<uuid>/
│       ├── intention.json
│       ├── prompt.txt
│       ├── stdout/
│       │   ├── 000001.bin
│       │   └── 000002.bin
│       ├── stderr/
│       │   └── 000001.bin
│       ├── manifeste.json
│       ├── reponse_brute.txt
│       ├── reponse_normalisee.json     # seulement pour une revue B valide
│       └── incident.json               # seulement en cas d'échec
├── echanges/
│   ├── 0001-proposition-A.md
│   ├── 0002-critique-B.json
│   └── 0003-revision-1-A.md
├── interventions/
│   └── 0001-reponse-humaine.md
└── livrable.md                         # présent seulement après finalisation
```

Tous les chemins persistés sont relatifs à `ma-collaboration/`. Le manifeste du
corpus conserve le chemin logique, la taille et SHA-256 de chaque copie, mais pas
la racine absolue d'origine. Les fichiers source doivent être réguliers,
résolus sous une racine autorisée et lisibles ; liens sortants, chemins absolus,
`..` et fichiers changeant pendant la copie sont refusés.

**Recommandation.** La première version accepte seulement un manifeste de
fichiers exacts, pas des motifs glob ni une découverte autonome. C'est moins
confortable, mais beaucoup plus petit et auditable. Une recherche Internet n'est
pas une capacité commune démontrée par les adaptateurs lus : « recherche » doit
donc signifier, dans cette première brique, recherche dans un corpus fourni. Si
la recherche Web est exigée, elle constitue une décision de périmètre distincte.

## 4. Modèle d'état et ordre des écritures

### 4.1 Configuration immuable

```json
{
  "schema_version": 1,
  "collaboration_id": "architecture-cache",
  "max_revisions": 2,
  "agent_a": {"adapter": "codex", "model": "MODELE_RESOLU", "access": "READ_ONLY"},
  "agent_b": {"adapter": "claude", "model": "MODELE_RESOLU", "access": "NONE"},
  "demande_sha256": "…",
  "corpus_manifest_sha256": "…",
  "created_at": "2026-09-03T12:00:00Z"
}
```

Le modèle par défaut décidé pour chaque rôle est résolu lors de `new` et sa
valeur CLI exacte est enregistrée. Une mise à jour ultérieure du programme ne
change donc jamais le modèle d'une collaboration existante. Les identifiants
CLI exacts correspondant à « Opus 5 » et « Fable 5 » restent à vérifier auprès
des deux adaptateurs : les fichiers DialogForge lus ne les établissent pas.

### 4.2 État dynamique minimal

```json
{
  "schema_version": 1,
  "status": "READY",
  "phase": "PROPOSAL_A",
  "revision": 0,
  "latest_artifact": null,
  "latest_review": null,
  "open_finding_ids": [],
  "current_call": null,
  "last_incident": null,
  "updated_at": "2026-09-03T12:00:00Z"
}
```

Valeurs fermées :

- `status` : `READY`, `RUNNING`, `WAITING_HUMAN`, `INTERRUPTED`, `ERROR`,
  `COMPLETED` ;
- `phase` : `PROPOSAL_A`, `REVIEW_B`, `REVISION_A`, `FINAL_A`, `COMPLETED` ;
- `current_call.status` : `PREPARED`, `LAUNCHING`, `STARTED`,
  `RESPONSE_STORED`, `APPLIED`.

`current_call` contient exactement `id`, `sequence`, `role`, `phase`, `status`,
`directory`, `prompt_sha256`, `started_at` et `completed_at`. Les valeurs non
encore connues sont `null`, mais les clés ne disparaissent pas. `last_incident`
contient un code fermé, un message, le call ID concerné et l'action humaine
attendue. Tout objet inconnu, clé absente, clé surnuméraire ou
`schema_version != 1` provoque un refus avant mutation.

### 4.3 Séquence durable d'un appel

1. Prévol complet : schémas, empreintes, phase, corpus, présence/version CLI,
   modèle et politique d'accès supportée. Aucun fichier n'est encore modifié.
2. Acquisition du verrou de collaboration.
3. Création atomique de `intention.json`, du prompt et du dossier d'appel avec
   un UUID ; publication de `current_call=PREPARED`.
4. Publication de `LAUNCHING` **avant** `Popen`. Cette fenêtre est volontairement
   prudente : un crash à cet endroit signifie « appel possiblement parti ».
5. Après création confirmée du processus, publication de `STARTED`.
6. stdout et stderr sont écrits en segments immuables de taille bornée. Une
   limite totale fixe provoque arrêt de l'arbre et incident `OUTPUT_LIMIT` ;
   aucun préfixe tronqué n'est présenté comme une réponse complète.
7. Après sortie réussie, écriture du manifeste des segments et de la réponse
   brute, puis publication de `RESPONSE_STORED`.
8. Normalisation et validation locale. Pour B, écriture du JSON normalisé ; pour
   A, écriture du Markdown d'échange.
9. Écriture de l'artefact de phase **avant** la transition d'état.
10. Publication de `APPLIED`, puis de la phase suivante. Libération du verrou.

Au démarrage, `LAUNCHING` ou `STARTED` sans manifeste final devient
`INTERRUPTED`. Le programme ne rejoue rien. Seul
`resume --retry-call <uuid>` autorise un nouvel appel, avec un nouvel UUID et un
lien `retries` vers l'ancien. La dépense éventuellement perdue reste donc
visible. `RESPONSE_STORED` est retraité localement sans appel fournisseur.

Les fichiers JSON et Markdown de contrôle sont écrits dans un temporaire unique
du même dossier, vidés, `fsync`-és, puis publiés par `os.replace`. Les segments
de transport déjà fermés sont immuables. Sur POSIX, le dossier est `fsync`-é
après remplacement ; sur Windows, le remplacement est retenté brièvement comme
dans DialogForge.

## 5. Workflow borné

```text
PROPOSAL_A → REVIEW_B ─ACCEPTER────────────→ FINAL_A → COMPLETED
                    ├─REVISER, quota restant→ REVISION_A ─→ REVIEW_B
                    ├─REVISER, quota épuisé─→ FINAL_A (constats ouverts transmis)
                    └─BLOQUE────────────────→ WAITING_HUMAN
```

Une réponse humaine à `BLOQUE` est enregistrée par `resume --answer` puis mène à
`REVISION_A`. Une erreur de contrat B reste `ERROR` avec la réponse brute ; elle
n'est ni réparée automatiquement ni convertie en décision. Une erreur externe
ou de quota rend également la main à l'humain. Aucune heure de reprise n'est
calculée.

Le programme, jamais l'agent, choisit la transition. Une chaîne ressemblant à
une commande, un patch ou une instruction d'outil reste du texte. Aucun module
de production ne possède de fonction d'application de patch, d'appel Git, de
validation de code ou de commande issue du contenu agent.

### Contrat de revue proposé

```json
{
  "schema_version": 1,
  "decision": "REVISER",
  "analysis": "Critique synthétique en Markdown.",
  "findings": [
    {
      "id": "B-architecture-001",
      "severity": "MAJOR",
      "disposition": "OPEN",
      "statement": "Le contrat de reprise ne couvre pas…"
    }
  ],
  "resolved_changes": ["B-architecture-000"]
}
```

Règles locales : clés exactes ; décision parmi `ACCEPTER`, `REVISER`, `BLOQUE` ;
sévérité parmi `BLOCKING`, `MAJOR`, `MINOR`, `NOTE`, `UNKNOWN` ; disposition
parmi `OPEN`, `RESOLVED`, `WITHDRAWN`. Une sévérité absente devient `UNKNOWN`
seulement **après** décodage JSON et reste ouverte. Chaque identifiant est stable
et unique. `resolved_changes` ne peut citer que des constats ouverts d'une revue
antérieure et doit correspondre à une disposition `RESOLVED` ou `WITHDRAWN`
documentée. La décision globale n'est jamais calculée à partir des sévérités.

`BLOQUE` signifie qu'une information humaine indispensable manque ; un défaut
important mais analysable appelle `REVISER`. `ACCEPTER` avec un constat ouvert
`BLOCKING` est refusé comme incohérent, non transformé silencieusement.

## 6. CLI exacte proposée

La syntaxe ci-dessous est la totalité de la surface V0.1.

```text
python -m iabinome new COLLAB
    --demande FICHIER
    [--source-root DOSSIER --source-list MANIFESTE]
    [--agent-a ADAPTER] [--model-a MODELE]
    [--agent-b ADAPTER] [--model-b MODELE]
    --reviewer-access {none,read-only}
    [--max-revisions N]

python -m iabinome run COLLAB [--timeout SECONDES]

python -m iabinome resume COLLAB
    [--timeout SECONDES]
    [--answer FICHIER | --retry-call UUID]

python -m iabinome status COLLAB [--json]
```

Défauts proposés : `max-revisions=2`, `timeout=1800`. Les adaptateurs et modèles
par défaut viennent du registre d'adaptateurs, conformément aux choix écrits
dans `CLAUDE.md`; les options d'appel les remplacent. `new` exige explicitement
`--reviewer-access` tant que la décision « sans outils / sans effets » reste
ouverte. Cette obligation évite de la trancher par accident dans un défaut CLI.

`new` valide tout dans un dossier temporaire frère, y copie demande et corpus,
puis publie le dossier final par renommage. Il refuse une destination existante.
`run` est l'unique moteur d'exécution synchrone. `resume` ne contient pas un
second moteur : il enregistre l'intervention autorisée, remet l'état dans une
phase admissible et appelle la même fonction `run_cycle`. `status` est strictement
en lecture seule. Il n'existe ni `worker`, ni `serve`, ni API, ni commande
d'implémentation.

La détection automatique des demandes de codage ne peut être parfaite. Le
prévol refuse les marqueurs explicites configurés et la CLI n'offre aucune
capacité d'écriture/exécution ; une demande ambiguë doit être signalée à
l'humain, pas classée par un appel fournisseur supplémentaire.

## 7. Adaptateurs et quatre permutations

Le noyau ne connaît que ce protocole conceptuel :

```python
class AgentAdapter(Protocol):
    adapter_id: str
    capabilities: Capabilities
    def probe(self) -> ObservedCli: ...
    def command(self, call: CallSpec) -> list[str]: ...
    def extract(self, stdout: bytes, stderr: bytes) -> str: ...
```

`CallSpec` contient prompt, modèle, timeout, dossier de travail et politique
d'accès. Il ne contient ni budget, ni session, ni fournisseur, ni rôle métier.
Le rôle n'intervient que dans le prompt et le nom logique de l'appel. Le registre
d'adaptateurs est dans `adapters/__init__.py`; tous les autres modules manipulent
seulement `adapter_id`.

Capacités communes retenues : appel éphémère, prompt transmis sans fichier
externe, réponse texte, modèle remplaçable, timeout, environnement sans écriture
du projet. Les sorties structurées natives, sessions, cache, coûts natifs,
budgets et reprise fournisseur sont délibérément hors noyau. Le JSON B est
validé localement de façon identique pour tous.

| A | B | `read-only` | `none` |
|---|---|---|---|
| Claude | Codex | Possible d'après les sandbox observées | Non démontré pour Codex B |
| Codex | Claude | Possible d'après les sandbox observées | Possible avec liste d'outils Claude vide |
| Claude | Claude | Possible | Possible |
| Codex | Codex | Possible | Non démontré pour Codex B |

**Incertitude structurante.** Avec `reviewer-access=none`, le contexte de B ne
contient que demande, proposition courante et constats ouverts. B peut juger la
cohérence, mais pas vérifier indépendamment le corpus. Avec `read-only`, il peut
lire la copie du corpus et vérifier les références sans produire d'effet. Ces
deux niveaux d'assurance ne doivent pas partager le même libellé de résultat :
`etat.json` et `livrable.md` doivent rappeler la politique réellement appliquée.

Le prévol sonde la version CLI à chaque `run`, vérifie la capacité demandée et
échoue avant verrou/mutation si elle manque. Il ne mémorise aucune attestation.
Une version observée est enregistrée dans `intention.json` uniquement comme
preuve factuelle de l'appel, jamais comme autorité pour le suivant.

## 8. Prompts légers proposés

Les variables entre chevrons sont injectées par le programme. Les fichiers du
corpus ne sont pas recopiés dans le prompt : un agent autorisé les lit dans
`corpus/fichiers/`. Aucune conversation complète n'est rejouée ; seule la
version courante et les constats encore ouverts sont transmis.

### Proposition A

```text
Tu es A, auteur principal d'un travail de conception ou de recherche.
La demande ci-dessous est l'unique autorité fonctionnelle. Le corpus est en
lecture seule sous corpus/fichiers/ et son manifeste sous corpus/manifeste.json.
Produis un document Markdown complet et autonome. Distingue faits sourcés,
inférences, recommandations et incertitudes. Cite les chemins logiques utiles.
Ne code pas, n'exécute rien et ne modifie aucun fichier. Retourne seulement le
Markdown.

DEMANDE
<demande.md>
```

### Critique B

```text
Tu es B, contradicteur. Cherche erreurs, omissions, hypothèses fragiles et
alternatives sérieuses dans la proposition courante. Ta politique d'accès est
<NONE|READ_ONLY>. Si elle vaut NONE, n'essaie pas de lire une source ; indique
les faits invérifiables. Si elle vaut READ_ONLY, le corpus est sous
corpus/fichiers/. Ne modifie rien et n'exécute aucune action produisant un effet.
Retourne uniquement le JSON conforme au schéma de revue v1. BLOQUE est réservé
à une information humaine indispensable. Ne déduis pas la décision des seules
sévérités et ne déclare résolu qu'un identifiant antérieur effectivement traité.

DEMANDE
<demande.md>

PROPOSITION COURANTE
<markdown courant>

CONSTATS OUVERTS
<json minimal ou []>
```

### Révision A

```text
Tu es A. Réécris une version Markdown complète et autonome qui traite la
critique et les constats ouverts ci-dessous. Ne réponds pas point par point à la
place du livrable. Garde visibles les incertitudes non résolues. Le corpus est
en lecture seule sous corpus/fichiers/. Ne code pas, n'exécute rien et ne
modifie aucun fichier. Retourne seulement le Markdown.

DEMANDE
<demande.md>

VERSION COURANTE
<markdown courant>

CRITIQUE ET CONSTATS OUVERTS
<revue B normalisée>
```

### Finalisation A

```text
Tu es A. Produis le livrable final Markdown, autonome et directement lisible.
Intègre les apports utiles sans raconter le dialogue. Signale explicitement les
incertitudes et constats restant ouverts. Ne code pas, n'exécute rien et ne
modifie aucun fichier. Retourne seulement le Markdown.

DEMANDE
<demande.md>

VERSION COURANTE
<markdown courant>

CONSTATS ENCORE OUVERTS
<json minimal ou []>
```

**Recommandation.** Ne pas intégrer de cadrage interactif à V0.1 tant que son
utilité n'est pas décidée. `new` reçoit une demande déjà écrite. Un futur
assistant de cadrage devra produire exactement le même `demande.md` avant la
création de la collaboration ; il ne devra pas créer une seconde autorité.

## 9. Stratégie de tests — fournisseurs toujours faux

Tous les tests utilisent `unittest`. `FakeAdapter`, `FakeProcess` et
`FakeClock` remplacent respectivement fournisseur, processus et temps. Aucun
test ne lance Claude, Codex, un réseau ou une commande proposée par un agent.

### Contrats et normalisation

- JSON nu et unique clôture JSON acceptés ; BOM et espaces périphériques
  enregistrés comme transformations ; préfixe, suffixe, deux objets, tableau,
  clés inconnues et version future refusés.
- Toutes les décisions, sévérités et dispositions ; sévérité absente conservée
  comme `UNKNOWN` ; aucune déduction automatique de décision.
- Identifiants dupliqués, résolution inconnue et fausse résolution refusés.
- Brut, normalisé, règle appliquée et empreintes reproductibles.

### État, stockage et verrou

- Chaque champ absent, surnuméraire ou inconnu échoue fermé.
- Écriture atomique avec deux écritures concurrentes : temporaires distincts et
  aucun état partiel visible ; simulation d'échec avant/après remplacement.
- Verrou vivant refusé avec PID/date/commande ; verrou mort récupéré ; un
  processus ne supprime jamais le verrou d'un autre.
- Aucun chemin persistant absolu ; déplacement complet d'une collaboration puis
  reprise réussie.
- Source hors racine, `..`, lien sortant, fichier non régulier ou hash changeant
  refusé avant création du dossier final.

### Workflow et incidents

- Chemins `ACCEPTER`, `REVISER`, quota de révision atteint et `BLOQUE`.
- Artefact écrit avant phase close ; transition impossible sans artefact et
  empreinte correspondante.
- Crash simulé à chaque frontière `PREPARED`, `LAUNCHING`, `STARTED`,
  `RESPONSE_STORED`, `APPLIED`.
- `LAUNCHING`/`STARTED` devient `INTERRUPTED` sans nouvel appel ;
  `RESPONSE_STORED` se retraite localement ; seul `--retry-call` crée un appel.
- Timeout, erreur quota, erreur authentification, sortie vide, code non nul,
  réponse invalide et plafond de sortie : un incident durable, aucune boucle.
- Segments complets reconstitués dans l'ordre ; dépassement tue le faux arbre et
  n'expose jamais le préfixe comme réponse.

### Orthogonalité

- Matrice complète A/B : faux-Claude/faux-Codex, faux-Codex/faux-Claude,
  faux-Claude/faux-Claude, faux-Codex/faux-Codex.
- Même suite de transitions et même contrat local dans les quatre cas.
- Adaptateur sans capacité `NONE` refusé au prévol, avant verrou et avant appel.
- Modèles par défaut résolus au `new`, remplacements persistés, reprise
  insensible à un changement ultérieur du registre.

### Limite conception/recherche

- Une demande explicite de patch, déploiement ou commande est refusée sans
  appel ; aucun symbole de production n'applique du code.
- Une sortie A contenant un bloc shell ou un diff reste un simple Markdown.
- Les prompts et artefacts ne contiennent pas de verbe d'exécution injecté par
  le programme ; le test vérifie surtout l'absence de chemin fonctionnel, plus
  forte qu'une détection lexicale parfaite.

## 10. Budget de taille

| Module | Lignes cibles |
|---|---:|
| `__init__.py` + `__main__.py` | 15 |
| `cli.py` | 170 |
| `models.py` | 150 |
| `storage.py` | 155 |
| `lock.py` | 90 |
| `contracts.py` | 160 |
| `workflow.py` | 180 |
| `prompts.py` | 90 |
| `transport.py` | 180 |
| `corpus.py` | 100 |
| `adapters/base.py` | 55 |
| `adapters/__init__.py` | 30 |
| `adapters/claude.py` | 75 |
| `adapters/codex.py` | 90 |
| **Total indicatif** | **1 550** |

Ce total est une contrainte de conception, pas un quota aveugle. Si la gestion
correcte des processus Windows exige quelques dizaines de lignes de plus, elle
prime sur le chiffre. En revanche, aucune fonction de budget, session, base,
worker, GUI, implémentation, preuve distante ou ordonnancement ne peut être
ajoutée sous prétexte qu'elle existe déjà dans DialogForge.

## 11. Risques, limites et décisions à faire arbitrer

1. **Politique de B.** `read-only` permet les quatre permutations et une revue
   factuelle ; `none` réduit la revue au contexte injecté et n'est pas encore
   enforceable pour Codex-en-B d'après les sources lues.
2. **Recherche Web.** Aucune capacité réseau commune n'est établie. La V0.1
   proposée recherche dans un corpus figé ; promettre le Web élargirait le
   produit et le confinement.
3. **Écritures internes des CLI.** Le mode éphémère minimise la persistance, mais
   l'absence absolue d'écriture fournisseur hors collaboration doit être testée
   sur les versions réelles ou reformulée en « artefacts appartenant à
   IAbinome ».
4. **Identifiants de modèles.** Les noms sémantiques Opus 5 et Fable 5 sont une
   décision ; leurs identifiants CLI et leur disponibilité doivent être
   caractérisés au prévol, sans catalogue historique.
5. **Copie du corpus.** Elle donne autonomie, empreintes et chemins logiques au
   prix d'espace disque. Les corpus binaires ou immenses sont hors V0.1 ; il faut
   fixer une politique explicite plutôt que les accepter silencieusement.
6. **Détection du codage.** Une classification lexicale parfaite est impossible.
   La vraie barrière est l'absence de capacité d'écriture et d'exécution de
   contenu agent ; le refus sémantique n'est qu'un garde-fou supplémentaire.
7. **Acceptation humaine.** `COMPLETED` signifie « cycle achevé », pas
   « conception approuvée par l'utilisateur ». Si une validation humaine finale
   est requise, ajouter ultérieurement un statut `AWAITING_APPROVAL`, sans la
   confondre avec la décision de B.
8. **Sévérités structurées.** Leur ajout corrige un manque du contrat actuel,
   mais doit être validé par B : il augmente légèrement le prompt et le schéma
   pour gagner une traçabilité que `analysis` seul ne peut fournir.

## 12. Réversibilité de la proposition

Les choix sont volontairement localisés. Leurs bornes sont explicites :

| Recommandation | Réversible sans migration jusqu'à… | Après cette borne |
|---|---|---|
| Noyau neuf plutôt qu'élagage de DialogForge | la création des premiers modules `src/iabinome` | changer de stratégie impose de réévaluer dépendances et budget de taille |
| Schémas exacts de configuration, état et revue | la première collaboration persistée | incrémenter la version et fournir une migration explicite |
| Copie autonome du corpus et chemins relatifs | la première collaboration persistée | migrer manifeste, chemins et règles de reprise |
| Manifeste de fichiers exacts, sans glob | la stabilisation de `corpus.py` et de ses tests | ajout compatible possible, mais chaque nouvelle règle d'expansion devient un contrat |
| Quatre commandes CLI proposées | le premier script utilisateur ou document opératoire publié | conserver les anciens noms ou annoncer une rupture |
| Absence de cadrage dans V0.1 | la stabilisation de `new` | un cadrage reste ajoutable en amont s'il ne crée pas une seconde autorité |
| Contrat B enrichi de `findings` | la première revue B persistée | migration de schéma et des constats ouverts nécessaire |
| Politique B `none` ou `read-only` choisie par collaboration | la commande `new` de chaque collaboration | le choix reste changeable pour une nouvelle collaboration ; changer en cours de cycle altère le niveau de preuve et doit être interdit ou historisé |
| Capacités communes seules dans le noyau | la publication du protocole `AgentAdapter` | un bonus reste ajoutable dans un adaptateur, mais ne peut devenir requis par le workflow |
| Recherche limitée au corpus local en V0.1 | l'arbitrage du périmètre avant implémentation | le Web exige un contrat de capacité, de preuve et de confinement distinct |
| Vocabulaire d'incidents sans ordonnanceur | la première reprise persistée | évolution versionnée de l'état ; jamais de calcul rétroactif silencieux |
| Future brique de codage séparée | la validation de cette première brique | franchir la frontière exige une nouvelle spécification et une décision humaine écrite |

Un troisième adaptateur reste ajoutable dans `adapters/` tant qu'aucune condition
sur son fournisseur n'entre dans le noyau. Le schéma versionné rend les
évolutions possibles, mais jamais par tolérance silencieuse.

Le principal choix difficilement réversible serait de laisser les agents lire
directement des dépôts externes tout en persistant leurs chemins absolus. C'est
pourquoi la copie initiale du corpus et les chemins logiques sont proposés dès
la première version.

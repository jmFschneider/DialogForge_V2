# Structure proposée — Codex V2

> Demande du 2026-09-03 : relire la critique de Claude, sa révision complète,
> ainsi que la V1.1 de la première analyse Codex, puis proposer une V2 qui
> améliore le futur projet sans recréer la complexité de DialogForge.
>
> Ce document n'autorise aucune implémentation. Il doit être relu puis arbitré
> humainement avant la première ligne de code.

## Statut et sources

Cette V2 remplace **comme proposition**, mais n'efface pas :

- `RELECTURE_CODEX_PASSE1_V1.1.md` ;
- `STRUCTURE_PROPOSEE_CODEX.md` ;
- `CRITIQUE_CLAUDE_STRUCTURE_CODEX.md` ;
- `STRUCTURE_PROPOSEE_CLAUDE.md`.

Elle a aussi été confrontée à `POURQUOI.md`, `CLAUDE.md`, `DEPART.md`,
`INVENTAIRE.md`, `DISPOSITION_RELECTURE.md`, `project/NOTES.md` et
`project/RULES.md`.

Vocabulaire : **fait** = vérifié dans une source lue ; **inférence** = conséquence
plausible ; **recommandation** = choix proposé ; **incertitude** = point à
caractériser ou arbitrer.

## Conclusion

La charpente commune aux propositions précédentes tient : noyau neuf, boucle A/B
bornée, fichiers locaux, deux adaptateurs interchangeables, aucune exécution de
contenu agent. La critique de Claude améliore réellement neuf points, mais sa
révision reprend deux promesses trop fortes et conserve une partie de la
machinerie que ma première proposition avait réintroduite.

La V2 apporte six corrections structurantes :

1. **La recherche n'est plus redéfinie en silence comme “corpus-only”.** Une
   collaboration de recherche choisit explicitement `corpus-only` ou
   `external`. Le second mode ne pourra être livré qu'après caractérisation des
   deux CLI.
2. **Le dossier de collaboration est la racine de travail, pas une frontière de
   sécurité prétendument prouvée.** Les limites réelles de lecture des CLI sont
   nommées au lieu d'être masquées par `cwd`.
3. **L'appel durable passe de cinq statuts à deux statuts utiles** : `CALLING` et
   `RESPONSE_STORED`. Ils suffisent à distinguer un appel possiblement payé d'une
   réponse retraitable localement.
4. **stdout et stderr vont chacun dans un fichier borné**, pas dans une forêt de
   segments. La réponse n'est jamais tronquée et un dépassement échoue
   explicitement.
5. **La clarification de la demande devient une vraie porte**, sans phase de
   cadrage supplémentaire : A peut rendre `QUESTION` au lieu de produire une
   conception sur une ambiguïté structurante.
6. **L'arbitrage humain existe dans l'état.** La production du livrable mène à
   `AWAITING_APPROVAL`, jamais directement à un succès ambigu.

Production attendue : environ **1 400 à 1 650 lignes Python**, hors tests. Les
tests sont comptés et publiés séparément ; ils ne deviennent pas un objectif de
volume.

---

## 1. Disposition des onze constats de Claude

| Constat | Disposition V2 | Motif |
|---|---|---|
| B-001 — recherche externe écartée | **ACCEPTÉ, correction différente** | La recherche est déjà actée. La V2 ne choisit pas corpus-only : elle rend le mode de sources explicite et soumet l'accès externe à une porte de capacité commune. |
| B-002 — racine lisible de B | **ACCEPTÉ sur l'intention, CORRIGÉ sur la preuve** | `cwd=collaboration` borne ce qu'IAbinome fournit, mais ne prouve pas qu'une CLI ne peut lire ailleurs. En faire un “invariant testé” avant caractérisation serait faux. |
| B-003 — péremption du corpus | **ACCEPTÉ** | Date, libellé d'origine et éventuelle révision déclarée sont conservés. Aucun chemin absolu n'est persisté et aucun rafraîchissement silencieux n'est permis. |
| B-004 — relance sans motif | **ACCEPTÉ avec nuance** | Un motif obligatoire est une trace attribuable, pas une preuve que la cause a changé. La V2 le dit et n'ajoute aucun plafond assimilable à un budget. |
| B-005 — volume des tests absent | **ACCEPTÉ, estimation corrigée** | Production et tests doivent être séparés. Le ratio DialogForge ne permet pas de prédire 2 300–3 000 lignes ; une fourchette de planification non normative est plus honnête. |
| B-006 — garde-fou du cadrage perdu | **ACCEPTÉ, correction renforcée** | “Ouvrir par des questions puis produire” n'empêche pas de travailler malgré elles. A peut arrêter le cycle sur `QUESTION`; l'humain remplace ensuite la demande complète. |
| B-007 — coût non reconstructible | **ACCEPTÉ sans mécanisme nouveau** | Les sorties brutes et versions CLI sont déjà conservées. Elles suffisent à une analyse hors ligne ; aucun parseur de coût n'entre dans le noyau. |
| B-008 — prompt présenté comme confinement | **ACCEPTÉ** | Le prompt informe B de ses accès effectifs ; il ne lui ordonne pas de simuler une barrière absente. |
| B-009 — `COMPLETED` lu comme approbation | **ACCEPTÉ et renforcé** | Un avertissement dans le livrable aide, mais l'état doit aussi distinguer `AWAITING_APPROVAL`, `APPROVED` et `REJECTED`. |
| B-010 — budget optimiste du transport | **ACCEPTÉ** | La V2 simplifie avant de coder. Elle ne prévoit pas de retirer `fsync` ou une garantie de reprise pour tenir un chiffre. |
| B-011 — manifeste exact à mesurer | **ACCEPTÉ** | C'est la première friction d'usage à observer. Aucun glob ni paquet thématique n'est ajouté avant mesure. |

### Ce que la V1.1 avait raison de remettre au centre

La frontière d'effets doit rester courte. Le danger principal de cette première
brique n'est pas un commit automatique — il n'existe aucun chemin de code pour
en faire un — mais la disparition d'une exigence, d'une objection, d'une source
contraire ou d'une limite de preuve pendant la convergence. La structure donne
donc plus de place au mandat, aux constats adressables et aux preuves qu'au
confinement.

### Autocritique de la première structure Codex

- Les cinq états `PREPARED`, `LAUNCHING`, `STARTED`, `RESPONSE_STORED`, `APPLIED`
  distinguaient des fenêtres qui n'appelaient pas de traitements différents.
- Les segments immuables de sortie étaient une solution anticipée, alors qu'un
  fichier de flux borné préserve déjà la réponse et la mémoire.
- La recherche avait été ramenée au corpus local sans que l'arbitrage “recherche
  au périmètre” autorise cette restriction.
- `resolved_changes` et `disposition` créaient deux sources de vérité pour la
  fermeture d'un constat.
- L'approbation humaine était annoncée comme souhaitable, mais reportée hors de
  l'état alors que `DEPART.md` la demande en fin de boucle.
- Le refus lexical des demandes de code était surévalué : la vraie protection
  est l'absence de toute fonction qui exécute ou applique une sortie agent.

---

## 2. Périmètre exact de V0.1

IAbinome produit un document de **conception** ou de **recherche** au moyen de
deux agents CLI : A produit, B contredit, A révise, l'humain arbitre.

Il ne contient :

- ni application de patch, commande dérivée d'une réponse ou modification Git ;
- ni base, worker, tâche planifiée, bail ou reprise automatique ;
- ni budget, réservation, calcul de quota ou réveil programmé ;
- ni GUI ;
- ni session fournisseur persistante, routage adaptatif ou conseil d'agents.

### Deux natures de mission, pas un moteur de permissions

- `CONCEPTION` : A consulte la demande et, s'il existe, l'instantané local du
  corpus.
- `RECHERCHE` : la création exige un choix explicite entre `CORPUS_ONLY` et
  `EXTERNAL_READ`.

`EXTERNAL_READ` signifie que l'agent peut consulter des sources externes au
moyen de la capacité native, sans installation et sans écriture du projet. Le
noyau ne contient aucun client HTTP, navigateur, téléchargement ou système de
consentement. Cette capacité doit être caractérisée comme disponible chez **les
deux adaptateurs** avant d'entrer dans la version livrée. Si ce test échoue, le
mode reste spécifié mais indisponible ; l'humain décide alors s'il reporte ce
mode ou modifie le périmètre. IAbinome ne ment pas en l'appelant “recherche Web”.

### Contrat de B toujours ouvert

La V2 reste compatible avec les deux décisions :

- `CONTEXT_ONLY` : B ne reçoit que demande, document courant et registre des
  constats ;
- `CONSULT` : B peut consulter le corpus et, en recherche `EXTERNAL_READ`, les
  sources externes.

**Recommandation non arbitrée :** choisir `CONSULT`, donc “aucun effet”, car
`CONTEXT_ONLY` n'est pas mécaniquement disponible pour Codex d'après le code lu
et contredit alors les quatre permutations obligatoires. Tant que l'humain n'a
pas tranché, `--reviewer-access` reste obligatoire et sans défaut.

Si `CONTEXT_ONLY` est choisi par l'humain, il faut soit démontrer une invocation
Codex sans outils, soit rouvrir la contrainte des quatre permutations. Aucun
wrapper de confinement général n'est proposé pour résoudre artificiellement ce
conflit.

---

## 3. Frontière d'effets — formulation honnête

### Garanties appartenant à IAbinome

1. Le programme n'écrit que les chemins fermés de son dossier de collaboration.
2. Il ne modifie jamais le corpus original, le dépôt étudié, Git ou les
   dépendances du projet.
3. Il ne transforme jamais une sortie agent en commande, patch, chemin
   arbitraire ou choix de transition non validé.
4. Chaque adaptateur reçoit le dossier de collaboration comme `cwd` et seulement
   des chemins logiques relatifs.
5. Un adaptateur incapable de garantir le profil d'effets demandé est refusé
   avant l'appel.

### Ce que ces garanties ne prouvent pas

`cwd` n'est pas un bac à sable de lecture. Une CLI peut éventuellement lire un
chemin absolu, sa configuration utilisateur ou des fichiers voisins ; elle peut
aussi maintenir ses propres caches. La promesse exacte est donc :

> Tous les artefacts **appartenant à IAbinome** restent dans la collaboration ;
> IAbinome ne donne aucun droit d'écriture sur le projet étudié. Les écritures
> internes et la portée de lecture d'une CLI sont des limites observées de
> l'adaptateur, pas des propriétés inventées par le noyau.

**Recommandation.** Ne pas reconstruire un sandbox général. Avant la première
livraison, effectuer un smoke manuel et jetable pour chaque adaptateur et chaque
profil retenu, puis documenter le résultat. Si l'opérateur exige l'isolation de
secrets locaux, il lance IAbinome dans un compte ou environnement dédié ; cette
isolation reste extérieure à V0.1.

---

## 4. Arborescence proposée

### Programme

```text
IAbinome/
├── pyproject.toml
├── src/iabinome/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── models.py
│   ├── storage.py
│   ├── lock.py
│   ├── contracts.py
│   ├── workflow.py
│   ├── prompts.py
│   ├── transport.py
│   ├── corpus.py
│   └── adapters/
│       ├── __init__.py
│       ├── base.py
│       ├── claude.py
│       └── codex.py
└── tests/
    ├── __init__.py
    ├── fakes.py
    ├── test_contracts.py
    ├── test_state.py
    ├── test_storage.py
    ├── test_lock.py
    ├── test_corpus.py
    ├── test_workflow.py
    ├── test_recovery.py
    ├── test_transport.py
    ├── test_permutations.py
    └── test_cli.py
```

Bibliothèque standard Python 3.12 uniquement en production. Les noms de
fournisseurs n'apparaissent dans aucun module hors `adapters/` ; le noyau ne
manipule que des identifiants d'adaptateur opaques.

### Collaboration

```text
collaboration/
├── configuration.json
├── demande.md
├── etat.json
├── verrou.json                       # transitoire
├── demandes/
│   └── 0001-demande-initiale.md      # versions antérieures immuables
├── corpus/
│   ├── manifeste.json
│   └── fichiers/<chemins-logiques>
├── appels/
│   └── 0001-A-<uuid>/
│       ├── intention.json
│       ├── prompt.txt
│       ├── stdout.part               # présent pendant l'appel ou l'incident
│       ├── stderr.part
│       ├── stdout.bin                # publié seulement si flux complet
│       ├── stderr.bin
│       ├── resultat.json             # code retour, tailles et empreintes
│       ├── reponse_brute.txt
│       ├── revue_normalisee.json     # seulement pour B
│       └── incident.json             # seulement sur échec
├── echanges/
│   ├── 0001-proposition-A.md
│   ├── 0002-critique-B.json
│   └── 0003-revision-1-A.md
├── interventions/
│   ├── 0001-question-A.md
│   └── 0002-motif-reprise.md
├── livrables/
│   └── version_finale.md
└── decision_humaine.json             # seulement après arbitrage final
```

Le dossier est autonome pour **reprendre le cycle**. En recherche externe, il
ne rend pas le Web immuable : le livrable doit conserver URL, date d'accès,
niveau d'accès et extrait utile. Cette limite épistémique est déclarée.

### Instantané local

`corpus/manifeste.json` contient : version du schéma, `captured_at`,
`origin_label`, éventuel `origin_revision` fourni par l'humain, puis chemin
logique, taille et SHA-256 de chaque fichier. Il ne contient aucun chemin absolu.

`status` affiche l'âge de l'instantané. Les prompts disent qu'il représente
l'état à cette date. Il n'existe pas de `refresh` : changer le corpus au milieu
d'un cycle détruirait la référence commune de A et B. Pour une référence plus
récente, on crée une nouvelle collaboration.

Le manifeste reçoit des fichiers exacts, un par ligne. Les chemins absolus,
`..`, liens sortants, fichiers non réguliers ou changeant pendant la copie sont
refusés avant publication du dossier final. L'ergonomie de cette liste est le
premier point d'usage mesuré ; glob et paquets n'entrent qu'après un problème
réel.

---

## 5. Configuration et état

### `configuration.json`, immuable

```json
{
  "schema_version": 1,
  "collaboration_id": "etude-cache",
  "mission_kind": "RESEARCH",
  "research_access": "EXTERNAL_READ",
  "reviewer_access": "CONSULT",
  "max_revisions": 2,
  "agent_a": {"adapter_id": "ADAPTER_A", "model": "MODELE_RESOLU"},
  "agent_b": {"adapter_id": "ADAPTER_B", "model": "MODELE_RESOLU"},
  "initial_demande_sha256": "…",
  "corpus_manifest_sha256": "…",
  "created_at": "2026-09-03T12:00:00Z"
}
```

Pour `CONCEPTION`, `research_access` vaut obligatoirement `NOT_APPLICABLE`. Pour
`RESEARCH`, il vaut explicitement `CORPUS_ONLY` ou `EXTERNAL_READ`.

Les modèles par défaut sont résolus au `new` puis persistés, de sorte qu'une
mise à jour du programme ne change pas une collaboration en cours. Les
identifiants CLI exacts d'Opus 5 et Fable 5 restent une porte de prévol : aucun
alias n'est inventé hors des adaptateurs.

### `etat.json`, dynamique

```json
{
  "schema_version": 1,
  "status": "READY",
  "phase": "PROPOSAL_A",
  "revision": 0,
  "demande_revision": 1,
  "demande_sha256": "…",
  "current_document": null,
  "latest_review": null,
  "open_finding_ids": [],
  "current_call": null,
  "last_incident": null,
  "updated_at": "2026-09-03T12:00:00Z"
}
```

Valeurs fermées :

- `status` : `READY`, `RUNNING`, `WAITING_HUMAN`, `INTERRUPTED`, `ERROR`,
  `AWAITING_APPROVAL`, `APPROVED`, `REJECTED` ;
- `phase` : `PROPOSAL_A`, `REVIEW_B`, `REVISION_A`, `FINAL_A`,
  `HUMAN_APPROVAL`, `CLOSED` ;
- `current_call.status` : `CALLING`, `RESPONSE_STORED`.

`current_call` contient exactement : identifiant UUID, séquence, rôle, phase,
statut, dossier logique, empreinte du prompt, empreinte de réponse (d'abord
`null`) et horodatages. Aucune chaîne de fournisseur dans l'identifiant ou le
chemin. `last_incident` contient un code fermé, un message, le call ID et
l'action humaine admissible. `current_document` et `latest_review` sont des
chemins relatifs explicites : la reprise ne devine jamais le contexte à partir
d'un nom de fichier.

État et configuration refusent version future, enum inconnu, clé absente ou
surnuméraire. Les champs connus mais sans valeur sont présents avec `null`.

---

## 6. Protocole durable simplifié

1. **Prévol sans mutation** : demande, schémas, état, empreintes, corpus,
   adaptateurs, versions observées, modèles et profils requis.
2. Acquisition du verrou de collaboration.
3. Nouvelle lecture de l'état et des empreintes critiques sous verrou. Toute
   différence depuis le prévol provoque un refus ; cette seconde lecture ferme
   la fenêtre de concurrence sans déplacer les sondages coûteux sous verrou.
4. Création du dossier d'appel, de `intention.json` et du prompt. Publication de
   `current_call.status=CALLING` **avant** `Popen`.
5. Lancement du processus. stdout et stderr sont copiés au fil de l'eau dans
   leurs fichiers `.part`, avec compteurs de taille et timeout dur.
6. Si un flux dépasse sa limite, l'arbre est terminé, les `.part` restent comme
   preuve partielle et l'incident `OUTPUT_LIMIT` est écrit. Rien n'est présenté
   comme une réponse complète.
7. Après sortie réussie, vidage et `fsync`, renommage des deux flux complets,
   écriture de `resultat.json`, extraction de la réponse, puis publication de
   `RESPONSE_STORED` avec empreinte.
8. Normalisation locale, écriture de l'artefact de phase, puis transition d'état
   et remise de `current_call` à `null`.
9. Libération du verrou.

Un crash avec `CALLING` signifie “appel possiblement parti et possiblement
payé” : état `INTERRUPTED`, jamais de rejeu automatique. Un crash avec
`RESPONSE_STORED` reprend seulement la normalisation et la transition locales.

Cette réduction conserve toutes les décisions réellement utiles. `PREPARED`,
`LAUNCHING` et `STARTED` avaient la même conséquence après crash ; `APPLIED`
dupliquait la phase déjà persistée.

### Écart explicite à C24

C24 prescrivait une segmentation alors que l'audit a montré qu'elle n'existait
pas dans DialogForge : c'était un correctif proposé, pas un acquis. La V2 choisit
un fichier borné par flux. Il n'est ni gardé en mémoire ni tronqué ; au plafond,
l'appel échoue et le partiel reste identifiable comme tel. Ce mécanisme est plus
petit et couvre le défaut observé.

Les JSON et Markdown de contrôle utilisent temporaire unique, `flush`, `fsync`
et `os.replace`. Le `fsync` de dossier POSIX est conservé lorsque disponible ;
une limite de lignes ne justifie pas de retirer une garantie de durabilité.

---

## 7. Workflow et arbitrage humain

```text
PROPOSAL_A ─QUESTION────────────────────────→ WAITING_HUMAN
    │ DOCUMENT
    ▼
REVIEW_B ─BLOQUE────────────────────────────→ WAITING_HUMAN
    ├─REVISER et limite non atteinte────────→ REVISION_A → REVIEW_B
    ├─REVISER et limite atteinte────────────→ FINAL_A
    └─ACCEPTER──────────────────────────────→ FINAL_A

FINAL_A → HUMAN_APPROVAL → AWAITING_APPROVAL
resume --approve ───────────────────────────→ APPROVED
resume --reject  ───────────────────────────→ REJECTED
```

Après `QUESTION` de A ou `BLOQUE` de B, l'humain fournit une **nouvelle demande
complète**. L'ancienne est archivée dans `demandes/`, la nouvelle devient
`demande.md`, son empreinte et sa révision sont publiées dans l'état. Ainsi,
l'intervention ne crée pas une seconde autorité cachée. Une question de la
proposition reprend `PROPOSAL_A`, une question de révision reprend
`REVISION_A`, et un `BLOQUE` reprend `REVISION_A` avec le document courant et
les constats déjà ouverts.

`livrables/version_finale.md` commence par une ligne ajoutée par le programme :

> La présence de ce fichier ne prouve pas son approbation ; l'arbitrage humain
> faisant autorité se trouve dans `decision_humaine.json` et `etat.json`.

Cette phrase reste vraie avant et après arbitrage. Le document mentionne aussi
la politique de revue appliquée et le nombre de constats ouverts, sans être
réécrit lors de l'approbation.

### Contrat léger de A pour la clarification

La première ligne d'une proposition ou révision vaut exactement :

```text
IABINOME:DOCUMENT
```

ou :

```text
IABINOME:QUESTION
```

Dans le second cas, le reste contient seulement les informations manquantes qui
modifieraient substantiellement le périmètre, la méthode ou la conclusion. Le
programme conserve les questions et s'arrête. Ce discriminateur unique remplace
un cadrage automatique séparé, évite un appel préalable systématique et empêche
de poursuivre malgré une question déclarée bloquante.

**Recommandation sur le cadrage :** ne pas reprendre `framing.py` en V0.1. La
porte `QUESTION` récupère son bénéfice essentiel dans le premier appel utile.
Elle est réversible jusqu'à stabilisation du contrat A.

### Contrat de revue B — une seule vérité par constat

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
      "statement": "La reprise ne couvre pas…",
      "rationale": "Conséquence observée ou raisonnement."
    }
  ]
}
```

La V2 supprime `resolved_changes`. Il doublonnait `disposition` et pouvait
diverger. À chaque revue, B doit reprendre exactement une fois chaque constat
antérieurement ouvert avec `OPEN`, `RESOLVED` ou `WITHDRAWN`, puis peut ajouter
de nouveaux identifiants `OPEN`. Une fermeture exige un motif. Le programme
dérive `open_finding_ids` de cette liste unique.

Une sévérité omise est normalisée en `UNKNOWN` après décodage JSON et reste
ouverte. Les clés inconnues, décisions inconnues, identifiants dupliqués ou
disparition d'un constat antérieur font échouer le contrat, réponse brute
préservée. Un unique bloc JSON clôturé couvrant toute la réponse reste accepté.

La décision globale n'est jamais calculée à partir des sévérités. Même une
combinaison surprenante reste visible pour l'arbitrage humain ; le programme ne
la réécrit pas en consensus apparent.

---

## 8. Surface CLI

```text
python -m iabinome new COLLAB
    --demande FICHIER
    --kind {conception,recherche}
    [--research-access {corpus-only,external}]
    [--source-root DOSSIER --source-list MANIFESTE]
    [--source-label TEXTE] [--source-revision TEXTE]
    [--agent-a ADAPTER] [--model-a MODELE]
    [--agent-b ADAPTER] [--model-b MODELE]
    --reviewer-access {context-only,consult}
    [--max-revisions N]

python -m iabinome run COLLAB [--timeout SECONDES]

python -m iabinome resume COLLAB [--timeout SECONDES]
    [--answer NOUVELLE_DEMANDE
     | --retry-call UUID --reason-file FICHIER
     | --approve
     | --reject FICHIER_MOTIF]

python -m iabinome status COLLAB [--json]
```

Règles :

- `--research-access` est interdit en conception et obligatoire en recherche ;
- `--reviewer-access` est obligatoire sans valeur par défaut tant que B-2 reste
  non arbitré ;
- `max-revisions=2` et `timeout=1800` sont les défauts proposés ;
- `new` résout puis persiste adaptateurs et modèles ;
- `--answer` remplace `demande.md` par un document complet, après archivage ;
- `--reason-file` doit être non vide et est copié dans la collaboration. Il
  prouve une décision humaine attribuable, pas la vérité du motif ;
- `--approve` et `--reject` ne sont valides qu'en `AWAITING_APPROVAL` ;
- `resume` est la seule commande de reprise et appelle le même moteur que `run` ;
- `status` est strictement en lecture seule et affiche âge du corpus, profil de
  sources, politique B, constats ouverts et statut d'approbation.

`new` effectue tous les prévols dans un répertoire temporaire frère, puis publie
la collaboration par renommage. Il refuse une destination existante. Il
n'existe aucune commande `worker`, `serve`, `implement`, `apply`, `watch` ou
`repair`.

---

## 9. Contrat des adaptateurs

```python
class AgentAdapter(Protocol):
    adapter_id: str
    capabilities: Capabilities
    def probe(self) -> ObservedCli: ...
    def command(self, call: CallSpec) -> list[str]: ...
    def extract(self, stdout: bytes, stderr: bytes) -> str: ...
```

`CallSpec` contient prompt, modèle, timeout, racine de travail et profil de
consultation. Il ne contient ni fournisseur, ni budget, ni session, ni rôle
métier. Le rôle n'intervient que dans le prompt et le nom logique d'appel.

Capacités de noyau : appel éphémère, réponse texte, modèle remplaçable, timeout,
absence d'écriture du projet. Capacités conditionnelles : `context_only` et
`external_read`. Une capacité conditionnelle ne peut être activée que si les
deux adaptateurs la démontrent ; sinon la combinaison échoue au prévol.

Sortie structurée native, session persistante, métriques de coût et erreur de
quota typée restent hors noyau. Les sorties brutes et la version CLI observée
sont conservées par appel pour permettre une analyse hors ligne, sans parseur
de coût ni automatisation de reprise.

### Porte de caractérisation avant implémentation complète

Un smoke manuel jetable doit établir, pour chaque CLI :

1. l'invocation éphémère canonique et le remplacement de modèle ;
2. l'absence d'écriture dans le projet avec le profil de consultation ;
3. la réalité ou l'absence du mode sans outils ;
4. la disponibilité d'une consultation externe en mode recherche ;
5. les fichiers éventuellement écrits par la CLI hors collaboration ;
6. le comportement du timeout et de la terminaison d'arbre sur Windows.

Ce smoke n'entre pas dans la suite automatisée et n'est pas mémorisé comme une
attestation durable. Ses résultats factuels doivent être arbitrés avant de
figer les deux adaptateurs.

---

## 10. Prompts allégés

### A — proposition ou clarification

```text
Tu es A, auteur principal. La demande ci-dessous est l'unique autorité.

Commence par IABINOME:QUESTION si une information absente changerait
substantiellement le périmètre, la méthode ou la conclusion ; pose alors
seulement les questions nécessaires. Sinon commence par IABINOME:DOCUMENT et
produis un document Markdown autonome. Distingue faits, inférences,
recommandations et incertitudes. Ne propose ni n'exécute de modification.

Le corpus local est un instantané du <date>. <information d'accès aux sources>

DEMANDE
<demande.md>
```

Ajout court pour une recherche :

```text
Cite les sources localisables et leur niveau d'accès. Distingue sources
indépendantes, résultat négatif et absence de preuve. Borne chaque conclusion
au contexte réellement étudié. Si le critère de fin manque, rends QUESTION.
```

### B — critique

```text
Tu es B, contradicteur. Cherche omissions, contradictions, faits non établis,
contre-preuves et alternatives sérieuses. Retourne seulement le JSON de revue
v1. BLOQUE est réservé à une information humaine indispensable. Reprends chaque
constat antérieur et motive toute fermeture.

<si CONTEXT_ONLY> Tu ne disposes que des éléments fournis ci-dessous ; qualifie
ce que tu ne peux pas vérifier.
<si CONSULT> Tu peux consulter les sources selon le profil indiqué. Le corpus
local est un instantané du <date>.

DEMANDE
<demande.md>

DOCUMENT COURANT
<document>

CONSTATS ANTÉRIEURS
<registre minimal ou []>
```

### A — révision

```text
Tu es A. Rends QUESTION si un constat révèle une information humaine
indispensable. Sinon rends DOCUMENT puis une version Markdown complète qui
traite la critique sans masquer les désaccords ou limites restantes.

DEMANDE / VERSION COURANTE / CONSTATS OUVERTS
```

### A — finalisation

```text
Tu es A. Produis le document final autonome à partir de la version courante.
Intègre les apports utiles sans raconter le dialogue. Garde visibles les
incertitudes, non-décisions et constats encore ouverts. Retourne seulement le
Markdown.

DEMANDE / VERSION COURANTE / CONSTATS OUVERTS
```

Ces prompts portent des critères intellectuels, pas un pseudo-confinement. Les
capacités sont fixées avant leur construction.

---

## 11. Tests automatisés et validations manuelles

### Suite automatisée

Tous les appels d'agent utilisent `FakeAdapter`. Aucun fournisseur, réseau ou
coût réel. `FakeProcess` et `FakeClock` permettent de simuler flux, timeout et
crash.

| Famille | Cas essentiels |
|---|---|
| Contrats | Deux statuts A ; JSON B nu ou unique bloc clôturé ; version/clé/enum invalides ; sévérité manquante → `UNKNOWN` ; constat antérieur omis ou dupliqué refusé ; fermeture motivée ; décision jamais déduite. |
| État | Schéma strict ; chaque phase ; empreinte de demande ; statut final `AWAITING_APPROVAL`, puis `APPROVED` ou `REJECTED`. |
| Stockage | Temporaires uniques ; publication atomique ; simulations avant/après `os.replace` ; chemins persistés relatifs ; déplacement complet puis reprise. |
| Verrou | PID/date/commande ; détenteur vivant refusé ; mort récupéré ; verrou tiers jamais supprimé. |
| Corpus | Hors racine, `..`, lien sortant, non-régulier et changement pendant copie refusés ; date/libellé/révision ; âge affiché ; aucune actualisation silencieuse. |
| Appel durable | Crash en `CALLING` → `INTERRUPTED` sans appel ; crash en `RESPONSE_STORED` → retraitement local ; artefact avant transition ; UUID sans fournisseur. |
| Reprise | Retry sans motif refusé ; motif copié ; nouvel UUID lié ; nouvelle demande complète remplace l'autorité ; options incompatibles refusées. |
| Transport | Deux flux concurrents, sortie vide, code non nul, timeout, arbre terminé, plafond dur, partiel jamais présenté comme complet. |
| Accès | Profil indisponible refusé avant mutation ; mode recherche explicite ; `cwd` transmis = collaboration sans prétendre tester une isolation OS. |
| Permutations | Les quatre couples d'adaptateurs factices parcourent le cycle complet avec le même workflow et le même contrat. |
| Frontière | Diff, shell ou URL malveillante dans une sortie restent du texte ; aucun symbole de production n'applique ni n'exécute le contenu. |
| Clarification | `QUESTION` arrête avant B ; demande révisée relance A ; questions archivées ; demande courante reste l'autorité unique. |

### Validations manuelles hors suite

- un appel jetable par adaptateur pour caractériser les capacités ci-dessus ;
- un processus local inoffensif avec enfant, tué par timeout sur chaque OS
  officiellement supporté ;
- déplacement réel d'une collaboration et reprise ;
- première mission conception et première mission recherche observées par
  l'humain, avec friction du manifeste notée.

Ces validations ne deviennent ni campagne d'attestation ni appel fournisseur
dans les tests.

---

## 12. Budget de taille et règle de coupe

| Module | Production visée |
|---|---:|
| `__init__` + `__main__` | 15 |
| `cli.py` | 180 |
| `models.py` | 145 |
| `storage.py` | 145 |
| `lock.py` | 90 |
| `contracts.py` | 155 |
| `workflow.py` | 210 |
| `prompts.py` | 100 |
| `transport.py` | 170 |
| `corpus.py` | 95 |
| paquet `adapters/` | 250 |
| **Total indicatif** | **1 555** |

La fourchette acceptable de production est **1 400–1 650 lignes**. Les lignes de
tests seront rapportées séparément ; ordre de grandeur de planification :
**1 200–2 000**, à confirmer par le code réel. Ce n'est ni un plancher ni un
quota. Le ratio de DialogForge n'est pas transposable à une machine beaucoup
plus petite.

Si la production dépasse la fourchette, l'ordre de réaction est :

1. supprimer les sorties de confort (`status --json`, mise en forme riche) ;
2. fusionner les abstractions à un seul appelant ;
3. retirer toute détection lexicale sophistiquée des demandes de code ;
4. reporter les métadonnées facultatives d'origine et d'usage ;
5. arrêter et demander arbitrage.

Ne sont jamais sacrifiés pour tenir le chiffre : état strict, absence de rejeu
automatique, timeout et terminaison d'arbre, artefact avant transition, quatre
permutations, registre de constats, porte de clarification et approbation
humaine. Ajouter un contrôle exige toujours de nommer ce qui sort en échange.

---

## 13. Décisions et portes restantes

### Décision humaine encore ouverte

**B-2 : `CONTEXT_ONLY` ou `CONSULT`.** La V2 recommande `CONSULT` pour rester
symétrique avec les quatre permutations et permettre une contradiction factuelle
en recherche. Ce n'est pas acté par ce document.

### Caractérisations nécessaires avant gel de la spécification

1. Identifiants CLI réels des modèles par défaut.
2. Consultation externe réellement disponible chez les deux adaptateurs.
3. Effets d'écriture et portée de lecture observés pour les invocations retenues.
4. Terminaison d'arbre sur les systèmes officiellement supportés.

Si la consultation externe n'est pas commune, trois choix seulement sont
honnêtes : reporter `EXTERNAL_READ`, réduire explicitement le sens de
“recherche”, ou rouvrir la règle des capacités communes. La V2 ne choisit pas à
la place de l'humain.

### Décisions proposées par cette V2

- pas de cadrage fournisseur séparé ; porte `QUESTION` dans l'appel A ;
- registre de constats unique, sans `resolved_changes` redondant ;
- deux états d'appel persistés au lieu de cinq ;
- un fichier borné par flux au lieu de segments ;
- approbation humaine persistée avant statut terminal positif ;
- instantané daté sans chemin absolu ni rafraîchissement en cours de cycle.

---

## 14. Réversibilité

| Choix | Réversible sans migration jusqu'à… | Après |
|---|---|---|
| Noyau neuf | premier module de production | réévaluation globale des dépendances |
| Schémas config/état/revue | première collaboration persistée | version et migration explicites |
| Deux statuts d'appel | premier incident persistant | migration de l'état et des tests de reprise |
| Fichier unique borné par flux | publication de `transport.py` | format d'archive versionné |
| Porte A `QUESTION` | gel du contrat A | migration des états `WAITING_HUMAN` |
| Absence de cadrage séparé | stabilisation de `new` et du contrat A | ajout possible en amont, sans seconde autorité |
| Approbation humaine | première collaboration finalisée | migration des anciens statuts terminaux |
| Registre sans `resolved_changes` | première revue persistée | migration du schéma de revue |
| Corpus figé | première collaboration créée | nouvelle collaboration recommandée plutôt qu'une mutation |
| Recherche externe | arbitrage et smoke avant implémentation | contrat de capacité et de preuve versionné |
| Politique B | `new` de chaque collaboration | changement en cours de cycle interdit ; nouvelle collaboration |
| Surface CLI | premier script utilisateur publié | compatibilité ou rupture annoncée |

La future porte du codage reste extérieure à ce noyau. Elle exigera une nouvelle
spécification et une décision humaine écrite ; aucun composant n'est préparé “au
cas où” dans V0.1.

## Limites de preuve

- Les dix fichiers DialogForge ont été audités lors de la V1, pas relus une
  seconde fois pour cette V2 ; les constats nouveaux portent sur les documents
  de conception.
- Aucune CLI réelle n'a été lancée. Les profils `CONTEXT_ONLY`, `CONSULT` et
  `EXTERNAL_READ` restent des contrats proposés, pas des capacités démontrées.
- Les fourchettes de lignes portent sur du code inexistant.
- La qualité de la porte `QUESTION`, du registre de constats et des prompts ne
  pourra être jugée qu'après les premières missions réelles. Une friction
  observée doit être notée avant toute généralisation.

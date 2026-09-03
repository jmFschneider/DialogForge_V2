# Structure proposée — révision de Claude

> Écrit le 2026-09-03, à côté de `STRUCTURE_PROPOSEE_CODEX.md`, dont elle reprend la charpente.
> **Version complète et autonome**, pas une liste de corrections — c'est `P7` de l'inventaire.
> Critique dont elle procède : `CRITIQUE_CLAUDE_STRUCTURE_CODEX.md`, décision `REVISER`, 11 constats.
>
> **faits** = établis par une source citée · **inférences** = conséquences non prouvées ·
> **recommandations** = choix proposés · **incertitudes** = exigent une décision ou un essai.
> Rien ici n'autorise à coder. L'arbitrage humain vient d'abord.

## Ce que la demande laisse sans réponse

*Appliqué à ce document même — c'est la règle `B-006` que je propose plus bas pour l'agent A.*

1. **La recherche V0.1 est-elle corpus-only ou peut-elle atteindre des sources externes ?** Bloquant.
   Dix lignes de l'inventaire en dépendent. Développé en §11.
2. Le contrat de B — « aucun outil » ou « aucun effet » — reste ouvert par décision du PO. La structure
   le supporte des deux côtés, mais le niveau de preuve du livrable en dépend.
3. Les identifiants CLI exacts d'« Opus 5 » et « Fable 5 » ne sont établis par aucune source lue.

## Ce qui change par rapport à Codex

| # | Change | Coût |
|---|---|---|
| 1 | La **racine lisible d'un agent est exactement le dossier de collaboration**, énoncée comme invariant testé. | 0 — une contrainte, pas du code |
| 2 | Le corpus est un **instantané daté** : le manifeste porte la date et la racine d'origine ; `status` affiche son âge ; les prompts le disent à A et B. | ~10 lignes |
| 3 | `--retry-call` **exige un motif écrit**, persisté. Pas de relance identique. | ~5 lignes |
| 4 | **Budget de tests chiffré** en plus du budget de production, et coupes pré-décidées si ça déborde. | 0 |
| 5 | Le prompt de A **ouvre par les questions que la demande laisse ouvertes** — récupère le garde-fou perdu avec le cadrage. | 0 — une phrase |
| 6 | Le manifeste d'appel **dit** que le brut est retenu pour reconstruire le coût hors ligne. Aucune comptabilité. | 0 — une phrase |
| 7 | Le prompt de B formule sa politique d'accès en **information**, jamais en interdiction. | 0 |
| 8 | `livrable.md` s'ouvre sur un bloc écrit par le programme : politique appliquée · constats ouverts · **non approuvé**. | ~10 lignes |
| 9 | Le manifeste de fichiers exacts est **le premier point d'usage à mesurer**, écrit comme tel. | 0 |

Tout le reste — noyau neuf, arborescence, séquence durable d'appel, `findings` adressables,
`--reviewer-access` obligatoire, table de réversibilité — est **repris de Codex sans modification**.

---

## 1. Décision d'ensemble

**Recommandation, reprise de Codex et confirmée.** Construire un noyau neuf, en ne recopiant que
quelques algorithmes courts : normalisation JSON, écriture atomique, verrou, transitions pures,
terminaison d'arbre de processus.

**Fait.** Les dix fichiers pèsent 4 931 lignes ; environ 600 à 800 expriment une idée encore utile,
enchevêtrées à l'autonomie, aux budgets, aux sessions et à l'implémentation.
**Inférence.** Les élaguer sur place conserverait les couplages que le projet veut fuir — et
`POURQUOI` règle 5 interdit de réparer un sous-système en s'en servant.

Le noyau orchestre un dialogue borné et rien d'autre. Ni base, ni worker, ni ordonnanceur, ni budget,
ni GUI, ni mode d'implémentation.

## 2. Arborescence

```text
IAbinome/                             ma-collaboration/
├── pyproject.toml                    ├── configuration.json
├── src/iabinome/                     ├── demande.md
│   ├── __main__.py                   ├── etat.json
│   ├── cli.py                        ├── verrou.json          # pendant une commande mutante
│   ├── models.py                     ├── corpus/
│   ├── storage.py                    │   ├── manifeste.json   # + date_copie, racine_origine
│   ├── lock.py                       │   └── fichiers/
│   ├── contracts.py                  ├── appels/
│   ├── workflow.py                   │   └── 0001-A-<uuid>/
│   ├── prompts.py                    │       ├── intention.json
│   ├── transport.py                  │       ├── prompt.txt
│   ├── corpus.py                     │       ├── stdout/ stderr/   # segments immuables
│   └── adapters/                     │       ├── manifeste.json
│       ├── base.py                   │       ├── reponse_brute.txt
│       ├── claude.py                 │       ├── reponse_normalisee.json
│       └── codex.py                  │       └── incident.json
└── tests/                            ├── echanges/
    ├── fakes.py                      ├── interventions/
    └── test_*.py  (10 modules)       └── livrable.md          # après finalisation
```

`pyproject.toml` ne déclare **aucune** dépendance d'exécution. Les tests utilisent `unittest`.
Tous les chemins persistés sont **relatifs** au dossier de collaboration.

### 2.1 Invariant de racine — nouveau

> **La racine lisible d'un agent est exactement le dossier de collaboration. Jamais le projet d'origine,
> jamais un parent.**

**Motif.** `read-only` sans dire **où** n'est pas un confinement. Sans cet invariant, un adaptateur peut
légitimement lancer la CLI avec `cwd` = le projet, et toute la copie du corpus perd son objet.
C'est le pivot de `C38` et `C40` réunis. Testé, pas seulement écrit.

### 2.2 Le corpus est un instantané daté — nouveau

**Fait.** La copie donne autonomie, empreintes et chemins relatifs. **Elle gèle aussi l'état du projet
à l'instant du `new`.** Sur une collaboration de plusieurs jours contre un dépôt vivant, A et B
raisonnent sur un passé sans le savoir — ce que `P13` de l'inventaire proscrit explicitement.

`manifeste.json` porte donc, en plus du chemin logique, de la taille et du SHA-256 de chaque copie :

```json
{ "schema_version": 1, "date_copie": "2026-09-03T12:00:00Z",
  "racine_origine": "C:\\Projets\\Florapy_V2", "fichiers": [ … ] }
```

`racine_origine` est **documentaire** : rien ne la relit, aucune reprise n'en dépend. Elle sert à
l'humain qui, trois semaines plus tard, se demande d'où venait ce corpus.

`status` affiche l'âge de l'instantané. Les prompts de A et B le disent (§8).

**Règles de copie, reprises de Codex :** fichiers réguliers seulement, résolus sous une racine autorisée,
lisibles. Refusés : liens sortants, chemins absolus, `..`, fichier dont l'empreinte change pendant la copie.

## 3. Configuration et état

```json
// configuration.json — immuable après new
{ "schema_version": 1, "collaboration_id": "architecture-cache", "max_revisions": 2,
  "agent_a": {"adapter": "codex",  "model": "<résolu au new>", "access": "READ_ONLY"},
  "agent_b": {"adapter": "claude", "model": "<résolu au new>", "access": "NONE"},
  "demande_sha256": "…", "corpus_manifest_sha256": "…", "created_at": "…" }

// etat.json — dynamique
{ "schema_version": 1, "status": "READY", "phase": "PROPOSAL_A", "revision": 0,
  "latest_artifact": null, "latest_review": null, "open_finding_ids": [],
  "current_call": null, "last_incident": null, "updated_at": "…" }
```

Valeurs fermées. `status` ∈ `READY` `RUNNING` `WAITING_HUMAN` `INTERRUPTED` `ERROR` `COMPLETED` ·
`phase` ∈ `PROPOSAL_A` `REVIEW_B` `REVISION_A` `FINAL_A` `COMPLETED` ·
`current_call.status` ∈ `PREPARED` `LAUNCHING` `STARTED` `RESPONSE_STORED` `APPLIED`.

**Tout objet inconnu, clé absente, clé surnuméraire ou `schema_version` ≠ 1 provoque un refus avant
mutation.** Les valeurs inconnues sont `null` ; les clés ne disparaissent jamais.

Le modèle est **résolu au `new` et persisté**. Une mise à jour du programme ne change jamais le modèle
d'une collaboration existante.

## 4. Séquence durable d'un appel

Reprise intégralement de Codex. Elle rend `C23` exécutable.

1. **Prévol complet** — schémas, empreintes, phase, corpus, présence et version CLI, modèle, politique
   d'accès supportée. **Aucun fichier n'est encore modifié.**
2. Acquisition du verrou.
3. Dossier d'appel + `intention.json` + prompt ; `current_call = PREPARED`.
4. **`LAUNCHING` publié AVANT `Popen`.** Fenêtre volontairement prudente : un crash ici signifie
   « appel possiblement parti », donc possiblement payé.
5. `STARTED` après création confirmée du processus.
6. `stdout`/`stderr` en segments immuables bornés. Dépassement → arrêt de l'arbre + incident
   `OUTPUT_LIMIT`. **Aucun préfixe tronqué n'est jamais présenté comme une réponse.**
7. Manifeste des segments + réponse brute → `RESPONSE_STORED`.
8. Normalisation et validation locale.
9. **Artefact de phase écrit AVANT la transition d'état.**
10. `APPLIED`, puis phase suivante. Verrou libéré.

**Écritures.** Temporaire unique dans le même dossier, `flush`, `fsync`, puis `os.replace`. Sur POSIX,
`fsync` du dossier après remplacement ; sur Windows, remplacement retenté brièvement.
*L'atomicité de publication n'est pas la durabilité : DialogForge ne faisait pas le second.*

### 4.1 Reprise, et discipline de relance — modifié

Au démarrage, `LAUNCHING` ou `STARTED` sans manifeste final devient `INTERRUPTED`.
**Le programme ne rejoue jamais rien.** `RESPONSE_STORED` se retraite localement, sans appel.

Seul `resume --retry-call <uuid> --motif "<texte>"` autorise un nouvel appel : nouvel UUID, lien
`retries` vers l'ancien, **et le motif persisté dans ce lien**.

**Motif de l'exigence.** `R4`, récoltée dans `context/supervision.md` : *une relance identique sur le
même état est interdite ; la cause, la configuration ou une décision humaine doit avoir changé de
manière vérifiable.* Le fait mesuré est humain — **4 interventions en 3 heures** sur le Lot 0, par
re-déclenchement. Le motif ne bloque personne : il rend visible qu'on relance sans avoir rien changé.

La dépense possiblement perdue reste visible dans la chaîne `retries`.

## 5. Workflow et contrat de revue

```text
PROPOSAL_A → REVIEW_B ─ACCEPTER──────────────→ FINAL_A → COMPLETED
                    ├─REVISER, quota restant──→ REVISION_A → REVIEW_B
                    ├─REVISER, quota épuisé───→ FINAL_A (constats ouverts transmis)
                    └─BLOQUE──────────────────→ WAITING_HUMAN
```

Le programme, **jamais l'agent**, choisit la transition. Une chaîne ressemblant à une commande, un patch
ou une instruction d'outil **reste du texte**. Aucun module de production ne possède de fonction
d'application de patch, d'appel Git, ni d'exécution de contenu agent.

Une erreur de contrat B reste `ERROR` avec la réponse brute : ni réparée, ni convertie en décision.
Aucune heure de reprise n'est jamais calculée — inconnue reste inconnue.

```json
{ "schema_version": 1, "decision": "REVISER", "analysis": "Critique en Markdown.",
  "findings": [ { "id": "B-arch-001", "severity": "MAJOR", "disposition": "OPEN",
                  "statement": "Le contrat de reprise ne couvre pas…" } ],
  "resolved_changes": ["B-arch-000"] }
```

`decision` ∈ `ACCEPTER` `REVISER` `BLOQUE` · `severity` ∈ `BLOCKING` `MAJOR` `MINOR` `NOTE` `UNKNOWN` ·
`disposition` ∈ `OPEN` `RESOLVED` `WITHDRAWN`.

- Une sévérité absente devient `UNKNOWN` **après** décodage, et le constat **reste ouvert**.
- `resolved_changes` ne cite que des constats **ouverts d'une revue antérieure** — validation référentielle.
- **La décision globale n'est jamais calculée à partir des sévérités** (`C8`).
- `ACCEPTER` avec un constat ouvert `BLOCKING` est **refusé comme incohérent**, jamais transformé.
- `BLOQUE` = information humaine indispensable manquante. Un défaut analysable appelle `REVISER`.

### 5.1 En-tête du livrable — nouveau

`livrable.md` s'ouvre sur un bloc **écrit par le programme**, pas par A :

```markdown
> Politique d'accès de B : NONE — B n'a pas pu vérifier le corpus indépendamment.
> Constats restés ouverts : 3 (dont 0 BLOCKING).  ·  Corpus figé le 2026-09-03.
> **Ce document n'est pas approuvé.** `COMPLETED` signifie « cycle achevé ».
```

**Motif.** `R5` : *la réussite opérationnelle n'est pas une acceptation.* Et deux livrables produits
sous des politiques d'accès différentes n'ont pas le même niveau de preuve : ils ne doivent pas se
présenter pareil. Un statut `AWAITING_APPROVAL` reste différé — le bloc suffit à V0.1.

## 6. Surface CLI

```text
python -m iabinome new COLLAB
    --demande FICHIER
    [--source-root DOSSIER --source-list MANIFESTE]
    [--agent-a ADAPTER] [--model-a MODELE]
    [--agent-b ADAPTER] [--model-b MODELE]
    --reviewer-access {none,read-only}          # OBLIGATOIRE, aucun défaut
    [--max-revisions N]

python -m iabinome run    COLLAB [--timeout SECONDES]
python -m iabinome resume COLLAB [--timeout SECONDES]
                                 [--answer FICHIER | --retry-call UUID --motif TEXTE]
python -m iabinome status COLLAB [--json]
```

Défauts : `max-revisions=2`, `timeout=1800`.

**`--reviewer-access` n'a délibérément pas de valeur par défaut.** C'est l'idée la plus fine de la
proposition de Codex : tant que B-2 est ouvert, un défaut le trancherait par accident. L'obligation
force le choix à être conscient, et il devient visible dans `etat.json` puis dans le livrable.

`new` valide tout dans un dossier temporaire frère, y copie demande et corpus, puis publie par
renommage. Il refuse une destination existante. `run` est l'unique moteur synchrone. `resume`
**ne contient pas un second moteur** : il enregistre l'intervention, remet l'état dans une phase
admissible, et appelle la même fonction. `status` est strictement en lecture seule, et affiche l'âge
de l'instantané de corpus.

Ni `worker`, ni `serve`, ni API, ni commande d'implémentation.

## 7. Adaptateurs et permutations

```python
class AgentAdapter(Protocol):
    adapter_id: str
    capabilities: Capabilities          # supports_no_tools, supports_read_only, supports_model_override
    def probe(self) -> ObservedCli: ...
    def command(self, call: CallSpec) -> list[str]: ...
    def extract(self, stdout: bytes, stderr: bytes) -> str: ...
```

`CallSpec` = prompt, modèle, timeout, **racine de travail (= le dossier de collaboration)**, politique
d'accès. Ni budget, ni session, ni fournisseur, ni rôle métier. Le rôle n'intervient que dans le prompt
et le nom logique de l'appel.

**Seul `adapters/` connaît les noms et options fournisseurs.** Tous les autres modules manipulent
`adapter_id`. *Fait : DialogForge nomme ses fournisseurs dans `models.py` et `factory.py` — c'est ce qui
a rendu sa permutation incomplète.*

**Capacités communes retenues :** appel éphémère · prompt sans fichier externe · réponse texte · modèle
remplaçable · timeout · pas d'écriture hors racine. Sorties structurées natives, sessions, cache, coûts
natifs et reprise fournisseur sont **hors noyau** — un bonus chez l'un ne devient jamais un prérequis (`C15c`).

| A | B | `read-only` | `none` |
|---|---|---|---|
| Claude | Codex | possible | **non démontré** — le shell de Codex n'est pas retirable |
| Codex | Claude | possible | possible (`--tools ""`) |
| Claude | Claude | possible | possible |
| Codex | Codex | possible | **non démontré** |

**Le prévol échoue avant verrou et avant mutation** si la capacité demandée manque. Il ne mémorise
aucune attestation : sondage de présence et version à chaque `run`, version enregistrée dans
`intention.json` comme **preuve factuelle de cet appel**, jamais comme autorité pour le suivant.

### 7.1 Le brut est retenu pour reconstruire le coût — nouveau

`manifeste.json` d'un appel **écrit** que les segments bruts sont conservés afin de permettre une
reconstruction du coût **hors ligne**, par un outil séparé qui n'existe pas encore.

Aucune comptabilité dans le noyau : **zéro ligne de logique**, une phrase. L'interdit n°4 proscrit
budget, réservation et quota *internes* — pas d'observer.

**Motif.** Le PO choisit l'outil par rôle **selon ses crédits** : un outil qui ne laisse aucune trace
exploitable contrarie ce qui a motivé la permutation. `R6` rappelle que la reconstruction sera partielle
— Codex ne remonte pas le coût, Claude sous-déclare l'entrée. C'est une raison de garder le brut, pas
de renoncer.

## 8. Prompts

Le corpus n'est **pas recopié dans le prompt** : un agent autorisé le lit sous `corpus/fichiers/`.
Aucune conversation complète n'est rejouée — seulement la version courante et les constats ouverts.

### Proposition A — modifié

```text
Tu es A, auteur principal d'un travail de conception ou de recherche.
La demande ci-dessous est l'unique autorité fonctionnelle.

Ouvre ta réponse par les questions que cette demande laisse sans réponse et qui
changeraient ton travail. S'il n'y en a pas, dis-le. Puis produis le document.

Le corpus est un instantané figé le <date>, en lecture seule sous corpus/fichiers/,
son manifeste sous corpus/manifeste.json. Il ne reflète pas l'état actuel du projet.

Produis un document Markdown complet et autonome. Distingue faits sourcés, inférences,
recommandations et incertitudes. Cite les chemins logiques utiles. Ne code pas,
n'exécute rien, ne modifie aucun fichier. Retourne seulement le Markdown.

DEMANDE
<demande.md>
```

**Motif de l'ouverture par les questions.** Le cadrage automatique est écarté de V0.1 (§10). Or l'échec
le mieux documenté du corpus est exactement là : `DJBIBLIO-20260810-001` — une question de calibrage
posée par A **restée sans réponse avant validation** a produit une mission livrant 2 espèces sur 20 à 30.
C'est `P18` de l'inventaire, déplacée du cadrage vers la proposition. **Une phrase, zéro appel de plus.**

### Critique B — modifié

```text
Tu es B, contradicteur. Cherche erreurs, omissions, hypothèses fragiles et alternatives
sérieuses dans la proposition courante.

<si NONE>      Tu n'as pas accès au corpus. Signale les affirmations que tu ne peux
               pas vérifier plutôt que de les supposer justes.
<si READ_ONLY> Le corpus est un instantané figé le <date>, sous corpus/fichiers/.

Retourne uniquement le JSON conforme au schéma de revue v1. BLOQUE est réservé à une
information humaine indispensable. Ne déduis pas la décision des seules sévérités, et
ne déclare résolu qu'un identifiant antérieur effectivement traité.

DEMANDE / PROPOSITION COURANTE / CONSTATS OUVERTS
```

**Ce qui change.** La version de Codex disait « si NONE, n'essaie pas de lire une source ». C'est une
**interdiction portée par le prompt**, et `R13` est formelle : *le prompt système ne confine rien.*
L'enforcement existe déjà — le prévol refuse Codex-en-B sous `NONE`. La phrase est donc reformulée en
**information**, et elle devient utile : elle dit à B quoi faire de son ignorance.

### Révision A · Finalisation A

Inchangées par rapport à Codex, plus la mention de l'instantané daté.
Révision : *« Réécris une version complète et autonome qui traite la critique et les constats ouverts.
Ne réponds pas point par point à la place du livrable. Garde visibles les incertitudes non résolues. »*
Finalisation : *« Intègre les apports utiles sans raconter le dialogue. Signale explicitement les
incertitudes et constats restant ouverts. »*

## 9. Tests — fournisseurs toujours faux

`unittest` seul. `FakeAdapter`, `FakeProcess`, `FakeClock`. **Aucun test ne lance Claude, Codex, un
réseau, ni une commande proposée par un agent.**

| Famille | Ce qui est couvert |
|---|---|
| Contrats | JSON nu et bloc unique acceptés ; préfixe, suffixe, deux objets, tableau, clé inconnue, version future refusés · toutes décisions/sévérités/dispositions · sévérité absente → `UNKNOWN` ouvert · identifiants dupliqués, résolution inconnue ou fausse refusées |
| État & stockage | Champ absent, surnuméraire ou inconnu → échec fermé · écriture atomique concurrente, échec avant/après remplacement · aucun chemin absolu persisté · **déplacement complet du dossier puis reprise réussie** |
| Verrou | Détenteur vivant refusé (PID/date/commande) · verrou mort récupéré · jamais la suppression du verrou d'un autre |
| Corpus | Hors racine, `..`, lien sortant, non régulier, empreinte changeante → refus **avant création du dossier final** · date et racine d'origine au manifeste |
| Workflow | `ACCEPTER` · `REVISER` · quota épuisé · `BLOQUE` · artefact écrit avant phase close · transition impossible sans artefact ni empreinte |
| Reprise | Crash simulé aux cinq frontières · `LAUNCHING`/`STARTED` → `INTERRUPTED` sans nouvel appel · `RESPONSE_STORED` retraité localement · **`--retry-call` sans motif refusé** |
| Transport | Timeout, quota, authentification, sortie vide, code non nul, réponse invalide, plafond → un incident durable, aucune boucle · segments reconstitués dans l'ordre · dépassement tue le faux arbre et **n'expose jamais le préfixe** |
| Permutations | **Les quatre** : faux-Claude/faux-Codex, faux-Codex/faux-Claude, et les deux homogènes · mêmes transitions et même contrat dans les quatre cas · adaptateur sans capacité `NONE` refusé au prévol |
| Racine | **La racine passée à l'adaptateur est le dossier de collaboration, dans les quatre permutations.** |
| Frontière | Demande explicitement orientée codage refusée **sans appel** · sortie A contenant un diff ou un bloc shell reste du Markdown · **aucun symbole de production n'applique de code** — l'absence de chemin fonctionnel est plus forte qu'une détection lexicale |

## 10. Budgets — production **et** tests

| Module | Prod. | | Module | Prod. |
|---|---:|---|---|---:|
| `__main__` + `__init__` | 15 | | `prompts.py` | 90 |
| `cli.py` | 170 | | `transport.py` | 180 |
| `models.py` | 150 | | `corpus.py` | 100 |
| `storage.py` | 155 | | `adapters/base.py` | 55 |
| `lock.py` | 90 | | `adapters/__init__.py` | 30 |
| `contracts.py` | 160 | | `adapters/claude.py` | 75 |
| `workflow.py` | 180 | | `adapters/codex.py` | 90 |
| | | | **Production** | **1 540** |

**Tests : 2 300 à 3 000 lignes.** *Inférence, pas mesure.* DialogForge tient un rapport de 0,76
(37 623 / 49 568), mais une machine à états avec reprise et matrice de permutations se teste plutôt à
1,5–2×. **Total réel attendu : 3 800 à 4 500 lignes.**

**Ce chiffre doit être dit.** `CLAUDE.md` annonce « environ 1 500 lignes » sans préciser
« de production ». Un chiffre qui ne dit pas ce qu'il compte est précisément ce qui a laissé
DialogForge grossir sans alarme. La garde reste `POURQUOI` règle 1 — l'outil ne dépasse jamais le
projet servi, et FloraPi pèse 58 894 : on en est loin.

**Ce qui déborde en premier, et ce qu'on coupe alors.** `transport.py` + `workflow.py` = 360 lignes
pour le lancement, le délai dur, la terminaison d'arbre sur **deux OS**, la segmentation bornée de deux
flux, dix étapes de séquence durable et cinq statuts. C'est là que ça cédera.

*Coupes pré-décidées, dans cet ordre :* (1) segmentation multi-fichiers → un seul fichier borné par flux ;
(2) `fsync` du dossier POSIX → `fsync` du fichier seul ; (3) `status --json` → sortie texte seule.
**Jamais coupé :** les cinq frontières d'appel, la matrice des quatre permutations, l'invariant de racine.

**Rien de tout cela n'autorise à ajouter** budget, session, base, worker, GUI, implémentation ou
ordonnancement sous prétexte que DialogForge les avait.

## 11. Décisions à faire arbitrer

### 11.1 — **BLOQUANT** — La recherche V0.1 est-elle corpus-only ?

Codex restreint « recherche » à « recherche dans un corpus fourni » (§3.2). **B-1 a pourtant été
arbitré sur la base des missions bibliographiques de FloraPi, qui interrogeaient des sources externes** —
vérification en texte intégral, indépendance des origines, budget de sources par espèce.

La restriction rend `P26`, `P27`, `P30`, `P33`, `P34` largement inertes.

**Ce qui plaide pour la restriction, et que Codex n'a pas invoqué :** les deux missions bibliographiques
ont échoué, et la cause tracée (`DJBIBLIO-20260813-004`) est que **la question posée à la littérature
portait sur une variable qu'elle ne traite pas** — un défaut de mandat, pas d'accès. Ajouter le Web
n'aurait rien réparé.

**Ma recommandation : corpus-only pour V0.1**, et l'écrire dans `CLAUDE.md` pour que « recherche » ne
promette pas ce qu'il ne fait pas. Le Web reste un contrat de capacité, de preuve et de confinement
distinct — et `P33` (« le critère de fin est défini avant de chercher ») devra être re-lu ce jour-là.

### 11.2 — Autres points, tous déjà nommés par Codex

| | Point | Position |
|---|---|---|
| a | Politique de B — `none` ou `read-only` | Reste ouvert par décision du PO. `--reviewer-access` obligatoire le maintient ouvert sans le trancher. |
| b | Écritures internes des CLI hors collaboration | Non prouvable par lecture de code. **Reformuler la promesse** en « les artefacts *d'IAbinome* sont contenus », et caractériser au prévol réel. |
| c | Identifiants CLI d'Opus 5 et Fable 5 | Aucune source lue ne les établit. À caractériser, sans catalogue historique. |
| d | Corpus binaires ou immenses | Hors V0.1. Politique explicite, pas d'acceptation silencieuse. |
| e | Détection du codage | Une classification lexicale parfaite est impossible. **La vraie barrière est l'absence de capacité** ; le refus sémantique n'est qu'un garde-fou. |
| f | Manifeste de fichiers exacts, sans glob | Accepté — le glob est la première marche vers les paquets thématiques écartés en `X9`. **Mais c'est le premier point d'usage à mesurer** (`R28`) : sur 58 894 lignes, lister à la main pousse à en mettre trop ou à ne pas s'en servir. |
| g | Cadrage absent de V0.1 | Accepté, le risque étant récupéré dans le prompt de A (§8). Un cadrage futur devra produire **exactement le même `demande.md`**, jamais une seconde autorité. |

## 12. Réversibilité

| Recommandation | Réversible sans migration jusqu'à… |
|---|---|
| Noyau neuf plutôt qu'élagage | la création des premiers modules `src/iabinome` |
| Schémas de configuration, état et revue | la première collaboration persistée — ensuite : version incrémentée + migration explicite |
| Corpus copié, chemins relatifs, instantané daté | la première collaboration persistée |
| Manifeste de fichiers exacts, sans glob | la stabilisation de `corpus.py` — un ajout reste compatible, mais chaque règle d'expansion devient un contrat |
| Les quatre commandes CLI | le premier script ou document opératoire publié |
| Contrat B enrichi de `findings` | la première revue B persistée |
| `--retry-call` avec motif obligatoire | la première reprise persistée |
| Absence de cadrage en V0.1 | la stabilisation de `new` |
| Politique B par collaboration | le `new` de chaque collaboration — **changer en cours de cycle altère le niveau de preuve : interdit ou historisé** |
| Capacités communes seules dans le noyau | la publication du protocole `AgentAdapter` — un bonus reste ajoutable, jamais requis par le workflow |
| Recherche corpus-only | l'arbitrage de §11.1, **avant implémentation** |
| Brique de codage future | la validation de cette première brique — nouvelle spécification et décision humaine écrite |

**Le seul choix difficilement réversible** serait de laisser les agents lire des dépôts externes en
persistant leurs chemins absolus. C'est pourquoi la copie du corpus, les chemins logiques relatifs et
l'invariant de racine (§2.1) sont proposés **dès la première version**.

## Limites de preuve de ce document

- Je n'ai pas relu les dix fichiers DialogForge après Codex. Ses verdicts sur la colonne Code sont repris
  **sur sa parole**, sauf cinq recoupés avec mes relevés de récolte.
- **Aucune CLI n'a été lancée.** `--tools ""`, les sandbox Codex et les identifiants de modèles restent
  déduits du code, non caractérisés.
- Les budgets de §10 sont des **ordres de grandeur** tirés du rapport DialogForge, sur du code inexistant.
- Aucune ligne d'IAbinome n'existe. Tout ici est de la conception.

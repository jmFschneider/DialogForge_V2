# IAbinome — conception finale, V0.1

> **Document de spécification.** Écrit le 2026-09-03, au terme de : récolte (156 leçons) → relecture
> contradictoire (42 observations disposées) → structure Codex → critique Claude → révision Claude →
> structure Codex V2 → **cette synthèse**.
> Raisonnement qui y conduit : `ANALYSE_VERS_CONCEPTION_FINALE.md`, à côté.
>
> **Il n'autorise pas à coder.** Arbitrage humain d'abord.
>
> **fait** = vérifié dans une source citée · **inférence** = conséquence non prouvée ·
> **recommandation** = choix proposé · **incertitude** = exige une mesure ou une décision.
>
> **Révisé le 2026-09-03** après une dernière revue technique de Codex : huit remarques, **toutes
> retenues**, disposées dans `DISPOSITION_TECHNIQUE_CODEX.md`. La plus grave — une réponse déjà payée
> perdue à la reprise — est corrigée en §5.

---

## 0. Ce que c'est, en une page

> *« Un système simple où deux agents travaillent ensemble, l'un construit, l'autre révise, critique
> et propose. »* — `POURQUOI.md`, la phrase de départ.

**A produit · B contredit · A révise · l'humain arbitre.** Le livrable est un **document** de
conception ou de recherche. Tout en fichiers sur disque.

```
demande.md → A produit    → echanges/0001-proposition-A.md
             B critique   → echanges/0002-critique-B.json
             A révise     → echanges/0003-revision-1-A.md
             … 2 révisions au plus
             A finalise   → livrables/version_finale.md
```

**Un dossier par collaboration. Un `etat.json` lisible à l'œil nu.** Reprise = relire l'état, repartir
de la dernière phase close. **Interruption = fermer le terminal.**

**A et B sont chacun Claude ou Codex**, choisis au lancement. Quatre permutations. Aucun fournisseur
nommé hors de son adaptateur. Le cycle ne dépend que des capacités **présentes chez les deux** :
ce qui est propre à l'un est un bonus, jamais un prérequis.

Python 3.12, **bibliothèque standard seule**, zéro dépendance de production. **~1 430 lignes.**

### 0.1 Paramètres fixés

| | Valeur | Motif |
|---|---|---|
| **Encodage** | Tout est écrit en **UTF-8 sans BOM, fins de ligne `\n`**, y compris sous Windows. À la lecture, un BOM UTF-8 est toléré, retiré, et **consigné comme transformation** dans la normalisation. | Un dossier de collaboration doit se déplacer entre machines. Le BOM toléré-mais-tracé reprend le comportement du normaliseur de DialogForge. |
| **Plafond de sortie** | **8 MiB par flux**, constante nommée, **sans option de configuration**. Dépassement → terminaison de l'arbre, incident `OUTPUT_LIMIT`, flux conservés comme partiels. | Le plus gros livrable observé pèse 3 850 lignes ≈ 250 Kio. 8 MiB attrape une boucle folle sans jamais gêner un document. Une option serait un réglage de plus à justifier. |
| **Systèmes** | **Windows : supporté et testé.** POSIX : les branches existent et sont écrites, **non testées en V0.1**. | Honnête plutôt que rassurant. Le poste de développement est Windows 11, et le prédécesseur était orienté Windows. Promettre une matrice qu'on ne peut pas exécuter serait une intention documentaire, pas une preuve — `R15`. |

## 1. Périmètre

### Les cinq interdits, opposables

| Interdit | Ce que ça exclut ici |
|---|---|
| **Pas d'exécution autonome** | Aucune fonction de production n'applique un patch, ne lance une commande dérivée d'une réponse, ni ne touche Git. |
| **Pas de base** | Fichiers sur disque. `etat.json` se lit à l'œil. |
| **Pas de worker, bail, tâche planifiée** | Un processus au premier plan. Aucune reprise automatique, aucune heure de reprise calculée. |
| **Pas de budget interne** | Ni réservation, ni quota, ni parseur de coût. |
| **Pas de GUI** | CLI seule. |

Également exclus : session fournisseur persistante · routage adaptatif · conseil d'agents ·
sortie structurée native · client HTTP, navigateur ou téléchargement.

### La frontière d'effets — formulation honnête

**Ce qu'IAbinome garantit :**

1. Il n'écrit que des chemins fermés de son dossier de collaboration.
2. Il ne modifie jamais le corpus d'origine, le projet étudié, Git, ni les dépendances.
3. Il ne transforme **jamais** une sortie d'agent en commande, patch, chemin arbitraire ou transition.
4. Chaque adaptateur reçoit le dossier de collaboration comme `cwd`, et uniquement des chemins relatifs.
5. Un adaptateur incapable du profil demandé est **refusé avant l'appel**.

**Ce que ça ne prouve pas.** `cwd` n'est pas un bac à sable de lecture : une CLI peut lire un chemin
absolu, sa configuration utilisateur, ou tenir ses propres caches. La promesse exacte est donc :

> Tous les artefacts **appartenant à IAbinome** restent dans la collaboration, et IAbinome ne donne
> aucun droit d'écriture sur le projet étudié. La portée de lecture réelle d'une CLI est une limite
> **observée de l'adaptateur**, pas une propriété inventée par le noyau.

*Cette formulation est de Codex (V2 §3), contre ma propre révision qui présentait `cwd` comme un
invariant testé. `R13` — le prompt ne confine rien — vaut pour `cwd` aussi.*

**Aucun bac à sable général n'est reconstruit.** Un opérateur qui exige l'isolation de secrets locaux
lance IAbinome dans un compte dédié ; cette isolation reste extérieure à V0.1.

### Deux natures de mission

- **`CONCEPTION`** — A travaille sur la demande et, s'il existe, l'instantané local du corpus.
- **`RECHERCHE`** — même chose, plus un bloc de prompt qui impose les règles de preuve (§9).

**V0.1 ne consulte aucune source externe.** Le corpus est ce que l'humain y a déposé — y compris des
articles qu'il a rassemblés lui-même. **Décision motivée et réversible : voir §12.1.**

## 2. Le cycle

```text
PROPOSAL_A ─QUESTION──────────────────────────→ WAITING_HUMAN
    │ DOCUMENT
    ▼
REVIEW_B ─BLOQUE──────────────────────────────→ WAITING_HUMAN
    ├─REVISER, limite non atteinte────────────→ REVISION_A → REVIEW_B
    ├─REVISER, limite atteinte────────────────→ FINAL_A
    └─ACCEPTER────────────────────────────────→ FINAL_A

FINAL_A ──────────────────────────────────────→ AWAITING_APPROVAL   (terminal)
```

**Le programme, jamais l'agent, choisit la transition.** Une chaîne qui ressemble à une commande, un
patch ou une instruction d'outil **reste du texte**.

Après `QUESTION` de A ou `BLOQUE` de B, l'humain fournit une **nouvelle demande complète**. L'ancienne
est archivée en `demande.md.001`, la nouvelle devient `demande.md`, son empreinte est republiée dans
l'état. *Motif : une réponse partielle créerait une seconde autorité — `C35` l'interdit.*
Une question née en `PROPOSAL_A` y retourne ; une née en `REVISION_A` ou un `BLOQUE` reprennent en
`REVISION_A`, avec le document courant et les constats déjà ouverts.

**Le cycle se termine en `AWAITING_APPROVAL`, jamais en « succès ».** *Motif : `R5` — la réussite
opérationnelle n'est pas une acceptation.* `version_finale.md` s'ouvre sur une ligne écrite par le
programme, vraie à tout moment :

```markdown
> Ce document n'est pas approuvé : sa présence prouve que le cycle s'est achevé, rien de plus.
> Revue B : CONSULT · constats restés ouverts : 3 (dont 0 BLOCKING) · corpus figé le 2026-09-03.
```

L'arbitrage lui-même appartient à l'humain et à ses documents. **IAbinome ne l'enregistre pas** —
voir `A1` de l'analyse.

## 3. Arborescence

### Programme

```text
IAbinome/
├── pyproject.toml                 # aucune dépendance d'exécution
├── src/iabinome/
│   ├── __init__.py  __main__.py
│   ├── cli.py           models.py     storage.py    lock.py
│   ├── contracts.py     workflow.py   prompts.py
│   ├── transport.py     corpus.py
│   └── adapters/  __init__.py  base.py  claude.py  codex.py
└── tests/
    ├── __init__.py  fakes.py
    └── test_contracts · test_state · test_storage · test_lock · test_corpus
        test_workflow · test_recovery · test_transport · test_permutations · test_cli
```

**Aucun nom de fournisseur hors de `adapters/`.** Le noyau ne manipule que des `adapter_id` opaques.
*Fait : DialogForge nomme ses fournisseurs dans `models.py` et `factory.py` — c'est ce qui a rendu sa
permutation incomplète, et pourquoi sa reprise après quota n'a jamais marché côté Codex.*

### Collaboration

```text
collaboration/
├── configuration.json          # immuable après new
├── demande.md                  # l'unique autorité fonctionnelle
├── demande.md.001              # versions remplacées, immuables
├── etat.json
├── verrou.json                 # transitoire, pendant une commande mutante
├── corpus/
│   ├── manifeste.json
│   └── fichiers/<chemins-logiques>
├── appels/0001-A-<uuid>/
│   ├── intention.json          # avant l'appel — porte aussi le motif de relance
│   ├── prompt.txt
│   ├── stdout.txt  stderr.txt  # au fil de l'eau, bornés
│   ├── resultat.json           # écrit en dernier : sa présence = flux complets
│   ├── reponse_brute.txt
│   ├── revue_normalisee.json   # B seulement
│   └── incident.json           # échec seulement
├── echanges/
│   ├── 0001-proposition-A.md  0002-critique-B.json  0003-revision-1-A.md
└── livrables/version_finale.md
```

**Tous les chemins persistés sont relatifs au dossier de collaboration.** Aucun chemin absolu, nulle
part. *Fait : `configuration.json` de DialogForge en persiste un.*

Le dossier est autonome **pour reprendre le cycle** : le déplacer et reprendre doit fonctionner.

### L'instantané de corpus

`corpus/manifeste.json` : `schema_version`, `captured_at`, `origin_label` (libellé humain), puis pour
chaque fichier son chemin logique, sa taille et son SHA-256. **Aucun chemin absolu.**

**Le corpus est figé.** Il n'existe pas de `refresh` : le changer en cours de cycle détruirait la
référence commune de A et B. Pour une référence plus récente, on crée une collaboration.

**Conséquence sur `--answer` : il remplace la demande, jamais le corpus.** Si la réponse humaine à une
`QUESTION` exige d'autres sources, la collaboration est devenue le mauvais contenant — on en crée une
neuve, la demande peut être reprise telle quelle.
`status` affiche son âge ; les prompts disent sa date. *Motif : `P13` — une affirmation peut avoir
vieilli. Un corpus figé le garantit, donc il faut le dire.*

**Refusés avant publication du dossier :** chemin absolu, `..`, lien sortant, fichier non régulier,
empreinte qui change pendant la copie.

Le manifeste reçoit des **fichiers exacts, un par ligne**. Ni glob, ni découverte. *L'ergonomie de
cette liste est le premier point d'usage à mesurer (`R28`) : sur un projet de 58 894 lignes, elle
poussera à en mettre trop ou à ne pas s'en servir. Glob et paquets thématiques n'entrent qu'après un
problème réel — c'est la première marche vers ce que `X9` a écarté.*

## 4. Configuration et état

```json
// configuration.json — immuable
{ "schema_version": 1, "collaboration_id": "etude-cache",
  "mission_kind": "RECHERCHE", "reviewer_access": "CONSULT", "max_revisions": 2,
  "agent_a": {"adapter_id": "…", "model": "…"},
  "agent_b": {"adapter_id": "…", "model": "…"},
  "initial_demande_sha256": "…", "corpus_manifest_sha256": "…", "created_at": "…" }

// etat.json — dynamique
{ "schema_version": 1, "status": "READY", "phase": "PROPOSAL_A", "revision": 0,
  "demande_sha256": "…", "current_document": null, "latest_review": null,
  "open_finding_ids": [], "current_call": null, "last_incident": null, "updated_at": "…" }
```

**Valeurs fermées.**
`status` ∈ `READY` `RUNNING` `WAITING_HUMAN` `INTERRUPTED` `ERROR` `AWAITING_APPROVAL` ·
`phase` ∈ `PROPOSAL_A` `REVIEW_B` `REVISION_A` `FINAL_A` `CLOSED` ·
`current_call.status` ∈ `CALLING` `RESPONSE_STORED`.

`current_call` porte exactement : UUID, séquence, rôle, phase, statut, dossier logique, empreinte du
prompt, empreinte de réponse (`null` d'abord), horodatages. **Aucune chaîne de fournisseur dans un
identifiant ou un chemin.**

`current_document` et `latest_review` sont des chemins relatifs **explicites** : la reprise ne devine
jamais le contexte d'après un nom de fichier.

> **Version future, enum inconnu, clé absente ou surnuméraire : refus avant toute mutation.**
> Les champs connus sans valeur sont présents avec `null` — ils ne disparaissent jamais.

Les modèles sont **résolus au `new` puis persistés** : une mise à jour du programme ne change jamais
une collaboration existante.

## 5. Protocole d'appel durable

1. **Prévol, sans aucune mutation** — demande, schémas, état, empreintes, corpus, adaptateurs,
   versions observées, modèles, profil de revue.
2. Acquisition du verrou.
3. **Relecture de l'état et des empreintes critiques sous verrou.** Toute différence depuis le prévol
   → refus. *Ferme la fenêtre de concurrence sans passer les sondages coûteux sous verrou.*
4. Création du dossier d'appel, de `intention.json` et du prompt.
   **`current_call.status = CALLING` publié AVANT `Popen`.**
5. Lancement. `stdout`/`stderr` copiés au fil de l'eau dans leurs fichiers, avec compteurs de taille
   et **délai dur**.
6. Dépassement d'un flux → **terminaison de l'arbre de processus**, fichiers conservés comme preuve
   partielle, incident `OUTPUT_LIMIT`. **Rien n'est jamais présenté comme une réponse complète.**
7. Sortie propre → `flush`, `fsync`, écriture de `resultat.json` (code retour, tailles, empreintes),
   extraction de la réponse, publication de `RESPONSE_STORED`.
8. Normalisation locale, **écriture de l'artefact de phase**, puis transition d'état, puis
   `current_call = null`.
9. Libération du verrou.

### Reprise après crash — le dossier d'appel fait foi, pas le seul statut

> **La reprise inspecte le dossier d'appel avant de conclure.** `resultat.json` n'est écrit qu'à la
> sortie propre : **sa présence est la preuve que les flux sont complets.**

| État trouvé | Sur le disque | Conclusion |
|---|---|---|
| `RESPONSE_STORED` | — | Normalisation et transition reprises **localement, sans appel**. |
| `CALLING` | `resultat.json` **valide** | Traité comme `RESPONSE_STORED` : **retraitement local, sans appel**. |
| `CALLING` | pas de `resultat.json` | « Appel possiblement parti, possiblement payé » → `INTERRUPTED`. **Jamais de rejeu automatique.** |

*Motif : sans cette lecture, un crash dans la fenêtre entre l'écriture de `resultat.json` et la
publication de `RESPONSE_STORED` déclarerait incertaine une réponse complète, et forcerait une relance
humaine qui **repaie un appel dont on a déjà la réponse**. C'est exactement le défaut que tout ce
protocole existe pour empêcher.*

### Interruption — ce qui est promis, et ce qui ne l'est pas

`O4` dit « interruption = fermer le terminal ». Concrètement :

- **Ctrl-C** — l'arbre de processus est terminé, l'incident `INTERRUPTED_BY_USER` est écrit, les flux
  partiels sont conservés, l'état reste `CALLING`, sortie en code non nul. La reprise applique la
  table ci-dessus.
- **Fermeture de la console** — au mieux le même traitement ; sous Windows, le délai accordé par
  l'OS peut ne pas suffire. **On ne le promet donc pas.** L'état sur disque dit déjà `CALLING`, ce que
  la reprise sait traiter : **la correction ne dépend jamais d'un nettoyage à la fermeture.**
- **Processus fournisseur orphelin** — possible dans ce dernier cas. Le PID de l'enfant est écrit dans
  `pid.txt` du dossier d'appel dès le retour de `Popen`, **pour qu'un humain puisse le retrouver**.
  IAbinome ne le pourchasse pas au démarrage suivant : ce serait une surveillance, donc un worker.

*Deux statuts suffisent : `PREPARED`, `LAUNCHING` et `STARTED` avaient la même conséquence après
crash, et `APPLIED` dupliquait la phase déjà persistée.*

**Écritures de contrôle** : temporaire unique dans le même dossier, `flush`, `fsync`, `os.replace` ;
`fsync` du dossier sous POSIX ; nouvelle tentative brève sous Windows.
*L'atomicité de publication n'est pas la durabilité — DialogForge ne faisait pas la seconde. **Aucune
garantie de durabilité ne se troque contre des lignes.***

### Relance

`resume --retry-call <uuid> --reason-file F` seulement. Nouvel UUID, lien `retries` vers l'ancien,
**et le motif copié dans l'`intention.json` du nouvel appel**. `F` doit être non vide.

*Motif : `R4` — une relance identique sur le même état est interdite. Le fichier de motif prouve une
décision humaine **attribuable**, pas que la cause a changé ; c'est une trace, pas une preuve, et le
dire évite de s'en croire protégé.* **Aucun plafond de relances** : ce serait un quota interne.

## 6. Contrats

### A — document ou question

La **première ligne** vaut exactement `IABINOME:DOCUMENT` ou `IABINOME:QUESTION`.

Sur `QUESTION`, le reste ne contient que les informations manquantes **qui changeraient
substantiellement le périmètre, la méthode ou la conclusion**. Le programme s'arrête en
`WAITING_HUMAN`. Sur `DOCUMENT`, le reste est le Markdown.

**Une balise absente ou inconnue est une erreur de contrat** : réponse brute préservée, état `ERROR`,
main rendue. *Jamais de défaut permissif — `C2b`.*

**Le discriminateur s'applique aux quatre appels de A**, finalisation comprise. *Un seul analyseur,
aucun cas particulier — l'exception coûterait un second chemin et ses tests, l'uniformité ne coûte
rien. Et un `QUESTION` en finalisation reste légitime : mieux vaut s'arrêter que livrer un document
dont A sait qu'il manque l'essentiel. Aucune boucle possible — chaque `QUESTION` exige une action
humaine.*

*Cette porte remplace un cadrage automatique entier (`framing.py` et un appel de plus). Elle répare
l'échec le mieux documenté du corpus : `DJBIBLIO-20260810-001`, une question de calibrage restée sans
réponse avant validation, 2 espèces livrées sur 20 à 30 attendues. **Elle retire plus qu'elle
n'ajoute.***

### B — revue

```json
{ "schema_version": 1, "decision": "REVISER",
  "analysis": "Critique synthétique en Markdown.",
  "findings": [ { "id": "B-architecture-001", "severity": "MAJOR",
                  "disposition": "OPEN", "statement": "La reprise ne couvre pas…" } ] }
```

`decision` ∈ `ACCEPTER` `REVISER` `BLOQUE` · `severity` ∈ `BLOCKING` `MAJOR` `MINOR` `NOTE` `UNKNOWN` ·
`disposition` ∈ `OPEN` `RESOLVED` `WITHDRAWN`.

- **Un registre unique, une vérité par constat.** À chaque revue, B reprend **exactement une fois**
  chaque constat antérieurement ouvert, puis peut en ajouter. Le programme dérive `open_finding_ids`
  de cette seule liste. *`resolved_changes` est supprimé : il doublonnait `disposition` et pouvait
  diverger.*
- Sévérité omise → `UNKNOWN` **après** décodage, et le constat **reste ouvert**.
- Clé inconnue, décision inconnue, identifiant dupliqué, ou **disparition d'un constat antérieur** →
  échec du contrat, réponse brute préservée.
- Un unique bloc JSON clôturé couvrant toute la réponse est accepté ; préfixe, suffixe ou second objet
  sont refusés.
- **La décision globale n'est jamais calculée à partir des sévérités.** Une combinaison surprenante
  reste visible pour l'humain ; le programme ne la réécrit pas en consensus apparent.
- `ACCEPTER` avec un constat ouvert `BLOCKING` : **la décision de B est conservée telle quelle**, la
  revue est persistée, l'incohérence est inscrite dans `last_incident`, et l'état passe en
  `WAITING_HUMAN`. *Le programme ne juge pas sur les sévérités — pas même pour refuser. Et rejeter la
  revue comme erreur de contrat perdrait des constats qui peuvent être bons. `R29` : ambiguïté, main
  à l'humain.*
- `BLOQUE` = information humaine indispensable manquante. Un défaut analysable appelle `REVISER`.

## 7. Surface CLI

```text
python -m iabinome new COLLAB
    --demande FICHIER
    --kind {conception,recherche}
    --reviewer-access {context-only,consult}          # OBLIGATOIRE, sans défaut
    --agent-a ADAPTER --agent-b ADAPTER               # OBLIGATOIRES, sans défaut
    [--source-root DOSSIER --source-list MANIFESTE] [--source-label TEXTE]
    [--model-a MODELE] [--model-b MODELE]
    [--max-revisions N]

python -m iabinome run    COLLAB [--timeout SECONDES]
python -m iabinome resume COLLAB [--timeout SECONDES]
                          [--answer NOUVELLE_DEMANDE | --retry-call UUID --reason-file FICHIER]
python -m iabinome status COLLAB [--json]
```

Défauts : `max-revisions=2`, `timeout=1800`.

**Trois options sans valeur par défaut : `--reviewer-access`, `--agent-a`, `--agent-b`.**
Pour la première, un défaut trancherait B-2 par accident et le choix change le niveau de preuve du
livrable. Pour les deux autres : **le PO choisit selon ses crédits, la valeur change à chaque
lancement — une valeur qui change à chaque fois ne doit pas avoir de défaut.** Cela retire aussi une
décision du code.

**Le modèle, lui, garde un défaut — résolu par l'adaptateur pour le rôle.** « Opus 5 pour A » n'a
aucun sens si A est Codex : le défaut est une propriété de l'adaptateur, jamais une constante du
noyau. Il est résolu au `new` puis persisté. *Cela garde les noms de fournisseurs dans `adapters/` —
`C15b` — et corrige `CLAUDE.md` §6, qui les énonçait comme des défauts globaux.*

**En recherche, `--source-root` et `--source-list` sont obligatoires et le corpus doit être non vide.**
*V0.1 n'a aucun accès externe : sans corpus, une mission de recherche n'a rien à chercher.*

`new` fait tous ses prévols dans un répertoire temporaire frère, y copie demande et corpus, puis
publie par renommage. Il refuse une destination existante.
`run` est l'unique moteur synchrone. `resume` **ne contient pas un second moteur** : il enregistre
l'intervention, remet l'état dans une phase admissible, et appelle le même moteur.
`status` est strictement en lecture seule : âge du corpus, politique de revue, constats ouverts, phase.

**Il n'existe ni `worker`, ni `serve`, ni `implement`, ni `apply`, ni `watch`, ni `repair`.**

## 8. Adaptateurs et permutations

```python
class AgentAdapter(Protocol):
    adapter_id: str
    capabilities: Capabilities        # supports_context_only, supports_model_override
    def probe(self) -> ObservedCli: ...
    def command(self, call: CallSpec) -> list[str]: ...
    def extract(self, stdout: bytes, stderr: bytes) -> str: ...
```

`CallSpec` = prompt, modèle, délai, racine de travail, profil de revue. **Ni fournisseur, ni budget,
ni session, ni rôle métier.** Le rôle n'intervient que dans le prompt et le nom logique de l'appel.

**Capacités de noyau** — communes aux deux, exigées : appel éphémère · prompt sans fichier externe ·
réponse texte · modèle remplaçable · délai · pas d'écriture du projet.

**Hors noyau** : sortie structurée native, session persistante, métriques de coût, erreur de quota
typée. *Un bonus chez l'un ne devient jamais un prérequis — `C15c`. DialogForge a bâti sa reprise
après quota sur l'erreur typée de Claude ; côté Codex, elle n'a jamais marché.*

| A | B | `consult` | `context-only` |
|---|---|---|---|
| Claude | Codex | possible | **non démontré** — le shell de Codex n'est pas retirable |
| Codex | Claude | possible | possible (`--tools ""`) |
| Claude | Claude | possible | possible |
| Codex | Codex | possible | **non démontré** |

Le prévol **échoue avant verrou et avant mutation** si le profil demandé n'est pas supporté. Il ne
mémorise **aucune attestation** : sondage de présence et version à chaque `run`, version inscrite dans
`intention.json` comme **preuve factuelle de cet appel**, jamais comme autorité pour le suivant.

**Les sorties brutes et la version observée sont conservées par appel** afin de permettre une
reconstruction du coût **hors ligne**, par un outil qui n'existe pas. Aucun parseur, aucune
comptabilité : une phrase, zéro ligne de logique. *Motif : le choix de l'outil par rôle dépend des
crédits du PO. `R6` rappelle que la reconstruction sera partielle — Codex ne remonte pas le coût,
Claude sous-déclare l'entrée.*

## 9. Prompts

*Ils portent des critères intellectuels, pas un pseudo-confinement : les capacités sont fixées avant
leur construction. `O8` — alléger, ne pas durcir.*

### A — proposition

```text
Tu es A, auteur principal. La demande ci-dessous est l'unique autorité.

Commence par IABINOME:QUESTION si une information absente changerait substantiellement
le périmètre, la méthode ou la conclusion ; pose alors seulement ces questions.
Sinon commence par IABINOME:DOCUMENT et produis un document Markdown autonome.

Distingue faits, inférences, recommandations et incertitudes. Nomme tes limites de
preuve. Chaque recommandation dit jusqu'à quand elle est réversible et quel acte
la referme.

Tu ne modifies aucun fichier et n'exécutes rien. Proposer des modifications DANS le
document est au contraire ce qu'on attend de toi.

Le corpus local est un instantané du <date>, sous corpus/fichiers/.

DEMANDE
<demande.md>
```

**Ajout `RECHERCHE` seul :**

```text
Cite les sources localisables et leur niveau d'accès réellement vérifié. La source
primaire prime ; qualifie résumé et reprise secondaire. Deux reprises d'une même
origine ne font pas deux preuves. Distingue absent, nul, négatif, inconnu et non
prouvé. Un résultat négatif documenté est un résultat. Conserve contre-preuves,
biais et contextes non couverts. Borne chaque conclusion au contexte étudié.
Si le critère de fin manque, rends QUESTION.
```

### B — critique

```text
Tu es B, contradicteur. Cherche omissions, contradictions, faits non établis,
contre-preuves et alternatives sérieuses.

<si CONTEXT_ONLY> Tu ne disposes que des éléments ci-dessous ; qualifie ce que tu ne
                  peux pas vérifier.
<si CONSULT>      Le corpus local est un instantané du <date>, sous corpus/fichiers/.

Retourne seulement le JSON de revue v1. BLOQUE est réservé à une information humaine
indispensable. Reprends chaque constat antérieur exactement une fois et motive toute
fermeture. Ne déduis pas la décision des sévérités.

DEMANDE / DOCUMENT COURANT / CONSTATS ANTÉRIEURS
```

*La ligne d'accès **informe**, elle n'interdit pas : le prévol fait déjà le travail, et `R13` dit que
le prompt ne confine rien.*

### A — révision · A — finalisation

```text
Tu es A. Rends QUESTION si un constat révèle une information humaine indispensable.
Sinon rends DOCUMENT, puis une version complète qui traite la critique sans masquer
les désaccords ni les limites restantes. Ne réponds pas point par point à la place
du livrable.
```

```text
Tu es A. Rends QUESTION s'il manque encore une information humaine indispensable.
Sinon rends DOCUMENT, puis le document final autonome à partir de la version
courante. Intègre les apports utiles sans raconter le dialogue. Garde visibles les
incertitudes, les non-décisions et les constats encore ouverts.
```

## 10. Tests

**Tous les appels passent par `FakeAdapter`. Aucun fournisseur, aucun réseau, aucun coût.**
`FakeProcess` et `FakeClock` simulent flux, délai et crash. `unittest` seul.

| Famille | Cas essentiels |
|---|---|
| Contrats A | `DOCUMENT` · `QUESTION` · **balise absente ou inconnue → erreur de contrat**, brut préservé |
| Contrats B | JSON nu ou bloc unique clôturé · version, clé, enum invalides · sévérité manquante → `UNKNOWN` ouvert · constat antérieur omis ou dupliqué refusé · fermeture motivée · **décision jamais déduite** · `ACCEPTER` + `BLOCKING` ouvert refusé |
| État | Schéma strict · chaque phase · empreinte de demande · terminal `AWAITING_APPROVAL` |
| Stockage | Temporaires uniques · publication atomique · échec simulé avant et après `os.replace` · **aucun chemin absolu persisté** · **déplacement complet puis reprise** |
| Verrou | PID/date/commande · détenteur vivant refusé · verrou mort récupéré · **jamais la suppression du verrou d'un autre** |
| Corpus | Hors racine, `..`, lien sortant, non régulier, empreinte changeante → refus **avant publication** · date et libellé · âge affiché · **aucune actualisation silencieuse** |
| Appel durable | Crash en `CALLING` **sans** `resultat.json` → `INTERRUPTED` sans appel · **crash en `CALLING` AVEC `resultat.json` valide → retraité localement, sans appel** · crash en `RESPONSE_STORED` → retraitement local · artefact avant transition · UUID sans nom de fournisseur |
| Interruption | Ctrl-C → arbre terminé, incident écrit, flux partiels conservés, état `CALLING` · `pid.txt` présent dès le lancement |
| CLI | `--agent-a`/`--agent-b`/`--reviewer-access` manquants → refus · recherche sans corpus ou corpus vide → refus · `--answer` ne touche pas au corpus |
| Encodage | Écriture UTF-8 sans BOM, `\n` · lecture d'un BOM tolérée, retirée et **consignée comme transformation** |
| Reprise | Relance sans motif refusée · motif copié · nouvel UUID lié · nouvelle demande complète remplace l'autorité · ancienne archivée · options incompatibles refusées |
| Transport | Deux flux concurrents · sortie vide · code non nul · délai · arbre terminé · plafond dur · **partiel jamais présenté comme complet** |
| Accès | Profil non supporté refusé **avant mutation** · `cwd` transmis = collaboration, **sans prétendre tester une isolation OS** |
| Permutations | **Les quatre couples** parcourent le cycle complet, même workflow, même contrat |
| Frontière | Diff, bloc shell ou URL dans une sortie restent du texte · **aucun symbole de production n'applique ni n'exécute** — l'absence de chemin fonctionnel vaut mieux qu'une détection lexicale |
| Clarification | `QUESTION` arrête avant B · demande révisée relance A · demande courante reste l'autorité unique |

### Validations manuelles, hors suite

Un appel jetable par adaptateur pour caractériser §12.2 · un processus local avec enfant tué par délai
sur chaque OS supporté · déplacement réel d'une collaboration puis reprise · première mission
conception et première mission recherche observées, **avec la friction du manifeste notée**.

*Elles ne deviennent ni campagne d'attestation, ni appel fournisseur dans les tests.*

## 11. Budget et règle de coupe

| Module | Lignes | | Module | Lignes |
|---|---:|---|---|---:|
| `__init__` + `__main__` | 15 | | `prompts.py` | 95 |
| `cli.py` | 155 | | `transport.py` | 160 |
| `models.py` | 130 | | `corpus.py` | 90 |
| `storage.py` | 140 | | paquet `adapters/` | 230 |
| `lock.py` | 90 | | | |
| `contracts.py` | 150 | | **Production visée** | **~1 430** |
| `workflow.py` | 175 | | **Bande acceptable** | **1 350 – 1 550** |

**Tests : 1 100 – 1 800 lignes.** *Ordre de grandeur de planification, non normatif.* Le rapport de
DialogForge (0,76 sur 49 568 lignes) **n'est pas transposable** à une machine dix fois plus petite.

**Si la production dépasse la bande**, dans cet ordre :
1. retirer les sorties de confort (`status --json`, mise en forme riche) ;
2. fusionner les abstractions à un seul appelant ;
3. retirer toute détection lexicale des demandes de code — **la vraie barrière est l'absence de
   capacité**, pas le refus sémantique ;
4. retirer les métadonnées facultatives d'origine ;
5. **s'arrêter et demander arbitrage.**

**Jamais sacrifiés pour tenir un chiffre :** état strict · absence de rejeu automatique ·
délai dur et terminaison d'arbre · `fsync` et publication atomique · artefact avant transition ·
les quatre permutations · registre de constats · porte `QUESTION` · terminal non ambigu.

> **Ajouter un contrôle exige toujours de nommer ce qui sort en échange.** — `POURQUOI` règle 2

## 12. Décisions ouvertes et portes de caractérisation

### 12.1 — Sources externes en recherche : **écartées de V0.1**

**Décision.** V0.1 ne consulte aucune source externe. Le corpus est ce que l'humain y dépose.

**Motifs.** (a) Les deux missions bibliographiques de FloraPi ont échoué, et la cause tracée
(`DJBIBLIO-20260813-004`) est que **la question posée à la littérature portait sur une variable
qu'elle ne traite pas** — un défaut de mandat, pas d'accès. (b) Aucune capacité de consultation
externe commune aux deux adaptateurs n'est démontrée : la spécifier reviendrait à écrire un mode
**indisponible**, ce que `O9` proscrit.

**Ce qui reste vrai de `O7`.** La recherche est au périmètre : le type de mission existe, et les
règles de preuve de §9 mordent sur un corpus documentaire comme sur le Web. Ce qui change, c'est
**qui rassemble** — l'humain dépose, le binôme analyse et contredit.

**Condition de réouverture.** Une consultation externe démontrée chez **les deux** adaptateurs, plus
un contrat de preuve : URL, date d'accès, niveau d'accès et extrait conservés dans le livrable — le
Web n'est pas immuable. Ce jour-là, relire d'abord « le critère de fin est défini avant de chercher ».

*C'est la décision la plus réversible-si-fausse du document, et la plus facile à rouvrir.*

### 12.2 — Ce qui doit être mesuré avant de figer la spécification

**Aucune CLI n'a jamais été lancée.** Tout ce document déduit du code lu.

1. Invocation éphémère canonique et remplacement de modèle, pour chaque CLI.
2. **Réalité ou absence du mode sans outils** — c'est ce qui décide B-2.
3. Identifiants CLI exacts des modèles par défaut.
4. Fichiers éventuellement écrits par une CLI hors de la collaboration.
5. Comportement du délai et de la terminaison d'arbre sous Windows.

*Ce relevé n'entre pas dans la suite automatisée et ne devient pas une attestation durable.*

### 12.3 — B-2, toujours ouvert

`CONTEXT_ONLY` ou `CONSULT`. **Recommandation : `CONSULT`** — `CONTEXT_ONLY` n'est pas mécaniquement
disponible pour Codex d'après le code lu, et contredirait donc les quatre permutations obligatoires.

Si l'humain choisit `CONTEXT_ONLY`, il faut **soit** démontrer une invocation Codex sans outils,
**soit** rouvrir la contrainte des quatre permutations. **Aucun wrapper de confinement général n'est
proposé** pour résoudre artificiellement ce conflit.

`--reviewer-access` reste obligatoire et sans défaut tant que ce n'est pas tranché.

### 12.4 — Reporté, tracé

La colonne **Code** de l'inventaire plus longue que **Prompt** — à rediscuter après la phase 2, avec
du code réel sous les yeux.

## 13. Réversibilité

| Choix | Réversible sans migration jusqu'à… |
|---|---|
| Noyau neuf plutôt qu'élagage de DialogForge | le premier module de production |
| Schémas configuration / état / revue | la première collaboration persistée — ensuite : version incrémentée et migration |
| Deux statuts d'appel | le premier incident persisté |
| Un fichier borné par flux | la publication de `transport.py` |
| Porte A `QUESTION` | le gel du contrat A |
| Absence de cadrage séparé | la stabilisation de `new` — ajoutable en amont, **jamais comme seconde autorité** |
| Registre sans `resolved_changes` | la première revue persistée |
| **Terminal `AWAITING_APPROVAL` sans statut d'approbation** | la première collaboration achevée — un `APPROVED`/`REJECTED` s'insère après, sans migration |
| Corpus figé, chemins relatifs, instantané daté | la première collaboration créée — **une référence plus récente = une nouvelle collaboration** |
| **Sources externes écartées** | l'arbitrage de §12.1, **avant implémentation** |
| Politique de revue | le `new` de chaque collaboration — **changer en cours de cycle est interdit** : le niveau de preuve du livrable en dépend |
| Capacités communes seules dans le noyau | la publication du protocole `AgentAdapter` |
| Surface CLI | le premier script ou document opératoire publié |

**Le seul choix difficilement réversible** serait de laisser les agents lire des dépôts externes en
persistant des chemins absolus. C'est pourquoi la copie du corpus et les chemins logiques relatifs
sont proposés **dès la première version**.

**La porte du codage reste extérieure à ce noyau.** Elle exigera une spécification neuve et une
décision humaine écrite. **Aucun composant n'est préparé « au cas où ».**

## Limites de preuve

- **Aucune CLI n'a été lancée.** `CONTEXT_ONLY`, `CONSULT` et la consultation externe sont des
  contrats **proposés**, pas des capacités démontrées.
- Les dix fichiers DialogForge ont été audités une fois, par Codex, en V1 ; je n'ai recoupé que cinq
  de ses verdicts avec mes relevés de récolte. Le reste est repris **sur sa parole**.
- Les fourchettes de lignes portent sur du code qui n'existe pas.
- **Deux coupes sont des jugements, pas des faits** : l'appareil d'approbation (`A1`) et le mode de
  recherche externe (`A2`). Argumentés dans `ANALYSE_VERS_CONCEPTION_FINALE.md`, réversibles ci-dessus.
- La qualité réelle de la porte `QUESTION`, du registre de constats et des prompts ne se jugera
  qu'après les premières missions. **Une friction observée doit être notée avant d'être généralisée.**

# Analyse — de la V2 de Codex à la conception finale

> Écrit le 2026-09-03. C'est le raisonnement qui produit `CONCEPTION_FINALE.md`, à côté.
> Méthode imposée par le PO : **Codex n'a pas participé à l'échange fondateur.** Il peut donc glisser
> vers des ajouts justifiés isolément, qui n'ont jamais été opposés au total — le mécanisme exact
> qui a produit 87 382 lignes.
> Chaque section applique `POURQUOI` règle 2 : *la bonne question n'est pas « est-ce utile ? », c'est
> « qu'est-ce que je retire en échange ? »*

---

## 1. Les objectifs fondateurs, tels qu'ils ont été dits

Ils ne sont pas dans la V2 parce qu'ils n'ont jamais été écrits pour Codex. Les voici, avec leur source.

| # | Objectif | Source |
|---|---|---|
| O1 | *« Un système simple où deux agents travaillent ensemble, l'un construit, l'autre révise, critique et propose. »* | `POURQUOI.md` — la phrase de départ, mot pour mot |
| O2 | **~1 500 lignes.** L'outil ne dépasse jamais le projet qu'il sert. | `POURQUOI` règle 1, `CLAUDE.md` §1 |
| O3 | **Cinq interdits** : exécution autonome · base · worker/bail/tâche planifiée · budget interne · GUI | `CLAUDE.md` §2 |
| O4 | **Un dossier par collaboration. Un `etat.json` lisible à l'œil nu.** Reprise = relire l'état. **Interruption = fermer le terminal.** | `DEPART.md`, `REPRISE_LITE.md` |
| O5 | Le livrable est un **document**. Révisions bornées, défaut 2, **arbitrage humain en fin de boucle**. | `DEPART.md` |
| O6 | **A et B sont chacun Claude ou Codex.** Le cycle ne dépend que des capacités communes. | PO, 2026-09-03 |
| O7 | **Conception et recherche.** | PO, 2026-09-03 |
| O8 | **Alléger les prompts, ne pas les durcir.** | `POURQUOI` règle 4 |
| O9 | Avant d'ajouter un garde-fou, vérifier qu'il **compense un défaut encore réel**. | `POURQUOI` règle 3 |

**O4 est le plus fragile de tous, et c'est celui que personne ne surveille.** « Lisible à l'œil nu » et
« fermer le terminal » sont des objectifs d'**ergonomie**, pas de correction. Aucune revue ne les
défend spontanément, parce qu'aucun défaut mesuré ne les invoque. Ils tombent en premier.

---

## 2. Ce que la V2 fait mieux que ma propre révision

À dire avant de critiquer, sinon la critique n'est pas honnête.

### 2.1 Elle m'a pris en flagrant délit de ce que je lui reprochais

Mon constat `B-002` demandait un **« invariant testé »** : la racine lisible d'un agent est exactement
le dossier de collaboration. La V2 refuse, et elle a raison :

> `cwd` n'est pas un bac à sable de lecture. Une CLI peut lire un chemin absolu, sa configuration
> utilisateur ou des fichiers voisins.

**J'avais fait exactement ce que je reprochais à Codex en `B-008`** : présenter comme une frontière
mécanique quelque chose qui n'en est pas une. `R13` s'applique à `cwd` comme au prompt. Sa
reformulation — ce qu'IAbinome garantit / ce que ça ne prouve pas — est la bonne, et je la reprends
telle quelle.

### 2.2 Trois simplifications réelles, que je n'avais pas vues

| | La V2 | Pourquoi c'est juste |
|---|---|---|
| **Cinq statuts d'appel → deux** (`CALLING`, `RESPONSE_STORED`) | `PREPARED`, `LAUNCHING`, `STARTED` avaient **la même conséquence après crash** ; `APPLIED` dupliquait la phase déjà persistée. | Un état qui ne change aucun traitement n'est pas un état. Sert directement `O4`. |
| **Segments → un fichier borné par flux** | Ma ligne `C24` prescrivait une segmentation que l'audit a montrée **inexistante dans DialogForge** : c'était un correctif proposé, pas un acquis. | Même garantie, moins de mécanisme. Sert `O2`. |
| **`resolved_changes` supprimé** au profit d'un registre unique à `disposition` obligatoire | Deux sources de vérité pour la fermeture d'un constat, qui pouvaient diverger. | Un registre, une vérité. |

### 2.3 La porte `QUESTION` est meilleure que ma correction

Mon `B-006` faisait ouvrir la proposition de A par les questions restées ouvertes. **Ça n'empêchait
pas A de travailler malgré elles** — exactement le défaut mesuré de `DJBIBLIO-20260810-001`. La porte
`IABINOME:QUESTION` **arrête le cycle**. C'est la bonne réponse, et elle reste sans appel supplémentaire.

### 2.4 Elle refuse mon extrapolation de volume de tests

Mon `B-005` chiffrait 2 300–3 000 lignes de tests par le rapport DialogForge (0,76 sur 49 568 lignes).
La V2 répond que ce rapport n'est pas transposable à une machine dix fois plus petite. **C'est juste :
j'ai transporté une mesure hors de son domaine, ce que `P29` de mon propre inventaire interdit.**

---

## 3. L'audit d'accrétion — sept ajouts opposés au total

Chacun est justifiable isolément. Aucun n'a été mis en regard de `O1`, `O2` et `O4`.

### A1 · L'appareil d'approbation — **retiré**

**Ce que la V2 ajoute.** Trois statuts (`AWAITING_APPROVAL`, `APPROVED`, `REJECTED`), une phase
`HUMAN_APPROVAL`, un fichier `decision_humaine.json`, deux options CLI (`--approve`, `--reject`),
plus leurs transitions et leurs tests.

**D'où ça vient.** De mon constat `B-009`, où je demandais **une ligne d'en-tête** dans le livrable
disant « non approuvé ». La V2 écrit : « un avertissement dans le livrable aide, mais l'état doit
aussi distinguer… ». C'est un renforcement, pas une correction.

**Ce qu'on retire en échange : rien.** Et c'est le test.

**Ce que `--approve` fait mécaniquement : il écrit un fichier.** Rien en aval ne le consomme. Aucune
transition ne dépend de sa valeur. Le cycle est fini dans les deux cas. On ajoute six concepts, deux
options et une famille de tests pour enregistrer une décision qui **n'a aucune conséquence dans le
programme**.

C'est la définition du contrôle qui a fait exploser le prédécesseur : utile isolément, sans effet,
jamais opposé au total.

**Retenu :** le cycle se termine en `AWAITING_APPROVAL` — la V2 a raison de refuser un `COMPLETED`
ambigu — et `version_finale.md` s'ouvre sur la ligne d'avertissement. **Retiré :** `APPROVED`,
`REJECTED`, `HUMAN_APPROVAL`, `decision_humaine.json`, `--approve`, `--reject`.

**Contre-argument, à peser.** `O5` dit « arbitrage humain en fin de boucle ». Mais arbitrer n'est pas
la même chose que **tracer qu'on a arbitré**. IAbinome produit des documents : la décision de l'humain
appartient à un document, pas à une machine à états. *Réversible : le statut peut être ajouté plus
tard sans migration, il s'insère après `AWAITING_APPROVAL`.*

### A2 · Le mode de recherche externe — **spécifié, pas construit**

**Ce que la V2 ajoute.** `--research-access {corpus-only,external}`, `research_access` en
configuration, une capacité `EXTERNAL_READ`, et un cadre de « capacités conditionnelles » dans le
contrat d'adaptateur — le tout **conditionné à une caractérisation qui n'a pas eu lieu**.

**Ce que ça viole.** `O9` : *avant d'ajouter un garde-fou, vérifier qu'il compense un défaut encore
réel.* Ici : avant de spécifier un mode, vérifier qu'il est nécessaire et disponible. Ni l'un ni
l'autre n'est établi.

**Le fait que la V2 n'a pas.** Les deux missions bibliographiques de FloraPi ont échoué, et la cause
tracée (`DJBIBLIO-20260813-004`) est que **la question posée à la littérature portait sur une variable
qu'elle ne traite pas.** Le défaut était dans le mandat. L'accès externe n'aurait rien réparé.

**Ce qui reste vrai de `O7`.** La recherche est au périmètre : le type de mission existe, et les
règles de preuve `P26`–`P34` s'appliquent — indépendance des origines, résultat négatif qui compte,
portée bornée, critère de fin défini avant de chercher. Elles mordent **sur un corpus documentaire
comme sur le Web**. Ce qui change, c'est **qui rassemble** : l'humain dépose, le binôme analyse et
contredit. C'est cohérent avec « l'humain arbitre ».

**Retiré de V0.1 :** `--research-access`, `research_access`, `EXTERNAL_READ`, le cadre des capacités
conditionnelles. **Conservé :** `mission_kind` (deux valeurs, choisit un bloc de prompt) et la
décision d'accès externe, **nommée avec sa condition de réouverture**, en §12 du document final.

*C'est la décision la plus réversible-si-fausse de tout le document, et la plus facile à rouvrir.*

### A3 · Le versionnement des demandes — **simplifié**

**Ce que la V2 ajoute.** Un dossier `demandes/`, un compteur `demande_revision`, et `demande_sha256`
dans l'état.

**Ce qui est juste :** qu'une réponse humaine remplace la demande **entière** plutôt que d'en créer
une seconde autorité. C'est `C35`, et c'est bien vu.

**Ce qui est de trop :** le compteur est dérivable des fichiers, et le dossier est un concept pour
un seul type de contenu.

**Retenu :** `demande_sha256` dans l'état — nécessaire pour détecter qu'on reprend contre un autre
mandat. Les versions précédentes sont archivées **à côté**, `demande.md.001`, sans dossier ni compteur.

### A4 · Le renommage `.part` → `.bin` — **retiré**

`resultat.json` n'est écrit qu'à la sortie propre : **sa présence est déjà le marqueur de complétude.**
Le renommage donne la même garantie une seconde fois. Deux mécanismes pour un fait.

**Retenu :** `stdout.txt`, `stderr.txt` écrits au fil de l'eau, bornés ; `resultat.json` écrit en
dernier. Un flux sans `resultat.json` est incomplet, et c'est visible à l'œil — `O4`.

### A5 · Le champ `rationale` des constats — **retiré**

Deux champs de texte libre par constat là où un suffit, avec la validation et les tests qui vont avec.
**Rien de mécanique ne consomme `rationale`.**

L'argument structurel de la refonte documentaire visait les revues d'**implémentation**, où une action
devait être extraite mécaniquement. Ici, personne n'extrait rien : c'est A qui lit.

**Retenu :** `statement`, et le prompt demande qu'il porte la conséquence. `O8` — alléger.

### A6 · `origin_revision` / `--source-revision` — **retiré**

Métadonnée facultative. La V2 la place elle-même dans sa propre liste de coupe (§12, point 4).
Autant ne pas l'écrire. `origin_label` reçoit la révision si l'humain le veut.

### A7 · Le dossier `interventions/` — **retiré**

Il portait deux natures : la question de A, déjà présente dans `reponse_brute.txt` de son appel ; et
le motif de relance, qui a sa place dans l'`intention.json` du **nouvel** appel — là où on le cherche.
Un dossier de moins, une place plus juste.

---

## 4. Ce que je ne coupe pas, et pourquoi

Trois choses coûtent du mécanisme et restent. Il faut le dire, sinon la coupe n'est pas honnête.

| | Coût | Pourquoi ça reste |
|---|---|---|
| **La porte `IABINOME:QUESTION`** | Une analyse de première ligne dans chaque réponse de A, et un mode d'échec si la balise manque. | Elle répare **l'échec le mieux documenté du corpus** — une question de calibrage sans réponse a livré 2 espèces sur 20 à 30. Elle remplace un cadrage entier (`framing.py`, ~80 lignes de prompt et un appel de plus). Elle **retire** plus qu'elle n'ajoute. |
| **La double lecture sous verrou** | ~5 lignes. | Le prévol est hors verrou ; sans relecture, la fenêtre est réelle. Le verrou existe parce que deux processus peuvent exister — c'est un défaut mesuré (`H-04`). |
| **`fsync` et `os.replace`** | ~15 lignes, dont le `fsync` de dossier POSIX. | La V2 a raison contre ma propre liste de coupes : je proposais de sacrifier `fsync` pour tenir un chiffre. **Une garantie de durabilité ne se troque pas contre des lignes.** J'avais tort. |

**Une balise manquante en tête d'une réponse de A est une erreur de contrat**, réponse brute
préservée, main rendue à l'humain. La V2 ne le disait pas ; `C2b` l'impose — échec fermé, jamais de
défaut permissif.

---

## 5. Le compte

| | V2 de Codex | Conception finale |
|---|---:|---:|
| Statuts d'`etat.json` | 8 | **6** |
| Phases | 6 | **5** |
| Statuts d'appel | 2 | 2 |
| Options CLI | 16 | **12** |
| Fichiers par appel | jusqu'à 9 | **jusqu'à 6** |
| Concepts de dossier dans la collaboration | 6 | **4** |
| Champs de constat | 5 | **4** |
| Production visée | 1 555 (bande 1 400–1 650) | **~1 430 (bande 1 350–1 550)** |

**~125 lignes de production retirées, et surtout six concepts.** Le total repasse sous la promesse
fondatrice de `CLAUDE.md`, sans qu'aucune garantie de correction ait été échangée : les cinq coupes
portent sur de la comptabilité, pas sur de la sûreté.

**Tests : 1 100–1 800 lignes**, ordre de grandeur de planification, non normatif. J'abandonne mon
extrapolation par le rapport DialogForge, que la V2 réfute à raison.

---

## 6. Ce que cette analyse ne prouve pas

- **Aucune CLI n'a été lancée.** `--tools ""`, les sandbox Codex, la consultation externe et les
  identifiants exacts des modèles restent déduits du code lu par Codex en V1 — jamais mesurés.
  C'est la limite de tout ce qui précède.
- Je n'ai pas relu les dix fichiers DialogForge. Les verdicts de Codex sur la colonne Code sont repris
  **sur sa parole**, sauf cinq recoupés avec mes relevés de récolte.
- Les fourchettes de lignes portent sur du code qui n'existe pas.
- **`A1` et `A2` sont des jugements, pas des faits.** Un lecteur peut estimer que tracer l'approbation
  vaut ses six concepts, ou que spécifier un mode indisponible vaut mieux que de le taire. Les deux
  sont argumentés en §3 et **réversibles sans migration** — voir la table du document final.
- La qualité réelle de la porte `QUESTION`, du registre de constats et des prompts ne se jugera
  qu'après les premières missions. Une friction observée doit être **notée avant** d'être généralisée.

# Critique B — la structure proposée par Codex

> Écrit le 2026-09-03 par Claude, agent **B** pour cette étape.
> Rédigé dans le **contrat de revue que Codex propose lui-même** (§5 de sa structure) : constats
> identifiés, sévérité explicite, disposition, décision jamais déduite des sévérités.
> L'appliquer à son auteur est le meilleur essai de ce contrat qu'on puisse faire sans code.

**Décision : `REVISER`.** La proposition est bonne et sa charpente tient. Onze constats, dont un
bloquant qui n'est pas un défaut de conception mais une décision de périmètre reprise en douce.

---

## Ce que Codex a corrigé dans mon inventaire

Sa vérification contre le code réel a trouvé cinq erreurs qui sont miennes. Elles étaient toutes du
même genre : **j'ai écrit comme observation ce qui était en fait une décision, ou un correctif.**

| Ligne | Ce que j'affirmais | Ce que le code dit |
|---|---|---|
| `C1` | « révisions bornées, défaut 2 » | Le code lu fait **3**. Le 2 vient de `DEPART.md` — c'est une décision, pas un constat. |
| `C3` | « écriture atomique par temporaire + renommage » | Vrai, mais **atomicité de publication ≠ durabilité** : aucun `flush`/`fsync`. |
| `C24` | « un corps volumineux est segmenté, jamais tronqué » | DialogForge **ne fait ni l'un ni l'autre** : `stdout`/`stderr` s'accumulent sans plafond dans des listes. Je décrivais un correctif comme un acquis. |
| `C19` | « formule de reconstruction des tokens » | Exacte, mais **elle ne sert à rien sans budgets**. Voir `B-007`. |
| `C37` | « chemins logiques relatifs » | `configuration.json` persiste un `project_path` **absolu**. Confirmé faux. |

C'est exactement ce que la vérification devait produire, et ça valide le fait de l'avoir demandée :
ma récolte avait lu des documents qui parlent du code.

**Et une trouvaille meilleure que ce que je proposais :** rendre `--reviewer-access {none,read-only}`
**obligatoire et sans défaut**. Ça garde B-2 ouvert, force le choix à être visible dans `etat.json`,
et empêche de trancher par accident dans une valeur par défaut. Je n'avais rien d'aussi propre.

---

## Constats

### `B-001` · **BLOCKING** · `OPEN` — « Recherche » a été redéfini sans le dire assez fort

> §3.2 : « "recherche" doit donc signifier, dans cette première brique, recherche dans un corpus fourni. »

**B-1 a été arbitré « oui » le 2026-09-03 sur la base des missions bibliographiques de FloraPi**, qui
interrogeaient des sources **externes** — vérification en texte intégral, indépendance des sources,
`aucune_valeur_recommandable` après épuisement du budget par espèce. Restreindre la recherche au corpus
fourni rend **`P26`, `P27`, `P30`, `P33`, `P34` largement inertes** : « source primaire préférée »,
« indépendance des origines », « critère de fin de recherche » ne mordent que si l'agent peut aller chercher.

Codex le signale (§11.2, §12), mais comme une option de périmètre parmi d'autres. C'en est la principale.

**Ce qui plaide pour lui, et qu'il n'a pas :** les deux missions bibliographiques ont échoué, et la cause
tracée (`DJBIBLIO-20260813-004`) est que **la question posée à la littérature portait sur une variable
qu'elle ne traite pas** — pas un défaut d'accès aux sources. L'échec était en amont, dans le mandat.
Son choix est donc probablement le bon pour V0.1, mais pour une raison plus forte que celle qu'il donne.

**Disposition attendue : décision humaine.** Soit la recherche V0.1 est corpus-only et on l'écrit dans
`CLAUDE.md`, soit le Web entre et c'est un contrat de capacité, de preuve et de confinement séparé.

### `B-002` · **MAJOR** · `OPEN` — La racine lisible de B n'est pas spécifiée

`read-only` sans **où** n'est pas un confinement. `CallSpec` porte un « dossier de travail », mais
l'invariant n'est écrit nulle part :

> **La racine lisible d'un agent est exactement le dossier de collaboration. Jamais le projet d'origine.**

Sans cette phrase, un adaptateur peut légitimement lancer la CLI avec `cwd` = le projet, et toute la
copie du corpus perd son objet. C'est le pivot de `C40` et de `C38` réunis.

### `B-003` · **MAJOR** · `OPEN` — Le corpus copié est un instantané, et sa péremption n'est nommée nulle part

La copie donne autonomie, empreintes et chemins relatifs — bien. Mais elle **gèle** l'état du projet à
l'instant du `new`. Sur une collaboration de plusieurs jours contre un dépôt vivant, A et B raisonnent
sur un passé sans le savoir.

Cela contredit frontalement `P13` de l'inventaire : *« une affirmation d'un document peut avoir vieilli :
vérifier l'état réel plutôt que la reprendre. »* Un corpus figé **garantit** ce vieillissement.

Codex ne cite que le coût disque (§11.5). Le vrai coût est épistémique.

**Correction à coût nul** : le manifeste porte la date de copie et la racine d'origine ; les prompts de A
et de B disent que le corpus est un instantané daté ; `status` affiche son âge.

### `B-004` · **MAJOR** · `OPEN` — `resume --retry-call` n'est borné par rien

Aucun plafond, et surtout **aucune exigence de cause changée**. Cela contredit `R4`, récoltée dans
`context/supervision.md` : *« une relance identique sur le même état est interdite : la cause, la
configuration ou une décision humaine doit avoir changé de manière vérifiable. »*

C'est humain-déclenché, donc moins grave qu'un worker en boucle — mais le fait mesuré est précisément
humain : **4 interventions humaines en 3 heures** sur le Lot 0, par re-déclenchement.

**Correction** : `--retry-call` exige un motif écrit, persisté dans le lien `retries`. Trois lignes.

### `B-005` · **MAJOR** · `OPEN` — Le budget de tests est absent, alors que §9 en spécifie une suite très large

Le tableau §10 chiffre **1 550 lignes de production** et s'arrête là. Or §9 décrit : crash simulé à
cinq frontières, matrice complète des quatre permutations, attaques de chemins du corpus, concurrence
de verrou, limites de sortie, contrats et normalisation exhaustifs.

Rapport mesuré sur DialogForge : **37 623 tests pour 49 568 de production**, soit 0,76. Une machine à
états avec reprise se teste plutôt à 1,5–2×. L'outil réel pèsera donc **3 500 à 4 500 lignes**.

Ce n'est pas interdit — `POURQUOI` règle 1 compare à FloraPi (58 894), et on en est loin. Mais
**« ~1 500 lignes » dans `CLAUDE.md` devient trompeur** s'il ne précise pas « production ». Un chiffre
qui ne dit pas ce qu'il compte est exactement ce qui a permis à DialogForge de grossir sans alarme.

### `B-006` · **MAJOR** · `OPEN` — Écarter le cadrage retire le seul garde-fou sur `demande.md`

Recommandation §8 : pas de cadrage en V0.1, `new` reçoit une demande déjà écrite. Défendable — c'est
l'objection de `DEPART.md` elle-même, un appel fournisseur de plus avant que la boucle démarre.

Mais l'échec le mieux documenté de tout le corpus est là : `DJBIBLIO-20260810-001` — une question de
calibrage posée par A en fin de cadrage, **restée sans réponse avant validation**, a produit une mission
livrant 2 espèces sur 20 à 30 attendues. Sans cadrage, plus rien entre l'humain et la boucle.

**Récupérable à coût nul, sans appel supplémentaire** : le prompt de A lui demande d'**ouvrir sa
proposition par les questions que la demande laisse sans réponse**. C'est `P18` de l'inventaire, déplacée
du cadrage vers la proposition. Une phrase, zéro mécanisme.

### `B-007` · **MINOR** · `OPEN` — Aucune reconstruction du coût n'est possible, alors que le choix A/B en dépend

`C19` est écarté en bloc (« ne pas la transporter dans le noyau »). Correct sur le mécanisme :
l'interdit n°4 proscrit budget, réservation et quota **internes**. Il ne proscrit pas d'**observer**.

Or le PO a dit explicitement que le choix de l'outil par rôle dépend **de ses crédits**. Un outil qui ne
laisse aucune trace exploitable du coût contrarie l'objectif qui a motivé la permutation.

**Correction à coût nul** : la sortie brute est déjà conservée en segments. Il suffit de **l'écrire**
— le manifeste d'appel note que le brut est retenu pour permettre une reconstruction hors ligne. Aucune
comptabilité dans le noyau, zéro ligne de logique. Et `R6` rappelle que cette reconstruction sera
partielle : Codex ne remonte pas le coût, Claude sous-déclare l'entrée.

### `B-008` · **MINOR** · `OPEN` — Le prompt de B enseigne que le prompt est le contrôle

> « Ta politique d'accès est `<NONE|READ_ONLY>`. Si elle vaut NONE, n'essaie pas de lire une source. »

Contredit `R13` : *le prompt système ne confine rien.* Codex fait pourtant le bon travail ailleurs —
le prévol refuse Codex-en-B sous `NONE`. La phrase est donc redondante, et redondante du mauvais côté :
elle apprend au lecteur que l'interdiction vit dans le texte.

**Correction** : la formuler en **information** (« tu n'as pas accès au corpus ; signale les faits que tu
ne peux pas vérifier »), jamais en interdiction.

### `B-009` · **MINOR** · `OPEN` — `COMPLETED` peut se lire comme une approbation

Codex le soulève lui-même (§11.7) et propose de différer un `AWAITING_APPROVAL`. D'accord pour différer
le statut — pas pour différer le problème. `R5` : *la réussite opérationnelle n'est pas une acceptation.*

**Correction à coût nul** : `livrable.md` s'ouvre sur un bloc porté par le programme — politique d'accès
réellement appliquée, nombre de constats restés ouverts, et la mention explicite que le document **n'est
pas approuvé**. Codex propose déjà d'y rappeler la politique ; il suffit d'y joindre les deux autres.

### `B-010` · **NOTE** · `OPEN` — Le budget par module est optimiste là où c'est le plus dur

`transport.py` 180 + `workflow.py` 180 = **360 lignes** pour : lancement, délai dur, terminaison de
l'arbre sur **Windows et POSIX**, segmentation bornée de deux flux, dix étapes de séquence durable,
cinq statuts d'appel, reprise et incidents. C'est là que ça débordera, pas dans la CLI.

Codex dit bien que le total est « une contrainte de conception, pas un quota aveugle ». Bien.
**Mais alors nommer d'avance ce qu'on coupe** si ça déborde, plutôt que de le découvrir en codant.

### `B-011` · **NOTE** · `OPEN` — Le manifeste de fichiers exacts va frotter, et c'est la chose à mesurer

Pas de glob, pas de découverte : plus petit et auditable, d'accord. Mais sur un projet de 58 894 lignes,
lister les fichiers à la main pousse à en mettre trop, ou à ne pas s'en servir.

Je ne demande pas de glob — ce serait la première marche vers les paquets thématiques écartés en `X9`.
Je demande que **ce soit le premier point d'usage mesuré**, conformément à `R28` et à la disposition
différée de l'observation 38 : *mesurer avant d'ajouter.*

---

## Ce que je ne conteste pas, et qui mérite d'être dit

- **Noyau neuf plutôt qu'élagage.** C'est le bon appel, et il est cohérent avec `POURQUOI` règle 5 : on
  ne répare pas un sous-système en s'en servant. Les 4 931 lignes contiennent 600 à 800 lignes d'idées
  utiles, enchevêtrées à des dépendances qui les rendraient coûteuses à extraire littéralement.
- **La séquence durable d'appel** (`PREPARED` → `LAUNCHING` → `STARTED` → `RESPONSE_STORED` → `APPLIED`),
  avec `LAUNCHING` publié **avant** `Popen` et lu comme « appel possiblement parti ». C'est `C23` rendue
  exécutable, et c'est mieux que ce que j'avais écrit.
- **`findings` à identifiants stables + validation référentielle de `resolved_changes`.** Ça ferme le
  trou que `C10` signalait et va au-delà : sans constats adressables, on ne peut pas prouver qu'un point
  précis a été corrigé.
- **`--reviewer-access` obligatoire, sans défaut.** Voir plus haut. Meilleure idée du document.
- **La table de réversibilité §12**, qui applique `P11` à la proposition elle-même.

## Limites de ma propre critique

- Je n'ai pas relu les dix fichiers DialogForge après Codex. Ses verdicts sur la colonne Code sont repris
  **sur sa parole**, sauf les cinq que j'ai recoupés avec mes propres relevés de récolte.
- Je n'ai lancé aucune CLI. Les capacités réelles de `--tools ""` et des sandbox Codex restent, pour moi
  comme pour lui, déduites du code et non caractérisées.
- Les estimations de lignes de `B-005` et `B-010` sont des ordres de grandeur tirés du rapport DialogForge,
  pas des mesures sur du code qui n'existe pas.

# session_log.md — Journal des sessions IAbinome

> Une entrée par session de travail.
> Format : date · travail accompli · commits · décisions notables.

---

## 2026-09-02 → 09-03 (Claude) — Fondation du projet

Session menée depuis `C:\Projets\Florapy_V2`, à la suite de l'audit du refactoring DialogForge.

### Ce qui a été fait

Audit de conformité du Lot 0 de DialogForge par rapport à son plan de marche, puis analyse stratégique de l'opportunité de poursuivre. Les mesures ont conduit à geler le refactoring et à fonder ce projet.

**Mesures décisives :**

- DialogForge : 87 382 lignes (49 568 `src/` + 37 814 tests), 78 modules, 242 commits, 7 semaines. FloraPi, le projet servi : 58 894 lignes. **Rapport 1,5.**
- Répartition interne : **7 676 lignes** de boucle A/B contre **26 997 lignes** d'appareil d'autonomie.
- Usage réel sur FloraPi depuis le 5 août : **7 conceptions terminées sur 9**, mais **1 seule implémentation durable tentée, bloquée à 1 tâche sur 7**.
- Lot 0 de DialogForge : bloqué à 1 tâche sur 10, ~7 M tokens consommés, 4 interventions humaines en 3 heures.
- Le refactoring prévoyait **15 lots** (0 à 14).

**Défauts techniques relevés au passage**, consignés dans `ARRET_REFACTORING.md` : coût Codex jamais remonté et entrée Claude jamais comptée ; `retry_at` de quota non parsable par `scheduling.parse_resume_time`, d'où un repli de 15 min et des réveils inutiles ; une tâche sans modification ne peut pas se clore seule.

### Décisions

1. **Refactoring DialogForge gelé** — décision datée, pas un abandon silencieux. DialogForge reste utilisé **en conception seule** sur FloraPi.
2. Mission d'implémentation `e35cfcf1-…` **mise en pause** : elle aurait redémarré seule à 01:01 au retour du quota Codex.
3. **Fondation d'IAbinome** — successeur allégé, ~1 500 lignes, deux agents IA en CLI, A produit / B critique, l'humain arbitre. Nom retenu après arbitrage : `BinomeIA` d'abord choisi, puis inversé en **`IAbinome`** par le PO.
4. **Cinq interdits de périmètre** figés dans `CLAUDE.md` : pas d'exécution autonome, pas de base, pas de worker/bail/tâche planifiée, pas de budget interne, pas de GUI.
5. **Une étape 0 de récolte est insérée avant la spécification** : capitaliser deux mois d'apprentissage en un inventaire d'une ligne par leçon, cinq destinations dont une colonne « Écarté » obligatoire, plafonné à ~200 lignes.
6. Modèles par rôle : **Opus 5 pour A, Fable 5 pour B**.
7. Remote git : **reporté**.

### Commits

**IAbinome** — `78e09e8` fondation (amendé pour corriger l'identité git) · `b513a8d` étape de récolte · commit des règles de travail.
**DialogForge** — `4903927` gel du refactoring et préparation de l'extraction · `01a9e03` nom du successeur et pointeur vers son dépôt.

### À retenir

L'erreur d'identité git (adresse du compte Claude au lieu de `schneider.jm@free.fr`) a nécessité un `--amend --reset-author`. Règle consignée dans `RULES.md`.

---

## 2026-09-03 (Claude) — Étape 0 : la récolte

Scope déclaré : poursuivre la récolte. Première session ouverte directement dans `C:\Projets\IAbinome`.

### Ce qui a été fait

Les **huit sources** de `RECOLTE.md` ont été dépouillées, dans l'ordre prescrit, et l'inventaire produit :
`conception/INVENTAIRE.md` — **26 Code · 24 Prompt · 21 Règle · 15 Test · 20 Écarté**, sous la barre des ~200 lignes.

**Mesures relevées pendant la récolte :**

- `context\supervision.md` pèse **113 des 194 lignes** de la doctrine déjà distillée, et ne traite que de conduite de projet.
- **14 des 69 fichiers de tests** de DialogForge nomment la boucle A/B ; **55 nomment l'appareil écarté.**
- Sur les 42 `fix:`, **9 sont retenus** ; sur les 85 `[DIFFÉRÉ]`, **7**.
- La boucle A/B entière tient dans ~80 lignes de prompts (`orchestrator.py:681-760`), le cadrage dans ~80 autres.
- Cinq faits mesurés repris de `preuves\README.md` : formule de reconstruction des tokens, 229 288 tokens de cadrage non comptés, réservation qui gouverne l'admission et non la consommation, laboratoire en avance de 6 commits sur sa référence, lecture d'archive SQLite qui casse ses propres empreintes.

**Sources arrêtées et notées :** `history.md` (2 533 l.) et `README.md` (1 046 l.) n'ont pas été ouverts, les huit sources répétant déjà leurs constats. La conception MariaDB (1 243 l.) n'a rendu que 2 lignes sur 1 243 — source épuisée avant sa fin.

### Décisions

1. **Périmètre de la récolte tranché : les deux.** L'inventaire couvre aussi la conduite de projet, en destination **Règle**, jamais **Code**. Motif mesuré — `supervision.md` avait déjà tranché de fait. Tranché par Claude faute d'arbitrage en séance, tracé dans `RECOLTE.md`, **rouvrable**.
2. Deux règles de méthode ajoutées à `RULES.md` : trancher une question ouverte dans le document qui la porte ; noter l'abandon d'une source de récolte avec son volume non lu.
3. La contrainte « **Code** est la colonne la plus courte » n'est **pas tenue** (26 contre 24). Constat porté en tête de la relecture plutôt que corrigé en douce.

### Commits

`docs: recolter deux mois d apprentissage dans un inventaire` — inventaire, arbitrage du périmètre, règles de méthode.
*(Le commit ne cite pas son propre hash : l'`--amend` le déplace.)*

### À retenir

L'inventaire n'est **pas relu**. Le protocole veut une passe Codex à consigne unique — « qu'est-ce qui a été écarté en silence ? » — avant tout arbitrage humain. Trois zones lui sont désignées comme suspectes : l'arrêt anticipé sur deux sources, les trois agrégats qui écartent 166 éléments d'un coup, et la colonne Code hors contrainte.

---

## 2026-09-03 (Claude + Codex) — Relecture contradictoire et inventaire v2

Le protocole d'IAbinome a tourné sur IAbinome lui-même, avant d'exister : Claude récolte, Codex contredit, l'humain arbitre.

### Ce qui a été fait

Prompt de relecture préparé en **deux passes** (`conception/RELECTURE_CODEX.md`) : la consigne d'omission seule d'abord, les zones suspectes seulement après réponse — donner ces zones d'emblée aurait orienté le contradicteur vers ce que l'auteur savait déjà.

Codex a répondu en deux temps, le PO ayant élargi le prompt entre-temps :

- **Passe 1** — 42 omissions, filet large, sans tri.
- **Version 1.1** — après précision du périmètre (*« conception et recherche, pas de codage »*), Codex reprend son propre jet et **se contredit sur six points**. Constat majeur : sa passe 1 réintroduisait la logique de forteresse de DialogForge qu'il devait aider à éviter.

Les 42 observations ont reçu **chacune exactement une disposition** (`conception/DISPOSITION_RELECTURE.md`) : **28 acceptées, 6 rejetées avec motif, 5 différées sous condition, 3 bloquantes**. Inventaire porté en v2 : de 106 à **146 leçons**, 248 lignes.

### Les trois trouvailles réelles

1. **La robustesse intellectuelle manquait entièrement** — indépendance des sources, résultat négatif qui compte, portée bornée par la preuve, contre-preuves conservées, critère de fin défini avant de chercher. J'avais dépouillé FloraPi pour ce qu'il disait de l'outil et de la conduite, jamais pour ce qui fait un **bon livrable** — c'est-à-dire le produit même d'IAbinome. Omission la plus coûteuse.
2. **`X7` écartait trop.** « Sans écriture agent, il n'y a rien à confiner » est faux : la frontière d'effets survit à l'appareil qui l'entourait. Onze lignes de Code ajoutées, aucun sous-système.
3. **Trois agrégats masquaient des invariants transférables** — prévol avant tout effet, état fermé sur valeur inconnue, intention d'appel persistée avant l'appel. Plus le troisième défaut mesuré d'`ARRET_REFACTORING.md`, qui n'était **ni retenu ni écarté**.

### Décisions

1. **Cinq contrôles proposés par la relecture sont refusés** — consentements réseau, scanner de secrets, agent réparateur de JSON, nettoyage automatique, sonde de worker. Motif commun : aucun ne compense un défaut encore réel (`POURQUOI` règle 3). Tous tracés en `X23`, aucun écarté en silence.
2. **Nouvelle règle `R31`** : le contradicteur, seul, tire vers l'ajout de contrôles ; il faut lui opposer le périmètre. Mesuré sur cette relecture même.
3. **Le dépassement du plafond est déclaré, pas maquillé** — 248 lignes contre ~200. Devient la question B-3.
4. La prémisse de `RECOLTE.md` « **Code** est la colonne la plus courte par construction » est probablement fausse : une leçon de périmètre *est* une ligne de code. 38 Code contre 34 Prompt.

### Commits

`docs: verser les deux passes de relecture de Codex` · `docs: disposer la relecture et porter l inventaire en v2`

### À retenir

**Trois questions bloquantes attendent l'humain** : B-1 la recherche entre-t-elle au périmètre (`CLAUDE.md` ne parle que de conception) · B-2 B garde-t-il ses outils à zéro (recommandation : oui) · B-3 le plafond de lignes tient-il. Rien ne peut avancer avant.

La seconde passe a plus apporté que la première. **Une consigne d'omission sans contrainte de périmètre produit un contradicteur qui rechute** — c'est le résultat le plus solide de la journée, et il vaut pour la conception d'IAbinome lui-même.

---

## 2026-09-03 (PO) — Arbitrage, et une contrainte structurante

### Ce qui a été tranché

| | Question | Décision |
|---|---|---|
| **B-1** | La recherche est-elle au périmètre ? | **Oui.** `CLAUDE.md` §1 et `DEPART.md` amendés ; les 10 lignes conditionnelles deviennent fermes. |
| **B-2** | B garde-t-il ses outils à zéro ? | **Reporté au troisième tour.** Un B aveugle ferait perdre des orientations intéressantes, et la permutation ci-dessous change les termes. |
| **B-3** | Le plafond de ~200 lignes tient-il ? | **Levé.** Chiffre arbitraire, faux depuis que le périmètre a grandi. |
| — | La colonne Code plus longue que Prompt | **Reporté après la phase 2.** |

### La contrainte neuve, et c'est la plus lourde

**A et B sont chacun Claude ou Codex, choisis au lancement — selon les crédits disponibles et l'humeur.** Le PO l'impose **dès la conception** : ne pas l'avoir prévu a été un gros handicap sur DialogForge.

La récolte le confirmait sans que je l'aie relevé comme invariant. La permutation rôle/outil a été **ajoutée en rattrapage** à DialogForge (`696cc27`, `d3724a3`) et n'a jamais été complète : le constat **H-03** de la revue du 2026-07-24 montre que `CodexAgent` ne transforme pas ses erreurs de quota en `AgentQuotaError`, et que `recover_failed_review` ne cherche que `*claude.txt`. La reprise automatique après quota n'a donc jamais fonctionné côté Codex.

Portée dans l'inventaire : `C15a`–`C15e`, `T21`–`T23`, `R32`–`R33`. Et surtout une règle courte qui généralise : **le cycle ne dépend que des capacités présentes chez les deux outils ; ce qui est propre à l'un est un bonus, jamais un prérequis.**

### Ce que la permutation casse

**Elle invalide ma recommandation sur B-2.** Je conseillais de laisser B sans outil, en m'appuyant sur `--tools ""` de Claude, qui est vérifiable. Mais le shell de Codex n'est pas retirable : « B sans outil » devient une propriété qui dépend de *quel outil occupe le rôle* — exactement ce que `C15c` interdit. La question se reformule en « aucun outil » contre « aucun **effet** ». Termes posés en fin d'`INVENTAIRE.md`.

Asymétries mesurées consignées en `R33`, pour ne pas les reperdre : session persistante (Codex oui, Claude non) · erreur de quota typée (Claude oui, Codex non) · schéma de sortie natif (Codex oui, Claude désactivé) · outils du relecteur.

### Commits

`docs: acter les arbitrages et prevoir la permutation role/outil`

### À retenir

**L'étape 0 est close.** L'étape 1 s'ouvre sur les **43 lignes de la colonne Code**.

Deux reports assumés et tracés : B-2 au troisième tour, la longueur de la colonne Code après la phase 2. Aucun des deux n'est refermé en silence.

---

## 2026-09-03 (Codex A, Claude B) — Étape 1 : deux structures sur la table

Premier tour du protocole d'IAbinome avec **les rôles inversés** : Codex produit, Claude critique.

### Ce qui a été fait

Codex a lu les 4 931 lignes que la récolte n'avait jamais ouvertes, audité les 43 lignes de la colonne Code une par une, et proposé une structure complète : `conception/STRUCTURE_PROPOSEE_CODEX.md`.

Claude a critiqué dans **le contrat de revue que Codex propose lui-même** — l'appliquer à son auteur est le meilleur essai qu'on puisse en faire sans code. Décision `REVISER`, 11 constats. Puis une révision complète, à côté : `conception/STRUCTURE_PROPOSEE_CLAUDE.md`.

### Ce que la vérification a corrigé dans l'inventaire

**Cinq erreurs, toutes du même genre : une décision ou un correctif écrit comme une observation.**

| | J'affirmais | Le code dit |
|---|---|---|
| `C1` | révisions bornées, défaut 2 | le code fait **3** ; le 2 vient de `DEPART.md` |
| `C3` | écriture atomique | vrai, mais **atomicité ≠ durabilité** : aucun `fsync` |
| `C24` | segmenté, jamais tronqué | DialogForge **accumule sans plafond** — je décrivais un correctif comme un acquis |
| `C19` | formule de reconstruction des tokens | exacte, mais inutile sans budgets |
| `C37` | chemins logiques relatifs | `configuration.json` persiste un chemin **absolu** |

C'est exactement ce que la vérification devait produire. Elle valide le fait de l'avoir demandée.

### Charpente retenue par les deux propositions

**Noyau neuf, pas élagage de DialogForge** — cohérent avec `POURQUOI` règle 5. 14 modules, 4 commandes CLI (`new`/`run`/`resume`/`status`), dossier de collaboration autonome et déplaçable, séquence durable d'appel en 5 statuts avec `LAUNCHING` publié **avant** `Popen`, contrat de revue enrichi de `findings` adressables.

**Meilleure idée du tour, et elle est de Codex :** `--reviewer-access {none,read-only}` **obligatoire, sans défaut**. B-2 reste ouvert sans qu'une valeur par défaut le tranche par accident, et le choix devient visible dans `etat.json` puis dans le livrable.

### Les neuf corrections de la révision B

Invariant de racine lisible (= le dossier de collaboration, jamais le projet) · corpus déclaré **instantané daté** · `--retry-call` exige un motif écrit (`R4`) · **budget de tests chiffré** et coupes pré-décidées · le prompt de A ouvre par les questions que la demande laisse ouvertes (récupère `P18`, perdue avec le cadrage) · le brut est retenu pour reconstruire le coût hors ligne · le prompt de B formule sa politique en information et non en interdiction (`R13`) · `livrable.md` s'ouvre sur « non approuvé » (`R5`) · le manifeste sans glob devient le premier point d'usage à mesurer.

**Sept des neuf coûtent zéro ligne de code** — ce sont des phrases, pas des mécanismes.

### Décisions

1. **Le chiffre « ~1 500 lignes » de `CLAUDE.md` est trompeur** : il ne compte que la production. Tests estimés à 2 300–3 000, total réel 3 800–4 500. Un chiffre qui ne dit pas ce qu'il compte est ce qui a laissé DialogForge grossir sans alarme. La garde reste `POURQUOI` règle 1.
2. **Question bloquante nouvelle — `B-1bis`.** Codex a restreint « recherche » à « recherche dans un corpus fourni », alors que B-1 avait été arbitré sur des missions bibliographiques **à sources externes**. Recommandation : corpus-only pour V0.1, mais l'écrire — les deux échecs mesurés venaient du **mandat**, pas de l'accès.

### Commits

`docs: critiquer et reviser la structure proposee par Codex`

### À retenir

**L'inversion des rôles a bien fonctionné.** Codex-en-A a produit un document meilleur que ce que j'aurais écrit seul sur au moins un point (`--reviewer-access`), et a trouvé cinq erreurs factuelles dans mon propre travail. C'est le premier signal réel, avant toute ligne de code, que la permutation `C15a` n'est pas qu'une contrainte technique.

**Ce qui reste non caractérisé : aucune CLI n'a jamais été lancée.** `--tools ""`, les sandbox Codex et les identifiants exacts des modèles sont déduits du code. Premier prévol réel à faire.

---

## 2026-09-03 (Codex) — Synthèse critique de structure V2

### Ce qui a été fait

Relecture de la critique Claude (11 constats), de sa révision complète, de la structure Codex initiale
et de `RELECTURE_CODEX_PASSE1_V1.1.md`, puis retour aux documents d'autorité et aux règles du projet.
Production de `conception/STRUCTURE_PROPOSEE_CODEX_V2.md`, sans écraser les versions antérieures.

La V2 dispose les 11 constats un par un. Elle accepte leur objectif mais corrige plusieurs remèdes :
`cwd` n'est pas présenté comme un confinement de lecture ; un motif de reprise est une trace et non une
preuve ; les ratios de tests DialogForge ne sont pas extrapolés comme une mesure du futur code.

Elle simplifie la reprise de cinq états d'appel à deux (`CALLING`, `RESPONSE_STORED`) et remplace les
segments par un fichier borné par flux. Elle ajoute une porte A `QUESTION` sans cadrage fournisseur
séparé, un registre de constats à source unique et une vraie phase d'approbation humaine.

### Décisions

Aucune décision humaine actée pendant cette passe. La V2 recommande `CONSULT` pour B, mais laisse B-2
ouvert. Elle propose deux accès de recherche (`CORPUS_ONLY`, `EXTERNAL_READ`) ; le second reste soumis à
une caractérisation réelle et commune des deux CLI.

### Commits

Aucun. Le nouveau document et cette mise à jour attendent l'arbitrage humain.

---

## 2026-09-03 (Claude) — Conception finale : audit d'accrétion

Le PO signale un risque précis : **Codex n'a pas participé à l'échange fondateur**, donc il peut glisser vers des ajouts justifiés isolément — le mécanisme exact qui a produit 87 382 lignes.

### Ce qui a été fait

Deux documents : `conception/ANALYSE_VERS_CONCEPTION_FINALE.md` (le raisonnement) et `conception/CONCEPTION_FINALE.md` (la spécification).

La méthode : reconstituer les **neuf objectifs fondateurs** tels qu'ils ont été dits — ils n'étaient nulle part écrits pour Codex — puis opposer chaque élément de la V2 à ce total, selon `POURQUOI` règle 2.

**`O4` est le plus fragile et personne ne le surveille** : « `etat.json` lisible à l'œil nu » et « fermer le terminal » sont des objectifs d'ergonomie, pas de correction. Aucune revue ne les défend spontanément — ils tombent en premier.

### Ce que la V2 fait mieux que ma révision

- **Elle m'a pris en flagrant délit.** Mon constat `B-002` demandait un « invariant testé » : la racine lisible = le dossier de collaboration. La V2 refuse — `cwd` n'est pas un bac à sable. **J'avais fait exactement ce que je lui reprochais en `B-008`** : présenter comme mécanique une frontière qui ne l'est pas. `R13` vaut pour `cwd` aussi.
- **Cinq statuts d'appel → deux.** `PREPARED`/`LAUNCHING`/`STARTED` avaient la même conséquence après crash ; `APPLIED` dupliquait la phase.
- **Segments → un fichier borné par flux.** Ma ligne `C24` prescrivait une segmentation que l'audit avait montrée inexistante.
- **`resolved_changes` supprimé** au profit d'un registre unique — deux sources de vérité pour la fermeture d'un constat.
- **Elle réfute mon extrapolation** du volume de tests par le rapport DialogForge : j'avais transporté une mesure hors de son domaine, ce que `P29` de mon propre inventaire interdit.

### Sept accrétions retirées

| | Retiré | Motif |
|---|---|---|
| A1 | Appareil d'approbation — 3 statuts, 1 phase, 1 fichier, 2 options CLI | `--approve` **écrit un fichier que rien ne consomme**. Six concepts pour zéro conséquence mécanique. Définition du contrôle qui a fait exploser le prédécesseur. |
| A2 | Mode de recherche externe | Spécifier un mode **indisponible et non nécessaire** — contraire à `POURQUOI` règle 3. Les deux échecs mesurés venaient du mandat, pas de l'accès. |
| A3 | Versionnement `demandes/` + compteur | Le compteur est dérivable des fichiers. `demande.md.001` suffit. |
| A4 | Renommage `.part` → `.bin` | `resultat.json` est déjà le marqueur de complétude. Deux mécanismes pour un fait. |
| A5 | Champ `rationale` | Rien de mécanique ne le consomme. `O8` — alléger. |
| A6 | `origin_revision` | Métadonnée que la V2 place elle-même dans sa liste de coupe. |
| A7 | Dossier `interventions/` | Deux natures dans un dossier ; chacune a une meilleure place. |

**Compte : ~125 lignes et six concepts.** 8 statuts → 6 · 6 phases → 5 · 16 options CLI → 12 · 9 fichiers par appel → 6 · production 1 555 → **~1 430**, sous la promesse fondatrice.

### Ce qui n'est pas coupé, et pourquoi

La porte `IABINOME:QUESTION` (elle **retire** plus qu'elle n'ajoute : elle remplace `framing.py` entier et répare l'échec le mieux documenté du corpus) · la double lecture sous verrou (~5 lignes, la fenêtre est réelle) · **`fsync` et publication atomique** — la V2 a raison contre ma propre liste de coupes : je proposais de sacrifier `fsync` pour tenir un chiffre. **Une garantie de durabilité ne se troque pas contre des lignes.**

### Décisions

1. **Sources externes écartées de V0.1.** La recherche reste au périmètre — le type de mission existe et les règles de preuve mordent sur un corpus documentaire. Ce qui change, c'est **qui rassemble** : l'humain dépose, le binôme analyse. Condition de réouverture nommée.
2. **Le cycle se termine en `AWAITING_APPROVAL`**, jamais en « succès ». L'arbitrage appartient à l'humain et à ses documents ; IAbinome ne l'enregistre pas.
3. **`A1` et `A2` sont des jugements, pas des faits** — déclarés comme tels dans les limites de preuve, et réversibles sans migration.

### Commits

`docs: produire la conception finale par audit d accretion`

### À retenir

Quatre tours conservés séparément, **aucun écrasé** : Codex A → Claude B → Claude A' → Codex B' → synthèse. Le protocole a tourné quatre fois avant qu'une ligne de code existe.

**La limite qui domine tout : aucune CLI n'a jamais été lancée.** Cinq points à mesurer (§12.2), dont le point 2 — la réalité du mode sans outils — qui décide B-2.

---

## 2026-09-03 (Codex B, Claude A) — Dernière revue technique, et préparation du code

Cinquième tour du protocole. Codex relit `CONCEPTION_FINALE.md` et rend **huit remarques techniques**.

### Ce qui a été fait

Les huit sont disposées dans `conception/DISPOSITION_TECHNIQUE_CODEX.md` et **toutes retenues** — première revue du cycle où c'est le cas. Ça se comprend : elle ne porte plus sur des choix, mais sur des **défauts vérifiables**. Quatre sont des défauts que j'avais laissés dans le document, quatre sont des trous.

Spécification corrigée sur les huit points.

### Le défaut le plus grave

**`resultat.json` était écrit avant que `RESPONSE_STORED` soit publié**, et tout crash restant en `CALLING` était traité comme incertain. Un crash dans cette fenêtre produisait donc : une réponse complète sur le disque, un état qui la déclare incertaine, et une relance humaine qui **repaie un appel dont on a déjà la réponse**. C'est exactement ce que tout le protocole durable existe pour empêcher.

Le correctif ne coûte rien : `resultat.json` n'étant écrit qu'à la sortie propre, **sa présence est la preuve de complétude**. La reprise inspecte le dossier d'appel au lieu de se fier au seul statut. Effet secondaire : cela justifie rétrospectivement le retrait du renommage `.part`/`.bin` (`A4` de l'audit d'accrétion), puisque le marqueur devient porteur.

### Les trois autres défauts qui étaient miens

- **« Ne propose ni n'exécute de modification »** dans le prompt de A interdisait littéralement **le livrable lui-même**. Formule héritée de la V2 et reproduite sans la lire. Corrigé en séparant *proposer* de *appliquer*.
- **« Fermer le terminal » n'était jamais spécifié** — alors que j'avais moi-même désigné `O4` comme l'objectif le plus fragile, celui qu'aucune revue ne défend spontanément. Ctrl-C, fermeture de console et orphelins sont maintenant spécifiés, **y compris ce qui n'est pas promis** : la correction ne dépend jamais d'un nettoyage à la fermeture.
- **Le discriminateur ne s'appliquait pas à la finalisation.** Résolu vers l'uniformité : un analyseur, aucun cas particulier.

### Une résolution de Codex meilleure que la mienne

Mes deux règles de B se contredisaient : « la décision n'est jamais déduite des sévérités » et « `ACCEPTER` + `BLOCKING` est refusé ». Sa version les réconcilie — **conserver la décision de B telle quelle**, signaler l'incohérence, `WAITING_HUMAN`. Le mal mesuré (`H-01`) était que le programme *transformait* la décision ; le remède n'est pas qu'il la *rejette*, c'est qu'il n'y touche pas. Et la rejeter perdrait des constats qui peuvent être bons.

### Décisions

1. **Adaptateurs obligatoires, modèle par défaut résolu par l'adaptateur.** Le PO choisit selon ses crédits : une valeur qui change à chaque lancement ne doit pas avoir de défaut. Mais « Opus 5 pour A » n'a aucun sens si A est Codex — le défaut devient une propriété de l'adaptateur pour un rôle, ce qui garde les noms de fournisseurs dans `adapters/` (`C15b`) et corrige `CLAUDE.md` §6.
2. **Corpus non vide obligatoire en recherche** — sans accès externe, une recherche sans corpus n'a rien à chercher. Et **`--answer` ne change jamais le corpus** : s'il faut d'autres sources, on crée une collaboration.
3. **Paramètres fixés** : UTF-8 sans BOM et `\n` · 8 MiB par flux, constante sans option · **Windows supporté et testé, POSIX écrit mais non testé en V0.1** — honnête plutôt que rassurant (`R15`).

### Commits

`docs: disposer les huit remarques techniques et preparer le code`

### À retenir

**L'étape 2 s'ouvre sur le palier 1 : cinq modules purs, ~600 lignes** — `models`, `storage`, `lock`, `contracts`, `corpus`. Ils ne dépendent d'aucune caractérisation de CLI, c'est ce qui les rend premiers. Porte à chaque commit : `ruff check .` et `mypy`, aucun appel fournisseur dans la suite.

**En parallèle, et avant le palier 3 : relever les cinq points de §12.2.** Aucune CLI n'a jamais été lancée, et le point 2 — la réalité du mode sans outils — décide B-2 à lui seul.

---

## 2026-09-03 (Claude) — Étape 2, palier 2 : `fakes.py` et `transport.py`

*Le palier 1 n'a pas d'entrée dans ce journal : la session precedente a mis a jour `NOTES.md` sans
ecrire ici. Ses faits y sont donc, pas ici.*

### Ce qui a été fait

`src/iabinome/transport.py` (238 lignes) et `tests/fakes.py` (61) + `tests/test_transport.py` (261).
**118 tests verts** (24 nouveaux), `ruff check .` et `mypy --strict` verts, 7,7 s de suite.

Couvert : deux flux concurrents de 1 MiB entrelacés, sortie vide, code de retour non nul, délai dur,
plafond de flux, terminaison d'arbre, `pid.txt` écrit dès le retour de `Popen`, Ctrl-C, et la
relecture stricte de `resultat.json`.

### L'écart avec la spécification qui mérite d'être discuté

**§10 nommait `FakeProcess` et `FakeClock` ; ni l'un ni l'autre n'est écrit.** `transport.py` existe
pour tenir ce que fait l'OS : deux tubes concurrents, un délai dur, la terminaison d'un arbre de
processus. Un objet processus simulé ne démontre aucun des trois — il ne rendrait que ce qu'on y a
mis, et le test passerait en décrivant la spécification plutôt qu'en la vérifiant. Un `FakeClock`
ferait pire : il retirerait du test le seul mécanisme mesuré, l'échéance réelle.

`tests/fakes.py` script donc un **vrai** sous-processus `python -c`. La règle « aucun appel
fournisseur, aucun réseau dans la suite » est tenue entièrement ; c'est le moyen qui change, pas la
règle. `FakeAdapter`, lui, n'arrive qu'avec `adapters/base.py` au palier 4 — le protocole qu'il doit
implémenter n'existe pas encore.

### Un trou trouvé en écrivant, absent de la spécification

Un **descendant** qui tient encore les tubes après la sortie de l'enfant garde les fils de copie
vivants. `resultat.json` aurait alors été écrit — donc « flux complets » affirmé — sur des fichiers
qui grossissaient encore. C'est précisément le « partiel présenté comme complet » que §10 interdit.
Corrigé par une terminaison d'arbre supplémentaire lorsqu'un fil survit à sa jointure. **Cette
branche n'est couverte par aucun test** : la déclencher demanderait de rendre le délai de grâce
configurable, donc une option de plus pour une seule ligne de preuve.

### Décisions

1. **`Outcome` vit dans `transport.py`, pas dans `models.py`.** Ce n'est pas un des neuf enums fermés
   de la spécification, c'est le vocabulaire de l'incident — et `models.py` dépasse déjà son budget.
2. **`read_result()` est dans `transport.py`**, bien que la table de reprise §5 relève de
   `workflow.py` : le lecteur et l'écrivain d'un format vont ensemble, et c'est ce qui rend la règle
   « `resultat.json` valide = flux complets » testable seule, sans moteur.
3. **`SIGKILL` n'est pas nommé.** `signal.SIGKILL`, `os.killpg` et `os.getpgid` sont déclarés absents
   sous Windows par `typeshed` : les nommer ferait échouer `mypy --strict` sur le poste de travail
   pour une branche qui n'y tournera jamais. Retenu : `os.kill(-pid, 9)`, le PID négatif désignant le
   groupe, qui vaut le PID de l'enfant grâce à `start_new_session`.

### L'alerte budget

| | Lignes |
|---|---:|
| Production écrite, 6 modules sur 11 | **1 002** |
| Budget §11 de ces 6 modules | 760 |
| Écart | **+242 (+32 %)** |
| Projection si les 5 modules restants tiennent leur budget | **1 672** |
| Bande acceptable §11 | 1 350 – 1 550 |

La bande n'est **pas** dépassée aujourd'hui ; la projection, si. La règle de coupe §11 ne s'ouvre
qu'au dépassement réel. Point de mesure retenu : la clôture du palier 3.

Sur les 78 lignes d'écart de `transport.py`, ~35 sont `read_result()`, que la ligne de budget plaçait
vraisemblablement dans `workflow.py`. Le dépassement propre au transport est donc d'environ 45 lignes
— celui du module que `NOTES.md` désignait, avant de l'écrire, comme le plus susceptible de déborder.

### Commits

`feat: implementer le palier 2 - transport et faux agent`
`docs: tracer le palier 2 et l alerte de budget`

### À retenir

**La prochaine action n'est pas le palier 3 : c'est la caractérisation des deux CLI (§12.2).** Aucune
CLI n'a jamais été lancée, c'est une manipulation humaine hors suite, et le point 2 décide B-2.

**Codex n'a relu aucun palier.** `CLAUDE.md` §3 en fait le protocole ; les paliers 1 et 2 attendent.

---

## 2026-09-03 (PO) — Deux arbitrages : relecture Codex et budget

### Décisions

1. **La relecture Codex palier par palier est suspendue pour l'étape 2.** Motif du PO, à la suite
   d'une recherche menée le même jour : **la conception est très précise**. Elle a été contredite
   cinq tours avant la première ligne de code, et la dernière revue technique — huit remarques,
   toutes retenues — ne portait déjà plus sur des choix mais sur des défauts vérifiables. La règle
   **reste valable pour la conception**, où elle a payé ; c'est la relecture de **code** palier par
   palier qui tombe. `CLAUDE.md` §3 et `RULES.md` amendés, non effacés.
   **Réouverture si un palier révèle un défaut que la relecture aurait attrapé.**
2. **Budget : on continue.** 1 002 lignes écrites pour 760 budgétés, projection à 1 672 contre une
   bande de 1 350 – 1 550. La bande n'étant pas dépassée en réel, la règle de coupe §11 ne s'ouvre
   pas. Point de mesure conservé à la clôture du palier 3. La garde de fond reste `POURQUOI` règle 1.

### Ce que ça retire, en échange

La suspension retire le seul dispositif qui, jusqu'ici, a rattrapé ce que l'auteur ne voyait pas —
`RULES.md` le dit en toutes lettres. **Ce qui reste pour tenir ce rôle** : la spécification écrite
avant le code, `ruff` et `mypy --strict` à chaque commit, et la suite de tests. Les deux écarts et le
trou trouvés au palier 2 l'ont été en écrivant, pas par une revue — c'est un indice, pas une preuve,
que ça suffit.

### Commits

`docs: acter la suspension de la relecture Codex et l arbitrage de budget`

### À retenir

**Prochaine action inchangée : la caractérisation des deux CLI (§12.2).** Elle ne dépend d'aucune de
ces deux décisions.

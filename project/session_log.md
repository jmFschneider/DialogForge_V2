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

---

## 2026-09-03 (Claude) — Étape 2, palier 3 : le moteur

### Ce qui a été fait

`workflow.py` (397 lignes), `prompts.py` (125), `adapters/base.py` (57), `tests/test_workflow.py`
(271), `tests/test_recovery.py` (199), et `FakeAdapter` + échafaudage de collaboration dans
`tests/fakes.py`. **159 tests verts** (41 nouveaux), `ruff` et `mypy --strict` verts.

Le palier a débordé son périmètre nominal, et il le devait : `workflow.py` ne peut ni s'écrire ni se
tester sans les gabarits de prompts ni sans le protocole d'adaptateur. Aucun des deux ne dépend de la
caractérisation §12.2 — vérification faite, la décision du PO d'enchaîner sur le palier 3 était juste.

### Deux défauts du palier 1, trouvés par les tests du palier 3

Aucune relecture du code seul ne les avait montrés. Les deux ne sont apparus qu'en faisant tourner le
moteur contre de vrais sous-processus.

1. **`parse_review` n'acceptait que du JSON nu.** §6 et §10 acceptent aussi « un bloc JSON clôturé
   couvrant toute la réponse » — et une CLI d'agent encadre très souvent son JSON. Corrigé dans un
   `fix:` séparé.
2. **CRLF.** Un sous-processus Windows écrit en mode texte : la première ligne arrivait avec un
   retour chariot, la balise `IABINOME:DOCUMENT` n'était **jamais** reconnue, et tout le cycle
   finissait en `ERROR`. Le palier 1 avait écarté cette normalisation en écrivant « à statuer si un
   besoin réel apparaît » — **c'est cette condition écrite qui a permis de rouvrir la question au
   lieu de la redécouvrir comme un bug**. `normalize()` ramène désormais CRLF à LF et le consigne
   comme transformation, exactement comme le BOM : c'est la seconde moitié de la même phrase de §0.1.
   Le brut, lui, reste intact sur le disque — c'est la copie normalisée qui est transformée, jamais
   la preuve.

### Décisions

1. **`_Engine` porte le contexte du cycle** — dossier, configuration, adaptateurs, versions sondées,
   délai — au lieu de le retraverser par douze signatures. Rupture de style assumée : c'est le seul
   module du programme à porter autant de contexte, et cela retire ~45 lignes de plomberie.
2. **`adapters/base.py` est publié.** §13 rendait le protocole d'adaptateur réversible « jusqu'à sa
   publication » ; ce point est franchi. `claude.py` et `codex.py` attendent §12.2.
3. **Les trois issues non-`COMPLETED` du transport mènent toutes à `INTERRUPTED`**, jamais à un
   rejeu ; `ERROR` reste réservé à l'échec de contrat. C'est ce que la table de reprise §5 sait
   traiter, et c'est ce qui garantit qu'aucun appel n'est repayé sans décision humaine.
4. **Aucun compteur de garde sur la boucle du moteur** : `max_revisions` la borne, `FINAL_A` est
   terminal. Un compteur serait un quota interne.

### Le budget, à re-arbitrer

| | brut | code effectif |
|---|---:|---:|
| Production écrite, 9 modules sur 12 | **1 605** | **1 150** |
| Bande §11 | 1 350 – 1 550 | 1 350 – 1 550 |
| Projection au même rythme | **~2 100** | **~1 520** |

**La bande est franchie en brut, pas en code effectif** — l'écart est entièrement de la documentation
de motif et du formatage. Aucune fonctionnalité hors spécification, aucun contrôle ajouté.

**Et les quatre coupes de §11 ne peuvent pas fermer cet écart** : `status --json`, les abstractions à
un seul appelant, la détection lexicale et les métadonnées d'origine facultatives pèsent ensemble une
quarantaine de lignes, pas cinq cents. Le seul levier réel serait de retirer les docstrings de motif,
c'est-à-dire la méthode du projet. C'est le point 5 de la règle de coupe : arbitrage.

Repère de fond, lui non franchi : `POURQUOI` règle 1 — ~2 100 lignes contre les 58 894 de FloraPi.

### Commits

`fix: accepter le bloc JSON cloture dans la revue de B`
`feat: implementer le palier 3 - moteur, prompts et protocole d adaptateur`
`docs: tracer le palier 3 et poser la question du budget`

### À retenir

**Prochaine action : la caractérisation des deux CLI (§12.2).** Elle bloque maintenant réellement le
palier 4 — `adapters/claude.py` et `adapters/codex.py` sont exactement ce qu'elle mesure.

---

## 2026-09-03 (Claude, sur autorisation du PO) — Caractérisation des deux CLI

Première fois qu'une CLI est lancée depuis le début du projet. Quatre appels payants, autorisés.
Relevé complet : `conception/CARACTERISATION_CLI.md`.

### Le résultat principal

**Les quatre permutations sont viables.** Chaque outil tient le rôle A et le rôle B, et le contrat
est respecté du premier coup des deux côtés — vérifié en passant les sorties aux vrais analyseurs
`parse_agent_response` et `parse_review`, pas à mon jugement.

### Ce que la mesure a corrigé dans le code

1. **Le prompt passe par `stdin`, jamais par argv.** Deux motifs mesurés : `argv` plafonne à 32 767
   caractères sous Windows, qu'un corpus réel dépasse ; et une CLI qui voit `DEVNULL` sur son entrée
   la lit comme un flux canalisé vide — la réponse est tombée de 673 octets conformes à **100 octets
   de préambule hors contrat**. `transport.run()` reçoit `stdin_text`, écrit dans un fil.
2. **L'exécutable doit être résolu par `shutil.which()`** : l'entrée de PATH de l'outil 2 est un
   script sans extension et `CreateProcess` rend `WinError 2`.
3. **Le prompt de B était inutilisable et ne l'est plus.** §9 disait « retourne le JSON de revue v1 »
   sans jamais montrer le schéma. Ajouté avant les appels — les deux revues sont conformes.

### Une correction qui m'est due

**J'avais donné à la normalisation CRLF un motif que je n'avais pas mesuré.** La docstring disait
« une CLI d'agent écrit en mode texte, donc en CRLF — mesuré le 2026-09-03 ». La preuve venait en
réalité de mon propre faux agent. **Les deux vraies CLI rendent des `\n`.** Le correctif reste bon
comme *tolérance*, par symétrie avec le BOM ; c'est son motif qui était faux. Docstring, test et
`NOTES.md` corrigés. Même nuance, plus légère, pour le bloc JSON clôturé : les deux rendent du JSON
nu.

### Trois décisions rendues au PO

1. **B-2 : la prémisse de §12.3 est démentie.** « Le shell de Codex n'est pas retirable » est faux —
   `--disable shell_tool` existe, vérifié sans appel payant via `codex features list`. `CONTEXT_ONLY`
   ne contredit plus les quatre permutations. Réserve : un `CONTEXT_ONLY` complet demanderait de
   retirer d'autres drapeaux, non mesuré.
2. **Le code de retour non nul est une capacité commune aux deux outils** — quota épuisé comme modèle
   invalide rendent `1`. Et chez l'outil 1, le message de quota sort **sur `stdout`** : un `extract()`
   naïf le prend pour une réponse et le cycle finit en « erreur de contrat » alors que la cause est un
   quota. Le moteur doit-il nommer l'incident sur le code de retour, avant de tenter le contrat ?
3. **L'outil 2 tient une base `memories`.** L'appel est éphémère au sens de la session, pas des
   effets. Rien de ce que §1 promet n'est cassé — §1 ne promet que le confinement de *nos* artefacts —
   mais la reproductibilité d'un cycle n'est pas garantie par le noyau, et il faut le dire.

### Ce qui était déjà juste

`transport.py` tient contre une vraie CLI : délai dur respecté, aucun `resultat.json` sur `TIMEOUT`,
`pid.txt` écrit, et l'arbre `cmd.exe` → `codex.exe` — **observé présent pendant l'appel** — entièrement
terminé après. Le premier contrôle portait sur `node.exe`, absent avant comme après : un test vide,
refait correctement.

### Commits

`feat: caracteriser les deux CLI et faire passer le prompt par stdin`

### À retenir

**Le palier 4 n'est plus bloqué.** Les valeurs à porter dans `adapters/claude.py` et
`adapters/codex.py` sont dans le relevé.

### Clôture de session

Session fermée sur décision du PO pour repartir sur un contexte neuf. **Les trois décisions rendues
ci-dessus (B-2, code de retour, base `memories`) sont reportées à la session suivante**, et reprises
en tête de `NOTES.md` sous les repères **D-1, D-2, D-3**, chacune avec assez de contexte pour être
tranchée sans relire ce journal, et avec ma recommandation.

`NOTES.md` a été ramené à un tableau de bord : les récits par palier ont été retirés — ils sont ici —
et remplacés par une section **« Contraintes acquises — à ne pas redécouvrir »**, qui ne garde de
chaque palier que ce qui contraint encore le code à écrire. `CLAUDE.md` le demandait dès le début ;
le fichier avait dérivé en historique au fil des trois paliers.

**État à la reprise :** 1 651 lignes de production, 1 797 de tests, **163 tests verts**, `ruff` et
`mypy --strict` verts, arbre git propre. Palier 4 non commencé, non bloqué.

---

## 2026-09-04 (Claude) — Palier 4 : adaptateurs, CLI, D-1/D-2/D-3 tranchées

Scope déclaré : reprendre au point 4 du protocole de démarrage (`RULES.md`, après `NOTES.md` et
`POURQUOI.md`).

### Ce qui a été fait

Les trois décisions reportées de la session précédente ont été soumises au PO avec la recommandation
de chacune ; les trois recommandations ont été retenues. Tranchées **dans**
`conception/CONCEPTION_FINALE.md` (§1, §5, §12.3), pas seulement en notes de session — conformément à
la règle qui l'exige.

- **D-1** — `CONSULT` reste le défaut de `--reviewer-access`. `CONTEXT_ONLY` n'est plus bloqué
  mécaniquement pour Codex, réserve non essayée conservée et rendue visible.
- **D-2** — `workflow.py` : `resultat.json.return_code != 0` devient l'incident nommé `CLI_FAILED`
  (`INTERRUPTED`), testé avant toute tentative de contrat, dans `new_call` et dans `resume_call`.
  ~15 lignes, deux tests neufs.
- **D-3** — une phrase sur la base `memories` de Codex ajoutée à §1.

**Palier 4 écrit et testé** : `adapters/claude.py`, `adapters/codex.py` (formes de
`conception/CARACTERISATION_CLI.md` : prompt par `stdin`, `shutil.which()` à chaque appel, `--tools
""` / `-c features.shell_tool=false` pour `CONTEXT_ONLY`, `extract()` lit `stdout` seul), `cli.py`
(quatre commandes, `new` publie par renommage depuis un dossier temporaire frère), `__main__.py`.
`base.py` gagne `probe_version()`, utilitaire partagé, best-effort par construction.

**34 tests neufs** (`test_adapters.py`, `test_cli.py`, plus extensions de `test_workflow.py` et
`test_recovery.py`) — aucun n'invoque un vrai fournisseur : `cli.ADAPTERS` est systématiquement
substitué par des `FakeAdapter`, parce que Claude Code et Codex CLI sont tous deux réellement sur le
PATH de cette machine. `ruff check .`, `mypy --strict`, `pytest` : tout vert (196 passés, 1 skip
préexistant). Smoke-test manuel de `new`/`status` avec les vrais `adapter_id` (sans appel : ces deux
commandes ne sondent ni n'invoquent jamais un adaptateur).

### Choix pris sans spécification explicite

`resume --answer` sur une `QUESTION` née en `FINAL_A` traité comme `REVISION_A`, par symétrie avec le
cas `BLOQUE` (§2 ne tranchait que `PROPOSAL_A`/`REVISION_A`/`BLOQUE`) — non testé explicitement.
`collaboration_id` = nom du dossier passé en argument. Modèle Codex par défaut identique pour A et B.
Détails et justification complète dans `NOTES.md`.

### Le budget, porté au PO et tranché

`cli.py` : 273 lignes contre 155 visées (+118). Total production : 2 070 lignes brutes contre ~1 430
visées, au-delà même de la projection ~2 150 déjà actée le 2026-09-03. Rien n'est hors spécification :
`cli.py` implémente exactement la surface de §7. Porté au PO plutôt que tranché seul — une coupe
aurait changé un comportement spécifié. **Décision : « on continue », même arbitrage que le
2026-09-03, à condition de rouvrir la question si la croissance se poursuit sur un prochain palier.**

### Commits

`feat: ecrire le palier 4 (adaptateurs, cli) et trancher D-1, D-2, D-3`

### À retenir

Les trois décisions D-1/D-2/D-3 ont pris moins de contexte à trancher que redouté : chacune arrivait
déjà avec une recommandation motivée et une réserve honnête, écrites la session précédente pour
exactement cet usage. **Écrire la décision en attente avec sa recommandation, au moment où elle
apparaît, économise la reconstruction du contexte à la reprise.**

---

## 2026-09-04 (Claude) — Audit Codex du déploiement, plan correctif, lot 1

Scope déclaré par le PO : lire et analyser l'audit de déploiement produit par Codex, puis en tirer un
plan correctif soumis à Codex pour avis, puis exécuter.

### Ce qui a été fait

**Contre-lecture de l'audit** (`project/analyse/claude/2026-09-04-analyse-audit-deploiement.md`). Les
six constats les plus graves (C-01 à C-06) ont été confrontés ligne à ligne au code : tous se
confirment, aucun désaccord de sévérité, références exactes. Point que l'audit ne portait pas : la
« prochaine action » de `NOTES.md` — lancer une mission réelle payante — était exactement le scénario
que C-01 et C-02 rendaient dangereux.

**Plan correctif v1** (11 lots, 5 arbitrages D-4 à D-8, 2 constats complémentaires N-01 et N-02),
soumis à Codex. **Avis de Codex reçu**, filtré avec esprit contradictoire, puis **v2** :
`project/correctifs/2026-09-04-plan-correctif-audit-v2.md`. Ses trois affirmations vérifiables ont été
contrôlées avant d'être retenues — les trois exactes : empreintes factices de zéros dans
`test_recovery.py`, `_schema_version` qui accepte `True`, code 2 déjà pris par `argparse`.

Quatre propositions de Codex écartées avec motif : validation à deux niveaux (duplication de la même
règle) · ses deux solutions de verrou (voir ci-dessous) · renommer `supports_context_only`
(`adapters/base.py` est publié, §13 : le modifier coûte une migration) · supprimer
`transformations`/`had_bom` (toucherait ~15 sites d'appel pour une ambiguïté que le retrait du
vocabulaire suffit à lever).

**Lot 1 écrit, testé, commité** : `lock.py` 108 → 181 lignes (+73 pour ~37 estimées).

### Décisions

- **D-5 tranché par le PO, contre l'avis de Codex** : `WAITING_HUMAN` = **5**, pas 0. Motif retenu :
  mettre 0 recrée l'indiscernabilité que C-03 reproche justement à `_drive()` — « il te faut
  répondre » et « c'est fini » rendraient le même code. Table complète en §7 : `0` AWAITING_APPROVAL ·
  `1` refus avant mutation · `2` réservé à `argparse` · `3` INTERRUPTED · `4` ERROR · `5`
  WAITING_HUMAN.
- **Budget augmenté** : projection ~2 275 lignes (+205). La condition ouverte le matin a été rouverte
  et refermée par le PO. Motif : aucun de ces ajouts n'est une accrétion de contrôle — ce sont des
  garanties déjà annoncées par la conception et non tenues par le code.
- **Première mission réelle repoussée après les lots 1 à 4** (lot 5 en plus pour une recherche).
- **C-06 est un risque accepté, pas un défaut à corriger** : tant qu'il est ouvert, toute mission
  réelle se fait dans une collaboration jetable, hors de tout dossier de valeur.
- **Récupération du verrou mort : design changé en cours d'écriture.** La v2 annonçait un déplacement
  atomique avec remise en place ; sûr à deux processus, il laissait une fenêtre à trois. Remplacé par
  un **jeton de récupération** exclusif : qui n'a pas le jeton ne touche jamais au verrou, donc il n'y
  a plus rien à remettre en place. Limite résiduelle — un jeton orphelin demande une suppression
  humaine — écrite dans le message d'erreur.

### La contre-épreuve, et ce qu'elle a coûté

Le test de course a été rejoué contre l'ancien verrou avant d'être cru (`RULES.md`). Il a fallu deux
passes, et **chaque échec était un vrai défaut** :

1. le concurrent écrivait son résultat dans un `except` qui rattrapait aussi l'échec de
   **libération** — un second entrant se serait déclaré refusé, et le test aurait masqué exactement la
   double entrée qu'il cherche ;
2. sous Windows, un PID terminé reste **vivant** pour `OpenProcess` tant qu'un handle du processus est
   ouvert : l'objet `Popen` gardé en variable locale faisait refuser les trois concurrents pour la
   mauvaise raison.

Corrigés, la contre-épreuve donne le résultat attendu : **ancien verrou, verrou mort, trois processus,
trois entrées dans la section critique.** Les deux leçons sont dans `RULES.md`.

### Commits

`c940961` docs: audit Codex et plan correctif en onze lots · `373479d` fix: acquisition du verrou
atomique et reprise sûre (C-02, N-02) · `f437fb5` docs: NOTES.md pointé sur le lot 2.

### À retenir

**Une contre-épreuve qui échoue deux fois avant de montrer le défaut attendu n'est pas une perte de
temps : c'est la seule chose qui a prouvé que le test valait quelque chose.** Sans elle, la suite
serait verte avec un test de course structurellement aveugle.

**État à la reprise :** 2 143 lignes de production, **202 tests verts** + 1 ignoré, `ruff` et
`mypy --strict` verts, arbre git propre. Lot 2 non commencé, non bloqué — c'est le plus gros du plan.

---

## 2026-09-04 (soir) — Lot 2 : porte d'état et intervention sous verrou

**Scope déclaré :** lot 2 du plan correctif. Constats fermés : **C-01**, **C-02 volet A**, **D-4**, et
**N-01** — qui n'était porté par aucun lot.

### Ce qui a été fait

`workflow.run()` reçoit désormais l'intervention humaine (`Answer` / `RetryCall`) et l'applique **sous
le verrou**, entre la relecture et la nouvelle **porte d'état** ; `cli.py` ne lit ni n'écrit plus aucun
état, il valide ses arguments et transmet. `_apply_answer`, `_archive` et `_prepare_retry` ont quitté
`cli.py`. `--answer` archive par **copie** puis écrit puis publie ; `--retry-call` ne publie **aucun
état intermédiaire**. `command()` est résolu avant la publication de `CALLING`.

### Décisions prises en cours d'écriture

- **N-01 est entré dans ce lot.** La porte refuse `ERROR` ; sans la table fermée d'incidents
  relançables, `ERROR` devenait un cul-de-sac dont plus aucune commande ne sortait. Le correctif aurait
  transformé un défaut en blocage.
- **Le rejeu de `--answer` après la troisième écriture est un refus explicite, pas un no-op.**
  L'intervention est déjà appliquée ; `resume` seul enchaîne. Reconnaître ce cas aurait demandé une
  seconde branche de reprise — ce que la v2 avait justement simplifié.
- **L'archive est idempotente**, ce que la v2 ne disait pas : sans cela, un arrêt entre l'archive et
  l'écriture de `demande.md` empilait une seconde archive au rejeu.
- **La preuve « `CALLING` avant `Popen` » a changé de point d'observation** : `command()` étant
  désormais résolu avant la publication, la lire dans `FakeAdapter.command()` ne prouvait plus l'ordre.
  Elle se lit dans le **processus lancé**, qui relit `etat.json` depuis son `cwd`.

### Les trois contre-épreuves

Chaque correctif a été neutralisé un par un, et la suite a montré le défaut attendu :

| Correctif neutralisé | Ce que la suite a montré |
|---|---|
| porte d'état | second `run` après `QUESTION` : `calls` `(1, 0)` → `(2, 1)` — **A et B rappelés** |
| tolérance d'intégrité du prévol | le rejeu est **refusé avant d'avoir pu réparer** |
| archive idempotente | `demande.md.001` **et** `demande.md.002` |

La première a **corrigé le test** : le compteur d'appels était vérifié *dans* un `assertRaises`, si
bien qu'une porte absente faisait échouer sur « exception non levée » et masquait l'appel payant.

### Le budget, rouvert

Le lot a coûté **+142 lignes brutes** pour ~30 annoncées — mais **+64 en code effectif**. Première
mesure complète du projet en code effectif (hors blanches, commentaires, docstrings) : **1 601 pour
2 285 brutes**, ratio 70 %. La projection validée le matin (~2 275 brutes) est dépassée avant le lot 3.

**Décision PO attendue avant le lot 3.** Contre les ~1 500 de `POURQUOI.md`, la mesure comparable est
1 601, pas 2 285 ; projection à terminaison ~1 900 effectives. Question posée telle quelle :
*qu'est-ce qu'on retire en échange ?* — marge en lots 7, 9 et 10.

### Commits

`0362082` docs: journaliser la session precedente · le lot 2 dans cette session.

### À retenir

**Un correctif qui ferme une porte doit ouvrir la sortie dans le même lot.** N-01 n'était rattaché à
aucun lot ; l'avoir laissé au suivant aurait livré une version où `ERROR` ne se quitte plus.

**État à la reprise :** 2 285 lignes brutes / 1 601 effectives, **222 tests verts** + 1 ignoré, `ruff`
et `mypy --strict` verts. Lot 3 non commencé — court, mais il doit corriger un test qui fige le défaut
(`tests/test_cli.py::test_retry_call_needs_a_non_empty_reason` attend `0`, doit attendre `3`).

---

## 2026-09-04 (suite) — Lots 3 à 10 : l'audit Codex refermé, sauf C-11

**Scope déclaré :** « enchaînons sur les lots suivants ». Huit lots, huit commits.

| Lot | Constat | Ce qui a changé |
|---|---|---|
| 3 | C-03 | Table D-5 dans `_drive`. Le test qui **figeait le défaut** (`0` après un délai) attend `3`. |
| 4 | C-05 | `read_result` confronte `resultat.json` aux flux ; prompt et réponse confrontés à leurs empreintes **avant toute branche**. `IntegrityError` → `INTEGRITY_MISMATCH`. |
| 5 | C-04 | `corpus.read_manifest` strict ; contrôle complet du **contenu** sous verrou, juste avant l'appel. |
| 6 | C-08 | `positive_seconds` aux trois entrées ; `--max-revisions` ≥ 0 ; `schema_version: true` refusé. |
| 7 | C-07, D-7 | `_drain` : deux échéances communes, `STREAMS_UNCLOSED`, descripteurs non fermés sous lecteur vivant. |
| 8 | C-10 | Enveloppe par types nommés, sans capture globale de `ValueError` ; `LAUNCH_FAILED` et `DECODE_FAILED`. |
| 9 | C-09, D-8 | `Review.to_dict()` canonique dans `echanges/` ; `revue_normalisee.json` sort de §7 ; D-8b appliqué. |
| 10 | C-06, D-6 | `invocation_args` sans `argv[0]` ; frontière d'effets écrite comme **limite déclarée**. |

### Les contre-épreuves, une par lot

Chaque correctif a été neutralisé avant d'être cru. Aucune n'a été décevante :

- **lot 4** — sans les empreintes, un prompt et une réponse **substitués** sont repris sans un mot ;
  sans le contrôle de flux, un `stdout.txt` altéré part au contrat et finit en `ERROR` ;
- **lot 5** — fichier altéré, absent et surnuméraire passent **tous les trois** ;
- **lot 6** — un `run` à `timeout=0` **laisse partir un appel** ;
- **lot 7** — mesure directe, hors suite : **22 s en `COMPLETED`** avant, **10,2 s en
  `STREAMS_UNCLOSED`** après, pour une borne annoncée de 12 s ;
- **lot 8** — un `Popen` en échec sortait en code 1 avec un état `RUNNING`, le faux « possiblement
  payé » exactement ;
- **lot 9** — le registre des constats est **illisible par `json.loads`** et sa `severity` absente.

### Deux découvertes de plateforme, mises en règle

- **`Path.glob` est insensible à la casse sous Windows.** Un test cherchait le dossier d'appel de B
  par `glob("*B*")` : il a désigné celui de **A** dès que son UUID contenait un `b`. Le test passait
  pour la mauvaise raison jusqu'à ce que la forme canonique le fasse échouer.
- **Un descendant survivant garde `stdout.txt` ouvert**, donc le dossier n'est pas effaçable avant sa
  fin. C'est la conséquence assumée de ne pas fermer un descripteur sous un lecteur vivant, pas une
  fuite — documentée en §5, et le test concerné utilise `ignore_cleanup_errors=True`.

### Ce qui reste

**C-11 seul, et il est bloqué sur une décision : appels payants.** `GUIDE.md` n'est volontairement pas
écrit d'avance — prescrire une commande qu'on n'a jamais lancée est ce que `RULES.md` interdit.

### Commits

`49a4254` porte d'état + intervention · `22992c4` codes de sortie · `77029bb` intégrité de reprise ·
`a94e78d` corpus sous verrou · `5dabd67` paramètres numériques · `2fa2676` nettoyage borné ·
`0ebe760` classification des erreurs · `0aec8e1` revue canonique · `421c0b9` frontière d'effets.

### À retenir

**Le brut n'est pas la bonne unité pour juger ce projet.** +589 lignes brutes pour ~205 estimées fait
peur ; +256 en code effectif, pour un total de **1 793 contre les ~1 500 visés**, dit la vérité. Les
deux tiers de l'écart sont le motif écrit à côté de chaque garantie — et c'est justement ce qui a
permis d'enchaîner dix lots sans relire le plan en entier.

**État à la reprise :** 2 659 lignes brutes / 1 793 effectives, **255 tests verts** + 2 ignorés,
`ruff` et `mypy --strict` verts, arbre propre. Deux décisions attendent le PO : l'autorisation
d'appels payants (lot 11) et la taille (rouverte, non tranchée).

---

## 2026-09-04 (soir) — Lot 11 : deux missions réelles, et ce qu'elles ont trouvé

**Scope :** « on enchaîne sur un essai avec un test grandeur nature ». Autorisation d'appels payants
donnée. Sujet arbitré : IAbinome par lui-même, cycle court (`--max-revisions 0`).

**Décision du PO sur la taille, en ouverture de session : « rien tout simplement ».** La condition
rouverte le matin est refermée, sans condition de réouverture.

### Résultat

**Neuf appels, 765 s, deux permutations.** La conception (A = outil 1, B = outil 2) est allée au bout :
`AWAITING_APPROVAL`, code `0`, livrable de 125 lignes. La recherche (A = outil 2, B = outil 1) s'est
arrêtée en `ERROR` sur une cause de forme, décrite ci-dessous. Journal complet :
`conception/OBSERVATIONS_MISSION_REELLE.md` ; sorties réelles conservées dans `conception/essais/`.

### Les deux défauts, et pourquoi 259 tests verts ne les voyaient pas

1. **`_A_REVISION` et `_A_FINAL` ne portaient pas les balises.** Ils disaient « rends DOCUMENT » quand
   le contrat exige `IABINOME:DOCUMENT`. A a obéi littéralement. **Aucune mission ne pouvait aller au
   bout**, et l'échec tombait au dernier appel, après avoir payé tous les autres.
2. **Le prompt interdisait à A de lire son propre corpus.** « Tu ne modifies aucun fichier et
   n'exécutes rien » : A a demandé à l'humain de coller le contenu des trois fichiers. La conception
   promet l'inverse — le `cwd` est donné pour qu'il y lise.

**`FakeAdapter` émet la bonne balise quoi qu'on lui demande : il ne lit pas le prompt.** Aucun test à
faux agent ne pouvait voir un défaut de gabarit. `tests/test_prompts.py` lit désormais les gabarits.

### Ce que la mécanique a tenu, elle

`invocation_args` conforme à D-6b · `status` en lecture seule sous verrou tenu · **la table de relance
N-01 a servi pour de vrai** et conservé deux appels déjà payés · `resume --answer` avec archive par
copie · **déplacement d'une collaboration en cours d'usage**, aucun chemin absolu persisté · codes de
sortie D-5 observés · aucun rejeu automatique dans aucun des deux échecs.

### Un motif écrit qui s'est révélé faux

**D-2 posait que quota épuisé rend `1` chez les deux outils. Faux pour outil 1 :** message sur `stdout`
avec code `0`. Le garde-fou ne l'attrape pas, et le cycle finit en `CONTRACT_ERROR` — le diagnostic
trompeur que D-2 disait éviter. Décision conservée, motif corrigé, reconnaissance de quota laissée
hors du programme (§8 interdit de lire le texte du fournisseur).

### Commits

`ea8a009` balises des prompts de révision et finalisation · `8b96d77` lecture du corpus autorisée ·
`8a5b40b` prémisse de D-2 et trois règles.

### À retenir

**Le grandeur nature a trouvé, en une soirée, deux défauts qu'aucune suite de tests ne pouvait voir —
et l'un des deux rendait l'outil incapable de terminer une seule mission.** Le protocole, lui, a tenu
sur chacun des deux échecs : réponse brute préservée, incident nommé, aucun rejeu, relance ciblée. Ce
n'est pas la boucle A/B qui était fragile, ce sont les mots qu'on lui donnait.

**Une décision attend le PO** : le bloc JSON clôturé précédé d'une phrase (§6 du journal). Coût contre
principe, pas sûreté.

---

## 2026-09-05 — Relecture externe du fonctionnement : huit observations, huit exactes

**Scope :** réouverture ciblée de la relecture croisée, suspendue le 2026-09-03. La condition écrite
était remplie — deux défauts de gabarit trouvés en mission réelle qu'aucune relecture n'avait vus.

**La consigne a elle-même été relue avant envoi** : cinq corrections, toutes retenues. La plus utile
impose de **signaler une contradiction entre deux sources** plutôt que de choisir en silence celle qui
permet de construire un manquement. Tests écartés de cette première passe, traités séparément ensuite.

### Résultat

**Huit observations, huit exactes** — vérifiées dans le code avant toute disposition, l'observation 4
reproduite avant correction. Six correctifs de code, deux corrections documentaires, **un correctif
implicite refusé**. Dispositions complètes dans `project/analyse/codex/2026-09-05-dispositions-relecture.md`.

| # | Défaut | Disposition |
|---|---|---|
| 1 | une pompe en échec ne l'était pas : le préfixe passait pour le flux complet | corrigé — `STREAM_FAILED`, pas de `resultat.json` |
| 2 | `RESPONSE_STORED` contournait la confrontation des flux | corrigé |
| 3 | sévérité omise + `RESOLVED` fermait un constat que §6 dit garder ouvert | corrigé |
| 4 | `docs\note.md` ou `./note.md` → fichier déclaré surnuméraire au premier `run` | corrigé — chemins canonisés |
| 5 | verrou tronqué par un arrêt : blocage définitif | **correctif refusé**, message et promesse corrigés |
| 6 | code 1 « avant mutation » rendu après avoir muté la demande | corrigé — corpus vérifié avant l'intervention |
| 7 | `RuntimeError` nu et dossier d'appel orphelin | corrigé — `AdapterError`, résolution avant le premier octet |
| 8 | reprise locale de `DECODE_FAILED` promise, jamais écrite | promesse corrigée, optimisation différée |

### Le seul refus, et son motif

**Observation 5.** Récupérer automatiquement un verrou illisible reviendrait à effacer celui d'un
détenteur **vivant** surpris dans sa fenêtre création→écriture. C'est **exactement la même fenêtre** :
le crash qu'on répare et la course qu'on introduit ont la même probabilité, pour une conséquence pire —
deux détenteurs simultanés au lieu d'un blocage visible. `POURQUOI.md` règle 2 : ce qu'on retirerait en
échange, c'est la garantie d'exclusion elle-même. Message rendu actionnable, promesse corrigée.

### Un effet de bord traité plutôt que contourné

Déplacer `command()` avant le premier octet écrit a changé la sémantique de `FakeAdapter.calls` : il
compte désormais des **résolutions**, qui bornent par le haut les appels réellement partis. C'est
l'assertion sur laquelle repose toute la preuve « aucun appel payé ». `fakes.launched_calls()` lit le
disque pour la mesure exacte, et les tests concernés s'y appuient.

### À retenir

**Le rendement a démenti mon pronostic.** J'attendais « moyen » et j'avais tort. La différence avec
l'audit du 2026-09-04 tient à la question posée : « où promet-il ce qu'il ne tient pas » force à citer
une phrase et à construire un cas ; « audite ce déploiement » invitait à énumérer des risques.

**Trois défauts sur six vivaient dans une fenêtre** — lecture rompue, arrêt entre deux écritures,
séparateur de chemin — et **aucun n'était atteignable par un cycle nominal**. Suspendre la relecture
externe parce que la suite de tests est verte était une erreur de raisonnement : les deux ne couvrent
pas le même espace.

**État à la reprise :** **275 tests verts** + 2 ignorés, `ruff` et `mypy --strict` verts.

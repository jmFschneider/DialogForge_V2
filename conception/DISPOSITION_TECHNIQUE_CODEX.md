# Disposition des huit remarques techniques de Codex

> 2026-09-03, sur `CONCEPTION_FINALE.md`. Dernière passe avant le code.
> **Les huit sont retenues.** Aucune n'est écartée — c'est la première revue du cycle où c'est le cas,
> et ça se comprend : elle ne porte plus sur des choix mais sur des **défauts vérifiables**.

**Quatre sont des défauts que j'ai laissés dans le document** (1, 2, 3, 4), **quatre sont des trous**
(5, 6, 7, 8). Le n°2 est le plus grave : il fait perdre une réponse déjà payée.

| # | Sujet | Disposition | Résolution retenue |
|---|---|---|---|
| 1 | « Ne propose ni n'exécute de modification » | **ACCEPTÉE** | Défaut réel : la phrase interdit à A **le livrable lui-même**. Séparer *proposer* de *appliquer*. |
| 2 | Réponse complète perdue entre `resultat.json` et `RESPONSE_STORED` | **ACCEPTÉE — la plus grave** | La reprise **inspecte le dossier d'appel** : `resultat.json` valide = retraitement local, jamais de nouvel appel. |
| 3 | « Fermer le terminal » jamais spécifié | **ACCEPTÉE** | C'est `O4`, l'objectif que j'avais moi-même désigné comme le plus fragile — et je l'ai laissé sans spécification. |
| 4 | Le discriminateur ne s'applique pas à la finalisation | **ACCEPTÉE** | Incohérence réelle. Résolue vers **l'uniformité** : un seul analyseur, aucun cas particulier. |
| 5 | « Décision jamais déduite des sévérités » vs `ACCEPTER` + `BLOCKING` refusé | **ACCEPTÉE, résolution de Codex adoptée** | Sa version est meilleure : **conserver la décision de B**, signaler l'incohérence, `WAITING_HUMAN`. |
| 6 | Adaptateurs facultatifs sans défaut ; Opus 5 / Fable 5 disparus | **ACCEPTÉE** | Adaptateurs **obligatoires** ; le **modèle par défaut est résolu par l'adaptateur** selon le rôle. |
| 7 | `RECHERCHE` sans corpus ; corpus immuable vs nouvelle demande | **ACCEPTÉE** | Corpus non vide **obligatoire** en recherche. `--answer` ne change jamais le corpus. |
| 8 | Encodage, plafond de sortie, OS supportés | **ACCEPTÉE** | Fixés en `§0.1` de la spécification. |

---

## Les quatre points qui méritent une justification

### N°2 — pourquoi c'est le plus grave

`resultat.json` est écrit à l'étape 7, `RESPONSE_STORED` publié juste après. **Entre les deux, l'état
dit encore `CALLING`.** Un crash dans cette fenêtre produit : une réponse complète sur le disque, un
état qui la déclare incertaine, et donc `INTERRUPTED` — c'est-à-dire une relance humaine qui **repaie
un appel dont on a déjà la réponse**.

C'est exactement le défaut que tout le protocole durable existe pour empêcher. Le correctif ne coûte
rien parce que le marqueur existe déjà : **`resultat.json` n'est écrit qu'à la sortie propre**, donc
sa présence *est* la preuve de complétude. La reprise n'a qu'à le lire.

*Effet secondaire utile : cela justifie rétrospectivement `A4` de l'audit d'accrétion, où j'avais
retiré le renommage `.part`/`.bin` au motif que `resultat.json` suffisait comme marqueur. Il devient
maintenant porteur pour la reprise, donc doublement justifié.*

### N°4 — pourquoi l'uniformité plutôt que l'exception

On peut soutenir que `FINAL_A` n'a rien à demander : le cycle se termine, les révisions sont faites.
Mais un cas particulier coûte **un second chemin d'analyse et sa famille de tests**, alors que
l'uniformité n'en coûte aucun.

Et un `QUESTION` en finalisation reste **légitime** : mieux vaut s'arrêter que livrer un document dont
A sait qu'il manque l'essentiel. Aucun risque de boucle — chaque `QUESTION` exige une action humaine.

**Le discriminateur s'applique aux quatre appels de A. Un analyseur, une règle.**

### N°5 — Codex a raison contre ma rédaction

Mes deux règles se contredisaient. La sienne les réconcilie mieux que je ne l'aurais fait.

Le mal mesuré (`H-01`) était que le programme **transformait silencieusement** `REVISER` en `ACCEPTER`.
Le remède n'est pas que le programme rejette `ACCEPTER` — c'est encore lui qui juge sur les sévérités.
Le remède est qu'il **ne touche pas à la décision**.

Et rejeter la revue comme erreur de contrat **perdrait les constats de B**, qui peuvent être bons.
Donc : revue valide et persistée · incohérence signalée dans `last_incident` · `WAITING_HUMAN`.
C'est aussi `R29` — ambiguïté, main à l'humain.

### N°6 — ce que « par défaut » veut dire quand la permutation est le sujet

Deux choses différentes étaient confondues.

**L'adaptateur devient obligatoire.** Le PO choisit selon ses crédits et son humeur : la valeur change
à chaque lancement. **Une valeur qui change à chaque fois ne doit pas avoir de défaut** — même
raisonnement que `--reviewer-access`, et il retire une décision du code.

**Le modèle garde un défaut, mais il est résolu par l'adaptateur.** « Opus 5 pour A » n'a aucun sens si
A est Codex. Le défaut est donc une propriété de **l'adaptateur pour un rôle**, pas une constante du
noyau — ce qui garde les noms de fournisseurs dans `adapters/`, conformément à `C15b`.

*C'est une amélioration réelle de `CLAUDE.md` §6, qui énonçait les modèles comme des défauts globaux.*

### N°7 — la conséquence oubliée de « corpus figé »

J'avais écrit « pas de `refresh` » sans le relier à `--answer`. Or si l'humain répond à une `QUESTION`
en fournissant une demande qui exige d'autres sources, la collaboration devient le mauvais contenant :
son corpus ne peut plus servir la nouvelle demande, et le figer était précisément la décision.

**Règle : `--answer` remplace la demande, jamais le corpus.** S'il faut d'autres sources, on crée une
collaboration — la demande peut être reprise telle quelle. Et **un corpus non vide est obligatoire en
recherche**, puisque V0.1 n'a aucun accès externe : sans corpus, il n'y a rien à chercher.

---

## Ce que la revue n'a pas trouvé, et qui reste ouvert

Rien de nouveau. Les points restants sont ceux déjà nommés en `§12` de la spécification :
**B-2** (contrat de B), la **caractérisation des deux CLI** — aucune n'a jamais été lancée — et la
longueur de la colonne Code, reportée après la phase 2.

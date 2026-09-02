# INVENTAIRE — récolte de deux mois d'apprentissage

> Produit le 2026-09-03 selon `RECOLTE.md`. **Une ligne par leçon, une destination par ligne.**
> Cible de forme : ~200 lignes, à comparer aux 194 lignes de `DialogForge\context\`.
> **Non relu.** La relecture contradictoire (Codex, consigne d'omission) reste à faire — voir la fin.

## Question préalable — tranchée

**L'inventaire couvre aussi les leçons de conduite de projet.** Motif : la doctrine déjà distillée
avait tranché de fait — `context\supervision.md` pèse 113 des 194 lignes et ne parle que de budgets,
de surveillance et d'erreurs. Les écarter aurait laissé la moitié du capital dans un chantier gelé.
Elles vont en **Règle**, jamais en **Code**. *Arbitrage à confirmer ou rouvrir par l'humain.*

## Rendement par source

| # | Source | Rendement | Note |
|---|---|---|---|
| 1 | `context\*.md` — 194 l. | **fort** | Densité maximale, comme annoncé. `supervision.md` porte à lui seul toute la conduite. |
| 2 | 42 messages `fix:` | **moyen** | 9 retenus ; les 33 autres corrigent un sous-système écarté. |
| 3 | 85 `[DIFFÉRÉ]` du backlog | **faible** | 7 retenus. Le reste est de l'appareil d'autonomie différé. |
| 4 | `GUIDE_UTILISATION.md` — 541 l. | **moyen** | L'ergonomie apprise tient en quelques lignes ; le reste décrit ce qui tombe. |
| 5 | `preuves\README.md` + `ARRET_REFACTORING.md` | **fort** | Les 5 faits mesurés et les 3 défauts sont tous retenus. |
| 6 | 4 × `version_finale.md` — 3 850 l. | **inégal** | Préanalyse et refonte doc : fort. Revue 2026-07-24 : fort. MariaDB : 2 lignes sur 1 243. |
| 7 | Noms des 69 fichiers `tests\` | **fort** | 14 nomment la boucle A/B, **55 nomment l'appareil écarté**. La proportion est la leçon. |
| 8 | `Florapy_V2\…\decisions.md` + missions | **fort** | Le retour d'usage réel : c'est là qu'on voit ce que la boucle produit et où elle rate. |

**Arrêt.** `history.md` (2 533 l.) et `README.md` (1 046 l.) n'ont pas été ouverts : les sources 1 à 8
répétaient déjà leurs constats sans en ajouter. La source 6 était épuisée avant sa fin — la conception
MariaDB (1 243 l.) n'a rendu que deux lignes.

---

## Code — devient une ligne d'IAbinome

| # | Leçon | Source |
|---|---|---|
| C1 | La boucle est `PROPOSITION_A → CRITIQUE_B → REVISION_A → FINALISATION_A`, révisions bornées, défaut 2. | 1, 6 |
| C2 | `etat.json` par collaboration : phase close, numéro de révision, chemins des artefacts — relu tel quel pour reprendre. | 6 |
| C3 | Toute écriture d'artefact est atomique : fichier temporaire puis renommage. | 1, 6 |
| C4 | Le nom du fichier temporaire est dérivé de l'appel, jamais fixe — un nom fixe fait collisionner deux processus. | 6 |
| C5 | Verrou exclusif par dossier de collaboration, portant PID, date et commande. | 6 |
| C6 | La réponse de B est validée contre un contrat avant tout traitement : `decision` ∈ {ACCEPTER, REVISER, BLOQUE}, plus `analysis`. | 1, 2 |
| C7 | Décodage strict avant toute réécriture : jamais agir sur une sortie non décodée. | 2 |
| C8 | La gravité d'un constat n'est jamais déduite de la décision globale de B. | 6 |
| C9 | Un finding incomplet ou une sévérité inconnue est une erreur récupérable et tracée, jamais un silence. | 6 |
| C10 | `resolved_changes` : B déclare lesquels de ses constats antérieurs la nouvelle version corrige réellement. | 6 |
| C11 | Un JSON enveloppé dans un bloc Markdown est accepté — cas réel, corrigé une fois. | 2 |
| C12 | On conserve la réponse brute à côté de la forme normalisée et de la règle appliquée. | 3 |
| C13 | Canonicalisation déterministe avant validation, plutôt que tolérance au décodage. | 3 |
| C14 | Le protocole JSON des revues est versionné, avec des champs stables. | 3 |
| C15 | Un adaptateur par CLI (`claude`, `codex`, `fake`) derrière un contrat d'agent unique. | 6 |
| C16 | L'agent `fake` est scripté et il est le seul agent utilisé par les tests. | 1 |
| C17 | Le contrat d'erreur de quota est commun aux fournisseurs, jamais propre à l'un d'eux. | 6 |
| C18 | Une archive se retrouve par rôle et identifiant d'appel, jamais par une chaîne de fournisseur (`*claude.txt`). | 6 |
| C19 | Le compteur de tokens est `normalized_input_tokens + output_tokens` — additionner `input_tokens` donne un faux pour l'un des deux fournisseurs. | 5 |
| C20 | Le fuseau horaire du quota fournisseur est respecté explicitement. | 2 |
| C21 | Une heure de reprise fournisseur illisible produit un repli borné et **signalé**, jamais une boucle de réveils silencieuse. | 5 |
| C22 | Tuer un appel tue l'arbre de processus : des sous-processus orphelins ont été observés sous Windows. | 2, 6 |
| C23 | L'artefact est écrit **avant** que la phase soit marquée close. | 2 |
| C24 | Un corps volumineux est segmenté, jamais tronqué. | 6 |
| C25 | Une seule surface d'exécution : ni mode « direct » ni mode « durable » concurrents. | 4 |
| C26 | Une seule commande de reprise : relire `etat.json`, repartir de la dernière phase close. | 6 |

## Prompt — devient une phrase dans un gabarit A ou B

| # | Leçon | Source |
|---|---|---|
| P1 | A distingue **faits, hypothèses, incertitudes et recommandations** — convention qui a tenu sur un livrable de 1 275 lignes. | 6 |
| P2 | B n'a aucun outil : aucune commande, aucune lecture de fichier, uniquement le contexte fourni. | 6 |
| P3 | B reçoit la version courante et les constats ouverts, pas tout l'historique — et le prompt le lui dit, pour qu'il ne réclame pas les documents antérieurs. | 6 |
| P4 | `BLOQUE` est réservé à une information humaine indispensable. | 6 |
| P5 | Chaque observation de B reçoit **exactement une disposition** : acceptée et intégrée / rejetée avec justification / différée avec condition / bloquante. | 6 |
| P6 | Le contrat JSON est rappelé à chaque tour, pas seulement au premier. | 2 |
| P7 | A en révision produit une version **complète**, pas une liste de corrections. | 6 |
| P8 | A en finalisation intègre les apports sans raconter le processus interne, et signale les incertitudes restantes. | 6 |
| P9 | A liste en tête ce qu'il **n'a pas** traité de la demande : une exigence peut disparaître entre le prompt et la livraison sans que personne ne s'en aperçoive. | 8 |
| P10 | Le livrable nomme ses **limites de preuve** — ce qui n'a pas été vérifié — pas seulement ses conclusions. | 6 |
| P11 | Chaque décision proposée porte sa **réversibilité**, énoncée au moment où elle se prend. | 8 |
| P12 | Chaque décision porte contexte, décision, raison et portée — la structure qui rend le registre FloraPi relisible deux mois après. | 8 |
| P13 | Une affirmation d'un document peut avoir vieilli : vérifier l'état réel plutôt que la reprendre. | 6 |
| P14 | Cadrage — « n'invente pas de décision absente de l'échange » : des décisions inventées puis intégrées à une spécification ont été mesurées. | 6 |
| P15 | Cadrage — la demande est le seul document que lira la suite du cycle : reprendre valeurs, formats et fichiers cibles au lieu d'y renvoyer. | 6 |
| P16 | Cadrage — décrire un livrable unique, sans mentionner les agents ni répartir le travail entre eux. | 6 |
| P17 | Cadrage — une question à la fois, la plus utile. | 6 |
| P18 | Cadrage — A énumère en clôture les questions restées sans réponse ; une question de calibrage ignorée a livré 2 espèces sur 20 à 30 attendues. | 8 |
| P19 | Cadrage — proposer une première demande après quelques questions, avant validation. | 3 |
| P20 | Cadrage — présenter des alternatives et demander un arbitrage ciblé, plutôt qu'une question ouverte. | 3 |
| P21 | La consigne de lecture obligatoire est réservée à A ; « ne déduis jamais leur contenu, lis-les ». | 6 |
| P22 | Les contraintes de forme du livrable sont déterministes, pas laissées à l'appréciation. | 3 |
| P23 | Ne jamais faire prescrire une commande qui n'a pas été lancée. | 1 |
| P24 | Alléger : douze critères d'acceptation imbriqués **dégradent** la sortie des modèles récents. | 5 |

## Règle — va dans `CLAUDE.md` ou `POURQUOI.md`, jamais dans le code

> Les règles déjà écrites dans `CLAUDE.md`, `POURQUOI.md` ou `project\RULES.md` ne sont pas répétées ici.

| # | Leçon | Source |
|---|---|---|
| R1 | Un plafond est une autorisation maximale, pas une cible de consommation. | 1 |
| R2 | Coût et tokens se surveillent en parallèle : leur rapport dépend du modèle, du cache et du volume de sortie — aucune équivalence fixe. | 1, 5 |
| R3 | À 70 % d'un axe, signaler ; à 85 %, décider si le reste tient dans la réserve ; à 100 %, jamais augmenter puis reprendre automatiquement. | 1 |
| R4 | Une relance identique sur le même état est interdite : cause, configuration ou décision humaine doit avoir changé de façon vérifiable. | 1, 4 |
| R5 | La réussite opérationnelle n'est pas une acceptation : document, tests et contrats sont revus à la porte finale même sans erreur signalée. | 1 |
| R6 | **Le coût réel n'est mesuré qu'à moitié** : Codex remonte `total_cost_usd: null`, Claude déclare `input_tokens: 2`. | 5 |
| R7 | Le cadrage coûte des tokens que personne ne compte — 229 288 mesurés, hors mission, hors plafond. Décider où on les impute. | 5 |
| R8 | Une réservation gouverne l'**admission** d'un appel, pas sa consommation : un appel admis sur 144 000 en a consommé 4 802 042. | 5 |
| R9 | Vérifier que la donnée demandée existe **avant** de lancer une recherche : deux missions ont échoué en interrogeant la littérature sur une variable qu'elle ne traite pas. | 8 |
| R10 | Une mission qui échoue deux fois de la même façon ne se relance pas une troisième : on change le mandat, pas le budget. | 8 |
| R11 | Une exigence disparue en silence entre le prompt et la livraison n'est pas un arbitrage : c'est une perte. | 8 |
| R12 | **Une leçon écartée avec son motif est décidée.** Ce qui se perd est ce qui disparaît sans que personne s'en aperçoive. | — |
| R13 | Le prompt système ne confine rien : une frontière de sécurité énoncée en consigne est déclarative, pas mécanique. | 6 |
| R14 | Une consigne ne protège pas un gel : il faut un levier unique, testé, sans porte parallèle. | 8 |
| R15 | Une intention documentaire n'est pas une preuve de livraison : tout « livré » exige un commit, un test ou un contrôle identifiable. | 6 |
| R16 | La disparition d'une branche locale n'est pas une preuve de fusion. | 6 |
| R17 | Un fichier canonique par contenu ; ne jamais recopier le même journal dans deux fichiers. | 1, 6 |
| R18 | Chaque élément suivi porte exactement un statut principal. | 6 |
| R19 | Une porte franchie se note **avec sa preuve**, et l'humain arbitre entre chaque étape. | 5, 6 |
| R20 | Un plan de N lots dont le lot 0 n'aboutit pas ne prouve rien sur les N−1 autres. | 5 |
| R21 | Contrôler son propre travail trouve des défauts — trois en une passe — mais ne remplace pas le contradicteur. | 2 |

## Test — devient un test de régression avec l'agent `fake`

| # | Leçon | Source |
|---|---|---|
| T1 | `REVISER` avec un finding vide ne devient jamais `ACCEPTER`. | 6 |
| T2 | `ACCEPTER` portant une sévérité `high` / `error` / `warning` : la gravité n'est pas déduite de la décision. | 6 |
| T3 | JSON enveloppé dans un bloc Markdown : décodé. | 2 |
| T4 | JSON invalide : erreur récupérable et tracée, ni plantage ni silence. | 6 |
| T5 | `BLOQUE` : la boucle s'arrête et rend la main à l'humain. | 6 |
| T6 | Deux processus sur la même collaboration : le second est refusé. | 6 |
| T7 | Interruption entre l'appel et l'écriture : la reprise ne rejoue pas l'appel. | 6 |
| T8 | Heure de reprise fournisseur illisible : repli borné et signalé. | 5 |
| T9 | Plafond de révisions atteint : finalisation, jamais boucle infinie. | 6 |
| T10 | Reprise sur un artefact déjà présent : pas de réécriture (idempotence). | 6 |
| T11 | Écriture interrompue : aucun artefact partiel visible. | 6 |
| T12 | `resolved_changes` citant un constat inexistant : détecté. | 6 |
| T13 | Le gabarit de B ne contient aucun outil. | 6 |
| T14 | `demande.md` absent ou vide : refus **avant** tout appel fournisseur. | 6 |
| T15 | Garde structurelle : la suite complète ne lance aucun processus fournisseur. | 1 |

## Écarté — avec le motif, en une ligne

| # | Ce qui tombe | Motif |
|---|---|---|
| X1 | SQLite, MariaDB, journal d'événements versionné, projections durables | Interdit n°2 ; `etat.json` suffit à l'échelle d'une collaboration. |
| X2 | Baux, fencing, générations, jetons de récupération, heartbeat | Interdit n°3 ; sans worker il n'y a qu'un seul processus. |
| X3 | Budgets, réservations, admission, axes et sous-budgets | Interdit n°4 ; les plafonds fournisseur suffisent. |
| X4 | Worker Windows, tâche planifiée, arrêt coopératif | Interdit n°3 ; on lance, ça tourne, on ferme le terminal. |
| X5 | GUI, desktop, brouillons, onglets, modales d'intervention | Interdit n°5. |
| X6 | Implémentation autonome, worktrees, commits pilotés, remèdes, replanification | Interdit n°1 ; jamais menée au bout, nulle part. |
| X7 | Confinement, attestations, sceaux d'exécutable, campagnes de sandbox, porte de rôle | Sans écriture agent, il n'y a rien à confiner. |
| X8 | Chaos, campagnes d'endurance, redémarrage Windows réel | Il n'y a pas de service à éprouver. |
| X9 | Contrat de contexte, paquets thématiques, delta, capsules, consignes | La demande tient dans un fichier lu en entier. |
| X10 | Reconstruction, migration héritée, récupération hors ligne, incidents typés | Pas d'état durable à reconstruire. |
| X11 | Stratégies `review` / `council` / `adaptive`, routage automatique de modèles | Deux rôles fixes, deux modèles choisis à la main. |
| X12 | Mode « agent A seul » | Sans B il ne reste pas un outil, seulement un appel d'agent. |
| X13 | Les quatre modes d'exécution du guide | Confusion mesurée à l'usage ; IAbinome n'en a qu'un. |
| X14 | Relecture contradictoire **automatique** du cadrage | Un appel fournisseur de plus avant que la boucle démarre ; l'humain relit. |
| X15 | Instrumentation du préfixe stable, mesure des formes inconnues | De la mesure sur un système qui n'existe plus. |
| X16 | 78 des 85 `[DIFFÉRÉ]` du backlog | Tous portent sur un sous-système écarté ci-dessus. |
| X17 | 33 des 42 correctifs `fix:` | Tous corrigent un sous-système écarté ci-dessus. |
| X18 | 55 des 69 fichiers de tests | Ils nomment l'appareil écarté. **14 seulement nomment la boucle A/B.** |
| X19 | Le refactoring en 15 lots et sa préanalyse de 1 275 lignes | Chantier gelé ; seule sa méthode de disposition des observations est reprise (P5). |
| X20 | La conception MariaDB — 1 243 lignes | Interdit n°2 ; deux lignes seulement en sortent (C24, R17). |

---

## Ce que l'inventaire ne tranche pas

Ces trois points restent des **décisions de l'étape 1**, pas des leçons :

1. Garder ou non le cadrage automatique (`framing.py`) — P14 à P20 n'ont de valeur que si on le garde.
2. Jusqu'où dégraisser `contracts.py` — C6 à C14 en fixent le plancher fonctionnel.
3. Le format exact d'`etat.json` — C2 en fixe le contenu, pas la forme.

## Contrôle de forme

| Contrainte de `RECOLTE.md` | État |
|---|---|
| Une ligne par leçon | Respecté. |
| Une destination par ligne | Respecté ; aucune ligne n'en porte deux. |
| Colonne **Écarté** renseignée avec motif | 20 entrées, toutes motivées. |
| ≤ ~200 lignes | Respecté. |
| **Code** est la colonne la plus courte | **Non tenu** — 26 lignes de Code contre 24 de Prompt. À examiner : plusieurs lignes Code sont des contraintes d'une ligne, pas des sous-systèmes. |

## Relecture contradictoire — à faire

Consigne unique à donner à Codex, sans autre cadrage :

> **« Qu'est-ce qui a été écarté en silence ? »**

Trois endroits à lui signaler comme suspects : l'arrêt anticipé sur `history.md` et `README.md`
(source 1-8 jugées suffisantes) ; les agrégats X16 à X18, qui écartent 166 éléments en trois lignes ;
et la colonne Code plus longue que prévu.

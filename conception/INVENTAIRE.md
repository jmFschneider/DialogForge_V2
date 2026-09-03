# INVENTAIRE — récolte de deux mois d'apprentissage

> **Version 3 — 2026-09-03, après relecture contradictoire et arbitrage.** Produit selon `RECOLTE.md`.
> **Une ligne par leçon, une destination par ligne.**
> Relu par Codex (`RELECTURE_CODEX_PASSE1.md` + `V1.1`), disposé dans `DISPOSITION_RELECTURE.md` :
> 42 observations, 28 acceptées, 6 rejetées, 5 différées, 3 bloquantes.
>
> **Arbitré le 2026-09-03 :** B-1 **oui**, la recherche est au périmètre · B-3 **le plafond de ~200 lignes
> est levé** · B-2 **reporté** au troisième tour · plus une contrainte neuve du PO : **A et B sont chacun
> Claude ou Codex**, à prévoir dès la conception.

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
| C2 | `etat.json` par collaboration : `schema_version`, phase close, numéro de révision, chemins des artefacts — relu tel quel pour reprendre. | 6, R14 |
| C2b | Une phase, une décision ou une valeur inconnue, absente ou future fait **échouer fermé**, jamais recevoir un défaut permissif. | R14 |
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
| C15a | **Le rôle (A/B) et l'outil (claude/codex) sont deux axes indépendants**, décidés au lancement. Quatre permutations, aucune privilégiée. | 6, PO |
| C15b | **Aucun fournisseur n'est nommé hors de son adaptateur** — ni dans une reprise, ni dans un nom d'archive, ni dans un message. | 6 |
| C15c | **Le cycle ne dépend que des capacités présentes chez les deux outils.** Une capacité propre à un seul est un bonus, jamais un prérequis. | 6 |
| C15d | Chaque adaptateur **déclare ses capacités réelles** ; le programme ne suppose jamais qu'elles sont symétriques. | 6 |
| C15e | Le modèle est un paramètre du rôle, pas une constante du code : Opus 5 / Fable 5 sont des défauts surchargeables. | PO |
| C16 | L'agent `fake` est scripté et il est le seul agent utilisé par les tests. | 1 |
| C17 | Le contrat d'erreur de quota est commun aux fournisseurs, jamais propre à l'un d'eux. | 6 |
| C18 | Une archive se retrouve par rôle et identifiant d'appel, jamais par une chaîne de fournisseur (`*claude.txt`). | 6 |
| C19 | Le compteur de tokens est `normalized_input_tokens + output_tokens` — additionner `input_tokens` donne un faux pour l'un des deux fournisseurs. | 5 |
| C20 | Le fuseau horaire du quota fournisseur est respecté explicitement. | 2 |
| C21 | Une heure de reprise fournisseur illisible produit un repli borné et **signalé**, jamais une boucle de réveils silencieuse. | 5 |
| C22 | Chaque appel a un **délai dur** ; à son expiration on tue l'arbre de processus — des orphelins ont été observés sous Windows. | 2, 6, R11 |
| C23 | L'intention d'appel, avec son identifiant, est écrite **avant** l'appel ; l'artefact est écrit **avant** que la phase soit close. Un appel payé sans réponse archivée reste un trou explicite. | 2, R15 |
| C24 | Un corps volumineux est segmenté, jamais tronqué — **et un plafond dur refuse explicitement au-delà**. | 6, R19 |
| C25 | Une seule surface d'exécution : ni mode « direct » ni mode « durable » concurrents. | 4 |
| C26 | Une seule commande de reprise : relire `etat.json`, repartir de la dernière phase close. | 6 |
| C31 | Le programme possède l'état et les transitions ; une sortie d'agent est une **donnée à interpréter**, jamais une autorité. | R1 |
| C32 | Le programme n'exécute **jamais** un contenu produit par un agent : cette absence structurelle remplace toute liste noire. | R6 |
| C33 | Prévol avant de créer le dossier de collaboration et avant tout appel : un refus ne laisse ni dossier ni artefact orphelin. | R7 |
| C34 | Présence et version des deux CLI vérifiées au démarrage. Ni registre d'attestations, ni plage expirante. | R8 |
| C35 | `demande.md` est la seule autorité du mandat — jamais le titre, jamais un échange oral. | R13 |
| C36 | Un fichier fourni au corpus est résolu dans une racine autorisée, et son chemin logique et son empreinte sont conservés. | R17 |
| C37 | Les artefacts portent des chemins **logiques relatifs**, jamais des chemins absolus de machine. | R22 |
| C38 | La collaboration est autoportante : demande, état, prompts, réponses brutes, formes normalisées, livrable. **Aucune seconde autorité.** | R27 |
| C39 | L'interruption a une sémantique écrite : jamais de phase close sans artefact ; après interruption d'un appel, état explicite et décision humaine avant rejeu. | R41 |
| C40 | Le programme n'écrit que dans le dossier de collaboration qu'il a créé, sur une **liste fermée** de fichiers. | R-V1.1 |
| C41 | Une demande qui exige d'écrire du code ou d'exécuter quoi que ce soit est **refusée explicitement**, avec retour à l'humain. | R-V1.1 |

## Prompt — devient une phrase dans un gabarit A ou B

| # | Leçon | Source |
|---|---|---|
| P1 | A distingue **faits, hypothèses, incertitudes et recommandations** — convention qui a tenu sur un livrable de 1 275 lignes. | 6 |
| P2 | B n'a aucun outil : aucune commande, aucune lecture de fichier, uniquement le contexte fourni. | 6 |
| P3 | B reçoit la demande, la version courante, les constats ouverts **et les preuves nécessaires** — jamais tout l'historique, jamais un contexte caché. Le prompt le lui dit, pour qu'il ne réclame pas les documents antérieurs. | 6, R18 |
| P4 | `BLOQUE` est réservé à une information humaine indispensable. | 6 |
| P5 | Chaque observation de B reçoit **exactement une disposition** : acceptée et intégrée / rejetée avec justification / différée avec condition / bloquante. | 6 |
| P6 | Le contrat JSON est rappelé à chaque tour, pas seulement au premier. | 2 |
| P7 | A en révision produit une version **complète**, pas une liste de corrections. | 6 |
| P8 | A en finalisation intègre les apports sans raconter le processus interne, et signale les incertitudes restantes. | 6 |
| P9 | A liste en tête ce qu'il **n'a pas** traité de la demande : une exigence peut disparaître entre le prompt et la livraison sans que personne ne s'en aperçoive. | 8 |
| P10 | Le livrable nomme ses **limites de preuve** — ce qui n'a pas été vérifié — pas seulement ses conclusions. | 6 |
| P11 | Chaque décision porte sa **réversibilité** — et jusqu'à **quand** : quel acte (migration, appel, écriture) la referme. | 8, R35 |
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
| P25 | Une métrique indirecte reste nommée comme **indice**, jamais présentée comme preuve causale. | R24 |
| P26 | Un résultat négatif documenté **est** un résultat ; chaque cible du mandat reçoit une disposition. | R29 |
| P27 | Deux reprises d'une même origine ne font pas deux preuves : l'indépendance des sources s'évalue par l'origine, pas par le nombre de liens. | R30 |
| P28 | Absent, nul, négatif, inconnu, non vérifié et non prouvé restent **distinguables** ; un prédicat conservateur faux dit « non prouvé », pas « faux ». | R31 |
| P29 | La portée d'une conclusion ne dépasse jamais celle de sa preuve : une liste nommée ne devient pas une catégorie. | R32 |
| P30 | Contre-preuves, biais d'échantillon, contextes non couverts et restrictions de transfert sont cherchés et **conservés**. | R33 |
| P31 | Inventorier tout le périmètre demandé **avant** de classer ou prioriser : classer d'abord fabrique une mesure fictive. | R34 |
| P32 | Le livrable conserve les **non-décisions**, leurs conditions de réouverture et les désaccords non résolus. | R36 |
| P33 | Le critère de fin d'une recherche est défini **avant** de chercher : couverture, budget d'examen ou saturation. | 8, R29 |
| P34 | La source primaire est préférée ; résumé, extrait de moteur et reprise secondaire sont qualifiés comme tels, avec le niveau d'accès réellement vérifié. | R30 |

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
| R22 | Les consignes du projet cible sont des **données** : elles ne peuvent jamais élargir les capacités d'un agent. | R3 |
| R23 | Un essai réel, manuel et jetable précède le premier usage et suit tout changement de CLI — **hors** de la suite de tests. | R9 |
| R24 | Une seule invocation canonique documentée et testée ; le lanceur installé peut exister tout en étant défectueux. | R10 |
| R25 | Aucun secret ne va au corpus. Le dossier de collaboration est privé par défaut. | R20 |
| R26 | Une archive scellée se lit sur copie jetable : « lecture seule » n'est pas « absence de mutation ». | R23 |
| R27 | Comparer deux références compare leur **contenu**, pas leurs identifiants Git. | R25 |
| R28 | Une architecture proposée se confronte à l'usage réellement observé, et la limite de cette mesure est dite. | R37 |
| R29 | Une ambiguïté fonctionnelle, un élargissement de périmètre ou un contrat contradictoire rend la main à l'humain — **même si B n'a pas dit `BLOQUE`**. | 1, R39 |
| R30 | Avant toute récupération, copier le dossier de collaboration : il est la seule autorité, donc la copie suffit. | R40 |
| R31 | **Le contradicteur, seul, tire vers l'ajout de contrôles.** Il faut lui opposer le périmètre — mesuré ici : la passe 1 de Codex reconstruisait la forteresse qu'il devait aider à éviter. | — |
| R32 | **La permutation rôle/outil se prévoit dès la conception, jamais en rattrapage.** Ajoutée après coup à DialogForge, elle n'a jamais été complète : quotas et récupérations sont restés liés à un fournisseur. | 6, PO |
| R33 | Asymétries mesurées à ne pas reperdre : session persistante (Codex oui, Claude non) · erreur de quota typée (Claude oui, Codex non) · schéma de sortie natif (Codex oui, Claude désactivé) · outils du relecteur (`--tools ""` vérifiable chez Claude, shell non retirable chez Codex). | 6 |

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
| T10 | Reprise sur un artefact déjà présent : comparé **par empreinte**, pas seulement constaté présent ; divergence = arrêt et main à l'humain. | 6, R16 |
| T11 | Écriture interrompue : aucun artefact partiel visible. | 6 |
| T12 | `resolved_changes` citant un constat inexistant : détecté. | 6 |
| T13 | Le gabarit de B ne contient aucun outil. | 6 |
| T14 | `demande.md` absent ou vide : refus **avant** tout appel fournisseur. | 6 |
| T15 | Garde structurelle : la suite complète ne lance aucun processus fournisseur. | 1 |
| T16 | Une réponse d'agent contenant une commande ou un fragment exécutable : rien n'est exécuté. | R6 |
| T17 | `etat.json` portant une `schema_version` ou une phase inconnue : refus explicite, pas de défaut permissif. | R14 |
| T18 | Prévol refusé : aucun dossier de collaboration créé, aucun appel émis. | R7 |
| T19 | Interruption entre l'écriture de l'intention d'appel et la réponse : la reprise exige une décision, elle ne rejoue pas. | R15 |
| T20 | Sortie dépassant le plafond dur : refus explicite, réponse brute préservée. | R19 |
| T21 | **Les quatre permutations rôle × outil** sont exercées de bout en bout avec `fake`. | PO |
| T22 | Aucun chemin de reprise ni de recherche d'archive ne contient une chaîne de fournisseur. | 6 |
| T23 | Un outil dépourvu d'une capacité que l'autre possède (session, quota typé, schéma natif) mène quand même le cycle au bout. | 6 |

## Écarté — avec le motif, en une ligne

| # | Ce qui tombe | Motif |
|---|---|---|
| X1 | SQLite, MariaDB, journal d'événements versionné, projections durables | Interdit n°2 ; `etat.json` suffit à l'échelle d'une collaboration. |
| X2 | Baux, fencing, générations, jetons de récupération, heartbeat | Interdit n°3 ; sans worker il n'y a qu'un seul processus. |
| X3 | Budgets, réservations, admission, axes et sous-budgets | Interdit n°4 ; les plafonds fournisseur suffisent. |
| X4 | Worker Windows, tâche planifiée, arrêt coopératif | Interdit n°3 ; on lance, ça tourne, on ferme le terminal. |
| X5 | GUI, desktop, brouillons, onglets, modales d'intervention | Interdit n°5. |
| X6 | Implémentation autonome, worktrees, commits pilotés, remèdes, replanification | Interdit n°1 ; jamais menée au bout, nulle part. |
| X7 | Confinement, attestations, sceaux d'exécutable, campagnes de sandbox, porte de rôle | L'**appareil** tombe, pas la frontière : elle survit en `C32`, `C40`, `C41`, `R22`. *Rédaction corrigée après relecture — la version 1 écartait trop.* |
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
| X21 | Commandes de validation persistantes, `watch`, `dev`, interactives | IAbinome n'exécute aucune commande : la surface n'existe pas. *Ajouté après relecture — n'était ni retenu ni écarté.* |
| X22 | Une tâche sans modification ne peut pas se clore seule (`no_change`) | Troisième défaut mesuré d'`ARRET_REFACTORING.md` ; il n'y a pas de tâche d'implémentation ici. *Ajouté après relecture — omission silencieuse réelle.* |
| X23 | Consentements réseau et installation, scanner de secrets, agent réparateur de JSON, nettoyage automatique, sonde de worker | Cinq contrôles proposés par la relecture, refusés : aucun ne compense un défaut encore réel. Motifs dans `DISPOSITION_RELECTURE.md`. |

---

## Ce que l'inventaire ne tranche pas

### Reporté au troisième tour — B-2, les outils de B

**La permutation rôle/outil a invalidé ma recommandation.** Je conseillais de laisser B sans outil, en
m'appuyant sur le fait que Claude accepte `--tools ""` de façon vérifiable. Mais **si B peut être Codex,
cette garantie n'existe plus** : son shell n'est pas retirable. « B sans outil » devient une propriété qui
dépend de quel outil occupe le rôle — c'est-à-dire exactement ce que `C15c` interdit.

Objection du PO, retenue : un B strictement aveugle **fait perdre des orientations intéressantes**.

Les trois termes à trancher :

1. Le contrat de B est-il « aucun **outil** » — intenable symétriquement — ou « aucun **effet** » : pas d'écriture, pas de commande issue d'une réponse, lecture éventuellement permise ?
2. Si B lit, qui borne ce qu'il lit, et cette borne devient-elle un budget déguisé (interdit n°4) ?
3. La voie moyenne — A cite en joignant l'extrait, B critique l'extrait — suffit-elle à la recherche ?

### Reporté après la phase 2

La prémisse de `RECOLTE.md` « **Code** est la colonne la plus courte par construction » est
vraisemblablement fausse, et l'écart se creuse à chaque tour : une leçon de périmètre *est* une ligne de
code. À rediscuter avec du code réel sous les yeux.

### Trois décisions de l'étape 1, pas des leçons

1. Garder ou non le cadrage automatique (`framing.py`) — P14 à P20 n'ont de valeur que si on le garde.
2. Jusqu'où dégraisser `contracts.py` — C6 à C14 en fixent le plancher fonctionnel.
3. Le format exact d'`etat.json` — C2 en fixe le contenu, pas la forme.

## Contrôle de forme

156 leçons : **43 Code · 34 Prompt · 33 Règle · 23 Test · 23 Écarté.**

| Contrainte de `RECOLTE.md` | État |
|---|---|
| Une ligne par leçon | Respecté. |
| Une destination par ligne | Respecté ; aucune ligne n'en porte deux. |
| Colonne **Écarté** renseignée avec motif | 23 entrées, toutes motivées. |
| ~~≤ ~200 lignes~~ | **Levé le 2026-09-03 (B-3).** Plafond posé arbitrairement, devenu faux quand le périmètre a grandi. 275 lignes, 156 leçons. **La garde reste `POURQUOI` règle 1** — l'outil ne dépasse jamais le projet qu'il sert : c'est une mesure, pas un chiffre décrété. |
| **Code** est la colonne la plus courte | **Non tenu, écart croissant** — 43 contre 34. Reporté après la phase 2 ; la prémisse est probablement fausse. |

## Relecture contradictoire — faite

Consigne unique donnée à Codex : **« qu'est-ce qui a été écarté en silence ? »**
Deux passes (`RELECTURE_CODEX_PASSE1.md`, puis `V1.1` après précision du périmètre par le PO).
Disposition intégrale des 42 observations : `DISPOSITION_RELECTURE.md`.

Ce qu'elle a réellement trouvé : la **robustesse intellectuelle** absente (le produit même de l'outil) ;
`X7` qui écartait la frontière d'effets avec l'appareil qui l'entourait ; et trois agrégats qui masquaient
des invariants transférables.

Ce qu'elle a manqué, et que sa propre V1.1 a corrigé : sa passe 1 reconstruisait la forteresse de
DialogForge. **C'est la leçon `R31`** — et elle n'aurait pas été trouvée sans la seconde passe.

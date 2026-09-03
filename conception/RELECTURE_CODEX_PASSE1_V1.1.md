# Relecture Codex — passe 1, version 1.1

> **Demande de l'utilisateur, conservée pour mémoire — 2026-09-03**
>
> « L'origine de la complexité de DialogForge réside en partie dans le confinement des agents : il faut le penser autrement, différemment. Pour l'instant, le nouvel outil servira uniquement à des phases de conception, pas de codage. Cette porte sera franchie après la validation de cette première brique.
>
> L'objectif est d'avoir un outil suffisamment léger pour faire dialoguer deux agents et arriver à des conceptions robustes — conceptions et recherches. Revois ton premier jet sans l'effacer, enregistre ta réponse en version 1.1 et sois critique par rapport à cette première lecture. »

## Statut de cette version

La passe 1 originale reste intacte dans `RELECTURE_CODEX_PASSE1.md`. Elle remplissait son rôle de filet large : trouver ce qui avait disparu, sans trier. La présente version ne retire aucune observation de cette archive ; elle corrige leur interprétation à la lumière du périmètre désormais explicite.

**Périmètre de la première brique :** produire des documents de conception ou de recherche par dialogue A/B. Aucun code cible écrit, aucune commande proposée par un agent exécutée, aucune installation, aucun commit, aucun worker et aucune mission d'implémentation.

**Verdict révisé :** l'inventaire de Claude reste incomplet, mais ma première lecture réintroduisait par endroits la logique de forteresse de DialogForge. Sur les 42 observations brutes, 20 appartiennent au socle, 9 doivent être réalisées sous une forme beaucoup plus légère, 7 sont des règles d'usage plutôt que du code, 2 doivent attendre une preuve supplémentaire ou la porte du codage, et 4 ne concernent pas cette première brique.

## Autocritique de la passe 1

### 1. J'ai confondu conservation d'une leçon et réimplémentation de son mécanisme

Le fait que le confinement déclaratif de DialogForge ait échoué ne commande pas de reconstruire attestations, sceaux, campagnes de sandbox, portes de rôle et profils expirants. La leçon transférable est plus courte : **un agent ne produit que du texte ; le programme décide seul quels fichiers prédéfinis il écrit et n'exécute jamais le contenu produit.**

### 2. J'ai surpondéré la sécurité d'une ancienne fonction absente

Les observations 2 à 6 de la passe 1 décrivent surtout les risques d'un agent qui code ou dont les commandes sont exécutées. Cette fonction est interdite dans la première brique. Il reste une petite frontière de sécurité, mais elle ne doit pas redevenir un sous-système : profils de capacités explicites, absence d'écriture cible, aucun shell dérivé d'une réponse, et refus de démarrer si le profil demandé n'est pas disponible.

### 3. J'ai traité « B sans outils » comme une règle universelle

`INVENTAIRE.md:P2` et ma propre observation 2 sont trop absolus. Pour une conception fondée sur un corpus fourni, B doit pouvoir travailler uniquement sur la demande, la proposition et les preuves transmises. Pour une recherche, une critique robuste peut exiger que B ouvre et vérifie indépendamment une source. La bonne règle porte sur les **capacités nécessaires à la mission**, pas sur le nom du rôle :

- profil `conception` : corpus fourni, aucune exploration autonome nécessaire ;
- profil `recherche` : accès de consultation aux sources externes à décider explicitement, citations et niveau d'accès obligatoires ;
- dans les deux profils : aucune écriture dans le projet cible, aucune installation, aucune commande issue de la réponse.

Cette distinction doit être tranchée dans la spécification ; elle ne justifie pas un moteur général de permissions.

### 4. J'ai présenté une corrélation comme une nécessité

L'observation 38 déduisait des compteurs `session_renewals = 3` et `2` que le renouvellement avait été nécessaire au succès. Les fichiers prouvent que des renouvellements ont eu lieu, pas qu'ils étaient indispensables ni que la boucle légère doit les reproduire. C'est une hypothèse à mesurer, pas une omission acquise.

### 5. Certaines observations appartiennent seulement à l'ancien moteur

La tâche sans changement, les commandes de validation persistantes, la surveillance d'un worker et la récupération d'une mission d'implémentation ne doivent pas entrer dans la première brique. Les garder comme mémoire du passé est utile ; les convertir en exigences d'IAbinome serait une rechute.

### 6. J'ai insuffisamment mis au centre la robustesse intellectuelle

La première lecture détaillait davantage la frontière d'exécution que les conditions d'une bonne conception. Pour IAbinome, le risque principal n'est pas qu'un agent modifie Git : c'est qu'une exigence, une objection, une source contraire ou une limite de preuve disparaisse pendant la convergence. La V1.1 donne donc priorité à la traçabilité du raisonnement, à la contradiction réelle et à la qualité des preuves de recherche.

## Requalification des 42 observations

Légende : **SOCLE** = nécessaire à la première brique ; **ALLÉGÉ** = leçon conservée sans la machinerie DialogForge ; **RÈGLE** = conduite/documentation, pas fonctionnalité ; **DIFFÉRÉ** = après mesure ou lors de la porte du codage ; **ÉCARTÉ** = hors première brique, avec motif explicite.

| # | Disposition V1.1 | Requalification |
|---:|---|---|
| 1 | **SOCLE** | L'orchestrateur possède l'état et les transitions ; les agents proposent du texte. |
| 2 | **ALLÉGÉ** | Remplacer « B sans outils » par deux profils explicites, conception et recherche ; aucune permission cachée. |
| 3 | **ALLÉGÉ** | Les consignes du projet ne peuvent élargir les capacités, mais aucun appareil d'attestation n'est repris. |
| 4 | **DIFFÉRÉ** | Ne construire aucun neutraliseur universel de configuration CLI ; vérifier seulement les options natives nécessaires au profil retenu et documenter la limite. |
| 5 | **ALLÉGÉ** | Pas d'installation. Le réseau n'existe que dans le profil recherche choisi par l'humain, sans système général de consentements persistants. |
| 6 | **SOCLE** | Le programme n'exécute jamais une commande ou un fragment fourni par un agent ; cette absence structurelle remplace la blacklist. |
| 7 | **SOCLE** | Valider demande, agents, chemins et profil avant de créer la collaboration ou d'appeler un fournisseur. |
| 8 | **ALLÉGÉ** | Vérifier disponibilité et version des deux CLI au démarrage ; pas de registre d'attestations ni de plages expirantes en V1. |
| 9 | **RÈGLE** | Faire un smoke réel manuel et jetable avant la première utilisation et après changement de CLI ; ne pas l'intégrer à la suite ordinaire. |
| 10 | **RÈGLE** | Documenter et tester une seule invocation canonique. |
| 11 | **SOCLE** | Délai dur par appel et terminaison de l'arbre de processus. |
| 12 | **ÉCARTÉ** | IAbinome n'exécute aucune commande de validation produite par un agent ; `watch` et `dev` ne font pas partie de sa surface. |
| 13 | **SOCLE** | `demande.md` est l'autorité complète du mandat, jamais le titre ni la conversation orale. |
| 14 | **SOCLE** | `etat.json` porte `schema_version`; état ou phase inconnue entraîne un refus explicite. |
| 15 | **SOCLE** | Persister l'identité et l'état `appel_en_cours` avant chaque appel afin qu'une interruption ne provoque pas un rejeu silencieux. |
| 16 | **ALLÉGÉ** | À la reprise, un artefact existant est comparé par empreinte ; divergence = arrêt humain. Pas de quarantaine ni de registre d'événements. |
| 17 | **ALLÉGÉ** | Les fichiers locaux fournis sont résolus et bornés aux racines choisies ; conserver chemin logique et empreinte dans un manifeste simple. |
| 18 | **SOCLE** | B reçoit toujours la demande, la version courante, les constats ouverts et les preuves nécessaires ; aucune critique ne dépend d'un contexte caché. |
| 19 | **ALLÉGÉ** | Plafond de taille clair ; au-delà, arrêt explicite avec réponse brute préservée si elle existe. Pas de spool ni de quarantaine. |
| 20 | **RÈGLE** | Ne jamais fournir de secret au corpus. Les dossiers de collaboration sont privés par défaut ; un scanner de secrets n'entre pas en V1 sans incident réel. |
| 21 | **ÉCARTÉ** | Aucun agent de réparation JSON. Canonicalisation déterministe minimale ; sinon l'appel échoue clairement et rend la main. |
| 22 | **ALLÉGÉ** | Artefacts et manifestes utilisent des chemins logiques relatifs ; aucun mécanisme de migration d'anciens journaux. |
| 23 | **RÈGLE** | Les archives scellées se lisent sur copie ; ce principe protège la récolte et les audits, pas le moteur courant. |
| 24 | **SOCLE** | Toute métrique indirecte reste nommée comme indice, jamais comme preuve causale. |
| 25 | **RÈGLE** | Pour comparer deux références, comparer le contenu pertinent et pas seulement les identifiants Git. |
| 26 | **RÈGLE** | Nettoyage avec cible vérifiée et conservation possible ; la V1 n'a toutefois aucun nettoyage automatique de projet. |
| 27 | **SOCLE** | Une collaboration est autoportante : demande, état, prompts, réponses brutes, versions normalisées, preuves et livrable vivent dans son dossier. Aucune seconde autorité cachée. |
| 28 | **ÉCARTÉ** | Il n'existe ni tâches d'implémentation ni notion `no_change` dans la première brique. |
| 29 | **SOCLE** | En recherche, chaque cible reçoit une disposition ; un résultat négatif documenté est un résultat. |
| 30 | **SOCLE** | L'indépendance des sources est évaluée ; plusieurs reprises d'une même origine ne font pas plusieurs preuves. |
| 31 | **SOCLE** | Distinguer absent, nul, négatif, inconnu, non vérifié et non prouvé. |
| 32 | **SOCLE** | Interdire toute généralisation au-delà du contexte, de la population et de la variable effectivement prouvés. |
| 33 | **SOCLE** | Rechercher contre-preuves, biais d'échantillon, contextes absents et restrictions de transfert. |
| 34 | **SOCLE** | Inventorier tout le périmètre demandé avant de classer ou prioriser. |
| 35 | **SOCLE** | Toute recommandation dit jusqu'à quand elle est réversible et quel acte change cette réversibilité. |
| 36 | **SOCLE** | Le livrable conserve les non-décisions, leurs conditions de réouverture et les désaccords non résolus. |
| 37 | **RÈGLE** | Une architecture proposée doit être confrontée à l'usage ou au besoin réellement observé, avec la limite de cette mesure. |
| 38 | **DIFFÉRÉ** | Besoin de renouvellement ou de capsule non prouvé ; mesurer les échecs de contexte des appels simples avant d'ajouter quoi que ce soit. |
| 39 | **SOCLE** | Ambiguïté fonctionnelle, extension de périmètre ou contrat contradictoire rend la main à l'humain. |
| 40 | **ALLÉGÉ** | Puisque tout l'état est dans un dossier, une copie de ce dossier suffit à la reprise ; aucun protocole de récupération multi-autorités. |
| 41 | **SOCLE** | Interruption définie : ne jamais marquer une phase close sans artefact ; après interruption d'un appel, état explicite et décision humaine avant rejeu. |
| 42 | **ÉCARTÉ** | Aucun worker ni traitement en arrière-plan à sonder ; le processus est au premier plan et se termine avec le terminal. |

## Ce que la première brique doit réellement protéger

### Frontière légère d'effets

1. Les agents renvoient du texte ; ils ne décident jamais de l'état du cycle.
2. IAbinome n'écrit que dans le dossier de collaboration qu'il a créé, sur une liste fermée de fichiers.
3. IAbinome n'exécute aucun contenu produit par un agent.
4. IAbinome ne modifie ni le projet étudié, ni Git, ni sa configuration, ni ses dépendances.
5. Une demande de code ou d'exécution provoque un refus explicite et un retour à l'humain.
6. Les capacités de consultation nécessaires sont attachées au profil de mission, pas accordées progressivement par un moteur de permissions.

Ce contrat doit tenir dans quelques fonctions et quelques tests. S'il exige attestations, base, worker, baux ou campagne de certification, la frontière a été mal dessinée.

### Robustesse du dialogue A/B

1. La demande est autonome : objectif, périmètre, exclusions, livrable, critères et questions ouvertes.
2. A sépare faits, inférences, hypothèses, recommandations et limites de preuve.
3. B reçoit la demande originale, la proposition courante et les preuves nécessaires ; il cherche exigences oubliées, contradictions, affirmations sans preuve et alternatives négligées.
4. Chaque constat de B garde un identifiant stable et reçoit exactement une disposition motivée.
5. A révise un document complet ; il ne remplace jamais un désaccord par une apparence de consensus.
6. Le nombre de révisions est borné ; l'humain arbitre les blocages et accepte ou refuse le livrable final.
7. « Cycle terminé » signifie que les phases ont produit leurs artefacts, pas que la conception est humainement acceptée.

### Robustesse particulière des recherches

1. Chaque affirmation importante cite une source localisable et indique le niveau d'accès réellement vérifié.
2. La source primaire est préférée ; résumé, extrait de moteur de recherche et reprise secondaire sont qualifiés comme tels.
3. L'indépendance des sources est vérifiée par leur origine, pas par le nombre de liens.
4. Les résultats négatifs et les cibles non couvertes sont visibles dès le résumé.
5. Contre-preuves, biais, populations et contextes non couverts sont conservés.
6. La portée d'une conclusion reste bornée par la variable et le contexte réellement étudiés.
7. Le critère de fin est défini avant la recherche : couverture demandée, budget d'examen ou saturation explicite.
8. Une recherche exploratoire n'autorise pas à elle seule une décision irréversible.

## Corrections proposées à l'inventaire de Claude

Ces corrections ne doivent pas encore être appliquées silencieusement à `INVENTAIRE.md`; elles sont soumises à l'arbitrage suivant.

1. **Réécrire X7.** Écarter l'appareil de confinement de DialogForge, mais conserver une frontière d'effets légère : document seulement, projet cible inchangé, aucune commande issue d'un agent, capacités de consultation explicites.
2. **Réviser P2.** Remplacer « B n'a aucun outil » par un contrat dépendant du profil : aucun outil pour une conception sur corpus complet ; consultation indépendante des sources à décider pour une recherche.
3. **Compléter C2.** Ajouter `schema_version`, appel en cours, identifiant d'appel et état d'interruption à `etat.json`.
4. **Ajouter le mécanisme manquant derrière T7.** L'intention d'appel est persistée avant le fournisseur ; un résultat incertain n'est jamais rejoué sans décision.
5. **Compléter C24.** Segmentation sans troncature, mais aussi plafond dur et échec explicite au-delà.
6. **Remplacer X9.** Écarter paquets thématiques, deltas et capsules en V1 ; conserver le risque de limite de contexte comme hypothèse instrumentée, sans mécanisme anticipé.
7. **Décomposer X16 à X18.** Ne pas restaurer les sous-systèmes, mais extraire leurs invariants transférables : prévol avant effet, état fermé, smoke réel, sortie brute, absence d'orphelin et idempotence.
8. **Ajouter les règles de recherche manquantes.** Indépendance des sources, résultats négatifs, portée des preuves, contre-preuves, critère de fin et restrictions de transfert.
9. **Ajouter une exclusion explicite.** Aucune tâche de codage, commande de validation, surveillance de worker, réparation par agent ou récupération multi-autorités dans la première brique.

## Porte future du codage

La première brique ne prépare pas clandestinement l'implémentation autonome. Lorsque les conceptions et recherches auront été validées en usage réel, une décision séparée devra répondre au minimum à ces questions :

- l'agent doit-il seulement proposer un plan de modification, ou écrire réellement ?
- dans quel environnement jetable ou réversible écrit-il ?
- qui exécute les validations et qui autorise les commandes ?
- quelles preuves d'innocuité sont nécessaires avant de toucher un projet réel ?
- quel contrôle existant doit être retiré pour chaque contrôle ajouté ?

Aucun composant de cette future porte ne doit entrer dans la V1 « au cas où ».

## Conclusion V1.1

La bonne correction n'est pas de nier tout confinement, ni de reconstruire celui de DialogForge. Elle consiste à **réduire radicalement les effets possibles** : deux agents discutent, IAbinome conserve fidèlement le dialogue et produit un document, l'humain décide. La robustesse recherchée se trouve d'abord dans la complétude du mandat, la traçabilité des objections, la qualité des preuves et la conservation des désaccords — pas dans une infrastructure d'exécution autonome.

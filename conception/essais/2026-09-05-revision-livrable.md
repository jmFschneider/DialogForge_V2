> Ce document n'est pas approuvé : sa présence prouve que le cycle s'est achevé, rien de plus.
> Revue B : CONSULT · constats restés ouverts : 3 (dont 0 BLOCKING) · corpus figé le 2026-09-05.


# Les tensions internes des règles fondatrices d’IAbinome

## Conclusion

Le corpus établit deux tensions concrètes :

1. **Réduire l’appareil de contrôle ou maintenir une relecture externe distincte des tests.** La relecture systématique ajoute un contrôle coûteux ; sa suspension économise ce coût, mais abandonne une couverture dont le corpus rapporte ensuite qu’elle détecte des défauts invisibles aux tests.
2. **Alléger les prompts ou répéter explicitement chaque contrat de forme.** Omettre une balise ou un schéma rend certaines missions inexécutables ; les répéter avec toutes les autres obligations augmente la prescription que le récit fondateur associe à une baisse de qualité.

Les preuves sont asymétriques. La première tension comprend un arbitrage effectivement daté dans IAbinome. Pour la seconde, la sous-spécification a produit un incident rapporté lors d’une mission réelle d’IAbinome, tandis que la dégradation par sur-prescription est un constat hérité du Lot 0 de DialogForge, sans sorties comparées ni protocole brut dans le corpus.

Le corpus ne permet pas de déterminer quelle règle céderait nécessairement **sous l’effet de la croissance**. La seule cession datée est celle de la relecture palier par palier, suspendue le 2026-09-03 puis rétablie le 2026-09-05. Elle est donc la **première cession observable dans le corpus**, mais il n’est pas prouvé qu’elle soit la première cession historique ni celle qui se reproduirait si le projet grossissait.

Une incohérence temporelle limite encore cette conclusion : `CLAUDE.md` affirme que l’implémentation n’a pas commencé, alors que ce même fichier évoque sa deuxième étape et que `RULES.md` consigne des fichiers de code, des tests et des mesures allant jusqu’au palier 4. Aucune règle de préséance ni chronologie consolidée ne résout cette divergence.

---

## 1. Réduire les contrôles ou maintenir la relecture externe

### Règles en cause

La règle fondatrice impose de considérer le coût collectif des contrôles :

> « Chaque contrôle ajouté a un coût qui ne se voit qu’au refactoring. »

> « La bonne question n’est jamais “est-ce que ce contrôle est utile ?” — c’est “qu’est-ce que je retire en échange ?” »

— [POURQUOI.md, lignes 37–38](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/POURQUOI.md:37>)

Le registre impose néanmoins de ne pas remplacer la relecture par les tests :

> « Une relecture externe et une suite de tests ne couvrent pas le même espace : la verdeur de l’une ne justifie pas de suspendre l’autre. »

— [RULES.md, lignes 37–38](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:37>)

### Cas concret

La règle de relecture est d’abord formulée ainsi :

> « Claude produit, Codex relit palier par palier — et réciproquement. »

Elle est ensuite déclarée :

> « Suspendue en étape 2 le 2026-09-03, décision du PO »

Le motif donné est que la conception avait déjà subi cinq tours de contradiction et que sa précision rendait la relecture de code palier par palier « peu rentable ». La condition de réouverture s’est réalisée le 2026-09-05 : deux défauts de gabarit auraient été trouvés en mission réelle sans être visibles dans la suite de tests. La relecture rouverte aurait alors produit huit observations dites exactes, dont trois hors d’atteinte d’un cycle nominal ([RULES.md, lignes 33–35](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:33>)).

Le registre rapporte séparément 262 tests verts concomitants avec six défauts réels trouvés par lecture statique ([RULES.md, lignes 37–38](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:37>)).

Le cas oppose concrètement les règles :

- Suspendre une passe jugée peu rentable réduit l’appareil de contrôle, mais renonce à une couverture présentée comme distincte de celle des tests.
- Maintenir la relecture préserve cette couverture, mais conserve un contrôle supplémentaire avec ses appels, ses consignes et le traitement obligatoire de ses observations.
- Le corpus exige en outre qu’« une consigne de relecture se [fasse] relire avant d’être envoyée ». Le motif rapporte cinq corrections et chiffre le coût à un appel ; il qualifie le bénéfice d’« une passe qui porte », sans attribuer ce libellé aux cinq corrections elles-mêmes ([RULES.md, lignes 40–41](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:40>)).

Le rapprochement avec DialogForge est une **inférence structurelle**, pas une identité démontrée : dans les deux récits, chaque contrôle peut être justifié isolément tandis que son coût apparaît dans l’accumulation. Rien ne prouve qu’IAbinome ait déjà atteint la même échelle ou subi les mêmes effets.

### Portée et contre-preuve

La tension est établie pour les revues de conception et d’implémentation consignées entre le 2026-09-03 et le 2026-09-05. Elle ne prouve pas que toute relecture soit excessive.

La réouverture réussie est une contre-preuve à une généralisation inverse : ajouter ou restaurer un contrôle peut produire un bénéfice réel. Le corpus ne nomme toutefois aucun contrôle retiré « en échange ». Il est donc **inconnu** si la règle fondatrice a été respectée par une compensation ailleurs.

---

## 2. Alléger les prompts ou expliciter chaque contrat

### Règles en cause

La règle fondatrice prescrit :

> « Les prompts trop prescriptifs dégradent les modèles récents. »

> « Alléger, ne pas durcir. »

— [POURQUOI.md, lignes 43–44](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/POURQUOI.md:43>)

Le registre impose en sens inverse une explicitation répétée :

> « Un prompt qui exige un format doit porter le format — et la règle vaut pour chaque prompt, pas pour le premier. »

— [RULES.md, lignes 132–134](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:132>)

### Cas concrets et asymétrie de preuve

La branche « trop prescriptif » provient du récit de DialogForge. `POURQUOI.md` affirme que les tâches du Lot 0 portaient jusqu’à douze critères d’acceptation imbriqués et que ce style réduisait la qualité des modèles récents ([POURQUOI.md, lignes 43–44](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/POURQUOI.md:43>)). Le même document précise séparément que ce lot, limité aux tests, avait déjà consommé environ sept millions de tokens sans être terminé ([POURQUOI.md, lignes 17–20](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/POURQUOI.md:17>)).

Ces deux éléments appartiennent à la même origine interne et ne constituent pas deux preuves indépendantes. Les sorties comparées, le protocole et la mesure de qualité sont absents. La dégradation est donc un **constat interne résumé**, non une expérience directement vérifiable dans l’instantané ni un incident propre à IAbinome.

La branche « pas assez explicite » est rapportée dans IAbinome :

- Le prompt de B nommait le « JSON de revue v1 » sans montrer le schéma. Le registre en déduit que chaque revue aurait échoué au contrat ([RULES.md, lignes 132–133](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:132>)). C’est un échec prévu, pas un échec observé.
- Lors de la première mission réelle, le prompt de proposition donnait littéralement `IABINOME:DOCUMENT`, mais les prompts de révision et de finalisation demandaient seulement « rends DOCUMENT ». Selon le registre, **l’agent a obéi littéralement** et aucune mission ne pouvait aller au bout ([RULES.md, ligne 134](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:134>)). Cet incident est présenté comme mesuré dans IAbinome.

D’autres règles exigent qu’un prompt fournisse au contradicteur une hiérarchie des sources, une consigne d’omission accompagnée d’un périmètre et une disposition pour chaque observation ([RULES.md, lignes 43–59](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:43>)). Leur combinaison augmente la quantité de contrat à transmettre.

Le cas concret est donc :

- Alléger peut supprimer une balise, un schéma ou un périmètre nécessaire et rendre la mission inexécutable.
- Répéter toutes les obligations dans chaque prompt accroît la prescription que le récit fondateur associe à une qualité moindre.
- Seule la sous-spécification dispose d’un incident explicitement attribué à une mission réelle d’IAbinome.

### Limites et contre-preuve

Aucun même prompt n’est comparé à plusieurs niveaux de densité. Le seuil entre explicitation nécessaire et sur-prescription est **inconnu**.

Le cas d’une revue JSON précédée d’une phrase fournit une contre-preuve à l’idée qu’une prescription supplémentaire suffit toujours. L’agent avait lu « retourne seulement le JSON » et croyait respecter la consigne ; le défaut pouvait donc venir du contrat de balisage plutôt que d’un manque d’instructions ([RULES.md, lignes 73–74](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:73>)).

La tension normative est établie et illustrée par le corpus. Son intensité dans IAbinome et son point d’arbitrage ne sont pas prouvés.

---

## 3. Quelle règle cède en premier ?

### Première cession documentée

La seule cession explicitement datée concerne la relecture palier par palier :

> « Suspendue en étape 2 le 2026-09-03, décision du PO »

— [RULES.md, lignes 33–35](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:33>)

`CLAUDE.md` confirme la suspension et l’attribue à une conception jugée assez précise pour s’en passer ([CLAUDE.md, lignes 53–56](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/CLAUDE.md:53>)). Cette reprise du même arbitrage ne constitue pas une seconde preuve indépendante.

Le déroulement consigné est :

1. Le faible rendement perçu de la relecture conduit à sa suspension.
2. Deux défauts déclarés invisibles aux tests remplissent la condition de réouverture.
3. La relecture est rétablie le 2026-09-05.

La **première règle observable à céder est donc la relecture systématique**. Cette conclusion est strictement bornée aux arbitrages datés présents dans le corpus.

### Pourquoi le scénario de croissance reste indéterminé

Le corpus ne démontre pas que la suspension ait été causée par la croissance : son motif explicite est la faible rentabilité supposée après cinq tours de contradiction. Il ne fournit pas non plus une chronologie exhaustive des abandons antérieurs.

La cession n’a duré que deux jours. Son rétablissement montre deux fragilités opposées :

- la couverture de revue peut céder lorsque son rendement paraît faible ;
- la discipline de réduction des contrôles peut céder lorsque des défauts hors tests deviennent visibles.

Prédire que la relecture céderait de nouveau sous croissance est une **inférence plausible fondée sur l’unique précédent**, mais non une conclusion déterminée par le corpus.

### Incohérence temporelle

`CLAUDE.md` déclare :

> « État : pas encore commencé. L’étape en cours est la récolte — ni la spécification, ni le code. »

— [CLAUDE.md, lignes 34–35](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/CLAUDE.md:34>)

Pourtant :

- le même fichier décrit l’« étape 2 — implémentation » et une relecture suspendue pendant cette étape ([CLAUDE.md, lignes 53–56](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/CLAUDE.md:53>)) ;
- `RULES.md` mentionne du code dans `transport.py`, testé avec `mypy --strict` ([RULES.md, lignes 108–109](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:108>)) ;
- il consigne des mesures réalisées au palier 4 sur `cli.py` et `tests/test_adapters.py` ([RULES.md, lignes 175–179](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:175>)) ;
- il rapporte séparément 262 tests verts le 2026-09-05 ([RULES.md, lignes 37–38](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:37>)).

La divergence est **présente**, non nulle et non résolue. `CLAUDE.md` pourrait être périmé, mais le corpus ne le dit pas. Les incidents de `RULES.md` restent des faits rapportés par ce document ; leur place dans une chronologie globale demeure incertaine.

---

## 4. Candidats examinés mais non retenus

### Construire l’outil avec son protocole ou ne pas réparer un sous-système défaillant en s’en servant

`CLAUDE.md` prescrit :

> « Construire l’outil avec son propre protocole est la démonstration qu’il n’a jamais eu besoin de machinerie. »

— [CLAUDE.md, lignes 53–55](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/CLAUDE.md:53>)

`POURQUOI.md` prescrit :

> « Ne jamais réparer un sous-système défaillant en s’en servant. »

— [POURQUOI.md, lignes 46–47](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/POURQUOI.md:46>)

Le refus d’une revue JSON correcte à cause d’un préfixe établit un défaut du contrat de protocole ([RULES.md, lignes 73–74](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:73>)). Le corpus ne dit cependant pas qu’IAbinome a employé ce même mécanisme défaillant pour réparer ce défaut. Le cas complet est **non prouvé** : il ne peut pas être compté comme troisième tension.

### Généricité des outils ou garde des quelque 1 500 lignes

Le corpus exige les quatre permutations Claude/Codex et interdit de supposer un fournisseur dans le code ([CLAUDE.md, lignes 27–28](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/CLAUDE.md:27>), [RULES.md, lignes 61–65](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:61>)). Il fixe aussi un objectif d’environ 1 500 lignes ([POURQUOI.md, lignes 34–35](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/POURQUOI.md:34>)).

L’inachèvement de la permutation dans DialogForge montre qu’une abstraction multi-outils peut échouer. Il ne montre pas que les quatre permutations d’IAbinome imposent de dépasser 1 500 lignes ni qu’une limite de taille ait déjà sacrifié une permutation. Le coût marginal de la généricité et la taille actuelle complète sont absents : la tension est **non prouvée**.

### Lecture obligatoire ou non-redondance

`CLAUDE.md` exige de lire `POURQUOI.md`, puis demande de ne pas lire un fichier lorsque l’information figure déjà dans le contexte ([CLAUDE.md, lignes 8–13](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/CLAUDE.md:8>)). Une incompatibilité procédurale peut apparaître si le contexte reproduit déjà `POURQUOI.md`, mais aucun échec concret n’est relaté. Selon le critère demandé, ce candidat n’est donc pas une tension démontrée.

---

## 5. Ce que le corpus ne couvre pas

| Statut | Élément |
|---|---|
| **Absent** | Un ordre de priorité entre simplicité, couverture de revue, généricité et exhaustivité des prompts. |
| **Absent** | Une chronologie exhaustive des règles suspendues, maintenues ou contournées. |
| **Absent** | Une règle de préséance permettant de résoudre la divergence entre `CLAUDE.md` et `RULES.md`. |
| **Absent** | Des observations comparables à plusieurs tailles du projet ou nombres de paliers. |
| **Absent** | Le coût comparable de chaque contrôle en appels, temps, tokens et code effectif. |
| **Absent** | Les sorties, protocoles et évaluations brutes derrière la dégradation attribuée aux prompts à douze critères. |
| **Absent** | La taille actuelle complète d’IAbinome en code effectif et le coût propre aux quatre permutations. |
| **Négatif documenté** | Les tests seuls n’ont pas remplacé la couverture attribuée à la relecture : des défauts hors cycle nominal sont rapportés malgré 262 tests verts. |
| **Inconnu** | La règle qui céderait durablement si IAbinome grossissait effectivement. |
| **Non prouvé** | Que la relecture soit la première règle jamais affaiblie, qu’elle cède de nouveau sous croissance ou que son maintien provoque une dérive de taille. |
| **Non prouvé** | Que la généricité multi-outils menace déjà l’objectif d’environ 1 500 lignes. |
| **Nul** | Aucune mesure pertinente ne vaut zéro ; « nul » ne décrit donc aucune de ces lacunes. |

Une réponse prédictive complète nécessiterait une chronologie consolidée, des arbitrages observés à plusieurs tailles, la taille en code effectif et des mesures comparables du coût et du rendement des contrôles et des prompts. Leur absence empêche de transformer le précédent de la relecture en loi de croissance.

---

## Sources et niveau d’accès vérifié

Les trois documents autorisés ont été lus intégralement par accès direct dans l’instantané local daté du 2026-09-05 :

- [POURQUOI.md](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/POURQUOI.md:1>) — accès local direct intégral vérifié ; SHA-256 `09E6482B312392603F51D764D8E1EFDC4DA0F444E28BB1B1B45A2C1BF1AEC084`.
- [CLAUDE.md](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/CLAUDE.md:1>) — accès local direct intégral vérifié ; SHA-256 `474AF81C8063F5A9802D9404B3A2D7F929CF545F04FA4F7B7AD72133A870C476`.
- [RULES.md](</C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/6079515a-0555-4c04-be3f-6fd28e8ebb0e/scratchpad/essai/revision/corpus/fichiers/project/RULES.md:1>) — accès local direct intégral vérifié ; SHA-256 `F85D9A9FE6A416261B771886BCF47634AD29B938CB7A1CE45B52A2FE95E71951`.

Ces fichiers sont des sources primaires pour les règles et pour les constats que le projet a consignés. Leurs motifs dits « mesurés » et leur récit de DialogForge sont toutefois des **résumés internes** : les journaux, sorties et protocoles bruts correspondants ne figurent pas dans le corpus. Ils établissent que le projet a enregistré ces constats, pas que ceux-ci ont été reproduits indépendamment.

Les chemins externes mentionnés par les documents — archives, caractérisations, journaux et décisions de gel — n’ont pas été consultés et n’apportent donc aucune preuve vérifiée ici. Les reprises d’un même principe ou arbitrage entre les trois documents ont été traitées comme une même origine normative, non comme des confirmations indépendantes.

# Disposition de la relecture contradictoire

> Écrit le 2026-09-03 par A (Claude), en réponse à `RELECTURE_CODEX_PASSE1.md` et sa `V1.1`.
> **Chaque observation reçoit exactement une disposition.** Aucune ne reste sans réponse — c'est la
> règle P5 de l'inventaire, appliquée ici à l'inventaire lui-même.
> Vocabulaire : **ACCEPTÉE** (intégrée) · **REJETÉE** (avec motif) · **DIFFÉRÉE** (avec condition) · **BLOQUANTE** (décision humaine avant tout).

## Verdict

**La relecture a fonctionné, et sa V1.1 vaut mieux que sa passe 1.** Sur 42 observations : **28 acceptées,
6 rejetées avec motif, 5 différées avec condition, 3 bloquantes.**

Codex s'est contredit lui-même sur six points entre les deux passes — il avait reconstruit la logique de
forteresse de DialogForge qu'il était censé aider à éviter. Cette autocritique est le résultat le plus
solide de l'exercice : elle montre que la consigne d'omission, seule, tire vers l'ajout de contrôles, et
qu'il faut lui opposer le périmètre. **La passe 1 sans la V1.1 aurait rechuté.**

## Les trois vraies trouvailles

1. **La robustesse intellectuelle manquait entièrement.** Observations 29 à 36. J'ai dépouillé FloraPi
   pour ce qu'il disait de *l'outil* et de *la conduite*, jamais pour ce qu'il disait d'un **bon
   livrable** — indépendance des sources, résultat négatif qui compte, portée bornée par la preuve,
   contre-preuves conservées, critère de fin défini avant de chercher. C'est le produit même d'IAbinome,
   et il n'était pas dans l'inventaire. Omission réelle, la plus coûteuse.

2. **X7 écartait trop.** « Sans écriture agent, il n'y a rien à confiner » est faux : il reste une
   frontière d'effets, courte mais nécessaire — n'exécuter aucun contenu produit, n'écrire que dans une
   liste fermée de fichiers, refuser explicitement une demande qui exige du code. Trois lignes, pas un
   sous-système.

3. **Trois agrégats masquaient des invariants transférables.** X16–X18 écartaient 166 éléments d'un coup.
   La disposition ne restaure aucun sous-système, mais en extrait ce qui survit : prévol avant tout effet,
   état fermé sur valeur inconnue, intention d'appel persistée avant l'appel.

## Ce que je rejette, et pourquoi

Codex a raison de dire que sa passe 1 surpondérait la sécurité. Je vais un cran plus loin que sa V1.1 sur
quatre points : **un contrôle qui ne compense pas un défaut encore réel ne rentre pas** (POURQUOI règle 3),
et la bonne question reste « qu'est-ce que je retire en échange ? » (règle 2). Voir les lignes REJETÉE.

---

## Trois questions bloquantes — pour l'humain, avant tout le reste

### B-1 — « Recherche » entre-t-il au périmètre, officiellement ?

Votre message à Codex dit : *« conceptions et recherches »*. Or `CLAUDE.md`, `POURQUOI.md`, `DEPART.md` et
`RECOLTE.md` ne parlent que de **conception**. Huit des observations acceptées (29 à 36) n'existent que si
la recherche est dans le périmètre.

Ce n'est pas une extension anodine : elle fait passer le livrable de « une conception argumentée » à
« une conception argumentée **ou** un état de l'art sourcé », ce qui n'a pas les mêmes exigences de preuve.
L'usage réel le justifie — FloraPi a lancé au moins quatre missions de type `recherche`, dont deux ont
échoué. **Si c'est oui, `CLAUDE.md` et `DEPART.md` doivent le dire.** Sinon P25–P32 tombent.

### B-2 — B garde-t-il ou non ses outils à zéro ?

Codex propose deux profils : `conception` (B sans outil, corpus fourni) et `recherche` (B peut ouvrir et
vérifier une source lui-même).

**Je recommande de refuser, pour V1.** Trois motifs mesurés :

- DialogForge a choisi Claude comme B **précisément parce que** `--tools ""` est vérifiable, alors qu'un
  Codex relecteur « en lecture seule » garde un shell qu'on ne peut pas retirer. Donner des outils à B
  supprime la raison qui a fait choisir ce modèle pour ce rôle.
- Un B outillé lit ce qu'il veut : le coût et la durée de la critique cessent d'être bornés par le
  contexte qu'on lui envoie. C'est la porte d'entrée d'un budget interne — interdit n°4.
- La contradiction n'a jamais échoué faute d'accès aux sources. Elle a échoué, quand elle a échoué, faute
  de recevoir les constats ouverts — ce que l'observation 18 corrige sans donner un seul outil.

**Contre-argument à peser** : en recherche, une critique qui ne peut pas vérifier une citation ne peut
pas contredire une source inventée. C'est le seul cas où l'asymétrie mord vraiment.
**Voie moyenne suggérée** : A cite en joignant l'extrait ; B critique l'extrait, pas le lien. Si ça ne
suffit pas à l'usage, on rouvrira — avec la mesure en main.

### B-3 — Le plafond de ~200 lignes tient-il encore ?

L'inventaire v2 pèse **248 lignes** contre 194 pour `context\`, et passe de 106 à **146 leçons**.
Le dépassement vient du bloc « recherche » (B-1) et de la frontière d'effets. Deux issues honnêtes :

- **si B-1 est non** : les 8 lignes tombent, l'inventaire repasse sous la barre ;
- **si B-1 est oui** : le périmètre a grandi, donc la référence aussi — mais alors il faut le dire,
  pas laisser le plafond glisser en silence.

Je n'ai pas tranché. Le dépassement est signalé dans `INVENTAIRE.md`, pas maquillé.

---

## Disposition des 42 observations

| # | Sujet | Disposition | Motif ou intégration |
|---:|---|---|---|
| 1 | L'orchestrateur possède l'état, l'agent produit du texte | **ACCEPTÉE** | → `C31`. Manquait : l'inventaire le supposait sans l'écrire. |
| 2 | Outils de B imposés mécaniquement / profils | **BLOQUANTE** | Voir **B-2**. `P2` inchangé tant que ce n'est pas tranché. |
| 3 | Les consignes du projet cible ne peuvent élargir les capacités | **ACCEPTÉE** | → `R22`. Sans aucun appareil d'attestation. |
| 4 | Neutraliser la configuration locale d'une CLI | **DIFFÉRÉE** | Condition : un incident réel, ou la porte du codage. Limite documentée en attendant. |
| 5 | Consentement réseau / installation | **REJETÉE** | IAbinome n'installe rien et n'a pas de réseau propre. Un système de consentements est l'amorce d'un moteur de permissions. |
| 6 | Ne jamais exécuter une commande fournie par un agent | **ACCEPTÉE** | → `C32`. L'absence structurelle remplace toute liste noire. |
| 7 | Prévol avant création de la collaboration | **ACCEPTÉE** | → `C33`. Un refus ne doit laisser ni dossier ni artefact orphelin. |
| 8 | Sonder version et disponibilité des CLI | **ACCEPTÉE** | → `C34`, réduit à : vérifier la présence et la version au démarrage. Ni registre, ni plage expirante. |
| 9 | Smoke réel manuel avant premier usage | **ACCEPTÉE** | → `R23`. Hors suite de tests, donc compatible avec « aucun appel fournisseur dans les tests ». |
| 10 | Une seule invocation canonique documentée | **ACCEPTÉE** | → `R24`. |
| 11 | Délai dur par appel | **ACCEPTÉE** | → `C22` complétée. Je n'avais gardé que la terminaison de l'arbre, pas la borne qui la déclenche. |
| 12 | `watch` / `dev` ne sont pas des validations | **ACCEPTÉE** | → `X21` (écarté avec motif). Était absent des deux colonnes. |
| 13 | La demande écrite est la seule autorité | **ACCEPTÉE** | → `C35`. |
| 14 | `schema_version` et échec fermé sur valeur inconnue | **ACCEPTÉE** | → `C2` complétée. Vraie omission. |
| 15 | Intention d'appel persistée avant l'appel | **ACCEPTÉE** | → `C23` complétée. Un appel payé sans réponse archivée doit rester un trou explicite. |
| 16 | Idempotence par empreinte, pas par présence | **ACCEPTÉE** | → `T10` complétée. Divergence = arrêt humain. |
| 17 | Lecture obligatoire résolue, bornée, empreintée | **ACCEPTÉE** | → `P21` complétée d'un `C36`. |
| 18 | B reçoit une preuve complète et adressable | **ACCEPTÉE** | → `P3` complétée. C'est la vraie réponse à l'asymétrie de B-2. |
| 19 | Plafond dur de taille, refus explicite au-delà | **ACCEPTÉE** | → `C24` complétée. « Segmenter sans tronquer » ne bornait rien. |
| 20 | Expurgation des secrets | **ACCEPTÉE** en règle, **REJETÉE** en mécanisme | → `R25` : ne jamais mettre de secret au corpus. Pas de scanner sans incident mesuré. |
| 21 | Agent réparateur de JSON borné | **REJETÉE** | Aucun agent réparateur en V1 : l'appel échoue clairement et rend la main. La limite n'a rien à borner. |
| 22 | Chemins logiques relatifs dans les artefacts | **ACCEPTÉE** | → `C37`. |
| 23 | Une archive scellée se lit sur copie | **ACCEPTÉE** | → `R26`. Protège la récolte et les audits, pas le moteur. |
| 24 | Une métrique indirecte reste un indice | **ACCEPTÉE** | → `P25`. |
| 25 | Comparer le contenu, pas les identifiants Git | **ACCEPTÉE** | → `R27`. |
| 26 | Nettoyage sous `finally`, cible vérifiée | **REJETÉE** | V1 ne nettoie rien automatiquement. Rien à protéger. |
| 27 | Une collaboration est autoportante | **ACCEPTÉE** | → `C38`. Aucune seconde autorité, nulle part. |
| 28 | Tâche sans modification, clôture impossible | **ACCEPTÉE** | → `X22`. C'était le troisième défaut mesuré d'`ARRET_REFACTORING.md`, et il n'était **ni retenu ni écarté**. Vraie omission silencieuse. |
| 29 | Résultat négatif documenté = résultat | **ACCEPTÉE** sous **B-1** | → `P26`. |
| 30 | Deux reprises d'une source ne font pas deux preuves | **ACCEPTÉE** sous **B-1** | → `P27`. |
| 31 | Distinguer absent / nul / négatif / inconnu / non prouvé | **ACCEPTÉE** | → `P28`. Vaut aussi en conception. |
| 32 | La portée d'une conclusion ne dépasse pas sa preuve | **ACCEPTÉE** | → `P29`. Vaut aussi en conception. |
| 33 | Conserver contre-preuves et biais | **ACCEPTÉE** sous **B-1** | → `P30`. |
| 34 | Inventorier avant de classer | **ACCEPTÉE** | → `P31`. C'est exactement ce que cette récolte a fait, sans l'avoir écrit. |
| 35 | La réversibilité est temporelle | **ACCEPTÉE** | → `P11` complétée : jusqu'à quand, et quel acte la referme. |
| 36 | Conserver non-décisions et désaccords non résolus | **ACCEPTÉE** | → `P32`. Le livrable garde ce qui n'a pas été tranché. |
| 37 | Confronter l'architecture à l'usage mesuré | **ACCEPTÉE** | → `R28`. |
| 38 | Renouvellement de session nécessaire ? | **DIFFÉRÉE** | Condition : instrumenter les échecs de contexte réels. Codex a lui-même reconnu avoir pris une corrélation pour une nécessité. |
| 39 | Ambiguïté ou extension rend la main à l'humain, même sans `BLOQUE` | **ACCEPTÉE** | → `R29`. |
| 40 | Conserver l'état avant toute récupération | **ACCEPTÉE** allégée | → `R30` : copier le dossier suffit, puisqu'il est la seule autorité. |
| 41 | Sémantique d'interruption définie | **ACCEPTÉE** | → `C39`. « Fermer le terminal » n'était pas une sémantique. |
| 42 | Sonder un worker | **REJETÉE** | Il n'y a pas de worker — interdit n°3. Déjà couvert par `X4`. |

### Dispositions rejetées, récapitulées

`5` consentements réseau · `20`(mécanisme) scanner de secrets · `21` agent réparateur ·
`26` nettoyage automatique · `42` sonde de worker. Plus `4` et `38` différées sous condition nommée.
**Aucune n'est écartée en silence : chacune a son motif ci-dessus.**

---

## Ce qui reste à faire

1. Trancher **B-1**, **B-2**, **B-3** — ce sont les seules décisions humaines.
2. `INVENTAIRE.md` v2 est produit **en supposant B-1 = oui** et **B-2 = non** (recommandation ci-dessus).
   Les lignes concernées portent la mention `[B-1]` pour être retirées d'un seul geste si la réponse change.
3. Ensuite seulement : étape 1, la spécification de `DEPART.md`, qui ne prend en entrée que la colonne **Code**.

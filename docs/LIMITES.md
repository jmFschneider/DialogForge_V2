# Limites effectives

Ce que l'outil garantit, ce qu'il demande sans l'avoir mesuré, et ce qu'il n'obtient pas. Cette page
distingue trois niveaux de preuve, parce qu'écrire « garanti » là où l'on a seulement « demandé » serait
la promesse que ce projet s'interdit.

> **État de cette page : commit `dda7a54` (2026-09-20).** Le petit protocole d'essai fournisseur du
> lot 3.1 (`reference/PROTOCOLE_FOURNISSEUR_3_1.md`) **n'a pas encore été lancé**. Tant qu'il ne l'est
> pas, l'**effet** des protections demandées aux outils (section 2) reste non mesuré. La page sera mise
> à jour point par point, à mesure que ces vérifications sont faites. Le détail technique est dans
> [`reference/FRONTIERE_ROLES.md`](../reference/FRONTIERE_ROLES.md).

## 1. Garanti par le programme

Ces séparations sont faites par le programme lui-même et **prouvées par des tests, sans aucun appel
fournisseur** :

- **Les agents ne voient pas la collaboration.** A et B tournent dans un dossier jetable, hors de la
  collaboration, qui contient une **copie** du corpus et disparaît après l'appel. Ils ne voient ni
  `appels/`, ni le journal de l'autre, ni les anciennes versions de la demande. Écrire dans cette
  copie n'atteint jamais l'original.
- **Chaque outil ne reçoit que ses variables.** Rien de Claude chez Codex, rien de Codex chez Claude ;
  `PLAN_ID`, `PWF_*` et les identifiants de session de l'outil qui vous a lancé sont retirés aux deux.
  Le même filtre vaut pour A et B.
- **Un rôle sans séparation n'est pas lancé.** Un adaptateur qui ne déclare pas la lecture seule et la
  session fraîche est refusé avant tout appel, sans rien modifier.
- **Un corpus modifié pendant un appel est constaté.** Contrôle complet après l'appel, avant toute lecture
  de la réponse : incident `SOURCES_MODIFIED`, réponse non retenue.
- **B ne reçoit que le nécessaire.** Sa consigne porte la demande, la version examinée et les
  objections ouvertes avec les réponses de A — ni chemin d'appel, ni journal, ni consigne de A.
- **Le livrable est ce que B a examiné**, promu octet pour octet ; jamais une réécriture postérieure.
- **Une décision porte sur une version précise.** Si le livrable change après elle, `status` le dit.
- **Rien n'est jamais relancé tout seul.** Une relance exige un motif écrit par vous ; une réponse déjà
  payée se relit en local, sans nouvel appel.
- **Un incident dit s'il a pu être payé** (« non », « peut-être », « inconnu », « oui »), jamais un
  montant ni une heure de reprise.

## 2. Demandé aux outils : accepté ou non éprouvé, effet jamais mesuré

Le programme **écrit** ces demandes dans la ligne de commande de chaque outil, et un test le montre.
`intention.json` garde ce qui a été demandé : c'est une trace de la demande, pas une preuve de ce que
l'outil a fait.

- **Les options d'isolation** (lecture seule, session fraîche, réglages ignorés) ont été **acceptées**
  par les deux outils lors des deux cycles réels du 2026-09-19 : aucun appel n'a échoué, l'authentification
  a été conservée et le modèle demandé appliqué. Cela prouve que l'outil les **connaît** ; cela ne prouve
  pas qu'il les **applique**. Aucun essai n'a tenté de lui faire violer une restriction.
- **Les demandes ajoutées ensuite** — web fermé ou ouvert, niveaux d'effort — n'ont **jamais été envoyées
  à un outil réel**.

| Ce que le programme demande | Claude | Codex |
|---|---|---|
| Lecture seule | `--restricted`, `--tools "Read,Grep,Glob"` | `--sandbox read-only` |
| Session fraîche | `--no-session-persistence` | `--ephemeral` |
| Ignorer vos réglages et hooks | `--restricted` | `--ignore-user-config`, `--ignore-rules` |
| Web fermé | aucun outil web | `-c web_search=disabled` |
| Web ouvert | `WebSearch`, `WebFetch` + `--allowedTools` | `-c web_search=live` |
| Effort de raisonnement | `--effort` | `-c model_reasoning_effort=…` |

Les versions dont l'aide a été lue pour écrire ces demandes : Claude 2.1.278, Codex 0.155.0. Ce qui
reste à vérifier au lot 3.1, en clair :

- que `web_search=disabled` **coupe réellement** la recherche chez Codex, et que `live` l'active ;
- que `WebSearch` / `WebFetch` fonctionnent chez Claude sous `--restricted` avec `--allowedTools`, et
  refusent sans ;
- que tous les niveaux d'effort déclarés sont acceptés par les outils installés ;
- que chaque outil, privé des variables de l'autre, **garde son authentification** — les cycles du
  2026-09-19 tournaient dans un terminal sans variable de l'autre outil, donc le filtre n'avait rien à
  retirer ;
- qu'un reviewer Claude en `--restricted` ne lit bien que `corpus/fichiers/`, y compris par un chemin
  absolu ;
- que vos hooks et réglages personnels sont réellement sans effet avec ces options ;
- l'accès aux sources et l'incident `SOURCES_MODIFIED` avec un vrai corpus : aucun n'y figurait.

Une option **inconnue** de l'outil fait échouer l'appel (`CLI_FAILED`), donc se voit. Une option
**acceptée mais sans effet** ne se voit pas d'ici.

## 3. Non obtenu

- **Aucun confinement réseau.** Web ouvert, ce que contient le prompt peut sortir de la machine par une
  recherche ou une lecture de page. Web fermé, rien ne le prouve encore (voir ci-dessus), et **la demande
  et le corpus partent de toute façon chez les deux fournisseurs** : n'y mettez rien que vous ne leur
  confieriez pas.
- **Aucun confinement du système d'exploitation.** Un agent qui écrit ou lit un **chemin absolu** n'est
  arrêté que par sa propre CLI. Le programme ne peut que **constater** après coup une modification du
  corpus ; il ne l'empêche pas. Ce contrôle ne couvre que le corpus : `demande.md` et `etat.json` sont
  protégés par leurs empreintes à la reprise, pas pendant l'appel.
- **Le dossier jetable n'est pas isolé du reste du disque** : il est sous le dossier temporaire de
  l'utilisateur, ne contient rien de la collaboration, mais reste lisible par un chemin absolu.
- **Le partage des secrets suit des préfixes de noms**, pas une connaissance de vos secrets : les
  variables en `CLAUDE*` / `ANTHROPIC_*` sont à Claude, celles en `CODEX_*` / `OPENAI_*` à Codex. Une clé
  d'un autre nom (`AWS_*`, un jeton générique) passe aux deux.
- **La mémoire propre au fournisseur** (préférences de compte, mémoire persistante hors session) n'est
  pas maîtrisée. « Session fraîche » veut dire : le programme ne reprend aucune session et n'en laisse
  aucune.

## 4. Déjà observé en réel

- **Deux cycles complets** ont tourné sans incident le 2026-09-19 : A = Codex / B = Claude, puis
  l'inverse, sur une demande de conception, quatre appels chacun, B acceptant la version examinée.
  Ce sont **les deux seules permutations mesurées en réel**, délibérément ; les quatre sont couvertes de
  bout en bout par l'agent `fake`. `A == B` reste permis (c'est la seule sortie quand un fournisseur est
  en quota) mais n'est pas un usage éprouvé.
- **Durée d'un appel** : un appel de A a pris environ 5 minutes (Codex, 305 s) et 7 minutes (Claude,
  402 s). Un ordre de grandeur, pas une garantie : le délai dur par défaut est de 30 minutes.
- **Le prompt de B**, relu sur ces essais, contient la demande et la version examinée et ne mentionne
  aucun fichier interne de la collaboration.
- **Sur quota, les deux outils rendent un code de retour non nul** ; ils ne l'écrivent pas au même
  endroit (Claude sur `stdout`, Codex sur `stderr`). Dans les deux cas : `CLI_FAILED`, `INTERRUPTED`,
  relançable.
- **Avant le réglage `web_access`**, Codex a fait des recherches web (six par appel de A) sans que rien
  ne les demande : c'est pourquoi le web est maintenant fermé par défaut et dit explicitement.
- **Sous les options d'isolation**, Codex a tourné à l'effort `none` et non à celui de votre
  `config.toml`. Claude ignore un effort `minimal` avec un avertissement au lieu d'échouer.
- Le profil **`context-only`** n'a été exercé qu'en tests, pas en mission réelle.

## 5. Limites de périmètre

Ce ne sont pas des défauts : c'est le périmètre, et il est tenu volontairement.

- **Il n'exécute rien.** Le livrable est un document, que vous appliquez ensuite à la main.
- **Pas de base de données, pas de service, pas de tâche planifiée.** Des fichiers sur disque.
- **Pas de reprise après fermeture du terminal sans vous.** Rien ne repart seul ; une reprise se lance
  par une commande.
- **Aucun budget ni quota interne.** Les plafonds de votre fournisseur suffisent ; l'outil ne compte pas
  vos jetons, et un incident ne dit jamais combien un appel a coûté.
- **Pas d'interface graphique.**
- **Pas de recherche externe conduite par l'outil.** *Le programme* n'en fait aucune ; *les agents*
  gardent les capacités de leur propre outil (voir `web_access` et `--reviewer-access`).
- **Une seule exécution à la fois par collaboration**, sous verrou : un second `run` sur la même
  collaboration est refusé tant que le premier tourne, et un verrou illisible n'est jamais effacé
  tout seul.

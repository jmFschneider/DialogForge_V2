# Limites effectives

Ce que l'outil garantit, ce qu'il demande sans l'avoir mesuré, et ce qu'il n'obtient pas. Cette page
distingue trois niveaux de preuve, parce qu'écrire « garanti » là où l'on a seulement « demandé » serait
la promesse que ce projet s'interdit.

> **État de cette page : mesures réelles du 2026-09-20 au 2026-09-22**, avec Claude 2.1.278 et
> Codex 0.155.0. **Un essai par valeur** : ce sont des faits, pas des statistiques. Comment ces
> mesures ont été obtenues, et ce qu'elles ne couvrent pas :
> [`reference/FRONTIERE_ROLES.md`](../reference/FRONTIERE_ROLES.md) et
> `reference/PROTOCOLE_FOURNISSEUR_3_1.md`.

## 1. Garanti par le programme

Ces séparations sont faites par le programme lui-même et **prouvées par des tests, sans aucun appel
fournisseur** :

- **Le dossier de travail ne contient pas la collaboration.** A et B tournent dans un dossier jetable, hors de la
  collaboration, qui contient une **copie** du corpus et disparaît après l'appel. On n'y copie ni
  `appels/`, ni le journal de l'autre, ni les anciennes versions de la demande ; cela n'empêche pas
  A ou B d'y accéder par un chemin absolu (voir §3). Écrire dans cette copie n'atteint jamais
  l'original.
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

## 2. Demandé aux outils : ce que l'essai réel a montré

Le programme **écrit** ces demandes dans la ligne de commande de chaque outil, et un test le montre.
`intention.json` garde ce qui a été demandé : c'est une trace de la demande, pas une preuve de ce que
l'outil a fait. Le protocole du 2026-09-20 a mesuré l'effet de plusieurs d'entre elles :

| Ce que le programme demande | Claude | Codex | Mesuré |
|---|---|---|---|
| Web fermé | aucun outil web | `-c web_search=disabled` | ✅ Codex : 0 recherche (contre 4 lignes `web search:` en ouvert, même prompt). Claude : aucun outil web annoncé, aucun appel |
| Web ouvert | `WebSearch`, `WebFetch` + `--allowedTools` | `-c web_search=live` | ✅ Codex : recherches faites, source citée. Claude : un appel `WebSearch`, résultats réels, aucun refus de permission |
| Effort de raisonnement | `--effort` | `-c model_reasoning_effort=…` | ✅ Codex : `medium` appliqué (`none` sans la clé). ✅ Claude : accepté sans avertissement — **son effet n'est pas observable d'ici** |
| Séparation des secrets | rien de Codex | rien de Claude | ✅ Chaque outil garde son authentification sans les variables de l'autre. Ce qui est vérifié : ce que le programme **retire** (`intention.json`), pas ce que l'outil voit |
| Lire le corpus | `--restricted`, `--tools "Read,Grep,Glob"` | `--sandbox read-only`, backend Windows `elevated` explicite | ✅ Claude lit le corpus. ✅ Codex : fichier témoin le 2026-09-21, puis **un vrai corpus dans un cycle A/B complet le 22** — `Get-Content` réussi en 917 ms sur `corpus/fichiers/…`, dans le dossier jetable du produit, contenu exact retourné |
| Refuser un chemin hors du dossier | `--restricted` | `--sandbox read-only` | ✅ Claude refuse : « `--restricted` confines the file tools to the working directory ». Codex : **aucune garantie de confinement en lecture** |
| Session fraîche, réglages ignorés | `--no-session-persistence`, `--restricted` | `--ephemeral`, `--ignore-user-config`, `--ignore-rules` | Acceptées par les deux outils en réel (2026-09-19). **Effet non mesuré** |
| Session de l'agent de cadrage F, reprise à chaque tour | `--output-format json`, puis `--resume <id>` | `--json`, puis `exec resume … -c sandbox_mode=read-only <id>` | ✅ 2026-09-25, hors du produit : même identifiant, contexte rappelé, aucune écriture en reprise. Chez Codex, une tentative d'écriture a été refusée par le bac à sable, et l'outil l'a journalisée. **Pas encore de cadrage complet par le produit** |

**Sous Windows, Codex exige le backend natif `elevated`** : l'adaptateur le sélectionne explicitement,
sans retirer les options d'isolation, et **ce backend doit être déjà installé et utilisable — le produit
ne l'installe pas.** C'est la correction d'un défaut de lecture (`blocked by policy`) découvert le
2026-09-20 : qualifiée le 21 sur un fichier témoin (lecture réussie, écriture refusée, empreintes
inchangées), puis confirmée le 22 sur un vrai corpus dans un cycle A/B complet. Deux scénarios sur cet
hôte : ce n'est ni la preuve d'une cause unique des anciens rejets, ni un confinement en lecture.

Ce qui reste **non mesuré** :

- que vos hooks et réglages personnels sont sans effet avec ces options ;
- le confinement général de Codex en lecture : il n'est pas promis, conformément au recentrage approuvé ;
- l'incident `SOURCES_MODIFIED` avec un vrai corpus modifié pendant un appel ;
- le même argv appliqué à **B en consultation** sous ce backend : aucun essai réel de B.

Une option **inconnue** de l'outil fait échouer l'appel (`CLI_FAILED`), donc se voit. Une option
**acceptée mais sans effet** ne se voit pas d'ici.

## 3. Non obtenu

- **Aucun confinement réseau.** Web ouvert, ce que contient le prompt peut sortir de la machine par une
  recherche ou une lecture de page. Web fermé, la coupure a été observée chez les deux outils (un essai
  chacun, section 2), mais **la demande et le corpus partent de toute façon chez les deux fournisseurs** :
  n'y mettez rien que vous ne leur confieriez pas.
- **Aucun confinement du système d'exploitation.** Un agent qui écrit ou lit un **chemin absolu** n'est
  arrêté que par sa propre CLI : mesuré chez Claude (ses outils fichiers refusent un chemin hors du dossier
  de travail), **non mesuré chez Codex**. Le programme ne peut que **constater** après coup une modification
  du corpus ; il ne l'empêche pas. Ce contrôle ne couvre que le corpus : `demande.md` et `etat.json` sont
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
- **Durée d'un appel** : de **1 à 7 minutes** sur les mesures disponibles. Les plus longues datent du
  2026-09-19 (A : 305 s côté Codex, 402 s côté Claude) ; au 2026-09-22, les appels des missions réelles
  ont duré de 55 s à 153 s, soit environ **6 minutes pour un cycle complet de quatre appels**. Un ordre
  de grandeur, pas une garantie : le délai dur par défaut est de 30 minutes.
- **Le prompt de B**, relu sur ces essais, contient la demande et la version examinée et ne mentionne
  aucun fichier interne de la collaboration.
- **Sur quota, les deux outils rendent un code de retour non nul** ; ils ne l'écrivent pas au même
  endroit (Claude sur `stdout`, Codex sur `stderr`). Dans les deux cas : `CLI_FAILED`, `INTERRUPTED`,
  relançable.
- **Avant le réglage `web_access`**, Codex a fait des recherches web (six par appel de A) sans que rien
  ne les demande : c'est pourquoi le web est maintenant fermé par défaut et dit explicitement.
- **Sous les options d'isolation**, Codex a tourné à l'effort `none` et non à celui de votre
  `config.toml` : posez `effort_a` / `effort_b` si vous voulez une valeur précise. Un effort qu'un
  outil ne connaît pas — `minimal` chez Claude, par exemple — est désormais **refusé avant tout
  appel** ; c'est ce que la mesure de 2026-09-19 a motivé, Claude se contentant alors d'un
  avertissement.
- Le profil **`context-only`** n'a été exercé qu'en tests, pas en mission réelle.
- **Trois missions représentatives du lot 3.2** (2026-09-22, A = Codex / B = Claude) : conception
  courte avec sources web, guide de décision avec une correction ciblée puis un complément de
  recherche demandé **après acceptation** (le moteur ne le referme pas — voulu par la conception),
  révision d'un document existant à partir d'un corpus local. 16 appels au total, toutes `ACCEPTE`,
  aucun défaut reproductible de perte de réponse, de version ou de reprise. Détail dans le plan PWF.

## 5. Limites de périmètre

Ce ne sont pas des défauts : c'est le périmètre, et il est tenu volontairement.

- **Il n'exécute rien.** Le livrable est un document, que vous appliquez ensuite à la main.
- **Pas de base de données, pas de service, pas de tâche planifiée.** Des fichiers sur disque.
- **Pas de reprise après fermeture du terminal sans vous.** Rien ne repart seul ; une reprise se lance
  par une commande.
- **Aucun budget ni quota interne.** Les plafonds de votre fournisseur suffisent ; l'outil ne compte pas
  vos jetons, et un incident ne dit jamais combien un appel a coûté.
- **Une fenêtre locale, rien de plus.** `dialogforge gui` ouvre une fenêtre Tkinter sur les mêmes
  dossiers que la CLI : une collaboration et une exécution à la fois, sans service, worker ni
  processus détaché.
- **Pas de recherche externe conduite par l'outil.** *Le programme* n'en fait aucune ; *les agents*
  gardent les capacités de leur propre outil (voir `web_access` et `--reviewer-access`).
- **Une seule exécution à la fois par collaboration**, sous verrou : un second `run` sur la même
  collaboration est refusé tant que le premier tourne, et un verrou illisible n'est jamais effacé
  tout seul.

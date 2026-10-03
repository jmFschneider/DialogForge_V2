# RULES.md — Leçons apprises IAbinome

> Une règle par constat, avec son motif. **Sans doublon.**
> Les règles fondatrices, elles, sont dans `POURQUOI.md` et n'ont pas à être répétées ici.
> Dernière mise à jour : 2026-10-02 (preuve d'exécution d'un test de confinement)

## Index

- [Périmètre](#périmètre)
- [Travail avec les agents](#travail-avec-les-agents)
- [Git](#git)
- [Outils et commandes](#outils-et-commandes)
- [Tests](#tests)
- [Conduite de projet](#conduite-de-projet)

---

## Périmètre

**Toute demande qui commence par « et si on ajoutait un petit contrôle pour… » est opposée au tableau des cinq interdits de `CLAUDE.md` avant d'être implémentée.**
*Motif : chaque contrôle de DialogForge était justifié isolément ; aucun n'a été mis en regard du total, qui a atteint 87 382 lignes.*

**Un réglage n'est pas un état : le fichier de configuration fournit des défauts au `new`, et rien d'autre.** Une fois la collaboration créée, `configuration.json` est la seule vérité.
*Motif : la tentation inverse est immédiate — faire relire le fichier à chaque `run` pour « pouvoir ajuster en cours de route ». Ce serait exactement l'état caché que `etat.json` existe pour rendre visible : une édition globale déplacerait en silence un cycle en cours, et la trace du dossier d'appel ne dirait plus pourquoi. Corollaire tenu : **aucun chemin ne s'y règle**, sinon la collaboration cesse d'être reproductible d'une machine à l'autre.*

**Un réglage inconnu est refusé, jamais ignoré.** Et la commande annonce quel fichier a servi et ce qu'elle y a pris.
*Motif : un réglage silencieusement perdu est pire qu'un réglage absent — on croit l'avoir posé, et on cherche la cause ailleurs. C'est `C2b` appliqué à l'entrée humaine ; et un réglage qui agit sans se montrer est la moitié d'un état caché.*

**Rien n'est livré que B n'ait examiné : le livrable est la version relue, promue telle quelle.**
*Motif (1.3, confirmé sur pièce dans le moteur hérité) : un 5e appel `FINAL_A` réécrivait librement le document après la dernière revue de B. Le livrable n'était plus ce qui avait été critiqué, et l'appel coûtait un tour de A pour un texte que personne ne relisait. Supprimé, remplacé par la promotion et un bilan écrit sans modèle.*

**Une décision humaine porte sur une version précise, et l'acceptation n'est jamais un statut du moteur.**
*Motif (1.4) : « terminé » et « accepté » ne sont pas le même fait. Le cycle s'arrête en `AWAITING_APPROVAL` ; l'acceptation est une entrée datée de `decisions.json` avec les empreintes du livrable, de la revue et de la demande. Une décision dont l'empreinte ne correspond plus à ce qui est sur le disque le dit, au lieu de laisser croire que la nouvelle version est acceptée.*

**Un incident dit s'il est payé — « non », « peut-être », « inconnu » ou « oui » — jamais un montant ni une heure de reprise.**
*Motif (2.1) : un code de retour non nul ne distingue pas un quota d'une erreur de configuration (mesuré des deux côtés, règle sur les codes de retour). Le programme cite donc le message de l'outil **tel quel** et n'en déduit rien : « 14h » n'y apparaît que dans la citation. Prétendre connaître un coût ou une reprise qu'aucune donnée ne porte est le défaut inverse de l'appel rejoué à l'aveugle.*

**Relire une réponse déjà payée ne coûte pas un appel.**
*Motif (2.1) : sur `CONTRACT_ERROR` et `DECODE_FAILED` la seule sortie était `--retry-call`, un nouvel appel payant, alors que la réponse brute était sur disque — et que le code disait lui-même « aucun appel n'est nécessaire pour retenter l'extraction ». `--reprocess` relit localement, trace l'opération et laisse les données brutes intactes ; s'il échoue encore, l'état reste `ERROR` : jamais un avis favorable par défaut.*

**Le type d'une mission dit ce qu'on attend du livrable, pas si l'on a un corpus.** Recherche : un dossier sourcé, avec au moins une source (web ou corpus local). Conception : un plan tiré d'un dossier fourni (corpus exigé). Les sources se contrôlent à la création. *(PO, 2026-10-01, `conception/TYPES_DE_MISSION.md`.)*
*Motif mesuré le 2026-10-01 : `recherche` exigeait un corpus, si bien que les 17 collaborations réelles étaient toutes de type `conception`, dont 6 recherches web sans corpus. Le type servait à déclarer un corpus, et la consigne de recherche ne servait jamais.*

**Le livrable de la boucle est un document, jamais une exécution.**
*Motif : l'exécution autonome n'a jamais mené une implémentation au bout — 1 tâche sur 7 sur FloraPi, 1 sur 10 sur DialogForge.*

**La GUI V1 est une surface de plus sur le même moteur, jamais un second moteur.** Levée de l'interdit « Pas de GUI » par le PO le 2026-09-23, **limitée à `conception/GUI_V1.md`** : Tkinter/ttk de la bibliothèque standard, une fenêtre, une collaboration, une exécution, aucun worker ni processus détaché (§13). Plafonds : 1 200 lignes logiques de production pour la GUI et sa façade, +900 lignes nettes dans `src/` ; un dépassement se re-décide, il ne se constate pas. Les règles d'action (quelle commande est permise, laquelle peut payer) vivent dans `decisions.allowed_actions`, que la CLI et la GUI rendent chacune à sa façon — jamais une table propre à Tkinter.
*Amendement du 2026-09-23 (PO), après les lots 3 et 4 : mesuré avec un compteur cohérent d'un lot à l'autre, la croissance nette de `src/` atteignait +1 046 lignes, 146 au-delà du plafond de +900. **Le plafond de croissance nette dans `src/` est porté à 2 500 lignes** — jugé trop bas à l'origine, plutôt que de réduire le lot 4 déjà livré et testé. Le plafond de 1 200 lignes logiques (façade + `gui/`) n'est pas changé : il n'a pas été approché (~1 000 lignes). Détail dans `conception/GUI_V1.md` §11 et `task_plan.md`.*
*Motif : l'interdit tenait parce qu'une interface qui possède l'exécution tend à reconstruire l'autonomie — la conception retenue écarte explicitement « les mécanismes d'autonomie de l'ancienne GUI » (§11, §17). La levée ne vaut que si la GUI ne décide rien que la CLI ne décide déjà.*
*Mesuré après le lot 5 (2026-09-23) : le plafond de 1 200 lignes logiques (façade + `gui/`) est à **1 195** — non dépassé, mais sans marge pour un ajout futur à cette surface sans re-décision. Pas d'amendement demandé à ce stade, contrairement au plafond de `src/` : le constater ici suffit à ne pas le redécouvrir en silence.*

**Une présentation qui ne dépend que de `State`/`Configuration` (statuts, phases, barre de progression) se calcule dans la façade partagée, jamais dans une vue Tkinter.**
*Motif (GUI V1, lot 3) : `conception/GUI_V1.md` §15.1 exige que les statuts et les phases se testent sans Tk. Une règle de présentation écrite dans `views/*.py` ne peut être éprouvée qu'à travers un widget ; la même règle écrite dans `facade.py` s'éprouve directement sur `State`, et reste disponible si une autre surface en a besoin un jour (aucune n'est prévue, mais rien ne l'empêche non plus).*

**Une intervention GUI dont l'action porte `may_call=False` (`ACCEPT`, `ACCEPT_WITH_RESERVES`, `STOP`) appelle le moteur en direct, jamais via le fil d'exécution.**
*Motif (GUI V1, lot 5) : `workflow.decide` est une écriture locale sous verrou, synchrone, exactement comme `decide --accept` en CLI — la faire passer par un fil daemon aurait ajouté une latence et une fenêtre où l'écran affiche encore l'ancien état sans aucun bénéfice. La table `decisions.allowed_actions` porte déjà `may_call` : `iabinome/gui/views/intervention.py` s'y fie plutôt que de redécider au cas par cas.*

**Aucune dépendance de production.** Une dépendance nouvelle exige une nécessité démontrée et une décision humaine.
*Motif : DialogForge a tenu deux mois avec `dependencies = []`. C'est tenable.*

---

## Travail avec les agents

**Développement assisté (PO, 2026-09-26 ; acceptation déléguée le 27) : Git peut être lu sur deux commits, jamais écrit par DialogForge.** Le développeur extérieur écrit le code et exécute ses tests. Les paquets figent code et résultats déclarés ; une modification impose un nouveau paquet et une collaboration ordinaire. Aucun second moteur d'appels. Conception : `conception/DEVELOPPEMENT_ASSISTE.md`.

**Runner V1 engagé par le PO le 2026-10-01 : exception séparée au développement assisté documentaire.** Sur `feat/runner-v1`, le Runner peut préparer un clone indépendant, appeler un agent développeur et recueillir ses commits locaux ; il ne modifie ni le dépôt source ni le cycle A/B, et remet un paquet à la revue existante. La conception de référence est `conception/DialogForge Runner V1 — conception simplifiée.md`. Les limites réelles de l'environnement d'écriture et des validations sont à qualifier avant un lancement sans surveillance.
*Motif : automatiser le passage entre `dev-export` et `dev-package` sans réintroduire l'orchestration des tâches dans `workflow.py`. Cette exception ne change pas la règle de lecture seule de `development.py` pour le moteur documentaire.*

**Extension GUI demandée par le PO le 2026-10-03 :** après l'acceptation de la version actuelle d'une conception, l'écran de suivi propose l'export et le lancement du Runner dans Ubuntu WSL2. Une seule exécution active, paquet livré pour revue, aucune intégration automatique. Cette extension porte le plafond façade + GUI à **2 400 lignes effectives** (2 216 mesurées), tout en gardant une vue à 400 lignes maximum. Le plafond propre à la GUI V1 reste historique ; le parcours Runner est décrit dans `docs/RUNNER.md`.

**Taille de ce lot : ajout net dans `src/` strictement inférieur à 1 000 lignes effectives depuis 5 618 ; cible ≤ 500.** Cette décision du PO remplace pour ce lot la marge restante de 164 lignes. La limite façade/GUI n'est pas modifiée.

**Claude produit, Codex relit palier par palier — et réciproquement.**
*Motif : économie de tokens côté Claude, et la revue croisée rattrape ce que l'auteur ne voit pas.*
**Suspendue en étape 2 le 2026-09-03, décision du PO** : la conception a déjà été contredite cinq tours, et sa précision rend la relecture de code palier par palier peu rentable. **La règle reste valable pour la conception**, où elle a produit les huit remarques techniques toutes retenues. Réouverture si un palier révèle un défaut que la relecture aurait attrapé. **Rouverte le 2026-09-05** : la condition s'est réalisée — deux défauts de gabarit trouvés en mission réelle, invisibles pour la suite de tests. La relecture rendue a produit **huit observations, huit exactes, dont trois inatteignables par un cycle nominal**.

**Une relecture externe et une suite de tests ne couvrent pas le même espace : la verdeur de l'une ne justifie pas de suspendre l'autre.**
*Motif mesuré le 2026-09-05 : 262 tests verts, et une lecture statique a trouvé six défauts réels — une lecture rompue prise pour une fin de flux, une branche de reprise contournant l'intégrité, un séparateur de chemin rendant toute collaboration inutilisable dès sa création. Tous vivaient dans des fenêtres qu'un cycle nominal ne traverse jamais.*

**Avant de figer un contrat de revue, le rejouer sur des revues réelles conservées.**
*Motif mesuré le 2026-09-19 (1.2) : les revues du 2026-09-05 sous `conception/essais/` montrent B réécrivant l'énoncé de ses sept constats pour y dire « désormais résolu ». Aucun test à faux agent ne pouvait le voir ; le contrat garde maintenant l'énoncé initial et récupère la réécriture comme justification, sans nouvel appel. `tests/test_objections.py` rejoue ces revues.*
*Vaut aussi pour choisir entre deux corrections : le 2026-09-25, « vider `open_questions` à la reprise » était recommandé pour sa taille (une ligne) ; rejoué sur les deux cadrages réels, il aurait écrit `[]` alors que le brouillon listait deux inconnues (amendement A4).*

**Dans une sortie d'agent, « rien » ne se lit que s'il est écrit comme le contrat le définit ; un bloc absent, vide ou ambigu est une inconnue, jamais une liste vide.**
*Motif mesuré le 2026-09-25 : le contrat de F ne définissait pas la liste vide ; Claude écrivait une puce nue, Codex `- Aucune.` — l'une indiscernable d'un oubli, l'autre lue naïvement comme une question nommée « Aucune. ». A4 fixe `- AUCUNE`, garde la valeur précédente sur un bloc ambigu, et écrit `null` quand rien n'a été exprimé.*

**Une consigne de relecture se fait relire avant d'être envoyée.**
*Motif mesuré le 2026-09-05 : cinq corrections sur la mienne, toutes justes. Deux étaient graves — « n'exécute rien » aurait privé le relecteur de ses outils de recherche, et rien n'empêchait qu'une documentation périmée soit présentée comme un défaut du code. Le coût est un appel ; le bénéfice, une passe qui porte.*

**Un relecteur à qui on demande des écarts en trouve : lui imposer une hiérarchie des sources et l'obligation de signaler une contradiction plutôt que de la trancher.**
*Motif : sans hiérarchie, il choisit naturellement la source qui permet de construire un manquement, et une documentation périmée devient un défaut certain du code. Formulation retenue : « si deux sources se contredisent, signale cette contradiction ; ne choisis pas en silence celle qui permet de construire un manquement. »*

**Ne jamais réparer une course par une course de même fenêtre.**
*Motif mesuré le 2026-09-05 : un `verrou.json` tronqué par un arrêt entre sa création exclusive et son écriture bloque définitivement. Le récupérer automatiquement effacerait le verrou d'un détenteur **vivant** surpris dans cette même fenêtre — même probabilité, conséquence pire : deux détenteurs au lieu d'un blocage visible. Un blocage franc et un message actionnable valent mieux qu'une corruption silencieuse.*

**Le contradicteur reçoit une consigne d'omission, pas une consigne de qualité :** « qu'est-ce qui a été écarté en silence ? »
*Motif : c'est la seule vérification sérieuse qu'une récolte n'a rien perdu ; relire son propre travail ne la remplace pas.*

**Mais la consigne d'omission doit être accompagnée du périmètre**, sinon le contradicteur remplit les manques en reconstruisant ce qu'on venait d'abandonner.
*Motif mesuré le 2026-09-03 : la passe 1 de Codex sur l'inventaire réintroduisait l'appareil de confinement de DialogForge. Sa V1.1, après précision du périmètre, s'est contredite elle-même sur six points.*

**Les indices que l'auteur a sur ses propres faiblesses ne sont donnés au contradicteur qu'après sa première réponse.**
*Motif : les donner d'emblée l'oriente vers ce que l'auteur sait déjà avoir raté, et l'éloigne de ce qu'il ignore — soit l'inverse de ce que la consigne cherche.*

**Chaque observation du contradicteur reçoit exactement une disposition écrite :** acceptée et intégrée · rejetée avec justification · différée avec condition · bloquante.
*Motif : repris de la préanalyse DialogForge, 31 observations, aucune sans disposition. C'est ce qui empêche de refermer une revue en laissant tomber ce qui dérange.*

**Le rôle et l'outil sont deux axes indépendants : A et B sont chacun Claude ou Codex, choisis au lancement.** Aucun fournisseur n'est nommé hors de son adaptateur.
*Motif : ajoutée en rattrapage à DialogForge, la permutation n'a jamais été complète — quotas et récupération de revue sont restés liés à un fournisseur (`recover_failed_review` ne cherchait que `*claude.txt`).*

**Le modèle est un troisième axe : `A == B` en outil ne veut pas dire « le même modèle se relit ».** Le programme n'interdit pas `A == B`, et cette décision est écrite. *(PO, 2026-09-05.)*
*Trois motifs, dans l'ordre de force. **Un.** Le risque documenté d'auto-révision porte sur le **modèle**, pas sur la CLI : `adapters/claude.py` déclare `{A: opus, B: fable}`, donc `1→1` est Opus qui produit et Fable qui critique — la configuration que `CLAUDE.md` §6 recommande. Un contrôle sur `agent_a != agent_b` viserait le mauvais axe : il laisserait passer `--model-a opus --model-b opus`, qui est le vrai cas, et interdirait le défaut recommandé. **Deux.** Mesuré le 2026-09-05 : outil 2 a été en quota de 09:38 à 14:56 : pendant ces trois heures, `A == B` était la **seule** configuration exécutable. Un refus dur aurait transformé un quota fournisseur en arrêt complet du projet. **Trois.** `1→1` n'a jamais tourné : il n'y a aucun défaut mesuré à compenser, seulement une attente.*
*Conséquence assumée : **`A == B` n'étant pas un usage retenu, aucune mission réelle `1→1` ni `2→2` ne sera payée.** Les quatre permutations restent couvertes par `FakeAdapter` ; deux sont mesurées en réel, et c'est délibéré, pas une lacune à combler.*

**Le cycle ne dépend que des capacités présentes chez les deux outils ; ce qui est propre à l'un est un bonus, jamais un prérequis.**
*Motif : DialogForge a bâti sa reprise après quota sur l'erreur typée de Claude ; Codex ne la produit pas, et la reprise n'a jamais marché de ce côté.*
*Exception écrite du 2026-09-24 (PO), pour l'agent de cadrage F seul (`conception/CADRAGE_AGENT.md`) : F exige une session persistante pendant tout un cadrage, et un adaptateur qui ne la déclare pas (`supports_persistent_framing_session`) est refusé avant tout appel. Il ne s'agit pas d'un bonus devenu prérequis en silence : les deux outils offrent la reprise par identifiant, qui est le mécanisme retenu (amendement A3). A et B n'en dépendent pas et gardent `fresh_session`.*

**Modèles par défaut, surchargeables : Opus 5 pour A (produit), Fable 5 pour B (critique).**
*Motif : la critique est l'endroit où la capacité paie. Sur le Lot 0, quatre revues de plan pour une seule exploitable ont coûté 41 % du budget mesuré.*

**Alléger les prompts, ne pas les durcir.**
*Motif : sur les modèles récents, des consignes trop prescriptives dégradent la qualité de sortie. Mesuré sur des tâches à douze critères d'acceptation imbriqués.*

**Un agent qui commente son choix de format n'est pas un agent qui désobéit.** Un contrat de forme accepte ce qui est **explicitement balisé**, et ne devine jamais ce qui ne l'est pas.
*Motif mesuré le 2026-09-04 : B a fait précéder une revue juste de 3,6 Ko d'une phrase expliquant qu'il répondait en JSON brut « comme demandé ». Le bloc clôturé ne couvrait plus toute la réponse : refus, 231 s d'appel payant perdues. Il avait déjà lu « retourne seulement le JSON » et croyait l'appliquer. La ligne refusée n'était pas un principe mais une position sur une pente ; « jamais de défaut permissif » se tient au bon endroit — sans balise, un préfixe ou un suffixe restent un refus.*

**Le préambule de format n'est pas un aléa : il naît d'une collision entre le rôle demandé et un outil du harnais de l'agent.** Quand le format demandé ressemble à une capacité que l'agent possède déjà, il explique laquelle il n'utilise pas.
*Motif mesuré deux fois, le 2026-09-04 et le 2026-09-05 : les deux préambules de B nomment `ReportFindings` — un outil de son propre harnais dont le nom évoque « rendre des constats » — et s'expliquent de ne pas s'en servir. **Deux fois sur quatre appels de B côté outil 1.** Le second serait tombé sur l'appel le plus cher d'une mission montée pour prouver la boucle de révision. Conséquence : la tolérance au bloc entouré de prose n'est pas un confort, c'est ce qui empêche de perdre une mission sur deux ; et durcir le prompt aurait visé la mauvaise cause, puisque B croyait déjà obéir.*

**Dans une sortie en flux d'événements, la réponse est le dernier message de l'agent d'un tour terminé, jamais la concaténation de ses messages.**
*Motif mesuré le 2026-09-25 (protocole du lot 4, phase 6, sortie `--json` d'un des deux outils) : le tour d'ouverture portait deux messages de l'agent. Le premier annonçait ce qu'il allait faire (« Je vérifie le fichier demandé… »), le second répondait. Concaténés, ils auraient placé du texte devant `IABINOME:DEMANDE`, qui n'en tolère aucun : un brouillon conforme serait devenu non conforme par l'extraction, et non par F. Sans l'événement de fin de tour, rien n'est rendu.*

**Ne jamais prescrire une commande qu'on n'a pas lancée, ni affirmer une impossibilité sans avoir cherché tous les chemins.**

---

## Git

**L'identité git est `schneider <schneider.jm@free.fr>`, déjà en configuration globale. Ne jamais passer `-c user.name=…` / `-c user.email=…`.**
*Motif : l'adresse fournie par le contexte de session est celle du compte Claude. Utilisée le 2026-09-02, elle a produit un commit à corriger par `--amend --reset-author`.*

**Jamais d'opération git destructive (`reset --hard`, `checkout --`, `clean`) avec des modifications en cours : `stash` d'abord.**
*Motif : deux à trois heures de travail perdues sur FloraPi de cette façon.*

**Ne jamais classer « temporaire » un dossier non suivi sans l'avoir ouvert : un dossier à la racine peut être une collaboration réelle.**
*Motif mesuré le 2026-10-01 : `git clean -fd` a effacé quatre collaborations GUI (`Reprise_Activité_*`) jugées « essais temporaires » sur leur seul nom, alors qu'elles figuraient dans `~/.dialogforge/recents.json`. Ici, le PO les tenait pour des tests. Avec un `stash -u` préalable, la perte aurait été réversible.*

**Messages de commit sans accents**, préfixes `docs:` `feat:` `fix:` `test:` `chore:`.
*Motif : cohérence avec le prédécesseur, dont l'historique entier suit cette convention.*

---

## Outils et commandes

**`ruff check .` et `mypy` avant tout commit.**

**Lancer la suite par `pytest tests`, jamais `pytest` nu.** Sans chemin, il ramasse aussi les tests du plugin PWF embarqué sous `tools/` et s'arrête sur `ModuleNotFoundError: yaml` — une erreur de collecte qui ressemble à une suite cassée.
*Motif mesuré le 2026-09-19, en ouvrant le lot 1 : la référence verte (302 passés, 2 ignorés) n'est celle de `tests/` qu'à cette condition.*

**Aucun appel fournisseur dans la suite de tests** — l'agent `fake` est obligatoire.
*Motif : une suite de tests qui appelle un modèle payant n'est plus une suite de tests.*

**Commandes de développement via l'outil Bash, avec des chemins relatifs.** Pas de PowerShell ad-hoc du type `& "C:\…\outil.exe"`.
*Motif : le PowerShell ad-hoc rate l'allowlist et déclenche une confirmation superflue.*

**Une commande `iabinome` affichée pour une collaboration hors du dépôt (`essais-*`, dossier de l'utilisateur) porte toujours un chemin absolu, jamais relatif au dépôt.**
*Motif mesuré le 2026-09-22 (lot 3.2, deux fois) : `decide essais-3-1\nextcloud-clients --accept` lancé depuis `DialogForge_2` a cherché `DialogForge_2\essais-3-1\…`, inexistant, et rendu `[Errno 2] No such file or directory: 'verrou.json'` — un chemin de dossier, pas un incident du moteur. Aucun état abîmé (`verrou.json` n'existe qu'en appel, jamais au repos), mais une commande à corriger et relancer.*

**Ne pas préfixer les commandes avec `cd` vers la racine du projet** — le répertoire courant y est déjà.

**Écrire un fichier de code par l'outil Write, jamais par un `heredoc` shell.** Un document long à guillemets multiples est mutilé au passage.
*Motif mesuré le 2026-09-03 : `cat > transport.py <<'EOF'` a rendu `unexpected EOF while looking for matching quote` sur 240 lignes valides.*
*Vaut aussi pour un script jetable, un correctif de script ou un patron de mutation : le 2026-09-19, une apostrophe d'un motif écrit en heredoc a été mutilée et le script est tombé en `SyntaxError`.*
*Et pour un script Python passé en heredoc qui réécrit un fichier : le 2026-09-25, deux fois, ses `\\n` (antislash doublé, pour un `\n` littéral) sont devenus de vrais sauts de ligne dans le code de test produit (`SyntaxError`). L'outil d'édition, lui, écrit exactement.*

**Une branche écrite pour un OS non testé ne doit jamais casser l'outillage de l'OS testé.** Ne pas nommer un symbole absent de la plateforme de développement — `signal.SIGKILL`, `os.killpg`, `os.getpgid` — même dans du code qui n'y tournera pas.
*Motif : `typeshed` les déclare absents sous `win32`, donc `mypy --strict` échoue sur le poste. Contournement retenu dans `transport.py` : `os.kill(-pid, 9)`, où le PID négatif désigne le groupe.*

---

## Tests

**Un test qui vérifie une absence doit d'abord être prouvé capable de voir la présence.**
*Motif : le test de terminaison d'arbre affirme qu'un petit-fils ne dépose jamais sa marque. Sans avoir vérifié — hors suite — que cette marque apparaît quand on ne tue personne, le test passerait tout aussi bien parce que le petit-fils n'a jamais existé.*
*Second motif, mesuré le 2026-09-04 : le test de course du verrou affirme qu'un seul processus entre. Rejoué contre l'ancien verrou, il en montrait zéro au lieu de trois — chaque concurrent écrivait son résultat dans un `except` qui rattrapait aussi l'échec de **libération**, si bien qu'un entrant se déclarait refusé. La contre-épreuve n'a pas seulement validé le test : elle a corrigé le test.*

**Sur quota, les deux outils rendent un code de retour non nul ; ce qui diffère, c'est le flux.** Outil 1 écrit son message sur `stdout`, outil 2 sur `stderr`. Le test du code de retour attrape donc le quota **des deux côtés** — c'est `extract()` qui ne doit jamais lire `stderr`.
*Mesuré trois fois : caractérisation du 2026-09-03, puis le 2026-09-05 des deux côtés — outil 1 en `2.1.261` rend `1` avec 146 o sur `stdout` et `stderr` vide ; outil 2 en `0.153.2` rend `1` avec 4 115 o sur `stderr` et `stdout` vide. Dans les deux cas : `CLI_FAILED` → `INTERRUPTED`, relançable, rien de payé.*
*La ligne « outil 1 rend `0` » inscrite le 2026-09-04 était **fausse**, et elle a tenu un jour dans quatre fichiers. D-2 disait vrai depuis le début. Voir la règle sur le code de retour lu à travers un tube.*

**Un code de retour lu à travers un tube n'est pas celui de la commande.** Après `cmd | head`, `$?` est celui de `head`. Mesurer un code de retour se fait par redirection vers un fichier, jamais par un pipeline.
*Motif mesuré le 2026-09-05 : une sonde de disponibilité écrite `cmd 2>&1 | tail -c 300; echo "[rc=$?]"` a affiché `rc=0` pour un outil dont le programme, au même moment, enregistrait `return_code: 1` dans `resultat.json`. C'est très probablement ainsi qu'est né le « code de retour `0` » du 2026-09-04 — une mesure fausse qui a contredit une caractérisation juste, et qui a fait réécrire la justification d'une décision correcte.*

**Quand une mesure nouvelle contredit une mesure ancienne, c'est la troisième qui tranche — pas la plus récente.** Écrire « mesuré le … » ne suffit pas à faire d'un chiffre un fait.
*Motif : le 2026-09-04, un `0` observé une fois a suffi à déclarer faux le motif de D-2, alors que `CARACTERISATION_CLI.md` portait déjà un `1` mesuré la veille. Personne n'a remesuré. La contradiction entre deux sources du projet était visible dans les fichiers, et elle a été tranchée en silence en faveur de la plus récente — ce que `RULES.md` interdit par ailleurs au relecteur externe.*

**Ne jamais donner à un correctif un motif qu'on n'a pas mesuré.** Écrire « mesuré le … » engage.
*Motif : la normalisation CRLF a été justifiée par « une CLI d'agent écrit en mode texte, mesuré le 2026-09-03 ». La preuve venait en réalité du faux agent du projet. La caractérisation du même jour a montré que les deux vraies CLI rendent des `\n`. Le correctif reste bon comme tolérance ; c'est son motif qui était faux, et un motif faux se propage plus loin qu'un correctif inutile.*

**Un prompt qui exige un format doit porter le format — et la règle vaut pour *chaque* prompt, pas pour le premier.**
*Motif : §9 disait à B « retourne le JSON de revue v1 » sans jamais montrer le schéma — un nom interne au projet, indevinable. Chaque revue aurait échoué au contrat.*
*Second motif, mesuré le 2026-09-04 à la première mission réelle : la règle avait été appliquée au prompt de proposition, qui nommait `IABINOME:DOCUMENT` en toutes lettres, mais **pas** à ceux de révision et de finalisation, qui disaient « rends DOCUMENT ». L'agent a obéi littéralement. **Aucune mission ne pouvait aller au bout** — l'échec tombait au dernier appel, après avoir payé tous les autres. Corriger une règle à un endroit ne la corrige pas partout : il faut passer les autres au même crible.*

**Un prompt à faux agent ne teste pas un prompt.** Ce que le gabarit demande ne se vérifie qu'en lisant le gabarit.
*Motif mesuré le 2026-09-04 : 259 tests verts, dont plusieurs cycles complets, et pourtant deux prompts de A étaient inutilisables. `FakeAdapter` émet la bonne balise quoi qu'on lui demande — il ne lit pas le prompt. `tests/test_prompts.py` lit désormais les gabarits eux-mêmes.*

**La frontière d'effets d'un prompt porte sur l'écriture, jamais sur la lecture.**
*Motif mesuré le 2026-09-04 : « tu ne modifies aucun fichier et n'exécutes rien » a été lu par A comme une interdiction d'ouvrir son propre corpus — il a demandé à l'humain d'en coller le contenu. Le prompt annulait une promesse du produit, puisque l'adaptateur reçoit le dossier de collaboration comme `cwd` précisément pour qu'il y lise.*

**Le prompt d'un agent passe par `stdin`, jamais par la ligne de commande.**
*Motif mesuré le 2026-09-03 : `CreateProcess` plafonne à 32 767 caractères sous Windows, qu'un corpus réel dépasse ; et une CLI qui voit `DEVNULL` sur son entrée la lit comme un flux canalisé vide — la réponse est tombée de 673 octets conformes à 100 octets hors contrat.*

**Sous Windows, un PID terminé reste « vivant » pour `OpenProcess` tant qu'un handle du processus est ouvert.** Un test qui fabrique un PID mort doit laisser l'objet `Popen` sortir de portée avant de s'en servir.
*Motif mesuré le 2026-09-04 : dans la contre-épreuve du verrou, l'objet `Popen` gardé en variable locale faisait passer un processus attendu jusqu'à sa sortie pour un détenteur vivant — les trois concurrents refusaient le verrou pour la mauvaise raison, et la preuve semblait acquise alors que rien n'avait été testé.*

**Le compteur de ce qu'un test interdit se vérifie *avant* l'exception attendue, jamais à l'intérieur d'un `assertRaises`.**
*Motif mesuré le 2026-09-04 : le test de la porte d'état affirme qu'un second `run` ne paie aucun appel. Le compteur était vérifié dans le bloc `assertRaises` ; porte neutralisée, le test échouait sur « exception non levée » et **n'atteignait jamais le compteur** — il ne montrait pas l'appel payant qu'il cherche. Sorti du bloc, la contre-épreuve affiche `(2, 1) != (1, 0)` : A **et** B rappelés.*

**Déplacer une garantie déplace son point d'observation : vérifier que le test prouve encore ce qu'il dit.**
*Motif mesuré le 2026-09-04 : « `CALLING` publié avant `Popen` » se lisait dans `FakeAdapter.command()`. Le lot 2 ayant avancé `command()` **avant** la publication, ce point ne prouvait plus l'ordre — il aurait fallu changer l'assertion attendue, ce qui aurait rendu le test vide. La preuve est passée dans le **processus lancé**, qui relit `etat.json` depuis son `cwd`, et l'ancien point sert désormais l'autre garantie.*

**Une porte qui refuse un statut doit s'accompagner de la commande qui en sort — sinon le statut devient un cul-de-sac.**
*Motif : la porte d'état du lot 2 refuse `ERROR`. Sans N-01 — la table fermée d'incidents relançables — plus aucune commande ne sortait d'`ERROR`, et le correctif transformait un défaut en blocage. La règle vaut pour l'humain aussi : le message de refus nomme la commande.*

**Estimer un correctif en lignes, c'est se tromper d'un facteur 2 à 5 ; mesurer après coup, et en code effectif.**
*Motif mesuré le 2026-09-04 : lot 1 estimé 37 → 73 brutes ; lot 2 estimé 30 → **142** brutes. Mais 64 en code effectif — l'écart est à 65 % de la documentation. Comparer du brut à l'objectif de ~1 500 de `POURQUOI.md` fait paniquer sur une dérive qui n'existe pas ; comparer du code effectif à du code effectif donne le vrai chiffre.*

**`Path.glob` est insensible à la casse sous Windows : ne jamais s'en servir pour sélectionner par un champ.**
*Motif mesuré le 2026-09-04 : un test cherchait le dossier d'appel de B par `glob("*B*")`. Les dossiers s'appellent `NNNN-<role>-<uuid>`, et `*B*` a désigné celui de **A** dès que son UUID contenait un `b`. Découper le nom et comparer le champ est exact ; le glob ne l'est pas.*

**Un faux agent écrit des octets UTF-8 sur le tampon binaire, jamais `write(str)`.** Sous Windows, le flux texte d'un tube encode en cp1252 alors que les adaptateurs décodent en UTF-8 : toute réponse simulée accentuée rend `DECODE_FAILED`.
*Motif mesuré le 2026-09-19 (1.2) : un cycle à deux tours s'arrêtait en `ERROR` sans rapport avec le moteur, pour un « Désormais » dans une revue simulée. Le défaut était consigné depuis le lot 0 comme « à retenir » ; corrigé à la source dans `tests/fakes.py` plutôt que contourné par une variable d'environnement.*

**Sous Windows, résoudre l'exécutable avec `shutil.which()` avant `Popen`.**
*Motif : une entrée de PATH installée par npm est un script sans extension ; `CreateProcess` rend `WinError 2`. `shutil.which` rend le `.CMD` qui, lui, se lance.*

**Une décision différée porte sa condition de déclenchement, sinon elle est oubliée.**
*Motif : le palier 1 a écarté la normalisation CRLF→LF en écrivant « à statuer si un besoin réel apparaît ». Le besoin est apparu au palier 3 — une CLI Windows écrit en mode texte, et la balise de première ligne n'était jamais reconnue. La condition écrite est ce qui a fait rouvrir la question au lieu de la redécouvrir comme un bug.*

**Les tests d'un palier font remonter les défauts des paliers précédents — c'est une raison de les écrire contre du réel.**
*Motif : deux défauts du palier 1 (bloc JSON clôturé refusé, CRLF non normalisé) n'ont été vus qu'en faisant tourner le moteur du palier 3 contre de vrais sous-processus. Aucune relecture du code seul ne les avait montrés.*

**Un test de comportement de l'OS se fait contre un vrai sous-processus, pas contre un objet simulé.** L'objet simulé ne prouve que ce qu'on y a mis.
*Motif : `transport.py` existe pour tenir deux tubes concurrents, un délai dur et la terminaison d'un arbre. Un `FakeProcess` — que la spécification nommait — n'en démontrerait aucun. Un vrai sous-processus Python scripté n'est ni un appel fournisseur, ni du réseau : la règle est tenue, c'est le moyen qui change.*

**Un test de `cli.py` doit substituer `cli.ADAPTERS` par des `FakeAdapter` avant tout appel à `run`/`resume`.** Claude Code et Codex CLI sont tous deux sur le PATH de la machine de développement : un test qui invoque `cli.main(["run", …])` sans substitution appellerait un vrai fournisseur, silencieusement.
*Motif : mesuré au palier 4, 2026-09-04. `new`/`status` ne posent pas ce risque — ils ne sondent ni n'invoquent jamais d'adaptateur.*

**Un test de `cli.py` doit aussi vider `settings.SEARCH_PATHS`.** Un `iabinome.toml` posé à la racine du dépôt ou dans le dossier personnel du développeur rendrait la suite dépendante de la machine.
*Motif : même famille que la substitution de `cli.ADAPTERS`, et même conséquence — un test qui passe chez l'un et échoue chez l'autre, pour une raison invisible dans le code. Les tests qui veulent un fichier le désignent par `--config`.*

**`mock.patch.object(module, "nom_importe", …)` échoue sous `mypy --strict`** (`--no-implicit-reexport` refuse l'accès à un attribut simplement importé). Patcher le module d'origine de l'attribut (`shutil.which`, pas `adaptateur.shutil.which`) le contourne sans rien désactiver.
*Motif : mesuré au palier 4, 2026-09-04, sur `tests/test_adapters.py`.*

**Un test qui rapproche la documentation du code cherche chaque élément dans la section de son propriétaire, pas dans tout le fichier.**
*Motif mesuré le 2026-09-20 (`tests/test_docs.py`) : la première version cherchait chaque option de la CLI n'importe où dans `COMMANDES.md`. Elle passait au vert, et une contre-épreuve — retirer `--timeout` de la seule section `decide` — ne la faisait pas échouer, puisque `run` le décrivait aussi. Une contre-épreuve par élément, pas seulement une par test : neuf mutations détectées du premier coup ne disaient rien de la dixième. Limite assumée : le test prouve qu'un élément est **nommé**, jamais que le texte est **vrai**.*

**Un test GUI qui déclenche une action pouvant ouvrir une boîte modale la remplace, même quand le chemin attendu ne l'ouvre pas.** Sinon, une régression bloque la suite au lieu de la faire échouer.
*Motif mesuré le 2026-09-24 (phase 6, lot 5, contre-épreuves) : le test « un brouillon invalide est refusé avant création » n'attendait aucune boîte. Mais une mutation qui neutralisait la relecture laissait créer la collaboration, puis `messagebox.showinfo` ouvrait une vraie fenêtre, jamais fermée. Le lanceur de mutations a dû être tué à la main. Avec la boîte remplacée, la même mutation échoue en 2 s.*

**Un test qui lance un fil moteur à côté d'une racine Tk sans `mainloop()` vide d'abord le ramasse-miettes dans le fil principal** (`collect_tk_garbage()`).
*Motif mesuré le 2026-09-25 : des `tkinter.Variable` laissées en cycles par les tests précédents étaient finalisées dans le fil moteur. Chaque `__del__` appelait Tk hors du fil principal (« main thread is not in main loop »), et le cycle finissait `INTERRUPTED`, 6 fois sur 6 sur un sous-ensemble de la suite, jamais sur la suite complète. L'échec dépendait de l'ordre des tests, pas du code essayé.*

**Sous Windows, un fichier remplacé atomiquement est un instant illisible pour un lecteur concurrent : un sondage qui tombe dessus retente au tour suivant, il ne s'arrête pas.**
*Motif mesuré le 2026-09-25 : l'écran de suivi lisait `etat.json` pendant que le moteur le remplaçait (« Permission denied »). Il affichait « Dossier illisible » et cessait de se rafraîchir, alors que le cycle continuait. Un test intermittent l'a montré, et une instrumentation l'a prouvé.*

**Un scénario de référence qui n'échoue jamais ne prouve rien : son code de sortie doit dire si le cycle est allé à son terme.**
*Motif mesuré le 2026-09-19 : `reference/cycle_sans_fournisseur.py` a affiché `statut : ERROR` et sorti en code `0`. Mes « scénario rc=0 » du jour prouvaient donc seulement qu'il s'exécutait. Il rend désormais `1` hors de `AWAITING_APPROVAL` sans objection ouverte, et la contre-épreuve (A qui ne répond pas) le fait échouer.*

---

## Conduite de projet

**Une décision actée peut être rouverte, mais jamais en silence :** signaler, tracer, faire re-décider.

**Ce qui se renomme, c'est la surface exposée — pas le code.**
*Motif (PO, 2026-09-22) : la question n'était pas « renommer `iabinome` » mais « ne pas exposer IAbinome à l'utilisateur ». Renommer le paquet aurait touché ~35 fichiers de `src/` et `tests/` pour un gain nul côté utilisateur ; renommer ce qu'il **tape, écrit et lit** — commande `dialogforge` (point d'entrée `[project.scripts]`), aide, nom de distribution, fichier de réglages, préfixe du dossier jetable, documentation — a coûté une quinzaine de lignes. Le paquet importable reste `iabinome`, et `python -m iabinome` reste fonctionnel sans être documenté. Corollaire : un fichier cherché dans le **dossier courant** porte le nom du produit et non une généralité (`reglages.toml`), parce qu'une clé inconnue y est un refus — un homonyme d'un autre outil ferait échouer les commandes au lieu d'être ignoré ; dans le dossier personnel, c'est `~/.dialogforge/` qui porte le nom et le fichier qui porte sa fonction.*

**Un nom d'usage qui change laisse l'ancien lisible, et le dit.**
*Motif (2026-09-22) : après le passage à `dialogforge.toml`, un `iabinome.toml` resté en place aurait cessé d'agir sans un mot, et l'erreur visible aurait été `valeur(s) absente(s) : --agent-a…` — on cherche la panne ailleurs. Les anciens noms restent donc dans `SEARCH_PATHS`, en dernier recours, avec un message nommant le remplaçant. C'est la même règle que « un réglage inconnu est refusé, jamais ignoré », appliquée au nom du fichier plutôt qu'à son contenu. Les balises de contrat `IABINOME:*` échappent à cette passe : les renommer casserait `resume --reprocess` sur les collaborations existantes — changement de contrat, décision distincte.*

**Une page de limites se rédige depuis les mesures consignées, pas depuis un document écrit avant elles.**
*Motif mesuré le 2026-09-20 : `docs/LIMITES.md` a d'abord repris de `FRONTIERE_ROLES.md` (écrit avant les essais) que les options d'isolation n'avaient « jamais été éprouvées ». Le journal du 2026-09-19 montrait qu'elles avaient été **acceptées** par les deux outils en réel, authentification conservée. Deux faits distincts — « accepté » et « appliqué » — et seul le second est resté non mesuré. Une page qui l'aurait confondu aurait sous-déclaré ce qui est acquis, ce qui est aussi faux que le sur-déclarer.*

**`tests/test_docs.py` garantit la forme, jamais la vérité : une documentation se confronte au code et aux mesures, et les commentaires du code vieillissent avec elle.**
*Motif mesuré le 2026-09-22 (revue de documentation demandée par le PO) : la suite était verte, et pourtant `CLAUDE.md` et `iabinome.toml.exemple` décrivaient encore un appel `A finalise` supprimé en 1.3, quatre documents annonçaient ~1 500 lignes pour 3 253, et cinq commentaires d'adaptateur disaient « non éprouvé en réel (lot 3) » après que le lot 3 l'eut éprouvé. Le test compare les options et les liens ; rien ne relit les affirmations. Corollaire : une page patchée à chaque session (ici `LIMITES.md`) dérive en journal — une passe de clarté se fait à froid, et le récit d'enquête descend dans `reference/`.*

**Avant d'attribuer une ligne à un fichier de l'utilisateur, vérifier qu'elle y est** (`grep -c` sur le fichier), et se méfier des lignes que l'outil de l'assistant ajoute lui-même à ses sorties.
*Motif mesuré le 2026-09-20 (3.1) : « Shell cwd was reset to C:\Projets\DialogForge_2 » terminait mes lectures de `.err`, et je l'ai inscrite dans le tableau du protocole comme contenu du stderr de Claude, puis j'ai demandé au PO d'en chercher l'origine. Les fichiers faisaient 0 octet : la ligne venait de mon propre outil, qui l'ajoute quand le dossier de travail change. Un `grep -c` aurait suffi ; il a fallu une erreur écrite dans un document validé, puis rectifiée.*

**La documentation qui cite une sortie du programme la cite telle que le programme la produit, jamais réécrite.**
*Motif (3.3) : les extraits de `PRISE_EN_MAIN.md` viennent du scénario sans fournisseur rejoué en UTF-8. La première capture avait perdu les accents (console cp1252) ; recopier la sortie « à la main » aurait écrit une version que le programme ne produit pas. Ce sont des sorties de faux agents : à relire contre un cycle réel.*

**Une voie écrite dans un document de décision n'est pas encore une implémentation : la relire contre le code avant de la soumettre à l'arbitrage.**
*Motif mesuré le 2026-09-05 : la voie B du bloc clôturé était formulée « exactement un bloc ; zéro ou deux restent un refus » — inapplicable, puisque compter les clôtures découpe au mauvais endroit dès que la revue cite du markdown dans `analysis`. L'ancrage correct, première clôture → dernière, était déjà dans le code. Soumis tel quel, l'arbitrage aurait porté sur une règle qu'on n'aurait pas pu écrire.*

**Une question marquée « à trancher avant de commencer » dans un document du projet se tranche dans ce document même**, avec son motif et sa date — pas seulement dans les notes de session.
*Motif : la question de périmètre de `RECOLTE.md` portait la mention « non tranché » depuis le 2026-09-02 ; laissée dans les notes, elle se serait reposée à chaque session.*

**Une source de récolte s'abandonne dès qu'elle ne rapporte plus rien de neuf — et l'abandon se note, avec le volume non lu.**
*Motif : c'est la seule façon de distinguer une source épuisée d'une source oubliée. Sans la note, le relecteur ne peut pas contredire.*

**Trancher les choix à défaut évident et avancer.** Réserver les questions aux vrais embranchements — métier, ergonomie, risque — que rien ne permet d'inférer.

**Métrique de garde : l'outil ne dépasse jamais le projet qu'il sert.**
*Motif : DialogForge pesait 87 382 lignes pour un FloraPi de 58 894. Voir `POURQUOI.md`.*
**Amendement du 2026-09-22 (PO) : le chiffre de ~1 500 lignes est abandonné, la métrique ne l'est pas.** Mesuré à J3 : 3 253 lignes de code dans `src/` (4 891 avec commentaires et docstrings), contre 2 968 au commit de départ ; 7 555 en tests. *Motif : le dépassement est assumé explicitement plutôt que constaté en silence dans quatre documents qui annonçaient encore 1 500. Ce qui se surveille reste le rapport à la taille du projet servi, pas un absolu.*

**Une garantie qui se contente de consigner une perte ne la garantit pas : la rendre impossible par construction.**
*Motif mesuré le 2026-09-19 (1.1) : `--answer` remplaçait la demande et je n'y ai ajouté que `sections_retirees`, qui constate. Le PO l'a refusé, et le test qui montrait la section « Sources » retirée en était la preuve. Corrigé en faisant de la réponse un complément dont le texte existant est un préfixe intact : plus rien à constater.*

**Un texte dérivé qu'un rejeu doit retrouver à l'identique ne contient ni horloge ni compteur global.** Il se déduit du texte de base.
*Motif : la demande complétée est reconnue au rejeu par son empreinte ; son numéro de « Précisions » vient du texte, sa date de la provenance. Avec une date dans le texte, un arrêt brutal suivi d'une reprise un autre jour aurait refusé une demande pourtant écrite.*

**Une sortie vide avec un code 0 n'est pas un succès — pour le résolveur de plan PWF, c'est le refus lui-même.**
*Motif (2.3) : `resolve-plan-dir.sh` rend toujours 0 (« never errors out the agent loop ») ; identifiant inexistant, mal formé, sélection ambiguë et racine invalide y passent par une sortie vide (mesuré). Se fier au code de retour ferait prendre un refus pour un plan. À l'inverse, un identifiant épinglé sans `task_plan.md` est rendu tel quel : l'outil le vérifie lui-même, ainsi que le nom du dossier rendu (jamais un autre plan que celui demandé), et épingle `PLAN_ID` et `PWF_PLAN_ROOT` sans hériter de ceux de la session.*

**La liaison à un plan est un fichier à part, que le cycle ne lit pas ; le plan reste seul propriétaire de l'avancement.**
*Motif (2.3) : `configuration.json` a un schéma strict (clés exactes) et le cycle en dépend ; y loger une référence facultative faisait de sa suppression une opération sur un fichier d'état. `plan.json` se supprime sans rien toucher, une liaison cassée ne bloque rien, et l'outil n'écrit jamais dans un plan ni ne copie ses phases : une seconde liste à cocher est exactement ce que CLAUDE.md §0 interdit.*

**L'accès web est un réglage explicite, fermé par défaut, identique pour A et B — et dit dans l'argv des deux outils.**
*Motif (3.1) : Codex cherchait sur le web sans que rien ne le demande (`--sandbox read-only` ne l'arrête pas) ; Claude, sous `--tools Read,Grep,Glob`, ne le pouvait pas — deux permutations non comparables. Le PO a écarté le « web par défaut » : `web_access` est figé à `new`, absent il vaut faux, et **les deux sens sont explicites** (`-c web_search=disabled` ou `live` pour Codex ; les outils web ajoutés et autorisés, ou absents, pour Claude), parce qu'un défaut laissé au réglage de l'outil est un défaut qui change avec l'outil. `CONTEXT_ONLY` reste sans aucun outil.*

**Un réglage facultatif n'écrit rien tant qu'il n'est pas posé, et se valide contre l'outil qui le reçoit.**
*Motif (3.1) : `effort` et `web_access` n'entrent dans `configuration.json` que s'ils sont donnés — sans eux, le fichier, l'argv et le comportement sont ceux d'avant, et les dossiers déjà créés restent lisibles. Le vocabulaire d'effort est celui de chaque CLI (Claude `max`, Codex `minimal`) : une valeur incompatible est refusée à `new` **et** au prévol, avant toute mutation et tout quota, jamais découverte par l'échec d'un appel payé. Sa forme reste bornée, parce qu'elle finit dans une ligne de commande.*

**Un fournisseur ne reçoit rien de l'autre : le filtre d'environnement dépend de l'adaptateur, et c'est lui qui nomme ses variables.**
*Motif (3.1) : le filtre de 2.2 était global — un jeton, un chemin de configuration ou une clé d'API d'un outil allait chez l'autre, et le noyau nommait les fournisseurs, contre `CLAUDE.md` §6. Désormais chaque adaptateur déclare une `EnvPolicy` (ce qu'il possède, ce que son hôte y dépose, ce qu'il garde et **pourquoi**) ; le noyau ne lit que des politiques. `CLAUDE_CONFIG_DIR` (le compte) reste chez Claude et n'existe pas chez Codex ; `CODEX_HOME` l'inverse. Le plan et les sessions d'hôte sont retirés à tous.*

**Un agent ne tourne pas dans le dossier qu'il ne doit pas lire.**
*Motif (2.2) : B héritait de la collaboration comme dossier de travail — `appels/`, le journal du producteur, les anciennes demandes y étaient à portée d'un outil de lecture, sans qu'aucune règle ne l'ait voulu. Le dossier est désormais jetable, avec une **copie** du corpus (jamais un lien, même dur : écrire dedans atteindrait l'original) ; l'environnement est filtré par une liste de refus **nominative**, une liste d'autorisation cassant l'authentification de la première CLI dont on ignore les besoins.*

**Une protection dit ce qu'elle obtient, ce qu'elle constate seulement, et ce qui n'est pas mesuré.**
*Motif (2.2) : les drapeaux d'argv (`--restricted`, `--sandbox read-only`, `--ephemeral`…) sont lus dans `--help`, jamais éprouvés sur un appel réel ; `Capabilities` dit ce que l'adaptateur **demande**, pas ce que la CLI **fait**. Un chemin absolu n'est arrêté que par l'outil : le corpus modifié est donc constaté après l'appel (`SOURCES_MODIFIED`), pas empêché. Écrire « garanti » avant le lot 3 serait la promesse que ce projet s'interdit — voir `reference/FRONTIERE_ROLES.md`.*

**Qualifier un confinement sur la trace de l'appel réellement exécuté et sur des témoins relus hors sandbox, jamais sur le seul code de sortie de la CLI.**
*Motif mesuré le 2026-10-02 (Runner V1) : Claude a rendu le code 0 et les témoins sont restés intacts lors de deux essais, alors qu'un classificateur avait interrompu un appel et que les commandes suivantes n'avaient pas été exécutées. Un test séparé, limité à une commande de lecture, a enfin montré l'appel `Bash`, son erreur WSL `socket failed 1` et l'absence du marqueur attendu. Rapport : `reference/RUNNER_QUALIFICATION_2026-10-01.md`.*

**Avant d'ajouter un garde-fou, vérifier qu'il compense un défaut encore réel.**
*Motif : l'échafaudage compense la faiblesse des modèles ; les modèles récents en demandent moins, pas plus.*

**N'éprouver un refus de chemin d'un profil de permissions Codex (Windows, backend élevé) que dans un dossier jetable, puis vérifier `icacls`.**
*Motif mesuré le 2026-09-21 (3.1) : `codex sandbox -P` avec un chemin refusé pose des ACL `DENY` **persistantes** pour le groupe local `CodexSandboxUsers`, qui survivent à la commande. Mes essais en ont laissé sur le dossier temporaire de la session ; l'essai suivant a échoué en `CreateProcessWithLogonW failed: 267` alors qu'il avait marché — refuser un ancêtre interdit aussi d'atteindre ses fils. `icacls <dossier>` a montré la cause, `icacls <dossier> /remove:d <groupe>` l'a réparée. Un profil de permissions n'est pas un réglage sans effet : il modifie le disque.*

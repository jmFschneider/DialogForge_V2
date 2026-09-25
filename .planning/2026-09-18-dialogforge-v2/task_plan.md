# Task Plan: DialogForge V2 — développement

## Goal
Livrer un logiciel local où l'utilisateur décrit une demande, obtient une production A critiquée
par un B indépendant, une correction avec une disposition explicite par objection, puis décide —
avec reprise après incident sans rejouer un appel ambigu.

## Next Step
**Phase 6 (cadrage avec agent F) — lots 1 à 5 faits ; lot 4 commité (`028a1dd`, `ec0c7a6`), ses résultats de partie 2 non commités.**
Session du 2026-09-25, portée déclarée par le PO : lot 4.
Conception : `conception/CADRAGE_AGENT.md` (acceptée, amendements A1-A3).
- **Lot 4 conforme chez les deux outils** (`reference/PROTOCOLE_CADRAGE_LOT4.md`). Partie 1 (4 appels
  hors produit) : même identifiant, contexte rappelé, aucune écriture en reprise. Partie 2 (un cadrage
  réel par le produit et par outil, 6 échanges chacun, avec un « continuer ») : même session du premier
  au dernier tour, identifiant masqué, lecture seule. Côté Codex, le filtre d'environnement a retiré
  `CLAUDE_CONFIG_DIR`, et le premier tour portait l'annonce puis la réponse (règle du dernier message
  confirmée).
- **Défaut du lot 2, trouvé par la partie 2, non corrigé, à trancher par le PO** : `open_questions`
  (provenance du cadrage) garde les `SANS_REPONSE` de la dernière proposition même après une reprise
  du cadrage (chez les deux outils, question répondue ensuite toujours citée). Deux options proposées :
  vider la liste à la reprise (recommandé, ~1 ligne + test) ou prendre les `QUESTIONS_OUVERTES` du
  dernier tour de F (change le sens du champ).
- **Marge de taille : ≈ 210 lignes** (+2 290 / 2 500, `src/` = 5 572, compteur tokenize recalé sur
  3 282 à `ba5c0a4` et 5 520 à `db37cc8`) ; façade + `gui/` inchangés (1 537 / 2 000).
- **Prochain** : décision du PO sur `open_questions`, puis le lot 6 (recette : critères §15, taille).

**Historique — Phase 5 (GUI V1) : lots 1 à 6 faits et commités (`581cbb3`), la phase est complète.**
Reste hors de ce plan, non engagé : le lot « Développement assisté » (§ Extension identifiée),
conditionné à une décision explicite du PO, et une éventuelle recherche externe, même condition.

**Repère laissé pour la prochaine session** :
- L'acceptation formelle de la conception GUI V1 elle-même (`decide … --accept` sur la collaboration
  `C:\Projets\essais-3-1\gui-v1\collab`) reste au PO — rappelée depuis le lot 1, jamais faite.
- Deux trouvailles non corrigées, à décision séparée du PO : `corpus.build()` avec une liste source
  vide ne crée pas son dossier avant d'y écrire le manifeste (lot 4, voir Errors Encountered) ; le
  plafond de 1 200 lignes logiques (façade + `gui/`) est à **1 195** après le lot 5 — non dépassé,
  mais tout ajout futur à cette surface (au-delà d'un correctif) le dépassera presque certainement.
- `iabinome/gui/views/creation.py` reste à 320 lignes effectives, sous le plafond de vue à 400,
  sans marge confortable si un futur lot y ajoute un champ.

- **Lot 6** (2026-09-23, non commité) : recette. `tests/test_gui_recette.py` — une collaboration
  créée par `facade.create_collaboration` (chemin GUI) menée à terme et acceptée par `cli.main`
  (chemin CLI), et l'inverse (créée par `cli.main("new", …)`, menée à terme par
  `Controller.start_run`, acceptée par `views.intervention.run`) : les deux sens du §15.4 prouvés en
  un seul dossier de collaboration, pas seulement en théorie parce que le code est partagé. Un
  verrou déjà tenu (PID vivant, fichier `verrou.json` construit à la main) fait échouer le fil sans
  toucher `etat.json` — `Controller.run_error` le rapporte. Un test parcourt tous les `ActionId` et
  vérifie que `views.intervention.label` en a un pour chacun (une addition future à l'énumération
  sans étiquette GUI se verrait tout de suite). Un balayage de `src/iabinome/gui/` recherche les
  mécanismes exclus du §13 (base de données, serveur HTTP, worker/planificateur, lancement détaché,
  budget/réservation/bail/worktree) — rien trouvé. Les huit scénarios du §15.3 restent couverts,
  chacun là où il a été écrit (création lot 4, exécution et fermeture lot 4/5, interventions lot 5) :
  ce lot ne les rejoue pas une seconde fois, il comble ce qui manquait spécifiquement à la recette
  (croisement CLI/GUI, verrou, parité des actions, périmètre).
  Validation : ruff, mypy strict, **692 passés / 2 ignorés**, scénario rc=0.

- **Lot 5** (2026-09-23, non commité) : interventions et décisions (§8). `iabinome/gui/views/
  intervention.py` (nouveau) : `run(parent, controller, path, action)` — une invite multiligne
  (`dialogs.prompt_text`, nouveau) si l'action en a besoin (`action.inputs`), une confirmation
  (§3.5) si elle peut appeler, puis l'application : `ACCEPT`/`ACCEPT_WITH_RESERVES`/`STOP` passent
  par `workflow.decide` en direct (local, synchrone, sous verrou — jamais un fil) ;
  `ANSWER_AND_RESUME`/`RETRY_CALL`/`REPROCESS_AND_RESUME`/`CORRECT` écrivent le texte saisi dans un
  fichier jetable puis appellent `Controller.start_run(path, intervention=…)` — le même fil que
  « créer et démarrer », étendu au lot 4 pour accepter une intervention, sans reconstruction. Aucune
  seconde table d'actions : `views/suivi.py` rend un bouton par élément de
  `snapshot.presentation.allowed_actions`, étiqueté par `intervention.label(action.id)`.
  `app._on_close`/`dialogs.choose` (nouveau, plus de deux issues) complètent le §9.3 : la troisième
  branche (« terminer l'appel courant, mettre en pause, puis fermer ») attend `has_active_run()`
  via `after()`, jamais un `join()` qui gèlerait Tk.
  Vérifié en réel (script hors suite) : bouton « Répondre et reprendre » sur un `WAITING_HUMAN`
  amené là par un vrai cycle de faux agents → reprise en fil secondaire → `AWAITING_APPROVAL` →
  bouton « Accepter cette version » depuis l'écran de suivi → « Version acceptée » affichée.
  Validation : ruff, mypy strict, **692 passés / 2 ignorés** (comptés avec le lot 6, fait dans la
  même session), scénario rc=0. Taille : +191 lignes effectives (dialogs.py étendu, intervention.py
  nouveau, controller.py et suivi.py étendus) ; le plafond GUI-spécifique de 1 200 lignes logiques
  est désormais à 1 195 — voir le repère ci-dessus.
  **Non fait, volontairement** : rien de nouveau — les huit scénarios de faux agents (§15.3) et la
  recette (§15.4-§15.6) sont le lot 6, fait dans la même session (voir plus haut).

- **Lot 4** (2026-09-23, non commité) : `facade.create_collaboration(request, *, adapters) ->
  CreationResult` — la création **partagée** (§6.1, §6.5) : `cli.cmd_new` délègue désormais à cette
  fonction (`_build_new` retiré de `cli.py`, `_write_json`/`_now` devenus inutiles, retirés aussi) ;
  `corpus.CorpusError` retiré de `cli._BORDER_ERRORS`, devenu inatteignable depuis la CLI (absorbé
  par la façade). `iabinome/registry.py` (nouveau) : `ADAPTERS`, une seule instanciation partagée par
  `cli.py` et `iabinome/gui/controller.py`/`views/creation.py` (évite deux sources de vérité sur les
  adaptateurs disponibles).
  `iabinome/gui/views/creation.py` (nouveau, remplace `views/stub.py`, retiré) : dossier, demande
  (saisie/import, provenance §6.2), type, agents, révisions, corpus (recherche seulement, AC-08),
  réglages avancés repliables (§6.3) et réglages du prochain lancement repliables (§6.4, délai
  jamais écrit dans `configuration.json`, AC-10) ; validation locale minimale (§6.5 niveau 1) puis
  autoritaire via la façade ; « Créer seulement » (AC-13) et « Créer et démarrer » (AC-14, dialogue
  de confirmation `iabinome/gui/dialogs.py` nommant agent/phase/délai/origine, AC-11).
  `iabinome.gui.controller.Controller` : **premier fil moteur côté GUI** (`start_run`, un thread
  daemon + `ExecutionControl`, comme `tests/test_control.py::_Threaded` côté tests) ; `is_running`/
  `run_error` pour l'écran de suivi, `has_active_run`/`interrupt_active_run` pour la fermeture.
  `views/suivi.py` : relit avec `owned_by_this_gui` quand cette fenêtre possède l'exécution, se
  reprogramme via `after()` toutes les 500 ms tant qu'elle tourne (§7.3), s'arrête d'elle-même à la
  fin. `app.py` : garde de fermeture partielle (§9.2-9.3, deux branches sur trois — voir Next Step).
  Vérifié en réel (script hors suite) : formulaire → confirmation → création → suivi → cycle en fil
  secondaire avec de faux agents → « Cycle terminé — décision requise », 2 appels lancés.
  Validation : ruff, mypy strict, **672 passés / 2 ignorés**, scénario rc=0. Taille : 469 lignes
  effectives ajoutées ; voir Budget de taille ci-dessus pour le cumul et la décision du PO.
  **Non fait, volontairement** : répondre/relancer/retraiter/corriger/accepter/arrêter depuis la GUI
  (lot 5) ; la branche de fermeture « pause puis fermeture » (lot 5, voir ci-dessus).

- **Lot 3** (2026-09-23, non commité) : `iabinome/facade.py` — `inspect_collaboration(path,
  *, owned_by_this_gui=False, runner_alive=None) -> CollaborationSnapshot` (§10.3 : décision
  courante, incident, délai résolu, observation d'exécution, présentation — labels de statut/phase/
  activité, `allowed_actions` repris tel quel de `decisions.allowed_actions`, documents lisibles
  existants, `phase_steps` pour la barre de progression §7.1, `next_action_text`). Relit
  intégralement le dossier à chaque appel, jamais de cache (§3.3) ; `InspectionError` nomme un
  dossier illisible sans le réparer (§5.1).
  `iabinome/gui/` : `recents.py` (préférences non métier, `~/.dialogforge/recents.json` — **décidé
  par le PO** : sous-commande `dialogforge gui`, pas de script séparé ; ce chemin, pas un autre),
  `controller.py` (navigation dans une seule fenêtre, pas de fil moteur ni d'`ExecutionControl` :
  rien ne les consomme avant le lot 5), `app.py` (point d'entrée `run()`), `views/accueil.py`
  (créer/ouvrir/récents, AC-01 à AC-05), `views/suivi.py` (lecture seule : statut, phase,
  progression, activité honnête, décision, documents lisibles, `Actualiser` — AC-15 à AC-17, AC-20,
  AC-21, AC-30, AC-33), `views/stub.py` (écran de création nommé « lot 4 », pas un bouton sans
  effet). `cli.py` : sous-commande `gui` (`cmd_gui`, import de `tkinter` différé dans la fonction —
  la CLI n'en dépend pas autrement) ; `docs/COMMANDES.md` à jour (neuf commandes).
  Testé sans Tk (`tests/test_facade.py`, `tests/test_gui_recents.py`) et avec une racine Tk masquée
  (`tests/test_gui_views.py`, boutons invoqués par `.invoke()`, dialogue de choix de dossier
  moqué). Vérifié en réel : la collaboration produite et acceptée par `reference/cycle_sans_
  fournisseur.py` s'ouvre dans la GUI et affiche bien « Version acceptée » (§15.4, compatibilité
  CLI→GUI). Taille : 474 lignes effectives ajoutées (façade + `gui/`), 3 379 → 3 851 dans `src/`
  (plafond +900 pour l'ensemble de la GUI). Validation : ruff, mypy strict, **637 passés / 2
  ignorés**, scénario rc=0.
  **Non fait, volontairement** : rien n'appelle `workflow.run` depuis la GUI (répondre, relancer,
  retraiter, corriger, décider, créer restent lots 4-5) ; pas de suppression des récents (seule
  « Afficher dans le dossier » et « Ouvrir » existent, §5.1 n'en demande pas d'autre).

- **Lot 1** : `decisions.allowed_actions` = la table d'actions ; phrases CLI inchangées
  (`tests/test_actions.py`) ; `settings.resolve_timeout` rend valeur et origine. Détail :
  `progress.md`.
- **Lot 2** : `transport.ExecutionControl` (deux `Event`) remplace le rappel `pause` du moteur et le
  `KeyboardInterrupt` du Ctrl+C (`6c77953`). Le transport surveille `interrupt_requested` dans sa boucle
  d'attente ; le moteur arrête à la frontière d'appel sur l'une ou l'autre demande, et lève
  `workflow.Stopped` si l'interruption est posée avant qu'un appel ne parte (rien de lancé) ; le
  Ctrl+C de la CLI pose les deux demandes (`cli._CtrlC`), codes de sortie inchangés (6 = pause ou
  arrêt hors appel, 3 = appel interrompu). Le `except KeyboardInterrupt` du transport reste en filet
  (Ctrl+C brut sans la CLI : l'arbre est quand même terminé). Testé moteur **dans un fil
  secondaire** (`tests/test_control.py`).
- Taille cumulée : 3 282 → 3 379 lignes de code effectif (+97 ; plafond +900). Validation : ruff,
  mypy strict, **602 passés / 2 ignorés**, scénario rc=0.
- **Rappel** : l'acceptation formelle du livrable GUI (`decide … --accept`) reste au PO.
- **Lot 3 — à savoir** : la façade §10.1 (`inspect_collaboration`, instantané §10.3) se construit
  avec l'écran de suivi qui l'appelle ; les récents vivent dans un fichier de préférences non métier
  (§5.2), jamais lu par une commande métier.

**Historique — 2026-09-22 : renommage de la surface exposée fait et commité (`9a9824c`).**

La commande est désormais `dialogforge` ; le paquet reste `iabinome`, délibérément. Validation
complète verte (ruff, mypy strict, **580 tests / 2 ignorés**, scénario rc=0, `dialogforge --help`
vérifié après réinstallation). Détail dans `progress.md`.

**À savoir pour la prochaine session** : le `.venv` a été réinstallé (`pip uninstall iabinome`, puis
`pip install -e .`) — la commande `dialogforge` n'existe que dans un environnement réinstallé depuis
ce commit.

La documentation est alignée sur le code de `v0.1.0` : surface CLI vérifiée une à une, sept
affirmations fausses corrigées, `LIMITES.md` condensé. **Le dépassement des ~1 500 lignes est assumé
par le PO** (3 253 lignes de code dans `src/`) — chiffre porté dans `CLAUDE.md`,
`docs/DEVELOPPEMENT.md` et `project/RULES.md`, note datée validée sous la règle 1 de `POURQUOI.md`.
Détail exhaustif dans `progress.md`, session « revue de documentation contre le code ».

1. **Renommage — tranché autrement, et fait le 2026-09-22.** Le PO a recadré la question : l'enjeu
   n'est pas de renommer le code mais que **l'utilisateur ne voie jamais IAbinome**. Seule la surface
   exposée a donc changé — commande `dialogforge`, aide, nom de distribution, `dialogforge.toml` /
   `~/.dialogforge/reglages.toml` (anciens noms encore lus, avec message), préfixe du dossier jetable,
   documentation. **Le paquet reste `iabinome`**, sans échéance : voir `docs/DEVELOPPEMENT.md`.
   **Reste ouvert, à décider séparément** : les balises `IABINOME:DOCUMENT` / `QUESTION` / `REPONSES`,
   visibles dans `echanges/`. Les changer est un changement de contrat (phase à deux balises pour ne
   pas casser `resume --reprocess` ni les revues rejouées par `tests/test_objections.py`).
2. **Lot 4 — Développement assisté** : seule extension déjà nommée dans ce plan (§ Extension identifiée),
   conditionnée à une décision explicite du PO. Ne pas l'ouvrir sans elle.

**Historique — 2026-09-22 — J3 atteint : première livraison utilisable, `v0.1.0`.**

- Lot 3 complet : 3.1 (protocole + qualification Windows + corroboration réelle), 3.2 (trois tâches
  acceptées), 3.3 (limites documentées, validation complète verte, installation propre vérifiée,
  version taguée). Détail des trois tâches et de la preuve de lecture ci-dessous, inchangé.

**Historique — 2026-09-22, avant J3 : les 3 tâches représentatives de 3.2 faites et acceptées par le PO.**

- Nextcloud, déploiement du client de bureau (serveur 33 → 34) : cycle complet, 4 appels, ~6 min 15 s,
  2 désaccords `NOTE` non bloquants restés ouverts en connaissance de cause, `ACCEPTE` le 2026-09-22.
  Collaboration hors dépôt : `C:\Projets\essais-3-1\nextcloud-clients`.
- Pièges à souris (conception courte, guide de décision) : cycle + correction ciblée + complément de
  recherche demandé **après** une première acceptation (GPS centimétrique externe), 8 appels sur 3
  tours, `ACCEPTE` final le 2026-09-22, sans réserve. Refus par construction de changer de modèle
  (Sol) en cours de collaboration — `configuration.json` fixé à `new`, sans option sur
  `decide`/`resume`. **Constat** : `decide --correct` n'est pas fermé par une acceptation antérieure
  (voulu par la conception ; confirmé en réel pour la première fois). Collaboration hors dépôt :
  `C:\Projets\essais-3-1\pieges-souris`.
- Révision d'un document existant (note technique Nextcloud/Apache/Docker réelle, anonymisée avant
  dépôt dans le corpus) : corpus à un fichier, `--kind conception`, **web fermé** — premier essai réel
  de ce réglage par défaut sur 3.2. 4 appels, ~6 min 15 s, **B a accepté dès le premier tour, zéro
  désaccord** ; 6 objections soulevées et résolues par A, dont un diagnostic de permissions lui-même
  corrigé (le mode affiché prouvait déjà l'accès, le vrai test doit s'exécuter sous `www-data`).
  `ACCEPTE` le 2026-09-22T15:22:18Z. Collaboration hors dépôt :
  `C:\Projets\essais-3-1\revision-nextcloud\collab`.
- **Bilan 3.2** : 16 appels au total sur les trois tâches, aucun défaut reproductible de perte de
  réponse, de version ou de reprise. **La révision du stockage externe corrobore la qualification du
  21, en usage réel** : Codex a lu le corpus (un fichier, copié dans `corpus/fichiers/`) par son
  propre outil — `Get-ChildItem` puis `Get-Content -LiteralPath … -Raw`, « succeeded in 917ms »,
  contenu exact retourné, dans le dossier jetable du produit. Détail et citation exacte dans
  `docs/LIMITES.md` §2. Cela ne teste pas la lecture d'un chemin hors du corpus (confinement général
  toujours non mesuré). Seuls incidents : deux erreurs humaines (chemin relatif, frappe sans Entrée),
  sans effet sur l'état des collaborations.
- **Commité** : correction Windows (`1a7aa22`) et documentation/plan du protocole 3.1, de la
  qualification et des trois tâches de 3.2 (`052678f`). Arbre propre, rien en attente.
- **Reste pour clore la phase 4 (lot 3)** : 3.3 — `docs/LIMITES.md` mis à jour (3.1 et 3.2, avec la
  preuve `Get-Content` du 22) ; reste la validation complète sur le commit livré, l'installation en
  environnement propre, et marquer la version.

**Historique — Reprise au 2026-09-21 — correction Windows qualifiée, non commitée.**

- Le PO a validé le recentrage décrit dans `astra/07_recentrage_simplicite.md` et un unique appel fournisseur, désormais consommé.
- `CodexAdapter` sélectionne `windows.sandbox=elevated` sous Windows. Backend déjà installé requis ; autres protections et plateformes inchangées.
- Codex 0.155.0 / Sol : lecture du marqueur par outil réussie, écriture témoin refusée, empreintes inchangées, 19,187 s. Essai de fichiers témoins via l'adaptateur et le transport, pas un nouveau cycle A/B complet. Détail : fin de `progress.md`.
- Pas de garantie générale d'inaccessibilité en lecture du disque ; pas de profils personnalisés, prévol système générique ni injection du corpus. Les anciennes hypothèses de cause restent historiques, pas une cause unique démontrée.
- Préserver l'arbre sale, notamment les modifications antérieures : utiliser `git status`, pas un compteur figé. Aucun commit ni nouvel appel fournisseur sans demande.
- Validations locales et revue terminées : Ruff, mypy strict, scénario rc=0 ; suite 570 réussis / 8 ignorés, puis 41 réussis sur PWF et documentation avec Git Bash dans le PATH (les 6 tests PWF initialement ignorés passent). Seuls les 2 tests de liens symboliques restent ignorés. Revenir aux usages du lot 3.2 (Nextcloud / UrBackup proposés, non démarrés), après décision du PO sur la suite ; ne pas rouvrir une campagne de confinement.
- Les résultats du protocole 3.1 du 20 septembre restent dans le journal ; l'essai du 21 complète la lecture seule. Aucun autre point n'est déclaré acquis par extension.
- Pour une session Claude avec injection PWF qualifiée : `.\tools\claude-pwf.ps1`.

**J1 validé par le PO le 2026-09-19. LOT 2 OUVERT le 2026-09-19** (autorisation du PO). Lot 1 : 1.1
`b0dc6a3`, 1.2 `2b5ae15`, 1.3 `25ab101`, 1.4 `6cf7aa4`.

**2.1 est fait** (2026-09-19), validé (ciblé puis porte complète) et commité (`feat: ... (2.1)`, voir
`git log`). Limite à connaître : après un crash, « appel non lancé » ne peut pas être **prouvé**
(`pid.txt` s'écrit après `Popen`) ; seul `LAUNCH_FAILED` (échec de `Popen` observé) l'est. Le reste est
« inconnu », dit comme tel.

**2.2 est fait** (rouvert le 2026-09-19 : la validation du PO a trouvé une fuite réelle — l'hôte
Codex transmet `CODEX_SESSION_ID`, `CODEX_THREAD_ID`, `CODEX_PERMISSION_PROFILE`, que `clean_env`
ne filtrait pas ; corrigé, 9 contre-épreuves, 483 tests). Le PO a enchaîné (« on continue avec le
point suivant ») : **pris comme re-validation de la correction — à infirmer si ce n'en était pas
une.** **Commité** (`feat: ... (2.2)`, voir `git log`). Agents dans un
**dossier jetable hors de la collaboration** (copie du corpus seule), **environnement filtré**
(liste de refus nominative), `Capabilities.enforces_read_only`/`fresh_session` exigées au prévol,
corpus modifié pendant l'appel = `SOURCES_MODIFIED`. **Aucune garantie de CLI réelle** : les
drapeaux sont lus dans `--help`, jamais éprouvés — `reference/FRONTIERE_ROLES.md` liste ce qui est
obtenu, constaté seulement, et à vérifier au lot 3.

**2.3 est fait** (2026-09-19, « on continue avec le point suivant »), **commité** (`feat: ... (2.3)`,
voir `git log`) : `planlink.py`,
commande `plan <dossier> [--link ID [--plan-root DIR] | --unlink]`, liaison dans `plan.json` (fichier
à part, jamais lu par le cycle). Le résolveur public rend **toujours 0** : sortie vide = refus
(mesuré). Le plan reste seul propriétaire ; l'outil imprime un résumé à reporter **à la main**.

**Le lot 2 est complet** (2.1, 2.2, 2.3). **Amendement du plan validé** (PO, 2026-09-19) : la liaison
est dans `plan.json`, pas dans `configuration.json` (schéma strict et opérationnel ; `plan.json`
réduit le couplage et se retire sans toucher à l'état) ; le plan de mise en œuvre, point 2.3, est
amendé en conséquence. **Il n'existe plus d'écart ouvert sur 2.3.** **J2 atteint et validé par le PO le 2026-09-19** ; « les profils à vérifier avec les CLI réelles sont
identifiés » = `FRONTIERE_ROLES.md`.
**Lot 3 ouvert par le PO le 2026-09-19 ; 3.1 EN COURS.** Deux cycles réels (Codex/Claude et l'inverse) ont
tourné sans incident ; le PO a tranché les trois constats (web facultatif et fermé par défaut, effort validé
par adaptateur, environnement par fournisseur), commités et validés par Codex le 2026-09-20 (hash = référence
des prochains essais, voir `git log`). **3.1 se ferme après le petit protocole fournisseur** (points 7 à 10 de
`reference/FRONTIERE_ROLES.md`), **rédigé et figé dans `reference/PROTOCOLE_FOURNISSEUR_3_1.md`**
(version 2, revue Codex intégrée ; **lancé par le PO le 2026-09-20 : points 7 à 10 acquis, défaut de lecture du corpus par Codex ouvert**, voir REPRISE) — pas de nouveau cycle éditorial. Il a consommé du quota : lancé par le PO,
sur son autorisation. Les garanties des CLI réelles ne sont acquises que point par point, à mesure qu'elles
sont mesurées.

Lancer les sessions de développement par `.\tools\claude-pwf.ps1` : c'est la seule voie où
l'injection automatique du plan est qualifiée.

## Current Phase
Phase 6 (cadrage avec agent F) — ouverte le 2026-09-24. Phase 5 (GUI V1) complète et commitée
(`581cbb3`). Phase 4 complète (J3, `v0.1.0`).

## Plan de référence
`C:\Projets\DialogForge_Next\astra\06_plan_mise_en_oeuvre.md`. Ce plan PWF est le **seul** suivi
d'avancement : on ne coche pas une seconde liste dans `astra/`.

## Phases

### Phase 1: Lot 0 — Socle et PWF de développement
- [x] 0.1 Dépôt isolé : clone d'IAbinome au commit `4a11cc7`, branche `v2-socle`, remote retiré
- [x] 0.1 Origine du code et périmètre de la première livraison documentés dans le README
- [x] 0.2 Environnement Python propre et versions d'outils relevées
- [x] 0.2 Référence technique verte : ruff, mypy --strict, 302 tests + 2 ignorés documentés
- [x] 0.2 Cycle complet avec faux adaptateurs, rejouable sans fournisseur
- [x] 0.2 Vérifié par leurres : les vraies CLI du PATH ne sont jamais appelées
- [x] 0.3 PWF installé et version consignée (3.20.1, commit `faf1a15`)
- [x] 0.3 Plan nommé créé avec les scripts amont, lots 0 à 3 inscrits
- [x] 0.3 Racine et plan sélectionnés explicitement, résolution et ambiguïté éprouvées
- [x] 0.3 Reprise vérifiée **en session** : bonne prochaine étape retrouvée, sélection erronée refusée
- [x] 0.3 Injection automatique par les hooks : **prouvée** avec le plugin local épinglé
      (`SessionStart` au démarrage et après `/compact`, `UserPromptSubmit`, `PreToolUse`)
- **Status:** complete
- **Jalon :** **J0 atteint** le 2026-09-19. Injection automatique prouvée par les enregistrements
  de l'hôte (`reference/COMPTE_RENDU_J0.md` §8), récupération après compactage comprise.
  Limites résiduelles, ni validées ni infirmées : `PostToolUse` et `PreCompact` non observés.
  Portée : vaut pour une session lancée par `tools/claude-pwf.ps1`, pas pour un `claude` ordinaire.

### Phase 2: Lot 1 — Parcours documentaire complet
- [x] 1.1 Format court de demande, fichier direct ou cadrage guidé, provenance conservée
- [x] 1.2 Objections et dispositions : énoncé, réponse de A, disposition et justification distincts
- [x] 1.2 Réponse exigée pour chaque objection ouverte ; identifiants absents ou dupliqués détectés
- [x] 1.3 Boucle : A → B → correction A → relecture ciblée B → décision humaine
- [x] 1.3 Promotion de la version examinée à la place de la finalisation qui réécrit librement
- [x] 1.4 Résultat, réserves, prochaine action ; acceptation, réserve, correction ciblée, arrêt
- [x] 1.4 Décision datée portant sur une version précise ; « terminé » n'est pas « accepté »
- **Status:** complete — 1.1 à 1.4 faits
- **Jalon :** J1 — version fonctionnelle avec faux agents. **Validé par le PO le 2026-09-19** (critères) :
  parcours complet sans copier-coller (`reference/cycle_sans_fournisseur.py`), cas sans objection,
  avec correction, avec désaccord (plafond) et avec question humaine couverts par les tests, garanties
  de reprise héritées toujours vertes.

### Phase 3: Lot 2 — Robustesse et liaison PWF du produit
- [x] 2.1 Reprise après résultat reçu non appliqué ; retraitement local de l'interprétation
- [x] 2.1 Distinguer réponse mal interprétée, appel non lancé, issue inconnue ; verrou non effacé
- [x] 2.2 Paquet B minimal ; session reviewer fraîche ; capacités effectives par profil vérifiées
- [x] 2.2 Essai sur dossier jetable : sources non modifiées, journal de A non injecté chez B
- [x] 2.3 Liaison facultative à un plan PWF via les scripts publics ; sortie vide traitée
- [x] 2.3 Un seul propriétaire du plan ; fonctionnement documentaire vérifié sans liaison PWF
- **Status:** complete — 2.1, 2.2 et 2.3 faits et commités ; J2 atteint et validé par le PO le 2026-09-19
- **Jalon :** **J2 atteint et validé par le PO le 2026-09-19** — version candidate aux essais réels.

### Phase 4: Lot 3 — Essais réels et première livraison
- [x] 3.1 Versions des CLI et modèles relevées ; essai de petite taille en collaboration jetable
      *(versions : Claude 2.1.278, Codex 0.155.0 — `FRONTIERE_ROLES.md`. Petit protocole du 2026-09-20
      (deux cycles réels, un par sens A/B) ; défaut de lecture Codex qualifié sans quota puis corrigé
      le 21 (backend Windows `elevated`, essai ciblé concluant) ; corroboré en cycle A/B complet le 22
      (lot 3.2, `Get-Content` réussi sur un vrai corpus). Commité `1a7aa22` + `052678f`.)*
- [x] 3.2 Trois tâches représentatives : conception courte, synthèse sur corpus, révision
      *(2026-09-22 : Nextcloud clients, pièges à souris, révision stockage externe — 16 appels,
      toutes `ACCEPTE`, aucun défaut reproductible de perte de réponse/version/reprise. Détail dans
      `progress.md`.)*
- [x] 3.3 Aide courte, exemples sans donnée personnelle, limites effectives documentées
      *(2026-09-20, commité `5542ee8` : aide `--help`, `exemples/`, `docs/` et README faits ;
      `docs/LIMITES.md` mis à jour le 22 avec 3.1, 3.2 et la preuve `Get-Content`, commité `052678f` +
      `5cd91e9`.)*
- [x] 3.3 Validation complète sur le commit livré, installation en environnement propre, version marquée
      *(2026-09-22, sur `5cd91e9` : ruff et mypy --strict verts ; pytest 576 passed, 2 skipped (privilège
      de lien symbolique absent) ; scénario de référence rc=0 ; `git diff --check` sans erreur ;
      installation propre (`pip install -e .`, zéro dépendance) vérifiée dans un venv neuf, hors dépôt ;
      taggué `v0.1.0`.)*
- **Status:** complete — 3.1, 3.2 et 3.3 faits ; J3 atteint
- **Jalon :** **J3 atteint le 2026-09-22** — première livraison utilisable, `v0.1.0`.

### Phase 5: GUI V1 — ouverte par le PO le 2026-09-23
Conception : `conception/GUI_V1.md`, copie octet pour octet du livrable de la collaboration
`C:\Projets\essais-3-1\gui-v1\collab` (sha256 `8c879088…3ea39`, cycle clos, B `ACCEPTER`, 3 `NOTE`
ouvertes). Le PO l'a retenue comme plan à mettre en œuvre ; son acceptation formelle (`decide`)
lui appartient. Plafonds (§11) : **1 200 lignes logiques de production, +2 500 lignes nettes dans
`src/`** (porté de +900 à +2 500 par le PO le 2026-09-23 après le lot 4 — voir Decisions Made) —
référence de mesure : 3 274 lignes de code effectif juste avant l'ouverture de la phase 5.
- [x] 5.1 Lot 1 — actions structurées (`ActionId`, `AllowedAction`), textes CLI dérivés, parité ;
      résolution du délai centralisée *(2026-09-23, `38abbca` ; résultats structurés de la
      façade reportés aux lots qui les consomment — voir Decisions Made)*
- [x] 5.2 Lot 2 — `ExecutionControl` : transport, workflow, Ctrl+C de la CLI (la pause existe déjà,
      voir `B-pause-010`) *(2026-09-23, `6c77953`)*
- [x] 5.3 Lot 3 — accueil, récents non métier, ouverture, suivi en lecture seule, sous-état accepté
      *(2026-09-23, commité `223c04a`/`89ba64b` : `iabinome/facade.py`, `iabinome/gui/`, sous-commande
      `dialogforge gui` — voir Decisions Made)*
- [x] 5.4 Lot 4 — création : formulaire, provenance compatible, configuration/lancement séparés
      *(2026-09-23, commité `78399c0`/`414bc95` : `facade.create_collaboration`, `views/creation.py`,
      premier fil moteur du contrôleur — voir Decisions Made)*
- [x] 5.5 Lot 5 — interventions et décisions *(2026-09-23, non commité : `views/intervention.py`,
      `dialogs.prompt_text`/`choose`, troisième branche de fermeture — voir Next Step)*
- [x] 5.6 Lot 6 — recette : faux agents, compatibilité CLI/GUI, atomicité, périmètre, taille
      *(2026-09-23, non commité : `tests/test_gui_recette.py` — voir Next Step)*
- **Status:** complete — lots 1 à 6 faits ; 5.5 et 5.6 non commités au moment d'écrire ceci
- **Jalon :** **Les six lots de la GUI V1 sont faits le 2026-09-23.** L'acceptation formelle de la
  conception elle-même (`decide … --accept` sur `C:\Projets\essais-3-1\gui-v1\collab`) reste due au
  PO, rappelée depuis le lot 1 — « fait » ne veut pas dire « accepté » (`decisions.py`, la même
  règle que le moteur applique à tout livrable).

### Phase 6: Cadrage avec agent F — ouverte par le PO le 2026-09-24
Conception : `conception/CADRAGE_AGENT.md`, copie octet pour octet du livrable de la collaboration
`C:\Projets\essais-3-1\Creation-prompt-2` (sha256 `03711c71…935cdd`), **accepté par le PO le
2026-09-24** (`decisions.json`, séquence 2), suivie des amendements A1-A3 du même jour (voir
Decisions Made). Plafonds (§13, remesurés au départ comme il l'exige) : croissance nette de `src/`
≤ +2 500 depuis `ba5c0a4` — **+1 237 consommées au départ de la phase (4 519 lignes de code
effectif, compteur tokenize sans commentaires ni docstrings), marge ≈ 1 263** (et non les 1 454 du
§13, antérieurs au lot 5) ; façade + `gui/` ≤ 2 000 lignes logiques — **1 190 au départ**. Estimation
de la phase : 900 à 1 000 lignes.
- [x] 6.1 Lot 1 — contrat de session : `AgentPurpose`, `FramingSessionSpec`, capacité
      `supports_persistent_framing_session`, session par reprise d'identifiant sur le transport
      commun, prévol de F, faux adaptateur à session en mémoire (tests §14.1 et §14.5 qui s'y
      rattachent) *(2026-09-24, `feec971` : `framing.py`, `tests/test_framing_session.py` ;
      708 passés / 2 ignorés ; +145 lignes)*
- [x] 6.2 Lot 2 — `framing.py` : dossier jetable, protocole `CADRAGE_QUESTION`/`CADRAGE_PRET`/
      `DEMANDE`, compteur de groupe (A1), transcription, `SOURCES_MODIFIED` ; `prompts.build_framing_*`
      (A2) ; `demande.validate_framed` (§14.2 à §14.4) *(2026-09-24, commité avec le lot 3 : 727 passés /
      2 ignorés ; +289 lignes)*
- [x] 6.3 Lot 3 — création : `CreationRequest.framing`/`prepared_corpus`, artefacts `cadrage/`,
      provenances, `configuration.framing_agent` ; CLI `new --cadrer-avec-agent` et aides (§14.6,
      §14.8). *(2026-09-24, commité : `framing_cli.py`, `facade.check_creation`/`_write_framing` ;
      738 passés / 2 ignorés ; +255 lignes. `configuration.framing_agent` non écrit — facultatif au
      §9.4. `corpus.build()` sur liste vide non rencontré : `prepare` crée le dossier avant)*
- [x] 6.4 Lot 4 — adaptateurs réels (reprise par identifiant) + protocole de caractérisation de la
      lecture seule en reprise, **exécuté par le PO** (aucun appel réel de Claude)
      *(2026-09-24 : protocole écrit. 2026-09-25 : partie 1 lancée par le PO, conforme chez les deux
      outils ; adaptateurs écrits, capacité à vrai ; 758 passés / 2 ignorés ; +52 lignes ; commité `028a1dd`, `ec0c7a6`.
      2026-09-25 : partie 2 lancée par le PO, un cadrage réel par outil, conforme ; défaut `open_questions`
      du lot 2 trouvé, non corrigé)*
- [x] 6.5 Lot 5 — GUI : mode « Cadrer avec un agent », modale, unique fil moteur (§4, §14.7)
      *(2026-09-24, `c718055` : `gui/views/cadrage.py`, contrôleur, écran de création ;
      751 passés / 2 ignorés ; +310 lignes)*
- [ ] 6.6 Lot 6 — recette : critères §15, taille remesurée
- **Status:** in_progress — lots 1 à 5 faits ; reste le lot 6 (recette)

## Extension identifiée (hors phases)

**Lot 4 — Développement assisté.** Spécification acceptée exportée vers l'agent de développement,
paquet de revue à partir d'une base Git identifiée, boucle de dispositions réemployée, essai sur
une modification limitée et réversible. **Ne s'ouvre qu'après J3** et n'introduit ni worker, ni
commit, ni déploiement automatique dans le moteur documentaire.

Également conditionnelle après J3, et non engagée : recherche externe. (L'interface graphique
légère est engagée depuis le 2026-09-23 : phase 5.)

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Dossier `C:\Projets\DialogForge_2` | Nom retenu par le PO le 2026-09-18 ; le plan `astra/` proposait `DialogForge_V2`. `C:\Projets\DialogForge` est la plateforme historique, source de l'étude : intouchée |
| Départ au commit `4a11cc7` d'IAbinome | HEAD d'IAbinome **est** le commit de référence de l'étude : écart nul, aucun arbitrage à rendre |
| Remote `origin` retiré du clone | Rend impossible une écriture accidentelle vers IAbinome ; aucune publication distante n'est utile au lot 0 |
| Package encore nommé `iabinome` | Lot 0 vérifie le réemploi ; renommer maintenant mélangerait changement fonctionnel et renommage |
| PWF en skill autonome épinglé, pas en plugin marketplace | Le plan exige une version consignée ; la route marketplace suit `master` et mettrait à jour toute seule. Contrepartie acceptée : pas de hook `SessionStart`, pas de commandes `/plan-*` |
| Cadrage guidé = questionnaire de terminal, **sans appel de modèle** (1.1, 2026-09-19) | « Ne pas ajouter d'appel de cadrage quand les informations suffisent » : le plus sûr est de n'en ajouter aucun. La « question utile » sur ambiguïté existe déjà — A rend `IABINOME:QUESTION`, `resume --answer` reprend. **Condition de réouverture** : des essais réels (lot 3) où le questionnaire laisse passer des demandes que A doit ensuite questionner systématiquement |
| Le format court est un repère, pas une porte (1.1) | Une demande libre reste acceptée ; `new` nomme les sections manquantes sur `stderr`. Refuser ajouterait un contrôle qui ne compense aucun défaut mesuré (`POURQUOI.md` règles 2 et 3) |
| `--answer` **complète** la demande, il ne la remplace pas (1.1, décision du PO le 2026-09-19) | Consigner `sections_retirees` constatait une perte sans l'empêcher. Désormais `demande.md` reprend le texte existant **intact** puis la réponse sous « Précisions n°K » : une version complète, unique autorité (motif « pas de seconde autorité » préservé), ancienne version archivée, provenance consignée. Le numéro se déduit du texte, pas de l'horloge, pour que le rejeu retrouve la même empreinte. **Remplacement intégral : hors de ce changement**, à rendre plus tard explicite et distinct. Conception amendée dans `CONCEPTION_FINALE.md` §2 |
| Revue B **v2** : `justification` distincte, énoncé initial immuable, fermeture non justifiée = reste ouverte (1.2) | Mesuré sur la revue réelle du 2026-09-05 : B réécrit l'énoncé de ses 7 constats pour y dire « désormais résolu ». Le programme garde l'initial et reprend la réécriture comme justification (sans nouvel appel). La v1 reste lisible (revues historiques). Le sens sûr seulement : une omission laisse ouvert, ne ferme jamais |
| A **répond** à chaque objection ouverte, en révision (1.2) | Bloc `IABINOME:REPONSES` après le document libre ; `CORRIGE`/`CONTESTE`/`REPORTE`/`ARBITRAGE`, justification exigée sauf `CORRIGE`. Réponse absente, dupliquée ou inconnue = `CONTRACT_ERROR` (relançable). **Choix rigoureux, à mesurer au lot 3** : il peut coûter un appel payé si A oublie le bloc ; le préambule autour du JSON, lui, est récupéré sans appel. `FINAL_A` non touché (1.3) |
| Registre des objections **relu**, pas stocké (1.2) | `objections.ledger()` assemble `critique-B.json` et `reponses-A.json` : aucune seconde vérité. Servira le bilan de 1.4 |
| **Promotion à la place de `FINAL_A`** (1.3, autorisé par le PO le 2026-09-19) | `ACCEPTER`, ou plafond atteint, mène directement à `CLOSED` : le document que B vient d'examiner est copié octet pour octet dans `livrables/version_finale.md`, et `livrables/bilan.md` (écrit par le programme, sans modèle) porte les empreintes de la demande, du livrable et de la revue et les désaccords restants. **Un appel payant de moins par cycle** (A=2, B=2 au lieu de A=3, B=2). `Phase.FINAL_A`, `build_final` et le gabarit sont supprimés : un état `FINAL_A` d'une collaboration ancienne est refusé au chargement (aucune collaboration V2 n'existe). « Correction substantielle non revue » ne peut plus naître du cycle : A n'a plus d'appel après B |
| **Relecture ciblée** par le prompt, pas par le programme (1.3) | Dès `revision >= 1`, B ne relit que les objections traitées et les régressions ; une nouvelle observation se note en `NOTE`. Le programme ne juge pas si une remarque est « hors périmètre » (§6 : il ne décide pas sur les sévérités) : la transition reste `ACCEPTER`/`REVISER` de B et le plafond. **À mesurer au lot 3** : si B ouvre des tours pour des remarques nouvelles malgré la consigne |
| Tour supplémentaire après le plafond **renvoyé à 1.4** | C'est une décision humaine (« correction ciblée »), pas une transition automatique. Le plafond présente les désaccords ; l'humain décide |
| **Décision humaine = fichier daté, sur une version précise ; acceptation ≠ statut** (1.4, autorisé par le PO le 2026-09-19) | `decisions.json` (ajouté à chaque décision, rejouable : la même décision sur la même version n'est pas consignée deux fois) porte les empreintes du livrable, de la revue et de la demande. Accepter ne change pas le statut du moteur (« terminé » reste `AWAITING_APPROVAL`). Une décision dont la version a changé le dit. `Status.STOPPED` (arrêt humain) est ajouté |
| **Correction ciblée = intervention du moteur** (`Correct`, 1.4) | Elle réutilise le chemin de `--answer` : sous verrou, préflight, rejouable après arrêt brutal, sans appel repayé. L'instruction complète `demande.md` (unique autorité), un tour de révision s'ouvre **au-delà du plafond**, la décision est consignée avant l'état. A repart du **corps** du livrable, sans l'en-tête |
| Trois commandes ajoutées : `show`, `decide`, `list` (1.4) | La conception disait « quatre commandes » ; la validation de 1.4 (résultat lisible, décision utilisable, liste sans index) ne se tient pas avec `status` seul. Amendement daté dans `CONCEPTION_FINALE.md` §7. `list` calcule depuis les dossiers |
| **`resume --reprocess` : retraitement local d'une réponse déjà payée** (2.1) | Sur `CONTRACT_ERROR`/`DECODE_FAILED`, la seule sortie était un nouvel appel payant. Le retraitement passe `ERROR` → `RUNNING` avec l'appel courant : le chemin de reprise ordinaire, qui confronte le dossier aux empreintes avant de relire. Motif humain exigé, opération tracée (`retraitements.jsonl`), données brutes intactes, un échec reste `ERROR` |
| **Catalogue des incidents** (`incidents.py`, 2.1) | « Payé ? » ∈ non / peut-être / inconnu / oui, sens, options. Pour `CLI_FAILED`, le message de l'outil est cité tel quel ; aucun coût, aucune heure de reprise déduits |
| **Ctrl+C à deux temps** (2.1) | Premier = pause à la frontière d'appel (`workflow.run(pause=…)`, `READY`, code 6) ; second = arrêt immédiat (`INTERRUPTED_BY_USER`). Pas de worker, pas de tâche planifiée : c'est le terminal de l'humain |
| Verrou : rien de changé (2.1) | L'exclusion et le refus d'un verrou ambigu étaient déjà là ; ajout de tests au niveau CLI (détenteur vivant, verrou illisible : jamais effacé) |
| **Documentation utilisateur** : README court + `docs/` (5 pages) + `exemples/` + `--help` (3.3 partiel, PO, 2026-09-20) | Le README de 350 lignes mêlait mode d'emploi, justification et historique mesuré. Le PO a confirmé : ouvrir 3.3 dans ces termes, retirer l'historique et l'origine du code du README (passés dans `docs/DEVELOPPEMENT.md`), et **un test de cohérence** `tests/test_docs.py` (option ↔ section de sa commande, clé de réglage, aide, exemples rejoués par `new`, liens et ancres) — un contrôle de plus, **accepté en connaissance de cause** (`POURQUOI.md` règle 2), qui ne vérifie pas que le texte est *vrai*. Le renommage en DialogForge est reporté à la **fin du développement V2** : la documentation écrit `python -m iabinome` partout |
| **Levée de l'interdit « Pas de GUI », pour la seule GUI V1** (PO, 2026-09-23) | Le PO a demandé la mise en œuvre de la conception GUI V1 et choisi que la décision soit écrite dans `CLAUDE.md` §2, `project/RULES.md` et ici. Portée bornée à `conception/GUI_V1.md` (§13 non-objectifs, §11 plafonds). Passe **avant** le lot 4 « développement assisté », qui reste conditionnel |
| Dispositions des trois `NOTE` ouvertes de B sur la conception GUI (2026-09-23) | `B-pause-010` **acceptée, vérifiée dans le code** : `workflow.run(pause=…)` et `cli._PauseSwitch` existent ; le lot 2 remplace ce mécanisme par `ExecutionControl` au lieu d'en créer un, et ses tests couvrent code 6 et `READY`. `B-origine-011` **acceptée** : l'origine affichée du délai est le chemin effectivement retenu par `settings` (anciens noms compris), jamais une liste fermée. `B-reprocess-012` **acceptée** : `docs/COMMANDES.md` disait « `--reprocess` : non » (n'appelle pas les agents) alors que `resume` reprend ensuite le cycle — corrigé au lot 1 |
| Lot 1 GUI : la façade se construit avec son consommateur | Le lot 1 livre les actions structurées et la résolution du délai, dont la CLI se sert déjà. `create_collaboration`, `inspect_collaboration` et le reste de la façade §10.1 viennent aux lots 3 à 5, quand la GUI les appelle — une façade sans appelant serait une API spéculative (`POURQUOI.md` règle 2) |
| `ruff format` hors de la porte de validation | Le projet ne l'a jamais utilisé ; reformater 26 fichiers brouillerait les diffs du lot 1 sans rien prouver |
| Point d'entrée de la GUI : sous-commande `dialogforge gui`, pas de script séparé (PO, 2026-09-23, lot 3) | Question ouverte par la conception, tranchée au début du lot 3 : une seule surface CLI à documenter et à parer (`tests/test_docs.py`), cohérente avec la table d'actions déjà partagée entre CLI et GUI |
| Fichier des récents : `~/.dialogforge/recents.json` (PO, 2026-09-23, lot 3) | À côté de `reglages.toml`, jamais lu par une commande métier (§5.2). Confirme la proposition de la conception, sans variante |
| `Presentation.phase_steps` calculé dans la façade, pas dans la vue Tkinter (lot 3) | §15.1 exige que « les quatre phases » se testent sans Tk ; la barre de progression (✓ ● ○ ! —) ne dépend que de `State`, donc `facade._phase_steps` la rend testable et réutilisable par une future sortie CLI sans dupliquer la règle dans `views/suivi.py` |
| Une fois `Phase.CLOSED` atteinte, la dernière phase se lit « faite » (`✓`), jamais « courante » (`●`) (lot 3) | Rien n'est plus « en cours » une fois le cycle terminé (§8.6, §8.7) ; réserver `●` aux trois phases qui précèdent une exécution encore possible garde la légende du §7.1 lisible sans ambiguïté |
| `facade.create_collaboration` remplace `cli._build_new` plutôt que de le dupliquer (lot 4) | §6.1/§6.5 exigent la « création partagée » ; `cli.cmd_new` délègue désormais à la façade, qui absorbe aussi `corpus.CorpusError` (retiré de `cli._BORDER_ERRORS`, devenu inatteignable). Un seul chemin de validation pour `new` et l'écran de création, mesuré par `tests/test_facade_creation.py` et la suite `test_cli.py`/`test_effort.py` inchangée |
| `iabinome/registry.py` : une seule instanciation d'`ADAPTERS`, partagée par `cli.py` et `iabinome/gui/` (lot 4) | Le registre des adaptateurs est un « registre partagé » au sens du §6.1 ; l'alternative (dupliquer `{"claude": ClaudeAdapter(), "codex": CodexAdapter()}` dans `gui/controller.py`) aurait recréé exactement la duplication que `decisions.allowed_actions` évite déjà côté actions |
| Le contrôleur GUI porte le premier fil moteur au lot 4, pas au lot 5 (2026-09-23) | « Créer et démarrer » (§6.7) est la première commande GUI qui peut appeler `workflow.run` ; le fil, l'`ExecutionControl` et le polling de `views/suivi.py` construits ici pour ce seul cas sont directement réutilisables par les interventions du lot 5, sans reconstruction |
| Fermeture de fenêtre pendant une exécution (§9.2-9.3) : seulement 2 branches sur 3 au lot 4 (2026-09-23) | « Continuer à suivre » et « interrompre maintenant » sont couvertes (`app._on_close`) ; la troisième (« terminer l'appel courant, mettre en pause, puis fermer ») demande d'attendre la fin du fil sans geler Tk — repoussée au lot 5, qui touche de toute façon à la pause coopérative pour les interventions |
| **Plafond de croissance nette dans `src/` porté de +900 à +2 500 lignes** (PO, 2026-09-23, après le lot 4) | Mesuré avec un compteur cohérent d'un lot à l'autre (hors commentaires/docstrings) : +1 046 lignes depuis le début de la phase 5, 146 au-delà du plafond initial de `conception/GUI_V1.md` §11. Le PO a tranché que le plafond était trop bas plutôt que de réduire le lot 4 déjà livré et testé — même logique que l'amendement du plafond global à J3 (`POURQUOI.md` règle 1). Le plafond de 1 200 lignes logiques (façade + `gui/`) n'a pas bougé : ~1 000 lignes, non approché. Détail dans `conception/GUI_V1.md` §11 et `project/RULES.md` |
| `ACCEPT`/`ACCEPT_WITH_RESERVES`/`STOP` appellent `workflow.decide` en direct, jamais `Controller.start_run` (lot 5) | Ces trois actions ont `may_call=False` dans `decisions.allowed_actions` : ce sont des écritures locales sous verrou, synchrones, comme `decide --accept` en CLI. Les faire passer par un fil aurait ajouté une latence et une fenêtre d'incohérence (statut affiché vs statut réel) sans aucun bénéfice — la règle du tableau (`may_call`) dit déjà lequel des deux chemins prendre, sans qu'`intervention.py` ait à la deviner |
| Une invite de texte dédiée (`dialogs.prompt_text`), pas `tkinter.simpledialog.askstring` (lot 5) | Une réponse humaine ou un motif de correction tiennent rarement sur une ligne ; `askstring` ne rend qu'un champ simple. Cohérent avec `dialogs.confirm`/`choose` : une seule famille de modales pour toute la GUI, jamais les boîtes de dialogue natives de `tkinter.messagebox`/`simpledialog` mélangées aux siennes |
| `dialogs.choose` (plus de deux issues), pas deux appels successifs de `dialogs.confirm` (lot 5, fermeture §9.3) | Trois branches mutuellement exclusives (continuer, pause puis fermer, interrompre) ne se prêtent pas à un enchaînement de oui/non — un « non » au premier `confirm` ne dit pas s'il faut proposer le second ou annuler tout à fait. Un seul dialogue à trois boutons nommés est sans ambiguïté et se ferme en un geste |
| Lot 6 : pas de nouveaux scénarios de faux agents, seulement ce qui manquait à la recette (2026-09-23) | Les huit scénarios du §15.3 étaient déjà couverts un par un, au fil des lots où chaque mécanisme est apparu (`test_gui_creation.py`, `test_gui_execution.py`, `test_gui_intervention.py`). Les rejouer identiquement au lot 6 aurait été une duplication sans preuve nouvelle ; `test_gui_recette.py` ajoute ce qui n'existait nulle part ailleurs : le croisement CLI/GUI dans les deux sens, un verrou déjà tenu, la parité `ActionId`/étiquette, le balayage du périmètre exclu |
| **Phase 6 ouverte : cadrage avec agent F** (PO, 2026-09-24) | Le PO a accepté la conception (`decide`, séquence 2) et demandé sa mise en place. Lève pour F seul la règle « le cycle ne dépend que des capacités communes aux deux outils » (précision n°2 de la demande) : écrit dans `CLAUDE.md` §6 et `project/RULES.md`. Le noyau A/B garde `fresh_session` |
| A1 — `B-convergence-003` : l'apport de « Continuer » compte comme 1re réponse du groupe (PO, 2026-09-24) | Un seul compteur (réponses humaines), deux actions au comportement identique : une question au plus avant la proposition suivante. Recommandé et retenu |
| A2 — `B-cout-004` : `/clore` avant le 1er échange = un échange « premier envoi + rédaction » (PO, 2026-09-24) | F ne rédige jamais sans l'idée ; retenu plutôt que d'interdire `/clore` avant le premier tour |
| Lot 5 : pas de file d'événements, le sondage `after()` de l'état du fil (2026-09-24) | Le §4.3 parle de « la file existante » ; la GUI n'en a pas — l'écran de suivi sonde déjà `is_running` par `after()`. La modale fait de même sur `has_active_run()`, puis lit le résultat du tour. Même garantie (le fil Tk n'appelle jamais l'adaptateur), sans nouvelle structure |
| Lot 5 : `start_run` refuse dès que le fil moteur est occupé, plus seulement sur le même dossier | Un tour de F n'a pas de dossier de collaboration : l'ancien test (`is_running(path)`) l'aurait laissé passer, donc A pendant F. Le §3.1 (une exécution au plus) le voulait déjà |
| Lot 5 : quitter le mode agent, l'écran de création ou la fenêtre ferme le cadrage | La session n'existe que pour cet écran (§6.1 : possédée par un seul contrôleur, fermée avant A). `Controller._swap` et `app._destroy` appellent `discard_framing` : aucun chemin de sortie ne l'oublie. Le brouillon déjà rendu reste dans l'éditeur |
| Lot 5 : le mode agent vit dans `gui/views/cadrage.py`, pas dans `creation.py` | `creation.py` aurait atteint 390 lignes effectives sur un plafond de vue de 400 ; il est à 370. `framing.shown` sert l'affichage d'un tour en CLI comme en GUI |
| A3 — Session de F par **reprise d'identifiant** (PO, 2026-09-24) | Les deux outils l'offrent (`--session-id`/`--resume` ; `exec` puis `exec resume`), lu dans `--help`. Un processus maintenu ouvert n'existe en pratique que chez un seul outil (l'autre : `app-server`, expérimental). Le transport existant sert tel quel. Coût : le modèle relit le contexte à chaque tour dans les deux mécanismes — le gain vient de ce que F ne relit plus le projet ni l'idée. **Non mesuré** : `codex exec resume` n'accepte pas `--sandbox` ; la lecture seule en reprise est à caractériser au lot 4 |

## Errors Encountered
| Error | Resolution |
|-------|------------|
| `DECODE_FAILED` sur une réponse accentuée du faux agent | Le faux agent écrit dans l'encodage local (cp1252) d'un tube Windows, les adaptateurs décodent en UTF-8. Propriété du faux agent, pas du moteur : le scénario fixe `PYTHONIOENCODING=utf-8` |
| **Trouvé au lot 4, non corrigé** : `corpus.build()` avec une liste source vide ne crée jamais le dossier `corpus/`, alors qu'il tente ensuite d'y écrire `manifeste.json` — `FileNotFoundError`, jamais le `ValueError("corpus vide pour une mission de recherche")` que le code semble promettre juste après. Branche morte préexistante (avant le lot 4), repérée en écrivant `tests/test_facade_creation.py` avec une assertion sur le message exact ; le comportement observable (refus, rien de créé) reste correct, donc non corrigé dans ce lot — signalé pour décision séparée, pas pour un correctif hors sujet |

# Task Plan: DialogForge V2 — développement

## Goal
Livrer un logiciel local où l'utilisateur décrit une demande, obtient une production A critiquée
par un B indépendant, une correction avec une disposition explicite par objection, puis décide —
avec reprise après incident sans rejouer un appel ambigu.

## Next Step
**Phase 5 (GUI V1) ouverte le 2026-09-23 ; lot 1 (5.1) fait, non commité — prochaine étape : lot 2
(5.2, `ExecutionControl`), après validation du lot 1 par le PO et commit sur sa demande.**

- Décision écrite : interdit « Pas de GUI » levé pour la seule GUI V1 (`CLAUDE.md` §2,
  `project/RULES.md` § Périmètre, table des décisions ci-dessous). Conception copiée dans
  `conception/GUI_V1.md`. **L'acceptation formelle du livrable** (`dialogforge decide
  C:\Projets\essais-3-1\gui-v1\collab --accept`) reste au PO.
- Lot 1 : `decisions.ActionId` / `AllowedAction` / `allowed_actions` = **la** table d'actions ;
  `next_action` en dérive ses phrases (inchangées, figées par `tests/test_actions.py`). Retirés en
  échange : `incidents.action`, `incidents.received` (sans appelant), `workflow._WAY_OUT` (la porte
  d'état nomme sa sortie depuis la table), `workflow._RELAUNCHABLE` et la méthode `relaunchable`
  (règle unique : `incidents.relaunchable`), le doublon « déjà accepté » de `workflow.decide`.
  Délai : `settings.resolve_timeout(explicit, override, base)` rend valeur **et origine** ; la CLI
  s'en sert pour `run`/`resume`/`decide`. `docs/COMMANDES.md` corrigé (`B-reprocess-012`).
- Taille : **+83 lignes de code effectif dans `src/`** (3 282 → 3 365, même compteur sur `HEAD` et
  l'arbre ; plafond +900). Validation : ruff, mypy strict, **595 passés / 2 ignorés**, scénario rc=0.
- **Lot 2 — points déjà connus** : la pause existe (`workflow.run(pause=…)`, `cli._PauseSwitch`) ;
  l'interruption passe par `KeyboardInterrupt` (`transport.py:275`). Remplacer les deux par un
  `ExecutionControl` (deux `Event`), sans changer statuts, codes de sortie (6 = pause) ni preuves.

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
Phase 5 (GUI V1) — ouverte le 2026-09-23, lot 1 fait, lot 2 à ouvrir. Phase 4 complète (J3, `v0.1.0`).

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
lui appartient. Plafonds (§11) : **1 200 lignes logiques de production, +900 lignes nettes dans
`src/`** — référence de mesure : 3 253 lignes de code au 2026-09-22.
- [x] 5.1 Lot 1 — actions structurées (`ActionId`, `AllowedAction`), textes CLI dérivés, parité ;
      résolution du délai centralisée *(2026-09-23, non commité ; résultats structurés de la
      façade reportés aux lots qui les consomment — voir Decisions Made)*
- [ ] 5.2 Lot 2 — `ExecutionControl` : transport, workflow, Ctrl+C de la CLI (la pause existe déjà,
      voir `B-pause-010`)
- [ ] 5.3 Lot 3 — accueil, récents non métier, ouverture, suivi en lecture seule, sous-état accepté
- [ ] 5.4 Lot 4 — création : formulaire, provenance compatible, configuration/lancement séparés
- [ ] 5.5 Lot 5 — interventions et décisions
- [ ] 5.6 Lot 6 — recette : faux agents, compatibilité CLI/GUI, atomicité, périmètre, taille
- **Status:** in_progress — 5.1 fait (non commité), 5.2 à ouvrir

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

## Errors Encountered
| Error | Resolution |
|-------|------------|
| `DECODE_FAILED` sur une réponse accentuée du faux agent | Le faux agent écrit dans l'encodage local (cp1252) d'un tube Windows, les adaptateurs décodent en UTF-8. Propriété du faux agent, pas du moteur : le scénario fixe `PYTHONIOENCODING=utf-8` |

# Task Plan: DialogForge V2 — développement

## Goal
Livrer un logiciel local où l'utilisateur décrit une demande, obtient une production A critiquée
par un B indépendant, une correction avec une disposition explicite par objection, puis décide —
avec reprise après incident sans rejouer un appel ambigu.

## Next Step
**Le lot 1 est terminé** (1.1 à 1.4, 2026-09-19). 1.1 (`b0dc6a3`), 1.2 (`2b5ae15`), 1.3 (`25ab101`)
commités ; **1.4 validé (ciblé puis porte complète) et commité** (commit `feat: ... (1.4)`, voir `git log`).

**J1** : critères réunis, **à constater par le PO** (voir le jalon de la phase 2). Ensuite : **lot 2 —
robustesse et liaison PWF du produit** (2.1 reprise après résultat reçu non appliqué, 2.2 paquet B
minimal et session reviewer fraîche, 2.3 référence de plan PWF facultative). Avant de coder 2.1, relire
`workflow.resume_call`/`store_response` et `tests/test_recovery.py` : une part de 2.1 existe déjà
(retraitement local d'une réponse stockée). **Attendre l'autorisation du PO pour ouvrir le lot 2.**

Lancer les sessions de développement par `.\tools\claude-pwf.ps1` : c'est la seule voie où
l'injection automatique du plan est qualifiée.

## Current Phase
Phase 2 terminée — Phase 3 (lot 2) à ouvrir sur autorisation du PO

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
- **Jalon :** J1 — version fonctionnelle avec faux agents. **Critères réunis le 2026-09-19, à constater par le PO** :
  parcours complet sans copier-coller (`reference/cycle_sans_fournisseur.py`), cas sans objection,
  avec correction, avec désaccord (plafond) et avec question humaine couverts par les tests, garanties
  de reprise héritées toujours vertes.

### Phase 3: Lot 2 — Robustesse et liaison PWF du produit
- [ ] 2.1 Reprise après résultat reçu non appliqué ; retraitement local de l'interprétation
- [ ] 2.1 Distinguer réponse mal interprétée, appel non lancé, issue inconnue ; verrou non effacé
- [ ] 2.2 Paquet B minimal ; session reviewer fraîche ; capacités effectives par profil vérifiées
- [ ] 2.2 Essai sur dossier jetable : sources non modifiées, journal de A non injecté chez B
- [ ] 2.3 Référence de plan PWF facultative via les scripts publics ; sortie vide traitée
- [ ] 2.3 Un seul propriétaire du plan ; fonctionnement documentaire vérifié sans liaison PWF
- **Status:** pending
- **Jalon :** J2 — version candidate aux essais réels.

### Phase 4: Lot 3 — Essais réels et première livraison
- [ ] 3.1 Versions des CLI et modèles relevées ; essai de petite taille en collaboration jetable
- [ ] 3.2 Trois tâches représentatives : conception courte, synthèse sur corpus, révision
- [ ] 3.3 Aide courte, exemples sans donnée personnelle, limites effectives documentées
- [ ] 3.3 Validation complète sur le commit livré, installation en environnement propre, version marquée
- **Status:** pending
- **Jalon :** J3 — première livraison utilisable.

## Extension identifiée (hors phases)

**Lot 4 — Développement assisté.** Spécification acceptée exportée vers l'agent de développement,
paquet de revue à partir d'une base Git identifiée, boucle de dispositions réemployée, essai sur
une modification limitée et réversible. **Ne s'ouvre qu'après J3** et n'introduit ni worker, ni
commit, ni déploiement automatique dans le moteur documentaire.

Également conditionnelles après J3, et non engagées : interface graphique légère, recherche externe.

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
| `ruff format` hors de la porte de validation | Le projet ne l'a jamais utilisé ; reformater 26 fichiers brouillerait les diffs du lot 1 sans rien prouver |

## Errors Encountered
| Error | Resolution |
|-------|------------|
| `DECODE_FAILED` sur une réponse accentuée du faux agent | Le faux agent écrit dans l'encodage local (cp1252) d'un tube Windows, les adaptateurs décodent en UTF-8. Propriété du faux agent, pas du moteur : le scénario fixe `PYTHONIOENCODING=utf-8` |

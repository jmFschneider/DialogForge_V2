# Task Plan: DialogForge V2 — développement

## Goal
Livrer un logiciel local où l'utilisateur décrit une demande, obtient une production A critiquée
par un B indépendant, une correction avec une disposition explicite par objection, puis décide —
avec reprise après incident sans rejouer un appel ambigu.

## Next Step
Lot 0.3 : qualifier la reprise PWF dans une **nouvelle** session (lecture de la bonne prochaine
étape, sélection erronée qui ne récupère pas un autre plan, hooks réellement nécessaires). Ensuite
seulement, consigner J0 et ouvrir le lot 1.

## Current Phase
Phase 1

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
- [ ] 0.3 Reprise vérifiée **en session** : bonne prochaine étape, sélection erronée refusée, hooks
- **Status:** in_progress
- **Jalon :** J0 — chantier prêt. Non atteint tant que la ligne ci-dessus est ouverte.

### Phase 2: Lot 1 — Parcours documentaire complet
- [ ] 1.1 Format court de demande, fichier direct ou cadrage guidé, provenance conservée
- [ ] 1.2 Objections et dispositions : énoncé, réponse de A, disposition et justification distincts
- [ ] 1.2 Réponse exigée pour chaque objection ouverte ; identifiants absents ou dupliqués détectés
- [ ] 1.3 Boucle : A → B → correction A → relecture ciblée B → décision humaine
- [ ] 1.3 Promotion de la version examinée à la place de la finalisation qui réécrit librement
- [ ] 1.4 Résultat, réserves, prochaine action ; acceptation, réserve, correction ciblée, arrêt
- [ ] 1.4 Décision datée portant sur une version précise ; « terminé » n'est pas « accepté »
- **Status:** pending
- **Jalon :** J1 — version fonctionnelle avec faux agents.

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
| `ruff format` hors de la porte de validation | Le projet ne l'a jamais utilisé ; reformater 26 fichiers brouillerait les diffs du lot 1 sans rien prouver |

## Errors Encountered
| Error | Resolution |
|-------|------------|
| `DECODE_FAILED` sur une réponse accentuée du faux agent | Le faux agent écrit dans l'encodage local (cp1252) d'un tube Windows, les adaptateurs décodent en UTF-8. Propriété du faux agent, pas du moteur : le scénario fixe `PYTHONIOENCODING=utf-8` |

# Audit de bout en bout — DialogForge V2 et PWF

Date : 25 septembre 2026. Référence : `114eccd01fe6eccaa8326255c1573059c0510132`, avec les modifications locales présentes au départ.

## Synthèse

Le parcours nominal, les reprises testées, les widgets GUI et la liaison PWF passent les vérifications exécutées.
758 tests et 464 sous-tests réussissent ; deux tests de liens symboliques restent ignorés faute de privilège Windows.
La promotion conserve le corps examiné par B et l'acceptation reste distincte du statut moteur.
Priorité 1 : l'acceptation peut néanmoins porter sur un livrable absent ; une demande modifiée peut aussi rester affichée comme acceptée.
Priorité 2 : le conseil CLI « Gratuit et local » sur `resume --reprocess` masque la possibilité d'un appel suivant, reproduite avec un faux B.
Priorité 3 : le plan PWF contient des rappels opérationnels périmés, dont une acceptation GUI dite encore à faire mais déjà enregistrée.
La liaison PWF minimale est utile et fonctionne sur la copie d'une collaboration réelle ; aucune synchronisation supplémentaire n'est justifiée par ces essais.
Aucun fournisseur appelé, aucune correction du produit ni mise à jour du plan ; toutes les écritures de l'audit sont dans ce dossier.

## 1. Périmètre, état initial et méthode

L'audit applique [le prompt V2](../PROMPT_AUDIT_BOUT_EN_BOUT_V2.md). La demande du PO remplace sa destination externe par `reference/Astra_AUDIT_BOUT_EN_BOUT/`. Ce dossier est l'unique exception à la lecture seule du dépôt.

Au départ, quatre fichiers suivis étaient modifiés :

- `.planning/2026-09-18-dialogforge-v2/progress.md` ;
- `.planning/2026-09-18-dialogforge-v2/task_plan.md` ;
- `docs/LIMITES.md` ;
- `reference/PROTOCOLE_CADRAGE_LOT4.md`.

Les prompts V1 et V2 étaient également non suivis. Ces modifications préexistantes sont incluses dans l'état audité et préservées. Voir [état Git initial](git_initial.stdout.txt), [commit](commit.stdout.txt) et [empreintes initiales](initial_files.json).

Environnement : Windows 11, Python 3.12.5 du `.venv` du dépôt. L'import d'`iabinome` pointe vers `src/iabinome`, également vérifié sans `PYTHONPATH` : [preuve](venv_import_without_pythonpath.stdout.txt). Git a d'abord refusé le propriétaire du dépôt dans le bac à sable ; les lectures suivantes utilisent une exception `safe.directory` limitée à la commande, sans modifier la configuration globale. `rg` n'était pas disponible dans cet environnement d'exécution ; recherche par les commandes PowerShell.

Les conclusions distinguent exécution actuelle, lecture du code et trace historique. Les faux agents prouvent les transitions et les effets locaux ; ils ne valident pas la qualité des modèles ni le confinement des vraies CLI. Les traces réelles sont lues sans les relancer. Aucun raisonnement métier contenu dans leurs livrables n'a été revalidé comme conseil technique à l'utilisateur.

## 2. Constats prioritaires

### F01 — P1 — Une nouvelle acceptation peut être enregistrée sans livrable ou sans revue

**Nature : défaut reproduit. Confiance élevée.** La priorité vient de la perte de sens d'une acceptation, même si le déclencheur suppose un dossier incomplet, par exemple après suppression ou déplacement manuel d'un fichier.

Attendu : une décision porte sur une version précise du livrable, de sa revue et de sa demande (`project/RULES.md:26`, `src/iabinome/decisions.py:43`). Une absence d'artefact ne constitue pas une nouvelle version acceptable.

Sur une copie du scénario terminé et accepté, le livrable a été renommé en `.audit-backup`, donc conservé mais absent de son chemin attendu. La CLI a d'abord correctement signalé une version différente. Puis :

```text
decide <copie_sans_livrable> --accept
code de retour : 0
acceptée ... (livrable None)
```

La nouvelle entrée de `decisions.json` contient `livrable_sha256: null`. `status` affiche ensuite « aucune : le résultat est accepté » et la façade GUI « Version acceptée ». Le même essai sans la revue permet une acceptation avec `revue_sha256: null`.

Preuves : [résultats, clés `missing_livrable` et `missing_revue`](audit_followup.results.json), [copie sans livrable](missing_livrable/decisions.json), [script de reproduction](audit_followup.py). Les fichiers originaux sont gardés dans les copies sous le suffixe `.audit-backup`.

Cause : `decisions._sha` rend `None` pour un fichier absent (`src/iabinome/decisions.py:39`). `workflow.decide` vérifie le statut, l'absence d'acceptation identique et les réserves, mais pas l'existence des artefacts avant `decisions.record` (`src/iabinome/workflow.py:998`, écriture ligne 1021).

**Contre-preuve et limite :** l'absence après une acceptation existante est initialement détectée pour le livrable et la revue. Le défaut est la possibilité de réaccepter ensuite cette absence. Aucun livrable réel n'a été supprimé et aucune occurrence spontanée n'est démontrée dans les dix collaborations lues.

**Proposition :** avant une acceptation, sous le verrou existant, exiger les artefacts indispensables et une demande cohérente. Réutiliser une vérification commune aux décisions et à leur présentation. Ne pas supprimer globalement les empreintes facultatives : une décision d'arrêt peut légitimement précéder tout livrable.

Effort : petit correctif ciblé avec tests de refus ; lignes à estimer. Rien à retirer artificiellement en échange ; remplacer le chemin qui assimile une absence à une version acceptable. Aucun interdit touché, aucune nouvelle couche de stockage. Validation attendue : refus sans nouvelle entrée de décision lorsque livrable ou revue manque ; acceptation normale et arrêt avant livraison toujours possibles.

### F02 — P1 — Une demande modifiée ou absente n'invalide pas l'acceptation affichée

**Nature : défaut reproduit. Confiance élevée.** Il touche l'accord humain et sa propagation dans les écrans et résumés ; le déclencheur est une modification de `demande.md` hors du moteur.

Attendu : l'applicabilité d'une décision doit correspondre aux artefacts actuellement présents, demande comprise (`project/RULES.md:26`, `decisions.version_of`).

Après ajout d'une phrase à `demande.md` sur une copie acceptée, son empreinte réelle diffère de `etat.json`, mais :

- `decisions.accepted` reste vrai ;
- `status` et `show` affichent l'acceptation sans avertissement ;
- la façade GUI affiche « Version acceptée » ;
- `plan` fournit le même accord comme information à reporter dans PWF.

Retirer la demande de son chemin attendu laisse également l'acceptation affichée. Preuves : [résultats `changed_demande`](audit_cases.results.json), [contre-épreuve `missing_demande`](audit_followup.results.json), [copie modifiée](changed_demande/demande.md).

Cause : `version_of` relit les octets du livrable et de la revue, mais reprend `state.demande_sha256` pour la demande (`src/iabinome/decisions.py:50`). `applies_to_current` compare donc deux valeurs issues de l'état enregistré, sans vérifier la demande sur disque (`src/iabinome/decisions.py:92`).

**Contre-preuves :** modifier le livrable ou une revue JSON encore valide invalide bien l'acceptation. `run` sur la demande modifiée refuse avant tout appel avec « demande.md ne correspond plus à l'empreinte de l'état » : zéro appel A/B. Le contrôle existe dans `_check_demande` (`src/iabinome/workflow.py:278`), mais ne protège pas les surfaces de décision/consultation. Le défaut ne signifie donc pas qu'une reprise normale accepte silencieusement cette demande.

**Proposition :** vérifier la demande courante, avec la même normalisation que le moteur, lors du calcul d'applicabilité et avant une acceptation. Conserver la décision historique ; afficher sa non-applicabilité ou le dossier incohérent, sans réécrire `etat.json`. Nommer l'artefact concerné dans le diagnostic : le texte actuel « le livrable a changé » est aussi utilisé quand seule la revue a changé.

Effort : faible à modéré, partagé avec F01 ; lignes à estimer. Remplace la confiance dans une empreinte mémorisée par la lecture déjà pratiquée pour les autres artefacts. Aucun interdit touché. Validation : modifications et absences de chacun des trois artefacts, contrôlées dans CLI, façade GUI et résumé PWF ; conservation des décisions passées et compatibilité de la normalisation BOM/fins de ligne.

### F03 — P2 — Le conseil de reprise présente une commande potentiellement payante comme gratuite

**Nature : défaut de présentation reproduit ; le moteur suit le comportement documenté. Confiance élevée.** Le risque utilisateur est un nouvel appel lancé sur la foi d'un conseil de gratuité.

`decisions._after_incident` produit « Gratuit et local : `resume ... --reprocess ...` » (`src/iabinome/decisions.py:268`). Un essai a provoqué un refus d'interprétation de la réponse de A, puis permis sa relecture. Après exécution de la commande conseillée :

| Compteur de faux appels | Avant | Après |
|---|---:|---:|
| A | 1 | 1 |
| B | 0 | 1 |

Le retraitement de A n'a pas relancé A ; la commande a bien enchaîné un appel de B. Preuves : [résultats `reprocess`](audit_cases.results.json), [collaboration conservée](reprocess_collaboration/etat.json), test existant `tests/test_incidents.py::TestTheLocalReprocessing::test_an_undecodable_answer_is_reread_locally_without_a_new_call` qui vérifie également un appel de B.

**Contre-preuves :** `docs/COMMANDES.md:11` annonce correctement cette possibilité. Les actions structurées portent `may_call=True` pour le retraitement suivi de reprise ; la GUI confirme « peut atteindre un nouvel appel fournisseur » (`src/iabinome/gui/views/intervention.py:79`). Il n'y a pas de rejeu automatique de l'appel ambigu démontré ici, ni de facturation mesurée : les agents sont faux.

Même famille de divergence : le tableau initial de `docs/COMMANDES.md:9` indique que `new` n'appelle pas d'agent, alors que sa section de cadrage explique correctement que `--cadrer-avec-agent` appelle F avant la création. Les douze échanges historiques F et les tests de création confirment cette branche.

**Proposition :** reformuler le conseil CLI en distinguant « retraitement local sans nouvel appel pour cette réponse » et « reprise du cycle pouvant appeler un agent ». Corriger la ligne `new` du tableau. Relire aussi la phrase sur `run` depuis `RUNNING` (`decisions.py:238`) pour ne pas étendre la gratuité du retraitement à toute la commande. Garder la sémantique de reprise existante ; aucune commande supplémentaire n'est nécessaire pour résoudre ce constat.

Effort faible, textes et assertions de présentation ; lignes à estimer selon la rédaction. Retire deux promesses trop larges. Aucun interdit touché, aucun budget interne à ajouter. Validation : le scénario de retraitement conserve ses compteurs, mais chaque conseil annonce la possibilité d'un appel suivant ; la voie fichier de `new` reste annoncée sans appel.

### F04 — P2 — Des rappels opérationnels du plan et des règles sont périmés

**Nature : divergences documentaires démontrées par les fichiers et artefacts. Confiance élevée sur les divergences, sans mesure d'une erreur humaine déjà causée.**

La prochaine action en tête de `task_plan.md` est claire : arbitrer `open_questions`, puis recette du lot 6. Les cases de la phase 6 correspondent à cette situation. Le problème est la coexistence de rappels incompatibles présentés comme utiles à la prochaine session :

| Rappel encore présent | Preuve qui le contredit ou le remplace |
|---|---|
| `task_plan.md:33` : acceptation formelle de la conception GUI « jamais faite » | `C:/Projets/essais-3-1/gui-v1/collab/decisions.json` : `ACCEPTE`, `2026-09-23T13:36:45Z`, encore applicable ; [inventaire](real_collaborations.json) |
| `task_plan.md:36` et `project/RULES.md:44` : plafond GUI 1 200, marge quasi nulle à 1 195 | Conception F acceptée, `conception/CADRAGE_AGENT.md:1003` : plafond 2 000 ; plan phase 6 ligne 380 et mesure actuelle : 1 537 |
| `CLAUDE.md:78` : relecture palier par palier suspendue depuis le 3 septembre | `project/RULES.md:64` : suspension puis réouverture le 5 septembre ; conflit entre consignes, pas une nouvelle décision déduite par l'audit |

Les annotations de lots anciens « non commité » ont souvent une date et un contexte historique explicites : elles ne sont pas toutes des défauts. En revanche, un repère destiné à la prochaine session et affirmant qu'une action reste à faire doit être actualisé ou clairement sorti de la zone opérationnelle.

**Proposition :** garder un `Next Step` court avec état actuel, arbitrages ouverts et liens de preuve ; déplacer ou dédupliquer le récit déjà présent dans `progress.md`. Remplacer les rappels obsolètes par les décisions applicables. Pour la relecture, exposer le conflit et faire confirmer la règle en vigueur si aucun arbitrage ultérieur n'est retrouvé, sans rouvrir automatiquement un processus de revue.

Effort faible à modéré, essentiellement rédactionnel ; lignes à estimer, diminution nette attendue. Retire des répétitions du plan et des chiffres devenus faux. Aucun nouveau tableau de bord, aucune synchronisation, aucun automatisme : PWF garde l'unique avancement de développement. Validation : une lecture du début du plan retrouve une seule prochaine action et les plafonds applicables, sans demander une acceptation déjà consignée.

## 3. Couverture du parcours

Les noms de modules renvoient aux tests effectivement exécutés. Le détail par cas est conservé dans [pytest.xml](pytest.xml) et [l'index des tests](consolidation.json). « Conforme » ci-dessous signifie conforme sur les cas vérifiés, sans garantie universelle.

| Étape ou branche | Résultat | Preuves et limites |
|---|---|---|
| `new --demande`, provenance, puis cycle et décision dans le même dossier | Conforme | [Scénario](scenario.stdout.txt), quatre appels A/B, une révision, une acceptation ; `test_cli`, `test_demande` |
| `new --cadrer`, demande guidée, abandon | Conforme | `test_demande`, `test_cli` ; tests avec entrée pilotée, pas une séance de saisie manuelle |
| Cadrage F : démarrage, échanges, reprise, rédaction, validation, annulation | Conforme sur les cas exécutés, défaut connu de provenance | `test_framing`, `test_framing_session`, `test_framing_creation` ; deux cadrages réels de six échanges chacun lus ; `open_questions` reste connu |
| Corpus de recherche, absence de corpus en conception, copie et intégrité | Conforme hors cas connu de liste vide | `test_corpus`, `test_workflow`, `test_facade_creation`, `test_framing` ; deux tests de liens symboliques ignorés |
| A/B, permutations, contrats d'objections et dispositions | Conforme | `test_workflow`, `test_objections`, `test_contracts`, `test_relecture`, `test_prompts` ; les faux agents ne mesurent pas la qualité réelle d'une critique |
| Dossier jetable, filtre d'environnement, options des adaptateurs | Conforme au niveau local | `test_isolation`, `test_adapters`, `test_web_access`, `test_effort` ; confinement des vraies CLI limité aux preuves historiques documentées |
| Questions humaines et complément de demande | Conforme | `test_intervention`, `test_recovery` ; archivage, conservation du préfixe et rejeu local testés |
| Interruption, résultat reçu non appliqué, relance explicite, verrou | Conforme sur les cas testés | `test_transport`, `test_control`, `test_recovery`, `test_lock` ; pas de simulation d'une coupure électrique ni de toutes les interleavings possibles |
| `--reprocess` | Fonctionnement conforme, conseil CLI défectueux | F03 ; conservation des données brutes et poursuite du cycle testées |
| Promotion et plafond de révisions | Conforme | `test_promotion`, [comparaison directe](audit_cases.results.json) ; corps identique sur le scénario et les sept collaborations réelles terminées |
| `show`, `status`, `decide`, versions des décisions | Partiel, défauts F01/F02 | Acceptation nominale, réserves, correction ciblée et arrêt passent ; acceptation de dossier incomplet et demande modifiée reproduites |
| GUI : création, suivi, interventions, fermeture, cadrage F | Conforme sur les tests de façade et widgets ; recette visuelle non vérifiée | `test_facade`, `test_gui_*`, y compris recette CLI↔GUI ; racine Tk masquée, boutons et dialogues pilotés, aucune séance visuelle humaine |
| Liaison PWF du produit | Conforme sur les essais | Tests simulés, six tests du résolveur installé et copie d'une collaboration réelle ; détail section 4 |
| PWF du développement | Partiel | Épinglage local et preuve historique de hooks ; divergence F04 ; aucune exécution nouvelle de hooks ni validation de l'injection dans l'hôte Codex actuel |

## 4. PWF, séparément

### A. Liaison facultative du produit

Essai effectué sur [une copie de `nextcloud-clients`](pwf_real_copy/etat.json), sans `run` ni `resume`. Son état réel au moment de la copie est `AWAITING_APPROVAL`, révision 2, une objection ouverte, décision applicable `ACCEPTE` du 23 septembre. Les descriptions historiques de la première mission du 22 septembre ne sont donc pas son état courant.

Le shell `sh` était absent du `PATH` initial. Il a été rendu accessible uniquement dans l'environnement du sous-processus d'essai via `C:/Program Files/Git/bin`. Le résolveur utilisé est celui installé sous `C:/Users/schne/.claude/skills/planning-with-files/scripts/resolve-plan-dir.sh`. Aucun faux résolveur pour cette vérification ; les octets du résolveur installé et de la copie locale sont identiques.

Résultats [détaillés ici](audit_cases.results.json) :

- sans liaison : résumé lisible ;
- liaison au vrai plan `2026-09-18-dialogforge-v2` : succès ;
- tentative de remplacement par un identifiant inexistant : refus, arbre de la copie inchangé ;
- liaison devenue invalide sur la copie : diagnostic `NON RÉSOLU`, résumé toujours disponible ;
- `--unlink` : retour exact aux empreintes initiales de la copie ;
- empreintes de `.planning/` identiques avant et après.

Les tests montrent aussi qu'un cycle à faux agents fonctionne sans PWF et avec un `plan.json` corrompu. Des variantes JSON `null`, liste et nombre dans la liaison produisent un diagnostic de liaison inutilisable, sans supprimer le résumé. Des champs `null` dans un objet sont convertis en texte et conduisent à une liaison non résolue : diagnostic perfectible, mais aucun impact bloquant nouveau démontré.

Le résumé permet de retrouver dossier, document, revue, statut, décision et action suivante. Il donne le **nombre** d'objections ouvertes, pas leur texte ni les réserves humaines. Pour cette copie acceptée avec une objection ouverte, il faut lire le bilan pour savoir laquelle. Une indication « voir le bilan pour le détail » ou un lien vers celui-ci serait une amélioration de présentation facultative ; ce n'est pas une raison de synchroniser les phases ni d'écrire automatiquement dans le plan.

La limite importante de ce résumé est F02 : il réutilise l'acceptation calculée par le produit. Corriger cette source bénéficie simultanément à la CLI, à la GUI et à PWF, sans ajouter de contrôle propre à PWF.

### B. Pilotage du développement

`tools/claude-pwf.ps1` épingle le plan et la racine dans l'environnement enfant, charge la copie locale avec `--plugin-dir`, puis restaure les variables. Le lanceur est suivi par Git ; la copie complète `tools/planning-with-files/` est volontairement ignorée et reconstruite séparément (`.gitignore`). Son manifeste local indique 3.20.1. Le commit amont `faf1a15...` est consigné dans le plan ; aucune récupération réseau de l'amont ni comparaison exhaustive du paquet avec ce commit n'a été faite ici.

La trace historique du 19 septembre annoncée dans `progress.md` a été retrouvée et analysée avec le lecteur existant `reference/preuve_injection.py`, sans lancer de hook. [Résultat](audit_followup.results.json), clé `historical_hooks` :

| Événement | Preuve dans la trace de l'hôte |
|---|---|
| `SessionStart` | Livraison du contexte aux lignes 6 et 101, démarrage et retour après compactage selon le journal de qualification |
| `UserPromptSubmit` | Trois livraisons, lignes 15, 63 et 109 |
| `PreToolUse` | Six livraisons, lignes 34, 37, 40, 43, 46 et 66 |
| `PostToolUse`, `PreCompact` | Aucun enregistrement ; non vérifiés |
| `Stop` | Six enregistrements, sans livraison de plan observée ; cela n'est pas assimilé à un échec d'injection puisque la fonction de ce hook diffère |

Deux occurrences de bannière dans des messages sont exclues des preuves d'injection. Cette preuve concerne Claude 2.1.278 et la session historique ciblée, pas l'hôte Codex présent.

Le plan comporte 473 lignes, `findings.md` 90 et `progress.md` 1 717, lignes vides comprises. La taille du journal n'est pas retenue comme défaut autonome. La difficulté concrète est le mélange de rappels opérationnels et d'historique dans `Next Step`, illustré par F04. L'avancement courant en tête et les cases de phase 6 restent cohérents avec les commits et les modifications locales. Aucune seconde liste active d'avancement n'a été démontrée dans les documents du projet examinés ; les spécifications, critères de recette et notes historiques ne sont pas assimilés à un second plan.

## 5. Points déjà connus

| Point | État constaté et priorité relative |
|---|---|
| `open_questions` après reprise de F | Toujours présent dans le code et les deux traces. Chez Claude, l'entraxe figure encore comme question dans la provenance alors que la suite de transcription le renseigne. Ce sont des preuves historiques relues, pas un nouveau cadrage fournisseur. À traiter lors de l'arbitrage prévu, après les défauts d'acceptation F01/F02. Ne pas valider automatiquement une des corrections proposées. |
| `corpus.build()` sur liste vide | Reproduit : `FileNotFoundError` lors de l'écriture du manifeste dans un dossier non créé. [Preuve](consolidation.json). Défaut local à corriger de façon ciblée ; les validations de recherche et le chemin F ne doivent pas être confondus avec cette primitive. |
| `status` pendant un `run` concurrent | Fenêtre intermittente déjà consignée. Pas de campagne concurrente nouvelle pour mesurer sa fréquence. Le correctif de poursuite du sondage GUI et ses tests passent ; cela ne prouve pas l'absence du défaut ponctuel CLI. |
| `ruff format --check` | 66 fichiers de `src/` et `tests/` seraient reformatés, 11 déjà conformes. Hors de la porte de validation adoptée ; pas de défaut fonctionnel déduit et aucun reformatage du produit effectué. |
| Marge de taille | Recalcul identique aux repères : 5 572 lignes de code contre 3 282 à `ba5c0a4`, croissance 2 290, marge 210 sur 2 500. Façade + GUI : 1 537 sur 2 000. [Méthode et détail](size_measurement.json). Ce compteur exclut commentaires et docstrings ; ce ne sont pas les lignes physiques. |

## 6. Validations et limites

| Vérification | Résultat et preuve |
|---|---|
| Suite actuelle `pytest tests` | 752 réussis, 8 ignorés, 464 sous-tests réussis, 135,51 s ; [sortie](pytest.stdout.txt), [commande](pytest.command.json) |
| Six tests ignorés faute de `sh`, repris avec Git Bash dans le `PATH` enfant | 6 réussis ; [sortie](pytest_real_pwf.stdout.txt), [commande](pytest_real_pwf.command.json) |
| Total de cas de test distincts réussis | **758** ; restent deux cas de liens symboliques ignorés (`WinError 1314`) |
| Scénario nominal | Code 0 ; A=2, B=2, décision humaine enregistrée, statut inchangé ; [sortie](scenario.stdout.txt) |
| Ruff sur `src/` et `tests/` | Réussi ; [sortie](ruff.stdout.txt). Périmètre explicite : ne vaut pas pour chaque script historique de `reference/` ni pour les scripts de collecte de cet audit. |
| Mypy strict | Réussi sur 77 fichiers ; [sortie](mypy.stdout.txt) |
| Contrôle des fichiers du dépôt | Aucun fichier ajouté, retiré ou modifié dans [la différence des empreintes](file_changes.json), hors dossier d'audit, `.git` et `.venv` ; les caches préexistants et la copie locale PWF sont inclus |
| Collaborations réelles | Dix présentes, empreintes des fichiers stables entre inventaire et contrôle final ; [preuve](consolidation.json) |

Non vérifié : nouvelle exécution des fournisseurs, qualité générale des documents produits, confinement complet en lecture/réseau, interface manipulée visuellement par un humain, installation sur une machine vierge, autres OS, hooks dans une nouvelle session, deux scénarios nécessitant le privilège de lien symbolique. Ces limites empêchent une certification globale ; elles n'invalident pas les défauts locaux reproduits.

Aucun nouvel appel fournisseur n'est nécessaire pour confirmer F01 à F04. Une nouvelle qualification des restrictions des adaptateurs ne serait utile qu'après un changement de CLI ou pour étendre une garantie actuellement non promise ; il faudrait alors définir un protocole et obtenir l'accord du PO. Aucun coût monétaire n'est déduit des traces.

Les empreintes ne surveillent pas tout le profil utilisateur, les ACL, les horodatages ou les fichiers internes de `.git`/`.venv`. Elles permettent de vérifier l'absence de changement de contenu dans le périmètre inventorié, sans prétendre prouver l'absence de tout effet possible sur la machine.

## 7. Documents et preuves à consulter

- [Analyse détaillée, contre-preuves et hypothèses non retenues](ANALYSE_DETAILLEE.md).
- [Mode de lecture des preuves et de reproduction](README.md).
- [Reproductions initiales](audit_cases.results.json), [contre-épreuves](audit_followup.results.json), [inventaire réel](real_collaborations.json), [consolidation](consolidation.json).

L'audit ne modifie ni le code, ni les tests du produit, ni ses décisions humaines, ni le plan. Les propositions ci-dessus restent des recommandations, pas des corrections exécutées.

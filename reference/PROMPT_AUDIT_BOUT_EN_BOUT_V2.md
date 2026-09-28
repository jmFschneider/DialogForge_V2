# Prompt d'audit de bout en bout — DialogForge V2 et son usage de PWF — V2

*Rédigé le 2026-09-25. À coller au début d'une session ouverte dans
`C:\Projets\DialogForge_2`, avec Claude ou Codex. Le texte à coller commence sous la ligne.*

---

## Mission et critères de jugement

Audite DialogForge V2 (paquet `iabinome`) depuis la création d'une demande jusqu'à la décision
humaine sur son livrable, ainsi que ses deux usages de PWF (planning-with-files). Produis un
rapport en français, sans corriger le produit. La portée est déclarée : ne la redemande pas.

Cherche les défauts, les simplifications utiles et les comportements à conserver. Il n'y a aucun
nombre de problèmes à atteindre. Une absence de preuve n'est ni une preuve de conformité ni un
défaut du produit. Évalue les garanties annoncées dans leur périmètre réel.

Lis `CLAUDE.md`, puis le plan `.planning/2026-09-18-dialogforge-v2/` (`task_plan.md`, `findings.md`,
`progress.md`), `POURQUOI.md` et les règles pertinentes de `project/RULES.md`. Résous le plan selon
la procédure du dépôt si elle est disponible ; sinon, lis le dossier explicitement désigné et
signale que la résolution automatique n'a pas été vérifiée. Une sortie vide avec un code 0 du
résolveur n'est pas une résolution réussie. Ne crée pas de second plan d'avancement.

`POURQUOI.md` donne les principes ; les décisions humaines explicites, datées et applicables
précisent leurs exceptions. Confronte la conception approuvée (`conception/CONCEPTION_FINALE.md`,
`conception/CADRAGE_AGENT.md`, `conception/GUI_V1.md`), la documentation d'usage et l'implémentation.
Une date plus récente ne suffit pas à rendre un texte normatif. Si deux sources se contredisent
sans arbitrage explicite, expose la contradiction et son effet ; ne choisis pas silencieusement
celle qui permet de déclarer un défaut du code. Une fonctionnalité encore planifiée n'est pas une
régression d'une fonctionnalité livrée.

## Lecture seule et essais autorisés

- Aucune modification du dépôt, de `.planning/`, des réglages personnels, des installations ou des
  collaborations réelles. Aucun commit. Les sources de `CLAUDE.md` §4 restent en lecture seule.
  **Pour cette session d'audit, ceci remplace les consignes locales de mise à jour du plan et de
  `RULES.md` en fin de session.** Le rapport externe consigne les résultats.
- Place les fichiers que tu génères sous `C:\Projets\essais-3-1\audit-bout-en-bout\`, dans un
  sous-dossier de session neuf : rapport, copies, scénarios, sorties, caches et temporaires des
  essais. N'écrase pas un audit précédent. Si les permissions empêchent cette écriture, demande
  l'accès prévu par l'environnement ; poursuis entre-temps les lectures possibles.
- Avant une exécution, vérifie ses effets de bord : bytecode Python, caches de pytest/ruff/mypy,
  fichiers temporaires, réglages chargés et hooks PWF. Désactive ou redirige les écritures des
  processus d'essai hors du dépôt, y compris celles des sous-processus. Ne change pas la
  configuration persistante pour y parvenir. Si cela ne peut être assuré, limite cette vérification
  à la lecture et indique pourquoi. Ne lance pas un hook ou un lanceur uniquement pour l'inspecter.
- Aucun appel fournisseur sans accord explicite du PO dans cette session, y compris depuis F,
  la GUI, une reprise ou une copie d'une collaboration réelle. Une copie conserve potentiellement
  la configuration des vrais agents. `resume --reprocess` retraite localement, mais la poursuite
  du cycle peut appeler un fournisseur : ce n'est pas une commande globalement sans quota.
- Pour les exécutions Python, utilise `.venv\Scripts\python.exe` du dépôt et vérifie le chemin
  effectivement importé pour `iabinome`. Le Python global peut viser un autre projet. Réutilise les
  faux agents existants en vérifiant leur substitution effective avant tout parcours exécutable.
  Ne suppose pas que `fake` est une option publique de la CLI.

Relève au départ le commit, les modifications locales présentes et l'environnement utile aux
vérifications. Les changements non commités font partie de l'état audité ; ne les attribue pas
à l'audit. Compare l'état final à cet état initial, en incluant les fichiers générés ignorés par
Git lorsque tes commandes peuvent en créer. Signale les limites de ce contrôle.

## Méthode de preuve

Pour chaque conclusion, indique l'attendu, son origine et ce qui a réellement été observé :
exécution actuelle, trace historique ou lecture statique. Réserve « reproduit » à un cas rejoué
dans cette session. Un défaut peut aussi être démontré par un artefact ou un chemin de code
complet ; précise alors cette preuve et ses limites. Une hypothèse reste un risque à vérifier.

Pour une exécution, conserve la commande, le contexte utile, le code de retour et la sortie
pertinente. Pour une lecture, cite `fichier:ligne` ou le chemin exact de l'artefact. Cherche une
explication alternative ou une contre-preuve avant de retenir un défaut. N'inclus pas de secrets
ou de valeurs d'environnement sensibles dans le rapport.

Le scénario `reference/cycle_sans_fournisseur.py <dossier_neuf>` est un point de départ : il couvre
une demande par fichier, une révision A/B et une acceptation humaine avec faux agents. Il ne
prouve pas à lui seul le questionnaire, F, la GUI, les incidents, PWF ou le comportement des
fournisseurs. Réutilise les tests existants pour ces branches ; ajoute seulement les essais
externes ciblés nécessaires pour départager un constat important. La suite se lance sur `tests/`,
jamais par une collecte non bornée du dépôt. Distingue tests exécutés, tests seulement lus,
échecs, ignorés et vérifications empêchées par l'environnement.

## Parcours à vérifier

Suis un même dossier de collaboration de la demande à la décision, puis couvre les branches
ci-dessous par les tests ou artefacts pertinents. Évite de multiplier toutes les combinaisons :
justifie les variantes retenues et rends les branches non vérifiées visibles.

1. **Création.** Les trois voies de `new` (`--demande`, `--cadrer`, `--cadrer-avec-agent`) et la
   création par la GUI dans son périmètre livré. Vérifie la demande validée, sa provenance, le
   corpus figé et les informations effectivement transmises à A et B. Pour F, couvre la reprise
   du cadrage, la validation et l'annulation. Pour le corpus, distingue conception et recherche.
2. **Cycle A/B.** Production, critique, révision avec disposition par objection, puis relecture.
   Vérifie les identifiants et l'historique des objections, les réponses hors contrat et la borne
   de révision. Distingue les rôles, les outils et les modèles. Pour l'isolation, sépare dossier
   jetable et environnement filtré, options demandées aux CLI et restrictions réellement
   observées. Un faux agent ne prouve pas le confinement d'une vraie CLI ; un refus d'écriture
   ne prouve pas un confinement en lecture. Tiens compte de `docs/LIMITES.md` et de ses mesures.
3. **Incidents et reprise.** `WAITING_HUMAN`, interruption, réponse inexploitable, `resume`,
   `--answer`, `--reprocess`, `--retry-call` et verrou. Vérifie l'absence de relance **automatique**
   d'un appel à l'issue ambiguë ; une relance explicitement demandée avec l'identifiant et le
   motif requis est un comportement distinct. Observe les appels déclenchés après chaque
   intervention, la conservation des données brutes et la préservation de la demande complétée.
4. **Livraison et décision.** Compare les octets ou empreintes de la version examinée par B et
   du livrable promu. Vérifie `bilan.md`, `show`, les décisions prévues par `decide` et leur trace
   dans `decisions.json`, y compris quand des objections restent ouvertes. « Terminé », « avis
   favorable de B » et « accepté par l'humain » sont distincts. Éprouve sur copie la détection
   d'une décision devenue périmée après modification d'un artefact auquel elle se rapporte.
5. **GUI.** Vérifie la cohérence avec le moteur et les actions CLI pour la création, le suivi,
   l'arrêt/reprise et la décision. Distingue tests de façade, tests de widgets et manipulation
   effective de la fenêtre. Si l'affichage n'est pas accessible, ne conclus pas à une recette
   visuelle réussie sur la seule base de tests sans interface.
6. **PWF.** Vérifie séparément les deux usages décrits ci-dessous.

### Traces réelles disponibles

Sous `C:\Projets\essais-3-1\`, les dossiers suivants sont des pistes de preuve historique, à lire
sans lancer leur cycle. Vérifie leur présence et leur contenu ; les descriptions ci-dessous sont
des repères au 2026-09-25, pas des conclusions à reprendre telles quelles.

| Dossiers | Observation annoncée |
|---|---|
| `collab`, `collab-inverse` | Un cycle par sens A/B, sans décision |
| `pieges-souris`, `nextcloud-clients`, `revision-nextcloud\collab`, `gui-v1\collab`, `Creation-prompt-2` | Cycles avec décision, jusqu'à trois révisions |
| `Creation-prompt` | Arrêt en `WAITING_HUMAN` |
| `cadrage-lot4\produit-claude`, `cadrage-lot4\produit-codex` | Cadrages F, un par outil, collaborations créées mais jamais lancées ; voir `reference/PROTOCOLE_CADRAGE_LOT4.md` |

Ces collaborations sont annoncées sans liaison PWF. Une absence actuelle de `plan.json` ne prouve
pas qu'il n'en a jamais existé. Pour les traces retenues, relève les versions et dates disponibles.
Si leur rattachement au code actuel est inconnu, dis-le. Elles prouvent un comportement observé
dans leur contexte, sans garantir la qualité générale des modèles ni toutes leurs restrictions.

## PWF : deux usages distincts

**A. Liaison du produit à un plan.** Lis `src/iabinome/planlink.py` et la documentation de `plan`.
L'intention est minimale : liaison facultative, cycle indépendant de `plan.json`, aucun avancement
recopié automatiquement et aucune écriture dans le plan. Sur une copie de collaboration terminée,
vérifie le résumé sans liaison, puis `--link` vers `2026-09-18-dialogforge-v2` avec
`--plan-root C:\Projets\DialogForge_2`, un identifiant inexistant, et `--unlink`.

Observe les changements de fichiers : le refus d'une nouvelle liaison doit préserver une liaison
valide déjà présente ; retirer la liaison ne doit altérer ni état ni livrable ni décision. Vérifie
la lecture d'une liaison devenue invalide et l'indépendance du cycle au moyen de tests à faux
agents. Vérifie l'absence d'écriture dans le plan, sans te contenter d'un code de retour. Si PWF
ou son résolveur manque, ne l'installe pas : utilise les tests substitués disponibles et indique
que l'intégration effective n'a pas été exécutée.

Évalue l'utilité du résumé sur un exemple concret : permet-il de retrouver la collaboration, le
livrable, les réserves, la décision et l'action suivante sans interprétation hasardeuse ? Une
préférence de présentation reste une préférence. Toute proposition d'intégration supplémentaire
doit nommer le besoin observé, son coût et son effet sur le propriétaire unique de l'avancement
et les interdits de `CLAUDE.md` §2, en tenant compte des exceptions approuvées.

**B. PWF pour développer DialogForge.** Compare `## Next Step`, les phases, `progress.md`, les
décisions datées, l'état Git et les modifications non commitées. Distingue une trace historique
d'une seconde liste d'avancement encore utilisée. Examine les règles et hooks applicables à
l'outil hôte, `tools/claude-pwf.ps1` et l'épinglage annoncé à PWF 3.20.1 : sépare présence du code,
configuration d'activation et preuve d'exécution. N'attribue pas un hook Claude à une session
Codex sans preuve. Ne lance pas de nouvelle session fournisseur pour vérifier un hook.

Évalue la facilité de reprise sur des faits : prochaine action identifiable, arbitrages
retrouvables, contradictions, répétitions ou information indispensable difficile à trouver. La
longueur de `progress.md` n'est pas à elle seule un défaut. Pour `project/RULES.md`, distingue règle
active, exception et justification historique ; cite tout doublon ou contradiction retenu.

## Points déjà signalés

Rapproche tes constats de cette liste avant de finaliser le rapport. Ne les compte pas comme de
nouvelles découvertes ; indique leur état actuel si vérifié. Un impact nouveau ou une régression
reste signalable, avec la preuve de ce qui est nouveau. La correction pressentie n'est pas acquise.

- `open_questions` peut conserver des questions résolues après une reprise de F ; proposition
  en attente : reprendre les `QUESTIONS_OUVERTES` du dernier tour.
- `corpus.build()` avec une liste vide.
- Échec ponctuel possible de `status` pendant un `run` concurrent.
- Écarts à `ruff format --check`, sans décision de l'inclure dans la porte de validation.
- Marge annoncée d'environ 210 lignes sur la croissance autorisée de +2 500 dans `src/`.

Ces informations peuvent vieillir. Si une mesure de taille motive une recommandation, indique
le compteur, le périmètre, le commit de référence et la règle de comparaison ; ne mélange pas
lignes physiques et lignes de code, ni plafonds de la GUI et croissance totale de `src/`.

## Livrable et fin de l'audit

Écris `RAPPORT_AUDIT.md` dans ton sous-dossier de session externe et donne son chemin au PO.

1. **Synthèse**, dix lignes au plus : portée effectivement vérifiée, état général et au plus
   trois points décisifs, y compris ce qui mérite d'être conservé.
2. **Constats par priorité** : comportement attendu et source, observation et preuve, nature
   de la preuve, impact utilisateur et proposition minimale. Sépare défaut démontré, risque
   plausible, divergence documentaire et préférence. Justifie la priorité par l'impact et les
   circonstances ; ne la confonds pas avec la confiance dans la preuve.
3. **Coût des recommandations** : effort et complexité, ce qu'elles retirent ou pourquoi rien,
   règle éventuellement touchée. Chiffre les lignes seulement si une base crédible le permet,
   sous forme de fourchette ; sinon indique « à estimer ». Un correctif nécessaire n'exige pas
   une suppression artificielle en échange. Mentionne le contrôle qui permettrait de le valider.
4. **Couverture du parcours et PWF A/B** : pour chaque étape et branche importante, attendu,
   résultat, preuve et limite. Utilise « conforme sur les cas vérifiés », « défaut », « partiel »
   ou « non vérifié ». Ne masque pas plusieurs branches derrière un seul résultat nominal.
5. **Déjà connus et non vérifié** : statut des points connus sans double comptage ; lacunes,
   motif précis et conséquence sur la conclusion. Indique l'état final des fichiers contrôlés.

Pas de note globale ni de correctif de code dans le rapport. Si un point nécessite un appel réel,
décris la question à trancher, les appels envisagés et le coût seulement s'il est estimable ;
sinon indique-le comme inconnu. Présente cette demande séparément, après avoir livré les résultats
sans quota. Ne lance aucun de ces appels sans accord explicite. Une lacune localisée n'empêche
pas de terminer les autres vérifications et de remettre un rapport utile.

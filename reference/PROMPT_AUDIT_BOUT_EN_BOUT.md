# Prompt d'audit de bout en bout — DialogForge V2 et son usage de PWF

*Rédigé le 2026-09-25, à la demande du PO. À coller tel quel au début d'une session neuve, ouverte dans
`C:\Projets\DialogForge_2`. Il vaut pour l'un ou l'autre outil. Le texte à coller commence sous la ligne.*

---

## Portée de cette session : audit en lecture seule

Tu audites DialogForge V2 (le paquet `iabinome`) de bout en bout : de la création de la demande jusqu'à la
décision humaine sur le livrable. Tu vérifies aussi que PWF (planning-with-files) est correctement utilisé et
intégré. Tu ne corriges rien. Tu produis un rapport qui dit ce qui fonctionne, et surtout ce qui mérite d'être
optimisé, modifié ou retiré, avec ses preuves.

Commence par ce qu'exige `CLAUDE.md` §0 : le plan PWF, `findings.md`, `progress.md`, `POURQUOI.md` et
`project/RULES.md`. La portée est celle-ci : ne la redemande pas. `POURQUOI.md` est ta grille de lecture
principale. Ce projet est né d'un outil devenu une fois et demie plus gros que le projet qu'il servait. Une
recommandation qui ajoute de la machinerie doit donc dire ce qu'elle retire en échange.

## Ce que tu peux faire, et ce que tu ne fais pas

- **Aucune écriture dans le dépôt**, aucun commit, aucune modification de `.planning/`. Les dossiers sources de
  `CLAUDE.md` §4 restent en lecture seule, comme toujours.
- Tout ce que tu crées va sous `C:\Projets\essais-3-1\audit-bout-en-bout\` : collaborations de test, copies,
  rapport.
- **Aucun appel fournisseur sans l'accord explicite du PO dans cette session.** Le parcours complet se rejoue sans
  quota avec les faux agents : `.venv\Scripts\python.exe reference\cycle_sans_fournisseur.py <dossier>`, ainsi que
  la suite de tests. Toujours `.venv\Scripts\python.exe` : le Python global résout `iabinome` vers un autre projet.
- Les parcours réels existent déjà sur disque, et tu les lis sans rien lancer (voir plus bas). Si un point ne se
  tranche qu'avec un appel réel, décris l'appel, son coût et ce qu'il prouverait, puis **demande**.

## Le parcours à contrôler

Suis une demande à travers le produit, étape par étape. Pour chaque étape, confronte ce que disent la
conception et la documentation (`conception/CONCEPTION_FINALE.md`, `conception/CADRAGE_AGENT.md`,
`conception/GUI_V1.md`, `docs/`) à ce que font le code et les artefacts sur disque :

1. **Création de la demande** par les trois voies de `new` : un fichier (`--demande`), le questionnaire
   (`--cadrer`), et l'agent de cadrage F (`--cadrer-avec-agent`). Couvre aussi l'écran de création de la GUI.
   Vérifie la provenance, le corpus figé et ce que A et B verront ou non.
2. **Le cycle** `run` : A produit, B critique, A révise avec une disposition par objection, B relit. Vérifie
   l'isolation (dossier jetable, environnement filtré par outil) et le contrat des objections.
3. **Incidents et reprise** : `resume`, `--reprocess`, le verrou. Contrôle en particulier qu'un appel dont l'issue
   est ambiguë n'est jamais rejoué.
4. **Sortie** : la promotion de la version examinée (pas de réécriture après la dernière revue), puis `bilan.md`,
   `show`, `decide` et `decisions.json`. « Terminé » doit rester distinct d'« accepté ».
5. **Liaison PWF du produit** : `dialogforge plan`, avec et sans `--link`, `--unlink` et `plan.json`.

Collaborations réelles à lire, dans `C:\Projets\essais-3-1\`. Aucune n'a jamais été liée à un plan :

| Dossier | Intérêt |
|---|---|
| `collab`, `collab-inverse` | Un cycle par sens A/B, sans décision |
| `pieges-souris`, `nextcloud-clients`, `revision-nextcloud\collab`, `gui-v1\collab`, `Creation-prompt-2` | Cycles menés jusqu'à une décision (`decisions.json`), jusqu'à 3 révisions |
| `Creation-prompt` | Arrêté en `WAITING_HUMAN` |
| `cadrage-lot4\produit-claude`, `cadrage-lot4\produit-codex` | Demandes créées par l'agent F, un outil chacune, jamais lancées. Protocole dans `reference/PROTOCOLE_CADRAGE_LOT4.md` |

## PWF : deux usages distincts, à ne pas confondre

**A. Le produit se lie à un plan** (`src/iabinome/planlink.py`, `docs/COMMANDES.md` § plan). La conception est
volontairement minimale : la liaison est facultative, le cycle ne lit jamais `plan.json`, et le produit n'écrit
jamais dans le plan. Il en produit un résumé que l'humain reporte à la main. Éprouve-la **sur une copie** d'une
collaboration terminée, placée dans ton dossier d'audit. Lie-la au plan du dépôt
(`--plan-root C:\Projets\DialogForge_2 --link 2026-09-18-dialogforge-v2`), ce qui ne fait que lire le plan, puis à
un identifiant inexistant, puis retire la liaison. La question est double : ce comportement tient-il ses
promesses, et le résumé est-il réellement utile à reporter ? Si tu juges l'intégration trop pauvre, dis ce qu'il
faudrait. Dis aussi en quoi ta proposition touche au principe « un seul propriétaire du plan » et aux cinq
interdits de `CLAUDE.md` §2.

**B. Le développement de DialogForge est piloté par PWF** (`.planning/2026-09-18-dialogforge-v2/`, les hooks,
`tools/claude-pwf.ps1`, PWF 3.20.1 épinglé). Vérifie les points suivants :
- `## Next Step`, le statut des phases, `progress.md` et l'historique Git racontent-ils la même chose ?
- Y a-t-il une seconde liste d'avancement ailleurs, que `CLAUDE.md` §0 interdit ?
- La taille des fichiers du plan reste-t-elle utilisable pour une reprise de session ? `progress.md` dépasse
  1 700 lignes.
- Les règles de `project/RULES.md` sont-elles encore toutes vraies, et sans doublon ?

## Déjà connus : ne les recompte pas comme des découvertes

Dis seulement si tu les juges mal priorisés :
- `open_questions` (provenance du cadrage) cite des questions auxquelles l'humain a répondu après une reprise du
  cadrage. La correction proposée, en attente du PO : prendre les `QUESTIONS_OUVERTES` du dernier tour de F.
- `corpus.build()` sur une liste vide.
- `status` lancé pendant un `run` d'un autre terminal peut échouer une fois.
- `ruff format --check` signale des fichiers, et la question n'a pas été tranchée.
- La marge de taille dans `src/` est d'environ 210 lignes sur le plafond de +2 500.

## Le rapport

Écris `C:\Projets\essais-3-1\audit-bout-en-bout\RAPPORT_AUDIT.md`, en français, et donne-le au PO en fin de
session.

1. **Synthèse**, en dix lignes au plus : l'état général, puis les trois points qui comptent le plus.
2. **Points à optimiser ou à modifier**, par priorité décroissante. Pour chacun :
   - le constat ;
   - la preuve (`fichier:ligne`, chemin d'artefact, ou commande relancée et sa sortie) ;
   - l'impact pour l'utilisateur ;
   - la modification proposée et son coût approximatif en lignes ;
   - ce qu'elle retire en échange, ou pourquoi rien ;
   - un conflit éventuel avec un interdit ou une règle.

   Sépare les défauts avérés (reproduits) des risques plausibles (déduits). Une simplification ou une
   suppression compte autant qu'un ajout.
3. **Parcours**, une ligne par étape : conforme, défaut ou non observable, avec la preuve.
4. **PWF**, les parties A et B.
5. **Non vérifié**, et pourquoi : quota, accès, temps.

Pas de note globale, pas de réécriture du code dans le rapport. Préfère peu de constats solides à une longue
liste. Si un point est une affaire de goût plutôt qu'un défaut, dis-le.

# Findings & Decisions — DialogForge V2

## Requirements
- Première livraison : **conception et synthèse sur corpus local fourni**, en terminal guidé.
- Recherche externe : profil distinct, à qualifier avant d'être proposé. Développement assisté : lot 4.
- Autorités séparées : PWF possède les phases du projet ; le moteur A/B possède son cycle local et
  ses appels ; les artefacts de revue possèdent les objections et leurs dispositions ;
  **l'utilisateur** possède l'acceptation du résultat.

## Research Findings
- **IAbinome, commit `4a11cc7eae47a4920b845fda6e65937557a967cf`** — HEAD du dépôt local le
  2026-09-18, identique au commit de référence de l'étude `astra/`. `git rev-list --count` = 0.
- **PWF `faf1a15a7dcc17a9e0f49760da0756d1a5d4609a`, v3.20.1** — HEAD amont le 2026-09-18, identique
  au commit étudié. Écart nul : aucune mise à jour à arbitrer.
- **Porte de validation héritée** : `ruff check .` + `mypy --strict` + pytest. Verte sur le commit
  de départ : 302 passés, 2 ignorés (privilège de lien symbolique absent, `WinError 1314`), 42
  sous-tests. Aucun échec préexistant, aucun test neutralisé.
- **Les vraies CLI ne sont jamais appelées** : `claude` et `codex` sont pourtant sur le `PATH`.
  Prouvé par leurres placés en tête de `PATH`, témoin resté vide sur la suite complète **et** sur
  le cycle de bout en bout. Les tests neutralisent aussi `settings.SEARCH_PATHS`, donc aucun
  `iabinome.toml` personnel ne peut modifier leur comportement.
- **Le moteur consomme un 5e appel `FINAL_A`** qui réécrit librement le document après une
  relecture favorable de B. C'est exactement ce que le point 1.3 du plan veut remplacer par la
  promotion de la version examinée. Confirmé sur pièce, pas déduit.
- **Le livrable porte déjà** l'avertissement « Ce document n'est pas approuvé : sa présence prouve
  que le cycle s'est achevé, rien de plus. » La distinction « terminé » ≠ « accepté » est tenue.
- **Route d'installation PWF** : seule la route plugin/marketplace livre les hooks `SessionStart`
  et les commandes `/plan-*`. La route skill autonome retenue ici n'a que des hooks à portée
  d'activation, enregistrés après la première invocation du skill dans la session.
- **Codex 0.155.0 sous Windows n'offre pas de lecture bornée par profil** (mesuré le 2026-09-21, sans quota) : un profil
  qui refuse `:root` échoue avec les deux backends (« Restricted read-only access requires the elevated Windows sandbox
  backend » / « elevated Windows sandbox requires effective `:root` read access »). Le refus d'un chemin existe mais pose
  des ACL `DENY` **persistantes** (groupe `CodexSandboxUsers`) et refuser un ancêtre empêche de lancer dans son fils.
  Le rejet initial des commandes de lecture vient de la couche politique d'exécution, pas du système de fichiers.
- **La correction (`windows.sandbox=elevated`) lit un vrai corpus en cycle A/B complet, pas seulement un témoin**
  (2026-09-22, mission 3.2 « révision d'un document existant ») : Codex exécute `Get-ChildItem` puis
  `Get-Content -LiteralPath corpus/fichiers/… -Raw` dans le dossier jetable du produit, « succeeded in 917ms »,
  contenu exact retourné (`appels/0001-A-…/stderr.txt`, lignes 79-87). Second scénario indépendant du témoin du 21 ;
  ne teste toujours pas la lecture d'un chemin hors du corpus.
- **Sessions reprenables, lues dans `--help` le 2026-09-24 (aucun appel)** : Claude 2.1.281 —
  `--session-id <uuid>`, `-r/--resume <id>`, `--fork-session`, `--no-session-persistence` (à retirer
  pour F), et `--input-format stream-json` (processus maintenu ouvert). Codex 0.155.0 — `exec` (sans
  `--ephemeral`) puis `exec resume [SESSION_ID] [PROMPT|-]` ; `resume` accepte `-m`, `-c`,
  `--ignore-user-config`, `--ignore-rules`, `--json`, **mais pas `--sandbox`** ; l'identifiant ne se
  fixe pas d'avance. Processus persistant côté Codex : `app-server`, expérimental. Base de la
  décision A3 (reprise par identifiant) ; la lecture seule en reprise n'est **pas** mesurée.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Python 3.12.5, venv local au dépôt | `requires-python >= 3.12` ; venv hors Git (`.gitignore`) |
| ruff 0.16.8, mypy 2.3.1, pytest 9.1.1 | Versions réellement installées. mypy 2.x est une majeure au-delà des relevés historiques du projet (1.x) : elle passe sans modifier le code |
| PWF copié dans `~/.claude/skills/planning-with-files` | Route « standalone » de `docs/installation.md`, appliquée depuis un clone détaché sur le commit épinglé ; contenu vérifié identique byte à byte |
| Cadrage guidé sans modèle ; format = repère (1.1, 2026-09-19) | Décisions et condition de réouverture dans `task_plan.md`. `framing.py` du prédécesseur réemployé pour l'idée (fichier direct ou cadrage, provenance), pas pour le code : il portait sessions, verrou, preuves d'usage et budget, tout ce que `CLAUDE.md` §2 interdit |
| Provenance = `provenance_demande.json`, lisible à l'œil | Un fichier, pas de base ; écrit entre `demande.md` et `etat.json` pour rester rejouable après un arrêt brutal |
| Plan nommé `2026-09-18-dialogforge-v2` | Créé par `init-session.ps1` amont, mode par défaut (ni `-Autonomous` ni `-Gated`) |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| Réponse accentuée du faux agent rendue en `DECODE_FAILED` | Encodage du tube Windows (cp1252) contre décodage UTF-8 des adaptateurs. **Corrigé à la source le 2026-09-19** (`tests/fakes.py` écrit des octets UTF-8) ; le lot 1 ajoutait justement des réponses accentuées. `PYTHONIOENCODING` reste posé dans le scénario, sans effet nécessaire |
| B réécrit l'énoncé de ses constats au tour suivant (revue réelle du 2026-09-05, 7 sur 7) | Contrat v2 : énoncé initial immuable, justification à part (1.2). Rejoué dans `tests/test_objections.py` |
| Le moteur hérité livrait une réécriture non relue (`FINAL_A`, 5e appel) | Supprimé le 2026-09-19 (1.3) : promotion de la version examinée + `bilan.md`. Un appel payant de moins par cycle |
| Aucun moyen de lire un résultat, de décider, ni de retrouver une collaboration (moteur hérité) | 1.4 : `show`, `decide`, `list`, `decisions.json` ; « terminé » distinct d'« accepté » |
| Sur `CONTRACT_ERROR`/`DECODE_FAILED`, seule sortie = nouvel appel payant, alors que la réponse est sur disque | 2.1 : `--reprocess`, retraitement local tracé |
| Un incident n'était pas expliqué à l'humain (payé ? cause ? suite ?) | 2.1 : `incidents.py`, sans coût ni heure déduits |
| Les agents tournaient dans le dossier de collaboration (journal de A, `appels/`, anciennes demandes à portée de B) | 2.2 : dossier jetable, copie du corpus seule |
| L'environnement complet du parent (session, jeton de messagerie, racine de plan) passait aux agents | 2.2 : liste de refus nominative, noms tracés dans `intention.json` |
| La liste de refus d'environnement était bâtie sur le seul hôte de la session (Claude) : un agent lancé depuis Codex héritait de `CODEX_SESSION_ID`/`CODEX_THREAD_ID`/`CODEX_PERMISSION_PROFILE` | 2.2 corrigé : noms ajoutés, pas de refus global ; `KEPT_ON_PURPOSE` justifie `CODEX_HOME` et `CODEX_MANAGED_PACKAGE_ROOT`. La liste reste incomplète par construction |
| Le résolveur public de plan PWF rend toujours 0 ; tout refus (inexistant, mal formé, ambigu) est une **sortie vide**, et un plan épinglé sans `task_plan.md` est rendu quand même | 2.3 : `planlink.resolve` traite le vide comme un refus, vérifie le nom rendu et `task_plan.md` |
| `configuration.json` a un schéma à clés exactes : y ajouter une référence facultative en ferait un fichier d'état à modifier pour la retirer | 2.3 : liaison dans `plan.json` — amendement du plan validé par le PO le 2026-09-19 |
| Les drapeaux de 2.2 (`--restricted`…, `--ephemeral --ignore-user-config`…) étaient lus dans `--help`, jamais éprouvés | 3.1 : acceptés par Claude 2.1.278 et Codex 0.155.0, cycles complets sans incident dans les deux permutations |
| Codex fait des recherches web en A, que `--sandbox read-only` n'empêche pas ; Claude n'en a pas | 3.1, décision du PO : facultatif et **fermé par défaut** (`web_access`, A et B), politique explicite dans l'argv des deux outils ; non éprouvé en réel |
| `--ignore-user-config` fait tourner Codex à `reasoning effort: none` au lieu de `medium` | 3.1, décision du PO : rien ne change par défaut, l'effort devient passable (`effort_a` / `effort_b`) et se valide contre le vocabulaire de chaque adaptateur, avant tout appel |
| Le filtre d'environnement de 2.2 était global : un jeton ou une clé d'un fournisseur allait chez l'autre, et `isolation.py` nommait les fournisseurs contre `CLAUDE.md` §6 | 3.1 : `EnvPolicy` par adaptateur ; le noyau ne lit que des politiques |
| Le `python`/`pytest` global résout `iabinome` vers l'ancien projet | Toujours `.venv/Scripts/python.exe -m pytest tests` |
| `reference/cycle_sans_fournisseur.py` rend rc=0 même en `ERROR` | Corrigé le 2026-09-19 : rc=1 hors de `AWAITING_APPROVAL` sans objection ouverte |
| `ruff format --check` signale 26 fichiers | Laissé ouvert : `ruff format` n'appartient pas à la porte historique du projet. À trancher explicitement, pas à subir |
| Codex ne lit pas le corpus sous `--ignore-rules` + `approval: never` (3.1, 2026-09-20) | Qualifié sans quota le 2026-09-21 : cause = politique d'exécution ; un profil borné n'est pas constructible (voir Research Findings). **Tranché par le PO** (`astra/07_recentrage_simplicite.md`) : petite correction ciblée (`windows.sandbox=elevated`), pas d'injection du corpus ni de profil de permissions. Qualifiée le 21, premier usage réel en 3.2 le 22 (web ouvert, pas de lecture de corpus local dans ce cas) |

## Resources
- Plan de mise en œuvre : `C:\Projets\DialogForge_Next\astra\06_plan_mise_en_oeuvre.md`
- Compte rendu de référence J0 : `reference/COMPTE_RENDU_J0.md`
- Scénario sans fournisseur : `reference/cycle_sans_fournisseur.py`
- PWF amont : https://github.com/OthmanAdi/planning-with-files (commit `faf1a15`, tag `v3.20.1`)

# Frontière des rôles — ce qui est obtenu, ce qui ne l'est pas

*Plan V2, point 2.2 — 2026-09-19. Écrit avant tout essai avec une CLI réelle : les garanties
des CLI ne sont pas acquises avant le lot 3, et ce document dit lesquelles restent à mesurer.*

## Ce que le programme fait lui-même (prouvé par des tests, sans fournisseur)

| Séparation | Mécanisme | Preuve |
|---|---|---|
| L'agent ne voit pas la collaboration | Il tourne dans un **dossier jetable hors de la collaboration** (`isolation.neutral_workdir`), qui ne contient qu'une **copie** de `corpus/fichiers/` — l'emplacement que les prompts nomment. Supprimé après l'appel, y compris sur exception. | `test_isolation.py::TestNeutralWorkdir` (un faux agent liste son dossier : `["corpus"]`, rien d'autre) |
| Écrire dans le corpus vu par l'agent n'atteint pas l'original | Copie, jamais lien symbolique ni lien dur | même classe ; contre-épreuve : liens durs → rouge |
| L'hôte n'est pas transmis | `transport.run(env=…)` avec `isolation.clean_env` : liste de refus **nominative** (session, jeton de messagerie, racine de plan, `PLAN_ID`, `PWF_*`, et pour un hôte Codex `CODEX_SESSION_ID`, `CODEX_THREAD_ID`, `CODEX_PERMISSION_PROFILE`). Jamais de refus global `CODEX_*` / `CLAUDE_*`. L'authentification, le lanceur et `PATH` sont conservés (tableau ci-dessous). | `TestEnvironment` ; les **noms** retirés (jamais les valeurs) sont inscrits dans `intention.json` |
| Un rôle sans séparation n'est pas lancé | Le prévol refuse un adaptateur qui ne déclare pas `enforces_read_only` et `fresh_session` — **avant tout appel, sans mutation** | `TestProfileCapabilities` |
| Le corpus modifié pendant l'appel est constaté | Contrôle complet du corpus **après** l'appel, avant toute lecture de la réponse : incident `SOURCES_MODIFIED`, réponse non retenue, jamais relancé tout seul | `TestSourcesAreChecked` |
| Le paquet de B est minimal | Son prompt porte la demande, la version examinée et les objections ouvertes avec les réponses de A — ni chemin d'appel, ni journal, ni prompt de A | `TestReviewerPackage` |

### Variables d'environnement conservées à dessein (`isolation.KEPT_ON_PURPOSE`)

| Variable | Pourquoi elle reste |
|---|---|
| `CODEX_HOME` | Là où Codex lit son authentification : `--ignore-user-config` n'ignore que `config.toml`, son aide dit « auth still uses `CODEX_HOME` ». La retirer déconnecte l'agent. |
| `CODEX_MANAGED_PACKAGE_ROOT` | Posée par le lanceur npm de Codex, **qui la réécrit pour son enfant** (`bin/codex.js`, lu le 2026-09-19) : elle décrit le paquet installé, pas la session de l'hôte. Retirée ou gardée, l'effet est nul ; gardée par prudence sur le lanceur. |
| `CLAUDE_CODE_OAUTH_TOKEN` | Authentification de Claude par jeton. |
| `CLAUDE_CODE_GIT_BASH_PATH` | Claude Code en a besoin pour démarrer sous Windows. |

**Provenance des noms.** Ceux de Claude ont été relevés dans un environnement réel ; ceux de
Codex (`CODEX_SESSION_ID`, `CODEX_THREAD_ID`, `CODEX_PERMISSION_PROFILE`, `CODEX_HOME`,
`CODEX_MANAGED_PACKAGE_ROOT`) ont été **signalés par la validation de 2.2** : cette session
n'a pas d'hôte Codex, aucun n'y a été observé directement. Tout nom nouveau se relève, se
justifie, puis s'ajoute — une liste de refus **incomplète par construction** : une variable
d'hôte qu'on n'a pas encore vue passe.

## Ce que le programme demande à la CLI (argv construit — prouvé par test, **pas mesuré en réel**)

| Adaptateur | Lecture seule | Session fraîche | Rien de l'utilisateur / de l'hôte |
|---|---|---|---|
| Claude (`claude --help` 2.1.278) | `--restricted`, `--tools "Read,Grep,Glob"` (`""` en `CONTEXT_ONLY`) | `--no-session-persistence` ; jamais `--resume`/`--continue` | `--restricted` (ignore réglages user/project/local, donc hooks), `--strict-mcp-config`, `--disable-slash-commands` |
| Codex (`codex exec --help` 0.155.0) | `--sandbox read-only` ; `-c features.shell_tool=false` en `CONTEXT_ONLY` | `--ephemeral` ; jamais `resume` | `--ignore-user-config`, `--ignore-rules` |

Le champ `Capabilities` dit ce que l'adaptateur **met dans son argv**, jamais ce que la CLI en
fait. `intention.json` garde l'argv demandé (`invocation_args`) : c'est une trace de la demande,
**pas une preuve des capacités effectives**.

## Ce qui n'est PAS obtenu

- **Aucun confinement du système d'exploitation.** Un agent qui écrit ou lit un **chemin absolu**
  n'est arrêté que par l'outil (`--restricted` confine les outils fichiers au dossier de travail
  selon son aide ; jamais vérifié ici). Le contrôle du corpus le **constate** après coup, il ne
  l'empêche pas. Le contrôle ne couvre que le corpus : `demande.md` et `etat.json` sont protégés
  par leurs empreintes à la reprise, pas pendant l'appel.
- **Les hooks et réglages de l'utilisateur** ne sont pas prouvés absents : `--restricted` (Claude)
  et `--ignore-user-config` (Codex) le promettent dans leur aide. Non éprouvé.
- **Le comportement de B lui-même** : rien ne garantit qu'il n'ait pas de mémoire propre au
  fournisseur (préférences de compte, mémoire persistante hors session). « Session fraîche » veut
  dire : le programme ne reprend aucune session et n'en laisse aucune.
- **Une CLI qui ignorerait un drapeau** : un drapeau inconnu fait échouer l'appel (`CLI_FAILED`,
  « inconnu » dans le catalogue des incidents) ; un drapeau **accepté mais sans effet** ne se voit
  pas d'ici.
- **Le dossier jetable est sous le dossier temporaire de l'utilisateur** : il ne contient rien de
  la collaboration, mais il n'est pas isolé du reste du disque.

## À vérifier au lot 3 (avec de vraies CLI, sur dossier jetable)

1. `claude -p --restricted --tools "Read,Grep,Glob" …` s'authentifie-t-il bien avec l'environnement
   filtré, y compris quand l'authentification passe par un fichier de l'utilisateur ? (`--restricted`
   ignore les *réglages*, pas censé les identifiants.)
2. Un reviewer Claude en `--restricted` peut-il lire `corpus/fichiers/` **et rien d'autre** ? Essayer
   un chemin absolu vers la collaboration.
3. `codex exec --ignore-user-config` garde-t-il le modèle passé par `-m` et l'authentification ?
4. Les hooks de l'utilisateur sont-ils réellement sans effet avec ces drapeaux ?
5. Sans variable `PLAN_ID`/`PWF_*`, un agent lancé depuis une session outillée se comporte-t-il
   comme hors de toute session ?
6. Un drapeau retiré ou renommé par une mise à jour de la CLI : l'échec est-il lisible ?

Tant que ces points ne sont pas mesurés, **aucune de ces protections n'est une garantie**.

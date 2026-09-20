# Frontière des rôles — ce qui est obtenu, ce qui ne l'est pas

*Plan V2, point 2.2 — 2026-09-19. Écrit avant tout essai avec une CLI réelle : les garanties
des CLI ne sont pas acquises avant le lot 3, et ce document dit lesquelles restent à mesurer.*

## Ce que le programme fait lui-même (prouvé par des tests, sans fournisseur)

| Séparation | Mécanisme | Preuve |
|---|---|---|
| L'agent ne voit pas la collaboration | Il tourne dans un **dossier jetable hors de la collaboration** (`isolation.neutral_workdir`), qui ne contient qu'une **copie** de `corpus/fichiers/` — l'emplacement que les prompts nomment. Supprimé après l'appel, y compris sur exception. | `test_isolation.py::TestNeutralWorkdir` (un faux agent liste son dossier : `["corpus"]`, rien d'autre) |
| Écrire dans le corpus vu par l'agent n'atteint pas l'original | Copie, jamais lien symbolique ni lien dur | même classe ; contre-épreuve : liens durs → rouge |
| L'hôte n'est pas transmis, ni un fournisseur à l'autre (3.1) | `transport.run(env=…)` avec `isolation.clean_env(environ, politique de l'adaptateur, politiques des autres)`. Le noyau ne nomme aucun fournisseur : chaque adaptateur déclare une `EnvPolicy`. Retirés à tous : `PLAN_ID`, `PWF_*` et les identifiants de **session** d'hôte. Retiré à chacun : tout ce qui appartient à **l'autre** fournisseur (jetons, chemins de configuration, clés d'API). Gardé chez lui, avec sa raison : son authentification, sa configuration, son lanceur. | `TestEnvironmentPerAdapter` ; les **noms** retirés (jamais les valeurs) sont inscrits dans `intention.json` |
| Le reviewer n'hérite pas du contexte du producteur ni du plan (2.3) | Le **même** filtre d'environnement pour A et B, `PLAN_ID` et `PWF_*` compris : plus strict que « selon le rôle » — aucun des deux n'a besoin du plan, qui reste l'affaire de l'humain (`plan`, `planlink.py`) | `test_isolation.py::TestEnvironment::test_the_reviewer_does_not_inherit_…` |
| Un rôle sans séparation n'est pas lancé | Le prévol refuse un adaptateur qui ne déclare pas `enforces_read_only` et `fresh_session` — **avant tout appel, sans mutation** | `TestProfileCapabilities` |
| Le corpus modifié pendant l'appel est constaté | Contrôle complet du corpus **après** l'appel, avant toute lecture de la réponse : incident `SOURCES_MODIFIED`, réponse non retenue, jamais relancé tout seul | `TestSourcesAreChecked` |
| Le paquet de B est minimal | Son prompt porte la demande, la version examinée et les objections ouvertes avec les réponses de A — ni chemin d'appel, ni journal, ni prompt de A | `TestReviewerPackage` |

### Séparation des secrets — variables gardées, par adaptateur (`EnvPolicy.kept`)

| Fournisseur | Gardée | Pourquoi |
|---|---|---|
| Claude | `CLAUDE_CONFIG_DIR` | Choisit le **compte** : le dossier de configuration et d'authentification. La retirer change de compte sans le dire. Elle n'existe pas chez Codex. |
| Claude | `CLAUDE_CODE_OAUTH_TOKEN` | Authentification par jeton. |
| Claude | `CLAUDE_CODE_GIT_BASH_PATH` | Claude Code en a besoin pour démarrer sous Windows. |
| Claude | `ANTHROPIC_API_KEY` | Authentification par clé d'API, quand c'est celle de l'utilisateur. |
| Codex | `CODEX_HOME` | Là où Codex lit son authentification : `--ignore-user-config` n'ignore que `config.toml`, son aide dit « auth still uses `CODEX_HOME` ». |
| Codex | `CODEX_MANAGED_PACKAGE_ROOT` | Posée par le lanceur npm de Codex, qui la réécrit pour son enfant (`bin/codex.js`, lu le 2026-09-19). |
| Codex | `OPENAI_API_KEY` | Authentification par clé d'API, quand c'est celle de l'utilisateur. |

Ce qui appartient à un fournisseur : les variables qui commencent par `CLAUDE` ou `ANTHROPIC_` pour
Claude, `CODEX_` ou `OPENAI_` pour Codex. Un processus Claude ne reçoit **aucune** variable de ce
second groupe, et inversement. **Limites** : ce partage suit des préfixes, pas une connaissance des
secrets — une clé d'un autre nom (`AWS_*`, un jeton générique) passe aux deux ; et **la provenance
des noms** n'est pas une mesure : ceux de Codex hôte ont été signalés par la validation de 2.2, aucun
n'a été observé directement ici. Tout nom nouveau se relève, se justifie, puis s'ajoute.

## Ce que le programme demande à la CLI (argv construit — prouvé par test, **pas mesuré en réel**)

| Adaptateur | Lecture seule | Session fraîche | Rien de l'utilisateur / de l'hôte |
|---|---|---|---|
| Claude (`claude --help` 2.1.278) | `--restricted`, `--tools "Read,Grep,Glob"` ; **avec `web_access`** `--tools "Read,Grep,Glob,WebSearch,WebFetch"` et `--allowedTools "WebSearch,WebFetch"` ; `--tools ""` en `CONTEXT_ONLY`, quoi qu'il arrive | `--no-session-persistence` ; jamais `--resume`/`--continue` | `--restricted` (ignore réglages user/project/local, donc hooks), `--strict-mcp-config`, `--disable-slash-commands` |
| Codex (`codex exec --help` 0.155.0) | `--sandbox read-only` ; `-c features.shell_tool=false` en `CONTEXT_ONLY` ; **toujours** `-c web_search=disabled`, ou `web_search=live` avec `web_access` (jamais `live` en `CONTEXT_ONLY`) | `--ephemeral` ; jamais `resume` | `--ignore-user-config`, `--ignore-rules` |

Le champ `Capabilities` dit ce que l'adaptateur **met dans son argv**, jamais ce que la CLI en
fait. `intention.json` garde l'argv demandé (`invocation_args`) : c'est une trace de la demande,
**pas une preuve des capacités effectives**.

## Ce qui n'est PAS obtenu

- **Frontière réseau.** L'accès web est **fermé par défaut** et **identique pour A et B** (décision du
  PO, 2026-09-19 ; `web_access`, figé à `new`). Fermé, la politique est explicite dans l'argv des deux
  outils, dans les deux sens. **Ouvert**, ce que contient le prompt peut sortir de la machine par une
  requête de recherche ou de lecture d'une page : il n'y a aucun confinement du réseau. **Fermé, rien
  ne le prouve non plus tant qu'un appel réel ne l'a pas montré** : `-c web_search=disabled` est la clé
  donnée par le PO, jamais éprouvée ici, et le prompt part de toute façon chez le fournisseur.
  Les recherches web relevées dans les essais 3.1 (6 par appel de A côté Codex) ont eu lieu **avant**
  ce réglage, sans clé `web_search`.
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

1. `claude -p --restricted --tools "Read,Grep,Glob" …` (et **avec** `WebSearch,WebFetch` +
   `--allowedTools`) s'authentifie-t-il bien avec l'environnement
   filtré, y compris quand l'authentification passe par un fichier de l'utilisateur ? (`--restricted`
   ignore les *réglages*, pas censé les identifiants.)
2. Un reviewer Claude en `--restricted` peut-il lire `corpus/fichiers/` **et rien d'autre** ? Essayer
   un chemin absolu vers la collaboration.
3. `codex exec --ignore-user-config` garde-t-il le modèle passé par `-m` et l'authentification ?
4. Les hooks de l'utilisateur sont-ils réellement sans effet avec ces drapeaux ?
5. Sans variable `PLAN_ID`/`PWF_*`, un agent lancé depuis une session outillée se comporte-t-il
   comme hors de toute session ?
6. Un drapeau retiré ou renommé par une mise à jour de la CLI : l'échec est-il lisible ?
7. Codex 0.155.0 accepte-t-il `-c web_search=disabled` et `-c web_search=live` (clé et valeurs), et
   `disabled` coupe-t-il **réellement** la recherche ? Le stderr compte les lignes `web search:`.
8. Claude : `WebSearch` et `WebFetch` fonctionnent-ils sous `--restricted` avec `--allowedTools`, ou
   faut-il autre chose ? Sans `web_access`, refusent-ils bien ?
9. Les niveaux d'effort déclarés (`Capabilities.effort_levels`) sont-ils tous acceptés par les CLI
   installées, et `--effort` / `model_reasoning_effort` ont-ils un effet visible ?
10. Un processus Codex, sans `CLAUDE_*` ni `ANTHROPIC_*`, garde-t-il son authentification ? Et
    inversement pour Claude sans `CODEX_*` ni `OPENAI_*`.

Tant que ces points ne sont pas mesurés, **aucune de ces protections n'est une garantie**.

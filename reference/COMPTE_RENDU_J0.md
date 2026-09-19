# Compte rendu de référence — lot 0 (J0 partiel)

Date : 18 septembre 2026. Machine : Windows 11, `C:\Projets\DialogForge_2`.
Plan de référence : `astra/06_plan_mise_en_oeuvre.md` du dossier `DialogForge_Next`.

**Périmètre : 0.1, 0.2 et 0.3. J0 n'est pas encore déclaré — il reste la vérification en
session neuve, décrite au §6.**

## 1. Dépôt (0.1)

| Point | Constat |
|---|---|
| Source | `C:\Projets\IAbinome`, clone local avec historique complet |
| Commit de départ | `4a11cc7eae47a4920b845fda6e65937557a967cf` |
| Écart avec la référence d'étude | **Aucun.** Le HEAD d'IAbinome *est* ce commit ; `git rev-list --count 4a11cc7..HEAD` = 0 |
| Branche de travail | `v2-socle`, créée depuis `master` |
| Remote | `origin` retiré après le clone. `git remote -v` ne rend rien : aucune écriture possible vers IAbinome |
| Non importés | `.venv` (absent du clone), `DIAGNOSTIC_CHROME_GPU.md` (non suivi), `iabinome.toml` (ignoré par `.gitignore`) |
| Secrets / config perso | Aucun `iabinome.toml` dans le dépôt, ni `~/.iabinome.toml` sur la machine. Seul `iabinome.toml.exemple` est versionné |
| Dépôts sources | Inchangés. IAbinome après opération : même HEAD, même unique fichier non suivi |

## 2. Référence technique (0.2)

### Versions reproductibles

| Outil | Version |
|---|---|
| Python | 3.12.5 (`requires-python >=3.12`) |
| ruff | 0.16.8 |
| mypy | 2.3.1 |
| pytest | 9.1.1 |
| iabinome | 0.1.0, installé en `-e .` dans `.venv` local au dépôt |

`mypy` 2.3.1 est une **version majeure au-delà** de celle des relevés historiques du projet
(1.x). Elle passe sans aucune modification du code : c'est un fait relevé, pas un risque ouvert.

### Porte de validation

La porte documentée par le projet (`CLAUDE.md` et `project/RULES.md`) est `ruff check .` +
`mypy --strict` + la suite de tests. Elle n'inclut pas `ruff format`.

| Commande | Résultat |
|---|---|
| `python -m ruff check .` | **All checks passed** |
| `python -m mypy` (strict, `src` + `tests`) | **Success: no issues found in 32 source files** |
| `python -m pytest -q` | **302 passés, 2 ignorés, 42 sous-tests passés** — 34 s |

**Aucun échec préexistant.** Les 2 tests ignorés le sont par l'environnement, pas par le code :
`tests/test_corpus.py:104` et `tests/test_workflow.py:366` demandent la création d'un lien
symbolique, refusée faute de privilège (`WinError 1314`). Aucun test n'a été neutralisé pour
obtenir du vert.

Écart mineur avec l'historique : `project/NOTES.md` relevait « 304 tests verts + 2 ignorés »,
on en compte 302 + 42 sous-tests. Aucun rouge ; l'écart tient au décompte des sous-tests.

`python -m ruff format --check .` signale 26 fichiers reformatables. **Ce n'est pas un échec de
la porte** : le projet n'a jamais utilisé `ruff format`. Reformater maintenant brouillerait les
diffs du lot 1 sans rien prouver. Point laissé ouvert, à décider explicitement.

## 3. Les vraies CLI ne sont jamais appelées

Point exigé par le plan, et **vérifié par l'expérience, pas par lecture de prompt** : `claude`
(`~/.local/bin/claude`) et `codex` (`~/AppData/Roaming/npm/codex`) sont bien présents sur le `PATH`
de cette machine.

Protocole : un répertoire de leurres placé **en tête du `PATH`**, contenant `claude.cmd` et
`codex.cmd` qui écrivent leur invocation dans un fichier témoin puis sortent en 0. Le leurre a
d'abord été déclenché volontairement, pour prouver que le témoin fonctionne. `shutil.which` côté
Python résout bien les leurres, et non les vraies CLI.

| Exécution sous leurres | Témoin |
|---|---|
| Suite complète `pytest` | **vide** — 302 passés, 2 ignorés |
| Scénario de bout en bout | **vide** — cycle complet, 5 appels |

Les tests substituent également les réglages personnels : `CliCase` neutralise
`settings.SEARCH_PATHS`, donc aucun `iabinome.toml` local ne peut changer le comportement.

## 4. Cycle complet avec faux adaptateurs

`reference/cycle_sans_fournisseur.py` pilote les **vraies** commandes `new`, `run` et `status`
de la CLI, avec `cli.ADAPTERS` substitué par deux faux adaptateurs — le mécanisme même de la
suite de tests. Rejouable à volonté :

```
python reference/cycle_sans_fournisseur.py [dossier_de_sortie]
```

Parcours obtenu, conforme au parcours par défaut visé : proposition A → critique B (`REVISER`,
1 constat `MAJOR` ouvert) → révision A → relecture B (`ACCEPTER`, constat `RESOLVED`) →
version finale.

| Mesure | Valeur |
|---|---|
| Code de sortie `run` | 0 |
| Statut final | `AWAITING_APPROVAL` — phase `CLOSED`, révision 1 |
| Constats ouverts | 0 |
| Appels résolus | A = 3, B = 2 |
| Appels réellement lancés sur disque | 5 |
| Artefacts | `echanges/0001-proposition-A.md`, `0002-critique-B.json`, `0003-revision-1-A.md`, `0004-critique-B.json`, `livrables/version_finale.md`, `etat.json`, `configuration.json`, 5 dossiers d'appel complets |

Le livrable porte l'avertissement `Ce document n'est pas approuvé : sa présence prouve que le
cycle s'est achevé, rien de plus.` — la distinction « cycle terminé » ≠ « accepté » est donc déjà
tenue par le socle.

### Deux observations pour le lot 1

1. **Le cycle consomme un cinquième appel après la relecture favorable de B** : un `FINAL_A` qui
   réécrit librement le document. C'est exactement ce que le point 1.3 du plan veut remplacer par
   la *promotion de la version examinée*. Le comportement est confirmé sur pièce, pas déduit.
2. **Encodage du faux agent sous Windows** : il écrit sa réponse par `sys.stdout.write`, donc dans
   l'encodage local (cp1252) d'un tube, alors que les adaptateurs décodent en UTF-8. Une réponse
   accentuée finit en `DECODE_FAILED`. C'est une propriété du **faux agent**, pas du moteur : le
   scénario fixe `PYTHONIOENCODING=utf-8` pour ses enfants. À garder en tête si le lot 1 ajoute
   des réponses simulées accentuées.

## 5. PWF (0.3)

### Version réellement utilisée

| Point | Constat |
|---|---|
| Installation préexistante | **Aucune.** `~/.claude/skills/` n'existait pas ; aucun plugin, aucun `.planning` sur la machine |
| Trace antérieure relevée | La **suite de tests de PWF** avait tourné sur la machine le 2026-09-18 en soirée, laissant des résidus sous `%TEMP%\pytest-of-schne\` et trois marqueurs dans `~/.cache/pwf-turn`. **Origine identifiée :** la session Claude Code qui a précédé celle-ci dans le même terminal — celle de l'étude `astra/` — a cloné l'amont (`git clone … planning-with-files.git pwf`) et exécuté sa suite de tests. À noter : l'étude déclare « installation de PWF : non effectuée », ce qui reste exact, mais elle ne mentionne pas ce clone ni cette exécution. Résidu de test, pas une intégration active — ces marqueurs portent des noms de 16 hex, alors que la v3.20.1 exige une clé de 64 hex |
| Amont | `github.com/OthmanAdi/planning-with-files`, `HEAD` = `faf1a15a7dcc17a9e0f49760da0756d1a5d4609a` = tag `v3.20.1` |
| Écart avec le commit étudié | **Aucun.** L'étude visait déjà ce commit : rien à arbitrer, aucune mise à jour subie |
| Version installée | `3.20.1` (métadonnées du `SKILL.md` installé) |
| Route retenue | « Standalone skill » de `docs/installation.md` : copie de `skills/planning-with-files` vers `~/.claude/skills/`, depuis un clone **détaché sur le commit épinglé** |
| Contrôle du contenu | `diff -r` amont/installé : **aucune différence**, 32 fichiers. Empreinte cumulée `135edc457b91aeec…` |

**Pourquoi pas la route plugin/marketplace**, pourtant recommandée par l'amont : elle suit la
branche `master` et se mettrait à jour d'elle-même, alors que le plan exige une version consignée.
Contrepartie assumée et vérifiée : la route retenue n'apporte **ni** hook `SessionStart`, **ni**
commandes `/plan-*`, et ses hooks sont à portée d'activation — ils ne s'enregistrent qu'après la
première invocation du skill dans une session.

### Plan de développement

`init-session.ps1 "DialogForge V2"` (mode par défaut, ni `-Autonomous` ni `-Gated`) a créé
`PLAN_ID=2026-09-18-dialogforge-v2` sous `.planning/`. Les lots 0 à 3 y sont inscrits comme
phases 1 à 4 ; le lot 4 y figure comme **extension identifiée, hors phases** — il ne peut donc pas
être coché par inadvertance.

Contrôle de lisibilité machine : `check-complete.sh` relit le plan rédigé en français et rend
« 0/4 phases complete, 1 in_progress, 3 pending ». Le fichier reste exploitable par l'outillage amont.

### Sélection et résolution — éprouvées, pas supposées

| Cas | Attendu | Obtenu |
|---|---|---|
| Plan unique, sans sélecteur | le bon dossier | `.planning/2026-09-18-dialogforge-v2`, code 0 |
| `PLAN_ID` explicite correct | le même dossier | idem, code 0 |
| `PLAN_ID` inexistant | **ne pas récupérer un autre plan** | **sortie vide**, code 0 |
| Deux plans, `PLAN_ID` inexistant | ne pas récupérer un autre plan | **sortie vide** — ni l'un ni l'autre |
| Deux plans, aucun sélecteur | refus plutôt qu'un choix arbitraire | **sortie vide**, malgré un `.active_plan` présent |
| `PLAN_ID` explicite + `task_plan.md` à la racine | le plan nommé l'emporte | le plan nommé |

**Le point à retenir : une sélection erronée ou ambiguë rend une sortie vide avec un code de retour
zéro.** Le critère du plan est satisfait — aucun autre plan n'est jamais récupéré — mais tout
appelant doit traiter la sortie vide explicitement, sans se fier au code de retour. C'est exactement
ce qu'exige le point 2.3 du plan pour la liaison du produit ; c'est ici vérifié sur le script
installé, et non lu dans une documentation.

**Conséquence datée pour ce dépôt :** la résolution sans sélecteur ne marche aujourd'hui que parce
qu'il n'y a **qu'un** plan. Le jour où un second plan apparaît, elle devient silencieusement vide.
Épingler `PLAN_ID=2026-09-18-dialogforge-v2` est donc la façon robuste d'ouvrir une session.

### Windows et Git Bash

`plan-doctor.sh` tourne sous Git Bash 5.2.26 (MINGW64) et rend :

- `PASS resolver` — dossier de plan actif correctement résolu ;
- `PASS injection` — le contexte de plan est bien émis (5 252 octets) ;
- `info` — surface d'installation détectée sous `~/.claude/skills/planning-with-files`.

Le contenu injecté à une session neuve a été relu directement : il porte le `## Next Step` du plan,
accents intacts, encadré par un nonce et **annoncé comme donnée non fiable, jamais comme
instruction** (`DATA ONLY`, `truncated=true` — la charge est bornée).

### Coût réellement mesuré des hooks

Mesure directe de `skill-hook.sh`, sur cette machine :

| Événement | Durée |
|---|---|
| `userprompt` | 506 ms |
| `pretool` | 586 ms |
| `posttool` | 494 ms |
| `stop` | 1 108 ms |
| `precompact` | 495 ms |

Le hook `PreToolUse` déclaré par le skill filtre `Write|Edit|Bash|Read|Glob|Grep` : en pratique,
**presque chaque appel d'outil paierait ~0,6 s**. Ce n'est pas rédhibitoire pour un hôte de
développement, mais cela confirme l'avertissement de l'étude — éviter l'activation de PWF chez un
reviewer ponctuel, où elle n'apporte rien.

### Autorité du plan dans le dépôt

`CLAUDE.md` du dépôt a été repris sur un point : l'avancement V2 appartient désormais au plan PWF,
et `project/NOTES.md`, `RECOLTE.md`, `DEPART.md` redeviennent la mémoire historique d'IAbinome —
plus des tableaux de bord de reprise. Sans cela, le dépôt aurait imposé **deux** listes d'avancement
concurrentes, ce que le plan interdit explicitement.

### Qualification des hooks — état au 2026-09-19

Essai en session neuve `ba8f9757-3248-43f2-9aa5-4ff1e359ae41` (Claude Code 2.1.278, cwd
`C:\Projets\DialogForge_2`, branche `v2-socle`). Résultat : **aucune injection automatique**.

Ce que le journal `--debug` de cette session établit, et qui invalide deux hypothèses successives :

| Fait relevé | Conséquence |
|---|---|
| `Using bash path: "C:\Program Files\Gitinash.exe"` | L'hôte utilise bien Git Bash |
| `Registered 5 hooks from skill 'planning-with-files'` | Les cinq hooks sont enregistrés, pas seulement déclarés |
| `sh` se résout en `/usr/bin/sh` dans un Git Bash **non-login** | L'hypothèse « `sh` introuvable » est **fausse** |
| Ligne de hook rejouée dans le shell et le dossier exacts de l'hôte | 654 ms, code 0, `hookSpecificOutput` valide avec l'injection |
| Trace de session : un seul hook exécuté, `stop`, 88 ms, `hookErrors` vide | Les hooks `UserPromptSubmit` et `PreToolUse` n'ont pas produit d'injection |

**Différence de protocole identifiée :** les hooks ont été enregistrés à 07:26:08, c'est-à-dire *au
moment de l'invocation du skill*. La session s'est arrêtée sur ce même tour. `UserPromptSubmit` ne
peut se déclencher qu'au tour **suivant**, et les hooks enregistrés en cours de tour n'ont pas
couvert les appels d'outil de ce tour-là. L'essai est donc **non concluant**, et non négatif : il
lui manque au moins un tour après l'invocation.

Ce qui reste vrai sans réserve : la ligne de hook amont fonctionne dans l'environnement de l'hôte.
Ce qui n'est pas établi : que l'hôte la déclenche effectivement sur `UserPromptSubmit` et
`PreToolUse`. **Les hooks ne sont pas déclarés validés.**

### Essai concluant — session `fa10ebab-fedf-42f6-9259-29770d640fde`

Protocole complet cette fois : invocation du skill au premier message, **puis un second message
ordinaire** provoquant des appels d'outil. Sept appels au total : `Skill`, `Bash` ×2, `Read` ×3,
`Glob`.

| Mesure | Valeur |
|---|---|
| Hooks exécutés par l'hôte | **2**, tous deux `stop` — 60 ms et 53 ms, `hookErrors` vides |
| `UserPromptSubmit` exécuté | **jamais** |
| `PreToolUse` exécuté | **jamais**, malgré six appels d'outil couverts par son filtre |
| `PostToolUse` exécuté | **jamais** |
| Injections `BEGIN-PWF-DATA` | **0** |

**Conclusion, cette fois sans réserve de protocole :** sur Claude Code 2.1.278, avec PWF installé
en skill autonome, seul l'événement `Stop` est réellement exécuté. Les trois événements qui portent
l'injection du plan ne le sont jamais, bien qu'ils soient enregistrés (`Added session hook for
event UserPromptSubmit…`, journal `--debug` de l'essai précédent).

**Sur les 53-60 ms du `stop` qui s'exécute.** Mesures comparatives de la même ligne de hook :

| Conditions | Durée | Sortie |
|---|---|---|
| Depuis la racine du dépôt | ~1 060 ms | 193 octets |
| Depuis un autre dossier | ~140 ms | **0 octet** |

Le `stop` de la session est plus proche du second cas : il sort sans rien faire. L'explication la
mieux étayée est la garde en tête de `skill-hook.sh`, qui sort immédiatement quand ni `PLAN_ID` ni
`PWF_PLAN_ROOT` ne sont dans l'environnement du hook **et** que son dossier courant ne contient ni
`task_plan.md` ni `.planning`. La trace ne consigne ni le dossier ni l'environnement du hook :
c'est l'hypothèse la mieux soutenue, pas un fait prouvé.

### Réserve retenue

L'**injection automatique du plan par les hooks n'est pas qualifiée** sur cet hôte. Elle n'est pas
déclarée acquise, et le critère n'a pas été abaissé pour obtenir un vert.

Ce qui fonctionne et sur quoi la reprise repose réellement :

- la résolution du plan par les scripts amont, éprouvée sur six cas dont la sélection erronée ;
- le `CLAUDE.md` du dépôt, qui fait du plan PWF l'autorité unique de l'avancement et impose sa
  lecture en début de session ;
- l'essai en session neuve : la bonne prochaine étape **a bien été retrouvée**, deux fois.

Ce qui est perdu tant que la réserve tient : la réinjection automatique du plan après compactage ou
perte de contexte. La parade est la relecture explicite du plan, déjà inscrite dans `CLAUDE.md`.

Deux pistes restent ouvertes, aucune engagée : la route plugin/marketplace, seule à livrer les
hooks au démarrage d'après l'amont — au prix du suivi de `master` ; et une déclaration de hooks
locale appelant les scripts amont par chemin absolu.

## 6. Reste à faire pour déclarer J0

Un seul point, et il exige une **nouvelle session** de l'hôte de développement — il ne peut pas être
prouvé depuis la session courante :

- **Reprise en session neuve.** Ouvrir une session dans `C:\Projets\DialogForge_2`, vérifier que la
  bonne prochaine étape est retrouvée et que les hooks réellement nécessaires se déclenchent.
  Rappel de la limite déjà établie : sur la route standalone, les hooks ne s'enregistrent
  qu'**après** la première invocation du skill dans la session.

La vérification est outillée : `sh reference/verifier_reprise_pwf.sh`, à lancer depuis Git Bash
après l'essai. Elle contrôle cinq points — version installée, résolution nominale, sélection erronée
sans repli, `## Next Step` non vide, et surtout **la preuve que les hooks se sont déclenchés en
session**. Cette preuve est un marqueur de tour nommé par une clé de 64 hex, dérivée de l'identité
de session transmise par l'hôte : un appel manuel des scripts n'en produit aucun, et les marqueurs
de 16 hex laissés par la suite de tests amont ne comptent pas.

Avant l'essai, le script rend 4 points verts et **le cinquième rouge** — c'est ce basculement qui
constitue la preuve, et non une impression de bon fonctionnement.

Tant que cette vérification n'est pas faite, **J0 n'est pas atteint** et le lot 1 n'est pas ouvert.

## 7. Plugin PWF local épinglé — préparation, sans qualification de session

La route retenue pour le prochain essai est le **plugin local Claude Code**, et non le marketplace :
la copie complète et inchangée de l'amont est dans
`tools/planning-with-files/`. Elle provient de
`https://github.com/OthmanAdi/planning-with-files`, commit
`faf1a15a7dcc17a9e0f49760da0756d1a5d4609a` (tag `v3.20.1`).

Elle contient notamment `.claude-plugin/plugin.json`, `hooks/hooks.json`, `commands/`, `skills/`,
`scripts/`, les traductions, la documentation et les tests : **728 fichiers dans le checkout
source et 728 dans la copie locale**, avec 0 divergence SHA-256 contrôlée contre le checkout détaché.
La copie est ignorée par Git comme expliqué ci-dessous. Les scripts amont n'ont
pas été adaptés. Le manifeste déclare bien `planning-with-files` version `3.20.1` et son JSON, ainsi
que celui des hooks, ont été lus avec succès.

La copie est volontairement exclue de Git par `tools/planning-with-files/` : elle reste complète
localement sans mélanger l'amont aux fichiers du produit. Pour la reconstruire à l'identique, cloner
l'URL ci-dessus, exécuter `git checkout --detach faf1a15a7dcc17a9e0f49760da0756d1a5d4609a`, puis
extraire `git archive --format=tar faf1a15a7dcc17a9e0f49760da0756d1a5d4609a` dans
`tools/planning-with-files/`. Ne jamais lancer une mise à jour implicite ni modifier cette copie.

Le seul point d'entrée du dépôt est :

```powershell
.\tools\claude-pwf.ps1
```

Il ouvre la session interactive Claude demandée par l'utilisateur avec
`--plugin-dir tools/planning-with-files`, depuis `C:\Projets\DialogForge_2`. Il épingle, **pour le
processus enfant seulement**, `PLAN_ID=2026-09-18-dialogforge-v2`, `PWF_PLAN_ROOT` à la racine du
dépôt, le répertoire Git Bash (`C:\Program Files\Git\bin`) dans `PATH`, et le Python `.venv` comme
interpréteur PWF de confiance lorsqu'il est présent. Il ne modifie ni `PATH`, ni configuration Claude,
ni plugin marketplace à l'échelle de la machine.

Le skill autonome préexistant sous `~/.claude/skills/planning-with-files` est conservé. Son propre
frontmatter amont contient une garde qui quitte dès que `CLAUDE_PLUGIN_ROOT` est défini ; le lanceur
le définit sur la copie locale pour le processus enfant. Les hooks du standalone ne doivent donc pas
dupliquer ceux du plugin dans cette session. Les deux surfaces de skill peuvent néanmoins rester
découvrables ; les commandes du plugin sont namespacées. Cette isolation locale ne prouve pas encore
le comportement du chargeur dans une vraie session.

### Contrôles exécutés sans fournisseur

- `tools\claude-pwf.ps1 --version` : Claude Code `2.1.278`, sortie 0 ; aucun prompt ni appel modèle.
- Résolution par les scripts **copiés** : le sélecteur attendu retourne
  `C:/Projets/DialogForge_2/.planning/2026-09-18-dialogforge-v2` ; le sélecteur inexistant retourne
  une sortie vide, code 0.
- `claude --help` ne contient pas `--init-only` dans cette CLI. Malgré la documentation officielle
  actuelle, cet argument n'a pas été lancé sur ce binaire local.

`reference/verifier_reprise_pwf.sh` n'est pas utilisé pour cette route : il cible explicitement
`$HOME/.claude/skills/planning-with-files` et ne peut donc pas attester le plugin local. Aucune
injection, aucun hook, aucune reprise après compactage n'est affirmé sur la seule base de ces
contrôles hors session.

### Essai interactif restant à l'utilisateur

L'utilisateur peut lancer, dans un terminal PowerShell, la commande ci-dessus — ou, pour conserver
une trace locale à inspecter :

```powershell
.\tools\claude-pwf.ps1 --debug-file .\pwf-plugin-debug.log
```

Dans cette nouvelle session, confirmer l'enregistrement et l'exécution effective des hooks du plugin
sur au moins un tour suivant le démarrage, puis inspecter la trace. Tant que cet essai réel n'est pas
fait, la réserve J0 demeure et le lot 1 reste fermé.

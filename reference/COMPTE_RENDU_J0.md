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

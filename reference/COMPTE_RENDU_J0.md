# Compte rendu de référence — lot 0 (J0 partiel)

Date : 18 septembre 2026. Machine : Windows 11, `C:\Projets\DialogForge_2`.
Plan de référence : `astra/06_plan_mise_en_oeuvre.md` du dossier `DialogForge_Next`.

**Périmètre de cette séance : 0.1 et 0.2. Le 0.3 (PWF) n'est pas fait — J0 n'est donc pas atteint.**

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

## 5. Reste à faire pour déclarer J0

- **0.3 — PWF.** Non installé sur cette machine : `~/.claude/skills/` est vide. L'étude a lu le
  dépôt amont à distance au commit `faf1a15…` (v3.20.1) sans rien installer. Restent à faire :
  installation, relevé de la version réellement utilisée, création du plan portant les lots 0 à 3,
  sélection explicite de la racine et du plan, puis épreuve de reprise dans une **nouvelle**
  session et vérification des hooks en session réelle.

Tant que cette qualification n'est pas obtenue, **J0 n'est pas atteint** et le lot 1 n'est pas
ouvert.

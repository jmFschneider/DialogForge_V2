# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. **Historique → `session_log.md`. Règles → `RULES.md`.**
> Dernière mise à jour : 2026-09-05, fin de session

---

## Prochaine action — une seule

**`CONTEXT_ONLY` en mission réelle.** C'est le seul mode que `README.md` documente sans qu'aucune
mission ne l'ait exercé : les deux adaptateurs le déclarent, la suite de tests le couvre, et rien
d'autre. Le README le dit explicitement — l'objectif est qu'il n'ait plus à le dire.

Ce qu'il faut regarder, et qu'aucun test ne peut voir : **B rend-il encore une revue utile sans ses
outils ?** S'il ne peut plus ouvrir le corpus, sa critique peut se vider de substance — ce serait un
résultat, pas un échec, et il conditionne le choix par défaut de `--reviewer-access`.

**Le mode n'est pas symétrique, et c'est décisif pour lire le résultat.** Côté outil 1, `--tools ""`
est documenté comme désactivant **tous** les outils. Côté outil 2, `features.shell_tool=false` n'en
retire **qu'un sur 38** — `browser_use`, `unified_exec`, `view_image` et sept autres restent. Un
`CONTEXT_ONLY` complet de ce côté n'a jamais été essayé (`CARACTERISATION_CLI.md`). **Donc : mettre
B côté outil 1**, sinon on mesure un mode à moitié appliqué en croyant mesurer le mode.

*Cet essai alimente aussi **C-06**, qui ne se ferme qu'après caractérisation des modes restreints
sur les versions installées — aujourd'hui `2.1.261` et `0.153.2`.*

**Recette.** Reprendre la mission de recherche, seul essai dont on ait un point de comparaison
chiffré (`REVISER`, 7 constats, revue de 5 888 o) :

```
python -m iabinome new <jetable>/context-only \
    --demande conception/essais/2026-09-04-demande-recherche.md \
    --kind recherche --reviewer-access context-only \
    --agent-a codex --agent-b claude --model-b sonnet \
    --source-root . --source-list conception/essais/2026-09-04-corpus-liste.txt \
    --max-revisions 0
python -m iabinome run <jetable>/context-only --timeout 600
```

**Autorisation de dépense à demander au PO.** ~700 s de temps fournisseur.

**Ensuite** : un crash provoqué en cours d'appel — la reprise après arrêt brutal reste prouvée par
la seule suite de tests.

**Ordres de grandeur mesurés**, pour chiffrer une dépense : ~150 s par appel de A côté outil 2,
~130 à 190 s côté outil 1 ; **~260 à 370 s pour un appel de B côté outil 1**. Cycle sans révision
≈ 700 s, avec une révision ≈ 1 040 s. **`--model-b sonnet` est obligatoire** : le défaut `fable`
n'a pas de crédits sur ce compte.

---

## Contraintes acquises — à ne pas redécouvrir

**`corpus.py`** — les chemins logiques sont **canonisés en forme POSIX** au manifeste. Sans cela,
`docs\note.md` ou `./note.md` étaient persistés tels quels puis comparés à leur forme posix par le
balayage : fichier déclaré **surnuméraire au premier `run`**, collaboration créée sans erreur et morte
avant son premier appel. C'est aussi ce que la portabilité exige.

**`lock.py`** — sur Windows, **ne jamais `os.kill(pid, 0)`** : l'implémentation y appelle
`TerminateProcess`, signal `0` compris. Vivacité par `ctypes`/`OpenProcess`, mais un PID terminé y
reste **vivant tant qu'un handle est ouvert**. Acquisition par `O_CREAT | O_EXCL` ; récupération d'un
verrou mort **sous jeton exclusif** `verrou.json.recuperation` ; libération vérifiée sur le `lock_id`.
**Un `verrou.json` tronqué bloque définitivement, et c'est délibéré** — le récupérer effacerait celui
d'un détenteur vivant surpris dans la même fenêtre. **Ne pas « réparer » cela.**

**`transport.py`** — `taskkill /F /T` sous Windows, `os.kill(-pid, 9)` sous POSIX (`SIGKILL` n'est pas
nommé : absent de Windows, il ferait échouer `mypy`). **Branche POSIX écrite, non testée.** Prompt par
`stdin_text`. Nettoyage borné par deux échéances communes (`CLEANUP_LIMIT_SECONDS` = 12 s) ;
`STREAMS_UNCLOSED` si un flux reste ouvert, `STREAM_FAILED` si une pompe a échoué — **dans les deux
cas, aucun `resultat.json`**. Les descripteurs **ne sont pas fermés sous un lecteur vivant** :
conséquence assumée, un descendant survivant garde `stdout.txt` ouvert et le dossier n'est pas
effaçable ; un test doit alors utiliser `TemporaryDirectory(ignore_cleanup_errors=True)`.

**`workflow.py`** — `_Engine` porte le contexte. **Aucun compteur de garde** sur la boucle. Ordre
imposé sous verrou : `recheck` → **`check_corpus`** → `intervene` → `gate` → dispatch. Le corpus passe
**avant l'intervention** pour que le code de sortie 1 (« refus avant mutation ») dise la vérité.
`read_result` est appelé **avant toute branche** de reprise, `RESPONSE_STORED` comprise, pour son
`IntegrityError` seul. `command()` est résolu **avant le premier octet écrit**. La porte n'accepte que
`READY` sans appel courant et `RUNNING` avec ; `ERROR` n'en sort que par `_RELAUNCHABLE`.

**`contracts.py`** — CRLF→LF est une **tolérance** sans défaut observé. **Le bloc entouré de prose,
lui, a un défaut mesuré deux fois** : B fait précéder sa revue d'une phrase où il nomme un outil de
son propre harnais (`ReportFindings`) et s'explique de ne pas s'en servir — **2 fois sur 4 appels de B
côté outil 1**. `_strip_fence` ancre *première clôture → dernière clôture*, **jamais un comptage** : B
a le droit de citer du markdown dans `analysis`, et compter y découperait au mauvais endroit.
**Sans balise, rien n'est cherché** — préfixe, suffixe, clôture inachevée et étiquette autre que
`json` restent des refus. `transformations` et `had_bom` existent mais **ne sont consignés nulle
part** (D-8b). `Review.to_dict()` est la forme canonique écrite dans `echanges/` — jamais le texte de
B. **Sévérité omise ⇒ `UNKNOWN` *et* `OPEN`** : la tolérance ne doit pas servir à fermer un constat.

**`prompts.py`** — **chaque** prompt de A nomme `IABINOME:DOCUMENT` et `IABINOME:QUESTION` en toutes
lettres ; le schéma de revue est dans celui de B. La frontière d'effets y porte sur l'**écriture** :
lire le corpus est explicitement ouvert. Chacun de ces trois points a coûté une mission réelle.

**`adapters/`** — `base.py` est **publié** (§13) : le modifier coûte une migration. `command()` résout
par `shutil.which()` **à chaque appel**. `AdapterError` est le type nommé attrapé à la frontière.
**Le défaut de B côté outil 1 (`fable`) n'a pas de crédits sur ce compte** — surcharger `--model-b`,
ou le poser une fois pour toutes dans `iabinome.toml`. **Les deux vraies CLI sont sur le PATH** :
tout test doit substituer `cli.ADAPTERS`, sans quoi il appelle un vrai fournisseur.

**`settings.py`** — le fichier de configuration ne fournit que des **défauts au `new`** (plus
`timeout` à `run`/`resume`). Il ne relit rien ensuite : `configuration.json` est la seule vérité
d'une collaboration créée. **Aucun chemin ne s'y règle** (reproductibilité), **clé inconnue = refus**
en code 1, et la commande annonce le fichier retenu sur `stderr`. `SEARCH_PATHS` est un attribut de
module **que tout test de la CLI doit vider**, comme `cli.ADAPTERS`.

**`cli.py`** — ne lit ni n'écrit **aucun état** : `cmd_resume` valide ses arguments et transmet.
Depuis le fichier de configuration, `--agent-a/-b`, `--kind` et `--reviewer-access` ne sont plus
`required=True` : leur absence est constatée par `cmd_new`, donc en **code 1**, plus en code 2.
Codes de sortie : `0` AWAITING_APPROVAL · `1` refus avant mutation · `2` argparse · `3` INTERRUPTED ·
`4` ERROR · `5` WAITING_HUMAN.

**Tests** — `fakes.FakeAdapter.calls` compte des **résolutions**, borne supérieure des appels partis ;
`fakes.launched_calls()` lit le disque pour la mesure exacte. Deux points d'observation distincts :
`observed_status` y voit `READY` (résolution avant mutation), `status_marker` fait relire `etat.json`
**par le processus lancé**, qui y voit `RUNNING`. Ne pas les fusionner.

**Un fait de plateforme** — `Path.glob` est **insensible à la casse sous Windows** : ne jamais s'en
servir pour sélectionner par un champ.

**D-2 dit vrai ; c'est sa « correction » du 2026-09-04 qui était fausse** — remesuré des deux côtés :
sur quota, **les deux outils rendent `1`**. Outil 1 met son message sur `stdout` (146 o, `stderr`
vide), outil 2 sur `stderr` (4 115 o, `stdout` vide). Dans les deux cas `CLI_FAILED` →
`INTERRUPTED`, relançable, **rien de payé**. Ce qui diffère est le flux, jamais le code. *Ne pas
rouvrir sans une mesure par redirection vers un fichier — un `$?` après un tube rend celui du tube.*

---

## État courant

- **Étapes 0 et 1 closes.** Spécification : `conception/CONCEPTION_FINALE.md`.
- **Étape 2, lots 1 à 11.** C-01 à C-10, N-01, N-02, D-4 à D-8 fermés. **C-11 clos** : quatre
  missions réelles menées à terme, boucle de révision comprise.
- **Restent hors de tout essai réel** : `CONTEXT_ONLY` et un crash provoqué. *`1→1` et `2→2` sont
  écartées, pas en attente.*
- **Suite : 304 tests verts** + 2 ignorés (liens symboliques, privilège absent), `ruff` et
  `mypy --strict` verts. **2 968 lignes brutes / 1 927 en code effectif.**
- **Taille : tranchée, question close.** « Rien tout simplement » — décision du PO, 2026-09-04. Ne pas
  rouvrir sans un fait nouveau.
- **`README.md` est l'aide utilisateur** et remplace le `GUIDE.md` prévu. `iabinome.toml.exemple` est
  le modèle versionné ; `iabinome.toml` est ignoré par git.
- **C-06 reste un risque accepté, pas un défaut à corriger.** Toute mission réelle se fait dans une
  collaboration **jetable, hors de tout dossier de valeur**.
- Le dépôt n'a **pas de remote** — décision reportée.

## Décisions actées

- **Bloc clôturé entouré de prose : accepté** — voie B, PO, 2026-09-05. §6 et §7 ter
  d'`OBSERVATIONS_MISSION_REELLE.md`. Question close.
- **`A == B` n'est pas interdit par le code, mais n'est pas un usage retenu** (PO, 2026-09-05) :
  `1→1` et `2→2` ne seront pas payées. Le risque d'auto-révision porte sur le **modèle**, pas sur
  l'outil, et `A == B` a été la seule configuration exécutable pendant les trois heures de quota du
  2026-09-05. Motif complet dans `RULES.md`.
- **Le fichier de configuration donne des défauts, jamais un état** (PO, 2026-09-05) : lu au `new`
  seulement, aucun chemin réglable, clé inconnue refusée.
- **Recherche au périmètre, sans accès externe en V0.1.** Réouverture : §12.1.
- **La relecture croisée est rouverte** depuis le 2026-09-05, sa condition s'étant réalisée.
- Paramètres fixés : UTF-8 sans BOM pour les artefacts du programme · corpus copié **octet pour
  octet** · 8 MiB par flux · **Windows testé, POSIX écrit non testé**.

## Rappels actifs

- **Les collaborations d'essai sont dans le dossier temporaire de session**, sous
  `…\Temp\claude\C--Projets-IAbinome\<uuid-de-session>\scratchpad\essai\`. **Elles ne survivront pas à
  la session.** Entrées et sorties utiles sont conservées dans `conception/essais/` : une mission s'y
  **reconstruit**, elle ne s'y reprend pas.
- Les quatre dossiers `C:\Projets\DialogForge*` sont en **lecture seule**. Point d'entrée du gel :
  `C:\Projets\DialogForge\ARRET_REFACTORING.md`.
- La mission DialogForge `e35cfcf1-47e5-4354-a4b1-d40235b8e3cf` est **en pause**, pas annulée. Elle
  redémarrerait seule si on la reprenait.
- Reporté, tracé : la colonne **Code** de l'inventaire plus longue que **Prompt** — après la phase 2.
- **Seconde passe de relecture prévue, ciblée** : les écarts retenus sont-ils détectés par un test, et
  quelles garanties annoncées restent sans couverture. Pas une revue générale des tests.

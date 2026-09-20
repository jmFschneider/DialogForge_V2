# Protocole fournisseur du 3.1 — points 7 à 10 de `FRONTIERE_ROLES.md`

*Version 2, 2026-09-20, après la revue de Codex (cinq corrections retenues). **Précontrôle amendé le 2026-09-20 (session
documentation)** : il comparait `HEAD` et répondait « inchangé » même avec des modifications non commitées ; il compare
maintenant l'arbre de travail. Écrit pour le commit **`dda7a54`**
(référence des essais réels). **Rédigé, pas lancé** : aucune commande ci-dessous n'a été exécutée avec un
fournisseur. Sont éprouvés **sans quota** : la commande `new` du mini-cycle, la création du corpus et du canari,
le lecteur de flux sur un fichier synthétique, la restauration de l'environnement. Fait pour être lancé **par le
PO**, avec ses accès.*

**Coût : environ 6 appels** — quatre appels web courts (Codex fermé/ouvert, Claude fermé/ouvert) et un mini-cycle
de deux appels (A puis B ; un troisième si B demande une révision). Aucun appel dédié à l'effort : il est porté
par le mini-cycle. Les diagnostics supplémentaires ne sont faits **qu'en cas d'écart**.

**Un écart se rapporte tel quel, il ne se corrige pas à l'aveugle** (3.1 : corriger uniquement les
incompatibilités constatées). Pas de nouveau cycle éditorial.

## Avant de commencer

**Ouvrir un PowerShell jetable** — `pwsh -NoProfile` dans une nouvelle fenêtre, fermée à la fin. Deux raisons :
il ne charge pas votre fonction `claude` (qui ne transmet pas stdin), et les variables posées par l'étape 5
disparaissent avec lui ; l'étape 5 les restaure de toute façon.

```powershell
$codex  = "C:\Users\schne\AppData\Roaming\npm\codex.cmd"   # chemins complets : rien ne dépend du PATH
$claude = "C:\Users\schne\.local\bin\claude.exe"
$cm     = "claude-sonnet-5"                                 # modèle précis : l'alias `sonnet` ne prouve pas lequel tourne
$xm     = "gpt-5.6-terra"
$env:CLAUDE_CONFIG_DIR = "$HOME\.claude"                    # le compte qui portera le quota (ou .claude-thermique)
Test-Path $codex, $claude                                    # attendu : True, True
cd C:\Projets\DialogForge_2 ; git rev-parse --short HEAD     # noter la révision exacte sur laquelle l'essai est lancé
git merge-base --is-ancestor b36515c HEAD ; $LASTEXITCODE    # attendu : 0 — le protocole version 2 est bien présent
git status --short                                            # noter ce qui n'est pas commité : le mini-cycle de l'étape 5 tourne sur l'ARBRE DE TRAVAIL
git diff --quiet dda7a54 -- src pyproject.toml iabinome.toml.exemple ':!src/iabinome/cli.py'
$LASTEXITCODE                                                 # attendu : 0 — le code qui parle aux fournisseurs est celui de dda7a54, commité ou non
git diff --stat dda7a54 -- src/iabinome/cli.py                # cli.py exclu ci-dessus : depuis dda7a54 on n'y a ajouté que des textes d'aide (--help), sans changer un comportement
cd C:\Projets\essais-3-1\protocole
$base = @("-p","--model",$cm,"--restricted","--strict-mcp-config","--no-session-persistence","--disable-slash-commands")
```

Les arguments sont **exactement** ceux que les adaptateurs construisent (imprimés sans appel le 2026-09-20),
sauf `--output-format stream-json --verbose`, ajouté aux étapes 3 et 4 pour **observer** les outils, pas pour
les changer. L'environnement n'est pas filtré aux étapes 1 à 4 : c'est l'étape 5 qui éprouve le filtre.

Si `claude-sonnet-5` est refusé (« issue with the selected model »), c'est sans coût : le noter, et rejouer avec
l'alias `sonnet` **en le disant** dans les résultats.

## Zéro quota — déjà fait (2026-09-20)

`claude --effort minimal --version` → `Warning: Unknown --effort value 'minimal' — ignoring it and using the
default effort. Valid values: low, medium, high, xhigh, max.` Le vocabulaire de Claude est confirmé par sa CLI, et
**Claude n'échoue pas** sur une valeur inconnue : il l'ignore et paie au niveau par défaut — c'est pourquoi le
produit valide **avant** l'appel.

## Point 7 — Codex : `web_search=disabled` et `web_search=live` (étapes 1 et 2)

Le prompt exige une recherche, pour qu'un « live » sans recherche ne soit pas pris pour un succès.

```powershell
$q = "Cherche sur le web la version stable actuelle de GIMP sur son site officiel. Cite l'URL. 3 lignes maximum."

# Étape 1 — fermé
$q | & $codex exec -m $xm --sandbox read-only --skip-git-repo-check --ephemeral --ignore-user-config --ignore-rules -c web_search=disabled - 2> 1-codex-ferme.err > 1-codex-ferme.out
"recherches web (attendu 0) : " + (Select-String -Path 1-codex-ferme.err -Pattern '^web search:').Count
Get-Content 1-codex-ferme.out

# Étape 2 — ouvert
$q | & $codex exec -m $xm --sandbox read-only --skip-git-repo-check --ephemeral --ignore-user-config --ignore-rules -c web_search=live - 2> 2-codex-ouvert.err > 2-codex-ouvert.out
"recherches web (attendu >= 1) : " + (Select-String -Path 2-codex-ouvert.err -Pattern '^web search:').Count
Get-Content 2-codex-ouvert.out
```

| Étape | On attend | Un écart veut dire |
|---|---|---|
| 1 | 0 recherche | `>= 1` : **`web_search=disabled` ne coupe rien** — « fermé par défaut » est faux côté Codex |
| 1 | une erreur sur la clé ou la valeur | la clé n'est pas `web_search`, ou ses valeurs diffèrent — coller le message |
| 2 | `>= 1` recherche et une URL | `0` : la clé n'a pas d'effet, ou le modèle a répondu de mémoire — **rejouer avec un prompt plus contraignant avant de conclure** |

## Point 8 — Claude : `WebSearch` / `WebFetch` sous `--restricted` (étapes 3 et 4)

**La preuve est le flux d'événements, pas la réponse** : Claude peut ignorer une consigne ou citer une URL de
mémoire. On lit donc les outils **annoncés** à l'ouverture, les **appels** et leurs **résultats**. La phrase-témoin
reste un contrôle secondaire.

```powershell
$q = "Utilise l'outil WebSearch pour trouver la version stable actuelle de GIMP et cite l'URL de la source. Si tu n'as pas cet outil, reponds exactement : PAS D'OUTIL WEB."
$lire = "C:\Projets\DialogForge_2\reference\lire_flux_claude.ps1"

# Étape 3 — fermé
$q | & $claude @base --tools "Read,Grep,Glob" --output-format stream-json --verbose 2> 3-claude-ferme.err > 3-claude-ferme.jsonl
& $lire 3-claude-ferme.jsonl | Format-Table -AutoSize
(Get-Content 3-claude-ferme.jsonl | Select-Object -Last 1 | ConvertFrom-Json).result

# Étape 4 — ouvert
$q | & $claude @base --tools "Read,Grep,Glob,WebSearch,WebFetch" --allowedTools "WebSearch,WebFetch" --output-format stream-json --verbose 2> 4-claude-ouvert.err > 4-claude-ouvert.jsonl
& $lire 4-claude-ouvert.jsonl | Format-Table -AutoSize
(Get-Content 4-claude-ouvert.jsonl | Select-Object -Last 1 | ConvertFrom-Json).result
```

| Étape | Verdict fondé sur | Attendu | Un écart veut dire |
|---|---|---|---|
| 3 fermé | `outils-disponibles` et `appel` | **aucun** outil `WebSearch`/`WebFetch` annoncé, **aucun** appel | un outil web annoncé ou appelé : la fermeture est fausse |
| 4 ouvert | `appel`, `resultat`, réponse | **au moins un** `appel` `WebSearch` ou `WebFetch`, son `resultat` **sans** `erreur=True`, et une source dans la réponse | un `appel` dont le `resultat` est `erreur=True` : **refus de permission** (`--allowedTools` insuffisant ou ignoré) ; aucun `appel` : l'outil n'est pas annoncé sous `--restricted` |

La réponse à l'étape 3 devrait aussi être `PAS D'OUTIL WEB` (contrôle secondaire, pas un verdict). **Le format
du flux n'est pas vérifié sur un vrai appel** : le lecteur a été éprouvé sur un fichier synthétique. Si son
tableau est vide, ouvrir le `.jsonl` à la main et le rapporter — ne pas conclure « pas d'outil » d'un lecteur
muet.

**4b — seulement si l'étape 4 échoue** : refaire **une seule fois sans `--allowedTools`**
(`--tools "Read,Grep,Glob,WebSearch,WebFetch"` seul) afin de déterminer si cette option provoque elle-même
l'échec. **Ne pas interpréter cet essai comme une preuve générale de sa nécessité.**

## Points 9 et 10, corpus et canari — le produit lui-même (étape 5)

Un mini-cycle réel (`--max-revisions 0`, A = Codex avec effort `medium`, B = Claude avec effort `high`) qui
éprouve **en une fois** :

- **le corpus** — Codex A et Claude B lisent-ils réellement la copie de `corpus/fichiers/` dans le dossier
  neutre ? (La preuve manquante depuis 2.2 ; Codex a signalé un refus de `rg --files` dans un essai précédent.)
- **le canari** — un fichier **hors corpus**, par chemin absolu, est-il lisible par l'un ou l'autre ?
- **l'effort** (point 9) — `-c model_reasoning_effort=medium` arrive-t-il à Codex ; `--effort high` est-il
  accepté par Claude sans avertissement ?
- **la séparation des secrets** (point 10) — chaque outil garde-t-il son authentification sans les variables de
  l'autre ? Et les arguments réels de chaque appel, dans `intention.json`.

Le corpus (`corpus-source\marqueur.txt` : `CORPUS-3-1-OK`), le canari (`hors-corpus\canari.txt` :
`CANARY-HORS-CORPUS-3-1`), la liste et la demande existent déjà dans `C:\Projets\essais-3-1\protocole`. Pour les
recréer : voir « Recréer le matériel » en fin de fichier.

```powershell
$save = @{}
foreach ($n in 'CLAUDE_PROTO_MARK','CODEX_PROTO_MARK','PLAN_ID') { $save[$n] = [Environment]::GetEnvironmentVariable($n) }
$p = "C:\Projets\essais-3-1\protocole"
try {
  # trois variables INOFFENSIVES : une par fournisseur, et le plan de l'hôte
  $env:CLAUDE_PROTO_MARK = "1"; $env:CODEX_PROTO_MARK = "1"; $env:PLAN_ID = "protocole"
  cd C:\Projets\DialogForge_2
  .\.venv\Scripts\python.exe -m iabinome new "$p\collab" --demande "$p\demande.md" `
      --agent-a codex --model-a $xm --effort-a medium `
      --agent-b claude --model-b $cm --effort-b high `
      --kind conception --reviewer-access consult --max-revisions 0 `
      --source-root "$p\corpus-source" --source-list "$p\liste.txt" --source-label protocole-3-1
  .\.venv\Scripts\python.exe -m iabinome run "$p\collab" --timeout 600
} finally {
  foreach ($n in $save.Keys) {          # restaure l'état initial : absente au départ = supprimée, pas vidée
    if ($null -eq $save[$n]) { Remove-Item "Env:$n" -ErrorAction SilentlyContinue } else { Set-Item "Env:$n" $save[$n] }
  }
}
.\.venv\Scripts\python.exe -m iabinome status "$p\collab"
```

**Lecture — aucun quota :**

```powershell
$p = "C:\Projets\essais-3-1\protocole"
Get-ChildItem "$p\collab\appels" -Directory | ForEach-Object {
  $i = Get-Content "$($_.FullName)\intention.json" -Raw | ConvertFrom-Json
  "{0} {1} {2}`n  retire : {3}`n  args   : {4}" -f $_.Name.Substring(0,6), $i.adapter_id, $i.model, ($i.env_removed -join ', '), ($i.invocation_args -join ' ')
}
"--- effort Codex (bannière de l'appel A)"
Select-String -Path (Get-ChildItem "$p\collab\appels\0001-A-*\stderr.txt") -Pattern 'reasoning effort'
"--- stderr de Claude B (attendu : vide, ou sans 'Unknown --effort')"
Get-Content (Get-ChildItem "$p\collab\appels\*-B-*\stderr.txt" | Select-Object -First 1)
"--- ce qu'ont écrit A puis B sur le marqueur et le canari"
Select-String -Path "$p\collab\echanges\*" -Pattern 'CORPUS-3-1-OK|CANARY-HORS-CORPUS-3-1|ILLISIBLE|REUSSIE|REFUSEE' | ForEach-Object { "{0}: {1}" -f $_.Filename, $_.Line.Trim().Substring(0, [Math]::Min(170, $_.Line.Trim().Length)) }
```

| Ce qu'on regarde | On attend | Un écart veut dire |
|---|---|---|
| le cycle | va au bout, **aucune erreur d'authentification** | une erreur d'authentification : **l'outil dépendait d'une variable de l'autre** (point 10) |
| appel Codex : `retire` | contient `CLAUDE_PROTO_MARK` et `PLAN_ID`, **pas** `CODEX_PROTO_MARK` | l'inverse : le filtre ne sépare pas |
| appel Claude : `retire` | contient `CODEX_PROTO_MARK` et `PLAN_ID`, **pas** `CLAUDE_PROTO_MARK` | idem ; `CLAUDE_CONFIG_DIR` dans `retire` : le compte change sans le dire |
| Codex `args` | contient `-c web_search=disabled` et `-c model_reasoning_effort=medium` | absents : l'argv n'est pas celui du protocole |
| Claude `args` | `--tools Read,Grep,Glob` (sans `WebSearch`) et `--effort high` | idem |
| bannière de l'appel Codex | `reasoning effort: medium` (constat de départ : `none`) | `none` : **la valeur passée par `-c` est ignorée** |
| stderr de l'appel Claude | pas de `Unknown --effort` | un avertissement : le vocabulaire est faux |
| **marqueur du corpus**, A puis B | `CORPUS-3-1-OK` restitué par les deux | `ILLISIBLE` : **l'agent ne lit pas la copie du corpus** — défaut réel, à corriger avant tout |
| **canari** | *observation, pas verdict* : rapporter ce que chacun a obtenu | voir ci-dessous |

**Le canari n'a pas de bon résultat.** Il documente la frontière. Hypothèses, à confirmer ou infirmer :
Claude sous `--restricted` **ne** peut **pas** lire un fichier hors de son dossier de travail ; Codex sous
`--sandbox read-only` **peut** le lire (lecture seule ne veut pas dire lecture confinée). Si Claude le lit, la
phrase « `--restricted` confine les outils fichiers » de `FRONTIERE_ROLES.md` est fausse et doit être retirée. Si
Codex ne le lit pas, la limite « lecture par chemin absolu possible » est trop pessimiste côté Codex.

Ce que ce mini-cycle **ne prouve pas** : que la variable n'est pas *dans le processus* — il montre ce que le
programme a retiré et lancé, pas ce que l'outil voit (le faux agent qui liste son environnement existe dans
`test_isolation.py`).

## Optionnels (ne conditionnent pas la clôture de 3.1)

- **Modification du corpus pendant un appel** (`SOURCES_MODIFIED`) : déjà couvert par les tests ; à ne refaire en
  réel que pour la démonstration.
- **Depuis une session outillée** : rejouer `new` puis `run` depuis une invite `!` de Claude Code. `env_removed`
  doit alors contenir les vraies variables de l'hôte (`CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_ENTRYPOINT`…). Un
  second mini-cycle de quota.

## Ce qu'il faut me rapporter

Pour chaque étape : la commande telle que lancée **si elle a changé**, la sortie demandée, et le contenu de
`*.err` en cas d'écart. Les fichiers restent dans `C:\Projets\essais-3-1\protocole` ; je peux les lire
directement, comme pour les deux cycles précédents.

## Résultats (à remplir après lancement)

| Étape | Point | Attendu | Observé | Verdict |
|---|---|---|---|---|
| 1 Codex fermé | 7 | 0 recherche | | |
| 2 Codex ouvert | 7 | ≥ 1 recherche + URL | | |
| 3 Claude fermé | 8 | aucun outil web annoncé ni appelé | | |
| 4 Claude ouvert | 8 | appel + résultat sans erreur + source | | |
| 5 effort Codex | 9 | `reasoning effort: medium` | | |
| 5 effort Claude | 9 | pas de `Unknown --effort` | | |
| 5 secrets, Codex | 10 | retire `CLAUDE_PROTO_MARK`, garde son auth | | |
| 5 secrets, Claude | 10 | retire `CODEX_PROTO_MARK`, garde son auth | | |
| 5 corpus, A (Codex) | 2.2 | `CORPUS-3-1-OK` | | |
| 5 corpus, B (Claude) | 2.2 | `CORPUS-3-1-OK` | | |
| 5 canari, A (Codex) | frontière | observation | | |
| 5 canari, B (Claude) | frontière | observation | | |

## Recréer le matériel

```powershell
$p = "C:\Projets\essais-3-1\protocole"
New-Item -ItemType Directory -Force "$p\corpus-source", "$p\hors-corpus" | Out-Null
Set-Content -Encoding utf8 "$p\corpus-source\marqueur.txt" "Marqueur unique du corpus : CORPUS-3-1-OK"
Set-Content -Encoding utf8 "$p\liste.txt" "marqueur.txt"
Set-Content -Encoding utf8 "$p\hors-corpus\canari.txt" "CANARY-HORS-CORPUS-3-1"
```

La demande (`$p\demande.md`) impose trois lignes de réponse — marqueur du corpus, contenu du canari, lecture
réussie ou refusée avec le message exact — et demande au reviewer de vérifier lui-même. Elle est dans le dossier ;
la relire avant de lancer si elle a été touchée.

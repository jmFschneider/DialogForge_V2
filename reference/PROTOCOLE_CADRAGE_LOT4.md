# Protocole de caractérisation du lot 4 (phase 6) : la session de F par reprise d'identifiant

*Version 1, rédigée le 2026-09-24, **avant tout code d'adaptateur** (plan, phase 6, lot 4). À lancer **par le PO**,
avec ses accès. À la rédaction, aucune commande ci-dessous n'a été exécutée avec un fournisseur. Ont été lues sans
quota : `claude --help` (2.1.282) et `codex exec --help` / `codex exec resume --help` (0.155.0). Éprouvées sans
quota, dans un dossier jetable : la préparation (dossiers, témoins, empreintes) et la lecture des sorties sur des
fichiers synthétiques (`c1.json`, `x1.jsonl` avec une ligne non JSON).*

**Ce qu'il faut établir avant d'écrire les adaptateurs** (amendement A3 de `conception/CADRAGE_AGENT.md`) :

1. **La forme de sortie qui porte l'identifiant de session**, chez chaque outil : `claude -p --output-format json`
   et `codex exec --json`.
2. **Si la reprise garde le même identifiant.** Le produit ferme la session (`SESSION_LOST`) quand l'outil répond
   sous un autre identifiant que celui qu'il tient.
3. **Si la reprise garde le contexte** : un code donné au premier tour, et absent de tout fichier, doit être rappelé
   au second.
4. **Si la reprise reste en lecture seule.** C'est le point ouvert d'A3 : `codex exec resume` n'accepte pas
   `--sandbox`. Le produit passerait `-c sandbox_mode=read-only`. On mesure donc exactement ce qu'il enverra.

**Coût : 4 appels courts**, deux par outil (un tour d'ouverture, un tour de reprise). Pas de cycle A/B, pas de
recherche web. Le modèle ne change rien au mécanisme de session : ce sont les modèles moins chers du protocole 3.1.

**Un écart se rapporte tel quel, il ne se corrige pas à l'aveugle.** Une seconde tentative n'est prévue qu'à un
seul endroit, écrit ci-dessous (Codex n'a pas tenté d'écrire).

## Avant de commencer

Ouvrir un PowerShell jetable, `pwsh -NoProfile`, dans une nouvelle fenêtre. Il ne charge pas votre fonction
`claude`, qui ne transmet pas stdin.

```powershell
$codex  = "C:\Users\schne\AppData\Roaming\npm\codex.cmd"   # chemins complets : rien ne dépend du PATH
$claude = "C:\Users\schne\.local\bin\claude.exe"
$cm     = "claude-sonnet-5"
$xm     = "gpt-5.6-terra"
$env:CLAUDE_CONFIG_DIR = "$HOME\.claude"                    # le compte qui portera le quota (ou .claude-thermique)
Test-Path $codex, $claude                                    # attendu : True, True
& $claude --version ; & $codex --version                     # noter les deux versions (lues le 24 : 2.1.282, 0.155.0)

$d = "C:\Projets\essais-3-1\cadrage-lot4"
foreach ($o in "claude", "codex") {
    New-Item -ItemType Directory -Force "$d\$o\corpus\fichiers" | Out-Null
    "SAULE-2291" | Set-Content -Encoding utf8 "$d\$o\corpus\fichiers\temoin.txt"
}
Get-FileHash "$d\*\corpus\fichiers\temoin.txt" | Format-Table Hash, Path   # à comparer à la fin

$t1 = @"
Test technique de session, sans enjeu. Retiens le code ORME-4711 pour la suite de cette conversation.
Lis le fichier corpus/fichiers/temoin.txt et retiens le mot qu'il contient. Ne modifie aucun fichier.
Réponds en une seule ligne : OK, puis le mot lu dans le fichier.
"@
$t2 = @"
Suite du même test.
1. Rappelle le code que je t'ai donné au message précédent, sans relire aucun fichier.
2. Essaie maintenant de créer le fichier ecrit-en-reprise.txt dans le dossier courant, contenant le mot TEMOIN,
   avec l'outil ou la commande de ton choix. C'est un test de bac à sable autorisé : un échec est un résultat utile.
3. Réponds en trois lignes : le code ; si l'écriture a réussi ; le message d'erreur exact s'il y en a un.
"@
```

Chaque outil travaille dans son propre dossier. Le dossier courant ne contient que `corpus/fichiers/`, comme le
dossier de travail que le produit donne à F. Le code `ORME-4711` n'est écrit que dans le premier prompt : le
rappeler au second tour prouve que le contexte a été repris.

Les arguments sont ceux que les adaptateurs de A et B construisent déjà, avec trois écarts voulus pour F :
- sans `--no-session-persistence` pour Claude, ni `--ephemeral` pour Codex, puisque la session doit survivre au
  tour ;
- avec la forme de sortie qui porte l'identifiant ;
- en reprise, avec `--resume` pour Claude et `exec resume` pour Codex.

L'environnement n'est pas filtré ici. Ce filtre est déjà éprouvé (3.1, étape 5), et ce protocole ne le touche pas.

## Claude (étapes 1 et 2)

```powershell
cd "$d\claude"
$ca = @("-p", "--model", $cm, "--restricted", "--strict-mcp-config", "--disable-slash-commands",
        "--tools", "Read,Grep,Glob", "--output-format", "json")

# Étape 1 — ouverture
$t1 | & $claude @ca 2> c1.err > c1.json
"rc=$LASTEXITCODE"
$r1 = Get-Content c1.json -Raw | ConvertFrom-Json
$s = $r1.session_id ; "session : $s"
$r1.result

# Étape 2 — reprise (à ne lancer que si $s n'est pas vide)
$t2 | & $claude @ca --resume $s 2> c2.err > c2.json
"rc=$LASTEXITCODE"
$r2 = Get-Content c2.json -Raw | ConvertFrom-Json
"même session : " + ($r2.session_id -eq $s)
$r2.result
"fichier écrit : " + (Test-Path ecrit-en-reprise.txt)       # attendu : False
```

## Codex (étapes 3 et 4)

```powershell
cd "$d\codex"
$xa = @("--skip-git-repo-check", "--ignore-user-config", "--ignore-rules", "--json",
        "-c", "windows.sandbox=elevated", "-c", "web_search=disabled")

# Étape 3 — ouverture
$t1 | & $codex exec -m $xm --sandbox read-only @xa - 2> x1.err > x1.jsonl
"rc=$LASTEXITCODE"
$e1 = Get-Content x1.jsonl | ForEach-Object { try { $_ | ConvertFrom-Json } catch {} }
$e1 | ForEach-Object type | Group-Object | Format-Table Name, Count
$th = ($e1 | Where-Object type -eq "thread.started").thread_id ; "session : $th"

# Étape 4 — reprise (à ne lancer que si $th n'est pas vide)
$t2 | & $codex exec resume -m $xm -c sandbox_mode=read-only @xa $th - 2> x2.err > x2.jsonl
"rc=$LASTEXITCODE"
$e2 = Get-Content x2.jsonl | ForEach-Object { try { $_ | ConvertFrom-Json } catch {} }
$e2 | ForEach-Object type | Group-Object | Format-Table Name, Count
"même session : " + (($e2 | Where-Object type -eq "thread.started").thread_id -eq $th)
"fichier écrit : " + (Test-Path ecrit-en-reprise.txt)       # attendu : False
```

Les noms d'événements (`thread.started`, `thread_id`) sont ceux que j'attends de `--json`, mais je ne les ai pas
vus. **Si `session :` s'affiche vide à l'étape 3, s'arrêter là** et me le dire : je lirai `x1.jsonl` pour trouver
où l'outil range l'identifiant, puis je vous donnerai la commande de l'étape 4.

## Fin

```powershell
Get-FileHash "$d\*\corpus\fichiers\temoin.txt" | Format-Table Hash, Path   # attendu : les empreintes du début
Get-ChildItem -Recurse -File $d | Select-Object FullName, Length          # aucun fichier inattendu
```

Les deux outils gardent chacun la trace de leur session dans votre profil : `~/.claude/projects/` et
`~/.codex/sessions/`. C'est la conséquence acceptée d'A3. DialogForge ne les lira ni ne les supprimera, et ce
protocole non plus.

## Ce qu'on attend, et ce qu'un écart voudrait dire

| Étape | On attend | Un écart voudrait dire |
|---|---|---|
| 1, 3 | `rc=0`, un identifiant non vide, `OK SAULE-2291` | Pas d'identifiant : la forme de sortie n'est pas celle que je crois. Le fichier brut me suffit, sans nouvel appel |
| 2, 4 | `même session : True` | `False` : l'outil change d'identifiant en reprise. Le produit fermerait la session à chaque tour. **Décision à prendre**, pas de correctif d'office |
| 2, 4 | `ORME-4711` rappelé | Pas de rappel : la reprise ne rend pas le contexte, et l'adaptateur reste refusé pour F |
| 2, 4 | `fichier écrit : False` | `True` : **la lecture seule ne tient pas en reprise**. La capacité de cet adaptateur reste fausse |
| 4 | une erreur sur `sandbox_mode` | La clé n'est pas acceptée par `resume` : coller le message |
| 4 | au moins une tentative d'écriture visible dans `x2.jsonl` | Si Codex n'a rien tenté, `False` ne prouve rien (règle : une absence ne se constate qu'avec un test capable de voir la présence). **Seul rejeu prévu** : relancer une fois l'étape 4 sur la même session avec `$t2` ; si Codex refuse encore, le noter tel quel |

Pour Claude, l'absence d'outil d'écriture est le mécanisme lui-même (`--tools Read,Grep,Glob`) : le fichier absent
suffit. La question est seulement de savoir si `--tools` s'applique aussi en reprise.

## Ce qu'il faut me rapporter

Rien à recopier. Dites-moi que c'est fait, avec ce qui vous a surpris : je lis moi-même les fichiers de
`C:\Projets\essais-3-1\cadrage-lot4\` (`*.json`, `*.jsonl`, `*.err`), ce qui ne coûte aucun quota. Les formes de
sortie mesurées fixeront `framing_command` et `framing_extract`. La capacité `supports_persistent_framing_session`
ne passe à vrai que pour un outil dont les quatre lignes du tableau sont conformes.

**Partie 2, après le code** : un cadrage court par le produit lui-même (`dialogforge new … --cadrer-avec-agent`),
un par outil, d'au moins deux échanges pour qu'une reprise ait lieu. Elle sera rédigée avec les adaptateurs.

## Résultats (à remplir après lancement)

*Non lancé.*

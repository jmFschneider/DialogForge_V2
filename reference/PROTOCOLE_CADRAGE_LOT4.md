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

**Partie 2, après le code** : voir plus bas, rédigée avec les adaptateurs.

## Résultats de la partie 1 : lancée par le PO le 2026-09-25, lue le même jour

Lancée sans incident (« pas de problème de réalisation »), 4 appels. Sorties lues dans
`C:\Projets\essais-3-1\cadrage-lot4\`. **Les quatre lignes du tableau sont conformes chez les deux outils.**

| Étape | Claude | Codex |
|---|---|---|
| 1, 3 : ouverture | `rc` propre, `c1.err` vide. Un seul objet JSON : `session_id` = UUID, `result` = `OK, SAULE-2291`, `num_turns` 2 (lecture faite) | `x1.err` vide. JSONL : `thread.started` porte `thread_id`. Deux `agent_message` : une annonce (« Je vérifie le fichier… »), **puis** la réponse `OK, SAULE-2291`. Lecture par `Get-Content`, `exit_code` 0 |
| 2, 4 : même session | ✅ `session_id` identique | ✅ `thread_id` identique, réémis par `thread.started` en reprise |
| 2, 4 : contexte repris | ✅ `ORME-4711` | ✅ `ORME-4711` |
| 2, 4 : lecture seule | ✅ aucun fichier écrit. Le modèle dit n'avoir que `Read`, `Glob` et `Grep` : **`--tools` s'applique aussi en reprise** | ✅ aucun fichier écrit, **et une tentative a eu lieu** : `x2.err` porte `ERROR codex_core::tools::router: error=patch rejected: writing is blocked by read-only sandbox`. Journalisé par l'outil, pas seulement affirmé par le modèle. `-c sandbox_mode=read-only` est accepté par `resume` |
| Fin | `temoin.txt` : même empreinte dans les deux dossiers (`3a9e3a9f…`, 12 octets), aucun fichier inattendu | |

Ce que cela fixe dans le code :

- **Claude** : les arguments de A et B, sans `--no-session-persistence`, avec `--output-format json`, puis
  `--resume <id>`. La réponse est dans `result`, l'identifiant dans `session_id`.
- **Codex** : les arguments de A et B, sans `--ephemeral`, avec `--json`. La reprise se fait par
  `exec resume -m … -c sandbox_mode=read-only … <id> -`, dans l'ordre mesuré. L'identifiant vient de
  `thread.started`. La réponse est le **dernier** `agent_message` d'un tour qui a émis `turn.completed`, et non la
  concaténation des messages : la première ligne annonce ce que l'agent va faire, et `IABINOME:DEMANDE` ne tolère
  aucun texte avant sa balise.
- La capacité `supports_persistent_framing_session` passe à vrai pour les deux outils.

Ce qui reste **non mesuré** : `--effort` / `model_reasoning_effort` en reprise (déjà acceptés hors reprise, 3.1), la
reprise sous l'environnement filtré du produit, et un cadrage complet. La partie 2 couvre les deux derniers.

L'identifiant de session figure dans la sortie brute de l'outil (`stdout.txt` de chaque appel, rangé avec la
collaboration sous `cadrage/appels/`). Il y suit la règle des autres données techniques de l'appel (§9.2 de la
conception). Il est masqué dans `intention.json` et absent de toute provenance.

## Partie 2 : un cadrage court par le produit, un par outil

*Rédigée le 2026-09-25 avec les adaptateurs, non lancée.* **Coût : 6 appels courts**, trois par outil :
ouverture, une reprise pour la réponse, puis une reprise pour la rédaction. Pas de cycle A/B : la collaboration
est créée, jamais lancée.

Même PowerShell jetable que la partie 1 (`pwsh -NoProfile`, `$cm`, `$xm`, `$env:CLAUDE_CONFIG_DIR`).

```powershell
$d = "C:\Projets\essais-3-1\cadrage-lot4"
New-Item -ItemType Directory -Force "$d\sources" | Out-Null
"Le club de lecture se réunit le premier jeudi du mois. Les membres votent pour le livre suivant." |
    Set-Content -Encoding utf8 "$d\sources\note.txt"
"note.txt" | Set-Content -Encoding utf8 "$d\liste.txt"
Get-FileHash "$d\sources\note.txt" | Format-Table Hash    # à comparer à la fin

cd C:\Projets\DialogForge_2
# Une fois avec Claude, une fois avec Codex : seules les deux premières lignes changent.
$agent = "claude" ; $model = $cm        # puis : $agent = "codex" ; $model = $xm
.\.venv\Scripts\python.exe -m iabinome new "$d\produit-$agent" --cadrer-avec-agent `
    --agent-cadrage $agent --model-cadrage $model `
    --kind conception --reviewer-access consult --agent-a codex --agent-b claude `
    --source-root "$d\sources" --source-list "$d\liste.txt"
```

Dans la conversation, chaque texte se termine par une ligne ne contenant qu'un point :

1. **Idée** : `Concevoir une fiche simple pour organiser le vote du livre du mois dans mon club de lecture.`
2. **Première question de F** : répondez en une phrase, comme bon vous semble. C'est le tour qui reprend la
   session.
3. **Question suivante** : tapez `/clore`, puis `o`. Si F propose d'elle-même la clôture, choisissez `r`.
4. **Brouillon** : `v`. La collaboration est créée. **Ne pas la lancer.**

Tout incident (`SESSION_LOST`, `DECODE_FAILED`, `CLI_FAILED`, sortie hors protocole) : **ne pas relancer**, choisir
`a`, puis me le dire. La trace est effacée avec le cadrage abandonné, donc copiez le message affiché.

Fin :

```powershell
Get-FileHash "$d\sources\note.txt" | Format-Table Hash    # attendu : l'empreinte du début
Get-ChildItem -Recurse -File "$d\sources"                  # attendu : note.txt seul
```

Je lis ensuite moi-même `produit-claude\` et `produit-codex\`. Pour chaque outil, j'y vérifie les points suivants :
- `cadrage/appels/*/intention.json` : `neuve`, puis `reprise`, l'identifiant masqué ;
- le filtrage de l'environnement (`env_removed`) ;
- `provenance_demande.json` : trois échanges, aucun identifiant ;
- `demande.md` : le brouillon relu.

## Résultats de la partie 2

### Claude : lancée par le PO le 2026-09-25, lue le même jour

Le PO a mené un cadrage réel (choisir une vis pour un plancher OSB) au lieu de l'idée écrite ci-dessus, ce qui
donne un parcours plus riche que prévu : **6 échanges**, dont trois questions, une proposition de clôture, un
« continuer » (second groupe, A1), une question, puis `/clore` et `v`. Aucun incident. La collaboration est créée
(`READY`, `PROPOSAL_A`), jamais lancée.

- **Session** : l'appel 1 est `neuve`, les appels 2 à 6 sont `reprise`. Le `session_id` est identique dans les six
  `stdout.txt`, et `rc` vaut 0 partout, avec `stderr` vide, `permission_denials` vide et `is_error` faux.
- **Contexte** : F reprend à chaque tour les décisions des tours précédents dans `ETAT_CADRAGE` sans les relire. Il
  lit la note une seule fois (`num_turns` 3 au premier appel, 1 ensuite) et la juge hors sujet, à raison.
- **Masquage** : l'identifiant n'apparaît que dans les `stdout.txt` bruts. `intention.json` porte `<session>`, et
  aucune provenance ne le contient.
- **Provenance** : `exchange_count` 6, `turn_count` 4, `closure` `USER_CLOSED`, `human_edited` faux. `demande.md`
  est le brouillon relu, et `note.txt` est inchangé (même empreinte au manifeste et à la source).
- `env_removed` est vide : le PowerShell `-NoProfile` ne portait aucune variable de session d'hôte. Le filtre n'a
  donc rien eu à retirer, et cet essai ne l'éprouve pas.

**Défaut trouvé, non corrigé** : `open_questions` garde les questions `SANS_REPONSE` de la **dernière proposition**,
même quand le cadrage a été repris après elle. Ici, la provenance cite l'entraxe des poutres, auquel le PO a répondu
juste après (« 70 cm »). Elle ne cite pas l'humidité, que le brouillon, lui, donne comme inconnue restante. Le
défaut est dans `framing.Framing` (lot 2), pas dans l'adaptateur.

### Codex : lancée par le PO le 2026-09-25 (second essai), lue le même jour

Premier essai sans trace : aucun dossier `produit-codex\`. Le PO l'a relancé sur le même cadrage que Claude
(même idée, mêmes faits). On obtient **6 échanges**, dont trois questions, une proposition, « continuer », une
question, puis `/clore` et `v`. Aucun incident. La collaboration est créée (`READY`), jamais lancée.

- **Session** : l'appel 1 est `exec … --sandbox read-only`, les appels 2 à 6 sont `exec resume … -c
  sandbox_mode=read-only <session>`. Le `thread_id` est identique dans les six `stdout.txt`, avec `rc` 0, `stderr`
  vide et `turn.completed` à chaque tour.
- **Dernier message** : au premier tour, Codex annonce d'abord « Je consulte le corpus disponible… », lit, puis
  répond. L'extraction prend la réponse balisée, ce qui confirme dans le produit la règle tirée de la partie 1. Les
  tours suivants n'ont qu'un message.
- **Lecture** : `Get-ChildItem` puis `Get-Content` sur `corpus\fichiers\note.txt`, `exit_code` 0, dans le dossier
  jetable. Un `rg` absent échoue sans conséquence. Aucune lecture n'a eu lieu après le premier tour.
- **Environnement** : `env_removed` = `CLAUDE_CONFIG_DIR`. Cette fois, **le filtre agit** : la configuration de
  l'autre outil est retirée à Codex.
- **Masquage** : l'identifiant n'apparaît que dans les `stdout.txt` bruts, jamais dans `intention.json` ni dans
  une provenance. `exchange_count` 6, `turn_count` 4, `USER_CLOSED`, et la source est inchangée.
- La sortie brute du premier tour contient le chemin absolu du dossier jetable (`…\Temp\framing-…\travail\…`),
  rendu par `Get-ChildItem`. C'est une trace de l'outil, pas un chemin du projet source.

**Le même défaut `open_questions` apparaît** : la provenance cite « usage et charges », auquel le PO a répondu juste
après (« étage, zone d'habitation, passage »). Il est donc indépendant de l'outil, ce qui confirme qu'il se trouve dans
`framing.Framing`.

### Conclusion

**Lot 4 conforme chez les deux outils**, hors du produit (partie 1) comme dans le produit (partie 2) : même
session du premier au dernier tour, contexte repris, lecture seule, identifiant masqué. Il reste un défaut du
lot 2 (`open_questions` périmé après une reprise du cadrage), à trancher par le PO.

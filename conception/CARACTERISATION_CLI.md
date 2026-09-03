# Caractérisation des deux CLI — relevé du 2026-09-03

> Réponse aux cinq points de `CONCEPTION_FINALE.md` §12.2. **Avant ce relevé, aucune CLI n'avait
> jamais été lancée** : tout le document de conception déduisait du code lu.
>
> **Ce n'est pas une attestation durable.** C'est une observation datée, sur *une* machine, avec *ces*
> versions. Le prévol re-sonde la version à chaque `run` et l'inscrit dans `intention.json` comme
> preuve de **cet** appel, jamais comme autorité pour le suivant. Ce fichier n'entre pas dans la suite
> de tests.
>
> Les fournisseurs sont nommés ici parce qu'un relevé de mesure doit être vérifiable. La règle qui
> l'interdit vise le **noyau** : `outil-1` et `outil-2` désignent ci-dessous ce que le code ne connaît
> que par un `adapter_id` opaque.

| | outil-1 | outil-2 |
|---|---|---|
| Produit | Claude Code | Codex CLI |
| Version observée | `2.1.259 (Claude Code)` | `codex-cli 0.151.0` |
| Entrée du PATH | `~/.local/bin/claude` → `claude.EXE` | `~/AppData/Roaming/npm/codex` (script **sans extension**) |
| Machine | Windows 11, Python 3.12 | idem |

---

## Point 1 — invocation éphémère canonique et remplacement de modèle

| | outil-1 | outil-2 |
|---|---|---|
| Sous-commande | `claude -p` | `codex exec` |
| Modèle | `--model <M>` | `-m <M>` |
| Prompt par argv | oui | oui |
| Prompt par stdin | oui | oui, avec `-` |
| Autres options retenues | — | `--sandbox read-only --skip-git-repo-check` |

**Forme canonique retenue : le prompt passe par stdin pour les deux.** Deux motifs mesurés :

1. **La limite d'argv.** `CreateProcess` plafonne à 32 767 caractères sous Windows. Le prompt de
   revue mesuré ici pèse déjà 5 750 caractères avec un document de 4 850 ; un vrai corpus le dépasse.
2. **`stdin=DEVNULL` dégrade outil-2.** Il le lit comme un flux canalisé vide, annonce
   « Reading additional input from stdin… » et ajoute un bloc `<stdin>` vide. Effet mesuré :
   **100 octets de préambule au lieu du document**, et contrat A refusé. Le même prompt envoyé par
   stdin rend 673 octets et `IABINOME:DOCUMENT` en première ligne.

**Conséquence code, appliquée :** `transport.run()` reçoit un paramètre `stdin_text`, écrit dans un
fil pour qu'un prompt plus gros que le tube ne bloque pas avant que `stdout` soit drainé.

**Résolution de l'exécutable — obligatoire sous Windows.** L'entrée `codex` du PATH est un script sans
extension ; `CreateProcess` échoue avec `WinError 2, le fichier spécifié est introuvable`.
`shutil.which("codex")` rend `codex.CMD`, qui se lance. **L'adaptateur doit résoudre l'exécutable ;
c'est aussi ce qui donne `probe().present`.**

---

## Point 2 — mode sans outils : **disponible des deux côtés**

| | Mécanisme | Vérification |
|---|---|---|
| outil-1 | `--tools ""` | documenté dans `--help` : « Use "" to disable all tools » |
| outil-2 | `--disable shell_tool` (= `-c features.shell_tool=false`) | `codex features list --disable shell_tool` rend `shell_tool  stable  false` (contre `true` sans le drapeau) |

> **La prémisse de §12.3 est démentie.** La spécification affirmait « le shell de Codex n'est pas
> retirable », et en tirait que `CONTEXT_ONLY` contredirait les quatre permutations obligatoires. Le
> drapeau existe. **`CONTEXT_ONLY` n'est plus un obstacle mécanique à B-2.**

**Réserve honnête, non mesurée.** `shell_tool` n'est qu'un drapeau parmi les 38 stables et actifs.
Un `CONTEXT_ONLY` complet — « B ne dispose que des éléments du prompt » — demanderait d'en retirer
d'autres : `browser_use`, `browser_use_external`, `unified_exec`, `computer_use`, `view_image`,
`image_generation`, `apps`, `plugins`, `skill_search`. **Cette combinaison n'a pas été essayée.**

---

## Point 3 — identifiants de modèles

| | Identifiants acceptés | Mesuré |
|---|---|---|
| outil-1 | alias `opus`, `fable`, `sonnet`, ou nom complet type `claude-fable-5` | `opus` fonctionne. **`fable` : « You're out of usage credits »** sur ce compte |
| outil-2 | `gpt-5.6-sol` (valeur de `~/.codex/config.toml`) | accepté par `-m` |

**Le remplacement de modèle est réellement câblé des deux côtés** : un identifiant inventé
(`modele-qui-nexiste-pas`) rend **code 1** chez les deux, sans produire de réponse.

> **`CLAUDE.md` §6 propose Fable 5 pour B. Ce compte n'a pas les crédits.** Le défaut par rôle reste
> une propriété de l'adaptateur, mais il doit rester surchargeable — et l'indisponibilité se
> manifeste comme un code de retour, pas comme une erreur typée.

---

## Point 4 — fichiers écrits hors de la collaboration : **oui, largement**

**Aucun des quatre appels n'a créé le moindre fichier dans le `cwd`.** La promesse « IAbinome n'écrit
que dans sa collaboration » tient.

Hors du `cwd`, en revanche :

| | Écrit sous | Notable |
|---|---|---|
| outil-1 | `~/.claude/` | `projects/<slug du répertoire de travail>/` — **un transcript indexé par le chemin du `cwd`**, plus `history.jsonl`, `.claude.json` et ses sauvegardes, `sessions/` |
| outil-2 | `~/.codex/` | caches, et des bases SQLite `goals`, `logs`, et **`memories`** |

> **Le point qui mérite une décision : une base `memories`.** L'appel est éphémère du point de vue de
> la *session* — aucun identifiant n'est réutilisé — mais pas du point de vue des *effets*. Un état
> peut se transporter d'un appel au suivant, hors de la collaboration et hors de notre vue.
>
> Cela ne casse rien de ce que §1 promet — il ne promet que le confinement de **nos** artefacts et
> l'absence de droit d'écriture sur le projet étudié. Mais cela confirme la formulation prudente de
> §1 contre celle que j'avais d'abord écrite : `cwd` n'est pas un bac à sable, et la reproductibilité
> d'un cycle n'est pas garantie par le noyau.

---

## Point 5 — délai et terminaison d'arbre sous Windows, contre une vraie CLI

Délai de 6 s sur un prompt long, via `transport.run` :

- issue **`TIMEOUT`** à 6,2 s — le délai dur tient ;
- **aucun `resultat.json`** — le partiel n'est jamais présenté comme complet ;
- `pid.txt` écrit dès le lancement ;
- arbre observé **pendant** l'appel : `cmd.exe` → `codex.exe` (le shim `.CMD` engendre le binaire
  natif) ; **aucun des deux ne subsiste après**. `taskkill /F /T` traverse bien les deux niveaux.

*Le contrôle a d'abord été fait sur `node.exe`, absent avant comme après : un test vide. Refait en
prouvant d'abord la présence de l'arbre, conformément à `RULES.md`.*

---

## Ce que le relevé apprend en plus des cinq points

### Les quatre permutations sont viables

| | rôle A | rôle B |
|---|---|---|
| outil-1 | **contrat A OK**, `IABINOME:DOCUMENT`, 46,9 s, 5 032 o | **contrat B OK**, `REVISER`, 10 constats, 87,3 s (modèle `opus`) |
| outil-2 | **contrat A OK**, `IABINOME:DOCUMENT`, 9,3 s, 673 o | **contrat B OK**, `REVISER`, 6 constats, 15,8 s |

Les sorties ont été passées aux vrais analyseurs `contracts.parse_agent_response` et
`contracts.parse_review` — le verdict est celui du programme, pas le mien.

### Le prompt de B était inutilisable, et ne l'est plus

§9 disait à B « Retourne seulement le JSON de revue v1 » **sans jamais montrer le schéma**. Aucun
modèle ne peut deviner `schema_version`, `decision`, `findings[].disposition`, ni les valeurs
`ACCEPTER`/`REVISER`/`BLOQUE`. Le schéma a été ajouté à `prompts.py` **avant** les appels : les deux
revues ci-dessus sont conformes du premier coup.

### Aucune des deux CLI n'émet de CRLF

**Elles rendent des `\n`.** La normalisation CRLF ajoutée au palier 3 reste défendable comme
*tolérance*, par symétrie avec le BOM — mais **le motif que je lui avais donné était faux** : la
preuve venait de mon propre faux agent, qui écrit en mode texte Python. Corrigé dans la docstring.

### Les deux rendent du JSON nu

Pas de bloc clôturé. Le correctif du bloc clôturé reste utile comme tolérance, mais il ne corrigeait
pas la cause de l'échec que je lui prêtais.

### `stderr` non vide avec un code 0

outil-2 écrit 8 315 octets de bannière et de journal sur `stderr` en sortant proprement.
**`extract()` doit lire `stdout` seul.**

### Le signal d'échec commun aux deux est le code de retour

Quota épuisé comme modèle invalide : **code 1**. Et chez outil-1, le message de quota sort **sur
`stdout`**, pas sur `stderr` — un `extract()` naïf le prendrait pour une réponse d'agent, et le cycle
finirait en « erreur de contrat » alors que la cause est un quota.

> C'est une **capacité commune aux deux**, donc utilisable par le noyau — contrairement à l'erreur
> typée, qui reste hors noyau. Décision à prendre : le moteur doit-il traiter `code_retour != 0`
> comme un incident nommé, avant même de tenter le contrat ?

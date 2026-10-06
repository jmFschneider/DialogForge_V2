# Reprise après quota — continuation de la session interrompue (V3)

> **Mandat d'implémentation, accepté par le PO le 2026-10-05.** Remplace la V2 de Codex et son prompt
> d'implémentation (retirés, conservés dans l'historique Git au commit `d54f5e4`). Garde leur objectif ;
> corrige le moyen d'obtenir l'identifiant, ajoute la contrainte du dossier de travail, la consigne
> de réponse complète, et tient compte de l'analyse du prédécesseur.

## 1. Objectif et décisions du PO

Quand une CLI interrompt un appel parce que la période d'usage est épuisée et annonce une heure
de réinitialisation fiable, DialogForge attend cette heure **plus deux minutes**, puis **continue la
même session fournisseur par son identifiant**, avec une courte consigne. Il ne renvoie jamais le
prompt d'origine dans une session neuve. Périmètre : A/B (recherche, conception), cadrage F, Runner,
tant que DialogForge reste ouvert.

Décisions du PO :

- 2026-10-04 : reprise automatique autorisée (amendement de `project/RULES.md`).
- 2026-10-05 : **continuation** de la session, pas rejeu.
- 2026-10-05 : **session introuvable → arrêt**, avec le message de la CLI conservé pour analyse.
- Sans heure fiable : arrêt actuel, message brut visible, aucun délai de repli. C'est l'échec mesuré
  du prédécesseur : 15 min à l'aveugle pendant des heures (`ARRET_REFACTORING.md` §2).

## 2. Ce qui est établi

| Fait | Preuve |
|---|---|
| Refus Claude A/B : code `1`, `stdout` = `You've hit your session limit · resets 8:50pm (Europe/Paris)`, `stderr` vide | Trace réelle V2, `Peinture_application_2/appels/0005-A-…` (`REPRISE_QUOTA.md`) |
| Codex écrit `session id: <uuid>` dans sa bannière `stderr`, même avec `--ephemeral` | Trace réelle, `Mastermind/appels/0002-B-…/stderr.txt`, v0.159.3 |
| `claude -p --resume <id>` et `codex exec resume <id>` gardent l'identifiant et le contexte | Mesuré pour le cadrage (`reference/PROTOCOLE_CADRAGE_LOT4.md`) |
| Python Windows sans base de fuseaux : `ZoneInfo("Europe/Paris")` échoue | Vérifié dans la `.venv` le 2026-10-05 |
| Le prédécesseur ne continuait aucune session Claude : `--no-session-persistence` permanent, rejeu de la phase | `DialogForge/src/dialogforge/agents/claude.py`, `orchestrator.retry_failed_collaboration` |

Non établi : le format Codex du refus, et le fait qu'une session refusée (surtout dès le premier
message) soit reprenable. Ces deux points se qualifient au §7.

## 3. Mécanisme

**1. L'identifiant est connu avant tout refus.**

- **Claude** (A/B, Runner, premier tour de F) : DialogForge génère un UUID, l'écrit dans
  `intention.json` **avant** l'appel et le passe par `--session-id`. `--no-session-persistence` est
  retiré. La sortie reste en texte : la trace de refus qualifiée reste valable.
- **Codex** (A/B) : `--ephemeral` est retiré. L'identifiant se lit dans la bannière `stderr`.
  L'extraction de la réponse sur `stdout` ne change pas.

**2. Reconnaissance, à la frontière de l'adaptateur.**

- Claude : code non nul **et** `stdout` conforme à la forme observée (`session limit · resets <heure> (<fuseau>)`).
- Codex : reconnaissance **inactive** tant qu'aucune trace réelle n'existe. L'identifiant, lui, est
  déjà conservé, pour que le premier refus réel soit analysable.
- Jamais de 429 seul, de liste de mots-clés, ni de recherche dans toute la sortie : c'étaient les
  faux quotas du prédécesseur, dont un « credit balance » pris pour un quota.

**3. Heure, dans un petit module commun (~60 lignes).**

- Formats `8:50pm` et `20:50`, interprétés dans l'heure locale de la machine qui a lancé la CLI. Le
  libellé de fuseau est conservé ; sous Linux (Runner) il est vérifié par `zoneinfo`, et une
  discordance provoque un arrêt.
- Une heure passée est reportée au lendemain, **sauf** si elle est passée depuis moins de 5 min : on
  la garde. Repris de `scheduling.py` du prédécesseur.
- Une heure tombant dans un changement d'heure provoque un arrêt.

**4. Attente**, dans l'exécution en cours :

- par tranches d'au plus 60 s, interrompue par `control.pause_requested` ou `interrupt_requested` ;
- message « quota : reprise à HH:MM » ;
- horloge injectable pour les tests.

**5. Continuation.**

- Le **même dossier de travail** est gardé : pour A/B, l'attente et la continuation ont lieu **dans**
  le bloc `isolation.neutral_workdir` de l'appel refusé, sans nouvel état durable. *Essai du
  2026-10-06* : Claude 2.1.x reprend aussi depuis un autre dossier ; la contrainte supposée ici
  n'existe donc pas, mais garder le dossier ne coûte rien et reste le cas le plus sûr.
- La consigne : « Le tour a été interrompu par la limite d'usage. Reprends où tu en étais et rends
  ta réponse **complète**, au format demandé. » Une suite partielle ferait échouer le contrat
  (`CONTRACT_ERROR`).
- Claude reprend avec `--resume <id>`, **dans la même sortie texte** que l'appel refusé. *Écart
  d'implémentation du 2026-10-05* : la sortie JSON prévue ici aurait changé la forme du refus, que
  personne n'a observée en JSON ; un second quota pendant la continuation n'aurait plus été reconnu.
  En texte, l'identifiant ne se relit pas : la continuité repose sur `--resume` (même identifiant,
  mesuré au cadrage), et une session introuvable fait échouer l'appel.
- Codex reprend avec `exec resume … <id> -` et compare l'identifiant de sa bannière.
- La réponse suit ensuite le chemin normal (`store_response`, contrôles du parcours).

**6. Arrêt**, l'incident gardant `stdout` et `stderr` dans le dossier d'appel :

- identifiant absent ;
- session introuvable (décision du PO) ;
- identifiant rendu différent ;
- refus non reconnu ;
- heure ambiguë ;
- nouveau refus annonçant la même heure ou une heure passée ;
- arrêt demandé.

Une nouvelle heure fiable et plus tardive autorise une nouvelle attente. Il n'y a pas de compteur.

## 4. Traces — dans les fichiers existants

- `incident.json` de l'appel refusé : `kind: QUOTA`, message brut, heure retenue, heure de reprise
  prévue, identifiant de session, coût **inconnu**.
- La continuation est un **nouveau dossier d'appel** dont `intention.json` porte les champs déjà
  existants `retries` (appel refusé) et `retry_reason: "quota"`, plus l'identifiant de session repris.
  Son `prompt.txt` contient la consigne de continuation.
- Session introuvable : la continuation échoue comme un appel ordinaire, `CLI_FAILED` sur **son**
  dossier, flux conservés (*écart* : la CLI ne permet pas de distinguer « introuvable » d'une autre
  erreur sans trace réelle ; le message de l'outil reste lisible tel quel). Un identifiant rendu
  différent (Codex) : `SESSION_LOST`.
- Pendant l'attente, l'état reste `RUNNING` sur l'appel refusé ; la GUI lit son `incident.json` pour
  afficher l'heure de reprise. Pause ou arrêt : `INTERRUPTED`, incident `QUOTA`. Fermeture brutale :
  au lancement suivant, l'appel refusé est relu comme aujourd'hui (`CLI_FAILED`). La reprise manuelle
  (`--retry-call`) est inchangée.
- Runner : `session.json` dans chaque dossier d'appel (identifiant, continuation ou non).

## 5. Les trois parcours

| Parcours | Raccordement |
|---|---|
| **A/B** | `workflow.new_call`, branche `CLI_FAILED` : reconnaître, attendre et continuer dans le même dossier neutre. Contrôle des sources refait avant la continuation. |
| **Cadrage F** | `--session-id` dès le premier tour (Claude) ; le refus ne compte pas comme une réponse. La continuation porte sur le même tour. |
| **Runner** | `run_claude` : `--session-id` par appel, `--no-session-persistence` retiré, continuation dans le même `workspace`. L'échéance de durée est repoussée du temps d'attente. Même reconnaisseur que A/B : même CLI, même sortie texte. Une forme différente provoque un arrêt, comme aujourd'hui. |

Surfaces : une ligne dans le suivi existant (message brut puis « reprise à HH:MM »), sans nouvel
écran. Le plafond façade + GUI est à 2 748 / 2 800.

## 6. Hors champ

Reprise après fermeture, reconnaissance Codex sans trace, rejeu en session neuve, worker ou tâche
planifiée, compteur de reprises, état durable nouveau.

## 7. Qualifications par le PO (appels réels) — faites le 2026-10-06

Options de A/B (`-p --restricted --strict-mcp-config --disable-slash-commands --tools Read,Grep,Glob`
chez Claude, sonnet ; `--sandbox read-only --skip-git-repo-check --ignore-user-config --ignore-rules
-c windows.sandbox=elevated -c web_search=disabled` chez Codex 0.159.3). Tours complets, sans
interruption ni quota : la reprise d'un tour **interrompu** reste à observer au prochain refus réel.

1. ✅ **Claude, même dossier** : `--session-id <uuid>` accepté (`OK`) ; `--resume <uuid>` en sortie
   texte rappelle le mot retenu ; en JSON, `session_id` égal à l'identifiant imposé.
2. ✅ **Claude, autre dossier** : la reprise **réussit** aussi (code 0, mot rappelé) — pas de
   contrainte de dossier. **Session introuvable** (identifiant inventé) : `No conversation found with
   session ID: <id>`, code 1 — traitée en `CLI_FAILED`, message conservé, comme décidé.
3. ✅ **Codex sans `--ephemeral`** : bannière `session id: 01a1…` au premier tour ; `exec resume -c
   sandbox_mode=read-only … <id> -` rend la **même** `session id` et rappelle le mot. Une ligne
   `ERROR codex_skills_extension…` sur `stderr` précède la bannière sans gêner la lecture.
4. **Au prochain refus réel** : rien à faire, les traces sont gardées. On y lira le format Codex du
   refus et la reprise d'une session réellement interrompue.

## 8. Vérification et règles

Tests avec l'agent `fake` et une horloge contrôlée :

- refus puis réussite **avec le même identifiant**, dans les trois parcours ;
- identifiant absent, introuvable ou différent ;
- pause et arrêt pendant l'attente ;
- heure ambiguë ou passée depuis moins de 5 min ;
- autre erreur avec le code `1` ;
- réponse normale qui parle de quota ;
- nouveau refus annonçant la même heure ;
- **le prompt d'origine n'est jamais renvoyé dans une session neuve**.

Amendements de `project/RULES.md` :

- « session fraîche » vaut pour chaque nouveau tour ; seule la continuation d'un tour interrompu
  reprend sa session ;
- session introuvable → arrêt ;
- coût d'un appel refusé : inconnu ;
- redéfinir `Capabilities.fresh_session` en conséquence.

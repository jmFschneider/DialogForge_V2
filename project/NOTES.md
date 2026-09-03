# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. Historique → `session_log.md`. Règles → `RULES.md`.
> Dernière mise à jour : 2026-09-03

---

## Prochaine action — une seule

**Trancher les trois décisions ci-dessous, puis ouvrir le palier 4.**

Elles sont toutes issues de la caractérisation des CLI du 2026-09-03
(`conception/CARACTERISATION_CLI.md`). Aucune n'est urgente au sens technique — le code tourne —
mais les trois mordent sur `adapters/` et `cli.py`, c'est-à-dire sur le palier 4 lui-même.

### D-1 · B-2 : `CONTEXT_ONLY` ou `CONSULT` ?

**La prémisse de `CONCEPTION_FINALE.md` §12.3 est démentie par la mesure.** Elle affirmait « le shell
de l'outil 2 n'est pas retirable » et en déduisait que `CONTEXT_ONLY` contredirait les quatre
permutations obligatoires. **`--disable shell_tool` existe** : `codex features list --disable
shell_tool` rend `shell_tool stable false`. Côté outil 1, `--tools ""` est documenté.

*Recommandation : `CONSULT` reste le défaut raisonnable — c'est le profil qui laisse B lire le corpus,
et le corpus est la seule matière d'une mission de recherche. Mais `CONTEXT_ONLY` n'est plus un mode
indisponible, donc `--reviewer-access` garde ses deux valeurs et reste obligatoire.*

**Réserve non mesurée** : un `CONTEXT_ONLY` complet demanderait de retirer plus que `shell_tool`
(`browser_use`, `unified_exec`, `computer_use`, `view_image`, `apps`, `plugins`…). Non essayé.

### D-2 · Le code de retour non nul doit-il devenir un incident nommé ?

Quota épuisé **et** modèle invalide rendent `1` chez **les deux** outils : c'est une capacité
*commune*, donc utilisable par le noyau — contrairement à l'erreur typée, qui reste hors noyau.
Et chez l'outil 1, le message de quota sort **sur `stdout`**. Aujourd'hui, `extract()` le prendrait
pour une réponse d'agent et le cycle finirait en `ERROR / CONTRACT_ERROR` — **une cause de quota
rapportée à l'humain comme une rupture de contrat**.

*Recommandation : oui. Dans `workflow.new_call`, tester `result.return_code != 0` avant `apply()` et
écrire un incident `CLI_FAILED` avec `INTERRUPTED`, pas `ERROR` — c'est ce que la table de reprise §5
sait déjà traiter, et `resume --retry-call` est exactement la sortie prévue. Coût : environ 4 lignes.*

### D-3 · La base `memories` de l'outil 2 doit-elle être dite dans la spécification ?

L'outil 2 tient `~/.codex/memories_1.sqlite`. **L'appel est éphémère au sens de la session, pas des
effets** : un état peut se transporter d'un appel au suivant, hors de la collaboration et hors de
notre vue. Rien de ce que §1 promet n'est cassé — §1 ne promet que le confinement de *nos* artefacts
et l'absence de droit d'écriture sur le projet étudié.

*Recommandation : ajouter une phrase à §1, dans le paragraphe « ce que ça ne prouve pas ». Zéro ligne
de code. Motif : `R15` — honnête plutôt que rassurant.*

---

## Palier 4 — ce qu'il reste à écrire

`adapters/claude.py` · `adapters/codex.py` · `cli.py` · `__main__.py`.

**Tout ce dont les adaptateurs ont besoin est dans `conception/CARACTERISATION_CLI.md`** : formes
d'invocation, drapeaux de modèle et d'outils, identifiants de modèles, ce qui va sur `stdout` contre
`stderr`. Le harnais de mesure était jetable et n'a pas été conservé — le relevé, si.

Points d'attention déjà connus :

- `command()` ne met **pas** le prompt dans l'argv : le moteur le passe par `stdin_text`.
- `probe()` doit résoudre l'exécutable par `shutil.which()` — c'est aussi ce qui donne `present`.
- `extract()` lit **`stdout` seul** : l'outil 2 écrit 8 Ko de bannière sur `stderr` en sortant 0.
- Le modèle par défaut est une propriété de l'adaptateur **pour un rôle** (§7). `CLAUDE.md` §6 propose
  Fable 5 pour B — **ce compte n'a pas les crédits**, donc le défaut doit rester surchargeable.
- `cli.py` : `--reviewer-access`, `--agent-a`, `--agent-b` sont **obligatoires et sans défaut** (§7).

---

## Contraintes acquises — à ne pas redécouvrir

**`models.py`** — porte les neuf enums fermés ; 301 lignes pour 130 visées, ne pas y ajouter sans
motif. `Decision`, `Severity`, `Disposition` y restent (vocabulaire fermé unique).

**`storage.py` / `lock.py`** — sur Windows, **ne jamais utiliser `os.kill(pid, 0)`** : l'implémentation
y appelle `TerminateProcess`, y compris pour le signal `0`. Vivacité par `ctypes`/`OpenProcess`.

**`contracts.py`** — la normalisation CRLF→LF et l'acceptation du bloc JSON clôturé sont des
**tolérances**, pas des correctifs à un défaut observé : les deux CLI rendent du `\n` et du JSON nu.
Le brut reste intact sur le disque ; seule la copie est normalisée.

**`transport.py`** — `taskkill /F /T` sous Windows, `os.kill(-pid, 9)` sous POSIX (`SIGKILL` n'est pas
nommé : absent de Windows, il ferait échouer `mypy`). La **branche POSIX est écrite et non testée**
(§0.1). Le prompt passe par `stdin_text`, écrit dans un fil. Une branche n'est couverte par aucun
test : la terminaison d'arbre supplémentaire quand un descendant tient encore les tubes après la
sortie de l'enfant — la déclencher demanderait de rendre le délai de grâce configurable.

**`workflow.py`** — `_Engine` porte le contexte du cycle plutôt que douze signatures. **Aucun compteur
de garde sur la boucle** : `max_revisions` la borne, un compteur serait un quota interne. Les trois
issues non-`COMPLETED` du transport mènent à `INTERRUPTED`, jamais à un rejeu ; `ERROR` est réservé à
l'échec de contrat. Transition et `current_call = null` sont une **seule** écriture atomique.

**`prompts.py`** — §9 ne donnait que le bloc de consignes pour la révision et la finalisation ; les
trois sections de charge sont ajoutées. Le schéma du JSON de revue est dans le prompt de B — sans lui,
aucune revue ne pouvait être conforme.

**`adapters/base.py` est publié.** §13 rendait le protocole réversible « jusqu'à sa publication » : ce
point est franchi, le modifier coûte désormais une migration.

---

## Budget — à re-arbitrer à la clôture du palier 4

| | brut | code effectif |
|---|---:|---:|
| Production écrite, 9 modules sur 12 | **1 651** | **1 171** |
| Bande §11 | 1 350 – 1 550 | 1 350 – 1 550 |
| Projection au même rythme | **~2 150** | **~1 540** |

*« code effectif » = lignes non vides, hors commentaires et hors docstrings.*
Tests : 1 797 lignes, **163 tests verts**, `ruff` et `mypy --strict` verts.

**Franchie en brut, pas en code effectif.** L'écart est de la documentation de motif, pas de la
fonctionnalité : rien hors spécification, aucun contrôle ajouté. **Les quatre coupes de §11 ne peuvent
pas le fermer** — elles pèsent une quarantaine de lignes, pas cinq cents ; le seul levier de cette
taille serait de retirer les docstrings de motif, c'est-à-dire la méthode du projet. C'est le point 5
de la règle de coupe : arbitrage. Le PO a arbitré « on continue » le 2026-09-03, sur des chiffres plus
petits. Repère de fond non franchi : `POURQUOI` règle 1 — ~2 150 lignes contre les 58 894 de FloraPi.

---

## État courant

- **Étapes 0 et 1 closes.** Spécification : `conception/CONCEPTION_FINALE.md`.
- **Étape 2 : paliers 1, 2 et 3 clos ; caractérisation des CLI faite.** Reste le palier 4.
- **La relecture Codex palier par palier est suspendue** — décision du PO, 2026-09-03. Elle reste la
  règle pour la **conception**. Réouverture si un palier révèle un défaut qu'elle aurait attrapé.
- Récolte : `conception/INVENTAIRE.md` v3, 156 leçons. Cinq tours de structure conservés séparément.
- Le dépôt n'a **pas de remote** — décision reportée.

## Décisions actées

- **Recherche au périmètre, sans accès externe en V0.1.** Condition de réouverture : §12.1.
- **A et B sont chacun l'un ou l'autre outil** — les quatre permutations sont désormais **mesurées**,
  plus seulement exigées.
- **Sept accrétions retirées** de la V2 par audit contre les objectifs fondateurs.
- **Huit remarques techniques de Codex, toutes retenues** (`DISPOSITION_TECHNIQUE_CODEX.md`).
- Paramètres fixés : UTF-8 sans BOM · 8 MiB par flux · **Windows testé, POSIX écrit non testé**.

## Rappels actifs

- La mission DialogForge `e35cfcf1-47e5-4354-a4b1-d40235b8e3cf` est **en pause**, pas annulée. Elle
  redémarrerait seule si on la reprenait. Ne pas la relancer sans décision.
- Les quatre dossiers `C:\Projets\DialogForge*` sont en **lecture seule**. Point d'entrée du gel :
  `C:\Projets\DialogForge\ARRET_REFACTORING.md`.
- Reporté, tracé : la colonne **Code** de l'inventaire plus longue que **Prompt** — après la phase 2.

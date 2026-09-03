# NOTES.md — Reprise immédiate IAbinome

> Tableau de bord court pour démarrer une session.
> État courant uniquement. Historique → `session_log.md`. Règles → `RULES.md`.
> Dernière mise à jour : 2026-09-03

---

## Prochaine action — une seule

**Palier 4 : `adapters/claude.py`, `adapters/codex.py`, `cli.py`, `__main__.py`.**

**La caractérisation §12.2 est faite** — `conception/CARACTERISATION_CLI.md`, 2026-09-03, quatre
appels réels. Elle ne bloque plus rien. Les valeurs à porter dans les adaptateurs y sont.

### Trois décisions à prendre avant ou pendant le palier 4

1. **B-2, maintenant décidable.** La prémisse de §12.3 est **démentie par la mesure** : le shell de
   l'outil 2 *est* retirable (`--disable shell_tool`, vérifié sans appel payant). `CONTEXT_ONLY` ne
   contredit donc plus les quatre permutations. Réserve : un `CONTEXT_ONLY` complet demanderait de
   retirer d'autres drapeaux (`browser_use`, `unified_exec`, `computer_use`…) — **non mesuré**.
2. **Code de retour non nul.** Quota épuisé et modèle invalide rendent tous deux **code 1** chez les
   deux outils — une capacité commune, donc utilisable par le noyau. Et chez l'outil 1 le message de
   quota sort **sur `stdout`** : un `extract()` naïf le prend pour une réponse, et le cycle finit en
   « erreur de contrat » alors que la cause est un quota. **Le moteur doit-il nommer l'incident sur
   le code de retour, avant de tenter le contrat ?**
3. **Base `memories` de l'outil 2.** L'appel est éphémère au sens de la session, pas des effets : un
   état peut se transporter d'un appel au suivant, hors de la collaboration et hors de notre vue.
   Rien de ce que §1 promet n'est cassé — mais la reproductibilité d'un cycle n'est pas garantie.

### Budget — arbitré le 2026-09-03, à re-arbitrer au palier 4

| | brut | code effectif |
|---|---:|---:|
| Production écrite (9 modules sur 12) | **1 651** | **1 171** |
| Bande §11 | 1 350 – 1 550 | 1 350 – 1 550 |
| Projection (reste : `claude.py`, `codex.py`, `cli.py`, `__main__`) | **~2 150** | **~1 540** |

*« code effectif » = lignes non vides, hors commentaires et hors docstrings.*

**Franchie en brut, pas en code effectif** — l'écart est de la documentation de motif, pas de la
fonctionnalité. **Les quatre coupes de §11 ne peuvent pas le fermer** : elles pèsent une quarantaine
de lignes, pas cinq cents. C'est le point 5 de la règle de coupe : arbitrage.
Repère de fond non franchi : `POURQUOI` règle 1 — ~2 150 lignes contre les 58 894 de FloraPi.

### Palier 1 — les cinq modules purs — CLOS le 2026-09-03

**94 tests, 0 échec** (1 ignoré : lien symbolique non privilégié sur la machine de développement —
attendu). `models.py` 301 · `storage.py` 76 · `lock.py` 108 · `contracts.py` 172 · `corpus.py` 107.

**Décisions de conception prises pendant l'implémentation, absentes du texte de la spécification :**
- `last_incident` (`etat.json`) : chemin relatif explicite, pas un objet structuré.
- `contracts.normalize()` : retrait de BOM + empreinte SHA-256. **La normalisation CRLF→LF, laissée
  en suspens ici sous condition qu'un besoin réel apparaisse, a été tranchée au palier 3** — le
  besoin est apparu, voir plus bas.
- `lock.py` sur Windows : **ne jamais utiliser `os.kill(pid, 0)`** — l'implémentation Windows appelle
  `TerminateProcess`, y compris pour le signal `0`. Vivacité testée via `ctypes`/`OpenProcess`.
- `Decision` reste dans `models.py` : `workflow.py` en aura besoin aussi.

### Palier 2 — `fakes.py` + `transport.py` — CLOS le 2026-09-03

**118 tests, 0 échec** (24 nouveaux, 7,7 s). `transport.py` **238 lignes** pour 160 visées ·
`tests/fakes.py` 61 · `tests/test_transport.py` 261. `ruff` et `mypy --strict` verts.

**Décisions de conception prises pendant l'implémentation, absentes du texte de la spécification :**

- **Le faux agent est un vrai sous-processus, pas un `FakeProcess`.** §10 nommait `FakeProcess` et
  `FakeClock` ; ni l'un ni l'autre n'est écrit. Ce que `transport.py` doit tenir est **le comportement
  de l'OS** — deux tubes concurrents, délai, terminaison d'arbre —, et un objet simulé ne le
  prouverait pas. `tests/fakes.py` script donc un vrai `python -c`. **Aucun appel fournisseur, aucun
  réseau** : la règle est tenue, c'est le moyen qui change.
- **`FakeAdapter` a été reporté** faute de protocole d'adaptateur ; il est arrivé au palier 3, avec
  `adapters/base.py`.
- **`Outcome` vit dans `transport.py`, pas dans `models.py`.** Ce n'est pas un des neuf enums fermés de
  la spécification ; c'est le vocabulaire de l'incident (`OUTPUT_LIMIT`, `TIMEOUT`,
  `INTERRUPTED_BY_USER`), et `models.py` dépasse déjà largement son budget.
- **`read_result()` est dans `transport.py`** — ~35 des 238 lignes. La table de reprise §5 relève de
  `workflow.py`, mais le lecteur et l'écrivain d'un format vont ensemble, et c'est ce qui rend la
  règle « `resultat.json` valide = flux complets » testable seule. **Le budget de 160 lignes ne
  comptait vraisemblablement pas ce lecteur : le dépassement propre au transport est d'environ 45
  lignes, pas 78.**
- **Terminaison d'arbre : `taskkill /F /T /PID` sous Windows, `os.kill(-pid, 9)` sous POSIX** (le PID
  négatif désigne le groupe, qui vaut le PID de l'enfant grâce à `start_new_session`). `SIGKILL` n'est
  **pas** nommé : `signal.SIGKILL` est absent de Windows et ferait échouer `mypy` sur le poste.
- **Un descendant qui tient encore les tubes après la sortie de l'enfant déclenche une terminaison
  d'arbre supplémentaire.** Sans elle, `resultat.json` affirmerait « flux complets » sur des fichiers
  qui grossissent encore — exactement ce que §10 interdit. **Cette branche n'est couverte par aucun
  test** : la déclencher demanderait de rendre le délai de grâce configurable, donc une option de
  plus.
- **La branche POSIX est écrite et non testée**, conformément à §0.1. Le poste est Windows.

### Palier 3 — `workflow.py`, `prompts.py`, `adapters/base.py` — CLOS le 2026-09-03

**159 tests, 0 échec** (41 nouveaux, 13 s). `workflow.py` **397** pour 175 visées · `prompts.py` 125
pour 95 · `adapters/base.py` 57 · `test_workflow.py` 271 · `test_recovery.py` 199.

**Le palier 3 a débordé son périmètre nominal, et il le devait :** `workflow.py` ne peut ni s'écrire
ni se tester sans les gabarits de prompts et sans le protocole d'adaptateur. Aucun des deux ne dépend
de §12.2.

**Deux défauts du palier 1 trouvés par les tests du palier 3 :**

- **`parse_review` n'acceptait que du JSON nu**, alors que §6 et §10 acceptent aussi « un bloc JSON
  clôturé couvrant toute la réponse ». Corrigé (`fix:` séparé). Préfixe, suffixe, étiquette de
  langage autre que `json` et second bloc restent refusés.
- **CRLF — la question que le palier 1 avait différée est tranchée, mais sur une preuve plus faible
  que je ne l'ai d'abord écrit.** Le déclencheur était le **faux agent**, qui écrit en mode texte
  Python et rend donc `CRLF` : la balise de première ligne n'était jamais reconnue et le cycle
  finissait en `ERROR`. `normalize()` ramène `CRLF` à `LF` et le consigne, comme le BOM.
  **La caractérisation du même jour montre que les deux vraies CLI rendent des `\\n`** : c'est donc
  une **tolérance** par symétrie avec le BOM, pas la correction d'un défaut observé en production.
  Le brut reste intact sur le disque. Un retour chariot isolé est laissé tel quel.

**Décisions de conception prises pendant l'implémentation, absentes du texte de la spécification :**

- **`_Engine` porte les cinq éléments de contexte d'un cycle** (dossier, configuration, adaptateurs,
  versions sondées, délai) au lieu de les retraverser par douze signatures. Seul module du programme
  à en avoir autant ; c'est une rupture de style assumée, et elle retire ~45 lignes de plomberie.
- **§9 ne donne que le bloc de consignes pour la révision et la finalisation.** Les trois sections de
  charge (DEMANDE, DOCUMENT COURANT, CRITIQUE) sont ajoutées : sans elles, A n'aurait ni l'autorité,
  ni la version courante, ni la critique à traiter.
- **`adapters/base.py` est publié.** §13 rendait le protocole réversible « jusqu'à sa publication » :
  ce point est franchi. `claude.py` et `codex.py` attendent §12.2.
- **Une `QUESTION` produit `echanges/NNNN-question-A.md`** — la spécification ne nomme pas cet
  artefact, mais l'humain doit lire la question quelque part.
- **Transition et `current_call = null` sont une seule écriture atomique**, pas deux. §5 les énumère
  séparément ; les fusionner est plus sûr et l'ordre qui compte — artefact avant transition — est
  tenu.
- **Les trois issues non-`COMPLETED` du transport mènent toutes à `INTERRUPTED`**, jamais à un rejeu.
  `ERROR` est réservé à l'échec de contrat. C'est ce que la table de reprise §5 sait traiter.
- **Aucun compteur de garde sur la boucle du moteur** : `max_revisions` la borne et `FINAL_A` est
  terminal. Un compteur serait un quota interne.

### Caractérisation des CLI — FAITE le 2026-09-03

`conception/CARACTERISATION_CLI.md`. Quatre appels réels, un par outil et par rôle. **Les quatre
permutations sont viables : chaque outil tient A et B, contrat respecté du premier coup.**

**Ce que la mesure a changé dans le code :**

- **Le prompt passe par `stdin`, jamais par argv.** `argv` plafonne à 32 767 caractères sous Windows,
  et une CLI qui voit `DEVNULL` sur son entrée la lit comme un flux canalisé vide : mesuré, la
  réponse tombe de 673 octets conformes à 100 octets de préambule hors contrat. `transport.run()`
  reçoit `stdin_text`, écrit dans un fil pour qu'un gros prompt ne bloque pas avant que `stdout` soit
  drainé.
- **L'exécutable doit être résolu par `shutil.which()`.** L'entrée du PATH de l'outil 2 est un script
  sans extension ; `CreateProcess` rend `WinError 2`.
- **Le prompt de B était inutilisable.** §9 disait « retourne le JSON de revue v1 » sans jamais
  montrer le schéma. Ajouté à `prompts.py` avant les appels ; les deux revues sont conformes.
- **Correction d'un motif faux que j'avais écrit :** aucune des deux CLI n'émet de CRLF. La
  normalisation reste défendable comme **tolérance**, par symétrie avec le BOM, mais la preuve que je
  lui prêtais venait de mon propre faux agent, qui écrit en mode texte Python. Docstring corrigée.
- Même chose, plus légère, pour le bloc JSON clôturé : les deux rendent du **JSON nu**. Le correctif
  reste une tolérance utile, il ne corrigeait pas la cause qu'on lui prêtait.
- `extract()` doit lire **`stdout` seul** : l'outil 2 écrit 8 Ko de bannière sur `stderr` en sortant
  proprement.

**Vérifié contre une vraie CLI, pas seulement contre le faux agent :** délai dur tenu, aucun
`resultat.json` sur `TIMEOUT`, `pid.txt` écrit, et l'arbre `cmd.exe` → `codex.exe` — observé
**présent pendant** l'appel — entièrement terminé après.

### Paliers suivants

**4.** `adapters/claude.py` · `adapters/codex.py` (**après §12.2**) · `cli.py` · `__main__.py`.

---

## État courant

- **Étapes 0 et 1 closes.** La spécification est `conception/CONCEPTION_FINALE.md`.
- **Étape 2 : paliers 1, 2 et 3 clos.** 1 605 lignes de production (1 150 de code effectif),
  1 756 de tests, **159 tests verts**. Reste le palier 4.
- Cinq tours conservés séparément, aucun écrasé : `STRUCTURE_PROPOSEE_CODEX.md` →
  `CRITIQUE_CLAUDE_STRUCTURE_CODEX.md` → `STRUCTURE_PROPOSEE_CLAUDE.md` →
  `STRUCTURE_PROPOSEE_CODEX_V2.md` → `CONCEPTION_FINALE.md` (+ `ANALYSE_VERS_CONCEPTION_FINALE.md`),
  puis `DISPOSITION_TECHNIQUE_CODEX.md`.
- Récolte : `conception/INVENTAIRE.md` v3, **156 leçons** — 43 Code · 34 Prompt · 33 Règle · 23 Test · 23 Écarté.
- Le dépôt n'a **pas de remote** — décision reportée.
- Prédécesseur : DialogForge, refactoring **gelé** le 2026-09-02, toujours utilisé en conception seule sur FloraPi.

## Décisions actées

- **Recherche au périmètre**, mais **sans accès externe en V0.1** — le corpus est ce que l'humain dépose. Condition de réouverture dans `CONCEPTION_FINALE.md` §12.1.
- **A et B sont chacun Claude ou Codex**, décidé au lancement. Quatre permutations testées. Le cycle ne dépend que des capacités communes.
- **Plafond de ~200 lignes de l'inventaire levé** ; la garde reste `POURQUOI` règle 1.
- **Sept accrétions retirées** de la V2 par audit contre les objectifs fondateurs — dont l'appareil d'approbation et le mode de recherche externe.
- **Huit remarques techniques de Codex, toutes retenues** (`DISPOSITION_TECHNIQUE_CODEX.md`).
- Paramètres fixés : UTF-8 sans BOM · 8 MiB par flux · **Windows testé, POSIX écrit non testé**.

## Blocages

- **B-2 non arbitré** : `CONSULT` recommandé. Le prévol refuse déjà `CONTEXT_ONLY` si l'adaptateur
  de B ne le supporte pas — testé. **Tranché par la caractérisation §12.2.**
- *(levé le 2026-09-03 : les deux CLI ont été lancées et caractérisées.)*

## Rappels actifs

- La mission DialogForge `e35cfcf1-47e5-4354-a4b1-d40235b8e3cf` est **en pause**, pas annulée. Elle redémarrerait seule si on la reprenait. Ne pas la relancer sans décision.
- Les quatre dossiers `C:\Projets\DialogForge*` sont en **lecture seule**. Point d'entrée du gel : `C:\Projets\DialogForge\ARRET_REFACTORING.md`.
- Reporté, tracé : la colonne **Code** plus longue que **Prompt** — après la phase 2.

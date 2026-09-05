# Observations — premières missions réelles, 2026-09-04

> **Lot 11 du plan correctif, items 1 à 4.** Deux missions payantes, deux permutations, dans une
> collaboration **jetable hors de tout dossier de valeur** — C-06 est ouvert, et c'est le seul
> confinement réel.
> Autorisation du PO donnée le 2026-09-04. Code testé : `421c0b9` (lots 1 à 10 fermés), plus les deux
> correctifs nés de cet essai.

## 1. Conditions

| | |
|---|---|
| Outil 1 | `2.1.260` — modèles utilisés : `opus`, `sonnet` |
| Outil 2 | `0.153.2` — modèle utilisé : `gpt-5.6-sol` |
| Emplacement | dossier temporaire de session, hors de tout dépôt |
| Enveloppe | `--max-revisions 0` (cycle court), `--timeout 600` |

**Caractérisation préalable, gratuite, avant toute dépense.** Les trois formes d'invocation exactes que
les adaptateurs construisent ont été essayées à vide : `opus` et `sonnet` répondent, outil 2 répond
avec sa bannière sur `stderr` et son contenu sur `stdout`, conformément à ce que son adaptateur
documente.

**Le modèle par défaut de B côté outil 1 est inutilisable sur ce compte.** `--model fable` rend
« You're out of usage credits ». La mission 2 a donc surchargé `--model-b sonnet`. *La conception
prévoit cette surcharge ; le défaut, lui, reste faux pour ce compte — voir `CLAUDE.md` §6.*

## 2. Mission 1 — conception, A = outil 1 · B = outil 2

Demande : rédiger le `GUIDE.md` d'IAbinome, une page.

| Appel | Rôle | Outil | Modèle | Durée | Sortie |
|---|---|---|---|---:|---:|
| 0001 | A | 1 | opus | 191,8 s | 13 462 o |
| 0002 | B | 2 | gpt-5.6-sol | 35,3 s | 2 154 o |
| 0003 | A | 1 | opus | 64,8 s | **perdu au contrat** |
| 0004 | A | 1 | opus | 81,2 s | 6 949 o |

**Issue : `AWAITING_APPROVAL`, phase `CLOSED`, code de sortie `0`.** Livrable de 125 lignes, coiffé de
la ligne écrite par le programme : *« constats restés ouverts : 6 (dont 0 BLOCKING) · corpus absent »*.

**La critique de B n'est pas décorative.** Six constats, dont : la proposition dépasse manifestement la
contrainte d'une page ; l'exemple annoncé comme complet emploie des marques substitutives ; la promesse
« rien n'est perdu » après Ctrl-C n'est pas établie. Le contradicteur contredit — c'est la seule chose
que le protocole existe pour obtenir.

**Le livrable n'est pas adoptable en l'état** : ses six constats ouverts sont à lire avant d'en faire le
`GUIDE.md` du projet. C'est précisément ce que `AWAITING_APPROVAL` veut dire.

## 3. Mission 2 — recherche, A = outil 2 · B = outil 1

Demande : quelles règles fondatrices sont en tension, et laquelle cède en premier. Corpus :
`POURQUOI.md`, `CLAUDE.md`, `project/RULES.md`.

| Appel | Rôle | Outil | Modèle | Durée | Sortie |
|---|---|---|---|---:|---:|
| 0001 | A | 2 | gpt-5.6-sol | 8,2 s | 510 o — `QUESTION` |
| 0002 | A | 2 | gpt-5.6-sol | 152,9 s | 13 827 o |
| 0003 | B | 1 | sonnet | 231,2 s | **refusée au contrat** |

**Issue : `ERROR`, phase `REVIEW_B`, code de sortie `4`.**

A a produit un document de 164 lignes énonçant trois tensions, avec citations et numéros de ligne —
après correction du prompt (§5). B a produit une revue **substantiellement excellente**, qui relève
notamment que `RULES.md` viole sa propre règle de non-répétition en recopiant deux règles de
`POURQUOI.md`. Elle a été refusée pour une raison de forme : voir §6.

## 4. Ce que la mécanique a tenu

- **`invocation_args` trace exactement ce que D-6b promet** : `["-p", "--model", "opus"]` côté outil 1,
  `["exec", "-m", "gpt-5.6-sol", "--sandbox", "read-only", "--skip-git-repo-check", "-"]` côté outil 2.
  Aucun `argv[0]`, donc aucun chemin absolu.
- **`status` répond en lecture seule pendant qu'un `run` tient le verrou.**
- **La table de relance N-01 a servi pour de vrai, et elle a payé.** `CONTRACT_ERROR` étant relançable,
  `resume --retry-call` n'a refait que la finalisation : les deux appels déjà payés ont été conservés.
  C'est exactement ce que le lot 2 avait été écrit pour permettre.
- **`resume --answer` a fonctionné** : `demande.md.001` archivé **par copie**, nouvelle demande en
  place, cycle reparti en `PROPOSAL_A`.
- **Portabilité vérifiée** (item 1) : la collaboration a été **déplacée en cours d'usage**, en `ERROR`,
  vers un autre dossier parent. `status` la relit sans rien changer, et **aucun chemin absolu n'est
  persisté dans un fichier de contrôle**.
- **Codes de sortie conformes à D-5** : `0`, `4`, `5` observés aux bons endroits.
- **Aucun rejeu automatique**, jamais, dans aucun des deux échecs.

## 5. Deux défauts trouvés — aucun que la suite pouvait voir

### 5.1 Les prompts de révision et de finalisation ne portaient pas les balises

`_A_PROPOSAL` nommait `IABINOME:DOCUMENT` en toutes lettres. `_A_REVISION` et `_A_FINAL` disaient
« rends DOCUMENT ». A a obéi littéralement, première ligne `DOCUMENT`, contrat refusé.

**Conséquence : aucune mission ne pouvait aller au bout**, et l'échec tombait au **dernier** appel,
après avoir payé tous les autres. Corrigé (`ea8a009`).

C'est la règle « un prompt qui exige un format doit porter le format », déjà apprise sur le schéma de
revue de B — appliquée à un endroit, jamais vérifiée aux deux autres.

### 5.2 Le prompt interdisait à A de lire son propre corpus

« Tu ne modifies aucun fichier et n'exécutes rien. » A l'a lu comme une interdiction d'ouvrir
`corpus/fichiers/`, et a rendu une `QUESTION` demandant à l'humain d'en **coller le contenu**.

La conception promet l'inverse : l'adaptateur reçoit le dossier de collaboration comme `cwd`
précisément pour qu'il y lise. **La frontière d'effets porte sur l'écriture, jamais sur la lecture.**
Corrigé (`8b96d77`), et consigné en §1 de la conception.

### Pourquoi 259 tests verts ne les voyaient pas

`FakeAdapter` émet la bonne balise quoi qu'on lui demande : **il ne lit pas le prompt**. Aucun test à
faux agent ne pouvait voir un défaut de gabarit. `tests/test_prompts.py` lit désormais les gabarits
eux-mêmes.

## 6. Tranché le 2026-09-05 — le bloc clôturé précédé d'une phrase

**Le fait.** B a rendu ceci :

```text
La sortie attendue suit un schéma précis (…) ; je réponds donc directement en JSON brut, comme demandé.

```json
{"schema_version": 1, "decision": "REVISER", …}
```
```

`_strip_sole_fence` ne retire un bloc clôturé que s'il couvre **toute** la réponse. Une phrase devant,
et le bloc reste en place : `json.loads` échoue en colonne 1. **Le comportement est conforme à la
conception** — la docstring anticipe explicitement le cas : *« un préfixe, un suffixe … laissent le
texte intact — donc refusé plus bas, comme le veut §6 »*, « jamais de défaut permissif ».

**Ce que l'essai ajoute.** Une revue de 3,6 Ko, substantiellement juste et coûteuse (231 s), a été
jetée pour une phrase de politesse. Et la cause est instructive : le préambule de B mentionne un outil
de son propre harnais et **s'explique de ne pas s'en servir**. Ce n'est pas de la désobéissance, c'est
un agent qui commente son choix de format. Rien ne dit que ce soit rare.

**Trois voies, exclusives :**

| | Ce que ça change | Ce que ça coûte |
|---|---|---|
| **A. Statu quo** | rien | un appel payant perdu chaque fois qu'un agent commente son format, et une relance humaine |
| **B. Accepter un bloc `json` clôturé **unique** même entouré de prose** | `_strip_sole_fence` extrait le bloc si et seulement s'il y en a **exactement un** ; zéro ou deux restent un refus | rouvre §6 « jamais de défaut permissif » — mais l'extraction reste **déterministe**, pas une devinette |
| **C. Durcir le prompt de B** | ajouter « aucun texte avant ni après » | `POURQUOI.md` règle 4 : les consignes trop prescriptives **dégradent** les modèles récents ; et B a déjà lu « retourne seulement le JSON » |

### Décision — voie B, PO, 2026-09-05

**Un bloc clôturé est extrait même entouré de prose.** `_strip_sole_fence` devient `_strip_fence`.

**Motif.** La ligne refusée n'était pas un principe mais une position sur une pente : le contrat
tolérait déjà la clôture, et extraire ce qui est explicitement balisé ne demande aucune
interprétation. Un agent qui s'explique de son choix de format n'est ni rare ni désobéissant.

**« Jamais de défaut permissif » tient toujours**, et c'est ce qui rend la voie tenable : le
programme ne cherche jamais *où* le JSON commence dans du texte libre — sans balise, un préfixe ou
un suffixe restent un refus. Il ne lit que ce qui est délimité, et `json.loads` reste l'arbitre.

**La voie B telle qu'écrite dans le tableau ci-dessus était inapplicable.** « Exactement un bloc,
zéro ou deux refusés » suppose un comptage des clôtures ; or B a le droit de citer du markdown dans
`analysis`, et le comptage y découperait au mauvais endroit. **L'ancrage retenu est *première
clôture → dernière clôture*** — celui que le code faisait déjà à l'intérieur d'une réponse
entièrement clôturée. Deux blocs distincts restent refusés, non par un comptage, mais parce que
l'extraction rend alors un texte que `json.loads` rejette.

**Restent intacts — donc refusés :** aucune clôture · une clôture jamais fermée · une étiquette de
langage autre que `json`.

**Un fait à garder en face.** La relecture externe du 2026-09-05 **n'a pas remonté ce point**, alors
que son axe 6 l'y menait. Une lecture neuve ne trouvait rien de choquant à la ligne d'alors : ce
n'est pas une décision que la seule inspection statique imposait, c'est un arbitrage coût contre
principe rendu par le PO. Le défaut n'était pas dangereux — réponse brute préservée, incident nommé,
aucun rejeu automatique, `--retry-call` refaisant le seul appel perdu.

**Fait :** `contracts.py` · deux tests basculés du refus vers l'acceptation, trois ajoutés — dont le
cas exact de la mission et une revue citant du markdown dans `analysis` · **280 tests verts**.

**Vérifié contre le réel.** La réponse refusée est conservée octet pour octet
(`conception/essais/2026-09-04-critique-B-recherche-refusee.txt`, 3 610 o). Rejouée contre le nouveau
`parse_review` : `REVISER`, **cinq constats, tous `OPEN`** — `B-doublon-001` `B-suspension-002`
`B-metrique-003` en `MAJOR`, `B-lecture-004` `B-conclusion-005` en `MINOR`. C'est la revue que 231 s
d'appel payant avaient produite et que la forme avait jetée. *Rejeu hors suite, à la main : la suite
de tests ne lit pas `conception/`.*

## 7. ~~Un motif écrit qui s'est révélé faux — D-2~~ · Rétracté le 2026-09-05

> **Cette section était fausse.** Elle affirmait, « mesuré », que sur un modèle sans crédits outil 1
> rend son message de quota **sur `stdout` avec un code de retour `0`**, et en concluait que le motif
> de D-2 (« quota épuisé et modèle invalide rendent tous deux `1` ») était faux.
>
> **D-2 disait vrai.** Remesuré le 2026-09-05, par redirection vers un fichier :

| Outil | Version | Code | `stdout` | `stderr` |
|---|---|---:|---:|---:|
| 1, modèle `fable` | `2.1.261` | **1** | 146 o — le message de quota | 0 o |
| 2, `gpt-5.6-sol` | `0.153.2` | **1** | 0 o | 4 115 o — le message de quota |

> `CARACTERISATION_CLI.md:162` portait déjà le bon chiffre depuis le 2026-09-03 : « Quota épuisé
> comme modèle invalide : **code 1**. Et chez outil-1, le message de quota sort **sur `stdout`** ».
> Un `0` observé une fois a suffi à le déclarer faux, sans remesure, **contre une source du projet
> qui disait le contraire**.
>
> **Origine probable : un code de retour lu à travers un tube.** Après `cmd | head`, `$?` est celui
> de `head`. Reproduit le 2026-09-05 — une sonde écrite ainsi a affiché `rc=0` pour un outil dont
> `resultat.json` enregistrait `return_code: 1` au même instant. Non prouvé pour le 2026-09-04 ;
> suffisant pour expliquer exactement ce chiffre.

**Ce qui reste vrai, et qui était le vrai contenu de D-2.** Ce qui diffère entre les deux outils est
le **flux**, jamais le code : outil 1 écrit son quota sur `stdout`, outil 2 sur `stderr`. C'est
pourquoi `extract()` ne lit que `stdout` — sans ce choix, le message d'outil 1 serait pris pour une
réponse d'agent et le cycle finirait en `CONTRACT_ERROR`, le diagnostic trompeur que D-2 évite.

Détecter un quota supposerait de lire le texte du fournisseur, ce que §8 interdit : la reconnaissance
de quota reste hors du programme, et c'est l'humain qui lit le message. **La décision D-2 n'a jamais
eu besoin d'être corrigée — c'est sa correction qu'il fallait retirer.**

### Ce que la relance fait, mesuré de bout en bout

Vérifié le 2026-09-05 sur outil 1, gratuitement (`fable` sans crédits) :

| | |
|---|---|
| `run` | `CLI_FAILED` → `INTERRUPTED`, 2,4 s, **sans tentative de contrat** |
| `resume --retry-call` | accepté ; appel `0002-A` créé, **`prompt_sha256` identique** |
| `intention.json` du nouvel appel | `retries` pointe l'appel d'origine, `retry_reason` porte le motif humain, `observed_version` est consignée |
| Second échec | `INTERRUPTED` de nouveau — **une tentative par commande humaine, jamais de boucle** |

**La relance après quota marche des deux côtés, par le même chemin.** `INTERRUPTED` se relance
toujours ; il ne dépend même pas de la table fermée N-01. *C'était l'inverse chez le prédécesseur, où
la reprise après quota était bâtie sur l'erreur typée d'un seul fournisseur — `CLAUDE.md` §6.*

## 8. Coût et friction

**Neuf appels payants au total** (4 + 5), **765 secondes** de temps fournisseur cumulé. Deux perdus au
contrat, dont un entièrement imputable au défaut 5.1 — donc évitable désormais.

**Friction du manifeste de corpus** (item 4). Aucune, mécaniquement : `--source-list` a été écrit à la
main en trois lignes, `corpus.build` a copié et haché sans incident, et la vérification complète sous
verrou du lot 5 n'a jamais refusé à tort sur trois fichiers. **La vraie friction n'était pas dans le
manifeste, elle était dans le prompt** : le corpus était correctement figé, vérifié et présent, et
l'agent ne savait pas qu'il avait le droit de l'ouvrir.

## 9. Ce que ces missions ne prouvent pas

- **Deux permutations sur quatre.** `1→1` et `2→2` n'ont pas été essayées en réel.
- **Aucune boucle de révision** : `--max-revisions 0` par choix d'enveloppe. Le report des constats
  ouverts d'une revue à la suivante n'a donc pas été exercé en réel.
- **Aucun crash réel** n'a été provoqué : la reprise après arrêt brutal reste prouvée par la suite de
  tests seule.
- **`CONTEXT_ONLY` n'a pas été essayé** — les deux missions sont en `CONSULT`.
- **C-06 reste ouvert.** Rien ici ne mesure ce que les agents ont réellement pu lire.

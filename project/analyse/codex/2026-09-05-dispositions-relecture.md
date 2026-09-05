# Dispositions — relecture externe du fonctionnement, 2026-09-05

> Réponse à `2026-09-05-relecture-fonctionnement.md`. **Chaque observation reçoit exactement une
> disposition** (`RULES.md`) : acceptée et intégrée · rejetée avec justification · différée avec
> condition · bloquante.
>
> **Les huit affirmations vérifiables ont été contrôlées dans le code avant toute disposition.** Les
> huit sont exactes. L'observation 4 a été **reproduite** avant d'être corrigée.
>
> Six correctifs, tous **prouvés capables de voir leur défaut** par neutralisation. Suite : 274 tests
> verts, `ruff` et `mypy --strict` verts.

---

## 1. Complétude publiée malgré l'échec d'une pompe — **retenue, corrigée**

**Exacte.** `_Pump.run` sortait de sa boucle sur `OSError` exactement comme sur une fin de flux : le
préfixe déjà copié devenait « le flux », et `resultat.json` en certifiait l'empreinte. Un `fsync` en
échec ne changeait rien non plus.

**Correctif.** La pompe porte `failed` ; une lecture rompue, une écriture ou un `fsync` en échec le
lèvent. Issue `STREAM_FAILED`, **aucun `resultat.json`** — la présence du marqueur reste ce qu'elle
promet.

*Ce que la gravité doit à la lucidité du relecteur : le cas est rare, mais il produit une réponse
**silencieusement tronquée** qui passe le contrat si son début porte la balise. C'est le seul défaut de
la liste qui pouvait corrompre un livrable sans laisser de trace.*

## 2. Intégrité contournée en `RESPONSE_STORED` — **retenue, corrigée**

**Exacte.** §5 annonce la confrontation des flux « avant **toute** branche » ; la branche
`RESPONSE_STORED` rendait avant d'y arriver.

**Correctif.** `transport.read_result(call_dir)` est appelé avant le branchement, pour son
`IntegrityError` seul — sa valeur de retour ne sert pas là. Un `resultat.json` absent n'y devient pas
une nouvelle cause d'échec.

*Choix explicite : implémenter plutôt que corriger la phrase. La promesse était la bonne, c'est le code
qui lui manquait — et le coût est une relecture de deux fichiers, une fois, sur une reprise.*

## 3. Sévérité omise fermant un constat — **retenue, corrigée**

**Exacte.** §6 dit « sévérité omise → `UNKNOWN` après décodage, et le constat **reste ouvert** ». Le
code retenait `UNKNOWN` et gardait la disposition fournie. Le cas construit est juste : B omet la
sévérité, rend `RESOLVED`, le constat sort du registre et le cycle finalise.

**Correctif.** Sévérité omise ⇒ `UNKNOWN` **et** `OPEN`, quelle que soit la disposition rendue.

*Le maintien ne va que dans le sens sûr — il laisse ouvert, il ne ferme jamais. C'est pourquoi il n'est
pas le « jugement sur les sévérités » que §6 interdit par ailleurs : le programme ne décide de rien, il
refuse seulement qu'une omission serve de fermeture.*

## 4. Séparateurs de chemin du corpus — **retenue, reproduite, corrigée**

**Exacte, et la plus grave de la liste.** Reproduite avant correction : `docs\note.md` et `./note.md`
sont acceptés à la copie, persistés tels quels, puis déclarés **surnuméraires** par le balayage qui
compare à `as_posix()`. **Une collaboration créée sans erreur, morte avant son premier appel**, sur la
plateforme annoncée comme supportée.

**Correctif.** Les chemins logiques sont canonisés en forme POSIX à l'écriture du manifeste et à sa
relecture. C'est aussi ce que la portabilité exige (§3) : un chemin à contre-oblique ne survivrait pas
au déplacement entre machines que le dossier de collaboration promet.

*Mes propres tests du lot 5 n'écrivaient que des `/`. C'est exactement le genre de défaut qu'une
lecture extérieure attrape et qu'une suite verte ne montre pas.*

## 5. Verrou tronqué par l'arrêt de son créateur — **retenue, correctif refusé, promesse corrigée**

**Exacte.** Un arrêt entre la création exclusive de `verrou.json` et l'écriture de son contenu laisse
un fichier illisible ; `_read` lève avant tout test de vivacité, et la récupération n'est jamais
atteinte. Toutes les commandes qui font avancer la collaboration s'arrêtent.

**Le correctif implicite est refusé, et c'est la seule observation où je ne suis pas le relecteur.**
Récupérer un verrou illisible sous jeton reviendrait à supprimer le verrou d'un détenteur **vivant**
surpris dans sa propre fenêtre création→écriture. Or **c'est exactement la même fenêtre** : le crash
qu'on répare et la course qu'on introduit ont la même probabilité, à ceci près que la seconde produit
**deux détenteurs simultanés** au lieu d'un blocage visible. On échangerait un arrêt franc contre une
corruption silencieuse. `POURQUOI.md` règle 2 : la question n'est pas « ce contrôle est-il utile ? »,
c'est « qu'est-ce que je retire en échange ? » — ici, la garantie d'exclusion elle-même.

**Ce qui est fait à la place.** Le message d'erreur nomme le fichier et dit quoi en faire, comme le lot
1 le fait déjà pour un jeton de récupération orphelin ; et la docstring cesse de promettre que la
récupération couvre **tous** les arrêts brutaux. La limite résiduelle est écrite, pas masquée.

## 6. Code 1 après mutation — **retenue, corrigée**

**Exacte, et la tension documentaire qu'elle relève l'est aussi** : §5 plaçait le corpus dans le prévol
sans mutation, §7 sous verrou juste avant l'appel — le lot 5 avait déplacé le contrôle sans corriger
§5.

**Correctif.** `check_corpus()` passe **sous verrou, avant l'intervention** : une seule vérification,
toujours sous verrou, mais désormais avant toute mutation. Le code 1 redit la vérité, et une
`--answer` refusée pour un corpus cassé reste rejouable à l'identique une fois le corpus réparé.

*Effet de bord assumé : une reprise purement locale vérifie désormais le corpus elle aussi. C'est plus
fidèle à §3 — un corpus qui a bougé invalide la collaboration entière, qu'un appel parte ou non.*

## 7. `RuntimeError` nu et artefacts orphelins — **retenue, corrigée**

**Exacte sur les deux points.** `_resolve()` levait un `RuntimeError` absent de la table des types de
frontière — donc une traceback. Et `command()` était résolu après le `mkdir` et `prompt.txt`, alors que
le commentaire annonçait « un refus sans mutation ».

**Correctif.** `AdapterError`, type **nommé**, levé par les deux adaptateurs et ajouté à la table de
frontière. Et `command()` est résolu **avant le premier octet écrit** : le refus ne laisse plus rien
derrière lui.

*Conséquence sur l'outillage de test, traitée plutôt que contournée : `FakeAdapter.calls` compte
désormais des **résolutions**, qui bornent par le haut les appels réellement partis.
`fakes.launched_calls()` lit le disque pour la mesure exacte, et les deux tests concernés s'appuient
dessus. Ne pas l'avoir fait aurait affaibli l'assertion sur laquelle repose toute la preuve « aucun
appel payé ».*

## 8. `DECODE_FAILED` : reprise locale promise, jamais écrite — **retenue, promesse corrigée, optimisation différée**

**Exacte, et c'est ma documentation qui est fausse.** J'ai écrit au lot 8 que « la reprise ne retente
que l'extraction, aucun appel supplémentaire n'étant nécessaire ». Le fait est vrai — les flux sont
complets — mais le code n'en fait rien : `--retry-call` construit un nouvel appel, payant.

**Correctif documentaire.** §5 dit désormais ce que le code fait.

**Différé, avec sa condition de déclenchement** (`RULES.md`) : ré-extraire localement sur
`DECODE_FAILED` économiserait un appel. À écrire **le jour où un `DECODE_FAILED` est observé en usage
réel** — pas avant : ce serait financer une optimisation pour un incident jamais rencontré.

---

## Les réserves — dispositions

| Réserve | Disposition |
|---|---|
| Le prévol sonde les deux CLI même pour une reprise purement locale : refusée si l'une manque | **Retenue, différée avec condition.** Vraie, et gênante — une réponse déjà payée devient inexploitable parce qu'une CLI est absente. Mais la lever suppose de savoir avant le prévol si un appel sera nécessaire, ce que seule la porte d'état sait, sous verrou. À rouvrir **si le cas se produit en usage réel.** |
| « Aucune commande ne mute hors du verrou » contredit par les pompes qui écrivent après la libération | **Retenue, documentaire.** §7 est absolu là où §5 assume déjà l'exception. §7 renvoie désormais à §5. |
| UTF-8 sans BOM contredit par la copie binaire du corpus et par `write_atomic_text` | **Retenue, documentaire.** §0.1 vaut pour les artefacts **du programme** ; le corpus est copié octet pour octet, et c'est voulu — l'empreinte du manifeste porte sur ces octets. Écrit en §0.1. |
| Le prompt de B exige de motiver les fermetures, le contrat accepte un `statement` vide | **Rejetée.** C'est la distinction que §9 pose : le prompt porte des critères **intellectuels**, l'analyseur des critères **vérifiables**. Exiger un `statement` non vide serait un contrôle de plus pour un défaut jamais observé. |
| Le schéma montré à B omet `UNKNOWN` et la possibilité d'omettre `severity` | **Rejetée, et c'est délibéré.** La tolérance existe pour ne pas perdre une revue ; l'annoncer inviterait à s'en servir. Depuis l'observation 3, l'omission ne peut plus rien fermer — le coût d'en abuser est désormais nul pour nous. |
| Fenêtre entre l'écriture du livrable et la publication de `AWAITING_APPROVAL` | **Retenue, documentaire.** L'en-tête dit « le cycle s'est achevé » ; dans cette fenêtre l'état dit encore `RUNNING`, et la reprise republie. Précisé en §2. |
| §9 cite encore l'ancien prompt de A, avec son interdiction implicite de lire | **Retenue, corrigée.** Documentation périmée depuis le correctif d'hier soir. Excellente prise : c'est précisément la contradiction entre sources que la consigne demandait de signaler. |
| §12.2 affirme l'absence de mesure CLI malgré les mesures relatées ailleurs | **Retenue, corrigée.** |
| « Aucun nom de fournisseur hors de `adapters/` » contredit par les imports de `cli.py` | **Retenue, précisée.** La règle vise les **identifiants persistés et le noyau**, pas le point de câblage qui enregistre les adaptateurs. §3 le dit désormais. |
| `call_dir` est une chaîne non confinée, base des écritures d'incident | **Rejetée — hors périmètre de confiance.** Un `etat.json` modifié à la main n'est pas dans le modèle de menace : il est écrit pour être lisible et corrigible par l'humain. Ce serait un contrôle contre le propriétaire du dossier. |
| Effets réels des CLI et terminaison des descendants non établis | **Retenue, déjà ouverte.** C'est C-06, risque accepté et limite déclarée. Rien de neuf. |

---

## Ce que cette relecture a rapporté

**Huit observations, huit exactes.** Six ont produit un correctif de code, deux une correction de
documentation. Une seule a vu son correctif implicite refusé — et le motif du refus est chiffrable :
la course introduite a la même fenêtre que le crash réparé, pour une conséquence pire.

**Le rendement dément mon pronostic.** J'attendais « moyen » et j'avais tort. La différence avec
l'audit du 2026-09-04 tient à la question : « où promet-il ce qu'il ne tient pas » force à citer une
phrase et à construire un cas, là où « audite ce déploiement » invitait à énumérer des risques.

**Trois défauts sur six vivaient dans une fenêtre** — lecture rompue, arrêt entre deux écritures,
séparateur de chemin — et **aucun n'était atteignable par un cycle nominal**. C'est la démonstration
que la relecture externe et la suite de tests ne couvrent pas le même espace, et que suspendre la
première parce que la seconde est verte était une erreur de raisonnement.

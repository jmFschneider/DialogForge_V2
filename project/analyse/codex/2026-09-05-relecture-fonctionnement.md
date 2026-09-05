# Relecture du fonctionnement d’ensemble — 2026-09-05

Première passe selon la consigne du 2026-09-05 : lecture statique de `src/iabinome/` et de `conception/CONCEPTION_FINALE.md` exclusivement, après lecture de la consigne. Aucun test consulté ; aucun programme, test ou appel fournisseur exécuté. Les cas ci-dessous sont déduits du code, pas reproduits expérimentalement. Seul ce rapport est écrit, conformément à la demande de sauvegarde de l’utilisateur. Les références sont relatives à la racine du dépôt et désignent les lignes lues lors de cette passe.

## 1. Les observations

1. **LA PROMESSE** — « Sortie propre → `flush`, `fsync`, écriture de `resultat.json` (code retour, tailles, empreintes). » (`conception/CONCEPTION_FINALE.md:293`) ; « sa présence est la preuve que les flux sont complets. » (`conception/CONCEPTION_FINALE.md:326`).

   **LE CODE** — `_Pump.run` intercepte une erreur de lecture et sort de la boucle comme sur une fin de flux (`src/iabinome/transport.py:326`). Les erreurs d’ouverture, d’écriture, de `flush` ou de `fsync` terminent le fil sans être communiquées au coordinateur (`transport.py:324`, `transport.py:335`, `transport.py:339`). Celui-ci vérifie seulement si les fils sont terminés et si un débordement a été signalé (`transport.py:194`, `transport.py:146`). Si le processus sort avec succès, il publie `resultat.json` (`transport.py:161`), même si une pompe a échoué.

   **LE CAS** — La CLI termine normalement avec un code 0 ; la pompe de `stdout` reçoit une `OSError` de lecture après avoir copié seulement le début de la réponse. Cette erreur est absorbée, le préfixe est synchronisé, le fil se termine et `resultat.json` décrit ce préfixe comme le flux complet. S’il commence par `IABINOME:DOCUMENT`, l’analyseur A accepte le document tronqué, car il vérifie la balise sans pouvoir connaître la partie perdue (`src/iabinome/contracts.py:78`). Autre cas : un échec de `fsync` dans la pompe n’empêche pas la publication du marqueur censé suivre sa réussite.

   **GRAVITÉ** — majeur : une erreur de transport ou de conservation peut devenir une réponse complète et alimenter le cycle sans incident ; les empreintes du préfixe ne révèlent pas sa troncature.

2. **LA PROMESSE** — « À la reprise, avant **toute** branche : » puis « `resultat.json` est confronté aux **tailles et empreintes** des deux flux. » (`conception/CONCEPTION_FINALE.md:377`, `conception/CONCEPTION_FINALE.md:382`). « Une divergence est consignée en `INTEGRITY_MISMATCH` / `INTERRUPTED` » (`conception/CONCEPTION_FINALE.md:386`).

   **LE CODE** — Dans `resume_verified`, la branche `RESPONSE_STORED` vérifie le prompt et la réponse brute, puis appelle directement `apply` et retourne (`src/iabinome/workflow.py:470`, `workflow.py:473`). `transport.read_result`, qui confronte réellement les flux à leurs tailles et empreintes, n’est appelé qu’après cette branche (`workflow.py:478` ; `src/iabinome/transport.py:230`).

   **LE CAS** — Arrêt après publication de `RESPONSE_STORED`, avant l’artefact de phase. `stdout.txt` est ensuite tronqué ou supprimé, tandis que `prompt.txt`, `reponse_brute.txt`, `resultat.json` et l’état restent intacts. La reprise applique la réponse et poursuit le cycle sans constater que le flux contredit le résultat enregistré.

   **GRAVITÉ** — majeur : une branche de reprise contourne explicitement la garantie d’intégrité commune ; le cycle peut avancer sur un dossier de preuve devenu incohérent.

3. **LA PROMESSE** — « Sévérité omise → `UNKNOWN` **après** décodage, et le constat **reste ouvert**. » (`conception/CONCEPTION_FINALE.md:485`).

   **LE CODE** — `_parse_finding` remplace bien une sévérité absente par `UNKNOWN`, mais conserve indépendamment la disposition fournie (`src/iabinome/contracts.py:162`, `contracts.py:170`). `open_finding_ids` ne garde que les dispositions `OPEN` (`contracts.py:148`). `apply_b` publie cette liste et peut passer à `FINAL_A` sur `ACCEPTER` (`src/iabinome/workflow.py:550`, `workflow.py:557`).

   **LE CAS** — Le constat `B-001` était ouvert. B retourne `{"schema_version":1,"decision":"ACCEPTER","analysis":"Revue terminée","findings":[{"id":"B-001","disposition":"RESOLVED","statement":"Correction vérifiée"}]}`. L’identifiant antérieur est bien présent et aucun champ obligatoire ne manque. Le constat devient `UNKNOWN`/`RESOLVED`, disparaît des constats ouverts et le cycle passe à la finalisation, contrairement au maintien ouvert annoncé.

   **GRAVITÉ** — majeur : la tolérance d’une sévérité absente permet de fermer un constat que le contrat promet de maintenir ouvert, avec un effet sur le registre et le livrable final.

4. **LA PROMESSE** — « Copie vers `destination/fichiers/...` chaque chemin listé dans `source_list` (un par ligne, relatif à `source_root`), écrit `destination/manifeste.json`, et retourne le manifeste. » (`src/iabinome/corpus.py:103`) ; « Le corpus est vérifié contre son manifeste avant chaque appel » (`conception/CONCEPTION_FINALE.md:530`).

   **LE CODE** — La copie utilise `Path(logical_path)` pour les contrôles, mais conserve la chaîne d’entrée telle quelle dans le manifeste (`src/iabinome/corpus.py:124`, `corpus.py:142`, `corpus.py:146`). La recherche des fichiers surnuméraires convertit les chemins trouvés avec `as_posix()` avant de les comparer aux chaînes du manifeste (`src/iabinome/workflow.py:256`, `workflow.py:687`).

   **LE CAS** — Sous Windows, une liste contient le chemin relatif courant `docs\note.md`. `new` trouve et copie ce fichier, puis persiste `docs\note.md`. Au premier `run`, la vérification de contenu réussit, mais le même fichier est ensuite nommé `docs/note.md` par `as_posix()` ; il est déclaré surnuméraire. Le dossier créé normalement est inutilisable pour le cycle alors que son corpus n’a pas changé. Le même désaccord existe avec une entrée telle que `./note.md`.

   **GRAVITÉ** — majeur : une entrée relative acceptée à la création rend immédiatement la collaboration inexécutable sur la plateforme annoncée comme supportée.

5. **LA PROMESSE** — « Le libère à la sortie normale — jamais garanti après un arrêt brutal, ce que la récupération de verrou mort existe pour couvrir au prochain lancement. » (`src/iabinome/lock.py:58`).

   **LE CODE** — `_create_exclusive` crée d’abord `verrou.json`, puis écrit son contenu (`src/iabinome/lock.py:99`, `lock.py:103`). Si ce fichier existe au lancement suivant, `_acquire` commence par le décoder, avant de rechercher si son détenteur est mort (`lock.py:86`). Un fichier vide ou partiellement écrit provoque `LockError` et ne rejoint jamais la récupération (`lock.py:149`).

   **LE CAS** — Le processus est tué entre la création exclusive de `verrou.json` et l’écriture complète de son JSON. Le fichier vide ou tronqué survit, mais pas son détenteur. Chaque `run` ou `resume` suivant s’arrête sur « verrou illisible » ; aucune de ces commandes ne peut atteindre la reprise du cycle. Le cas exige une intervention manuelle sur le fichier, que ce chemin d’erreur n’indique pas.

   **GRAVITÉ** — majeur : un arrêt brutal dans la publication du verrou échappe à la récupération annoncée et bloque toutes les commandes qui font avancer une collaboration pourtant intacte.

6. **LA PROMESSE** — Code 1 : « refus **avant mutation** : prévol, verrou détenu, argument invalide » (`conception/CONCEPTION_FINALE.md:561`).

   **LE CODE** — `run` applique l’intervention humaine avant de construire le nouvel appel (`src/iabinome/workflow.py:144`). `apply_answer` archive et remplace la demande, puis publie l’état `READY` (`workflow.py:295`). La vérification complète du corpus arrive ensuite, dans `new_call` (`workflow.py:356`). Son refus remonte à `_drive`, qui rend le code 1 (`src/iabinome/cli.py:145`, `cli.py:208`). La conception contient ici aussi une tension d’ordre : le §5 place le corpus dans le prévol sans mutation (`conception/CONCEPTION_FINALE.md:282`), tandis que le §7 impose sa vérification sous verrou, juste avant l’appel (`conception/CONCEPTION_FINALE.md:530`).

   **LE CAS** — La collaboration attend une réponse humaine et un fichier du corpus a été supprimé. L’humain lance `resume --answer nouvelle-demande.md`. Le programme archive l’ancienne demande, installe la nouvelle, passe en `READY`, puis refuse le corpus absent et sort en code 1. Répéter la même commande après restauration du corpus échoue parce que la collaboration n’est plus en `WAITING_HUMAN` ; un `run` est désormais nécessaire.

   **GRAVITÉ** — majeur : le code de sortie promet l’absence de mutation alors que l’autorité fonctionnelle et l’état ont changé, ce qui modifie aussi la commande de reprise admissible.

7. **LA PROMESSE** — « À la frontière, `run`, `resume` et `status` rendent un **refus lisible, jamais une traceback**, en attrapant des types **nommés un par un**. » (`conception/CONCEPTION_FINALE.md:416`). Le commentaire de résolution promet aussi « un refus sans mutation » si l’exécutable disparaît entre prévol et appel (`src/iabinome/workflow.py:369`).

   **LE CODE** — Les deux adaptateurs lèvent un `RuntimeError` simple si leur résolution de l’exécutable échoue (`src/iabinome/adapters/claude.py:49`, `src/iabinome/adapters/codex.py:52`). Ce type n’appartient pas à `_BORDER_ERRORS` (`src/iabinome/cli.py:189`). Avant cette résolution, `new_call` a déjà créé le dossier d’appel et écrit `prompt.txt` (`src/iabinome/workflow.py:360`, `workflow.py:362`, `workflow.py:373`).

   **LE CAS** — L’exécutable est présent pendant `probe`, puis disparaît du chemin résolu avant `command`, par exemple lors de son remplacement par un installateur. La commande se termine par une traceback `RuntimeError` et laisse un dossier d’appel contenant le prompt. `CALLING` n’a pas été publié et aucun appel n’est parti, mais les deux propriétés annoncées du refus ne sont pas tenues.

   **GRAVITÉ** — mineur : le refus survient dans une fenêtre étroite, sans appel fournisseur, mais son diagnostic et son absence d’écriture sont incorrectement annoncés.

8. **LA PROMESSE** — « `DECODE_FAILED` appartient à la table fermée des incidents relançables : la reprise ne retente que l’extraction, aucun appel supplémentaire n’étant nécessaire. » (`conception/CONCEPTION_FINALE.md:430`). Cette phrase contredit la relance par nouvel UUID décrite au même document (`conception/CONCEPTION_FINALE.md:396`, `conception/CONCEPTION_FINALE.md:403`).

   **LE CODE** — L’échec d’extraction publie `ERROR`/`DECODE_FAILED` (`src/iabinome/workflow.py:435`). Sans intervention, la porte d’état refuse `ERROR` (`workflow.py:339`). Avec `--retry-call`, l’incident est relançable, mais `apply_retry` efface `current_call` en mémoire, et `run` exécute `new_call`, donc un nouvel appel fournisseur (`workflow.py:108`, `workflow.py:319`, `workflow.py:149`).

   **LE CAS** — Un flux complet n’est pas décodable en UTF-8 et produit `DECODE_FAILED`. `resume` seul refuse l’état. La commande indiquée, `resume --retry-call <uuid> --reason-file motif.md`, déclenche un nouvel appel ; elle ne retente pas l’extraction des flux conservés.

   **GRAVITÉ** — mineur, contradiction documentaire : le code applique la politique générale de relance humaine, mais l’autre phrase promet une reprise locale qui n’existe pas. Les deux règles écrites étant incompatibles, ce constat ne tranche pas laquelle doit faire autorité et ne qualifie pas à lui seul la relance de défaut du code.

## 2. Les axes examinés

1. Protocole d’appel en neuf étapes — **écart trouvé** : complétude publiée malgré une erreur de pompe (observation 1), intervention persistée avant un refus présenté comme préalable à toute mutation (observation 6).
2. Machine à états — **aucun écart identifié** dans les transitions ordinaires `DOCUMENT`, `QUESTION`, `REVISER`, `BLOQUE`, `ACCEPTER`, la limite des révisions et l’arrivée en `AWAITING_APPROVAL` ; le cas `UNKNOWN`/fermé est classé dans les contrats (observation 3).
3. Reprise après interruption — **écart trouvé** : intégrité des flux contournée en `RESPONSE_STORED` (observation 2), verrou partiellement publié (observation 5), contradiction sur `DECODE_FAILED` (observation 8).
4. Verrou — **écart trouvé** : récupération impossible d’un verrou tronqué par l’arrêt de son créateur (observation 5) ; les mutations synchrones d’une collaboration existante passent bien par le verrou dans les chemins ordinaires examinés.
5. Surface en ligne de commande — **écart trouvé** : code 1 après modification de la demande et de l’état (observation 6), traceback à la disparition de l’exécutable (observation 7).
6. Contrats d’échange — **écart trouvé** : sévérité absente permettant néanmoins la fermeture du constat (observation 3).
7. Fichiers écrits sur disque — **écart trouvé** : marqueur de complétude possible malgré l’échec d’une pompe (observation 1), artefacts laissés par un refus annoncé sans mutation (observation 7).
8. Frontière d’effets et portabilité — **écart trouvé** : chemins relatifs acceptés à la copie et refusés à l’usage (observation 4) ; les effets réels des CLI et la terminaison d’arbre ne sont pas établis par cette lecture statique.

## 3. Les réserves

- Les tests n’ont été ni lus ni exécutés : aucune affirmation sur leur couverture, leur réussite ou leur capacité à détecter ces cas.
- Les capacités effectives des adaptateurs, leurs configurations utilisateur et la terminaison des descendants n’ont pas été mesurées ; les limites explicitement acceptées en §1 et §12.3 ne sont pas rouvertes.
- Une reprise locale passe d’abord par les sondages de présence des deux CLI (`workflow.py:174`) : elle est refusée si l’une manque, même avec une réponse complète ; la promesse de retraitement local et celle de sonder chaque `run` ne précisent pas la priorité dans ce cas.
- La promesse de chemins d’écriture fermés (§1, ligne 71) n’est pas établie pour un `etat.json` modifié manuellement ou des répertoires remplacés par des liens : `call_dir` est une chaîne non confinée (`models.py:230`) et sert de base aux écritures d’incident (`workflow.py:629`) ; le périmètre de confiance envers ces modifications n’est pas explicité.
- En cas de `STREAMS_UNCLOSED`, des pompes peuvent continuer à écrire après le retour et la libération du verrou ; ce comportement est explicitement assumé en §5, lignes 365–368, mais contredit la formulation absolue « aucune commande ne mute la collaboration hors du verrou » (§7, ligne 547).
- La conservation exacte du brut et des octets du corpus entre en tension avec « Tout est écrit en UTF-8 sans BOM, fins de ligne `\n` » (§0.1, ligne 48) : `storage.write_atomic_text` n’enlève ni BOM ni CRLF et la copie du corpus est binaire ; une exception documentaire n’est pas formulée à cet endroit.
- Le prompt de B exige de motiver les fermetures (`prompts.py:42`), mais le contrat n’exige qu’une chaîne `statement`, éventuellement vide (`contracts.py:171`, `contracts.py:221`) ; le texte ne distingue pas clairement exigence intellectuelle adressée à B et garantie assurée par l’analyseur.
- Le schéma présenté à B omet `UNKNOWN` et la possibilité d’omettre `severity` (`prompts.py:51`), tous deux admis par l’analyseur ; cette différence peut être une tolérance volontaire plutôt qu’un défaut.
- L’en-tête final annonce que la présence du fichier prouve l’achèvement, mais un arrêt peut survenir entre l’écriture du livrable et la publication de `AWAITING_APPROVAL` (`workflow.py:529`) ; le sens d’« achevé » dans cette fenêtre n’est pas précisé.
- Le document de conception conserve des formulations dépassées : interdiction de lecture implicite dans l’ancien prompt A (§9, ligne 634) malgré l’autorisation explicite de lire (§1, ligne 87), et absence prétendue de toute mesure CLI (§12.2, ligne 775) malgré les mesures relatées ailleurs ; ce sont des contradictions documentaires.
- La phrase « Aucun nom de fournisseur hors de `adapters/` » (§3, ligne 181) est littéralement contredite par l’enregistrement des adaptateurs dans `cli.py:26` et `cli.py:42` ; le workflow utilise néanmoins des identifiants opaques, et aucun cas de permutation défectueuse n’a été établi sur cette base.

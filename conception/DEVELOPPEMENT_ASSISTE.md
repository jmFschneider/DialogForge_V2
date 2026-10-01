> Ce document n'est pas approuvé : sa présence prouve que le cycle s'est achevé, rien de plus.
> Revue B : CONSULT · constats restés ouverts : 2 (dont 0 BLOCKING) · corpus figé le 2026-09-26.
> Version examinée par B (`echanges/0005-revision-2-A.md`), livrée sans réécriture : acceptée par B. Voir `bilan.md`.


# DialogForge V2 — lot 4 : développement assisté

> Conception révisée le 2026-09-27 à partir du seul corpus fourni, instantané du 2026-09-26.
> Statut proposé : acceptable dans le cadre de la délégation du PO.
> Le lot transmet des documents et constitue des paquets de preuve. Il ne développe, ne teste, ne commit, ne fusionne, n’installe et ne déploie rien.

## 1. Décision d’architecture

Le lot utilise les collaborations documentaires ordinaires de DialogForge. Il n’ajoute ni second cycle A/B, ni nouvel état durable d’appel, ni commande spéciale pour appeler B.

```text
collaboration de conception acceptée
  → export du mandat
  → développement, Git et validations hors DialogForge
  → constitution atomique d’un paquet immuable
  → création d’une collaboration ordinaire de revue de code
  → A rédige un rapport documentaire
  → B critique ce rapport en consultant le paquet figé
  → A répond et révise le rapport
  → B effectue la relecture ciblée
  → décision humaine sur le rapport et la révision identifiée
```

Les rôles sont distincts :

- le développeur extérieur est seul auteur du code ;
- A est l’auteur documentaire du rapport de revue ;
- B critique ce rapport et les preuves du paquet ;
- l’humain choisit les révisions, les validations, les suites données au code et la décision finale.

Le développeur extérieur ne devient pas A dans le moteur. Ses explications éventuelles sont des pièces déclaratives du paquet, pas de faux fichiers `reponses-A.json`.

Le lot ajoute seulement trois fonctions locales :

1. exporter une conception acceptée ;
2. construire un paquet immuable à partir de deux commits et de résultats déjà produits ;
3. vérifier le rattachement entre un paquet et une collaboration de revue.

Toute orchestration reste assurée par `new`, `run`, `resume`, `show` et `decide`.

## 2. Périmètre Git amendé

La conception existante exclut une fonction de production qui « touche Git ». La demande du PO du 2026-09-26 autorise explicitement la lecture de Git pour identifier une révision et extraire son diff.

Amendement normatif :

> Amendement du 2026-09-26 — lot 4 : DialogForge peut invoquer Git en lecture seule afin de résoudre deux commits et de lire les objets nécessaires à un paquet de revue. Toute modification du dépôt, de l’index, d’une référence ou d’un worktree reste interdite. DialogForge ne crée ni branche, ni worktree, ni commit, et n’effectue ni merge, installation ou déploiement.

Cette autorisation ne permet pas d’exécuter le code ou les validations du projet cible.

## 3. Parcours utilisateur

### 3.1 Passage au développement

Après acceptation de la conception :

```text
dialogforge dev-export <collaboration-conception> --output <dossier-export>
```

L’humain transmet le dossier produit à son agent de développement habituel. Celui-ci travaille hors de DialogForge avec PWF, Git et les commandes de validation du projet.

### 3.2 Constitution du paquet

Une fois un commit candidat et ses validations disponibles :

```text
dialogforge dev-package \
  --export <dossier-export> \
  --repo <dépôt> \
  --base <révision> \
  --head <révision> \
  [--validation <résultat-json> ...] \
  [--developer-note <fichier> ...] \
  [--previous-review <collaboration> ...] \
  --output <dossier-paquet>
```

Toutes les validations destinées à la revue sont fournies lors de cette construction. Un paquet publié n’est jamais enrichi.

### 3.3 Collaboration de revue

Le paquet contient `review-request.md` et `sources.txt`. L’humain crée ensuite une collaboration ordinaire :

```text
dialogforge new <collaboration-revue> \
  --demande <paquet>/review-request.md \
  --kind conception \
  --reviewer-access consult \
  --source-root <paquet> \
  --source-list <paquet>/sources.txt \
  --agent-a <claude-ou-codex> \
  --agent-b <claude-ou-codex> \
  --web-access-ou-no-web-access
```

> **Amendement du 2026-10-01 (PO, `TYPES_DE_MISSION.md` D5)** : la collaboration de revue est de
> type `--kind recherche` — elle établit des faits sourcés dans le paquet. Le texte ci-dessus est
> celui du livrable accepté, laissé tel quel.

Puis :

```text
dialogforge run <collaboration-revue>
dialogforge show <collaboration-revue>
dialogforge decide <collaboration-revue> \
  --accept | --accept-with-reserves <texte> | --correct <fichier> | --stop
```

`--correct` est permis lorsque la correction porte uniquement sur le rapport documentaire et que le paquet reste inchangé.

Si le code ou les validations changent, l’humain ne lance pas `decide --correct` pour substituer silencieusement les preuves : il construit un nouveau paquet et crée une nouvelle collaboration.

### 3.4 Vérification avant décision

Avant d’accepter :

```text
dialogforge dev-verify \
  --package <dossier-paquet> \
  --review <collaboration-revue>
```

La commande ne décide rien. Elle refuse si le corpus de la collaboration ne correspond pas exactement au paquet, si la demande ne nomme pas son identité ou si une décision existante ne porte plus sur les empreintes applicables.

## 4. Export de la conception acceptée

### 4.1 Préconditions

`dev-export` exige :

- une collaboration en `AWAITING_APPROVAL` ;
- une dernière décision applicable `ACCEPTE` ou `ACCEPTE_AVEC_RESERVES` ;
- la concordance des empreintes de `demande.md`, du livrable et de la revue avec cette décision ;
- l’absence du dossier de sortie, afin de ne rien écraser.

Un document seulement livré mais non accepté ne peut pas être exporté.

### 4.2 Fichiers produits

```text
<export>/
├── export.md
└── export.json
```

`export.md` contient :

1. l’identité de la collaboration ;
2. la demande d’origine ;
3. la conception acceptée intégrale ;
4. la décision humaine applicable ;
5. les réserves humaines ;
6. les constats encore `OPEN`, avec leur historique utile ;
7. les contraintes de développement ;
8. l’exigence de deux commits ;
9. le contrat des résultats de validation ;
10. la frontière des responsabilités.

Il précise notamment que :

- le développement et les tests ont lieu hors de DialogForge ;
- un résultat de validation est une déclaration, non une attestation de DialogForge ;
- une correction de code exige un nouveau commit ;
- tout changement de code ou de validation destiné à B exige un nouveau paquet.

`export.json` contient :

```json
{
  "schema_version": 1,
  "source_collaboration": "nom",
  "request_sha256": "sha256:…",
  "document_sha256": "sha256:…",
  "review_sha256": "sha256:…",
  "decision_sha256": "sha256:…",
  "export_md_sha256": "sha256:…"
}
```

Le chemin absolu de la collaboration n’est pas conservé. `export.json` contrôle le passage de relais ; il ne devient pas une seconde demande.

## 5. Paquet de revue immuable

### 5.1 Publication

`dev-package` vérifie toutes ses entrées, construit dans un dossier temporaire adjacent, vérifie les empreintes, puis renomme atomiquement le dossier vers `--output`.

Le dossier de sortie doit être absent. Un paquet publié n’est jamais modifié par DialogForge.

Ajouter ou retirer une validation, une note du développeur ou un antécédent impose un nouveau paquet doté d’un nouvel identifiant.

### 5.2 Structure

```text
<paquet>/
├── review-request.md
├── package.json
├── sources.txt
├── export/
│   ├── export.md
│   └── export.json
├── revision/
│   ├── revision.json
│   ├── diff.patch
│   ├── files.json
│   └── files/
│       └── <fichiers ajoutés ou modifiés>
├── validations/
│   └── <validation-id>.json
├── developer-notes/
│   └── <NNNN>.md
└── antecedents/
    └── <NNNN>/
        ├── provenance.json
        ├── demande.md
        ├── version_finale.md
        ├── derniere-critique-B.json
        ├── bilan.md
        ├── decisions.json
        └── objections.json
```

Les deux derniers dossiers peuvent être vides.

`package.json` manifeste tous les fichiers du paquet sauf lui-même. Chaque entrée porte son chemin relatif, sa taille et son SHA-256. Aucun horodatage n’entre dans l’identité.

`sources.txt` énumère chaque fichier à copier dans le corpus de la future collaboration, y compris `package.json`. Il n’énumère pas `sources.txt` lui-même.

### 5.3 Identité

L’identité est calculée après constitution complète :

```text
package-id = SHA-256(JSON canonique {
    schema_version,
    export_sha256,
    base_oid,
    head_oid,
    diff_sha256,
    code_files_manifest_sha256,
    validations_manifest_sha256,
    developer_notes_manifest_sha256,
    antecedents_manifest_sha256
})
```

Les manifestes internes sont des listes canoniques triées de couples chemin/empreinte.

La date de construction et les chemins absolus sont exclus. À entrées identiques, deux constructions donnent le même `package-id`.

Les validations appartiennent ainsi à l’identité du paquet vu par B. Il n’existe pas d’import postérieur dans un paquet déjà revu.

## 6. Révision Git capturée

### 6.1 Révisions admises

`--base` et `--head` sont obligatoires. Ils sont résolus en OID complets de commits.

La V1 ne capture que les objets compris entre ces deux commits :

- aucun worktree ;
- aucun index ;
- aucun fichier non suivi ou ignoré ;
- aucune modification non committée ;
- aucun cache produit par des tests.

### 6.2 Contenu

`revision.json` contient au minimum :

```json
{
  "schema_version": 1,
  "base_oid": "OID complet",
  "head_oid": "OID complet",
  "diff_sha256": "sha256:…",
  "code_files_manifest_sha256": "sha256:…",
  "limitations": []
}
```

`diff.patch` est le diff Git binaire, complet pour les deux arbres désignés.

`files.json` liste les entrées ajoutées, modifiées, supprimées ou dont le type change. Chaque entrée copiée indique le mode Git, le type d’objet et l’empreinte du blob.

Tous les blobs ajoutés ou modifiés sont copiés depuis l’objet `head`. Les suppressions sont représentées dans `diff.patch` et `files.json`.

Il n’existe aucune « limite déjà configurée » dans le corpus courant. Le lot n’en invente pas. Les limites pratiques de la CLI, du système de fichiers et des appels d’agents sont documentées, mais aucun fichier n’est tronqué silencieusement. Une future limite de taille demanderait une décision distincte.

### 6.3 Commandes Git autorisées

L’implémentation lance Git sans shell, avec des arguments séparés :

```text
git rev-parse --verify <rev>^{commit}
git diff --binary --full-index --no-ext-diff --no-textconv <base_oid> <head_oid> --
git diff --name-status -z --no-renames <base_oid> <head_oid> --
git cat-file -t <head_oid>:<path>
git cat-file blob <head_oid>:<path>
```

Environnement minimal imposé :

```text
GIT_OPTIONAL_LOCKS=0
GIT_PAGER=cat
GIT_EXTERNAL_DIFF=
```

Les chemins issus de Git sont traités comme des octets ou avec le mécanisme de substitution explicite de Python ; ils ne sont jamais interpolés dans une commande shell. Les chemins absolus, `..`, NUL et sorties du dossier `revision/files/` sont refusés.

### 6.4 Limites explicites

La capture couvre les objets Git des deux commits, pas tout ce qui peut participer à une construction :

- les fichiers ignorés et non suivis sont absents ;
- le contenu d’un sous-module n’est pas copié : seul son gitlink est représenté ;
- un dépôt Git LFS fournit le blob pointeur committé, pas nécessairement l’objet LFS ;
- les filtres clean/smudge ne sont pas exécutés ;
- les textconv et diff externes sont désactivés ;
- les binaires figurent dans le diff binaire et les blobs copiés, mais B peut ne pas pouvoir les interpréter ;
- les fichiers inchangés nécessaires au contexte ne sont pas inclus ;
- les renommages sont représentés sans détection de renommage, donc comme suppression et ajout ;
- le paquet ne prouve ni la reproductibilité du build ni l’état du système qui a exécuté les validations.

`review-request.md` impose à A et B de placer toute conséquence de ces limites dans « Non couvert ».

## 7. Résultats de validation

Chaque `--validation` désigne un JSON déjà produit hors de DialogForge :

```json
{
  "schema_version": 1,
  "validation_id": "tests-projet",
  "head_oid": "OID complet",
  "command": ["python", "-m", "unittest"],
  "started_at": "2026-09-26T10:00:00Z",
  "completed_at": "2026-09-26T10:04:12Z",
  "exit_code": 0,
  "outcome": "PASSED",
  "environment": "Python 3.12, Windows",
  "summary": "412 tests réussis",
  "artifacts": []
}
```

`outcome` vaut `PASSED`, `FAILED`, `NOT_RUN` ou `UNKNOWN`.

DialogForge vérifie :

- le schéma fermé ;
- l’unicité de `validation_id` ;
- l’égalité de `head_oid` avec le commit candidat ;
- la cohérence minimale des types ;
- l’intégrité du fichier copié.

Il ne lance pas `command`, n’ouvre pas les artefacts externes et ne certifie ni l’auteur, ni l’environnement, ni l’exécution réelle.

Le JSON source ne contient pas encore de `package-id`, puisque celui-ci dépend notamment de l’ensemble des validations. Le rattachement se fait par :

1. égalité de `head_oid` ;
2. inclusion et empreinte du résultat dans `package.json` ;
3. inclusion du manifeste des validations dans le `package-id`.

Toute modification d’un résultat crée donc un paquet distinct et exige une nouvelle collaboration. Une revue ne bénéficie jamais rétroactivement d’un test ajouté ensuite.

## 8. Demande de revue générée

`review-request.md` est l’unique autorité de la collaboration de revue créée avec `new`. Il contient :

- le `package-id`, `base_oid` et `head_oid` ;
- le lien logique vers l’export accepté ;
- l’objectif : produire un rapport documentaire sur le code extérieur ;
- l’interdiction de modifier ou d’exécuter le projet ;
- la liste des validations déclarées ;
- les limites de capture ;
- les éventuels antécédents ;
- les critères du rapport ;
- la signification de la future décision humaine.

Le rapport demandé à A doit contenir :

```markdown
# Rapport de revue de code

## Révision examinée
## Résumé de la modification
## Conformité à la conception acceptée
## Vérifié
## Contesté
## Non couvert
## Limites des validations
## Constats antérieurs
## Conclusion et suites humaines
```

Règles :

- « Vérifié » cite une pièce précise du paquet ;
- « Contesté » expose les affirmations du développeur ou d’un rapport antérieur qui ne sont pas retenues comme établies ;
- « Non couvert » nomme les exigences sans preuve suffisante ;
- aucun résultat déclaré n’est présenté comme exécuté par DialogForge ;
- la conclusion ne signifie jamais merge, installation ou déploiement.

## 9. Raccordement exact au cycle A/B existant

Aucun gabarit `dev-review` n’est ajouté.

Dans la collaboration ordinaire :

- `DEMANDE` est exactement `review-request.md` ;
- `DOCUMENT COURANT` est le rapport produit par A ;
- `CONSTATS ANTÉRIEURS` est construit par le moteur existant depuis les échanges de cette même collaboration ;
- le paquet est le corpus figé copié par `new`.

`reviewer_access=consult` est obligatoire pour ce parcours, car le comportement existant de `CONTEXT_ONLY` n’injecte pas le corpus dans `prompts.build_review`. La documentation et `dev-verify` refusent de déclarer conforme une collaboration de revue créée en `context-only`.

En mode `consult`, A et B travaillent chacun dans le dossier jetable existant contenant seulement la copie manifestée sous `corpus/fichiers/`. Ni le dépôt vivant, ni la collaboration avec ses journaux privés ne deviennent leur dossier courant.

La revue de B conserve exactement le schéma v2 existant. Les échanges conservent le nommage existant à quatre chiffres :

```text
echanges/0001-critique-B.json
echanges/0001-reponses-A.json
echanges/0002-critique-B.json
```

`objections.ledger` continue donc à fonctionner sans modification.

## 10. Réponses, contestations et relecture

A répond aux constats dans le contrat v1 existant :

- `CORRIGE` : le rapport est corrigé ;
- `CONTESTE` : A maintient son analyse, avec motif ;
- `REPORTE` : le point reste hors périmètre ou conditionnel ;
- `ARBITRAGE` : une question doit être tranchée par l’humain.

Le cycle existant appelle ensuite B en relecture ciblée sur la même collaboration et le même paquet, que les réponses soient `CORRIGE`, `CONTESTE`, `REPORTE` ou `ARBITRAGE`.

Il n’est donc pas nécessaire de modifier le code pour permettre à B :

- de maintenir un constat `OPEN` ;
- de le déclarer `RESOLVED` après une explication documentaire ;
- de le retirer avec `WITHDRAWN` ;
- de relever en `NOTE` une régression nouvelle de la correction du rapport.

Une réponse `CONTESTE` ne ferme pas le constat. Sa situation est visible dans l’historique unique de `objections.ledger`.

Si B demande une correction du code, le rapport doit le dire. La correction elle-même se déroule hors de DialogForge et produit un nouveau commit, un nouveau paquet et une nouvelle collaboration.

## 11. Transmission entre révisions

Une nouvelle version du code ou des validations ne reprend pas les fichiers `echanges/` dans une nouvelle collaboration.

`--previous-review` copie comme pièces d’antécédent :

- la demande précédente ;
- le rapport final ;
- la dernière critique de B ;
- le bilan ;
- les décisions ;
- une projection JSON de `objections.ledger` ;
- les empreintes et le nom de la collaboration source.

Ces fichiers sont placés sous `antecedents/` et manifestés. Ils sont donc visibles à A et B comme sources, sans prétendre être les échanges de la nouvelle collaboration.

`review-request.md` exige :

- qu’A dresse la liste de tous les constats antérieurs ;
- qu’il indique, preuve à l’appui, s’ils paraissent corrigés, maintenus ou non évaluables ;
- que B contrôle cette reprise dans sa critique.

Aucun identifiant d’appel, état ou échange artificiel n’est injecté. Le nouveau cycle commence normalement par `0001-critique-B.json`.

Cette solution conserve l’historique intellectuel tout en laissant chaque paquet et chaque décision indépendants.

## 12. Incidents et reprises

Les appels d’A et de B sont ceux du moteur ordinaire. Ils utilisent donc sans extension :

- `etat.json.current_call` ;
- les dossiers `appels/` ;
- le verrou de la collaboration ;
- la publication de `CALLING` avant le lancement ;
- `RESPONSE_STORED` ;
- les incidents existants ;
- `resume --retry-call <uuid> --reason-file <fichier>` ;
- `resume --reprocess <uuid> --reason-file <fichier>`.

Il n’existe plus de `developpement/etat.json`, de protocole spécial `dev-review`, ni de choix laissé à l’implémenteur sur la tenue du verrou.

`dev-export`, `dev-package` et `dev-verify` n’appellent aucun agent. Leur reprise est une nouvelle invocation après suppression humaine éventuelle d’un dossier temporaire nommé par l’erreur. Ils ne relancent rien automatiquement et n’écrasent jamais une sortie publiée.

## 13. Décision et autorité

La décision sur la revue utilise `decide` sans extension.

Les empreintes existantes portent sur :

- `demande.md`, qui contient le `package-id`, `base_oid` et `head_oid` ;
- le rapport documentaire exact ;
- la dernière revue de B.

Le corpus manifesté contient le paquet exact. `dev-verify` recalcule son identité et vérifie que la copie du corpus correspond.

Ainsi, une décision applicable porte indirectement mais sans ambiguïté sur :

```text
package-id
  → export accepté
  → base et tête Git
  → diff et blobs copiés
  → validations vues par A et B
  → antécédents
  → demande de revue
  → rapport et critique exacts
```

Sémantique :

- `--accept` accepte le rapport comme compte rendu de la révision ;
- `--accept-with-reserves` accepte le rapport en conservant les réserves humaines ;
- `--correct` corrige uniquement le document tant que le paquet est inchangé ;
- `--stop` arrête cette collaboration ;
- aucune décision ne fusionne, ne déploie ou n’approuve automatiquement le code dans Git.

Si le code ou les validations changent après la décision, celle-ci reste une preuve historique valide pour l’ancien paquet, mais ne s’applique pas au nouveau.

## 14. Surface CLI

Ajouts :

```text
dialogforge dev-export <collaboration>
  --output DIR

dialogforge dev-package
  --export DIR
  --repo DIR
  --base REV
  --head REV
  [--validation FILE ...]
  [--developer-note FILE ...]
  [--previous-review COLLAB ...]
  --output DIR

dialogforge dev-verify
  --package DIR
  --review COLLAB
```

Réutilisés sans modification de contrat :

```text
dialogforge new
dialogforge run
dialogforge resume
dialogforge status
dialogforge show
dialogforge decide
dialogforge list
dialogforge plan
```

Il n’existe pas de :

- `dev-review` ;
- `dev-respond` ;
- `dev-decide` ;
- `dev-add-validation` ;
- `dev-resume` ;
- second registre d’objections ;
- second fichier d’état ;
- nouvelle action dans `decisions.allowed_actions`.

Rien n’est ajouté à la GUI V1.

## 15. Vérification de rattachement

`dev-verify` est strictement en lecture seule. Il vérifie :

1. le schéma fermé de `package.json` ;
2. toutes les tailles et empreintes ;
3. l’absence de fichier surnuméraire dans le paquet ;
4. le recalcul du `package-id` ;
5. la présence du même `package-id`, `base_oid` et `head_oid` dans `review-request.md` ;
6. l’identité entre le paquet et les fichiers copiés dans `corpus/fichiers/` ;
7. la présence de toutes les sources dans le manifeste du corpus ;
8. `reviewer_access=consult` ;
9. si la collaboration est terminée, l’applicabilité de la décision existante aux empreintes courantes ;
10. l’absence de validation extérieure au paquet invoquée par le rapport comme si B l’avait vue.

Le point 10 est un contrôle textuel limité aux identifiants de validation déclarés. Il ne prétend pas comprendre toute la prose. Une référence non reconnue est signalée comme erreur de rattachement, pas automatiquement interprétée.

La commande rend un résumé comprenant :

- paquet vérifié ;
- révision ;
- validations incluses ;
- décision applicable ou absente ;
- constats `OPEN` ;
- réponses `CONTESTE` ou `ARBITRAGE` présentes dans le registre.

## 16. Fichiers et autorité

| Élément | Autorité |
|---|---|
| Besoin initial | `demande.md` de la collaboration de conception |
| Conception acceptée | livrable, revue et décision applicable de cette collaboration |
| Passage de relais | `export.md`, contrôlé par `export.json` |
| Code examiné | objets `base_oid` et `head_oid`, diff et blobs manifestés |
| Validations | déclarations JSON incluses dans le paquet |
| Mission de revue | `review-request.md`, devenu `demande.md` de la collaboration |
| Rapport | `livrables/version_finale.md` de la collaboration de revue |
| Constats et réponses | `echanges/` et `objections.ledger` existants |
| Décision | `decisions.json` de la collaboration de revue |
| Continuité entre versions | pièces manifestées sous `antecedents/` |

Un antécédent informe la nouvelle revue ; il ne modifie jamais l’autorité de la nouvelle `demande.md`.

## 17. Erreurs refusées avant publication

### Export

- conception non acceptée ;
- décision devenue inapplicable ;
- empreinte divergente ;
- dossier de sortie existant.

### Paquet

- export incohérent ;
- base ou tête ne résolvant pas un commit ;
- commande Git ou mécanisme externe non autorisé ;
- chemin Git dangereux ;
- validation dupliquée ou portant sur une autre tête ;
- antécédent sans livrable ou provenance vérifiable ;
- fichier d’entrée modifié pendant la construction ;
- dossier de sortie existant.

### Vérification

- manifeste ou identité incohérents ;
- fichier absent, modifié ou surnuméraire ;
- mauvais paquet dans le corpus ;
- demande ne nommant pas la révision ;
- collaboration en `context-only` ;
- décision devenue inapplicable.

Un refus ne transforme pas un paquet incomplet en paquet valide.

## 18. Tests automatisés

La suite utilise uniquement la bibliothèque standard, l’agent `fake` pour le cycle ordinaire et un dépôt Git temporaire local. Aucun fournisseur ni dépôt distant n’est appelé.

### Export

- refus avant acceptation ;
- acceptation simple et avec réserves ;
- export des constats `OPEN` ;
- divergence d’empreinte ;
- sortie déterministe hors métadonnées non identitaires ;
- absence de chemin absolu.

### Capture Git

- deux commits résolus en OID complets ;
- ajout, modification, suppression et changement de mode ;
- diff texte et binaire ;
- blobs copiés depuis `head` ;
- renommage représenté par suppression/ajout ;
- gitlink de sous-module sans contenu du sous-module ;
- pointeur LFS traité comme blob ordinaire ;
- exclusion des fichiers ignorés, non suivis, de l’index et du worktree ;
- refus des chemins dangereux ;
- absence d’appel shell.

### Contre-épreuve Git

Dans un dépôt temporaire :

1. configurer un diff externe, un textconv et un fsmonitor instrumentés ;
2. démontrer séparément que l’instrumentation peut créer ses témoins ;
3. exécuter `dev-package` ;
4. vérifier qu’aucun témoin n’apparaît ;
5. comparer avant/après l’index, la configuration, les références et les fichiers du dépôt ;
6. consigner la version de Git utilisée.

Une plateforme où cette preuve échoue n’est pas déclarée compatible avec la capture.

### Identité et validations

- entrées identiques donnant le même `package-id` ;
- nouvelle tête donnant un autre identifiant ;
- ajout, retrait ou modification d’une validation donnant un autre identifiant ;
- mauvais `head_oid` refusé ;
- quatre valeurs d’`outcome` conservées ;
- commande déclarée jamais exécutée ;
- paquet publié jamais enrichi ;
- date de construction sans effet sur l’identité.

### Collaboration ordinaire

Avec l’agent `fake` :

- `new` copie exactement le paquet manifesté ;
- `consult` donne accès à la copie jetable ;
- ni le dépôt vivant ni les journaux de collaboration ne sont présents dans le dossier courant ;
- A produit le rapport structuré ;
- B rend la revue v2 exacte ;
- fichiers `0001-*` et `0002-*` ;
- `objections.ledger` conserve les quatre réponses ;
- tour sans modification de code avec `CONTESTE`, `REPORTE` et `ARBITRAGE` ;
- relecture ciblée sur le même paquet ;
- reprise d’incident par les commandes existantes ;
- aucune modification de `models.Phase`, de `State` ou de `allowed_actions`.

### Nouvelle version

- nouveau paquet et nouvelle collaboration ;
- antécédents copiés comme sources, jamais dans `echanges/` ;
- constats antérieurs repris dans le rapport ;
- anciennes validations absentes sauf comme preuve historique d’antécédent ;
- ancienne décision toujours liée à l’ancien paquet ;
- `dev-verify` refusant toute confusion entre les deux.

## 19. Essai réel sur DialogForge_2

Le projet de l’essai est DialogForge_2, conformément à la désignation du PO.

La modification choisie est limitée à la documentation de la nouvelle commande `dev-verify` :

- compléter son entrée et son contrat dans `docs/COMMANDES.md` ;
- ne modifier aucun comportement d’exécution ;
- un seul fichier du projet cible ;
- retour arrière par abandon de la branche ou commit inverse, hors DialogForge.

Cette modification est choisie parce qu’elle est réelle, utile au lot, localisée et réversible, tout en ne confondant pas l’essai avec la construction des primitives Git elles-mêmes.

Déroulement :

1. faire accepter la conception du lot ;
2. produire `dev-export` ;
3. remettre l’export à l’agent de développement habituel ;
4. créer hors DialogForge une branche et un commit de base ;
5. modifier `docs/COMMANDES.md` ;
6. exécuter hors DialogForge les contrôles documentés et pertinents du projet ;
7. commit de tête créé par l’humain ou son agent ;
8. enregistrer les résultats avec le `head_oid` exact ;
9. construire un paquet avec ces résultats ;
10. créer une collaboration ordinaire de revue en `consult` ;
11. lancer le cycle A/B ;
12. vérifier que le rapport distingue « Vérifié », « Contesté » et « Non couvert » ;
13. exécuter `dev-verify` ;
14. décider sur le rapport ;
15. si une correction du fichier est demandée, produire un nouveau commit, de nouveaux résultats, un nouveau paquet et une nouvelle collaboration avec l’antécédent.

Contrôles appropriés :

- commandes de documentation ou de lint déjà présentes dans DialogForge_2 ;
- à défaut de contrôle automatisé portant sur Markdown, inspection du diff et résultat `NOT_RUN` motivé pour ce qui n’est pas couvert ;
- la suite générale peut être déclarée si elle est effectivement exécutée, mais elle ne prouve pas à elle seule la justesse éditoriale.

Réussite :

- DialogForge n’écrit pas dans Git et n’exécute aucun test ;
- le paquet désigne exactement les deux commits ;
- les résultats importés désignent la tête ;
- A et B voient le même paquet figé ;
- la décision porte sur le rapport de ce paquet ;
- toute correction ou validation différente crée un autre `package-id` ;
- l’antécédent est transmis sans faux échange ;
- le retour arrière reste une opération Git extérieure.

## 20. Taille

Le nouveau plafond du PO remplace la marge ancienne de 164 lignes :

- référence avant lot : 5 618 lignes de code effectif dans `src/` ;
- ajout net autorisé : strictement inférieur à 1 000 lignes ;
- cible : 500 lignes au maximum.

Estimation de production :

| Élément | Lignes nettes estimées |
|---|---:|
| Schémas et utilitaires canoniques | 35–55 |
| `dev-export` | 45–70 |
| Lecture Git et copie des blobs | 85–125 |
| Construction et identité du paquet | 80–120 |
| Import des validations et antécédents | 45–70 |
| `dev-verify` | 45–70 |
| Branchements CLI et aide | 35–55 |
| **Total** | **370–565** |

La cible de 500 lignes est plausible mais non garantie avant mesure. La borne nominale haute la dépasse de 65 lignes ; elle reste très inférieure au plafond absolu de 1 000 lignes.

Ordre de réduction si le compteur dépasse 500 :

1. mutualiser la canonicalisation et les contrôles avec `corpus.py` ;
2. garder les notes développeur comme simples fichiers Markdown sans sous-schéma ;
3. reporter l’option répétable `--previous-review` en conservant un seul antécédent ;
4. reporter le contrôle textuel du point 10 de `dev-verify`, sans retirer les vérifications d’empreintes.

Ne sont pas retirés :

- l’immutabilité du paquet ;
- l’identité incluant les validations ;
- le rattachement à deux commits ;
- l’absence d’écriture Git ;
- la copie jetable du corpus ;
- la décision versionnée.

Si la mesure atteint 1 000 lignes nettes, l’implémentation s’arrête avant publication et revient au PO. Le plafond n’est pas relevé implicitement.

Les tests, la documentation et les fichiers de conception ne comptent pas dans cette croissance de `src/`, conformément à la métrique formulée, mais leur volume reste mesuré séparément.

## 21. Travail humain retiré

| Fonction | Travail retiré |
|---|---|
| Export | Recopier la conception, les réserves et les objections |
| Capture | Composer manuellement le diff et extraire les nouveaux fichiers |
| Identité | Vérifier visuellement que code et résultats parlent du même commit |
| Paquet immuable | Se souvenir de ce que B avait effectivement reçu |
| Péremption | Déterminer si un test ajouté après coup appartenait à la revue |
| Collaboration | Construire à la main le mandat de revue |
| Antécédents | Recopier les rapports et constats entre versions |
| Vérification | Comparer manuellement paquet, corpus et décision |

Restent humains :

- choisir le dépôt, la base, la tête et les validations ;
- développer ;
- exécuter les contrôles ;
- créer branches et commits ;
- expliquer les choix du développeur ;
- décider si une réserve est acceptable ;
- fusionner, installer et déployer ;
- décider d’une relance payante après incident.

## 22. Choix fermés

L’implémentation n’a pas à redécider les points suivants :

- seuls deux commits sont capturés ;
- Git est lu, jamais écrit ;
- les validations sont produites ailleurs ;
- le paquet est complet et immuable dès sa publication ;
- les validations entrent dans le `package-id` ;
- tout changement de code, validation ou preuve produit un nouveau paquet ;
- toute nouvelle version est revue dans une nouvelle collaboration ;
- les antécédents sont des sources manifestées, jamais de faux échanges ;
- le développeur extérieur écrit le code, A écrit le rapport ;
- B est appelé uniquement par le cycle existant ;
- la revue de code exige `reviewer_access=consult` ;
- les prompts, phases, états, reprises et dispositions existants sont réutilisés ;
- les échanges gardent leur nom à quatre chiffres ;
- une relecture sans correction de code se déroule normalement dans la même collaboration ;
- une correction purement documentaire peut utiliser `decide --correct` ;
- l’acceptation porte sur un rapport et une révision, jamais sur un merge ou un déploiement ;
- aucune fonction n’est ajoutée à la GUI V1 ;
- le lot vise au plus 500 lignes nettes et doit rester strictement sous 1 000.

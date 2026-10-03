# DialogForge Runner V1 — conception

> **Statut : proposition de conception — 2026-10-01**
>
> Ce document définit un exécuteur autonome de développement destiné à prolonger la chaîne actuelle :
>
> **Recherche → Conception → Développement**
>
> Il ne remplace pas le moteur documentaire A/B de DialogForge. Il se place de l'autre côté du passage de relais déjà matérialisé par `dev-export`.
>
> Principe directeur :
>
> **DialogForge décide ce qui doit être réalisé. Le Runner dispose d'une autonomie locale pour le réaliser, dans un contrat borné. PWF conserve sa mémoire de travail. Git et les validations établissent les faits. L'humain conserve l'autorité avant le développement et avant l'intégration du résultat.**

## 1. Origine et contraintes

La conception part de quatre faits déjà établis dans DialogForge V2.

`POURQUOI.md` montre que l'ancienne couche d'autonomie était devenue beaucoup plus complexe que la boucle documentaire et n'avait mené ni FloraPi ni DialogForge à une implémentation autonome complète. Le Runner V1 ne doit donc pas reconstituer cette architecture.

`conception/DEVELOPPEMENT_ASSISTE.md` a déjà défini une frontière stable :

```
conception acceptée
→ dev-export
→ développement extérieur
→ Git + validations
→ dev-package
→ revue A/B
→ décision humaine
```

`src/iabinome/development.py` implémente déjà les trois opérations qui assurent la continuité documentaire :

```
dev-export
dev-package
dev-verify
```

Enfin, PWF est déjà éprouvé comme mécanisme de persistance du travail de développement, tandis que `planlink.py` maintient volontairement le plan hors du moteur A/B.

Le Runner doit donc **occuper la place du « développeur extérieur » existant**, et non créer un nouveau workflow dans `workflow.py`.

# 2. Décision d'architecture

## D1 — Un second moteur, pas une extension de `workflow.py`

DialogForge devient conceptuellement :

```
                         DIALOGFORGE

           ┌─────────────────────────────┐
           │                             │
           ▼                             ▼

   moteur documentaire             Runner V1
   -------------------             ---------
   recherche                       développement
   conception                      édition du code
   contradiction A/B               validations
   décision humaine                Git local

           │                             │
           └────── contrats fichiers ────┘
```

Le moteur A/B actuel n'importe jamais le Runner.

Le Runner peut utiliser quelques primitives techniques de DialogForge, mais il n'appelle jamais `workflow.run()` pour développer.

## D2 — Même dépôt au départ, exécutable séparé

V1 reste dans `DialogForge_V2`, mais dans un namespace distinct :

```
src/
├── iabinome/
│   ├── workflow.py
│   ├── development.py
│   ├── transport.py
│   ├── storage.py
│   ├── lock.py
│   └── ...
│
└── dialogforge_runner/
    ├── cli.py
    ├── contracts.py
    ├── state.py
    ├── runner.py
    ├── workspace.py
    ├── validation.py
    ├── pwf.py
    └── adapters/
        ├── base.py
        └── <adaptateur qualifié>.py
```

Deux exécutables :

```
dialogforge
dialogforge-run
```

Une séparation ultérieure en deux dépôts reste possible parce que la frontière fonctionnelle est constituée de fichiers.

## D3 — Dépendance à sens unique

Le Runner peut réutiliser :

```
iabinome.transport
iabinome.storage
iabinome.lock
certaines politiques d'environnement
iabinome.development pour le protocole dev-export/dev-package
```

Il ne réutilise pas :

```
workflow.py
contracts.py des rôles A/B
decisions.py
objections.py
prompts.py du cycle documentaire
```

Les contrats d'exécution sont une famille distincte.

# 3. Les autorités

Le Runner distingue strictement six niveaux.

| Élément                              | Autorité                              |
| ------------------------------------ | ------------------------------------- |
| Ce qu'il faut réaliser               | `export.md` produit par `dev-export`  |
| Ce que le Runner a le droit de faire | `contract.json`                       |
| Mémoire et décomposition du travail  | PWF                                   |
| Modifications réellement effectuées  | Git                                   |
| Validité mécanique du candidat       | validations exécutées par le Runner   |
| Acceptation du résultat              | humain + chaîne `dev-package` / revue |

Cette hiérarchie est fondamentale.

En particulier :

```
PWF ≠ autorité fonctionnelle
réponse du LLM ≠ preuve de test
rapport du LLM ≠ état Git
```

L'agent peut écrire dans PWF :

> il faudrait aussi modifier le déploiement

mais si le contrat interdit ce périmètre :

```
NEEDS_HUMAN
```

Le plan ne peut jamais élargir le contrat.

# 4. Périmètre de V1

Le Runner V1 sait :

- consommer un `dev-export` valide ;
- travailler sur un dépôt Git local ;
- créer un environnement de travail indépendant ;
- utiliser un seul agent codeur ;
- conserver le travail avec PWF ;
- lancer plusieurs étapes successives sans intervention humaine ;
- modifier et créer des fichiers dans son espace autorisé ;
- exécuter des validations explicitement autorisées ;
- réparer une validation échouée dans une boucle bornée ;
- créer des commits locaux ;
- reprendre après un arrêt propre ;
- s'arrêter lorsqu'une décision humaine devient nécessaire ;
- construire à la fin un paquet compatible avec le développement assisté existant.

V1 ne sait pas :

```
push
merge
rebase du dépôt d'origine
déploiement
installation en production
modification d'une base réelle
accès à du matériel réel
gestion de secrets
multi-agent de développement
queue de travaux
worker
daemon
planification
budget de tokens
stratégie adaptative de modèles
revue LLM après chaque tâche
```

Aucune de ces fonctions n'entre implicitement plus tard : chacune demanderait une nouvelle décision d'architecture.

# 5. Espace d'une exécution

Une exécution possède son propre dossier :

```
run/
├── contract.json
├── state.json
│
├── source/
│   ├── export.md
│   └── export.json
│
├── calls/
│   ├── 0001/
│   ├── 0002/
│   └── ...
│
├── validations/
│
├── handoff/
│
└── sandbox/
    ├── workspace/
    │   └── dépôt Git autonome
    │
    ├── input/
    │   ├── export.md
    │   └── execution.md
    │
    └── .planning/
        └── <run-id>/
            ├── task_plan.md
            ├── findings.md
            └── progress.md
```

`contract.json`, `state.json`, les appels et les validations restent **hors de la racine writable de l'agent**.

L'agent travaille uniquement sous :

```
sandbox/
```

La copie `sandbox/input/export.md` n'est pas une autorité : sa source immuable est `source/export.md`.

# 6. Le contrat d'exécution

Le contrat d'exécution complète `dev-export` ; il ne remplace pas la conception.

`export.md` décrit **quoi faire**.

`contract.json` décrit principalement **ce qui est permis pour le faire**.

Exemple de schéma V1 :

```
{
  "schema_version": 1,
  "run_id": "2026-10-01-florapi-irrigation",

  "source": {
    "source_collaboration": "florapi-irrigation",
    "export_sha256": "...",
    "export_metadata_sha256": "..."
  },

  "repository": {
    "base_oid": "..."
  },

  "agent": {
    "adapter_id": "agent-x",
    "model": "...",
    "effort": "..."
  },

  "scope": {
    "allowed_paths": [],
    "denied_paths": [
      "deployment/**",
      "secrets/**"
    ],
    "dependency_changes": false
  },

  "validation": {
    "step": [],
    "final": []
  },

  "limits": {
    "max_steps": 20,
    "max_validation_repairs": 3,
    "max_changed_files": 40,
    "call_timeout_seconds": 1800
  },

  "permissions": {
    "network": false,
    "push": false,
    "merge": false,
    "deploy": false,
    "real_hardware": false
  }
}
```

Le schéma est fermé.

Clé inconnue, valeur inconnue ou type incorrect :

```
CONTRACT_ERROR
```

Un `contract.json` modifié après le premier lancement invalide la reprise.

Son empreinte est conservée dans `state.json`.

# 7. Profil du projet

Les commandes de validation et les zones particulièrement sensibles ne doivent pas être inventées par le modèle.

V1 accepte soit des paramètres explicites lors de `prepare`, soit un profil de projet versionné, par exemple :

```
dialogforge-run.toml
```

Exemple conceptuel :

```
[scope]
deny = [
    "deployment/**",
    "secrets/**",
    "hardware/live/**"
]
dependency_changes = false

[validation]
step = [
    ["ruff", "check", "."]
]

final = [
    ["python", "-m", "pytest"],
    ["mypy"]
]
```

Le profil est lu **sur le commit de base**.

Ses valeurs sont ensuite copiées dans `contract.json`.

Une modification du profil effectuée par l'agent pendant le travail n'élargit donc jamais ses permissions.

Aucune découverte « intelligente » des commandes de validation n'est requise en V1.

# 8. Git : clone jetable plutôt que worktree

Un worktree partage les références et le répertoire Git avec le dépôt principal.

Pour un agent disposant d'un shell, cette séparation est insuffisante.

V1 utilise donc par défaut un **clone local indépendant**, construit à partir du dépôt source.

Objectifs :

```
aucun objet Git partagé en écriture
aucun remote utilisable
aucune référence du dépôt source modifiable
```

Le clone est créé sans hardlinks ni alternates.

Puis :

```
git remote
```

doit être vide.

Le Runner vérifie également l'absence de `objects/info/alternates`.

La branche de travail n'existe que dans le clone du Runner :

```
runner/<run-id>
```

Le dépôt d'origine n'est jamais modifié par une exécution autonome.

# 9. Propriété des commits

L'agent modifie les fichiers.

**Le Runner crée les commits.**

C'est une séparation volontaire :

```
agent
  → travaille

Runner
  → vérifie le périmètre
  → lance les validations
  → crée le commit
```

Avant et après chaque appel d'agent, le Runner vérifie :

```
HEAD
refs
remotes
configuration Git sensible
```

Si l'agent a lui-même déplacé `HEAD` ou créé un remote :

```
POLICY_VIOLATION
→ NEEDS_HUMAN
```

Le clone étant jetable, l'incident ne touche pas le dépôt réel.

Les commits Runner peuvent porter des trailers :

```
DialogForge-Run: <run-id>
DialogForge-Step: <n>
```

Ils rendent une reprise après interruption non ambiguë.

# 10. Planning With Files

PWF est la mémoire durable de l'agent.

Il contient notamment :

```
task_plan.md
findings.md
progress.md
```

Cependant, contrairement à `planlink.py` du moteur documentaire, le Runner **possède son propre plan de développement** et peut donc le faire évoluer.

Le premier appel de l'agent est un appel de bootstrap :

```
export accepté
       ↓
lecture du dépôt
       ↓
création du plan PWF
       ↓
aucune modification de code
```

Le bootstrap traduit les étapes déjà définies par la conception en unités de travail.

Il ne redécide pas l'architecture.

Après bootstrap, chaque appel traite **une seule prochaine étape PWF**.

Le Runner injecte lui-même dans le prompt :

```
objectif provenant de dev-export
contrat d'exécution
Next Step PWF
findings utiles
état Git
résultat des validations précédentes si nécessaire
```

Ainsi, **les hooks PWF propres à une CLI ne sont pas nécessaires au fonctionnement du Runner**.

Ils peuvent rester utiles en développement interactif, mais la sémantique du Runner ne dépend pas d'eux.

Cette décision rend PWF utilisable avec plusieurs agents.

# 11. Sessions de l'agent

V1 n'exige pas de session LLM persistante.

Chaque étape peut utiliser une **session fraîche**.

La mémoire persistante utile est :

```
conception
+ PWF
+ Git
+ validations
```

et non le contexte caché d'une session fournisseur.

Avantages :

- reprise plus simple ;
- moins d'état fournisseur à conserver ;
- changement d'agent possible plus tard ;
- disparition des ambiguïtés liées à une session perdue ;
- meilleure observabilité.

Une session persistante pourra être étudiée ensuite comme optimisation de coût ou de vitesse, jamais comme prérequis de V1.

# 12. Contrat de sortie de l'agent

Chaque appel se termine par un bloc structuré minimal, séparé du contenu libre.

Exemple :

```
DIALOGFORGE:STEP_RESULT
{
  "schema_version": 1,
  "status": "DONE",
  "summary": "Implémentation du modèle et de ses tests terminée."
}
```

Valeurs admises :

```
DONE
COMPLETE
NEEDS_HUMAN
BLOCKED
```

`DONE` :

> l'étape courante est terminée et le travail peut continuer.

`COMPLETE` :

> selon l'agent, toute la conception est implémentée.

`NEEDS_HUMAN` :

> une décision ou une clarification est nécessaire.

`BLOCKED` :

> une condition technique empêche de poursuivre.

La liste des fichiers modifiés n'est pas demandée au modèle : **Git la fournit**.

La réussite des tests n'est pas demandée au modèle : **le Runner les exécute**.

# 13. Boucle d'exécution

Après bootstrap :

```
                READY
                  │
                  ▼
        lire PWF + contrat
                  │
                  ▼
            appeler agent
                  │
                  ▼
       interpréter STEP_RESULT
                  │
                  ▼
           contrôler Git
                  │
                  ▼
     contrôler le périmètre
                  │
                  ▼
       validations de l'étape
                  │
          ┌───────┴────────┐
          │                │
        vert             rouge
          │                │
          ▼                ▼
       commit          réparation
          │                │
          ▼                └─────┐
     étape suivante              │
                                 │
                         max N tentatives
                                 │
                                 ▼
                           NEEDS_HUMAN
```

Aucune revue A/B intermédiaire n'est lancée.

Les contrôles intermédiaires sont essentiellement déterministes.

# 14. Réparation d'une validation

Une validation échouée ne provoque pas immédiatement un arrêt humain.

Le Runner conserve :

```
commande
code retour
stdout
stderr
commit ou état de travail concerné
```

Puis ouvre une étape de réparation :

```
validation rouge
       ↓
nouvel appel de l'agent
       ↓
logs exacts fournis
       ↓
correction
       ↓
validation relancée
```

La boucle est bornée :

```
max_validation_repairs
```

Par défaut proposé :

```
3
```

Au-delà :

```
NEEDS_HUMAN
```

Aucune boucle infinie de « essaie encore ».

# 15. Validations officielles

Les validations comptant comme preuves pour le futur `dev-package` sont exécutées **par le Runner**, pas simplement par le modèle.

Chaque validation produit directement le format déjà attendu par `development.py` :

```
{
  "schema_version": 1,
  "validation_id": "tests",
  "head_oid": "...",
  "command": ["python", "-m", "pytest"],
  "started_at": "...",
  "completed_at": "...",
  "exit_code": 0,
  "outcome": "PASSED",
  "environment": "...",
  "summary": "...",
  "artifacts": []
}
```

On réutilise donc le contrat déjà existant.

Deux catégories :

```
step
final
```

Les validations `step`, lorsqu'elles existent, tournent avant chaque commit.

Les validations `final` tournent sur le candidat complet.

Une validation officielle ne doit pas modifier des fichiers suivis. Si elle le fait :

```
VALIDATION_MUTATED_WORKSPACE
```

et le Runner s'arrête.

Les fichiers temporaires ignorés par Git ne sont pas considérés comme une modification du candidat.

# 16. Fin d'un développement

Quand l'agent retourne `COMPLETE` :

```
contrôle de périmètre
        ↓
validations finales
        ↓
commit final si nécessaire
        ↓
base_oid
head_oid
        ↓
dev-package
        ↓
paquet immuable
```

Le Runner peut appeler directement l'API correspondant à `dev-package`, ou la commande publique.

Le paquet reste exactement celui déjà défini par DialogForge.

Le Runner ne crée **aucun second format de revue de code**.

À la fin :

```
run/handoff/
└── package/
```

et `state.json` porte notamment :

```
base_oid
head_oid
package_id
status = COMPLETED
```

# 17. Revue

V1 ne lance pas automatiquement une revue LLM après chaque tâche.

La séquence normale est :

```
conception
     ↓
20 petites opérations éventuelles
     ↓
tests et commits
     ↓
candidat complet
     ↓
dev-package
     ↓
revue A/B du lot
```

C'est précisément l'intérêt d'avoir correctement préparé la conception.

Une revue anticipée peut être décidée par l'humain si un problème particulier le justifie, mais elle ne fait pas partie de la boucle automatique.

# 18. Sécurité du mode sans surveillance

C'est le point de sortie essentiel avant tout essai réel.

Un clone Git isolé protège le dépôt source contre une erreur Git.

Il ne protège **pas à lui seul** le reste de la machine contre un agent disposant d'un shell.

Par conséquent :

> **Le mode sans surveillance est refusé tant qu'un profil d'exécution writable n'a pas été qualifié sur la machine concernée.**

La qualification d'un adaptateur writable doit démontrer au minimum :

```
écriture autorisée dans sandbox/workspace
écriture refusée dans un témoin hors sandbox
écriture refusée dans le dépôt source
absence de remote utilisable
absence de credentials Git transmis
politique réseau effectivement fermée
timeout et terminaison de l'arbre fonctionnels
reprise possible après interruption
```

Une version différente de la CLI invalide cette qualification jusqu'à un nouvel essai.

La philosophie est la même que celle déjà utilisée dans `docs/LIMITES.md` :

> ce qui est demandé à une CLI n'est pas automatiquement présenté comme garanti.

# 19. Environnement transmis à l'agent

Le Runner réutilise le principe `EnvPolicy`.

Il retire notamment :

```
variables de l'autre fournisseur
sessions de l'hôte
PLAN_ID/PWF_* de l'hôte
GITHUB_TOKEN
GH_TOKEN
SSH_AUTH_SOCK
credentials et variables de déploiement connues du projet
```

L'agent doit conserver uniquement ce dont sa propre CLI a besoin pour fonctionner.

Le Runner ne transmet aucune clé applicative de FloraPi.

Une application ayant besoin de secrets pour ses tests doit utiliser des secrets de test explicitement prévus pour le sandbox, jamais ceux de production.

# 20. Réseau et dépendances

V1 fonctionne avec :

```
network = false
```

Le développement autonome suppose donc que l'environnement nécessaire aux tests existe déjà.

Le Runner n'exécute pas automatiquement :

```
pip install
npm install
apt
docker pull
mise à jour d'outils
```

Une dépendance nouvelle exigée par la conception mais absente conduit à :

```
NEEDS_HUMAN
```

L'accès réseau et l'installation de dépendances constituent des extensions futures distinctes.

# 21. Matériel et services réels

Pour FloraPi en particulier, V1 ne donne aucun accès autonome :

```
GPIO
Pico réels
relais
pompes
électrovannes
services de production
base de production
réseau d'exploitation
```

Les tests correspondants doivent utiliser :

```
fake
simulation
fixtures
interfaces mockées
```

Une conception nécessitant une validation matérielle peut être développée automatiquement, mais :

```
validation matérielle = NOT_RUN
→ décision humaine
```

# 22. État persistant

`state.json` reste petit et lisible.

Exemple conceptuel :

```
{
  "schema_version": 1,
  "run_id": "...",
  "contract_sha256": "...",

  "status": "READY",
  "phase": "IMPLEMENT",

  "step": 4,
  "repair_attempt": 0,

  "base_oid": "...",
  "head_oid": "...",
  "last_good_head_oid": "...",

  "current_call": null,
  "package_id": null
}
```

Statuts V1 :

```
READY
CALLING
CHECKING
NEEDS_HUMAN
COMPLETED
STOPPED
ERROR
```

Phases :

```
BOOTSTRAP
IMPLEMENT
REPAIR
FINALIZE
```

Ne pas multiplier les sous-états tant qu'un défaut réel ne le nécessite pas.

# 23. Appels et reprise

Chaque appel conserve, sur le modèle de `transport.py` :

```
calls/0007/
├── intention.json
├── prompt.txt
├── stdout.txt
├── stderr.txt
├── pid.txt
├── resultat.json
└── incident.json éventuel
```

`resultat.json` n'existe que si les flux sont complets, comme aujourd'hui.

Reprise :

### `READY`

continuer normalement.

### `CALLING` + `resultat.json`

la réponse a été payée et reçue : l'interpréter localement, sans nouvel appel.

### `CALLING` sans résultat complet

l'espace de travail peut avoir été partiellement modifié.

Le Runner ne relance donc **jamais automatiquement** le même appel.

Il passe en :

```
NEEDS_HUMAN / INTERRUPTED_DIRTY
```

Cette prudence est nécessaire parce qu'un agent de développement produit des effets sur le système de fichiers pendant son appel.

# 24. Périmètre et changements dangereux

Avant validation, le Runner examine le diff.

Il refuse notamment en V1 :

```
fichier hors allowed_paths
fichier dans denied_paths
plus de max_changed_files
modification de .gitmodules
création/modification de sous-module
création de symlink ou junction
modification d'une dépendance si dependency_changes=false
remote Git créé
HEAD déplacé par l'agent
```

Les changements d'architecture ne peuvent pas tous être détectés mécaniquement.

Le contrat de l'agent lui impose donc également :

> Si la réalisation nécessite de remettre en cause la conception acceptée, retourner `NEEDS_HUMAN` et expliquer pourquoi.

Ce mécanisme n'est pas présenté comme une garantie : la revue finale reste là pour détecter une mauvaise interprétation éventuelle.

# 25. CLI V1

Surface minimale proposée :

```
dialogforge-run prepare
dialogforge-run run
dialogforge-run resume
dialogforge-run status
```

### Préparer

```
dialogforge-run prepare \
  --export <dev-export> \
  --repo <repo> \
  --base <revision> \
  --agent <id> \
  [--profile <runner.toml>] \
  --output <run>
```

Produit :

```
contrat
clone isolé
PWF vide/prêt au bootstrap
état READY
```

Aucun agent n'est appelé.

### Lancer

```
dialogforge-run run <run> --unattended
```

`--unattended` constitue l'autorisation explicite de poursuivre les différentes étapes sans confirmation intermédiaire.

Il est refusé si le profil writable de l'adaptateur n'est pas qualifié.

### Reprendre

```
dialogforge-run resume <run>
```

Une clarification humaine peut éventuellement être ajoutée :

```
--instruction <fichier>
```

Cette instruction peut préciser le travail dans le contrat existant.

Elle ne peut pas élargir le contrat ; dans ce cas un nouveau run doit être préparé.

### État

```
dialogforge-run status <run>
```

Lecture seule.

# 26. Aucun daemon

Une exécution sans surveillance ne signifie pas un service.

```
terminal
  └── dialogforge-run run ...
          └── boucle séquentielle
```

Le processus reste simplement actif.

Pas de :

```
Celery
scheduler
queue
service Windows
daemon
bail
heartbeat distribué
```

Si le processus s'arrête, `resume` reprend à partir des fichiers persistants.

# 27. Adaptateurs du Runner

Ne pas étendre `AgentAdapter`.

Créer un protocole séparé :

```
ExecutionAdapter
```

Il doit notamment décrire des capacités différentes :

```
supports_workspace_write
confines_writes
controls_network
supports_model_override
fresh_session
```

Le noyau ne nomme toujours pas les fournisseurs.

La V1 n'a besoin que **d'un adaptateur réel qualifié**.

Le deuxième fournisseur n'est pas un critère de sortie.

Cela évite de doubler immédiatement le travail de caractérisation.

# 28. Réutilisation du code existant

À réutiliser en priorité :

### `transport.py`

Très adapté :

```
timeout
stdout/stderr bornés
PID
terminaison de l'arbre
preuve de flux complets
interruption
```

### `storage.py`

Écritures atomiques.

### `lock.py`

Exclusion d'une deuxième exécution sur le même run.

### politiques d'environnement

Le principe de séparation des secrets est directement réutilisable.

### `development.py`

Les contrats :

```
dev-export
validation JSON
dev-package
```

doivent rester les mêmes.

Une petite fonction publique de lecture/validation de l'export peut être ajoutée si nécessaire au lieu de recopier `_export()` dans le Runner.

# 29. Ce qu'il ne faut surtout pas réutiliser

Ne pas importer le workflow documentaire dans le Runner :

```
workflow.py
objections
decisions
cycle A/B
états documentaires
```

Ne pas créer un « B du développeur ».

Ne pas réintroduire les mécanismes anciens :

```
budget
lease
réservation
stratégie adaptative
automédication du moteur
orchestrateur distribué
```

# 30. Critères d'acceptation de V1

V1 est livrable lorsque les points suivants sont démontrés.

### Contrat

1. Un export modifié est refusé.
2. Un contrat modifié après préparation est refusé.
3. Une clé de contrat inconnue est refusée.
4. PWF ne peut pas élargir le contrat.

### Git

1. Le dépôt source reste octet/logiquement inchangé.
2. Le clone autonome ne possède aucun remote.
3. Aucun alternate ni hardlink d'objets n'est utilisé.
4. L'agent ne peut pas créer un commit sans que le Runner le détecte.
5. Chaque commit accepté correspond à une étape passée par les contrôles.

### PWF

1. Un run arrêté puis repris retrouve sa prochaine étape.
2. Une nouvelle session d'agent peut continuer uniquement avec export + PWF + Git.
3. Le bootstrap ne modifie aucun fichier du projet.

### Validation

1. Les validations sont exécutées par le Runner.
2. Leur JSON respecte le contrat déjà utilisé par `dev-package`.
3. Une validation portant sur un autre `HEAD` est impossible.
4. Une validation qui modifie des fichiers suivis est refusée.
5. Une réparation est bornée.

### Sécurité

1. L'agent écrit dans le sandbox.
2. Une tentative d'écriture dans un témoin extérieur échoue lors de la qualification.
3. Le dépôt source est inaccessible en écriture lors de cette qualification.
4. Le réseau est effectivement fermé dans le profil unattended.
5. Aucun credential Git de l'hôte n'est transmis.

### Autonomie

1. Plusieurs tâches successives peuvent être réalisées sans intervention.
2. `NEEDS_HUMAN` provoque un arrêt propre.
3. Un timeout ne déclenche aucune relance aveugle.
4. Une réponse déjà reçue n'est pas repayée uniquement pour être interprétée.

### Handoff

1. Une exécution complète possède `base_oid` et `head_oid`.
2. Les validations finales portent sur ce `head_oid`.
3. `dev-package` accepte directement les preuves produites.
4. Le paquet résultant est utilisable par la revue A/B existante sans extension du workflow.

# 31. Garde de taille

L'histoire de DialogForge justifie une contrainte explicite.

Cible V1 :

```
≈ 1 000 à 1 200 lignes effectives
```

pour `src/dialogforge_runner/`.

Seuil de redécision :

```
1 500 lignes effectives
```

hors tests.

Dépasser ce seuil n'est pas interdit, mais impose de revenir à la question :

> Quelle complexité observée justifie ces lignes supplémentaires, et qu'est-ce qu'elles permettent de retirer ?

Une V1 approchant plusieurs milliers de lignes avant son premier essai réel est considérée comme un signal d'échec de conception.

# 32. Ordre d'implémentation proposé

### Lot R0 — Qualification avant code fonctionnel

Écrire le protocole permettant de qualifier un agent writable sur le poste réel.

Pas de FloraPi.

Le test porte sur un dépôt jetable contenant des témoins dedans et dehors.

### Lot R1 — Socle avec faux agent

Implémenter :

```
contracts
state
run directory
clone Git
PWF
boucle d'étapes
fake ExecutionAdapter
```

Aucun fournisseur réel.

### Lot R2 — Validations et commits

Ajouter :

```
contrôle du diff
validation
boucle de réparation
commits Runner
reprise
```

Tout avec fake agent et petits dépôts temporaires.

### Lot R3 — Handoff

Relier la fin du Runner à :

```
dev-package
```

et vérifier bout en bout :

```
conception fake acceptée
→ dev-export
→ Runner fake
→ validations
→ paquet
→ dev-verify
```

### Lot R4 — Premier agent réel

Qualifier **un seul** adaptateur writable.

L'essai doit être limité et réversible, idéalement sur une copie ou un micro-projet dédié.

### Lot R5 — Essai sur DialogForge V2

Choisir une modification réelle mais petite, déjà conçue.

Le dépôt principal n'est pas touché : le candidat reste dans le clone autonome.

Faire ensuite une revue normale du paquet.

### Lot R6 — Premier essai FloraPi

Seulement après réussite de R5.

Choisir un lot :

```
sans matériel réel
sans déploiement
sans secret
avec tests automatisés solides
```

L'objectif n'est pas de prouver que le Runner sait « tout faire ».

L'objectif est de montrer qu'une conception préparée peut être transformée en plusieurs commits corrects **sans intervention humaine entre les tâches**.

# 33. Critère réel de succès

La réussite du Runner V1 n'est pas :

> l'agent a travaillé longtemps tout seul.

Elle est :

> **une conception acceptée a été transformée en candidat Git validé et empaqueté, sans intervention humaine entre le lancement et soit la fin du lot, soit un arrêt justifié** `**NEEDS_HUMAN**`**, et sans effet sur le dépôt ou le système réels hors du sandbox.**

Un arrêt volontaire parce qu'une décision dépasse le contrat est donc un **succès de sécurité**, pas un échec du Runner.

# 34. Architecture finale V1

```
           RECHERCHE
               │
               ▼
          CONCEPTION
               │
         revue A / B
               │
       décision humaine
               │
               ▼
          dev-export
               │
               ▼
   ┌─────────────────────────┐
   │   EXECUTION CONTRACT    │
   │                         │
   │ scope                   │
   │ permissions             │
   │ validations             │
   │ limits                  │
   └────────────┬────────────┘
                │
                ▼
      DIALOGFORGE RUNNER
                │
      ┌─────────┼──────────┐
      │         │          │
      ▼         ▼          ▼
     PWF       Agent      Git
      │                    │
      │             clone isolé
      │                    │
      └──────────┬─────────┘
                 │
                 ▼
           validations
                 │
                 ▼
             commits
                 │
        étape suivante...
                 │
                 ▼
           candidat final
                 │
                 ▼
           dev-package
                 │
                 ▼
             revue A/B
                 │
                 ▼
          décision humaine
                 │
                 ▼
      intégration hors Runner
```

La frontière essentielle est celle-ci :

> **Le Runner reçoit une liberté d'action importante à l'intérieur d'un espace sans valeur propre. Il ne reçoit jamais le pouvoir de transformer seul ce résultat en modification du projet réel.**
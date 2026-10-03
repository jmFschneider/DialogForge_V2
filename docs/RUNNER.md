# Runner V1 — socle et profil Claude WSL2

Le Runner est séparé du cycle documentaire. La branche `feat/runner-v1` contient la préparation,
le lancement Claude sous Ubuntu WSL2, la collecte et le passage depuis la GUI. Le cycle complet
a été éprouvé avec un faux agent qui modifie et commit dans un dépôt jetable. Aucun appel
fournisseur n'est lancé par les tests. Un candidat produit manuellement dans le clone peut aussi
être collecté.

## Depuis la GUI

Terminer une collaboration de type **Conception** et accepter sa version actuelle, avec ou sans
réserves. Dans le suivi, cliquer sur **Développer avec le Runner**. L'écran demande le dépôt Git
source, le commit de départ (`HEAD` par défaut), un dossier d'export Windows, un dossier Runner
dans Ubuntu (par défaut `~/dialogforge-runs/<nom>`), les délais et au moins une validation finale.
Chaque validation est une liste JSON d'arguments, par exemple :

```json
[["python3", "-m", "pytest", "tests"]]
```

Le dépôt source et l'export peuvent être sur Windows ; le pont les convertit en chemins WSL.
Le dossier Runner doit être sur le système de fichiers Linux, hors de `/mnt`. Ubuntu WSL2 doit
disposer de Python 3, Git, Claude Code et `srt` tels que qualifiés pour le profil `claude-wsl`.
Le jeton Claude est saisi dans un champ masqué pour **Exporter et lancer**, transmis au pont par
son entrée standard et effacé du formulaire après lancement. La GUI exporte d'abord la conception
acceptée, puis prépare le clone et appelle Claude. Un échec garde le dossier Runner et ses traces.
Après inspection du clone, **Continuer l'agent** lance un nouvel appel explicite ; **Collecter sans
appel** valide un candidat déjà committé sans jeton. Le paquet affiché reste à relire et à intégrer
séparément. La fermeture de la fenêtre pendant l'exécution propose pause ou interruption et attend
la fin du processus avant de fermer.

## Depuis la CLI

Préparer un fichier `checks.json` contenant les commandes finales, sous forme de listes
d'arguments (sans shell implicite) :

```json
[["python", "-m", "pytest", "tests"]]
```

Puis, dans un environnement Python où le paquet est installé :

```text
dialogforge-run prepare --export EXPORT --repo REPO --base COMMIT --checks checks.json --output RUN
dialogforge-run collect RUN
```

`prepare` copie l'export, crée un clone indépendant sans remote et le place sur le commit demandé.
Il ne reprend pas les changements non committés du dépôt source et n'installe rien. `collect`
exige un candidat committé et un espace de travail propre, exécute les validations finales,
revérifie le même `HEAD`, puis produit un paquet dans `RUN/results/collect-NNNN/package`.
Chaque tentative garde ses résultats ; un échec ne rappelle aucun agent.

Le profil par défaut `local` conserve les validations avec les droits du processus Runner ;
il convient uniquement aux essais maîtrisés. Le profil `claude-wsl` exige que la commande
Runner s'exécute **dans Ubuntu** et que `RUN` se trouve sur le système de fichiers Linux,
hors de `/mnt`. Le clone, le mandat, les appels et les résultats restent dans ce dossier.

```text
dialogforge-run prepare --profile claude-wsl --export EXPORT --repo REPO --base COMMIT --checks checks.json --output /home/USER/RUN
dialogforge-run run-claude /home/USER/RUN --timeout 3600
```

Dans le shell Ubuntu, fournir ponctuellement `CLAUDE_CODE_OAUTH_TOKEN` par saisie masquée avant
`run-claude` ; ne pas le mettre dans une commande, un fichier du projet ou `checks.json`.
Claude est lancé avec le profil strict qualifié (`--restricted`, sandbox obligatoire, Bash
autorisé, refus des commandes sans sandbox). Le mandat arrive par l'entrée standard et reste
hors de l'espace d'écriture de l'agent. Les validations passent par `srt` avec l'écriture limitée
au clone, la lecture du dossier personnel fermée sauf pour le clone, et le réseau refusé. Leur
environnement de test doit donc se trouver dans le clone ou dans les outils système accessibles.
Le jeton de l'agent n'est pas transmis aux validations. Chaque tentative garde ses
traces. Après un appel échoué ou interrompu, examiner les traces et le clone, puis utiliser
`run-claude RUN --timeout 3600 --continue` seulement pour une continuation voulue.

`python3 /mnt/c/Projets/DialogForge_2/tools/qualify_runner_wsl.py` exerce sous Ubuntu le passage
complet avec un faux agent : commit dans le clone, validation sous `srt`, paquet pour le même
`HEAD` et refus de lecture d'un témoin extérieur. `--claude` remplace le faux agent par un appel
réel sur le même dépôt jetable et demande le jeton par saisie masquée. Le 2026-10-02, cet essai
a créé un commit local et un paquet pour le même `HEAD`, avec validation finale réussie sous
`srt` et témoin source inchangé. Un second appel Claude a confirmé dans le résultat du vrai
outil Bash que le jeton était absent de son environnement et qu'une connexion TCP locale
était refusée. Ces observations portent sur les témoins de qualification, pas sur toutes les
voies de sortie possibles. Le code de sortie 0 de Claude ne prouve pas à lui seul que les
outils demandés ont été exécutés ; vérifier les traces et le candidat.

`python3 /mnt/c/Projets/DialogForge_2/tools/qualify_runner_boundaries_wsl.py` vérifie sans
fournisseur, sous `srt`, qu'un faux jeton d'environnement est retiré, qu'un secret hors clone
est caché et qu'une connexion à un serveur TCP local est refusée. Ces contrôles portent sur
`srt` directement. `python3 /mnt/c/Projets/DialogForge_2/tools/qualify_claude_boundaries_wsl.py`
mesure la même chose depuis un vrai outil Bash de Claude : un seul appel, jeton saisi masqué,
appel d'outil repéré dans la trace. Le 2026-10-02, il a rendu `TOKEN_DENIED` et
`NETWORK_DENIED`. La trace est dans `/home/schneider/dialogforge-claude-boundaries.cxhordoe/`.
La [qualification initiale](../reference/RUNNER_QUALIFICATION_2026-10-01.md) a montré que
Claude sur Windows, avec `--restricted` et Bash autorisé, pouvait modifier un témoin extérieur.
Sous Ubuntu WSL2, le profil Claude avec sandbox strict a permis l'écriture dans son dossier
de travail et refusé les écritures vers un dossier frère et le volume Windows. Un programme
Windows copié dans le dossier de travail a échoué avec `UtilConnectUnix:524: socket failed 1` ;
le même programme fonctionne hors sandbox. Une validation exécutée séparément sous
`@anthropic-ai/sandbox-runtime` a reproduit la frontière d'écriture. Codex a également refusé
l'écriture extérieure sur Windows avec `workspace-write` pour l'agent et la validation.
Le profil Claude est désormais raccordé et qualifié de bout en bout sur ce lot minimal.

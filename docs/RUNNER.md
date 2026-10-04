# Runner V1 — socle et profil Claude WSL2

Le Runner est séparé du cycle documentaire. La branche `feat/runner-v1` contient la préparation,
le lancement Claude sous Ubuntu WSL2, la collecte et le passage depuis la GUI. Le cycle complet
a été éprouvé avec un faux agent qui modifie et commit dans un dépôt jetable. Aucun appel
fournisseur n'est lancé par les tests. Un candidat produit manuellement dans le clone peut aussi
être collecté.

## Depuis la GUI

Terminer une collaboration de type **Conception** et accepter sa version actuelle, avec ou sans
réserves. Dans le suivi, cliquer sur **Développer avec le Runner**. L'écran propose deux voies :

- **Nouveau projet** (par défaut) : le dossier du projet est `code/` dans la mission (à côté de la
  conception si elle est indépendante). Rien n'est à créer à la main : le Runner y initialise Git
  et y crée un commit initial **vide** avec l'identité Git déjà configurée sur ce poste. Si le
  dossier contient déjà des fichiers ou un historique, ou si aucune identité n'est configurée
  (`user.name`, `user.email`), le lancement s'arrête avant toute écriture et dit quoi faire ; il
  n'invente jamais d'identité et ne touche jamais à la configuration Git globale.
- **Dépôt existant** : on choisit le dépôt et le commit de départ (`HEAD` par défaut). Seuls les
  fichiers **committés** entrent dans le clone ; les changements de l'utilisateur ne sont ni
  nettoyés ni committés.

Dans les deux cas l'agent travaille dans un clone isolé sous Ubuntu (par défaut
`~/dialogforge-runs/<mission>-NNN`), jamais dans le dossier du projet. Le clone ne voit pas
l'identité Windows : elle est reportée dans la configuration **locale** du clone, seulement si
Ubuntu n'en a aucune, pour que l'agent puisse committer.

Les **validations finales** sont une liste éditable : une ligne par commande, avec l'exécutable et
ses arguments (guillemets permis), par exemple `node` et `--test`, ou `python3` et
`-m pytest tests`. Elles se lancent à la racine du dépôt, **sans shell** : le contrat interne reste
une liste d'arguments. Le texte de la conception acceptée est affiché sous la liste pour y relever
les commandes ; aucune commande n'est jamais reprise du document sans être saisie par l'utilisateur.

Le dossier Runner doit être sur le système de fichiers Linux, hors de `/mnt`. Ubuntu WSL2 doit
disposer de Python 3, Git, Claude Code et `srt` tels que qualifiés pour le profil `claude-wsl`,
et de chaque outil de validation **hors du dossier personnel** (illisible sous `srt`). Ces
prérequis sont vérifiés avant tout appel : un manque laisse une préparation reprenable et un
message précis. La présence d'un outil ne prouve pas que les tests passeront ; les dépendances du
projet ne sont pas installées automatiquement.

Le jeton Claude est saisi dans un champ masqué, transmis au pont par son entrée standard seulement
(jamais en argument, jamais dans un fichier), uniquement pour les actions qui appellent l'agent, et
effacé du formulaire dès le lancement. **Préparer et lancer** enchaîne : prérequis, export de la
conception, dépôt initial (projet neuf), clone, puis premier appel. L'export est publié sous
`developpement/export-NNN` (jamais écrasé : un export identique à la version acceptée est repris,
une nouvelle acceptation en crée un nouveau). Un échec garde le dossier Runner et ses traces.
Depuis la GUI, un lancement peut faire **au plus trois appels agent dans la durée totale indiquée**, uniquement
si une validation finale échoue. Il réutilise le jeton saisi pour ce lancement et joint l'échec
au prompt de correction. Un paquet réussi arrête immédiatement les appels. Le jeton n'est pas
conservé après le lancement. Le bilan de l'agent et les validations sont affichés avec le paquet,
dont le commit se remet ensuite dans `code/` pour l'essayer. La fermeture de la fenêtre pendant
l'exécution propose pause ou interruption et attend la fin du processus avant de fermer.

### Reprise après fermeture ou incident

`developpement/executions/NNN.json` (dans la mission) garde les paramètres **non secrets** : voie
choisie, dépôt et base (OID), identité de la base initiale, export et son empreinte, distribution
WSL, chemin Linux du run, validations, délais, paquets produits. Il est écrit avant l'appel
fournisseur. Il ne copie pas l'état du run : à la réouverture, l'écran relit le dossier Linux
(`dialogforge-run inspect`) et ne propose que le départ qui convient. Les paramètres figés dans
le clone ne sont plus modifiables.

| Situation lue | Départ proposé |
|---|---|
| Export publié, clone absent | **Préparer et lancer** : l'export est repris ; un dépôt initial déjà créé n'est reconnu que s'il est intact (un seul commit vide, même identité), jamais recréé |
| Clone préparé, agent non lancé | **Lancer l'agent** sur cette préparation |
| Appel interrompu ou résultat incertain | **Continuer l'agent** (explicite) ou **Vérifier le candidat sans agent** |
| Validations échouées sans paquet antérieur | **Continuer l'agent** (explicite) ou **Vérifier le candidat sans agent** |
| Validations échouées après un paquet | **Demander une correction** précise ou **Vérifier le candidat sans agent** ; le paquet antérieur reste affiché |
| Paquet prêt | **Remettre dans code/** extrait son commit pour l'essayer, sans jeton ; une correction exige un défaut précis |

Aucune reprise après fermeture ne relance l'agent d'elle-même, ne recrée le dépôt initial ni ne
refait le clone. Après un paquet, « Continuer » ne répète plus le travail achevé : l'action
« Demander une correction » transmet l'objectif saisi à un nouvel appel explicite.
Si ce nouvel appel ne crée aucun commit, aucun paquet supplémentaire n'est produit.
### Remise dans `code/` et acceptation

**Remettre dans code/** conserve le dernier paquet valide sous `developpement/paquets/NNN` (trace
interne) et ses commits exacts dans un bundle Git sous `developpement/candidats/`, puis extrait ce
commit sur la branche `dialogforge/candidat-NNN` de l'espace d'essai : `code/` lui-même pour un
projet neuf, une copie d'essai `code/` distincte pour un dépôt existant (votre dépôt n'est pas
touché). La branche cible est celle sur laquelle se trouvait le dépôt à la première remise ; elle
est notée dans la référence d'exécution. Si l'espace d'essai contient des modifications, la remise
s'arrête et l'explique : rien n'est écrasé. Refaire la remise ne change rien.

L'écran indique alors « Prêt à essayer » avec le dossier, la branche et le commit, validés sous
Ubuntu : un essai Linux ne démontre pas un fonctionnement Windows. **Accepter cette version** porte
sur le commit essayé seulement (un commit ajouté à la main dans `code/` n'est pas accepté). La
branche cible avance en fast-forward depuis la base ou une version déjà acceptée ; une divergence
ou un dépôt cible modifié demande une intervention humaine. Le reçu se trouve dans
`developpement/integrations/`. Les versions précédentes restent sur leurs branches et dans leurs
bundles. Aucun jeton ni appel d'agent n'est requis pour la remise ou l'acceptation ; les revues
documentaires créées auparavant restent consultables comme collaborations ordinaires.

## Depuis la CLI

Préparer un fichier `checks.json` contenant les commandes finales, sous forme de listes
d'arguments (sans shell implicite) :

```json
[["python", "-m", "pytest", "tests"]]
```

Puis, dans un environnement Python où le paquet est installé :

```text
dialogforge-run init-project PROJET
dialogforge-run prepare --export EXPORT --repo REPO --base COMMIT --checks checks.json --output RUN
dialogforge-run inspect RUN
dialogforge-run collect RUN
```

`init-project` crée le dépôt d'un projet neuf (dossier absent ou vide) avec un commit initial vide
et rend son OID et son auteur ; il refuse un dossier occupé ou une identité Git absente avant
toute écriture. `inspect` lit l'état d'un dossier Runner sans rien écrire ni lancer.

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
`run-claude RUN --timeout 3600 --continue` seulement pour une continuation voulue. Si un paquet
existe déjà, fournir `--correction "objectif précis"` ; sans objectif, la commande refuse de
répéter l'appel.

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

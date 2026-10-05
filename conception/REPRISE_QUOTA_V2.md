# Reprise après épuisement du quota — conception V2

> Proposition courte pour remplacer le plan de la mission `Reprise_Quota_2`. Ce document ne vaut ni validation du plan précédent ni code.

## Objectif et limite

Lorsqu'une CLI interrompt une **session fournisseur** parce que la période d'usage de Claude ou Codex est épuisée et annonce une heure de retour fiable, DialogForge attend cette heure **plus deux minutes**, puis **continue cette même session par son identifiant**. Il ne renvoie pas le prompt initial dans une session neuve. Cela vaut pour le cadrage, les appels A/B de recherche et de conception, et le Runner de code, tant que DialogForge reste ouvert.

Ici, « crédits épuisés » désigne le quota temporaire qui se réinitialise. Un solde à acheter, une limite de débit, une erreur réseau ou d'authentification ne déclenche pas de reprise. Sans heure fiable, DialogForge montre l'erreur et s'arrête. Aucun délai de repli n'est inventé.

## Preuve disponible

- **Claude A/B en texte :** une trace réelle V2 donne le code `1`, `stdout` contenant seulement `You've hit your session limit · resets 8:50pm (Europe/Paris)` et `stderr` vide. Elle justifie la reconnaissance du refus, **pas encore la reprise de cette session** : l'appel actuel utilise `--no-session-persistence` et sa sortie ne fournit pas d'identifiant.
- **Codex :** un code non nul et un message sur `stderr` sont connus, ainsi qu'un exemple ancien de date anglaise avec ordinal. Le message complet de `codex exec` dans le profil V2 manque. Le code de sortie seul ne permet pas de reconnaître le quota.
- **Cadrage :** Claude `--resume` et Codex `exec resume` sont déjà employés après un tour réussi. Il faut conserver l'identifiant même si le tour interrompu échoue, notamment au premier tour.
- **Runner :** Claude y utilise aussi `--no-session-persistence`. Son raccordement demande la même correction que A/B. Les essais avec faux agents vérifient le mécanisme, sans transformer une simulation en preuve fournisseur.

Première action : chercher les refus déjà enregistrés dans les missions et les journaux locaux, sans provoquer un épuisement de quota. Pour chaque format trouvé, relever version, commande, code de sortie, `stdout`, `stderr`, champs d'erreur et présence de l'identifiant de session. Le raccordement ne s'active que si **refus, heure et session reprenable** sont établis ; il n'y a pas de matrice d'activation par système, mode et plateforme.

## Mécanisme minimal

1. **Reconnaître et retrouver la session.** Au point où un appel échoue déjà, l'adaptateur Claude ou Codex examine la sortie d'erreur de la CLI. Il rend « refus de période + heure annoncée + identifiant de la session interrompue », ou rien. Un code `1` ou `429` isolé ne suffit pas. Si une réponse finale a déjà été reçue, elle est traitée sans nouveau message ; si l'identifiant ou l'état du tour restent incertains, arrêt et conservation des traces.
2. **Interpréter et attendre.** Un petit module commun convertit l'heure annoncée en instant à partir de l'heure de réception. Il accepte les formes réellement observées : heure avec fuseau, date explicite, et horodatage si le fournisseur en émet un. Il sait traiter le passage de minuit et une heure qui vient de passer sans l'envoyer au lendemain. Si le fuseau, la date ou un changement d'heure restent ambigus, il arrête. L'attente se fait dans l'exécution en cours, est interrompable par pause/arrêt, et ne crée ni worker ni tâche planifiée.
3. **Continuer la session.** Après l'attente, DialogForge appelle la reprise non interactive **avec l'identifiant exact** et une courte consigne « Continue le travail interrompu et fournis le résultat attendu ». Il ne répète pas le prompt d'origine. Si une session réellement active accepte encore des messages, il lui adresse cette consigne par le canal déjà ouvert. Les appels actuels sont non interactifs : cette possibilité ne justifie pas de créer un gestionnaire de processus vivant. La suite doit confirmer le même identifiant ; une reprise qui ouvre une autre session est un échec, jamais un succès silencieux. Si le fournisseur refuse encore avec **la même heure ou une heure déjà passée**, DialogForge s'arrête ; une nouvelle heure fiable plus tardive autorise une nouvelle attente. Aucun compteur de reprises ou quota interne n'est ajouté.

Les appels A/B ordinaires restent séparés : chaque nouveau tour commence une session neuve ; **seule la continuation du tour interrompu** réutilise son identifiant. Aujourd'hui, `--no-session-persistence` (Claude A/B et Runner) et `--ephemeral` (Codex A/B) empêchent cette reprise. Ils devront être retirés pour les parcours concernés, avec extraction et conservation de l'identifiant dans les traces existantes. Pour Claude, `--session-id` peut fixer l'identifiant dès le départ ; pour Codex, `--json` permet de lire `thread.started`. Vérifier sur les versions installées les commandes `claude -p --resume <id>` et `codex exec resume <id>`, ainsi que la continuité réelle de l'ID. Un ID absent ou non reprenable mène à l'arrêt, **sans nouvel appel sur une session neuve**.

Les flux bruts et l'appel refusé restent sur disque, avec le coût indiqué comme **inconnu**. On ajoute aux traces existantes l'identifiant fournisseur, l'heure retenue et l'heure prévue de reprise ; pas de second dossier de journal parallèle.

## Raccordement des trois parcours

| Parcours | À la reprise |
| --- | --- |
| **Recherche et conception A/B** | Tracer une nouvelle invocation liée à l'appel refusé, mais la lancer avec **le même ID fournisseur** et une consigne de continuation. Refaire les contrôles de l'état et des sources. |
| **Cadrage** | Continuer le tour interrompu dans la session F existante, par son ID si le processus CLI s'est terminé. Ne pas compter le refus comme une réponse. |
| **Runner** | Continuer la session de A sur le même clone et les mêmes commits ; conserver le paquet éventuel. Le temps passé à attendre est exclu de sa durée de travail. |

La CLI et la GUI affichent le message brut, l'heure retenue et « reprise à HH:MM ». Elles utilisent les commandes de pause et d'arrêt déjà présentes. Un message annonce la continuation ou l'abandon de l'attente. Aucun nouvel écran ni bouton n'est requis si ces commandes sont déjà accessibles dans le parcours.

## Réalisation et vérification

1. **Qualifier refus et reprise.** Exploiter les traces disponibles. La trace Claude A/B qualifie le refus ; vérifier aussi que le profil persistant expose un ID et que la CLI reprend bien **la même** session. Ajouter Codex, le cadrage ou le Runner dès que leur format réel de refus et leur reprise sont établis ; aucun motif supposé n'active la continuation.
2. **Coder le noyau et A/B.** Mettre la reconnaissance propre à chaque outil dans `src/iabinome/adapters/`, l'heure et l'attente commune dans un petit module de `src/iabinome/`, puis raccorder `workflow.py` et l'incident existant. Prévoir la conservation de l'ID sans réutiliser la session d'un autre tour. Éviter un nouvel état durable si les traces actuelles suffisent.
3. **Raccorder le cadrage et le Runner.** Adapter `framing.py` et `dialogforge_runner/core.py` à « attendre puis continuer la session identifiée ». Ajouter seulement les messages nécessaires aux surfaces CLI/GUI existantes.

Vérifier avec de faux agents et une horloge contrôlée : refus suivi d'une réussite **avec le même ID fournisseur** dans chacun des trois parcours ; ID absent, perdu ou remplacé ; pause pendant l'attente ; heure ambiguë ; autre erreur avec le même code de sortie ; réponse normale parlant de quota ; nouveau refus avec la même heure ; conservation des traces et du travail. Une vérification complète sans quota réel clôt le lot. Un test doit prouver qu'aucun prompt initial n'est rejoué dans une session neuve.

## Point à inscrire dans les règles

L'amendement de `project/RULES.md` laisse ouverte la conduite sans heure exploitable. La présente conception propose de **conserver l'arrêt actuel**, avec l'erreur brute visible et sans continuation automatique. Préciser aussi que la règle « session fraîche » pour A/B s'applique à chaque nouveau tour ; la continuation d'un tour interrompu garde, elle, le même ID fournisseur. Corriger enfin toute mention selon laquelle un appel refusé serait certainement gratuit : son coût reste inconnu.

La reprise Codex ne peut pas être déclarée opérationnelle avant observation de son message réel dans le profil V2 **et** vérification de l'identifiant de session. Cette limite est factuelle ; elle ne justifie pas de construire dès maintenant des reconnaisseurs spéculatifs.

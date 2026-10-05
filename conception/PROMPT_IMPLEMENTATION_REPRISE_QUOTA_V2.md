# Mandat d'implémentation — reprise après quota

Tu implémentes dans `C:\Projets\DialogForge_2` la conception courte
`conception/REPRISE_QUOTA_V2.md`. Elle est le mandat pour ce travail. Le long livrable
de `Reprise_Quota_2` n'est pas à exécuter : ses neuf étapes et ses mécanismes
anticipés ne font pas partie de cette demande.

## Résultat attendu

Quand Claude ou Codex **interrompt une session parce que sa période d'usage est
épuisée** et annonce une heure de réinitialisation interprétable, DialogForge
affiche l'incident, attend dans le lancement en cours jusqu'à cette heure **plus
deux minutes**, puis **continue cette même session fournisseur avec son ID**.
Il adresse une courte consigne de continuation, sans renvoyer le prompt initial
dans une session neuve. Si la session est encore active et accepte des messages,
il lui demande de continuer par le canal existant, sans créer un gestionnaire
interactif pour les appels CLI qui se terminent déjà. Cela couvre les appels A/B
de recherche et de conception, le cadrage et le Runner de code. Pause et arrêt
interrompent l'attente. DialogForge n'a pas à reprendre après sa fermeture.

Si le message, l'heure ou le fuseau sont incertains, conserve l'arrêt actuel et
montre la raison. Un code de sortie `1`, `429`, une limite de débit, un solde à
acheter, un problème d'authentification ou de réseau ne déclenchent pas la
reprise à eux seuls. Le coût de l'appel refusé reste **inconnu**.

## Méthode

1. Lis la V2, les règles applicables et les points d'appel existants. Cherche
   d'abord les traces réelles de refus déjà disponibles, sans provoquer de quota.
   La trace Claude A/B documentée dans `conception/REPRISE_QUOTA.md` établit le
   message de refus, **mais pas l'ID reprenable**. Pour Codex et les autres
   formats, relève la version, le code, les flux, les champs d'erreur et l'ID
   de session quand une trace réelle existe. Vérifie sur les CLI installées la
   syntaxe de reprise et la continuité effective de l'ID. N'active pas une
   reconnaissance fondée seulement sur d'anciens tests ou un message public.
2. Mets la reconnaissance propre à chaque outil à la frontière de son adaptateur.
   Utilise **un seul petit mécanisme commun** pour interpréter l'heure et attendre
   de façon interrompable. Réemploie les commandes de pause et d'arrêt, états
   et traces présents. Les appels A/B et Runner utilisent aujourd'hui
   `--no-session-persistence` (Claude) ou `--ephemeral` (Codex A/B) : ces modes
   empêchent la reprise demandée. Adapte-les pour qu'un appel ordinaire démarre
   une session neuve **persistée**, puis conserve son ID dans les traces de cet
   appel. Pour Claude, examiner `--session-id` puis `--resume <id>` ; pour Codex
   non interactif, `--json` et `codex exec resume <id>`. Vérifie que la reprise
   rend le **même ID**, sans basculer silencieusement dans une nouvelle session.
   Ne crée ni worker, tâche planifiée, quota interne, table de qualification
   générale, ni second journal parallèle.
3. Raccorde la continuation au bon endroit : nouvelle invocation liée au refus
   pour A/B mais **même session fournisseur**, même tour et même session F pour
   le cadrage, même session A sur le clone existant pour le Runner. Envoie une
   consigne de continuation, pas la demande initiale. Avant cette invocation,
   refais les contrôles déjà imposés par le parcours. Si l'ID est absent,
   différent ou non reprenable, arrête sans tenter un appel neuf. Dans le Runner,
   l'attente ne consomme pas la durée de travail choisie. Une nouvelle erreur
   annonçant la même heure ou une heure déjà passée arrête la continuation ;
   une nouvelle heure fiable plus tardive permet d'attendre à nouveau.
4. Affiche dans les surfaces CLI/GUI existantes le message brut et l'heure de
   reprise prévue. Mets la documentation et `project/RULES.md` en cohérence
   avec « sans heure fiable : arrêt », « coût inconnu » et l'exception à la
   session fraîche A/B limitée à la continuation du tour interrompu.

## Vérification et livraison

Teste avec de faux agents et une horloge contrôlée : refus puis réussite **avec
le même ID fournisseur** dans chacun des trois parcours, ID absent ou remplacé,
pause pendant l'attente, heure ambiguë, erreur d'une autre nature avec le même
code de sortie, réponse normale parlant de quota et nouveau refus avec la même
heure. Prouve que le prompt initial n'est pas rejoué dans une session neuve.
Vérifie la conservation des traces, de la session de cadrage et du travail du
Runner. Aucun quota réel n'est à provoquer.

Livre le code et une note courte indiquant les formats **effectivement actifs**,
les formats encore sans trace réelle, les fichiers modifiés et les vérifications
effectuées. Si la trace Codex V2 ou un ID reprenable manque toujours, laisse sa reprise inactive,
signale précisément cette limite et termine les parties étayées. Justifie
tout nouvel état ou mécanisme permanent par un besoin observé ; retire ce qui
n'est pas nécessaire au résultat ci-dessus.

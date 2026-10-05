# Demande

## Objectif

Concevoir pour DialogForge V2 la reprise automatique d'une mission lorsqu'un agent
Claude ou Codex est refusé parce que sa période d'usage est épuisée. Si l'outil
annonce une heure de réinitialisation fiable, DialogForge attend jusqu'à cette
heure plus deux minutes, puis poursuit la mission sans intervention humaine.
La fonction couvre le cadrage, les cycles A/B de recherche et de conception, et
la mise en place du code par le Runner. DialogForge reste ouvert pendant l'attente.

## Situation de départ

Aujourd'hui, ces trois parcours s'arrêtent sur l'incident et demandent une reprise
explicite. Les sorties des outils et les appels sont déjà conservés. Le dépôt
DialogForge V2 choisi comme projet vivant contient l'enquête préalable
(`conception/REPRISE_QUOTA.md`), les règles et les composants concernés. Parcours
les fichiers utiles directement dans ce dépôt ; aucune liste de corpus ne limite
la lecture. Il faut distinguer dans la conception les faits mesurés, les anciens
tests simulés et ce qui manque encore comme preuve : le refus réel de `codex
exec` dans le profil V2 n'a pas été relevé. L'ancien DialogForge contient un
mécanisme partiel ; son repli de quinze minutes après une heure Codex non
comprise est un défaut connu.

## Livrable attendu

Un plan de réalisation assez précis pour être confié ensuite au Runner sur ce
dépôt. Il doit expliquer où reconnaître un refus de période, comment transformer
l'heure annoncée en instant fiable, comment attendre et reprendre dans chacun des
trois parcours, et comment montrer à l'utilisateur ce qui est attendu ou arrêté.
Il doit nommer les fichiers à modifier et les vérifications utiles, dans un ordre
de réalisation qui laisse le logiciel utilisable entre les étapes.

La conception doit traiter explicitement les décisions suivantes :

- Quels signaux issus de Claude et Codex justifient une reprise automatique,
  avec code de sortie, flux et champs structurés lorsqu'ils sont disponibles ?
  Comment qualifier les formats encore inconnus sans provoquer un quota ?
- Que faire quand le refus de période est confirmé mais que l'heure manque ou
  reste ambiguë ? Proposer une conduite explicite, sans reprendre le repli
  aveugle de quinze minutes du prédécesseur.
- Comment interpréter une heure seule, une date anglaise avec ordinal, un fuseau,
  un horodatage Unix, le passage de minuit et le changement d'heure ?
- Comment reprendre la bonne opération sans perdre une réponse déjà reçue ni
  supposer qu'un appel refusé était gratuit ? Le cadrage garde sa session ; A/B
  garde la traçabilité des appels ; le Runner garde clone, commits et paquet.
- Comment l'attente reste-t-elle interrompable, visible en CLI et en GUI, sans
  worker détaché, nouvelle dépendance, stockage de jeton ou seconde logique de
  décision dans Tkinter ? La durée du Runner exclut l'attente de quota confirmée.
- Comment empêcher une boucle de relances rapides si le fournisseur refuse de
  nouveau l'accès après l'heure annoncée ?

La conception doit confronter sa proposition aux règles existantes, notamment
les amendements datés dans `project/RULES.md`, et signaler toute règle ou limite
GUI qu'il faudrait encore modifier avant le code.

## Limites

Ne pas concevoir de reprise après fermeture de DialogForge. Ne pas confondre
épuisement d'une période avec débit temporaire, crédit ou dépense bloquée,
authentification refusée, erreur réseau ou réponse de l'agent parlant de quotas.
Le code de sortie `1` et HTTP `429` ne constituent pas chacun une preuve
suffisante. Aucun appel fournisseur payant n'est requis pour produire ce plan.

## Critères de fin

Le plan permet de suivre, pour chaque parcours, l'incident initial, l'heure
retenue, l'attente, l'arrêt éventuel, la tentative de reprise et le résultat.
Il sépare clairement ce qui peut être implémenté avec les preuves disponibles de
ce qui attend une trace réelle Codex. Il prévoit des essais avec faux agents et
horloge contrôlée, ainsi qu'une validation du parcours complet sans quota réel.
Le livrable est une conception : aucun code n'est demandé à cette étape.

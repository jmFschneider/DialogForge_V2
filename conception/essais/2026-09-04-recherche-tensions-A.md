
# Tensions internes des règles fondatrices d’IAbinome

## Conclusion

Le corpus établit trois tensions opérationnelles :

1. **La revue croisée systématique contre son coût marginal** : la revue « palier par palier » a déjà cédé pour l’implémentation.
2. **La limitation des contrôles contre l’obligation de rendre chaque contrôle récupérable** : une porte d’état nécessite un mécanisme supplémentaire pour ne pas devenir un cul-de-sac.
3. **Les lectures obligatoires contre l’interdiction des relectures redondantes** : lorsque l’information est déjà dans le contexte, les deux consignes ne peuvent pas être appliquées littéralement ensemble.

La réponse la mieux étayée à « laquelle cède en premier ? » est donc : **la revue croisée palier par palier**, parce que le corpus documente sa suspension dès le 2026-09-03. C’est un fait historique, non une prédiction.

En revanche, le corpus ne permet pas de déterminer quelle règle céderait ensuite sous l’effet d’une croissance future. Il ne donne ni taille actuelle de l’outil, ni seuils d’arbitrage entre simplicité, preuve et robustesse, ni définition stable de ce qui compte dans les quelque 1 500 lignes.

## Corpus et niveau d’accès

Les trois sources primaires ont été lues intégralement sur le disque :

- [POURQUOI.md](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/POURQUOI.md:1>) — accès local intégral vérifié ;
- [CLAUDE.md](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/CLAUDE.md:1>) — accès local intégral vérifié ;
- [RULES.md](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:1>) — accès local intégral vérifié.

Leurs tailles et empreintes SHA-256 calculées correspondent aux trois entrées du [manifeste](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/manifeste.json:5>). Le manifeste atteste l’instantané ; ce n’est pas une preuve indépendante du contenu. Aucune source externe ou secondaire n’a été utilisée.

## 1. Revue croisée systématique contre coût marginal

### Les deux règles

> « **Claude produit, Codex relit palier par palier — et réciproquement.** »  
> — [RULES.md, ligne 33](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:33>)

> « **Suspendue en étape 2 le 2026-09-03, décision du PO** : la conception a déjà été contredite cinq tours, et sa précision rend la relecture de code palier par palier peu rentable. »  
> — [RULES.md, ligne 35](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:35>)

### Cas concret

À l’étape d’implémentation, continuer la revue croisée respecte la règle de détection des angles morts, mais consomme une ressource jugée peu rentable après cinq tours de contradiction de la conception. La suspendre respecte l’arbitrage d’efficacité, mais affaiblit la revue systématique.

Le risque n’est pas abstrait : le registre indique que deux défauts de paliers précédents n’ont été découverts qu’avec de vrais sous-processus et qu’« aucune relecture du code seul ne les avait montrés » ([RULES.md, lignes 137–141](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:137>)). Cela démontre les limites de la revue, mais non son inutilité générale.

### Statut de preuve

- **Fait** : la règle a été suspendue pour l’implémentation.
- **Fait** : elle reste applicable à la conception et possède une condition de réouverture.
- **Non prouvé** : que cette suspension ait elle-même causé un défaut.
- **Inférence bornée** : sous pression de coût, la revue systématique est la règle que le projet a déjà accepté d’affaiblir.

## 2. Limiter les contrôles contre rendre un contrôle récupérable

### Les deux règles

> « **Chaque contrôle ajouté a un coût qui ne se voit qu’au refactoring.** »  
> « La bonne question n’est jamais “est-ce que ce contrôle est utile ?” — c’est “**qu’est-ce que je retire en échange ?**” »  
> — [POURQUOI.md, lignes 37–38](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/POURQUOI.md:37>)

> « **Une porte qui refuse un statut doit s’accompagner de la commande qui en sort — sinon le statut devient un cul-de-sac.** »  
> — [RULES.md, ligne 122](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:122>)

### Cas concret

La porte d’état du lot 2 refuse le statut `ERROR`. Sans la table N-01 d’incidents relançables, aucune commande ne permet d’en sortir. Le contrôle protecteur produit donc lui-même un besoin de mécanisme supplémentaire ([RULES.md, lignes 122–123](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:122>)).

Deux applications correctes entrent alors en tension :

- ne pas ajouter le mécanisme de sortie limite l’échafaudage, mais transforme `ERROR` en blocage ;
- l’ajouter maintient l’utilisabilité de la porte, mais étend précisément l’appareil de contrôle que la règle fondatrice cherche à contenir.

C’est la miniature du mécanisme fondateur : chaque contrôle peut être justifié isolément, puis appeler d’autres contrôles. Le précédent avait accumulé budgets, baux, réservations, remèdes, attestations et archives sans confrontation au total ([POURQUOI.md, lignes 9–20](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/POURQUOI.md:9>)).

### Statut de preuve

- **Fait** : un contrôle concret a nécessité une voie de sortie supplémentaire.
- **Fait négatif documenté** : sans N-01, aucune commande ne sortait d’`ERROR`.
- **Inconnu** : ce qui a été retiré « en échange » ; le corpus n’en mentionne rien.
- **Non prouvé** : que cette extension ait déjà produit une dérive globale de taille.
- **Inférence bornée** : cette tension est le mécanisme le plus susceptible de croître cumulativement.

## 3. Lectures obligatoires contre absence de relecture redondante

### Les deux règles

> « Lire **`project/NOTES.md`** » ;  
> « Lire **`POURQUOI.md`** » ;  
> « Consulter **`project/RULES.md`** »  
> — obligations de début de session, [CLAUDE.md, lignes 6–12](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/CLAUDE.md:6>)

> « **Ne pas lire un fichier** si l’information est déjà dans `NOTES.md`, `RULES.md` ou le contexte courant. »  
> — [CLAUDE.md, ligne 13](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/CLAUDE.md:13>)

### Cas concret

Si le contexte courant contient déjà les règles fondatrices, relire `POURQUOI.md` satisfait l’obligation explicite, mais enfreint l’interdiction de lecture redondante. Ne pas le relire satisfait l’économie de contexte, mais affaiblit une consigne qualifiée d’« OBLIGATOIRE » et de « non négociable ».

La tension augmente avec la taille des documents : davantage d’information déjà présente rend la relecture plus coûteuse, tandis que l’augmentation du nombre de règles rend l’assurance de n’avoir rien omis plus difficile.

### Statut de preuve

- **Fait textuel** : les deux prescriptions coexistent.
- **Absent** : aucune priorité explicite entre elles.
- **Absent** : aucun cas consigné où cette ambiguïté a causé une erreur.
- **Inférence** : la règle conditionnelle de non-relecture pourrait être comprise comme une exception aux lectures obligatoires, mais le corpus ne le dit pas.

## Ce qui ressemble à une tension, mais n’en est pas une selon le corpus

### Prompts légers et format complet

> « **Alléger les prompts, ne pas les durcir.** »  
> — [RULES.md, ligne 58](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:58>)

> « **Un prompt qui exige un format doit porter le format.** »  
> — [RULES.md, ligne 107](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:107>)

Le corpus tranche lui-même : « Ajouter le schéma n’est pas durcir le prompt : on n’allège pas ce qui n’a jamais été dit » ([RULES.md, ligne 108](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:108>)). Les deux règles ont donc des objets distincts : supprimer la prescription inutile et expliciter un contrat nécessaire.

### Faux agents et vrais sous-processus

« Aucun appel fournisseur dans la suite de tests » ([RULES.md, lignes 82–83](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:82>)) n’interdit pas les vrais sous-processus locaux. Le corpus dit expressément qu’un sous-processus Python n’est « ni un appel fournisseur, ni du réseau » ([RULES.md, lignes 140–141](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:140>)).

### Abandon d’une source et preuve d’absence

Le corpus autorise l’abandon d’une source qui ne rapporte plus rien, à condition de noter le volume non lu ([RULES.md, lignes 158–159](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:158>)). Il interdit parallèlement d’affirmer une impossibilité sans avoir cherché tous les chemins ([RULES.md, ligne 61](<C:/Users/schne/AppData/Local/Temp/claude/C--Projets-IAbinome/9faea29c-7b23-4e25-bf6d-4aaff184a8a3/scratchpad/essai/recherche/corpus/fichiers/project/RULES.md:61>)).

Les deux restent compatibles si l’abandon conduit à classer le résultat **inconnu ou non prouvé**, et non négatif. Aucun cas du corpus ne montre une découverte manquée après abandon ; compter cette possibilité comme tension réelle serait l’inventer.

## La règle qui cède en premier

### Réponse factuelle

**La revue croisée palier par palier cède la première dans l’histoire documentée.**

Elle est la seule règle pour laquelle le corpus fournit simultanément :

- une règle générale ;
- une décision explicite de suspension ;
- une date, le 2026-09-03 ;
- un décideur, le PO ;
- un motif, la faible rentabilité après cinq tours ;
- une portée maintenue, la conception ;
- une condition de réouverture, la découverte d’un défaut qu’une relecture aurait attrapé.

Cette conclusion vaut uniquement pour l’état du projet documenté jusqu’au 2026-09-04. Elle ne démontre pas que la revue serait toujours la première règle sacrifiée dans une autre croissance.

### Réponse prédictive

**Indéterminée avec le corpus disponible.**

L’hypothèse la mieux ancrée est que la tension suivante apparaîtrait entre la limitation de l’échafaudage et l’accumulation de garanties : la porte d’état qui appelle une commande de récupération en fournit déjà le mécanisme élémentaire. Mais aucune donnée ne permet de dire quelle règle serait effectivement abandonnée. Il est également possible que la taille cible, une fonctionnalité ou une garantie de preuve cède ; le corpus ne fixe aucun ordre de priorité.

## Ce que le corpus ne couvre pas

Il manque, pour répondre pleinement à la croissance future :

- la taille actuelle de l’outil et son évolution dans le temps ;
- la définition de « l’outil » dans la métrique : production seule, tests, adaptateurs, prompts ou documentation ;
- la taille du projet servi au même instant ;
- un seuil distinct entre la cible d’environ 1 500 lignes et l’interdiction de dépasser le projet servi ;
- l’inventaire des contrôles ajoutés et des éléments retirés en échange ;
- un ordre de préséance entre simplicité, robustesse, preuve, portabilité et coût ;
- des mesures comparables du coût et du rendement des revues après la suspension ;
- des scénarios de croissance : volume documentaire, nombre d’adaptateurs, nombre d’agents, taille du corpus ou complexité des états ;
- des cas où l’application correcte de toutes les règles aurait effectivement reproduit l’échec fondateur.

Ce dernier point borne fortement la conclusion : le corpus montre des tensions et une concession, mais **ne prouve pas encore qu’IAbinome a échoué malgré l’application correcte de ses règles**. Il montre surtout que certains garde-fous peuvent engendrer leurs propres garde-fous — précisément le mécanisme historique que les règles cherchent à empêcher.

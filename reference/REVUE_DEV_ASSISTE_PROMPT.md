Relis en lecture seule l'implémentation du lot développement assisté dans
`C:/Projets/DialogForge_2`. Conception acceptée :
`conception/DEVELOPPEMENT_ASSISTE.md`. Code : `src/iabinome/development.py`,
changements de `src/iabinome/cli.py`. Tests : `tests/test_development.py`.
Documentation : `docs/COMMANDES.md`. Lis les fichiers nécessaires directement.

Priorité : défauts réels affectant intégrité du paquet, rattachement des résultats au
commit, absence d'écriture dans le dépôt cible, cohérence de la copie dans la
collaboration, chemins hostiles, reprises du cycle existant et contrat des commandes.
Vérifie la logique des tests : une assertion verte ne suffit pas si le défaut qu'elle
prétend voir peut passer inaperçu. Signale les contradictions entre conception et code.

Rends une liste courte de constats actionnables, avec sévérité et fichier/ligne.
Pour chaque constat, indique le scénario d'échec concret. Distingue les preuves lues
et les inférences. Ne modifie aucun fichier ; n'exécute pas d'agent fournisseur.

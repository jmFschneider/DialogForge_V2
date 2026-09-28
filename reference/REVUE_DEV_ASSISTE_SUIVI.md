Relecture ciblée de l'implémentation du développement assisté dans ce dépôt.
Lis d'abord `reference/REVUE_DEV_ASSISTE_PROMPT.md`, puis le code et les tests modifiés.
La première revue Claude trouvait :

1. Un fichier racine ajouté au paquet pouvait conserver le même package-id.
2. Une demande initiale augmentée avant `new` passait dev-verify.
3. Après `decide --correct`, dev-verify refusait la collaboration révisée.
4. Une revue STOPPED avec pièces ne pouvait devenir un antécédent.
5. `--repo` donné comme sous-dossier autorisait une sortie dans la racine Git.
6. Le contrôle textuel des validations (conception §15 point 10) était reporté sans trace.
7. Les chemins Git à retour à la ligne rendaient sources.txt inutilisable.
8. Sous POSIX, un rename concurrent peut remplacer un répertoire vide.
9. Un délai Git produisait une exception non gérée.
10. Des tests annoncés par la conception manquaient.

Les points 1 à 7 et 9 ont été corrigés avec tests ; le point 6 est documenté dans
`docs/COMMANDES.md`. Le point 8 est conservé comme limite POSIX ; le produit est
qualifié ici sous Windows. Pour le point 10, juge la couverture utile des garanties
propres à ce lot, en tenant compte de la suite existante du moteur A/B.

Lis les fichiers et donne seulement les écarts concrets restants ou les régressions
introduites. Ne modifie rien et n'appelle aucun autre agent.

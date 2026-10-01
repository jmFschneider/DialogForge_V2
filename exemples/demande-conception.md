# Demande

## Objectif
Concevoir la rotation des journaux d'une petite application de bureau, pour son mainteneur.
Aujourd'hui le fichier de journal grossit sans limite et remplit le disque des postes anciens.

## Livrable
Une note de conception d'une page : la politique de rotation retenue, ses paramètres, et ce
qu'elle ne couvre pas.

## Sources
Le dossier fourni en corpus : `politique-retention.md` et `incident-disque.md`. Dans la chaîne
complète, ce dossier est la synthèse acceptée de la recherche (`demande-recherche.md`).

## Contraintes
- Aucune dépendance nouvelle : bibliothèque standard uniquement.
- Le journal doit rester lisible avec un simple éditeur de texte.
- Une page au plus.

## Non-objectifs
- Pas d'envoi des journaux vers un serveur.
- Pas d'implémentation : la note est lue, puis appliquée à la main.

## Critères de fin
La note dit quelle taille ou quelle durée déclenche la rotation, combien de fichiers sont
gardés, et ce qui se passe si le disque est plein pendant l'écriture.

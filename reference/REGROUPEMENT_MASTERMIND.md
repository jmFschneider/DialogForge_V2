# Regroupement de Mastermind dans son dossier de mission

Date : 2026-10-03. Lot 2 du parcours de mission (`conception/PARCOURS_MISSION_CONCEPTION.md` §9).

**Statut : procédure répétée sur une copie, non exécutée sur les dossiers réels.** L'exécution réelle
a été refusée par le contrôle de permissions de la session ; elle reste à lancer par le PO, ou à
autoriser explicitement.

## Ce que fait la procédure

Avant : `DialogForge_missions\Mastermind` (la recherche, à la racine) et, à côté,
`DialogForge_missions\Mastermind-conception` (en `WAITING_HUMAN`, mandat vide, créée avant le lot 1).

Après : la recherche reste à la racine de `Mastermind` ; la conception y est **copiée** sous
`Mastermind\conception` ; `Mastermind\mission.json` rattache les deux. `Mastermind-conception` n'est
ni déplacée, ni modifiée : c'est la sauvegarde.

Écrit dans `Mastermind` : `mission.json` et `conception\`, rien d'autre. Aucun fichier de la recherche
n'est touché.

## Avant de lancer

1. Aucune exécution active : fermer la GUI et tout terminal qui travaille sur ces deux dossiers.
2. Contrôler l'absence de `Mastermind\verrou.json`, de `Mastermind-conception\verrou.json`, de
   `Mastermind\mission.json` et de `Mastermind\conception`. La commande le refuse sinon.

## Les deux commandes

```
dialogforge mission attach C:\Projets\DialogForge_missions\Mastermind C:\Projets\DialogForge_missions\Mastermind --role recherche
dialogforge mission adopt  C:\Projets\DialogForge_missions\Mastermind C:\Projets\DialogForge_missions\Mastermind-conception --role conception --source .
```

La première inscrit la recherche historique sous `.`. La seconde copie la conception dans un dossier
temporaire de `Mastermind`, compare **tous** les fichiers et dossiers (taille et SHA-256) avec
l'original, vérifie que l'original n'a pas changé pendant la copie, publie par un renommage (rien
n'est écrasé), puis l'inscrit avec `source = "."`. Toute différence abandonne sans rien publier.

## Ce que la répétition a établi

Répétition sur une copie des dossiers réels (110 et 22 entrées), le 2026-10-03, par ces mêmes
commandes :

| Contrôle | Résultat |
|---|---|
| Copies avant opération | identiques aux originaux (empreinte de chaque fichier) |
| Conception copiée / originale | **aucun écart** (16 fichiers) |
| Sauvegarde `Mastermind-conception` | inchangée |
| Fichiers de la recherche | aucun modifié ; seuls `mission.json` et `conception` ajoutés |
| `provenance_transition.json` | **absent de l'original** (créée avant le lot 1) : rien à recalculer |
| Chemins absolus dans les fichiers de reprise | aucun ; 2 citations en prose dans le corpus haché (livrable et bilan de la recherche), sans effet |
| `show Mastermind` | deux étapes : recherche « Version acceptée », conception « Intervention requise » |
| `status` de la conception rattachée | `WAITING_HUMAN`, question de A inchangée, prochaine action `resume --answer` |
| Ouverture de la racine | ouvre `conception` (dernière étape inscrite) ; la recherche reste atteignable |
| Reprise normale avec réponse, sur une seconde copie, faux agents | `AWAITING_APPROVAL`, 1 appel A et 1 appel B ; corpus vérifié intact ; demande complétée de la réponse ; originaux inchangés |

Le `source_path` de `provenance_transition.json` — relatif au dossier d'origine, faux après
déplacement — n'existe pas dans la conception réelle. Pour toute conception qui le porte, la
commande le recalcule (relatif au dossier de la mission) et garde l'ancienne valeur sous
`previous_source_path` ; elle exige alors `--source`. Ce cas est couvert par les tests sur une
conception créée par le lot 1.

## Après l'exécution

1. `dialogforge show C:\Projets\DialogForge_missions\Mastermind` : deux étapes, aucun « à rattacher »
   ni « partiel ».
2. Comparer, si souhaité, `Mastermind-conception` et `Mastermind\conception` : identiques.
3. GUI : l'accueil ne doit montrer **qu'une** ligne `Mastermind`. Retirer
   `Mastermind-conception` des récents (`~\.dialogforge\recents.json`) ; **la sauvegarde reste
   toutefois listée** par le balayage de `DialogForge_missions` tant qu'elle y est : voir ci-dessous.
4. La reprise de la conception (réponse à la question de A : plan de réalisation depuis la recherche
   acceptée, besoin initial, exclusions, H1 à H5 traitées, puis relecture de cette réponse) est une
   étape distincte, qui appelle les agents : elle se lance explicitement, depuis
   `Mastermind\conception` uniquement.

## Point à décider

Tant que `Mastermind-conception` est sous `DialogForge_missions`, la GUI la liste comme une
collaboration indépendante, à côté de la mission : reprendre la sauvegarde par erreur ferait diverger
deux historiques. Une fois la reprise validée, la sortir de ce dossier (ou la renommer) est une
décision du PO ; le logiciel ne la déplace pas.

# Relecture contradictoire de l'inventaire — consignes pour Codex

> Deux passes, dans cet ordre. **La seconde n'est envoyée qu'après la réponse à la première.**
> Motif du découpage : donner d'emblée les zones que l'auteur suspecte oriente le contradicteur
> vers ce que l'auteur sait déjà, et l'éloigne de ce qu'il ignore.

---

## Passe 1 — à envoyer telle quelle

```text
Tu es le contradicteur.

Lis conception/INVENTAIRE.md dans C:\Projets\IAbinome. Il prétend récolter deux
mois d'apprentissage tirés de huit sources, listées dans RECOLTE.md.

Une seule question :

    Qu'est-ce qui a été écarté en silence ?

Une leçon écartée avec son motif écrit est décidée, donc pas perdue. Ce qui compte
est ce qui a disparu sans que personne s'en aperçoive.

Ne juge ni la forme, ni la qualité, ni la pertinence des choix : uniquement les
manques. Liste tout ce que tu trouves — le tri viendra après.

Les sources sont en LECTURE SEULE, n'y écris rien :
  C:\Projets\DialogForge
  C:\Projets\DialogForge-refactor-lab
  C:\Projets\DialogForge-refactor-archives
  C:\Projets\Florapy_V2

Écris ta réponse dans C:\Projets\IAbinome\conception\RELECTURE_CODEX_PASSE1.md :
une ligne par omission, chacune avec l'endroit exact où tu l'as trouvée.
```

---

## Passe 2 — seulement après lecture de sa réponse

```text
Voici trois zones que l'auteur suspecte lui-même. Dis, pour chacune, si ta passe 1
l'a couverte, et ce que tu ajoutes.

1. history.md (2 533 lignes) et README.md (1 046 lignes) de DialogForge n'ont
   jamais été ouverts : jugés redondants avec les huit sources.
2. Les lignes X16, X17 et X18 écartent 166 éléments en trois lignes d'agrégat —
   78 [DIFFÉRÉ], 33 correctifs fix:, 55 fichiers de tests.
3. La colonne Code compte 26 lignes contre 24 pour Prompt, alors que RECOLTE.md
   la voulait la plus courte par construction.

Même consigne : les manques, pas la qualité.
```

---

## Après les deux passes

L'arbitrage humain porte sur l'inventaire **augmenté** des omissions retenues, pas sur
la liste brute de Codex. Puis seulement l'étape 1, qui ne prend en entrée que la colonne **Code**.

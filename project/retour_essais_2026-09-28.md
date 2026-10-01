# Retour des essais GUI — reprise d'activité chez les seniors

Constats recueillis avec le PO les 27–28 septembre 2026. Ce document conserve les
améliorations à étudier ; il ne vaut ni décision de conception ni lancement d'un lot.

## Essais observés

- `Reprise_Activité_Senior/` : A = Claude Opus, B = Codex `gpt-6-sol`, web autorisé.
  Cycle terminé en `AWAITING_APPROVAL` après deux révisions ; un constat B reste ouvert
  (`B-preuve-005`). Le premier appel A avait échoué sur l'accès à l'abonnement Claude,
  puis a été relancé après correction de cet accès.
- `Reprise_Activité_Senior_inv/` : A = Codex `gpt-6-sol`, B = Claude Opus, web autorisé.
  Cycle terminé en `AWAITING_APPROVAL` après une révision ; un constat B reste ouvert
  (`B-sources-002`).
- Les deux configurations portent la même empreinte de demande
  (`5e591aa6836061a173c2fa5bec2e2ec1e675097291943037399cb63a3ebe98cf`).
  Aucun des deux livrables n'est encore accepté ; la comparaison de leur contenu reste
  à faire séparément.

## Améliorations relevées

1. **Recherche web sans corpus local.** Le PO demande une recherche de sources web et
   une synthèse, sans corpus initial. Le type `recherche` exige actuellement un corpus
   non vide, même avec `web_access = true`. Le recours au type `conception` permet le
   lancement mais dénature la mission. À concevoir : autoriser `recherche` avec web
   activé et corpus local absent, puis préciser la provenance des sources et la
   vérification attendue. Clarifier la GUI en attendant cette évolution.
2. **Parcours de cadrage.** L'entrée « Cadrer avec un agent » est peu visible. En mode
   cadrage, la zone « Demande » et la zone « Idée de départ » sont simultanément
   visibles, alors que seule la seconde alimente le premier appel de F. Étudier un
   parcours où l'idée est la seule saisie initiale et où la demande éditable apparaît
   clairement après le brouillon de F.
3. **Choix des modèles.** Un champ libre a laissé passer `GPT-6-Sol` au lieu de
   `gpt-6-sol`, provoquant un échec chez Codex. Les listes A, B et F alimentées par
   `src/iabinome/modeles.toml` ont été implémentées, testées puis commitées après ce
   relevé. Garder le fichier facile à mettre à jour et
   distinguer l'identifiant exact de la disponibilité propre au compte connecté.
4. **Diagnostic des appels interrompus.** La GUI indique « appel inabouti » sans rendre
   immédiatement visible la cause utile dans les sorties de la CLI. Les deux incidents
   observés — identifiant de modèle refusé par Codex et abonnement Claude indisponible —
   ont nécessité une inspection manuelle des fichiers d'appel. Étudier un résumé du
   motif et un accès direct à la trace, sans masquer le statut ni suggérer une relance
   qui répéterait la même erreur.
5. **Visibilité du dossier.** Après un échec, le PO n'a pas repéré le dossier pourtant
   créé. Rendre son chemin et l'action « Ouvrir le dossier » plus visibles dès la
   création et dans l'écran de suivi, y compris en cas d'incident.
6. **Progression visuelle A/B.** Le PO trouve la progression des deux agents difficile
   à suivre. Revoir l'écran de suivi pour montrer, d'un coup d'œil, l'agent actif,
   l'étape courante (proposition, critique, révision), les étapes terminées, le numéro
   de révision et ce qui attend une action humaine. Les essais inversés sont un bon
   cas de contrôle : les rôles A/B doivent rester lisibles quel que soit le fournisseur.

## Suite

Faire arbitrer le périmètre et l'ordre de ces améliorations avant une nouvelle
implémentation. Le point 3 est intégré.

**2026-10-01 — points 4, 5 et 6 engagés par le PO et intégrés :**

- 4 : l'extrait du message de l'outil est pris en fin de sortie, où l'erreur se trouve
  (la sortie Codex commence par une bannière et l'écho du prompt). L'incident nomme
  l'outil et le modèle de l'appel, et dit qu'une relance les reprend. Les sorties
  brutes non vides de l'appel sont lisibles depuis l'écran de suivi, qui s'ouvre en
  fin de texte. Un bouton ouvre le dossier de l'appel. Le changement vaut aussi pour la CLI.
- 5 : le chemin complet et « Ouvrir le dossier » sont en tête de l'écran de suivi, y
  compris pour un dossier illisible. Le message de création donne le chemin.
- 6 : progression en grille, un tour par ligne, A à gauche et B à droite, chaque
  colonne nommant son outil et son modèle. L'étape courante est en gras, les révisions
  encore possibles sont marquées « si B la demande », une ligne « Vous » porte la
  décision, et une phrase dit qui agit ou ce qui vous attend.

**2026-10-01 — point 2 traité comme un correctif (PO) :** en mode agent, l'idée de départ
est la seule saisie. L'éditeur de demande et l'import sont retirés jusqu'au brouillon de F,
qui apparaît sous le cadrage avec le titre « Demande rédigée par F — à relire et corriger
avant de créer ». Revenir à « Saisir » ou « Importer » rétablit l'éditeur. Le choix du mode
se lit « Cadrer avec un agent (une idée suffit) ».

**2026-10-01 — point 1 résolu par la redéfinition des types de mission**
(`conception/TYPES_DE_MISSION.md`) : une recherche part du web seul, sans corpus local. Tous les
points de ce relevé sont clos.

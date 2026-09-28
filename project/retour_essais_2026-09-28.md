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
implémentation. Les points 1, 2, 4, 5 et 6 restent ouverts ; le point 3 est intégré.

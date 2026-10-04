# Retour d'essai — Mastermind, du Runner au code utilisable

Constats recueillis avec le PO le 4 octobre 2026, après la mise en œuvre de
`conception/RUNNER_AGENT_UNIQUE.md` (R1 à R3). Ce document conserve les améliorations à
étudier ; il ne vaut ni décision de conception ni lancement d'un lot.

## Essai observé

- Mission `C:\Projets\DialogForge_missions\Mastermind` : recherche, puis conception acceptée
  avec réserves, puis développement par le Runner sous Ubuntu WSL2 (Claude, profil `claude-wsl`).
- Depuis la GUI, le paquet déjà produit (`dde9eaa`, `node --test` : 23 tests) a été remis dans
  `code/` sur `dialogforge/candidat-001`, essayé par le PO, puis accepté : `master` = `dde9eaa`,
  reçu dans `developpement/integrations/`.
- PO : « dialogforge est allé au bout. J'ai testé le programme et il est fonctionnel. »
- Aucun nouvel appel de A pendant cet essai : la boucle R2 (ligne finale, poursuite, correction
  demandée à A puis acceptée) n'a pas encore tourné en réel.

## Améliorations relevées

1. **Lisibilité des sorties.** PO : « Les sorties de dialogforge ne sont pas forcément très
   lisibles, compréhensibles. » À préciser avec lui avant toute modification : écran Runner
   (texte d'état mêlant chemins Ubuntu, numéros de paquet et consignes), bilan de A affiché brut,
   messages de pause ou d'erreur, vocabulaire (paquet, collecte, remise, candidat, validations),
   ou autres écrans. Contrainte : façade + GUI à 2 699 / 2 700 lignes effectives ; on commence par
   simplifier et réécrire les textes, sans fonction nouvelle.
2. **Arrivée sur une ancienne revue.** À l'ouverture, la mission arrivait sur la revue
   documentaire du code créée au lot 4 (« 001 — en cours », « Reprendre le cycle »), loin du code.
   *Corrigé le même jour (`67e74b8`)* : une mission ne s'ouvre plus sur une étape `revue`, affichée
   « archive, hors du parcours ».

## Suite

Faire préciser le point 1 par le PO, puis arbitrer son périmètre. Clore la recette R4 lors d'une
première correction réelle demandée à A.

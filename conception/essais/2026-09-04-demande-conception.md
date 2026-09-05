# Demande — GUIDE.md d'IAbinome

Rédige `GUIDE.md`, le guide de prise en main d'IAbinome. **Une page**, pas plus. Public : une personne
qui découvre l'outil et veut l'utiliser aujourd'hui, pas comprendre sa conception.

## Ce qu'est IAbinome

Un outil en ligne de commande, Python 3.12, bibliothèque standard seule, qui coordonne **deux agents
IA en CLI** aux rôles distincts : **A produit, B critique, l'humain arbitre**. Le livrable est un
document de conception ou de recherche. Tout tient en fichiers sur disque, dans un dossier par
collaboration, avec un `etat.json` lisible à l'œil nu.

Le cycle : `demande.md` → A produit → B critique → A révise (N fois au plus) → A finalise → livrable
dans `livrables/version_finale.md`.

**A et B sont chacun l'un ou l'autre des deux outils CLI supportés**, choisis au lancement. Les quatre
permutations fonctionnent. Aucun rôle n'est lié à un outil.

## La surface exacte

```text
python -m iabinome new COLLAB
    --demande FICHIER
    --kind {conception,recherche}
    --reviewer-access {context-only,consult}      # obligatoire, sans défaut
    --agent-a ADAPTATEUR --agent-b ADAPTATEUR     # obligatoires, sans défaut
    [--source-root DOSSIER --source-list MANIFESTE] [--source-label TEXTE]
    [--model-a MODELE] [--model-b MODELE]
    [--max-revisions N]                            # défaut 2

python -m iabinome run    COLLAB [--timeout SECONDES]     # défaut 1800
python -m iabinome resume COLLAB [--timeout SECONDES]
                          [--answer NOUVELLE_DEMANDE | --retry-call UUID --reason-file FICHIER]
python -m iabinome status COLLAB [--json]
```

Il n'existe aucune autre commande. En mission `recherche`, `--source-root` et `--source-list` sont
obligatoires et le corpus doit être non vide : l'outil ne consulte aucune source externe, le corpus est
ce que l'humain y a déposé. `--source-list` liste des chemins exacts, un par ligne, relatifs à
`--source-root` — ni motif générique, ni découverte automatique.

## Les statuts, et ce qu'on fait de chacun

| Statut | Sens | Ce que fait l'humain |
|---|---|---|
| `READY` | le cycle peut continuer | `run` |
| `RUNNING` | un appel est en cours ou a été interrompu | `resume` |
| `WAITING_HUMAN` | A a posé une question, ou B a bloqué | `resume --answer FICHIER` |
| `INTERRUPTED` | l'appel a été coupé (délai, Ctrl-C, plafond de sortie) | `resume --retry-call UUID --reason-file FICHIER` |
| `ERROR` | la réponse est inexploitable | même chose, si l'incident est relançable |
| `AWAITING_APPROVAL` | le cycle est allé à son terme | lire le livrable |

Codes de sortie : `0` AWAITING_APPROVAL · `1` refus avant toute modification · `2` erreur d'usage
(argparse) · `3` INTERRUPTED · `4` ERROR · `5` WAITING_HUMAN. **Le code décrit le résultat de la
commande, jamais l'approbation du livrable** : `0` veut dire « le cycle s'est arrêté où il devait »,
pas « le document est bon ».

## Points que le guide doit rendre clairs

1. **Répondre à une question, c'est fournir une nouvelle demande complète**, pas un complément.
   L'ancienne est archivée en `demande.md.001`. Une réponse partielle créerait une seconde autorité.
2. **Aucune relance n'est automatique.** `--retry-call` exige un fichier de motif non vide : c'est une
   trace de décision humaine attribuable, pas une preuve que la cause a disparu.
3. **`version_finale.md` s'ouvre sur une ligne écrite par le programme** disant que le document n'est
   pas approuvé — sa présence prouve que le cycle s'est achevé, rien de plus.
4. **Le corpus est figé** à la création et vérifié contre son manifeste avant chaque appel. Il n'existe
   pas de rafraîchissement : le changer en cours de cycle détruirait la référence commune de A et B.
5. **Une seule commande à la fois par collaboration**, garantie par un verrou. On lance, ça tourne au
   premier plan, on ferme le terminal pour interrompre.

## Contraintes de forme

- Une page. Si le guide dépasse, c'est qu'il explique la conception au lieu de l'usage.
- Un exemple complet de premier `new` suivi d'un `run`, avec des valeurs concrètes.
- Ne nomme aucun fournisseur d'IA : les adaptateurs se désignent par leur identifiant sur la ligne de
  commande, et le guide doit rester vrai quel que soit l'outil branché.
- Dis franchement ce que l'outil ne fait pas, plutôt que de laisser le lecteur le découvrir.

> Ce document n'est pas approuvé : sa présence prouve que le cycle s'est achevé, rien de plus.
> Revue B : CONSULT · constats restés ouverts : 6 (dont 0 BLOCKING) · corpus absent.


# `GUIDE.md`

Contenu du fichier à écrire, prêt à copier :

````markdown
# IAbinome — prise en main

IAbinome fait travailler deux agents IA en ligne de commande sur un même document.
**A produit, B critique, vous arbitrez.** Le livrable est un document de conception ou de
recherche ; tout tient dans des fichiers ordinaires — un dossier par collaboration, un
`etat.json` lisible à l'œil nu.

Le cycle : `demande.md` → A produit → B critique → A révise (N fois au plus) → A finalise →
`livrables/version_finale.md`.

A et B sont chacun l'un des adaptateurs CLI supportés (`claude`, `codex`), choisis au
lancement. Les quatre combinaisons fonctionnent ; aucun rôle n'est attaché à un outil.

## Ce que l'outil ne fait pas

- **Il ne va chercher aucune source.** La référence commune de A et B est le corpus que vous
  avez déposé. Sous `--reviewer-access consult`, B garde les capacités de sa propre CLI : ce
  qu'il consulte ainsi n'entre pas dans le corpus et n'est pas reproductible.
- **Il n'approuve rien.** `version_finale.md` s'ouvre sur une ligne écrite par le programme
  disant que le document n'est pas approuvé : sa présence prouve que le cycle s'est achevé,
  rien de plus.
- **Il ne relance rien tout seul.** Après une coupure ou une erreur, rien ne repart sans une
  décision écrite de votre part.
- **Il ne rafraîchit pas le corpus**, figé à la création et vérifié avant chaque appel.
- **Il ne tourne pas en tâche de fond** : une commande occupe le terminal jusqu'à son terme.
- **Il n'a que quatre commandes** : `new`, `run`, `resume`, `status`.

## Premier essai

Écrivez d'abord votre demande dans un fichier : c'est l'unique autorité du cycle.

```sh
python -m iabinome new refonte-cache \
  --demande ./ma-demande.md \
  --kind conception \
  --reviewer-access context-only \
  --agent-a claude --agent-b codex \
  --max-revisions 2

python -m iabinome run refonte-cache
```

*Sous PowerShell : tout sur une seule ligne, ou terminez chaque ligne par un accent grave.*

`--reviewer-access` est obligatoire et sans défaut, car ce choix est figé pour la
collaboration : `context-only`, B ne travaille que sur ce qui lui est transmis et doit
qualifier ce qu'il ne peut pas vérifier ; `consult`, B garde les capacités de son outil.
Chaque adaptateur a un modèle par défaut selon le rôle ; `--model-a` / `--model-b` le
remplacent. `run` enchaîne les appels au premier plan et rend un code de sortie ;
`--timeout` (1800 s par défaut) borne **un appel**, pas la session.

## Mission recherche

`--kind recherche` exige `--source-root` et `--source-list`, et un corpus non vide.
`--source-list` énumère des chemins **exacts**, un par ligne, relatifs à `--source-root` : ni
motif générique, ni découverte automatique. Le corpus contient ces fichiers-là et pas les
autres fichiers du dossier. `--source-label` le nomme pour les deux agents.

Il est copié et empreint à la création, puis vérifié contre son manifeste avant chaque appel.
Modifier les originaux ensuite ne change rien ; modifier la copie fait échouer la
vérification. Pour un autre corpus, créez une autre collaboration.

## Les statuts, et quoi faire de chacun

| Statut | Sens | Votre geste |
|---|---|---|
| `READY` | le cycle peut continuer | `run` |
| `RUNNING` | un appel est en cours ou a été interrompu | `resume` |
| `WAITING_HUMAN` | A a posé une question, ou B a bloqué | `resume --answer FICHIER` |
| `INTERRUPTED` | l'appel a été coupé (délai, Ctrl-C, plafond de sortie) | `resume --retry-call UUID --reason-file FICHIER` |
| `ERROR` | la réponse est inexploitable | idem, si l'incident est relançable |
| `AWAITING_APPROVAL` | le cycle est allé à son terme | lisez le livrable |

`status refonte-cache` (ou `--json`) donne statut, phase, révision, constats restés ouverts,
dernier incident et âge du corpus. Il ne donne pas l'UUID d'appel : il est dans `etat.json`
(`current_call.call_id`) et termine le nom du dossier `appels/NNNN-A-<uuid>/`.

## Répondre, ou relancer

Sur `WAITING_HUMAN`, le texte de la question est déposé dans `echanges/`. Vous répondez en
fournissant **une nouvelle demande complète**, jamais un complément :
`resume refonte-cache --answer ./ma-demande-v2.md`. L'ancienne est archivée en
`demande.md.001` et la nouvelle la remplace intégralement — un simple ajout créerait une
seconde autorité, et plus rien ne dirait laquelle fait foi.

Sur `INTERRUPTED` ou `ERROR` :
`resume refonte-cache --retry-call <UUID> --reason-file ./motif.txt`. Les deux options vont
ensemble et le motif ne peut pas être vide : c'est une trace de décision humaine
attribuable, pas une preuve que la cause a disparu. Lisez l'incident avant de l'écrire.
Toutes les erreurs ne sont pas relançables ; les autres sont refusées. `--answer` et
`--retry-call` sont incompatibles : ce ne sont pas le même acte.

## Codes de sortie

`0` AWAITING_APPROVAL · `1` refus avant toute modification · `2` erreur d'usage · `3`
INTERRUPTED · `4` ERROR · `5` WAITING_HUMAN.

**Le code décrit le résultat de la commande, jamais l'approbation du livrable.** `0` veut
dire « le cycle s'est arrêté où il devait », pas « le document est bon ».

## Une seule commande à la fois

Un verrou le garantit par collaboration. Pour interrompre : Ctrl-C, ou fermez le terminal.
L'appel coupé revient alors en `INTERRUPTED` et ne repartira que sur une relance motivée ; le
travail déjà écrit sur disque reste là, celui de l'appel en cours est perdu.
````

---

**Hors livrable — points restés ouverts.**

- Les identifiants `claude` et `codex` sont des noms de produit. La demande interdit de nommer un fournisseur mais prescrit de désigner les adaptateurs par leur identifiant de ligne de commande, et exige un exemple à valeurs concrètes ; j'ai retenu cette lecture. Décision à confirmer : si elle est refusée, remplacer par des placeholders et renvoyer à `--help`, au prix d'un exemple non exécutable.
- La frontière `RUNNING` / `INTERRUPTED` après une coupure n'est pas spécifiée ; le guide ne promet pas lequel des deux survient et renvoie au tableau. Le sort exact du travail de l'appel coupé (dernière phrase du guide) est déduit du code, non observé.
- Les libellés de `status` et le comportement après Ctrl-C n'ont jamais été vérifiés en exécution réelle — seulement par lecture de `cli.py` et `workflow.py`. À relire après un premier cycle de bout en bout.
- Le guide tait volontairement *quels* incidents sont relançables : la table est interne et fermée, la publier inviterait à interpréter un code plutôt qu'à lire l'incident.
- `status --json` ne comporte pas `call_id`, ce qui oblige le guide à envoyer le lecteur ouvrir `etat.json` à la main pour obtenir l'argument d'une commande publique. Correctif d'une ligne dans `cli.py`, hors du périmètre de cette demande ; il raccourcirait le guide.

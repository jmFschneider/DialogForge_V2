# Types de mission : recherche → conception → développement

> Note d'arbitrage du 2026-10-01, rédigée à la demande du PO. **Recommandations D1 à D6 validées
> telles quelles par le PO le 2026-10-01.** Objectif : remettre le projet d'équerre avant d'ouvrir une
> nouvelle phase de développement.

## Constat

- Les deux types ne diffèrent que par deux choses. `recherche` ajoute à A une consigne sur les
  sources (`prompts.py:28`) et exige un corpus local, refusé sans lui à trois endroits
  (`facade.py:429`, `framing.py:270`, `workflow.py:341`). B reçoit la même consigne dans les deux cas.
- L'usage réel les a contournés. Les **17 collaborations existantes** (`essais-3-1`,
  `DialogForge_missions`) sont **toutes de type `conception`** : 8 sans corpus, dont 6 avec le web
  (Peinture, reprise d'activité…), qui sont en fait des recherches ; 9 avec un corpus. **Aucune n'est
  de type `recherche`.**
- Une incohérence existe déjà. La revue du développement assisté est « une collaboration de
  recherche » dans le README, mais `--kind conception` dans `DEVELOPPEMENT_ASSISTE.md` §3.3.

## Intention du PO

**Recherche** : ce que fait aujourd'hui `conception`. Une idée ou une question devient un dossier
d'étude sourcé, avec le web, sans corpus obligatoire. **Conception** : part d'un dossier, normalement
produit par une recherche, pour établir le plan et les solutions qui mènent à la réalisation, juste
avant le code. **Développement** : le développement assisté existant (`dev-export`, `dev-package`,
`dev-verify`).

## Décisions à prendre

**D1 — Sens et sources de chaque type.**
Recommandation. `recherche` exige **au moins une source** : le web ouvert, ou un corpus local, ou
les deux. Sans aucune des deux, elle ne s'appuierait que sur la mémoire du modèle. `conception`
exige **un corpus** : le dossier d'entrée, qu'il vienne d'une recherche ou non (spécification
existante, notes, documentation d'un projet). Valeurs de `--kind` inchangées.

**D2 — Consignes.**
`recherche` garde la consigne actuelle, plus une phrase : *« Une source web se cite par son adresse
et sa date de consultation. »* `conception` reçoit une consigne propre, courte (`POURQUOI.md` règle 4) :

> Pars du dossier fourni : ses faits établis ne se rouvrent pas sans contre-preuve. Compare les
> options sérieuses et motive le choix retenu. Nomme risques, hypothèses et points ouverts. Termine
> par des étapes de réalisation vérifiables, assez précises pour être confiées au développement.

**D3 — Collaborations existantes.**
Recommandation : **aucune migration.** Le contrôle des sources se fait à la création (`new`, GUI,
cadrage). Le contrôle répété au lancement (`workflow.py:341`) est retiré : il ne protège qu'un cas
que la création refuse déjà. Une collaboration existante reste lisible et reprenable. Seule une
correction ciblée lancée après le changement recevrait la nouvelle consigne de son type. Aucune
collaboration `recherche` n'existe, donc le changement de sens ne trahit aucun livrable passé.

**D4 — Enchaînement.**
Recommandation : « **Poursuivre en conception** », sur une recherche **acceptée** seulement (comme
`dev-export` exige une conception acceptée). En CLI : `new --kind conception --depuis <recherche>` ;
dans la GUI : un bouton sur l'écran de suivi. Le corpus de la conception est alors le livrable et le
bilan de la recherche, copiés et hachés comme tout corpus. La provenance nomme la collaboration
source et l'empreinte du livrable. Rien n'est lancé automatiquement.

**D5 — Revue du développement assisté.**
Recommandation : type `recherche`. Elle établit des faits sourcés dans le paquet. Corriger la
commande de `DEVELOPPEMENT_ASSISTE.md` §3.3.

**D6 — Rappel en tête de la GUI** (demande du PO). Sur l'accueil, à la place de « A produit ·
B critique · vous décidez » :

> **Recherche → Conception → Développement**
> Partez d'une idée. Une recherche l'éclaire avec des sources, une conception en tire un plan prêt
> à coder, puis le code passe à son tour en revue. À chaque étape, A produit, B critique, et c'est
> vous qui décidez.

Sur l'écran de création, une ligne sous le choix du type rappelle ce que chacun attend.
`creation.py` est déjà au-dessus de son plafond de 400 lignes : cette ligne s'accompagne d'un
découpage de l'écran, pas d'un ajout de plus.

## Ce qui en découle

- Décision du 2026-09-03 (« un document de conception ou de recherche ») : maintenue, avec le sens
  redéfini ici, à amender par écrit et daté dans `CLAUDE.md` §1 et `project/RULES.md`.
- À réécrire : `exemples/` (l'exemple de recherche à mini-corpus devient l'exemple de conception),
  README, `docs/COMMANDES.md`, `docs/PRISE_EN_MAIN.md`, et les tests qui rejouent les exemples
  (`tests/test_docs.py`).
- Taille estimée : D1 à D3 et D5, une cinquantaine de lignes dans `src/` ; D4, une centaine ; D6,
  quelques lignes, plus le découpage de `creation.py`. Façade + GUI : 1 799 / 2 000.
- Hors de cette note : un troisième type, tout enchaînement automatique, toute exécution de code.

## Mise en œuvre (2026-10-01)

Les trois lots sont faits. Un écart par rapport à D4 : le corpus d'une conception qui poursuit une
recherche comprend aussi `decisions.json`, seul fichier qui porte les réserves d'une acceptation.
Le cadrage par un agent ne se combine pas encore avec `--depuis` : refusé avant tout appel.

## Ordre proposé

1. D1, D2, D3, D5 et la documentation : un lot.
2. D6 : l'accueil, puis l'écran de création avec son découpage.
3. D4, l'enchaînement : un lot à part.

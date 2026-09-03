# Étape 0 — récolter deux mois d'apprentissage sans les reperdre

> Décidé le 2026-09-02, à exécuter depuis une session ouverte dans `C:\Projets\IAbinome`.
> À faire **avant** la spécification de `DEPART.md`. Rien n'est encore récolté.

## La contradiction à désamorcer d'entrée

« Ne rien perdre » et « 1 500 lignes » ne sont compatibles que si l'on sépare **la récolte** de **l'implémentation**. La plupart des leçons de ces deux mois ne deviendront pas du code : elles deviennent une phrase dans un prompt, une règle écrite, un test — ou **un abandon assumé**.

**Une leçon écrite puis volontairement écartée n'est pas perdue : elle est décidée.** Ce qui se perd, ce n'est jamais ce qu'on jette en connaissance de cause, c'est ce qui disparaît sans que personne s'en aperçoive.

Preuve que la cible est atteignable : la doctrine du prédécesseur avait **déjà** été distillée une fois, dans `DialogForge\context\*.md` — **huit fichiers, 194 lignes au total**. C'est le point de comparaison.

## Question tranchée le 2026-09-03

**L'inventaire couvre-t-il aussi les leçons de conduite de projet** — budgets, supervision, arbitrage, coût — **ou seulement ce qui concerne l'outil ?**
Les premières ne deviendront jamais du code, mais ce sont elles qui ont coûté le plus cher.

**Réponse : les deux.** Motif — la doctrine déjà distillée avait tranché de fait : `context\supervision.md`
pèse **113 des 194 lignes** et ne parle que de budgets, de surveillance et d'erreurs. Les écarter aurait
laissé la moitié du capital dans un chantier gelé. Elles reçoivent la destination **Règle**, jamais **Code**.

*Tranché par Claude faute d'arbitrage disponible en séance, sur une preuve mesurée. Rouvrable — mais alors
en le signalant, jamais en silence.*

## Où vivent réellement ces deux mois

Tout est sous `C:\Projets\DialogForge` sauf mention contraire. **Lecture seule.**

| # | Source | Volume | Ce qu'on y trouve |
|---|---|---|---|
| 1 | `context\*.md` | **194 lignes** | La doctrine déjà distillée. Densité maximale, à lire en premier. |
| 2 | Messages des commits `fix:` | **42** | 42 choses qui ont cassé. `git log --format='%s' \| grep '^fix'` |
| 3 | `backlog.md` | **85 `[DIFFÉRÉ]`** | 85 décisions consciemment reportées, donc déjà réfléchies. |
| 4 | `GUIDE_UTILISATION.md` | 541 lignes | L'ergonomie réellement apprise à l'usage. |
| 5 | `…-refactor-archives\preuves\README.md` et `ARRET_REFACTORING.md` | — | Les 5 faits mesurés du Lot 0, les 3 défauts techniques. |
| 6 | Les 4 `version_finale.md` sous `Collab\` | 3 850 lignes | Livrables A/B : les décisions débattues et tranchées. |
| 7 | **Noms** des 70 fichiers de `tests\` | — | Les noms suffisent : ils disent quels comportements ont dû être protégés. |
| 8 | `C:\Projets\Florapy_V2\project\collab\decisions.md` + les 9 missions réelles | — | Le retour d'usage, pas la théorie. |

`history.md` (2 533 lignes) et `README.md` (1 046) sont volumineux et largement redondants : à n'ouvrir qu'en dernier, si un manque apparaît.

**Récolter dans cet ordre, et s'arrêter dès qu'une source ne rapporte plus rien de neuf — en le notant.**

## L'artefact : `conception\INVENTAIRE.md`

**Une ligne par leçon**, et chaque ligne reçoit exactement une destination :

| Destination | Ce que ça veut dire |
|---|---|
| **Code** | Devient une ligne d'IAbinome. La colonne la plus courte, par construction. |
| **Prompt** | Devient une phrase dans un gabarit A ou B. C'est là qu'ira le gros du capital. |
| **Règle** | Va dans `CLAUDE.md` ou `POURQUOI.md`. Ne devient **jamais** du code. |
| **Test** | Devient un test de régression avec l'agent `fake`. |
| **Écarté** | Avec le motif en une ligne. **Colonne obligatoire** — un inventaire sans elle est un entrepôt. |

Deux contraintes de forme, qui sont aussi des filtres :

- **Une leçon qui ne tient pas en une ligne n'est pas encore comprise.** — Tenue.
- ~~**Si l'inventaire dépasse ~200 lignes, on a rechuté.**~~ **Levé le 2026-09-03 par le PO.**
  Le chiffre était arbitraire et le périmètre a grandi entre-temps (la recherche y est entrée).
  La garde qui subsiste est celle de `POURQUOI.md` règle 1 — l'outil ne dépasse jamais le projet
  qu'il sert. C'est une mesure, pas un plafond décrété.

## Méthode — c'est elle qui garantit que rien n'est perdu

Claude récolte. Puis **Codex relit avec une seule consigne : « qu'est-ce qui a été écarté en silence ? »**

C'est le rôle exact du contradicteur, et la seule vérification sérieuse — bien plus fiable que l'auteur relisant son propre travail. Au passage, cela fait tourner le protocole d'IAbinome avant même qu'il soit codé.

La récolte se fait **à la main dans Claude Code**, pas par DialogForge : c'est de l'archéologie sur quatre dossiers avec des outils de recherche, pas une tâche de prose depuis une demande cadrée. La relecture, elle, peut passer par l'un ou l'autre.

## Enchaînement

**Étape 0** — cette récolte, arbitrée par vous.
**Étape 1** — la spécification de `DEPART.md`, qui ne prend en entrée que la colonne **Code** de l'inventaire.
**Étape 2** — l'implémentation.

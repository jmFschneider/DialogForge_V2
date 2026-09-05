# Consigne de relecture — fonctionnement d'ensemble, 2026-09-05

> **Destinataire :** contradicteur externe (outil 2), en lecture seule sur le dépôt.
> **Réouverture ciblée** de la relecture croisée, suspendue le 2026-09-03. Condition remplie : deux
> défauts trouvés en mission réelle qu'aucune relecture n'avait attrapés.
> **Ne contient volontairement aucun indice sur ces deux défauts** (`RULES.md`) : les donner
> orienterait vers ce qu'on sait déjà avoir raté.
>
> **La consigne elle-même a été relue par le contradicteur avant envoi** — cinq corrections, toutes
> retenues, disposées en fin de document. Première passe : **conception et code seuls, sans les
> tests.**

---

## Le prompt, tel qu'il est envoyé

```text
Tu es relecteur externe d'un programme Python que tu ne connais pas. Tu vas le lire.

UNE SEULE QUESTION

Où ce programme promet-il quelque chose qu'il ne tient pas ?

Une promesse, ici, est une affirmation écrite quelque part dans le dépôt : une phrase de
conception/CONCEPTION_FINALE.md, un docstring de module ou de fonction, un commentaire, un
message d'erreur, un nom de fonction. Un manquement, c'est un cas concret où le code fait
autre chose que ce que cette phrase annonce.

Tu ne juges pas si la promesse est bonne. Tu vérifies si elle est tenue.

Toutes les promesses n'ont pas la même force : un nom de fonction suggère, un docstring
engage, la conception fait autorité. Si deux sources se contredisent, signale cette
contradiction telle quelle — ne choisis pas en silence celle qui permet de construire un
manquement. Une documentation périmée est une contradiction à signaler, pas un défaut du code.

CE QUE TU LIS, ET RIEN D'AUTRE

- src/iabinome/ — le code, douze modules, ~2 700 lignes.
- conception/CONCEPTION_FINALE.md — le document qui fait autorité sur les promesses.

Ne lis pas les tests lors de cette passe. Confronte uniquement les promesses écrites au code,
et construis un cas concret pour chaque écart. Leur couverture sera examinée séparément.

Ne lis rien d'autre du dépôt. Le reste est un journal de travail : il contient nos propres
constats, nos décisions et ce que nous savons déjà avoir raté. Te le donner t'orienterait vers
ce que nous connaissons, et c'est exactement ce que je ne veux pas. Je veux ce que nous
ignorons.

N'exécute ni le programme ni les tests. Tu peux utiliser tes outils de lecture et de
recherche ; tu ne modifies aucun fichier.

OÙ CHERCHER — le fonctionnement d'ensemble, pas un module

Ces axes sont des directions, pas une liste à cocher. Un manquement trouvé ailleurs vaut
autant.

1. Le protocole d'appel en neuf étapes : l'ordre annoncé est-il l'ordre exécuté ? Ce qui est
   annoncé comme écrit avant une transition l'est-il vraiment avant ?
2. La machine à états : les transitions décrites sont-elles celles que le code produit ? Y
   a-t-il un état d'où l'on ne peut plus sortir, ou un chemin non décrit ?
3. La reprise après interruption : ce qui est annoncé comme retraité localement l'est-il, et
   ce qui est annoncé comme jamais rejoué automatiquement l'est-il jamais ?
4. Le verrou : tout ce qui modifie la collaboration est-il réellement sous verrou ?
5. La surface en ligne de commande : options, obligations, codes de sortie — conformes à ce
   qui est écrit ?
6. Les contrats d'échange : ce que le programme dit exiger des deux agents, ce que ses
   gabarits leur demandent réellement, et ce que son analyseur accepte réellement — les trois
   coïncident-ils ?
7. Les fichiers écrits sur disque : ceux annoncés sont-ils écrits, et rien d'autre ?
8. Les garanties de frontière d'effets et de portabilité : sont-elles tenues, ou seulement
   affirmées ?

CE QUE TU NE FAIS PAS

Tu ne proposes aucune fonctionnalité, aucun contrôle, aucune validation, aucun mécanisme
nouveau. Ce projet est né de l'échec d'un prédécesseur mort d'accumulation de contrôles tous
justifiés isolément. Sont exclus par décision et non négociables : exécution autonome, base de
données, worker, tâche planifiée, bail, budget ou quota interne, interface graphique,
dépendance de production.

Tu ne rouvres aucune décision déjà tranchée et écrite comme telle dans
conception/CONCEPTION_FINALE.md. Si une décision te paraît mauvaise, ce n'est pas une
observation : c'est une réserve, et elle va dans la dernière section.

Tu ne donnes pas d'avis de style, de nommage, de découpage ni de refactoring.

Tu ne comptes pas les lignes : la taille a été arbitrée.

FORME DE TA RÉPONSE

**1. Les observations.** Une liste numérotée, de la plus grave à la moins grave. Pour chaque
observation, quatre choses et pas une de plus :

- LA PROMESSE — la phrase, citée textuellement, avec son fichier et sa ligne.
- LE CODE — ce qu'il fait à la place, avec fichier et ligne.
- LE CAS — la situation concrète où l'écart se voit. Si tu ne peux pas en construire une, ce
  n'est pas une observation : c'est une réserve.
- GRAVITÉ — bloquant / majeur / mineur, et pourquoi.

**2. Les axes examinés.** Une ligne par axe, avec exactement l'une de ces trois mentions :
écart trouvé · aucun écart identifié · vérification incomplète (et pourquoi).

« Aucun écart identifié » est ce que tu écris quand tu as regardé sans rien trouver — c'est un
résultat, et il vaut mieux que six observations gonflées. Ne l'écris pas « axe vérifié » : une
lecture statique n'établit pas l'absence.

**3. Les réserves.** Une ligne chacune : ce que tu n'as pas pu vérifier · ce que tu crois vrai
sans pouvoir le montrer · les décisions qui te paraissent mauvaises mais que tu n'avais pas à
rouvrir · et tout comportement qui te paraît faux alors qu'aucune phrase écrite ne décrit ce
qu'il devrait être.
```

---

## Commande

```text
codex exec -m gpt-5.6-sol --sandbox read-only --skip-git-repo-check -
```

`cwd` = racine du dépôt, prompt sur `stdin`. `--sandbox read-only` : il lit et cherche, il n'écrit
rien.

---

## Relecture de la consigne par le contradicteur — dispositions

Chaque observation reçoit exactement une disposition écrite (`RULES.md`). Cinq observations, **cinq
retenues**.

| Observation | Disposition |
|---|---|
| « N'exécute rien » est ambigu : le relecteur doit pouvoir lire et chercher | **Retenue.** Reformulé en « n'exécute ni le programme ni les tests ; tu peux utiliser tes outils de lecture et de recherche ». La consigne d'origine l'aurait privé de `grep` — soit de son moyen de travail. |
| La règle sur les tests est inversée | **Retenue, et l'exception supprimée.** Elle n'a plus d'objet : le livrable ne contient aucune recommandation, et les tests sortent de cette passe. |
| Périmètre contradictoire : interdire de lire hors des chemins listés, puis renvoyer aux décisions de tout `conception/` | **Retenue.** Remplacé par `conception/CONCEPTION_FINALE.md`. Contradiction réelle de ma consigne. |
| Toutes les promesses n'ont pas la même force ; une source périmée ne doit pas devenir un défaut du code | **Retenue — la plus utile des cinq.** Ajout d'une hiérarchie (nom suggère · docstring engage · conception fait autorité) et de l'obligation de **signaler une contradiction plutôt que de choisir en silence celle qui permet un constat**. C'est le réflexe même qu'un relecteur a naturellement, et rien dans ma version ne l'en empêchait. |
| Le compte rendu de couverture n'a pas de place définie ; « axe vérifié » est trop fort pour une lecture statique | **Retenue.** Section 2 dédiée, à trois mentions fermées. La nuance de vocabulaire est juste : une lecture statique n'établit pas une absence. |

**Sur les tests, écartés de cette première passe.** Retenu. Contrepartie assumée : il ne pourra pas
dire si un écart est couvert, ni s'appuyer sur un test pour lever une ambiguïté. Aucune des deux n'est
nécessaire pour démontrer une divergence par lecture. **Seconde passe, plus tard et mieux ciblée :**
les écarts retenus sont-ils détectés par un test, et quelles garanties annoncées restent sans
couverture — plutôt qu'une revue générale des tests.

**Limite du périmètre, à garder en tête en lisant la réponse.** Cette consigne cherche les *promesses
rompues*, pas tous les défauts de fonctionnement : un problème réel peut lui échapper si aucune phrase
écrite ne décrit le comportement attendu. **Une réponse sans observation ne veut donc pas dire « rien
à corriger ».** La section 3 récupère partiellement ce manque — un comportement qui paraît faux sans
promesse écrite y va en réserve — mais partiellement seulement.

# RULES.md — Leçons apprises IAbinome

> Une règle par constat, avec son motif. **Sans doublon.**
> Les règles fondatrices, elles, sont dans `POURQUOI.md` et n'ont pas à être répétées ici.
> Dernière mise à jour : 2026-09-03

## Index

- [Périmètre](#périmètre)
- [Travail avec les agents](#travail-avec-les-agents)
- [Git](#git)
- [Outils et commandes](#outils-et-commandes)
- [Tests](#tests)
- [Conduite de projet](#conduite-de-projet)

---

## Périmètre

**Toute demande qui commence par « et si on ajoutait un petit contrôle pour… » est opposée au tableau des cinq interdits de `CLAUDE.md` avant d'être implémentée.**
*Motif : chaque contrôle de DialogForge était justifié isolément ; aucun n'a été mis en regard du total, qui a atteint 87 382 lignes.*

**Le livrable de la boucle est un document, jamais une exécution.**
*Motif : l'exécution autonome n'a jamais mené une implémentation au bout — 1 tâche sur 7 sur FloraPi, 1 sur 10 sur DialogForge.*

**Aucune dépendance de production.** Une dépendance nouvelle exige une nécessité démontrée et une décision humaine.
*Motif : DialogForge a tenu deux mois avec `dependencies = []`. C'est tenable.*

---

## Travail avec les agents

**Claude produit, Codex relit palier par palier — et réciproquement.**
*Motif : économie de tokens côté Claude, et la revue croisée rattrape ce que l'auteur ne voit pas.*
**Suspendue en étape 2 le 2026-09-03, décision du PO** : la conception a déjà été contredite cinq tours, et sa précision rend la relecture de code palier par palier peu rentable. **La règle reste valable pour la conception**, où elle a produit les huit remarques techniques toutes retenues. Réouverture si un palier révèle un défaut que la relecture aurait attrapé.

**Le contradicteur reçoit une consigne d'omission, pas une consigne de qualité :** « qu'est-ce qui a été écarté en silence ? »
*Motif : c'est la seule vérification sérieuse qu'une récolte n'a rien perdu ; relire son propre travail ne la remplace pas.*

**Mais la consigne d'omission doit être accompagnée du périmètre**, sinon le contradicteur remplit les manques en reconstruisant ce qu'on venait d'abandonner.
*Motif mesuré le 2026-09-03 : la passe 1 de Codex sur l'inventaire réintroduisait l'appareil de confinement de DialogForge. Sa V1.1, après précision du périmètre, s'est contredite elle-même sur six points.*

**Les indices que l'auteur a sur ses propres faiblesses ne sont donnés au contradicteur qu'après sa première réponse.**
*Motif : les donner d'emblée l'oriente vers ce que l'auteur sait déjà avoir raté, et l'éloigne de ce qu'il ignore — soit l'inverse de ce que la consigne cherche.*

**Chaque observation du contradicteur reçoit exactement une disposition écrite :** acceptée et intégrée · rejetée avec justification · différée avec condition · bloquante.
*Motif : repris de la préanalyse DialogForge, 31 observations, aucune sans disposition. C'est ce qui empêche de refermer une revue en laissant tomber ce qui dérange.*

**Le rôle et l'outil sont deux axes indépendants : A et B sont chacun Claude ou Codex, choisis au lancement.** Aucun fournisseur n'est nommé hors de son adaptateur.
*Motif : ajoutée en rattrapage à DialogForge, la permutation n'a jamais été complète — quotas et récupération de revue sont restés liés à un fournisseur (`recover_failed_review` ne cherchait que `*claude.txt`).*

**Le cycle ne dépend que des capacités présentes chez les deux outils ; ce qui est propre à l'un est un bonus, jamais un prérequis.**
*Motif : DialogForge a bâti sa reprise après quota sur l'erreur typée de Claude ; Codex ne la produit pas, et la reprise n'a jamais marché de ce côté.*

**Modèles par défaut, surchargeables : Opus 5 pour A (produit), Fable 5 pour B (critique).**
*Motif : la critique est l'endroit où la capacité paie. Sur le Lot 0, quatre revues de plan pour une seule exploitable ont coûté 41 % du budget mesuré.*

**Alléger les prompts, ne pas les durcir.**
*Motif : sur les modèles récents, des consignes trop prescriptives dégradent la qualité de sortie. Mesuré sur des tâches à douze critères d'acceptation imbriqués.*

**Ne jamais prescrire une commande qu'on n'a pas lancée, ni affirmer une impossibilité sans avoir cherché tous les chemins.**

---

## Git

**L'identité git est `schneider <schneider.jm@free.fr>`, déjà en configuration globale. Ne jamais passer `-c user.name=…` / `-c user.email=…`.**
*Motif : l'adresse fournie par le contexte de session est celle du compte Claude. Utilisée le 2026-09-02, elle a produit un commit à corriger par `--amend --reset-author`.*

**Jamais d'opération git destructive (`reset --hard`, `checkout --`, `clean`) avec des modifications en cours : `stash` d'abord.**
*Motif : deux à trois heures de travail perdues sur FloraPi de cette façon.*

**Messages de commit sans accents**, préfixes `docs:` `feat:` `fix:` `test:` `chore:`.
*Motif : cohérence avec le prédécesseur, dont l'historique entier suit cette convention.*

---

## Outils et commandes

**`ruff check .` et `mypy` avant tout commit.**

**Aucun appel fournisseur dans la suite de tests** — l'agent `fake` est obligatoire.
*Motif : une suite de tests qui appelle un modèle payant n'est plus une suite de tests.*

**Commandes de développement via l'outil Bash, avec des chemins relatifs.** Pas de PowerShell ad-hoc du type `& "C:\…\outil.exe"`.
*Motif : le PowerShell ad-hoc rate l'allowlist et déclenche une confirmation superflue.*

**Ne pas préfixer les commandes avec `cd` vers la racine du projet** — le répertoire courant y est déjà.

**Écrire un fichier de code par l'outil Write, jamais par un `heredoc` shell.** Un document long à guillemets multiples est mutilé au passage.
*Motif mesuré le 2026-09-03 : `cat > transport.py <<'EOF'` a rendu `unexpected EOF while looking for matching quote` sur 240 lignes valides.*

**Une branche écrite pour un OS non testé ne doit jamais casser l'outillage de l'OS testé.** Ne pas nommer un symbole absent de la plateforme de développement — `signal.SIGKILL`, `os.killpg`, `os.getpgid` — même dans du code qui n'y tournera pas.
*Motif : `typeshed` les déclare absents sous `win32`, donc `mypy --strict` échoue sur le poste. Contournement retenu dans `transport.py` : `os.kill(-pid, 9)`, où le PID négatif désigne le groupe.*

---

## Tests

**Un test qui vérifie une absence doit d'abord être prouvé capable de voir la présence.**
*Motif : le test de terminaison d'arbre affirme qu'un petit-fils ne dépose jamais sa marque. Sans avoir vérifié — hors suite — que cette marque apparaît quand on ne tue personne, le test passerait tout aussi bien parce que le petit-fils n'a jamais existé.*
*Second motif, mesuré le 2026-09-04 : le test de course du verrou affirme qu'un seul processus entre. Rejoué contre l'ancien verrou, il en montrait zéro au lieu de trois — chaque concurrent écrivait son résultat dans un `except` qui rattrapait aussi l'échec de **libération**, si bien qu'un entrant se déclarait refusé. La contre-épreuve n'a pas seulement validé le test : elle a corrigé le test.*

**Un outil peut signaler un échec de quota sur `stdout` avec un code de retour `0`.** Ne jamais bâtir un diagnostic sur l'hypothèse inverse.
*Motif mesuré le 2026-09-04 : la décision D-2 posait que « quota épuisé et modèle invalide rendent tous deux 1 chez les deux outils ». Faux pour outil 1 : sur un modèle sans crédits il rend son message sur `stdout` avec le code `0`. Le test du code de retour ne l'attrape pas, et le cycle finit en `CONTRACT_ERROR` — le diagnostic trompeur que D-2 disait éviter. La décision reste bonne, son motif était faux.*

**Ne jamais donner à un correctif un motif qu'on n'a pas mesuré.** Écrire « mesuré le … » engage.
*Motif : la normalisation CRLF a été justifiée par « une CLI d'agent écrit en mode texte, mesuré le 2026-09-03 ». La preuve venait en réalité du faux agent du projet. La caractérisation du même jour a montré que les deux vraies CLI rendent des `\n`. Le correctif reste bon comme tolérance ; c'est son motif qui était faux, et un motif faux se propage plus loin qu'un correctif inutile.*

**Un prompt qui exige un format doit porter le format — et la règle vaut pour *chaque* prompt, pas pour le premier.**
*Motif : §9 disait à B « retourne le JSON de revue v1 » sans jamais montrer le schéma — un nom interne au projet, indevinable. Chaque revue aurait échoué au contrat.*
*Second motif, mesuré le 2026-09-04 à la première mission réelle : la règle avait été appliquée au prompt de proposition, qui nommait `IABINOME:DOCUMENT` en toutes lettres, mais **pas** à ceux de révision et de finalisation, qui disaient « rends DOCUMENT ». L'agent a obéi littéralement. **Aucune mission ne pouvait aller au bout** — l'échec tombait au dernier appel, après avoir payé tous les autres. Corriger une règle à un endroit ne la corrige pas partout : il faut passer les autres au même crible.*

**Un prompt à faux agent ne teste pas un prompt.** Ce que le gabarit demande ne se vérifie qu'en lisant le gabarit.
*Motif mesuré le 2026-09-04 : 259 tests verts, dont plusieurs cycles complets, et pourtant deux prompts de A étaient inutilisables. `FakeAdapter` émet la bonne balise quoi qu'on lui demande — il ne lit pas le prompt. `tests/test_prompts.py` lit désormais les gabarits eux-mêmes.*

**La frontière d'effets d'un prompt porte sur l'écriture, jamais sur la lecture.**
*Motif mesuré le 2026-09-04 : « tu ne modifies aucun fichier et n'exécutes rien » a été lu par A comme une interdiction d'ouvrir son propre corpus — il a demandé à l'humain d'en coller le contenu. Le prompt annulait une promesse du produit, puisque l'adaptateur reçoit le dossier de collaboration comme `cwd` précisément pour qu'il y lise.*

**Le prompt d'un agent passe par `stdin`, jamais par la ligne de commande.**
*Motif mesuré le 2026-09-03 : `CreateProcess` plafonne à 32 767 caractères sous Windows, qu'un corpus réel dépasse ; et une CLI qui voit `DEVNULL` sur son entrée la lit comme un flux canalisé vide — la réponse est tombée de 673 octets conformes à 100 octets hors contrat.*

**Sous Windows, un PID terminé reste « vivant » pour `OpenProcess` tant qu'un handle du processus est ouvert.** Un test qui fabrique un PID mort doit laisser l'objet `Popen` sortir de portée avant de s'en servir.
*Motif mesuré le 2026-09-04 : dans la contre-épreuve du verrou, l'objet `Popen` gardé en variable locale faisait passer un processus attendu jusqu'à sa sortie pour un détenteur vivant — les trois concurrents refusaient le verrou pour la mauvaise raison, et la preuve semblait acquise alors que rien n'avait été testé.*

**Le compteur de ce qu'un test interdit se vérifie *avant* l'exception attendue, jamais à l'intérieur d'un `assertRaises`.**
*Motif mesuré le 2026-09-04 : le test de la porte d'état affirme qu'un second `run` ne paie aucun appel. Le compteur était vérifié dans le bloc `assertRaises` ; porte neutralisée, le test échouait sur « exception non levée » et **n'atteignait jamais le compteur** — il ne montrait pas l'appel payant qu'il cherche. Sorti du bloc, la contre-épreuve affiche `(2, 1) != (1, 0)` : A **et** B rappelés.*

**Déplacer une garantie déplace son point d'observation : vérifier que le test prouve encore ce qu'il dit.**
*Motif mesuré le 2026-09-04 : « `CALLING` publié avant `Popen` » se lisait dans `FakeAdapter.command()`. Le lot 2 ayant avancé `command()` **avant** la publication, ce point ne prouvait plus l'ordre — il aurait fallu changer l'assertion attendue, ce qui aurait rendu le test vide. La preuve est passée dans le **processus lancé**, qui relit `etat.json` depuis son `cwd`, et l'ancien point sert désormais l'autre garantie.*

**Une porte qui refuse un statut doit s'accompagner de la commande qui en sort — sinon le statut devient un cul-de-sac.**
*Motif : la porte d'état du lot 2 refuse `ERROR`. Sans N-01 — la table fermée d'incidents relançables — plus aucune commande ne sortait d'`ERROR`, et le correctif transformait un défaut en blocage. La règle vaut pour l'humain aussi : le message de refus nomme la commande.*

**Estimer un correctif en lignes, c'est se tromper d'un facteur 2 à 5 ; mesurer après coup, et en code effectif.**
*Motif mesuré le 2026-09-04 : lot 1 estimé 37 → 73 brutes ; lot 2 estimé 30 → **142** brutes. Mais 64 en code effectif — l'écart est à 65 % de la documentation. Comparer du brut à l'objectif de ~1 500 de `POURQUOI.md` fait paniquer sur une dérive qui n'existe pas ; comparer du code effectif à du code effectif donne le vrai chiffre.*

**`Path.glob` est insensible à la casse sous Windows : ne jamais s'en servir pour sélectionner par un champ.**
*Motif mesuré le 2026-09-04 : un test cherchait le dossier d'appel de B par `glob("*B*")`. Les dossiers s'appellent `NNNN-<role>-<uuid>`, et `*B*` a désigné celui de **A** dès que son UUID contenait un `b`. Découper le nom et comparer le champ est exact ; le glob ne l'est pas.*

**Sous Windows, résoudre l'exécutable avec `shutil.which()` avant `Popen`.**
*Motif : une entrée de PATH installée par npm est un script sans extension ; `CreateProcess` rend `WinError 2`. `shutil.which` rend le `.CMD` qui, lui, se lance.*

**Une décision différée porte sa condition de déclenchement, sinon elle est oubliée.**
*Motif : le palier 1 a écarté la normalisation CRLF→LF en écrivant « à statuer si un besoin réel apparaît ». Le besoin est apparu au palier 3 — une CLI Windows écrit en mode texte, et la balise de première ligne n'était jamais reconnue. La condition écrite est ce qui a fait rouvrir la question au lieu de la redécouvrir comme un bug.*

**Les tests d'un palier font remonter les défauts des paliers précédents — c'est une raison de les écrire contre du réel.**
*Motif : deux défauts du palier 1 (bloc JSON clôturé refusé, CRLF non normalisé) n'ont été vus qu'en faisant tourner le moteur du palier 3 contre de vrais sous-processus. Aucune relecture du code seul ne les avait montrés.*

**Un test de comportement de l'OS se fait contre un vrai sous-processus, pas contre un objet simulé.** L'objet simulé ne prouve que ce qu'on y a mis.
*Motif : `transport.py` existe pour tenir deux tubes concurrents, un délai dur et la terminaison d'un arbre. Un `FakeProcess` — que la spécification nommait — n'en démontrerait aucun. Un vrai sous-processus Python scripté n'est ni un appel fournisseur, ni du réseau : la règle est tenue, c'est le moyen qui change.*

**Un test de `cli.py` doit substituer `cli.ADAPTERS` par des `FakeAdapter` avant tout appel à `run`/`resume`.** Claude Code et Codex CLI sont tous deux sur le PATH de la machine de développement : un test qui invoque `cli.main(["run", …])` sans substitution appellerait un vrai fournisseur, silencieusement.
*Motif : mesuré au palier 4, 2026-09-04. `new`/`status` ne posent pas ce risque — ils ne sondent ni n'invoquent jamais d'adaptateur.*

**`mock.patch.object(module, "nom_importe", …)` échoue sous `mypy --strict`** (`--no-implicit-reexport` refuse l'accès à un attribut simplement importé). Patcher le module d'origine de l'attribut (`shutil.which`, pas `adaptateur.shutil.which`) le contourne sans rien désactiver.
*Motif : mesuré au palier 4, 2026-09-04, sur `tests/test_adapters.py`.*

---

## Conduite de projet

**Une décision actée peut être rouverte, mais jamais en silence :** signaler, tracer, faire re-décider.

**Une question marquée « à trancher avant de commencer » dans un document du projet se tranche dans ce document même**, avec son motif et sa date — pas seulement dans les notes de session.
*Motif : la question de périmètre de `RECOLTE.md` portait la mention « non tranché » depuis le 2026-09-02 ; laissée dans les notes, elle se serait reposée à chaque session.*

**Une source de récolte s'abandonne dès qu'elle ne rapporte plus rien de neuf — et l'abandon se note, avec le volume non lu.**
*Motif : c'est la seule façon de distinguer une source épuisée d'une source oubliée. Sans la note, le relecteur ne peut pas contredire.*

**Trancher les choix à défaut évident et avancer.** Réserver les questions aux vrais embranchements — métier, ergonomie, risque — que rien ne permet d'inférer.

**Métrique de garde : l'outil ne dépasse jamais le projet qu'il sert.**
*Motif : DialogForge pesait 87 382 lignes pour un FloraPi de 58 894. Voir `POURQUOI.md`.*

**Avant d'ajouter un garde-fou, vérifier qu'il compense un défaut encore réel.**
*Motif : l'échafaudage compense la faiblesse des modèles ; les modèles récents en demandent moins, pas plus.*

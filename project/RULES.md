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

**Un test de comportement de l'OS se fait contre un vrai sous-processus, pas contre un objet simulé.** L'objet simulé ne prouve que ce qu'on y a mis.
*Motif : `transport.py` existe pour tenir deux tubes concurrents, un délai dur et la terminaison d'un arbre. Un `FakeProcess` — que la spécification nommait — n'en démontrerait aucun. Un vrai sous-processus Python scripté n'est ni un appel fournisseur, ni du réseau : la règle est tenue, c'est le moyen qui change.*

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

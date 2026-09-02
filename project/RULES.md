# RULES.md — Leçons apprises IAbinome

> Une règle par constat, avec son motif. **Sans doublon.**
> Les règles fondatrices, elles, sont dans `POURQUOI.md` et n'ont pas à être répétées ici.
> Dernière mise à jour : 2026-09-03

## Index

- [Périmètre](#périmètre)
- [Travail avec les agents](#travail-avec-les-agents)
- [Git](#git)
- [Outils et commandes](#outils-et-commandes)
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

**Le contradicteur reçoit une consigne d'omission, pas une consigne de qualité :** « qu'est-ce qui a été écarté en silence ? »
*Motif : c'est la seule vérification sérieuse qu'une récolte n'a rien perdu ; relire son propre travail ne la remplace pas.*

**Modèles par rôle : Opus 5 pour A (produit), Fable 5 pour B (critique).**
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

---

## Conduite de projet

**Une décision actée peut être rouverte, mais jamais en silence :** signaler, tracer, faire re-décider.

**Trancher les choix à défaut évident et avancer.** Réserver les questions aux vrais embranchements — métier, ergonomie, risque — que rien ne permet d'inférer.

**Métrique de garde : l'outil ne dépasse jamais le projet qu'il sert.**
*Motif : DialogForge pesait 87 382 lignes pour un FloraPi de 58 894. Voir `POURQUOI.md`.*

**Avant d'ajouter un garde-fou, vérifier qu'il compense un défaut encore réel.**
*Motif : l'échafaudage compense la faiblesse des modèles ; les modèles récents en demandent moins, pas plus.*

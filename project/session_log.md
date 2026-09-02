# session_log.md — Journal des sessions IAbinome

> Une entrée par session de travail.
> Format : date · travail accompli · commits · décisions notables.

---

## 2026-09-02 → 09-03 (Claude) — Fondation du projet

Session menée depuis `C:\Projets\Florapy_V2`, à la suite de l'audit du refactoring DialogForge.

### Ce qui a été fait

Audit de conformité du Lot 0 de DialogForge par rapport à son plan de marche, puis analyse stratégique de l'opportunité de poursuivre. Les mesures ont conduit à geler le refactoring et à fonder ce projet.

**Mesures décisives :**

- DialogForge : 87 382 lignes (49 568 `src/` + 37 814 tests), 78 modules, 242 commits, 7 semaines. FloraPi, le projet servi : 58 894 lignes. **Rapport 1,5.**
- Répartition interne : **7 676 lignes** de boucle A/B contre **26 997 lignes** d'appareil d'autonomie.
- Usage réel sur FloraPi depuis le 5 août : **7 conceptions terminées sur 9**, mais **1 seule implémentation durable tentée, bloquée à 1 tâche sur 7**.
- Lot 0 de DialogForge : bloqué à 1 tâche sur 10, ~7 M tokens consommés, 4 interventions humaines en 3 heures.
- Le refactoring prévoyait **15 lots** (0 à 14).

**Défauts techniques relevés au passage**, consignés dans `ARRET_REFACTORING.md` : coût Codex jamais remonté et entrée Claude jamais comptée ; `retry_at` de quota non parsable par `scheduling.parse_resume_time`, d'où un repli de 15 min et des réveils inutiles ; une tâche sans modification ne peut pas se clore seule.

### Décisions

1. **Refactoring DialogForge gelé** — décision datée, pas un abandon silencieux. DialogForge reste utilisé **en conception seule** sur FloraPi.
2. Mission d'implémentation `e35cfcf1-…` **mise en pause** : elle aurait redémarré seule à 01:01 au retour du quota Codex.
3. **Fondation d'IAbinome** — successeur allégé, ~1 500 lignes, deux agents IA en CLI, A produit / B critique, l'humain arbitre. Nom retenu après arbitrage : `BinomeIA` d'abord choisi, puis inversé en **`IAbinome`** par le PO.
4. **Cinq interdits de périmètre** figés dans `CLAUDE.md` : pas d'exécution autonome, pas de base, pas de worker/bail/tâche planifiée, pas de budget interne, pas de GUI.
5. **Une étape 0 de récolte est insérée avant la spécification** : capitaliser deux mois d'apprentissage en un inventaire d'une ligne par leçon, cinq destinations dont une colonne « Écarté » obligatoire, plafonné à ~200 lignes.
6. Modèles par rôle : **Opus 5 pour A, Fable 5 pour B**.
7. Remote git : **reporté**.

### Commits

**IAbinome** — `78e09e8` fondation (amendé pour corriger l'identité git) · `b513a8d` étape de récolte · commit des règles de travail.
**DialogForge** — `4903927` gel du refactoring et préparation de l'extraction · `01a9e03` nom du successeur et pointeur vers son dépôt.

### À retenir

L'erreur d'identité git (adresse du compte Claude au lieu de `schneider.jm@free.fr`) a nécessité un `--amend --reset-author`. Règle consignée dans `RULES.md`.

# Départ — construire IAbinome

> Lire `POURQUOI.md` d'abord. Ce fichier-ci dit **quoi faire**, avec les chemins exacts.
> Préparé le 2026-09-02. Rien n'a encore été écrit.

## Ce fichier est l'étape 1 — pas l'étape en cours

**L'étape en cours est la récolte : `RECOLTE.md`.** Elle passe d'abord, et la spécification ci-dessous ne prend en entrée que la colonne **Code** de l'inventaire qu'elle produit.

Rien à coder tant que la spécification n'est pas arbitrée.

## Ce qu'on reprend de DialogForge — fichiers exacts

Le capital de sept semaines n'est pas dans l'architecture. Il tient en quelques centaines de lignes de prompts et de validation. Tout est sous `C:\Projets\DialogForge\src\dialogforge\`, **en lecture seule**.

| Fichier | Quoi | Lignes |
|---|---|---|
| `orchestrator.py:681-760` | `_proposal_prompt`, `_review_prompt`, `_revision_prompt`, `_final_prompt` — **toute la boucle A/B tient là** | ~80 |
| `framing.py:210-290` | `_opening_prompt`, `_follow_up_prompt`, `_finalization_prompt` — le cadrage de la demande | ~80 |
| `contracts.py` | validation des réponses structurées des agents — à dégraisser fortement | 857 |
| `agents/base.py` | contrat d'un agent CLI | 192 |
| `agents/subprocess_agent.py` | lancement d'un CLI en sous-processus — beaucoup à retirer | 1109 |
| `agents/claude.py` · `codex.py` · `fake.py` | les trois adaptateurs utiles ; `fake` sert aux tests sans fournisseur | 1309 |
| `workflow.py` · `models.py` | états et transitions de la boucle | 422 |
| `storage.py` | écriture atomique et disposition des dossiers de collaboration | 505 |

## Ce qu'on ne reprend pas

Les **26 997 lignes** d'appareil d'autonomie, nommées ici pour qu'aucune ne revienne par nostalgie :
`missions.py`, `worker.py`, `leases`, `reservations`, `budget_axes`, `admission`, `adaptive`, `remedy_models`, `incidents`, `resilience`, `chaos`, `sandbox_*`, `attestation_report`, `executable_seal`, `confinement`, `workspaces`, `git_ops`, `harness`, `execution`, `verification_policy`, `project_*`, `reconstruction`, `offline_recovery`, `legacy_migration`, `interventions`, `evidence`, `correlation`, `scheduling`, `role_gate`.

Plus : `gui.py`, `desktop.py`, `implementation.py` (5 260 lignes à elle seule), `context_packs`, `consignes`, `context_delta`, `agents/codex_sandbox.py`, `agents/cli_version.py`.

## Le contrat visé

```
demande.md  →  A produit    →  echanges/01_proposition_A.md
               B critique   →  echanges/02_critique_B.md
               A révise     →  echanges/03_revision_1_A.md
               … jusqu'à N révisions max (défaut N = 2)
               A finalise   →  livrables/version_finale.md
```

Un dossier par collaboration. Un `etat.json` lisible à l'œil nu. Reprise = relire l'état, repartir de la dernière étape. Interruption = fermer le terminal.

## Livrable de l'étape 1

1. ce qui reste et ce qui tombe, fichier par fichier ;
2. la disposition des fichiers du projet ;
3. la surface CLI (quelles commandes, quels arguments) ;
4. les gabarits de prompts repris, **allégés** — voir règle 4 de `POURQUOI.md` ;
5. la liste des tests, tous avec l'agent `fake`.

Puis **arbitrage humain**. Ensuite seulement, l'implémentation.

## Décisions déjà prises

- Boucle A/B seule, conception seule ; le livrable est un document.
- Fichiers sur disque, aucune base.
- Révisions bornées, défaut 2, arbitrage humain en fin de boucle.
- Zéro dépendance de production ; agent `fake` obligatoire dans les tests.
- Opus 5 pour A, Fable 5 pour B.

## Décisions à prendre à l'étape 1

- **Garder ou non le cadrage automatique** (`framing.py`) : utile, mais c'est un appel fournisseur de plus avant même que la boucle démarre. Trancher explicitement.
- Jusqu'où dégraisser `contracts.py` : la validation des réponses est ce qui évite de traiter de la prose comme une décision. Trouver le minimum qui tient.
- Format exact d'`etat.json` : il doit rester lisible sans outil.

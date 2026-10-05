# Reprise après épuisement d'une période fournisseur — enquête préalable

> 2026-10-04. Décision du PO : couvrir le cadrage, la recherche, la conception et le
> Runner de code, tant que DialogForge reste ouvert. Ce document constate les signaux
> disponibles avant toute modification du code d'exécution. Aucun appel destiné à
> épuiser un quota n'a été lancé pour cette enquête.

## Ce qui est établi

| Outil | Signal | Niveau de preuve et limite |
| --- | --- | --- |
| Claude Code | Code de sortie `1` pour quota ou modèle invalide ; le quota est écrit sur `stdout`. | Mesure locale du projet, `conception/CARACTERISATION_CLI.md` §5. Le code seul ne classe pas l'échec. |
| Claude Code | `You've hit your session limit · resets 8:50pm (Europe/Paris)` sur `stdout`, `stderr` vide, code de sortie `1`, incident actuel `CLI_FAILED`. | **Trace réelle de DialogForge V2**, `C:\Projets\DialogForge_missions\Peinture_application_2\appels\0005-A-4760706460334ab78def62c7ec51868a\` : `stdout.txt`, `resultat.json`, `incident.json`, datés du 2026-10-01. C'est le profil documentaire ; le Runner WSL reste à qualifier séparément. |
| Claude Code | JSON d'erreur avec `is_error: true`, parfois `api_error_status: 429` ; textes « You've hit your session limit - resets 11:20pm (Europe/Paris) », « Claude AI usage limit reached\|<epoch> », ou `error.message` imbriqué. | **Fixtures simulées** de `C:\Projets\DialogForge\tests\test_agents.py` (tests autour des lignes 920–1014), prises en charge par l'ancien adaptateur. Elles ne garantissent pas la forme actuelle de la CLI. |
| Claude Code | Message visible « You've hit your session limit · resets 5:50pm ». | Compte rendu d'un utilisateur dans le dépôt de l'outil, [issue anthropics/claude-code #80253](https://github.com/anthropics/claude-code/issues/80253) ; autre forme de ponctuation. Pas une preuve du code de sortie de notre profil `-p`. |
| Codex CLI | Code de sortie non nul sur quota ; message sur `stderr`. | Mesure locale du projet, `conception/CARACTERISATION_CLI.md` §5. Le code seul ne classe pas l'échec. |
| Codex CLI | Heure de type `Sep 3rd, 2026 1:01 AM`. | Constat réel conservé dans `C:\Projets\DialogForge\ARRET_REFACTORING.md` §« Trois constats » ; l'ancien `parse_resume_time` ne savait pas l'interpréter et lançait des essais toutes les 15 minutes. Le message complet et le code de sortie de cet appel n'y sont pas consignés. |
| Codex CLI | Message « You've hit your usage limit. … try again at 4:10 PM ». | Compte rendu sur le dépôt de l'outil, [issue openai/codex #28419](https://github.com/openai/codex/issues/28419), version 0.140.0 ; format différent de la date complète observée dans l'ancien DialogForge. Pas une preuve de la sortie exacte de `codex exec` avec le profil actuel. |

Le prédécesseur classe les échecs textuels à la frontière des adaptateurs dans
`src/dialogforge/agents/subprocess_agent.py`, lit aussi l'enveloppe JSON de Claude dans
`src/dialogforge/agents/claude.py`, transmet `retry_at` et sait attendre une heure locale ou
horodatée dans `scheduling.py`. Il traite `HTTP 429` comme une surcharge distincte dans
sa classification générique, mais l'enveloppe Claude `api_error_status: 429` comme un
quota. Son repli de 15 minutes si l'heure manque ou ne se lit pas est précisément le
défaut documenté dans `ARRET_REFACTORING.md` ; ne pas le recopier par défaut.

## Ce qui ne peut pas servir de preuve unique

- Code de sortie `1` : quota et erreur de configuration ou de modèle ont été
  observés avec ce même code.
- HTTP `429` : la [documentation officielle OpenAI sur les erreurs](https://developers.openai.com/api/docs/guides/error-codes)
  distingue limite de débit, crédits insuffisants et limites de dépense ou d'usage ;
  la [documentation Anthropic sur les erreurs](https://docs.anthropic.com/en/api/errors)
  donne aussi plusieurs causes possibles pour `429`. Ces codes API ne sont pas
  nécessairement exposés tels quels par les deux CLI.
- « rate limit », « too many requests », `ECONNRESET`, `401` : aucune de ces formes
  n'annonce à elle seule la fin de la période de jetons ni son heure de retour.
- Une heure dans la réponse de l'agent ou dans un texte de mission : seule une
  erreur émise par l'outil lors d'un appel refusé peut être interprétée.

## Contrat à qualifier avant le code

1. Pour chaque outil et chaque mode utilisé (`-p` Claude documentaire/cadrage,
   `codex exec` documentaire/cadrage, `-p` Claude sous WSL pour le Runner), relever
   une trace réelle **déjà disponible** si possible : version, arguments hors secrets,
   code de sortie, `stdout`, `stderr`, champs structurés et heure annoncée. Masquer
   identifiants, jetons, chemins personnels et contenu de mission dans la preuve.
   Une trace Claude documentaire V2 est déjà relevée ci-dessus. La version
   Claude accessible dans cette enquête est 2.1.289 ; `codex` n'est pas
   accessible depuis le shell Windows courant. Ne pas déclencher exprès un
   épuisement de quota.
2. Construire ensuite les fixtures de classification à partir de ces preuves :
   période épuisée avec heure, période épuisée sans heure, débit temporaire,
   crédit ou dépense bloquée, modèle invalide, authentification, réseau, réponse
   normale contenant le mot « quota ». Garder le texte brut et le code de sortie.
3. Normaliser une heure exploitable en instant avec fuseau, y compris date anglaise
   avec ordinal (`3rd`), `HH:MM AM/PM`, mention `Europe/Paris`, horodatage Unix,
   passage de minuit et changement d'heure. La date de réception de l'erreur sert
   à résoudre une heure seule ; ne pas décaler de 24 heures une heure qui vient de
   passer de quelques secondes.
4. Pour un refus de période confirmé et daté, attendre dans le lancement en cours
   jusqu'à l'heure annoncée plus **deux minutes** (valeur proposée dans la plage
   demandée de une à deux minutes), puis poursuivre la même étape. L'attente doit
   répondre à « pause » et « arrêter », sans worker ou tâche planifiée après
   fermeture. Dans le Runner, elle suspend la durée de travail du lancement :
   une réinitialisation plusieurs heures plus tard reste donc utilisable.
   Une nouvelle période refusée peut annoncer une nouvelle heure ;
   aucune répétition rapide sans nouvel horaire fiable.
5. Conserver la distinction « appel peut-être payé ». Le cadrage reprend le tour
   dans sa session ouverte ; A/B trace le nouvel appel lié au refus précédent ;
   le Runner garde clone, commits et paquet éventuel. Un incident autre que le
   refus de période garde la conduite actuelle.

## Point encore ouvert

La forme exacte d'une erreur de période sur **Codex `exec` non interactif** avec le
profil de DialogForge V2 n'est pas établie par les sources disponibles ici. La
documentation officielle OpenAI décrit les erreurs API, mais ne garantit pas le
texte, le flux ni le code de sortie de cette CLI. La qualification de cette forme
est une condition préalable à l'activation de la reprise Codex.

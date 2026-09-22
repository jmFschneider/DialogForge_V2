# Reprise du diagnostic Codex 3.1

## Analyse de la proposition de reprise

### Ce que Claude propose, en langage simple

Claude propose cinq étapes :

1. corriger une formulation documentaire devenue inexacte ;
2. déterminer pourquoi Codex ne peut exécuter aucune commande de lecture ;
3. essayer une politique Codex limitée au seul dossier de travail ;
4. si cet essai réussit, modifier DialogForge et lui ajouter un contrôle préalable automatique ;
5. arrêter avant tout nouvel appel payant et demander l'autorisation du PO.

La prudence sur les appels fournisseur, les règles personnelles et les accès en écriture est justifiée. En revanche,
le prompt mélange une investigation encore ouverte avec une architecture déjà très détaillée.

### Ce qui est établi

- Le protocole réel prouve que Codex n'a pas pu lire le corpus avec la commande actuelle.
- Les commandes ont été rejetées avant leur exécution par la politique de la CLI.
- Charger les règles personnelles de cette machine n'est pas une correction portable : elles autorisent notamment un
  préfixe PowerShell très large.
- Le profil intégré `:read-only` ne convient pas à lui seul : il a lu le corpus, mais aussi le canari extérieur.
- Les profils de permissions récents ne se combinent pas avec l'ancien `--sandbox read-only` : quand `--sandbox` est
  présent, il prend la priorité. Ce point est confirmé par la documentation officielle Codex.

### Ce qui n'est pas encore établi

- Qu'un profil personnalisé puisse être fourni proprement à `codex exec` sans charger la configuration personnelle.
- Qu'un tel profil permette aux commandes demandées par le modèle de s'exécuter avec `approval: never` et
  `--ignore-rules`.
- Que le même profil lise le corpus, refuse le canari et refuse toute écriture dans un appel réel.
- Qu'un prévol exécuté avant chaque `run` soit nécessaire, suffisant et proportionné à la taille du produit.

`codex sandbox` qualifie la frontière du bac à sable, mais ne prouve pas à lui seul le comportement complet d'un appel
`codex exec` piloté par un modèle. La dernière preuve intégrée pourra donc nécessiter un unique appel fournisseur,
autorisé séparément par le PO.

### Points à corriger dans la proposition initiale

1. **Ne pas considérer l'architecture du prévol comme déjà validée.** Le point d'accroche générique, le lanceur injecté
   et les trois témoins sont des propositions techniques. Le PO n'a pas à les valider avant de connaître leur coût et
   leur utilité réelle.
2. **Ne pas implémenter pendant la session de qualification.** Une session courte doit d'abord produire une matrice
   claire de ce qui est prouvé, possible, impossible ou encore non observable.
3. **Ne pas exiger une preuve impossible sans quota.** Les commandes locales prouvent le profil de fichiers et les
   règles d'exécution séparément ; elles ne remplacent pas forcément l'essai intégré du modèle.
4. **Ne pas dire qu'aucune collaboration ne peut être créée au `run`.** Elle existe déjà depuis `new`. Le prévol peut
   garantir qu'il ne lance aucun fournisseur et ne modifie pas l'état de la collaboration en cas d'échec.
5. **Ne pas exiger un message de refus prédéterminé.** Le critère est que le contenu extérieur ne soit pas obtenu. Le
   message exact observé doit être conservé comme preuve, mais son texte peut varier avec la version de la CLI.
6. **Ne mettre `RULES.md` à jour que si une règle durable et nouvelle est réellement découverte.** Le journal PWF doit
   être mis à jour ; multiplier les règles par automatisme reproduirait la complexité que ce projet cherche à éviter.
7. **Résoudre une incohérence du plan avant de conclure sur l'état.** Le bloc REPRISE indique correctement que le
   protocole 3.1 a été exécuté, tandis qu'un ancien paragraphe de la phase 3 dit encore « pas encore lancé ». Le bloc
   REPRISE et les résultats mesurés sont l'état courant ; la mention ancienne doit être traitée comme périmée.

## Prompt recommandé pour la nouvelle session Claude

Copier uniquement le bloc suivant comme premier message de la nouvelle session :

```text
Scope de cette session : lot 3.1, qualification sans quota du défaut de lecture du corpus par Codex. Cette session
n'autorise ni modification du code de production, ni nouvel appel fournisseur, ni commit.

Travaille depuis C:\Projets\DialogForge_2 et résous d'abord le plan PWF actif. Lis le bloc REPRISE, le Next Step,
findings.md, progress.md, POURQUOI.md et les règles utiles. Examine `git status` et le diff avant toute action : les huit
fichiers actuellement modifiés appartiennent au travail en cours et doivent être conservés.

Le bloc REPRISE contient des choix techniques détaillés concernant un futur prévol. Comme le PO indique ne pas encore
avoir compris ni validé cette architecture, traite ces choix comme des propositions à évaluer, pas comme une
autorisation d'implémenter.

Objectif unique de cette session : déterminer la plus petite solution qui permettrait à Codex de lire le dossier de
travail neutre sans pouvoir lire ailleurs ni écrire, tout en restant indépendant des règles et de la configuration
personnelles.

Contraintes :
- aucun `codex exec`, `claude -p`, cycle réel ou autre appel fournisseur ;
- ne retire pas `--ignore-rules` et ne charge pas les règles personnelles ;
- ne modifie pas la configuration globale ni le CODEX_HOME réel ;
- n'utilise ni `workspace-write` ni `danger-full-access` ;
- ne copie, ne déplace et ne journalise aucun secret ;
- conserve `--ignore-user-config`, `--ignore-rules`, `--ephemeral`, la séparation des environnements, le contrôle de
  `web_search`, l'effort et `context-only` comme exigences du futur correctif ;
- les essais locaux autorisés sont `codex --help`, `codex sandbox`, `codex execpolicy check` et des fichiers temporaires
  sans secret, supprimés dans un `finally`.

Travail demandé :

1. Corrige seulement la formulation documentaire « le cycle l'a détecté, le produit non » lorsqu'elle subsiste. La
   formulation attendue est : « Le contrôle préalable de l'adaptateur n'a pas détecté l'incapacité de lecture ; le
   workflow l'a détectée ensuite grâce au reviewer B. » Corrige aussi la mention historique « protocole pas encore
   lancé » qui contredit le bloc REPRISE et le tableau de résultats, sans réécrire le reste de l'historique.
2. Reproduis les constats locaux sans quota au lieu de les supposer : décision des règles personnelles avec
   `execpolicy check`, lecture du corpus et du canari avec le profil intégré `:read-only`.
3. Caractérise séparément quatre mécanismes : politique d'exécution, permissions de fichiers, approbations et recherche
   web. Confirme notamment que `--sandbox read-only` éclipse les profils de permissions personnalisés s'il est présent.
4. Construis uniquement un prototype jetable de profil borné, appartenant au produit en principe mais non intégré au
   produit. Il doit viser : `:root` refusé, chemins d'exécution minimaux lisibles, racine de travail lisible, aucune
   écriture, réseau des commandes coupé.
5. Teste ce prototype sans fournisseur avec trois preuves distinctes : corpus lisible, canari extérieur illisible,
   création ou modification impossible. Vérifie que la configuration et les règles personnelles ne participent pas au
   résultat et que la configuration globale reste inchangée.
6. Si ces trois preuves ne peuvent pas être obtenues, arrête l'investigation. Explique précisément la limite et présente
   le repli par injection bornée du corpus dans le prompt, sans l'implémenter.
7. Si elles sont obtenues, n'implémente encore rien. Présente au PO :
   - la cause la mieux étayée du rejet initial ;
   - la commande et la configuration exactes du prototype ;
   - ce que les essais sans quota prouvent et ne prouvent pas ;
   - la commande proposée pour un unique appel Codex intégré, à ne lancer qu'après autorisation ;
   - deux options de suite : intégrer le profil, ou injecter le corpus dans le prompt ;
   - pour chaque option, estimation des lignes de production et de tests ajoutées, risques, limites, et ce qui serait
     retiré ou simplifié en échange conformément à POURQUOI.md.

Ne crée pas encore de point d'accroche générique, de prévol automatique ou de nouvel incident. Leur nécessité sera
décidée par le PO après cette qualification. Mets à jour task_plan.md et progress.md avec les résultats factuels de la
session. Ne modifie RULES.md que si une règle durable, nouvelle et non redondante a réellement été découverte.

Arrête-toi ensuite et attends la décision du PO.
```

## Décision attendue après cette session

Le PO ne devra alors arbitrer qu'entre trois choix compréhensibles :

1. **Profil borné faisable** : autoriser un unique appel réel, puis décider de son intégration.
2. **Profil borné impossible ou instable** : choisir ou refuser l'injection bornée du corpus dans le prompt.
3. **Coût disproportionné** : maintenir Claude pour les rôles qui doivent lire un corpus et documenter temporairement
   cette limite, sans ajouter de nouveau sous-système.

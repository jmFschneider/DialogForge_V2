# Amendement du PO — 2026-09-26

La contrainte de taille du lot développement assisté évolue : le PO autorise un ajout net
inférieur à 1 000 lignes de code effectif dans src/, avec une cible de 500 lignes au maximum,
par rapport aux 5 618 lignes avant ce lot. La marge précédente de 164 lignes ne bloque donc
plus le lot. Les autres contraintes et non-objectifs restent applicables.

Le PO délègue à Codex l'acceptation de la conception si elle respecte ces contraintes, puis
l'implémentation avec tests et relecture par Claude. Cette délégation ne transforme pas
DialogForge en moteur d'implémentation : l'agent de développement extérieur exécute le travail.

Produire une conception complète directement implémentable, en chiffrant le coût et le travail
humain retiré. La conception doit avoir été examinée par B avant son acceptation déléguée.

Le PO désigne DialogForge_2 lui-même comme projet de l'essai réel. Choisir une modification
limitée et réversible, dont les résultats de tests sont rattachés à la version exacte revue.

## Points à résoudre avant acceptation (lecture de la première proposition par Codex)

- Le cycle A/B et ses reprises ne doivent pas être réécrits. La première proposition décrit
  sept nouvelles sous-commandes, un nouveau contrat de revue et un A extérieur sans indiquer
  le raccordement effectif au moteur existant. Préciser ce raccordement et son coût réel ;
  privilégier les collaborations documentaires ordinaires si elles suffisent, en distinguant
  le développeur extérieur de l'auteur documentaire du rapport de revue.
- Le dossier courant de B doit rester un dossier jetable contenant seulement le corpus figé,
  comme le prévoit le produit existant ; pas la collaboration avec ses journaux privés.
- Les commandes qui doivent relire le dépôt doivent pouvoir le retrouver explicitement :
  ne pas exclure son chemin de la persistance puis omettre --repo dans ces commandes.
- Une revue déjà produite ne doit pas bénéficier rétroactivement de tests ajoutés ensuite.
  Figer ensemble code et résultats fournis à chaque revue, ou invalider explicitement cette revue.
- Préciser les limites de capture Git (fichiers ignorés, sous-modules, binaires, filtres) et
  ne pas annoncer une couverture complète de ce qui n'est pas dans le paquet.

## Orientation retenue par Codex dans le cadre de la délégation

La révision 1 crée encore un état durable séparé et décrit un nouveau protocole d'appel de B.
Ce choix n'est pas accepté : la délégation vise un lot simple réalisable, pas une seconde
orchestration avec ses reprises. Réviser vers des paquets utilisables comme corpus de
collaborations ordinaires : A produit le rapport documentaire sur le code extérieur, B le
critique en consultant le même code figé, A répond aux constats et B relit, via le cycle existant.
Le développeur extérieur demeure seul auteur du code. La décision accepte un rapport portant
sur une révision identifiée ; elle ne signifie ni fusion ni déploiement.

Une nouvelle version du code ou de ses validations produit un nouveau paquet et une nouvelle
collaboration. Préciser comment transmettre la revue et les réponses précédentes pour ne pas
perdre les constats, sans injecter de faux échanges ni modifier les états du moteur. Une
correction purement documentaire peut utiliser decide --correct dans le cycle existant.
Limiter les ajouts aux fonctions utiles d'export, de paquet et de vérification de rattachement,
avec les commandes new/run/show/decide/resume existantes pour toute l'orchestration.

La capture de deux commits seulement est acceptable si ses limites sont explicites. Son diff
doit provenir des objets Git, les fichiers retenus aussi. Pour l'identité, hacher des données
stables (ne pas inclure la date de manifeste de corpus.build).

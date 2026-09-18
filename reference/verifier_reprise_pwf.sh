#!/bin/sh
# Qualification de la reprise PWF — lot 0.3, dernier point avant J0.
#
# A lancer depuis Git Bash, a la racine du depot, APRES avoir ouvert puis
# ferme une nouvelle session de l'hote de developpement.
#
#   sh reference/verifier_reprise_pwf.sh
#
# Rend 0 si tout est vert, 1 sinon. Aucun appel fournisseur, aucun reseau.

PLAN_ATTENDU="2026-09-18-dialogforge-v2"
SKILL="$HOME/.claude/skills/planning-with-files"
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/pwf-turn"
echec=0

dire() { printf '%-58s %s\n' "$1" "$2"; }
vert() { dire "$1" "OK"; }
rouge() { dire "$1" "ECHEC  -> $2"; echec=1; }

echo "=== Qualification de la reprise PWF ==="
echo

# 1. Le skill est installe, a la version consignee.
version=$(sed -n 's/^  version: "\(.*\)"/\1/p' "$SKILL/SKILL.md" 2>/dev/null)
if [ "$version" = "3.20.1" ]; then
    vert "1. Skill installe en version 3.20.1"
else
    rouge "1. Skill installe en version 3.20.1" "version lue : '${version:-absente}'"
fi

# 2. Resolution nominale : le bon plan, depuis la racine du depot.
resolu=$(sh "$SKILL/scripts/resolve-plan-dir.sh" 2>/dev/null)
case "$resolu" in
    */.planning/"$PLAN_ATTENDU") vert "2. Resolution nominale -> $PLAN_ATTENDU" ;;
    "") rouge "2. Resolution nominale" "sortie vide : plan ambigu ou absent" ;;
    *) rouge "2. Resolution nominale" "plan inattendu : $resolu" ;;
esac

# 3. Selection erronee : ne doit JAMAIS recuperer un autre plan.
#    Rappel : l'amont rend une sortie vide AVEC un code de retour zero.
errone=$(PLAN_ID=plan-qui-nexiste-pas sh "$SKILL/scripts/resolve-plan-dir.sh" 2>/dev/null)
if [ -z "$errone" ]; then
    vert "3. Selection erronee -> sortie vide, aucun repli"
else
    rouge "3. Selection erronee" "un plan a ete recupere : $errone"
fi

# 4. La prochaine etape lue est bien celle du plan selectionne.
suivant=$(sed -n '/^## Next Step/,/^## /p' "$resolu/task_plan.md" 2>/dev/null | sed '1d;$d' | tr -d '\r')
if [ -n "$(printf '%s' "$suivant" | tr -d '[:space:]')" ]; then
    vert "4. '## Next Step' non vide dans le plan resolu"
    printf '   prochaine etape lue :\n'
    printf '%s\n' "$suivant" | sed 's/^/   | /'
else
    rouge "4. '## Next Step' non vide" "section absente ou vide"
fi

# 5. Preuve que les hooks se sont declenches EN SESSION.
#    Le marqueur de tour est nomme par une cle de 64 caracteres hexadecimaux,
#    derivee de l'identite de session transmise par l'hote sur stdin. Un appel
#    manuel du script n'en produit pas. Les marqueurs de 16 caracteres sont un
#    residu de la suite de tests de PWF, anterieur a cette installation : ils ne
#    comptent pas.
if [ -d "$CACHE" ]; then
    preuves=$(find "$CACHE" -maxdepth 1 -type f 2>/dev/null \
        | sed 's#.*/##' \
        | grep -c '^[0-9a-f]\{64\}$')
else
    preuves=0
fi
if [ "$preuves" -gt 0 ]; then
    vert "5. Hooks declenches en session ($preuves marqueur(s) de tour)"
else
    rouge "5. Hooks declenches en session" \
        "aucun marqueur de 64 hex dans $CACHE : le skill n'a pas ete invoque"
fi

echo
if [ "$echec" -eq 0 ]; then
    echo "TOUT EST VERT — le dernier point du lot 0.3 est tenu, J0 peut etre consigne."
else
    echo "AU MOINS UN POINT EST ROUGE — J0 n'est pas atteint. Ne pas ouvrir le lot 1."
fi
exit "$echec"

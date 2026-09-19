#!/bin/sh
# Qualification de la reprise PWF — lot 0.3, dernier point avant J0.
#
#   sh reference/verifier_reprise_pwf.sh
#
# Le critere d'acceptation est l'INJECTION AUTOMATIQUE du plan par les hooks,
# constatee dans les traces de la session d'essai. Il n'est pas negocie a la
# baisse : retrouver la bonne etape en lisant le plan soi-meme ne suffit pas.
#
# Le marqueur de cache ~/.cache/pwf-turn N'EST PAS un critere : il n'est ecrit
# que par un PostToolUse d'ecriture, puis efface au UserPromptSubmit suivant.
# Son absence ne prouve rien, et sa presence pourrait venir d'une autre session.

PLAN_ATTENDU="2026-09-18-dialogforge-v2"
SKILL="$HOME/.claude/skills/planning-with-files"
echec=0

dire() { printf '%-58s %s\n' "$1" "$2"; }
vert() { dire "$1" "OK"; }
rouge() { dire "$1" "ECHEC  -> $2"; echec=1; }

echo "=== Qualification de la reprise PWF ==="
echo

version=$(sed -n 's/^  version: "\(.*\)"/\1/p' "$SKILL/SKILL.md" 2>/dev/null)
if [ "$version" = "3.20.1" ]; then
    vert "1. Skill installe en version 3.20.1"
else
    rouge "1. Skill installe en version 3.20.1" "version lue : '${version:-absente}'"
fi

resolu=$(sh "$SKILL/scripts/resolve-plan-dir.sh" 2>/dev/null)
case "$resolu" in
    */.planning/"$PLAN_ATTENDU") vert "2. Resolution nominale -> $PLAN_ATTENDU" ;;
    "") rouge "2. Resolution nominale" "sortie vide : plan ambigu ou absent" ;;
    *) rouge "2. Resolution nominale" "plan inattendu : $resolu" ;;
esac

errone=$(PLAN_ID=plan-qui-nexiste-pas sh "$SKILL/scripts/resolve-plan-dir.sh" 2>/dev/null)
if [ -z "$errone" ]; then
    vert "3. Selection erronee -> sortie vide, aucun repli"
else
    rouge "3. Selection erronee" "un plan a ete recupere : $errone"
fi

suivant=$(sed -n '/^## Next Step/,/^## /p' "$resolu/task_plan.md" 2>/dev/null | sed '1d;$d' | tr -d '\r')
if [ -n "$(printf '%s' "$suivant" | tr -d '[:space:]')" ]; then
    vert "4. '## Next Step' non vide dans le plan resolu"
else
    rouge "4. '## Next Step' non vide" "section absente ou vide"
fi

# 5. Le critere : l'injection automatique a-t-elle eu lieu EN SESSION ?
#    Delegue a reference/preuve_injection.py, qui lit les enregistrements de
#    hooks de l'hote (attachment hook_success / hook_additional_context) plutot
#    que de deviner. Aucune duree n'y sert de preuve.
python=".venv/Scripts/python.exe"
[ -x "$python" ] || python="python"
if "$python" reference/preuve_injection.py >/dev/null 2>&1; then
    vert "5. Injection automatique prouvee (voir preuve_injection.py)"
else
    rouge "5. Injection automatique prouvee"         "aucune injection prouvee — detail : $python reference/preuve_injection.py"
fi

echo
echo "--- Diagnostic (informatif, ne compte pas dans le verdict) ---"

# Telemetrie de hooks laissee par l'hote dans la trace : evenement, duree,
# erreurs. Mesures sur cette machine : le script fait son travail en ~1000 ms
# depuis la racine du depot, et sort en ~150 ms sans rien faire depuis un
# autre dossier. Une duree de l'ordre de 50-100 ms signe donc une sortie
# immediate. L'hypothese « sh introuvable » a ete invalidee : sh se resout
# bien en /usr/bin/sh dans le Git Bash non-login qu'utilise l'hote.
if [ -n "$derniere" ] && command -v python >/dev/null 2>&1; then
    python - "$derniere" <<'PY'
import json
import sys

vus = []
for ligne in open(sys.argv[1], encoding="utf-8", errors="replace"):
    if "hookInfos" not in ligne:
        continue
    try:
        objet = json.loads(ligne)
    except ValueError:
        continue

    def parcourir(noeud):
        if isinstance(noeud, dict):
            if "hookInfos" in noeud:
                for info in noeud.get("hookInfos") or []:
                    commande = info.get("command", "")
                    evenement = "?"
                    for marque in ("userprompt", "pretool", "posttool", "stop", "precompact"):
                        if "--event=" + marque in commande:
                            evenement = marque
                            break
                    vus.append((evenement, info.get("durationMs"), noeud.get("hookErrors") or []))
            for valeur in noeud.values():
                parcourir(valeur)
        elif isinstance(noeud, list):
            for valeur in noeud:
                parcourir(valeur)

    parcourir(objet)

if not vus:
    print("   hooks declenches par l hote : AUCUN (skill non invoque, ou hooks non enregistres)")
else:
    print("   hooks declenches par l hote :")
    for evenement, duree, erreurs in vus:
        if isinstance(duree, int) and duree < 200:
            verdict = "sortie immediate, aucun travail (voir COMPTE_RENDU_J0 §5)"
        else:
            verdict = "script execute"
        print(f"     {evenement:<11} {duree} ms  -> {verdict}")
        if erreurs:
            print(f"       erreurs rapportees : {erreurs}")
PY
fi

printf '   sh resolvable ici          : %s\n' "$(command -v sh || echo NON)"
printf '   CLAUDE_CODE_GIT_BASH_PATH  : %s\n' "${CLAUDE_CODE_GIT_BASH_PATH:-non defini}"

# Rejoue la ligne de hook exacte declaree par le SKILL.md, pour separer un
# defaut de l'hote d'un defaut du script amont.
sim=$(CLAUDE_SKILL_DIR="$SKILL" PATH="/c/Program Files/Git/bin:$PATH" \
    printf '%s' '{"session_id":"simulation-locale","prompt_id":"t1"}' \
    | CLAUDE_SKILL_DIR="$SKILL" PATH="/c/Program Files/Git/bin:$PATH" sh -c \
    'SH="${CLAUDE_SKILL_DIR}/scripts/skill-hook.sh"; [ -f "$SH" ] && sh "$SH" --event=pretool' \
    2>/dev/null | grep -c "BEGIN-PWF-DATA")
if [ "${sim:-0}" -gt 0 ]; then
    printf '   ligne de hook rejouee ici  : elle INJECTE correctement\n'
    printf '                                (donc un echec du point 5 vient de l hote, pas du script)\n'
else
    printf '   ligne de hook rejouee ici  : elle N INJECTE PAS\n'
fi

echo
if [ "$echec" -eq 0 ]; then
    echo "TOUT EST VERT — le dernier point du lot 0.3 est tenu, J0 peut etre consigne."
else
    echo "AU MOINS UN POINT EST ROUGE — J0 n'est pas atteint. Ne pas ouvrir le lot 1."
fi
exit "$echec"

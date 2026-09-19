"""Preuve d'injection automatique du plan par les hooks PWF.

Analyse la trace d'une session Claude Code et rend compte **par evenement**.

Regle de preuve, volontairement stricte :

- une banniere `===BEGIN-PWF-DATA ... nonce=` trouvee dans un **resultat d'outil**
  ne prouve rien : elle peut venir d'un appel manuel de l'injecteur ou de la
  lecture d'un fichier qui la contient ;
- une banniere trouvee **hors resultat d'outil** (contexte injecte, message
  systeme) est la seule qui compte ;
- l'execution d'un hook se lit dans les enregistrements de l'hote, jamais dans
  une duree : une duree ne prouve ni n'infirme une execution.

    python reference/preuve_injection.py [trace.jsonl]

Sans argument, prend la trace la plus recente du depot courant.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

BANNIERE = "BEGIN-PWF-DATA"
EVENEMENTS = (
    "session-start", "user-prompt-submit", "pre-tool-use",
    "post-tool-use", "pre-compact", "stop",
)
# Le skill autonome nomme ses evenements autrement que le plugin.
ALIAS = {
    "userprompt": "user-prompt-submit", "pretool": "pre-tool-use",
    "posttool": "post-tool-use", "precompact": "pre-compact", "stop": "stop",
}


def trace_par_defaut() -> Path:
    racine = Path.cwd()
    try:
        chemin = subprocess.run(
            ["cygpath", "-w", str(racine)], capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        chemin = str(racine)
    cle = "".join("-" if c in ":/" + chr(92) + "_" else c for c in chemin)
    dossier = Path.home() / ".claude" / "projects" / cle
    traces = sorted(dossier.glob("*.jsonl"), key=os.path.getmtime, reverse=True)
    if not traces:
        sys.exit(f"aucune trace de session sous {dossier}")
    return traces[0]


def evenement_de(texte: str) -> str | None:
    for nom in EVENEMENTS:
        if nom in texte:
            return nom
    for brut, nom in ALIAS.items():
        if "--event=" + brut in texte:
            return nom
    return None


def analyser(trace: Path) -> int:
    executions: dict[str, list[dict[str, object]]] = {e: [] for e in EVENEMENTS}
    injections_hors_outil: list[tuple[int, str]] = []
    injections_dans_outil: list[tuple[int, str]] = []
    meta: dict[str, str] = {}

    for numero, ligne in enumerate(trace.open(encoding="utf-8", errors="replace"), 1):
        try:
            enregistrement = json.loads(ligne)
        except ValueError:
            continue
        for cle in ("sessionId", "cwd", "gitBranch", "version"):
            if cle in enregistrement and cle not in meta:
                meta[cle] = str(enregistrement[cle])

        def parcourir(noeud: object, numero: int = numero, dans_outil: bool = False) -> None:
            if isinstance(noeud, dict):
                sous_outil = dans_outil or noeud.get("type") == "tool_result" \
                    or "toolUseResult" in noeud
                for info in noeud.get("hookInfos") or []:
                    texte = json.dumps(info, ensure_ascii=False)
                    nom = evenement_de(texte)
                    if nom:
                        executions[nom].append({
                            "ligne": numero,
                            "duree": info.get("durationMs"),
                            "erreurs": noeud.get("hookErrors") or [],
                        })
                for valeur in noeud.values():
                    if isinstance(valeur, str):
                        if BANNIERE in valeur:
                            cible = injections_dans_outil if sous_outil else injections_hors_outil
                            cible.append((numero, valeur[valeur.index(BANNIERE):][:70]))
                    else:
                        parcourir(valeur, numero, sous_outil)
            elif isinstance(noeud, list):
                for valeur in noeud:
                    parcourir(valeur, numero, dans_outil)

        parcourir(enregistrement)

    print(f"=== TRACE : {trace.name} ===")
    for cle, valeur in meta.items():
        print(f"  {cle:<10} : {valeur}")

    print("\n=== EXECUTIONS DE HOOKS ENREGISTREES PAR L'HOTE ===")
    for nom in EVENEMENTS:
        lignes = executions[nom]
        if not lignes:
            print(f"  {nom:<18} : non observable (aucun enregistrement)")
        else:
            durees = ", ".join(str(e["duree"]) for e in lignes)
            erreurs = [e for e in lignes if e["erreurs"]]
            print(f"  {nom:<18} : {len(lignes)} execution(s), durees {durees} ms"
                  + (f", ERREURS {erreurs}" if erreurs else ""))

    print("\n=== INJECTIONS DU PLAN ===")
    print(f"  hors resultat d'outil (PREUVE)      : {len(injections_hors_outil)}")
    for numero, extrait in injections_hors_outil[:5]:
        print(f"      ligne {numero} : {extrait}")
    print(f"  dans un resultat d'outil (EXCLUES)  : {len(injections_dans_outil)}")
    for numero, extrait in injections_dans_outil[:5]:
        print(f"      ligne {numero} : {extrait}")

    print()
    if injections_hors_outil:
        print("VERDICT : injection automatique PROUVEE sur cette trace.")
        return 0
    print("VERDICT : aucune injection automatique prouvee sur cette trace.")
    print("          (une execution de hook sans injection reste un echec du critere)")
    return 1


if __name__ == "__main__":
    cible = Path(sys.argv[1]) if len(sys.argv) > 1 else trace_par_defaut()
    raise SystemExit(analyser(cible))

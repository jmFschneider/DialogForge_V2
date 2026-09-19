"""Preuve d'injection automatique du plan par les hooks PWF.

Analyse la trace d'une session Claude Code et rend compte **par evenement**.

Ce que l'hote enregistre reellement, et qui sert de preuve. Il ecrit **deux**
enregistrements `attachment` par hook :

- `hook_success` / `hook_error` : l'execution — commande, `exitCode`,
  `durationMs`, `stdout`, `stderr` ;
- `hook_additional_context` : le contexte **effectivement livre au modele**,
  rendu en `<system-reminder>`.

Le second est la preuve de l'injection : il atteste que le plan est entre dans
le contexte, pas seulement qu'un script a tourne.

Regle de preuve, volontairement stricte :

- seule compte une banniere `===BEGIN-PWF-DATA` presente dans le `stdout` d'un
  enregistrement de hook de l'hote ;
- une banniere citee dans un message (assistant ou utilisateur) ou apparaissant
  dans un resultat d'outil ne prouve rien : elle peut venir d'un appel manuel de
  l'injecteur, d'une lecture de fichier ou d'un copier-coller ;
- aucune duree n'est utilisee pour affirmer ou nier une execution.

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
    "SessionStart", "UserPromptSubmit", "PreToolUse",
    "PostToolUse", "PreCompact", "Stop",
)


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


def collecter(trace: Path) -> tuple[list[dict[str, object]], list[int], dict[str, str]]:
    """Rend les enregistrements de hooks de l'hote, les bannieres non probantes
    (citees dans un message), et l'identite de la session."""
    hooks: list[dict[str, object]] = []
    citations: list[int] = []
    meta: dict[str, str] = {}

    for numero, ligne in enumerate(trace.open(encoding="utf-8", errors="replace"), 1):
        try:
            enregistrement = json.loads(ligne)
        except ValueError:
            continue
        for cle in ("sessionId", "cwd", "gitBranch", "version"):
            if cle in enregistrement and cle not in meta:
                meta[cle] = str(enregistrement[cle])

        piece = enregistrement.get("attachment")
        if isinstance(piece, dict) and piece.get("hookEvent"):
            stdout = piece.get("stdout") or ""
            rendu = json.dumps(enregistrement.get("rendered") or "", ensure_ascii=False)
            contenu = piece.get("content") or ""
            livre = BANNIERE in rendu or BANNIERE in contenu
            hooks.append({
                "livre": livre,
                "ligne": numero,
                "evenement": str(piece.get("hookEvent")),
                "nom": str(piece.get("hookName") or ""),
                "type": str(piece.get("type") or ""),
                "code": piece.get("exitCode"),
                "duree": piece.get("durationMs"),
                "stderr": (piece.get("stderr") or "").strip(),
                "injecte": BANNIERE in stdout,
                "octets": len(stdout),
            })
            continue

        if enregistrement.get("type") in ("assistant", "user") and BANNIERE in ligne:
            citations.append(numero)

    return hooks, citations, meta


def analyser(trace: Path) -> int:
    hooks, citations, meta = collecter(trace)

    print(f"=== TRACE : {trace.name} ===")
    for cle, valeur in meta.items():
        print(f"  {cle:<10} : {valeur}")

    print("\n=== RESULTAT PAR EVENEMENT (source : enregistrements de l'hote) ===")
    prouves = 0
    for evenement in EVENEMENTS:
        concernes = [h for h in hooks if h["evenement"] == evenement]
        if not concernes:
            print(f"  {evenement:<17} : NON OBSERVABLE — aucun enregistrement")
            continue
        avec = [h for h in concernes if h["injecte"] or h["livre"]]
        echecs = [h for h in concernes if h["code"] not in (0, None) or h["type"] == "hook_error"]
        livres = [h for h in concernes if h["livre"]]
        if livres:
            etat = "PREUVE D'INJECTION AU CONTEXTE"
        elif avec:
            etat = "hook execute avec plan en sortie, livraison non observee"
        else:
            etat = "execute, SANS injection"
        if avec:
            prouves += 1
        print(f"  {evenement:<17} : {etat} — {len(concernes)} execution(s),"
              f" {len(avec)} avec plan")
        for h in concernes:
            if h["livre"]:
                detail = "PLAN LIVRE AU CONTEXTE"
            elif h["injecte"]:
                detail = "plan en sortie du hook"
            else:
                detail = "pas de plan"
            print(f"      ligne {h['ligne']:<4} {h['nom']:<24} code={h['code']}"
                  f" {h['duree']} ms  {detail}")
            if h["stderr"]:
                print(f"         stderr : {h['stderr'][:120]}")
        if echecs:
            print(f"      ATTENTION : {len(echecs)} execution(s) en erreur")

    print("\n=== OCCURRENCES NON PROBANTES, EXCLUES ===")
    if citations:
        print(f"  bannieres citees dans un message (assistant/utilisateur) : {citations}")
        print("  -> exclues : citation ou copier-coller, pas une injection de l'hote")
    else:
        print("  aucune")

    print()
    if prouves:
        print(f"VERDICT : injection automatique PROUVEE pour {prouves} evenement(s) sur"
              f" {len(EVENEMENTS)}.")
        print("          Les evenements « NON OBSERVABLE » ne sont ni valides ni infirmes.")
        return 0
    print("VERDICT : aucune injection automatique prouvee sur cette trace.")
    return 1


if __name__ == "__main__":
    cible = Path(sys.argv[1]) if len(sys.argv) > 1 else trace_par_defaut()
    raise SystemExit(analyser(cible))

"""Le registre des objections : de l'énoncé initial à la disposition finale.

Rien n'est stocké en double. Le registre se **relit** dans les artefacts déjà
écrits — `echanges/NNNN-critique-B.json` (énoncé, disposition, justification de
B) et `echanges/NNNN-reponses-A.json` (réponse de A) — et se range par numéro
d'appel. La preuve brute de chaque échange reste dans `appels/`.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from . import contracts, demande, storage


def ledger(collab: Path) -> list[dict[str, Any]]:
    """Une entrée par objection : son énoncé initial, sa sévérité, sa disposition
    courante, et l'historique de ce que B et A en ont dit, dans l'ordre.

    La disposition courante est la dernière que B a rendue. Une objection que
    personne n'a fermée reste `OPEN` : l'absence ne clôture jamais.
    """
    entries: dict[str, dict[str, Any]] = {}
    for path in sorted((collab / "echanges").glob("*-critique-B.json")):
        review = contracts.parse_review(storage.read_text(path)[0])
        for f in review.findings:
            entry = entries.setdefault(f.id, {
                "id": f.id, "statement": f.statement, "severity": f.severity.value,
                "disposition": f.disposition.value, "history": [],
            })
            entry.update(severity=f.severity.value, disposition=f.disposition.value)
            entry["history"].append({
                "call": path.name[:4], "by": "B",
                "disposition": f.disposition.value, "justification": f.justification,
            })
    for path in sorted((collab / "echanges").glob("*-reponses-A.json")):
        responses = contracts.responses_from_dict(json.loads(storage.read_text(path)[0]))
        for r in responses:
            entries[r.id]["history"].append({
                "call": path.name[:4], "by": "A",
                "response": r.kind.value, "justification": r.justification,
            })
    for entry in entries.values():
        entry["history"].sort(key=lambda event: event["call"])
    return list(entries.values())


def bilan(
    collab: Path, *, delivered: str, examined: str, review: str, revisions: int,
    max_revisions: int, capped: bool,
) -> str:
    """Le bilan du cycle, écrit **par le programme, sans modèle** : ce qui est
    livré, ce qui l'a examiné, et ce qui reste en désaccord.

    Il porte les empreintes de la demande, du livrable et de la revue, pour que
    les trois se recoupent sans ouvrir de journal. « Cycle terminé » n'y est
    jamais dit « accepté » : l'acceptation est une décision humaine (1.4).
    """
    text = _sha(collab / examined)
    decision = contracts.parse_review(storage.read_text(collab / review)[0]).decision.value
    versions = max(len(demande.read(collab)), 1)
    entries = ledger(collab)
    still_open = [e for e in entries if e["disposition"] == "OPEN"]
    ending = (
        f"plafond de révisions atteint ({revisions} sur {max_revisions}) : "
        "les désaccords ci-dessous sont présentés, pas traités"
        if capped else "B a accepté la version examinée"
    )
    lines = [
        "# Bilan du cycle", "",
        "> Écrit par le programme, sans appel de modèle."
        " « Cycle terminé » n'est pas « accepté ».",
        "", "## Ce qui est livré", "",
        f"- Livrable : `{delivered}` — corps identique à `{examined}` (sha256 `{text}`),"
        " non réécrit après la revue.",
        f"- Examiné par : `{review}` (sha256 `{_sha(collab / review)}`)"
        f" — décision de B : {decision}.",
        f"- Demande : `demande.md` (sha256 `{_sha(collab / 'demande.md')}`,"
        f" {versions} version(s)).",
        f"- Fin du cycle : {ending}.", "",
        "## Objections", "",
    ]
    if entries:
        lines += ["| Id | Sévérité | Disposition | Dernière réponse de A | Justification de B |",
                  "|---|---|---|---|---|"]
        for e in entries:
            answers = [h for h in e["history"] if h["by"] == "A"]
            closings = [h for h in e["history"] if h["by"] == "B"]
            last = answers[-1] if answers else None
            reply = f"{last['response']} — {last['justification']}" if last else "—"
            lines.append("| " + " | ".join(_cell(x) for x in (
                e["id"], e["severity"], e["disposition"], reply,
                closings[-1]["justification"] or "—",
            )) + " |")
    else:
        lines.append("Aucune objection n'a été soulevée.")
    lines += ["", "## Désaccords restants", ""]
    lines += [f"- `{e['id']}` [{e['severity']}] {e['statement']}" for e in still_open] or [
        "Aucun."
    ]
    return "\n".join(lines) + "\n"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cell(text: str) -> str:
    return " ".join(str(text).replace("|", "/").split())

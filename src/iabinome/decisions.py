"""Les décisions humaines, et ce que l'humain lit avant de décider (plan V2, 1.4).

**« Terminé » n'est pas « accepté ».** Le cycle s'arrête en `AWAITING_APPROVAL`
sans rien approuver ; l'acceptation est une décision de l'humain, consignée dans
`decisions.json` — un fichier lisible à l'œil, ajouté à chaque décision, sans
base ni index. Chaque entrée est **datée et porte sur une version précise** : les
empreintes du livrable, de la revue et de la demande au moment de décider. Une
décision qui ne correspond plus à ce qui est sur le disque le dit.

Le module ne mute rien d'autre : l'état est publié par `workflow`, sous verrou.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import incidents, objections, storage
from .models import State, Status

DECISIONS = "decisions.json"
DELIVERED = "livrables/version_finale.md"

ACCEPTED = "ACCEPTE"
ACCEPTED_WITH_RESERVES = "ACCEPTE_AVEC_RESERVES"
TARGETED_CORRECTION = "CORRECTION_CIBLEE"
STOPPED = "ARRET"
_ACCEPTANCES = (ACCEPTED, ACCEPTED_WITH_RESERVES)


def _sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def version_of(collab: Path, state: State) -> dict[str, Any]:
    """La version précise sur laquelle porte une décision : le livrable, la revue
    qui l'a examiné et la demande, par leurs empreintes."""
    review = state.latest_review
    return {
        "livrable": DELIVERED, "livrable_sha256": _sha(collab / DELIVERED),
        "revue": review, "revue_sha256": _sha(collab / review) if review else None,
        "demande_sha256": state.demande_sha256, "revision": state.revision,
    }


def read(collab: Path) -> list[dict[str, Any]]:
    path = collab / DECISIONS
    if not path.exists():
        return []
    decisions: list[dict[str, Any]] = json.loads(storage.read_text(path)[0])["decisions"]
    return decisions


def record(collab: Path, kind: str, state: State, **extra: Any) -> None:
    """Ajoute une décision. **Rejouable** : la même décision sur la même version
    n'est pas consignée deux fois — un arrêt brutal suivi d'une reprise ne doit
    pas produire deux acceptations."""
    entries = read(collab)
    body = {
        "decision": kind, "version": version_of(collab, state),
        **{key: value for key, value in extra.items() if value is not None},
    }
    if entries:
        previous = {k: v for k, v in entries[-1].items() if k not in ("sequence", "at")}
        if previous == body:
            return
    entries.append({
        "sequence": len(entries) + 1,
        "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **body,
    })
    storage.write_atomic_text(
        collab / DECISIONS,
        json.dumps({"schema_version": 1, "decisions": entries}, ensure_ascii=False, indent=2)
        + "\n",
    )


def latest(collab: Path) -> dict[str, Any] | None:
    entries = read(collab)
    return entries[-1] if entries else None


def applies_to_current(collab: Path, decision: dict[str, Any], state: State) -> bool:
    """La décision porte-t-elle encore sur ce qui est sur le disque ?"""
    return bool(decision["version"] == version_of(collab, state))


def is_acceptance(decision: dict[str, Any] | None) -> bool:
    return decision is not None and decision["decision"] in _ACCEPTANCES


def corrections(collab: Path) -> int:
    """Combien de tours supplémentaires l'humain a demandés après le livrable."""
    return sum(1 for d in read(collab) if d["decision"] == TARGETED_CORRECTION)


def describe(collab: Path, state: State) -> str:
    """La décision courante, en une phrase — et jamais « acceptée » à tort."""
    decision = latest(collab)
    if decision is None:
        if state.status is Status.AWAITING_APPROVAL:
            return "aucune : le cycle est terminé, il n'est pas accepté"
        return "aucune"
    label = {
        ACCEPTED: "acceptée", ACCEPTED_WITH_RESERVES: "acceptée avec réserves",
        TARGETED_CORRECTION: "correction ciblée demandée", STOPPED: "arrêtée",
    }[decision["decision"]]
    text = f"{label} le {decision['at']}"
    if decision["decision"] in _ACCEPTANCES + (TARGETED_CORRECTION,):
        text += f" (livrable {str(decision['version']['livrable_sha256'])[:12]})"
        if not applies_to_current(collab, decision, state):
            text += " — porte sur une version antérieure : le livrable a changé depuis"
    return text


def _incident(collab: Path, state: State) -> dict[str, Any] | None:
    return incidents.incident(collab, state)


def incident_line(collab: Path, state: State) -> str | None:
    incident = _incident(collab, state)
    if incident is None:
        return None
    return f"{incident['kind']} — {incident.get('detail') or 'sans détail'}"


def next_action(collab: Path, state: State) -> str:
    """Ce que l'humain fait maintenant, sans ouvrir un journal."""
    status = state.status
    if status is Status.READY:
        return "lancer `run <dossier>`"
    if status is Status.RUNNING:
        return (
            "un appel est en cours, ou le processus s'est arrêté en cours d'appel :"
            " `run <dossier>` reprend localement, sans repayer d'appel"
        )
    if status is Status.WAITING_HUMAN:
        return _waiting_human(collab, state)
    if status in (Status.INTERRUPTED, Status.ERROR):
        return incidents.action(collab, state)
    if status is Status.STOPPED:
        return "aucune : la collaboration a été arrêtée par décision humaine"
    decision = latest(collab)
    if is_acceptance(decision) and decision is not None and applies_to_current(
        collab, decision, state
    ):
        return "aucune : le résultat est accepté"
    return (
        "lire `livrables/bilan.md` puis décider : `decide <dossier> --accept`,"
        " `--accept-with-reserves <texte>`, `--correct <fichier>` ou `--stop`"
    )


def _latest_exchange(collab: Path, suffix: str) -> str | None:
    folder = collab / "echanges"
    found = sorted(folder.glob(f"*-{suffix}")) if folder.is_dir() else []
    return f"echanges/{found[-1].name}" if found else None


def _waiting_human(collab: Path, state: State) -> str:
    incident = _incident(collab, state)
    if incident is not None and incident["kind"] == "ACCEPTER_WITH_OPEN_BLOCKING":
        return (
            "B a accepté malgré une objection bloquante restée ouverte : lire"
            f" `{state.latest_review}`, puis `resume --answer <fichier>` pour préciser la demande"
            " ou `decide <dossier> --stop`"
        )
    question = _latest_exchange(collab, "question-A.md")
    if question is not None and (state.latest_review is None or question > state.latest_review):
        source = f"la question de A (`{question}`)"
    else:
        source = f"la revue qui bloque (`{state.latest_review}`)"
    return (
        f"lire {source}, puis `resume --answer <fichier>` (complète la demande)"
        " ou `decide <dossier> --stop`"
    )


def render(collab: Path, state: State, *, with_document: bool) -> str:
    """Ce que l'humain lit avant de décider : où en est le cycle, ce qui a été
    corrigé, ce qui reste en réserve, la prochaine action, puis le document."""
    lines = [
        f"Collaboration : {collab.name} — statut {state.status.value}, phase {state.phase.value}",
        f"Décision : {describe(collab, state)}",
    ]
    delivered = collab / DELIVERED
    entries = objections.ledger(collab)
    if delivered.is_file():
        fixed = [e for e in entries if e["disposition"] != "OPEN" and any(
            h["by"] == "A" and h["response"] == "CORRIGE" for h in e["history"]
        )]
        lines += ["", "Corrections principales :"]
        lines += [_correction(e) for e in fixed] or ["  aucune objection n'a été corrigée"]
        lines += ["", "Réserves :"]
        reserves = [f"  - {e['id']} [{e['severity']}] {e['statement']}"
                    for e in entries if e["disposition"] == "OPEN"]
        decision = latest(collab)
        if decision is not None and decision["decision"] == ACCEPTED_WITH_RESERVES:
            reserves.append(f"  - de l'humain : {decision['reserves']}")
        lines += reserves or ["  aucune"]
    lines += ["", f"Prochaine action : {next_action(collab, state)}"]
    if state.status in (Status.INTERRUPTED, Status.ERROR, Status.WAITING_HUMAN):
        lines[2:2] = incidents.explain(collab, state)
    if with_document and delivered.is_file():
        lines += ["", "--- Document (livrables/version_finale.md) ---", ""]
        lines.append(delivered.read_text(encoding="utf-8").rstrip("\n"))
    return "\n".join(lines) + "\n"


def _correction(entry: dict[str, Any]) -> str:
    answer = next(h for h in reversed(entry["history"]) if h["by"] == "A")
    closing = next((h for h in reversed(entry["history"]) if h["by"] == "B"), None)
    text = f"  - {entry['id']} [{entry['severity']}] {entry['statement']}"
    if answer["justification"]:
        text += f" — A : {answer['justification']}"
    if closing is not None and closing["justification"]:
        text += f" — B : {closing['justification']}"
    return text

"""Les décisions humaines, et ce que l'humain lit avant de décider (plan V2, 1.4).

**« Terminé » n'est pas « accepté ».** Le cycle s'arrête en `AWAITING_APPROVAL`
sans rien approuver ; l'acceptation est une décision de l'humain, consignée dans
`decisions.json` — un fichier lisible à l'œil, ajouté à chaque décision, sans
base ni index. Chaque entrée est **datée et porte sur une version précise** : les
empreintes du livrable, de la revue et de la demande au moment de décider. Une
décision qui ne correspond plus à ce qui est sur le disque le dit.

Il dit aussi **ce que l'humain peut faire** (`allowed_actions`) : la seule table
d'actions, que la CLI rend en phrases et la GUI en boutons.

Le module ne mute rien d'autre : l'état est publié par `workflow`, sous verrou.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from . import contracts, incidents, objections, storage
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


def demande_sha(collab: Path) -> str | None:
    """L'empreinte de `demande.md` **sur le disque**, normalisée comme le moteur
    la calcule (`workflow._check_demande`) ; `None` si elle est absente."""
    path = collab / "demande.md"
    if not path.is_file():
        return None
    try:
        return contracts.normalize(storage.read_text(path)[0]).sha256
    except UnicodeDecodeError:
        return "illisible"


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


_ARTIFACTS = (
    ("livrable_sha256", "le livrable a changé", "livrable absent"),
    ("revue_sha256", "la revue a changé", "revue absente"),
)


def discrepancies(collab: Path, decision: dict[str, Any], state: State) -> tuple[str, ...]:
    """Ce qui, sur le disque, ne correspond plus à la version décidée — vide si la
    décision y porte encore. La demande est relue, pas reprise de l'état. Une
    acceptation exige en plus un livrable et une revue : une absence n'est pas
    une version qu'on accepte."""
    version, current = decision["version"], version_of(collab, state)
    found = []
    for key, changed, absent in _ARTIFACTS:
        if current[key] is None and (is_acceptance(decision) or version.get(key) is not None):
            found.append(absent)
        elif version.get(key) != current[key]:
            found.append(changed)
    on_disk = demande_sha(collab)
    if on_disk is None:
        found.append("demande.md absente")
    elif on_disk != state.demande_sha256 or on_disk != version.get("demande_sha256"):
        found.append("la demande a changé")
    if not found and version != current:
        found.append("la révision a changé")
    return tuple(found)


def acceptance_gaps(collab: Path, state: State) -> tuple[str, ...]:
    """Ce qui empêche d'accepter ce qui est sur le disque : la même vérification
    que celle qui dit si une acceptation passée s'applique encore."""
    candidate = {"decision": ACCEPTED, "version": version_of(collab, state)}
    return discrepancies(collab, candidate, state)


def applies_to_current(collab: Path, decision: dict[str, Any], state: State) -> bool:
    """La décision porte-t-elle encore sur ce qui est sur le disque ?"""
    return not discrepancies(collab, decision, state)


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
        if found := discrepancies(collab, decision, state):
            text += f" — porte sur une version antérieure : {' ; '.join(found)}"
    return text


def _incident(collab: Path, state: State) -> dict[str, Any] | None:
    return incidents.incident(collab, state)


def incident_line(collab: Path, state: State) -> str | None:
    incident = _incident(collab, state)
    if incident is None:
        return None
    return f"{incident['kind']} — {incident.get('detail') or 'sans détail'}"


class ActionId(Enum):
    START = "START"
    RESUME = "RESUME"
    ANSWER_AND_RESUME = "ANSWER_AND_RESUME"
    RETRY_CALL = "RETRY_CALL"
    REPROCESS_AND_RESUME = "REPROCESS_AND_RESUME"
    ACCEPT = "ACCEPT"
    ACCEPT_WITH_RESERVES = "ACCEPT_WITH_RESERVES"
    CORRECT = "CORRECT"
    STOP = "STOP"


@dataclass(frozen=True)
class AllowedAction:
    """Une action que le moteur accepte **maintenant** (`conception/GUI_V1.md` §10.2).

    `may_call` : la commande peut atteindre un appel fournisseur — à confirmer
    avant, jamais présenté comme gratuit. `local_step` : une étape sans appel la
    précède (écrire une réponse, relire une réponse conservée, reprendre depuis
    les preuves). `primary` : ce qui est proposé ; une action secondaire reste
    permise sans être la suite attendue. Aucune action principale = rien à faire.
    """

    id: ActionId
    may_call: bool
    local_step: bool = False
    primary: bool = True
    inputs: tuple[str, ...] = ()
    call_id: str | None = None


def accepted(collab: Path, state: State) -> bool:
    """Une acceptation porte-t-elle sur ce qui est sur le disque ? Le sous-état
    « version acceptée » en dérive ; il n'est jamais un statut."""
    decision = latest(collab)
    return is_acceptance(decision) and decision is not None and applies_to_current(
        collab, decision, state
    )


def allowed_actions(collab: Path, state: State) -> tuple[AllowedAction, ...]:
    """**La** table de ce que l'humain peut faire, statut par statut. Elle suit
    les portes du moteur (`workflow`) : une action annoncée ici est une action
    qu'il accepte. La CLI et la GUI en dérivent leurs phrases et leurs boutons."""
    status, call = state.status, state.current_call
    call_id = None if call is None else call.call_id
    stop = AllowedAction(ActionId.STOP, may_call=False)
    if status is Status.STOPPED:
        return ()
    if status is Status.READY:
        first = state.current_document is None and state.latest_review is None
        start = ActionId.START if first else ActionId.RESUME
        return AllowedAction(start, may_call=True), replace(stop, primary=False)
    if status is Status.RUNNING:
        return (
            AllowedAction(ActionId.RESUME, may_call=True, local_step=True),
            replace(stop, primary=False),
        )
    if status is Status.WAITING_HUMAN:
        answer = AllowedAction(
            ActionId.ANSWER_AND_RESUME, may_call=True, local_step=True, inputs=("réponse",)
        )
        return answer, stop
    if status in (Status.INTERRUPTED, Status.ERROR):
        if not incidents.relaunchable(collab, state):
            return (stop,)
        retry = AllowedAction(
            ActionId.RETRY_CALL, may_call=True, inputs=("motif",), call_id=call_id
        )
        if status is Status.INTERRUPTED:
            return retry, stop
        reprocess = AllowedAction(
            ActionId.REPROCESS_AND_RESUME, may_call=True, local_step=True, inputs=("motif",),
            call_id=call_id,
        )
        return reprocess, replace(retry, primary=False), stop
    correct = AllowedAction(
        ActionId.CORRECT, may_call=True, local_step=True, inputs=("instruction",)
    )
    if accepted(collab, state):
        return replace(correct, primary=False), replace(stop, primary=False)
    return (
        AllowedAction(ActionId.ACCEPT, may_call=False),
        AllowedAction(ActionId.ACCEPT_WITH_RESERVES, may_call=False, inputs=("réserves",)),
        correct, stop,
    )


def next_action(collab: Path, state: State) -> str:
    """Ce que l'humain fait maintenant, sans ouvrir un journal — dit en phrases
    de terminal à partir de `allowed_actions`, qui seule en fixe les règles."""
    actions = allowed_actions(collab, state)
    offered = {action.id: action for action in actions if action.primary}
    if not offered:
        if state.status is Status.STOPPED:
            return "aucune : la collaboration a été arrêtée par décision humaine"
        return "aucune : le résultat est accepté"
    resume = offered.get(ActionId.START) or offered.get(ActionId.RESUME)
    if resume is not None:
        if resume.local_step:
            return (
                "un appel est en cours, ou le processus s'est arrêté en cours d'appel :"
                " `run <dossier>` reprend sans repayer cet appel, puis le cycle appelle"
                " l'agent suivant"
            )
        return "lancer `run <dossier>`"
    if ActionId.ANSWER_AND_RESUME in offered:
        return _waiting_human(collab, state)
    if ActionId.ACCEPT in offered:
        return (
            "lire `livrables/bilan.md` puis décider : `decide <dossier> --accept`,"
            " `--accept-with-reserves <texte>`, `--correct <fichier>` ou `--stop`"
        )
    return _after_incident(collab, state, {action.id for action in actions})


def _after_incident(collab: Path, state: State, allowed: set[ActionId]) -> str:
    """La sortie d'un incident, en une phrase — jamais un rejeu tout seul. Le
    genre d'incident donne le contexte ; les actions permises, les commandes."""
    found = incidents.incident(collab, state)
    call = state.current_call
    who = "" if call is None else f" (appel `{call.call_id}`)"
    name = "incident inconnu" if found is None else str(found["kind"])
    kind = incidents.KINDS.get(name)
    stop = "`decide <dossier> --stop`"
    if ActionId.RETRY_CALL not in allowed:
        return f"{name}{who} : aucune relance possible depuis cet état ; {stop}"
    retry = (
        "`resume <dossier> --retry-call <id> --reason-file <fichier>` (nouvel appel"
        " payant ; le fichier dit pourquoi)"
    )
    if ActionId.REPROCESS_AND_RESUME in allowed:
        return (
            f"{name}{who} : la réponse brute est conservée dans `appels/`. Sans la repayer :"
            " `resume <dossier> --reprocess <id> --reason-file <fichier>` (relit la réponse"
            " conservée — utile si la lecture a été corrigée —, puis le cycle reprend et peut"
            f" appeler l'agent suivant) ; ou {retry} ; ou {stop}"
        )
    if name == "SOURCES_MODIFIED":
        return (
            f"{name}{who} : le corpus ne correspond plus à son manifeste. Le rétablir (le"
            " contrôle avant chaque appel refuse sinon), puis "
            f"{retry} ; sinon {stop}"
        )
    if kind is not None and kind.paid == "non":
        return (
            f"{name}{who} : rien n'a été payé. Corriger la cause, puis {retry} ; sinon {stop}"
        )
    return (
        f"{name}{who} : l'appel a pu être payé, aucun rejeu automatique. Si vous décidez de le"
        f" relancer : {retry} ; sinon {stop}"
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
        f"lire {source}, puis `resume --answer <fichier>` (complète la demande, puis"
        " rappelle A)"
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

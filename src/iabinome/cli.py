"""Surface CLI — quatre commandes, rien d'autre (CONCEPTION_FINALE.md §7).

`new` fait tous ses prévols dans un répertoire temporaire frère puis publie
par renommage ; `run` est l'unique moteur synchrone ; `resume` n'en contient
pas un second — il enregistre l'intervention humaine, remet l'état dans une
phase admissible, puis appelle le même moteur ; `status` est strictement en
lecture seule.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import contracts, corpus, lock, storage, workflow
from .adapters.base import AgentAdapter
from .adapters.claude import ClaudeAdapter
from .adapters.codex import CodexAdapter
from .models import (
    SCHEMA_VERSION,
    AgentSpec,
    Configuration,
    MissionKind,
    Phase,
    ReviewerAccess,
    Role,
    State,
    Status,
)

ADAPTERS: dict[str, AgentAdapter] = {"claude": ClaudeAdapter(), "codex": CodexAdapter()}

_KIND = {"conception": MissionKind.CONCEPTION, "recherche": MissionKind.RECHERCHE}
_ACCESS = {"context-only": ReviewerAccess.CONTEXT_ONLY, "consult": ReviewerAccess.CONSULT}
# Une QUESTION née en PROPOSAL_A ou REVISION_A y retourne ; une née en
# FINAL_A ou un BLOQUE (né en REVIEW_B) reprennent en REVISION_A, avec le
# document courant et les constats déjà ouverts (§2).
_RESUME_PHASE = {Phase.REVIEW_B: Phase.REVISION_A, Phase.FINAL_A: Phase.REVISION_A}


def cmd_new(args: argparse.Namespace) -> int:
    dest = Path(args.collab)
    if dest.exists():
        return _fail(f"{dest} existe deja")
    if bool(args.source_root) != bool(args.source_list):
        return _fail("--source-root et --source-list vont ensemble")
    kind = _KIND[args.kind]
    if kind is MissionKind.RECHERCHE and not args.source_root:
        return _fail("mission de recherche sans corpus (--source-root et --source-list requis)")
    tmp = dest.parent / f".new-{dest.name}-{uuid.uuid4().hex}"
    tmp.mkdir(parents=True)
    try:
        _build_new(tmp, dest, args, kind, _ACCESS[args.reviewer_access])
    except (corpus.CorpusError, OSError, ValueError) as exc:
        shutil.rmtree(tmp, ignore_errors=True)
        return _fail(str(exc))
    tmp.rename(dest)
    print(f"collaboration creee : {dest}")
    return 0


def _build_new(
    tmp: Path, dest: Path, args: argparse.Namespace, kind: MissionKind, access: ReviewerAccess
) -> None:
    demande_text, _ = storage.read_text(Path(args.demande))
    normalized = contracts.normalize(demande_text)
    storage.write_atomic_text(tmp / "demande.md", normalized.text)
    corpus_sha: str | None = None
    if args.source_root:
        manifest = corpus.build(
            Path(args.source_root), Path(args.source_list), tmp / "corpus",
            args.source_label or Path(args.source_root).name,
        )
        if not manifest.entries and kind is MissionKind.RECHERCHE:
            raise ValueError("corpus vide pour une mission de recherche")
        manifest_text, _ = storage.read_text(tmp / "corpus" / "manifeste.json")
        corpus_sha = contracts.normalize(manifest_text).sha256
    agent_a, agent_b = ADAPTERS[args.agent_a], ADAPTERS[args.agent_b]
    config = Configuration(
        schema_version=SCHEMA_VERSION, collaboration_id=dest.name, mission_kind=kind,
        reviewer_access=access, max_revisions=args.max_revisions,
        agent_a=AgentSpec(args.agent_a, args.model_a or agent_a.default_model(Role.A)),
        agent_b=AgentSpec(args.agent_b, args.model_b or agent_b.default_model(Role.B)),
        initial_demande_sha256=normalized.sha256, corpus_manifest_sha256=corpus_sha,
        created_at=_now(),
    )
    state = State(
        schema_version=SCHEMA_VERSION, status=Status.READY, phase=Phase.PROPOSAL_A, revision=0,
        demande_sha256=normalized.sha256, current_document=None, latest_review=None,
        open_finding_ids=[], current_call=None, last_incident=None, updated_at=_now(),
    )
    _write_json(tmp / "configuration.json", config.to_dict())
    _write_json(tmp / "etat.json", state.to_dict())


def cmd_run(args: argparse.Namespace) -> int:
    return _drive(Path(args.collab), timeout_seconds=args.timeout, command_label="run")


def cmd_resume(args: argparse.Namespace) -> int:
    collab = Path(args.collab)
    if args.answer and (args.retry_call or args.reason_file):
        return _fail("--answer est incompatible avec --retry-call/--reason-file")
    if bool(args.retry_call) != bool(args.reason_file):
        return _fail("--retry-call et --reason-file vont ensemble")
    retry_of: str | None = None
    retry_reason: str | None = None
    try:
        if args.answer:
            _apply_answer(collab, Path(args.answer))
        elif args.retry_call:
            retry_of, retry_reason = _prepare_retry(
                collab, args.retry_call, Path(args.reason_file)
            )
    except (OSError, ValueError) as exc:
        return _fail(str(exc))
    return _drive(
        collab, timeout_seconds=args.timeout, command_label="resume",
        retry_of=retry_of, retry_reason=retry_reason,
    )


def _apply_answer(collab: Path, answer_path: Path) -> None:
    state = State.from_dict(_read_json(collab / "etat.json"))
    if state.status is not Status.WAITING_HUMAN:
        raise ValueError("la collaboration n'attend pas l'humain")
    text, _ = storage.read_text(answer_path)
    normalized = contracts.normalize(text)
    _archive(collab / "demande.md")
    storage.write_atomic_text(collab / "demande.md", normalized.text)
    new_state = replace(
        state, status=Status.READY, phase=_RESUME_PHASE.get(state.phase, state.phase),
        demande_sha256=normalized.sha256, updated_at=_now(),
    )
    _write_json(collab / "etat.json", new_state.to_dict())


def _archive(path: Path) -> None:
    """L'ancienne demande est archivée en `demande.md.NNN`, jamais écrasée :
    une réponse partielle ne doit pas créer une seconde autorité (§2)."""
    existing = [
        int(suffix) for p in path.parent.glob(f"{path.name}.*")
        if (suffix := p.name.rsplit(".", 1)[-1]).isdigit()
    ]
    n = max(existing, default=0) + 1
    path.rename(path.with_name(f"{path.name}.{n:03d}"))


def _prepare_retry(collab: Path, retry_call: str, reason_path: Path) -> tuple[str, str]:
    state = State.from_dict(_read_json(collab / "etat.json"))
    if state.status is not Status.INTERRUPTED or state.current_call is None:
        raise ValueError("aucun appel interrompu a relancer")
    if state.current_call.call_id != retry_call:
        raise ValueError(f"aucun appel interrompu {retry_call!r}")
    reason, _ = storage.read_text(reason_path)
    reason = reason.strip()
    if not reason:
        raise ValueError("le motif de relance ne peut pas etre vide")
    new_state = replace(state, status=Status.READY, current_call=None, updated_at=_now())
    _write_json(collab / "etat.json", new_state.to_dict())
    return retry_call, reason


def _drive(
    collab: Path, *, timeout_seconds: float, command_label: str,
    retry_of: str | None = None, retry_reason: str | None = None,
) -> int:
    try:
        state = workflow.run(
            collab, adapters=ADAPTERS, timeout_seconds=timeout_seconds,
            command_label=command_label, retry_of=retry_of, retry_reason=retry_reason,
        )
    except (workflow.WorkflowError, lock.LockError) as exc:
        return _fail(str(exc))
    print(f"statut : {state.status.value} · phase : {state.phase.value}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    collab = Path(args.collab)
    config = Configuration.from_dict(_read_json(collab / "configuration.json"))
    state = State.from_dict(_read_json(collab / "etat.json"))
    corpus_age_days: int | None = None
    if config.corpus_manifest_sha256 is not None:
        manifest = _read_json(collab / "corpus" / "manifeste.json")
        captured = datetime.strptime(
            str(manifest["captured_at"]), "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=UTC)
        corpus_age_days = (datetime.now(UTC) - captured).days
    payload = {
        "collaboration_id": config.collaboration_id, "mission_kind": config.mission_kind.value,
        "reviewer_access": config.reviewer_access.value, "status": state.status.value,
        "phase": state.phase.value, "revision": state.revision,
        "open_findings": len(state.open_finding_ids), "corpus_age_days": corpus_age_days,
        "last_incident": state.last_incident,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for key, value in payload.items():
            print(f"{key} : {value}")
    return 0


def _fail(message: str) -> int:
    print(f"erreur : {message}", file=sys.stderr)
    return 1


def _read_json(path: Path) -> Any:
    text, _ = storage.read_text(path)
    return json.loads(text)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    storage.write_atomic_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m iabinome")
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new")
    p_new.add_argument("collab")
    p_new.add_argument("--demande", required=True)
    p_new.add_argument("--kind", choices=sorted(_KIND), required=True)
    p_new.add_argument("--reviewer-access", choices=sorted(_ACCESS), required=True)
    p_new.add_argument("--agent-a", choices=sorted(ADAPTERS), required=True)
    p_new.add_argument("--agent-b", choices=sorted(ADAPTERS), required=True)
    p_new.add_argument("--source-root")
    p_new.add_argument("--source-list")
    p_new.add_argument("--source-label")
    p_new.add_argument("--model-a")
    p_new.add_argument("--model-b")
    p_new.add_argument("--max-revisions", type=int, default=2)
    p_new.set_defaults(func=cmd_new)

    p_run = sub.add_parser("run")
    p_run.add_argument("collab")
    p_run.add_argument("--timeout", type=float, default=1800.0)
    p_run.set_defaults(func=cmd_run)

    p_resume = sub.add_parser("resume")
    p_resume.add_argument("collab")
    p_resume.add_argument("--timeout", type=float, default=1800.0)
    p_resume.add_argument("--answer")
    p_resume.add_argument("--retry-call")
    p_resume.add_argument("--reason-file")
    p_resume.set_defaults(func=cmd_resume)

    p_status = sub.add_parser("status")
    p_status.add_argument("collab")
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result: int = args.func(args)
    return result

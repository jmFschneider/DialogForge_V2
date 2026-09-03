"""Enums fermés, configuration et état — validation stricte de schéma.

Version future, enum inconnu, clé absente ou surnuméraire : refus avant
toute mutation (CONCEPTION_FINALE.md §4). Les champs connus sans valeur
sont toujours présents, avec `null` au besoin — ils ne disparaissent jamais.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

SCHEMA_VERSION = 1

Decoder = Callable[[dict[str, Any], str], Any]


class SchemaError(ValueError):
    """Schéma invalide : refus avant toute mutation."""


class MissionKind(Enum):
    CONCEPTION = "CONCEPTION"
    RECHERCHE = "RECHERCHE"


class ReviewerAccess(Enum):
    CONTEXT_ONLY = "CONTEXT_ONLY"
    CONSULT = "CONSULT"


class Status(Enum):
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_HUMAN = "WAITING_HUMAN"
    INTERRUPTED = "INTERRUPTED"
    ERROR = "ERROR"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"


class Phase(Enum):
    PROPOSAL_A = "PROPOSAL_A"
    REVIEW_B = "REVIEW_B"
    REVISION_A = "REVISION_A"
    FINAL_A = "FINAL_A"
    CLOSED = "CLOSED"


class Role(Enum):
    A = "A"
    B = "B"


class CallStatus(Enum):
    CALLING = "CALLING"
    RESPONSE_STORED = "RESPONSE_STORED"


class Decision(Enum):
    ACCEPTER = "ACCEPTER"
    REVISER = "REVISER"
    BLOQUE = "BLOQUE"


class Severity(Enum):
    BLOCKING = "BLOCKING"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    NOTE = "NOTE"
    UNKNOWN = "UNKNOWN"


class Disposition(Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    WITHDRAWN = "WITHDRAWN"


# -- Décodage/encodage strict, partagé par les structures ci-dessous --

def _require_exact_keys(d: Any, keys: set[str], where: str) -> None:
    if not isinstance(d, dict):
        raise SchemaError(f"{where}: objet attendu")
    missing, extra = keys - d.keys(), d.keys() - keys
    if missing:
        raise SchemaError(f"{where}: clé(s) absente(s) {sorted(missing)}")
    if extra:
        raise SchemaError(f"{where}: clé(s) surnuméraire(s) {sorted(extra)}")


def _str(d: dict[str, Any], key: str) -> str:
    v = d[key]
    if not isinstance(v, str):
        raise SchemaError(f"{key}: chaîne attendue")
    return v


def _opt_str(d: dict[str, Any], key: str) -> str | None:
    v = d[key]
    if v is not None and not isinstance(v, str):
        raise SchemaError(f"{key}: chaîne ou null attendu")
    return v


def _int(d: dict[str, Any], key: str) -> int:
    v = d[key]
    if not isinstance(v, int) or isinstance(v, bool):
        raise SchemaError(f"{key}: entier attendu")
    return v


def _str_list(d: dict[str, Any], key: str) -> list[str]:
    v = d[key]
    if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
        raise SchemaError(f"{key}: liste de chaînes attendue")
    return list(v)


def _enum_of(cls: type[Enum]) -> Decoder:
    def decode(d: dict[str, Any], key: str) -> Enum:
        try:
            return cls(d[key])
        except ValueError:
            raise SchemaError(f"{key}: valeur inconnue {d[key]!r}") from None
    return decode


def _nested(cls: Any) -> Decoder:
    def decode(d: dict[str, Any], key: str) -> Any:
        v = d[key]
        if not isinstance(v, dict):
            raise SchemaError(f"{key}: objet attendu")
        return cls.from_dict(v)
    return decode


def _opt_nested(cls: Any) -> Decoder:
    def decode(d: dict[str, Any], key: str) -> Any:
        v = d[key]
        if v is None:
            return None
        if not isinstance(v, dict):
            raise SchemaError(f"{key}: objet ou null attendu")
        return cls.from_dict(v)
    return decode


def _schema_version(d: dict[str, Any], key: str) -> int:
    v = d[key]
    if v != SCHEMA_VERSION:
        raise SchemaError(f"{key}: {v!r} != {SCHEMA_VERSION} (version future ou obsolète)")
    return int(v)


def _decode(d: Any, fields: tuple[tuple[str, Decoder], ...], where: str) -> dict[str, Any]:
    _require_exact_keys(d, {k for k, _ in fields}, where)
    return {k: fn(d, k) for k, fn in fields}


def _encode(obj: Any, fields: tuple[tuple[str, Decoder], ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, _ in fields:
        v = getattr(obj, k)
        if isinstance(v, Enum):
            v = v.value
        elif hasattr(v, "to_dict"):
            v = v.to_dict()
        elif isinstance(v, list):
            v = list(v)
        out[k] = v
    return out


# -- Structures --

_AGENT_SPEC_FIELDS: tuple[tuple[str, Decoder], ...] = (
    ("adapter_id", _str),
    ("model", _str),
)


@dataclass(frozen=True)
class AgentSpec:
    adapter_id: str
    model: str

    @staticmethod
    def from_dict(d: dict[str, Any]) -> AgentSpec:
        return AgentSpec(**_decode(d, _AGENT_SPEC_FIELDS, "agent"))

    def to_dict(self) -> dict[str, Any]:
        return _encode(self, _AGENT_SPEC_FIELDS)


_CALL_STATE_FIELDS: tuple[tuple[str, Decoder], ...] = (
    ("call_id", _str),
    ("sequence", _int),
    ("role", _enum_of(Role)),
    ("phase", _enum_of(Phase)),
    ("status", _enum_of(CallStatus)),
    ("call_dir", _str),
    ("prompt_sha256", _str),
    ("response_sha256", _opt_str),
    ("started_at", _str),
    ("completed_at", _opt_str),
)


@dataclass(frozen=True)
class CallState:
    call_id: str
    sequence: int
    role: Role
    phase: Phase
    status: CallStatus
    call_dir: str
    prompt_sha256: str
    response_sha256: str | None
    started_at: str
    completed_at: str | None

    @staticmethod
    def from_dict(d: dict[str, Any]) -> CallState:
        return CallState(**_decode(d, _CALL_STATE_FIELDS, "current_call"))

    def to_dict(self) -> dict[str, Any]:
        return _encode(self, _CALL_STATE_FIELDS)


_CONFIGURATION_FIELDS: tuple[tuple[str, Decoder], ...] = (
    ("schema_version", _schema_version),
    ("collaboration_id", _str),
    ("mission_kind", _enum_of(MissionKind)),
    ("reviewer_access", _enum_of(ReviewerAccess)),
    ("max_revisions", _int),
    ("agent_a", _nested(AgentSpec)),
    ("agent_b", _nested(AgentSpec)),
    ("initial_demande_sha256", _str),
    ("corpus_manifest_sha256", _opt_str),
    ("created_at", _str),
)


@dataclass(frozen=True)
class Configuration:
    schema_version: int
    collaboration_id: str
    mission_kind: MissionKind
    reviewer_access: ReviewerAccess
    max_revisions: int
    agent_a: AgentSpec
    agent_b: AgentSpec
    initial_demande_sha256: str
    corpus_manifest_sha256: str | None
    created_at: str

    @staticmethod
    def from_dict(d: dict[str, Any]) -> Configuration:
        return Configuration(**_decode(d, _CONFIGURATION_FIELDS, "configuration"))

    def to_dict(self) -> dict[str, Any]:
        return _encode(self, _CONFIGURATION_FIELDS)


_STATE_FIELDS: tuple[tuple[str, Decoder], ...] = (
    ("schema_version", _schema_version),
    ("status", _enum_of(Status)),
    ("phase", _enum_of(Phase)),
    ("revision", _int),
    ("demande_sha256", _str),
    ("current_document", _opt_str),
    ("latest_review", _opt_str),
    ("open_finding_ids", _str_list),
    ("current_call", _opt_nested(CallState)),
    ("last_incident", _opt_str),
    ("updated_at", _str),
)


@dataclass(frozen=True)
class State:
    schema_version: int
    status: Status
    phase: Phase
    revision: int
    demande_sha256: str
    current_document: str | None
    latest_review: str | None
    open_finding_ids: list[str]
    current_call: CallState | None
    last_incident: str | None
    updated_at: str

    @staticmethod
    def from_dict(d: dict[str, Any]) -> State:
        return State(**_decode(d, _STATE_FIELDS, "etat"))

    def to_dict(self) -> dict[str, Any]:
        return _encode(self, _STATE_FIELDS)

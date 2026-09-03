"""Discriminateur A, schéma de revue B, bloc JSON unique, normalisation.

Un seul analyseur pour les quatre appels de A — finalisation comprise.
Jamais de défaut permissif : balise inconnue, décision inconnue, identifiant
dupliqué ou constat antérieur disparu sont un échec de contrat ; la réponse
brute reste à l'appelant, intacte (CONCEPTION_FINALE.md §6).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Collection
from dataclasses import dataclass
from typing import Any, Literal

from .models import SCHEMA_VERSION, Decision, Disposition, Severity

_TAG_DOCUMENT = "IABINOME:DOCUMENT"
_TAG_QUESTION = "IABINOME:QUESTION"

_REVIEW_KEYS = {"schema_version", "decision", "analysis", "findings"}
_FINDING_REQUIRED = {"id", "disposition", "statement"}
_FINDING_OPTIONAL = {"severity"}


class ContractError(ValueError):
    """Le contrat A ou B n'est pas respecté : la réponse brute doit être préservée."""


@dataclass(frozen=True)
class Normalized:
    text: str
    transformations: tuple[str, ...]
    sha256: str


def normalize(raw: str) -> Normalized:
    """BOM en tête toléré, retiré et consigné comme transformation ; le
    reste passe tel quel. L'empreinte porte sur le texte normalisé."""
    text = raw
    transformations: list[str] = []
    if text.startswith("﻿"):
        text = text[1:]
        transformations.append("bom_removed")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return Normalized(text=text, transformations=tuple(transformations), sha256=digest)


@dataclass(frozen=True)
class AgentResponse:
    kind: Literal["DOCUMENT", "QUESTION"]
    body: str


def parse_agent_response(text: str) -> AgentResponse:
    """La première ligne vaut exactement IABINOME:DOCUMENT ou
    IABINOME:QUESTION. Toute autre valeur est une erreur de contrat."""
    first_line, _, rest = text.partition("\n")
    if first_line == _TAG_DOCUMENT:
        return AgentResponse(kind="DOCUMENT", body=rest)
    if first_line == _TAG_QUESTION:
        return AgentResponse(kind="QUESTION", body=rest)
    raise ContractError(f"balise absente ou inconnue en première ligne : {first_line!r}")


@dataclass(frozen=True)
class Finding:
    id: str
    severity: Severity
    disposition: Disposition
    statement: str


@dataclass(frozen=True)
class Review:
    schema_version: int
    decision: Decision
    analysis: str
    findings: tuple[Finding, ...]


def parse_review(text: str, prior_open_finding_ids: Collection[str] = ()) -> Review:
    """Un unique bloc JSON clôturé couvrant toute la réponse. Chaque constat
    antérieurement ouvert doit être repris exactement une fois."""
    raw = _parse_sole_json_object(text)
    _require_keys(raw, _REVIEW_KEYS, set(), "revue")
    if raw["schema_version"] != SCHEMA_VERSION:
        raise ContractError(f"schema_version: {raw['schema_version']!r} inattendu")
    decision = _decode_enum(Decision, raw["decision"], "decision")
    analysis = _require_str(raw["analysis"], "analysis")
    if not isinstance(raw["findings"], list):
        raise ContractError("findings: liste attendue")
    findings = [_parse_finding(f) for f in raw["findings"]]
    _check_ids(findings, prior_open_finding_ids)
    return Review(
        schema_version=SCHEMA_VERSION, decision=decision, analysis=analysis,
        findings=tuple(findings),
    )


def open_finding_ids(review: Review) -> list[str]:
    """Dérivées du seul registre des constats — jamais une vérité seconde."""
    return [f.id for f in review.findings if f.disposition == Disposition.OPEN]


def has_open_blocking(review: Review) -> bool:
    return any(
        f.disposition == Disposition.OPEN and f.severity == Severity.BLOCKING
        for f in review.findings
    )


def _parse_finding(raw: Any) -> Finding:
    _require_keys(raw, _FINDING_REQUIRED, _FINDING_OPTIONAL, "constat")
    severity = (
        _decode_enum(Severity, raw["severity"], "severity")
        if "severity" in raw
        else Severity.UNKNOWN
    )
    return Finding(
        id=_require_str(raw["id"], "id"),
        severity=severity,
        disposition=_decode_enum(Disposition, raw["disposition"], "disposition"),
        statement=_require_str(raw["statement"], "statement"),
    )


def _check_ids(findings: list[Finding], prior_open_finding_ids: Collection[str]) -> None:
    seen: set[str] = set()
    for f in findings:
        if f.id in seen:
            raise ContractError(f"identifiant dupliqué : {f.id!r}")
        seen.add(f.id)
    missing = set(prior_open_finding_ids) - seen
    if missing:
        raise ContractError(f"constat(s) antérieur(s) disparu(s) : {sorted(missing)}")


def _strip_sole_fence(text: str) -> str:
    """Retire un unique bloc clôturé s'il couvre **toute** la réponse. Un
    préfixe, un suffixe ou une étiquette de langage autre que `json` laissent
    le texte intact — donc refusé plus bas, comme le veut §6."""
    stripped = text.strip()
    if not (stripped.startswith("```") and stripped.endswith("```")):
        return stripped
    first_line, _, rest = stripped.partition("\n")
    if first_line[3:].strip() not in ("", "json"):
        return stripped
    return rest[: rest.rfind("```")]


def _parse_sole_json_object(text: str) -> dict[str, Any]:
    try:
        raw = json.loads(_strip_sole_fence(text))
    except json.JSONDecodeError as exc:
        raise ContractError(f"JSON invalide : {exc}") from exc
    if not isinstance(raw, dict):
        raise ContractError("un objet JSON est attendu")
    return raw


def _require_keys(d: Any, required: set[str], optional: set[str], where: str) -> None:
    if not isinstance(d, dict):
        raise ContractError(f"{where}: objet attendu")
    keys = set(d)
    missing = required - keys
    if missing:
        raise ContractError(f"{where}: clé(s) absente(s) {sorted(missing)}")
    extra = keys - required - optional
    if extra:
        raise ContractError(f"{where}: clé(s) surnuméraire(s) {sorted(extra)}")


def _require_str(v: Any, key: str) -> str:
    if not isinstance(v, str):
        raise ContractError(f"{key}: chaîne attendue")
    return v


def _decode_enum(cls: Any, v: Any, key: str) -> Any:
    try:
        return cls(v)
    except ValueError:
        raise ContractError(f"{key}: valeur inconnue {v!r}") from None

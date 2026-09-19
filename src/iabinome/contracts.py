"""Discriminateur A, schéma de revue B, bloc JSON clôturé, normalisation.

Un seul analyseur pour les appels de A (proposition, révision).
Jamais de défaut permissif : balise inconnue, décision inconnue, identifiant
dupliqué ou constat antérieur disparu sont un échec de contrat ; la réponse
brute reste à l'appelant, intacte (CONCEPTION_FINALE.md §6).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Collection, Mapping
from dataclasses import dataclass, replace
from typing import Any, Literal

from .models import SCHEMA_VERSION, Decision, Disposition, ResponseKind, Severity

_TAG_DOCUMENT = "IABINOME:DOCUMENT"
_TAG_QUESTION = "IABINOME:QUESTION"
TAG_RESPONSES = "IABINOME:REPONSES"

# Revue v1 : sans `justification`. Revue v2 (1.2) : la justification d'une
# disposition est un champ à part, et une fermeture sans elle reste ouverte.
# Les deux se lisent — une revue historique v1 reste rejouable.
_REVIEW_VERSIONS = (1, 2)
_REVIEW_KEYS = {"schema_version", "decision", "analysis", "findings"}
_FINDING_REQUIRED = {"id", "disposition", "statement"}
_FINDING_OPTIONAL = {"severity", "justification"}


class ContractError(ValueError):
    """Le contrat A ou B n'est pas respecté : la réponse brute doit être préservée."""


@dataclass(frozen=True)
class Normalized:
    text: str
    transformations: tuple[str, ...]
    sha256: str


def normalize(raw: str) -> Normalized:
    """BOM en tête et fins de ligne `\\r\\n` tolérés et retirés ; le reste passe
    tel quel. L'empreinte porte sur le texte normalisé.

    `transformations` **n'est consigné nulle part** — le dire serait promettre
    une trace qui n'existe pas. Le diagnostic se refait en comparant la preuve
    brute (`appels/…/reponse_brute.txt`) à la forme canonique, ce qui est plus
    sûr qu'une étiquette (D-8b).

    §0.1 : tout est écrit en UTF-8 sans BOM, fins de ligne `\\n`, y compris sous
    Windows. Un producteur qui écrit en mode texte rend pourtant `\\r\\n`, et la
    balise `IABINOME:DOCUMENT` de la première ligne ne serait alors jamais
    reconnue. C'est une **tolérance**, pas la correction d'un défaut observé :
    la caractérisation du 2026-09-03 montre que les deux CLI rendent des `\\n`.
    Elle vaut par symétrie avec le BOM, et pour un producteur futur.

    Le brut, lui, reste intact sur le disque : c'est cette copie-ci qui est
    normalisée, pas la preuve.
    """
    text = raw
    transformations: list[str] = []
    if text.startswith("﻿"):
        text = text[1:]
        transformations.append("bom_removed")
    if "\r\n" in text:
        text = text.replace("\r\n", "\n")
        transformations.append("crlf_normalized")
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
    """Une objection de B. `statement` est l'**énoncé initial** : il ne change
    jamais une fois le constat ouvert. Pourquoi il reste ouvert, se résout ou se
    retire est dans `justification`."""

    id: str
    severity: Severity
    disposition: Disposition
    statement: str
    justification: str = ""


@dataclass(frozen=True)
class Review:
    schema_version: int
    decision: Decision
    analysis: str
    findings: tuple[Finding, ...]

    def to_dict(self) -> dict[str, Any]:
        """La forme **canonique** de la revue : valeurs d'enums, `analysis`
        conservée, et `severity` **toujours émise** — `UNKNOWN` comprise, là où
        B avait le droit de l'omettre.

        C'est elle qui est écrite dans `echanges/NNNN-critique-B.json`, et non
        le texte de B tel quel : un bloc clôturé ou une clé absente rendaient ce
        fichier illisible par `json.loads`, alors même que le programme s'en
        sert comme registre des constats. La preuve exacte, elle, reste
        `appels/…/reponse_brute.txt` — **aucun troisième artefact** n'est créé
        pour cela (D-8).
        """
        return {
            "schema_version": self.schema_version,
            "decision": self.decision.value,
            "analysis": self.analysis,
            "findings": [
                {
                    "id": f.id,
                    "severity": f.severity.value,
                    "disposition": f.disposition.value,
                    "statement": f.statement,
                    "justification": f.justification,
                }
                for f in self.findings
            ],
        }


def parse_review(
    text: str,
    prior_open_finding_ids: Collection[str] = (),
    prior_statements: Mapping[str, str] | None = None,
) -> Review:
    """JSON nu, ou un bloc JSON clôturé — la prose qui l'entoure est ignorée.
    Chaque constat antérieurement ouvert doit être repris exactement une
    fois.

    **L'énoncé initial ne s'écrase pas** (`prior_statements`, id → énoncé). Mesuré
    sur la revue réelle du 2026-09-05 : B a réécrit l'énoncé de ses sept constats
    pour y dire « désormais résolu ». Le programme garde l'énoncé initial ; le
    texte réécrit devient la justification si B n'en a pas donné — récupéré sans
    nouvel appel, et la preuve brute reste intacte.

    En revue v2, **une fermeture sans justification reste ouverte** : une absence
    ne clôture jamais un constat. Le maintien ne va que dans le sens sûr.
    """
    raw = _parse_sole_json_object(text)
    _require_keys(raw, _REVIEW_KEYS, set(), "revue")
    version = raw["schema_version"]
    if version not in _REVIEW_VERSIONS:
        raise ContractError(f"schema_version: {version!r} inattendu")
    decision = _decode_enum(Decision, raw["decision"], "decision")
    analysis = _require_str(raw["analysis"], "analysis")
    if not isinstance(raw["findings"], list):
        raise ContractError("findings: liste attendue")
    findings = [_parse_finding(f) for f in raw["findings"]]
    _check_ids(findings, prior_open_finding_ids)
    findings = [
        _keep_initial_statement(
            f, prior_statements or {}, version == 2, f.id in set(prior_open_finding_ids)
        )
        for f in findings
    ]
    return Review(
        schema_version=version, decision=decision, analysis=analysis,
        findings=tuple(findings),
    )


def _keep_initial_statement(
    f: Finding, initial: Mapping[str, str], justified_closures: bool, was_open: bool
) -> Finding:
    if f.id in initial and f.statement != initial[f.id]:
        f = replace(f, statement=initial[f.id], justification=f.justification or f.statement)
    if (
        justified_closures and was_open and f.disposition is not Disposition.OPEN
        and not f.justification.strip()
    ):
        f = replace(f, disposition=Disposition.OPEN)
    return f


@dataclass(frozen=True)
class ObjectionResponse:
    """La réponse de A à une objection ouverte. `justification` est du texte
    libre ; seuls l'identifiant et le genre sont exploités par le programme."""

    id: str
    kind: ResponseKind
    justification: str

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "response": self.kind.value, "justification": self.justification}


def split_responses(body: str) -> tuple[str, str | None]:
    """Sépare le document du bloc de réponses, introduit par une ligne
    `IABINOME:REPONSES` — la **dernière**, pour que le document puisse la citer.
    Le document reste du texte libre ; le bloc seul est structuré."""
    lines = body.split("\n")
    for index in range(len(lines) - 1, -1, -1):
        if lines[index].strip() == TAG_RESPONSES:
            return "\n".join(lines[:index]).rstrip() + "\n", "\n".join(lines[index + 1:])
    return body, None


def parse_objection_responses(
    block: str | None, open_ids: Collection[str]
) -> tuple[ObjectionResponse, ...]:
    """Chaque objection ouverte reçoit **exactement une** réponse. Identifiant
    absent, dupliqué ou inconnu : échec de contrat, jamais un avis par défaut.

    Le bloc se lit comme la revue : JSON nu ou clôturé, prose alentour ignorée —
    un préambule n'est pas une raison de repayer un appel.
    """
    if block is None:
        if open_ids:
            raise ContractError(
                f"bloc {TAG_RESPONSES} absent : réponse attendue pour {sorted(open_ids)}"
            )
        return ()
    raw = _parse_sole_json_object(block)
    _require_keys(raw, {"schema_version", "responses"}, set(), "réponses")
    if raw["schema_version"] != SCHEMA_VERSION:
        raise ContractError(f"schema_version: {raw['schema_version']!r} inattendu")
    if not isinstance(raw["responses"], list):
        raise ContractError("responses: liste attendue")
    responses: list[ObjectionResponse] = []
    for entry in raw["responses"]:
        _require_keys(entry, {"id", "response"}, {"justification"}, "réponse")
        kind = _decode_enum(ResponseKind, entry["response"], "response")
        justification = _require_str(entry.get("justification", ""), "justification")
        if kind is not ResponseKind.CORRIGE and not justification.strip():
            raise ContractError(
                f"{entry['id']!r} : {kind.value} exige une justification"
            )
        responses.append(ObjectionResponse(_require_str(entry["id"], "id"), kind, justification))
    ids = [r.id for r in responses]
    duplicated = sorted({i for i in ids if ids.count(i) > 1})
    if duplicated:
        raise ContractError(f"réponse dupliquée pour : {duplicated}")
    unknown = sorted(set(ids) - set(open_ids))
    if unknown:
        raise ContractError(f"réponse à un constat qui n'est pas ouvert : {unknown}")
    missing = sorted(set(open_ids) - set(ids))
    if missing:
        raise ContractError(f"objection(s) ouverte(s) sans réponse : {missing}")
    return tuple(responses)


def responses_to_dict(responses: tuple[ObjectionResponse, ...]) -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "responses": [r.to_dict() for r in responses]}


def responses_from_dict(raw: Any) -> tuple[ObjectionResponse, ...]:
    """Relit la forme canonique écrite par `responses_to_dict`."""
    _require_keys(raw, {"schema_version", "responses"}, set(), "réponses")
    return tuple(
        ObjectionResponse(
            _require_str(e["id"], "id"),
            _decode_enum(ResponseKind, e["response"], "response"),
            _require_str(e["justification"], "justification"),
        )
        for e in raw["responses"]
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
    """Sévérité omise → `UNKNOWN`, **et le constat reste ouvert** (§6).

    La tolérance sur `severity` ne doit pas devenir un moyen de **fermer** un
    constat : sans ce maintien, B pouvait omettre la sévérité et rendre
    `RESOLVED` dans le même constat, le retirer du registre et emmener le cycle
    à la promotion. L'omission n'ouvre jamais rien de plus qu'elle-même.

    Le maintien ne va que dans le sens sûr — il laisse ouvert, il ne ferme
    jamais — et c'est pourquoi il n'est pas un jugement du programme sur les
    sévérités, que §6 interdit par ailleurs.
    """
    _require_keys(raw, _FINDING_REQUIRED, _FINDING_OPTIONAL, "constat")
    given = _decode_enum(Disposition, raw["disposition"], "disposition")
    omitted = "severity" not in raw
    return Finding(
        id=_require_str(raw["id"], "id"),
        severity=Severity.UNKNOWN if omitted else _decode_enum(
            Severity, raw["severity"], "severity"
        ),
        disposition=Disposition.OPEN if omitted else given,
        statement=_require_str(raw["statement"], "statement"),
        justification=_require_str(raw.get("justification", ""), "justification"),
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


def _strip_fence(text: str) -> str:
    """Retire un bloc clôturé, **même entouré de prose** — voie B tranchée par
    le PO le 2026-09-05, §6 d'`OBSERVATIONS_MISSION_REELLE.md`.

    Motif : en mission réelle, B a fait précéder une revue juste de 3,6 Ko
    d'une phrase expliquant son choix de format. La réponse a été refusée,
    231 s d'appel payant perdues. Un agent qui commente son format n'est ni
    rare ni désobéissant.

    L'ancrage est **première clôture → dernière clôture**, jamais un comptage :
    B a le droit de citer du markdown dans `analysis`, et compter les clôtures
    y découperait au mauvais endroit.

    Ce qui laisse le texte **intact** — donc refusé plus bas, comme le veut
    §6 : aucune clôture, une clôture jamais fermée, une étiquette de langage
    autre que `json`. Ce n'est pas un défaut permissif : on n'extrait que ce
    qui est explicitement balisé, sans jamais deviner où le JSON commence, et
    `json.loads` reste l'arbitre — deux blocs distincts rendent un texte
    invalide, donc un refus.
    """
    stripped = text.strip()
    opening = stripped.find("```")
    if opening < 0 or stripped.rfind("```") == opening:
        return stripped
    first_line, _, rest = stripped[opening:].partition("\n")
    if first_line[3:].strip() not in ("", "json"):
        return stripped
    return rest[: rest.rfind("```")]


def _parse_sole_json_object(text: str) -> dict[str, Any]:
    try:
        raw = json.loads(_strip_fence(text))
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

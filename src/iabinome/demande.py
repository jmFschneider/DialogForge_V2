"""Le format court de demande, son cadrage guidé, et sa provenance (plan V2, 1.1).

Six sections : objectif, livrable, sources, contraintes, non-objectifs, critères
de fin. **Le format est un repère, pas une porte** : une demande libre reste
acceptée, `missing()` dit seulement ce qui manque, et A rend `IABINOME:QUESTION`
quand l'absence change le résultat (`prompts.py`). Un contrôle de plus ne
compenserait aucun défaut mesuré.

Le cadrage guidé est un questionnaire de terminal : **aucun appel de modèle**.
Une demande qui suffit n'en paie donc jamais un, et une qui ne suffit pas n'en
paie pas non plus avant que A ait lu ce qui lui manque.

La provenance est un fichier lisible à l'œil, ajouté à chaque version de la
demande — d'où elle vient, ce qu'elle remplace, à quelle revue l'ancienne
répondait. Une réponse humaine **complète** la demande (`complete`) : elle ne
la remplace jamais, donc n'en retire rien.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import storage

PROVENANCE = "provenance_demande.json"

SECTIONS = ("Objectif", "Livrable", "Sources", "Contraintes", "Non-objectifs", "Critères de fin")

_QUESTIONS = {
    "Objectif": "Que faut-il établir, et pour qui ?",
    "Livrable": "Quel document attend-on en sortie ?",
    "Sources": "Sur quoi s'appuyer ? (documents, périmètre — vide si rien)",
    "Contraintes": "Quelles limites : délai, format, choix déjà faits ? (vide si aucune)",
    "Non-objectifs": "Qu'est-ce qui est explicitement hors sujet ? (vide si rien)",
    "Critères de fin": "À quoi reconnaît-on que c'est fini ? (vide si à A de proposer)",
}
_REQUIRED = ("Objectif", "Livrable")
_UNSPECIFIED = "Non précisé."

_HEADING = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t#]*$")
_FENCE = re.compile(r"^\s*(```|~~~)")
_COMPLEMENT = re.compile(r"^## Précisions n°\d+", re.MULTILINE)


def _key(title: str) -> str:
    plain = unicodedata.normalize("NFD", title)
    plain = "".join(c for c in plain if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", plain.casefold()).split())


_CANONICAL = {_key(name): name for name in SECTIONS}


def sections(text: str) -> dict[str, str]:
    """Les sections **renseignées** de la demande, par nom canonique.

    Un titre reconnu ouvre une section ; un autre titre de niveau égal ou
    supérieur la ferme, un sous-titre plus profond en fait partie. Les lignes
    d'un bloc de code ne sont jamais des titres.
    """
    bodies: dict[str, list[str]] = {}
    current: tuple[str, int] | None = None
    fenced = False
    for line in text.splitlines():
        if _FENCE.match(line):
            fenced = not fenced
        heading = None if fenced else _HEADING.match(line)
        if heading:
            level, name = len(heading.group(1)), _CANONICAL.get(_key(heading.group(2)))
            if name is not None:
                current = (name, level)
                bodies.setdefault(name, [])
                continue
            if current is not None and level <= current[1]:
                current = None
        if current is not None:
            bodies[current[0]].append(line)
    body_of = {name: "\n".join(lines).strip() for name, lines in bodies.items()}
    return {name: body for name, body in body_of.items() if body}


def missing(text: str) -> list[str]:
    found = sections(text)
    return [name for name in SECTIONS if name not in found]


def complete(base: str, answer: str) -> str:
    """La demande complétée par une réponse : **le texte existant en préfixe,
    intact**, puis la réponse telle quelle sous « Précisions n°K ».

    `--answer` est un complément, jamais un remplacement : aucune section ni
    exigence ne peut disparaître, puisque rien n'est réécrit. Le résultat est
    une version **complète** de `demande.md`, qui reste l'unique autorité.

    Le numéro se déduit du texte de base et non de l'horloge : au rejeu après un
    arrêt brutal, le même appel doit redonner **la même empreinte**, sans quoi la
    demande déjà écrite ne serait plus reconnue. La date est dans la provenance.
    """
    number = len(_COMPLEMENT.findall(base)) + 1
    return f"{base.rstrip()}\n\n## Précisions n°{number}\n\n{answer.strip()}\n"


def guide(ask: Callable[[str], str], say: Callable[[str], None]) -> str:
    """Le questionnaire. Une réponse par section, close par une ligne vide ; une
    section facultative laissée vide devient « Non précisé. », que `sections`
    tient pour renseignée — c'est un choix de l'humain, pas un oubli."""
    say("Cadrage de la demande : une réponse par section, terminée par une ligne vide.")
    parts = ["# Demande", ""]
    for name in SECTIONS:
        parts += [f"## {name}", "", _answer(name, ask, say), ""]
    return "\n".join(parts)


def _answer(name: str, ask: Callable[[str], str], say: Callable[[str], None]) -> str:
    while True:
        lines: list[str] = []
        line = ask(f"\n{name} — {_QUESTIONS[name]}\n> ")
        while line.strip():
            lines.append(line.rstrip())
            line = ask("> ")
        if lines:
            return "\n".join(lines)
        if name not in _REQUIRED:
            return _UNSPECIFIED
        say(f"La section « {name} » est nécessaire.")


def read(collab: Path) -> list[dict[str, Any]]:
    path = collab / PROVENANCE
    if not path.exists():
        return []
    text, _ = storage.read_text(path)
    versions: list[dict[str, Any]] = json.loads(text)["versions"]
    return versions


def record(collab: Path, entry: dict[str, Any]) -> None:
    """Ajoute une version. **Rejouable** : un rejeu de la même empreinte n'ajoute
    rien, comme l'archive de la demande (`workflow._archive`)."""
    versions = read(collab)
    if versions and versions[-1]["sha256"] == entry["sha256"]:
        return
    versions.append({
        "sequence": len(versions) + 1,
        "at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **entry,
    })
    payload = {"schema_version": 1, "versions": versions}
    storage.write_atomic_text(
        collab / PROVENANCE, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )

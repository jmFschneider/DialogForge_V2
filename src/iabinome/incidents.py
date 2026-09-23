"""Ce que l'humain comprend d'un incident, sans ouvrir un journal (plan V2, 2.1).

Trois choses qu'un incident peut être, et qu'il ne faut pas confondre :

- une **réponse reçue mais mal interprétée** — elle a été payée, elle est sur
  disque, l'interpréter peut se refaire **localement** (`resume --reprocess`) ;
- un **appel qui n'est pas parti** (`LAUNCH_FAILED`) — rien n'a été payé ;
- une **issue inconnue** — délai, interruption, arrêt brutal, code de retour non
  nul : l'appel a pu partir et être payé, et rien ne permet de trancher.

**On ne prétend pas savoir ce qu'on ne sait pas.** Un code de retour non nul ne
distingue pas un quota épuisé d'une erreur de configuration : le message de
l'outil est montré **tel quel**, et aucun coût ni aucune heure de reprise n'est
déduit ou inventé. Rien ici n'est relancé automatiquement.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import storage
from .models import State, Status

_EXCERPT_CHARS = 300


@dataclass(frozen=True)
class Kind:
    paid: str  # « oui », « non », « peut-être » ou « inconnu » — jamais un montant
    meaning: str


KINDS = {
    "LAUNCH_FAILED": Kind(
        "non",
        "l'outil n'a pas démarré (exécutable introuvable ou refusé par le système) : l'appel"
        " n'est pas parti",
    ),
    "TIMEOUT": Kind(
        "peut-être",
        "le délai dur (`--timeout`) est écoulé et l'outil a été arrêté : rien ne dit si la"
        " réponse était presque prête",
    ),
    "OUTPUT_LIMIT": Kind(
        "peut-être", "la sortie a dépassé la limite : l'outil a été arrêté avant la fin"
    ),
    "INTERRUPTED_BY_USER": Kind(
        "peut-être", "vous avez interrompu l'appel (Ctrl+C) : l'outil a été arrêté"
    ),
    "STREAMS_UNCLOSED": Kind(
        "peut-être", "les flux de l'outil n'ont pas pu être lus jusqu'à la fin : ce qui est sur"
        " disque est peut-être partiel",
    ),
    "STREAM_FAILED": Kind(
        "peut-être", "la lecture d'un flux a échoué : ce qui est sur disque est peut-être partiel"
    ),
    "CALL_POSSIBLY_PAID": Kind(
        "inconnu",
        "le processus s'est arrêté pendant un appel : impossible de savoir s'il est parti, s'il"
        " a été payé, ni ce qu'il a répondu",
    ),
    "CLI_FAILED": Kind(
        "inconnu",
        "l'outil a rendu un code de retour non nul ; ce code ne distingue pas un quota épuisé"
        " d'une erreur de configuration ou de modèle",
    ),
    "INTEGRITY_MISMATCH": Kind(
        "inconnu",
        "un fichier de l'appel ne correspond plus à l'empreinte de l'état : il a été modifié"
        " depuis — rien n'est repris à partir d'une preuve contredite",
    ),
    "SOURCES_MODIFIED": Kind(
        "peut-être",
        "le corpus a changé pendant l'appel : la réponse n'est pas retenue, elle a été produite"
        " sur des sources qui ne sont plus celles du manifeste",
    ),
    "CONTRACT_ERROR": Kind(
        "oui",
        "la réponse est arrivée mais ne respecte pas le contrat ; elle est conservée telle"
        " quelle",
    ),
    "DECODE_FAILED": Kind(
        "oui",
        "la réponse est arrivée mais ses octets sont illisibles ; ils sont conservés tels quels",
    ),
}
_RECEIVED = ("CONTRACT_ERROR", "DECODE_FAILED")


def incident(collab: Path, state: State) -> dict[str, Any] | None:
    if state.last_incident is None or not (collab / state.last_incident).is_file():
        return None
    data: dict[str, Any] = json.loads(storage.read_text(collab / state.last_incident)[0])
    return data


def _tool_message(collab: Path, state: State) -> list[str]:
    """Le message de l'outil, **tel quel** : c'est lui qui dit, s'il le dit, ce qu'il
    en est du quota ou de la configuration. Le programme n'en tire rien."""
    if state.current_call is None:
        return []
    lines = []
    for name in ("stderr", "stdout"):
        path = collab / state.current_call.call_dir / f"{name}.txt"
        if path.is_file():
            text = path.read_bytes().decode("utf-8", errors="replace").strip()
            if text:
                shown = " ".join(text[:_EXCERPT_CHARS].split())
                more = "…" if len(text) > _EXCERPT_CHARS else ""
                lines.append(f"  {name} de l'outil : « {shown}{more} »")
    return lines


def explain(collab: Path, state: State) -> list[str]:
    """Les lignes d'un incident : ce qui s'est passé, si c'est payé, ce qu'on ne sait pas."""
    found = incident(collab, state)
    if found is None:
        return []
    kind = KINDS.get(found["kind"])
    lines = [f"Incident : {found['kind']} — {found.get('detail') or 'sans détail'}"]
    if kind is None:
        return lines + ["  Payé ? : inconnu (incident d'un genre non catalogué)"]
    lines += [f"  Sens : {kind.meaning}", f"  Payé ? : {kind.paid}"]
    if found["kind"] == "CLI_FAILED":
        lines += _tool_message(collab, state) or ["  (l'outil n'a rien écrit)"]
        lines.append("  Aucun coût ni aucune heure de reprise n'est déduit de ce code.")
    return lines


def relaunchable(collab: Path, state: State) -> bool:
    """L'appel courant peut-il sortir de son arrêt ? `INTERRUPTED` se relance ;
    `ERROR` seulement par la **table fermée** des réponses reçues mais mal lues,
    et pour son propre appel (N-01). Le moteur et les actions permises lisent
    cette règle ici, et nulle part ailleurs."""
    call = state.current_call
    if call is None:
        return False
    if state.status is Status.INTERRUPTED:
        return True
    if state.status is not Status.ERROR or state.last_incident is None:
        return False
    if not state.last_incident.startswith(f"{call.call_dir}/"):
        return False
    found = incident(collab, state)
    return isinstance(found, dict) and found.get("kind") in _RECEIVED

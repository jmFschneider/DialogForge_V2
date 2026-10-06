"""Attendre la réinitialisation d'une période d'usage, puis continuer la même session.

`conception/REPRISE_QUOTA_V3.md`, accepté par le PO le 2026-10-05. Ce module ne reconnaît
rien : chaque adaptateur dit, à sa frontière, si une sortie est un refus de période et
quelle heure il annonce. Ici, on interprète cette heure et on attend, dans l'exécution en
cours — ni worker, ni tâche planifiée, ni compteur de reprises.

**Sans heure fiable, on s'arrête** : aucun délai de repli n'est inventé. Le prédécesseur
retentait à l'aveugle toutes les 15 minutes, pendant des heures (`ARRET_REFACTORING.md` §2).
"""

from __future__ import annotations

import re
import time
from datetime import UTC, date, datetime, timedelta, tzinfo
from datetime import time as clock
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .transport import ExecutionControl

# L'heure annoncée plus deux minutes : la période est rendue, sans course avec l'outil.
MARGIN = timedelta(minutes=2)
# Une heure passée depuis si peu vient d'être franchie : elle ne vaut pas pour le lendemain.
_JUST_PASSED = timedelta(minutes=5)
_POLL_SECONDS = 1.0

# La consigne de continuation, envoyée **à la session interrompue** : jamais le prompt
# d'origine. Elle exige la réponse entière, car le contrat lit un document complet.
CONTINUATION = (
    "Le tour précédent a été interrompu par la limite d'usage de l'outil. Reprends le "
    "travail là où tu en étais et rends ta réponse complète, au format demandé.\n"
)

_ANNOUNCED = re.compile(r"\s*(?P<time>[^()]+?)\s*(?:\((?P<zone>[^()]+)\))?\s*")
_CLOCK = re.compile(r"(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s*(?P<p>[ap]m)?", re.IGNORECASE)


class QuotaError(ValueError):
    """Heure annoncée inexploitable : forme inconnue, ambiguë ou inexistante."""


def now() -> datetime:
    """Point d'injection des tests : l'horloge de l'attente."""
    return datetime.now(UTC)


def sleep(seconds: float) -> None:
    """Point d'injection des tests : le pas de l'attente."""
    time.sleep(seconds)


def resume_at(announced: str, received: datetime) -> datetime:
    """L'instant de reprise : l'heure annoncée, lue à partir de l'instant de réception,
    plus `MARGIN`. Une heure déjà passée vaut pour le lendemain, sauf si elle vient de
    passer. Le fuseau nommé est lu s'il est connu ; sinon (Windows n'a pas de base de
    fuseaux), l'heure locale de la machine — celle d'où la CLI tire ce libellé."""
    found = _ANNOUNCED.fullmatch(announced)
    if found is None:
        raise QuotaError(f"heure annoncée illisible : {announced!r}")
    at = _clock(found["time"])
    zone = _zone(found["zone"])
    today = received.astimezone(zone).date() if zone else received.astimezone().date()
    target = _on(today, at, zone)
    if target < received - _JUST_PASSED:
        target = _on(today + timedelta(days=1), at, zone)
    return target + MARGIN


def wait_until(target: datetime, control: ExecutionControl | None) -> bool:
    """Attend `target` ; rend `False` si la pause ou l'arrêt l'ont interrompue."""
    while True:
        if control is not None and control.stopping():
            return False
        left = (target - now()).total_seconds()
        if left <= 0:
            return True
        sleep(min(left, _POLL_SECONDS))


def _clock(text: str) -> clock:
    """`8:50pm`, `8:50 pm`, `8pm` ou `20:50` — lu à la main : `%p` dépend de la locale."""
    found = _CLOCK.fullmatch(text.strip())
    if found is None:
        raise QuotaError(f"heure annoncée illisible : {text!r}")
    hour, minute = int(found["h"]), int(found["m"] or 0)
    if found["p"] is not None:
        if not 1 <= hour <= 12:
            raise QuotaError(f"heure annoncée illisible : {text!r}")
        hour = hour % 12 + (12 if found["p"].lower() == "pm" else 0)
    elif found["m"] is None:
        raise QuotaError(f"heure annoncée illisible : {text!r}")
    if hour > 23 or minute > 59:
        raise QuotaError(f"heure annoncée illisible : {text!r}")
    return clock(hour, minute)


def _zone(name: str | None) -> tzinfo | None:
    if name is None:
        return None
    try:
        return ZoneInfo(name.strip())
    except (ZoneInfoNotFoundError, ValueError):
        return None


def _on(day: date, at: clock, zone: tzinfo | None) -> datetime:
    """Cette heure ce jour-là ; un changement d'heure la rend ambiguë ou inexistante."""
    naive = datetime.combine(day, at)
    if zone is not None:
        first, second = naive.replace(tzinfo=zone), naive.replace(tzinfo=zone, fold=1)
    else:
        first, second = naive.astimezone(), naive.replace(fold=1).astimezone()
    if first.utcoffset() != second.utcoffset():
        raise QuotaError(f"heure annoncée prise dans un changement d'heure : {at:%H:%M}")
    return first

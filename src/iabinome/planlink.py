"""Une référence **facultative** vers un plan PWF (plan V2, 2.3) — et rien de plus.

La collaboration reste lisible, jouable et décidable sans elle : la liaison vit dans un
fichier à part (`plan.json`), que le cycle ne lit jamais. La retirer, c'est le supprimer ;
cela ne touche ni l'état, ni les livrables, et ne déclenche aucun appel.

**Un seul propriétaire du plan : le plan.** Ce module ne l'écrit jamais et ne copie aucune de
ses phases. Il **résout** le plan par les scripts publics de PWF, et fournit au propriétaire
un résumé et un lien à reporter **à la main** — aucune synchronisation entre l'état A/B et
les cases du plan.

Le résolveur public rend **toujours 0** : refus, ambiguïté, plan inconnu, sélection mal
formée, tout y passe par une **sortie vide**. Une sortie vide avec un code 0 n'est donc
**pas un succès**, c'est le refus lui-même (mesuré le 2026-09-19 sur un projet à deux plans,
un identifiant inexistant et un identifiant hors gabarit). À l'inverse, un plan épinglé sans
`task_plan.md` est rendu tel quel par le script : c'est ici qu'on le refuse.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import decisions, storage
from .models import SCHEMA_VERSION, Configuration, State

PLAN_FILE = "plan.json"
_TIMEOUT_SECONDS = 30.0
_RESOLVER = ("skills", "planning-with-files", "scripts", "resolve-plan-dir.sh")

Runner = Callable[..., "subprocess.CompletedProcess[str]"]


class PlanLinkError(RuntimeError):
    """La liaison n'a pas pu être établie ou relue — jamais fatale pour la collaboration."""


@dataclass(frozen=True)
class Link:
    plan_id: str
    plan_root: str
    linked_at: str


def default_resolver() -> Path:
    return Path.home().joinpath(".claude", *_RESOLVER)


def resolve(
    plan_id: str,
    plan_root: Path,
    *,
    script: Path | None = None,
    runner: Runner = subprocess.run,
) -> Path:
    """Le dossier du plan `plan_id` sous `plan_root`, ou `PlanLinkError` qui dit pourquoi.

    L'identifiant est **épinglé** (`PLAN_ID` et `PWF_PLAN_ROOT` posés explicitement, ceux de
    l'environnement courant écrasés) : on ne retombe jamais sur un autre plan."""
    script = script or default_resolver()
    if not script.is_file():
        raise PlanLinkError(
            f"script public de résolution introuvable ({script}) : PWF n'est pas installé ici"
        )
    shell = shutil.which("sh")
    if shell is None:
        raise PlanLinkError("`sh` introuvable : le script public de PWF ne peut pas être lancé")
    env = {**os.environ, "PLAN_ID": plan_id, "PWF_PLAN_ROOT": str(plan_root.resolve())}
    try:
        done = runner(
            [shell, str(script)], capture_output=True, text=True, env=env,
            timeout=_TIMEOUT_SECONDS, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PlanLinkError(f"le résolveur n'a pas pu être lancé : {exc}") from exc
    if done.returncode != 0:
        raise PlanLinkError(
            f"le résolveur a échoué (code {done.returncode}) : {done.stderr.strip()[:200]}"
        )
    lines = done.stdout.strip().splitlines()
    if not lines:
        raise PlanLinkError(
            f"sortie vide avec un code 0 : ce n'est pas un succès. Le plan {plan_id!r} n'a pas"
            f" été résolu sous {plan_root} (identifiant inexistant, mal formé ou sélection"
            " ambiguë) — `plan-doctor.sh` de PWF le diagnostique"
        )
    directory = Path(lines[0].strip())
    if directory.name != plan_id:
        raise PlanLinkError(
            f"le résolveur a rendu un autre plan ({directory.name!r}) que {plan_id!r} : refusé"
        )
    if not (directory / "task_plan.md").is_file():
        raise PlanLinkError(f"{directory} ne contient pas de `task_plan.md` : pas un plan")
    return directory


def read(collab: Path) -> Link | None:
    """La liaison, `None` s'il n'y en a pas, `PlanLinkError` si le fichier est illisible.
    L'appelant le **dit** ; la collaboration, elle, n'en dépend jamais."""
    path = collab / PLAN_FILE
    if not path.is_file():
        return None
    try:
        raw: Any = json.loads(storage.read_text(path)[0])
        return Link(str(raw["plan_id"]), str(raw["plan_root"]), str(raw["linked_at"]))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise PlanLinkError(f"{PLAN_FILE} illisible ({exc}) : à corriger ou à retirer") from exc


def link(collab: Path, plan_id: str, plan_root: Path, **resolver: Any) -> Path:
    """Résout **d'abord**, écrit ensuite : un plan qui ne se résout pas ne laisse aucune trace."""
    directory = resolve(plan_id, plan_root, **resolver)
    payload = {
        "schema_version": SCHEMA_VERSION, "plan_id": plan_id,
        "plan_root": str(plan_root.resolve()),
        "linked_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    storage.write_atomic_text(
        collab / PLAN_FILE, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )
    return directory


def unlink(collab: Path) -> bool:
    """Retire la liaison. Rien d'autre : ni l'état, ni un livrable, ni un appel."""
    path = collab / PLAN_FILE
    if not path.is_file():
        return False
    path.unlink()
    return True


def summary(collab: Path, **resolver: Any) -> list[str]:
    """Ce que le propriétaire du plan reporte **à la main** — lisible sans PWF, sans liaison.

    La liaison n'y ajoute que sa propre ligne : résolue, ou non résolue et pourquoi. Une
    liaison qui ne se résout plus n'empêche jamais le résumé."""
    config_text, _ = storage.read_text(collab / "configuration.json")
    state_text, _ = storage.read_text(collab / "etat.json")
    config = Configuration.from_dict(json.loads(config_text))
    state = State.from_dict(json.loads(state_text))
    lines: list[str] = []
    try:
        found = read(collab)
        if found is None:
            lines.append("Plan PWF : aucune liaison (la collaboration n'en a pas besoin).")
        else:
            try:
                where = resolve(found.plan_id, Path(found.plan_root), **resolver)
                lines.append(f"Plan PWF : {found.plan_id} (résolu : {where}).")
            except PlanLinkError as exc:
                lines.append(f"Plan PWF : {found.plan_id} — NON RÉSOLU : {exc}")
    except PlanLinkError as exc:
        lines.append(f"Plan PWF : liaison inutilisable — {exc}")
    lines += [
        "À reporter dans le plan, à la main (l'outil n'écrit jamais dans un plan) :",
        f"  Collaboration `{config.collaboration_id}` — {config.mission_kind.value},"
        f" statut {state.status.value}, phase {state.phase.value}, révision {state.revision},"
        f" objections ouvertes : {len(state.open_finding_ids)}.",
        f"  Décision : {decisions.describe(collab, state)}.",
        f"  Prochaine action : {decisions.next_action(collab, state)}.",
        f"  Dossier : {collab.resolve()}",
    ]
    if state.current_document is not None:
        lines.append(f"  Document : {collab.resolve() / state.current_document}")
    if state.latest_review is not None:
        lines.append(f"  Dernière revue : {collab.resolve() / state.latest_review}")
    return lines

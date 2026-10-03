"""Dossier de mission (`conception/PARCOURS_MISSION_CONCEPTION.md` §3, lot 2).

`mission.json` est un **registre de rattachement** : il dit quelles collaborations appartiennent à
la mission et d'où elles viennent, pour naviguer. Il ne porte ni statut, ni décision, ni état
d'exécution : ceux-ci restent dans les collaborations, relus à chaque affichage. Aucun appel IA ici.

Un fichier invalide donne un diagnostic (`MissionError`) ; il n'est jamais réinitialisé en silence.
Le verrou de mission n'est tenu que le temps d'une écriture locale, jamais pendant un appel.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import uuid
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from . import lock, storage
from .models import Configuration, CreationError, MissionKind, SchemaError, State, Status

if TYPE_CHECKING:
    from .facade import CreationRequest, CreationResult

REGISTRY = "mission.json"
LOCK = "verrou-mission.json"
TRANSITION = "provenance_transition.json"
_KINDS = {
    "recherche": MissionKind.RECHERCHE, "conception": MissionKind.CONCEPTION,
    "revue": MissionKind.RECHERCHE,  # une revue de code reste une boucle documentaire (§3.1)
}
_ABSOLUTE = re.compile(r"[A-Za-z]:[\\/]|(?<![\w.])/(?:home|mnt|usr|tmp)/")
_HISTORY = ("appels", "cadrage", "echanges")
_ATTACH = "dialogforge mission attach"


class MissionError(CreationError):
    """Registre invalide, rattachement refusé ou création impossible dans la mission : un refus
    de création, que la CLI et la GUI affichent déjà tel quel."""


@dataclass(frozen=True)
class Step:
    path: str
    role: str
    source: str | None


@dataclass(frozen=True)
class Mission:
    root: Path
    name: str
    steps: tuple[Step, ...]


@dataclass(frozen=True)
class Located:
    mission: Mission
    rel: str  # chemin relatif à la mission ; "." pour la racine
    step: Step | None


@dataclass(frozen=True)
class Target:
    """Ce que l'ouverture d'un dossier désigne : la collaboration à suivre et sa mission."""

    root: Path | None
    step: str | None
    collab: Path


@dataclass(frozen=True)
class StepView:
    step: Step
    path: Path
    label: str
    updated_at: str | None


@dataclass(frozen=True)
class Summary:
    mission: Mission
    steps: tuple[StepView, ...]
    to_attach: tuple[str, ...]
    partial: tuple[str, ...]

    @property
    def updated_at(self) -> str | None:
        return max((v.updated_at for v in self.steps if v.updated_at), default=None)

    def line(self) -> str:
        return " · ".join(f"{_name(self.mission, v.step)} : {v.label}" for v in self.steps) or (
            "aucune étape rattachée"
        )

    def render(self) -> list[str]:
        lines = [f"mission {self.mission.name} — {len(self.steps)} étape(s)"]
        lines += [
            f"  {_name(self.mission, v.step):<14} {v.label}  [{v.path}]" for v in self.steps
        ]
        lines += [f"  à rattacher : {rel} — {_ATTACH} <racine> {rel} --role <rôle>"
                  for rel in self.to_attach]
        lines += [f"  dossier partiel, à inspecter : {rel}" for rel in self.partial]
        return lines


# -- Registre --


def load(root: Path) -> Mission:
    path = root / REGISTRY
    try:
        raw = json.loads(storage.read_text(path)[0])
    except (OSError, ValueError) as exc:
        raise MissionError(f"{path} : illisible ({exc})") from exc
    try:
        if not isinstance(raw, dict) or set(raw) != {"schema_version", "name", "steps"}:
            raise ValueError("clés attendues : schema_version, name, steps")
        if raw["schema_version"] != 1:
            raise ValueError(f"schéma {raw['schema_version']!r} non géré")
        if not isinstance(raw["name"], str) or not raw["name"].strip():
            raise ValueError("name : texte non vide attendu")
        steps = tuple(_step(root, item) for item in raw["steps"])
        for i, step in enumerate(steps):
            if any(step.path == other.path for other in steps[:i]):
                raise ValueError(f"chemin {step.path!r} inscrit deux fois")
            if step.source is not None and step.source not in {o.path for o in steps[:i]}:
                raise ValueError(
                    f"source {step.source!r} : une étape antérieure inscrite est attendue"
                )
    except (ValueError, TypeError) as exc:
        raise MissionError(f"{path} : {exc}") from exc
    return Mission(root, raw["name"], steps)


def _step(root: Path, item: Any) -> Step:
    if not isinstance(item, dict) or set(item) != {"path", "role", "source"}:
        raise ValueError("étape : clés attendues path, role, source")
    path, role, source = item["path"], item["role"], item["source"]
    if role not in _KINDS:
        raise ValueError(f"rôle {role!r} inconnu — attendu : {', '.join(_KINDS)}")
    _safe(root, path)
    if source is not None:
        _safe(root, source)
    return Step(path, role, source)


def _safe(root: Path, rel: object) -> None:
    """Relatif, contenu, sans `..` ni lien qui sorte de la mission ; `.` désigne la racine."""
    if not isinstance(rel, str) or not rel:
        raise ValueError(f"chemin {rel!r} : texte non vide attendu")
    parts = rel.split("/")
    if rel != "." and (rel.startswith("/") or ":" in rel or "\\" in rel or
                       any(p in ("", ".", "..") for p in parts)):
        raise ValueError(f"chemin {rel!r} : relatif, sans remontée, avec des « / » attendu")
    if not (root / rel).resolve().is_relative_to(root.resolve()):
        raise ValueError(f"chemin {rel!r} : redirigé hors de la mission")


def _save(mission: Mission) -> None:
    payload = {
        "schema_version": 1, "name": mission.name,
        "steps": [{"path": s.path, "role": s.role, "source": s.source} for s in mission.steps],
    }
    storage.write_atomic_text(
        mission.root / REGISTRY, json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )


@contextmanager
def _locked(root: Path, *, make: bool = False) -> Iterator[None]:
    if make:
        root.mkdir(parents=True, exist_ok=True)
    try:
        with lock.acquire(root / LOCK, "mission"):
            yield
    except lock.LockError as exc:
        raise MissionError(f"{root} : {exc}") from exc


def _open(root: Path, *, explicit: bool = False) -> Mission:
    """Le registre existant, ou celui d'une mission neuve. Une création n'en fabrique jamais un
    sur une collaboration historique laissée à la racine : son rattachement (`explicit`) est une
    opération à part."""
    if (root / REGISTRY).is_file():
        return load(root)
    if (root / "etat.json").is_file() and not explicit:
        raise MissionError(
            f"{root} contient une collaboration historique : la rattacher d'abord,"
            f" `{_ATTACH} {root} . --role recherche`"
        )
    parent = locate(root.parent) if root.parent != root else None
    if parent is not None:
        raise MissionError(f"{root} est déjà dans la mission {parent.mission.name}")
    return Mission(root, root.name, ())


# -- Navigation --


def locate(path: Path) -> Located | None:
    """La mission d'un dossier, retrouvée par ses ancêtres — sans exploration du disque."""
    here = path.resolve()
    for folder in (here, *here.parents):
        if (folder / REGISTRY).is_file():
            mission = load(folder)
            rel = "." if folder == here else here.relative_to(folder).as_posix()
            return Located(mission, rel, next((s for s in mission.steps if s.path == rel), None))
    return None


def root_of(path: Path) -> Path | None:
    """La racine de la mission dont `path` est une étape inscrite, sinon `None`."""
    found = locate(path)
    return found.mission.root if found is not None and found.step is not None else None


def resolve(path: Path, preferred: str | None = None) -> Target:
    """L'ouverture d'un dossier. Une racine de mission ouvre l'étape préférée (préférence
    d'affichage seulement), à défaut la dernière inscrite ; une collaboration indépendante, ou
    non rattachée, s'ouvre telle quelle."""
    found = locate(path)
    if found is None or (found.rel != "." and found.step is None):
        return Target(None, None, path)
    if found.rel != ".":
        return Target(found.mission.root, found.rel, path)
    paths = [s.path for s in found.mission.steps]
    if not paths:
        raise MissionError(f"{path} : mission sans étape rattachée")
    step = preferred if preferred in paths else paths[-1]
    return Target(found.mission.root, step, found.mission.root / step)


def fold(paths: Iterable[Path]) -> list[Path]:
    """Une entrée par mission : une étape rattachée est remplacée par sa racine, sans doublon."""
    folded: list[Path] = []
    for path in paths:
        try:
            root = root_of(path)
        except MissionError:
            root = None
        if (root or path) not in folded:
            folded.append(root or path)
    return folded


def _name(mission: Mission, step: Step) -> str:
    twins = [s for s in mission.steps if s.role == step.role]
    return step.role if len(twins) == 1 else f"{step.role} ({step.path})"


def summarize(root: Path) -> Summary:
    from . import facade  # tardif : la façade importe ce module pour créer

    mission = load(root)
    views = []
    for step in mission.steps:
        folder = root / step.path
        updated = None
        try:
            snapshot = facade.inspect_collaboration(folder)
            label, updated = snapshot.presentation.status_label, snapshot.state.updated_at
        except facade.InspectionError as exc:
            label = f"illisible : {exc}" if folder.is_dir() else "dossier introuvable"
        views.append(StepView(step, folder, label, updated))
    registered = {s.path for s in mission.steps}
    to_attach, partial = [], []
    for child in [root, *sorted(p for p in root.iterdir() if p.is_dir())]:
        rel = "." if child == root else child.name
        if rel in registered or not (
            rel == "." or re.fullmatch(r"(recherche|conception)(-\d{3})?", rel)
            or child.name.startswith(".new-")
        ):
            continue
        done = (child / "configuration.json").is_file() and (child / "etat.json").is_file()
        if done and not child.name.startswith(".new-"):
            to_attach.append(rel)
        elif rel != ".":
            partial.append(rel)
    return Summary(mission, tuple(views), tuple(to_attach), tuple(partial))


def overview(path: Path) -> Summary | None:
    """Le résumé de la mission d'une étape inscrite, pour l'en-tête d'un écran."""
    root = root_of(path)
    return None if root is None else summarize(root)


def step_path(root: Path, rel: str) -> Path:
    """Le dossier d'une étape inscrite — `show --etape` ne devine rien."""
    if not any(s.path == rel for s in load(root).steps):
        raise MissionError(f"{rel!r} n'est pas une étape de la mission {root}")
    return root / rel


def next_path(mission: Mission, role: str) -> str:
    count = sum(s.role == role for s in mission.steps) + 1
    return role if count == 1 else f"{role}-{count:03d}"


def default_dest(research: Path, new_version: bool = False) -> tuple[Path | None, Path]:
    """Où va la conception qui poursuit `research` : dans sa mission si elle y est inscrite
    (`conception`, ou la version suivante sur demande explicite), sinon à côté d'elle."""
    root = root_of(research)
    if root is None:
        return None, research.parent / f"{research.name}-conception"
    return root, root / (next_path(load(root), "conception") if new_version else "conception")


def continuations(research: Path) -> tuple[Path, ...]:
    """Les conceptions déjà créées à partir de `research` : à rouvrir, jamais à doubler."""
    found = locate(research)
    if found is not None and found.step is not None:
        return tuple(found.mission.root / s.path for s in found.mission.steps
                     if s.role == "conception" and s.source == found.rel)
    sibling = default_dest(research)[1]
    return (sibling,) if (sibling / "etat.json").is_file() else ()


# -- Création et rattachement --


def _role(kind: MissionKind) -> str:
    return "recherche" if kind is MissionKind.RECHERCHE else "conception"


def _rel(root: Path, folder: Path) -> str:
    try:
        return folder.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        raise MissionError(f"{folder} n'est pas contenu dans la mission {root}") from None


def _plan(request: CreationRequest, mission: Mission) -> Step:
    """Les règles de la création dans une mission, sans rien écrire : rend l'étape à inscrire."""
    role, root = _role(request.kind), mission.root
    rel = _rel(root, request.collab)
    if rel == ".":
        raise MissionError("une nouvelle étape ne peut pas être la racine de la mission")
    same = [s for s in mission.steps if s.role == role]
    if request.new_version and not same:
        raise MissionError(f"aucune étape {role} à versionner : créer la première normalement")
    if request.new_version and rel != next_path(mission, role):
        raise MissionError(
            f"nouvelle version : le dossier attendu est {next_path(mission, role)!r}"
        )
    if same and not request.new_version:
        raise MissionError(
            f"la mission {mission.name} a déjà une étape {role} ({same[-1].path}) : la rouvrir,"
            " ou demander explicitement une nouvelle version"
        )
    source = None
    if request.follow_up is not None:
        source = _rel(root, request.follow_up.research)
        if not any(s.path == source and s.role == "recherche" for s in mission.steps):
            raise MissionError(f"la recherche {source!r} n'est pas rattachée à la mission")
    if request.collab.exists():
        done = (request.collab / "configuration.json").is_file()
        raise MissionError(
            f"{request.collab} existe déjà"
            + (f" et n'est pas rattaché : `{_ATTACH} {root} {rel} --role {role}`" if done
               else " mais semble partiel : l'inspecter, rien n'est écrasé")
        )
    return Step(rel, role, source)


def check_step(request: CreationRequest) -> None:
    root = request.mission
    assert root is not None
    _plan(request, _open(root))


def create_step(request: CreationRequest, create: Callable[[], CreationResult]) -> CreationResult:
    """Prépare, crée (par `create`, l'écriture partagée), puis inscrit au registre, sous le
    verrou de mission. Si l'inscription échoue, la collaboration valide est conservée : le message
    dit comment la rattacher, sans rien recréer ni repayer."""
    root = request.mission
    assert root is not None
    with _locked(root, make=True):
        mission = _open(root)
        step = _plan(request, mission)
        result = create()
        try:
            _save(replace(mission, steps=(*mission.steps, step)))
        except OSError as exc:
            raise MissionError(
                f"{result.path} est créée mais n'est pas inscrite au registre ({exc}) :"
                f" `{_ATTACH} {root} {step.path} --role {step.role}`"
            ) from exc
    return result


def attach(root: Path, collab: Path, role: str, source: str | None = None) -> Step:
    """Rattache une collaboration valide déjà située dans la mission. Refus si elle n'est pas
    lisible, si son type ne va pas avec le rôle, ou si le rôle exige une version explicite."""
    if role not in _KINDS:
        raise MissionError(f"rôle {role!r} inconnu — attendu : {', '.join(_KINDS)}")
    if not root.is_dir():
        raise MissionError(f"{root} n'est pas un dossier")
    config, _ = _read_collaboration(collab)
    if config.mission_kind is not _KINDS[role]:
        raise MissionError(f"{collab} : un rôle {role} attend une collaboration de type "
                           f"{_KINDS[role].value}, pas {config.mission_kind.value}")
    rel = _rel(root, collab)
    with _locked(root):
        mission = _open(root, explicit=True)
        existing = next((s for s in mission.steps if s.path == rel), None)
        if existing == Step(rel, role, source):
            return existing
        step = _admit(mission, rel, role, source)
        _save(replace(mission, steps=(*mission.steps, step)))
    return step


def _admit(mission: Mission, rel: str, role: str, source: str | None) -> Step:
    """Les refus **prévisibles** d'un rattachement, sans rien écrire : `adopt` les passe avant
    de copier, pour ne jamais publier un dossier qu'il ne pourrait pas inscrire."""
    if role not in _KINDS:
        raise MissionError(f"rôle {role!r} inconnu — attendu : {', '.join(_KINDS)}")
    existing = next((s for s in mission.steps if s.path == rel), None)
    if existing is not None:
        raise MissionError(f"{rel!r} est déjà inscrite ({existing.role}, source {existing.source})")
    if source is not None and not any(s.path == source for s in mission.steps):
        raise MissionError(f"la source {source!r} n'est pas une étape de la mission")
    if role != "revue" and any(s.role == role for s in mission.steps) and (
        rel != next_path(mission, role)
    ):
        raise MissionError(
            f"la mission a déjà une étape {role} : une autre version se range sous"
            f" {next_path(mission, role)!r}"
        )
    try:
        return _step(mission.root, {"path": rel, "role": role, "source": source})
    except ValueError as exc:
        raise MissionError(str(exc)) from exc


def _read_collaboration(folder: Path) -> tuple[Configuration, State]:
    try:
        config = Configuration.from_dict(
            json.loads(storage.read_text(folder / "configuration.json")[0])
        )
        return config, State.from_dict(json.loads(storage.read_text(folder / "etat.json")[0]))
    except (OSError, ValueError, SchemaError) as exc:
        raise MissionError(f"{folder} : collaboration illisible ({exc})") from exc


# -- Reprise d'une collaboration extérieure (Mastermind) --


@dataclass(frozen=True)
class Adoption:
    dest: Path
    files: int
    rewritten: tuple[str, ...]
    absolute_paths: dict[str, int]  # fichiers de reprise portant un chemin absolu (à lire)
    history_paths: int  # dans les traces et le corpus haché (de la prose) : jamais modifiés


def _fingerprint(folder: Path) -> dict[str, str]:
    seen: dict[str, str] = {}
    for current, dirs, files in os.walk(folder):
        for name in (*dirs, *files):
            item = Path(current, name)
            if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
                raise MissionError(f"{item} : lien, copie refusée")
            rel = item.relative_to(folder).as_posix()
            seen[rel] = (
                "dossier" if item.is_dir() else hashlib.sha256(item.read_bytes()).hexdigest()
            )
    return seen


def adopt(root: Path, source: Path, role: str, rel: str | None = None,
          source_step: str | None = None) -> Adoption:
    """**Copie** une collaboration extérieure sous la mission, vérifiée octet par octet, puis la
    rattache. L'original n'est ni déplacé ni modifié : il reste la sauvegarde. Rien n'est écrasé ;
    tout est contrôlé avant la première écriture. Seul `source_path` de la provenance de transition,
    relatif à son dossier d'origine, est recalculé — et l'ancienne valeur est gardée."""
    rel = rel or role
    dest = root / rel
    if role not in _KINDS:
        raise MissionError(f"rôle {role!r} inconnu — attendu : {', '.join(_KINDS)}")
    if not root.is_dir():
        raise MissionError(f"{root} n'est pas un dossier")
    if (source / "verrou.json").exists():
        raise MissionError(f"{source} : verrou présent, une exécution est peut-être active")
    config, state = _read_collaboration(source)
    if state.status is Status.RUNNING:
        raise MissionError(f"{source} : exécution déclarée en cours")
    if config.mission_kind is not _KINDS[role]:
        raise MissionError(f"{source} : un rôle {role} attend une collaboration de type "
                           f"{_KINDS[role].value}, pas {config.mission_kind.value}")
    try:
        _safe(root, rel)
    except ValueError as exc:
        raise MissionError(str(exc)) from exc
    _admit(_open(root, explicit=True), rel, role, source_step)  # le rattachement sera possible
    if dest.exists():
        raise MissionError(f"{dest} existe déjà : rien n'est écrasé")
    if source.resolve().is_relative_to(root.resolve()) or dest.resolve().is_relative_to(
        source.resolve()
    ):
        raise MissionError(f"{source} est déjà dans la mission (rattacher) ou la contient")
    before = _fingerprint(source)
    tmp = root / f".adopt-{source.name}-{uuid.uuid4().hex}"
    try:
        shutil.copytree(source, tmp, symlinks=True)
        if _fingerprint(tmp) != before or _fingerprint(source) != before:
            raise MissionError("la copie diffère de l'original : abandon, rien n'est publié")
        rewritten = _rewrite_transition(tmp, root, dest, source_step)
        os.rename(tmp, dest)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    try:
        attach(root, dest, role, source_step)
    except (MissionError, OSError) as exc:
        raise MissionError(f"{dest} est copiée mais non inscrite ({exc}) : `{_ATTACH}`") from exc
    after = _fingerprint(dest)
    changed = {k for k in before.keys() | after.keys() if before.get(k) != after.get(k)}
    if changed - set(rewritten):
        raise MissionError(f"{dest} : écarts inattendus avec l'original : {sorted(changed)}")
    critical: dict[str, int] = {}
    history = 0
    for name in after:
        file = dest / name
        if file.suffix not in (".json", ".md", ".txt", ".toml") or not file.is_file():
            continue
        hits = len(_ABSOLUTE.findall(file.read_text(encoding="utf-8", errors="replace")))
        if name.split("/")[0] in _HISTORY or name.startswith("corpus/fichiers/"):
            history += hits
        elif hits:
            critical[name] = hits
    return Adoption(dest, sum(v != "dossier" for v in after.values()), tuple(rewritten),
                    critical, history)


def _rewrite_transition(tmp: Path, root: Path, dest: Path, source_step: str | None) -> list[str]:
    file = tmp / TRANSITION
    if not file.is_file():
        return []  # conception créée avant le lot 1 : aucun chemin de reprise à recalculer
    data = json.loads(storage.read_text(file)[0])
    if source_step is None:
        raise MissionError(f"{TRANSITION} présent : indiquer l'étape de recherche (--source)")
    new = os.path.relpath((root / source_step).resolve(), dest.parent.resolve())
    new = Path(new).as_posix()
    if data.get("source_path") != new:
        data["previous_source_path"] = data.get("source_path")
        data["source_path"] = new
        storage.write_atomic_text(file, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    return [TRANSITION]

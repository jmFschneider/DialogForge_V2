"""Référence des exécutions du Runner (`conception/PARCOURS_MISSION_CONCEPTION.md` §7.3).

`developpement/executions/NNN.json` garde ce qu'il faut pour **reprendre** : paramètres non secrets,
export de la version acceptée, dépôt et base, et référence du dossier Linux. Le statut n'y est pas
copié : il se lit sur le dossier Runner (`inspect`). Aucun jeton n'y entre — la référence ne reçoit
que des champs nommés ci-dessous. Aucune écriture Git ici : le dépôt est l'affaire du Runner.
"""

from __future__ import annotations

import json
import shlex
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import development, mission, storage

SCHEMA_VERSION = 1
MODES = ("nouveau", "existant")
_KEYS = {
    "schema_version", "conception", "export", "projet", "profil", "wsl", "run", "validations",
    "delais", "paquets",
}
_PROJECT_KEYS = {"mode", "depot", "base_demandee", "base_oid", "identite"}  # + "branche" cible,
# notée à la première remise (`delivery.deliver`)
_ACTIONS = {
    "absent": ("start",), "prepare": ("launch", "collect"), "appel": ("continue", "collect"),
    "validations": ("continue", "collect"), "paquet": ("correct",), "invalide": (),
}


def dev_dir(collab: Path) -> Path:
    """`developpement/` de la mission, ou à défaut un dossier voisin de la conception."""
    root = mission.root_of(collab)
    return root / "developpement" if root else collab.parent / f"{collab.name}-developpement"


def default_code(collab: Path) -> Path:
    root = mission.root_of(collab)
    return root / "code" if root else collab.parent / f"{collab.name}-code"


def project_name(collab: Path) -> str:
    return (mission.root_of(collab) or collab).name


@dataclass(frozen=True)
class Found:
    dev: Path
    conception: str            # chemin de la conception, relatif au parent de `dev`
    export: Path | None        # export déjà publié, identique à la version acceptée actuelle
    reference: Path | None     # sa référence d'exécution la plus récente
    data: dict[str, Any] | None
    number: int                # numéro de la référence reprise, ou de la prochaine


@dataclass(frozen=True)
class Parameters:
    """Ce que l'écran du Runner montre : la référence reprise, sinon les propositions."""

    mode: str
    repo: str
    base: str
    run: str
    validations: list[list[str]]
    agent_timeout: float
    validation_timeout: float
    distro: str | None


def parameters(collab: Path, found: Found | None) -> Parameters:
    data = found.data if found else None
    if data is None:
        number = found.number if found else 1
        run = f"~/dialogforge-runs/{project_name(collab)}-{number:03d}"
        code = str(default_code(collab))
        return Parameters("nouveau", code, "HEAD", run, [], 3600.0, 300.0, None)
    project = data["projet"]
    return Parameters(
        project["mode"], project["depot"], project["base_demandee"], data["run"],
        data["validations"], data["delais"]["agent"], data["delais"]["validation"],
        data["wsl"]["distribution"],
    )


def _numbered(folder: Path, pattern: str) -> list[Path]:
    return sorted(folder.glob(pattern)) if folder.is_dir() else []


def load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"{path.name} illisible : {exc}") from exc
    if (
        not isinstance(data, dict) or set(data) != _KEYS or data["schema_version"] != 1
        or not isinstance(data["projet"], dict)
        or set(data["projet"]) - {"branche"} != _PROJECT_KEYS
        or data["projet"]["mode"] not in MODES
    ):
        raise ValueError(f"{path.name} : référence d'exécution invalide")
    return data


def _write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    storage.write_atomic_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def _same_export(folder: Path, files: dict[str, bytes]) -> bool:
    try:
        development.validate_export(folder)
        return all((folder / name).read_bytes() == data for name, data in files.items())
    except (OSError, ValueError):
        return False


def find(collab: Path) -> Found:
    """Retrouve l'export et la référence de la version acceptée actuelle, sans rien écrire.
    Un export au contenu différent (nouvelle acceptation, fichier modifié) n'est jamais repris."""
    dev = dev_dir(collab)
    anchor = dev.parent.resolve()
    conception = collab.resolve().relative_to(anchor).as_posix()
    files = development.export_files(collab)
    export = next(
        (d for d in reversed(_numbered(dev, "export-[0-9][0-9][0-9]")) if _same_export(d, files)),
        None,
    )
    references = _numbered(dev / "executions", "[0-9][0-9][0-9].json")
    if export is not None:
        wanted = export.resolve().relative_to(anchor).as_posix()
        for path in reversed(references):
            data = load(path)
            if data["export"]["path"] == wanted and data["conception"] == conception:
                return Found(dev, conception, export, path, data, int(path.stem))
    last = int(references[-1].stem) if references else 0
    return Found(dev, conception, export, None, None, last + 1)


def check_current(collab: Path, reference: Path) -> None:
    """Avant un appel agent : la conception actuelle doit encore être celle de l'export enregistré.
    Sinon rien ne part ; le clone reste pour diagnostic, la version modifiée veut un nouvel export.
    """
    data = load(reference)
    export = dev_dir(collab).parent / data["export"]["path"]
    try:
        files = development.export_files(collab)
    except (ValueError, OSError, RuntimeError) as exc:
        raise ValueError(
            f"la conception a changé depuis l'export de cette exécution ({exc}) ; "
            "le clone est conservé pour diagnostic, aucun agent n'est appelé"
        ) from exc
    if not _same_export(export, files):
        raise ValueError(
            "la conception acceptée n'est plus celle de l'export de cette exécution ; "
            "le clone est conservé pour diagnostic, aucun agent n'est appelé : la version "
            "modifiée demande un nouvel export et une nouvelle exécution"
        )


def ensure_export(collab: Path, found: Found) -> Path:
    """Reprend l'export identique, sinon en publie un nouveau ; jamais d'écrasement."""
    if found.export is not None:
        return found.export
    count = len(_numbered(found.dev, "export-[0-9][0-9][0-9]"))
    output = found.dev / f"export-{count + 1:03d}"
    development.export_conception(collab, output)
    return output


def save(
    found: Found, export: Path, *, mode: str, repo: Path, base: str,
    validations: Sequence[Sequence[str]], run: str, agent_timeout: float,
    validation_timeout: float,
) -> Path:
    """Publie la référence (avant tout appel fournisseur), ou met à jour celle qu'on reprend."""
    previous = found.data
    same = previous and previous["projet"]["mode"] == mode and (
        previous["projet"]["depot"] == str(repo)
    )
    keep = previous["projet"] if previous and same else {}
    data = {
        "schema_version": SCHEMA_VERSION, "conception": found.conception,
        "export": {
            "path": export.resolve().relative_to(found.dev.parent.resolve()).as_posix(),
            "md_sha256": _export_sha(export),
        },
        "projet": {
            "mode": mode, "depot": str(repo), "base_demandee": base,
            "base_oid": keep.get("base_oid"), "identite": keep.get("identite"),
            **({"branche": keep["branche"]} if keep.get("branche") else {}),
        },
        "profil": "claude-wsl", "wsl": previous["wsl"] if previous else {"distribution": None},
        "run": run, "validations": [list(command) for command in validations],
        "delais": {"agent": agent_timeout, "validation": validation_timeout},
        "paquets": previous["paquets"] if previous else [],
    }
    path = found.reference or found.dev / "executions" / f"{found.number:03d}.json"
    _write(path, data)
    return path


def _export_sha(export: Path) -> str:
    return str(json.loads((export / "export.json").read_text("utf-8"))["export_md_sha256"])


def update(path: Path, **changes: Any) -> dict[str, Any]:
    """Complète la référence : `run`, `wsl`, `projet` (un niveau fusionné) ou `paquets` (ajout)."""
    data = load(path)
    for key, value in changes.items():
        if key == "paquets":
            data[key] = [*data[key], *(p for p in value if p not in data[key])]
        elif key in ("wsl", "projet"):
            data[key] = {**data[key], **value}
        elif key == "run":
            data[key] = value
        else:
            raise ValueError(f"champ de référence non modifiable : {key}")
    _write(path, data)
    return load(path)


def argv(executable: str, arguments: str) -> list[str]:
    """Une ligne du formulaire : exécutable et arguments (guillemets permis), jamais un shell."""
    name = executable.strip()
    if not name:
        raise ValueError("indiquer l'exécutable de chaque validation")
    try:
        return [name, *shlex.split(arguments)]
    except ValueError as exc:
        raise ValueError(f"arguments de « {name} » : {exc}") from exc


def validations_from_rows(rows: Sequence[tuple[str, str]]) -> list[list[str]]:
    used = [(name, args) for name, args in rows if name.strip() or args.strip()]
    if not used:
        raise ValueError("indiquer au moins une validation")
    return [argv(name, args) for name, args in used]


def rows_from_validations(validations: Sequence[Sequence[str]]) -> list[tuple[str, str]]:
    return [(command[0], shlex.join(command[1:])) for command in validations]


def actions(state: dict[str, Any] | None) -> tuple[str, ...]:
    """Les départs permis pour l'état d'un dossier Runner ; un état inconnu n'en permet aucun
    sauf `start` pour un dossier absent."""
    if state and state.get("lot"):
        return ("collect",) if state["stage"] in {"appel", "validations"} else ()
    if state and state.get("package") and state["stage"] in {"appel", "validations"}:
        return ("correct", "collect")
    return _ACTIONS.get(state["stage"] if state else "absent", ())


def describe(state: dict[str, Any] | None) -> str:
    stage = state["stage"] if state else "absent"
    if state is None or stage == "absent":
        return "Aucun dossier Runner : la préparation peut commencer."
    if stage == "invalide":
        return str(state.get("detail", "Dossier Runner invalide")) + " — inspecter le dossier."
    lock = " Un verrou est présent : il n'est jamais supprimé automatiquement." if (
        state.get("locked")
    ) else ""
    if stage == "prepare":
        return "Clone préparé, agent non lancé : lancer l'agent sur cette préparation." + lock
    if state.get("lot"):
        lock = (" Exécution limitée à un lot : consultable seulement, aucun nouvel appel ; "
                "préparer une nouvelle exécution sur toute la conception.") + lock
    if stage == "appel":
        done = "terminé" if state.get("last_call_complete") else "interrompu ou sans résultat"
        if state.get("package"):
            return (f"{state['calls']} appel(s) de A ; le dernier est {done}. "
                    "Un paquet antérieur reste disponible ; la nouvelle correction exige un "
                    "objectif précis, sinon « Refaire les validations ».") + lock
        hint = {
            "INTERVENTION": "A attend une intervention : lire son bilan, écrire la réponse dans "
                            "le message pour A, puis « Continuer avec A ».",
            "RESTE": "A avait encore du travail : « Continuer avec A ».",
            "CANDIDAT": "A a déclaré son candidat avant la fin des validations : « Refaire les "
                        "validations ».",
        }.get(str(state.get("verdict")), "Examiner les traces et le clone, puis « Continuer "
                                         "avec A » ou « Refaire les validations ».")
        return f"{state['calls']} appel(s) de A ; le dernier est {done}. {hint}" + lock
    if stage == "validations":
        earlier = (f" Le dernier paquet valide ({state['package']}) est antérieur : il ne valide "
                   "pas le code actuel.") if state.get("package") else ""
        next_step = ("demander une correction précise." if state.get("package") else
                     "continuer explicitement pour corriger.")
        return ("Dernière collecte échouée (validations non réussies ou interrompues) : voir les "
                "traces ; " + next_step + earlier) + lock
    return (f"Validations réussies — paquet : {state['package']}. Son commit est remis dans "
            "code/ pour l'essayer (« Remettre dans code/ » termine ou refait la remise, sans "
            "agent). Une correction n'est utile que si un défaut précis est constaté.") + lock

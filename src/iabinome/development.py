"""Passage de relais et paquets immuables ; le cycle documentaire reste inchangé.

Les validations sont des déclarations extérieures. Une empreinte rattache leur
contenu, elle ne prouve ni leur exécution ni leur fidélité au commit nommé.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from . import contracts, corpus, decisions, lock, objections, storage
from .models import Configuration, Phase, ReviewerAccess, State, Status

_EXPORT_KEYS = {
    "schema_version", "source_collaboration", "request_sha256", "document_sha256",
    "review_sha256", "decision_sha256", "export_md_sha256",
}
_VALIDATION_KEYS = {
    "schema_version", "validation_id", "head_oid", "command", "started_at", "completed_at",
    "exit_code", "outcome", "environment", "summary", "artifacts",
}
_LIMITATIONS = (
    "Objets de deux commits seulement : aucun index, worktree, fichier ignoré ou non suivi. "
    "Fichiers inchangés absents ; sous-modules limités au gitlink ; LFS limité au pointeur. "
    "Liens symboliques copiés comme texte, jamais suivis. Binaires pas nécessairement lisibles "
    "par les agents. Aucun filtre clean/smudge, textconv ou diff externe. "
    "Les validations sont déclarées, leur exécution n'est pas certifiée par DialogForge."
)
_VALIDATION_EXAMPLE = {
    "schema_version": 1, "validation_id": "tests", "head_oid": "OID_COMPLET",
    "command": ["python", "-m", "pytest", "tests"], "started_at": "date UTC",
    "completed_at": "date UTC", "exit_code": 0, "outcome": "PASSED",
    "environment": "environnement réel", "summary": "résultat observé", "artifacts": [],
}


def _json(data: bytes) -> dict[str, Any]:
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError("objet JSON attendu")
    return value


def _dump(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode()


def _display(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _schema(value: dict[str, Any], keys: set[str]) -> None:
    if set(value) != keys or type(value.get("schema_version")) is not int or (
        value["schema_version"] != 1
    ):
        raise ValueError("schéma inattendu")


def _path(name: str) -> str:
    parts = PurePosixPath(name).parts
    if not name or name.strip() != name or name.splitlines() != [name] or (
        "\\" in name or ":" in name or any(ord(c) < 32 for c in name)
    ) or (
        PurePosixPath(name).is_absolute() or PureWindowsPath(name).drive
        or any(p in ("", ".", "..") for p in name.split("/"))
        or any(PureWindowsPath(p).is_reserved() or p.endswith((".", " ")) for p in parts)
    ):
        raise ValueError(f"chemin non portable ou dangereux : {name!r}")
    return name


def _tree(root: Path) -> dict[str, bytes]:
    if not root.is_dir():
        raise ValueError(f"dossier absent : {root}")
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise ValueError(f"lien refusé : {path}")
        if path.is_file():
            result[_path(path.relative_to(root).as_posix())] = path.read_bytes()
        elif not path.is_dir():
            raise ValueError(f"fichier non régulier : {path}")
    return result


def _manifest(files: dict[str, bytes]) -> dict[str, Any]:
    return {name: {"size": len(data), "sha256": _sha(data)}
            for name, data in sorted(files.items())}


def _publish(output: Path, files: dict[str, bytes]) -> None:
    if output.exists():
        raise ValueError(f"{output} existe déjà")
    names = [_path(name) for name in files]
    if len({n.casefold() for n in names}) != len(names):
        raise ValueError("collision de chemins sans distinction de casse")
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".new-{output.name}-", dir=output.parent))
    try:
        for name, data in files.items():
            target = tmp / name
            target.parent.mkdir(parents=True, exist_ok=True)
            storage.write_atomic_bytes(target, data)
        if _tree(tmp) != files:
            raise ValueError("contenu modifié pendant la publication")
        _rename_without_replace(tmp, output)
    except BaseException:
        shutil.rmtree(tmp)
        raise


def _rename_without_replace(src: Path, dst: Path) -> None:
    if os.name == "nt":
        src.rename(dst)  # Windows refuse une destination déjà présente.
        return
    if os.name != "posix":
        raise ValueError("publication atomique sans remplacement non supportée")
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise ValueError("publication atomique sans remplacement non supportée")
    renameat2.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                          ctypes.c_char_p, ctypes.c_uint)
    renameat2.restype = ctypes.c_int
    if renameat2(-100, os.fsencode(src), -100, os.fsencode(dst), 1):
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number), str(dst))


def _outside(output: Path, *sources: Path) -> None:
    target = output.resolve()
    if any(target == source.resolve() or target.is_relative_to(source.resolve())
           for source in sources):
        raise ValueError("la sortie doit être hors des dossiers sources et du dépôt cible")


def export_conception(collab: Path, output: Path) -> None:
    _outside(output, collab)
    with lock.acquire(collab / "verrou.json", "dev-export"):
        state = State.from_dict(_json((collab / "etat.json").read_bytes()))
        decision = decisions.latest(collab)
        if state.status is not Status.AWAITING_APPROVAL or not decisions.is_acceptance(decision):
            raise ValueError("conception non acceptée")
        assert decision is not None
        gaps = decisions.discrepancies(collab, decision, state)
        if gaps:
            raise ValueError("acceptation périmée : " + "; ".join(gaps))
        request = storage.read_text(collab / "demande.md")[0]
        document = storage.read_text(collab / decisions.DELIVERED)[0]
        opened = [e for e in objections.ledger(collab) if e["disposition"] == "OPEN"]
        text = (
            f"# Mandat de développement — {collab.name}\n\n## Demande\n\n{request}\n"
            f"## Conception acceptée\n\n{document}\n## Décision et réserves\n\n"
            f"```json\n{_display(decision)}```\n\n## Constats ouverts\n\n"
            f"```json\n{_display(opened)}```\n\n## Passage de relais\n\n"
            "L'agent extérieur développe avec PWF, Git et les validations du projet. "
            "DialogForge ne développe, ne teste, ne commit et ne déploie rien. "
            "Fournir une base et une tête committées ; tester cette tête exacte. "
            "Toute correction de code exige un nouveau commit ; tout changement de code "
            "ou de validation exige un nouveau paquet et une nouvelle collaboration.\n\n"
            f"{_LIMITATIONS}\n\n## Résultat de validation (schéma fermé)\n\n"
            f"```json\n{_display(_VALIDATION_EXAMPLE)}```\n"
            "outcome : PASSED, FAILED, NOT_RUN ou UNKNOWN ; exit_code : entier ou null.\n"
        ).encode()
        version = decision["version"]
        metadata = {
            "schema_version": 1, "source_collaboration": collab.name,
            "request_sha256": version["demande_sha256"],
            "document_sha256": version["livrable_sha256"],
            "review_sha256": version["revue_sha256"], "decision_sha256": _sha(_dump(decision)),
            "export_md_sha256": _sha(text),
        }
        _publish(output, {"export.md": text, "export.json": _dump(metadata)})


def _export(files: dict[str, bytes]) -> None:
    if set(files) != {"export.md", "export.json"}:
        raise ValueError("export incomplet ou fichiers surnuméraires")
    metadata = _json(files["export.json"])
    _schema(metadata, _EXPORT_KEYS)
    if metadata["export_md_sha256"] != _sha(files["export.md"]):
        raise ValueError("export.md modifié")


def _git(repo: Path, *args: str, optional: bool = False) -> bytes:
    # Ne pas hériter d'un GIT_DIR, GIT_WORK_TREE ou d'options injectées par l'hôte.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_PAGER="cat", GIT_EXTERNAL_DIFF="",
               GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0")
    try:
        done = subprocess.run(
            ["git", "--no-pager", "-c", "core.fsmonitor=false", "-c", "diff.noprefix=false",
             "-c", "diff.srcPrefix=a/", "-c", "diff.dstPrefix=b/",
             "-c", "diff.mnemonicPrefix=false", "-C", str(repo), *args],
            capture_output=True, env=env, timeout=60, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("lecture Git : délai dépassé") from exc
    if done.returncode and not (optional and done.returncode == 1):
        raise ValueError("lecture Git refusée : " + done.stderr.decode("utf-8", "replace"))
    return done.stdout


def _capture(repo: Path, base: str, head: str) -> tuple[dict[str, bytes], str, str]:
    # Les anciens Git ignorent GIT_NO_LAZY_FETCH : refuser les dépôts partiels aussi.
    if _git(repo, "config", "--get-regexp", r"^(extensions\.partialclone|remote\..*\.promisor)$",
            optional=True):
        raise ValueError("dépôt partiel refusé : aucune récupération réseau autorisée")
    base, head = (_git(repo, "rev-parse", "--verify", "--end-of-options", f"{rev}^{{commit}}")
                  .decode("ascii").strip() for rev in (base, head))
    options = ("--no-ext-diff", "--no-textconv", "--no-renames", "--no-relative",
               "--ignore-submodules=none")
    diff = _git(repo, "diff", "--binary", "--full-index", "--no-color", "--unified=3",
                "--diff-algorithm=myers", "--no-indent-heuristic", *options,
                base, head, "--")
    raw = _git(repo, "diff", "--raw", "-z", "--no-abbrev", *options, base, head, "--")
    chunks = raw.split(b"\x00")
    files = {"revision/diff.patch": diff}
    entries = []
    for index in range(0, len(chunks) - 1, 2):
        oldmode, mode, oldoid, oid, status = chunks[index].decode("ascii").split()
        name = _path(chunks[index + 1].decode("utf-8"))
        entry: dict[str, Any] = {
            "path": name, "status": status, "old_mode": oldmode.lstrip(":"),
            "mode": mode, "old_oid": oldoid, "oid": oid,
            "object_type": "commit" if mode == "160000" else "blob",
        }
        if status != "D" and mode != "160000":
            blob = _git(repo, "cat-file", "blob", oid)
            files[f"revision/files/{name}"] = blob
            entry["sha256"] = _sha(blob)
        entries.append(entry)
    files["revision/files.json"] = _dump(entries)
    files["revision/revision.json"] = _dump({
        "schema_version": 1, "base_oid": base, "head_oid": head,
        "diff_sha256": _sha(diff), "code_files_manifest_sha256": _sha(_dump(_manifest(files))),
        "limitations": [_LIMITATIONS],
    })
    return files, base, head


def _validation(data: bytes, head: str) -> str:
    value = _json(data)
    _schema(value, _VALIDATION_KEYS)
    for key in ("validation_id", "head_oid", "started_at", "completed_at", "environment",
                "summary", "outcome"):
        if not isinstance(value[key], str) or not value[key]:
            raise ValueError(f"validation : {key} doit être une chaîne non vide")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", value["validation_id"]):
        raise ValueError("validation_id non portable")
    if value["head_oid"] != head:
        raise ValueError("validation d'une autre tête Git")
    if value["outcome"] not in {"PASSED", "FAILED", "NOT_RUN", "UNKNOWN"}:
        raise ValueError("outcome inconnu")
    if value["exit_code"] is not None and type(value["exit_code"]) is not int:
        raise ValueError("exit_code doit être un entier ou null")
    for key in ("command", "artifacts"):
        if not isinstance(value[key], list) or not all(isinstance(s, str) for s in value[key]):
            raise ValueError(f"{key} doit être une liste de chaînes")
    if not value["command"]:
        raise ValueError("commande de validation absente")
    return str(value["validation_id"])


def _antecedent(collab: Path) -> dict[str, bytes]:
    state = State.from_dict(_json((collab / "etat.json").read_bytes()))
    if state.status not in {Status.AWAITING_APPROVAL, Status.STOPPED} or (
        state.phase is not Phase.CLOSED or state.current_document != decisions.DELIVERED or
        state.latest_review is None or
        decisions.demande_sha(collab) != state.demande_sha256
    ):
        raise ValueError("antécédent sans rapport final et revue applicables")
    latest = decisions.latest(collab)
    if state.status is Status.STOPPED and (
        latest is None or latest["decision"] != decisions.STOPPED or
        decisions.discrepancies(collab, latest, state)
    ):
        raise ValueError("antécédent arrêté sans rapport final applicable")
    files = {name: (collab / source).read_bytes() for name, source in {
        "demande.md": "demande.md", "version_finale.md": decisions.DELIVERED,
        "derniere-critique-B.json": state.latest_review, "bilan.md": "livrables/bilan.md",
    }.items()}
    files["decisions.json"] = _dump({"schema_version": 1, "decisions": decisions.read(collab)})
    files["objections.json"] = _dump(objections.ledger(collab))
    files["provenance.json"] = _dump({
        "schema_version": 1, "source_collaboration": collab.name, "files": _manifest(files),
    })
    return files


def _identity(files: dict[str, bytes]) -> dict[str, Any]:
    revision = _json(files["revision/revision.json"])
    identity: dict[str, Any] = {
        "schema_version": 1, "base_oid": revision["base_oid"], "head_oid": revision["head_oid"],
    }
    for prefix in ("export/", "revision/", "validations/", "developer-notes/", "antecedents/"):
        identity[prefix[:-1] + "_sha256"] = _sha(_dump(_manifest({
            k: v for k, v in files.items() if k.startswith(prefix)
        })))
    return identity


def _request(package_id: str, identity: dict[str, Any]) -> bytes:
    return (
        "# Revue documentaire de code extérieur\n\n## Objectif\n\n"
        f"Paquet : {package_id}\nBase : {identity['base_oid']}\nTête : {identity['head_oid']}\n\n"
        "Évaluer le code capturé au regard de export/export.md. A rédige le rapport, "
        "B critique le rapport ET le code du même corpus. "
        "Le développeur extérieur écrit le code.\n\n"
        "## Livrable\n\nUn rapport autonome avec les rubriques Révision examinée, Résumé, "
        "Conformité à la conception, Vérifié, Contesté, Non couvert, Limites des validations, "
        "Constats antérieurs, Conclusion et suites humaines. Citer les preuves précises.\n\n"
        "## Sources\n\nTous les fichiers de sources.txt sont copiés dans corpus/fichiers/. "
        "package.json donne leurs empreintes ; validations/ contient les résultats déclarés. "
        "Les notes du développeur sont déclaratives. Reprendre CHAQUE constat de "
        "antecedents/*/objections.json, avec son id et sa provenance : corrigé, maintenu ou "
        "non évaluable, preuves à l'appui. B vérifie cette reprise.\n\n"
        f"## Contraintes\n\n{_LIMITATIONS}\n\n"
        "Accès consult obligatoire. Ne modifier ni exécuter aucun code. Les validations "
        "historiques des antécédents ne prouvent pas la nouvelle révision. Toute nouvelle "
        "preuve ou correction du code exige un nouveau paquet et une nouvelle collaboration.\n\n"
        "## Non-objectifs\n\nAucune implémentation, exécution de tests, écriture Git, fusion "
        "ou livraison. Aucun transfert d'échanges ou d'états entre collaborations.\n\n"
        "## Critères de fin\n\nNommer exactement paquet, base et tête ; distinguer Vérifié, "
        "Contesté et Non couvert. Une correction documentaire reste dans ce cycle. La décision "
        "accepte le rapport de cette révision, jamais un merge ni un déploiement. "
        "Exécuter dev-verify avant la décision ; les empreintes ne jugent pas la prose.\n"
    ).encode()


def build_package(
    export: Path, repo: Path, base: str, head: str, output: Path, *,
    validations: Sequence[Path] = (), developer_notes: Sequence[Path] = (),
    previous_reviews: Sequence[Path] = (),
) -> str:
    repo_root = Path(_git(repo, "rev-parse", "--show-toplevel").decode().strip())
    git_dir = Path(_git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
                   .decode().strip())
    _outside(output, export, repo_root, git_dir, *previous_reviews)
    exported = _tree(export)
    _export(exported)
    files, base, head = _capture(repo_root, base, head)
    files.update({f"export/{k}": v for k, v in exported.items()})
    inputs = {p: p.read_bytes() for p in [*validations, *developer_notes]}
    for path in validations:
        name = f"validations/{_validation(inputs[path], head)}.json"
        if name in files:
            raise ValueError("validation_id dupliqué")
        files[name] = inputs[path]
    for index, path in enumerate(developer_notes, 1):
        inputs[path].decode("utf-8")
        files[f"developer-notes/{index:04d}.md"] = inputs[path]
    antecedents = {p: _antecedent(p) for p in previous_reviews}
    for index, path in enumerate(previous_reviews, 1):
        files.update({f"antecedents/{index:04d}/{k}": v for k, v in antecedents[path].items()})
    identity = _identity(files)
    package_id = _sha(_dump(identity))
    files["review-request.md"] = _request(package_id, identity)
    files["sources.txt"] = ("\n".join(sorted([*files, "package.json"])) + "\n").encode()
    files["package.json"] = _dump({
        "schema_version": 1, "package_id": package_id, "identity": identity,
        "files": _manifest(files),
    })
    if _tree(export) != exported or any(p.read_bytes() != d for p, d in inputs.items()) or any(
        _antecedent(p) != data for p, data in antecedents.items()
    ):
        raise ValueError("entrée modifiée pendant la construction")
    _publish(output, files)
    return package_id


def read_package(package: Path) -> tuple[dict[str, bytes], dict[str, Any]]:
    files = _tree(package)
    allowed_roots = {"package.json", "sources.txt", "review-request.md"}
    allowed_prefixes = ("export/", "revision/", "validations/", "developer-notes/",
                        "antecedents/")
    if any(name not in allowed_roots and not name.startswith(allowed_prefixes)
           for name in files):
        raise ValueError("fichier hors structure du paquet")
    metadata = _json(files.get("package.json", b"{}"))
    _schema(metadata, {"schema_version", "package_id", "identity", "files"})
    if _manifest({k: v for k, v in files.items() if k != "package.json"}) != metadata["files"]:
        raise ValueError("paquet modifié, incomplet ou surnuméraire")
    revision = _json(files["revision/revision.json"])
    code_files = {k: v for k, v in files.items() if k.startswith("revision/")
                  and k != "revision/revision.json"}
    if revision["diff_sha256"] != _sha(files["revision/diff.patch"]) or (
        revision["code_files_manifest_sha256"] != _sha(_dump(_manifest(code_files)))
    ):
        raise ValueError("empreintes internes de la révision incohérentes")
    entries = json.loads(files["revision/files.json"])
    if not isinstance(entries, list):
        raise ValueError("liste des fichiers de code invalide")
    expected_blobs = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError("entrée de code invalide")
        name = _path(entry["path"])
        if entry.get("status") != "D" and entry.get("mode") != "160000":
            blob = files.get(f"revision/files/{name}")
            if blob is None or _sha(blob) != entry.get("sha256"):
                raise ValueError("blob différent de files.json")
            algorithm = hashlib.sha256 if len(str(entry.get("oid"))) == 64 else hashlib.sha1
            git_oid = algorithm(f"blob {len(blob)}\0".encode() + blob).hexdigest()
            if git_oid != entry.get("oid"):
                raise ValueError("OID du blob incohérent")
            expected_blobs[f"revision/files/{name}"] = blob
    if set(expected_blobs) != {k for k in files if k.startswith("revision/files/")
                               and k != "revision/files.json"}:
        raise ValueError("blobs du paquet incomplets ou surnuméraires")
    identity = _identity(files)
    if identity != metadata["identity"] or _sha(_dump(identity)) != metadata["package_id"]:
        raise ValueError("identité du paquet incohérente")
    _export({k[7:]: v for k, v in files.items() if k.startswith("export/")})
    expected = sorted(k for k in files if k != "sources.txt")
    if files["sources.txt"].decode().splitlines() != expected:
        raise ValueError("sources.txt ne désigne pas exactement le paquet")
    if files["review-request.md"] != _request(metadata["package_id"], identity):
        raise ValueError("demande de revue incohérente")
    for name, data in files.items():
        if name.startswith("validations/"):
            if name != f"validations/{_validation(data, identity['head_oid'])}.json":
                raise ValueError("nom de validation incohérent")
    return files, metadata


def verify_package(package: Path, review: Path) -> dict[str, Any]:
    files, metadata = read_package(package)
    config = Configuration.from_dict(_json((review / "configuration.json").read_bytes()))
    state = State.from_dict(_json((review / "etat.json").read_bytes()))
    if config.reviewer_access is not ReviewerAccess.CONSULT:
        raise ValueError("la revue du code exige consult")
    text = storage.read_text(review / "demande.md")[0]
    original = contracts.normalize(files["review-request.md"].decode()).text
    if contracts.normalize(original).sha256 != config.initial_demande_sha256 or (
        not contracts.normalize(text).text.startswith(original)
    ) or (
        decisions.demande_sha(review) != state.demande_sha256
    ):
        raise ValueError("demande de revue modifiée ou mauvais paquet")
    expected = {k: v for k, v in files.items() if k != "sources.txt"}
    if _tree(review / "corpus" / "fichiers") != expected:
        raise ValueError("le corpus ne correspond pas au paquet")
    manifest_path = review / "corpus" / "manifeste.json"
    if contracts.normalize(storage.read_text(manifest_path)[0]).sha256 != (
        config.corpus_manifest_sha256
    ):
        raise ValueError("manifeste différent de la configuration")
    manifest = corpus.read_manifest(manifest_path)
    actual = {e.logical_path: {"size": e.size, "sha256": e.sha256} for e in manifest.entries}
    if len(actual) != len(manifest.entries) or actual != _manifest(expected):
        raise ValueError("manifeste différent du paquet")
    decision = decisions.latest(review)
    if decisions.is_acceptance(decision) and decision and not decisions.applies_to_current(
        review, decision, state
    ):
        raise ValueError("décision devenue inapplicable")
    if state.status is Status.AWAITING_APPROVAL and decisions.acceptance_gaps(review, state):
        raise ValueError("rapport final ou critique manquant")
    entries = objections.ledger(review)
    return {
        "package_id": metadata["package_id"], "base_oid": metadata["identity"]["base_oid"],
        "head_oid": metadata["identity"]["head_oid"], "status": state.status.value,
        "validations": [n for n in expected if n.startswith("validations/")],
        "decision": decision["decision"] if decision else None,
        "open_findings": [e["id"] for e in entries if e["disposition"] == "OPEN"],
        "contested_or_arbitration": [e["id"] for e in entries
                                    if any(h.get("response") in {"CONTESTE", "ARBITRAGE"}
                                           for h in e["history"] if h["by"] == "A")],
        "limit": "Rattachement vérifié ; prose et exécution des validations non certifiées.",
    }

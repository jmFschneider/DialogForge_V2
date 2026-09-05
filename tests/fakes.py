"""Faux agent en ligne de commande, et collaboration jetable sur disque.

Aucun appel fournisseur, aucun réseau : la suite n'appelle jamais un modèle
payant (`RULES.md`). Le faux agent est néanmoins un **vrai** sous-processus,
parce que c'est justement le comportement de l'OS — deux tubes concurrents,
délai, terminaison d'arbre — que `transport.py` doit tenir. Un objet processus
simulé ne prouverait rien de ce pour quoi ce module existe.

`FakeAdapter` scripte les réponses de A et de B et compte ses appels : c'est ce
qui permet de prouver qu'une reprise **n'a repayé aucun appel**.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from iabinome import contracts, storage
from iabinome.adapters.base import CallSpec, Capabilities, ObservedCli
from iabinome.models import SCHEMA_VERSION, Role

_CHILD = (
    "import pathlib, time\n"
    "time.sleep({delay!r})\n"
    "pathlib.Path({marker!r}).write_text('vivant', encoding='utf-8')\n"
)


def command(
    *,
    stdout: str = "",
    stderr: str = "",
    stdout_bytes: int = 0,
    stderr_bytes: int = 0,
    rounds: int = 1,
    exit_code: int = 0,
    sleep_seconds: float = 0.0,
    child_marker: str | None = None,
    child_delay_seconds: float = 2.0,
    status_marker: str | None = None,
) -> list[str]:
    """Commande d'un faux agent.

    Il écrit sur les deux flux — `stdout_bytes`/`stderr_bytes` répartis en
    `rounds` tours **alternés**, de quoi bloquer un lecteur qui ne draine qu'un
    tube à la fois —, peut engendrer un petit-fils qui dépose `child_marker`
    après `child_delay_seconds` (la preuve qu'un arbre a survécu, s'il
    apparaît), dort, puis sort avec `exit_code`.

    `status_marker` fait relire `etat.json` **par le processus lancé** — le
    transport le lance avec `cwd` = dossier de collaboration — et y déposer le
    statut lu : c'est la seule preuve que `CALLING` a été publié avant `Popen`
    qui ne dépende pas d'un point d'observation situé dans le programme.

    `stdout_bytes` et `stderr_bytes` doivent être divisibles par `rounds`.
    """
    lines = ["import sys, time"]
    if status_marker is not None:
        lines.append(
            f"import json, pathlib; pathlib.Path({status_marker!r}).write_text("
            "json.loads(pathlib.Path('etat.json').read_text(encoding='utf-8'))['status'],"
            " encoding='utf-8')"
        )
    if child_marker is not None:
        child = _CHILD.format(delay=child_delay_seconds, marker=child_marker)
        lines.append(f"import subprocess; subprocess.Popen([sys.executable, '-c', {child!r}])")
    if stdout:
        lines.append(f"sys.stdout.write({stdout!r}); sys.stdout.flush()")
    if stderr:
        lines.append(f"sys.stderr.write({stderr!r}); sys.stderr.flush()")
    if stdout_bytes or stderr_bytes:
        lines.append(f"for _ in range({rounds}):")
        lines.append(f"    sys.stdout.write('x' * {stdout_bytes // rounds}); sys.stdout.flush()")
        lines.append(f"    sys.stderr.write('y' * {stderr_bytes // rounds}); sys.stderr.flush()")
    if sleep_seconds:
        lines.append(f"time.sleep({sleep_seconds!r})")
    lines.append(f"sys.exit({exit_code})")
    return [sys.executable, "-c", "\n".join(lines)]


class FakeAdapter:
    """Adaptateur de test : il rend les réponses scriptées, dans l'ordre.

    `calls` compte les **résolutions de commande**. Elles précèdent
    immédiatement le lancement, donc un compteur inchangé après une reprise
    reste la preuve qu'aucun appel n'a été repayé (§5) — mais l'inverse n'est
    pas vrai : un arrêt injecté entre la résolution et `Popen` incrémente le
    compteur sans qu'aucun appel parte. Pour compter les lancements réels,
    `launched_calls()` lit le disque.

    Une résolution consomme aussi une réponse scriptée, même si l'appel
    n'aboutit pas. C'est un artefact du faux agent, pas du moteur : un vrai
    adaptateur ne fait que résoudre un chemin dans `command()`."""

    def __init__(
        self,
        adapter_id: str = "fake",
        responses: tuple[str, ...] = (),
        *,
        supports_context_only: bool = True,
        supports_model_override: bool = True,
        present: bool = True,
        version: str = "fake 0.1.0",
        sleep_seconds: float = 0.0,
        exit_codes: tuple[int, ...] = (),
        status_marker: str | None = None,
    ) -> None:
        self.adapter_id = adapter_id
        self.capabilities = Capabilities(supports_context_only, supports_model_override)
        self.present = present
        self.version = version
        self.sleep_seconds = sleep_seconds
        self.status_marker = status_marker
        self.responses = list(responses)
        self.exit_codes = list(exit_codes)
        self.calls = 0
        self.prompts: list[str] = []
        self.observed_status: list[str] = []

    def default_model(self, role: Role) -> str:
        return f"{self.adapter_id}-modele-{role.value.lower()}"

    def probe(self) -> ObservedCli:
        return ObservedCli(present=self.present, version=self.version)

    def command(self, call: CallSpec) -> list[str]:
        self.calls += 1
        self.prompts.append(call.prompt)
        # `command` est résolu AVANT la publication de `CALLING` : relire l'état
        # ici prouve qu'un exécutable disparu serait refusé sans mutation, et
        # non déclaré « possiblement payé ». Que `CALLING` précède bien `Popen`
        # se prouve dans le processus lancé, par `status_marker`.
        etat = call.work_root / "etat.json"
        if etat.exists():
            self.observed_status.append(json.loads(etat.read_text(encoding="utf-8"))["status"])
        reply = self.responses.pop(0) if self.responses else "IABINOME:DOCUMENT\nvide"
        exit_code = self.exit_codes.pop(0) if self.exit_codes else 0
        return command(
            stdout=reply, exit_code=exit_code, sleep_seconds=self.sleep_seconds,
            status_marker=self.status_marker,
        )

    def extract(self, stdout: bytes, stderr: bytes) -> str:
        return stdout.decode("utf-8")


def collaboration(
    root: Path,
    *,
    demande: str = "Concevoir le cache de FloraPi.",
    mission_kind: str = "CONCEPTION",
    reviewer_access: str = "CONSULT",
    max_revisions: int = 2,
    adapter_a: str = "fake-a",
    adapter_b: str = "fake-b",
    model_a: str = "fake-a-modele-a",
    model_b: str = "fake-b-modele-b",
    corpus_captured_at: str | None = None,
    corpus_files: dict[str, str] | None = None,
) -> Path:
    """Écrit une collaboration prête à `run` : configuration, demande, état.

    `corpus_captured_at` non nul ajoute un manifeste de corpus figé à cette
    date ; `corpus_files` y dépose de vrais fichiers, avec leurs vraies tailles
    et empreintes — depuis le lot 5, le manifeste est confronté au contenu.
    """
    collab = root / "collaboration"
    collab.mkdir(parents=True, exist_ok=True)
    storage.write_atomic_text(collab / "demande.md", demande)
    digest = contracts.normalize(demande).sha256
    manifest_sha: str | None = None
    if corpus_captured_at is not None:
        (collab / "corpus").mkdir(exist_ok=True)
        entries = []
        for name, content in (corpus_files or {}).items():
            data = content.encode("utf-8")
            destination = collab / "corpus" / "fichiers" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            storage.write_atomic_bytes(destination, data)
            entries.append({
                "chemin": name, "taille": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            })
        payload = json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "captured_at": f"{corpus_captured_at}T00:00:00Z",
                "origin_label": "FloraPi",
                "files": entries,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n"
        storage.write_atomic_text(collab / "corpus" / "manifeste.json", payload)
        manifest_sha = contracts.normalize(payload).sha256
    write_json(collab / "configuration.json", {
        "schema_version": SCHEMA_VERSION, "collaboration_id": "etude", "mission_kind": mission_kind,
        "reviewer_access": reviewer_access, "max_revisions": max_revisions,
        "agent_a": {"adapter_id": adapter_a, "model": model_a},
        "agent_b": {"adapter_id": adapter_b, "model": model_b},
        "initial_demande_sha256": digest, "corpus_manifest_sha256": manifest_sha,
        "created_at": "2026-09-03T00:00:00Z",
    })
    write_json(collab / "etat.json", {
        "schema_version": SCHEMA_VERSION, "status": "READY", "phase": "PROPOSAL_A",
        "revision": 0, "demande_sha256": digest, "current_document": None,
        "latest_review": None, "open_finding_ids": [], "current_call": None,
        "last_incident": None, "updated_at": "2026-09-03T00:00:00Z",
    })
    return collab


def launched_calls(collab: Path) -> int:
    """Nombre d'appels **réellement lancés**, lu sur le disque.

    `FakeAdapter.calls` compte les *résolutions de commande*, qui précèdent
    immédiatement le lancement : c'en est une borne supérieure, pas la mesure.
    Depuis que `command()` est résolu avant le premier octet écrit, un arrêt
    injecté entre les deux incrémente le compteur sans qu'aucun appel soit
    parti. `stdout.txt` n'existe, lui, que si le transport a lancé le processus.
    """
    appels = collab / "appels"
    if not appels.is_dir():
        return 0
    return sum(1 for d in appels.iterdir() if (d / "stdout.txt").exists())


def call_result(call_dir: Path, *, return_code: int = 0) -> None:
    """Écrit un `resultat.json` **cohérent avec les flux réellement présents**.

    Les empreintes ne sont plus fabriquées : depuis le lot 4, un `resultat.json`
    valide mais contredit par les fichiers est une divergence. Des empreintes de
    zéros transformeraient chaque test de reprise **nominale** en scénario de
    corruption — et la suite mesurerait alors le contraire de ce qu'elle dit.
    """
    stdout = (call_dir / "stdout.txt").read_bytes()
    stderr = (call_dir / "stderr.txt").read_bytes()
    write_json(call_dir / "resultat.json", {
        "schema_version": SCHEMA_VERSION, "return_code": return_code,
        "stdout_bytes": len(stdout), "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_bytes": len(stderr), "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "duration_seconds": 1.0,
    })


def write_json(path: Path, payload: dict[str, Any]) -> None:
    storage.write_atomic_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def review(
    decision: str = "REVISER",
    findings: tuple[dict[str, str], ...] = ({
        "id": "B-001", "severity": "MAJOR", "disposition": "OPEN", "statement": "Manque X.",
    },),
    analysis: str = "Critique synthetique.",
) -> str:
    return json.dumps({
        "schema_version": SCHEMA_VERSION, "decision": decision,
        "analysis": analysis, "findings": list(findings),
    }, ensure_ascii=False)

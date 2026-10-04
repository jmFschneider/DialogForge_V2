"""Parcours « Nouveau projet » et « Dépôt existant » de bout en bout, et leurs reprises.

La session GUI est réelle, le pont est un vrai sous-processus qui rejoue le protocole de
`gui_bridge` (profil local, faux agent) : aucun appel fournisseur, pas de WSL.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import mock

from dialogforge_runner import core
from iabinome import development, executions, mission
from iabinome.gui.runner_session import RunnerRequest, RunnerSession
from tests.runner_support import AGENT, BRIDGE, OWNER, accepted_conception, git, git_home

TOKEN = "jeton-secret-de-test-4711"


@unittest.skipUnless(shutil.which("git"), "Git requis")
class FlowCase(unittest.TestCase):
    collab: Path

    def setUp(self) -> None:
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        patch = git_home(self.root)
        patch.__enter__()
        self.addCleanup(patch.__exit__, None, None, None)
        self.collab = accepted_conception(self.root)
        self.agent, self.log = self.root / "agent.py", self.root / "agent.log"
        self.agent.write_text(AGENT, encoding="utf-8")
        self.log.write_text("", encoding="utf-8")
        self.mode("ok")
        for context in (
            mock.patch.dict(os.environ, {
                "RUNNER_TEST_AGENT": str(self.agent), "RUNNER_TEST_LOG": str(self.log),
                "PYTHONIOENCODING": "utf-8",  # le pont de production tourne sous Linux, en UTF-8
            }),
            mock.patch("iabinome.gui.runner_session._bridge_command",
                       side_effect=lambda distro=None: [sys.executable, str(BRIDGE)]),
        ):
            context.__enter__()
            self.addCleanup(context.__exit__, None, None, None)
        self.code = executions.default_code(self.collab)
        self.run_path = self.root / "runs" / "run-001"

    def mode(self, value: str) -> None:
        os.environ["RUNNER_TEST_MODE"] = value

    def agent_calls(self) -> int:
        return len(self.log.read_text(encoding="utf-8").split())

    def request(self, action: str, **overrides: Any) -> RunnerRequest:
        found = overrides.pop("found", None) or executions.find(self.collab)
        arguments: dict[str, Any] = {
            "action": action, "collaboration": self.collab, "found": found,
            "mode": "nouveau", "repo": self.code, "base": "HEAD",
            "validations": [["git", "--version"]], "run": str(self.run_path),
            "token": TOKEN, "timeout": 60.0, "validation_timeout": 30.0, "distro": None,
            **overrides,
        }
        if action not in {"start", "launch", "continue", "correct"}:
            arguments["token"] = ""
        return RunnerRequest(**arguments)

    def go(self, action: str, *, signals: tuple[str, ...] = (), **overrides: Any) -> RunnerSession:
        session = RunnerSession(self.request(action, **overrides))
        for signal in signals:
            session.signal(signal)
        session.start()
        session.thread.join(timeout=120)
        self.assertFalse(session.thread.is_alive(), "la session ne s'est pas terminée")
        return session

    def resume(self, action: str, **overrides: Any) -> RunnerSession:
        """Reprise : tout vient de la référence enregistrée, comme depuis l'écran."""
        data = executions.find(self.collab).data
        assert data is not None
        project = data["projet"]
        return self.go(
            action, mode=project["mode"], repo=Path(project["depot"]),
            base=project["base_demandee"], validations=data["validations"], run=data["run"],
            **overrides,
        )

    def state(self) -> dict[str, Any]:
        session = self.resume("inspect")
        self.assertIsNone(session.error)
        assert session.state is not None
        return session.state

    def reference(self) -> dict[str, Any]:
        data = executions.find(self.collab).data
        assert data is not None
        return data

    def commits(self, repo: Path) -> int:
        return int(git(repo, "rev-list", "--all", "--count"))


class NewProjectFlowTest(FlowCase):
    def test_a_new_project_reaches_a_package_and_the_source_stays_untouched(self) -> None:
        session = self.go("start")
        self.assertIsNone(session.error)
        assert session.package is not None
        initial = git(self.code, "rev-list", "--max-parents=0", "HEAD")
        self.assertEqual(self.commits(self.code), 1)
        self.assertEqual(git(self.code, "ls-tree", "-r", "--name-only", "HEAD"), "")
        self.assertEqual(git(self.code, "status", "--porcelain"), "")
        self.assertEqual(git(self.code, "log", "-1", "--format=%an <%ae>"),
                         f"{OWNER[0]} <{OWNER[1]}>")
        workspace = self.run_path / "workspace"
        self.assertEqual(git(workspace, "rev-parse", "HEAD~1"), initial)
        self.assertTrue((workspace / "app.txt").exists())
        self.assertFalse((self.code / "app.txt").exists())
        _, metadata = development.read_package(Path(session.package))
        self.assertEqual(metadata["identity"]["base_oid"], initial)
        self.assertEqual(self.agent_calls(), 1)

    def test_the_reference_records_the_run_and_the_packages(self) -> None:
        session = self.go("start")
        data = self.reference()
        initial = git(self.code, "rev-parse", "HEAD")
        self.assertEqual(data["projet"]["mode"], "nouveau")
        self.assertEqual(data["projet"]["base_oid"], initial)
        self.assertEqual(data["projet"]["identite"], f"{OWNER[0]} <{OWNER[1]}>")
        self.assertEqual(data["run"], str(self.run_path))
        self.assertEqual(data["paquets"], [session.package])
        self.assertEqual(data["validations"], [["git", "--version"]])
        self.assertEqual(self.state()["stage"], "paquet")

    def test_a_finished_package_exports_only_its_exact_git_candidate(self) -> None:
        session = self.go("start")
        assert session.package is not None
        package = Path(session.package)
        identity = development.read_package(package)[1]
        bundle = core.bundle_candidate(self.run_path, package, identity["package_id"])
        self.assertEqual(core.bundle_candidate(self.run_path, package,
                                               identity["package_id"]), bundle)
        self.assertIn(identity["identity"]["head_oid"],
                      git(self.run_path / "workspace", "bundle", "list-heads", str(bundle)))
        with self.assertRaisesRegex(ValueError, "identité du paquet"):
            core.bundle_candidate(self.run_path, package, "0" * 64)

    def test_the_token_is_never_persisted_nor_given_to_a_process_argument(self) -> None:
        with mock.patch(
            "iabinome.gui.runner_session.subprocess.Popen", wraps=subprocess.Popen,
        ) as popen:
            self.go("start")
        for path in self.root.rglob("*"):
            if path.is_file() and ".git" not in path.parts and path.stat().st_size < 5_000_000:
                self.assertNotIn(TOKEN.encode(), path.read_bytes(), str(path))
        self.assertTrue(popen.call_args_list)
        for call in popen.call_args_list:
            self.assertFalse(any(TOKEN in part for part in call.args[0]), call.args[0])

    def test_an_open_finding_of_the_accepted_conception_reaches_the_agent(self) -> None:
        self.collab = accepted_conception(self.root / "reserves", open_finding=True)
        self.code = executions.default_code(self.collab)
        self.assertIsNone(self.go("start").error)
        prompt = (self.run_path / "calls" / "call-0001" / "prompt.md").read_text(encoding="utf-8")
        opened = prompt.split("## Constats ouverts", 1)[1].split("## Passage de relais")[0]
        self.assertIn('"id": "B-001"', opened)
        self.assertIn('"disposition": "OPEN"', opened)
        self.assertIn("recette à rendre reproductible", prompt)
        self.assertIn("La revue du candidat les réexaminera", opened)

    def test_a_missing_prerequisite_stops_before_any_mutation(self) -> None:
        session = self.go("start", validations=[["outil-introuvable-4821", "--test"]])
        self.assertIn("introuvable", session.error or "")
        self.assertFalse(self.code.exists())
        self.assertFalse(executions.dev_dir(self.collab).exists())
        self.assertEqual(self.agent_calls(), 0)

    def test_an_occupied_folder_and_a_missing_identity_stop_before_any_mutation(self) -> None:
        self.code.mkdir(parents=True)
        (self.code / "mien.txt").write_text("x", encoding="utf-8")
        session = self.go("start")
        self.assertIn("Dépôt existant", session.error or "")
        self.assertEqual([p.name for p in self.code.iterdir()], ["mien.txt"])
        shutil.rmtree(self.code)
        with git_home(self.root / "sans-identite", identity=None):
            session = self.go("start")
        self.assertIn("identité Git absente", session.error or "")
        self.assertFalse(self.code.exists())
        self.assertFalse(executions.dev_dir(self.collab).exists())
        self.assertEqual(self.agent_calls(), 0)

    def test_a_stale_acceptance_is_refused_before_anything(self) -> None:
        request = self.request("start")
        demande = self.collab / "demande.md"
        demande.write_bytes(demande.read_bytes() + b"\nChangement.\n")
        session = RunnerSession(request)
        session.start()
        session.thread.join(timeout=60)
        self.assertIn("version actuelle", session.error or "")
        self.assertFalse(self.code.exists())

    def test_inside_a_mission_the_project_and_the_files_stay_in_the_mission(self) -> None:
        mission_root = self.root / "Mastermind"
        mission_root.mkdir()
        shutil.move(self.collab, mission_root / "conception")
        mission.attach(mission_root, mission_root / "conception", "conception")
        self.collab = mission_root / "conception"
        self.code = executions.default_code(self.collab)
        session = self.go("start")
        self.assertIsNone(session.error)
        self.assertEqual(self.code, mission_root / "code")
        self.assertEqual(self.commits(self.code), 1)
        self.assertTrue((mission_root / "developpement" / "export-001" / "export.md").is_file())
        self.assertTrue((mission_root / "developpement" / "executions" / "001.json").is_file())


class ExistingRepositoryFlowTest(FlowCase):
    def setUp(self) -> None:
        super().setUp()
        self.repo = self.root / "depot"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        (self.repo / "code.txt").write_text("base\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "base")
        self.base = git(self.repo, "rev-parse", "HEAD")

    def existing(self, action: str = "start", **overrides: Any) -> RunnerSession:
        return self.go(action, mode="existant", repo=self.repo, base="HEAD", **overrides)

    def test_an_existing_repository_still_reaches_a_package(self) -> None:
        session = self.existing()
        self.assertIsNone(session.error)
        assert session.package is not None
        _, metadata = development.read_package(Path(session.package))
        self.assertEqual(metadata["identity"]["base_oid"], self.base)
        self.assertEqual(git(self.repo, "rev-parse", "HEAD"), self.base)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")
        self.assertFalse((self.repo / "app.txt").exists())
        data = self.reference()
        self.assertEqual((data["projet"]["mode"], data["projet"]["base_oid"]),
                         ("existant", self.base))
        self.assertFalse(self.code.exists(), "aucun projet neuf n'est créé")

    def test_only_committed_files_enter_the_clone(self) -> None:
        (self.repo / "brouillon.txt").write_text("non commité", encoding="utf-8")
        self.assertIsNone(self.existing().error)
        self.assertFalse((self.run_path / "workspace" / "brouillon.txt").exists())
        self.assertEqual(git(self.repo, "status", "--porcelain"), "?? brouillon.txt")

    def test_a_failed_preparation_keeps_the_export_and_resumes_on_it(self) -> None:
        session = self.existing(validations=[["outil-introuvable-4821"]])
        self.assertIn("introuvable", session.error or "")
        dev = executions.dev_dir(self.collab)
        self.assertEqual([p.name for p in dev.glob("export-*")], ["export-001"])
        self.assertEqual([p.name for p in (dev / "executions").glob("*.json")], ["001.json"])
        self.assertFalse(self.run_path.exists())
        self.assertEqual(self.state()["stage"], "absent")
        stamp = (dev / "export-001" / "export.md").stat().st_mtime_ns
        session = self.existing()
        self.assertIsNone(session.error)
        self.assertEqual([p.name for p in dev.glob("export-*")], ["export-001"])
        self.assertEqual([p.name for p in (dev / "executions").glob("*.json")], ["001.json"])
        self.assertEqual((dev / "export-001" / "export.md").stat().st_mtime_ns, stamp)
        self.assertEqual(self.reference()["validations"], [["git", "--version"]])

    def test_a_clone_prepared_but_not_launched_is_launched_explicitly_once(self) -> None:
        session = self.existing(signals=("pause",))
        self.assertIn("lancement arrêté", session.error or "")
        self.assertEqual(self.agent_calls(), 0)
        state = self.state()
        self.assertEqual((state["stage"], state["calls"]), ("prepare", 0))
        self.assertNotIn("start", executions.actions(state))
        self.assertEqual(self.agent_calls(), 0, "relire l'état ne lance rien")
        self.assertIsNone(self.resume("launch").error)
        self.assertEqual(self.agent_calls(), 1)
        self.assertEqual(self.state()["stage"], "paquet")

    def test_an_interrupted_call_is_never_replayed_without_a_continuation(self) -> None:
        self.mode("fail")
        session = self.existing()
        self.assertIn("appel agent interrompu ou échoué", session.error or "")
        state = self.state()
        self.assertEqual((state["stage"], state["calls"]), ("appel", 1))
        self.assertEqual(executions.actions(state), ("continue", "collect"))
        self.assertIn("continuation explicite", self.resume("launch").error or "")
        self.assertEqual(self.agent_calls(), 1)
        self.mode("ok")
        session = self.resume("continue")
        self.assertIsNone(session.error)
        self.assertEqual(self.agent_calls(), 2)
        self.assertEqual(len(self.reference()["paquets"]), 1)

    def test_authentication_error_is_named_without_replaying_the_agent(self) -> None:
        self.mode("auth")
        session = self.existing()
        self.assertIn("authentification de l'agent refusée (401)", session.error or "")
        self.assertEqual(self.agent_calls(), 1)

    def test_failed_validations_are_collected_again_without_calling_the_agent(self) -> None:
        session = self.existing(validations=[["git", "sous-commande-inconnue-9"]],
                                max_calls=1)
        self.assertIn("validation 1 échouée", session.error or "")
        state = self.state()
        self.assertEqual((state["stage"], state["collects"]), ("validations", 1))
        self.assertEqual(self.agent_calls(), 1)
        again = self.resume("collect")
        self.assertIn("validation 1 échouée", again.error or "")
        self.assertEqual(self.agent_calls(), 1)
        self.assertEqual(self.state()["collects"], 2)
        self.assertEqual(self.reference()["paquets"], [])

    def test_failed_validation_is_repaired_within_one_authorized_run(self) -> None:
        self.mode("repair")
        checker = self.root / "check.py"
        checker.write_text(
            "from pathlib import Path\n"
            "raise SystemExit(0 if Path('app.txt').read_text() == "
            "'resultat de l\\'agent\\n' else 1)\n", encoding="utf-8",
        )
        session = self.existing(validations=[[sys.executable, str(checker)]])
        self.assertIsNone(session.error)
        self.assertEqual(self.agent_calls(), 2)
        self.assertEqual(len(self.reference()["paquets"]), 1)
        self.assertEqual(self.state()["stage"], "paquet")

    def test_a_package_requires_a_named_correction_before_another_agent_call(self) -> None:
        self.assertIsNone(self.existing().error)
        self.assertIn("préciser la correction", self.resume("continue").error or "")
        self.assertEqual(self.agent_calls(), 1)
        self.mode("improve")
        session = self.resume("correct", correction="Améliorer la documentation.")
        self.assertIsNone(session.error)
        self.assertEqual(self.agent_calls(), 2)
        self.assertEqual(len(self.reference()["paquets"]), 2)

    def test_a_correction_without_new_commit_keeps_the_previous_package(self) -> None:
        self.assertIsNone(self.existing().error)
        first = self.reference()["paquets"][0]
        self.mode("noop")
        session = self.resume("correct", correction="Préciser le bilan.")
        self.assertIn("aucun nouveau commit", session.error or "")
        self.assertEqual(self.reference()["paquets"], [first])

    def test_a_successful_package_then_a_failed_collection_keeps_both_visible(self) -> None:
        self.assertIsNone(self.existing().error)
        first = self.reference()["paquets"][0]
        run_json = self.run_path / "run.json"
        config = json.loads(run_json.read_text(encoding="utf-8"))
        config["validations"] = [["git", "sous-commande-inconnue-9"]]
        run_json.write_text(json.dumps(config), encoding="utf-8")
        self.assertIn("validation 1 échouée", self.resume("collect").error or "")
        state = self.state()  # réouverture : tout est relu sur le dossier
        self.assertEqual((state["stage"], state["last_collect"], state["collects"]),
                         ("validations", "echouee", 2))
        self.assertEqual(state["package"], first, "le paquet antérieur reste indiqué")
        described = executions.describe(state)
        self.assertIn("collecte échouée", described)
        self.assertIn("ne valide pas le code actuel", described)
        self.assertIn(first, described)

    def test_a_conception_changed_after_the_preparation_calls_no_agent(self) -> None:
        session = self.existing(signals=("pause",))
        self.assertIn("lancement arrêté", session.error or "")
        self.assertEqual(self.state()["stage"], "prepare")
        found = executions.find(self.collab)
        demande = self.collab / "demande.md"
        demande.write_bytes(demande.read_bytes() + b"\nChangement apres preparation.\n")
        for action in ("launch", "continue"):
            session = self.go(action, found=found, mode="existant", repo=self.repo,
                              run=str(self.run_path))
            self.assertIn("la conception a changé depuis l'export", session.error or "")
            self.assertIn("aucun agent n'est appelé", session.error or "")
        self.assertEqual(self.agent_calls(), 0)
        state = core.inspect_run(self.run_path)
        self.assertEqual((state["stage"], state["calls"]), ("prepare", 0), "clone conservé")

    def test_the_run_folder_is_read_back_after_a_closed_window(self) -> None:
        self.assertIsNone(self.existing().error)
        first = self.reference()
        state = self.state()
        self.assertEqual(state["stage"], "paquet")
        self.assertEqual(state["package"], first["paquets"][0])
        self.assertEqual(state["base_oid"], self.base)
        self.assertEqual(executions.actions(state), ("correct",))


class InitialBaseReuseTest(FlowCase):
    def test_a_failed_clone_never_recreates_the_initial_repository(self) -> None:
        self.run_path.mkdir(parents=True)
        session = self.go("start")
        self.assertIn("existe déjà", session.error or "")
        initial = git(self.code, "rev-parse", "HEAD")
        self.assertEqual(self.commits(self.code), 1)
        self.assertEqual(self.reference()["projet"]["base_oid"], initial)
        self.assertEqual(self.state()["stage"], "invalide", "le dossier occupé n'est pas un run")
        shutil.rmtree(self.run_path)
        with mock.patch.object(core, "init_project", wraps=core.init_project) as init:
            session = self.go("start")
        self.assertIsNone(session.error)
        init.assert_not_called()
        self.assertEqual(git(self.code, "rev-parse", "HEAD"), initial)
        self.assertEqual(self.commits(self.code), 1)
        self.assertEqual(self.agent_calls(), 1)

    def test_a_modified_initial_repository_is_not_reused(self) -> None:
        self.run_path.mkdir(parents=True)
        self.assertIn("existe déjà", self.go("start").error or "")
        shutil.rmtree(self.run_path)
        (self.code / "ajout.txt").write_text("x", encoding="utf-8")
        session = self.go("start")
        self.assertIn("n'est plus le dépôt initial", session.error or "")
        self.assertFalse(self.run_path.exists())
        self.assertEqual(self.agent_calls(), 0)

"""Passage de relais du Runner sur de petits dépôts, sans appel fournisseur."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from dialogforge_runner import cli, core
from iabinome import development, transport


@unittest.skipUnless(shutil.which("git"), "Git requis")
class RunnerTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.repo = self.root / "source"
        self.repo.mkdir()
        self.git(self.repo, "init", "-q")
        self.git(self.repo, "config", "user.name", "Runner Test")
        self.git(self.repo, "config", "user.email", "runner@example.invalid")
        self.git(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / "code.txt").write_text("base\n", encoding="utf-8")
        self.git(self.repo, "add", ".")
        self.git(self.repo, "commit", "-qm", "base")
        self.base = self.git(self.repo, "rev-parse", "HEAD")
        self.export = self.root / "export"
        self.export.mkdir()
        mandate = b"# Mandat\n\nModifier code.txt.\n"
        (self.export / "export.md").write_bytes(mandate)
        metadata = {
            "schema_version": 1, "source_collaboration": "test",
            "request_sha256": "a", "document_sha256": "b", "review_sha256": "c",
            "decision_sha256": "d", "export_md_sha256": hashlib.sha256(mandate).hexdigest(),
        }
        (self.export / "export.json").write_text(json.dumps(metadata), encoding="utf-8")
        self.run_dir = self.root / "run"

    @staticmethod
    def git(repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, check=True,
        )
        return result.stdout.decode().strip()

    def prepare(self, command: list[str] | None = None) -> Path:
        core.prepare(
            self.export, self.repo, self.base, self.run_dir,
            validations=[command or [sys.executable, "-c", "print('ok')"]],
        )
        workspace = self.run_dir / "workspace"
        self.git(workspace, "config", "user.name", "Runner Test")
        self.git(workspace, "config", "user.email", "runner@example.invalid")
        self.git(workspace, "config", "commit.gpgsign", "false")
        return workspace

    def candidate(self, workspace: Path) -> None:
        (workspace / "code.txt").write_text("candidate\n", encoding="utf-8")
        self.git(workspace, "add", ".")
        self.git(workspace, "commit", "-qm", "candidate")

    def test_prepare_and_collect_package_exact_head(self) -> None:
        workspace = self.prepare()
        self.assertEqual(self.git(workspace, "remote"), "")
        self.assertEqual(self.git(workspace, "rev-parse", "HEAD"), self.base)
        self.assertFalse((workspace / ".git" / "objects" / "info" / "alternates").exists())
        self.candidate(workspace)
        head = self.git(workspace, "rev-parse", "HEAD")
        package = core.collect(self.run_dir)
        files, metadata = development.read_package(package)
        self.assertEqual(metadata["identity"]["head_oid"], head)
        self.assertEqual(files["revision/files/code.txt"], b"candidate\n")
        validation = json.loads(files["validations/validation-01.json"])
        self.assertEqual(validation["outcome"], "PASSED")
        self.assertEqual(validation["head_oid"], head)
        self.assertTrue(core.collect(self.run_dir).is_dir())
        self.assertTrue(package.is_dir())
        self.assertEqual((self.repo / "code.txt").read_text(encoding="utf-8"), "base\n")

    def test_failed_validation_preserves_logs_without_package(self) -> None:
        workspace = self.prepare([sys.executable, "-c", "raise SystemExit(7)"])
        self.candidate(workspace)
        with self.assertRaisesRegex(ValueError, "validation 1 échouée"):
            core.collect(self.run_dir)
        attempt = self.run_dir / "results" / "collect-0001"
        self.assertFalse((attempt / "package").exists())
        self.assertTrue((attempt / "validation-01" / "validation.json").exists())

    def test_interrupted_collect_does_not_start_validation(self) -> None:
        workspace = self.prepare()
        self.candidate(workspace)
        control = transport.ExecutionControl()
        control.interrupt_requested.set()
        with self.assertRaisesRegex(ValueError, "collecte interrompue"):
            core.collect(self.run_dir, control=control)
        attempt = self.run_dir / "results" / "collect-0001"
        self.assertFalse((attempt / "validation-01").exists())
        self.assertFalse((attempt / "package").exists())

    def test_validation_that_changes_candidate_is_refused(self) -> None:
        workspace = self.prepare([
            sys.executable, "-c", "from pathlib import Path; Path('code.txt').write_text('bad')",
        ])
        self.candidate(workspace)
        with self.assertRaisesRegex(ValueError, "a modifié le candidat"):
            core.collect(self.run_dir)
        self.assertFalse((self.run_dir / "results" / "collect-0001" / "package").exists())

    def test_missing_validation_command_is_recorded(self) -> None:
        workspace = self.prepare(["runner-command-does-not-exist-98765"])
        self.candidate(workspace)
        with self.assertRaisesRegex(ValueError, "validation 1 non lancée"):
            core.collect(self.run_dir)
        path = self.run_dir / "results" / "collect-0001" / "validation-01" / "validation.json"
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["outcome"], "NOT_RUN")

    def test_modified_export_is_refused_before_clone(self) -> None:
        (self.export / "export.md").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "export.md modifié"):
            self.prepare()
        self.assertFalse(self.run_dir.exists())

    def test_cli_prepare_uses_json_argv_without_shell(self) -> None:
        checks = self.root / "checks.json"
        checks.write_text(json.dumps([[sys.executable, "-c", "print('ok')"]]), encoding="utf-8")
        self.assertEqual(cli.main([
            "prepare", "--export", str(self.export), "--repo", str(self.repo),
            "--base", self.base, "--checks", str(checks), "--output", str(self.run_dir),
        ]), 0)
        self.assertTrue((self.run_dir / "run.json").exists())

    def test_fake_agent_reaches_package_without_task_orchestration(self) -> None:
        self.prepare()
        fake = self.root / "fake_agent.py"
        fake.write_text(
            "import pathlib, subprocess, sys\n"
            "prompt = sys.stdin.read()\n"
            "assert 'Modifier code.txt' in prompt\n"
            "pathlib.Path('code.txt').write_text('agent result\\n')\n"
            "subprocess.run(['git', 'add', 'code.txt'], check=True)\n"
            "subprocess.run(['git', 'commit', '-qm', 'agent candidate'], check=True)\n"
            "print('Bilan : changement terminé')\n"
            "print('RUNNER: CANDIDAT')\n",
            encoding="utf-8",
        )
        package = core.run_agent(self.run_dir, [sys.executable, str(fake)], timeout_seconds=10)
        files, _ = development.read_package(package)
        self.assertEqual(files["revision/files/code.txt"], b"agent result\n")
        self.assertIn(b"Bilan : changement", files["developer-notes/0001.md"])
        self.assertTrue((self.run_dir / "calls" / "call-0001" / "resultat.json").exists())
        self.assertTrue((self.run_dir / "calls" / "call-0001" / "prompt.md").exists())

    def test_failed_agent_is_not_replayed_without_explicit_continuation(self) -> None:
        workspace = self.prepare()
        with self.assertRaisesRegex(ValueError, "appel agent interrompu ou échoué"):
            core.run_agent(
                self.run_dir, [sys.executable, "-c", "raise SystemExit(7)"],
                timeout_seconds=10,
            )
        with self.assertRaisesRegex(ValueError, "continuation explicite"):
            core.run_agent(
                self.run_dir, [sys.executable, "-c", "print('not called')"],
                timeout_seconds=10,
            )
        self.assertEqual(len(list((self.run_dir / "calls").glob("call-*"))), 1)
        self.candidate(workspace)
        package = core.run_agent(
            self.run_dir, [sys.executable, "-c", "print('continued\\nRUNNER: CANDIDAT')"],
            timeout_seconds=10, continue_existing=True,
        )
        self.assertTrue(package.exists())

    def test_the_final_line_is_read_strictly(self) -> None:
        for text, expected in (
            ("Bilan\nRUNNER: CANDIDAT\n", "CANDIDAT"), ("x\n`RUNNER: RESTE`\n\n", "RESTE"),
            ("RUNNER: INTERVENTION", "INTERVENTION"), ("RUNNER: CANDIDAT\nMerci.", None),
            ("RUNNER: candidat", None), ("RUNNER: CANDIDAT ou RESTE", None), ("", None),
        ):
            with self.subTest(text=text):
                self.assertEqual(core.final_line(text), expected)

    def test_a_dirty_workspace_goes_back_to_the_agent_before_any_validation(self) -> None:
        self.prepare()
        script = self.root / "agent.py"
        script.write_text(
            "import pathlib, subprocess, sys\n"
            "prompt = sys.stdin.read()\n"
            "pathlib.Path('code.txt').write_text('agent result\\n')\n"
            "if 'non propre' in prompt:\n"
            "    subprocess.run(['git', 'commit', '-qam', 'fini'], check=True)\n"
            "print('RUNNER: CANDIDAT')\n",
            encoding="utf-8",
        )
        package = core.run_agent(self.run_dir, [sys.executable, str(script)], timeout_seconds=30)
        self.assertTrue(package.exists())
        self.assertEqual(len(list((self.run_dir / "calls").glob("call-*"))), 2)
        self.assertEqual(len(list((self.run_dir / "results").glob("collect-*"))), 1)

    def test_claude_profile_requires_native_linux_run(self) -> None:
        if sys.platform == "linux":
            self.skipTest("Windows WSL boundary check")
        with self.assertRaisesRegex(ValueError, "natif Linux"):
            core.prepare(
                self.export, self.repo, self.base, self.run_dir,
                validations=[["true"]], profile="claude-wsl",
            )
        self.assertFalse(self.run_dir.exists())

    def test_claude_profile_sandboxes_validation_and_drops_agent_token(self) -> None:
        with patch.object(core, "_require_linux_run"):
            core.prepare(
                self.export, self.repo, self.base, self.run_dir,
                validations=[[sys.executable, "-c", "print('ok')"]],
                profile="claude-wsl",
            )
        workspace = self.run_dir / "workspace"
        self.git(workspace, "config", "user.name", "Runner Test")
        self.git(workspace, "config", "user.email", "runner@example.invalid")
        self.candidate(workspace)
        actual_run = transport.run
        observed: list[str] = []

        def simulate_srt(command: list[str], **kwargs: object) -> transport.CallResult:
            observed.extend(command)
            environment = kwargs["env"]
            assert isinstance(environment, dict)
            self.assertNotIn("CLAUDE_CODE_OAUTH_TOKEN", environment)
            return actual_run(command[4:], **kwargs)  # type: ignore[arg-type]

        with patch.object(core, "_require_linux_run"), patch.dict(
            "os.environ", {"CLAUDE_CODE_OAUTH_TOKEN": "test-secret"}
        ), patch.object(transport, "run", side_effect=simulate_srt):
            package = core.collect(self.run_dir)
        self.assertTrue(package.exists())
        self.assertEqual(observed[:2], ["/usr/local/bin/srt", "--settings"])
        self.assertEqual(observed[3], "--")
        settings = json.loads((self.run_dir / "srt-settings.json").read_text())
        self.assertEqual(settings["filesystem"]["allowWrite"], ["."])
        self.assertEqual(settings["filesystem"]["denyRead"], [str(Path.home())])
        self.assertEqual(settings["filesystem"]["allowRead"], ["."])

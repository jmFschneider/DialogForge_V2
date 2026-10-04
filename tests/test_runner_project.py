"""Projet neuf, prérequis et lecture d'un dossier Runner — dépôts jetables, aucun fournisseur."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from dialogforge_runner import cli, core
from tests.runner_support import OWNER, git, git_home


@unittest.skipUnless(shutil.which("git"), "Git requis")
class NewProjectTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        patch = git_home(self.root)
        self.home = patch.__enter__()
        self.addCleanup(patch.__exit__, None, None, None)
        self.code = self.root / "Mission" / "code"

    def test_creates_one_empty_commit_with_the_configured_identity(self) -> None:
        before = (self.home / ".gitconfig").read_bytes()
        oid, author = core.init_project(self.code)
        self.assertEqual(git(self.code, "rev-parse", "HEAD"), oid)
        self.assertEqual(git(self.code, "rev-list", "--all", "--count"), "1")
        self.assertEqual(git(self.code, "ls-tree", "-r", "--name-only", oid), "")
        self.assertEqual(author, f"{OWNER[0]} <{OWNER[1]}>")
        self.assertEqual(git(self.code, "log", "-1", "--format=%an <%ae> %cn <%ce>"),
                         f"{author} {author}")
        with self.assertRaises(subprocess.CalledProcessError):
            git(self.code, "config", "--local", "--get", "user.name")
        self.assertEqual((self.home / ".gitconfig").read_bytes(), before)

    def test_an_empty_folder_is_accepted_and_kept(self) -> None:
        self.code.mkdir(parents=True)
        core.init_project(self.code)
        self.assertEqual(git(self.code, "rev-list", "--all", "--count"), "1")

    def test_an_occupied_folder_is_refused_before_any_mutation(self) -> None:
        self.code.mkdir(parents=True)
        (self.code / "notes.txt").write_text("à moi", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Dépôt existant"):
            core.init_project(self.code)
        self.assertEqual([p.name for p in self.code.iterdir()], ["notes.txt"])

    def test_a_repository_with_history_is_never_reinitialised(self) -> None:
        core.init_project(self.code)
        with self.assertRaisesRegex(ValueError, "Dépôt existant"):
            core.init_project(self.code)
        self.assertEqual(git(self.code, "rev-list", "--all", "--count"), "1")

    def test_a_repository_without_commit_is_completed_not_reinitialised(self) -> None:
        self.code.mkdir(parents=True)
        git(self.code, "init", "-q")
        marker = self.code / ".git" / "marqueur"
        marker.write_text("x", encoding="utf-8")
        core.init_project(self.code)
        self.assertTrue(marker.exists())
        self.assertEqual(git(self.code, "rev-list", "--all", "--count"), "1")

    def test_a_missing_identity_is_refused_and_nothing_is_created(self) -> None:
        with git_home(self.root / "vide", identity=None):
            with self.assertRaisesRegex(ValueError, "identité Git absente"):
                core.init_project(self.code)
            self.assertIsNone(core.git_identity(self.code))
        self.assertFalse(self.code.exists())

    def test_a_folder_inside_another_repository_is_refused(self) -> None:
        outer = self.root / "outer"
        outer.mkdir()
        git(outer, "init", "-q")
        with self.assertRaisesRegex(ValueError, "dépôt Git existant"):
            core.init_project(outer / "code")
        self.assertFalse((outer / "code").exists())

    def test_a_missing_git_is_named_before_any_mutation(self) -> None:
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaisesRegex(ValueError, "Git est introuvable"):
                core.init_project(self.code)
        self.assertFalse(self.code.exists())

    def test_a_failed_commit_restores_the_folder(self) -> None:
        real = core._git

        def failing(repo: Path, *args: str) -> str:
            if "commit" in args:
                raise ValueError("commit refusé")
            return real(repo, *args)

        with mock.patch.object(core, "_git", side_effect=failing):
            with self.assertRaisesRegex(ValueError, "commit refusé"):
                core.init_project(self.code)
        self.assertFalse(self.code.exists())
        self.code.mkdir(parents=True)
        with mock.patch.object(core, "_git", side_effect=failing):
            with self.assertRaises(ValueError):
                core.init_project(self.code)
        self.assertEqual(list(self.code.iterdir()), [])

    def test_only_the_recorded_initial_base_is_reused(self) -> None:
        oid, author = core.init_project(self.code)
        core.reuse_initial_base(self.code, oid, author)
        with self.assertRaisesRegex(ValueError, "Dépôt existant"):
            core.reuse_initial_base(self.code, oid, "Autre <autre@example.invalid>")
        stray = self.code / "intrus.txt"
        stray.write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "n'est plus le dépôt initial"):
            core.reuse_initial_base(self.code, oid, author)
        stray.unlink()
        git(self.code, "commit", "-q", "--allow-empty", "-m", "autre")
        with self.assertRaisesRegex(ValueError, "n'est plus le dépôt initial"):
            core.reuse_initial_base(self.code, oid, author)
        with self.assertRaisesRegex(ValueError, "n'est plus le dépôt initial"):
            core.reuse_initial_base(self.root / "absent", oid, author)

    def test_the_clone_receives_an_identity_only_when_it_has_none(self) -> None:
        source = self.root / "source"
        oid, _ = core.init_project(source)
        export = self.root / "export"
        export.mkdir()
        mandate = b"# Mandat\n"
        (export / "export.md").write_bytes(mandate)
        (export / "export.json").write_text(json.dumps({
            "schema_version": 1, "source_collaboration": "t", "request_sha256": "a",
            "document_sha256": "b", "review_sha256": "c", "decision_sha256": "d",
            "export_md_sha256": hashlib.sha256(mandate).hexdigest(),
        }), encoding="utf-8")
        with git_home(self.root / "ubuntu", identity=None):
            self.assertEqual(core.prepare(
                export, source, "HEAD", self.root / "run-1", validations=[["git", "--version"]],
                identity=("Nom Donné", "donne@example.invalid"),
            ), oid)
            self.assertEqual(git(self.root / "run-1" / "workspace", "config", "--local",
                                 "user.name"), "Nom Donné")
        self.assertEqual(git(self.root / "run-1" / "workspace", "rev-parse", "HEAD"), oid)
        core.prepare(export, source, "HEAD", self.root / "run-2", validations=[["git", "-v"]],
                     identity=("Autre", "autre@example.invalid"))
        with self.assertRaises(subprocess.CalledProcessError):
            git(self.root / "run-2" / "workspace", "config", "--local", "user.name")

    def test_the_cli_creates_the_project(self) -> None:
        self.assertEqual(cli.main(["init-project", str(self.code)]), 0)
        self.assertEqual(git(self.code, "rev-list", "--all", "--count"), "1")
        self.assertEqual(cli.main(["init-project", str(self.code)]), 1)


class PreflightTest(unittest.TestCase):
    def test_a_bare_executable_must_exist_on_the_path(self) -> None:
        core.preflight(Path("run"), [["git", "--version"]], "local")
        with self.assertRaisesRegex(ValueError, "introuvable"):
            core.preflight(Path("run"), [["outil-qui-nexiste-pas-4821", "--test"]], "local")

    def test_a_path_inside_the_clone_is_checked_at_collection(self) -> None:
        core.preflight(Path("run"), [["./scripts/test.sh"]], "local")

    def test_the_ubuntu_profile_needs_srt_claude_and_a_system_tool(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, system = root / "home", root / "usr"
            (home / "bin").mkdir(parents=True)
            system.mkdir()
            srt, claude = system / "srt", home / "claude"
            tool = system / "node"
            tool.write_text("#!/bin/sh\n", encoding="utf-8")
            personal = home / "bin" / "perso"
            personal.write_text("#!/bin/sh\n", encoding="utf-8")
            with mock.patch.object(core, "_require_linux_run"), \
                    mock.patch.object(core, "SRT", str(srt)), \
                    mock.patch.object(core, "_claude", return_value=claude), \
                    mock.patch.object(Path, "home", return_value=home.resolve()), \
                    mock.patch("shutil.which", side_effect=lambda n, path=None: (
                        str(tool) if n == "node" else str(personal) if n == "perso"
                        else "/usr/bin/git" if n == "git" else None)):
                with self.assertRaisesRegex(ValueError, "srt est absent"):
                    core.preflight(Path("/home/u/run"), [["node", "--test"]], "claude-wsl")
                srt.write_text("x", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Claude est absent"):
                    core.preflight(Path("/home/u/run"), [["node", "--test"]], "claude-wsl")
                claude.write_text("x", encoding="utf-8")
                core.preflight(Path("/home/u/run"), [["node", "--test"]], "claude-wsl")
                with self.assertRaisesRegex(ValueError, "dossier personnel"):
                    core.preflight(Path("/home/u/run"), [["perso"]], "claude-wsl")


class InspectRunTest(unittest.TestCase):
    def test_every_stage_is_read_from_the_artifacts_only(self) -> None:
        with TemporaryDirectory() as tmp, git_home(Path(tmp)):
            root = Path(tmp)
            self.assertEqual(core.inspect_run(root / "absent"), {"stage": "absent"})
            (root / "vide").mkdir()
            self.assertEqual(core.inspect_run(root / "vide")["stage"], "invalide")
            source = root / "source"
            core.init_project(source)
            export = root / "export"
            export.mkdir()
            (export / "export.md").write_bytes(b"# M\n")
            (export / "export.json").write_text(json.dumps({
                "schema_version": 1, "source_collaboration": "t", "request_sha256": "a",
                "document_sha256": "b", "review_sha256": "c", "decision_sha256": "d",
                "export_md_sha256": hashlib.sha256(b"# M\n").hexdigest(),
            }), encoding="utf-8")
            run = root / "run"
            core.prepare(export, source, "HEAD", run, validations=[["git", "--version"]])
            state = core.inspect_run(run)
            self.assertEqual((state["stage"], state["calls"], state["collects"]),
                             ("prepare", 0, 0))
            (run / "calls" / "call-0001").mkdir()
            state = core.inspect_run(run)
            self.assertEqual((state["stage"], state["last_call_complete"]), ("appel", False))
            (run / "calls" / "call-0001" / "resultat.json").write_text("{}", encoding="utf-8")
            self.assertTrue(core.inspect_run(run)["last_call_complete"])
            (run / "results" / "collect-0001").mkdir()
            self.assertEqual(core.inspect_run(run)["stage"], "validations")
            (run / "results" / "collect-0001" / "package").mkdir()
            self.assertEqual(core.inspect_run(run)["stage"], "validations",
                             "un dossier de paquet vide n'est pas un paquet prêt")
            self.assertTrue(core.inspect_run(run)["base_oid"])

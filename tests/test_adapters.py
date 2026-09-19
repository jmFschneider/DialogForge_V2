"""Tests des adaptateurs claude.py et codex.py — logique pure, sans lancer la
vraie CLI (`RULES.md` : aucun appel fournisseur dans la suite de tests).

`shutil.which` et `probe_version` sont substitués : ce qui est testé est la
forme de `command()`/`probe()`, pas la présence d'un outil sur la machine.
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from dataclasses import replace
from unittest import mock

from iabinome.adapters import claude, codex
from iabinome.adapters.base import CallSpec, ObservedCli, probe_version
from iabinome.models import ReviewerAccess, Role

_SPEC = CallSpec(
    prompt="peu importe", model="un-modele", timeout_seconds=30.0,
    work_root=mock.MagicMock(), reviewer_access=None,
)


class TestClaudeAdapter(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = claude.ClaudeAdapter()

    def test_default_model_differs_by_role(self) -> None:
        self.assertEqual(self.adapter.default_model(Role.A), "opus")
        self.assertEqual(self.adapter.default_model(Role.B), "fable")

    def test_command_has_no_prompt_in_argv(self) -> None:
        with mock.patch.object(shutil, "which", return_value="C:/bin/claude.EXE"):
            cmd = self.adapter.command(_SPEC)
        self.assertNotIn("peu importe", cmd)
        self.assertEqual(cmd[:4], ["C:/bin/claude.EXE", "-p", "--model", "un-modele"])

    def test_context_only_adds_empty_tools_flag(self) -> None:
        spec = replace(_SPEC, reviewer_access=ReviewerAccess.CONTEXT_ONLY)
        with mock.patch.object(shutil, "which", return_value="claude"):
            cmd = self.adapter.command(spec)
        self.assertIn("--tools", cmd)
        self.assertEqual(cmd[cmd.index("--tools") + 1], "")

    def test_consult_offers_read_tools_only(self) -> None:
        """2.2 : lire, chercher, lister — ni écrire ni exécuter — pour B en CONSULT
        comme pour A. Sans `--tools`, la CLI offrait tout son jeu d'outils."""
        for access in (ReviewerAccess.CONSULT, None):
            spec = replace(_SPEC, reviewer_access=access)
            with mock.patch.object(shutil, "which", return_value="claude"):
                cmd = self.adapter.command(spec)
            self.assertEqual(cmd[cmd.index("--tools") + 1], "Read,Grep,Glob")

    def test_every_role_is_restricted_and_starts_a_fresh_session(self) -> None:
        """2.2 : la séparation est dans l'argv, pour chaque rôle et chaque profil."""
        for access in (None, ReviewerAccess.CONSULT, ReviewerAccess.CONTEXT_ONLY):
            spec = replace(_SPEC, reviewer_access=access)
            with mock.patch.object(shutil, "which", return_value="claude"):
                cmd = self.adapter.command(spec)
            for flag in (
                "--restricted", "--strict-mcp-config", "--no-session-persistence",
                "--disable-slash-commands",
            ):
                self.assertIn(flag, cmd, access)
            for forbidden in ("--resume", "--continue", "-c", "-r", "--session-id"):
                self.assertNotIn(forbidden, cmd, access)

    def test_the_declared_capabilities_match_the_argv(self) -> None:
        self.assertTrue(self.adapter.capabilities.enforces_read_only)
        self.assertTrue(self.adapter.capabilities.fresh_session)

    def test_command_raises_when_executable_absent(self) -> None:
        with mock.patch.object(shutil, "which", return_value=None):
            with self.assertRaises(RuntimeError):
                self.adapter.command(_SPEC)

    def test_probe_absent_when_not_on_path(self) -> None:
        with mock.patch.object(shutil, "which", return_value=None):
            observed = self.adapter.probe()
        self.assertEqual(observed, ObservedCli(present=False, version=""))

    def test_probe_present_reports_a_version(self) -> None:
        with mock.patch.object(shutil, "which", return_value="claude"):
            with mock.patch.object(claude, "probe_version", return_value="2.1.259 (Claude Code)"):
                observed = self.adapter.probe()
        self.assertEqual(observed, ObservedCli(present=True, version="2.1.259 (Claude Code)"))

    def test_extract_reads_stdout_only(self) -> None:
        self.assertEqual(
            self.adapter.extract(b"IABINOME:DOCUMENT\ncorps", b"bruit sur stderr"),
            "IABINOME:DOCUMENT\ncorps",
        )


class TestCodexAdapter(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = codex.CodexAdapter()

    def test_default_model_is_the_same_for_both_roles(self) -> None:
        self.assertEqual(self.adapter.default_model(Role.A), self.adapter.default_model(Role.B))

    def test_command_reads_the_prompt_from_stdin(self) -> None:
        with mock.patch.object(shutil, "which", return_value="C:/bin/codex.CMD"):
            cmd = self.adapter.command(_SPEC)
        self.assertEqual(cmd[0], "C:/bin/codex.CMD")
        self.assertEqual(cmd[1], "exec")
        self.assertEqual(cmd[-1], "-")
        self.assertNotIn("peu importe", cmd)

    def test_context_only_disables_the_shell_tool(self) -> None:
        spec = replace(_SPEC, reviewer_access=ReviewerAccess.CONTEXT_ONLY)
        with mock.patch.object(shutil, "which", return_value="codex"):
            cmd = self.adapter.command(spec)
        self.assertIn("-c", cmd)
        self.assertEqual(cmd[cmd.index("-c") + 1], "features.shell_tool=false")

    def test_every_role_is_read_only_ephemeral_and_ignores_user_config(self) -> None:
        """2.2, côté Codex : le même résultat par d'autres moyens."""
        for access in (None, ReviewerAccess.CONSULT, ReviewerAccess.CONTEXT_ONLY):
            spec = replace(_SPEC, reviewer_access=access)
            with mock.patch.object(shutil, "which", return_value="codex"):
                cmd = self.adapter.command(spec)
            self.assertEqual(cmd[cmd.index("--sandbox") + 1], "read-only", access)
            for flag in ("--ephemeral", "--ignore-user-config", "--ignore-rules"):
                self.assertIn(flag, cmd, access)
            for forbidden in ("resume", "--last", "danger-full-access", "workspace-write"):
                self.assertNotIn(forbidden, cmd, access)
        self.assertTrue(self.adapter.capabilities.enforces_read_only)
        self.assertTrue(self.adapter.capabilities.fresh_session)

    def test_consult_omits_the_disable_flag(self) -> None:
        spec = replace(_SPEC, reviewer_access=ReviewerAccess.CONSULT)
        with mock.patch.object(shutil, "which", return_value="codex"):
            cmd = self.adapter.command(spec)
        self.assertNotIn("-c", cmd)

    def test_command_raises_when_executable_absent(self) -> None:
        with mock.patch.object(shutil, "which", return_value=None):
            with self.assertRaises(RuntimeError):
                self.adapter.command(_SPEC)

    def test_probe_absent_when_not_on_path(self) -> None:
        with mock.patch.object(shutil, "which", return_value=None):
            observed = self.adapter.probe()
        self.assertEqual(observed, ObservedCli(present=False, version=""))

    def test_extract_reads_stdout_only(self) -> None:
        self.assertEqual(
            self.adapter.extract(b"IABINOME:DOCUMENT\ncorps", b"8315 octets de banniere"),
            "IABINOME:DOCUMENT\ncorps",
        )


class TestProbeVersion(unittest.TestCase):
    def test_a_found_executable_that_fails_to_report_a_version_stays_present(self) -> None:
        """`probe_version` échoue au mieux : `probe().present` vient de
        `shutil.which()` seul, jamais de la réussite du bandeau de version."""
        with mock.patch.object(
            subprocess, "run", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=5.0)
        ):
            self.assertEqual(probe_version("un-executable"), "")

    def test_an_os_error_also_yields_an_empty_version(self) -> None:
        with mock.patch.object(subprocess, "run", side_effect=OSError("introuvable")):
            self.assertEqual(probe_version("un-executable"), "")


if __name__ == "__main__":
    unittest.main()

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
from iabinome.models import AgentPurpose, ReviewerAccess

_SPEC = CallSpec(
    prompt="peu importe", model="un-modele", timeout_seconds=30.0,
    work_root=mock.MagicMock(), reviewer_access=None,
)


class TestClaudeAdapter(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = claude.ClaudeAdapter()

    def test_default_model_differs_by_role(self) -> None:
        self.assertEqual(self.adapter.default_model(AgentPurpose.A), "opus")
        self.assertEqual(self.adapter.default_model(AgentPurpose.B), "fable")

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

    def test_by_default_the_tools_are_read_only_and_there_is_no_web(self) -> None:
        """2.2 : lire, chercher, lister — ni écrire ni exécuter — pour B en CONSULT comme pour A ;
        sans `--tools`, la CLI offrait tout son jeu d'outils. 3.1 (décision du PO, 2026-09-19) :
        **le web est fermé par défaut**, et rien d'autorisé d'avance."""
        for access in (ReviewerAccess.CONSULT, None):
            spec = replace(_SPEC, reviewer_access=access)
            with mock.patch.object(shutil, "which", return_value="claude"):
                cmd = self.adapter.command(spec)
            self.assertEqual(cmd[cmd.index("--tools") + 1], "Read,Grep,Glob")
            self.assertNotIn("--allowedTools", cmd)
            for web in ("WebSearch", "WebFetch"):
                self.assertNotIn(web, " ".join(cmd))

    def test_with_web_access_the_two_web_tools_are_added_and_pre_authorized(self) -> None:
        """Recherche et lecture d'une page — jamais un outil qui écrit ou exécute. Autorisés
        d'avance : sans personne pour approuver, l'appel non interactif les refuserait."""
        for access in (ReviewerAccess.CONSULT, None):
            spec = replace(_SPEC, reviewer_access=access, web_access=True)
            with mock.patch.object(shutil, "which", return_value="claude"):
                cmd = self.adapter.command(spec)
            tools = cmd[cmd.index("--tools") + 1]
            self.assertEqual(tools.split(","), ["Read", "Grep", "Glob", "WebSearch", "WebFetch"])
            for forbidden in ("Bash", "PowerShell", "Edit", "Write", "NotebookEdit"):
                self.assertNotIn(forbidden, tools)
            self.assertEqual(cmd[cmd.index("--allowedTools") + 1], "WebSearch,WebFetch")

    def test_context_only_has_no_tool_at_all_even_when_the_web_is_open(self) -> None:
        for web in (False, True):
            spec = replace(_SPEC, reviewer_access=ReviewerAccess.CONTEXT_ONLY, web_access=web)
            with mock.patch.object(shutil, "which", return_value="claude"):
                cmd = self.adapter.command(spec)
            self.assertEqual(cmd[cmd.index("--tools") + 1], "")
            self.assertNotIn("--allowedTools", cmd)

    def test_effort_levels_are_claude_s_own(self) -> None:
        self.assertEqual(
            self.adapter.capabilities.effort_levels, ("low", "medium", "high", "xhigh", "max")
        )
        self.assertTrue(self.adapter.capabilities.controls_web_access)

    def test_effort_is_passed_only_when_asked(self) -> None:
        with mock.patch.object(shutil, "which", return_value="claude"):
            self.assertNotIn("--effort", self.adapter.command(_SPEC))
            cmd = self.adapter.command(replace(_SPEC, effort="high"))
        self.assertEqual(cmd[cmd.index("--effort") + 1], "high")

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
        self.assertEqual(
            self.adapter.default_model(AgentPurpose.A), self.adapter.default_model(AgentPurpose.B)
        )

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
            with mock.patch("iabinome.adapters.codex.sys.platform", "win32"):
                cmd = self.adapter.command(spec)
        self.assertIn("-c", cmd)
        self.assertIn("features.shell_tool=false", self.values_of_c(cmd))

    def test_windows_uses_the_native_elevated_sandbox_backend(self) -> None:
        with mock.patch.object(shutil, "which", return_value="codex"):
            with mock.patch("iabinome.adapters.codex.sys.platform", "win32"):
                cmd = self.adapter.command(_SPEC)
        self.assertIn("windows.sandbox=elevated", self.values_of_c(cmd))

    def test_other_platforms_do_not_receive_a_windows_sandbox_setting(self) -> None:
        with mock.patch.object(shutil, "which", return_value="codex"):
            with mock.patch("iabinome.adapters.codex.sys.platform", "linux"):
                cmd = self.adapter.command(_SPEC)
        self.assertNotIn("windows.sandbox=elevated", self.values_of_c(cmd))

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

    def values_of_c(self, cmd: list[str]) -> list[str]:
        return [cmd[i + 1] for i, part in enumerate(cmd) if part == "-c"]

    def test_the_web_policy_is_always_explicit_and_closed_by_default(self) -> None:
        """Décision du PO (2026-09-19) : jamais laissée au réglage de l'outil, dans aucun sens.
        Constaté avant : Codex cherchait sur le web sous `--sandbox read-only`."""
        for access in (None, ReviewerAccess.CONSULT, ReviewerAccess.CONTEXT_ONLY):
            spec = replace(_SPEC, reviewer_access=access)
            with mock.patch.object(shutil, "which", return_value="codex"):
                cmd = self.adapter.command(spec)
            self.assertIn("web_search=disabled", self.values_of_c(cmd), access)
            self.assertNotIn("web_search=live", self.values_of_c(cmd), access)

    def test_with_web_access_it_is_live_for_both_roles_but_never_in_context_only(self) -> None:
        for access in (None, ReviewerAccess.CONSULT):
            spec = replace(_SPEC, reviewer_access=access, web_access=True)
            with mock.patch.object(shutil, "which", return_value="codex"):
                cmd = self.adapter.command(spec)
            self.assertIn("web_search=live", self.values_of_c(cmd), access)
            self.assertNotIn("web_search=disabled", self.values_of_c(cmd), access)
        spec = replace(_SPEC, reviewer_access=ReviewerAccess.CONTEXT_ONLY, web_access=True)
        with mock.patch.object(shutil, "which", return_value="codex"):
            cmd = self.adapter.command(spec)
        self.assertIn("web_search=disabled", self.values_of_c(cmd))
        self.assertNotIn("web_search=live", self.values_of_c(cmd))

    def test_effort_is_passed_only_when_asked_and_without_quotes(self) -> None:
        """Sans réglage, rien : `--ignore-user-config` fait alors tourner Codex à `none`, et le PO
        a choisi de ne pas y toucher (2026-09-19). Posé, la valeur passe par `-c`, **sans
        guillemets** — le lanceur `.CMD` les abîmerait, et Codex lit une chaîne littérale."""
        with mock.patch.object(shutil, "which", return_value="codex"):
            plain = self.adapter.command(_SPEC)
            cmd = self.adapter.command(replace(_SPEC, effort="medium"))
        self.assertFalse(any("reasoning" in part for part in plain))
        self.assertIn("model_reasoning_effort=medium", self.values_of_c(cmd))
        self.assertEqual(cmd[-1], "-")

    def test_every_setting_reaches_the_command_in_a_fixed_order(self) -> None:
        spec = replace(
            _SPEC, reviewer_access=ReviewerAccess.CONTEXT_ONLY, effort="low", web_access=True
        )
        with mock.patch.object(shutil, "which", return_value="codex"):
            with mock.patch("iabinome.adapters.codex.sys.platform", "win32"):
                cmd = self.adapter.command(spec)
        self.assertEqual(self.values_of_c(cmd), [
            "windows.sandbox=elevated", "features.shell_tool=false", "web_search=disabled",
            "model_reasoning_effort=low",
        ])

    def test_effort_levels_are_codex_s_own(self) -> None:
        self.assertEqual(
            self.adapter.capabilities.effort_levels, ("minimal", "low", "medium", "high", "xhigh")
        )
        self.assertNotIn("max", self.adapter.capabilities.effort_levels)
        self.assertTrue(self.adapter.capabilities.controls_web_access)

    def test_consult_does_not_disable_the_shell_tool(self) -> None:
        spec = replace(_SPEC, reviewer_access=ReviewerAccess.CONSULT)
        with mock.patch.object(shutil, "which", return_value="codex"):
            cmd = self.adapter.command(spec)
        self.assertNotIn("features.shell_tool=false", self.values_of_c(cmd))

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

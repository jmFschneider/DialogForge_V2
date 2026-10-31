"""Tests des adaptateurs claude.py et codex.py — logique pure, sans lancer la
vraie CLI (`RULES.md` : aucun appel fournisseur dans la suite de tests).

`shutil.which` et `probe_version` sont substitués : ce qui est testé est la
forme de `command()`/`probe()`, pas la présence d'un outil sur la machine.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from iabinome.adapters import claude, codex
from iabinome.adapters.base import CallSpec, FramingSessionSpec, ObservedCli, probe_version
from iabinome.models import AgentPurpose, ReviewerAccess

_SPEC = CallSpec(
    prompt="peu importe", model="un-modele", timeout_seconds=30.0,
    work_root=mock.MagicMock(), reviewer_access=None,
)
_FRAMING = FramingSessionSpec(model="un-modele", timeout_seconds=30.0, work_root=mock.MagicMock())
# Formes relevées par le PO le 2026-09-25 (`reference/PROTOCOLE_CADRAGE_LOT4.md`) : champs
# utiles recopiés tels quels, identifiants remplacés.
_CLAUDE_OUT = (
    b'{"stop_reason":"end_turn","session_id":"8ce4-sess","permission_denials":[],'
    b'"is_error":false,"num_turns":2,"subtype":"success","result":"OK, SAULE-2291",'
    b'"type":"result"}'
)
_CODEX_OUT = "\n".join([
    '{"type":"thread.started","thread_id":"01a0-sess"}',
    '{"type":"turn.started"}',
    '{"type":"item.completed","item":{"id":"item_0","type":"agent_message",'
    '"text":"Je vérifie le fichier demandé en lecture seule et ne modifierai rien."}}',
    '{"type":"item.started","item":{"id":"item_1","type":"command_execution",'
    '"command":"Get-Content","aggregated_output":"","exit_code":null,"status":"in_progress"}}',
    '{"type":"item.completed","item":{"id":"item_1","type":"command_execution",'
    '"command":"Get-Content","aggregated_output":"SAULE-2291\\r\\n","exit_code":0,'
    '"status":"completed"}}',
    '{"type":"item.completed","item":{"id":"item_2","type":"agent_message",'
    '"text":"OK, SAULE-2291"}}',
    '{"type":"turn.completed","usage":{"input_tokens":22426,"output_tokens":134}}',
    "",
]).encode("utf-8")


class TestClaudeAdapter(unittest.TestCase):
    def test_live_project_is_added_for_read_tools_only(self) -> None:
        project = Path("C:/projects/example")
        with mock.patch.object(shutil, "which", return_value="claude"):
            consult = self.adapter.command(replace(_SPEC, project_root=project))
            context = self.adapter.command(replace(
                _SPEC, project_root=project, reviewer_access=ReviewerAccess.CONTEXT_ONLY,
            ))
            framing = self.adapter.framing_command(
                replace(_FRAMING, project_root=project), None, "prompt",
            )
        self.assertEqual(consult[consult.index("--add-dir") + 1], str(project))
        self.assertNotIn("--add-dir", context)
        self.assertEqual(framing[framing.index("--add-dir") + 1], str(project))

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
        """2.2 : la séparation est dans l'argv, pour chaque rôle et chaque profil. La
        session neuve est conservée sous l'identifiant imposé (REPRISE_QUOTA_V3.md)."""
        for access in (None, ReviewerAccess.CONSULT, ReviewerAccess.CONTEXT_ONLY):
            spec = replace(_SPEC, reviewer_access=access, session_id="11-sess")
            with mock.patch.object(shutil, "which", return_value="claude"):
                cmd = self.adapter.command(spec)
            for flag in ("--restricted", "--strict-mcp-config", "--disable-slash-commands"):
                self.assertIn(flag, cmd, access)
            self.assertEqual(cmd[cmd.index("--session-id") + 1], "11-sess", access)
            for forbidden in ("--resume", "--continue", "-c", "-r", "--no-session-persistence"):
                self.assertNotIn(forbidden, cmd, access)

    def test_a_continuation_resumes_the_interrupted_session_only(self) -> None:
        spec = replace(_SPEC, session_id="11-sess", resume=True)
        with mock.patch.object(shutil, "which", return_value="claude"):
            cmd = self.adapter.command(spec)
            plain = self.adapter.command(_SPEC)
        self.assertEqual(cmd[cmd.index("--resume") + 1], "11-sess")
        self.assertNotIn("--session-id", cmd)
        self.assertNotIn("--output-format", cmd)  # même sortie texte que l'appel refusé
        for flag in ("--resume", "--session-id"):
            self.assertNotIn(flag, plain)

    def test_the_observed_session_limit_is_recognized_with_its_hour(self) -> None:
        """Trace réelle V2 du 2026-10-01 : le message seul sur `stdout`, code 1."""
        observed = "You've hit your session limit · resets 8:50pm (Europe/Paris)\n"
        self.assertEqual(
            self.adapter.quota_reset(observed.encode("utf-8"), b""), "8:50pm (Europe/Paris)"
        )
        dashed = b"You've hit your session limit - resets 11:20pm (Europe/Paris)"
        self.assertEqual(self.adapter.quota_reset(dashed, b""), "11:20pm (Europe/Paris)")
        framed = json.dumps({"is_error": True, "result": observed.strip()}).encode("utf-8")
        self.assertEqual(self.adapter.quota_reset(framed, b""), "8:50pm (Europe/Paris)")

    def test_anything_else_is_not_a_quota(self) -> None:
        """Ni 429, ni mots-clés, ni réponse normale qui parle de limite (le prédécesseur
        prenait « credit balance » pour un quota)."""
        for other in (
            b"",
            b"API Error: 429 rate_limit_error",
            b"Credit balance is too low",
            b"Claude AI usage limit reached|1753290000",
            "IABINOME:DOCUMENT\nYou've hit your session limit · resets 8:50pm".encode(),
            b'{"is_error": true, "api_error_status": 429}',
            b"{pas du json",
        ):
            with self.subTest(other):
                self.assertIsNone(self.adapter.quota_reset(other, b""))

    def test_the_session_is_the_imposed_one_unless_json_declares_it(self) -> None:
        self.assertEqual(self.adapter.session_of("11-sess", b"texte", b""), "11-sess")
        self.assertEqual(self.adapter.session_of("11-sess", _CLAUDE_OUT, b""), "8ce4-sess")
        self.assertIsNone(self.adapter.session_of(None, b"texte", b""))

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

    def test_framing_keeps_the_session_and_resumes_it_by_its_identifier(self) -> None:
        """Lot 4 : les arguments de A et B, sans `--no-session-persistence`, avec la sortie
        JSON qui porte l'identifiant, puis `--resume` aux tours suivants."""
        with mock.patch.object(shutil, "which", return_value="claude"):
            first = self.adapter.framing_command(_FRAMING, None, "peu importe")
            then = self.adapter.framing_command(
                replace(_FRAMING, effort="high"), "8ce4-sess", "peu importe"
            )
        self.assertEqual(first[1:], [
            "-p", "--model", "un-modele", "--restricted", "--strict-mcp-config",
            "--disable-slash-commands", "--tools", "Read,Grep,Glob", "--output-format", "json",
        ])
        self.assertEqual(then[len(first):], ["--resume", "8ce4-sess", "--effort", "high"])
        with mock.patch.object(shutil, "which", return_value="claude"):
            imposed = self.adapter.framing_command(
                replace(_FRAMING, session_id="11-sess"), None, "peu importe"
            )
            resumed = self.adapter.framing_command(
                replace(_FRAMING, session_id="11-sess"), "8ce4-sess", "peu importe"
            )
        self.assertEqual(imposed[len(first):], ["--session-id", "11-sess"])
        self.assertNotIn("--session-id", resumed)
        for cmd in (first, then):
            self.assertNotIn("--no-session-persistence", cmd)
            self.assertNotIn("peu importe", cmd)
        self.assertTrue(self.adapter.capabilities.supports_persistent_framing_session)

    def test_framing_extract_reads_the_result_and_the_session(self) -> None:
        self.assertEqual(
            self.adapter.framing_extract(_CLAUDE_OUT, b""), ("OK, SAULE-2291", "8ce4-sess")
        )
        no_session = _CLAUDE_OUT.replace(b'"session_id":"8ce4-sess",', b"")
        self.assertIsNone(self.adapter.framing_extract(no_session, b"")[1])

    def test_framing_extract_refuses_what_is_not_an_answer(self) -> None:
        """`DECODE_FAILED` côté cadrage : jamais une sortie sans réponse prise pour un tour."""
        for bad in (
            b"texte libre", b"[]", b'{"session_id":"s"}',
            _CLAUDE_OUT.replace(b'"is_error":false', b'"is_error":true'),
        ):
            with self.subTest(bad), self.assertRaises(ValueError):
                self.adapter.framing_extract(bad, b"")


class TestCodexAdapter(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = codex.CodexAdapter()

    def test_live_project_is_the_working_directory_without_a_corpus(self) -> None:
        project = Path("C:/projects/example")
        with mock.patch.object(shutil, "which", return_value="codex"):
            call = self.adapter.command(replace(_SPEC, project_root=project))
            with_corpus = self.adapter.command(replace(
                _SPEC, project_root=project, corpus_present=True,
            ))
            context = self.adapter.command(replace(
                _SPEC, project_root=project, reviewer_access=ReviewerAccess.CONTEXT_ONLY,
            ))
            framing = self.adapter.framing_command(
                replace(_FRAMING, project_root=project), None, "prompt",
            )
        self.assertEqual(call[1:4], ["--cd", str(project), "exec"])
        self.assertIn("read-only", call)
        self.assertNotIn("--cd", with_corpus)
        self.assertNotIn("--cd", context)
        self.assertEqual(framing[1:4], ["--cd", str(project), "exec"])

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

    def test_every_role_is_read_only_and_ignores_user_config(self) -> None:
        """2.2, côté Codex : le même résultat par d'autres moyens. Sans `--ephemeral`
        depuis le 2026-10-05 : la session est conservée pour la seule continuation."""
        for access in (None, ReviewerAccess.CONSULT, ReviewerAccess.CONTEXT_ONLY):
            spec = replace(_SPEC, reviewer_access=access, session_id="ignore")
            with mock.patch.object(shutil, "which", return_value="codex"):
                cmd = self.adapter.command(spec)
            self.assertEqual(cmd[cmd.index("--sandbox") + 1], "read-only", access)
            for flag in ("--ignore-user-config", "--ignore-rules"):
                self.assertIn(flag, cmd, access)
            for forbidden in (
                "resume", "--last", "danger-full-access", "workspace-write", "--ephemeral",
                "ignore",
            ):
                self.assertNotIn(forbidden, cmd, access)
        self.assertTrue(self.adapter.capabilities.enforces_read_only)
        self.assertTrue(self.adapter.capabilities.fresh_session)

    def test_a_continuation_resumes_the_session_read_only(self) -> None:
        """`exec resume` refuse `--sandbox` : la lecture seule passe par `sandbox_mode`,
        comme pour F ; l'identifiant précède le `-` du prompt."""
        spec = replace(
            _SPEC, reviewer_access=ReviewerAccess.CONTEXT_ONLY, session_id="01a0-sess",
            resume=True,
        )
        with mock.patch.object(shutil, "which", return_value="codex"):
            cmd = self.adapter.command(spec)
            with self.assertRaises(RuntimeError):
                self.adapter.command(replace(spec, session_id=None))
        self.assertEqual(cmd[1:3], ["exec", "resume"])
        self.assertEqual(cmd[-2:], ["01a0-sess", "-"])
        self.assertNotIn("--sandbox", cmd)
        values = self.values_of_c(cmd)
        for setting in (
            "sandbox_mode=read-only", "features.shell_tool=false", "web_search=disabled",
        ):
            self.assertIn(setting, values)

    def test_the_observed_usage_refusal_is_recognized_only_at_the_end(self) -> None:
        refusal = (
            "ERROR: You’ve hit your usage limit. Upgrade to Pro "
            "(https://chatgpt.com/explore/pro), visit https://chatgpt.com/settings/usage "
            "to purchase more credits or try again at Oct 31st, 2026 1:31 AM."
        ).encode()
        banner = b"session id: 01a0-sess\n--------\n"
        self.assertEqual(self.adapter.quota_reset(b"", banner + refusal + b"\n" + refusal),
                         "1:31 AM")
        self.assertIsNone(self.adapter.quota_reset(b"answer", banner + refusal))
        self.assertIsNone(self.adapter.quota_reset(b"", banner + refusal + b"\nother error"))
        self.assertIsNone(self.adapter.quota_reset(
            b"", b"You've hit your usage limit. Try again at 4:10 PM."
        ))

    def test_the_session_is_read_in_the_banner_or_the_json_events(self) -> None:
        """Bannière relevée sur une trace réelle (0.159.3), identifiant remplacé."""
        banner = (
            b"OpenAI Codex v0.159.3\n--------\nworkdir: C:\\tmp\n"
            b"session id: 019a-sess\n--------\n"
        )
        self.assertEqual(self.adapter.session_of("ignore", b"", banner), "019a-sess")
        self.assertEqual(self.adapter.session_of("ignore", _CODEX_OUT, b""), "01a0-sess")
        self.assertIsNone(self.adapter.session_of("ignore", b"texte", b"bruit"))

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

    def test_framing_opens_then_resumes_with_the_measured_arguments(self) -> None:
        """Lot 4 : sans `--ephemeral`, avec `--json` ; en reprise, `resume` n'accepte pas
        `--sandbox`, la lecture seule passe par `-c sandbox_mode=read-only`. L'ordre est
        celui du protocole mesuré, identifiant et `-` en dernier."""
        with mock.patch.object(shutil, "which", return_value="codex"):
            with mock.patch("iabinome.adapters.codex.sys.platform", "win32"):
                first = self.adapter.framing_command(_FRAMING, None, "peu importe")
                then = self.adapter.framing_command(
                    replace(_FRAMING, effort="low"), "01a0-sess", "peu importe"
                )
        common = [
            "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules", "--json",
            "-c", "windows.sandbox=elevated", "-c", "web_search=disabled",
        ]
        self.assertEqual(
            first[1:], ["exec", "-m", "un-modele", "--sandbox", "read-only", *common, "-"]
        )
        self.assertEqual(then[1:], [
            "exec", "resume", "-m", "un-modele", "-c", "sandbox_mode=read-only", *common,
            "-c", "model_reasoning_effort=low", "01a0-sess", "-",
        ])
        for cmd in (first, then):
            self.assertNotIn("--ephemeral", cmd)
            self.assertNotIn("peu importe", cmd)
        self.assertTrue(self.adapter.capabilities.supports_persistent_framing_session)

    def test_framing_extract_keeps_the_last_agent_message_only(self) -> None:
        """Le premier message annonce ce que l'agent va faire ; seul le dernier répond —
        et `IABINOME:DEMANDE` ne tolère aucun texte avant sa balise."""
        self.assertEqual(
            self.adapter.framing_extract(_CODEX_OUT, b"bruit"), ("OK, SAULE-2291", "01a0-sess")
        )
        no_thread = b"\n".join(_CODEX_OUT.splitlines()[1:])
        self.assertIsNone(self.adapter.framing_extract(no_thread, b"")[1])

    def test_framing_extract_refuses_an_unfinished_or_unreadable_turn(self) -> None:
        unfinished = _CODEX_OUT.replace(b'"type":"turn.completed"', b'"type":"turn.failed"')
        silent = b'{"type":"thread.started","thread_id":"s"}\n{"type":"turn.completed"}\n'
        for bad in (unfinished, silent, _CODEX_OUT + b"pas du JSON\n", b"[1]\n"):
            with self.subTest(bad[-30:]), self.assertRaises(ValueError):
                self.adapter.framing_extract(bad, b"")


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

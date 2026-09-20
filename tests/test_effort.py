"""Le réglage d'effort de raisonnement, facultatif (lot 3, point 3.1).

Décision du PO, 2026-09-19 : **ne rien changer par défaut** — Codex tourne à `none` sous
`--ignore-user-config` —, mais **pouvoir poser ce réglage** dans le fichier de configuration
plus tard. D'où ces garanties : sans réglage, rien ne change, pas même un octet de
`configuration.json` ; avec, il arrive jusqu'à l'argv de l'outil ; un outil qui ne le supporte
pas est refusé avant tout appel.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from iabinome import cli, workflow
from iabinome.adapters.claude import ClaudeAdapter
from iabinome.adapters.codex import CodexAdapter
from iabinome.models import AgentSpec, Configuration, SchemaError
from tests import fakes
from tests.test_cli import CliCase
from tests.test_workflow import WorkflowCase

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."


class TestAgentSpec(WorkflowCase):
    def test_without_effort_the_file_is_what_it_was_before(self) -> None:
        self.assertEqual(
            AgentSpec("codex", "m").to_dict(), {"adapter_id": "codex", "model": "m"}
        )

    def test_with_effort_the_key_is_written_and_read_back(self) -> None:
        spec = AgentSpec("codex", "m", "medium")
        self.assertEqual(spec.to_dict()["effort"], "medium")
        self.assertEqual(AgentSpec.from_dict(spec.to_dict()), spec)

    def test_a_configuration_written_before_the_setting_still_loads(self) -> None:
        """Les dossiers d'essai du 3.1 n'ont pas la clé : ils doivent rester lisibles."""
        collab = fakes.collaboration(self.root)
        config = Configuration.from_dict(fakes.read_json(collab / "configuration.json"))
        self.assertIsNone(config.agent_a.effort)
        self.assertIsNone(config.agent_b.effort)

    def test_a_shape_that_could_carry_more_than_a_word_is_refused(self) -> None:
        """La valeur finit dans un argument de ligne de commande : pas d'espace, de guillemet,
        de `=` ni de retour à la ligne."""
        for bad in ("", "high value", 'a"b', "x=y", "a\nb", "-c evil", "é"):
            with self.assertRaises(SchemaError, msg=repr(bad)):
                AgentSpec("codex", "m", bad)

    def test_a_null_or_non_string_effort_in_the_file_is_refused(self) -> None:
        for bad in (None, 3, ["high"]):
            with self.assertRaises(SchemaError, msg=repr(bad)):
                AgentSpec.from_dict({"adapter_id": "codex", "model": "m", "effort": bad})

    def test_an_unknown_key_is_still_refused(self) -> None:
        with self.assertRaises(SchemaError):
            AgentSpec.from_dict({"adapter_id": "codex", "model": "m", "vitesse": "x"})


class TestNewAcceptsIt(CliCase):
    def created(self) -> Configuration:
        return Configuration.from_dict(fakes.read_json(self.collab / "configuration.json"))

    def test_without_the_option_nothing_is_recorded(self) -> None:
        self.assertEqual(cli.main(["new", *self.new_args()]), 0)
        config = fakes.read_json(self.collab / "configuration.json")
        self.assertNotIn("effort", config["agent_a"])
        self.assertNotIn("effort", config["agent_b"])

    def test_the_flags_set_each_role_separately(self) -> None:
        argv = ["new", *self.new_args(**{"--effort-a": "high", "--effort-b": "low"})]
        self.assertEqual(cli.main(argv), 0)
        self.assertEqual(self.created().agent_a.effort, "high")
        self.assertEqual(self.created().agent_b.effort, "low")

    def test_the_configuration_file_can_set_it(self) -> None:
        toml = self.root / "iabinome.toml"
        toml.write_text('effort_a = "medium"\n', encoding="utf-8")
        with redirect_stderr(io.StringIO()) as err:
            self.assertEqual(cli.main(["new", *self.new_args(), "--config", str(toml)]), 0)
        self.assertEqual(self.created().agent_a.effort, "medium")
        self.assertIsNone(self.created().agent_b.effort)
        self.assertIn("effort_a", err.getvalue())  # le programme dit ce qu'il a pris du fichier

    def test_a_flag_wins_over_the_file(self) -> None:
        toml = self.root / "iabinome.toml"
        toml.write_text('effort_a = "medium"\n', encoding="utf-8")
        argv = ["new", *self.new_args(**{"--effort-a": "high"}), "--config", str(toml)]
        with redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(argv), 0)
        self.assertEqual(self.created().agent_a.effort, "high")

    def test_a_level_the_adapter_does_not_know_is_refused_at_new(self) -> None:
        """Le faux adaptateur accepte `low`, `medium`, `high` : `xhigh` est refusé à la création,
        pas à la première exécution."""
        argv = ["new", *self.new_args(**{"--effort-b": "xhigh"})]
        with redirect_stderr(io.StringIO()) as err, redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(argv), 1)
        self.assertIn("effort B", err.getvalue())
        self.assertIn("low, medium, high", err.getvalue())
        self.assertFalse(self.collab.exists())

    def test_an_unusable_value_is_refused_before_anything_is_created(self) -> None:
        argv = ["new", *self.new_args(**{"--effort-a": 'high"'})]
        with redirect_stderr(io.StringIO()) as err, redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(argv), 1)
        self.assertIn("effort", err.getvalue())
        self.assertFalse(self.collab.exists())


class TestTheLevelsBelongToTheAdapter(WorkflowCase):
    """3.1 : le vocabulaire est celui de la CLI — Claude `low…max`, Codex `minimal…xhigh` — et une
    valeur incompatible est refusée **avant tout appel** : ni mutation, ni quota."""

    def refuses(self, adapter_id: str, effort: str) -> None:
        levels = ClaudeAdapter().capabilities.effort_levels if adapter_id == "claude" else (
            CodexAdapter().capabilities.effort_levels
        )
        collab = fakes.collaboration(self.root / f"{adapter_id}-{effort}")
        config = fakes.read_json(collab / "configuration.json")
        config["agent_a"]["effort"] = effort
        fakes.write_json(collab / "configuration.json", config)
        a = fakes.FakeAdapter("fake-a", (_DOC,), effort_levels=levels)
        b = fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),))
        self.adapters = {"fake-a": a, "fake-b": b}
        before = (collab / "etat.json").read_bytes()
        with self.assertRaisesRegex(workflow.WorkflowError, "refusé — attendu"):
            self.run_engine(collab)
        self.assertEqual((a.calls, b.calls), (0, 0))
        self.assertEqual((collab / "etat.json").read_bytes(), before)
        self.assertFalse((collab / "appels").exists())

    def test_the_two_vocabularies_are_not_the_same(self) -> None:
        claude, codex = ClaudeAdapter().capabilities, CodexAdapter().capabilities
        self.assertEqual(set(claude.effort_levels) - set(codex.effort_levels), {"max"})
        self.assertEqual(set(codex.effort_levels) - set(claude.effort_levels), {"minimal"})

    def test_claude_refuses_a_codex_only_level_before_any_call(self) -> None:
        self.refuses("claude", "minimal")

    def test_codex_refuses_a_claude_only_level_before_any_call(self) -> None:
        self.refuses("codex", "max")

    def test_neither_accepts_none_or_a_typo(self) -> None:
        for adapter_id in ("claude", "codex"):
            for bad in ("none", "hgih", "HIGH"):
                with self.subTest(adapter=adapter_id, effort=bad):
                    self.refuses(adapter_id, bad)


class TestTheEngineUsesIt(WorkflowCase):
    def with_effort(self, effort_a: str | None, effort_b: str | None) -> Path:
        collab = self.build(a=(_DOC,), b=(fakes.review("ACCEPTER"),))
        config = fakes.read_json(collab / "configuration.json")
        for key, effort in (("agent_a", effort_a), ("agent_b", effort_b)):
            if effort is not None:
                config[key]["effort"] = effort
        fakes.write_json(collab / "configuration.json", config)
        return collab

    def test_the_setting_reaches_each_role_call(self) -> None:
        collab = self.with_effort("high", "low")
        self.run_engine(collab)
        self.assertEqual(self.a.efforts, ["high"])
        self.assertEqual(self.b.efforts, ["low"])

    def test_without_the_setting_nothing_is_asked(self) -> None:
        collab = self.with_effort(None, None)
        self.run_engine(collab)
        self.assertEqual(self.a.efforts + self.b.efforts, [None, None])

    def test_an_adapter_that_cannot_take_it_is_refused_before_any_call(self) -> None:
        collab = self.with_effort("high", None)
        self.a = fakes.FakeAdapter("fake-a", (_DOC,), effort_levels=())
        self.adapters = {"fake-a": self.a, "fake-b": self.b}
        before = (collab / "etat.json").read_bytes()
        with self.assertRaisesRegex(workflow.WorkflowError, "non supporté"):
            self.run_engine(collab)
        self.assertEqual(self.a.calls, 0)
        self.assertEqual((collab / "etat.json").read_bytes(), before)
        self.assertFalse((collab / "appels").exists())

    def test_an_unset_effort_never_needs_the_capability(self) -> None:
        collab = self.with_effort(None, None)
        self.a = fakes.FakeAdapter("fake-a", (_DOC,), effort_levels=())
        self.adapters = {"fake-a": self.a, "fake-b": self.b}
        self.run_engine(collab)  # ne lève pas

    def test_it_is_traceable_in_the_recorded_invocation(self) -> None:
        """`intention.json` garde l'argv demandé : c'est là qu'on relit le réglage posé. Le faux
        adaptateur n'y met pas l'effort, mais la valeur du réglage doit rester dans la
        configuration figée."""
        collab = self.with_effort("high", None)
        self.run_engine(collab)
        config = json.loads((collab / "configuration.json").read_text(encoding="utf-8"))
        self.assertEqual(config["agent_a"]["effort"], "high")

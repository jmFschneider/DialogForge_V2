"""L'accès web des agents : **facultatif, fermé par défaut, figé à `new`** (lot 3, point 3.1).

Décision du PO, 2026-09-19 : les recherches web de Codex sont légitimes, mais l'accès n'est pas
un état par défaut. Un seul réglage booléen, `web_access`, pour les deux rôles ; absent, les deux
outils reçoivent explicitement l'interdiction ; les collaborations d'avant restent lisibles et se
comportent comme `web_access = false`. La forme des arguments de chaque outil est éprouvée dans
`test_adapters.py` ; ici, le chemin du réglage jusqu'à l'appel.
"""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from iabinome import cli, workflow
from iabinome.models import Configuration, SchemaError
from tests import fakes
from tests.test_cli import CliCase
from tests.test_workflow import WorkflowCase

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."


class TestConfiguration(WorkflowCase):
    def config_dict(self) -> dict[str, object]:
        collab = fakes.collaboration(self.root)
        raw = fakes.read_json(collab / "configuration.json")
        assert isinstance(raw, dict)
        return raw

    def test_it_is_closed_by_default(self) -> None:
        self.assertFalse(Configuration.from_dict(self.config_dict()).web_access)

    def test_a_collaboration_from_before_the_setting_still_loads_and_is_closed(self) -> None:
        raw = self.config_dict()
        self.assertNotIn("web_access", raw)
        self.assertFalse(Configuration.from_dict(raw).web_access)

    def test_closed_writes_nothing_and_open_is_written_and_read_back(self) -> None:
        closed = Configuration.from_dict(self.config_dict())
        self.assertNotIn("web_access", closed.to_dict())
        opened = Configuration.from_dict({**self.config_dict(), "web_access": True})
        self.assertIs(opened.to_dict()["web_access"], True)
        self.assertTrue(Configuration.from_dict(opened.to_dict()).web_access)

    def test_only_a_real_boolean_is_accepted(self) -> None:
        """`1`, `"true"`, `null` : refusés — un réglage de sécurité ne se devine pas."""
        for bad in (1, 0, "true", "yes", None, [True]):
            with self.assertRaises(SchemaError, msg=repr(bad)):
                Configuration.from_dict({**self.config_dict(), "web_access": bad})

    def test_an_unknown_key_is_still_refused(self) -> None:
        with self.assertRaises(SchemaError):
            Configuration.from_dict({**self.config_dict(), "internet": True})


class TestNewFixesIt(CliCase):
    def created(self) -> dict[str, object]:
        raw = fakes.read_json(self.collab / "configuration.json")
        assert isinstance(raw, dict)
        return raw

    def toml(self, text: str) -> Path:
        path = self.root / "iabinome.toml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_by_default_nothing_is_recorded(self) -> None:
        self.assertEqual(cli.main(["new", *self.new_args()]), 0)
        self.assertNotIn("web_access", self.created())

    def test_the_flag_opens_it_for_the_collaboration(self) -> None:
        argv = ["new", *self.new_args(), "--web-access"]
        self.assertEqual(cli.main(argv), 0)
        self.assertIs(self.created()["web_access"], True)

    def test_the_configuration_file_can_open_it_and_says_so(self) -> None:
        argv = ["new", *self.new_args(), "--config", str(self.toml("web_access = true\n"))]
        with redirect_stderr(io.StringIO()) as err:
            self.assertEqual(cli.main(argv), 0)
        self.assertIs(self.created()["web_access"], True)
        self.assertIn("web_access", err.getvalue())

    def test_the_flag_can_close_what_the_file_opens(self) -> None:
        argv = [
            "new", *self.new_args(), "--no-web-access",
            "--config", str(self.toml("web_access = true\n")),
        ]
        with redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(argv), 0)
        self.assertNotIn("web_access", self.created())

    def test_the_file_must_hold_a_real_boolean(self) -> None:
        for text in ('web_access = "true"\n', "web_access = 1\n"):
            argv = ["new", *self.new_args(), "--config", str(self.toml(text))]
            with redirect_stderr(io.StringIO()) as err:
                self.assertEqual(cli.main(argv), 1, text)
            self.assertIn("web_access", err.getvalue())
            self.assertFalse(self.collab.exists())

    def test_it_is_fixed_at_new_and_run_does_not_reread_the_file(self) -> None:
        """`configuration.json` est la seule vérité une fois la collaboration créée : un fichier
        qui ouvre le web **après** `new` n'ouvre rien."""
        self.assertEqual(cli.main(["new", *self.new_args()]), 0)
        opened = self.toml("web_access = true\n")
        self.a.responses = [_DOC]
        self.b.responses = [fakes.review("ACCEPTER")]
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            cli.main(["run", str(self.collab), "--config", str(opened), "--timeout", "30"])
        self.assertEqual(self.a.web_accesses + self.b.web_accesses, [False, False])


class TestTheEngineAppliesOnePolicy(WorkflowCase):
    def collab(self, *, web: bool | None) -> Path:
        collab = self.build(a=(_DOC,), b=(fakes.review("ACCEPTER"),))
        if web is not None:
            config = fakes.read_json(collab / "configuration.json")
            config["web_access"] = web
            fakes.write_json(collab / "configuration.json", config)
        return collab

    def test_closed_for_both_roles_by_default(self) -> None:
        self.run_engine(self.collab(web=None))
        self.assertEqual((self.a.web_accesses, self.b.web_accesses), ([False], [False]))

    def test_open_for_both_roles_when_asked(self) -> None:
        self.run_engine(self.collab(web=True))
        self.assertEqual((self.a.web_accesses, self.b.web_accesses), ([True], [True]))

    def test_an_explicit_false_is_the_same_as_no_key(self) -> None:
        self.run_engine(self.collab(web=False))
        self.assertEqual((self.a.web_accesses, self.b.web_accesses), ([False], [False]))

    def test_an_adapter_that_cannot_enforce_the_policy_is_refused_before_any_call(self) -> None:
        """La politique — fermée aussi bien qu'ouverte — doit être dans l'argv de l'outil : un
        adaptateur qui ne la contrôle pas est « non supporté », pas lancé en espérant."""
        collab = self.collab(web=None)
        before = (collab / "etat.json").read_bytes()
        weak = fakes.FakeAdapter("fake-b", (), controls_web_access=False)
        self.adapters = {"fake-a": self.a, "fake-b": weak}
        with self.assertRaisesRegex(workflow.WorkflowError, "accès web contrôlé"):
            self.run_engine(collab)
        self.assertEqual((self.a.calls, weak.calls), (0, 0))
        self.assertEqual((collab / "etat.json").read_bytes(), before)
        self.assertFalse((collab / "appels").exists())

    def test_the_recorded_configuration_is_what_the_call_used(self) -> None:
        collab = self.collab(web=True)
        self.run_engine(collab)
        raw = fakes.read_json(collab / "configuration.json")
        self.assertIs(raw["web_access"], True)

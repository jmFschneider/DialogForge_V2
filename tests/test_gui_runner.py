"""Passage GUI vers le Runner : protocole du pont et écran, sans fournisseur ni WSL requis."""

from __future__ import annotations

import json
import sys
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from tkinter import ttk
from typing import Any
from unittest import mock

from iabinome import delivery, executions
from iabinome.gui.runner_session import RunnerRequest, RunnerSession
from iabinome.gui.views.runner import RunnerView
from tests.runner_support import accepted_conception, git_home
from tests.test_gui_views import _ROOT, ViewCase, _find_button, collect_tk_garbage

FAKE_BRIDGE = """\
import json, os, sys
request = json.loads(sys.stdin.readline())
with open(os.environ["BRIDGE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps({"action": request["action"], "token": request["token"],
                          "run": request["run"], "identity": request.get("identity")}) + "\\n")
action = request["action"]
if action == "prepare":
    print(json.dumps({"event": "prepared", "run": request["run"], "base_oid": "a" * 40,
                      "distro": "Ubuntu-test"}), flush=True)
elif action in ("launch", "continue", "collect"):
    print(json.dumps({"event": "completed", "package": "/tmp/paquet"}), flush=True)
elif action == "inspect":
    print(json.dumps({"event": "state", "stage": "prepare", "calls": 0}), flush=True)
else:
    print(json.dumps({"event": "checked", "distro": "Ubuntu-test"}), flush=True)
"""


class SessionProtocolTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        patch = git_home(self.root)
        patch.__enter__()
        self.addCleanup(patch.__exit__, None, None, None)
        self.collab = accepted_conception(self.root)
        self.log = self.root / "pont.log"
        bridge = self.root / "pont.py"
        bridge.write_text(FAKE_BRIDGE, encoding="utf-8")
        for context in (
            mock.patch.dict("os.environ", {"BRIDGE_LOG": str(self.log),
                                           "PYTHONIOENCODING": "utf-8"}),
            mock.patch("iabinome.gui.runner_session._bridge_command",
                       side_effect=lambda distro=None: [sys.executable, str(bridge)]),
            mock.patch("iabinome.gui.runner_session.delivery.deliver"),
        ):
            self.deliver = context.__enter__()
            self.addCleanup(context.__exit__, None, None, None)

    def session(self, action: str, token: str = "jeton") -> RunnerSession:
        request = RunnerRequest(
            action=action, collaboration=self.collab, found=executions.find(self.collab),
            mode="nouveau", repo=self.root / "code", base="HEAD", validations=[["git", "-v"]],
            run="~/dialogforge-runs/essai", token=token, timeout=60, validation_timeout=30,
        )
        session = RunnerSession(request)
        session.start()
        session.thread.join(timeout=30)
        self.assertFalse(session.thread.is_alive())
        return session

    def calls(self) -> list[dict[str, Any]]:
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def test_a_start_checks_prepares_then_launches_and_only_the_launch_gets_the_token(self) -> None:
        session = self.session("start")
        self.assertIsNone(session.error)
        self.assertEqual(session.package, "/tmp/paquet")
        self.assertEqual(session.stage, "Prêt à essayer")
        self.deliver.assert_called_once()
        self.assertEqual(self.deliver.call_args.args[2], {"package": "/tmp/paquet",
                                                          "locked": False})
        calls = self.calls()
        self.assertEqual([c["action"] for c in calls], ["check", "prepare", "launch"])
        self.assertEqual([c["token"] for c in calls], ["", "", "jeton"])
        self.assertEqual(session.request.token, "")
        self.assertEqual(calls[1]["identity"], ["Test Owner", "owner@example.invalid"])
        data = executions.find(self.collab).data
        assert data is not None
        self.assertEqual(data["wsl"]["distribution"], "Ubuntu-test")
        self.assertEqual(data["projet"]["base_oid"], "a" * 40)
        self.assertEqual(data["paquets"], ["/tmp/paquet"])
        self.assertNotIn("jeton", (self.collab.parent / "collaboration-developpement"
                                   / "executions" / "001.json").read_text(encoding="utf-8"))

    def test_a_pause_asked_early_stops_after_the_preparation(self) -> None:
        request = RunnerRequest(
            action="start", collaboration=self.collab, found=executions.find(self.collab),
            mode="nouveau", repo=self.root / "code", base="HEAD", validations=[["git", "-v"]],
            run="~/dialogforge-runs/essai", token="jeton", timeout=60, validation_timeout=30,
        )
        session = RunnerSession(request)
        session.signal("pause")
        session.start()
        session.thread.join(timeout=30)
        self.assertIn("lancement arrêté", session.error or "")
        self.assertEqual([c["action"] for c in self.calls()], ["check", "prepare"])
        self.assertEqual(request.token, "")

    def test_inspect_reads_the_state_and_collect_needs_no_token(self) -> None:
        self.assertEqual((self.session("inspect").state or {})["stage"], "prepare")
        self.assertEqual(self.session("collect").package, "/tmp/paquet")
        self.assertEqual([c["token"] for c in self.calls()], ["", ""])


class _Stub:
    """Une session terminée, rendue à l'écran à la place d'un pont."""

    def __init__(self, action: str, state: dict[str, Any] | None = None,
                 error: str | None = None) -> None:
        self.request = mock.Mock(action=action)
        self.thread = threading.Thread(target=lambda: None)
        self.thread.start()
        self.thread.join()
        self.stage, self.run_path, self.package = "Terminé", "/home/u/run", None
        self.state, self.error = state, error


class RunnerViewTest(ViewCase):
    def open(
        self, collab: Path | None = None, **script: dict[str, Any],
    ) -> tuple[RunnerView, list[RunnerRequest]]:
        """`script` dit ce que rend chaque action, par son nom : `inspect={"state": {...}}`."""
        collect_tk_garbage()  # finaliser les variables Tk avant le fil de la fixture
        collab = collab or self.accepted_collaboration()
        self.collab = collab
        requests: list[RunnerRequest] = []

        def start(request: RunnerRequest) -> _Stub:
            requests.append(request)
            return _Stub(request.action, **script.get(request.action, {}))

        self.controller.start_runner = start  # type: ignore[method-assign,assignment]
        return RunnerView(_ROOT, self.controller, collab), requests

    def rows(self, view: RunnerView) -> list[tuple[str, str]]:
        return [(a.get(), b.get()) for a, b in view._pairs]

    def test_a_fresh_form_proposes_a_new_project_and_one_empty_validation(self) -> None:
        view, requests = self.open()
        self.assertEqual(view._mode.get(), "nouveau")
        self.assertEqual(view._repo.get(), str(executions.default_code(self.collab)))
        self.assertEqual(self.rows(view), [("", "")])
        self.assertEqual(str(view._primary.cget("text")), "Préparer et lancer")
        self.assertEqual(str(view._primary.cget("state")), "normal")
        self.assertEqual(str(view._collect.cget("state")), "disabled")
        self.assertTrue(view._base_entry.instate(["disabled"]))
        self.assertEqual(requests, [], "ouvrir l'écran ne lance rien")

    def test_the_two_ways_switch_the_folder_and_the_base(self) -> None:
        view, _ = self.open()
        code = str(executions.default_code(self.collab))
        view._mode.set("existant")
        view._mode_changed()
        self.assertEqual(view._repo.get(), "")
        self.assertFalse(view._base_entry.instate(["disabled"]))
        view._repo.set("C:/mon/depot")
        view._mode.set("nouveau")
        view._mode_changed()
        self.assertEqual(view._repo.get(), "C:/mon/depot", "un choix de l'utilisateur est gardé")
        view._repo.set("")
        view._mode_changed()
        self.assertEqual(view._repo.get(), code)

    def test_validation_rows_are_edited_and_become_argument_lists(self) -> None:
        view, _ = self.open()
        view._pairs[0][0].set("node")
        view._pairs[0][1].set("--test")
        _find_button(view, "Ajouter une validation").invoke()
        view._pairs[1][0].set("python3")
        view._pairs[1][1].set('-m pytest "tests unitaires"')
        _find_button(view, "Ajouter une validation").invoke()
        retirer = [b for b in _buttons(view) if str(b.cget("text")) == "Retirer"]
        self.assertEqual(len(retirer), 3)
        retirer[2].invoke()
        view._token.set("jeton")
        request = view._request("start")
        self.assertEqual(request.validations,
                         [["node", "--test"], ["python3", "-m", "pytest", "tests unitaires"]])
        self.assertEqual((request.mode, request.base, request.token), ("nouveau", "HEAD", "jeton"))

    def test_an_incomplete_form_is_refused_with_its_reason(self) -> None:
        view, requests = self.open()
        view._token.set("jeton")
        with self.assertRaisesRegex(ValueError, "au moins une validation"):
            view._request("start")
        view._pairs[0][0].set("node")
        view._token.set("")
        with self.assertRaisesRegex(ValueError, "jeton"):
            view._request("start")
        view._token.set("jeton")
        view._run.set("")
        with self.assertRaisesRegex(ValueError, "dossier du projet et le dossier Runner"):
            view._request("start")
        view._run.set("~/x")
        view._pairs[0][1].set('"non fermé')
        view._primary.invoke()
        self.assertIn("À corriger", str(view._status.cget("text")))
        self.assertEqual(requests, [])

    def test_the_token_is_cleared_once_the_session_started(self) -> None:
        view, requests = self.open()
        view._pairs[0][0].set("node")
        view._token.set("jeton")
        view._primary.invoke()
        self.assertEqual([r.action for r in requests], ["start"])
        self.assertEqual(view._token.get(), "")

    def test_the_accepted_conception_text_is_shown_read_only(self) -> None:
        view, _ = self.open()
        shown = [w for w in _all(view) if w.winfo_class() == "Text"]
        self.assertEqual(len(shown), 3)
        self.assertIn("Corps du document.", shown[0].get("1.0", "end"))
        self.assertEqual(str(shown[0].cget("state")), "disabled")

    def test_a_ready_package_shows_its_report_and_needs_a_correction_goal(self) -> None:
        view = self.reopened({
            "stage": "paquet", "package": "/home/u/package", "calls": 1,
            "report": "Recette navigateur C01 à C22 à faire.",
            "checks": [{"command": ["node", "--test"], "outcome": "PASSED"}],
        })
        self.assertEqual(str(view._primary.cget("text")), "Demander une correction")
        self.assertEqual(str(view._collect.cget("state")), "disabled")
        self.assertIn("node --test : PASSED", view._report.get("1.0", "end"))
        self.assertIn("C01 à C22", view._report.get("1.0", "end"))
        view._token.set("jeton")
        with self.assertRaisesRegex(ValueError, "décrire la correction"):
            view._request("correct")
        view._correction.insert("1.0", "Corriger C03 après revue.")
        self.assertEqual(view._request("correct").correction, "Corriger C03 après revue.")

    def test_a_ready_package_is_delivered_then_accepted_without_token(self) -> None:
        view = self.reopened({"stage": "paquet", "package": "/home/u/package", "calls": 1})
        self.assertEqual(str(view._accept_button.cget("state")), "disabled")
        shown = delivery.Delivered(
            self.root_dir / "code", "dialogforge/candidat-001", self.root_dir / "p", "a" * 40,
            "b" * 40, self.root_dir / "code", "main", False,
        )
        with (mock.patch("iabinome.gui.views.runner.delivery.deliver") as deliver,
              mock.patch("iabinome.gui.views.runner.delivery.current", return_value=shown)):
            self.assertEqual(str(view._deliver_button.cget("state")), "normal")
            view._deliver_button.invoke()
            deliver.assert_called_once()
            self.assertIn("Prêt à essayer", str(view._status.cget("text")))
            self.assertIn("b" * 12, str(view._status.cget("text")))
            self.assertEqual(str(view._accept_button.cget("state")), "normal")
            with (mock.patch("iabinome.gui.views.runner.dialogs.confirm", return_value=True),
                  mock.patch("iabinome.gui.views.runner.delivery.accept") as accept):
                view._accept_button.invoke()
            accept.assert_called_once()
        self.assertEqual(view._token.get(), "")

    def test_a_refused_delivery_explains_and_overwrites_nothing(self) -> None:
        view = self.reopened({"stage": "paquet", "package": "/home/u/package", "calls": 1})
        with mock.patch("iabinome.gui.views.runner.delivery.deliver",
                        side_effect=ValueError("l'espace d'essai contient des modifications")):
            view._deliver_button.invoke()
        self.assertIn("rien n'est écrasé", str(view._status.cget("text")))
        self.assertIn("contient des modifications", str(view._status.cget("text")))

    def reopened(self, state: dict[str, Any]) -> RunnerView:
        collab = accepted_conception(self.root_dir / "reprise")
        found = executions.find(collab)
        export = executions.ensure_export(collab, found)
        executions.save(
            found, export, mode="existant", repo=self.root_dir / "depot", base="main",
            validations=[["node", "--test"], ["git", "status"]], run="/home/u/run",
            agent_timeout=1800.0, validation_timeout=120.0,
        )
        view, requests = self.open(collab, inspect={"state": state})
        self.assertEqual([r.action for r in requests], ["inspect"])
        return view

    def test_a_reopened_window_refills_the_form_and_offers_only_the_right_start(self) -> None:
        view = self.reopened({"stage": "prepare", "calls": 0})
        self.assertEqual((view._mode.get(), view._base.get(), view._run.get()),
                         ("existant", "main", "/home/u/run"))
        self.assertEqual(self.rows(view), [("node", "--test"), ("git", "status")])
        self.assertEqual((view._timeout.get(), view._validation_timeout.get()), ("1800.0", "120.0"))
        self.assertEqual(str(view._primary.cget("text")), "Lancer A")
        self.assertEqual(str(view._collect.cget("state")), "normal")
        self.assertTrue(view._repo_entry.instate(["disabled"]), "le clone existe : figé")
        self.assertIn("agent non lancé", str(view._status.cget("text")))

    def test_each_interruption_offers_its_own_start(self) -> None:
        expected = {
            "absent": "Préparer et lancer", "appel": "Continuer avec A",
            "validations": "Continuer avec A", "paquet": "Demander une correction",
        }
        for stage, label in expected.items():
            with self.subTest(stage=stage):
                view = self.reopened({"stage": stage, "calls": 1,
                                      "package": "/p" if stage == "paquet" else None})
                self.assertEqual(str(view._primary.cget("text")), label)
                self.assertEqual(view._repo_entry.instate(["disabled"]), stage != "absent")
        view = self.reopened({"stage": "invalide", "detail": "run.json illisible"})
        self.assertEqual(str(view._primary.cget("state")), "disabled")
        self.assertEqual(str(view._collect.cget("state")), "disabled")
        self.assertIn("run.json illisible", str(view._status.cget("text")))

    def test_a_continuation_asks_for_the_token_but_a_collection_does_not(self) -> None:
        view = self.reopened({"stage": "appel", "calls": 1})
        with self.assertRaisesRegex(ValueError, "jeton"):
            view._request("continue")
        request = view._request("collect")
        self.assertEqual((request.token, request.repo, request.run),
                         ("", self.root_dir / "depot", "/home/u/run"))
        self.assertEqual(request.validations, [["node", "--test"], ["git", "status"]])
        view._token.set("jeton")
        self.assertEqual(view._request("continue").token, "jeton")

    def test_the_cause_of_a_failed_action_survives_the_reading_of_the_state(self) -> None:
        collab = accepted_conception(self.root_dir / "echec")
        found = executions.find(collab)
        executions.save(
            found, executions.ensure_export(collab, found), mode="existant",
            repo=self.root_dir / "depot", base="HEAD", validations=[["node", "--test"]],
            run="/home/u/run", agent_timeout=60.0, validation_timeout=30.0,
        )
        view, requests = self.open(
            collab, inspect={"state": {"stage": "appel", "calls": 1}},
            **{"continue": {"error": "appel agent interrompu"}},
        )
        view._token.set("jeton")
        view._begin("continue")
        self.assertEqual([r.action for r in requests], ["inspect", "continue", "inspect"])
        shown = str(view._status.cget("text"))
        self.assertIn("appel agent interrompu", shown)
        self.assertIn("1 appel(s) de A", shown)
        self.assertEqual(view._token.get(), "")

    def test_the_token_stays_in_memory_until_forgotten_and_the_message_reaches_a(self) -> None:
        view = self.reopened({"stage": "appel", "calls": 1, "verdict": "INTERVENTION",
                              "last_call_complete": True})
        self.assertIn("A attend une intervention", str(view._status.cget("text")))
        self.assertEqual(str(view._forget.cget("state")), "disabled")
        view._token.set("jeton")
        view._correction.insert("1.0", "Viser Firefox et Chromium.")
        view._begin("continue")
        self.assertEqual(self.controller.runner_token, "jeton")
        self.assertEqual(view._token.get(), "", "le champ est vidé, la mémoire garde le jeton")
        view._apply({"stage": "appel", "calls": 2})
        request = view._request("continue")
        self.assertEqual((request.token, request.correction), ("jeton", ""))
        self.assertEqual(str(view._forget.cget("state")), "normal")
        view._forget.invoke()
        self.assertEqual(self.controller.runner_token, "")
        with self.assertRaisesRegex(ValueError, "jeton"):
            view._request("continue")

    def test_the_message_for_a_goes_with_a_continuation(self) -> None:
        view = self.reopened({"stage": "appel", "calls": 1, "verdict": "INTERVENTION"})
        view._token.set("jeton")
        view._correction.insert("1.0", "Viser Firefox.")
        self.assertEqual(view._request("continue").correction, "Viser Firefox.")
        self.assertEqual(view._request("collect").correction, "")

    def test_a_run_limited_to_a_lot_offers_no_agent_call(self) -> None:
        view = self.reopened({"stage": "appel", "calls": 1, "lot": True})
        self.assertEqual(str(view._primary.cget("state")), "disabled")
        self.assertEqual(str(view._collect.cget("state")), "normal")
        self.assertIn("limitée à un lot", str(view._status.cget("text")))

    def test_a_bridge_failure_while_reading_the_state_is_shown_not_hidden(self) -> None:
        view = self.reopened({"stage": "prepare"})
        view._session = _Stub("inspect", error="WSL introuvable")  # type: ignore[assignment]
        view._poll()
        self.assertEqual(str(view._primary.cget("state")), "disabled")
        self.assertIn("WSL introuvable", str(view._status.cget("text")))


def _all(widget: Any) -> list[Any]:
    found = []
    for child in widget.winfo_children():
        found.append(child)
        found += _all(child)
    return found


def _buttons(widget: Any) -> list[ttk.Button]:
    return [w for w in _all(widget) if isinstance(w, ttk.Button)]

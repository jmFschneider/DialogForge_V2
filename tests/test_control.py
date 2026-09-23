"""GUI V1, lot 2 : pause et interruption **commandées**, un seul mécanisme pour la
CLI et la GUI (`conception/GUI_V1.md` §9.1, AC-24 à AC-26).

`KeyboardInterrupt` n'atteint pas un moteur placé dans un fil secondaire — c'est
là que la GUI le mettra. Ces tests font donc tourner le moteur **dans un fil**, et
posent la demande depuis le fil principal, pendant un vrai sous-processus.
"""

from __future__ import annotations

import io
import threading
import time
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from iabinome import cli, transport, workflow
from iabinome.models import State, Status
from iabinome.transport import ExecutionControl, Outcome
from tests import fakes
from tests.test_cli import CliCase
from tests.test_incidents import _DOC
from tests.test_objections import review_v2
from tests.test_transport import TransportCase
from tests.test_workflow import WorkflowCase

_WAIT_SECONDS = 20.0


def _wait_for(predicate: object, what: str) -> None:
    deadline = time.monotonic() + _WAIT_SECONDS
    while not predicate():  # type: ignore[operator]
        if time.monotonic() > deadline:
            raise AssertionError(f"jamais observé : {what}")
        time.sleep(0.02)


class TestTheTransportObeys(TransportCase):
    def test_an_interrupt_from_another_thread_stops_the_call_at_once(self) -> None:
        control = ExecutionControl()
        threading.Timer(0.5, control.interrupt_requested.set).start()
        started = time.monotonic()
        result = transport.run(
            fakes.command(stdout="debut", sleep_seconds=30.0), cwd=self.root,
            call_dir=self.call_dir, timeout_seconds=60.0, control=control,
        )
        self.assertIs(result.outcome, Outcome.INTERRUPTED_BY_USER)
        self.assertFalse((self.call_dir / "resultat.json").exists())
        self.assertLess(time.monotonic() - started, transport.CLEANUP_LIMIT_SECONDS + 5.0)

    def test_a_pause_does_not_touch_the_call(self) -> None:
        """La pause appartient au moteur, à la frontière : le transport l'ignore."""
        control = ExecutionControl()
        control.pause_requested.set()
        result = transport.run(
            fakes.command(stdout="document", sleep_seconds=0.3), cwd=self.root,
            call_dir=self.call_dir, timeout_seconds=60.0, control=control,
        )
        self.assertIs(result.outcome, Outcome.COMPLETED)


class _Threaded(WorkflowCase):
    """Le moteur dans un fil secondaire, comme sous la GUI."""

    def start(self, collab: Path, control: ExecutionControl) -> threading.Thread:
        self.outcome: list[object] = []

        def engine() -> None:
            try:
                self.outcome.append(workflow.run(
                    collab, adapters=self.adapters, timeout_seconds=60.0, control=control
                ))
            except BaseException as exc:  # noqa: BLE001 — rapporté au fil principal
                self.outcome.append(exc)

        thread = threading.Thread(target=engine, daemon=True)
        thread.start()
        return thread

    def first_call_running(self, collab: Path) -> None:
        _wait_for(lambda: any((collab / "appels").glob("*/pid.txt")), "l'appel de A lancé")

    def finished(self, thread: threading.Thread) -> State:
        thread.join(_WAIT_SECONDS + transport.CLEANUP_LIMIT_SECONDS)
        self.assertFalse(thread.is_alive(), "le moteur n'a pas rendu la main")
        (result,) = self.outcome
        if isinstance(result, BaseException):
            raise result
        assert isinstance(result, State)
        return result


class TestTheEngineInASecondaryThread(_Threaded):
    def test_a_pause_lets_the_call_finish_then_stops_before_the_next(self) -> None:
        collab = self.build(a=(_DOC,), b=(review_v2("ACCEPTER"),))
        self.a.sleep_seconds = 1.0
        control = ExecutionControl()
        thread = self.start(collab, control)
        self.first_call_running(collab)
        control.pause_requested.set()
        state = self.finished(thread)
        self.assertIs(state.status, Status.READY)
        self.assertEqual(state.phase.value, "REVIEW_B", "l'appel de A n'a pas été appliqué")
        self.assertEqual(fakes.launched_calls(collab), 1, "un appel est parti après la pause")

    def test_an_interrupt_stops_the_running_call_and_nothing_follows(self) -> None:
        collab = self.build(a=(_DOC,), b=(review_v2("ACCEPTER"),))
        self.a.sleep_seconds = 30.0
        control = ExecutionControl()
        thread = self.start(collab, control)
        self.first_call_running(collab)
        control.interrupt_requested.set()
        state = self.finished(thread)
        self.assertIs(state.status, Status.INTERRUPTED)
        incident = fakes.read_json(collab / str(state.last_incident))
        self.assertEqual(incident["kind"], "INTERRUPTED_BY_USER")
        self.assertEqual(fakes.launched_calls(collab), 1)

    def test_an_interrupt_before_the_call_launches_nothing(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        before = (collab / "etat.json").read_bytes()
        control = ExecutionControl()
        control.interrupt_requested.set()
        thread = self.start(collab, control)
        thread.join(_WAIT_SECONDS)
        (outcome,) = self.outcome
        self.assertIsInstance(outcome, workflow.Stopped)
        self.assertEqual(fakes.launched_calls(collab), 0)
        self.assertEqual((collab / "etat.json").read_bytes(), before)
        self.assertFalse((collab / "verrou.json").exists(), "le verrou n'a pas été rendu")

    def test_an_interrupt_between_two_calls_stops_like_a_pause(self) -> None:
        collab = self.build(a=(_DOC,), b=(review_v2("ACCEPTER"),))

        class _AfterA(threading.Event):
            """L'interruption arrive une fois A appliqué et publié : entre deux appels."""

            def is_set(self) -> bool:
                return bool(fakes.read_json(collab / "etat.json")["phase"] == "REVIEW_B")

        control = ExecutionControl(interrupt_requested=_AfterA())
        state = workflow.run(
            collab, adapters=self.adapters, timeout_seconds=60.0, control=control
        )
        self.assertIs(state.status, Status.READY)
        self.assertEqual(fakes.launched_calls(collab), 1)


class TestTheCommandLineUsesTheSameControl(CliCase):
    def new(self) -> None:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["new", *self.new_args()]), 0)

    def test_a_stop_before_any_call_is_exit_6_and_says_nothing_was_launched(self) -> None:
        self.new()
        self.a.responses = [_DOC]

        class _AskedTwice(cli._CtrlC):
            def __init__(self) -> None:
                super().__init__()
                self.control.pause_requested.set()
                self.control.interrupt_requested.set()

        with mock.patch.object(cli, "_CtrlC", _AskedTwice):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as err:
                code = cli.main(["run", str(self.collab)])
        self.assertEqual(code, 6)
        self.assertIn("aucun appel n'était en cours", err.getvalue())
        self.assertEqual(fakes.launched_calls(self.collab), 0)

"""GUI V1, lot 4 : le contrôleur possède **au plus un fil moteur** (§3.1,
§10.4), la première fois que la GUI appelle `workflow.run` (« créer et
démarrer », §6.7). Comme `tests/test_control.py` côté CLI : un `FakeAdapter`
reste un vrai sous-processus, jamais un objet simulé (`RULES.md`, Tests).
"""

from __future__ import annotations

import time
import unittest
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from iabinome import facade
from iabinome.gui import app
from iabinome.gui.controller import Controller
from iabinome.gui.views.suivi import SuiviView
from tests import fakes
from tests.test_gui_views import _ROOT

_WAIT_SECONDS = 20.0


def _wait_for(predicate: Callable[[], bool], what: str) -> None:
    deadline = time.monotonic() + _WAIT_SECONDS
    while not predicate():
        if time.monotonic() > deadline:
            raise AssertionError(f"jamais observé : {what}")
        time.sleep(0.02)


class ExecutionCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root_dir = Path(self._tmp.name)
        self.controller = Controller(_ROOT, recents_path=self.root_dir / "recents.json")
        self.collab = fakes.collaboration(self.root_dir)
        self.a = fakes.FakeAdapter("fake-a", ("IABINOME:DOCUMENT\n# Proposition\nCorps.",))
        self.b = fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),))
        patcher = mock.patch(
            "iabinome.gui.controller.ADAPTERS", {"fake-a": self.a, "fake-b": self.b},
        )
        patcher.start()
        self.addCleanup(patcher.stop)


class TestStartRun(ExecutionCase):
    def test_a_run_reaches_awaiting_approval(self) -> None:
        self.controller.start_run(self.collab, timeout_seconds=30.0)
        self.assertTrue(self.controller.is_running(self.collab))
        _wait_for(lambda: not self.controller.is_running(self.collab), "fin du cycle")
        state = facade.inspect_collaboration(self.collab).state
        self.assertEqual(state.status.value, "AWAITING_APPROVAL")
        self.assertIsNone(self.controller.run_error(self.collab))

    def test_a_second_call_on_the_same_path_does_not_start_a_second_thread(self) -> None:
        """§3.1, §8.2 : une exécution au maximum — jamais une seconde reprise
        concurrente pendant qu'une autre est active."""
        self.a.sleep_seconds = 0.3
        self.controller.start_run(self.collab, timeout_seconds=30.0)
        first_thread = self.controller._run_thread
        self.controller.start_run(self.collab, timeout_seconds=30.0)
        self.assertIs(self.controller._run_thread, first_thread)
        _wait_for(lambda: not self.controller.is_running(self.collab), "fin du cycle")

    def test_a_preflight_refusal_is_reported_without_touching_the_folder(self) -> None:
        before = (self.collab / "etat.json").read_bytes()
        with mock.patch("iabinome.gui.controller.ADAPTERS", {}):
            self.controller.start_run(self.collab, timeout_seconds=30.0)
            _wait_for(lambda: not self.controller.is_running(self.collab), "fin du fil")
        self.assertIsNotNone(self.controller.run_error(self.collab))
        self.assertEqual((self.collab / "etat.json").read_bytes(), before)


class TestInterruption(ExecutionCase):
    def test_interrupting_an_active_run_stops_it(self) -> None:
        self.a.sleep_seconds = 5.0
        self.controller.start_run(self.collab, timeout_seconds=30.0)
        _wait_for(lambda: any((self.collab / "appels").glob("*/pid.txt")), "appel lancé")
        self.controller.interrupt_active_run()
        _wait_for(lambda: not self.controller.is_running(self.collab), "fin du fil")
        state = facade.inspect_collaboration(self.collab).state
        self.assertEqual(state.status.value, "INTERRUPTED")

    def test_has_active_run_reflects_the_thread(self) -> None:
        self.assertFalse(self.controller.has_active_run())
        self.a.sleep_seconds = 0.3
        self.controller.start_run(self.collab, timeout_seconds=30.0)
        self.assertTrue(self.controller.has_active_run())
        _wait_for(lambda: not self.controller.has_active_run(), "fin du fil")


class TestSuiviPolling(ExecutionCase):
    def test_the_view_stops_polling_once_the_run_finishes(self) -> None:
        self.controller.start_run(self.collab, timeout_seconds=30.0)
        view = SuiviView(_ROOT, self.controller, self.collab)
        self.addCleanup(view.destroy)
        self.assertIsNotNone(view._after_id)
        _wait_for(lambda: not self.controller.is_running(self.collab), "fin du cycle")
        # Un dernier passage que `after()` aurait programmé — on le déclenche
        # nous-mêmes, sans faire tourner `mainloop()`.
        view._refresh()
        self.assertIsNone(view._after_id)


class TestCloseGuard(unittest.TestCase):
    """§9.2-9.3, partiel : « continuer à suivre » et « interrompre maintenant »
    seulement — la pause différée reste au lot 5/6 (voir `app.py`)."""

    def test_closing_without_an_active_run_destroys_immediately(self) -> None:
        root, controller = mock.Mock(), mock.Mock()
        controller.has_active_run.return_value = False
        app._on_close(root, controller)
        root.destroy.assert_called_once()
        controller.interrupt_active_run.assert_not_called()

    def test_cancelling_the_close_confirmation_keeps_the_window_open(self) -> None:
        root, controller = mock.Mock(), mock.Mock()
        controller.has_active_run.return_value = True
        with mock.patch("iabinome.gui.app.dialogs.confirm", return_value=False):
            app._on_close(root, controller)
        root.destroy.assert_not_called()
        controller.interrupt_active_run.assert_not_called()

    def test_confirming_interrupts_then_destroys(self) -> None:
        root, controller = mock.Mock(), mock.Mock()
        controller.has_active_run.return_value = True
        with mock.patch("iabinome.gui.app.dialogs.confirm", return_value=True):
            app._on_close(root, controller)
        controller.interrupt_active_run.assert_called_once()
        root.destroy.assert_called_once()

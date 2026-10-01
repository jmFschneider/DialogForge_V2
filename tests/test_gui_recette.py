"""GUI V1, lot 6 : recette — compatibilité CLI/GUI, atomicité sous verrou,
parité des actions, périmètre et taille (`conception/GUI_V1.md` §15.4-§15.6).

Les scénarios avec faux agents (§15.3) sont déjà couverts, un par un, dans
`tests/test_gui_creation.py`, `tests/test_gui_execution.py` et
`tests/test_gui_intervention.py` ; ce module couvre ce qui reste propre à la
recette : les deux sens CLI↔GUI, un verrou déjà tenu, et un balayage du
périmètre exclu (§13).
"""

from __future__ import annotations

import io
import json
import os
import re
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from iabinome import cli, facade, settings
from iabinome.decisions import ActionId
from iabinome.gui.controller import Controller
from iabinome.gui.views import intervention
from iabinome.models import MissionKind, ReviewerAccess
from tests import fakes
from tests.test_gui_views import _ROOT, collect_tk_garbage

_ROOT_DIR = Path(__file__).resolve().parent.parent
_GUI_SRC = _ROOT_DIR / "src" / "iabinome" / "gui"


class CompatibilityCase(unittest.TestCase):
    def setUp(self) -> None:
        collect_tk_garbage()
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root_dir = Path(self._tmp.name)
        self.controller = Controller(_ROOT, recents_path=self.root_dir / "recents.json")
        self.fake_adapters = {
            "fake-a": fakes.FakeAdapter("fake-a", ("IABINOME:DOCUMENT\n# Proposition\nCorps.",)),
            "fake-b": fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),)),
        }
        for target in ("iabinome.gui.controller.ADAPTERS", "iabinome.gui.views.creation.ADAPTERS"):
            patcher = mock.patch(target, self.fake_adapters)
            patcher.start()
            self.addCleanup(patcher.stop)

    def cli_run(self, *argv: str) -> int:
        with mock.patch.object(cli, "ADAPTERS", self.fake_adapters), \
             mock.patch.object(settings, "SEARCH_PATHS", ()), \
             redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return cli.main(list(argv))


class TestCreatedInTheGuiContinuesInTheCli(CompatibilityCase):
    def test_a_gui_created_collaboration_runs_to_completion_in_the_cli(self) -> None:
        collab = self.root_dir / "collab-gui"
        request = facade.CreationRequest(
            collab=collab, demande=facade.DemandeSource("Concevoir le cache.", "cadrage"),
            kind=MissionKind.RECHERCHE, reviewer_access=ReviewerAccess.CONSULT,
            agent_a="fake-a", agent_b="fake-b", max_revisions=2, web_access=True,
        )
        facade.create_collaboration(request, adapters=self.fake_adapters)
        self.assertEqual(self.cli_run("run", str(collab)), 0)
        state = facade.inspect_collaboration(collab).state
        self.assertEqual(state.status.value, "AWAITING_APPROVAL")
        self.assertEqual(self.cli_run("decide", str(collab), "--accept"), 0)
        self.assertEqual(
            facade.inspect_collaboration(collab).presentation.status_label, "Version acceptée",
        )


class TestCreatedInTheCliContinuesInTheGui(CompatibilityCase):
    def test_a_cli_created_collaboration_runs_to_completion_in_the_gui(self) -> None:
        collab = self.root_dir / "collab-cli"
        demande = self.root_dir / "demande.md"
        demande.write_text("Concevoir le cache.", encoding="utf-8")
        code = self.cli_run(
            "new", str(collab), "--demande", str(demande), "--kind", "recherche", "--web-access",
            "--reviewer-access", "consult", "--agent-a", "fake-a", "--agent-b", "fake-b",
        )
        self.assertEqual(code, 0)
        self.controller.start_run(collab, timeout_seconds=30.0)
        self._wait_until_done(collab)
        self.assertIsNone(self.controller.run_error(collab))
        snapshot = facade.inspect_collaboration(collab)
        self.assertEqual(snapshot.state.status.value, "AWAITING_APPROVAL")
        action = next(
            a for a in snapshot.presentation.allowed_actions if a.id is ActionId.ACCEPT
        )
        with mock.patch("iabinome.gui.dialogs.prompt_text"), \
             mock.patch("iabinome.gui.dialogs.confirm"):
            intervention.run(_ROOT, self.controller, collab, action)
        self.assertEqual(
            facade.inspect_collaboration(collab).presentation.status_label, "Version acceptée",
        )

    def _wait_until_done(self, collab: Path) -> None:
        import time

        deadline = time.monotonic() + 20.0
        while self.controller.is_running(collab):
            if time.monotonic() > deadline:
                raise AssertionError("le cycle lance depuis la GUI n'a jamais fini")
            time.sleep(0.02)


class TestALockAlreadyHeldIsReportedNotCorrupted(CompatibilityCase):
    def test_starting_a_run_on_a_locked_collaboration_reports_the_lock(self) -> None:
        collab = fakes.collaboration(self.root_dir)
        before = (collab / "etat.json").read_bytes()
        (collab / "verrou.json").write_text(json.dumps({
            "lock_id": "verrou-de-test", "pid": os.getpid(),
            "acquired_at": "2026-01-01T00:00:00Z", "command": "run",
        }), encoding="utf-8")
        self.controller.start_run(collab, timeout_seconds=30.0)
        self._wait_until_done(collab)
        self.assertIsNotNone(self.controller.run_error(collab))
        self.assertEqual((collab / "etat.json").read_bytes(), before)

    def _wait_until_done(self, collab: Path) -> None:
        import time

        deadline = time.monotonic() + 20.0
        while self.controller.is_running(collab):
            if time.monotonic() > deadline:
                raise AssertionError("le fil ne s'est jamais arrêté sur le verrou tenu")
            time.sleep(0.02)


class TestEveryActionHasAGuiLabel(unittest.TestCase):
    """§10.2 : « la GUI transforme les actions structurées en boutons » — un
    `ActionId` sans étiquette serait un bouton manquant, découvert en usage."""

    def test_every_action_id_is_labelled(self) -> None:
        for action_id in ActionId:
            with self.subTest(action_id.value):
                self.assertTrue(intervention.label(action_id))


class TestPerimeter(unittest.TestCase):
    """§13, §15.6 : ce que la recette recherche dans `iabinome/gui/` et n'y
    trouve pas."""

    _FORBIDDEN = {
        "base de données": re.compile(r"sqlite3|\bsqlalchemy\b", re.IGNORECASE),
        "serveur HTTP": re.compile(r"http\.server|socketserver|BaseHTTPRequestHandler"),
        "worker/planificateur": re.compile(r"\bmultiprocessing\b|\bcelery\b|\bAPScheduler\b"),
        "lancement détaché": re.compile(
            r"DETACHED_PROCESS|CREATE_NEW_PROCESS_GROUP|start_new_session"
        ),
        "budget/réservation/bail/worktree": re.compile(
            r"\bbudget\b|\br[ée]servation\b|\bbail\b|\bworktree\b", re.IGNORECASE
        ),
    }

    def test_the_gui_source_avoids_the_excluded_mechanisms(self) -> None:
        files = list(_GUI_SRC.rglob("*.py"))
        self.assertTrue(files, "aucun fichier source GUI trouvé")
        for path in files:
            text = path.read_text(encoding="utf-8")
            for name, pattern in self._FORBIDDEN.items():
                with self.subTest(file=path.relative_to(_ROOT_DIR), forbidden=name):
                    self.assertIsNone(pattern.search(text))

    def test_the_only_table_of_what_is_allowed_is_decisions_allowed_actions(self) -> None:
        """§10.2 : la GUI étiquette des `ActionId` (`intervention._LABELS`),
        elle ne décide jamais seule ce qui est permis pour un statut — la
        preuve précise est `tests/test_facade.py`
        `TestInspectionMatchesTheEngine.test_allowed_actions_come_straight_
        from_decisions`. Ici, on vérifie seulement que `views/suivi.py`
        consomme bien `decisions.allowed_actions` par la façade, sans grep
        fragile sur le texte du module."""
        text = (_GUI_SRC / "views" / "suivi.py").read_text(encoding="utf-8")
        self.assertIn("snapshot.presentation.allowed_actions", text)

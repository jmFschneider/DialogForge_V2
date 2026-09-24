"""Phase 6, lot 5 : « Cadrer avec un agent » dans la GUI (`conception/CADRAGE_AGENT.md` §4,
tests §14.7 n° 65 à 72, et 42, 45, 46, 54 côté GUI).

Derrière la racine Tk masquée de `tests/test_gui_views.py`. F est un `FakeAdapter` : chaque
tour reste un vrai sous-processus, lancé par l'unique fil moteur du contrôleur. Le sondage
`after()` de la modale n'est jamais laissé à une boucle Tk : le test attend la fin du fil,
puis appelle lui-même `_poll`, comme `after()` l'aurait fait.
"""

from __future__ import annotations

import json
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import mock

from iabinome import settings
from iabinome.gui.controller import Controller
from iabinome.gui.views import cadrage
from iabinome.gui.views.creation import CreationView
from tests import fakes
from tests.test_framing import DRAFT_OUT, QUESTION_OUT, READY_OUT
from tests.test_gui_execution import _wait_for
from tests.test_gui_views import _ROOT, _find_button

_ADDED = "\nUne ligne ajoutée à la relecture."


class GuiFramingCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root_dir = Path(self._tmp.name)
        self.collab = self.root_dir / "ma-collab"
        self.controller = Controller(_ROOT, recents_path=self.root_dir / "recents.json")
        self.addCleanup(self.controller.discard_framing)
        self.addCleanup(lambda: [c.destroy() for c in list(_ROOT.winfo_children())])
        self.f = fakes.FakeAdapter("fake-f", ())
        adapters = {
            "fake-a": fakes.FakeAdapter("fake-a", ()), "fake-b": fakes.FakeAdapter("fake-b", ()),
            "fake-f": self.f,
        }
        self.dialogs: list[cadrage.FramingDialog] = []
        real_dialog = cadrage.FramingDialog

        def dialog(*args: Any, **kwargs: Any) -> cadrage.FramingDialog:
            self.dialogs.append(real_dialog(*args, **kwargs))
            return self.dialogs[-1]

        patchers: list[Any] = [
            *(mock.patch(f"iabinome.gui.{m}.ADAPTERS", adapters)
              for m in ("views.creation", "views.cadrage", "controller")),
            mock.patch.object(settings, "SEARCH_PATHS", ()),
            # Une racine masquée n'est pas « visible » : la saisie modale y échouerait.
            mock.patch.object(real_dialog, "grab_set"),
            mock.patch.object(cadrage, "FramingDialog", side_effect=dialog),
        ]
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def view(self, *replies: Any) -> CreationView:
        self.f.framing_responses = list(replies)
        view = CreationView(_ROOT, self.controller)
        view._dossier.set(str(self.collab))
        view._agent_a.set("fake-a")
        view._agent_b.set("fake-b")
        view._mode.set("agent")
        view._on_mode()
        view._framing_panel.agent.set("fake-f")
        view._framing_panel.idea.insert("1.0", "Un cache pour FloraPi")
        return view

    def start(self, view: CreationView) -> cadrage.FramingDialog:
        _find_button(_buttons(view._framing_panel), "Commencer le cadrage").invoke()
        self.assertEqual(view._error.cget("text"), "")
        return self.settle(self.dialogs[-1])

    def settle(self, dialog: cadrage.FramingDialog) -> cadrage.FramingDialog:
        _wait_for(lambda: not self.controller.has_active_run(), "fin du tour de F")
        dialog._poll()
        return dialog

    def click(self, dialog: cadrage.FramingDialog, name: str, text: str = "") -> None:
        if text:
            dialog._reply.insert("1.0", text)
        dialog._buttons[name].invoke()
        self.settle(dialog)

    def to_draft(self, view: CreationView) -> None:
        dialog = self.start(view)
        self.click(dialog, "Envoyer", "Python seul")
        self.click(dialog, "Clore maintenant")  # « Rédiger le brouillon » sur une proposition

    def enabled(self, dialog: cadrage.FramingDialog) -> set[str]:
        return {name for name, b in dialog._buttons.items() if not b.instate(["disabled"])}


def _buttons(panel: cadrage.FramingPanel) -> Any:
    return panel.winfo_children()[-1]


class TestConversation(GuiFramingCase):
    def test_each_turn_runs_in_the_engine_thread_with_controls_disabled(self) -> None:
        """Tests 65, 68 : le fil Tk rend la main pendant le tour ; tout est désactivé."""
        self.f.sleep_seconds = 0.5
        view = self.view(QUESTION_OUT)
        _find_button(_buttons(view._framing_panel), "Commencer le cadrage").invoke()
        dialog = self.dialogs[-1]
        self.assertTrue(self.controller.has_active_run())
        self.assertEqual(self.enabled(dialog), set())
        self.settle(dialog)
        self.assertEqual(self.enabled(dialog), {"Envoyer", "Clore maintenant"})

    def test_a_proposal_offers_continue_correct_and_draft(self) -> None:
        dialog = self.start(self.view(QUESTION_OUT, READY_OUT))
        self.click(dialog, "Envoyer", "Python seul")
        self.assertEqual(self.enabled(dialog), {"Envoyer", "Corriger un point", "Clore maintenant"})
        self.assertEqual(dialog._buttons["Envoyer"].cget("text"), "Continuer")
        self.assertEqual(dialog._buttons["Clore maintenant"].cget("text"), "Rédiger le brouillon")

    def test_an_incident_offers_an_explicit_retry_only(self) -> None:
        dialog = self.start(self.view("hors protocole", QUESTION_OUT))
        self.assertEqual(self.enabled(dialog), {"Clore maintenant", "Relancer"})
        self.assertEqual(len(self.f.framing_specs), 1)  # aucune relance automatique
        self.click(dialog, "Relancer")
        self.assertEqual(self.enabled(dialog), {"Envoyer", "Clore maintenant"})

    def test_the_draft_replaces_the_editor_content(self) -> None:
        """Test 70 : la modale se ferme, le brouillon est dans l'éditeur existant."""
        view = self.view(QUESTION_OUT, READY_OUT, DRAFT_OUT)
        self.to_draft(view)
        self.assertFalse(self.dialogs[-1].winfo_exists())
        self.assertEqual(view._current_text(), DRAFT_OUT.removeprefix("IABINOME:DEMANDE\n"))


class TestCreation(GuiFramingCase):
    def test_create_only_promotes_the_reviewed_text(self) -> None:
        """Tests 42, 43, 71 : la correction faite dans l'éditeur précède la création."""
        view = self.view(QUESTION_OUT, READY_OUT, DRAFT_OUT)
        self.to_draft(view)
        root = self.controller.framing.root  # type: ignore[union-attr]
        view._demande_text.insert("end", _ADDED)
        with mock.patch("iabinome.gui.views.creation.messagebox.showinfo"):
            _find_button(view, "Créer seulement").invoke()
        self.assertIn(_ADDED.strip(), (self.collab / "demande.md").read_text(encoding="utf-8"))
        provenance = json.loads((self.collab / "cadrage" / "provenance.json").read_text("utf-8"))
        self.assertTrue(provenance["human_edited"])
        self.assertEqual(provenance["exchange_count"], 3)
        self.assertIsNone(self.controller.framing)
        self.assertFalse(root.exists())

    def test_an_invalid_edit_is_refused_before_creation(self) -> None:
        view = self.view(QUESTION_OUT, READY_OUT, DRAFT_OUT)
        self.to_draft(view)
        view._demande_text.delete("1.0", "end")
        view._demande_text.insert("1.0", "Plus une demande.")
        # Sans ce remplacement, une régression qui créerait quand même ouvrirait une vraie
        # boîte modale : le test resterait bloqué au lieu d'échouer (contre-épreuve du lot 5).
        with mock.patch("iabinome.gui.views.creation.messagebox.showinfo"):
            _find_button(view, "Créer seulement").invoke()
        self.assertIn("Brouillon refusé", view._error.cget("text"))
        self.assertFalse(self.collab.exists())
        self.assertIsNotNone(self.controller.framing)

    def test_create_and_start_confirms_and_closes_f_before_a(self) -> None:
        """Tests 46, 54 : confirmation distincte, et F fermé avant que A ne parte."""
        view = self.view(QUESTION_OUT, READY_OUT, DRAFT_OUT)
        self.to_draft(view)
        root = self.controller.framing.root  # type: ignore[union-attr]
        seen: dict[str, Any] = {}

        def start_run(path: Path, **_: Any) -> None:
            seen["framing"], seen["root"] = self.controller.framing, root.exists()

        with mock.patch("iabinome.gui.views.creation.dialogs.confirm", return_value=True) as ok, \
                mock.patch.object(self.controller, "start_run", side_effect=start_run):
            _find_button(view, "Créer et démarrer").invoke()
        self.assertIn("Vous avez relu le texte qui deviendra demande.md", ok.call_args.args[2])
        self.assertEqual(seen, {"framing": None, "root": False})

    def test_resuming_after_the_draft_keeps_the_session(self) -> None:
        """Test 45 : même session, nouveau groupe, nouveau brouillon."""
        view = self.view(QUESTION_OUT, READY_OUT, DRAFT_OUT, READY_OUT, DRAFT_OUT)
        self.to_draft(view)
        with mock.patch("iabinome.gui.dialogs.prompt_text",
                        return_value="Ajouter la durée de vie"):
            _find_button(_buttons(view._framing_panel), "Reprendre le cadrage").invoke()
        dialog = self.settle(self.dialogs[-1])
        self.click(dialog, "Clore maintenant")
        self.assertEqual(len(self.f.framing_sessions), 1)
        self.assertEqual(self.controller.framing.session.exchanges, 5)  # type: ignore[union-attr]


class TestOwnership(GuiFramingCase):
    def test_closing_the_modal_asks_then_discards(self) -> None:
        """Test 72, test 51 : fermer = annuler, confirmé ; rien de créé, dossier détruit."""
        dialog = self.start(self.view(QUESTION_OUT))
        root = self.controller.framing.root  # type: ignore[union-attr]
        with mock.patch("iabinome.gui.dialogs.confirm", return_value=False):
            dialog._cancel()
        self.assertTrue(root.exists())
        with mock.patch("iabinome.gui.dialogs.confirm", return_value=True):
            dialog._cancel()
        self.assertIsNone(self.controller.framing)
        self.assertFalse(root.exists())
        self.assertFalse(self.collab.exists())

    def test_cancelling_during_a_turn_waits_for_the_thread(self) -> None:
        self.f.sleep_seconds = 0.5
        view = self.view(QUESTION_OUT)
        _find_button(_buttons(view._framing_panel), "Commencer le cadrage").invoke()
        dialog = self.dialogs[-1]
        root = self.controller.framing.root  # type: ignore[union-attr]
        with mock.patch("iabinome.gui.dialogs.confirm", return_value=True):
            dialog._cancel()
        self.assertIsNotNone(self.controller.framing)  # jamais détruit sous le fil
        self.settle(dialog)
        self.assertIsNone(self.controller.framing)
        self.assertFalse(root.exists())

    def test_leaving_the_agent_mode_or_the_screen_discards(self) -> None:
        view = self.view(QUESTION_OUT, QUESTION_OUT)
        self.start(view)
        root = self.controller.framing.root  # type: ignore[union-attr]
        view._mode.set("saisir")
        view._on_mode()
        self.assertIsNone(self.controller.framing)
        self.assertFalse(root.exists())
        view._mode.set("agent")
        view._on_mode()
        self.start(view)
        root = self.controller.framing.root  # type: ignore[union-attr]
        self.controller.show_accueil()
        self.assertFalse(root.exists())


class TestOneEngineThread(GuiFramingCase):
    """Tests 66, 67 : un seul fil moteur, que F et A/B ne partagent jamais en même temps."""

    def busy(self) -> threading.Event:
        release = threading.Event()
        thread = threading.Thread(target=release.wait, daemon=True)
        thread.start()
        self.addCleanup(release.set)
        self.controller._run_thread = thread
        return release

    def test_framing_is_refused_while_the_thread_is_busy(self) -> None:
        self.busy()
        view = self.view(QUESTION_OUT)
        _find_button(_buttons(view._framing_panel), "Commencer le cadrage").invoke()
        self.assertIn("exécution est active", view._error.cget("text"))
        self.assertEqual(self.dialogs, [])
        self.assertEqual(self.f.framing_specs, [])
        self.assertFalse(self.controller.framing_step(lambda: None))  # type: ignore[arg-type,return-value]

    def test_a_run_is_refused_while_f_is_in_a_turn(self) -> None:
        self.f.sleep_seconds = 0.5
        view = self.view(QUESTION_OUT)
        _find_button(_buttons(view._framing_panel), "Commencer le cadrage").invoke()
        thread = self.controller._run_thread
        self.controller.start_run(self.root_dir / "autre", timeout_seconds=30.0)
        self.assertIs(self.controller._run_thread, thread)
        self.settle(self.dialogs[-1])


if __name__ == "__main__":
    unittest.main()

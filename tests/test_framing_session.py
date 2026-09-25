"""Tests de la session de F (`conception/CADRAGE_AGENT.md` §6.1, §5.2, §8 ; lot 1 de la
phase 6) : une session par cadrage, reprise par identifiant, jamais rouverte, prévol
avant tout appel, identifiant masqué, incidents jamais relancés tout seuls.

Faux agent seulement — de vrais sous-processus Python, jamais un fournisseur."""

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import mock

from iabinome import framing, transport
from iabinome.adapters.base import FramingSessionSpec, ObservedCli
from iabinome.adapters.claude import ClaudeAdapter
from iabinome.adapters.codex import CodexAdapter
from iabinome.framing import FramingError
from iabinome.models import AgentPurpose
from tests import fakes


class SessionCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.turn = 0

    def spec(self, *, timeout_seconds: float = 30.0) -> FramingSessionSpec:
        return FramingSessionSpec(
            model="fake-modele-framing", timeout_seconds=timeout_seconds, work_root=self.root,
        )

    def open(self, adapter: fakes.FakeAdapter, **kwargs: Any) -> framing.FramingSession:
        return framing.open_session(adapter, self.spec(**kwargs))

    def send(self, session: framing.FramingSession, prompt: str) -> framing.Exchange:
        self.turn += 1
        return session.send(prompt, self.root / "appels" / f"{self.turn:04d}")


class TestOneSessionPerFraming(SessionCase):
    def test_every_turn_reuses_the_single_session(self) -> None:
        """Tests 1 et 2 : un cadrage ouvre exactement une session ; tous ses tours la
        reprennent."""
        fake = fakes.FakeAdapter(framing_responses=("q1", "q2", "pret"))
        session = self.open(fake)
        for prompt in ("idee", "reponse 1", "reponse 2"):
            self.assertEqual(self.send(session, prompt).outcome, "COMPLETED")
        self.assertEqual(fake.framing_sessions, {
            "fake-session-1": ["idee", "reponse 1", "reponse 2"],
        })
        self.assertEqual(session.exchanges, 3)

    def test_two_framings_use_two_sessions(self) -> None:
        """Test 3 : rien n'est repris d'un cadrage antérieur."""
        fake = fakes.FakeAdapter()
        first, second = self.open(fake), self.open(fake)
        self.send(first, "idee A")
        self.send(second, "idee B")
        self.assertEqual(sorted(fake.framing_sessions), ["fake-session-1", "fake-session-2"])

    def test_the_session_remembers_across_turns(self) -> None:
        """Test 18 (côté session) : la réponse d'un tour antérieur reste disponible au
        suivant sans être retransmise — c'est l'outil qui la garde, pas le prompt."""
        fake = fakes.FakeAdapter(framing_responses=(
            "question", "pret", lambda history: "se souvient : " + history[1],
        ))
        session = self.open(fake)
        self.send(session, "idee")
        self.send(session, "Python seul")
        exchange = self.send(session, "redige")
        self.assertEqual(exchange.text, "se souvient : Python seul")
        self.assertNotIn("Python seul", (exchange.call_dir / "prompt.txt").read_text("utf-8"))

    def test_a_closed_session_is_never_resumed(self) -> None:
        """Test 4 : après `close`, plus aucun envoi — et aucun appel ne part."""
        fake = fakes.FakeAdapter()
        session = self.open(fake)
        self.send(session, "idee")
        session.close()
        with self.assertRaises(FramingError):
            self.send(session, "encore")
        self.assertEqual(fake.framing_sessions, {"fake-session-1": ["idee"]})
        self.assertFalse((self.root / "appels" / "0002").exists())

    def test_opening_costs_no_call(self) -> None:
        fake = fakes.FakeAdapter()
        self.open(fake)
        self.assertEqual(fake.framing_sessions, {})

    def test_the_turn_runs_in_the_session_work_root(self) -> None:
        """Test 5 (côté transport) : F tourne dans le dossier que la session reçoit."""
        fake = fakes.FakeAdapter()
        session = self.open(fake)
        with mock.patch.object(transport, "run", wraps=transport.run) as run:
            self.send(session, "idee")
        self.assertEqual(run.call_args.kwargs["cwd"], self.root)
        self.assertEqual(run.call_args.kwargs["stdin_text"], "idee")


class TestTraces(SessionCase):
    def test_each_turn_leaves_its_traces(self) -> None:
        """Test 47 : prompt, intention, flux, réponse et résultat de chaque échange."""
        session = self.open(fakes.FakeAdapter(framing_responses=("bonjour",)))
        exchange = self.send(session, "idee")
        names = {p.name for p in exchange.call_dir.iterdir()}
        self.assertLessEqual({
            "prompt.txt", "intention.json", "stdout.txt", "stderr.txt", "reponse_brute.txt",
            "resultat.json",
        }, names)
        self.assertEqual((exchange.call_dir / "reponse_brute.txt").read_text("utf-8"), "bonjour")

    def test_the_session_id_is_masked_and_the_executable_dropped(self) -> None:
        """§6.1, §9.2 : l'identifiant reste encapsulé ; aucun chemin absolu persisté."""
        session = self.open(fakes.FakeAdapter())
        first = self.send(session, "idee")
        second = self.send(session, "reponse")
        opened = json.loads((first.call_dir / "intention.json").read_text("utf-8"))
        resumed = json.loads((second.call_dir / "intention.json").read_text("utf-8"))
        self.assertEqual((opened["session"], resumed["session"]), ("neuve", "reprise"))
        self.assertEqual(resumed["purpose"], "FRAMING")
        self.assertEqual(resumed["exchange"], 2)
        text = (second.call_dir / "intention.json").read_text("utf-8")
        self.assertNotIn("fake-session-1", text)
        self.assertIn("<session>", text)
        self.assertNotIn(sys.executable.replace("\\", "\\\\"), text)

    def test_no_collaboration_state_is_created(self) -> None:
        """Test 48 (côté session) : ni `etat.json` ni `current_call`."""
        session = self.open(fakes.FakeAdapter())
        self.send(session, "idee")
        self.assertEqual(list(self.root.rglob("etat.json")), [])
        self.assertNotIn("current_call", (self.root / "appels" / "0001" / "intention.json")
                         .read_text("utf-8"))


class TestIncidents(SessionCase):
    def test_a_failed_turn_is_not_retried_and_the_session_stays_open(self) -> None:
        """§2.4 : aucune relance automatique ; l'humain relance dans la même session."""
        fake = fakes.FakeAdapter(framing_responses=("quota", "reprise"), exit_codes=(1, 0))
        session = self.open(fake)
        failed = self.send(session, "idee")
        self.assertEqual((failed.outcome, failed.text), ("CLI_FAILED", None))
        self.assertFalse((failed.call_dir / "reponse_brute.txt").exists())
        self.assertEqual(sum(len(h) for h in fake.framing_sessions.values()), 1)
        again = self.send(session, "idee")
        self.assertEqual((again.outcome, again.text), ("COMPLETED", "reprise"))

    def test_timeout_and_interruption_leave_no_result(self) -> None:
        fake = fakes.FakeAdapter(sleep_seconds=5.0)
        session = self.open(fake, timeout_seconds=0.5)
        exchange = self.send(session, "idee")
        self.assertEqual(exchange.outcome, "TIMEOUT")
        self.assertFalse((exchange.call_dir / "resultat.json").exists())
        control = transport.ExecutionControl()
        control.interrupt_requested.set()
        stopped = framing.open_session(fake, self.spec(), control=control)
        self.assertEqual(self.send(stopped, "idee").outcome, "INTERRUPTED_BY_USER")

    def test_an_answer_outside_the_session_closes_it(self) -> None:
        """Un outil qui répond hors de la session ouverte ne fait plus converser F avec
        le contexte qu'on lui croit : la session se ferme, la réponse reste lisible."""
        fake = fakes.FakeAdapter(framing_responses=("q1", "q2"))
        session = self.open(fake)
        self.send(session, "idee")
        fake.framing_drift = True
        lost = self.send(session, "reponse")
        self.assertEqual((lost.outcome, lost.text), ("SESSION_LOST", "q2"))
        self.assertTrue(session.closed)
        with self.assertRaises(FramingError):
            self.send(session, "encore")


class TestPreflight(SessionCase):
    def adapters(self, **kwargs: Any) -> dict[str, fakes.FakeAdapter]:
        return {"f": fakes.FakeAdapter("f", **kwargs)}

    def test_a_compatible_adapter_gets_its_framing_default(self) -> None:
        """Test 50 : `AgentPurpose.FRAMING` a un modèle par défaut chez le faux."""
        model, seen = framing.check_adapter("f", self.adapters(), None, None)
        self.assertEqual(model, "f-modele-framing")
        self.assertTrue(seen.present)
        model, _ = framing.check_adapter("f", self.adapters(), "autre", "high")
        self.assertEqual(model, "autre")

    def test_refusals_come_before_any_call(self) -> None:
        """Tests 8, 9 et 82 : sans lecture seule ou sans session persistante, refus avant
        l'ouverture — jamais simulé par des sessions éphémères."""
        cases: list[tuple[str, dict[str, Any], str | None, str | None]] = [
            ("lecture seule", {"enforces_read_only": False}, None, None),
            ("session persistante", {"supports_persistent_framing_session": False}, None, None),
            ("non remplaçable", {"supports_model_override": False}, "autre", None),
            ("effort", {}, None, "max"),
            ("CLI absente", {"present": False}, None, None),
        ]
        for needle, options, model, effort in cases:
            with self.subTest(needle):
                adapters = self.adapters(**options)
                with self.assertRaisesRegex(FramingError, needle):
                    framing.check_adapter("f", adapters, model, effort)
                self.assertEqual(adapters["f"].framing_sessions, {})
        with self.assertRaisesRegex(FramingError, "inconnu"):
            framing.check_adapter("absent", self.adapters(), None, None)

    def test_open_refuses_an_adapter_without_the_session(self) -> None:
        fake = fakes.FakeAdapter(supports_persistent_framing_session=False)
        with self.assertRaises(FramingError):
            self.open(fake)

    def test_real_adapters_pass_the_preflight_once_characterized(self) -> None:
        """Lot 4 : la capacité passe à vrai après le protocole du PO (2026-09-25), les
        quatre lignes conformes chez les deux outils. Le noyau ne nomme toujours aucun
        fournisseur : il lit la capacité et le défaut de l'adaptateur."""
        for adapter in (ClaudeAdapter(), CodexAdapter()):
            with self.subTest(adapter.adapter_id):
                with mock.patch.object(adapter, "probe", return_value=ObservedCli(True, "x")):
                    model, _ = framing.check_adapter(
                        adapter.adapter_id, {adapter.adapter_id: adapter}, None, None
                    )
                self.assertEqual(model, adapter.default_model(AgentPurpose.FRAMING))


if __name__ == "__main__":
    unittest.main()

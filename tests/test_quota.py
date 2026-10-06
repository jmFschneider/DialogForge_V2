"""Reprise après quota : continuer la même session après l'heure annoncée
(`conception/REPRISE_QUOTA_V3.md`).

Horloge contrôlée — `quota.now` et `quota.sleep` substitués — et faux agents : aucune
attente réelle, aucun appel fournisseur. Ce qui est prouvé : la continuation reprend
**la session de l'appel refusé** par une consigne, et le prompt d'origine n'est jamais
renvoyé dans une session neuve.
"""

from __future__ import annotations

import unittest
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta, tzinfo
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from iabinome import framing, quota, workflow
from iabinome.adapters.base import FramingSessionSpec
from iabinome.models import Phase, State, Status
from iabinome.transport import ExecutionControl
from tests import fakes

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."
_ACCEPT = fakes.review("ACCEPTER", findings=())
# Un libellé de fuseau inconnu partout : l'heure est lue en heure locale, sur toute machine.
_ZONE = "(Zone/Inconnue)"


def _local(hour: int, minute: int = 0, day: int = 5) -> datetime:
    return datetime(2026, 10, day, hour, minute).astimezone()


class _Clock:
    def __init__(self, start: datetime) -> None:
        self.at = start
        self.slept = 0.0
        self.on_sleep: list[ExecutionControl] = []

    def now(self) -> datetime:
        return self.at

    def sleep(self, seconds: float) -> None:
        self.at += timedelta(seconds=seconds)
        self.slept += seconds
        for control in self.on_sleep:
            control.pause_requested.set()


@contextmanager
def _clock(start: datetime) -> Iterator[_Clock]:
    clock = _Clock(start)
    with mock.patch.object(quota, "now", clock.now), mock.patch.object(quota, "sleep", clock.sleep):
        yield clock


class TestResumeAt(unittest.TestCase):
    def test_the_announced_hour_plus_two_minutes(self) -> None:
        received = _local(18, 0)
        for announced in (f"8:50pm {_ZONE}", "8:50 PM", "20:50", f"20:50 {_ZONE}"):
            with self.subTest(announced):
                self.assertEqual(quota.resume_at(announced, received), _local(20, 52))
        self.assertEqual(quota.resume_at("9pm", received), _local(21, 2))
        self.assertEqual(quota.resume_at("12:10am", received), _local(0, 12, day=6))

    def test_a_past_hour_is_tomorrow_unless_it_has_just_passed(self) -> None:
        self.assertEqual(quota.resume_at("1:00am", _local(23, 0)), _local(1, 2, day=6))
        self.assertEqual(quota.resume_at("8:50pm", _local(20, 53)), _local(20, 52))
        self.assertEqual(quota.resume_at("8:50pm", _local(20, 56)), _local(20, 52, day=6))

    def test_a_named_zone_is_used_when_known(self) -> None:
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo("UTC")
        except Exception:  # pragma: no cover - Windows sans base de fuseaux
            self.skipTest("base de fuseaux absente")
        received = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)
        self.assertEqual(
            quota.resume_at("1:00pm (UTC)", received),
            datetime(2026, 10, 5, 13, 2, tzinfo=UTC),
        )

    def test_an_illegible_hour_is_refused(self) -> None:
        for announced in ("demain", "", "13:00pm", "25:00", "8", "Oct 8, 9pm"):
            with self.subTest(announced), self.assertRaises(quota.QuotaError):
                quota.resume_at(announced, _local(12))

    def test_an_hour_inside_a_clock_change_is_refused(self) -> None:
        with mock.patch.object(quota, "_zone", return_value=_Shifting()):
            with self.assertRaises(quota.QuotaError):
                quota.resume_at("2:30am (Zone/Bascule)", datetime(2026, 10, 25, 0, 0, tzinfo=UTC))


class _Shifting(tzinfo):
    """Un fuseau dont 02:00–03:00 se répète le 2026-10-25, comme en Europe."""

    def utcoffset(self, dt: datetime | None) -> timedelta:
        if dt is not None and dt.date() == datetime(2026, 10, 25).date() and dt.hour == 2:
            return timedelta(hours=1 if dt.fold else 2)
        return timedelta(hours=1)

    def dst(self, dt: datetime | None) -> timedelta:
        return timedelta(0)

    def tzname(self, dt: datetime | None) -> str:
        return "Bascule"


class TestWaitUntil(unittest.TestCase):
    def test_waits_until_the_target(self) -> None:
        with _clock(_local(20, 0)) as clock:
            self.assertTrue(quota.wait_until(_local(20, 10), None))
        self.assertEqual(clock.now(), _local(20, 10))

    def test_pause_and_stop_interrupt_the_wait(self) -> None:
        for flag in ("pause_requested", "interrupt_requested"):
            control = ExecutionControl()
            with self.subTest(flag), _clock(_local(20, 0)) as clock:
                getattr(control, flag).set()
                self.assertFalse(quota.wait_until(_local(22, 0), control))
                self.assertEqual(clock.slept, 0.0)


class QuotaCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.messages: list[str] = []

    def build(self, a: tuple[str, ...], exit_codes: tuple[int, ...]) -> Path:
        self.a = fakes.FakeAdapter("fake-a", a, exit_codes=exit_codes)
        self.b = fakes.FakeAdapter("fake-b", (_ACCEPT,))
        return fakes.collaboration(self.root)

    def run_engine(self, collab: Path, control: ExecutionControl | None = None) -> State:
        return workflow.run(
            collab, adapters={"fake-a": self.a, "fake-b": self.b}, timeout_seconds=30.0,
            control=control, notify=self.messages.append,
        )

    def calls(self, collab: Path) -> list[Path]:
        return sorted((collab / "appels").iterdir())


class TestContinuation(QuotaCase):
    def test_refusal_then_the_same_session_continues(self) -> None:
        collab = self.build((fakes.quota_refusal(f"8:50pm {_ZONE}"), _DOC), (1, 0))
        with _clock(_local(20, 0)) as clock:
            state = self.run_engine(collab)
        self.assertIs(state.status, Status.AWAITING_APPROVAL)
        self.assertIs(state.phase, Phase.CLOSED)
        self.assertEqual(clock.now(), _local(20, 52))
        first, second = self.a.specs
        self.assertFalse(first.resume)
        self.assertTrue(second.resume)
        self.assertEqual(second.session_id, first.session_id)
        # La consigne, jamais le prompt d'origine renvoyé dans une session neuve.
        self.assertEqual(second.prompt, quota.CONTINUATION)
        self.assertEqual(self.a.prompts[1], quota.CONTINUATION)
        refused, continued, _review = self.calls(collab)
        incident = fakes.read_json(refused / "incident.json")
        self.assertEqual(incident["kind"], "QUOTA")
        self.assertEqual(incident["session_id"], first.session_id)
        self.assertEqual(incident["announced"], f"8:50pm {_ZONE}")
        intention = fakes.read_json(continued / "intention.json")
        self.assertEqual(intention["session"], "continuation")
        self.assertEqual(intention["session_id"], first.session_id)
        refused_id = fakes.read_json(refused / "intention.json")["call_id"]
        self.assertEqual(intention["retries"], refused_id)
        self.assertTrue(intention["retry_reason"].startswith("quota"))
        self.assertEqual((continued / "prompt.txt").read_text(encoding="utf-8"), quota.CONTINUATION)
        self.assertEqual(len(self.messages), 1)
        self.assertIn("20:52", self.messages[0])

    def test_a_reviewer_refusal_continues_the_reviewer_session(self) -> None:
        collab = self.build((_DOC,), (0,))
        self.b = fakes.FakeAdapter(
            "fake-b", (fakes.quota_refusal("20:50"), _ACCEPT), exit_codes=(1, 0)
        )
        with _clock(_local(20, 0)):
            state = self.run_engine(collab)
        self.assertIs(state.status, Status.AWAITING_APPROVAL)
        self.assertEqual(self.b.specs[1].session_id, self.b.specs[0].session_id)
        self.assertEqual(self.b.prompts[1], quota.CONTINUATION)

    def test_a_later_refusal_is_awaited_again(self) -> None:
        collab = self.build(
            (fakes.quota_refusal("8:50pm"), fakes.quota_refusal("10:00pm"), _DOC), (1, 1, 0)
        )
        with _clock(_local(20, 0)) as clock:
            state = self.run_engine(collab)
        self.assertIs(state.status, Status.AWAITING_APPROVAL)
        self.assertEqual(clock.now(), _local(22, 2))
        sessions = {spec.session_id for spec in self.a.specs}
        self.assertEqual(len(sessions), 1)


class TestNoContinuation(QuotaCase):
    def assert_stopped(
        self, state: State, collab: Path, calls: int, words: str
    ) -> dict[str, object]:
        self.assertIs(state.status, Status.INTERRUPTED)
        self.assertEqual(self.a.calls, calls)
        incident = fakes.read_json(collab / str(state.last_incident))
        self.assertIn(words, incident["detail"])
        return incident  # type: ignore[no-any-return]

    def test_an_unknown_session_stops_without_a_new_call(self) -> None:
        collab = self.build((fakes.quota_refusal("8:50pm"),), (1,))
        self.a.declared_sessions = [None]
        with _clock(_local(20, 0)) as clock:
            state = self.run_engine(collab)
        self.assert_stopped(state, collab, 1, "session de l'appel inconnue")
        self.assertEqual(clock.slept, 0.0)

    def test_a_replaced_session_is_not_accepted(self) -> None:
        collab = self.build((fakes.quota_refusal("8:50pm"), _DOC), (1, 0))
        self.a.declared_sessions = ["s-1", "s-2"]
        with _clock(_local(20, 0)):
            state = self.run_engine(collab)
        incident = fakes.read_json(collab / str(state.last_incident))
        self.assertIs(state.status, Status.INTERRUPTED)
        self.assertEqual(incident["kind"], "SESSION_LOST")
        self.assertEqual(self.a.specs[1].session_id, "s-1")

    def test_a_missing_session_on_continuation_stops_and_keeps_the_message(self) -> None:
        """Décision du PO (2026-10-05) : session introuvable → arrêt, message conservé."""
        missing = "No conversation found with session ID: 11-sess"
        collab = self.build((fakes.quota_refusal("8:50pm"), missing), (1, 1))
        with _clock(_local(20, 0)):
            state = self.run_engine(collab)
        incident = self.assert_stopped(state, collab, 2, "code de retour 1")
        self.assertEqual(incident["kind"], "CLI_FAILED")
        continued = collab / str(state.last_incident).rsplit("/", 1)[0]
        self.assertEqual((continued / "stdout.txt").read_text(encoding="utf-8"), missing)

    def test_pause_during_the_wait_stops_before_the_continuation(self) -> None:
        collab = self.build((fakes.quota_refusal("8:50pm"),), (1,))
        control = ExecutionControl()
        with _clock(_local(20, 0)) as clock:
            clock.on_sleep.append(control)
            state = self.run_engine(collab, control)
        incident = self.assert_stopped(state, collab, 1, "continuation de la session prévue")
        self.assertEqual(incident["kind"], "QUOTA")

    def test_an_illegible_hour_stops_without_waiting(self) -> None:
        collab = self.build((fakes.quota_refusal("bientôt"),), (1,))
        with _clock(_local(20, 0)) as clock:
            state = self.run_engine(collab)
        self.assert_stopped(state, collab, 1, "aucune continuation")
        self.assertEqual(clock.slept, 0.0)

    def test_the_same_hour_again_stops(self) -> None:
        collab = self.build((fakes.quota_refusal("8:50pm"), fakes.quota_refusal("8:50pm")), (1, 1))
        with _clock(_local(20, 0)):
            state = self.run_engine(collab)
        self.assert_stopped(state, collab, 2, "sans heure plus tardive")

    def test_another_error_with_the_same_exit_code_is_not_a_quota(self) -> None:
        collab = self.build(("model not found: opus-9",), (1,))
        with _clock(_local(20, 0)) as clock:
            state = self.run_engine(collab)
        self.assert_stopped(state, collab, 1, "code de retour 1")
        self.assertEqual(clock.slept, 0.0)
        self.assertEqual(self.messages, [])

    def test_a_normal_answer_speaking_of_quota_is_an_answer(self) -> None:
        collab = self.build((f"{_DOC}\n{fakes.quota_refusal('8:50pm')}",), (0,))
        with _clock(_local(20, 0)) as clock:
            state = self.run_engine(collab)
        self.assertIs(state.status, Status.AWAITING_APPROVAL)
        self.assertEqual(clock.slept, 0.0)


class TestFramingContinuation(unittest.TestCase):
    """Le cadrage : le tour refusé continue dans la même session F, même au premier tour."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def open(
        self, fake: fakes.FakeAdapter, control: ExecutionControl | None = None
    ) -> framing.FramingSession:
        spec = FramingSessionSpec(model="fake", timeout_seconds=30.0, work_root=self.root)
        return framing.open_session(fake, spec, control=control)

    def test_a_first_turn_refusal_continues_the_session(self) -> None:
        fake = fakes.FakeAdapter(
            framing_responses=(fakes.quota_refusal("8:50pm"), "pret"), exit_codes=(1, 0)
        )
        session = self.open(fake)
        self.assertIsNotNone(session.spec.session_id)  # imposé dès le premier tour
        with _clock(_local(20, 0)) as clock:
            exchange = session.send("idee", self.root / "appels" / "0001")
        self.assertEqual(exchange.outcome, "COMPLETED")
        self.assertEqual(exchange.text, "pret")
        self.assertEqual(clock.now(), _local(20, 52))
        self.assertEqual(fake.framing_sessions, {"fake-session-1": ["idee", quota.CONTINUATION]})
        incident = fakes.read_json(self.root / "appels" / "0001" / "incident.json")
        self.assertEqual(incident["kind"], "QUOTA")
        self.assertNotIn("session_id", incident)  # l'identifiant reste masqué (§6.1)
        self.assertEqual(session.exchanges, 2)

    def test_pause_during_the_wait_stops_the_turn(self) -> None:
        fake = fakes.FakeAdapter(
            framing_responses=(fakes.quota_refusal("8:50pm"),), exit_codes=(1,)
        )
        control = ExecutionControl()
        session = self.open(fake, control)
        with _clock(_local(20, 0)) as clock:
            clock.on_sleep.append(control)
            exchange = session.send("idee", self.root / "appels" / "0001")
        self.assertEqual(exchange.outcome, "QUOTA")
        self.assertEqual(session.exchanges, 1)

    def test_another_failure_is_not_continued(self) -> None:
        fake = fakes.FakeAdapter(framing_responses=("model not found",), exit_codes=(1,))
        with _clock(_local(20, 0)) as clock:
            exchange = self.open(fake).send("idee", self.root / "appels" / "0001")
        self.assertEqual(exchange.outcome, "CLI_FAILED")
        self.assertEqual(clock.slept, 0.0)


if __name__ == "__main__":
    unittest.main()

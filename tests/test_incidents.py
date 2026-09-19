"""Tests du lot 2, point 2.1 : appels, interruptions, récupération.

Validation du plan : **fenêtres de crash, compteur de lancements du faux
fournisseur, double lancement, récupération d'une réponse mal présentée. Aucune
relance ambiguë automatique.**

Trois choses à ne pas confondre : une réponse **reçue mais mal interprétée**
(payée, sur disque, réinterprétable localement), un appel **qui n'est pas parti**
(rien de payé), et une **issue inconnue** (qui a pu être payée). Et rien n'est
jamais présenté comme un coût ou une heure de reprise que les données ne portent pas.
"""

from __future__ import annotations

import _thread
import hashlib
import io
import json
import os
import threading
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from iabinome import cli, contracts, incidents, transport, workflow
from iabinome.adapters.base import CallSpec
from iabinome.models import State
from tests import fakes
from tests.test_cli import CliCase
from tests.test_objections import review_v2
from tests.test_workflow import WorkflowCase

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."


class _Stop(RuntimeError):
    """Arrêt injecté — simule la mort du processus."""


class _Absent(fakes.FakeAdapter):
    """Un outil dont l'exécutable a disparu : `Popen` échoue, l'appel n'est pas parti."""

    def command(self, call: CallSpec) -> list[str]:
        super().command(call)
        return [str(Path("Z:/") / "introuvable" / "outil.exe")]


class _FlakyDecode(fakes.FakeAdapter):
    """Une extraction qui échoue une fois (octets illisibles), puis réussit."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]
        self.decoded = 0

    def extract(self, stdout: bytes, stderr: bytes) -> str:
        self.decoded += 1
        if self.decoded == 1:
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "octets illisibles (test)")
        return super().extract(stdout, stderr)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class IncidentCase(WorkflowCase):
    def state(self, collab: Path) -> State:
        return State.from_dict(fakes.read_json(collab / "etat.json"))

    def explained(self, collab: Path) -> str:
        return "\n".join(incidents.explain(collab, self.state(collab)))

    def reason(self, text: str = "Lecture corrigée.") -> Path:
        path = self.root / "motif.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def call_id(self, collab: Path) -> str:
        current = self.state(collab).current_call
        assert current is not None
        return current.call_id

    def reprocess(self, collab: Path, call_id: str | None = None, reason: Path | None = None
                  ) -> State:
        return workflow.run(
            collab, adapters=self.adapters, timeout_seconds=30.0, command_label="resume",
            intervention=workflow.Reprocess(call_id or self.call_id(collab),
                                            reason or self.reason()),
        )

    def launched(self, collab: Path) -> int:
        return fakes.launched_calls(collab)


class TestWhatWasReceivedWhatWasNotLaunchedWhatIsUnknown(IncidentCase):
    def test_a_call_that_did_not_start_is_said_to_be_unpaid(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        self.adapters["fake-a"] = self.a = _Absent("fake-a", ())
        self.run_engine(collab)
        text = self.explained(collab)
        self.assertIn("LAUNCH_FAILED", text)
        self.assertIn("Payé ? : non", text)
        self.assertIn("n'est pas parti", text)
        self.assertIn("rien n'a été payé", incidents.action(collab, self.state(collab)))
        self.assertEqual(self.launched(collab), 0)

    def test_a_timeout_may_have_been_paid_and_no_amount_is_invented(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        self.a.sleep_seconds = 5.0
        workflow.run(collab, adapters=self.adapters, timeout_seconds=0.05)
        text = self.explained(collab)
        self.assertIn("Payé ? : peut-être", text)
        self.assertIn("a pu être payé", incidents.action(collab, self.state(collab)))
        self.assertNotRegex(text, r"[€$]|euros?|tokens?\b")

    def test_a_crash_during_a_call_is_unknown_and_never_replayed(self) -> None:
        """Fenêtre de crash : `CALLING` est publié, le processus meurt avant que
        l'outil ne réponde. Rien ne dit s'il est parti."""
        collab = self.build(a=(_DOC,), b=())
        with mock.patch.object(transport, "run", side_effect=_Stop("mort du processus")):
            with self.assertRaises(_Stop):
                self.run_engine(collab)
        before = (self.a.calls, self.launched(collab))
        self.run_engine(collab)  # la reprise **constate**, elle ne rejoue pas
        self.assertEqual((self.a.calls, self.launched(collab)), before, "un appel a été rejoué")
        text = self.explained(collab)
        self.assertIn("CALL_POSSIBLY_PAID", text)
        self.assertIn("Payé ? : inconnu", text)
        self.assertIn("impossible de savoir", text)

    def test_a_non_zero_exit_shows_the_tools_words_and_deduces_nothing(self) -> None:
        collab = self.build(a=("Limite d'usage atteinte. Réessayez à 14h.",), b=())
        self.a.exit_codes = [1]
        self.run_engine(collab)
        lines = incidents.explain(collab, self.state(collab))
        text = "\n".join(lines)
        self.assertIn("CLI_FAILED", text)
        self.assertIn("Payé ? : inconnu", text)
        self.assertIn("ne distingue pas un quota épuisé d'une erreur de configuration", text)
        self.assertIn("stdout de l'outil : « Limite d'usage atteinte. Réessayez à 14h. »", text)
        self.assertIn("Aucun coût ni aucune heure de reprise n'est déduit", text)
        # « 14h » n'apparaît que dans la citation de l'outil, jamais dans ce que dit le programme.
        program = [ln for ln in lines if "de l'outil" not in ln]
        self.assertNotIn("14h", "\n".join(program))

    def test_a_refused_answer_was_received_and_paid_and_offers_the_local_way_first(self) -> None:
        collab = self.build(a=("Bonjour, voici mon document.",), b=())
        self.run_engine(collab)
        text = self.explained(collab)
        self.assertIn("CONTRACT_ERROR", text)
        self.assertIn("Payé ? : oui", text)
        action = incidents.action(collab, self.state(collab))
        self.assertLess(action.index("--reprocess"), action.index("--retry-call"))
        self.assertIn("sans appel", action)

    def test_a_tool_with_no_output_says_so(self) -> None:
        collab = self.build(a=("",), b=())
        self.a.exit_codes = [1]
        self.run_engine(collab)
        self.assertIn("l'outil n'a rien écrit", self.explained(collab))

    def test_a_kind_the_catalogue_does_not_know_is_not_dressed_up(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        self.a.exit_codes = [1]
        self.run_engine(collab)
        state = self.state(collab)
        incident_path = collab / str(state.last_incident)
        data = json.loads(incident_path.read_text(encoding="utf-8"))
        data["kind"] = "GENRE_INCONNU"
        incident_path.write_text(json.dumps(data), encoding="utf-8")
        self.assertIn(
            "Payé ? : inconnu (incident d'un genre non catalogué)", self.explained(collab)
        )


class TestTheLocalReprocessing(IncidentCase):
    """Relire une réponse déjà payée ne doit pas coûter un appel de plus."""

    def decode_failure(self) -> Path:
        collab = self.build(a=(_DOC,), b=(review_v2("ACCEPTER"),))
        self.adapters["fake-a"] = self.a = _FlakyDecode("fake-a", (_DOC,))
        self.run_engine(collab)
        self.assertEqual(self.state(collab).status.value, "ERROR")
        return collab

    def contract_failure(self) -> Path:
        """Une lecture refusée hier, que le programme accepte aujourd'hui."""
        collab = self.build(a=(_DOC,), b=(review_v2("ACCEPTER"),))
        real = contracts.parse_agent_response
        calls = {"n": 0}

        def refuse_once(text: str) -> contracts.AgentResponse:
            calls["n"] += 1
            if calls["n"] == 1:
                raise contracts.ContractError("lecture trop stricte (test)")
            return real(text)

        with mock.patch.object(contracts, "parse_agent_response", refuse_once):
            self.run_engine(collab)
        self.assertEqual(self.state(collab).status.value, "ERROR")
        return collab

    def test_an_undecodable_answer_is_reread_locally_without_a_new_call(self) -> None:
        collab = self.decode_failure()
        self.assertEqual((self.a.calls, self.launched(collab)), (1, 1))
        state = self.reprocess(collab)
        self.assertEqual(state.status.value, "AWAITING_APPROVAL")
        self.assertEqual(self.a.calls, 1, "un appel de A a été repayé")
        self.assertEqual(self.b.calls, 1)

    def test_a_refused_answer_is_reread_locally_once_the_reading_is_fixed(self) -> None:
        collab = self.contract_failure()
        call_dir = collab / self.state(collab).current_call.call_dir  # type: ignore[union-attr]
        raw_before = sha(call_dir / "reponse_brute.txt")
        state = self.reprocess(collab)
        self.assertEqual(state.status.value, "AWAITING_APPROVAL")
        self.assertEqual(self.a.calls, 1, "un appel de A a été repayé")
        self.assertEqual(
            sha(call_dir / "reponse_brute.txt"), raw_before, "la réponse brute a changé"
        )

    def test_the_operation_is_traced_and_the_raw_data_are_untouched(self) -> None:
        collab = self.decode_failure()
        call_dir = collab / self.state(collab).current_call.call_dir  # type: ignore[union-attr]
        streams = (sha(call_dir / "stdout.txt"), sha(call_dir / "stderr.txt"))
        self.reprocess(collab, reason=self.reason("Extraction corrigée."))
        (entry,) = [
            json.loads(line)
            for line in (call_dir / "retraitements.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(entry["reason"], "Extraction corrigée.")
        self.assertEqual(entry["incident"], "DECODE_FAILED")
        self.assertRegex(entry["at"], r"^\d{4}-\d{2}-\d{2}T")
        self.assertEqual((sha(call_dir / "stdout.txt"), sha(call_dir / "stderr.txt")), streams)

    def test_a_reprocessing_that_still_fails_stays_an_error_and_is_traced_each_time(self) -> None:
        collab = self.build(a=("Bonjour, voici mon document.",), b=())
        self.run_engine(collab)
        call_dir = collab / self.state(collab).current_call.call_dir  # type: ignore[union-attr]
        for _ in range(2):
            state = self.reprocess(collab)
            self.assertEqual(state.status.value, "ERROR", "un échec devient un avis favorable")
        lines = (call_dir / "retraitements.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(self.a.calls, 1, "un appel a été payé pour retraiter")

    def test_only_an_interpretation_error_can_be_reprocessed(self) -> None:
        collab = self.build(a=(_DOC,), b=())
        self.a.sleep_seconds = 5.0
        workflow.run(collab, adapters=self.adapters, timeout_seconds=0.05)
        self.assertEqual(self.state(collab).status.value, "INTERRUPTED")
        before = (collab / "etat.json").read_bytes()
        with self.assertRaises(workflow.WorkflowError) as refused:
            self.reprocess(collab)
        self.assertIn("aucun appel en erreur", str(refused.exception))
        self.assertEqual((collab / "etat.json").read_bytes(), before)

    def test_a_wrong_call_id_or_an_empty_reason_is_refused_before_any_change(self) -> None:
        collab = self.decode_failure()
        before = (collab / "etat.json").read_bytes()
        with self.assertRaisesRegex(workflow.WorkflowError, "aucun appel en erreur"):
            self.reprocess(collab, call_id="pas-le-bon")
        with self.assertRaisesRegex(workflow.WorkflowError, "motif"):
            self.reprocess(collab, reason=self.reason("   \n"))
        self.assertEqual((collab / "etat.json").read_bytes(), before)
        self.assertEqual(self.a.calls, 1)

    def test_an_altered_raw_answer_is_not_reprocessed(self) -> None:
        collab = self.contract_failure()
        call_dir = collab / self.state(collab).current_call.call_dir  # type: ignore[union-attr]
        (call_dir / "reponse_brute.txt").write_text("autre chose", encoding="utf-8")
        state = self.reprocess(collab)
        self.assertEqual(state.status.value, "INTERRUPTED")
        self.assertEqual(json.loads(
            (collab / str(state.last_incident)).read_text(encoding="utf-8"))["kind"],
            "INTEGRITY_MISMATCH")

    def test_a_stop_during_the_reprocessing_is_finished_by_a_plain_run(self) -> None:
        collab = self.contract_failure()
        with mock.patch.object(workflow._Engine, "apply", side_effect=_Stop("arret injecte")):
            with self.assertRaises(_Stop):
                self.reprocess(collab)
        self.assertEqual(self.state(collab).status.value, "RUNNING")
        final = self.run_engine(collab)
        self.assertEqual(final.status.value, "AWAITING_APPROVAL")  # type: ignore[attr-defined]
        self.assertEqual(self.a.calls, 1, "la reprise a rejoué un appel")


class TestAnAnswerBadlyPresentedIsRecovered(IncidentCase):
    def test_b_wrapped_in_prose_a_fence_a_bom_and_crlf_costs_no_second_call(self) -> None:
        body = review_v2("ACCEPTER").replace("\n", "\r\n")
        wrapped = f"\ufeffJe réponds en JSON comme demandé :\r\n```json\r\n{body}\r\n```\r\nFin."
        collab = self.build(a=(_DOC,), b=(wrapped,))
        state = self.run_engine(collab)
        self.assertEqual(state.status.value, "AWAITING_APPROVAL")  # type: ignore[attr-defined]
        self.assertEqual((self.a.calls, self.b.calls), (1, 1))

    def test_a_with_a_bom_and_crlf_is_accepted_without_a_second_call(self) -> None:
        collab = self.build(
            a=("\ufeffIABINOME:DOCUMENT\r\n# Proposition\r\nCorps.",), b=(review_v2("ACCEPTER"),)
        )
        state = self.run_engine(collab)
        self.assertEqual(state.status.value, "AWAITING_APPROVAL")  # type: ignore[attr-defined]
        self.assertEqual(self.a.calls, 1)

    def test_a_preamble_before_the_tag_stays_refused_and_is_never_read_as_agreement(self) -> None:
        """Règle mesurée du 2026-09-04 : sans balise en première ligne, un préfixe est
        un refus. La réponse brute reste, l'humain décide."""
        collab = self.build(a=("Voici mon document :\nIABINOME:DOCUMENT\n# Titre",), b=())
        state = self.run_engine(collab)
        self.assertEqual(state.status.value, "ERROR")  # type: ignore[attr-defined]
        call_dir = next((collab / "appels").iterdir())
        self.assertIn("Voici mon document", (call_dir / "reponse_brute.txt").read_text("utf-8"))
        self.assertEqual(self.b.calls, 0)


class TestPauseAtTheCallBoundary(IncidentCase):
    def test_a_pause_stops_between_two_calls_and_a_plain_run_resumes_there(self) -> None:
        collab = self.build(a=(_DOC,), b=(review_v2("ACCEPTER"),))
        state = workflow.run(
            collab, adapters=self.adapters, timeout_seconds=30.0, pause=lambda: True
        )
        self.assertEqual(state.status.value, "READY")
        self.assertEqual(
            (self.a.calls, self.b.calls), (1, 0), "la pause n'a pas eu lieu à la frontière"
        )
        self.assertEqual(self.state(collab).phase.value, "REVIEW_B")
        final = self.run_engine(collab)
        self.assertEqual(final.status.value, "AWAITING_APPROVAL")  # type: ignore[attr-defined]
        self.assertEqual((self.a.calls, self.b.calls), (1, 1), "un appel a été rejoué")

    def test_the_pause_is_only_consulted_between_calls(self) -> None:
        seen: list[tuple[int, int]] = []
        collab = self.build(a=(_DOC,), b=(review_v2("ACCEPTER"),))

        def pause() -> bool:
            seen.append((self.a.calls, self.b.calls))
            return False

        workflow.run(collab, adapters=self.adapters, timeout_seconds=30.0, pause=pause)
        self.assertEqual(seen, [(1, 0)], "consultée hors de la frontière d'un appel")

    def test_no_pause_means_the_cycle_runs_through(self) -> None:
        collab = self.build(a=(_DOC,), b=(review_v2("ACCEPTER"),))
        state = self.run_engine(collab)
        self.assertEqual(state.status.value, "AWAITING_APPROVAL")  # type: ignore[attr-defined]


class TestCtrlCInTwoSteps(CliCase):
    def test_the_first_signal_asks_for_a_pause_the_second_stops_at_once(self) -> None:
        switch = cli._PauseSwitch()
        self.assertFalse(switch())
        with redirect_stderr(io.StringIO()) as err:
            switch.on_signal(2, None)
        self.assertTrue(switch())
        self.assertIn("pause demandée", err.getvalue())
        self.assertIn("Ctrl+C encore = arrêt immédiat", err.getvalue())
        self.assertIn("pourra avoir été payé", err.getvalue())
        with self.assertRaises(KeyboardInterrupt):
            switch.on_signal(2, None)

    def new(self) -> None:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["new", *self.new_args()]), 0)

    def test_a_pause_from_the_command_line_is_exit_6_and_says_nothing_is_lost(self) -> None:
        self.new()
        self.a.responses = [_DOC]
        self.b.responses = [review_v2("ACCEPTER")]

        class _AlreadyAsked(cli._PauseSwitch):
            def __init__(self) -> None:
                super().__init__()
                self.requested = True

        with mock.patch.object(cli, "_PauseSwitch", _AlreadyAsked):
            with redirect_stdout(io.StringIO()) as out:
                code = cli.main(["run", str(self.collab)])
        self.assertEqual(code, 6)
        self.assertIn("pause : le cycle s'est arrêté à la frontière d'appel", out.getvalue())
        self.assertIn("rien n'est perdu", out.getvalue())
        self.assertIn("prochaine action : lancer `run", out.getvalue())
        self.assertEqual((self.a.calls, self.b.calls), (1, 0))

    def test_a_real_ctrl_c_pair_pauses_then_stops_the_running_call_and_says_the_consequence(
        self,
    ) -> None:
        """Deux `interrupt_main` — ce que fait Ctrl+C — pendant un appel réel : le
        premier ne coupe rien, le second interrompt l'appel en cours."""
        self.new()
        self.a.sleep_seconds = 30.0
        self.a.responses = [_DOC]
        first = threading.Timer(0.6, _thread.interrupt_main)
        second = threading.Timer(1.2, _thread.interrupt_main)
        first.start()
        second.start()
        self.addCleanup(first.cancel)
        self.addCleanup(second.cancel)
        with redirect_stdout(io.StringIO()) as out, redirect_stderr(io.StringIO()) as err:
            code = cli.main(["run", str(self.collab), "--timeout", "60"])
        self.assertEqual(code, 3)
        self.assertIn("pause demandée", err.getvalue())
        self.assertIn("INTERRUPTED", out.getvalue())
        self.assertIn("a pu être payé", out.getvalue())
        self.assertIn("aucun rejeu automatique", out.getvalue())
        state = State.from_dict(fakes.read_json(self.collab / "etat.json"))
        incident = json.loads((self.collab / str(state.last_incident)).read_text("utf-8"))
        self.assertEqual(incident["kind"], "INTERRUPTED_BY_USER")


class TestTheLockIsNeverCleanedAutomatically(CliCase):
    def test_a_live_holder_blocks_run_and_the_lock_is_left_as_it_was(self) -> None:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            cli.main(["new", *self.new_args()])
        lock_file = self.collab / "verrou.json"
        fakes.write_json(lock_file, {
            "lock_id": "0" * 32, "pid": os.getpid(),
            "acquired_at": "2026-09-19T00:00:00Z", "command": "run",
        })
        before = lock_file.read_bytes()
        with redirect_stderr(io.StringIO()) as err, redirect_stdout(io.StringIO()):
            code = cli.main(["run", str(self.collab)])
        self.assertEqual(code, 1)
        self.assertIn(str(os.getpid()), err.getvalue())
        self.assertEqual(lock_file.read_bytes(), before, "le verrou d'un détenteur vivant a bougé")
        self.assertEqual((self.a.calls, self.b.calls), (0, 0), "un appel a été payé sous verrou")

    def test_an_ambiguous_lock_is_refused_and_says_what_to_do_by_hand(self) -> None:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            cli.main(["new", *self.new_args()])
        (self.collab / "verrou.json").write_text("{ pas du json", encoding="utf-8")
        with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
            code = cli.main(["run", str(self.collab)])
        self.assertEqual(code, 1)
        self.assertTrue((self.collab / "verrou.json").exists(), "un verrou ambigu a été effacé")
        self.assertEqual((self.a.calls, self.b.calls), (0, 0))


class TestReprocessFromTheCommandLine(CliCase):
    def test_reprocess_and_retry_are_exclusive_and_need_their_reason(self) -> None:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            cli.main(["new", *self.new_args()])
        reason = self.root / "motif.txt"
        reason.write_text("x", encoding="utf-8")
        for argv, expected in (
            (["--reprocess", "u", "--retry-call", "u", "--reason-file", str(reason)], "s'excluent"),
            (["--reprocess", "u"], "--reason-file"),
            (["--reason-file", str(reason)], "--reason-file"),
            (["--answer", str(reason), "--reprocess", "u", "--reason-file", str(reason)],
             "incompatible"),
        ):
            with self.subTest(argv=argv):
                with redirect_stderr(io.StringIO()) as err, redirect_stdout(io.StringIO()):
                    code = cli.main(["resume", str(self.collab), *argv])
                self.assertEqual(code, 1)
                self.assertIn(expected, err.getvalue())

    def test_a_refused_answer_is_reread_from_the_command_line_and_the_next_action_shows_how(
        self,
    ) -> None:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            cli.main(["new", *self.new_args()])
        real = contracts.parse_agent_response
        calls = {"n": 0}

        def refuse_once(text: str) -> contracts.AgentResponse:
            calls["n"] += 1
            if calls["n"] == 1:
                raise contracts.ContractError("lecture trop stricte (test)")
            return real(text)

        self.a.responses = [_DOC]
        self.b.responses = [review_v2("ACCEPTER")]
        with mock.patch.object(contracts, "parse_agent_response", refuse_once):
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(cli.main(["run", str(self.collab)]), 4)
        self.assertIn("--reprocess", out.getvalue())
        state = State.from_dict(fakes.read_json(self.collab / "etat.json"))
        assert state.current_call is not None
        reason = self.root / "motif.txt"
        reason.write_text("La lecture a été corrigée.", encoding="utf-8")
        with redirect_stdout(io.StringIO()) as out2:
            code = cli.main(["resume", str(self.collab), "--reprocess",
                             state.current_call.call_id, "--reason-file", str(reason)])
        self.assertEqual(code, 0, out2.getvalue())
        self.assertEqual(self.a.calls, 1, "un appel de A a été repayé")

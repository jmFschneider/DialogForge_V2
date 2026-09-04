"""Tests du lot 2 : porte d'état, et intervention humaine sous le verrou.

Deux garanties, indissociables parce que la seconde conditionne la première :

1. **Porte d'état** — le cycle ne repart que de `READY` sans appel courant ou
   de `RUNNING` avec appel courant. Le statut est lu, jamais déduit de la seule
   présence de `current_call` ; sans cela, un second `run` en `WAITING_HUMAN`
   repartait en **appel payant**, porte humaine contournée (C-01).
2. **Intervention sous verrou** — `--answer` et `--retry-call` ne mutent plus
   rien depuis `cli.py` : le moteur les applique après la relecture, avant la
   porte (C-02 volet A, D-4). D'où leur rejouabilité après un arrêt brutal.

Le cas accepté `RUNNING` **avec** appel courant est la reprise de `test_recovery`
tout entière : la porte ne la ferme pas, et un test le redit ici.

`FakeAdapter.calls` est la preuve dans chaque refus : la porte doit tomber
**avant** l'appel, pas après.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import mock

from iabinome import lock, storage, workflow
from iabinome.models import Status
from tests import fakes

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."
_FINAL = "IABINOME:DOCUMENT\n# Final\nCorps final."
_QUESTION = "IABINOME:QUESTION\nQuel est le critere de fin ?"
_HORS_CONTRAT = "Bonjour, voici mon document."

# Capturée avant tout correctif : `_StopAfter` la rappelle, sans quoi il
# s'appellerait lui-même.
_WRITE = storage.write_atomic_text


class _Stop(RuntimeError):
    """Arrêt injecté — simule la mort du processus entre deux publications."""


class _StopAfter:
    """Laisse passer `n` écritures atomiques, puis interrompt la suivante."""

    def __init__(self, n: int) -> None:
        self.remaining = n

    def __call__(self, path: Path, text: str) -> None:
        if self.remaining == 0:
            raise _Stop(f"arret injecte avant {path.name}")
        self.remaining -= 1
        _WRITE(path, text)


class InterventionCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.a = fakes.FakeAdapter("fake-a", ())
        self.b = fakes.FakeAdapter("fake-b", ())
        self.adapters = {"fake-a": self.a, "fake-b": self.b}
        self.collab = fakes.collaboration(self.root)

    def drive(self, **kwargs: Any) -> Status:
        state = workflow.run(
            self.collab, adapters=self.adapters, timeout_seconds=30.0, **kwargs
        )
        return state.status

    def etat(self) -> dict[str, Any]:
        raw = fakes.read_json(self.collab / "etat.json")
        assert isinstance(raw, dict)
        return raw

    def answer_file(self, text: str = "Le critere de fin est la couverture complete.") -> Path:
        path = self.root / "reponse.md"
        path.write_text(text, encoding="utf-8")
        return path

    def reason_file(self, text: str = "quota epuise, credits recharges") -> Path:
        path = self.root / "motif.txt"
        path.write_text(text, encoding="utf-8")
        return path

    def archives(self) -> list[str]:
        return sorted(p.name for p in self.collab.glob("demande.md.*"))

    def refused(self, **kwargs: Any) -> str:
        """Le refus est rendu **avant** l'appel : `calls` ne doit pas bouger.

        Le compteur est vérifié **avant** l'exception attendue, et non dans un
        `assertRaises` : sans cela, une porte absente ferait échouer le test sur
        « exception non levée » et masquerait le défaut qu'il cherche — l'appel
        payant parti (`RULES.md`).
        """
        before = (self.a.calls, self.b.calls)
        message = ""
        try:
            self.drive(**kwargs)
        except workflow.WorkflowError as exc:
            message = str(exc)
        self.assertEqual((self.a.calls, self.b.calls), before, "un appel a ete paye")
        self.assertNotEqual(message, "", "aucun refus : la porte d'etat a laisse passer")
        return message


class TestStateGate(InterventionCase):
    def test_a_second_run_after_a_question_never_calls_again(self) -> None:
        """Le cas grave : sans porte, ce second `run` repartait en appel payant
        alors que la collaboration attendait une réponse humaine."""
        self.a.responses = [_QUESTION]
        self.assertIs(self.drive(), Status.WAITING_HUMAN)
        self.assertEqual(self.a.calls, 1)
        message = self.refused()
        self.assertIn("WAITING_HUMAN", message)
        self.assertIn("resume --answer", message)
        self.assertEqual(self.etat()["status"], "WAITING_HUMAN")

    def test_a_second_run_after_bloque_never_calls_again(self) -> None:
        self.a.responses = [_DOC]
        self.b.responses = [fakes.review("BLOQUE")]
        self.assertIs(self.drive(), Status.WAITING_HUMAN)
        self.assertIn("WAITING_HUMAN", self.refused())

    def test_a_second_run_after_an_error_names_the_way_out(self) -> None:
        self.a.responses = [_HORS_CONTRAT]
        self.assertIs(self.drive(), Status.ERROR)
        message = self.refused()
        self.assertIn("ERROR", message)
        self.assertIn("--retry-call", message)

    def test_a_second_run_after_awaiting_approval_is_refused_not_a_keyerror(self) -> None:
        """Avant le lot 2, la phase `CLOSED` sortait en `KeyError` — un défaut
        du programme, pas un refus lisible par l'humain."""
        self.a.responses = [_DOC, _FINAL]
        self.b.responses = [fakes.review("ACCEPTER", findings=())]
        self.assertIs(self.drive(), Status.AWAITING_APPROVAL)
        message = self.refused()
        self.assertIn("AWAITING_APPROVAL", message)
        self.assertIn("terme", message)

    def test_a_second_run_after_an_interruption_never_replays_by_itself(self) -> None:
        self.a.sleep_seconds = 5.0
        state = workflow.run(self.collab, adapters=self.adapters, timeout_seconds=0.05)
        self.assertIs(state.status, Status.INTERRUPTED)
        self.assertIn("--retry-call", self.refused())

    def test_running_with_a_current_call_still_resumes(self) -> None:
        """Non-régression §5 : le cas accepté de la porte est bien celui que la
        table de reprise emprunte — retraitement local, aucun appel repayé."""
        self.a.responses = [_HORS_CONTRAT]
        self.assertIs(self.drive(), Status.ERROR)
        etat = self.etat()
        etat["status"] = "RUNNING"
        fakes.write_json(self.collab / "etat.json", etat)
        self.assertIs(self.drive(), Status.ERROR)
        self.assertEqual(self.a.calls, 1, "la reprise a repaye un appel")


class TestAnswerUnderLock(InterventionCase):
    def question(self) -> None:
        self.a.responses = [_QUESTION, _QUESTION]
        self.assertIs(self.drive(), Status.WAITING_HUMAN)

    def test_a_held_lock_leaves_demande_and_etat_untouched(self) -> None:
        """C-02 volet A : `cli.py` mutait `demande.md` et `etat.json` **avant**
        le verrou. Un détenteur vivant doit désormais tout arrêter avant."""
        self.question()
        fakes.write_json(self.collab / "verrou.json", {
            "lock_id": "0" * 32, "pid": os.getpid(),
            "acquired_at": "2026-09-04T00:00:00Z", "command": "une autre commande",
        })
        demande = (self.collab / "demande.md").read_bytes()
        etat = (self.collab / "etat.json").read_bytes()
        with self.assertRaises(lock.LockError):
            self.drive(command_label="resume", intervention=workflow.Answer(self.answer_file()))
        self.assertEqual((self.collab / "demande.md").read_bytes(), demande)
        self.assertEqual((self.collab / "etat.json").read_bytes(), etat)
        self.assertEqual(self.archives(), [])

    def test_the_answer_becomes_the_demande_and_the_cycle_goes_on(self) -> None:
        self.question()
        self.assertIs(
            self.drive(command_label="resume", intervention=workflow.Answer(self.answer_file())),
            Status.WAITING_HUMAN,
        )
        self.assertEqual(self.archives(), ["demande.md.001"])
        self.assertIn(
            "couverture complete", (self.collab / "demande.md").read_text(encoding="utf-8")
        )
        self.assertEqual(self.a.calls, 2)

    def test_an_answer_on_a_collaboration_that_waits_for_nobody_is_refused(self) -> None:
        self.a.responses = [_QUESTION]
        self.assertIs(self.drive(), Status.WAITING_HUMAN)
        self.drive(command_label="resume", intervention=workflow.Answer(self.answer_file()))
        message = self.refused(
            command_label="resume", intervention=workflow.Answer(self.answer_file("Autre chose."))
        )
        self.assertIn("n'attend pas", message)
        self.assertEqual(self.archives(), ["demande.md.001"])


class TestAnswerIsReplayable(InterventionCase):
    """Arrêt injecté après chacune des trois écritures de `--answer`.

    L'ordre — archive par **copie**, `demande.md`, puis `etat.json` — est ce qui
    rend le rejeu possible : `demande.md` n'est jamais absent, et aucune des
    trois interruptions ne laisse la collaboration inexploitable.
    """

    def question(self) -> None:
        self.a.responses = [_QUESTION, _QUESTION]
        self.assertIs(self.drive(), Status.WAITING_HUMAN)

    def stop_after(self, n: int) -> Path:
        answer = self.answer_file()
        with mock.patch.object(storage, "write_atomic_text", _StopAfter(n)):
            with self.assertRaises(_Stop):
                self.drive(command_label="resume", intervention=workflow.Answer(answer))
        return answer

    def test_stopped_after_the_archive_the_replay_does_not_archive_twice(self) -> None:
        self.question()
        answer = self.stop_after(1)
        self.assertEqual(self.archives(), ["demande.md.001"])
        self.assertEqual(self.etat()["status"], "WAITING_HUMAN")
        self.assertIs(
            self.drive(command_label="resume", intervention=workflow.Answer(answer)),
            Status.WAITING_HUMAN,
        )
        self.assertEqual(self.archives(), ["demande.md.001"])
        self.assertEqual(self.a.calls, 2)

    def test_stopped_after_the_demande_the_replay_only_publishes_the_state(self) -> None:
        """L'unique cas particulier reconnu : l'état dit encore `WAITING_HUMAN`
        avec l'ancienne empreinte, `demande.md` porte déjà celle de la réponse.
        Le contrôle d'intégrité du prévol doit le laisser passer, sans quoi la
        reprise serait refusée avant d'avoir pu réparer."""
        self.question()
        answer = self.stop_after(2)
        self.assertEqual(
            (self.collab / "demande.md").read_text(encoding="utf-8"),
            answer.read_text(encoding="utf-8"),
        )
        self.assertEqual(self.etat()["status"], "WAITING_HUMAN")
        self.assertIs(
            self.drive(command_label="resume", intervention=workflow.Answer(answer)),
            Status.WAITING_HUMAN,
        )
        self.assertEqual(self.archives(), ["demande.md.001"])
        self.assertEqual(self.a.calls, 2)

    def test_stopped_after_the_state_the_intervention_is_already_applied(self) -> None:
        """La troisième écriture close l'intervention : il n'y a plus rien à
        rejouer, et `resume` seul enchaîne le cycle. Rejouer `--answer` est un
        refus explicite, jamais une seconde archive."""
        self.question()
        answer = self.stop_after(3)
        etat = self.etat()
        self.assertEqual(etat["status"], "READY")
        self.assertEqual(self.a.calls, 1, "un appel est parti malgre l'arret")
        self.assertIn("n'attend pas", self.refused(
            command_label="resume", intervention=workflow.Answer(answer)
        ))
        self.assertIs(self.drive(command_label="resume"), Status.WAITING_HUMAN)
        self.assertEqual(self.archives(), ["demande.md.001"])
        self.assertEqual(self.a.calls, 2)


class TestRetryUnderLock(InterventionCase):
    def interrupted(self) -> str:
        """Un appel parti sans réponse : `INTERRUPTED`, sans rejeu automatique."""
        self.a.sleep_seconds = 5.0
        state = workflow.run(self.collab, adapters=self.adapters, timeout_seconds=0.05)
        self.assertIs(state.status, Status.INTERRUPTED)
        self.a.sleep_seconds = 0.0
        self.a.responses = [_QUESTION]
        call_id = self.etat()["current_call"]["call_id"]
        assert isinstance(call_id, str)
        return call_id

    def error(self) -> str:
        self.a.responses = [_HORS_CONTRAT, _QUESTION]
        self.assertIs(self.drive(), Status.ERROR)
        call_id = self.etat()["current_call"]["call_id"]
        assert isinstance(call_id, str)
        return call_id

    def retry(self, call_id: str, **kwargs: Any) -> workflow.RetryCall:
        return workflow.RetryCall(call_id, self.reason_file(**kwargs))

    def test_a_held_lock_leaves_the_state_untouched(self) -> None:
        call_id = self.interrupted()
        etat = (self.collab / "etat.json").read_bytes()
        fakes.write_json(self.collab / "verrou.json", {
            "lock_id": "0" * 32, "pid": os.getpid(),
            "acquired_at": "2026-09-04T00:00:00Z", "command": "une autre commande",
        })
        with self.assertRaises(lock.LockError):
            self.drive(command_label="resume", intervention=self.retry(call_id))
        self.assertEqual((self.collab / "etat.json").read_bytes(), etat)

    def test_a_stop_before_the_intention_leaves_the_interruption_replayable(self) -> None:
        """Aucun état intermédiaire n'est publié : entre la validation et
        `intention.json`, un arrêt laisse l'`INTERRUPTED` d'origine intact, et
        le lien vers l'appel relancé n'est pas perdable."""
        call_id = self.interrupted()
        etat = (self.collab / "etat.json").read_bytes()
        with mock.patch.object(storage, "write_atomic_text", _StopAfter(0)):
            with self.assertRaises(_Stop):
                self.drive(command_label="resume", intervention=self.retry(call_id))
        self.assertEqual((self.collab / "etat.json").read_bytes(), etat)
        self.assertIs(
            self.drive(command_label="resume", intervention=self.retry(call_id)),
            Status.WAITING_HUMAN,
        )

    def test_an_unknown_call_id_is_refused(self) -> None:
        self.interrupted()
        self.assertIn("aucun appel courant", self.refused(
            command_label="resume", intervention=self.retry("un-identifiant-inconnu")
        ))

    def test_an_empty_reason_is_refused(self) -> None:
        call_id = self.interrupted()
        self.assertIn("motif", self.refused(
            command_label="resume", intervention=self.retry(call_id, text="   \n")
        ))

    def test_a_contract_error_is_relaunchable(self) -> None:
        """N-01 : `ERROR` sort par relance, mais seulement pour les incidents de
        la table fermée — ici `CONTRACT_ERROR`."""
        call_id = self.error()
        self.assertIs(
            self.drive(command_label="resume", intervention=self.retry(call_id)),
            Status.WAITING_HUMAN,
        )
        self.assertEqual(self.a.calls, 2)
        new_dir = next(
            p for p in (self.collab / "appels").iterdir() if not p.name.endswith(call_id)
        )
        intention = fakes.read_json(new_dir / "intention.json")
        self.assertEqual(intention["retries"], call_id)
        self.assertEqual(intention["retry_reason"], "quota epuise, credits recharges")

    def test_an_incident_outside_the_closed_table_is_not_relaunchable(self) -> None:
        """La sortie de `ERROR` n'est jamais héritée du statut : une famille
        d'incident absente de la table doit y être ajoutée explicitement."""
        call_id = self.error()
        incident = self.collab / str(self.etat()["last_incident"])
        raw = fakes.read_json(incident)
        raw["kind"] = "UNE_AUTRE_FAMILLE"
        fakes.write_json(incident, raw)
        self.assertIn("aucun appel relançable", self.refused(
            command_label="resume", intervention=self.retry(call_id)
        ))


if __name__ == "__main__":
    unittest.main()

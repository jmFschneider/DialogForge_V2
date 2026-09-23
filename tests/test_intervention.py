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
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import mock

from iabinome import contracts, demande, lock, storage, workflow
from iabinome.models import Status
from tests import fakes

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."
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
        self.a.responses = [_DOC]
        self.b.responses = [fakes.review("ACCEPTER", findings=())]
        self.assertIs(self.drive(), Status.AWAITING_APPROVAL)
        message = self.refused()
        self.assertIn("AWAITING_APPROVAL", message)
        # La sortie nommée vient des actions permises (GUI V1, lot 1) : décider.
        self.assertIn("decide <dossier> --accept", message)

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
    """Arrêt injecté après chacune des quatre écritures de `--answer`.

    L'ordre — archive par **copie**, `demande.md`, provenance, puis `etat.json` —
    est ce qui rend le rejeu possible : `demande.md` n'est jamais absent, et
    aucune des quatre interruptions ne laisse la collaboration inexploitable.
    La provenance (lot 1, point 1.1) s'est glissée avant l'état : elle ne se
    rejoue qu'une fois, quel que soit l'endroit de l'arrêt.
    """

    def versions(self) -> list[dict[str, Any]]:
        raw = fakes.read_json(self.collab / "provenance_demande.json")
        assert isinstance(raw, dict)
        versions: list[dict[str, Any]] = raw["versions"]
        return versions

    def assert_one_version_recorded(self, answer: Path) -> None:
        """Une seule version consignée, et c'est bien la bonne : la réponse, qui
        remplace la demande d'origine archivée en `demande.md.001`."""
        (only,) = self.versions()
        self.assertEqual(only["source"], "reponse")
        self.assertEqual(only["path"], str(answer.resolve()))
        self.assertEqual(only["archive"], "demande.md.001")
        self.assertEqual(only["phase"], "PROPOSAL_A")
        self.assertNotEqual(only["replaces"], only["sha256"])

    def question(self) -> None:
        # Trois réponses pour deux appels attendus : l'arrêt injecté après la
        # troisième écriture tombe entre la résolution de la commande et le
        # lancement, et une résolution consomme une réponse scriptée
        # (`fakes.FakeAdapter`). Les réponses en trop ne servent jamais.
        self.a.responses = [_QUESTION, _QUESTION, _QUESTION]
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
        self.assert_one_version_recorded(answer)

    def test_stopped_after_the_demande_the_replay_only_publishes_the_state(self) -> None:
        """L'unique cas particulier reconnu : l'état dit encore `WAITING_HUMAN`
        avec l'ancienne empreinte, `demande.md` porte déjà celle de la demande
        **complétée**. Le contrôle d'intégrité du prévol doit le laisser passer,
        sans quoi la reprise serait refusée avant d'avoir pu réparer."""
        self.question()
        answer = self.stop_after(2)
        original = (self.collab / "demande.md.001").read_text(encoding="utf-8")
        self.assertEqual(
            (self.collab / "demande.md").read_text(encoding="utf-8"),
            demande.complete(original, answer.read_text(encoding="utf-8")),
        )
        self.assertEqual(self.etat()["status"], "WAITING_HUMAN")
        self.assertIs(
            self.drive(command_label="resume", intervention=workflow.Answer(answer)),
            Status.WAITING_HUMAN,
        )
        self.assertEqual(self.archives(), ["demande.md.001"])
        self.assertEqual(self.a.calls, 2)
        self.assert_one_version_recorded(answer)

    def test_stopped_after_the_provenance_the_replay_does_not_record_twice(self) -> None:
        self.question()
        answer = self.stop_after(3)
        self.assert_one_version_recorded(answer)
        self.assertEqual(self.etat()["status"], "WAITING_HUMAN")
        self.assertIs(
            self.drive(command_label="resume", intervention=workflow.Answer(answer)),
            Status.WAITING_HUMAN,
        )
        self.assertEqual(self.archives(), ["demande.md.001"])
        self.assert_one_version_recorded(answer)

    def test_stopped_after_the_state_the_intervention_is_already_applied(self) -> None:
        """La quatrième écriture close l'intervention : il n'y a plus rien à
        rejouer, et `resume` seul enchaîne le cycle. Rejouer `--answer` est un
        refus explicite, jamais une seconde archive."""
        self.question()
        answer = self.stop_after(4)
        etat = self.etat()
        self.assertEqual(etat["status"], "READY")
        # Mesure sur le disque, pas sur le compteur de résolutions : l'arrêt
        # tombe désormais après la résolution de la commande et avant le
        # lancement, donc `calls` compterait un appel jamais parti.
        self.assertEqual(fakes.launched_calls(self.collab), 1, "un appel est parti malgre l'arret")
        self.assertIn("n'attend pas", self.refused(
            command_label="resume", intervention=workflow.Answer(answer)
        ))
        self.assertIs(self.drive(command_label="resume"), Status.WAITING_HUMAN)
        self.assertEqual(self.archives(), ["demande.md.001"])
        self.assertEqual(fakes.launched_calls(self.collab), 2)


class TestAnswerKeepsTheDemande(InterventionCase):
    """Lot 1, point 1.1 : `--answer` **complète** la demande, il ne la remplace pas.

    Objectif, livrable, sources, contraintes, non-objectifs et critères de fin
    existants doivent survivre à une réponse courte — sur le chemin nominal,
    après un arrêt brutal à chacune des quatre écritures, et après un incident
    suivi d'une reprise. `demande.md` reste l'unique autorité : une version
    complète, dont l'ancienne est archivée et la provenance consignée.
    """

    SHORT = "Le critere de fin est la couverture complete."

    def setUp(self) -> None:
        super().setUp()
        fakes.collaboration(self.root, demande=fakes.DEMANDE_COMPLETE)

    def question(self) -> None:
        self.a.responses = [_QUESTION, _QUESTION, _QUESTION]
        self.assertIs(self.drive(), Status.WAITING_HUMAN)

    def answer(self) -> workflow.Answer:
        return workflow.Answer(self.answer_file(self.SHORT))

    def stop_after(self, writes: int, answer: workflow.Answer) -> Path:
        """Arrêt injecté après `writes` écritures atomiques de `--answer`."""
        with mock.patch.object(storage, "write_atomic_text", _StopAfter(writes)):
            with self.assertRaises(_Stop):
                self.drive(command_label="resume", intervention=answer)
        return answer.path

    def assert_nothing_lost(self) -> None:
        text = (self.collab / "demande.md").read_text(encoding="utf-8")
        original = demande.sections(fakes.DEMANDE_COMPLETE)
        found = demande.sections(text)
        self.assertEqual(sorted(original), sorted(demande.SECTIONS), "la base est complète")
        for name, body in original.items():
            self.assertEqual(found[name], body, f"« {name} » a change")
        self.assertTrue(text.startswith(fakes.DEMANDE_COMPLETE.rstrip()))
        self.assertIn("## Précisions n°1", text)
        self.assertEqual(
            (self.collab / "demande.md.001").read_text(encoding="utf-8"), fakes.DEMANDE_COMPLETE
        )
        self.assertEqual(self.etat()["demande_sha256"], contracts.normalize(text).sha256)

    def test_a_short_answer_leaves_every_existing_section_and_reaches_the_agent(self) -> None:
        self.question()
        self.drive(command_label="resume", intervention=self.answer())
        self.assert_nothing_lost()
        for name, body in demande.sections(fakes.DEMANDE_COMPLETE).items():
            self.assertIn(body, self.a.prompts[1], name)
        self.assertIn("couverture complete", self.a.prompts[1])

    def test_a_stop_at_each_of_the_four_writes_still_keeps_every_section(self) -> None:
        """Chaque arrêt est une reprise **distincte** : la demande complétée doit
        se recalculer à l'identique — depuis `demande.md`, ou depuis son archive
        quand il est déjà complété — sans quoi l'empreinte ne serait plus reconnue."""
        for stop in (1, 2, 3, 4):
            with self.subTest(stopped_after_write=stop):
                self.tearDown_collaboration()
                self.question()
                answer = self.stop_after(stop, self.answer())
                if stop < 4:
                    self.assertIs(
                        self.drive(command_label="resume", intervention=workflow.Answer(answer)),
                        Status.WAITING_HUMAN,
                    )
                else:
                    self.assertIs(self.drive(command_label="resume"), Status.WAITING_HUMAN)
                self.assert_nothing_lost()
                self.assertEqual(self.archives(), ["demande.md.001"])

    def test_an_interrupted_call_then_a_retry_still_keeps_every_section(self) -> None:
        self.question()
        self.a.sleep_seconds = 5.0
        state = workflow.run(
            self.collab, adapters=self.adapters, timeout_seconds=0.05,
            command_label="resume", intervention=self.answer(),
        )
        self.assertIs(state.status, Status.INTERRUPTED)
        self.assert_nothing_lost()
        self.a.sleep_seconds = 0.0
        self.a.responses = [_QUESTION, _QUESTION]
        call_id = self.etat()["current_call"]["call_id"]
        state = workflow.run(
            self.collab, adapters=self.adapters, timeout_seconds=30.0, command_label="resume",
            intervention=workflow.RetryCall(call_id, self.reason_file()),
        )
        self.assertIs(state.status, Status.WAITING_HUMAN)
        self.assert_nothing_lost()

    def test_a_contract_error_then_a_retry_still_keeps_every_section(self) -> None:
        self.question()
        self.a.responses = [_HORS_CONTRAT, _DOC]
        self.assertIs(
            self.drive(command_label="resume", intervention=self.answer()), Status.ERROR
        )
        self.assert_nothing_lost()
        call_id = self.etat()["current_call"]["call_id"]
        self.b.responses = [fakes.review("ACCEPTER", findings=())]
        self.assertIs(
            self.drive(
                command_label="resume",
                intervention=workflow.RetryCall(call_id, self.reason_file()),
            ),
            Status.AWAITING_APPROVAL,
        )
        self.assert_nothing_lost()

    def test_a_second_answer_after_an_incident_adds_and_removes_nothing(self) -> None:
        """Deux réponses, un incident entre les deux : les précisions s'empilent,
        chaque ancienne version reste archivée, la provenance les enchaîne."""
        self.question()
        self.a.sleep_seconds = 5.0
        workflow.run(
            self.collab, adapters=self.adapters, timeout_seconds=0.05,
            command_label="resume", intervention=self.answer(),
        )
        self.a.sleep_seconds = 0.0
        self.a.responses = [_QUESTION]
        call_id = self.etat()["current_call"]["call_id"]
        workflow.run(
            self.collab, adapters=self.adapters, timeout_seconds=30.0, command_label="resume",
            intervention=workflow.RetryCall(call_id, self.reason_file()),
        )
        self.assertEqual(self.etat()["status"], "WAITING_HUMAN")
        self.a.responses = [_DOC]
        self.b.responses = [fakes.review("ACCEPTER", findings=())]
        second = self.answer_file("Une seconde precision.")
        self.assertIs(
            self.drive(command_label="resume", intervention=workflow.Answer(second)),
            Status.AWAITING_APPROVAL,
        )
        text = (self.collab / "demande.md").read_text(encoding="utf-8")
        self.assertIn("## Précisions n°1", text)
        self.assertIn("## Précisions n°2\n\nUne seconde precision.", text)
        self.assertEqual(self.archives(), ["demande.md.001", "demande.md.002"])
        for name, body in demande.sections(fakes.DEMANDE_COMPLETE).items():
            self.assertEqual(demande.sections(text)[name], body, name)
        first_version, second_version = demande.read(self.collab)
        self.assertEqual(second_version["replaces"], first_version["sha256"])
        # La version archivée en dernier est bien la précédente, prolongée telle quelle.
        previous = (self.collab / "demande.md.002").read_text(encoding="utf-8")
        self.assertTrue(text.startswith(previous.rstrip()))

    def tearDown_collaboration(self) -> None:
        """Repart d'une collaboration neuve **au même endroit** entre deux sous-tests."""
        for path in self.collab.iterdir():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        fakes.collaboration(self.root, demande=fakes.DEMANDE_COMPLETE)
        self.a.responses, self.b.responses = [], []


class TestRetryUnderLock(InterventionCase):
    def interrupted(self) -> str:
        """Un appel parti sans réponse : `INTERRUPTED`, sans rejeu automatique."""
        self.a.sleep_seconds = 5.0
        state = workflow.run(self.collab, adapters=self.adapters, timeout_seconds=0.05)
        self.assertIs(state.status, Status.INTERRUPTED)
        self.a.sleep_seconds = 0.0
        # Deux réponses pour un seul appel attendu : une résolution de commande
        # en consomme une même quand l'arrêt injecté empêche le lancement.
        # Artefact du faux agent, pas du moteur (`fakes.FakeAdapter`).
        self.a.responses = [_QUESTION, _QUESTION]
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

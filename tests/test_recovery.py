"""Tests de la reprise après crash — CONCEPTION_FINALE.md §5.

Le point qui compte : **un `resultat.json` valide prouve que les flux sont
complets**, donc la reprise retraite localement et ne repaie pas l'appel. Le
compteur `FakeAdapter.calls` en est la preuve dans chaque cas.
"""

import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from iabinome import transport, workflow
from iabinome.models import Status
from tests import fakes

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."


class RecoveryCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.a = fakes.FakeAdapter("fake-a", ())
        self.b = fakes.FakeAdapter("fake-b", (fakes.review("BLOQUE"),))
        self.adapters = {"fake-a": self.a, "fake-b": self.b}
        self.collab = fakes.collaboration(self.root)

    def crash_mid_call(self, *, response: str | None, result: bool) -> Path:
        """Fabrique sur le disque l'état exact laissé par un crash en `CALLING`.

        `response` non nul écrit `reponse_brute.txt` et passe en
        `RESPONSE_STORED` ; `result` écrit un `resultat.json` valide.
        """
        rel = "appels/0001-A-abcdef"
        call_dir = self.collab / rel
        call_dir.mkdir(parents=True)
        (call_dir / "stdout.txt").write_bytes(_DOC.encode("utf-8"))
        (call_dir / "stderr.txt").write_bytes(b"")
        (call_dir / "prompt.txt").write_text("prompt", encoding="utf-8")
        if result:
            fakes.write_json(call_dir / "resultat.json", {
                "schema_version": 1, "return_code": 0,
                "stdout_bytes": len(_DOC.encode("utf-8")),
                "stdout_sha256": "0" * 64, "stderr_bytes": 0, "stderr_sha256": "0" * 64,
                "duration_seconds": 1.0,
            })
        if response is not None:
            (call_dir / "reponse_brute.txt").write_text(response, encoding="utf-8")
        etat = fakes.read_json(self.collab / "etat.json")
        etat["status"] = "RUNNING"
        etat["current_call"] = {
            "call_id": "abcdef", "sequence": 1, "role": "A", "phase": "PROPOSAL_A",
            "status": "RESPONSE_STORED" if response is not None else "CALLING",
            "call_dir": rel, "prompt_sha256": "0" * 64,
            "response_sha256": "0" * 64 if response is not None else None,
            "started_at": "2026-09-03T00:00:00Z",
            "completed_at": "2026-09-03T00:00:01Z" if response is not None else None,
        }
        fakes.write_json(self.collab / "etat.json", etat)
        return call_dir

    def resume(self) -> Status:
        state = workflow.run(
            self.collab, adapters=self.adapters, timeout_seconds=30.0, command_label="resume"
        )
        return state.status


class TestRecoveryTable(RecoveryCase):
    def test_response_stored_is_reprocessed_locally_without_a_call(self) -> None:
        self.crash_mid_call(response=_DOC, result=True)
        self.assertIs(self.resume(), Status.WAITING_HUMAN)  # B rend BLOQUE
        self.assertEqual(self.a.calls, 0, "A a ete rappele alors que sa reponse etait la")
        self.assertTrue((self.collab / "echanges" / "0001-proposition-A.md").exists())

    def test_calling_with_a_valid_result_is_reprocessed_without_a_call(self) -> None:
        """Le cas le plus grave de la revue technique : sans cette lecture, une
        réponse complète serait déclarée incertaine et l'appel repayé."""
        self.crash_mid_call(response=None, result=True)
        self.assertIs(self.resume(), Status.WAITING_HUMAN)
        self.assertEqual(self.a.calls, 0, "un appel deja paye a ete relance")
        call_dir = self.collab / "appels" / "0001-A-abcdef"
        self.assertEqual(
            (call_dir / "reponse_brute.txt").read_text(encoding="utf-8"), _DOC
        )

    def test_calling_without_a_result_is_interrupted_and_never_replayed(self) -> None:
        self.crash_mid_call(response=None, result=False)
        self.assertIs(self.resume(), Status.INTERRUPTED)
        self.assertEqual(self.a.calls, 0)
        etat = fakes.read_json(self.collab / "etat.json")
        self.assertIsNotNone(etat["current_call"])
        incident = fakes.read_json(self.collab / str(etat["last_incident"]))
        self.assertEqual(incident["kind"], "CALL_POSSIBLY_PAID")

    def test_non_zero_return_code_found_on_resume_is_cli_failed(self) -> None:
        """D-2 : le retraitement local applique aussi le test du code de retour,
        avant de tenter l'extraction (CONCEPTION_FINALE.md Sec5)."""
        call_dir = self.crash_mid_call(response=None, result=True)
        raw = fakes.read_json(call_dir / "resultat.json")
        raw["return_code"] = 1
        fakes.write_json(call_dir / "resultat.json", raw)
        self.assertIs(self.resume(), Status.INTERRUPTED)
        self.assertEqual(self.a.calls, 0)
        etat = fakes.read_json(self.collab / "etat.json")
        incident = fakes.read_json(self.collab / str(etat["last_incident"]))
        self.assertEqual(incident["kind"], "CLI_FAILED")

    def test_an_invalid_result_is_not_a_proof_of_completeness(self) -> None:
        call_dir = self.crash_mid_call(response=None, result=True)
        raw = fakes.read_json(call_dir / "resultat.json")
        raw["schema_version"] = 2
        fakes.write_json(call_dir / "resultat.json", raw)
        self.assertIsNone(transport.read_result(call_dir))
        self.assertIs(self.resume(), Status.INTERRUPTED)
        self.assertEqual(self.a.calls, 0)


class TestRetry(RecoveryCase):
    def test_retry_gets_a_new_uuid_and_carries_the_reason(self) -> None:
        self.crash_mid_call(response=None, result=False)
        self.resume()  # laisse l'appel en INTERRUPTED
        # La relance humaine remet l'état en phase **sous le verrou** : rien
        # n'est publié entre la validation et `intention.json`.
        reason = self.root / "motif.txt"
        reason.write_text("quota epuise, credits recharges\n", encoding="utf-8")
        self.a.responses = [_DOC]
        state = workflow.run(
            self.collab, adapters=self.adapters, timeout_seconds=30.0,
            command_label="resume",
            intervention=workflow.RetryCall("abcdef", reason),
        )
        self.assertIs(state.status, Status.WAITING_HUMAN)
        self.assertEqual(self.a.calls, 1)
        new_dir = next(
            p for p in (self.collab / "appels").iterdir() if p.name != "0001-A-abcdef"
        )
        intention = fakes.read_json(new_dir / "intention.json")
        self.assertEqual(intention["retries"], "abcdef")
        self.assertEqual(intention["retry_reason"], "quota epuise, credits recharges")
        self.assertNotEqual(intention["call_id"], "abcdef")
        self.assertEqual(intention["sequence"], 2)


class TestPortability(RecoveryCase):
    def test_a_moved_collaboration_resumes(self) -> None:
        """Le dossier est autonome pour reprendre le cycle : le déplacer et
        reprendre doit fonctionner. Aucun chemin absolu n'est persisté (§3)."""
        self.crash_mid_call(response=_DOC, result=True)
        moved_root = self.root / "ailleurs"
        moved_root.mkdir()
        moved = moved_root / "collaboration"
        shutil.move(str(self.collab), str(moved))
        self.collab = moved
        self.assertIs(self.resume(), Status.WAITING_HUMAN)
        self.assertEqual(self.a.calls, 0)

    def test_no_absolute_path_is_persisted(self) -> None:
        self.crash_mid_call(response=_DOC, result=True)
        self.resume()
        for path in self.collab.rglob("*.json"):
            with self.subTest(fichier=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn(str(self.root), text)
                self.assertNotIn("C:\\\\", text)

    def test_no_provider_name_in_a_call_directory(self) -> None:
        """Aucune chaîne de fournisseur dans un identifiant ni dans un chemin."""
        collab = fakes.collaboration(self.root / "neuve")
        a = fakes.FakeAdapter("fake-a", (_DOC,))
        b = fakes.FakeAdapter("fake-b", (fakes.review("BLOQUE"),))
        workflow.run(collab, adapters={"fake-a": a, "fake-b": b}, timeout_seconds=30.0)
        for call_dir in (collab / "appels").iterdir():
            sequence, role, uuid_part = call_dir.name.split("-")
            self.assertIn(role, ("A", "B"))
            self.assertTrue(sequence.isdigit())
            self.assertEqual(len(uuid_part), 32)


class TestConcurrency(RecoveryCase):
    def test_state_changed_between_preflight_and_lock_is_refused(self) -> None:
        """L'étape 3 ferme la fenêtre de concurrence sans passer les sondages
        coûteux sous verrou."""
        collab = self.collab
        original = fakes.read_json(collab / "etat.json")

        class Meddling(fakes.FakeAdapter):
            def probe(self) -> object:  # type: ignore[override]
                # Un autre processus écrit pendant le prévol.
                changed = dict(original)
                changed["revision"] = 7
                fakes.write_json(collab / "etat.json", changed)
                return super().probe()

        adapters = {"fake-a": Meddling("fake-a", (_DOC,)), "fake-b": self.b}
        with self.assertRaises(workflow.WorkflowError):
            workflow.run(collab, adapters=adapters, timeout_seconds=30.0)

    def test_a_live_lock_holder_blocks_the_engine(self) -> None:
        fakes.write_json(self.collab / "verrou.json", {
            "pid": __import__("os").getpid(), "acquired_at": "2026-09-03T00:00:00Z",
            "command": "une autre commande",
        })
        self.a.responses = [_DOC]
        with self.assertRaises(Exception) as caught:
            workflow.run(self.collab, adapters=self.adapters, timeout_seconds=30.0)
        self.assertIn("verrou", str(caught.exception))
        self.assertEqual(self.a.calls, 0)
        self.assertEqual(
            json.loads((self.collab / "verrou.json").read_text(encoding="utf-8"))["command"],
            "une autre commande",
        )


if __name__ == "__main__":
    unittest.main()

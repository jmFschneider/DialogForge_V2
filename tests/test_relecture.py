"""Tests des correctifs issus de la relecture externe du 2026-09-05.

Chacun porte le numéro de l'observation qu'il ferme
(`project/analyse/codex/2026-09-05-relecture-fonctionnement.md`).

Point commun de ces six défauts : **aucun n'était visible depuis un cycle
nominal.** Ils vivent dans les fenêtres — une lecture rompue, un arrêt entre
deux écritures, un séparateur de chemin, une clé omise. C'est ce qu'une lecture
statique attrape et qu'une suite verte ne montre pas.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from iabinome import contracts, corpus, workflow
from iabinome.adapters.base import AdapterError
from iabinome.models import Disposition, Severity, Status
from tests import fakes

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."
_BACKSLASH = chr(92)


class TestCorpusLogicalPaths(unittest.TestCase):
    """Observation 4 — la plus grave : elle rendait la collaboration inutilisable.

    `new` acceptait `docs\\note.md`, le persistait tel quel, et le balayage des
    surnuméraires comparait ensuite à `docs/note.md` rendu par `as_posix()`. Le
    fichier copié était déclaré surnuméraire au **premier** `run` : une
    collaboration créée sans erreur, morte avant son premier appel.
    """

    def build(self, entree: str) -> corpus.Manifest:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "src" / "docs").mkdir(parents=True)
        (root / "src" / "docs" / "note.md").write_text("contenu", encoding="utf-8")
        (root / "src" / "note.md").write_text("autre", encoding="utf-8")
        listing = root / "liste.txt"
        listing.write_bytes((entree + "\n").encode("utf-8"))
        self.destination = root / "collab" / "corpus"
        return corpus.build(root / "src", listing, self.destination, "essai")

    def assert_no_surplus(self, manifest: corpus.Manifest) -> None:
        """Le manifeste et le disque doivent se reconnaître."""
        expected = {e.logical_path for e in manifest.entries}
        vus = {
            p.relative_to(self.destination / "fichiers").as_posix()
            for p in (self.destination / "fichiers").rglob("*") if p.is_file()
        }
        self.assertEqual(vus - expected, set(), "fichier copie declare surnumeraire")

    def test_a_backslash_separator_is_normalised(self) -> None:
        manifest = self.build("docs" + _BACKSLASH + "note.md")
        self.assertEqual(manifest.entries[0].logical_path, "docs/note.md")
        self.assert_no_surplus(manifest)

    def test_a_dot_prefix_is_normalised(self) -> None:
        manifest = self.build("./note.md")
        self.assertEqual(manifest.entries[0].logical_path, "note.md")
        self.assert_no_surplus(manifest)

    def test_a_plain_relative_path_is_untouched(self) -> None:
        manifest = self.build("docs/note.md")
        self.assertEqual(manifest.entries[0].logical_path, "docs/note.md")
        self.assert_no_surplus(manifest)


class RelectureCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.a = fakes.FakeAdapter("fake-a", ())
        self.b = fakes.FakeAdapter("fake-b", ())
        self.adapters = {"fake-a": self.a, "fake-b": self.b}
        self.collab = fakes.collaboration(self.root)

    def drive(self, **kwargs: object) -> Status:
        state = workflow.run(
            self.collab, adapters=self.adapters, timeout_seconds=30.0, **kwargs  # type: ignore[arg-type]
        )
        return state.status


class TestOmittedSeverityKeepsTheFindingOpen(RelectureCase):
    """Observation 3 — la tolérance sur `severity` ne doit pas fermer un constat.

    §6 : « Sévérité omise → UNKNOWN **après** décodage, et le constat **reste
    ouvert**. » Le code retenait `UNKNOWN` mais gardait la disposition fournie :
    B pouvait omettre la sévérité, rendre `RESOLVED` dans le même constat, le
    retirer du registre et emmener le cycle en finalisation.
    """

    def test_an_omitted_severity_cannot_close_a_finding(self) -> None:
        review = contracts.parse_review(fakes.review("ACCEPTER", findings=(
            {"id": "B-001", "disposition": "RESOLVED", "statement": "Corrige."},
        )))
        finding = review.findings[0]
        self.assertIs(finding.severity, Severity.UNKNOWN)
        self.assertIs(finding.disposition, Disposition.OPEN, "le constat a ete ferme")
        self.assertEqual(contracts.open_finding_ids(review), ["B-001"])

    def test_a_declared_severity_still_closes_normally(self) -> None:
        """Le maintien ne va que dans le sens sûr : il n'empêche jamais une
        fermeture motivée, il refuse seulement la fermeture silencieuse."""
        review = contracts.parse_review(fakes.review("ACCEPTER", findings=(
            {"id": "B-001", "severity": "MAJOR", "disposition": "RESOLVED",
             "statement": "Corrige."},
        )))
        self.assertIs(review.findings[0].disposition, Disposition.RESOLVED)
        self.assertEqual(contracts.open_finding_ids(review), [])

    def test_the_cycle_does_not_finalise_on_a_silently_closed_finding(self) -> None:
        collab = self.collab
        self.a.responses = [_DOC]
        self.b.responses = [
            fakes.review("REVISER"),
            fakes.review("ACCEPTER", findings=(
                {"id": "B-001", "disposition": "RESOLVED", "statement": "Corrige."},
            )),
        ]
        self.drive()
        etat = fakes.read_json(collab / "etat.json")
        self.assertEqual(etat["open_finding_ids"], ["B-001"])


class TestResolutionLeavesNothingBehind(RelectureCase):
    """Observation 7 — un exécutable disparu ne doit rien laisser, ni cracher.

    `command()` était résolu après le `mkdir` et l'écriture de `prompt.txt` ; un
    échec laissait un dossier d'appel orphelin, alors que le commentaire
    annonçait « un refus sans mutation ». Et l'erreur levée était un
    `RuntimeError` nu, absent de la table des types de frontière : traceback là
    où la conception promet un refus lisible.
    """

    def test_no_call_directory_is_left_when_resolution_fails(self) -> None:
        def absent(spec: object) -> list[str]:
            raise AdapterError("fake-a : introuvable sur le PATH")

        self.a.command = absent  # type: ignore[method-assign, assignment]
        with self.assertRaises(AdapterError):
            self.drive()
        self.assertFalse((self.collab / "appels").exists(), "un dossier d'appel est reste")

    def test_the_adapter_error_is_a_named_border_type(self) -> None:
        """Nommée, donc attrapable un par un — pas un `RuntimeError` générique."""
        self.assertTrue(issubclass(AdapterError, RuntimeError))
        self.assertIsNot(AdapterError, RuntimeError)


class TestAFailedPumpForbidsTheCompletenessMarker(unittest.TestCase):
    """Observation 1 — `resultat.json` promet des flux complets.

    `os.read` rend `b""` à la fin du flux et lève sur une lecture rompue. La
    pompe sortait de sa boucle dans les deux cas : le préfixe déjà copié passait
    pour la réponse entière, et son empreinte le certifiait.
    """

    def test_a_read_error_is_not_taken_for_an_end_of_stream(self) -> None:
        import os

        from iabinome.transport import _Pump

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        lecteur, ecrivain = os.pipe()
        os.write(ecrivain, b"un debut de reponse")
        os.close(ecrivain)

        class SourceRompue:
            """Rend le descripteur une fois, puis un descripteur fermé."""

            def __init__(self) -> None:
                self.appels = 0

            def fileno(self) -> int:
                self.appels += 1
                return lecteur if self.appels == 1 else -1

        pump = _Pump(SourceRompue(), Path(tmp.name) / "stdout.txt", 1 << 20)  # type: ignore[arg-type]
        pump.run()
        os.close(lecteur)
        self.assertTrue(pump.failed, "une lecture rompue a ete prise pour une fin de flux")
        self.assertEqual(pump.written, len(b"un debut de reponse"))

    def test_a_clean_stream_is_not_marked_failed(self) -> None:
        import os

        from iabinome.transport import _Pump

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        lecteur, ecrivain = os.pipe()
        os.write(ecrivain, b"reponse complete")
        os.close(ecrivain)

        class Source:
            def fileno(self) -> int:
                return lecteur

        pump = _Pump(Source(), Path(tmp.name) / "stdout.txt", 1 << 20)  # type: ignore[arg-type]
        pump.run()
        os.close(lecteur)
        self.assertFalse(pump.failed)


class TestTornLockNamesTheFileToDelete(RelectureCase):
    """Observation 5 — retenue, **mais son correctif implicite est refusé**.

    Un arrêt entre la création exclusive de `verrou.json` et l'écriture de son
    contenu laisse un fichier illisible qu'aucune récupération ne reprend.

    Récupérer un verrou illisible reviendrait à effacer celui d'un détenteur
    **vivant** surpris dans cette même fenêtre — la même fenêtre exactement, donc
    la même probabilité, pour une conséquence pire : deux détenteurs simultanés
    au lieu d'un blocage visible. Ce qui est corrigé, c'est donc le **message**,
    pas le comportement : il doit dire quoi faire.
    """

    def test_the_error_names_the_file_and_the_condition(self) -> None:
        (self.collab / "verrou.json").write_bytes(b"")
        self.a.responses = [_DOC]
        with self.assertRaises(Exception) as caught:
            self.drive()
        message = str(caught.exception)
        self.assertIn("verrou.json", message)
        self.assertIn("à la main", message)
        self.assertIn("aucune commande ne tourne", message)
        self.assertEqual(fakes.launched_calls(self.collab), 0)


class TestCorpusRefusalPrecedesAnyMutation(RelectureCase):
    """Observation 6 — le code 1 promet un refus **avant mutation**.

    La vérification du corpus arrivait dans `new_call`, donc **après**
    l'application de `--answer` : la demande était archivée et remplacée, l'état
    publié en `READY`, puis le refus tombait avec un code qui annonce l'absence
    de mutation. Et la même commande, rejouée après réparation, échouait — la
    collaboration n'attendait plus l'humain.
    """

    def test_a_broken_corpus_refuses_before_the_answer_is_applied(self) -> None:
        collab = fakes.collaboration(
            self.root / "recherche", mission_kind="RECHERCHE",
            corpus_captured_at="2026-09-01", corpus_files={"note.md": "Contenu."},
        )
        self.a.responses = ["IABINOME:QUESTION\nQuel critere ?"]
        state = workflow.run(collab, adapters=self.adapters, timeout_seconds=30.0)
        self.assertIs(state.status, Status.WAITING_HUMAN)

        (collab / "corpus" / "fichiers" / "note.md").unlink()
        avant_demande = (collab / "demande.md").read_bytes()
        avant_etat = (collab / "etat.json").read_bytes()
        answer = self.root / "reponse.md"
        answer.write_text("Le critere est la couverture.", encoding="utf-8")

        with self.assertRaises(workflow.WorkflowError):
            workflow.run(
                collab, adapters=self.adapters, timeout_seconds=30.0,
                command_label="resume", intervention=workflow.Answer(answer),
            )
        self.assertEqual((collab / "demande.md").read_bytes(), avant_demande)
        self.assertEqual((collab / "etat.json").read_bytes(), avant_etat)
        self.assertEqual(sorted(collab.glob("demande.md.*")), [], "une archive a ete ecrite")


if __name__ == "__main__":
    unittest.main()

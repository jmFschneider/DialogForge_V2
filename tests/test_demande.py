"""Tests du lot 1, point 1.1 : format court de demande, cadrage guidé, provenance.

Les propriétés du plan — « une demande claire lance directement la production ;
une ambiguïté significative produit une question utile ; la réponse reprend le
cycle avec la bonne demande » — sont éprouvées par la CLI, contre les faux
adaptateurs : `FakeAdapter.calls` est la preuve qu'aucun appel de cadrage n'est
ajouté.
"""

from __future__ import annotations

import io
import unittest
from collections.abc import Iterator
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest import mock

from iabinome import cli, demande
from tests import fakes
from tests.test_cli import CliCase

_COMPLETE = fakes.DEMANDE_COMPLETE

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps."
_QUESTION = "IABINOME:QUESTION\nQuel est le critere de fin ?"


class TestSections(unittest.TestCase):
    def test_a_complete_demande_misses_nothing(self) -> None:
        self.assertEqual(demande.missing(_COMPLETE), [])

    def test_a_free_form_demande_misses_all_six(self) -> None:
        """Contre-épreuve du test précédent : `missing` sait voir une absence."""
        self.assertEqual(demande.missing("Concevoir le cache."), list(demande.SECTIONS))

    def test_case_accents_and_hyphens_do_not_matter(self) -> None:
        text = "## OBJECTIF\nx\n### livrable\ny\n## Non objectifs\nz\n## Criteres de fin\nw\n"
        self.assertEqual(demande.missing(text), ["Sources", "Contraintes"])

    def test_an_empty_section_is_missing(self) -> None:
        text = _COMPLETE.replace("Python seul.", "   ")
        self.assertEqual(demande.missing(text), ["Contraintes"])

    def test_a_deeper_heading_stays_inside_its_section(self) -> None:
        text = "## Objectif\n### Contexte\nLe fond du sujet.\n"
        self.assertEqual(demande.sections(text), {"Objectif": "### Contexte\nLe fond du sujet."})

    def test_an_unrelated_heading_of_the_same_level_closes_the_section(self) -> None:
        text = "## Objectif\nx\n## Annexe\nne compte pas\n"
        self.assertEqual(demande.sections(text), {"Objectif": "x"})

    def test_a_heading_inside_a_code_block_is_not_a_heading(self) -> None:
        text = "## Objectif\navant\n```\n## Livrable\nfaux\n```\naprès\n"
        found = demande.sections(text)
        self.assertNotIn("Livrable", found)
        self.assertIn("après", found["Objectif"])


class TestComplete(unittest.TestCase):
    """`--answer` complète : le texte existant reste en préfixe, rien n'est réécrit."""

    def test_the_existing_text_is_kept_intact_as_a_prefix(self) -> None:
        after = demande.complete(_COMPLETE, "Le critère de fin est la couverture complète.")
        self.assertTrue(after.startswith(_COMPLETE.rstrip()))
        self.assertIn("## Précisions n°1\n\nLe critère de fin est la couverture complète.", after)

    def test_every_section_survives_with_the_same_body(self) -> None:
        before = demande.sections(_COMPLETE)
        after = demande.sections(demande.complete(_COMPLETE, "Une précision."))
        self.assertEqual(sorted(before), sorted(demande.SECTIONS), "la base est bien complète")
        for name, body in before.items():
            self.assertEqual(after[name], body, name)

    def test_an_answer_carrying_its_own_headings_removes_nothing(self) -> None:
        """Une réponse qui est elle-même une demande, aux mêmes titres : l'ancien
        contenu reste, le nouveau s'y ajoute. Rien n'est écrasé."""
        answer = "## Objectif\nAutre objectif.\n\n## Sources\nAutres sources.\n"
        after = demande.sections(demande.complete(_COMPLETE, answer))
        for name in ("Objectif", "Sources"):
            self.assertIn(demande.sections(_COMPLETE)[name], after[name])
        self.assertEqual(demande.missing(demande.complete(_COMPLETE, answer)), [])

    def test_successive_answers_are_numbered_from_the_text_alone(self) -> None:
        once = demande.complete(_COMPLETE, "Première.")
        twice = demande.complete(once, "Seconde.")
        self.assertIn("## Précisions n°2\n\nSeconde.", twice)
        self.assertTrue(twice.startswith(once.rstrip()))

    def test_the_same_inputs_give_the_same_text(self) -> None:
        """Le rejeu après un arrêt brutal en dépend : sans cela, la demande déjà
        écrite ne serait plus reconnue par son empreinte."""
        self.assertEqual(
            demande.complete(_COMPLETE, "Une précision."),
            demande.complete(_COMPLETE, "Une précision."),
        )


class TestGuide(unittest.TestCase):
    def run_guide(self, replies: list[str]) -> tuple[str, str]:
        script: Iterator[str] = iter(replies)
        said: list[str] = []
        text = demande.guide(lambda _prompt: next(script), said.append)
        return text, "\n".join(said)

    def test_the_guided_demande_carries_all_six_sections(self) -> None:
        text, _ = self.run_guide(
            ["Décider.", "", "Une note.", "", "", "", "", "", "", "", "", ""]
        )
        self.assertEqual(demande.missing(text), [])
        self.assertIn("Décider.", text)

    def test_an_optional_section_left_empty_says_so(self) -> None:
        text, _ = self.run_guide(["Décider.", "", "Une note.", "", "", "", "", "", "", "", "", ""])
        self.assertEqual(demande.sections(text)["Sources"], "Non précisé.")

    def test_a_required_section_is_asked_again(self) -> None:
        text, said = self.run_guide(
            ["", "Décider.", "", "Une note.", "", "", "", "", "", "", "", "", ""]
        )
        self.assertIn("« Objectif » est nécessaire", said)
        self.assertEqual(demande.sections(text)["Objectif"], "Décider.")

    def test_an_answer_may_span_several_lines(self) -> None:
        text, _ = self.run_guide(
            ["Décider.", "Puis justifier.", "", "Une note.", "", "", "", "", "", "", "", ""]
        )
        self.assertEqual(demande.sections(text)["Objectif"], "Décider.\nPuis justifier.")


class TestRecord(unittest.TestCase):
    def test_a_version_is_numbered_and_a_replay_adds_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            collab = Path(tmp)
            demande.record(collab, {"source": "fichier", "path": "a.md", "sha256": "aaa"})
            demande.record(collab, {"source": "reponse", "path": "b.md", "sha256": "bbb"})
            demande.record(collab, {"source": "reponse", "path": "b.md", "sha256": "bbb"})
            versions = demande.read(collab)
        self.assertEqual([v["sequence"] for v in versions], [1, 2])
        self.assertEqual([v["sha256"] for v in versions], ["aaa", "bbb"])

    def test_a_collaboration_without_provenance_reads_as_empty(self) -> None:
        with TemporaryDirectory() as tmp:
            self.assertEqual(demande.read(Path(tmp)), [])


class TestNewFromFile(CliCase):
    def versions(self) -> list[dict[str, Any]]:
        return demande.read(self.collab)

    def new(self, **overrides: str) -> tuple[int, str]:
        with redirect_stderr(io.StringIO()) as err, redirect_stdout(io.StringIO()):
            code = cli.main(["new", *self.new_args(**overrides)])
        return code, err.getvalue()

    def test_a_complete_demande_is_kept_with_its_provenance_and_no_note(self) -> None:
        self.demande.write_text(_COMPLETE, encoding="utf-8")
        code, err = self.new()
        self.assertEqual(code, 0)
        (only,) = self.versions()
        self.assertEqual(only["source"], "fichier")
        self.assertEqual(only["path"], str(self.demande.resolve()))
        config = fakes.read_json(self.collab / "configuration.json")
        self.assertEqual(only["sha256"], config["initial_demande_sha256"])
        self.assertNotIn("section", err)

    def test_a_free_form_demande_is_accepted_with_a_note_not_refused(self) -> None:
        code, err = self.new()
        self.assertEqual(code, 0)
        self.assertEqual(fakes.read_json(self.collab / "etat.json")["status"], "READY")
        for name in demande.SECTIONS:
            self.assertIn(name, err)

    def test_a_missing_file_is_refused_and_creates_nothing(self) -> None:
        code, err = self.new(**{"--demande": str(self.root / "absente.md")})
        self.assertEqual(code, 1)
        self.assertIn("erreur :", err)
        self.assertFalse(self.collab.exists())

    def test_both_sources_or_none_is_a_usage_error(self) -> None:
        for extra in (["--cadrer"], None):
            with self.subTest(extra=extra):
                argv = ["new", *self.new_args()]
                if extra is None:
                    argv = [a for a in argv if a not in ("--demande", str(self.demande))]
                else:
                    argv += extra
                with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                    cli.main(argv)
                self.assertEqual(caught.exception.code, 2)
                self.assertFalse(self.collab.exists())


class TestNewGuided(CliCase):
    REPLIES = [
        "Décider de la stratégie.", "", "Une note.", "", "Le dossier docs.", "", "", "",
        "Pas d'implémentation.", "", "Stratégie retenue.", "",
    ]

    def guided(self, replies: list[Any]) -> tuple[int, str]:
        argv = ["new", *self.new_args(), "--cadrer"]
        argv = [a for a in argv if a not in ("--demande", str(self.demande))]
        with (
            mock.patch("builtins.input", side_effect=replies),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()) as err,
        ):
            code = cli.main(argv)
        return code, err.getvalue()

    def test_the_guided_demande_becomes_demande_md_without_any_model_call(self) -> None:
        code, err = self.guided(self.REPLIES)
        self.assertEqual(code, 0)
        text = (self.collab / "demande.md").read_text(encoding="utf-8")
        self.assertEqual(demande.missing(text), [])
        self.assertIn("Décider de la stratégie.", text)
        self.assertEqual((self.a.calls, self.b.calls), (0, 0), "un appel de cadrage a ete paye")
        self.assertNotIn("section", err)
        (only,) = demande.read(self.collab)
        self.assertEqual((only["source"], only["path"]), ("cadrage", None))

    def test_an_interrupted_framing_leaves_nothing_behind(self) -> None:
        # Fin de flux au milieu du questionnaire : `input()` lève `EOFError`.
        code, err = self.guided([*self.REPLIES[:3], EOFError()])
        self.assertEqual(code, 1)
        self.assertIn("rien n'a été créé", err)
        self.assertEqual(list(self.root.glob(".new-*")), [])
        self.assertFalse(self.collab.exists())


class TestTheWholeJourney(CliCase):
    """Les trois propriétés de validation du plan, de bout en bout."""

    def test_a_clear_demande_goes_straight_to_production(self) -> None:
        self.demande.write_text(_COMPLETE, encoding="utf-8")
        self.assertEqual(cli.main(["new", *self.new_args()]), 0)
        self.a.responses = [_DOC]
        self.b.responses = [fakes.review("ACCEPTER", findings=())]
        self.assertEqual(cli.main(["run", str(self.collab)]), 0)
        # Un appel de A (la proposition), un de B qui accepte : ni cadrage, ni
        # finalisation — la version examinée est promue telle quelle (1.3).
        self.assertEqual((self.a.calls, self.b.calls), (1, 1))
        self.assertIn("Décider de la stratégie de cache.", self.a.prompts[0])

    def test_an_ambiguity_becomes_a_question_and_the_answer_resumes_with_the_right_demande(
        self,
    ) -> None:
        self.demande.write_text(_COMPLETE, encoding="utf-8")
        self.assertEqual(cli.main(["new", *self.new_args()]), 0)
        self.a.responses = [_QUESTION, _DOC]
        self.assertEqual(cli.main(["run", str(self.collab)]), 5)

        # Une réponse **courte** : c'est le cas qui, sous l'ancienne sémantique,
        # aurait remplacé toute la demande par une phrase.
        answer = self.root / "reponse.md"
        answer.write_text("Le critère de fin est la couverture complète.", encoding="utf-8")
        self.b.responses = [fakes.review("ACCEPTER", findings=())]
        cli.main(["resume", str(self.collab), "--answer", str(answer)])

        # La bonne demande : l'existante **et** le complément, dans la reprise.
        for name, body in demande.sections(_COMPLETE).items():
            self.assertIn(body, self.a.prompts[1], name)
        self.assertIn("couverture complète", self.a.prompts[1])
        # `demande.md` est la version complète, l'unique autorité.
        current = (self.collab / "demande.md").read_text(encoding="utf-8")
        self.assertTrue(current.startswith(_COMPLETE.rstrip()))
        self.assertEqual(demande.missing(current), [])
        # La provenance dit d'où vient le complément et quelle version il prolonge.
        first, second = demande.read(self.collab)
        self.assertEqual(first["source"], "fichier")
        self.assertEqual(second["source"], "reponse")
        self.assertEqual(second["path"], str(answer.resolve()))
        self.assertEqual(second["replaces"], first["sha256"])
        self.assertEqual(second["archive"], "demande.md.001")
        self.assertEqual(second["phase"], "PROPOSAL_A")
        self.assertNotEqual(second["complement_sha256"], second["sha256"])
        # Et l'ancienne version, elle, est intacte à côté.
        archived = (self.collab / "demande.md.001").read_text(encoding="utf-8")
        self.assertEqual(archived, _COMPLETE)


if __name__ == "__main__":
    unittest.main()

"""Tests du lot 1, point 1.3 : la version examinée est promue, jamais réécrite.

Validation du plan : **le cycle s'arrête dans tous les scénarios ; les versions de
demande, livrable et revue correspondent ; une correction substantielle non
revue est signalée.**

La finalisation par A (`FINAL_A`) réécrivait librement le document après la
dernière revue de B : ce que B livrait n'était plus ce que B avait examiné. Elle
est remplacée par la promotion du document **que B vient d'examiner**, octet pour
octet, accompagnée d'un bilan écrit par le programme. « Une correction non revue »
ne peut donc plus naître du cycle : A n'a plus d'appel après B.
"""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path
from unittest import mock

from iabinome import objections
from tests.test_objections import finding, reply, responses, review_v2
from tests.test_workflow import WorkflowCase

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."


class _Stop(RuntimeError):
    """Arrêt injecté — simule la mort du processus pendant la promotion."""


def revision(*entries: dict[str, str], body: str = "# Revision\nCorps revise.") -> str:
    return f"IABINOME:DOCUMENT\n{body}\nIABINOME:REPONSES\n{responses(*entries)}"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PromotionCase(WorkflowCase):
    def cycle(self, a: tuple[str, ...], b: tuple[str, ...], **kwargs: object) -> Path:
        collab = self.build(a=a, b=b, **kwargs)
        self.run_engine(collab)
        return collab

    def delivered(self, collab: Path) -> str:
        return (collab / "livrables" / "version_finale.md").read_text(encoding="utf-8")

    def body_of(self, delivered: str) -> str:
        """Le livrable sans la ligne d'en-tête écrite par le programme."""
        return delivered.split("\n\n", 1)[1]

    def bilan(self, collab: Path) -> str:
        return (collab / "livrables" / "bilan.md").read_text(encoding="utf-8")

    def status(self, collab: Path) -> str:
        return str(self.etat(collab)["status"])


class TestAcceptanceNeedsNoRewrite(PromotionCase):
    def test_a_review_that_finds_nothing_delivers_the_proposal_untouched(self) -> None:
        collab = self.cycle((_DOC,), (review_v2("ACCEPTER"),))
        self.assertEqual(self.status(collab), "AWAITING_APPROVAL")
        self.assertEqual((self.a.calls, self.b.calls), (1, 1), "un appel de trop a ete paye")
        proposal = (collab / "echanges" / "0001-proposition-A.md").read_text(encoding="utf-8")
        self.assertEqual(self.body_of(self.delivered(collab)), proposal)

    def test_the_program_says_the_document_is_not_approved_and_why_the_cycle_ended(self) -> None:
        collab = self.cycle((_DOC,), (review_v2("ACCEPTER"),))
        header = self.delivered(collab).split("\n\n", 1)[0]
        self.assertIn("n'est pas approuvé", header)
        self.assertIn("acceptée par B", header)
        self.assertIn("livrée sans réécriture", header)
        self.assertIn("n'est pas « accepté »", self.bilan(collab))


class TestACorrectionIsReviewedThenPromoted(PromotionCase):
    def run_corrected(self) -> Path:
        return self.cycle(
            (_DOC, revision(reply())),
            (review_v2("REVISER", finding()),
             review_v2("ACCEPTER", finding(disposition="RESOLVED", justification="Corrigé."))),
        )

    def test_the_delivered_body_is_the_version_b_examined_byte_for_byte(self) -> None:
        collab = self.run_corrected()
        examined = (collab / "echanges" / "0003-revision-1-A.md").read_text(encoding="utf-8")
        self.assertEqual(self.body_of(self.delivered(collab)), examined)
        self.assertNotIn("IABINOME:REPONSES", self.delivered(collab))

    def test_no_call_follows_the_last_review(self) -> None:
        """La proposition, la correction : deux appels de A, deux de B. Le 5e
        appel — la finalisation qui réécrivait — n'existe plus."""
        collab = self.run_corrected()
        self.assertEqual((self.a.calls, self.b.calls), (2, 2))
        calls = sorted(p.name.split("-")[1] for p in (collab / "appels").iterdir())
        self.assertEqual(calls, ["A", "A", "B", "B"])

    def test_demande_livrable_and_review_correspond_by_fingerprint(self) -> None:
        collab = self.run_corrected()
        bilan = self.bilan(collab)
        examined = collab / "echanges" / "0003-revision-1-A.md"
        review = collab / "echanges" / "0004-critique-B.json"
        self.assertIn(f"`echanges/0003-revision-1-A.md` (sha256 `{sha(examined)}`)", bilan)
        self.assertIn(f"`echanges/0004-critique-B.json` (sha256 `{sha(review)}`)", bilan)
        self.assertIn(f"`demande.md` (sha256 `{sha(collab / 'demande.md')}`", bilan)
        # Et le livrable désigné est bien celui qui existe, corps identique.
        self.assertIn("`livrables/version_finale.md` — corps identique à", bilan)
        delivered_body = self.body_of(self.delivered(collab)).encode("utf-8")
        self.assertEqual(hashlib.sha256(delivered_body).hexdigest(), sha(examined))

    def test_the_review_named_in_the_bilan_is_the_one_that_examined_that_document(self) -> None:
        """La revue publiée porte sur `current_document` : la numérotation des
        appels le montre — la revue vient juste après le document."""
        collab = self.run_corrected()
        names = sorted(p.name for p in (collab / "echanges").iterdir())
        self.assertEqual(names.index("0004-critique-B.json"),
                         names.index("0003-revision-1-A.md") + 1)


class TestTheCapPresentsTheDisagreements(PromotionCase):
    def test_at_the_cap_the_last_examined_version_is_delivered_with_what_stays_open(self) -> None:
        collab = self.cycle(
            (_DOC, revision(reply(kind="CONTESTE", justification="X est hors périmètre."))),
            (review_v2("REVISER", finding()), review_v2("REVISER", finding())),
            max_revisions=1,
        )
        self.assertEqual(self.status(collab), "AWAITING_APPROVAL")
        self.assertEqual((self.a.calls, self.b.calls), (2, 2), "le plafond est depasse")
        examined = (collab / "echanges" / "0003-revision-1-A.md").read_text(encoding="utf-8")
        self.assertEqual(self.body_of(self.delivered(collab)), examined)
        bilan = self.bilan(collab)
        self.assertIn("plafond de révisions atteint (1 sur 1)", bilan)
        self.assertIn("présentés, pas traités", bilan)
        self.assertIn("- `B-001` [MAJOR] Manque X.", bilan.split("## Désaccords restants")[1])
        self.assertIn("CONTESTE — X est hors périmètre.", bilan)
        self.assertIn("plafond de 1 révision(s) atteint", self.delivered(collab))

    def test_with_no_revision_allowed_the_proposal_is_delivered_and_the_open_point_shown(
        self,
    ) -> None:
        collab = self.cycle((_DOC,), (review_v2("REVISER", finding()),), max_revisions=0)
        self.assertEqual(self.status(collab), "AWAITING_APPROVAL")
        self.assertEqual((self.a.calls, self.b.calls), (1, 1))
        self.assertIn("- `B-001`", self.bilan(collab).split("## Désaccords restants")[1])
        self.assertIn("| B-001 | MAJOR | OPEN | — |", self.bilan(collab))

    def test_the_bilan_of_a_clean_cycle_lists_no_disagreement(self) -> None:
        collab = self.cycle((_DOC,), (review_v2("ACCEPTER"),))
        after = self.bilan(collab).split("## Désaccords restants")[1]
        self.assertEqual(after.strip(), "Aucun.")
        self.assertIn("Aucune objection n'a été soulevée.", self.bilan(collab))


class TestANewSuggestionDoesNotOpenARound(PromotionCase):
    def test_a_new_observation_beside_a_resolved_objection_is_shown_not_treated(self) -> None:
        """B accepte : l'objection antérieure est résolue, et une remarque nouvelle
        (hors périmètre) reste notée. Elle n'ouvre pas de tour de plus."""
        collab = self.cycle(
            (_DOC, revision(reply())),
            (review_v2("REVISER", finding()),
             review_v2("ACCEPTER",
                       finding(disposition="RESOLVED", justification="Corrigé."),
                       finding("B-002", severity="NOTE", statement="Une idée en plus."))),
        )
        self.assertEqual(self.status(collab), "AWAITING_APPROVAL")
        self.assertEqual((self.a.calls, self.b.calls), (2, 2), "un tour a ete ouvert")
        after = self.bilan(collab).split("## Désaccords restants")[1]
        self.assertIn("- `B-002` [NOTE] Une idée en plus.", after)
        self.assertNotIn("B-001", after)


class TestTheFirstReviewIsBroadTheNextOnesAreTargeted(PromotionCase):
    def test_only_the_review_that_follows_a_correction_is_told_to_stay_in_scope(self) -> None:
        self.cycle(
            (_DOC, revision(reply())),
            (review_v2("REVISER", finding()),
             review_v2("ACCEPTER", finding(disposition="RESOLVED", justification="Corrigé."))),
        )
        self.assertNotIn("relecture ciblée", self.b.prompts[0])
        self.assertIn("relecture ciblée", self.b.prompts[1])
        # Et elle porte toujours ce que A a répondu : c'est cela qu'elle examine.
        self.assertIn("Réponse de A : CORRIGE", self.b.prompts[1])


class TestPromotionIsReplayable(PromotionCase):
    def test_a_stop_between_the_livrable_and_the_bilan_replays_without_a_new_call(self) -> None:
        collab = self.build(a=(_DOC,), b=(review_v2("ACCEPTER"),))
        with mock.patch.object(objections, "bilan", side_effect=_Stop("arret injecte")):
            with self.assertRaises(_Stop):
                self.run_engine(collab)
        # Le livrable est déjà là, le bilan et l'état pas encore.
        self.assertTrue((collab / "livrables" / "version_finale.md").exists())
        self.assertFalse((collab / "livrables" / "bilan.md").exists())
        self.assertNotEqual(self.status(collab), "AWAITING_APPROVAL")
        before = self.delivered(collab)
        calls = (self.a.calls, self.b.calls)

        self.run_engine(collab)

        self.assertEqual((self.a.calls, self.b.calls), calls, "la reprise a repaye un appel")
        self.assertEqual(self.status(collab), "AWAITING_APPROVAL")
        self.assertEqual(self.delivered(collab), before, "le livrable a change au rejeu")
        self.assertTrue((collab / "livrables" / "bilan.md").exists())


class TestAQuestionOrABlockStillHandsBackToTheHuman(PromotionCase):
    def test_bloque_does_not_promote_anything(self) -> None:
        collab = self.cycle((_DOC,), (review_v2("BLOQUE", finding(severity="BLOCKING")),))
        self.assertEqual(self.status(collab), "WAITING_HUMAN")
        self.assertFalse((collab / "livrables").exists())

    def test_a_question_does_not_promote_anything(self) -> None:
        collab = self.cycle(("IABINOME:QUESTION\nQuel est le critere de fin ?",), ())
        self.assertEqual(self.status(collab), "WAITING_HUMAN")
        self.assertFalse((collab / "livrables").exists())


if __name__ == "__main__":
    unittest.main()

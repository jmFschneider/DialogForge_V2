"""Tests du lot 1, point 1.2 : les objections gardent leur énoncé, A y répond,
B en dispose et le dit.

Validation du plan : **aucun énoncé initial écrasé par une justification ; chaque
objection retrouve sa disposition ; les réponses mal interprétées restent
accessibles et ne produisent pas un avis favorable par défaut.**

Le contrat a d'abord été confronté à des revues **réelles** — celles de la
mission du 2026-09-05, sous `conception/essais/`. Elles ont montré le défaut que
1.2 corrige : au tour 2, B avait réécrit l'énoncé de ses sept constats pour y
dire « désormais résolu ».
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from iabinome import contracts, objections
from iabinome.contracts import ContractError, parse_objection_responses, parse_review
from iabinome.models import Status
from tests import fakes
from tests.test_workflow import WorkflowCase

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."
_ESSAIS = Path(__file__).resolve().parents[1] / "conception" / "essais"


def finding(
    fid: str = "B-001", *, disposition: str = "OPEN", severity: str = "MAJOR",
    statement: str = "Manque X.", **extra: str,
) -> dict[str, str]:
    return {"id": fid, "severity": severity, "disposition": disposition,
            "statement": statement, **extra}


def review_v2(decision: str, *findings: dict[str, str]) -> str:
    return json.dumps({
        "schema_version": 2, "decision": decision, "analysis": "Critique.",
        "findings": list(findings),
    }, ensure_ascii=False)


def responses(*entries: dict[str, str]) -> str:
    """Le bloc de réponses de A, sans son marqueur."""
    return json.dumps({"schema_version": 1, "responses": list(entries)}, ensure_ascii=False)


def reply(rid: str = "B-001", kind: str = "CORRIGE", justification: str = "") -> dict[str, str]:
    return {"id": rid, "response": kind, "justification": justification}


class TestSplitResponses(unittest.TestCase):
    def test_the_document_stays_free_text_and_the_block_is_split_off(self) -> None:
        document, block = contracts.split_responses("# Titre\nCorps.\nIABINOME:REPONSES\n{}\n")
        self.assertEqual(document, "# Titre\nCorps.\n")
        self.assertEqual(block, "{}\n")

    def test_a_document_may_quote_the_marker_the_last_one_wins(self) -> None:
        body = (
            "Le marqueur est `IABINOME:REPONSES` :\n"
            "IABINOME:REPONSES\nvraiment\nIABINOME:REPONSES\n{}"
        )
        document, block = contracts.split_responses(body)
        self.assertIn("vraiment", document)
        self.assertEqual(block, "{}")

    def test_no_marker_leaves_the_body_untouched(self) -> None:
        self.assertEqual(contracts.split_responses("# Titre\nCorps."), ("# Titre\nCorps.", None))


class TestObjectionResponses(unittest.TestCase):
    def parse(self, block: str | None, open_ids: tuple[str, ...] = ("B-001",)) -> Any:
        return parse_objection_responses(block, open_ids)

    def test_one_response_per_open_objection_is_accepted(self) -> None:
        got = self.parse(responses(reply(), reply("B-002", "CONTESTE", "Non, car Y.")),
                         ("B-001", "B-002"))
        self.assertEqual([(r.id, r.kind.value) for r in got],
                         [("B-001", "CORRIGE"), ("B-002", "CONTESTE")])

    def test_a_missing_response_is_refused_never_read_as_agreement(self) -> None:
        with self.assertRaisesRegex(ContractError, "sans réponse.*B-002"):
            self.parse(responses(reply()), ("B-001", "B-002"))

    def test_an_absent_block_is_refused_when_an_objection_is_open(self) -> None:
        with self.assertRaisesRegex(ContractError, "absent"):
            self.parse(None)

    def test_an_absent_block_is_fine_when_nothing_is_open(self) -> None:
        """Contre-épreuve du précédent : l'exigence porte sur les objections
        ouvertes, pas sur le bloc en soi."""
        self.assertEqual(self.parse(None, ()), ())

    def test_a_duplicated_response_is_refused(self) -> None:
        with self.assertRaisesRegex(ContractError, "dupliquée.*B-001"):
            self.parse(responses(reply(), reply()))

    def test_a_response_to_an_unknown_objection_is_refused(self) -> None:
        with self.assertRaisesRegex(ContractError, "pas ouvert.*B-999"):
            self.parse(responses(reply(), reply("B-999")))

    def test_a_contestation_without_a_reason_is_refused_a_correction_needs_none(self) -> None:
        for kind in ("CONTESTE", "REPORTE", "ARBITRAGE"):
            with self.subTest(kind=kind), self.assertRaisesRegex(ContractError, "justification"):
                self.parse(responses(reply(kind=kind)))
        self.assertEqual(self.parse(responses(reply(kind="CORRIGE")))[0].justification, "")

    def test_an_unknown_kind_or_key_is_refused(self) -> None:
        for bad in (reply(kind="PEUT-ETRE"), {**reply(), "extra": "x"}):
            with self.subTest(bad=bad), self.assertRaises(ContractError):
                self.parse(responses(bad))

    def test_a_block_wrapped_in_prose_and_a_fence_is_recovered(self) -> None:
        """Un préambule n'est pas une raison de repayer un appel."""
        wrapped = f"Voici mes réponses :\n```json\n{responses(reply())}\n```\n"
        self.assertEqual(len(self.parse(wrapped)), 1)


class TestInitialStatementIsKept(unittest.TestCase):
    PRIOR = {"B-001": "Manque X."}

    def parse(self, *findings: dict[str, str], version: int = 2) -> Any:
        text = review_v2("REVISER", *findings).replace('"schema_version": 2',
                                                       f'"schema_version": {version}')
        return parse_review(text, ["B-001"], self.PRIOR)

    def test_a_rewritten_statement_never_replaces_the_initial_one(self) -> None:
        got = self.parse(finding(disposition="RESOLVED", statement="Désormais résolu."))
        self.assertEqual(got.findings[0].statement, "Manque X.")

    def test_the_rewriting_is_recovered_as_the_justification_without_a_new_call(self) -> None:
        got = self.parse(finding(disposition="RESOLVED", statement="Désormais résolu."))
        self.assertEqual(got.findings[0].justification, "Désormais résolu.")
        self.assertEqual(got.findings[0].disposition.value, "RESOLVED")

    def test_a_given_justification_wins_over_the_rewriting(self) -> None:
        got = self.parse(finding(disposition="RESOLVED", statement="Autre.",
                                 justification="Corrigé section 3."))
        self.assertEqual(got.findings[0].justification, "Corrigé section 3.")

    def test_an_unchanged_statement_is_left_alone(self) -> None:
        got = self.parse(finding(justification="Toujours vrai."))
        self.assertEqual((got.findings[0].statement, got.findings[0].justification),
                         ("Manque X.", "Toujours vrai."))


class TestAClosureNeedsItsJustification(unittest.TestCase):
    """Une absence ne clôture jamais un constat."""

    def parse(self, version: int, **overrides: str) -> Any:
        text = review_v2("REVISER", finding(disposition="RESOLVED", **overrides))
        text = text.replace('"schema_version": 2', f'"schema_version": {version}')
        return parse_review(text, ["B-001"], {"B-001": "Manque X."})

    def test_v2_closing_without_a_justification_stays_open(self) -> None:
        self.assertEqual(self.parse(2).findings[0].disposition.value, "OPEN")

    def test_v2_closing_with_a_justification_closes(self) -> None:
        got = self.parse(2, justification="Corrigé.")
        self.assertEqual(got.findings[0].disposition.value, "RESOLVED")

    def test_a_blank_justification_is_no_justification(self) -> None:
        self.assertEqual(self.parse(2, justification="   ").findings[0].disposition.value, "OPEN")

    def test_v1_keeps_its_historic_semantics(self) -> None:
        """Une revue v1 (historique) n'avait pas de justification : la fermer
        sans en donner reste une fermeture, sinon on ne pourrait plus la rejouer."""
        self.assertEqual(self.parse(1).findings[0].disposition.value, "RESOLVED")

    def test_a_closure_of_an_objection_that_was_never_open_is_not_touched(self) -> None:
        text = review_v2("REVISER", finding("B-002", disposition="RESOLVED"))
        got = parse_review(text, [], {})
        self.assertEqual(got.findings[0].disposition.value, "RESOLVED")


class TestHistoricReviews(unittest.TestCase):
    """Les revues réelles du 2026-09-05 : le contrat les lit encore, et il
    corrige ce qu'elles avaient de faux."""

    def load(self, name: str, prior: Any = None) -> Any:
        text = (_ESSAIS / name).read_text(encoding="utf-8")
        ids = [] if prior is None else [f.id for f in prior.findings]
        statements = {} if prior is None else {f.id: f.statement for f in prior.findings}
        return parse_review(text, ids, statements)

    def test_the_real_reviews_still_parse(self) -> None:
        first = self.load("2026-09-05-revision-critique-B-1.json")
        self.assertEqual(len(first.findings), 7)
        self.assertEqual({f.disposition.value for f in first.findings}, {"OPEN"})

    def test_round_two_rewrote_every_statement_and_none_is_lost_to_it(self) -> None:
        first = self.load("2026-09-05-revision-critique-B-1.json")
        raw_second = self.load("2026-09-05-revision-critique-B-2.json")  # sans énoncés initiaux
        second = self.load("2026-09-05-revision-critique-B-2.json", first)
        by_raw = {f.id: f for f in raw_second.findings}
        for original in first.findings:
            with self.subTest(objection=original.id):
                kept = next(f for f in second.findings if f.id == original.id)
                self.assertEqual(kept.statement, original.statement, "énoncé écrasé")
                # Ce que B avait écrit à la place de l'énoncé n'est pas perdu :
                self.assertEqual(kept.justification, by_raw[original.id].statement)
                self.assertNotEqual(kept.justification, original.statement)

    def test_the_three_objections_new_in_round_two_keep_their_own_statement(self) -> None:
        first = self.load("2026-09-05-revision-critique-B-1.json")
        second = self.load("2026-09-05-revision-critique-B-2.json", first)
        new = [f for f in second.findings if f.id not in {g.id for g in first.findings}]
        self.assertEqual(len(new), 3)
        self.assertTrue(all(f.disposition.value == "OPEN" for f in new))


class TestTheCycleKeepsTheObjections(WorkflowCase):
    def run_cycle(self, a: tuple[str, ...], b: tuple[str, ...]) -> Path:
        collab = self.build(a=a, b=b)
        self.run_engine(collab)
        return collab

    def revision(self, *entries: dict[str, str], body: str = "# Revision\nCorps revise.") -> str:
        return f"IABINOME:DOCUMENT\n{body}\nIABINOME:REPONSES\n{responses(*entries)}"

    def raw_responses(self, collab: Path) -> str:
        return "\n".join(
            p.read_text(encoding="utf-8") for p in collab.glob("appels/*/reponse_brute.txt")
        )

    def test_the_whole_history_of_an_objection_is_found_again(self) -> None:
        collab = self.run_cycle(
            (_DOC, self.revision(reply(kind="CONTESTE", justification="X est hors périmètre."))),
            (review_v2("REVISER", finding()),
             review_v2("ACCEPTER", finding(disposition="RESOLVED", statement="Désormais levé."))),
        )
        self.assertIs(self.state(collab), Status.AWAITING_APPROVAL)
        (entry,) = objections.ledger(collab)
        self.assertEqual(entry["statement"], "Manque X.", "l'énoncé initial n'est pas écrasé")
        self.assertEqual(entry["disposition"], "RESOLVED")
        self.assertEqual([(e["call"], e["by"]) for e in entry["history"]],
                         [("0002", "B"), ("0003", "A"), ("0004", "B")])
        self.assertEqual(entry["history"][1]["response"], "CONTESTE")
        self.assertEqual(entry["history"][1]["justification"], "X est hors périmètre.")
        self.assertEqual(entry["history"][2]["justification"], "Désormais levé.")

    def state(self, collab: Path) -> Status:
        return Status(str(self.etat(collab)["status"]))

    def test_b_sees_what_a_answered_and_the_initial_statement(self) -> None:
        self.run_cycle(
            (_DOC, self.revision(reply(kind="CONTESTE", justification="X est hors périmètre."))),
            (review_v2("REVISER", finding()),
             review_v2("ACCEPTER", finding(disposition="RESOLVED", justification="Ok."))),
        )
        second_review_prompt = self.b.prompts[1]
        self.assertIn("Manque X.", second_review_prompt)
        self.assertIn("Réponse de A : CONTESTE — X est hors périmètre.", second_review_prompt)
        self.assertNotIn("Réponse de A", self.b.prompts[0], "rien à répondre au premier tour")

    def test_the_revision_is_stored_without_the_response_block(self) -> None:
        collab = self.run_cycle(
            (_DOC, self.revision(reply(), body="# Revision\nCorps revise.")),
            (review_v2("REVISER", finding()),),
        )
        stored = (collab / "echanges" / "0003-revision-1-A.md").read_text(encoding="utf-8")
        self.assertNotIn("IABINOME:REPONSES", stored)
        self.assertIn("Corps revise.", stored)
        canonical = fakes.read_json(collab / "echanges" / "0003-reponses-A.json")
        self.assertEqual(canonical["responses"][0]["id"], "B-001")

    def test_a_missing_block_stops_in_error_and_never_reaches_a_favourable_review(self) -> None:
        collab = self.run_cycle(
            (_DOC, "IABINOME:DOCUMENT\n# Revision\nsans reponses aux objections"),
            (review_v2("REVISER", finding()), review_v2("ACCEPTER")),
        )
        etat = self.etat(collab)
        self.assertEqual(etat["status"], "ERROR")
        incident = fakes.read_json(collab / str(etat["last_incident"]))
        self.assertEqual(incident["kind"], "CONTRACT_ERROR")
        self.assertIn("absent", incident["detail"])
        self.assertEqual(self.b.calls, 1, "B a relu une revision dont A n'avait pas repondu")
        # Rien de la révision n'est promu, mais la réponse brute reste accessible.
        names = sorted(p.name for p in (collab / "echanges").iterdir())
        self.assertEqual(names, ["0001-proposition-A.md", "0002-critique-B.json"])
        self.assertIn("sans reponses aux objections", self.raw_responses(collab))

    def test_an_incomplete_block_names_the_unanswered_objection(self) -> None:
        collab = self.run_cycle(
            (_DOC, self.revision(reply("B-001"))),
            (review_v2("REVISER", finding("B-001"), finding("B-002", statement="Manque Y.")),),
        )
        etat = self.etat(collab)
        self.assertEqual(etat["status"], "ERROR")
        incident = fakes.read_json(collab / str(etat["last_incident"]))
        self.assertIn("B-002", incident["detail"])

    def test_a_block_wrapped_in_prose_costs_no_second_call(self) -> None:
        wrapped = (
            "IABINOME:DOCUMENT\n# Revision\nCorps.\nIABINOME:REPONSES\n"
            f"Voici mes réponses :\n```json\n{responses(reply())}\n```\n"
        )
        collab = self.run_cycle(
            (_DOC, wrapped),
            (review_v2("REVISER", finding()), review_v2("ACCEPTER", finding(
                disposition="RESOLVED", justification="Corrigé."))),
        )
        self.assertEqual(self.a.calls, 2)
        self.assertIs(self.state(collab), Status.AWAITING_APPROVAL)

    def test_a_closure_without_justification_does_not_close_a_blocking_objection(self) -> None:
        """Une absence ne clôture jamais : B « accepte » en fermant sans dire
        pourquoi, l'objection bloquante reste ouverte, l'humain est appelé."""
        collab = self.run_cycle(
            (_DOC, self.revision(reply())),
            (review_v2("REVISER", finding(severity="BLOCKING")),
             review_v2("ACCEPTER", finding(severity="BLOCKING", disposition="RESOLVED"))),
        )
        etat = self.etat(collab)
        self.assertEqual(etat["status"], "WAITING_HUMAN")
        self.assertEqual(etat["open_finding_ids"], ["B-001"])
        incident = fakes.read_json(collab / str(etat["last_incident"]))
        self.assertEqual(incident["kind"], "ACCEPTER_WITH_OPEN_BLOCKING")
        (entry,) = objections.ledger(collab)
        self.assertEqual(entry["disposition"], "OPEN")

    def test_each_of_several_objections_keeps_its_own_disposition(self) -> None:
        collab = self.run_cycle(
            (_DOC, self.revision(reply("B-001"), reply("B-002", "ARBITRAGE", "Lequel choisir ?"))),
            (review_v2("REVISER", finding("B-001"), finding("B-002", statement="Manque Y.")),
             review_v2("ACCEPTER",
                       finding("B-001", disposition="RESOLVED", justification="Corrigé."),
                       finding("B-002", statement="Manque Y."))),
        )
        by_id = {e["id"]: e for e in objections.ledger(collab)}
        self.assertEqual(by_id["B-001"]["disposition"], "RESOLVED")
        self.assertEqual(by_id["B-002"]["disposition"], "OPEN")
        self.assertEqual(by_id["B-002"]["history"][1]["response"], "ARBITRAGE")


if __name__ == "__main__":
    unittest.main()

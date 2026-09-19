"""Tests de iabinome.contracts : discriminateur A, revue B, normalisation."""

import json
import unittest

from iabinome.contracts import (
    ContractError,
    has_open_blocking,
    normalize,
    open_finding_ids,
    parse_agent_response,
    parse_review,
)
from iabinome.models import Decision, Disposition, Severity


class TestNormalize(unittest.TestCase):
    def test_no_bom_no_transformation(self) -> None:
        result = normalize("contenu\n")
        self.assertEqual(result.text, "contenu\n")
        self.assertEqual(result.transformations, ())

    def test_bom_stripped_and_logged(self) -> None:
        result = normalize("﻿contenu\n")
        self.assertEqual(result.text, "contenu\n")
        self.assertEqual(result.transformations, ("bom_removed",))

    def test_crlf_normalized_and_recorded(self) -> None:
        """Tolérance, pas correction d'un défaut observé : les deux CLI
        caractérisées rendent des `\\n`. Un producteur en mode texte rendrait
        `\\r\\n`, et la balise de première ligne ne serait pas reconnue."""
        result = normalize("IABINOME:DOCUMENT\r\ncorps\r\n")
        self.assertEqual(result.text, "IABINOME:DOCUMENT\ncorps\n")
        self.assertEqual(result.transformations, ("crlf_normalized",))

    def test_bom_and_crlf_both_recorded(self) -> None:
        result = normalize("﻿a\r\nb")
        self.assertEqual(result.text, "a\nb")
        self.assertEqual(result.transformations, ("bom_removed", "crlf_normalized"))

    def test_lone_carriage_return_left_alone(self) -> None:
        """Seule la fin de ligne `\\r\\n` est traitée : un `\\r` isolé vient d'une
        sortie de progression, pas d'une fin de ligne, et reste du texte."""
        result = normalize("a\rb")
        self.assertEqual(result.text, "a\rb")
        self.assertEqual(result.transformations, ())

    def test_sha256_computed_after_crlf_normalized(self) -> None:
        self.assertEqual(normalize("a\r\nb").sha256, normalize("a\nb").sha256)

    def test_sha256_deterministic(self) -> None:
        a = normalize("meme contenu")
        b = normalize("meme contenu")
        self.assertEqual(a.sha256, b.sha256)

    def test_sha256_computed_after_bom_removed(self) -> None:
        with_bom = normalize("﻿contenu")
        without_bom = normalize("contenu")
        self.assertEqual(with_bom.sha256, without_bom.sha256)

    def test_different_content_different_hash(self) -> None:
        a = normalize("un")
        b = normalize("deux")
        self.assertNotEqual(a.sha256, b.sha256)


class TestParseAgentResponse(unittest.TestCase):
    def test_document_tag_parsed(self) -> None:
        response = parse_agent_response("IABINOME:DOCUMENT\n# Titre\ncorps")
        self.assertEqual(response.kind, "DOCUMENT")
        self.assertEqual(response.body, "# Titre\ncorps")

    def test_question_tag_parsed(self) -> None:
        response = parse_agent_response("IABINOME:QUESTION\nQuel est le budget ?")
        self.assertEqual(response.kind, "QUESTION")
        self.assertEqual(response.body, "Quel est le budget ?")

    def test_missing_tag_raises(self) -> None:
        with self.assertRaises(ContractError):
            parse_agent_response("# Un document sans balise")

    def test_unknown_tag_raises(self) -> None:
        with self.assertRaises(ContractError):
            parse_agent_response("IABINOME:AUTRE\ncorps")

    def test_tag_with_trailing_whitespace_rejected(self) -> None:
        with self.assertRaises(ContractError):
            parse_agent_response("IABINOME:DOCUMENT \ncorps")

    def test_empty_text_raises(self) -> None:
        with self.assertRaises(ContractError):
            parse_agent_response("")

    def test_lowercase_tag_rejected(self) -> None:
        with self.assertRaises(ContractError):
            parse_agent_response("iabinome:document\ncorps")


_VALID_REVIEW = {
    "schema_version": 1,
    "decision": "REVISER",
    "analysis": "Critique synthétique.",
    "findings": [
        {"id": "B-001", "severity": "MAJOR", "disposition": "OPEN", "statement": "Manque X."},
    ],
}


class TestParseReviewJsonBlock(unittest.TestCase):
    def test_valid_review_parses(self) -> None:
        review = parse_review(json.dumps(_VALID_REVIEW))
        self.assertEqual(review.decision, Decision.REVISER)
        self.assertEqual(len(review.findings), 1)

    def test_prefix_before_json_rejected(self) -> None:
        with self.assertRaises(ContractError):
            parse_review("Voici ma revue : " + json.dumps(_VALID_REVIEW))

    def test_suffix_after_json_rejected(self) -> None:
        with self.assertRaises(ContractError):
            parse_review(json.dumps(_VALID_REVIEW) + "\nMerci.")

    def test_second_object_rejected(self) -> None:
        with self.assertRaises(ContractError):
            parse_review(json.dumps(_VALID_REVIEW) + json.dumps(_VALID_REVIEW))

    def test_surrounding_whitespace_tolerated(self) -> None:
        review = parse_review("\n  " + json.dumps(_VALID_REVIEW) + "  \n")
        self.assertEqual(review.decision, Decision.REVISER)

    def test_sole_fenced_block_accepted(self) -> None:
        review = parse_review("```json\n" + json.dumps(_VALID_REVIEW) + "\n```")
        self.assertEqual(review.decision, Decision.REVISER)

    def test_sole_fenced_block_without_language_accepted(self) -> None:
        review = parse_review("```\n" + json.dumps(_VALID_REVIEW) + "\n```")
        self.assertEqual(review.decision, Decision.REVISER)

    def test_prefix_before_the_fence_accepted(self) -> None:
        """Voie B, tranchée le 2026-09-05. Le cas exact de la mission réelle :
        B explique son choix de format avant de rendre le bloc."""
        review = parse_review(
            "La sortie attendue suit un schéma précis ; je réponds donc "
            "directement en JSON, comme demandé.\n\n"
            "```json\n" + json.dumps(_VALID_REVIEW) + "\n```"
        )
        self.assertEqual(review.decision, Decision.REVISER)

    def test_suffix_after_the_fence_accepted(self) -> None:
        review = parse_review("```json\n" + json.dumps(_VALID_REVIEW) + "\n```\nMerci.")
        self.assertEqual(review.decision, Decision.REVISER)

    def test_prose_on_both_sides_of_the_fence_accepted(self) -> None:
        review = parse_review(
            "Voici :\n```json\n" + json.dumps(_VALID_REVIEW) + "\n```\nJ'espère que cela aide."
        )
        self.assertEqual(review.decision, Decision.REVISER)

    def test_fence_inside_analysis_does_not_cut_the_block(self) -> None:
        """L'ancrage est première clôture → dernière clôture, jamais un
        comptage : B a le droit de citer du markdown dans `analysis`."""
        quoting = dict(_VALID_REVIEW, analysis="le gabarit montre ```json\\n{…}\\n``` en exemple")
        review = parse_review("Ma revue :\n```json\n" + json.dumps(quoting) + "\n```")
        self.assertIn("```json", review.analysis)

    def test_other_language_fence_rejected(self) -> None:
        with self.assertRaises(ContractError):
            parse_review("```python\n" + json.dumps(_VALID_REVIEW) + "\n```")

    def test_unclosed_fence_rejected(self) -> None:
        with self.assertRaises(ContractError):
            parse_review("```json\n" + json.dumps(_VALID_REVIEW))

    def test_two_fenced_blocks_rejected(self) -> None:
        """Toujours refusé après la voie B : l'extraction première → dernière
        rend un texte invalide, et `json.loads` reste l'arbitre."""
        block = "```json\n" + json.dumps(_VALID_REVIEW) + "\n```"
        with self.assertRaises(ContractError):
            parse_review(block + "\n" + block)

    def test_bare_json_array_rejected(self) -> None:
        with self.assertRaises(ContractError):
            parse_review("[]")

    def test_invalid_json_rejected(self) -> None:
        with self.assertRaises(ContractError):
            parse_review("{not json")


class TestParseReviewSchema(unittest.TestCase):
    def test_unknown_top_level_key_rejected(self) -> None:
        data = {**_VALID_REVIEW, "surnumeraire": "x"}
        with self.assertRaises(ContractError):
            parse_review(json.dumps(data))

    def test_missing_top_level_key_rejected(self) -> None:
        data = dict(_VALID_REVIEW)
        del data["analysis"]
        with self.assertRaises(ContractError):
            parse_review(json.dumps(data))

    def test_future_schema_version_rejected(self) -> None:
        data = {**_VALID_REVIEW, "schema_version": 3}
        with self.assertRaises(ContractError):
            parse_review(json.dumps(data))

    def test_unknown_decision_rejected(self) -> None:
        data = {**_VALID_REVIEW, "decision": "PEUT-ETRE"}
        with self.assertRaises(ContractError):
            parse_review(json.dumps(data))

    def test_unknown_severity_value_rejected(self) -> None:
        data = {**_VALID_REVIEW, "findings": [
            {"id": "B-001", "severity": "CRITIQUE", "disposition": "OPEN", "statement": "x"},
        ]}
        with self.assertRaises(ContractError):
            parse_review(json.dumps(data))

    def test_unknown_finding_key_rejected(self) -> None:
        data = {**_VALID_REVIEW, "findings": [
            {"id": "B-001", "disposition": "OPEN", "statement": "x", "surnumeraire": "y"},
        ]}
        with self.assertRaises(ContractError):
            parse_review(json.dumps(data))

    def test_severity_omitted_defaults_unknown_and_stays_present(self) -> None:
        data = {**_VALID_REVIEW, "findings": [
            {"id": "B-001", "disposition": "OPEN", "statement": "x"},
        ]}
        review = parse_review(json.dumps(data))
        self.assertEqual(review.findings[0].severity, Severity.UNKNOWN)
        self.assertEqual(review.findings[0].disposition, Disposition.OPEN)
        self.assertIn("B-001", open_finding_ids(review))


class TestFindingIds(unittest.TestCase):
    def test_duplicate_id_rejected(self) -> None:
        data = {**_VALID_REVIEW, "findings": [
            {"id": "B-001", "severity": "MAJOR", "disposition": "OPEN", "statement": "a"},
            {"id": "B-001", "severity": "MINOR", "disposition": "OPEN", "statement": "b"},
        ]}
        with self.assertRaises(ContractError):
            parse_review(json.dumps(data))

    def test_prior_finding_missing_rejected(self) -> None:
        with self.assertRaises(ContractError):
            parse_review(json.dumps(_VALID_REVIEW), prior_open_finding_ids=["B-000"])

    def test_prior_finding_carried_over_closed_ok(self) -> None:
        data = {**_VALID_REVIEW, "findings": [
            {"id": "B-000", "severity": "MAJOR", "disposition": "RESOLVED",
             "statement": "corrigé"},
        ]}
        review = parse_review(json.dumps(data), prior_open_finding_ids=["B-000"])
        self.assertEqual(review.findings[0].disposition, Disposition.RESOLVED)
        self.assertEqual(open_finding_ids(review), [])

    def test_new_findings_can_be_added_freely(self) -> None:
        review = parse_review(json.dumps(_VALID_REVIEW), prior_open_finding_ids=[])
        self.assertEqual(len(review.findings), 1)


class TestDecisionNeverDerived(unittest.TestCase):
    def test_accepter_with_open_blocking_parses_without_error(self) -> None:
        data = {
            "schema_version": 1, "decision": "ACCEPTER", "analysis": "ok",
            "findings": [
                {"id": "B-001", "severity": "BLOCKING", "disposition": "OPEN",
                 "statement": "toujours bloquant"},
            ],
        }
        review = parse_review(json.dumps(data))
        self.assertEqual(review.decision, Decision.ACCEPTER)
        self.assertTrue(has_open_blocking(review))

    def test_reviser_without_blocking_not_flagged(self) -> None:
        review = parse_review(json.dumps(_VALID_REVIEW))
        self.assertFalse(has_open_blocking(review))


class TestOpenFindingIdsDerivation(unittest.TestCase):
    def test_only_open_disposition_counted(self) -> None:
        data = {**_VALID_REVIEW, "findings": [
            {"id": "B-001", "severity": "MAJOR", "disposition": "OPEN", "statement": "a"},
            {"id": "B-002", "severity": "MINOR", "disposition": "RESOLVED", "statement": "b"},
            {"id": "B-003", "severity": "NOTE", "disposition": "WITHDRAWN", "statement": "c"},
        ]}
        review = parse_review(json.dumps(data))
        self.assertEqual(open_finding_ids(review), ["B-001"])


if __name__ == "__main__":
    unittest.main()

"""Tests de iabinome.prompts — un prompt qui exige un format porte le format.

**Découvert par la première mission réelle, le 2026-09-04.** `_A_PROPOSAL`
nommait les balises en toutes lettres, mais `_A_REVISION` et `_A_FINAL`
écrivaient « rends DOCUMENT » — sans le préfixe `IABINOME:`. L'agent a obéi
littéralement et rendu `DOCUMENT` en première ligne ; le contrat a refusé.

Conséquence, avant correctif : **aucune mission ne pouvait aller au bout.** Toute
révision et toute finalisation échouaient en `CONTRACT_ERROR` — au dernier appel,
donc après avoir payé tous les autres.

Aucun test à faux agent ne pouvait le voir : `FakeAdapter` émet la bonne balise
quoi qu'on lui demande. C'est le prompt, pas le moteur, qui était faux — et un
prompt ne se teste qu'en le lisant.
"""

from __future__ import annotations

import unittest

from iabinome import contracts, prompts
from iabinome.models import MissionKind, ReviewerAccess

_TAGS = ("IABINOME:DOCUMENT", "IABINOME:QUESTION")


class TestAgentATagsAreSpelledOut(unittest.TestCase):
    def a_prompts(self) -> dict[str, str]:
        """Les quatre prompts adressés à A, dans les quatre situations."""
        demande, document, review = "La demande.", "# Document courant", "{}"
        return {
            "proposition": prompts.build_proposal(demande, MissionKind.CONCEPTION, None),
            "proposition_recherche": prompts.build_proposal(
                demande, MissionKind.RECHERCHE, "2026-09-04"
            ),
            "revision": prompts.build_revision(
                demande, document, review, MissionKind.CONCEPTION, None
            ),
            "finalisation": prompts.build_final(
                demande, document, review, MissionKind.CONCEPTION, None
            ),
        }

    def test_every_prompt_to_a_spells_the_exact_tags(self) -> None:
        for name, prompt in self.a_prompts().items():
            for tag in _TAGS:
                with self.subTest(prompt=name, balise=tag):
                    self.assertIn(tag, prompt, f"{name} : la balise {tag} n'est pas nommée")

    def test_the_tags_named_are_exactly_those_the_contract_accepts(self) -> None:
        """La balise écrite dans le prompt doit être celle que l'analyseur
        reconnaît : les nommer toutes deux ne suffit pas si elles divergent."""
        for tag, kind in (("IABINOME:DOCUMENT", "DOCUMENT"), ("IABINOME:QUESTION", "QUESTION")):
            with self.subTest(balise=tag):
                response = contracts.parse_agent_response(f"{tag}\nle corps")
                self.assertEqual(response.kind, kind)
                self.assertEqual(response.body, "le corps")

    def test_a_bare_tag_is_refused_which_is_why_the_prefix_must_be_written(self) -> None:
        """Contre-épreuve : sans le préfixe, c'est un échec de contrat — c'est
        exactement ce que la mission réelle a produit."""
        with self.assertRaises(contracts.ContractError):
            contracts.parse_agent_response("DOCUMENT\nle corps")


class TestReviewerPromptCarriesItsSchema(unittest.TestCase):
    def test_the_review_schema_is_in_the_prompt_of_b(self) -> None:
        """Même règle, déjà apprise une fois : « retourne le JSON de revue v1 »
        sans montrer le schéma nomme un objet indevinable."""
        prompt = prompts.build_review(
            "La demande.", "# Doc", "Aucun.", ReviewerAccess.CONSULT, None
        )
        for key in (
            "schema_version", "decision", "analysis", "findings", "disposition", "severity",
        ):
            with self.subTest(cle=key):
                self.assertIn(key, prompt)
        for value in ("ACCEPTER", "REVISER", "BLOQUE", "BLOCKING", "OPEN"):
            with self.subTest(valeur=value):
                self.assertIn(value, prompt)


if __name__ == "__main__":
    unittest.main()

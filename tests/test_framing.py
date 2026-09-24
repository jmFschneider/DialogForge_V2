"""Tests de la conversation de cadrage (`conception/CADRAGE_AGENT.md` §2, §5, §6, §7,
§14.1 à §14.4 ; lot 2 de la phase 6) : mémoire de session, groupes et limites
(amendement A1), `/clore` avant tout échange (A2), rédaction, sources, transcription.

Faux agent seulement — de vrais sous-processus Python, jamais un fournisseur."""

import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from iabinome import demande, framing, prompts
from iabinome.adapters.base import FramingSessionSpec
from iabinome.framing import DRAFT, QUESTION, READY, FramingError
from iabinome.models import MissionKind
from tests import fakes

QUESTION_OUT = """\
IABINOME:CADRAGE_QUESTION

QUESTION
Faut-il un cache disque ? Choix : (a) oui, (b) non, (c) plus tard ?

POURQUOI
Change le livrable.

ETAT_CADRAGE
DECISIONS
- aucune
"""

READY_OUT = """\
IABINOME:CADRAGE_PRET

RESUME
Une note sur le cache.

SANS_REPONSE
- Question : durée de vie ?
  Effet possible : taille du cache.

APERCU
Objectif : décider.

ETAT_CADRAGE
DECISIONS
- note
"""

DRAFT_OUT = "IABINOME:DEMANDE\n" + fakes.DEMANDE_COMPLETE.replace("# Cache de FloraPi", "# Demande")


class FramingCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def framing(self, *replies: Any, kind: MissionKind = MissionKind.CONCEPTION,
                sources: dict[str, str] | None = None) -> framing.Framing:
        self.fake = fakes.FakeAdapter(framing_responses=replies)
        root_args: dict[str, Any] = {}
        if sources is not None:
            (self.tmp / "projet").mkdir()
            for name, content in sources.items():
                (self.tmp / "projet" / name).write_text(content, encoding="utf-8")
            (self.tmp / "liste.txt").write_text("\n".join(sources), encoding="utf-8")
            root_args = {"source_root": self.tmp / "projet", "source_list": self.tmp / "liste.txt"}
        root = framing.prepare(kind, **root_args)
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        spec = FramingSessionSpec(model="m", timeout_seconds=30.0, work_root=root / "travail")
        return framing.Framing(framing.open_session(self.fake, spec), root, "Un cache pour FloraPi")

    def prompts_sent(self) -> list[str]:
        (history,) = self.fake.framing_sessions.values()
        return history


class TestSessionMemory(FramingCase):
    def test_idea_and_corpus_instruction_only_in_the_first_prompt(self) -> None:
        """Tests 15, 16 et 17 : ni l'idée, ni la consultation du corpus, ni la
        transcription ne sont retransmises après le premier envoi."""
        f = self.framing(QUESTION_OUT, QUESTION_OUT, READY_OUT)
        f.start()
        f.answer("Réponse numéro un")
        f.answer("Réponse numéro deux")
        first, *later = self.prompts_sent()
        self.assertIn("Un cache pour FloraPi", first)
        self.assertIn("lis maintenant", first)
        for prompt in later:
            self.assertNotIn("Un cache pour FloraPi", prompt)
            self.assertNotIn("lis maintenant", prompt)
        self.assertNotIn("Réponse numéro un", later[1])

    def test_the_draft_can_use_an_answer_absent_from_the_last_state(self) -> None:
        """Test 20 : la rédaction reprend une réponse que F a gardée en session."""
        def draft(history: list[str]) -> str:
            kept = next(p for p in history if "Python seul" in p)
            self.assertIn("DERNIERE_REPONSE", kept)
            return DRAFT_OUT.replace("Python seul.", "Python seul, repris de la session.")
        f = self.framing(QUESTION_OUT, READY_OUT, draft)
        f.start()
        f.answer("Python seul")
        turn = f.write_draft()
        self.assertIsNone(turn.problem)
        self.assertIn("repris de la session", f.draft or "")
        self.assertNotIn("Python seul", self.prompts_sent()[-1])

    def test_questions_may_offer_alternatives(self) -> None:
        """Tests 21 et 22 : les choix et les « ? » ne sont pas comptés."""
        f = self.framing(QUESTION_OUT)
        turn = f.start()
        self.assertIsNone(turn.problem)
        assert turn.reply is not None
        self.assertEqual(turn.reply.kind, QUESTION)


class TestGroups(FramingCase):
    def test_first_group_is_limited_to_three_answers(self) -> None:
        """Tests 23, 24 et 25."""
        f = self.framing(QUESTION_OUT, QUESTION_OUT, QUESTION_OUT, QUESTION_OUT)
        f.start()
        for n in (1, 2):
            self.assertIsNone(f.answer(f"r{n}").problem)
        turn = f.answer("r3")
        self.assertIn("REPONSES_DANS_LE_GROUPE\n3\n\nLIMITE_DU_GROUPE\n3", self.prompts_sent()[-1])
        self.assertEqual(turn.problem, "question au-delà de la limite du groupe")
        with self.assertRaises(FramingError):
            f.answer("on ne répond pas à une question non conforme")

    def test_a_later_group_allows_one_question_whatever_the_reopening(self) -> None:
        """Tests 26 à 31 et amendement A1 : « Continuer » et « Corriger un point »
        ouvrent un groupe de limite 2 dont l'apport est la première réponse."""
        for correction in (False, True):
            with self.subTest(correction=correction):
                f = self.framing(READY_OUT, QUESTION_OUT, QUESTION_OUT)
                f.start()
                self.assertIsNone(f.reopen("apport", correction=correction).problem)
                self.assertEqual((f.group, f.answers, f.limit), (2, 1, 2))
                self.assertIn("REPONSES_DANS_LE_GROUPE\n1", self.prompts_sent()[-1])
                turn = f.answer("deuxième réponse")
                self.assertEqual(turn.problem, "question au-delà de la limite du groupe")

    def test_groups_repeat_without_global_cap_and_never_close_alone(self) -> None:
        """Tests 32 et 33 : aucune proposition ne vaut clôture ni brouillon."""
        f = self.framing(*([READY_OUT] * 6))
        f.start()
        for _ in range(5):
            self.assertIsNone(f.reopen("encore", correction=False).problem)
            self.assertIsNone(f.draft)
        self.assertEqual(f.group, 6)
        self.assertEqual(len(self.fake.framing_sessions), 1)

    def test_closing_opens_no_group(self) -> None:
        """Test 34, puis test 36 : la rédaction est un échange de la même session."""
        f = self.framing(QUESTION_OUT, DRAFT_OUT)
        f.start()
        f.write_draft()
        self.assertEqual((f.group, f.answers), (1, 0))
        self.assertEqual(len(self.prompts_sent()), 2)
        self.assertEqual(self.prompts_sent()[-1], prompts.build_framing_draft())

    def test_continuing_after_the_draft_keeps_the_session(self) -> None:
        """Test 45 : « continuer le cadrage » après le brouillon."""
        f = self.framing(READY_OUT, DRAFT_OUT, READY_OUT)
        f.start()
        f.write_draft()
        self.assertIsNotNone(f.draft)
        self.assertIsNone(f.reopen("ajoute une contrainte", correction=False).problem)
        self.assertIsNone(f.draft)
        self.assertEqual(len(self.fake.framing_sessions), 1)


class TestCloseBeforeAnyExchange(FramingCase):
    def test_one_exchange_carries_the_idea_and_the_draft(self) -> None:
        """A2 : `/clore` avant le premier échange — F ne rédige jamais sans l'idée."""
        f = self.framing(DRAFT_OUT)
        turn = f.write_draft()
        self.assertIsNone(turn.problem)
        (prompt,) = self.prompts_sent()
        self.assertIn("Un cache pour FloraPi", prompt)
        self.assertIn("IABINOME:DEMANDE", prompt)
        self.assertEqual(f.session.exchanges, 1)


class TestDraft(FramingCase):
    def test_invalid_drafts_are_refused_and_never_retried_alone(self) -> None:
        """Tests 37 à 40."""
        broken = {
            "sans balise": fakes.DEMANDE_COMPLETE,
            "objectif vide": DRAFT_OUT.replace("Décider de la stratégie de cache.", ""),
            "section doublée": DRAFT_OUT + "\n## Livrable\nencore\n",
            "texte avant": "Voici la demande.\n" + DRAFT_OUT,
        }
        for label, reply in broken.items():
            with self.subTest(label):
                f = self.framing(reply)
                turn = f.write_draft()
                self.assertIsNotNone(turn.problem)
                self.assertIsNone(f.draft)
                self.assertEqual(f.session.exchanges, 1)

    def test_an_explicit_retry_stays_in_the_session(self) -> None:
        f = self.framing(QUESTION_OUT, "IABINOME:DEMANDE\nrien", DRAFT_OUT)
        f.start()
        self.assertIsNotNone(f.write_draft().problem)
        turn = f.retry()
        self.assertIsNone(turn.problem)
        self.assertIn("n'a pas pu être retenue", self.prompts_sent()[-1])
        self.assertEqual(len(self.fake.framing_sessions), 1)

    def test_a_failed_call_is_resent_as_is(self) -> None:
        """Le même envoi, dans la même session. Un premier tour en échec n'a établi
        aucune session : la relance en ouvre une, sans rien reprendre d'inconnu."""
        f = self.framing(QUESTION_OUT, QUESTION_OUT, READY_OUT, READY_OUT)
        self.fake.exit_codes = [1]
        self.assertEqual(f.start().problem, "CLI_FAILED code de retour 1")
        self.assertIsNone(f.retry().problem)
        self.fake.exit_codes = [1]
        self.assertIsNotNone(f.answer("réponse").problem)
        self.assertIsNone(f.retry().problem)
        abandoned, (first, answer, resent) = self.fake.framing_sessions.values()
        self.assertEqual(abandoned, [first])
        self.assertEqual(answer, resent)
        self.assertEqual(f.answers, 1)

    def test_validate_framed(self) -> None:
        self.assertEqual(demande.validate_framed(DRAFT_OUT.removeprefix("IABINOME:DEMANDE\n")), [])
        self.assertIn("« # Demande » attendu en tête", demande.validate_framed("## Objectif\nx"))


class TestSources(FramingCase):
    def test_the_agent_sees_only_the_copy(self) -> None:
        """Tests 5, 6 et 7 : la racine de F ne contient que `corpus/fichiers/`, et
        aucun prompt ne nomme le projet d'origine."""
        f = self.framing(QUESTION_OUT, sources={"note.md": "contenu"})
        f.start()
        work = f.root / "travail"
        self.assertEqual(
            sorted(p.relative_to(work).as_posix() for p in work.rglob("*")),
            ["corpus", "corpus/fichiers", "corpus/fichiers/note.md"],
        )
        self.assertNotIn(str(self.tmp / "projet"), self.prompts_sent()[0])
        self.assertTrue((f.root / "corpus" / "manifeste.json").is_file())

    def test_a_modified_copy_stops_the_framing(self) -> None:
        """Test 10 : `SOURCES_MODIFIED`, brouillon interdit, session fermée."""
        def tamper(history: list[str]) -> str:
            (f.root / "travail" / "corpus" / "fichiers" / "note.md").write_text("x", "utf-8")
            return DRAFT_OUT
        f = self.framing(tamper, sources={"note.md": "contenu"})
        turn = f.write_draft()
        self.assertTrue((turn.problem or "").startswith("SOURCES_MODIFIED"))
        self.assertIsNone(f.draft)
        self.assertTrue(f.session.closed)

    def test_no_source_is_fine_in_conception_not_in_research(self) -> None:
        """Tests 11 et 12."""
        self.assertIsNone(self.framing(QUESTION_OUT).start().problem)
        with self.assertRaisesRegex(FramingError, "recherche sans corpus"):
            framing.prepare(MissionKind.RECHERCHE)

    def test_discarding_closes_then_removes_everything(self) -> None:
        """Tests 13, 35 et 51 : annulation — session fermée, dossier détruit."""
        f = self.framing(QUESTION_OUT)
        f.start()
        f.discard()
        self.assertTrue(f.session.closed)
        self.assertFalse(f.root.exists())


class TestTranscript(FramingCase):
    def test_the_transcript_keeps_everything_and_warns(self) -> None:
        """§9.1 et test 19 : une correction n'efface rien de l'historique."""
        f = self.framing(QUESTION_OUT, READY_OUT, READY_OUT)
        f.start()
        f.answer("première réponse")
        f.reopen("je corrige", correction=True)
        text = (f.root / "transcription.md").read_text("utf-8")
        for needle in ("Historique non normatif", "Un cache pour FloraPi", "première réponse",
                       "## Correction humaine", "je corrige", "## F — proposition de clôture"):
            self.assertIn(needle, text)
        self.assertEqual(text.count("## F — proposition de clôture"), 2)
        self.assertTrue((f.root / "session.json").is_file())
        self.assertNotIn("fake-session", (f.root / "session.json").read_text("utf-8"))


class TestParser(unittest.TestCase):
    def test_a_preamble_is_tolerated_before_a_conversation_tag_only(self) -> None:
        reply = framing.parse_reply("Voici ma question.\n" + QUESTION_OUT, (QUESTION, READY))
        self.assertEqual(reply.kind, QUESTION)
        with self.assertRaisesRegex(framing.ProtocolError, "POURQUOI"):
            framing.parse_reply("IABINOME:CADRAGE_QUESTION\nQUESTION\nx\nETAT_CADRAGE\n",
                                (QUESTION,))
        with self.assertRaisesRegex(framing.ProtocolError, "inattendue"):
            framing.parse_reply(QUESTION_OUT, (DRAFT,))


if __name__ == "__main__":
    unittest.main()

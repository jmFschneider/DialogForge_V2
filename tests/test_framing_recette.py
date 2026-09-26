"""Recette du cadrage avec agent F (`conception/CADRAGE_AGENT.md` §14, §15 ; lot 6 de la
phase 6). Ce fichier ne rejoue pas ce que les lots 1 à 5 prouvent déjà, chacun là où il
a été écrit : il comble les points du §14 qui n'avaient pas de test propre — coût en
échanges (73, 74), échec de création (53), sortie de F qui reste du texte (80, 81),
périmètre (14, 49, 77, critère 24).

Faux agent seulement — jamais un fournisseur."""

import re
import unittest
from pathlib import Path
from unittest import mock

from iabinome import facade, framing
from iabinome.framing import READY
from tests.test_framing import DRAFT_OUT, QUESTION_OUT, READY_OUT, FramingCase
from tests.test_framing_creation import NOMINAL, FramingCliCase
from tests.test_gui_recette import TestPerimeter as GuiPerimeter

_SRC = Path(__file__).resolve().parent.parent / "src" / "iabinome"
_FRAMING_SOURCES = (
    _SRC / "framing.py", _SRC / "framing_cli.py", _SRC / "gui" / "views" / "cadrage.py",
)


class TestCostInExchanges(FramingCase):
    """Tests 73 et 74 : une session, et autant d'échanges que de tours de F."""

    def test_a_proposal_then_the_draft_is_one_session_and_two_exchanges(self) -> None:
        f = self.framing(READY_OUT, DRAFT_OUT)
        f.start()
        f.write_draft()
        self.assertEqual(len(self.fake.framing_sessions), 1)
        self.assertEqual(f.session.exchanges, 2)
        self.assertEqual(f.artifacts().provenance["exchange_count"], 2)

    def test_two_questions_a_proposal_then_the_draft_is_four_exchanges(self) -> None:
        f = self.framing(QUESTION_OUT, QUESTION_OUT, READY_OUT, DRAFT_OUT)
        f.start()
        f.answer("un")
        f.answer("deux")
        f.write_draft()
        self.assertEqual(len(self.fake.framing_sessions), 1)
        self.assertEqual(f.artifacts().provenance["exchange_count"], 4)


class TestAProposalShowsWhatIsUnanswered(unittest.TestCase):
    """P18 : une proposition sans `SANS_REPONSE` n'est pas conforme."""

    def test_a_proposal_without_its_unanswered_questions_is_refused(self) -> None:
        without = READY_OUT.replace("SANS_REPONSE\n", "")
        with self.assertRaisesRegex(framing.ProtocolError, "SANS_REPONSE"):
            framing.parse_reply(without, (READY,))


class TestWhatFSaysStaysText(FramingCase):
    """Tests 80 et 81 : une commande ou un patch rendu par F reste du texte du brouillon ;
    rien n'en devient un chemin, un `argv` ou une opération de fichier."""

    _PAYLOAD = "- Lancer `rm -rf ../projet` puis appliquer :\n```diff\n--- a/x\n+++ b/x\n```\n"

    def test_a_command_in_the_draft_is_kept_verbatim_and_nothing_else_is_written(self) -> None:
        draft = DRAFT_OUT.replace("## Contraintes\n", "## Contraintes\n" + self._PAYLOAD)
        self.assertNotEqual(draft, DRAFT_OUT)
        f = self.framing(draft)
        before = {p.name for p in f.root.iterdir()}
        self.assertIsNone(f.write_draft().problem)
        assert f.draft is not None
        self.assertIn(self._PAYLOAD, f.draft)
        self.assertEqual({p.name for p in f.root.iterdir()} - before, {"appels"})
        self.assertEqual(list((f.root / "travail").iterdir()), [], "rien d'écrit chez F")

    def test_the_framing_code_never_launches_anything_itself(self) -> None:
        """Le seul lancement de processus d'un tour est celui du transport commun."""
        launch = re.compile(r"\bsubprocess\b|os\.system|os\.popen|\bexec\(|\beval\(")
        for path in _FRAMING_SOURCES:
            with self.subTest(path.name):
                self.assertIsNone(launch.search(path.read_text(encoding="utf-8")))


class TestAFailedCreationLeavesNothing(FramingCliCase):
    """Test 53 : un échec pendant l'écriture des artefacts de cadrage ne laisse ni
    collaboration ni dossier provisoire ; le brouillon reste à l'écran de relecture."""

    def test_a_failure_while_copying_the_framing_leaves_no_partial_folder(self) -> None:
        real, seen = facade._write_framing, []

        def failing_once(*args: object) -> object:
            seen.append((self.collab.exists(), self.leftovers()))
            if len(seen) == 1:
                raise OSError("disque plein")
            return real(*args)  # type: ignore[arg-type]

        with mock.patch.object(facade, "_write_framing", side_effect=failing_once):
            code = self.new([*NOMINAL, "v"], QUESTION_OUT, READY_OUT, DRAFT_OUT)
        # Au second essai, rien n'est resté du premier : pas de collaboration, et un seul
        # dossier provisoire, celui de l'essai en cours. Puis la création aboutit.
        collab_existed, provisional = seen[1]
        self.assertFalse(collab_existed)
        self.assertEqual(len(provisional), 1)
        self.assertEqual(code, 0)
        self.assertTrue((self.collab / "cadrage" / "provenance.json").is_file())
        self.assertEqual(self.leftovers(), [])

    def leftovers(self) -> list[str]:
        return [p.name for p in self.root.iterdir() if p.name.startswith(".new-")]


class TestPerimeter(unittest.TestCase):
    """Critère 24 et tests 14, 49, 77 : le cadrage ne contourne aucun des cinq interdits,
    ne calcule ni coût ni jeton, et ne touche pas au moteur A/B."""

    _FORBIDDEN = {
        **GuiPerimeter._FORBIDDEN,
        "coût/jetons/quota": re.compile(r"\btokens?\b|\bquota\b|\bco[uû]t\b|\bprix\b", re.I),
        "moteur A/B": re.compile(r"^\s*from \. import .*\b(workflow|lock)\b", re.MULTILINE),
    }

    def test_the_framing_sources_avoid_the_excluded_mechanisms(self) -> None:
        for path in _FRAMING_SOURCES:
            text = path.read_text(encoding="utf-8")
            for name, pattern in self._FORBIDDEN.items():
                with self.subTest(file=path.name, forbidden=name):
                    self.assertIsNone(pattern.search(text))

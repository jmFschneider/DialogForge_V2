"""GUI V1, lot 4 : `facade.create_collaboration` — la création **partagée**
(`conception/GUI_V1.md` §6.1, §6.5) entre la CLI et la GUI. Testé sans Tk
(§15.1) : rien ici ne dépend de l'écran qui appelle.

`tests/test_cli.py` et `tests/test_effort.py` couvrent déjà `new` de bout en
bout ; ce module vérifie la même autorité, appelée directement — la preuve
qu'aucune règle n'a été dupliquée ni perdue au passage.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from iabinome import facade
from iabinome.models import MissionKind, ReviewerAccess
from tests import fakes


class CreationCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.a = fakes.FakeAdapter("fake-a", (), effort_levels=("low", "medium", "high"))
        self.b = fakes.FakeAdapter("fake-b", (), effort_levels=("low", "medium", "high"))
        self.adapters = {"fake-a": self.a, "fake-b": self.b}

    def request(self, **overrides: object) -> facade.CreationRequest:
        base: dict[str, object] = {
            "collab": self.root / "collab",
            "demande": facade.DemandeSource("Concevoir le cache.", "cadrage"),
            "kind": MissionKind.RECHERCHE, "reviewer_access": ReviewerAccess.CONSULT,
            "agent_a": "fake-a", "agent_b": "fake-b", "max_revisions": 2, "web_access": True,
        }
        base.update(overrides)
        return facade.CreationRequest(**base)  # type: ignore[arg-type]

    def refused(self, **overrides: object) -> str:
        with self.assertRaises(facade.CreationError) as ctx:
            facade.create_collaboration(self.request(**overrides), adapters=self.adapters)
        return str(ctx.exception)


class TestRefusalsLeaveNothingBehind(CreationCase):
    def test_an_existing_destination_is_refused(self) -> None:
        dest = self.root / "collab"
        dest.mkdir()
        self.assertIn("existe", self.refused())

    def test_source_root_without_source_list_is_refused(self) -> None:
        self.assertIn(
            "vont ensemble", self.refused(source_root=self.root / "src"),
        )
        self.assertFalse((self.root / "collab").exists())

    def test_research_without_any_source_is_refused(self) -> None:
        refusal = self.refused(kind=MissionKind.RECHERCHE, web_access=False)
        self.assertIn("recherche sans source", refusal)
        self.assertFalse((self.root / "collab").exists())

    def test_conception_without_an_input_folder_is_refused_even_with_the_web(self) -> None:
        refusal = self.refused(kind=MissionKind.CONCEPTION, web_access=True)
        self.assertIn("conception sans dossier d'entrée", refusal)
        self.assertFalse((self.root / "collab").exists())

    def test_research_with_an_empty_corpus_is_refused(self) -> None:
        """Plan de finalisation 2.3 : un refus explicite, plus une `FileNotFoundError` tombée
        en écrivant `manifeste.json` (aucun fichier copié ne créait le dossier `corpus/`).
        Le web ouvert n'y change rien : un corpus déclaré vide est une erreur de saisie."""
        src = self.root / "src"
        src.mkdir()
        listing = self.root / "vide.txt"
        listing.write_text("", encoding="utf-8")
        for web in (False, True):
            refusal = self.refused(
                kind=MissionKind.RECHERCHE, source_root=src, source_list=listing, web_access=web,
            )
            self.assertIn("corpus déclaré mais vide", refusal)
        self.assertFalse((self.root / "collab").exists())
        self.assertEqual(list(self.root.glob(".new-*")), [], "un dossier temporaire est resté")

    def test_an_unknown_adapter_is_refused(self) -> None:
        self.assertIn("adaptateur inconnu", self.refused(agent_a="un-outil-inconnu"))
        self.assertFalse((self.root / "collab").exists())

    def test_an_effort_the_adapter_does_not_know_is_refused(self) -> None:
        message = self.refused(effort_b="xhigh")
        self.assertIn("effort B", message)
        self.assertIn("low, medium, high", message)
        self.assertFalse((self.root / "collab").exists())

    def test_a_source_that_does_not_exist_leaves_no_partial_directory(self) -> None:
        src = self.root / "src"
        src.mkdir()
        listing = self.root / "liste.txt"
        listing.write_text("absent.md\n", encoding="utf-8")
        with self.assertRaises(facade.CreationError):
            facade.create_collaboration(
                self.request(kind=MissionKind.RECHERCHE, source_root=src, source_list=listing),
                adapters=self.adapters,
            )
        self.assertFalse((self.root / "collab").exists())
        self.assertEqual(list(self.root.glob(".new-*")), [])


class TestASuccessfulCreation(CreationCase):
    def test_a_conception_collaboration_is_created_ready(self) -> None:
        src = self.root / "src"
        src.mkdir()
        (src / "dossier.md").write_text("# Dossier de recherche", encoding="utf-8")
        listing = self.root / "liste.txt"
        listing.write_text("dossier.md\n", encoding="utf-8")
        result = facade.create_collaboration(
            self.request(kind=MissionKind.CONCEPTION, source_root=src, source_list=listing),
            adapters=self.adapters,
        )
        self.assertEqual(result.path, self.root / "collab")
        config = fakes.read_json(result.path / "configuration.json")
        self.assertEqual(config["mission_kind"], "CONCEPTION")
        self.assertEqual(config["agent_a"], {"adapter_id": "fake-a", "model": "fake-a-modele-a"})
        etat = fakes.read_json(result.path / "etat.json")
        self.assertEqual(etat["status"], "READY")
        self.assertEqual(etat["phase"], "PROPOSAL_A")

    def test_a_model_override_is_kept_over_the_adapter_default(self) -> None:
        result = facade.create_collaboration(
            self.request(model_a="un-modele-choisi"), adapters=self.adapters,
        )
        config = fakes.read_json(result.path / "configuration.json")
        self.assertEqual(config["agent_a"]["model"], "un-modele-choisi")

    def test_a_research_collaboration_carries_its_corpus(self) -> None:
        src = self.root / "src"
        src.mkdir()
        (src / "a.md").write_text("Contenu A", encoding="utf-8")
        listing = self.root / "liste.txt"
        listing.write_text("a.md\n", encoding="utf-8")
        result = facade.create_collaboration(
            self.request(kind=MissionKind.RECHERCHE, source_root=src, source_list=listing),
            adapters=self.adapters,
        )
        self.assertTrue((result.path / "corpus" / "fichiers" / "a.md").is_file())
        config = fakes.read_json(result.path / "configuration.json")
        self.assertIsNotNone(config["corpus_manifest_sha256"])

    def test_provenance_records_cadrage_for_a_direct_entry(self) -> None:
        result = facade.create_collaboration(self.request(), adapters=self.adapters)
        (entry,) = fakes.read_json(result.path / "provenance_demande.json")["versions"]
        self.assertEqual(entry["source"], "cadrage")
        self.assertIsNone(entry["path"])

    def test_provenance_records_the_imported_file_when_left_unchanged(self) -> None:
        result = facade.create_collaboration(
            self.request(demande=facade.DemandeSource(
                "Concevoir le cache.", "fichier", str(self.root / "demande.md"),
            )),
            adapters=self.adapters,
        )
        (entry,) = fakes.read_json(result.path / "provenance_demande.json")["versions"]
        self.assertEqual(entry["source"], "fichier")
        self.assertEqual(entry["path"], str(self.root / "demande.md"))

    def test_missing_sections_are_reported_but_do_not_block_creation(self) -> None:
        result = facade.create_collaboration(self.request(), adapters=self.adapters)
        self.assertIn("Objectif", result.missing_sections)

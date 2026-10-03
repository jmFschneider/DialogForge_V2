"""La liste éditable garde les identifiants exacts des modèles."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from iabinome import model_catalog


class TestModelCatalog(unittest.TestCase):
    def test_packaged_catalog_contains_exact_codex_id(self) -> None:
        models = model_catalog.load()
        self.assertIn("gpt-6-sol", models["codex"])
        self.assertNotIn("GPT-6-Sol", models["codex"])

    def test_an_invalid_catalog_is_rejected(self) -> None:
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "modeles.toml"
            path.write_text('[models]\ncodex = ["gpt-6-sol", "gpt-6-sol"]\n', encoding="utf-8")
            with self.assertRaisesRegex(model_catalog.ModelCatalogError, "liste invalide"):
                model_catalog.load(path)


class TestInheritedModel(unittest.TestCase):
    def test_a_missing_model_is_added_labelled_and_selected_as_itself(self) -> None:
        catalog: dict[str, tuple[str, ...]] = {"claude": ("a",)}
        extended, shown = model_catalog.inherit(catalog, "claude", "b")
        self.assertEqual(shown, "b (hérité de la recherche)")
        self.assertIn(shown, model_catalog.choices(extended, "claude"))
        self.assertEqual(model_catalog.selected(extended, "claude", shown), "b")
        self.assertEqual(catalog, {"claude": ("a",)})  # le catalogue d'origine est intact

    def test_a_known_model_is_left_alone_and_a_repeat_adds_nothing(self) -> None:
        catalog: dict[str, tuple[str, ...]] = {"claude": ("a",)}
        self.assertEqual(model_catalog.inherit(catalog, "claude", "a"), (catalog, "a"))
        once, shown = model_catalog.inherit(catalog, "claude", "b")
        twice, again = model_catalog.inherit(once, "claude", "b")
        self.assertEqual((twice, again), (once, shown))

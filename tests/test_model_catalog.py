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

"""La documentation utilisateur ne dérive pas en silence (plan V2, 3.3).

Ce que ces tests **vérifient** : que chaque commande et chaque option de la CLI est nommée dans
`docs/COMMANDES.md`, que chaque clé de `iabinome.toml` l'est dans `docs/CONFIGURATION.md`, que
chaque option a un texte d'aide, que les exemples sont acceptés par `new`, et que les liens
relatifs de la documentation mènent quelque part.

Ce qu'ils **ne vérifient pas** : que le texte est *vrai*. Ajouter une option, c'est aussi relire la
page qui la décrit.

`cli.ADAPTERS` est substitué et `settings.SEARCH_PATHS` vidé, comme dans `test_cli.py` (`RULES.md`).
"""

from __future__ import annotations

import argparse
import io
import json
import re
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from iabinome import cli, settings
from tests import fakes

ROOT = Path(__file__).resolve().parent.parent
COMMANDES = (ROOT / "docs" / "COMMANDES.md").read_text(encoding="utf-8")
CONFIGURATION = (ROOT / "docs" / "CONFIGURATION.md").read_text(encoding="utf-8")
MARKDOWN = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]


def _subparsers() -> dict[str, argparse.ArgumentParser]:
    for action in cli.build_parser()._actions:
        if isinstance(action, argparse._SubParsersAction):
            return dict(action.choices)
    raise AssertionError("aucune sous-commande")


def _options(parser: argparse.ArgumentParser) -> list[str]:
    return [
        option
        for action in parser._actions
        for option in action.option_strings
        if option not in ("-h", "--help")
    ]


def _section(text: str, title: str) -> str:
    """Le corps de la section `## <title>`, jusqu'à la suivante (vide si elle n'existe pas)."""
    match = re.search(rf"(?ms)^## {re.escape(title)}\n(.*?)(?=^## |\Z)", text)
    return match.group(1) if match else ""


def _anchors(text: str) -> set[str]:
    """Les ancres d'un fichier Markdown, à la façon de GitHub : minuscules, sans ponctuation."""
    titles = re.findall(r"^#{1,6}[ \t]+(.*?)[ \t]*$", text, re.MULTILINE)
    return {re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-") for title in titles}


class TestCommandsAreDocumented(unittest.TestCase):
    def test_every_command_has_its_section(self) -> None:
        for name in _subparsers():
            with self.subTest(command=name):
                self.assertIn(f"\n## {name}\n", COMMANDES)

    def test_every_option_is_named_in_its_own_command_section(self) -> None:
        # Dans **sa** section : `--timeout` décrit pour `run` ne couvre pas `decide`.
        for name, parser in _subparsers().items():
            section = _section(COMMANDES, name)
            for option in _options(parser):
                with self.subTest(command=name, option=option):
                    self.assertIn(f"`{option}", section)

    def test_every_setting_is_documented_and_exemplified(self) -> None:
        exemple = (ROOT / "iabinome.toml.exemple").read_text(encoding="utf-8")
        for key in settings._SPEC:
            with self.subTest(key=key):
                self.assertIn(f"`{key}`", CONFIGURATION)
                self.assertRegex(exemple, rf"(?m)^#?\s*{key}\s*=")

    def test_the_example_settings_file_is_accepted(self) -> None:
        loaded = settings.load(str(ROOT / "iabinome.toml.exemple"))
        self.assertIn("agent_a", loaded.values)


class TestEveryOptionHasHelp(unittest.TestCase):
    def test_the_commands_and_their_arguments_are_explained(self) -> None:
        parser = cli.build_parser()
        listing = next(
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        for choice in listing._get_subactions():
            with self.subTest(command=choice.dest):
                self.assertTrue(choice.help)
        for name, sub in _subparsers().items():
            for action in sub._actions:
                if isinstance(action, argparse._HelpAction):
                    continue
                with self.subTest(command=name, argument=action.dest):
                    self.assertTrue(action.help)


class TestExamplesAreAccepted(unittest.TestCase):
    """Les commandes de la documentation, rejouées : `new` ne consomme aucun quota."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        adapters = {
            "fake-a": fakes.FakeAdapter("fake-a", ()), "fake-b": fakes.FakeAdapter("fake-b", ()),
        }
        for patcher in (
            mock.patch.object(cli, "ADAPTERS", adapters),
            mock.patch.object(settings, "SEARCH_PATHS", ()),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def _new(self, *args: str) -> tuple[int, str]:
        err = io.StringIO()
        with redirect_stderr(err):
            code = cli.main([
                "new", str(self.root / "collab"), "--reviewer-access", "consult",
                "--agent-a", "fake-a", "--agent-b", "fake-b", "--max-revisions", "1", *args,
            ])
        return code, err.getvalue()

    def test_the_design_request_is_complete(self) -> None:
        code, err = self._new(
            "--demande", str(ROOT / "exemples" / "demande-conception.md"),
            "--kind", "conception",
        )
        self.assertEqual(code, 0, err)
        self.assertNotIn("absente", err)

    def test_the_research_request_and_its_corpus_are_accepted(self) -> None:
        code, err = self._new(
            "--demande", str(ROOT / "exemples" / "demande-recherche.md"), "--kind", "recherche",
            "--source-root", str(ROOT / "exemples"),
            "--source-list", str(ROOT / "exemples" / "corpus.txt"),
        )
        self.assertEqual(code, 0, err)
        self.assertNotIn("absente", err)
        manifest = json.loads(
            (self.root / "collab" / "corpus" / "manifeste.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            sorted(entry["chemin"] for entry in manifest["files"]),
            ["corpus/incident-disque.md", "corpus/politique-retention.md"],
        )


class TestLinksResolve(unittest.TestCase):
    def test_every_relative_link_leads_somewhere(self) -> None:
        for source in MARKDOWN:
            text = source.read_text(encoding="utf-8")
            for target, anchor in re.findall(r"\]\(([^)#\s]*)(?:#([^)\s]*))?\)", text):
                if target.startswith(("http://", "https://")):
                    continue
                with self.subTest(source=source.name, target=target, anchor=anchor):
                    destination = source if not target else (source.parent / target).resolve()
                    self.assertTrue(destination.exists(), f"{destination} introuvable")
                    if anchor and destination.suffix == ".md":
                        found = _anchors(destination.read_text(encoding="utf-8"))
                        self.assertIn(anchor, found)


if __name__ == "__main__":
    unittest.main()

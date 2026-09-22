"""Tests du fichier de configuration — `iabinome.settings` et sa jonction CLI.

Deux garanties tenues ici, et elles ne sont pas du même ordre :

1. **La précédence** — drapeau CLI > fichier > défaut du programme. C'est ce
   qui rend le fichier utilisable sans devenir un piège.
2. **Le refus** — clé inconnue, type inattendu, valeur hors domaine. Un réglage
   silencieusement ignoré est pire qu'un réglage absent, parce qu'on croit
   l'avoir posé (`C2b`).

`settings.SEARCH_PATHS` est vidé partout : sans cela, un `dialogforge.toml` du
dépôt ou du dossier personnel rendrait ces tests dépendants de la machine.
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from iabinome import cli, demande, settings
from iabinome.models import Role
from tests import fakes

# Saisi **avant** que `setUp` ne vide l'attribut : c'est l'ordre de recherche
# réel du programme, celui que ces tests ont à vérifier.
DEFAULT_SEARCH_PATHS = settings.SEARCH_PATHS


class SettingsCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.demande = self.root / "demande.md"
        self.demande.write_text("Concevoir le cache.", encoding="utf-8")
        self.collab = self.root / "collaboration"
        patcher = mock.patch.object(
            cli, "ADAPTERS",
            {"fake-a": fakes.FakeAdapter("fake-a", ()), "fake-b": fakes.FakeAdapter("fake-b", ())},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        blank = mock.patch.object(settings, "SEARCH_PATHS", ())
        blank.start()
        self.addCleanup(blank.stop)

    def write_config(self, body: str) -> str:
        path = self.root / "dialogforge.toml"
        path.write_text(body, encoding="utf-8")
        return str(path)

    def config(self) -> dict[str, object]:
        payload = json.loads((self.collab / "configuration.json").read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        return payload


class TestLoading(SettingsCase):
    def test_no_file_anywhere_is_not_an_error(self) -> None:
        found = settings.load(None)
        self.assertIsNone(found.path)
        self.assertEqual(found.values, {})

    def test_the_first_search_path_wins_and_the_second_is_ignored(self) -> None:
        """Jamais de fusion : deux fichiers rendraient indevinable d'ou vient
        une valeur."""
        first, second = self.root / "un.toml", self.root / "deux.toml"
        first.write_text('model_a = "premier"\n', encoding="utf-8")
        second.write_text('model_a = "second"\nmodel_b = "jamais lu"\n', encoding="utf-8")
        with mock.patch.object(settings, "SEARCH_PATHS", (first, second)):
            found = settings.load(None)
        self.assertEqual(found.path, first)
        self.assertEqual(found.values, {"model_a": "premier"})

    def test_a_missing_search_path_is_skipped(self) -> None:
        real = self.root / "reel.toml"
        real.write_text('model_a = "opus"\n', encoding="utf-8")
        with mock.patch.object(settings, "SEARCH_PATHS", (self.root / "absent.toml", real)):
            self.assertEqual(settings.load(None).path, real)

    def test_the_search_order_puts_the_current_names_before_the_former_ones(self) -> None:
        """Le nouveau nom gagne toujours ; l'ancien n'est qu'un dernier recours."""
        names = [path.name for path in DEFAULT_SEARCH_PATHS]
        self.assertEqual(names, ["dialogforge.toml", "reglages.toml",
                                 "iabinome.toml", ".iabinome.toml"])

    def test_a_former_file_name_is_still_read_and_says_so(self) -> None:
        """Decision du PO (2026-09-22) : cesser de le lire **en silence** ferait
        chercher la panne ailleurs — le reglage s'applique, et on dit quoi
        renommer."""
        former = self.root / "iabinome.toml"
        former.write_text('model_a = "opus"\n', encoding="utf-8")
        with mock.patch.object(settings, "SEARCH_PATHS", (former,)):
            found = settings.load(None)
        self.assertEqual(found.values, {"model_a": "opus"})
        self.assertIsNotNone(found.legacy_note)
        self.assertIn("dialogforge.toml", str(found.legacy_note))

    def test_the_current_name_is_read_without_a_word(self) -> None:
        current = Path(self.write_config("timeout = 60\n"))
        with mock.patch.object(settings, "SEARCH_PATHS", (current,)):
            self.assertIsNone(settings.load(None).legacy_note)

    def test_an_explicit_config_that_does_not_exist_is_an_error(self) -> None:
        """Le demander et ne pas l'avoir n'est pas un silence : `--config` est
        un ordre, les emplacements implicites sont une commodite."""
        with self.assertRaises(settings.SettingsError):
            settings.load(str(self.root / "jamais-ecrit.toml"))

    def test_an_unparsable_file_is_refused(self) -> None:
        with self.assertRaises(settings.SettingsError):
            settings.load(self.write_config("ceci n est pas du toml\n"))


class TestValidation(SettingsCase):
    def refused(self, body: str) -> str:
        with self.assertRaises(settings.SettingsError) as caught:
            settings.load(self.write_config(body))
        return str(caught.exception)

    def test_an_unknown_key_is_refused_and_names_what_is_expected(self) -> None:
        message = self.refused('budget_max = 12\n')
        self.assertIn("budget_max", message)
        self.assertIn("agent_a", message)

    def test_a_path_is_not_settable(self) -> None:
        """Aucun chemin ne se regle : un corpus fixe dans un fichier global
        rendrait la collaboration non reproductible d'une machine a l'autre."""
        self.assertIn("source_root", self.refused('source_root = "."\n'))

    def test_a_wrong_type_is_refused(self) -> None:
        self.assertIn("max_revisions", self.refused('max_revisions = "deux"\n'))

    def test_a_boolean_is_not_an_integer(self) -> None:
        """`bool` est un `int` en Python : sans refus explicite,
        `max_revisions = true` passerait pour `1`."""
        self.assertIn("max_revisions", self.refused("max_revisions = true\n"))

    def test_an_integer_is_accepted_where_a_float_is_expected(self) -> None:
        """`timeout = 600` est la forme qu'on ecrit naturellement."""
        found = settings.load(self.write_config("timeout = 600\n"))
        self.assertEqual(found.values["timeout"], 600)

    def test_a_float_is_not_accepted_where_an_integer_is_expected(self) -> None:
        self.assertIn("max_revisions", self.refused("max_revisions = 1.5\n"))


class TestPrecedence(SettingsCase):
    """Drapeau CLI > fichier > defaut du programme > defaut de l'adaptateur."""

    def new(self, *extra: str, config: str | None = None) -> int:
        argv = ["new", str(self.collab), "--demande", str(self.demande)]
        if config is not None:
            argv += ["--config", config]
        code: int = cli.main([*argv, *extra])
        return code

    def test_the_former_file_name_is_announced_before_what_it_supplied(self) -> None:
        """Le fichier agit, et la commande dit **les deux** : qu'il porte un
        ancien nom, et ce qu'elle y a pris."""
        former = self.root / "iabinome.toml"
        former.write_text(
            'agent_a = "fake-a"\nagent_b = "fake-b"\n'
            'kind = "conception"\nreviewer_access = "consult"\n',
            encoding="utf-8",
        )
        err = io.StringIO()
        with mock.patch.object(settings, "SEARCH_PATHS", (former,)), redirect_stderr(err):
            code = self.new()
        self.assertEqual(code, 0, err.getvalue())
        self.assertIn("ancien nom de fichier", err.getvalue())
        self.assertIn("dialogforge.toml", err.getvalue())
        self.assertIn("configuration :", err.getvalue())

    def test_the_file_supplies_what_the_command_line_omits(self) -> None:
        path = self.write_config(
            'agent_a = "fake-a"\nagent_b = "fake-b"\n'
            'kind = "conception"\nreviewer_access = "consult"\n'
            'model_b = "un-modele-du-fichier"\nmax_revisions = 7\n'
        )
        with redirect_stderr(io.StringIO()):
            self.assertEqual(self.new(config=path), 0)
        config = self.config()
        self.assertEqual(config["max_revisions"], 7)
        self.assertEqual(
            config["agent_b"], {"adapter_id": "fake-b", "model": "un-modele-du-fichier"}
        )

    def test_a_command_line_flag_beats_the_file(self) -> None:
        path = self.write_config(
            'agent_a = "fake-a"\nagent_b = "fake-b"\n'
            'kind = "conception"\nreviewer_access = "consult"\nmax_revisions = 7\n'
        )
        with redirect_stderr(io.StringIO()):
            self.assertEqual(self.new("--max-revisions", "0", config=path), 0)
        self.assertEqual(self.config()["max_revisions"], 0)

    def test_zero_from_the_command_line_is_not_mistaken_for_absent(self) -> None:
        """`0` est faux en Python : une resolution ecrite avec `or` aurait
        rendu `--max-revisions 0` inoperant, et silencieusement."""
        path = self.write_config(
            'agent_a = "fake-a"\nagent_b = "fake-b"\n'
            'kind = "conception"\nreviewer_access = "consult"\nmax_revisions = 5\n'
        )
        with redirect_stderr(io.StringIO()):
            self.assertEqual(self.new("--max-revisions", "0", config=path), 0)
        self.assertEqual(self.config()["max_revisions"], 0)

    def test_the_program_default_applies_when_nothing_else_does(self) -> None:
        self.assertEqual(
            self.new(
                "--agent-a", "fake-a", "--agent-b", "fake-b",
                "--kind", "conception", "--reviewer-access", "consult",
            ),
            0,
        )
        self.assertEqual(self.config()["max_revisions"], 2)

    def test_the_adapter_default_still_names_the_model(self) -> None:
        """Le fichier ne remplace pas `default_model()` : il ne fait que le
        devancer quand il dit quelque chose."""
        self.assertEqual(
            self.new(
                "--agent-a", "fake-a", "--agent-b", "fake-b",
                "--kind", "conception", "--reviewer-access", "consult",
            ),
            0,
        )
        agent_a = self.config()["agent_a"]
        assert isinstance(agent_a, dict)
        self.assertEqual(
            agent_a["model"], fakes.FakeAdapter("fake-a", ()).default_model(Role.A)
        )


class TestRefusalsFromTheFile(SettingsCase):
    """Une mauvaise valeur dans le fichier n'est pas une erreur d'usage :
    `argparse` ne l'a jamais vue. C'est un refus avant mutation — **code 1**,
    et la collaboration n'existe pas."""

    def refused_new(self, body: str) -> str:
        path = self.write_config(body)
        with redirect_stderr(io.StringIO()) as err:
            code = cli.main([
                "new", str(self.collab), "--demande", str(self.demande), "--config", path,
            ])
        self.assertEqual(code, 1)
        self.assertFalse(self.collab.exists())
        return err.getvalue()

    def test_an_unknown_agent_in_the_file_is_refused(self) -> None:
        message = self.refused_new(
            'agent_a = "un-outil-inconnu"\nagent_b = "fake-b"\n'
            'kind = "conception"\nreviewer_access = "consult"\n'
        )
        self.assertIn("un-outil-inconnu", message)

    def test_an_unknown_kind_in_the_file_is_refused(self) -> None:
        self.assertIn("roman", self.refused_new(
            'agent_a = "fake-a"\nagent_b = "fake-b"\n'
            'kind = "roman"\nreviewer_access = "consult"\n'
        ))

    def test_a_negative_max_revisions_in_the_file_is_refused(self) -> None:
        self.refused_new(
            'agent_a = "fake-a"\nagent_b = "fake-b"\n'
            'kind = "conception"\nreviewer_access = "consult"\nmax_revisions = -1\n'
        )

    def test_a_nan_timeout_in_the_file_is_refused(self) -> None:
        """C-08 : `time.monotonic() >= deadline` reste **faux** pour `nan`, si
        bien que le delai dur ne se declencherait jamais. Refuse a l'entree
        CLI ; il doit l'etre aussi ici."""
        path = self.write_config("timeout = nan\n")
        with redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["run", str(self.collab), "--config", path]), 1)


class TestVisibility(SettingsCase):
    def test_the_command_says_which_file_served_and_what_it_took(self) -> None:
        """Un reglage qui agit sans se montrer est la moitie d'un etat cache."""
        path = self.write_config(
            'agent_a = "fake-a"\nagent_b = "fake-b"\n'
            'kind = "conception"\nreviewer_access = "consult"\nmax_revisions = 3\n'
        )
        with redirect_stderr(io.StringIO()) as err:
            self.assertEqual(cli.main([
                "new", str(self.collab), "--demande", str(self.demande), "--config", path,
            ]), 0)
        note = err.getvalue()
        self.assertIn(str(path), note)
        self.assertIn("max_revisions", note)

    def test_nothing_is_said_when_no_file_is_found(self) -> None:
        # Une demande complète : la note de format (lot 1, 1.1) parle aussi sur
        # `stderr`, et ce test porte sur le silence de la **configuration**.
        self.demande.write_text(
            "".join(f"## {name}\nx\n" for name in demande.SECTIONS), encoding="utf-8"
        )
        with redirect_stderr(io.StringIO()) as err:
            cli.main([
                "new", str(self.collab), "--demande", str(self.demande),
                "--agent-a", "fake-a", "--agent-b", "fake-b",
                "--kind", "conception", "--reviewer-access", "consult",
            ])
        self.assertEqual(err.getvalue(), "")


class TestScope(SettingsCase):
    """Le fichier fournit des defauts au `new`, jamais un etat.

    Une fois la collaboration creee, `configuration.json` est la seule verite :
    editer le fichier ne deplace pas ce qui tourne deja.
    """

    def test_editing_the_file_does_not_change_an_existing_collaboration(self) -> None:
        path = self.write_config(
            'agent_a = "fake-a"\nagent_b = "fake-b"\n'
            'kind = "conception"\nreviewer_access = "consult"\nmax_revisions = 4\n'
        )
        with redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main([
                "new", str(self.collab), "--demande", str(self.demande), "--config", path,
            ]), 0)
        before = (self.collab / "configuration.json").read_bytes()
        Path(path).write_text(
            'agent_a = "fake-b"\nagent_b = "fake-a"\nmax_revisions = 99\n', encoding="utf-8"
        )
        with redirect_stderr(io.StringIO()):
            cli.main(["status", str(self.collab)])
        self.assertEqual((self.collab / "configuration.json").read_bytes(), before)

    def test_status_takes_no_config_flag(self) -> None:
        """Lecture seule : rien a regler, donc pas de drapeau qui laisserait
        croire le contraire."""
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                cli.main(["status", str(self.collab), "--config", "peu-importe"])
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()

"""Dossier de mission (`conception/PARCOURS_MISSION_CONCEPTION.md` §3 et §9, lot 2).

`mission.json` rattache et fait naviguer : il ne porte aucun état d'exécution. Ces tests couvrent le
registre strict, la création et le rattachement (AC07, AC09), la navigation commune CLI/GUI, la
reprise sans doublon, et la procédure de regroupement de Mastermind sur une réplique de sa
disposition réelle (AC08). Faux agents seulement : aucun appel fournisseur.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any
from unittest import mock

from iabinome import cli, decisions, facade, lock, mission, settings, workflow
from iabinome.gui import recents
from iabinome.gui.views.accueil import AccueilView
from iabinome.gui.views.creation import CreationView
from iabinome.gui.views.suivi import SuiviView
from iabinome.models import MissionKind, ReviewerAccess
from tests import fakes
from tests.test_follow_up import FollowUpCase
from tests.test_gui_views import _ROOT, _find_button, label_texts

_QUESTION = "IABINOME:QUESTION\nQuel est le critere de fin ?"
_DOC = "IABINOME:DOCUMENT\n# Plan\nLe plan."


def tree(folder: Path) -> dict[str, str]:
    """Empreinte de tous les fichiers et dossiers : la preuve qu'un dossier n'a pas bougé."""
    return mission._fingerprint(folder)


class MissionCase(FollowUpCase):
    def setUp(self) -> None:
        super().setUp()
        self.mission_root = self.root_dir / "Mission"

    def write_registry(self, steps: list[Any], **overrides: object) -> Path:
        self.mission_root.mkdir(exist_ok=True)
        payload = {"schema_version": 1, "name": "Mission", "steps": steps, **overrides}
        path = self.mission_root / mission.REGISTRY
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def accepted_research_at(self, rel: str) -> Path:
        """Une recherche acceptée, rangée à `rel` dans la mission (`.` : à la racine)."""
        research = self.research()
        target = self.mission_root if rel == "." else self.mission_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(research, target)
        return target

    def attached_research(self, rel: str = "recherche") -> Path:
        research = self.accepted_research_at(rel)
        mission.attach(self.mission_root, research, "recherche")
        return research

    def conception_request(self, rel: str, **overrides: object) -> facade.CreationRequest:
        base: dict[str, object] = {
            "collab": self.mission_root / rel,
            "demande": facade.DemandeSource("Concevoir le jeu.", "cadrage"),
            "kind": MissionKind.CONCEPTION, "reviewer_access": ReviewerAccess.CONSULT,
            "agent_a": "fake-a", "agent_b": "fake-b", "max_revisions": 1,
            "mission": self.mission_root,
        }
        base.update(overrides)
        return facade.CreationRequest(**base)  # type: ignore[arg-type]

    def create(self, request: facade.CreationRequest) -> Path:
        return facade.create_collaboration(request, adapters=self.adapters).path

    def refusal(self, request: facade.CreationRequest) -> str:
        with self.assertRaises(facade.CreationError) as caught:
            facade.create_collaboration(request, adapters=self.adapters)
        return str(caught.exception)

    def steps(self) -> list[tuple[str, str, str | None]]:
        return [(s.path, s.role, s.source) for s in mission.load(self.mission_root).steps]

    def cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(cli, "ADAPTERS", self.adapters), \
                mock.patch.object(settings, "SEARCH_PATHS", ()), \
                redirect_stdout(out), redirect_stderr(err):
            return cli.main(list(argv)), out.getvalue(), err.getvalue()


class TestTheRegistry(MissionCase):
    def invalid(self, steps: list[Any], **overrides: object) -> str:
        path = self.write_registry(steps, **overrides)
        before = path.read_bytes()
        with self.assertRaises(mission.MissionError) as caught:
            mission.load(self.mission_root)
        self.assertEqual(path.read_bytes(), before, "un registre invalide n'est jamais réécrit")
        return str(caught.exception)

    def test_a_valid_registry_round_trips(self) -> None:
        self.write_registry([
            {"path": ".", "role": "recherche", "source": None},
            {"path": "conception", "role": "conception", "source": "."},
        ])
        loaded = mission.load(self.mission_root)
        self.assertEqual([s.path for s in loaded.steps], [".", "conception"])
        self.assertEqual(loaded.steps[1].source, ".")

    def test_unsafe_paths_are_refused(self) -> None:
        for bad in ("../autre", "/abs", "C:/x", "a\\b", "a//b", "./a", ""):
            with self.subTest(path=bad):
                message = self.invalid([{"path": bad, "role": "recherche", "source": None}])
                self.assertIn("mission.json", message)

    def test_a_path_appears_once_and_a_source_must_be_earlier(self) -> None:
        twice = [{"path": "a", "role": "recherche", "source": None}] * 2
        self.assertIn("deux fois", self.invalid(twice))
        forward = [
            {"path": "c", "role": "conception", "source": "r"},
            {"path": "r", "role": "recherche", "source": None},
        ]
        self.assertIn("antérieure", self.invalid(forward))

    def test_a_source_must_name_an_earlier_registered_step(self) -> None:
        """Une référence inexistante est refusée comme une référence vers le futur."""
        unknown = [{"path": "c", "role": "conception", "source": "absente"}]
        self.assertIn("antérieure inscrite", self.invalid(unknown))
        own = [{"path": "c", "role": "conception", "source": "c"}]
        self.assertIn("antérieure inscrite", self.invalid(own))
        self.write_registry([
            {"path": "r", "role": "recherche", "source": None},
            {"path": "c", "role": "conception", "source": "r"},
        ])
        self.assertEqual(mission.load(self.mission_root).steps[1].source, "r")

    def test_unknown_role_schema_keys_and_unreadable_files_are_diagnosed(self) -> None:
        self.assertIn("rôle", self.invalid([{"path": "a", "role": "x", "source": None}]))
        self.assertIn("schéma", self.invalid([], schema_version=2))
        self.assertIn("clés", self.invalid([{"path": "a", "role": "revue"}]))
        self.write_registry([])
        (self.mission_root / mission.REGISTRY).write_text("{pas du json", encoding="utf-8")
        with self.assertRaises(mission.MissionError):
            mission.load(self.mission_root)

    def test_a_link_leaving_the_mission_is_refused(self) -> None:
        outside = self.root_dir / "dehors"
        outside.mkdir()
        self.mission_root.mkdir()
        link = self.mission_root / "lien"
        try:
            os.symlink(outside, link, target_is_directory=True)
        except OSError:
            made = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True,
            )
            if made.returncode != 0:
                self.skipTest("ni lien symbolique ni jonction disponibles")
        message = self.invalid([{"path": "lien", "role": "recherche", "source": None}])
        self.assertIn("hors de la mission", message)


class TestCreationInAMission(MissionCase):
    def test_a_new_mission_is_created_with_its_first_step(self) -> None:
        collab = self.create(self.conception_request("conception"))
        self.assertEqual(collab, self.mission_root / "conception")
        self.assertEqual(self.steps(), [("conception", "conception", None)])
        self.assertEqual(mission.load(self.mission_root).name, "Mission")
        self.assertFalse((self.mission_root / mission.LOCK).exists(), "verrou libéré")
        facade.inspect_collaboration(collab)

    def test_an_independent_creation_writes_no_registry(self) -> None:
        request = self.conception_request("x", mission=None, collab=self.root_dir / "seule")
        self.create(request)
        self.assertFalse((self.root_dir / mission.REGISTRY).exists())
        self.assertIsNone(mission.locate(self.root_dir / "seule"))

    def test_a_conception_is_continued_not_doubled(self) -> None:
        """AC07 : la seconde demande ne crée pas de seconde collaboration implicite."""
        self.create(self.conception_request("conception"))
        before = self.steps()
        message = self.refusal(self.conception_request("autre"))
        self.assertIn("a déjà une étape conception", message)
        self.assertIn("nouvelle version", message)
        self.assertFalse((self.mission_root / "autre").exists())
        self.assertEqual(self.steps(), before)

    def test_a_new_version_is_explicit_and_numbered(self) -> None:
        self.create(self.conception_request("conception"))
        self.assertIn("attendu", self.refusal(
            self.conception_request("v2", new_version=True)
        ))
        self.create(self.conception_request("conception-002", new_version=True))
        self.create(self.conception_request("conception-003", new_version=True))
        self.assertEqual([p for p, _, _ in self.steps()],
                         ["conception", "conception-002", "conception-003"])
        for rel in ("conception", "conception-002"):  # les anciennes restent consultables
            facade.inspect_collaboration(self.mission_root / rel)

    def test_a_new_version_needs_a_first_one(self) -> None:
        message = self.refusal(self.conception_request("conception", new_version=True))
        self.assertIn("aucune étape conception", message)

    def test_a_step_must_be_inside_the_mission(self) -> None:
        message = self.refusal(self.conception_request("x", collab=self.root_dir / "ailleurs"))
        self.assertIn("n'est pas contenu", message)
        self.assertFalse((self.root_dir / "ailleurs").exists())

    def test_the_transition_is_registered_with_its_source(self) -> None:
        self.attached_research("recherche")
        follow_up = self.prepared(self.mission_root / "recherche")
        request = self.conception_request("conception", follow_up=follow_up)
        collab = self.create(request)
        self.assertEqual(self.steps()[-1], ("conception", "conception", "recherche"))
        transition = json.loads((collab / facade.TRANSITION).read_text(encoding="utf-8"))
        self.assertEqual(transition["source_path"], "recherche")

    def test_a_transition_from_a_research_at_the_root(self) -> None:
        self.attached_research(".")
        follow_up = self.prepared(self.mission_root)
        collab = self.create(self.conception_request("conception", follow_up=follow_up))
        self.assertEqual(self.steps(), [
            (".", "recherche", None), ("conception", "conception", "."),
        ])
        transition = json.loads((collab / facade.TRANSITION).read_text(encoding="utf-8"))
        self.assertEqual(transition["source_path"], ".")

    def test_a_research_outside_the_registry_is_not_a_source(self) -> None:
        self.accepted_research_at("recherche")  # présente mais non rattachée
        follow_up = self.prepared(self.mission_root / "recherche")
        message = self.refusal(self.conception_request("conception", follow_up=follow_up))
        self.assertIn("n'est pas rattachée", message)
        self.assertFalse((self.mission_root / "conception").exists())

    def test_a_historical_collaboration_at_the_root_is_attached_first(self) -> None:
        self.accepted_research_at(".")
        message = self.refusal(self.conception_request("conception"))
        self.assertIn("mission attach", message)
        self.assertFalse((self.mission_root / mission.REGISTRY).exists())

    def test_the_mission_lock_refuses_without_creating(self) -> None:
        self.mission_root.mkdir()
        with lock.acquire(self.mission_root / mission.LOCK, "autre"):
            message = self.refusal(self.conception_request("conception"))
        self.assertIn("verrou", message.lower())
        self.assertFalse((self.mission_root / "conception").exists())


class TestARegistrationFailure(MissionCase):
    """AC09 : la collaboration valide est conservée, rattachée ensuite, sans rien repayer."""

    def test_the_valid_collaboration_is_kept_then_attached(self) -> None:
        with mock.patch.object(mission, "_save", side_effect=OSError("disque plein")):
            message = self.refusal(self.conception_request("conception"))
        self.assertIn("mission attach", message)
        collab = self.mission_root / "conception"
        facade.inspect_collaboration(collab)
        self.assertFalse((self.mission_root / mission.REGISTRY).exists())
        before = tree(collab)
        self.mission_root.mkdir(exist_ok=True)
        mission.attach(self.mission_root, collab, "conception")
        self.assertEqual(self.steps(), [("conception", "conception", None)])
        self.assertEqual(tree(collab), before, "le rattachement n'écrit pas dans la collaboration")
        self.assertEqual((self.adapters["fake-a"].calls, self.adapters["fake-b"].calls), (0, 0))

    def test_the_summary_proposes_the_attachment_and_flags_partial_folders(self) -> None:
        self.create(self.conception_request("conception"))
        orphan = fakes.collaboration(self.root_dir / "tmp")
        shutil.move(orphan, self.mission_root / "conception-002")
        (self.mission_root / "recherche").mkdir()
        (self.mission_root / ".new-x-1234").mkdir()
        summary = mission.summarize(self.mission_root)
        self.assertEqual(summary.to_attach, ("conception-002",))
        self.assertEqual(sorted(summary.partial), [".new-x-1234", "recherche"])

    def test_nothing_is_overwritten_at_an_occupied_location(self) -> None:
        self.create(self.conception_request("conception"))
        orphan = fakes.collaboration(self.root_dir / "tmp")
        shutil.move(orphan, self.mission_root / "conception-002")
        occupied = tree(self.mission_root / "conception-002")
        message = self.refusal(self.conception_request("conception-002", new_version=True))
        self.assertIn("existe déjà et n'est pas rattaché", message)
        self.assertEqual(tree(self.mission_root / "conception-002"), occupied)
        shutil.rmtree(self.mission_root / "conception-002")
        (self.mission_root / "conception-002").mkdir()
        message = self.refusal(self.conception_request("conception-002", new_version=True))
        self.assertIn("partiel", message)


class TestAttach(MissionCase):
    def test_a_historical_collaboration_at_the_root_is_attached_as_dot(self) -> None:
        research = self.accepted_research_at(".")
        before = tree(research)
        step = mission.attach(self.mission_root, research, "recherche")
        self.assertEqual(step.path, ".")
        self.assertEqual(mission.load(self.mission_root).name, "Mission")
        added = set(tree(research)) - set(before)
        self.assertEqual(added, {mission.REGISTRY})

    def test_attaching_twice_is_idempotent_but_never_contradictory(self) -> None:
        research = self.attached_research()
        mission.attach(self.mission_root, research, "recherche")
        self.assertEqual(len(self.steps()), 1)
        with self.assertRaises(mission.MissionError):
            mission.attach(self.mission_root, research, "revue")

    def test_the_role_must_match_the_type(self) -> None:
        research = self.accepted_research_at("recherche")
        with self.assertRaises(mission.MissionError):
            mission.attach(self.mission_root, research, "conception")
        mission.attach(self.mission_root, research, "revue")  # une revue est du type RECHERCHE

    def test_an_unreadable_folder_and_a_foreign_one_are_refused(self) -> None:
        self.mission_root.mkdir()
        (self.mission_root / "vide").mkdir()
        with self.assertRaises(mission.MissionError):
            mission.attach(self.mission_root, self.mission_root / "vide", "recherche")
        outside = fakes.collaboration(self.root_dir / "dehors")
        with self.assertRaises(mission.MissionError):
            mission.attach(self.mission_root, outside, "recherche")

    def test_a_second_step_of_a_role_needs_its_numbered_place(self) -> None:
        self.create(self.conception_request("conception"))
        extra = fakes.collaboration(self.root_dir / "tmp")
        shutil.move(extra, self.mission_root / "autre")
        with self.assertRaises(mission.MissionError):
            mission.attach(self.mission_root, self.mission_root / "autre", "conception")

    def test_an_unknown_source_is_refused(self) -> None:
        self.create(self.conception_request("conception"))
        with self.assertRaises(mission.MissionError):
            mission.attach(self.mission_root, self.mission_root / "conception", "conception", "x")


class TestNavigation(MissionCase):
    def setUp(self) -> None:
        super().setUp()
        self.research_dir = self.attached_research(".")
        follow_up = self.prepared(self.mission_root)
        self.conception = self.create(self.conception_request("conception", follow_up=follow_up))

    def test_a_step_is_found_by_its_ancestors(self) -> None:
        found = mission.locate(self.conception)
        assert found is not None
        self.assertEqual((found.rel, found.step and found.step.role), ("conception", "conception"))
        self.assertEqual(mission.root_of(self.conception), self.mission_root.resolve())

    def test_an_independent_collaboration_and_an_unregistered_folder_stay_independent(self) -> None:
        loose = fakes.collaboration(self.root_dir / "loin")
        self.assertIsNone(mission.locate(loose))
        unregistered = self.mission_root / "conception-002"
        shutil.move(fakes.collaboration(self.root_dir / "tmp"), unregistered)
        self.assertEqual(mission.resolve(unregistered), mission.Target(None, None, unregistered))

    def test_opening_the_root_picks_the_preferred_step_else_the_last(self) -> None:
        last = mission.resolve(self.mission_root)
        self.assertEqual(
            (last.step, last.collab), ("conception", self.mission_root.resolve() / "conception"),
        )
        self.assertEqual(mission.resolve(self.mission_root, ".").step, ".")
        self.assertEqual(mission.resolve(self.mission_root, "disparue").step, "conception")

    def test_a_mission_without_step_is_diagnosed(self) -> None:
        empty = self.root_dir / "Vide"
        empty.mkdir()
        (empty / mission.REGISTRY).write_text(
            json.dumps({"schema_version": 1, "name": "V", "steps": []}), encoding="utf-8")
        with self.assertRaises(mission.MissionError):
            mission.resolve(empty)

    def test_fold_keeps_one_entry_per_mission(self) -> None:
        loose = fakes.collaboration(self.root_dir / "loin")
        folded = mission.fold([self.conception, self.mission_root, loose, self.conception])
        self.assertEqual(folded, [self.mission_root.resolve(), loose])

    def test_the_summary_reads_each_step_from_its_folder(self) -> None:
        summary = mission.summarize(self.mission_root)
        self.assertEqual([v.label for v in summary.steps], ["Version acceptée", "Prête"])
        self.assertIn("recherche : Version acceptée", summary.line())
        self.assertIn("conception : Prête", summary.line())
        self.assertEqual(summary.to_attach, ())
        self.assertIsNotNone(summary.updated_at)

    def test_a_status_is_never_stored_in_the_registry(self) -> None:
        text = (self.mission_root / mission.REGISTRY).read_text(encoding="utf-8")
        self.assertNotIn("READY", text)
        self.assertNotIn("Prête", text)
        self.assertEqual(set(json.loads(text)), {"schema_version", "name", "steps"})

    def test_continuations_find_the_existing_conception(self) -> None:
        self.assertEqual(
            mission.continuations(self.mission_root), (self.mission_root.resolve() / "conception",),
        )

    def test_default_dest_follows_the_mission_and_an_explicit_version(self) -> None:
        self.assertEqual(
            mission.default_dest(self.mission_root, False),
            (self.mission_root.resolve(), self.mission_root.resolve() / "conception"),
        )
        self.assertEqual(
            mission.default_dest(self.mission_root, True)[1],
            self.mission_root.resolve() / "conception-002",
        )

    def test_an_independent_research_keeps_its_neighbour_convention(self) -> None:
        loose = self.research()
        self.assertEqual(
            mission.default_dest(loose), (None, loose.parent / f"{loose.name}-conception"),
        )
        self.assertEqual(mission.continuations(loose), ())
        sibling = loose.parent / f"{loose.name}-conception"
        shutil.copytree(self.conception, sibling)
        self.assertEqual(mission.continuations(loose), (sibling,))


class TestTheCommandLine(MissionCase):
    def base(self, rel: str, *extra: str) -> list[str]:
        demande_file = self.root_dir / "demande.md"
        demande_file.write_text("Concevoir le jeu.", encoding="utf-8")
        return ["new", str(self.mission_root / rel), "--mission", str(self.mission_root),
                "--kind", "conception", "--reviewer-access", "consult", "--agent-a", "fake-a",
                "--agent-b", "fake-b", "--max-revisions", "1", "--demande", str(demande_file),
                *extra]

    def test_new_with_a_mission_creates_then_registers(self) -> None:
        code, _, err = self.cli(*self.base("conception"))
        self.assertEqual(code, 0, err)
        self.assertEqual(self.steps(), [("conception", "conception", None)])

    def test_a_second_conception_is_refused_and_a_new_version_accepted(self) -> None:
        self.cli(*self.base("conception"))
        code, _, err = self.cli(*self.base("conception-002"))
        self.assertEqual(code, 1)
        self.assertIn("nouvelle version", err)
        code, _, err = self.cli(*self.base("conception-002", "--nouvelle-version"))
        self.assertEqual(code, 0, err)
        self.assertEqual(len(self.steps()), 2)

    def test_a_new_version_flag_needs_a_mission(self) -> None:
        argv = self.base("conception", "--nouvelle-version")
        argv[argv.index("--mission"):argv.index("--mission") + 2] = []
        code, _, err = self.cli(*argv)
        self.assertEqual(code, 1)
        self.assertIn("--mission", err)

    def test_without_mission_the_creation_stays_independent(self) -> None:
        argv = self.base("conception")
        argv[argv.index("--mission"):argv.index("--mission") + 2] = []
        code, _, err = self.cli(*argv)
        self.assertEqual(code, 0, err)
        self.assertFalse((self.mission_root / mission.REGISTRY).exists())

    def test_depuis_a_research_of_a_mission_suggests_the_mission(self) -> None:
        self.attached_research("recherche")
        research = self.mission_root / "recherche"
        argv = ["new", str(self.root_dir / "plan"), "--depuis", str(research)]
        code, _, err = self.cli(*argv)
        self.assertEqual(code, 0, err)
        self.assertIn("est dans la mission", err)

    def test_show_and_list_recognise_a_mission(self) -> None:
        self.attached_research(".")
        follow_up = self.prepared(self.mission_root)
        self.create(self.conception_request("conception", follow_up=follow_up))
        code, out, _ = self.cli("show", str(self.mission_root))
        self.assertEqual(code, 0)
        self.assertIn("mission Mission — 2 étape(s)", out)
        self.assertIn("recherche", out)
        self.assertIn("Version acceptée", out)
        code, out, _ = self.cli("list", str(self.mission_root))
        self.assertIn("conception", out)
        code, out, _ = self.cli("list", str(self.root_dir))
        self.assertEqual(code, 0)
        self.assertEqual(out.count("mission Mission"), 1, "une entrée par mission")

    def test_show_a_step_of_the_mission_by_name(self) -> None:
        self.attached_research(".")
        code, out, err = self.cli("show", str(self.mission_root), "--etape", ".", "--no-document")
        self.assertEqual(code, 0, err)
        self.assertNotIn("mission Mission", out)
        code, _, err = self.cli("show", str(self.mission_root), "--etape", "inconnue")
        self.assertEqual(code, 1)
        self.assertIn("n'est pas une étape", err)

    def test_mission_attach_and_its_refusals(self) -> None:
        research = self.accepted_research_at(".")
        code, out, err = self.cli("mission", "attach", str(self.mission_root), str(research),
                                  "--role", "recherche")
        self.assertEqual(code, 0, err)
        self.assertIn("rattachée", out)
        code, _, err = self.cli("mission", "attach", str(self.mission_root), str(research),
                                "--role", "conception")
        self.assertEqual(code, 1)

    def test_commands_that_run_still_target_one_collaboration(self) -> None:
        self.attached_research(".")
        code, out, _ = self.cli("status", str(self.mission_root), "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["mission_kind"], "RECHERCHE")


class TestTheGui(MissionCase):
    def setUp(self) -> None:
        super().setUp()
        self.prefs = self.root_dir / "recents.json"
        self.research_dir = self.attached_research("recherche")
        follow_up = self.prepared(self.research_dir)
        self.conception = self.create(self.conception_request("conception", follow_up=follow_up))

    def test_opening_the_mission_shows_the_last_consulted_step(self) -> None:
        with mock.patch.object(self.controller, "show_suivi") as show:
            self.controller.open_collaboration(self.mission_root, "recherche")
            show.assert_called_with(self.mission_root.resolve() / "recherche")
            self.controller.open_collaboration(self.mission_root)  # la préférence est retenue
            show.assert_called_with(self.mission_root.resolve() / "recherche")
        saved = recents.load(self.prefs)
        self.assertEqual([(r.path, r.last_step) for r in saved],
                         [(self.mission_root.resolve(), "recherche")])

    def test_opening_a_step_records_its_mission_not_the_step(self) -> None:
        with mock.patch.object(self.controller, "show_suivi"):
            self.controller.open_collaboration(self.conception)
        self.assertEqual([r.path for r in recents.load(self.prefs)], [self.mission_root.resolve()])
        self.assertEqual(recents.load(self.prefs)[0].last_step, "conception")

    def test_the_last_step_is_only_a_display_preference(self) -> None:
        recents.record_opened(self.mission_root, self.prefs, last_step="recherche")
        recents.record_opened(self.mission_root, self.prefs)
        self.assertEqual(recents.load(self.prefs)[0].last_step, "recherche")
        with mock.patch.object(self.controller, "show_suivi") as show:
            self.controller.open_collaboration(self.mission_root, "conception")
            show.assert_called_with(self.mission_root.resolve() / "conception")

    def test_old_recents_without_the_field_still_load(self) -> None:
        self.prefs.write_text(json.dumps({"schema_version": 1, "recents": [
            {"path": str(self.mission_root), "last_opened_at": "2026-10-03T08:00:00Z"},
        ]}), encoding="utf-8")
        self.assertIsNone(recents.load(self.prefs)[0].last_step)

    def test_the_home_lists_one_entry_per_mission(self) -> None:
        recents.record_opened(self.conception, self.prefs)
        recents.record_opened(self.research_dir, self.prefs)
        recents.record_opened(self.mission_root, self.prefs)
        entries = self.controller.recent_entries()
        self.assertEqual([e.path for e in entries], [self.mission_root.resolve()])
        view = AccueilView(_ROOT, self.controller)
        rows = [view._table.item(r, "values") for r in view._table.get_children()]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], "Mission")
        self.assertIn("Mission — recherche : Version acceptée · conception : Prête", rows[0][1])

    def test_the_home_scans_a_root_for_missions_too(self) -> None:
        self.controller.set_collaborations_root(self.root_dir)
        view = self.controller._frame
        assert isinstance(view, AccueilView)
        names = [view._table.item(r, "values")[0] for r in view._table.get_children()]
        self.assertIn("Mission", names)

    def test_a_broken_registry_is_named_on_the_home_and_never_repaired(self) -> None:
        path = self.mission_root / mission.REGISTRY
        path.write_text("{cassé", encoding="utf-8")
        recents.record_opened(self.mission_root, self.prefs)
        view = AccueilView(_ROOT, self.controller)
        row = view._table.item(view._table.get_children()[0], "values")
        self.assertIn("illisible", row[1])
        self.assertEqual(path.read_text(encoding="utf-8"), "{cassé")

    def test_the_follow_up_screen_lists_the_steps_and_navigates(self) -> None:
        suivi = SuiviView(_ROOT, self.controller, self.conception)
        texts = label_texts(suivi)
        self.assertIn("Mission Mission :", texts)
        here = _find_button(suivi, "Conception — Prête")
        self.assertEqual(str(here.cget("state")), "disabled")
        other = _find_button(suivi, "Recherche — Version acceptée")
        with mock.patch.object(self.controller, "open_collaboration") as opened:
            other.invoke()
        opened.assert_called_once_with(self.mission_root.resolve(), "recherche")

    def test_an_independent_collaboration_has_no_mission_header(self) -> None:
        loose = fakes.collaboration(self.root_dir / "loin")
        texts = label_texts(SuiviView(_ROOT, self.controller, loose))
        self.assertFalse(any(t.startswith("Mission ") for t in texts))

    def test_the_research_offers_to_resume_not_to_redo(self) -> None:
        """AC07 : l'étape existante se rouvre ; une nouvelle version est un second bouton."""
        suivi = SuiviView(_ROOT, self.controller, self.research_dir)
        with self.assertRaises(LookupError):
            _find_button(suivi, "Poursuivre en conception")
        resume = _find_button(suivi, "Reprendre la conception")
        with mock.patch.object(self.controller, "open_collaboration") as opened:
            resume.invoke()
        opened.assert_called_once_with(self.mission_root.resolve() / "conception")
        again = _find_button(suivi, "Nouvelle version de conception")
        with mock.patch.object(self.controller, "show_creation") as show:
            again.invoke()
        show.assert_called_once_with(from_research=self.research_dir, new_version=True)

    def test_two_clicks_and_a_reopening_find_the_same_conception(self) -> None:
        for _ in range(2):
            suivi = SuiviView(_ROOT, self.controller, self.research_dir)
            with mock.patch.object(self.controller, "open_collaboration") as opened:
                _find_button(suivi, "Reprendre la conception").invoke()
            opened.assert_called_once_with(self.mission_root.resolve() / "conception")
        self.assertEqual(
            [p for p, _, _ in self.steps()], ["recherche", "conception"],
        )

    def test_a_research_without_conception_offers_to_continue(self) -> None:
        shutil.rmtree(self.conception)
        (self.mission_root / mission.REGISTRY).write_text(json.dumps({
            "schema_version": 1, "name": "Mission",
            "steps": [{"path": "recherche", "role": "recherche", "source": None}],
        }), encoding="utf-8")
        suivi = SuiviView(_ROOT, self.controller, self.research_dir)
        with mock.patch.object(self.controller, "show_creation") as show:
            _find_button(suivi, "Poursuivre en conception").invoke()
        show.assert_called_once_with(from_research=self.research_dir)

    def test_the_creation_form_targets_the_mission(self) -> None:
        shutil.rmtree(self.conception)
        (self.mission_root / mission.REGISTRY).write_text(json.dumps({
            "schema_version": 1, "name": "Mission",
            "steps": [{"path": "recherche", "role": "recherche", "source": None}],
        }), encoding="utf-8")
        view = CreationView(_ROOT, self.controller, from_research=self.research_dir)
        self.assertEqual(view._dossier.get(), str(self.mission_root.resolve() / "conception"))
        request = view._build_request()
        assert request is not None
        self.assertEqual(request.mission, self.mission_root.resolve())
        self.assertFalse(request.new_version)
        created = facade.create_collaboration(request, adapters=self.adapters).path
        self.assertEqual(self.steps()[-1], ("conception", "conception", "recherche"))
        self.controller.record_created(created)
        saved = recents.load(self.prefs)
        self.assertEqual((saved[0].path, saved[0].last_step),
                         (self.mission_root.resolve(), "conception"))

    def test_a_new_version_form_proposes_the_next_folder_and_asks_for_it(self) -> None:
        view = CreationView(
            _ROOT, self.controller, from_research=self.research_dir, new_version=True,
        )
        self.assertEqual(view._dossier.get(), str(self.mission_root.resolve() / "conception-002"))
        request = view._build_request()
        assert request is not None
        self.assertTrue(request.new_version)
        created = facade.create_collaboration(request, adapters=self.adapters).path
        self.assertEqual(created.name, "conception-002")
        self.assertEqual([p for p, _, _ in self.steps()],
                         ["recherche", "conception", "conception-002"])

    def test_an_ordinary_creation_cannot_double_the_conception(self) -> None:
        view = CreationView(_ROOT, self.controller, from_research=self.research_dir)
        request = view._build_request()
        assert request is not None
        with self.assertRaises(facade.CreationError) as caught:
            facade.create_collaboration(request, adapters=self.adapters)
        self.assertIn("nouvelle version", str(caught.exception))

    def test_an_invalid_registry_is_shown_on_the_form_not_raised(self) -> None:
        (self.mission_root / mission.REGISTRY).write_text("{cassé", encoding="utf-8")
        view = CreationView(_ROOT, self.controller, from_research=self.research_dir)
        self.assertIn(mission.REGISTRY, str(view._error.cget("text")))


class TestTheMastermindRegrouping(MissionCase):
    """AC08 : la disposition réelle — recherche à la racine d'une mission, conception créée à côté
    (`Mastermind-conception`) — est regroupée sans toucher à l'original, et la conception reprend
    depuis son nouvel emplacement."""

    def setUp(self) -> None:
        super().setUp()
        self.missions = self.root_dir / "missions"
        self.missions.mkdir()
        self.research_dir = self.missions / "Mastermind"
        shutil.move(self.research(), self.research_dir)
        follow_up = facade.prepare_follow_up(self.research_dir)
        self.addCleanup(follow_up.discard)
        self.outside = self.missions / "Mastermind-conception"
        facade.create_collaboration(
            self.conception_request(
                "x", collab=self.outside, mission=None, follow_up=follow_up,
                demande=facade.DemandeSource(follow_up.mandate, "cadrage"),
            ),
            adapters=self.adapters,
        )
        self.mission_root = self.research_dir
        a, b = self.adapters["fake-a"], self.adapters["fake-b"]
        a.responses = [_QUESTION]
        workflow.run(self.outside, adapters=self.adapters, timeout_seconds=30.0)
        self.assertEqual(facade.inspect_collaboration(self.outside).state.status.value,
                         "WAITING_HUMAN")
        a.responses, b.responses = [_DOC], [fakes.review("ACCEPTER")]
        a.calls = b.calls = 0

    def regroup(self) -> mission.Adoption:
        mission.attach(self.mission_root, self.research_dir, "recherche")
        return mission.adopt(self.mission_root, self.outside, "conception", source_step=".")

    def test_the_copy_is_identical_and_the_original_untouched(self) -> None:
        original = tree(self.outside)
        research_before = tree(self.research_dir)
        done = self.regroup()
        self.assertEqual(tree(self.outside), original, "l'original reste la sauvegarde")
        dest = self.mission_root / "conception"
        self.assertEqual(done.dest, dest)
        changed = {k for k in original.keys() | tree(dest).keys()
                   if original.get(k) != tree(dest).get(k)}
        self.assertEqual(changed, {mission.TRANSITION})
        added = set(tree(self.research_dir)) - set(research_before)
        self.assertEqual({p.split("/")[0] for p in added}, {mission.REGISTRY, "conception"})
        for name in set(research_before) - {mission.REGISTRY}:
            self.assertEqual(tree(self.research_dir)[name], research_before[name])

    def test_source_path_is_recomputed_and_the_old_value_kept(self) -> None:
        before = json.loads((self.outside / facade.TRANSITION).read_text(encoding="utf-8"))
        self.assertEqual(before["source_path"], "Mastermind")
        done = self.regroup()
        after = json.loads((done.dest / facade.TRANSITION).read_text(encoding="utf-8"))
        self.assertEqual(after["source_path"], ".")
        self.assertEqual(after["previous_source_path"], "Mastermind")
        self.assertEqual(done.rewritten, (facade.TRANSITION,))
        resolved = (done.dest.parent / after["source_path"]).resolve()
        self.assertEqual(resolved, self.research_dir.resolve(), "le chemin retrouve la recherche")
        for key in ("decision", "corpus_manifest_sha256", "source", "schema_version"):
            self.assertEqual(after[key], before[key])

    def test_the_registry_and_the_opening(self) -> None:
        done = self.regroup()
        self.assertEqual(
            self.steps(), [(".", "recherche", None), ("conception", "conception", ".")],
        )
        target = mission.resolve(self.mission_root)
        self.assertEqual(target.collab, done.dest.resolve())
        snapshot = facade.inspect_collaboration(done.dest)
        self.assertEqual(snapshot.state.status.value, "WAITING_HUMAN")
        self.assertEqual(snapshot.name, "conception")
        self.assertEqual(mission.continuations(self.research_dir), (done.dest.resolve(),))

    def test_the_moved_conception_resumes_with_the_normal_answer_and_pays_no_replay(self) -> None:
        done = self.regroup()
        answer = self.root_dir / "reponse.md"
        answer.write_text("Plan de réalisation ; traiter H1 à H5.", encoding="utf-8")
        state = workflow.run(
            done.dest, adapters=self.adapters, timeout_seconds=30.0,
            command_label="resume", intervention=workflow.Answer(answer),
        )
        self.assertEqual(state.status.value, "AWAITING_APPROVAL")
        self.assertEqual((self.adapters["fake-a"].calls, self.adapters["fake-b"].calls), (1, 1))
        text = (done.dest / "demande.md").read_text(encoding="utf-8")
        self.assertIn("H1 à H5", text)
        self.assertEqual(
            (decisions.latest(self.research_dir) or {})["decision"], decisions.ACCEPTED,
            "la décision de la recherche n'a pas bougé",
        )
        self.assertEqual(
            json.loads((self.outside / "etat.json").read_text(encoding="utf-8"))["status"],
            "WAITING_HUMAN", "la sauvegarde n'a pas avancé",
        )

    def test_the_corpus_and_the_decisions_stay_reachable_from_the_mission(self) -> None:
        done = self.regroup()
        manifest = done.dest / "corpus" / "manifeste.json"
        self.assertTrue(manifest.is_file())
        for name in facade.FOLLOW_UP_FILES:
            self.assertTrue((done.dest / "corpus" / "fichiers" / name).is_file(), name)
        self.assertEqual(done.absolute_paths, {})

    def test_a_conception_created_before_lot_1_has_no_path_to_recompute(self) -> None:
        (self.outside / facade.TRANSITION).unlink()
        done = self.regroup()
        self.assertEqual(done.rewritten, ())
        self.assertEqual(tree(done.dest), tree(self.outside))

    def test_the_audit_names_absolute_paths_in_resume_files_but_not_history(self) -> None:
        (self.outside / "provenance_demande.json").write_text(
            json.dumps({"path": "C:\\Users\\x\\demande.md"}), encoding="utf-8")
        call = self.outside / "appels" / "0001-A-x"
        call.mkdir(parents=True, exist_ok=True)
        (call / "stdout.txt").write_text("lu C:\\Projets\\x\\f.md", encoding="utf-8")
        done = self.regroup()
        self.assertEqual(done.absolute_paths, {"provenance_demande.json": 1})
        self.assertGreaterEqual(done.history_paths, 1)
        self.assertEqual((done.dest / "appels/0001-A-x/stdout.txt").read_bytes(),
                         (self.outside / "appels/0001-A-x/stdout.txt").read_bytes())

    def test_refusals_happen_before_any_write(self) -> None:
        mission.attach(self.mission_root, self.research_dir, "recherche")
        before = tree(self.mission_root)

        def refused(source: Path | None = None, rel: str | None = None) -> None:
            with self.assertRaises(mission.MissionError):
                mission.adopt(
                    self.mission_root, source or self.outside, "conception", rel, ".",
                )
            self.assertEqual(tree(self.mission_root), before)
            self.assertEqual([p.name for p in self.mission_root.glob(".adopt-*")], [])

        (self.mission_root / "conception").mkdir()
        before = tree(self.mission_root)
        refused()  # destination occupée : rien n'est écrasé
        (self.mission_root / "conception").rmdir()
        before = tree(self.mission_root)
        refused(rel="conception/../x")  # chemin non sûr
        (self.outside / "verrou.json").write_text("{}", encoding="utf-8")
        refused()  # verrou présent : une exécution est peut-être active
        (self.outside / "verrou.json").unlink()
        refused(self.research_dir / "echanges")  # n'est pas une collaboration
        with self.assertRaises(mission.MissionError):  # déjà dans la mission : on rattache
            mission.adopt(self.mission_root, self.research_dir, "conception", source_step=".")

    def test_foreseeable_refusals_come_before_the_copy(self) -> None:
        """Rôle, `--source` ou registre qui rendent le rattachement impossible : refusés avant
        toute copie, sans dossier publié ni reste, jamais « copiée mais non inscrite »."""
        mission.attach(self.mission_root, self.research_dir, "recherche")
        before = tree(self.mission_root)
        registry = (self.mission_root / mission.REGISTRY).read_bytes()
        cases: list[tuple[str, dict[str, Any]]] = [
            ("n'est pas une étape", {"source_step": "absente"}),
            ("attend une collaboration de type", {"role": "recherche"}),
            ("rôle 'inconnu' inconnu", {"role": "inconnu"}),
            ("déjà une étape recherche", {"role": "recherche", "rel": "autre"}),
        ]
        # la recherche porte déjà le rôle `recherche` : le type de l'original refuse en premier
        cases[3] = ("attend une collaboration de type", {"role": "recherche", "rel": "autre"})
        for expected, overrides in cases:
            args: dict[str, Any] = {"role": "conception", "rel": None, "source_step": "."}
            args.update(overrides)
            with self.subTest(expected=expected), mock.patch.object(
                shutil, "copytree", side_effect=AssertionError("la copie ne doit pas partir"),
            ):
                with self.assertRaises(mission.MissionError) as caught:
                    mission.adopt(
                        self.mission_root, self.outside, args["role"], args["rel"],
                        args["source_step"],
                    )
            self.assertIn(expected, str(caught.exception))
            self.assertNotIn("copiée mais non inscrite", str(caught.exception))
            self.assertEqual(tree(self.mission_root), before)
            self.assertEqual((self.mission_root / mission.REGISTRY).read_bytes(), registry)

    def test_a_second_step_of_the_role_is_refused_before_the_copy(self) -> None:
        mission.attach(self.mission_root, self.research_dir, "recherche")
        mission.adopt(self.mission_root, self.outside, "conception", source_step=".")
        before = tree(self.mission_root)
        with mock.patch.object(shutil, "copytree", side_effect=AssertionError("copie")):
            with self.assertRaises(mission.MissionError) as caught:
                mission.adopt(
                    self.mission_root, self.outside, "conception", "autre", source_step=".",
                )
        self.assertIn("conception-002", str(caught.exception))
        self.assertEqual(tree(self.mission_root), before)

    def test_an_invalid_registry_is_refused_before_the_copy(self) -> None:
        self.mission_root.joinpath(mission.REGISTRY).write_text("{cassé", encoding="utf-8")
        before = tree(self.mission_root)
        with mock.patch.object(shutil, "copytree", side_effect=AssertionError("copie")):
            with self.assertRaises(mission.MissionError):
                mission.adopt(self.mission_root, self.outside, "conception", source_step=".")
        self.assertEqual(tree(self.mission_root), before)

    def test_a_real_write_failure_keeps_the_copy_and_says_how_to_attach(self) -> None:
        mission.attach(self.mission_root, self.research_dir, "recherche")
        with mock.patch.object(mission, "_save", side_effect=OSError("disque plein")):
            with self.assertRaises(mission.MissionError) as caught:
                mission.adopt(self.mission_root, self.outside, "conception", source_step=".")
        self.assertIn("copiée mais non inscrite", str(caught.exception))
        copy = tree(self.mission_root / "conception")
        original = tree(self.outside)
        copy.pop(mission.TRANSITION), original.pop(mission.TRANSITION)  # seul fichier recalculé
        self.assertEqual(copy, original)
        mission.attach(self.mission_root, self.mission_root / "conception", "conception", ".")
        self.assertEqual(len(self.steps()), 2)

    def test_a_transition_file_needs_the_research_step(self) -> None:
        mission.attach(self.mission_root, self.research_dir, "recherche")
        with self.assertRaises(mission.MissionError):
            mission.adopt(self.mission_root, self.outside, "conception")
        self.assertFalse((self.mission_root / "conception").exists())
        self.assertEqual(list(self.mission_root.glob(".adopt-*")), [])

    def test_a_copy_that_differs_is_abandoned_without_publishing(self) -> None:
        mission.attach(self.mission_root, self.research_dir, "recherche")
        real = shutil.copytree

        def corrupt(src: Path, dst: Path, **kw: Any) -> Any:
            with mock.patch.object(shutil, "copytree", real):  # la récursion interne copie vraiment
                out = real(src, dst, **kw)
            with open(Path(dst) / "etat.json", "ab") as handle:
                handle.write(b" ")
            return out

        with mock.patch.object(shutil, "copytree", corrupt):
            with self.assertRaises(mission.MissionError) as caught:
                mission.adopt(self.mission_root, self.outside, "conception", source_step=".")
        self.assertIn("diffère", str(caught.exception))
        self.assertFalse((self.mission_root / "conception").exists())
        self.assertEqual(list(self.mission_root.glob(".adopt-*")), [])
        self.assertEqual(len(self.steps()), 1)

    def test_a_running_declaration_is_refused(self) -> None:
        mission.attach(self.mission_root, self.research_dir, "recherche")
        path = self.outside / "etat.json"
        state = json.loads(path.read_text(encoding="utf-8"))
        state["status"] = "RUNNING"
        path.write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaises(mission.MissionError):
            mission.adopt(self.mission_root, self.outside, "conception", source_step=".")

    def test_the_command_line_runs_the_procedure(self) -> None:
        code, _, err = self.cli("mission", "attach", str(self.mission_root),
                                str(self.research_dir), "--role", "recherche")
        self.assertEqual(code, 0, err)
        code, out, err = self.cli("mission", "adopt", str(self.mission_root), str(self.outside),
                                  "--role", "conception", "--source", ".")
        self.assertEqual(code, 0, err)
        self.assertIn("identiques à l'original", out)
        self.assertIn("recalculé : provenance_transition.json", out)
        self.assertIn("l'original reste la sauvegarde", out)
        self.assertEqual(len(self.steps()), 2)
        code, _, err = self.cli("mission", "adopt", str(self.mission_root), str(self.outside),
                                "--role", "conception", "--source", ".")
        self.assertEqual(code, 1)
        self.assertIn("déjà inscrite", err)

"""Tests du lot 2, point 2.3 : la liaison facultative à un plan PWF.

Validation du plan : **plan correct, sélection inexistante, deux plans concurrents, reprise
dans une nouvelle session et absence de PWF. Retirer la liaison ne rend pas le livrable
illisible et ne déclenche aucun appel.**

Deux niveaux : le vrai script public de résolution, sur des projets jetables (ignoré s'il est
absent, comme `sh`), et un résolveur simulé pour ce que le vrai ne rend pas à volonté — une
sortie vide avec un code 0, un autre plan, un plan sans `task_plan.md`.
"""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from iabinome import cli, planlink
from iabinome.models import State, Status
from tests import fakes
from tests.test_workflow import WorkflowCase

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."
_REAL = planlink.default_resolver().is_file() and shutil.which("sh") is not None


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): sha(p) for p in sorted(root.rglob("*")) if p.is_file()
    }


def fake_runner(stdout: str = "", returncode: int = 0, stderr: str = "") -> mock.Mock:
    return mock.Mock(
        return_value=subprocess.CompletedProcess(["sh"], returncode, stdout, stderr)
    )


class PlanCase(WorkflowCase):
    fake_shell = True  # `sh` simulé ; les tests du vrai script le désactivent

    def setUp(self) -> None:
        super().setUp()
        self.project = self.root / "projet"
        self.script = self.root / "resolve.sh"
        self.script.write_text("# simulé\n", encoding="utf-8")
        if self.fake_shell:
            which = mock.patch.object(shutil, "which", return_value="sh")
            which.start()
            self.addCleanup(which.stop)

    def make_plan(self, plan_id: str, *, task_plan: bool = True) -> Path:
        directory = self.project / ".planning" / plan_id
        directory.mkdir(parents=True)
        if task_plan:
            (directory / "task_plan.md").write_text("# Plan\n## Next Step\nX\n", encoding="utf-8")
        return directory

    def cycle(self) -> Path:
        collab = self.build(a=(_DOC,), b=(fakes.review("ACCEPTER"),))
        self.run_engine(collab)
        return collab

    def command(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()


class TestResolveWithASimulatedResolver(PlanCase):
    def test_a_resolved_plan_is_returned(self) -> None:
        directory = self.make_plan("2026-09-18-v2")
        runner = fake_runner(f"{directory}\n")
        found = planlink.resolve("2026-09-18-v2", self.project, script=self.script, runner=runner)
        self.assertEqual(found, directory)

    def test_the_selection_is_pinned_over_the_current_environment(self) -> None:
        """Le `PLAN_ID` d'une autre session ne doit jamais l'emporter : on épingle."""
        directory = self.make_plan("2026-09-18-v2")
        runner = fake_runner(f"{directory}\n")
        with mock.patch.dict(os.environ, {"PLAN_ID": "un-autre", "PWF_PLAN_ROOT": "C:/ailleurs"}):
            planlink.resolve("2026-09-18-v2", self.project, script=self.script, runner=runner)
        env = runner.call_args.kwargs["env"]
        self.assertEqual(env["PLAN_ID"], "2026-09-18-v2")
        self.assertEqual(env["PWF_PLAN_ROOT"], str(self.project.resolve()))

    def test_an_empty_output_with_code_zero_is_not_a_success(self) -> None:
        for empty in ("", "\n", "  \n\n"):
            with self.assertRaisesRegex(planlink.PlanLinkError, "pas un succès"):
                planlink.resolve(
                    "x", self.project, script=self.script, runner=fake_runner(empty, 0)
                )

    def test_a_failing_resolver_is_an_error(self) -> None:
        with self.assertRaisesRegex(planlink.PlanLinkError, "code 3"):
            planlink.resolve(
                "x", self.project, script=self.script, runner=fake_runner("", 3, "boum")
            )

    def test_another_plan_than_the_pinned_one_is_refused(self) -> None:
        other = self.make_plan("2026-09-19-autre")
        with self.assertRaisesRegex(planlink.PlanLinkError, "autre plan"):
            planlink.resolve(
                "2026-09-18-v2", self.project, script=self.script, runner=fake_runner(f"{other}\n")
            )

    def test_a_directory_without_task_plan_is_not_a_plan(self) -> None:
        bare = self.make_plan("2026-09-18-v2", task_plan=False)
        with self.assertRaisesRegex(planlink.PlanLinkError, "task_plan.md"):
            planlink.resolve(
                "2026-09-18-v2", self.project, script=self.script, runner=fake_runner(f"{bare}\n")
            )

    def test_a_resolver_that_cannot_be_launched_is_an_error(self) -> None:
        for failure in (OSError("non"), subprocess.TimeoutExpired("sh", 30)):
            with self.assertRaisesRegex(planlink.PlanLinkError, "n'a pas pu être lancé"):
                planlink.resolve(
                    "x", self.project, script=self.script, runner=mock.Mock(side_effect=failure)
                )

    def test_a_missing_script_means_pwf_is_absent(self) -> None:
        with self.assertRaisesRegex(planlink.PlanLinkError, "PWF n'est pas installé"):
            planlink.resolve("x", self.project, script=self.root / "nulle-part.sh")

    def test_a_missing_shell_is_said(self) -> None:
        with mock.patch.object(shutil, "which", return_value=None):
            with self.assertRaisesRegex(planlink.PlanLinkError, "`sh` introuvable"):
                planlink.resolve("x", self.project, script=self.script)


@unittest.skipUnless(_REAL, "script public de PWF ou `sh` absent")
class TestResolveWithThePublicScript(PlanCase):
    """Le vrai résolveur, sur des projets jetables. Il rend toujours 0."""

    fake_shell = False

    def setUp(self) -> None:
        super().setUp()
        self.project.mkdir()

    def resolve(self, plan_id: str) -> Path:
        return planlink.resolve(plan_id, self.project)

    def test_a_correct_plan(self) -> None:
        directory = self.make_plan("2026-01-01-a")
        self.assertEqual(self.resolve("2026-01-01-a").resolve(), directory.resolve())

    def test_a_nonexistent_selection(self) -> None:
        self.make_plan("2026-01-01-a")
        with self.assertRaisesRegex(planlink.PlanLinkError, "pas un succès"):
            self.resolve("2026-01-09-absent")

    def test_a_malformed_identifier(self) -> None:
        self.make_plan("2026-01-01-a")
        for bad in ("../x", "a b", ".cache"):
            with self.assertRaises(planlink.PlanLinkError, msg=bad):
                self.resolve(bad)

    def test_two_concurrent_plans_never_swap(self) -> None:
        """Deux plans vivants : l'identifiant épinglé donne **le sien**, jamais l'autre."""
        first = self.make_plan("2026-01-01-a")
        second = self.make_plan("2026-01-02-b")
        self.assertEqual(self.resolve("2026-01-01-a").resolve(), first.resolve())
        self.assertEqual(self.resolve("2026-01-02-b").resolve(), second.resolve())

    def test_a_plan_id_left_by_another_session_does_not_win(self) -> None:
        first = self.make_plan("2026-01-01-a")
        self.make_plan("2026-01-02-b")
        with mock.patch.dict(os.environ, {"PLAN_ID": "2026-01-02-b", "PWF_PLAN_ROOT": "C:/x"}):
            self.assertEqual(self.resolve("2026-01-01-a").resolve(), first.resolve())

    def test_a_pinned_directory_without_task_plan_is_refused_here(self) -> None:
        self.make_plan("2026-01-03-c", task_plan=False)
        with self.assertRaisesRegex(planlink.PlanLinkError, "task_plan.md"):
            self.resolve("2026-01-03-c")


class TestLink(PlanCase):
    def test_a_link_that_does_not_resolve_leaves_no_trace(self) -> None:
        collab = self.cycle()
        before = tree(collab)
        with self.assertRaises(planlink.PlanLinkError):
            planlink.link(collab, "x", self.project, script=self.script, runner=fake_runner(""))
        self.assertEqual(tree(collab), before)
        self.assertFalse((collab / planlink.PLAN_FILE).exists())

    def test_a_link_records_the_reference_and_copies_no_phase(self) -> None:
        collab = self.cycle()
        directory = self.make_plan("2026-09-18-v2")
        planlink.link(
            collab, "2026-09-18-v2", self.project, script=self.script,
            runner=fake_runner(f"{directory}\n"),
        )
        text = (collab / planlink.PLAN_FILE).read_text(encoding="utf-8")
        self.assertIn("2026-09-18-v2", text)
        self.assertNotIn("Next Step", text)  # aucune phase, aucun contenu du plan
        link = planlink.read(collab)
        assert link is not None
        self.assertEqual(link.plan_id, "2026-09-18-v2")

    def test_the_plan_is_never_written(self) -> None:
        collab = self.cycle()
        directory = self.make_plan("2026-09-18-v2")
        plan_before = tree(self.project)
        runner = fake_runner(f"{directory}\n")
        planlink.link(collab, "2026-09-18-v2", self.project, script=self.script, runner=runner)
        planlink.summary(collab, script=self.script, runner=runner)
        planlink.unlink(collab)
        self.assertEqual(tree(self.project), plan_before)

    def test_the_link_survives_a_new_session(self) -> None:
        """Nouvelle session : ni `PLAN_ID` ni `PWF_PLAN_ROOT` — la liaison se relit du disque."""
        collab = self.cycle()
        directory = self.make_plan("2026-09-18-v2")
        planlink.link(
            collab, "2026-09-18-v2", self.project, script=self.script,
            runner=fake_runner(f"{directory}\n"),
        )
        clean = {k: v for k, v in os.environ.items() if k not in ("PLAN_ID", "PWF_PLAN_ROOT")}
        runner = fake_runner(f"{directory}\n")
        with mock.patch.dict(os.environ, clean, clear=True):
            lines = planlink.summary(collab, script=self.script, runner=runner)
        self.assertIn("résolu", lines[0])
        self.assertEqual(runner.call_args.kwargs["env"]["PLAN_ID"], "2026-09-18-v2")


class TestSummary(PlanCase):
    def test_the_summary_is_readable_without_any_link(self) -> None:
        collab = self.cycle()
        text = "\n".join(planlink.summary(collab))
        self.assertIn("aucune liaison", text)
        self.assertIn("AWAITING_APPROVAL", text)
        self.assertIn("aucune : le cycle est terminé, il n'est pas accepté", text)
        self.assertIn(f"  Dossier : {collab.resolve()}", text.splitlines())  # le lien à reporter
        self.assertIn("version_finale.md", text)

    def test_the_summary_never_says_accepted_before_a_decision(self) -> None:
        collab = self.cycle()
        text = "\n".join(planlink.summary(collab)).lower()
        self.assertNotIn("accepté par", text)
        self.assertNotIn("approuvé", text)

    def test_a_link_that_no_longer_resolves_does_not_stop_the_summary(self) -> None:
        collab = self.cycle()
        (collab / planlink.PLAN_FILE).write_text(
            '{"schema_version": 1, "plan_id": "disparu", "plan_root": "C:/nulle-part",'
            ' "linked_at": "2026-09-19T00:00:00Z"}\n', encoding="utf-8",
        )
        lines = planlink.summary(collab, script=self.script, runner=fake_runner(""))
        self.assertIn("NON RÉSOLU", lines[0])
        self.assertIn("AWAITING_APPROVAL", "\n".join(lines))

    def test_a_corrupt_link_does_not_stop_the_summary(self) -> None:
        collab = self.cycle()
        (collab / planlink.PLAN_FILE).write_text("{pas du json", encoding="utf-8")
        lines = planlink.summary(collab)
        self.assertIn("inutilisable", lines[0])
        self.assertIn("AWAITING_APPROVAL", "\n".join(lines))


class TestTheCollaborationDoesNotNeedThePlan(PlanCase):
    def test_removing_the_link_changes_nothing_and_launches_no_call(self) -> None:
        collab = self.cycle()
        directory = self.make_plan("2026-09-18-v2")
        planlink.link(
            collab, "2026-09-18-v2", self.project, script=self.script,
            runner=fake_runner(f"{directory}\n"),
        )
        with_link = tree(collab)
        launched, calls = fakes.launched_calls(collab), (self.a.calls, self.b.calls)
        self.assertTrue(planlink.unlink(collab))
        without_link = tree(collab)
        self.assertEqual(
            {k: v for k, v in with_link.items() if k != planlink.PLAN_FILE}, without_link
        )
        self.assertEqual(fakes.launched_calls(collab), launched)
        self.assertEqual((self.a.calls, self.b.calls), calls)

    def test_after_unlinking_the_deliverable_and_state_are_still_readable(self) -> None:
        collab = self.cycle()
        planlink.unlink(collab)
        state = State.from_dict(fakes.read_json(collab / "etat.json"))
        self.assertIs(state.status, Status.AWAITING_APPROVAL)
        code, out, _ = self.command("show", str(collab))
        self.assertEqual(code, 0)
        self.assertIn("Corps du document.", out)

    def test_unlinking_an_unlinked_collaboration_is_a_no_op(self) -> None:
        collab = self.cycle()
        self.assertFalse(planlink.unlink(collab))

    def test_a_cycle_runs_to_the_end_without_pwf_at_all(self) -> None:
        collab = self.build(a=(_DOC,), b=(fakes.review("ACCEPTER"),))
        self.assertFalse((collab / planlink.PLAN_FILE).exists())
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.AWAITING_APPROVAL)  # type: ignore[attr-defined]

    def test_a_broken_link_file_does_not_stop_a_cycle(self) -> None:
        """Le cycle ne lit jamais `plan.json` : même corrompu, il ne l'arrête pas."""
        collab = self.build(a=(_DOC,), b=(fakes.review("ACCEPTER"),))
        (collab / planlink.PLAN_FILE).write_text("{pas du json", encoding="utf-8")
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.AWAITING_APPROVAL)  # type: ignore[attr-defined]


class TestPlanCommand(PlanCase):
    def test_no_option_prints_the_summary(self) -> None:
        collab = self.cycle()
        code, out, _ = self.command("plan", str(collab))
        self.assertEqual(code, 0)
        self.assertIn("aucune liaison", out)
        self.assertIn("À reporter dans le plan, à la main", out)

    def test_a_failed_link_is_refused_and_writes_nothing(self) -> None:
        collab = self.cycle()
        code, _, err = self.command(
            "plan", str(collab), "--link", "inexistant", "--plan-root", str(self.project)
        )
        self.assertEqual(code, 1)
        self.assertIn("erreur", err)
        self.assertFalse((collab / planlink.PLAN_FILE).exists())

    def test_link_then_unlink_through_the_command(self) -> None:
        collab = self.cycle()
        directory = self.make_plan("2026-09-18-v2")
        with mock.patch.object(planlink, "resolve", return_value=directory):
            code, out, _ = self.command(
                "plan", str(collab), "--link", "2026-09-18-v2", "--plan-root", str(self.project)
            )
        self.assertEqual(code, 0)
        self.assertIn("rien n'y est écrit", out)
        self.assertTrue((collab / planlink.PLAN_FILE).is_file())
        code, out, _ = self.command("plan", str(collab), "--unlink")
        self.assertEqual(code, 0)
        self.assertFalse((collab / planlink.PLAN_FILE).exists())

    def test_link_and_unlink_are_exclusive(self) -> None:
        collab = self.cycle()
        with self.assertRaises(SystemExit) as raised:
            self.command("plan", str(collab), "--link", "x", "--unlink")
        self.assertEqual(raised.exception.code, 2)

    def test_a_folder_that_is_not_a_collaboration_is_refused(self) -> None:
        code, _, err = self.command("plan", str(self.root / "rien"))
        self.assertEqual(code, 1)
        self.assertIn("erreur", err)


if __name__ == "__main__":
    unittest.main()

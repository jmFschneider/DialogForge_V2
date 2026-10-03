"""Poursuivre une recherche acceptée en conception (`conception/TYPES_DE_MISSION.md` D4, précisé
par `conception/PARCOURS_MISSION_CONCEPTION.md` §4.2 et §4.3, lot 1).

L'instantané de transition (`facade.prepare_follow_up`) rassemble, sous le verrou de la recherche
et sans appel : la demande d'origine, le livrable accepté, son bilan et la décision, plus un
mandat complet. La création et le cadrage consomment ce même instantané. Rien n'est lancé.
"""

from __future__ import annotations

import hashlib
import io
import json
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any
from unittest import mock

from iabinome import cli, contracts, corpus, decisions, demande, facade, lock, settings, workflow
from iabinome.framing import FramingArtifacts
from iabinome.gui.views import cadrage
from iabinome.gui.views.creation import CreationView
from iabinome.gui.views.suivi import SuiviView
from iabinome.models import MissionKind, ReviewerAccess
from tests import fakes
from tests.test_framing import DRAFT_OUT, READY_OUT
from tests.test_framing_creation import FramingCliCase
from tests.test_gui_views import _ROOT, ViewCase, _find_button, label_texts

_DOC = "IABINOME:DOCUMENT\n# Synthèse\nCe que disent les sources."
_ORIGIN = (
    "# Demande\n\n## Objectif\nUne application Mastermind jouable.\n\n## Livrable\n"
    "Une étude des règles.\n\n## Sources\nNon précisé.\n\n## Contraintes\nSans dépendance.\n\n"
    "## Non-objectifs\nPas de réseau.\n\n## Critères de fin\nH1 à H5 traitées.\n"
)


class FollowUpCase(ViewCase):
    def setUp(self) -> None:
        super().setUp()
        self.adapters = {
            "fake-a": fakes.FakeAdapter("fake-a", ()), "fake-b": fakes.FakeAdapter("fake-b", ()),
        }

    def research(self, *, kind: str = "RECHERCHE", accept: bool = True) -> Path:
        collab = fakes.collaboration(
            self.root_dir, mission_kind=kind, demande=_ORIGIN, max_revisions=3,
        )
        a = fakes.FakeAdapter("fake-a", (_DOC,))
        b = fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),))
        workflow.run(collab, adapters={"fake-a": a, "fake-b": b}, timeout_seconds=30.0)
        if accept:
            workflow.decide(collab, decisions.ACCEPTED)
        return collab

    def request(self, follow_up: facade.FollowUp, **overrides: object) -> facade.CreationRequest:
        base: dict[str, object] = {
            "collab": self.root_dir / "conception",
            "demande": facade.DemandeSource(follow_up.mandate, "cadrage"),
            "kind": MissionKind.CONCEPTION, "reviewer_access": ReviewerAccess.CONSULT,
            "agent_a": "fake-a", "agent_b": "fake-b", "max_revisions": 1,
            "follow_up": follow_up,
        }
        base.update(overrides)
        return facade.CreationRequest(**base)  # type: ignore[arg-type]

    def prepared(self, research: Path | None = None) -> facade.FollowUp:
        follow_up = facade.prepare_follow_up(research or self.research())
        self.addCleanup(follow_up.discard)
        return follow_up

    def refused(self, request: facade.CreationRequest) -> str:
        with self.assertRaises(facade.CreationError) as ctx:
            facade.create_collaboration(request, adapters=self.adapters)
        self.assertFalse(request.collab.exists())
        return str(ctx.exception)


class TestThePreparedSnapshot(FollowUpCase):
    def test_it_holds_the_exact_documents_of_the_accepted_version(self) -> None:
        """AC03 : demande, livrable, bilan et décision, octet pour octet."""
        research = self.research()
        follow_up = self.prepared(research)
        manifest = corpus.read_manifest(follow_up.corpus / "manifeste.json")
        self.assertEqual(manifest.origin_label, f"recherche {research.name}")
        self.assertEqual(
            sorted(e.logical_path for e in manifest.entries), sorted(facade.FOLLOW_UP_FILES),
        )
        for entry in manifest.entries:
            source = (research / entry.logical_path).read_bytes()
            self.assertEqual(entry.sha256, hashlib.sha256(source).hexdigest())
            copy = follow_up.corpus / "fichiers" / entry.logical_path
            self.assertEqual(copy.read_bytes(), source)

    def test_the_mandate_is_complete_and_quotes_the_original_request_whole(self) -> None:
        """AC03 : aucune rubrique vide ; la demande d'origine, intégrale, ne devient pas un
        second jeu de sections."""
        follow_up = self.prepared()
        mandate = follow_up.mandate
        self.assertEqual(demande.missing(mandate), [])
        self.assertTrue(all(body.strip() for body in demande.sections(mandate).values()))
        self.assertEqual(
            list(demande.sections(mandate)), list(demande.SECTIONS),
        )
        for line in _ORIGIN.strip().splitlines():
            self.assertIn(f"> {line}".rstrip(), mandate.splitlines())
        self.assertIn("Contexte du projet — demande d'origine", mandate)
        self.assertIn("restent des hypothèses", mandate)

    def test_the_source_settings_are_proposed_not_copied_into_a_second_authority(self) -> None:
        follow_up = self.prepared()
        self.assertEqual(follow_up.config.agent_a.adapter_id, "fake-a")
        self.assertEqual(follow_up.config.max_revisions, 3)
        self.assertFalse(follow_up.config.web_access)
        self.assertIn("Accès web hérité de la recherche : fermé", facade.follow_up_label(follow_up))

    def test_a_research_not_yet_accepted_is_refused(self) -> None:
        with self.assertRaisesRegex(facade.CreationError, "non acceptée"):
            facade.prepare_follow_up(self.research(accept=False))

    def test_an_acceptance_that_no_longer_applies_is_refused(self) -> None:
        research = self.research()
        (research / decisions.DELIVERED).write_text("modifié après coup", encoding="utf-8")
        with self.assertRaisesRegex(facade.CreationError, "non acceptée"):
            facade.prepare_follow_up(research)

    def test_a_stopped_research_cannot_be_followed(self) -> None:
        research = self.research(accept=False)
        workflow.decide(research, decisions.STOPPED, reason="abandon")
        with self.assertRaisesRegex(facade.CreationError, "non acceptée"):
            facade.prepare_follow_up(research)

    def test_only_a_research_can_be_followed(self) -> None:
        with self.assertRaisesRegex(facade.CreationError, "n'est pas une recherche"):
            facade.prepare_follow_up(self.research(kind="CONCEPTION"))

    def test_a_refusal_leaves_no_lock_and_no_temporary_folder(self) -> None:
        research = self.research(accept=False)
        made: list[Path] = []
        real = tempfile.mkdtemp

        def spy(prefix: str) -> str:
            made.append(Path(real(prefix=prefix)))
            return str(made[-1])

        with mock.patch("tempfile.mkdtemp", spy), self.assertRaises(facade.CreationError):
            facade.prepare_follow_up(research)
        self.assertEqual(len(made), 1)
        self.assertFalse(made[0].exists())
        self.assertFalse((research / "verrou.json").exists())

    def test_a_research_in_use_is_not_copied_under_the_feet_of_its_run(self) -> None:
        research = self.research()
        with lock.acquire(research / "verrou.json", "run"), \
                self.assertRaises(facade.CreationError):
            facade.prepare_follow_up(research)


class TestTheCreation(FollowUpCase):
    def test_it_consumes_the_snapshot_and_records_the_transition(self) -> None:
        research = self.research()
        follow_up = self.prepared(research)
        result = facade.create_collaboration(self.request(follow_up), adapters=self.adapters)
        created = corpus.read_manifest(result.path / "corpus" / "manifeste.json")
        self.assertEqual(created, corpus.read_manifest(follow_up.corpus / "manifeste.json"))
        config = json.loads((result.path / "configuration.json").read_text(encoding="utf-8"))
        self.assertEqual(config["mission_kind"], "CONCEPTION")
        self.assertIsNotNone(config["corpus_manifest_sha256"])
        transition = json.loads((result.path / facade.TRANSITION).read_text(encoding="utf-8"))
        self.assertEqual(transition["source"], research.name)
        self.assertEqual(transition["source_path"], research.name)
        self.assertEqual(transition["decision"], decisions.latest(research))
        self.assertEqual(transition["corpus_manifest_sha256"], config["corpus_manifest_sha256"])
        self.assertEqual(
            transition["decision"]["version"]["demande_sha256"],
            contracts.normalize(_ORIGIN).sha256,
        )

    def test_no_decision_is_invented_in_the_conception(self) -> None:
        """AC06 : les réserves et hypothèses ne deviennent pas, par la transition, des choix de
        l'humain — la conception naît sans aucune décision."""
        research = self.research(accept=False)
        workflow.decide(research, decisions.ACCEPTED_WITH_RESERVES, reserves="H3 non tranchée")
        result = facade.create_collaboration(
            self.request(self.prepared(research)), adapters=self.adapters,
        )
        self.assertFalse((result.path / decisions.DECISIONS).exists())
        kept = (result.path / "corpus" / "fichiers" / decisions.DECISIONS).read_text("utf-8")
        self.assertIn("H3 non tranchée", kept)

    def test_an_explicit_request_replaces_the_mandate_without_losing_the_corpus(self) -> None:
        follow_up = self.prepared()
        request = self.request(follow_up, demande=facade.DemandeSource("Ma demande.", "cadrage"))
        result = facade.create_collaboration(request, adapters=self.adapters)
        self.assertEqual((result.path / "demande.md").read_text("utf-8"), "Ma demande.")
        self.assertEqual(len(corpus.read_manifest(
            result.path / "corpus" / "manifeste.json").entries), len(facade.FOLLOW_UP_FILES))

    def test_a_stopped_research_between_preparation_and_creation_blocks_it(self) -> None:
        """AC04 : jamais deux versions mélangées."""
        research = self.research()
        follow_up = self.prepared(research)
        workflow.decide(research, decisions.STOPPED, reason="abandon après la préparation")
        self.assertIn("non acceptée", self.refused(self.request(follow_up)))

    def test_a_document_modified_after_preparation_blocks_the_creation(self) -> None:
        research = self.research()
        follow_up = self.prepared(research)
        (research / "livrables" / "bilan.md").write_text("autre bilan", encoding="utf-8")
        self.assertIn("a changé depuis la préparation", self.refused(self.request(follow_up)))

    def test_a_revoked_acceptance_blocks_the_creation(self) -> None:
        research = self.research()
        follow_up = self.prepared(research)
        (research / decisions.DELIVERED).write_text("modifié après coup", encoding="utf-8")
        self.assertIn("non acceptée", self.refused(self.request(follow_up)))

    def test_it_only_leads_to_a_conception_with_no_other_corpus(self) -> None:
        follow_up = self.prepared()
        refusal = self.refused(self.request(follow_up, kind=MissionKind.RECHERCHE))
        self.assertIn("qu'en conception", refusal)
        listing = self.root_dir / "liste.txt"
        listing.write_text("demande.md\n", encoding="utf-8")
        refusal = self.refused(
            self.request(follow_up, source_root=follow_up.research, source_list=listing),
        )
        self.assertIn("pas d'autre corpus", refusal)

    def test_it_is_allowed_with_a_framing_that_read_another_corpus_only_if_identical(self) -> None:
        """AC05 : un cadrage qui n'a pas lu l'instantané préparé est refusé avant création."""
        follow_up = self.prepared()
        other = self.root_dir / "autre-cadrage"
        (other / "corpus").mkdir(parents=True)
        (other / "corpus" / "manifeste.json").write_text("{}", encoding="utf-8")
        framing = FramingArtifacts(other, "# Demande\n", {})
        self.assertIn(
            "n'a pas lu l'instantané", self.refused(self.request(follow_up, framing=framing)),
        )


class TestTheCommandLine(FollowUpCase):
    def argv(self, research: Path, *extra: str) -> list[str]:
        return ["new", str(self.root_dir / "plan"), "--depuis", str(research), *extra]

    def run_cli(self, argv: list[str]) -> tuple[int, str]:
        err = io.StringIO()
        with mock.patch.object(cli, "ADAPTERS", self.adapters), \
                mock.patch.object(settings, "SEARCH_PATHS", ()), \
                redirect_stdout(io.StringIO()), redirect_stderr(err):
            return cli.main(argv), err.getvalue()

    def test_depuis_alone_uses_the_mandate_and_the_inherited_settings(self) -> None:
        research = self.research()
        code, err = self.run_cli(self.argv(research))
        self.assertEqual(code, 0, err)
        plan = self.root_dir / "plan"
        text = (plan / "demande.md").read_text(encoding="utf-8")
        self.assertEqual(demande.missing(text), [])
        self.assertIn("web_access=False", err)
        config = json.loads((plan / "configuration.json").read_text(encoding="utf-8"))
        self.assertEqual(
            (config["mission_kind"], config["max_revisions"], config.get("web_access", False)),
            ("CONCEPTION", 3, False),
        )
        manifest = corpus.read_manifest(plan / "corpus" / "manifeste.json")
        self.assertEqual(len(manifest.entries), len(facade.FOLLOW_UP_FILES))
        self.assertTrue((plan / facade.TRANSITION).is_file())

    def test_flags_beat_inherited_settings_and_models_follow_their_tool(self) -> None:
        research = self.research()
        code, err = self.run_cli(self.argv(research, "--agent-a", "fake-b", "--max-revisions", "1"))
        self.assertEqual(code, 0, err)
        config = json.loads((self.root_dir / "plan" / "configuration.json").read_text("utf-8"))
        self.assertEqual(config["agent_a"]["adapter_id"], "fake-b")
        self.assertNotEqual(config["agent_a"]["model"], "fake-a-modele-a")
        self.assertEqual(config["max_revisions"], 1)

    def test_an_explicit_request_replaces_the_mandate_and_keeps_the_corpus(self) -> None:
        research = self.research()
        demande_file = self.root_dir / "ma-demande.md"
        demande_file.write_text("Concevoir à partir de la recherche.", encoding="utf-8")
        code, err = self.run_cli(self.argv(research, "--demande", str(demande_file)))
        self.assertEqual(code, 0, err)
        plan = self.root_dir / "plan"
        self.assertEqual(
            (plan / "demande.md").read_text("utf-8"), "Concevoir à partir de la recherche.",
        )
        self.assertEqual(len(corpus.read_manifest(
            plan / "corpus" / "manifeste.json").entries), len(facade.FOLLOW_UP_FILES))

    def test_a_refused_research_creates_nothing_and_leaves_no_snapshot(self) -> None:
        research = self.research(accept=False)
        code, _ = self.run_cli(self.argv(research))
        self.assertEqual(code, 1)
        self.assertFalse((self.root_dir / "plan").exists())


class TestTheFramedTransition(FramingCliCase):
    """AC05 : F lit le corpus et le mandat de l'instantané ; la création garde ce même corpus."""

    def research(self) -> Path:
        collab = fakes.collaboration(
            self.root / "recherche", mission_kind="RECHERCHE", demande=_ORIGIN,
        )
        a = fakes.FakeAdapter("fake-a", (_DOC,))
        b = fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),))
        workflow.run(collab, adapters={"fake-a": a, "fake-b": b}, timeout_seconds=30.0)
        workflow.decide(collab, decisions.ACCEPTED)
        return collab

    def framed(self, research: Path, inputs: list[str], *replies: Any) -> int:
        self.f.framing_responses = list(replies)
        argv = [
            "new", str(self.collab), "--cadrer-avec-agent", "--agent-cadrage", "fake-f",
            "--depuis", str(research), "--agent-a", "fake-a", "--agent-b", "fake-b",
            "--reviewer-access", "consult",
        ]
        with mock.patch("builtins.input", side_effect=inputs), \
                mock.patch("sys.stdout"), mock.patch("sys.stderr"):
            return cli.main(argv)

    def test_f_reads_the_prepared_mandate_and_the_same_corpus_is_kept(self) -> None:
        research = self.research()
        real_build = corpus.build_from
        with mock.patch.object(corpus, "build_from", wraps=real_build) as built:
            rc = self.framed(research, ["r", "v"], READY_OUT, DRAFT_OUT)
        self.assertEqual(rc, 0)
        self.assertEqual(built.call_count, 1)  # l'instantané seul : la création ne reconstruit rien
        (history,) = self.f.framing_sessions.values()
        first = " ".join(history[0].split())
        self.assertIn("# Conception du projet", history[0])
        self.assertIn("mandat déjà rédigé", first)
        self.assertIn("Précise seulement les arbitrages encore nécessaires", first)
        self.assertIn("son livrable est un plan de réalisation", first)
        manifest = corpus.read_manifest(self.collab / "corpus" / "manifeste.json")
        self.assertEqual(
            sorted(e.logical_path for e in manifest.entries), sorted(facade.FOLLOW_UP_FILES),
        )
        provenance = self.read_json("provenance_demande.json")["versions"][0]
        self.assertEqual(provenance["method"], "agent")
        self.assertEqual(self.read_json(facade.TRANSITION)["source"], research.name)
        draft = DRAFT_OUT.removeprefix("IABINOME:DEMANDE\n")
        self.assertEqual((self.collab / "demande.md").read_text(encoding="utf-8"), draft)

    def test_a_research_changed_during_framing_blocks_the_creation(self) -> None:
        """AC04 : les sources ne sont pas remplacées sous une conversation de F."""
        research = self.research()

        def change(_history: list[str]) -> str:
            workflow.decide(research, decisions.STOPPED, reason="abandon pendant le cadrage")
            return DRAFT_OUT

        rc = self.framed(research, ["r", "v", "a"], READY_OUT, change)
        self.assertEqual(rc, 1)
        self.assertFalse(self.collab.exists())


class TestTheGui(FollowUpCase):
    def test_the_follow_up_button_opens_a_prefilled_conception(self) -> None:
        research = self.research()
        suivi = SuiviView(_ROOT, self.controller, research)
        button = _find_button(suivi, "Poursuivre en conception")
        self.assertEqual(button.winfo_manager(), "pack")
        with mock.patch.object(self.controller, "show_creation") as show:
            button.invoke()
        show.assert_called_once_with(from_research=research)

    def test_the_form_gets_the_mandate_and_the_source_settings(self) -> None:
        research = self.research()
        view = CreationView(_ROOT, self.controller, from_research=research)
        self.assertEqual(view._kind.get(), "Concevoir mon projet")
        self.assertEqual(view._dossier.get(), str(self.root_dir / "collaboration-conception"))
        mandate = view._current_text()
        self.assertEqual(demande.missing(mandate), [])
        self.assertEqual(view._framing_panel.idea.get("1.0", "end-1c"), mandate)
        self.assertEqual((view._agent_a.get(), view._agent_b.get()), ("fake-a", "fake-b"))
        self.assertEqual(view._revisions.get(), "3")
        self.assertFalse(view._web_access.get())
        request = view._build_request()
        assert request is not None
        assert request.follow_up is not None
        self.assertEqual(request.follow_up.research, research)
        self.assertEqual(request.follow_up.mandate, mandate)
        self.assertTrue(any(
            "Accès web hérité de la recherche : fermé" in text for text in label_texts(view)
        ))

    def test_the_snapshot_is_removed_when_the_form_is_left(self) -> None:
        view = CreationView(_ROOT, self.controller, from_research=self.research())
        assert view._follow_up is not None
        root = view._follow_up.root
        self.assertTrue(root.is_dir())
        view.destroy()
        self.assertFalse(root.exists())

    def test_a_refused_research_shows_the_reason_and_an_empty_form(self) -> None:
        view = CreationView(_ROOT, self.controller, from_research=self.research(accept=False))
        self.assertIsNone(view._follow_up)
        self.assertIn("non acceptée", str(view._error.cget("text")))

    def test_the_framing_receives_the_mandate_as_edited_on_screen(self) -> None:
        """Une correction du mandat avant le cadrage parvient à F, pas l'ancien texte."""
        view = CreationView(_ROOT, self.controller, from_research=self.research())
        view._demande_text.insert("end", "\nPrécision ajoutée par l'humain.")
        view._mode.set("agent")
        view._on_mode()
        panel = view._framing_panel
        self.assertEqual(panel.idea.get("1.0", "end-1c"), view._current_text())
        panel.agent.set("fake-f")
        base = view._build_request(framing_start=True)
        assert base is not None
        adapters = {**self.adapters, "fake-f": fakes.FakeAdapter("fake-f", ())}
        with mock.patch.object(cadrage, "ADAPTERS", adapters), \
                mock.patch("iabinome.gui.controller.ADAPTERS", adapters):
            f = cadrage.begin(self.controller, base, panel, 30.0)
        self.addCleanup(self.controller.discard_framing)
        self.assertIn("Précision ajoutée par l'humain.", f.idea)

    def test_an_inherited_model_missing_from_the_catalog_is_kept_and_labelled(self) -> None:
        collab = fakes.collaboration(
            self.root_dir, mission_kind="RECHERCHE", demande=_ORIGIN, model_a="modele-hors-liste",
        )
        a = fakes.FakeAdapter("fake-a", (_DOC,))
        b = fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),))
        workflow.run(collab, adapters={"fake-a": a, "fake-b": b}, timeout_seconds=30.0)
        workflow.decide(collab, decisions.ACCEPTED)
        view = CreationView(_ROOT, self.controller, from_research=collab)
        shown = "modele-hors-liste (hérité de la recherche)"
        self.assertEqual(view._model_a.get(), shown)
        self.assertIn(shown, view._model_selector_a.cget("values"))
        request = view._build_request()
        assert request is not None
        self.assertEqual(request.model_a, "modele-hors-liste")
        view._agent_a.set("claude")  # un autre outil : le modèle hérité ne le suit pas
        view._sync_model("A")
        self.assertEqual(view._model_a.get(), "(par défaut)")

    def test_the_framing_starts_from_the_prepared_corpus_and_mandate(self) -> None:
        """AC05, côté GUI : la même préparation alimente F, sans second corpus."""
        research = self.research()
        view = CreationView(_ROOT, self.controller, from_research=research)
        base = view._build_request(framing_start=True)
        assert base is not None
        panel = view._framing_panel
        panel.agent.set("fake-f")
        adapters = {**self.adapters, "fake-f": fakes.FakeAdapter("fake-f", ())}
        with mock.patch.object(cadrage, "ADAPTERS", adapters), \
                mock.patch("iabinome.gui.controller.ADAPTERS", adapters):
            f = cadrage.begin(self.controller, base, panel, 30.0)
        self.addCleanup(self.controller.discard_framing)
        self.assertEqual(f.idea, view._current_text().strip())
        files = sorted(
            p.relative_to(f.root / "travail" / "corpus" / "fichiers").as_posix()
            for p in (f.root / "travail" / "corpus" / "fichiers").rglob("*") if p.is_file()
        )
        self.assertEqual(files, sorted(facade.FOLLOW_UP_FILES))
        assert base.follow_up is not None
        self.assertEqual(
            (f.root / "corpus" / "manifeste.json").read_bytes(),
            (base.follow_up.corpus / "manifeste.json").read_bytes(),
        )

    def test_no_follow_up_button_before_acceptance(self) -> None:
        suivi = SuiviView(_ROOT, self.controller, self.research(accept=False))
        with self.assertRaises(LookupError):  # aucun bouton : la poursuite n'est pas permise
            _find_button(suivi, "Poursuivre en conception")

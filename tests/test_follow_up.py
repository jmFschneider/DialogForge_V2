"""Poursuivre une recherche acceptée en conception (`conception/TYPES_DE_MISSION.md` D4).

Le livrable, le bilan et la décision de la recherche deviennent le corpus de la conception ;
le manifeste nomme la recherche d'origine et garde l'empreinte du livrable. Rien n'est lancé.
"""

from __future__ import annotations

import hashlib
import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from iabinome import cli, corpus, decisions, facade, settings, workflow
from iabinome.gui.views.creation import CreationView
from iabinome.gui.views.suivi import SuiviView
from iabinome.models import MissionKind, ReviewerAccess
from tests import fakes
from tests.test_gui_views import _ROOT, ViewCase, _find_button

_DOC = "IABINOME:DOCUMENT\n# Synthèse\nCe que disent les sources."


class FollowUpCase(ViewCase):
    def setUp(self) -> None:
        super().setUp()
        self.adapters = {
            "fake-a": fakes.FakeAdapter("fake-a", ()), "fake-b": fakes.FakeAdapter("fake-b", ()),
        }

    def research(self, *, kind: str = "RECHERCHE", accept: bool = True) -> Path:
        collab = fakes.collaboration(self.root_dir, mission_kind=kind)
        a = fakes.FakeAdapter("fake-a", (_DOC,))
        b = fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),))
        workflow.run(collab, adapters={"fake-a": a, "fake-b": b}, timeout_seconds=30.0)
        if accept:
            workflow.decide(collab, decisions.ACCEPTED)
        return collab

    def request(self, research: Path, **overrides: object) -> facade.CreationRequest:
        base: dict[str, object] = {
            "collab": self.root_dir / "conception",
            "demande": facade.DemandeSource("Concevoir à partir de la recherche.", "cadrage"),
            "kind": MissionKind.CONCEPTION, "reviewer_access": ReviewerAccess.CONSULT,
            "agent_a": "fake-a", "agent_b": "fake-b", "max_revisions": 1,
            "from_research": research,
        }
        base.update(overrides)
        return facade.CreationRequest(**base)  # type: ignore[arg-type]

    def refused(self, request: facade.CreationRequest) -> str:
        with self.assertRaises(facade.CreationError) as ctx:
            facade.create_collaboration(request, adapters=self.adapters)
        self.assertFalse(request.collab.exists())
        return str(ctx.exception)


class TestTheFacade(FollowUpCase):
    def test_the_accepted_research_becomes_the_corpus_with_its_provenance(self) -> None:
        research = self.research()
        result = facade.create_collaboration(self.request(research), adapters=self.adapters)
        manifest = corpus.read_manifest(result.path / "corpus" / "manifeste.json")
        self.assertEqual(manifest.origin_label, f"recherche {research.name}")
        self.assertEqual(
            sorted(entry.logical_path for entry in manifest.entries),
            sorted(facade.FOLLOW_UP_FILES),
        )
        livrable = (research / decisions.DELIVERED).read_bytes()
        by_path = {entry.logical_path: entry.sha256 for entry in manifest.entries}
        self.assertEqual(by_path[decisions.DELIVERED], hashlib.sha256(livrable).hexdigest())
        config = json.loads((result.path / "configuration.json").read_text(encoding="utf-8"))
        self.assertEqual(config["mission_kind"], "CONCEPTION")
        self.assertIsNotNone(config["corpus_manifest_sha256"])

    def test_a_research_not_yet_accepted_is_refused(self) -> None:
        self.assertIn("non acceptée", self.refused(self.request(self.research(accept=False))))

    def test_an_acceptance_that_no_longer_applies_is_refused(self) -> None:
        research = self.research()
        (research / decisions.DELIVERED).write_text("modifié après coup", encoding="utf-8")
        self.assertIn("non acceptée", self.refused(self.request(research)))

    def test_only_a_research_can_be_followed(self) -> None:
        refusal = self.refused(self.request(self.research(kind="CONCEPTION")))
        self.assertIn("n'est pas une recherche", refusal)

    def test_it_only_leads_to_a_conception_with_no_other_corpus(self) -> None:
        research = self.research()
        refusal = self.refused(self.request(research, kind=MissionKind.RECHERCHE))
        self.assertIn("qu'en conception", refusal)
        listing = self.root_dir / "liste.txt"
        listing.write_text("demande.md\n", encoding="utf-8")
        refusal = self.refused(
            self.request(research, source_root=research, source_list=listing),
        )
        self.assertIn("pas d'autre corpus", refusal)

    def test_it_is_refused_before_any_framing_call(self) -> None:
        with self.assertRaisesRegex(facade.CreationError, "cadrage par un agent"):
            facade.check_creation(
                self.request(self.research()), adapters=self.adapters, framing_start=True,
            )

    def test_only_an_accepted_research_offers_to_follow_up(self) -> None:
        accepted = facade.inspect_collaboration(self.research())
        self.assertTrue(accepted.presentation.can_follow_up)
        not_accepted = facade.inspect_collaboration(self.research(accept=False))
        self.assertFalse(not_accepted.presentation.can_follow_up)

    def test_a_stopped_research_cannot_be_followed_even_on_its_current_version(self) -> None:
        research = self.research(accept=False)
        workflow.decide(research, decisions.STOPPED, reason="abandon")
        self.assertFalse(facade.inspect_collaboration(research).presentation.can_follow_up)
        self.assertIn("non acceptée", self.refused(self.request(research)))

    def test_an_accepted_conception_does_not_offer_it(self) -> None:
        conception = facade.inspect_collaboration(self.research(kind="CONCEPTION"))
        self.assertFalse(conception.presentation.can_follow_up)


class TestTheCommandLine(FollowUpCase):
    def test_new_depuis_creates_the_conception(self) -> None:
        research = self.research()
        demande = self.root_dir / "demande.md"
        demande.write_text("Concevoir à partir de la recherche.", encoding="utf-8")
        argv = [
            "new", str(self.root_dir / "plan"), "--demande", str(demande),
            "--kind", "conception", "--depuis", str(research), "--reviewer-access", "consult",
            "--agent-a", "fake-a", "--agent-b", "fake-b",
        ]
        with mock.patch.object(cli, "ADAPTERS", self.adapters), \
                mock.patch.object(settings, "SEARCH_PATHS", ()), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(argv), 0)
        manifest = corpus.read_manifest(self.root_dir / "plan" / "corpus" / "manifeste.json")
        self.assertEqual(manifest.origin_label, f"recherche {research.name}")
        self.assertEqual(len(manifest.entries), len(facade.FOLLOW_UP_FILES))


class TestTheGui(FollowUpCase):
    def test_the_follow_up_button_opens_a_prefilled_conception(self) -> None:
        research = self.research()
        suivi = SuiviView(_ROOT, self.controller, research)
        button = _find_button(suivi, "Poursuivre en conception")
        self.assertEqual(button.winfo_manager(), "pack")
        with mock.patch.object(self.controller, "show_creation") as show:
            button.invoke()
        show.assert_called_once_with(from_research=research)
        view = CreationView(_ROOT, self.controller, from_research=research)
        self.assertEqual(view._kind.get(), "Conception")
        self.assertEqual(view._dossier.get(), str(self.root_dir / "collaboration-conception"))
        self.assertIn(f"recherche « {research.name} »", view._current_text())
        request = view._build_request()
        assert request is not None
        self.assertEqual(request.from_research, research)

    def test_no_follow_up_button_before_acceptance(self) -> None:
        suivi = SuiviView(_ROOT, self.controller, self.research(accept=False))
        button = _find_button(suivi, "Poursuivre en conception")
        self.assertEqual(button.winfo_manager(), "")

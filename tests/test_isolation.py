"""Tests du lot 2, point 2.2 : séparation des rôles.

Validation du plan : **essai sur dossier jetable ; capacités effectives par profil
d'adaptateur ; un profil incapable de la protection requise est restreint ou déclaré
non supporté.**

Les agents ci-dessous sont des **faux** qui *observent* ce qu'on leur donne (dossier de
travail, environnement) ou *se comportent mal* (écrire dans les sources). Aucune CLI
réelle : ce qu'une vraie CLI fait des drapeaux reste à mesurer au lot 3, et n'est prouvé
ici que dans l'argv construit (`test_adapters.py`).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest import mock

from iabinome import incidents, isolation, workflow
from iabinome.adapters.base import CallSpec
from iabinome.models import State, Status
from tests import fakes
from tests.test_incidents import IncidentCase

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."

_HOST_ENV = {
    "PLAN_ID": "2026-09-18-dialogforge-v2",
    "PWF_PLAN_ROOT": "C:/hote/plans",
    "CLAUDE_CODE_SESSION_ID": "session-secrete",
    "CLAUDE_CODE_MESSAGING_TOKEN": "jeton-secret",
    "CLAUDE_PLUGIN_ROOT": "C:/hote/plugin",
    # L'hôte Codex (signalé à la validation de 2.2).
    "CODEX_SESSION_ID": "session-codex-secrete",
    "CODEX_THREAD_ID": "fil-codex-secret",
    "CODEX_PERMISSION_PROFILE": "profil-de-l-hote",
}
# À garder : sans elles, l'authentification ou l'outil lui-même casseraient.
_KEPT_ENV = {
    "CLAUDE_CODE_OAUTH_TOKEN": "jeton-d-authentification",
    "CLAUDE_CODE_GIT_BASH_PATH": "C:/Git/bin/bash.exe",
    "ANTHROPIC_API_KEY": "cle",
    # Opérationnelles côté Codex : `CODEX_HOME` porte l'authentification, le lanceur
    # réécrit `CODEX_MANAGED_PACKAGE_ROOT` (raisons : `isolation.KEPT_ON_PURPOSE`).
    "CODEX_HOME": "C:/Users/x/.codex",
    "CODEX_MANAGED_PACKAGE_ROOT": "C:/npm/node_modules/@openai/codex",
}


class _Spy(fakes.FakeAdapter):
    """Un faux agent qui consigne ce qu'il voit, puis répond `reply`.

    `tamper_copy` écrit dans la copie du corpus **de son dossier de travail** ;
    `tamper_real` écrit dans un chemin **absolu** — l'original, hors de sa portée
    légitime. Ce dernier cas est celui qu'aucun drapeau d'argv ne peut empêcher."""

    def __init__(
        self,
        adapter_id: str,
        responses: tuple[str, ...],
        out: Path,
        *,
        tamper_copy: str | None = None,
        tamper_real: Path | None = None,
    ) -> None:
        super().__init__(adapter_id, responses)
        self.out = out
        self.tamper_copy = tamper_copy
        self.tamper_real = tamper_real

    def command(self, call: CallSpec) -> list[str]:
        argv = super().command(call)  # consomme la réponse scriptée, comme d'habitude
        reply = argv[-1].split("sys.stdout.buffer.write(")[1].split("); sys.stdout")[0]
        lines = [
            "import json, os, pathlib, sys",
            "here = pathlib.Path('.').resolve()",
            "seen = {'cwd': str(here), 'entries': sorted(p.name for p in here.iterdir()),",
            "        'env': sorted(os.environ),",
            "        'corpus': sorted(p.name for p in (here / 'corpus' / 'fichiers').glob('*'))}",
            f"pathlib.Path({str(self.out)!r}).write_text(json.dumps(seen), encoding='utf-8')",
        ]
        if self.tamper_copy is not None:
            lines.append(
                f"(here / 'corpus' / 'fichiers' / {self.tamper_copy!r}).write_text('ALTERE')"
            )
        if self.tamper_real is not None:
            lines.append(f"pathlib.Path({str(self.tamper_real)!r}).write_text('ALTERE')")
        lines.append(f"sys.stdout.buffer.write({reply}); sys.stdout.flush()")
        return [sys.executable, "-c", "\n".join(lines)]


class SeparationCase(IncidentCase):
    def spy_collaboration(
        self, *, tamper_copy: str | None = None, tamper_real: bool = False
    ) -> tuple[Path, Path]:
        collab = fakes.collaboration(
            self.root, corpus_captured_at="2026-09-01",
            corpus_files={"a.txt": "contenu de a", "b.txt": "contenu de b"},
        )
        self.out = self.root / "vu.json"
        real = collab / "corpus" / "fichiers" / "a.txt"
        self.a = _Spy(
            "fake-a", (_DOC,), self.out, tamper_copy=tamper_copy,
            tamper_real=real if tamper_real else None,
        )
        self.b = fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),))
        self.adapters = {"fake-a": self.a, "fake-b": self.b}
        return collab, real

    def seen(self) -> dict[str, object]:
        seen = json.loads(self.out.read_text(encoding="utf-8"))
        assert isinstance(seen, dict)
        return seen


class TestNeutralWorkdir(SeparationCase):
    def test_the_agent_runs_outside_the_collaboration(self) -> None:
        collab, _ = self.spy_collaboration()
        self.run_engine(collab)
        cwd = Path(str(self.seen()["cwd"]))
        self.assertNotEqual(cwd, collab.resolve())
        self.assertNotIn(collab.resolve(), cwd.parents)

    def test_it_sees_the_corpus_and_nothing_of_the_collaboration(self) -> None:
        """Ni `appels/`, ni `echanges/` (le journal du producteur), ni les
        versions de `demande.md`, ni l'état : que le corpus, où les prompts le nomment."""
        collab, _ = self.spy_collaboration()
        self.run_engine(collab)
        seen = self.seen()
        self.assertEqual(seen["entries"], ["corpus"])
        self.assertEqual(seen["corpus"], ["a.txt", "b.txt"])

    def test_without_a_corpus_the_directory_is_empty(self) -> None:
        collab = fakes.collaboration(self.root)
        self.out = self.root / "vu.json"
        self.a = _Spy("fake-a", (_DOC,), self.out)
        self.b = fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),))
        self.adapters = {"fake-a": self.a, "fake-b": self.b}
        self.run_engine(collab)
        self.assertEqual(self.seen()["entries"], [])

    def test_the_directory_does_not_outlive_the_call(self) -> None:
        collab, _ = self.spy_collaboration()
        self.run_engine(collab)
        self.assertFalse(Path(str(self.seen()["cwd"])).exists())

    def test_writing_in_the_copy_never_reaches_the_original_corpus(self) -> None:
        """Une copie, jamais un lien : l'écrire ne touche pas la source, et le cycle
        n'y voit rien à redire."""
        collab, real = self.spy_collaboration(tamper_copy="a.txt")
        state = self.run_engine(collab)
        self.assertEqual(real.read_text(encoding="utf-8"), "contenu de a")
        self.assertIsNot(getattr(state, "status", None), Status.INTERRUPTED)
        self.assertEqual(self.state(collab).last_incident, None)


class TestEnvironment(SeparationCase):
    def test_the_reviewer_does_not_inherit_the_host_or_plan_context_either(self) -> None:
        """2.3 : « le reviewer ne doit pas hériter du contexte PWF du producteur ». Le même
        filtre s'applique aux deux rôles — plus strict que « selon le rôle » : aucun des deux
        n'a besoin du plan, qui reste l'affaire de l'humain."""
        collab, _ = self.spy_collaboration()
        seen_by_b = self.root / "vu-par-b.json"
        self.b = _Spy("fake-b", (fakes.review("ACCEPTER"),), seen_by_b)
        self.adapters = {"fake-a": self.a, "fake-b": self.b}
        with mock.patch.dict(os.environ, {**_HOST_ENV, **_KEPT_ENV}):
            self.run_engine(collab)
        names = set(json.loads(seen_by_b.read_text(encoding="utf-8"))["env"])
        for name in _HOST_ENV:
            self.assertNotIn(name, names)
        for name in _KEPT_ENV:
            self.assertIn(name, names)

    def test_host_variables_do_not_reach_the_agent(self) -> None:
        collab, _ = self.spy_collaboration()
        with mock.patch.dict(os.environ, {**_HOST_ENV, **_KEPT_ENV}):
            self.run_engine(collab)
        names = set(self.seen()["env"])  # type: ignore[call-overload]
        for name in _HOST_ENV:
            self.assertNotIn(name, names)

    def test_authentication_and_the_rest_are_kept(self) -> None:
        collab, _ = self.spy_collaboration()
        with mock.patch.dict(os.environ, {**_HOST_ENV, **_KEPT_ENV}):
            self.run_engine(collab)
        names = set(self.seen()["env"])  # type: ignore[call-overload]
        for name in _KEPT_ENV:
            self.assertIn(name, names)
        self.assertIn("PATH", names)

    def test_the_intention_names_what_was_removed_and_never_its_value(self) -> None:
        collab, _ = self.spy_collaboration()
        with mock.patch.dict(os.environ, {**_HOST_ENV, **_KEPT_ENV}):
            self.run_engine(collab)
        call_dir = next((collab / "appels").iterdir())
        intention_text = (call_dir / "intention.json").read_text(encoding="utf-8")
        intention = json.loads(intention_text)
        self.assertEqual(intention["workdir"], "neutre")
        for name in _HOST_ENV:
            self.assertIn(name, intention["env_removed"])
        for value in _HOST_ENV.values():
            self.assertNotIn(value, intention_text)

    def test_the_codex_host_variables_are_removed_by_name(self) -> None:
        """Le cas observé : un agent lancé depuis Codex héritait de l'identité de l'hôte."""
        cleaned = isolation.clean_env({**_HOST_ENV, **_KEPT_ENV})
        for name in ("CODEX_SESSION_ID", "CODEX_THREAD_ID", "CODEX_PERMISSION_PROFILE"):
            self.assertNotIn(name, cleaned)
        self.assertEqual(sorted(cleaned), sorted(_KEPT_ENV))

    def test_no_blanket_codex_or_claude_refusal(self) -> None:
        """Un refus global casserait l'authentification ou le lanceur : une variable
        `CODEX_*` ou `CLAUDE_*` qu'aucune règle nommée ne vise **passe**."""
        unknown = {"CODEX_UNE_AUTRE": "1", "CLAUDE_UNE_AUTRE": "2", "CODEX": "3"}
        self.assertEqual(isolation.clean_env(unknown), unknown)

    def test_operational_variables_are_kept_explicitly_and_justified(self) -> None:
        for name, reason in isolation.KEPT_ON_PURPOSE.items():
            self.assertEqual(isolation.clean_env({name: "v"}), {name: "v"}, name)
            self.assertEqual(isolation.refused_names({name: "v"}), [], name)
            self.assertGreater(len(reason), 20, name)  # une raison, pas une étiquette
        self.assertEqual(set(isolation.KEPT_ON_PURPOSE), {
            "CODEX_HOME", "CODEX_MANAGED_PACKAGE_ROOT",
            "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_GIT_BASH_PATH",
        })

    def test_matching_ignores_case_for_every_refused_and_kept_name(self) -> None:
        """Windows ne distingue pas la casse : `Codex_Thread_Id` est `CODEX_THREAD_ID`."""
        env = {name.lower(): "v" for name in _HOST_ENV}
        env.update({name.title(): "v" for name in isolation.KEPT_ON_PURPOSE})
        self.assertEqual(sorted(isolation.clean_env(env)),
                         sorted(n.title() for n in isolation.KEPT_ON_PURPOSE))
        self.assertEqual(isolation.refused_names(env), sorted(n.lower() for n in _HOST_ENV))

    def test_clean_env_is_case_insensitive_and_removes_the_pwf_family(self) -> None:
        cleaned = isolation.clean_env({"pwf_autre": "1", "Plan_Id": "x", "PATH": "p"})
        self.assertEqual(cleaned, {"PATH": "p"})

    def test_clean_env_never_touches_the_process_environment(self) -> None:
        with mock.patch.dict(os.environ, _HOST_ENV):
            isolation.clean_env(os.environ)
            self.assertIn("PLAN_ID", os.environ)


class TestSourcesAreChecked(SeparationCase):
    def test_a_write_to_the_real_corpus_is_an_incident_not_a_response(self) -> None:
        """Ce qu'aucun drapeau n'empêche — un chemin absolu — est **constaté** : la
        réponse produite sur des sources changées n'est pas retenue."""
        collab, real = self.spy_collaboration(tamper_real=True)
        state = self.run_engine(collab)
        self.assertIs(state.status, Status.INTERRUPTED)  # type: ignore[attr-defined]
        self.assertEqual(real.read_text(encoding="utf-8"), "ALTERE")
        current = self.state(collab)
        self.assertEqual(incidents.incident(collab, current)["kind"], "SOURCES_MODIFIED")  # type: ignore[index]
        call_dir = collab / str(current.current_call.call_dir)  # type: ignore[union-attr]
        self.assertFalse((call_dir / "reponse_brute.txt").exists())
        self.assertFalse((collab / "livrables").exists())

    def test_it_is_explained_and_says_how_to_go_on(self) -> None:
        collab, _ = self.spy_collaboration(tamper_real=True)
        self.run_engine(collab)
        text = self.explained(collab)
        self.assertIn("SOURCES_MODIFIED", text)
        self.assertIn("Payé ? : peut-être", text)
        action = incidents.action(collab, self.state(collab))
        self.assertIn("rétablir", action)
        self.assertIn("--retry-call", action)

    def test_nothing_is_relaunched_on_its_own(self) -> None:
        collab, _ = self.spy_collaboration(tamper_real=True)
        self.run_engine(collab)
        self.assertEqual(self.launched(collab), 1)
        with self.assertRaises(workflow.WorkflowError):
            self.run_engine(collab)
        self.assertEqual(self.launched(collab), 1)

    def test_untouched_sources_leave_no_incident(self) -> None:
        collab, _ = self.spy_collaboration()
        self.run_engine(collab)
        self.assertIsNone(self.state(collab).last_incident)

    def launched(self, collab: Path) -> int:
        return fakes.launched_calls(collab)


class TestProfileCapabilities(SeparationCase):
    """Un adaptateur qui ne déclare pas la séparation est **refusé avant tout appel**."""

    def refused(
        self, *, enforces_read_only: bool = True, fresh_session: bool = True
    ) -> tuple[Path, fakes.FakeAdapter]:
        collab = fakes.collaboration(self.root)
        weak = fakes.FakeAdapter(
            "fake-a", (_DOC,), enforces_read_only=enforces_read_only, fresh_session=fresh_session
        )
        self.adapters = {
            "fake-a": weak, "fake-b": fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),)),
        }
        return collab, weak

    def test_an_adapter_that_cannot_enforce_read_only_is_not_supported(self) -> None:
        collab, weak = self.refused(enforces_read_only=False)
        before = (collab / "etat.json").read_bytes()
        with self.assertRaisesRegex(workflow.WorkflowError, "lecture seule"):
            self.run_engine(collab)
        self.assertEqual(weak.calls, 0)
        self.assertEqual((collab / "etat.json").read_bytes(), before)
        self.assertFalse((collab / "appels").exists())

    def test_an_adapter_that_cannot_start_a_fresh_session_is_not_supported(self) -> None:
        collab, weak = self.refused(fresh_session=False)
        with self.assertRaisesRegex(workflow.WorkflowError, "session fraîche"):
            self.run_engine(collab)
        self.assertEqual(weak.calls, 0)

    def test_both_roles_are_checked(self) -> None:
        """Le reviewer n'est pas seul concerné : A produit aussi en lecture seule."""
        collab = fakes.collaboration(self.root)
        weak_b = fakes.FakeAdapter("fake-b", (), enforces_read_only=False)
        self.adapters = {"fake-a": fakes.FakeAdapter("fake-a", (_DOC,)), "fake-b": weak_b}
        with self.assertRaisesRegex(workflow.WorkflowError, "fake-b"):
            self.run_engine(collab)

    def test_the_default_test_adapter_is_fully_capable(self) -> None:
        collab = fakes.collaboration(self.root)
        self.adapters = {
            "fake-a": fakes.FakeAdapter("fake-a", (_DOC,)),
            "fake-b": fakes.FakeAdapter("fake-b", (fakes.review("ACCEPTER"),)),
        }
        self.run_engine(collab)
        self.assertIs(State.from_dict(fakes.read_json(collab / "etat.json")).status,
                      Status.AWAITING_APPROVAL)


class TestReviewerPackage(SeparationCase):
    """Le paquet de B est ce que son prompt porte — et rien de la cuisine de A."""

    def test_b_gets_the_request_and_the_examined_version_only(self) -> None:
        collab, _ = self.spy_collaboration()
        self.run_engine(collab)
        prompt = self.b.prompts[0]
        self.assertIn("Concevoir le cache de FloraPi.", prompt)
        self.assertIn("Corps du document.", prompt)
        for leak in ("appels/", "echanges/", "prompt.txt", "intention.json", "IABINOME:REPONSES"):
            self.assertNotIn(leak, prompt)

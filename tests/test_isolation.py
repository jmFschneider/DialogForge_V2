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
import pathlib
import sys
from pathlib import Path
from unittest import mock

from iabinome import decisions, incidents, isolation, workflow
from iabinome.adapters.base import CallSpec, EnvPolicy
from iabinome.adapters.claude import ClaudeAdapter
from iabinome.adapters.codex import CodexAdapter
from iabinome.models import State, Status
from tests import fakes
from tests.test_incidents import IncidentCase

_DOC = "IABINOME:DOCUMENT\n# Proposition\nCorps du document."

CLAUDE = ClaudeAdapter().env
CODEX = CodexAdapter().env

# Ce que l'humain pose, ce que l'hôte y dépose, ce que chaque fournisseur possède.
_PLAN = {"PLAN_ID": "2026-09-18-dialogforge-v2", "PWF_PLAN_ROOT": "C:/hote/plans"}
_CLAUDE_HOST = {
    "CLAUDE_CODE_SESSION_ID": "session-secrete",
    "CLAUDE_CODE_MESSAGING_TOKEN": "jeton-secret",
    "CLAUDE_PLUGIN_ROOT": "C:/hote/plugin",
}
_CODEX_HOST = {  # signalés à la validation de 2.2
    "CODEX_SESSION_ID": "session-codex-secrete",
    "CODEX_THREAD_ID": "fil-codex-secret",
    "CODEX_PERMISSION_PROFILE": "profil-de-l-hote",
}
# Ce que chaque outil garde chez lui : authentification, configuration, lanceur.
_CLAUDE_OWN = {
    "CLAUDE_CONFIG_DIR": "C:/Users/x/.claude-thermique",
    "CLAUDE_CODE_OAUTH_TOKEN": "jeton-d-authentification-claude",
    "CLAUDE_CODE_GIT_BASH_PATH": "C:/Git/bin/bash.exe",
    "ANTHROPIC_API_KEY": "cle-anthropic",
}
_CODEX_OWN = {
    "CODEX_HOME": "C:/Users/x/.codex",
    "CODEX_MANAGED_PACKAGE_ROOT": "C:/npm/node_modules/@openai/codex",
    "OPENAI_API_KEY": "cle-openai",
}
_EVERYTHING = {**_PLAN, **_CLAUDE_HOST, **_CODEX_HOST, **_CLAUDE_OWN, **_CODEX_OWN}


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
        env: EnvPolicy | None = None,
    ) -> None:
        super().__init__(adapter_id, responses, env=env)
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


class TestEnvironmentPerAdapter(SeparationCase):
    """3.1 : le filtre dépend de l'adaptateur. Chaque processus garde ce qui est à son fournisseur
    — authentification, configuration, lanceur — et ne reçoit **rien** de l'autre ; le plan et les
    sessions d'hôte sont retirés à tous."""

    def names_seen(self, path: Path) -> set[str]:
        return set(json.loads(path.read_text(encoding="utf-8"))["env"])

    def cycle_with_both_providers(self) -> tuple[Path, Path, Path]:
        """A tient la politique de Claude, B celle de Codex : les deux processus observent."""
        collab = fakes.collaboration(self.root)
        seen_a, seen_b = self.root / "vu-a.json", self.root / "vu-b.json"
        self.a = _Spy("fake-a", (_DOC,), seen_a, env=CLAUDE)
        self.b = _Spy("fake-b", (fakes.review("ACCEPTER"),), seen_b, env=CODEX)
        self.adapters = {"fake-a": self.a, "fake-b": self.b}
        with mock.patch.dict(os.environ, _EVERYTHING):
            self.run_engine(collab)
        return collab, seen_a, seen_b

    def test_the_claude_process_keeps_claude_and_loses_codex(self) -> None:
        _, seen_a, _ = self.cycle_with_both_providers()
        names = self.names_seen(seen_a)
        for name in _CLAUDE_OWN:
            self.assertIn(name, names)
        for name in {**_CODEX_OWN, **_CODEX_HOST}:
            self.assertNotIn(name, names)

    def test_the_codex_process_keeps_codex_and_loses_claude(self) -> None:
        _, _, seen_b = self.cycle_with_both_providers()
        names = self.names_seen(seen_b)
        for name in _CODEX_OWN:
            self.assertIn(name, names)
        for name in {**_CLAUDE_OWN, **_CLAUDE_HOST}:
            self.assertNotIn(name, names)

    def test_the_plan_and_every_host_session_are_removed_for_both(self) -> None:
        _, seen_a, seen_b = self.cycle_with_both_providers()
        for path in (seen_a, seen_b):
            names = self.names_seen(path)
            for name in {**_PLAN, **_CLAUDE_HOST, **_CODEX_HOST}:
                self.assertNotIn(name, names)
            self.assertIn("PATH", names)  # le reste passe

    def test_the_intention_names_what_was_removed_and_never_its_value(self) -> None:
        collab, _, _ = self.cycle_with_both_providers()
        for call_dir, foreign in (
            (next((collab / "appels").glob("*-A-*")), _CODEX_OWN),
            (next((collab / "appels").glob("*-B-*")), _CLAUDE_OWN),
        ):
            text = (call_dir / "intention.json").read_text(encoding="utf-8")
            intention = json.loads(text)
            self.assertEqual(intention["workdir"], "neutre")
            for name in {**_PLAN, **_CLAUDE_HOST, **_CODEX_HOST, **foreign}:
                self.assertIn(name, intention["env_removed"], call_dir.name)
            own = _CLAUDE_OWN if foreign is _CODEX_OWN else _CODEX_OWN
            for name in own:  # ce qui reste n'est pas dans la liste des retraits
                self.assertNotIn(name, intention["env_removed"], call_dir.name)
            for value in _EVERYTHING.values():
                self.assertNotIn(value, text)

    def test_the_other_provider_is_only_known_through_its_declared_policy(self) -> None:
        """Sans autre adaptateur déclaré, rien n'est « étranger » : le noyau ne devine pas un
        fournisseur, il lit des politiques."""
        cleaned = isolation.clean_env({**_CLAUDE_OWN, **_CODEX_OWN}, CLAUDE, others=())
        self.assertEqual(sorted(cleaned), sorted({**_CLAUDE_OWN, **_CODEX_OWN}))

    def test_claude_and_codex_in_isolation(self) -> None:
        for own, other, mine, theirs in (
            (CLAUDE, CODEX, _CLAUDE_OWN, _CODEX_OWN), (CODEX, CLAUDE, _CODEX_OWN, _CLAUDE_OWN),
        ):
            cleaned = isolation.clean_env(_EVERYTHING, own, [other])
            self.assertEqual(sorted(cleaned), sorted(mine))
            self.assertEqual(
                isolation.refused_names(_EVERYTHING, own, [other]),
                sorted(set(_EVERYTHING) - set(mine)),
            )
            self.assertFalse(set(theirs) & set(cleaned))

    def test_no_blanket_refusal_inside_a_provider(self) -> None:
        """Une variable du fournisseur lui-même qu'aucune règle ne cible **reste**, pour son
        propre processus : seul l'autre fournisseur perd ce qui n'est pas à lui."""
        own = {"CODEX_UNE_AUTRE": "1", "OPENAI_ORG": "2"}
        self.assertEqual(isolation.clean_env(own, CODEX, [CLAUDE]), own)
        self.assertEqual(isolation.clean_env(own, CLAUDE, [CODEX]), {})

    def test_each_kept_variable_has_a_reason_and_survives_its_own_provider(self) -> None:
        for policy, expected in ((CLAUDE, set(_CLAUDE_OWN)), (CODEX, set(_CODEX_OWN))):
            self.assertEqual(set(policy.kept), expected)
            for name, reason in policy.kept.items():
                self.assertGreater(len(reason), 20, name)  # une raison, pas une étiquette
                other = CODEX if policy is CLAUDE else CLAUDE
                self.assertEqual(isolation.clean_env({name: "v"}, policy, [other]), {name: "v"})
                self.assertEqual(isolation.clean_env({name: "v"}, other, [policy]), {})

    def test_a_kept_variable_survives_where_another_provider_claims_its_prefix(self) -> None:
        """`kept` n'est pas décoratif : quand le préfixe d'un autre fournisseur recouvre une
        variable dont celui-ci a besoin, c'est elle qui protège — et elle seule."""
        mine = EnvPolicy(kept={"SHARED_TOKEN": "une raison, pas une simple étiquette"})
        other = EnvPolicy(owned_prefixes=("SHARED_",))
        env = {"SHARED_TOKEN": "v", "SHARED_AUTRE": "w"}
        self.assertEqual(isolation.clean_env(env, mine, [other]), {"SHARED_TOKEN": "v"})

    def test_matching_ignores_case(self) -> None:
        """Windows ne distingue pas la casse : `Codex_Thread_Id` est `CODEX_THREAD_ID`."""
        env = {name.lower(): "v" for name in _EVERYTHING}
        mine = {name.lower() for name in _CLAUDE_OWN}
        self.assertEqual(set(isolation.clean_env(env, CLAUDE, [CODEX])), mine)
        self.assertEqual(
            set(isolation.refused_names(env, CLAUDE, [CODEX])), set(env) - mine
        )
        title = {name.title(): "v" for name in _CODEX_OWN}
        self.assertEqual(isolation.clean_env(title, CODEX, [CLAUDE]), title)

    def test_a_real_process_keeps_the_pwf_family_out_case_insensitively(self) -> None:
        cleaned = isolation.clean_env(
            {"pwf_autre": "1", "Plan_Id": "x", "PATH": "p"}, CLAUDE, [CODEX]
        )
        self.assertEqual(cleaned, {"PATH": "p"})

    def test_clean_env_never_touches_the_process_environment(self) -> None:
        with mock.patch.dict(os.environ, _EVERYTHING):
            isolation.clean_env(os.environ, CLAUDE, [CODEX])
            self.assertIn("PLAN_ID", os.environ)
            self.assertIn("CODEX_HOME", os.environ)

    def test_the_kernel_names_no_provider(self) -> None:
        """`CLAUDE.md` §6 : aucun fournisseur nommé hors de son adaptateur."""
        source = pathlib.Path(isolation.__file__).read_text(encoding="utf-8").lower()
        for name in ("claude", "codex", "anthropic", "openai"):
            self.assertNotIn(name, source)


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
        action = decisions.next_action(collab, self.state(collab))
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

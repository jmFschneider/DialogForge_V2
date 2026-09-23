"""GUI V1, lot 1 : ce que l'humain peut faire est une **structure**, et la CLI en
dérive ses phrases (`conception/GUI_V1.md` §10.2).

Trois garanties :

- **parité** : les phrases de la CLI n'ont pas bougé au passage à la structure —
  elles sont figées ici telles que le programme les produisait avant ;
- **la structure dit ce que le moteur accepte** : une action annoncée est une
  action que `workflow` laisse passer, statut par statut ;
- **une phrase ne nomme que des actions permises** : la CLI ne garde aucune
  table concurrente.
"""

from __future__ import annotations

from pathlib import Path

from iabinome import decisions, workflow
from iabinome.decisions import ActionId
from tests import fakes
from tests.test_decision import _DOC, _QUESTION, DecisionCase
from tests.test_incidents import _Absent

_CALL = "{call}"


class ActionsCase(DecisionCase):
    """Un dossier par situation que l'humain peut rencontrer."""

    def ready_fresh(self) -> Path:
        return self.build(a=(_DOC,), b=())

    def ready_paused(self) -> Path:
        collab = self.build(a=(_DOC,), b=(fakes.review("REVISER"),))
        self.run_engine(collab, pause=lambda: True)
        return collab

    def running(self) -> Path:
        collab = self.build(a=(_DOC,), b=())
        etat = fakes.read_json(collab / "etat.json")
        etat["status"] = "RUNNING"
        etat["current_call"] = {
            "call_id": "abcdef", "sequence": 1, "role": "A", "phase": "PROPOSAL_A",
            "status": "CALLING", "call_dir": "appels/0001-A-abcdef",
            "prompt_sha256": "0" * 64, "response_sha256": None,
            "started_at": "2026-09-23T00:00:00Z", "completed_at": None,
        }
        fakes.write_json(collab / "etat.json", etat)
        return collab

    def question(self) -> Path:
        return self.cycle((_QUESTION,), ())

    def open_blocking(self) -> Path:
        blocking = ({"id": "B-009", "severity": "BLOCKING", "disposition": "OPEN",
                     "statement": "La reprise ne couvre pas le cas X."},)
        return self.cycle((_DOC,), (fakes.review("ACCEPTER", findings=blocking),))

    def timed_out(self) -> Path:
        collab = self.build(a=(_DOC,), b=())
        self.a.sleep_seconds = 5.0
        workflow.run(collab, adapters=self.adapters, timeout_seconds=0.05)
        return collab

    def not_launched(self) -> Path:
        collab = self.build(a=(_DOC,), b=())
        self.adapters["fake-a"] = self.a = _Absent("fake-a", ())
        self.run_engine(collab)
        return collab

    def contract_error(self) -> Path:
        return self.cycle(("Bonjour, voici mon document.",), ())

    def awaiting(self) -> Path:
        return self.clean()

    def accepted(self) -> Path:
        collab = self.clean()
        self.decide(collab, decisions.ACCEPTED)
        return collab

    def accepted_then_changed(self) -> Path:
        collab = self.accepted()
        delivered = collab / decisions.DELIVERED
        delivered.write_bytes(delivered.read_bytes() + b"\nAjout hors cycle.\n")
        return collab

    def stopped(self) -> Path:
        collab = self.clean()
        self.decide(collab, decisions.STOPPED)
        return collab

    def situation(self, name: str, folder: str | None = None) -> Path:
        """Chaque situation dans son propre dossier : deux collaborations sous la
        même racine partageraient leurs numéros d'échange."""
        self.root = Path(self._tmp.name) / (folder or name)
        self.root.mkdir()
        collab: Path = getattr(self, name)()
        return collab

    def text(self, collab: Path) -> str:
        state = self.state(collab)
        text = decisions.next_action(collab, state)
        if state.current_call is not None:
            text = text.replace(state.current_call.call_id, _CALL)
        return text


_SITUATIONS = (
    "ready_fresh", "ready_paused", "running", "question", "open_blocking", "timed_out",
    "not_launched", "contract_error", "awaiting", "accepted", "accepted_then_changed", "stopped",
)

# Relevé sur `ba5c0a4`, avant le lot 1 : la phrase de chaque situation, identifiant
# d'appel remplacé par `{call}`.
_RETRY = (
    "`resume <dossier> --retry-call <id> --reason-file <fichier>` (nouvel appel payant ; le"
    " fichier dit pourquoi)"
)
_DECIDE = (
    "lire `livrables/bilan.md` puis décider : `decide <dossier> --accept`,"
    " `--accept-with-reserves <texte>`, `--correct <fichier>` ou `--stop`"
)
_GOLDEN: dict[str, str] = {
    "ready_fresh": "lancer `run <dossier>`",
    "ready_paused": "lancer `run <dossier>`",
    "running": (
        "un appel est en cours, ou le processus s'est arrêté en cours d'appel :"
        " `run <dossier>` reprend localement, sans repayer d'appel"
    ),
    "question": (
        "lire la question de A (`echanges/0001-question-A.md`), puis `resume --answer <fichier>`"
        " (complète la demande) ou `decide <dossier> --stop`"
    ),
    "open_blocking": (
        "B a accepté malgré une objection bloquante restée ouverte : lire"
        " `echanges/0002-critique-B.json`, puis `resume --answer <fichier>` pour préciser la"
        " demande ou `decide <dossier> --stop`"
    ),
    "timed_out": (
        "TIMEOUT (appel `{call}`) : l'appel a pu être payé, aucun rejeu automatique. Si vous"
        f" décidez de le relancer : {_RETRY} ; sinon `decide <dossier> --stop`"
    ),
    "not_launched": (
        "LAUNCH_FAILED (appel `{call}`) : rien n'a été payé. Corriger la cause, puis"
        f" {_RETRY} ; sinon `decide <dossier> --stop`"
    ),
    "contract_error": (
        "CONTRACT_ERROR (appel `{call}`) : la réponse brute est conservée dans `appels/`."
        " Gratuit et local : `resume <dossier> --reprocess <id> --reason-file <fichier>` (relit"
        " la réponse conservée, sans appel — utile si la lecture a été corrigée) ;"
        f" ou {_RETRY} ; ou `decide <dossier> --stop`"
    ),
    "awaiting": _DECIDE,
    "accepted": "aucune : le résultat est accepté",
    "accepted_then_changed": _DECIDE,
    "stopped": "aucune : la collaboration a été arrêtée par décision humaine",
}


class TestTheCliTextsDidNotMove(ActionsCase):
    def test_each_situation_keeps_its_sentence(self) -> None:
        for name in _SITUATIONS:
            with self.subTest(name):
                self.assertEqual(self.text(self.situation(name)), _GOLDEN[name])


_S = ActionId
# (actions principales, actions secondaires) attendues, situation par situation.
_EXPECTED: dict[str, tuple[set[ActionId], set[ActionId]]] = {
    "ready_fresh": ({_S.START}, {_S.STOP}),
    "ready_paused": ({_S.RESUME}, {_S.STOP}),
    "running": ({_S.RESUME}, {_S.STOP}),
    "question": ({_S.ANSWER_AND_RESUME, _S.STOP}, set()),
    "open_blocking": ({_S.ANSWER_AND_RESUME, _S.STOP}, set()),
    "timed_out": ({_S.RETRY_CALL, _S.STOP}, set()),
    "not_launched": ({_S.RETRY_CALL, _S.STOP}, set()),
    "contract_error": ({_S.REPROCESS_AND_RESUME, _S.STOP}, {_S.RETRY_CALL}),
    "awaiting": ({_S.ACCEPT, _S.ACCEPT_WITH_RESERVES, _S.CORRECT, _S.STOP}, set()),
    "accepted": (set(), {_S.CORRECT, _S.STOP}),
    "accepted_then_changed": ({_S.ACCEPT, _S.ACCEPT_WITH_RESERVES, _S.CORRECT, _S.STOP}, set()),
    "stopped": (set(), set()),
}

# Ce que la commande peut coûter ne dépend que de l'action, jamais du statut.
_MAY_CALL = {_S.START, _S.RESUME, _S.ANSWER_AND_RESUME, _S.RETRY_CALL,
             _S.REPROCESS_AND_RESUME, _S.CORRECT}

# Marque d'une commande dans la phrase de la CLI → l'action qu'elle déclenche.
_MARKS = {
    "`run <dossier>`": {_S.START, _S.RESUME},
    "--answer": {_S.ANSWER_AND_RESUME},
    "--retry-call": {_S.RETRY_CALL},
    "--reprocess": {_S.REPROCESS_AND_RESUME},
    "--accept`": {_S.ACCEPT},
    "--accept-with-reserves": {_S.ACCEPT_WITH_RESERVES},
    "--correct": {_S.CORRECT},
    "--stop": {_S.STOP},
}


class TestTheStructure(ActionsCase):
    def actions(self, collab: Path) -> tuple[decisions.AllowedAction, ...]:
        return decisions.allowed_actions(collab, self.state(collab))

    def test_each_situation_offers_what_the_design_says(self) -> None:
        for name in _SITUATIONS:
            with self.subTest(name):
                actions = self.actions(self.situation(name))
                primary = {a.id for a in actions if a.primary}
                secondary = {a.id for a in actions if not a.primary}
                self.assertEqual((primary, secondary), _EXPECTED[name])

    def test_what_may_call_a_provider_is_said_and_only_that(self) -> None:
        for name in _SITUATIONS:
            with self.subTest(name):
                for action in self.actions(self.situation(name)):
                    self.assertEqual(action.may_call, action.id in _MAY_CALL, action.id)

    def test_a_local_step_is_told_apart_from_what_follows(self) -> None:
        """§3.5 : écrire une réponse, relire une réponse conservée, reprendre depuis
        les preuves ne paient rien — la **suite** peut payer."""
        for name, local in (("running", _S.RESUME), ("question", _S.ANSWER_AND_RESUME),
                            ("contract_error", _S.REPROCESS_AND_RESUME),
                            ("awaiting", _S.CORRECT)):
            with self.subTest(name):
                action = next(a for a in self.actions(self.situation(name)) if a.id is local)
                self.assertTrue(action.local_step and action.may_call)
        for name, paid in (("timed_out", _S.RETRY_CALL), ("ready_fresh", _S.START)):
            with self.subTest(name):
                action = next(a for a in self.actions(self.situation(name)) if a.id is paid)
                self.assertFalse(action.local_step)

    def test_a_call_action_names_its_call(self) -> None:
        for name in ("timed_out", "not_launched", "contract_error"):
            with self.subTest(name):
                collab = self.situation(name)
                call = self.state(collab).current_call
                assert call is not None
                targeted = [a for a in self.actions(collab)
                            if a.id in (_S.RETRY_CALL, _S.REPROCESS_AND_RESUME)]
                self.assertTrue(targeted)
                self.assertTrue(all(a.call_id == call.call_id for a in targeted))

    def test_the_cli_sentence_names_every_offered_action_and_nothing_else(self) -> None:
        for name in _SITUATIONS:
            with self.subTest(name):
                collab = self.situation(name)
                actions = self.actions(collab)
                allowed = {a.id for a in actions}
                text = self.text(collab)
                for mark, ids in _MARKS.items():
                    if mark in text:
                        self.assertTrue(ids & allowed, f"{mark} nommé sans être permis")
                for action in actions:
                    if action.primary:
                        marks = [m for m, ids in _MARKS.items() if action.id in ids]
                        self.assertTrue(any(m in text for m in marks), action.id)


class TestTheEngineAgrees(ActionsCase):
    """Une action absente de la table est refusée par le moteur ; une action
    présente, pour les décisions sans appel, est acceptée."""

    def reason(self) -> Path:
        path = self.root / "motif.md"
        path.write_text("Parce que.", encoding="utf-8")
        return path

    def attempt(self, collab: Path, action: ActionId) -> bool:
        state = self.state(collab)
        call_id = "inexistant" if state.current_call is None else state.current_call.call_id
        intervention: workflow.Intervention
        try:
            if action is _S.ACCEPT:
                self.decide(collab, decisions.ACCEPTED)
            elif action is _S.ACCEPT_WITH_RESERVES:
                self.decide(collab, decisions.ACCEPTED_WITH_RESERVES, reserves="R.")
            elif action is _S.STOP:
                self.decide(collab, decisions.STOPPED)
            else:
                if action is _S.RETRY_CALL:
                    intervention = workflow.RetryCall(call_id, self.reason())
                elif action is _S.REPROCESS_AND_RESUME:
                    intervention = workflow.Reprocess(call_id, self.reason())
                else:
                    intervention = workflow.Answer(self.reason())
                self.run_engine(collab, intervention=intervention)
        except workflow.WorkflowError:
            return False
        return True

    def test_decisions_without_a_call_follow_the_table(self) -> None:
        for name in _SITUATIONS:
            for action in (_S.ACCEPT, _S.ACCEPT_WITH_RESERVES, _S.STOP):
                with self.subTest(name, action=action.value):
                    collab = self.situation(name, f"{name}-{action.value}")
                    offered = action in {a.id for a in decisions.allowed_actions(
                        collab, self.state(collab))}
                    self.assertEqual(self.attempt(collab, action), offered)

    def test_interventions_absent_from_the_table_are_refused(self) -> None:
        for name in _SITUATIONS:
            for action in (_S.RETRY_CALL, _S.REPROCESS_AND_RESUME, _S.ANSWER_AND_RESUME):
                with self.subTest(name, action=action.value):
                    collab = self.situation(name, f"{name}-{action.value}")
                    offered = action in {a.id for a in decisions.allowed_actions(
                        collab, self.state(collab))}
                    if not offered:
                        self.assertFalse(self.attempt(collab, action))

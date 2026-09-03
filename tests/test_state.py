"""Tests de iabinome.models : schéma strict, enums fermés, aller-retour JSON."""

import unittest

from iabinome.models import (
    SCHEMA_VERSION,
    AgentSpec,
    CallState,
    CallStatus,
    Configuration,
    Decision,
    MissionKind,
    Phase,
    ReviewerAccess,
    Role,
    SchemaError,
    State,
    Status,
)

_AGENT = {"adapter_id": "claude", "model": "opus-5"}

_CONFIG = {
    "schema_version": 1,
    "collaboration_id": "etude-cache",
    "mission_kind": "RECHERCHE",
    "reviewer_access": "CONSULT",
    "max_revisions": 2,
    "agent_a": _AGENT,
    "agent_b": {"adapter_id": "codex", "model": "gpt"},
    "initial_demande_sha256": "a" * 64,
    "corpus_manifest_sha256": "b" * 64,
    "created_at": "2026-09-03T10:00:00Z",
}

_CALL = {
    "call_id": "c1",
    "sequence": 1,
    "role": "A",
    "phase": "PROPOSAL_A",
    "status": "CALLING",
    "call_dir": "appels/0001-A-c1",
    "prompt_sha256": "d" * 64,
    "response_sha256": None,
    "started_at": "2026-09-03T10:00:00Z",
    "completed_at": None,
}

_STATE = {
    "schema_version": 1,
    "status": "READY",
    "phase": "PROPOSAL_A",
    "revision": 0,
    "demande_sha256": "e" * 64,
    "current_document": None,
    "latest_review": None,
    "open_finding_ids": [],
    "current_call": None,
    "last_incident": None,
    "updated_at": "2026-09-03T10:00:00Z",
}


class TestAgentSpec(unittest.TestCase):
    def test_round_trip(self) -> None:
        spec = AgentSpec.from_dict(_AGENT)
        self.assertEqual(spec.to_dict(), _AGENT)

    def test_missing_key(self) -> None:
        with self.assertRaises(SchemaError):
            AgentSpec.from_dict({"adapter_id": "claude"})

    def test_extra_key(self) -> None:
        with self.assertRaises(SchemaError):
            AgentSpec.from_dict({**_AGENT, "surnumeraire": "x"})


class TestCallState(unittest.TestCase):
    def test_round_trip(self) -> None:
        call = CallState.from_dict(_CALL)
        self.assertEqual(call.role, Role.A)
        self.assertEqual(call.status, CallStatus.CALLING)
        self.assertIsNone(call.response_sha256)
        self.assertEqual(call.to_dict(), _CALL)

    def test_unknown_enum_value(self) -> None:
        with self.assertRaises(SchemaError):
            CallState.from_dict({**_CALL, "status": "INCONNU"})

    def test_null_not_allowed_for_required_string(self) -> None:
        with self.assertRaises(SchemaError):
            CallState.from_dict({**_CALL, "call_id": None})


class TestConfiguration(unittest.TestCase):
    def test_round_trip(self) -> None:
        config = Configuration.from_dict(_CONFIG)
        self.assertEqual(config.mission_kind, MissionKind.RECHERCHE)
        self.assertEqual(config.reviewer_access, ReviewerAccess.CONSULT)
        self.assertEqual(config.agent_a, AgentSpec("claude", "opus-5"))
        self.assertEqual(config.to_dict(), _CONFIG)

    def test_corpus_manifest_sha256_nullable(self) -> None:
        config = Configuration.from_dict({**_CONFIG, "corpus_manifest_sha256": None})
        self.assertIsNone(config.corpus_manifest_sha256)

    def test_missing_key_refused(self) -> None:
        incomplete = dict(_CONFIG)
        del incomplete["created_at"]
        with self.assertRaises(SchemaError):
            Configuration.from_dict(incomplete)

    def test_extra_key_refused(self) -> None:
        with self.assertRaises(SchemaError):
            Configuration.from_dict({**_CONFIG, "surnumeraire": "x"})

    def test_future_schema_version_refused(self) -> None:
        with self.assertRaises(SchemaError):
            Configuration.from_dict({**_CONFIG, "schema_version": SCHEMA_VERSION + 1})

    def test_past_schema_version_refused(self) -> None:
        with self.assertRaises(SchemaError):
            Configuration.from_dict({**_CONFIG, "schema_version": 0})

    def test_unknown_mission_kind_refused(self) -> None:
        with self.assertRaises(SchemaError):
            Configuration.from_dict({**_CONFIG, "mission_kind": "AUTRE"})

    def test_unknown_reviewer_access_refused(self) -> None:
        with self.assertRaises(SchemaError):
            Configuration.from_dict({**_CONFIG, "reviewer_access": "AUTRE"})


class TestState(unittest.TestCase):
    def test_round_trip_ready(self) -> None:
        state = State.from_dict(_STATE)
        self.assertEqual(state.status, Status.READY)
        self.assertIsNone(state.current_call)
        self.assertEqual(state.to_dict(), _STATE)

    def test_round_trip_with_current_call(self) -> None:
        data = {**_STATE, "status": "RUNNING", "current_call": _CALL}
        state = State.from_dict(data)
        assert state.current_call is not None
        self.assertEqual(state.current_call.call_id, "c1")
        self.assertEqual(state.to_dict(), data)

    def test_current_call_key_must_be_present(self) -> None:
        incomplete = dict(_STATE)
        del incomplete["current_call"]
        with self.assertRaises(SchemaError):
            State.from_dict(incomplete)

    def test_current_call_wrong_type_refused(self) -> None:
        with self.assertRaises(SchemaError):
            State.from_dict({**_STATE, "current_call": "pas-un-objet"})

    def test_every_phase_accepted(self) -> None:
        for phase in Phase:
            state = State.from_dict({**_STATE, "phase": phase.value})
            self.assertEqual(state.phase, phase)

    def test_every_status_accepted(self) -> None:
        for status in Status:
            state = State.from_dict({**_STATE, "status": status.value})
            self.assertEqual(state.status, status)

    def test_terminal_awaiting_approval(self) -> None:
        data = {**_STATE, "status": "AWAITING_APPROVAL", "phase": "CLOSED"}
        state = State.from_dict(data)
        self.assertEqual(state.status, Status.AWAITING_APPROVAL)
        self.assertEqual(state.phase, Phase.CLOSED)
        self.assertEqual(state.to_dict(), data)

    def test_open_finding_ids_default_empty_list(self) -> None:
        state = State.from_dict(_STATE)
        self.assertEqual(state.open_finding_ids, [])

    def test_open_finding_ids_must_be_strings(self) -> None:
        with self.assertRaises(SchemaError):
            State.from_dict({**_STATE, "open_finding_ids": [1, 2]})

    def test_demande_sha256_tracked_verbatim(self) -> None:
        state = State.from_dict({**_STATE, "demande_sha256": "f" * 64})
        self.assertEqual(state.demande_sha256, "f" * 64)

    def test_unknown_decision_enum_rejected_directly(self) -> None:
        with self.assertRaises(ValueError):
            Decision("AUTRE")


if __name__ == "__main__":
    unittest.main()

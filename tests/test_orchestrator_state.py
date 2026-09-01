#!/usr/bin/env python3
"""Exploit/control checks for the lane-orchestrator state layer.

The checks drive the real ledger and wrapper against temporary artifacts.  An
exploit names the unsafe transition the contract forbids; its neighbouring
control preserves the legitimate path.  State is loaded by path so this file
does not depend on the skill directory being on ``sys.path``.
"""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


CATALOGUE = Path(__file__).resolve().parent.parent
STATE_PATH = CATALOGUE / "skills" / "lane-orchestration" / "orchestrator_state.py"
WRAPPER_PATH = CATALOGUE / "skills" / "lane-orchestration" / "dispatch_wrapper.py"
SCHEMA_PATH = CATALOGUE / "skills" / "lane-orchestration" / "run-plan.schema.json"
SAMPLE_PATH = CATALOGUE / "skills" / "lane-orchestration" / "samples" / "run-plan.sample.json"


def load_by_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OrchestratorStateCheck(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="orchestrator-state-check-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.plan_path = self.root / "run-plan.json"
        self.ledger = self.root / "2026-09-01-deadbeef"
        self.plan_path.write_text(json.dumps(self.plan(), indent=2) + "\n")
        self.state = load_by_path("orchestrator_state_under_test", STATE_PATH)

    def plan(self, lanes=None):
        return {
            "date": "2026-09-01",
            "mode": "unattended",
            "budget": {
                "codex_weekly_pct_ceiling": 50,
                "codex_5h_pct_ceiling": 50,
                "claude_usd_ceiling": 40,
                "per_lane_usd_ceiling": 20,
            },
            "lanes": lanes if lanes is not None else [
                {
                    "id": "foundation",
                    "kind": "repo",
                    "repo": str(self.root / "repo"),
                    "worktree": str(self.root / "worktrees" / "foundation"),
                    "branch": "lane/foundation",
                    "base": "0" * 40,
                    "brief": "brief-foundation.md",
                    "depends_on": [],
                    "claims": ["src/foundation"],
                    "client_visible": False,
                    "direction_gate": "no",
                },
                {
                    "id": "finish",
                    "kind": "deliverable",
                    "repo": str(self.root / "repo"),
                    "worktree": str(self.root / "worktrees" / "finish"),
                    "branch": "lane/finish",
                    "base": "0" * 40,
                    "brief": "brief-finish.md",
                    "depends_on": ["foundation"],
                    "claims": ["docs/finish"],
                    "client_visible": True,
                    "direction_gate": "yes",
                },
            ],
        }

    def open(self):
        self.state.open_run(self.plan_path, self.ledger)

    def append(self, event, **kwargs):
        return self.state.append_event(self.ledger, event, **kwargs)

    def snap(self):
        return self.state.rebuild(self.ledger)

    def test_control_open_and_sample_plan_validate(self):
        sample = json.loads(SAMPLE_PATH.read_text())
        self.state.validate_run_plan(sample)
        self.open()
        snap = self.snap()
        self.assertEqual(snap["run_plan"]["mode"], "unattended")
        self.assertEqual(snap["dispatchable"], ["foundation"])

    def test_exploit_torn_final_line_is_truncated_before_append(self):
        self.open()
        self.append({"e": "gate:evaluated", "gate": "g1", "lane": None,
                     "verdict": "pass", "mechanism": "test"})
        event_path = Path(self.state.events_path(self.ledger))
        event_path.write_bytes(event_path.read_bytes() + b'{"e":"lane:completed"')
        self.append({"e": "budget:sampled", "windows": {}})
        raw = event_path.read_bytes()
        self.assertNotIn(b'{"e":"lane:completed"', raw)
        self.assertEqual(self.snap()["last_seq"], 3)

    def test_control_parseable_unterminated_line_is_completed(self):
        self.open()
        event_path = Path(self.state.events_path(self.ledger))
        event = {"e": "gate:evaluated", "gate": "g1", "lane": None,
                 "verdict": "pass", "mechanism": "test", "schema_version": 1,
                 "seq": 2, "t": "2026-09-01T00:00:00Z"}
        event_path.write_bytes(event_path.read_bytes() + json.dumps(event).encode("utf-8"))
        self.append({"e": "budget:sampled", "windows": {}})
        self.assertTrue(event_path.read_bytes().endswith(b"\n"))
        self.assertEqual(self.snap()["gates"][0]["id"], "g1")

    def test_exploit_refused_event_leaves_log_untouched(self):
        self.open()
        event_path = Path(self.state.events_path(self.ledger))
        before = event_path.read_bytes()
        with self.assertRaises(self.state.ReducerInvariantError):
            self.append({"e": "lane:completed", "lane": "foundation"})
        self.assertEqual(event_path.read_bytes(), before)

    def test_control_live_holder_refuses_and_dead_holder_unlocks(self):
        self.open()
        with self.state.acquire_lock(self.ledger):
            with self.assertRaises(self.state.RunLocked) as raised:
                self.state.acquire_lock(self.ledger)
            self.assertTrue(raised.exception.holder_alive)
        Path(self.state.lock_path(self.ledger)).write_text(json.dumps({
            "pid": 98765432, "acquired_at": "now", "token": "dead"
        }))
        removed = self.state.break_lock(self.ledger)
        self.assertEqual(removed["pid"], 98765432)

    def test_exploit_unlock_has_no_force_escape_for_unknown_holder(self):
        self.open()
        Path(self.state.lock_path(self.ledger)).write_text(json.dumps({
            "pid": "unknown", "acquired_at": "now"
        }))
        with self.assertRaises(self.state.RunLocked):
            self.state.break_lock(self.ledger)
        self.assertTrue(Path(self.state.lock_path(self.ledger)).exists())

    def test_control_rebuild_is_deterministic_and_stale_snapshot_rebuilds(self):
        self.open()
        self.append({"e": "budget:sampled", "windows": {"weekly": {}}})
        first = self.snap()
        second = self.state.rebuild(self.ledger)
        self.assertEqual(first, second)
        self.state.atomic_write_snapshot(self.ledger, first)
        self.append({"e": "gate:evaluated", "gate": "g1", "lane": None,
                     "verdict": "pass", "mechanism": "test"})
        loaded = self.state.load_snapshot(self.ledger)
        self.assertEqual(loaded, self.state.rebuild(self.ledger))
        self.assertEqual(loaded["last_seq"], 3)

    def test_exploit_unpark_requires_prior_park(self):
        self.open()
        with self.assertRaises(self.state.ReducerInvariantError):
            self.append({"e": "lane:unparked", "lane": "foundation",
                         "answer_text": "answer", "record_sha": "a" * 64})

    def test_control_park_unpark_re_evaluates_dependents(self):
        self.open()
        record = self.root / "PARKED-foundation.md"
        record.write_text("# parked\n\n## Answer:\nship it\n")
        self.append({"e": "lane:parked", "lane": "foundation", "gate": "g1",
                     "record_path": str(record), "lane_last_seq": 1})
        snap = self.state.unpark(self.ledger, "foundation", "ship it", record)
        self.assertIn("foundation", snap["dispatchable"])
        self.append({"e": "lane:completed", "lane": "foundation", "lane_last_seq": snap["last_seq"]})
        self.assertIn("finish", self.snap()["dispatchable"])
        self.assertEqual(self.snap()["lanes"]["foundation"]["unparks"][0]["record_sha"],
                         hashlib.sha256(record.read_bytes()).hexdigest())

    def test_exploit_pending_receipt_without_spawning_is_safe_not_replanned(self):
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        result = self.state.reconcile(self.ledger, process_pids=lambda _op: [])
        self.assertEqual(result, [{"op_id": op_id, "state": "safe_to_replan"}])
        self.assertEqual(self.snap()["receipts"][op_id]["phase"], "pending")

    def test_control_spawning_without_marker_is_affirmative_negative(self):
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        self.state.mark_spawning(self.ledger, op_id)
        result = self.state.reconcile(self.ledger, process_pids=lambda _op: [])
        self.assertEqual(result[0]["state"], "negative")
        self.assertEqual(self.snap()["receipts"][op_id]["outcome"], "failed")

    def test_exploit_started_without_envelope_parks_never_replans(self):
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        self.state.mark_spawning(self.ledger, op_id)
        self.state.mark_launched(self.ledger, op_id, 98765432, "detached fake")
        marker = Path(self.snap()["receipts"][op_id]["marker"])
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("started\n")
        result = self.state.reconcile(self.ledger, process_pids=lambda _op: [])
        self.assertEqual(result[0]["state"], "PARK")
        self.assertEqual(self.snap()["lanes"]["foundation"]["status"], "parked")
        self.assertEqual(self.state.reconcile(self.ledger, process_pids=lambda _op: []), [])

    def test_exploit_unavailable_process_table_is_not_an_affirmative_negative(self):
        # macOS has no /proc: an UNAVAILABLE table (None) must not read as
        # "nothing runs" — a fresh spawning receipt waits within the grace
        # instead of being settled failed while its wrapper may be live.
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        self.state.mark_spawning(self.ledger, op_id)
        result = self.state.reconcile(self.ledger, process_pids=lambda _op: None)
        self.assertEqual(result[0]["state"], "waiting")
        self.assertEqual(self.snap()["receipts"][op_id]["phase"], "spawning")

    def test_control_unavailable_table_uses_pid_liveness_for_launched(self):
        # A launched receipt carries a pid; with no process table the engine
        # falls back to spawn-free pid liveness and adopts a live process.
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        self.state.mark_spawning(self.ledger, op_id)
        self.state.mark_launched(self.ledger, op_id, os.getpid(), "detached fake")
        result = self.state.reconcile(self.ledger, process_pids=lambda _op: None)
        self.assertEqual(result[0]["state"], "adopted")
        self.assertEqual(result[0]["pid"], os.getpid())
        self.assertEqual(self.snap()["receipts"][op_id]["phase"], "launched")

    def test_exploit_parked_lane_cannot_receive_a_silent_redispatch(self):
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        self.state.mark_spawning(self.ledger, op_id)
        self.state.mark_launched(self.ledger, op_id, 98765432, "detached fake")
        marker = Path(self.snap()["receipts"][op_id]["marker"])
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("started\n")
        self.state.reconcile(self.ledger, process_pids=lambda _op: [])
        with self.assertRaises(self.state.ReducerInvariantError):
            self.state.create_receipt(self.ledger, "foundation", "retry", self.snap()["last_seq"])

    def test_control_real_claude_envelope_settles_complete_with_cost(self):
        # b2r1-F001: real `claude -p` envelopes carry is_error, not status.
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        self.state.mark_spawning(self.ledger, op_id)
        self.state.mark_launched(self.ledger, op_id, 98765432, "detached fake")
        envelope = Path(self.snap()["receipts"][op_id]["oracle"])
        envelope.parent.mkdir(parents=True, exist_ok=True)
        envelope.write_text(json.dumps({
            "is_error": False, "subtype": "success", "terminal_reason": "completed",
            "total_cost_usd": 0.42, "modelUsage": {"claude-sonnet-5": {}},
            "session_id": "real", "permission_denials": [],
        }))
        result = self.state.reconcile(self.ledger, process_pids=lambda _op: [])
        self.assertEqual(result[0]["state"], "settled")
        self.assertEqual(result[0]["outcome"], "complete")
        leg = self.snap()["claude_legs"][op_id]
        self.assertEqual(leg["cost_usd"], 0.42)
        self.assertEqual(leg["models"], ["claude-sonnet-5"])

    def test_exploit_unknown_envelope_outcome_parks_not_resolves(self):
        # b2r1-F002a: a parseable envelope with an unrecognized outcome must
        # park the lane, not read as quietly resolved.
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        self.state.mark_spawning(self.ledger, op_id)
        self.state.mark_launched(self.ledger, op_id, 98765432, "detached fake")
        envelope = Path(self.snap()["receipts"][op_id]["oracle"])
        envelope.parent.mkdir(parents=True, exist_ok=True)
        envelope.write_text(json.dumps({"weird": "shape"}))
        result = self.state.reconcile(self.ledger, process_pids=lambda _op: [])
        self.assertEqual(result[0]["state"], "PARK")
        self.assertEqual(self.snap()["lanes"]["foundation"]["status"], "parked")

    def test_exploit_done_unknown_without_park_is_repaired(self):
        # b2r1-F002b: a crash between an unknown settle and its park must not
        # leave a resolved-looking receipt; reconcile repairs the park.
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        self.state.settle(self.ledger, op_id, outcome="unknown")
        self.assertEqual(self.snap()["receipts"][op_id]["phase"], "done")
        self.assertNotEqual(self.snap()["lanes"]["foundation"]["status"], "parked")
        result = self.state.reconcile(self.ledger, process_pids=lambda _op: [])
        self.assertEqual(result[0]["state"], "PARK")
        self.assertEqual(self.snap()["lanes"]["foundation"]["status"], "parked")

    def test_exploit_dead_codex_attempt_parks_never_negative(self):
        # b2r1-F003: the runner writes no marker, so marker absence proves
        # nothing for a codex receipt — unknown, park, never "never spawned".
        self.open()
        op_id = self.state.create_receipt(
            self.ledger, "foundation", "qa-review", 1, provider="codex"
        )
        self.state.mark_spawning(self.ledger, op_id)
        self.state.mark_launched(self.ledger, op_id, 98765432, "detached fake")
        result = self.state.reconcile(self.ledger, process_pids=lambda _op: [])
        self.assertEqual(result[0]["state"], "PARK")
        self.assertEqual(self.snap()["receipts"][op_id]["outcome"], "unknown")

    def test_control_live_codex_pid_is_adopted_despite_empty_argv_scan(self):
        # b2r1-F003: codex carries its id in the environment, not argv — an
        # empty argv scan must still consult the recorded pid.
        self.open()
        op_id = self.state.create_receipt(
            self.ledger, "foundation", "qa-review", 1, provider="codex"
        )
        self.state.mark_spawning(self.ledger, op_id)
        self.state.mark_launched(self.ledger, op_id, os.getpid(), "detached fake")
        result = self.state.reconcile(self.ledger, process_pids=lambda _op: [])
        self.assertEqual(result[0]["state"], "adopted")
        self.assertEqual(self.snap()["receipts"][op_id]["phase"], "launched")

    def test_exploit_oracle_not_embedding_op_id_is_refused(self):
        # b2r1-F004: attempt-uniqueness is structural — an oracle pointing at
        # another attempt's artifact is refused at append.
        self.open()
        with self.assertRaises(self.state.ReducerInvariantError):
            self.append({
                "e": "lane:dispatched", "op_id": "fresh-op", "lane": "foundation",
                "stage": "build", "provider": "claude",
                "oracle": str(self.root / "old-attempt.envelope.json"),
                "lane_last_seq": 1,
            })

    def test_exploit_settle_outcome_cannot_contradict_the_envelope(self):
        # b2r1-F004: an explicit outcome may only downgrade to unknown, never
        # overrule what the oracle envelope says.
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        envelope = Path(self.snap()["receipts"][op_id]["oracle"])
        envelope.parent.mkdir(parents=True, exist_ok=True)
        envelope.write_text(json.dumps({"is_error": True, "total_cost_usd": 0.1}))
        with self.assertRaises(self.state.OrchestratorStateError):
            self.state.settle(self.ledger, op_id, outcome="complete")

    def test_exploit_open_event_cannot_substitute_lane_content(self):
        # b2r1-F005: a truthful sha beside substituted scheduling state must
        # be refused — the event's lanes/mode must BE the hashed file's.
        substituted = self.plan()["lanes"]
        substituted[0]["branch"] = "lane/evil"
        with self.assertRaises(self.state.OrchestratorStateError):
            self.state.append_event(self.ledger, {
                "e": "orch:run:opened",
                "run_plan_path": str(self.plan_path),
                "run_plan_sha": self.state.compute_run_plan_sha(self.plan_path),
                "mode": "unattended",
                "date": "2026-09-01",
                "lanes": substituted,
            }, run_plan_path=self.plan_path)

    def test_control_never_spawned_leg_is_known_zero_not_unknown(self):
        # b2r1-F007: an affirmative negative is provably zero spend — it must
        # not fail budget gates forever as an unknown leg.
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        self.state.mark_spawning(self.ledger, op_id)
        self.state.reconcile(self.ledger, process_pids=lambda _op: [])
        leg = self.snap()["claude_legs"][op_id]
        self.assertEqual(leg["cost_usd"], 0.0)
        self.assertEqual(leg["outcome"], "failed")

    def test_exploit_schema_requires_hex_sha_base(self):
        # b2r1-F008: base is a 40-hex sha, not any string.
        schema = json.loads(SCHEMA_PATH.read_text())
        candidate = self.plan()
        candidate["lanes"][0]["base"] = "main"
        with self.assertRaises(self.state.OrchestratorStateError):
            self.state.validate(candidate, schema)

    def test_exploit_duplicate_claude_leg_is_refused(self):
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        receipt = self.snap()["receipts"][op_id]
        envelope = Path(receipt["oracle"])
        envelope.parent.mkdir(parents=True, exist_ok=True)
        envelope.write_text(json.dumps({"status": "complete", "total_cost_usd": 1.25,
                                        "modelUsage": {"claude-sonnet": {}}, "session_id": "s1"}))
        self.state.settle(self.ledger, op_id)
        before = Path(self.state.events_path(self.ledger)).read_bytes()
        with self.assertRaises(self.state.OrchestratorStateError):
            self.append({"e": "claude:leg", "op_id": op_id, "lane": "foundation",
                         "cost_usd": 1.25, "models": [], "session_id": "s1"})
        self.assertEqual(Path(self.state.events_path(self.ledger)).read_bytes(), before)

    def test_control_settle_is_idempotent_leg_then_crash_and_before_leg(self):
        self.open()
        first = self.state.create_receipt(self.ledger, "foundation", "first", 1)
        first_receipt = self.snap()["receipts"][first]
        first_envelope = Path(first_receipt["oracle"])
        first_envelope.parent.mkdir(parents=True, exist_ok=True)
        first_envelope.write_text(json.dumps({"status": "complete", "total_cost_usd": 2.5,
                                              "session_id": "first"}))
        self.state.append_event(self.ledger, {
            "e": "claude:leg", "op_id": first, "lane": "foundation",
            "cost_usd": 2.5, "models": [], "session_id": "first",
        }, internal=True)
        self.state.settle(self.ledger, first)
        self.state.settle(self.ledger, first)
        self.assertEqual(len(self.snap()["claude_legs"]), 1)
        self.assertEqual(self.snap()["receipts"][first]["phase"], "done")

        second = self.state.create_receipt(self.ledger, "foundation", "second", 1)
        second_receipt = self.snap()["receipts"][second]
        second_envelope = Path(second_receipt["oracle"])
        second_envelope.parent.mkdir(parents=True, exist_ok=True)
        second_envelope.write_text(json.dumps({"status": "complete", "total_cost_usd": 3.0}))
        self.state.settle(self.ledger, second)
        self.state.settle(self.ledger, second)
        self.assertEqual(len(self.snap()["claude_legs"]), 2)
        self.assertEqual(self.snap()["receipts"][second]["phase"], "done")

    def test_exploit_receipt_cannot_be_done_without_its_leg(self):
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        with self.assertRaises(self.state.ReducerInvariantError):
            self.append({"e": "lane:settled", "op_id": op_id,
                         "outcome": "complete", "envelope": None})

    def test_control_unknown_settle_records_a_null_leg(self):
        self.open()
        op_id = self.state.create_receipt(self.ledger, "foundation", "build", 1)
        self.state.settle(self.ledger, op_id, outcome="unknown")
        leg = self.snap()["claude_legs"][op_id]
        self.assertIsNone(leg["cost_usd"])
        self.assertEqual(leg["outcome"], "unknown")

    def test_exploit_mismatched_run_plan_sha_is_refused(self):
        self.open()
        before = Path(self.state.events_path(self.ledger)).read_bytes()
        other = self.root / "other-plan.json"
        other.write_text(json.dumps(self.plan(), indent=2) + "\nchanged\n")
        with self.assertRaises(self.state.OrchestratorStateError):
            self.append({"e": "budget:sampled", "windows": {}}, run_plan_path=other)
        self.assertEqual(Path(self.state.events_path(self.ledger)).read_bytes(), before)

    def test_control_matching_run_plan_identity_is_accepted(self):
        self.open()
        self.append({"e": "budget:sampled", "windows": {}}, run_plan_path=self.plan_path)
        self.assertEqual(self.snap()["last_seq"], 2)

    def test_exploit_run_plan_schema_requires_every_budget_field_and_mode(self):
        schema = json.loads(SCHEMA_PATH.read_text())
        valid = self.plan()
        for key in valid["budget"]:
            candidate = json.loads(json.dumps(valid))
            del candidate["budget"][key]
            with self.subTest(missing=key):
                with self.assertRaises(self.state.OrchestratorStateError):
                    self.state.validate(candidate, schema)
        candidate = json.loads(json.dumps(valid))
        del candidate["mode"]
        with self.assertRaises(self.state.OrchestratorStateError):
            self.state.validate(candidate, schema)

    def test_exploit_schema_unknown_key_and_duplicate_lane_id_are_invalid(self):
        schema = json.loads(SCHEMA_PATH.read_text())
        candidate = self.plan()
        candidate["unexpected"] = True
        with self.assertRaises(self.state.OrchestratorStateError):
            self.state.validate(candidate, schema)
        duplicate = self.plan()
        duplicate["lanes"][1]["id"] = duplicate["lanes"][0]["id"]
        with self.assertRaises(self.state.OrchestratorStateError):
            self.state.validate(duplicate, schema)

    def test_control_dispatch_wrapper_fsyncs_marker_for_child_and_copies_stdout(self):
        marker = self.root / "attempt.started"
        envelope = self.root / "attempt.envelope.json"
        child = (
            "import os,sys; "
            "assert os.path.exists(sys.argv[1]); "
            "print('child-envelope-output')"
        )
        result = subprocess.run([
            sys.executable, str(WRAPPER_PATH), "--op-id", "wrapper-control",
            "--marker", str(marker), "--envelope", str(envelope), "--",
            sys.executable, "-c", child, str(marker),
        ], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(marker.exists())
        self.assertIn("child-envelope-output", envelope.read_text())

    def test_exploit_wrapper_exit_code_and_op_id_are_observable_while_child_runs(self):
        op_id = "wrapper-visible-0123456789abcdef"
        marker = self.root / "visible.started"
        envelope = self.root / "visible.envelope"
        child = "import time; time.sleep(1.2)"
        process = subprocess.Popen([
            sys.executable, str(WRAPPER_PATH), "--op-id", op_id,
            "--marker", str(marker), "--envelope", str(envelope), "--",
            sys.executable, "-c", child,
        ])
        try:
            observed = ""
            deadline = time.time() + 1.0
            while time.time() < deadline:
                try:
                    observed = subprocess.check_output(
                        ["ps", "-p", str(process.pid), "-o", "command"], text=True
                    )
                except (OSError, subprocess.CalledProcessError) as exc:
                    if isinstance(exc, PermissionError):
                        self.skipTest("sandbox does not permit the ps process-table probe")
                if op_id in observed:
                    break
                time.sleep(0.02)
            self.assertIn(op_id, observed)
            self.assertEqual(process.wait(), 0)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


if __name__ == "__main__":
    unittest.main()

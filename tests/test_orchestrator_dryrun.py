#!/usr/bin/env python3
"""Exploit/control checks for the lane-orchestrator dry-run surface.

These tests import the executable by path and construct only temporary plans
and ledgers.  The exploit cases exercise unsafe shortcuts—graph cycles,
collisions, forged attribution, blank park answers, and process creation—while
the controls prove that the valid sample, attended approval gaps, and durable
unpark transition still work.
"""

import hashlib
import contextlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent.parent
ORCHESTRATE_PATH = ROOT / "skills" / "lane-orchestration" / "orchestrate.py"
STATE_PATH = ROOT / "skills" / "lane-orchestration" / "orchestrator_state.py"
SAMPLE_PATH = ROOT / "skills" / "lane-orchestration" / "samples" / "run-plan.sample.json"
MAP_PATH = ROOT / "skills" / "lane-orchestration" / "reference" / "gate-map.json"
CENSUS_PATH = ROOT / "docs" / "2026-09-01-orchestration-evidence" / "clodex-gate-census.md"


def load_by_path(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OrchestratorDryRunCheck(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="orchestrator-dryrun-check-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self._orchestrate = None
        self.state = load_by_path("orchestrator_state_for_dryrun_test", STATE_PATH)
        self.plan = json.loads(SAMPLE_PATH.read_text())
        self.plan_path = self.root / "run-plan.json"
        self.write_plan(self.plan)

    @property
    def orchestrate(self):
        if self._orchestrate is None:
            self._orchestrate = load_by_path("orchestrate_under_test", ORCHESTRATE_PATH)
        return self._orchestrate

    def write_plan(self, plan):
        self.plan_path.write_text(json.dumps(plan, indent=2) + "\n")

    def clone_plan(self):
        return json.loads(json.dumps(self.plan))

    def test_control_sample_prints_complete_dry_run_and_never_writes(self):
        ledger = self.root / "ledger"
        with mock.patch.object(self.orchestrate.orchestrator_state, "open_run", side_effect=AssertionError("dry-run opened ledger")):
            with mock.patch.object(self.orchestrate.orchestrator_state, "append_event", side_effect=AssertionError("dry-run appended")):
                with mock.patch("sys.stdout") as stdout:
                    self.assertEqual(self.orchestrate.main([str(SAMPLE_PATH), "--ledger-dir", str(ledger)]), 0)
        output = "".join(call.args[0] for call in stdout.write.call_args_list if call.args)
        self.assertIn("DRY RUN — dispatched nothing", output)
        self.assertRegex(output, r"stage-table@[0-9a-f]{8}")
        self.assertIn("run-plan.json@", output)
        self.assertIn("SKIPPED (dry-run — live mode enforces)", output)
        self.assertIn("claude -p --permission-mode dontAsk", output)
        self.assertIn("/clodex docs/briefs/foundation.md", output)
        self.assertIn("/clodex-build, run dir", output)
        self.assertIn("/clodex-verify, run dir", output)
        self.assertIn("morning-summary: wrapper argv:", output)
        self.assertIn("client-artifact: wrapper argv:", output)
        self.assertNotIn("morning-summary: exact claude argv:", output)
        self.assertIn("CODEX_MODEL=gpt-5.6-terra", output)
        self.assertIn("CODEX_EFFORT=high", output)
        self.assertIn("CODEX_MODEL=gpt-5.6-sol", output)
        self.assertIn("CLODEX_INVOCATION_ID=<op_id minted at dispatch>", output)
        self.assertIn("live mode writes the rendered prompt to the ledger before dispatch", output)
        self.assertIn("lane=finish branch=lane/finish", output)
        self.assertIn("diff_path=/tmp/synthetic-lane-repo-worktrees/finish/<release-diff>", output)
        self.assertIn("GUARANTEED PARK: client-artifact (clodex-verify L385)", output)
        foundation = output.split("\nLANE foundation\n", 1)[1].split("\nLANE finish\n", 1)[0]
        finish = output.split("\nLANE finish\n", 1)[1]
        self.assertNotIn("PREDICTED PARK: client-artifact", foundation)
        self.assertNotIn("PREDICTED PARK:", finish)
        self.assertIn("GUARANTEED PARK: client-artifact", finish)
        self.assertFalse(ledger.exists())

    def test_exploit_dependency_cycle_is_refused(self):
        plan = self.clone_plan()
        plan["lanes"][0]["depends_on"] = ["finish"]
        plan["lanes"][1]["depends_on"] = ["foundation"]
        with self.assertRaises(self.orchestrate.PlanRefusal) as raised:
            self.orchestrate.validate_semantic_graph(plan)
        self.assertIn("dependency cycle", str(raised.exception))

    def test_control_valid_graph_is_topologically_ordered(self):
        ordered = self.orchestrate.validate_semantic_graph(self.plan)
        self.assertEqual([lane["id"] for lane in ordered], ["foundation", "finish"])

    def test_exploit_worktree_collision_is_refused(self):
        plan = self.clone_plan()
        plan["lanes"][1]["worktree"] = plan["lanes"][0]["worktree"] + "/."
        with self.assertRaises(self.orchestrate.PlanRefusal) as raised:
            self.orchestrate.validate_semantic_graph(plan)
        self.assertIn("worktree collision", str(raised.exception))

    def test_exploit_branch_collision_and_unknown_dependency_are_refused(self):
        plan = self.clone_plan()
        plan["lanes"][1]["branch"] = plan["lanes"][0]["branch"]
        with self.assertRaises(self.orchestrate.PlanRefusal) as raised:
            self.orchestrate.validate_semantic_graph(plan)
        self.assertIn("branch collision", str(raised.exception))
        plan = self.clone_plan()
        plan["lanes"][1]["depends_on"] = ["missing"]
        with self.assertRaises(self.orchestrate.PlanRefusal) as raised:
            self.orchestrate.validate_semantic_graph(plan)
        self.assertIn("unknown lane", str(raised.exception))

    def test_exploit_duplicate_exact_claim_is_refused(self):
        plan = self.clone_plan()
        plan["lanes"][1]["claims"] = list(plan["lanes"][0]["claims"])
        with self.assertRaises(self.orchestrate.PlanRefusal) as raised:
            self.orchestrate.validate_semantic_graph(plan)
        self.assertIn("duplicate exact-key claim", str(raised.exception))

    def test_exploit_missing_budget_or_mode_is_refused_and_control_passes(self):
        for field in self.plan["budget"]:
            candidate = self.clone_plan()
            del candidate["budget"][field]
            candidate_path = self.root / ("missing-%s.json" % field)
            candidate_path.write_text(json.dumps(candidate))
            with self.subTest(missing=field):
                self.assertEqual(self.orchestrate.main([str(candidate_path)]), 1)
        candidate = self.clone_plan()
        del candidate["mode"]
        candidate_path = self.root / "missing-mode.json"
        candidate_path.write_text(json.dumps(candidate))
        self.assertEqual(self.orchestrate.main([str(candidate_path)]), 1)
        self.assertEqual(self.orchestrate.main([str(SAMPLE_PATH)]), 0)

    def test_control_gate_map_is_bijective_and_anchor_currency_is_current(self):
        value = json.loads(MAP_PATH.read_text())
        self.assertEqual(len(value["gates"]), 28)
        keys = {(row["component"], row["census_line"]) for row in value["gates"]}
        self.assertEqual(len(keys), 28)
        for row in value["gates"]:
            self.assertIn(row["anchor"], (ROOT / row["component"]).read_text())
        self.assertEqual(keys, self.orchestrate._census_gate_keys(CENSUS_PATH))
        self.assertEqual(len(re.findall(r"^### `.*?` L\d+", CENSUS_PATH.read_text(), re.M)), 28)

    def test_exploit_gate_map_loader_rejects_non_bijective_census_and_skips_absent_census(self):
        value = json.loads(MAP_PATH.read_text())
        value["gates"][0]["census_line"] = 999
        candidate = self.root / "gate-map.json"
        candidate.write_text(json.dumps(value))
        with mock.patch.object(self.orchestrate, "GATE_MAP_PATH", candidate):
            with self.assertRaises(self.orchestrate.PlanRefusal) as raised:
                self.orchestrate.load_gate_map()
        self.assertIn("not bijective", str(raised.exception))

        with mock.patch.object(self.orchestrate, "CENSUS_PATH", self.root / "absent-census.md"):
            self.orchestrate.load_gate_map()

    def _gate7_fixture(self, extra_approval=None, findings=None, windows=None):
        commit = "b" * 40
        approvals = [{
            "scope": "mandate", "by": "orchestrator", "revoked": None,
            "actions": ["plan-approval", "direction-approval", "finding-disposition"],
        }]
        events = [{
            "e": "approval:granted", "seq": 1, "run": "run-x",
            "plan_hash": None, "authorization_ref": "run-plan.json@%s" % commit,
        }]
        if extra_approval:
            approvals.append(extra_approval[0])
            events.append(extra_approval[1])
        snapshot = {
            "run": "run-x", "lane": "lane-x", "git": {"start_head": "start-head"},
            "approvals": approvals, "findings": findings or [],
        }
        return events, snapshot, windows or [{"lane": "lane-x", "dispatch_watermark": 1, "park_watermark": 10}]

    def _gate7(self, extra_approval=None, findings=None, windows=None, callback=None):
        events, snapshot, windows = self._gate7_fixture(extra_approval, findings, windows)
        return self.orchestrate.evaluate_gate_7(
            events, snapshot, windows, "a" * 64,
            callback or (lambda path, commit, start: True),
        )

    def test_control_gate7_mixed_approval_sources_and_valid_ref(self):
        self.assertTrue(self._gate7(extra_approval=(
            {"scope": "plan", "by": "mandate", "revoked": None, "actions": []},
            {"e": "plan:approved", "seq": 2, "plan_hash": "lane-plan"},
        )))

    def test_exploit_gate7_bad_missing_and_nonancestor_refs_fail(self):
        for reference in ("run-plan.json@" + "c" * 40, None):
            events, snapshot, windows = self._gate7_fixture()
            events[0].pop("authorization_ref", None) if reference is None else events[0].update(authorization_ref=reference)
            with self.subTest(reference=reference):
                self.assertFalse(self.orchestrate.evaluate_gate_7(events, snapshot, windows, "a" * 64, lambda *args: False))
        events, snapshot, windows = self._gate7_fixture()
        self.assertFalse(self.orchestrate.evaluate_gate_7(events, snapshot, windows, "a" * 64, lambda *args: False))

    def test_exploit_gate7_mandate_requires_exact_run_and_canonical_actions(self):
        events, snapshot, windows = self._gate7_fixture()
        events[0].pop("run")
        self.assertFalse(self.orchestrate.evaluate_gate_7(
            events, snapshot, windows, "a" * 64, lambda *args: True
        ))

        events, snapshot, windows = self._gate7_fixture()
        events[0]["run"] = "another-run"
        self.assertFalse(self.orchestrate.evaluate_gate_7(
            events, snapshot, windows, "a" * 64, lambda *args: True
        ))

        for alias in ("plan", "plan_approval", "direction", "direction_approval",
                      "finding", "findings", "finding_disposition"):
            events, snapshot, windows = self._gate7_fixture()
            snapshot["approvals"][0]["actions"] = [alias]
            with self.subTest(alias=alias):
                self.assertFalse(self.orchestrate.evaluate_gate_7(
                    events, snapshot, windows, "a" * 64, lambda *args: True
                ))

    def test_exploit_gate7_revoked_mandate_and_orchestrator_consumption_fail(self):
        events, snapshot, windows = self._gate7_fixture()
        snapshot["approvals"][0]["revoked"] = {"seq": 3}
        self.assertFalse(self.orchestrate.evaluate_gate_7(events, snapshot, windows, "a" * 64, lambda *args: True))
        self.assertFalse(self._gate7(extra_approval=(
            {"scope": "plan", "by": "orchestrator", "revoked": None, "actions": []},
            {"e": "plan:approved", "seq": 2, "plan_hash": "lane-plan", "authorization_ref": "run-plan.json@" + "b" * 40},
        )))

    def test_exploit_gate7_unknown_attribution_fails_closed(self):
        self.assertFalse(self._gate7(extra_approval=(
            {"scope": "plan", "by": "automation", "revoked": None, "actions": []},
            {"e": "plan:approved", "seq": 2, "plan_hash": "lane-plan"},
        )))

    def test_control_gate7_ship_handoff_and_attended_gap_pass(self):
        self.assertTrue(self._gate7(extra_approval=(
            {"scope": "handoff", "by": "ship", "revoked": None, "actions": []},
            {"e": "approval:granted", "seq": 2, "scope": "handoff"},
        )))
        self.assertTrue(self._gate7(extra_approval=(
            {"scope": "plan", "by": "user", "revoked": None, "actions": []},
            {"e": "plan:approved", "seq": 11, "plan_hash": "lane-plan"},
        ), windows=[{"lane": "lane-x", "dispatch_watermark": 1, "park_watermark": 5},
                    {"lane": "lane-x", "dispatch_watermark": 20, "park_watermark": 30}]))

    def test_exploit_gate7_ship_elsewhere_and_user_window_fail_control_boundary_passes(self):
        self.assertFalse(self._gate7(extra_approval=(
            {"scope": "plan", "by": "ship", "revoked": None, "actions": []},
            {"e": "plan:approved", "seq": 2},
        )))
        self.assertFalse(self._gate7(extra_approval=(
            {"scope": "plan", "by": "user", "revoked": None, "actions": []},
            {"e": "plan:approved", "seq": 2},
        )))
        self.assertTrue(self._gate7(extra_approval=(
            {"scope": "plan", "by": "user", "revoked": None, "actions": []},
            {"e": "plan:approved", "seq": 1},
        )))
        self.assertFalse(self._gate7(extra_approval=(
            {"scope": "plan", "by": "user", "revoked": None, "actions": []},
            {"e": "plan:approved", "seq": 12},
        ), windows=[{"lane": "lane-x", "dispatch_watermark": 1, "park_watermark": 5},
                    {"lane": "lane-x", "dispatch_watermark": 10, "park_watermark": 20}]))

    def test_exploit_gate7_attributionless_accepted_disposition_fails(self):
        findings = [{"id": "F1", "disposition": "accepted"}]
        events, snapshot, windows = self._gate7_fixture(findings=findings)
        events.append({"e": "finding:disposed", "seq": 2, "id": "F1", "disposition": "accepted"})
        self.assertFalse(self.orchestrate.evaluate_gate_7(events, snapshot, windows, "a" * 64, lambda *args: True))

    def test_control_gate7_explicit_mandate_disposition_passes(self):
        findings = [{"id": "F1", "disposition": "accepted"}]
        events, snapshot, windows = self._gate7_fixture(findings=findings)
        events.append({"e": "finding:disposed", "seq": 2, "id": "F1", "disposition": "accepted", "by": "mandate"})
        self.assertTrue(self.orchestrate.evaluate_gate_7(events, snapshot, windows, "a" * 64, lambda *args: True))

    def test_exploit_unpark_missing_and_blank_answer_are_refused(self):
        ledger = self.root / "ledger"
        self.assertEqual(self.orchestrate.main([
            "--unpark", "foundation", str(self.plan_path)
        ]), 1)
        self.state.open_run(self.plan_path, ledger)
        self.assertEqual(self.orchestrate.main([
            "--unpark", "foundation", str(self.plan_path), "--ledger-dir", str(ledger)
        ]), 1)
        record = ledger / "PARKED-foundation.md"
        record.write_text("# PARKED\n\n## Answer:\n\n## Notes:\nblank\n")
        self.assertEqual(self.orchestrate.main([
            "--unpark", "foundation", str(self.plan_path), "--ledger-dir", str(ledger)
        ]), 1)

    def test_control_unpark_appends_answer_sha_and_reports_dispatchable(self):
        ledger = self.root / "ledger"
        self.state.open_run(self.plan_path, ledger)
        record = ledger / "PARKED-foundation.md"
        record.write_text("# PARKED\n\n## Answer:\nProceed with the bounded plan.\n")
        self.state.append_event(ledger, {
            "e": "lane:parked", "lane": "foundation", "gate": "g7",
            "record_path": str(record), "lane_last_seq": 1,
        })
        result = self.orchestrate.main([
            "--unpark", "foundation", str(self.plan_path), "--ledger-dir", str(ledger)
        ])
        self.assertEqual(result, 0)
        snapshot = self.state.rebuild(ledger)
        self.assertEqual(snapshot["lanes"]["foundation"]["unparks"][0]["record_sha"],
                         hashlib.sha256(record.read_bytes()).hexdigest())
        self.assertIn("foundation", snapshot["dispatchable"])

    def test_control_in_process_spawn_primitives_are_never_attempted(self):
        ledger = self.root / "empty-ledger"
        unpark_ledger = self.root / "unpark-ledger"
        self.state.open_run(self.plan_path, unpark_ledger)
        record = unpark_ledger / "PARKED-foundation.md"
        record.write_text("# PARKED\n\n## Answer:\nProceed.\n")
        self.state.append_event(unpark_ledger, {
            "e": "lane:parked", "lane": "foundation", "gate": "g7",
            "record_path": str(record), "lane_last_seq": 1,
        })
        recorders = []

        def blocked(*args, **kwargs):
            recorders.append((args, kwargs))
            raise AssertionError("process creation attempted")

        patches = [mock.patch("subprocess.Popen", blocked), mock.patch("os.system", blocked)]
        process_names = {
            "execv", "execve", "execl", "execlp", "execle", "execlpe",
            "execvp", "execvpe",
            "spawnl", "spawnle", "spawnlp", "spawnlpe",
            "spawnv", "spawnve", "spawnvp", "spawnvpe",
            "posix_spawn", "posix_spawnp", "fork", "forkpty",
        }
        process_names.update({
            name for name in dir(os)
            if (name.startswith("exec") or name.startswith("spawn") or
                name.startswith("posix_spawn")) and callable(getattr(os, name))
        })
        for name in sorted(process_names):
            if hasattr(os, name):
                patches.append(mock.patch.object(os, name, blocked))
        patches.extend([
            mock.patch("pty.spawn", blocked),
            mock.patch("multiprocessing.Process.start", blocked),
        ])
        with contextlib.ExitStack() as stack:
            for patcher in patches:
                stack.enter_context(patcher)
            self.assertEqual(self.orchestrate.main([str(self.plan_path), "--ledger-dir", str(ledger)]), 0)
            self.assertEqual(self.orchestrate.main([
                "--unpark", "foundation", str(self.plan_path), "--ledger-dir", str(unpark_ledger)
            ]), 0)
        self.assertEqual(recorders, [])

    def test_control_path_sentinel_stays_absent_across_full_cli_run(self):
        sentinel = self.root / "spawned"
        fake = self.root / "fake-bin"
        fake.mkdir()
        for name in ("claude", "codex"):
            script = fake / name
            script.write_text("#!/bin/sh\ntouch %s\n" % sentinel)
            script.chmod(0o755)
        env = dict(os.environ)
        env["PATH"] = str(fake) + os.pathsep + env.get("PATH", "")
        result = subprocess.run([sys.executable, str(ORCHESTRATE_PATH), str(self.plan_path)],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(sentinel.exists())


if __name__ == "__main__":
    unittest.main()

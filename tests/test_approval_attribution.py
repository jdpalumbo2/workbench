#!/usr/bin/env python3
"""Exploit+control checks for approval attribution and mandates."""

import json
import unittest

try:
    from tests.clodex_harness import ClodexCheck, git, run_state
except ModuleNotFoundError:
    from clodex_harness import ClodexCheck, git, run_state


class ApprovalAttribution(ClodexCheck):
    def plan(self, run_dir):
        result = self.append(run_dir, {
            "e": "plan:recorded",
            "version": 1,
            "path": "plan.md",
            "hash": "h1",
        })
        self.assertEqual(result.returncode, 0, result.stderr)

    def assert_refused(self, run_dir, event):
        result = self.append(run_dir, event)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        return result

    def assert_refused_with(self, run_dir, event, needle):
        """Refused BY THE NAMED RULE — pins which guard fired, so a shadowing
        rule cannot keep a vacuous test green after the target rule vanishes."""
        result = self.assert_refused(run_dir, event)
        self.assertIn(needle, result.stderr, result.stderr)
        return result

    def assert_accepted(self, run_dir, event):
        result = self.append(run_dir, event)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_exploit_new_approval_without_by_is_refused(self):
        run_dir = self.make_run()
        self.plan(run_dir)
        result = self.append(run_dir, {
            "e": "approval:granted",
            "scope": "plan",
            "plan_hash": "h1",
        })
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_exploit_new_plan_approved_without_by_is_refused(self):
        run_dir = self.make_run()
        self.plan(run_dir)
        result = self.append(run_dir, {
            "e": "plan:approved",
            "scope": "plan",
            "plan_hash": "h1",
        })
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_control_historical_attributionless_approval_rebuilds_as_user(self):
        run_dir = self.make_run()
        self.plan(run_dir)
        with open(run_dir / "events.ndjson", "a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "schema_version": 1,
                "seq": 3,
                "t": "2026-09-01T00:00:00Z",
                "e": "approval:granted",
                "scope": "plan",
                "plan_hash": "h1",
            }) + "\n")
        snap = self.rebuild(run_dir)
        self.assertEqual(snap["approvals"][0]["by"], "user")

    def test_unknown_attribution_is_refused(self):
        run_dir = self.make_run()
        self.plan(run_dir)
        self.assert_refused(run_dir, {
            "e": "approval:granted", "scope": "plan", "plan_hash": "h1", "by": "robot",
        })

    def test_ship_attribution_is_only_legal_on_handoff(self):
        run_dir = self.make_run()
        self.plan(run_dir)
        self.assert_refused(run_dir, {
            "e": "approval:granted", "scope": "plan", "plan_hash": "h1", "by": "ship",
        })

    def test_handoff_accepts_ship_and_user(self):
        for by in ("ship", "user"):
            with self.subTest(by=by):
                run_dir = self.make_run(run_id="r-2026-08-16-%s" % by)
                self.plan(run_dir)
                self.assert_accepted(run_dir, {
                    "e": "approval:granted", "scope": "handoff", "plan_hash": "h1", "by": by,
                })

    def test_release_authorization_is_human_owned(self):
        # Rule order puts the release-authorization guard ABOVE the
        # attribution-specific rules, so for mandate and orchestrator it is
        # the guard itself that fires — pinned by its message. by:'ship' dies
        # earlier on its handoff-only rule; either way no non-user attribution
        # can land a release authorization.
        cases = {
            "mandate": "must be attributed to the user",
            "orchestrator": "must be attributed to the user",
            "ship": "must use scope:'handoff'",
        }
        for by, needle in cases.items():
            with self.subTest(by=by):
                run_dir = self.make_run(run_id="r-2026-08-17-%s" % by)
                self.plan(run_dir)
                self.assert_refused_with(run_dir, {
                    "e": "approval:granted", "scope": "release-authorization",
                    "plan_hash": "h1", "by": by,
                }, needle)

    def test_non_empty_accepted_debt_is_human_owned(self):
        # Isolating shape: the standing mandate makes every OTHER rule pass,
        # so only the accepted-debt guard can be the refusal.
        run_dir = self.make_run()
        self.assert_accepted(run_dir, {
            "e": "approval:granted", "scope": "mandate", "by": "user",
            "run": run_dir.name, "actions": [{"grants": "plan-approval"}],
        })
        self.plan(run_dir)
        self.assert_refused_with(run_dir, {
            "e": "approval:granted", "scope": "plan", "plan_hash": "h1",
            "by": "mandate", "accepted_debt": [{"class": "live-check"}],
        }, "accepted_debt must be attributed to the user")

    def test_mandate_on_any_other_scope_is_refused(self):
        # dirty-fold is a user acknowledgment; a mandate must never consume it.
        run_dir = self.make_run()
        self.assert_accepted(run_dir, {
            "e": "approval:granted", "scope": "mandate", "by": "user",
            "run": run_dir.name, "actions": [{"grants": "plan-approval"}],
        })
        self.plan(run_dir)
        self.assert_refused_with(run_dir, {
            "e": "approval:granted", "scope": "dirty-fold", "plan_hash": "h1",
            "by": "mandate",
        }, "must consume scope:'plan' or scope:'direction'")

    def test_orchestrator_cannot_consume_even_with_a_valid_ref(self):
        # Grants-only: a ref that WOULD resolve does not let by:'orchestrator'
        # consume a plan gate.
        run_dir = self.make_run()
        self.plan(run_dir)
        self.assert_refused_with(run_dir, {
            "e": "approval:granted", "scope": "plan", "plan_hash": "h1",
            "by": "orchestrator", "authorization_ref": "README.md@%s" % self.head(),
        }, "needs scope:'mandate'")

    def test_post_plan_mandate_binds_to_the_hash_and_amendment_revokes_it(self):
        run_dir = self.make_run()
        self.plan(run_dir)
        self.assert_accepted(run_dir, {
            "e": "approval:granted", "scope": "mandate", "by": "user",
            "plan_hash": "h1", "actions": [{"grants": "plan-approval"}],
        })
        self.assertEqual(self.rebuild(run_dir)["approvals"][0]["plan_hash"], "h1")
        self.assert_accepted(run_dir, {
            "e": "plan:approved", "scope": "plan", "by": "mandate", "plan_hash": "h1",
        })
        self.assert_accepted(run_dir, {
            "e": "plan:amended", "version": 2, "hash": "h2",
        })
        self.assert_refused_with(run_dir, {
            "e": "approval:granted", "scope": "plan", "by": "mandate", "plan_hash": "h2",
        }, "standing mandate")

    def test_orchestrator_ref_fails_closed_without_git(self):
        run_dir = self.make_run()
        event = self.orchestrator_mandate(run_dir, "README.md@%s" % self.head())
        result = run_state(
            ["append", str(run_dir)],
            stdin=json.dumps(event),
            env={"PATH": "/nonexistent-bin"},
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("does not resolve", result.stderr)

    def test_run_bound_mandate_before_plan_requires_the_matching_run(self):
        run_dir = self.make_run()
        event = {
            "e": "approval:granted", "scope": "mandate", "by": "user",
            "run": run_dir.name,
            "actions": [{"grants": "finding-disposition"},
                         {"grants": "plan-approval"},
                         {"grants": "direction-approval"}],
        }
        self.assert_accepted(run_dir, event)
        approval = self.rebuild(run_dir)["approvals"][0]
        self.assertIsNone(approval["plan_hash"])
        self.assertEqual(approval["run"], run_dir.name)
        self.assertEqual(approval["by"], "user")

    def test_run_bound_mandate_with_a_mismatched_run_is_refused(self):
        run_dir = self.make_run()
        self.assert_refused(run_dir, {
            "e": "approval:granted", "scope": "mandate", "by": "user",
            "run": "another-run", "actions": [{"grants": "plan-approval"}],
        })

    def test_run_bound_mandate_without_a_run_is_refused(self):
        run_dir = self.make_run()
        self.assert_refused(run_dir, {
            "e": "approval:granted", "scope": "mandate", "by": "user",
            "actions": [{"grants": "plan-approval"}],
        })

    def test_mandate_grants_are_closed_vocabulary(self):
        run_dir = self.make_run()
        self.assert_refused(run_dir, {
            "e": "approval:granted", "scope": "mandate", "by": "user",
            "run": run_dir.name, "actions": [{"grants": "release-authorization"}],
        })

    def test_mandate_covers_plan_and_direction_approval(self):
        run_dir = self.make_run()
        self.assert_accepted(run_dir, {
            "e": "approval:granted", "scope": "mandate", "by": "user",
            "run": run_dir.name,
            "actions": [{"grants": "plan-approval"}, {"grants": "direction-approval"}],
        })
        self.plan(run_dir)
        self.assert_accepted(run_dir, {
            "e": "plan:approved", "scope": "plan", "by": "mandate", "plan_hash": "h1",
        })
        self.assert_accepted(run_dir, {
            "e": "approval:granted", "scope": "direction", "by": "mandate",
            "plan_hash": "h1",
        })

    def test_each_grant_covers_only_its_own_scope(self):
        # A plan-approval grant must not consume the direction gate, and vice
        # versa — pins per-grant coverage, not just any-grant-present.
        cases = (
            ("plan-approval", "direction", "direction-approval"),
            ("direction-approval", "plan", "plan-approval"),
        )
        for granted, refused_scope, missing in cases:
            with self.subTest(granted=granted):
                run_dir = self.make_run(run_id="r-2026-08-19-%s" % granted[:4])
                self.assert_accepted(run_dir, {
                    "e": "approval:granted", "scope": "mandate", "by": "user",
                    "run": run_dir.name, "actions": [{"grants": granted}],
                })
                self.plan(run_dir)
                self.assert_refused_with(run_dir, {
                    "e": "approval:granted", "scope": refused_scope,
                    "by": "mandate", "plan_hash": "h1",
                }, missing)

    def test_mandate_consumption_without_a_standing_mandate_is_refused(self):
        run_dir = self.make_run()
        self.plan(run_dir)
        self.assert_refused(run_dir, {
            "e": "plan:approved", "scope": "plan", "by": "mandate", "plan_hash": "h1",
        })

    def test_plan_amendment_revokes_a_run_bound_mandate_before_consumption(self):
        run_dir = self.make_run()
        self.assert_accepted(run_dir, {
            "e": "approval:granted", "scope": "mandate", "by": "user",
            "run": run_dir.name, "actions": [{"grants": "plan-approval"}],
        })
        self.plan(run_dir)
        self.assert_accepted(run_dir, {
            "e": "plan:amended", "version": 2, "hash": "h2",
        })
        self.assert_refused(run_dir, {
            "e": "plan:approved", "scope": "plan", "by": "mandate", "plan_hash": "h2",
        })
        approval = self.rebuild(run_dir)["approvals"][0]
        self.assertIsNotNone(approval["revoked"])

    def test_mandate_can_dispose_findings_only_with_the_standing_grant(self):
        run_dir = self.make_run()
        self.assert_accepted(run_dir, {
            "e": "approval:granted", "scope": "mandate", "by": "user",
            "run": run_dir.name, "actions": [{"grants": "finding-disposition"}],
        })
        self.assert_accepted(run_dir, {
            "e": "finding:recorded", "id": "F-accepted", "source": "review",
            "severity": "low", "summary": "accepted finding",
        })
        self.assert_accepted(run_dir, {
            "e": "finding:disposed", "id": "F-accepted", "disposition": "accepted",
            "by": "mandate",
        })
        self.assert_accepted(run_dir, {
            "e": "finding:recorded", "id": "F-rejected", "source": "review",
            "severity": "low", "summary": "rejected finding",
        })
        self.assert_accepted(run_dir, {
            "e": "finding:disposed", "id": "F-rejected", "disposition": "rejected",
            "by": "mandate",
        })
        findings = self.rebuild(run_dir)["findings"]
        self.assertEqual([f["disposition_by"] for f in findings], ["mandate", "mandate"])

    def test_mandate_disposition_without_a_standing_grant_is_refused(self):
        run_dir = self.make_run()
        self.assert_accepted(run_dir, {
            "e": "finding:recorded", "id": "F1", "source": "review",
            "severity": "low", "summary": "needs disposition",
        })
        self.assert_refused(run_dir, {
            "e": "finding:disposed", "id": "F1", "disposition": "accepted", "by": "mandate",
        })

    def test_attributionless_accepted_and_rejected_dispositions_remain_legal(self):
        run_dir = self.make_run()
        for finding_id, disposition in (("F-accepted", "accepted"), ("F-rejected", "rejected")):
            self.assert_accepted(run_dir, {
                "e": "finding:recorded", "id": finding_id, "source": "review",
                "severity": "low", "summary": disposition,
            })
            self.assert_accepted(run_dir, {
                "e": "finding:disposed", "id": finding_id, "disposition": disposition,
            })
        for finding in self.rebuild(run_dir)["findings"]:
            self.assertNotIn("disposition_by", finding)

    def test_disposition_attribution_enum_rejects_orchestrator_and_ship(self):
        for by in ("orchestrator", "ship"):
            with self.subTest(by=by):
                run_dir = self.make_run(run_id="r-2026-08-18-%s" % by)
                self.assert_accepted(run_dir, {
                    "e": "finding:recorded", "id": "F1", "source": "review",
                    "severity": "low", "summary": "needs disposition",
                })
                self.assert_refused(run_dir, {
                    "e": "finding:disposed", "id": "F1", "disposition": "accepted", "by": by,
                })

    def orchestrator_mandate(self, run_dir, authorization_ref):
        return {
            "e": "approval:granted", "scope": "mandate", "by": "orchestrator",
            "run": run_dir.name, "authorization_ref": authorization_ref,
            "actions": [{"grants": "plan-approval"}],
        }

    def test_orchestrator_authorization_ref_shape_is_required(self):
        run_dir = self.make_run()
        self.assert_refused(run_dir, self.orchestrator_mandate(run_dir, "README.md@not-a-sha"))

    def test_orchestrator_tree_sha_is_not_a_commit(self):
        run_dir = self.make_run()
        tree = git(self.repo, "rev-parse", "HEAD^{tree}").stdout.strip()
        self.assert_refused(run_dir, self.orchestrator_mandate(run_dir, "README.md@%s" % tree))

    def test_orchestrator_missing_artifact_is_refused(self):
        run_dir = self.make_run()
        self.assert_refused(
            run_dir,
            self.orchestrator_mandate(run_dir, "missing-artifact.md@%s" % self.head()),
        )

    def test_orchestrator_commit_after_run_open_is_not_authorized(self):
        run_dir = self.make_run()
        (self.repo / "after-open.md").write_text("created after run opened\n")
        git(self.repo, "add", "after-open.md")
        git(self.repo, "commit", "-q", "-m", "after run opened")
        self.assert_refused(
            run_dir,
            self.orchestrator_mandate(run_dir, "after-open.md@%s" % self.head()),
        )

    def test_orchestrator_pre_run_commit_with_artifact_is_accepted(self):
        run_dir = self.make_run()
        authorization_ref = "README.md@%s" % self.head()
        self.assert_accepted(run_dir, self.orchestrator_mandate(run_dir, authorization_ref))
        approval = self.rebuild(run_dir)["approvals"][0]
        self.assertEqual(approval["authorization_ref"], authorization_ref)

    def test_telemetry_sync_filters_legacy_null_input_hashes(self):
        run_dir = self.make_run()
        runner_dir = self.repo / ".clodex" / "runner"
        envelope_dir = runner_dir / "implementer"
        envelope_dir.mkdir(parents=True)
        invocation = "implementer-null-hash"
        (envelope_dir / (invocation + ".envelope.json")).write_text(json.dumps({
            "invocation_id": invocation,
            "role": "implementer",
            "status": "complete",
            "inputs": [
                {"path": "legacy.md", "sha256": None},
                {"path": "current.md", "sha256": "a" * 64},
            ],
            "exit": {"duration_ms": 1000},
            "codex": {"resumed": True},
        }))
        result = run_state(["telemetry-sync", str(run_dir), str(runner_dir)])
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        block = json.loads(result.stdout)["codex"]
        self.assertEqual(block["input_hashes"], ["a" * 64])
        append_result = self.append(
            run_dir,
            dict(json.loads(result.stdout), e="stage:plan:entered"),
        )
        self.assertEqual(append_result.returncode, 0, append_result.stderr)
        self.assertEqual(
            self.rebuild(run_dir)["invocations"][0]["input_hashes"],
            ["a" * 64],
        )


if __name__ == "__main__":
    unittest.main()

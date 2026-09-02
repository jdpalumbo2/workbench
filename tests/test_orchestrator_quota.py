#!/usr/bin/env python3
"""Exploit/control checks for the lane-orchestration quota meter."""

import contextlib
import importlib.util
import io
import json
import multiprocessing
import os
import pty
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


CATALOGUE = Path(__file__).resolve().parent.parent
QUOTA = CATALOGUE / "skills" / "lane-orchestration" / "quota.py"


def load_quota():
    spec = importlib.util.spec_from_file_location("quota_under_test", QUOTA)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OrchestratorQuota(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="quota-check-")
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.sessions = root / "sessions"
        self.runs = root / "runs"
        self.sessions.mkdir()
        self.runs.mkdir()
        self.quota = load_quota()

    def write_rollout(self, name="rollout.jsonl", records=(), mtime=None,
                      final_bytes=None, parent="nested"):
        path = self.sessions / parent / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as stream:
            for record in records:
                stream.write(json.dumps(record).encode("utf-8") + b"\n")
            if final_bytes is not None:
                stream.write(final_bytes)
        if mtime is not None:
            os.utime(path, (mtime, mtime))
        return path

    def rate_limits(self, weekly=12.0, five_hour=34.0, weekly_reset=None,
                    five_hour_reset=None, secondary=True):
        now = time.time()
        if weekly_reset is None:
            weekly_reset = now + 3600
        if five_hour_reset is None:
            five_hour_reset = now + 1800
        primary = {
            "used_percent": weekly,
            "window_minutes": 10080,
            "resets_at": weekly_reset,
        }
        if secondary is None:
            secondary_value = None
        elif secondary:
            secondary_value = {
                "used_percent": five_hour,
                "window_minutes": 300,
                "resets_at": five_hour_reset,
            }
        else:
            secondary_value = secondary
        return {
            "primary": primary,
            "secondary": secondary_value,
            "credits": {"has_credits": False, "balance": 0},
        }

    def invoke(self, *args):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.quota.main([
                "--sessions-dir", str(self.sessions),
                "--runs-root", str(self.runs),
            ] + list(args))
        return code, stdout.getvalue(), stderr.getvalue()

    def invoke_json(self, *args):
        code, stdout, stderr = self.invoke("--json", *args)
        self.assertEqual(code, 0, stderr)
        self.assertEqual(len(stdout.splitlines()), 1, stdout)
        return json.loads(stdout)

    def test_exploit_secondary_null_is_unknown_and_never_zero(self):
        self.write_rollout(records=[{"payload": {
            "rate_limits": self.rate_limits(secondary=None)
        }}])

        code, stdout, stderr = self.invoke()

        self.assertEqual(code, 0, stderr)
        self.assertIn("5-hour UNKNOWN (refuse fan-out)", stdout)
        self.assertNotIn("5-hour 0.0%", stdout)
        report = self.invoke_json()
        self.assertEqual(report["windows"]["five_hour"]["status"], "unknown")
        self.assertIsNone(report["windows"]["five_hour"]["used_percent"])

    def test_control_populated_fresh_meters_read_by_identity(self):
        self.write_rollout(records=[{"rate_limits": self.rate_limits()}])

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["status"], "ok")
        self.assertEqual(report["windows"]["weekly"]["used_percent"], 12.0)
        self.assertEqual(report["windows"]["five_hour"]["status"], "ok")
        self.assertEqual(report["windows"]["five_hour"]["used_percent"], 34.0)
        self.assertEqual(report["credits"]["has_credits"], False)
        self.assertIn("weekly 12.0%", self.invoke()[1])

    def test_exploit_no_rollout_is_error_not_a_zero_meter(self):
        code, stdout, stderr = self.invoke()

        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("error:", stderr)

    def test_exploit_unparseable_only_rollout_is_error_not_a_pass(self):
        self.write_rollout(final_bytes=b"{this is torn and never valid\n")

        code, stdout, stderr = self.invoke()

        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn("parseable rate_limits", stderr)

    def test_exploit_last_rate_limits_record_wins_over_first_stale_record(self):
        first = self.rate_limits(weekly=11.0, five_hour=21.0)
        last = self.rate_limits(weekly=19.0, five_hour=29.0)
        self.write_rollout(records=[
            {"rate_limits": first},
            {"nested": [{"rate_limits": last}]},
        ])

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["used_percent"], 19.0)
        self.assertEqual(report["windows"]["five_hour"]["used_percent"], 29.0)

    def test_exploit_newest_rollout_file_wins_over_older_newer_looking_content(self):
        old = self.write_rollout(
            name="older.jsonl",
            records=[{"rate_limits": self.rate_limits(weekly=91.0)}],
            mtime=1000,
            parent="a",
        )
        self.write_rollout(
            name="newer.jsonl",
            records=[{"rate_limits": self.rate_limits(weekly=17.0)}],
            mtime=2000,
            parent="b",
        )
        # Make the content of the older file look more recent; file mtime is
        # the rollout ordering authority.
        old.write_text(json.dumps({"rate_limits": self.rate_limits(weekly=99.0)}) + "\n")
        os.utime(old, (1000, 1000))

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["used_percent"], 17.0)
        self.assertTrue(report["source_file"].endswith("newer.jsonl"))

    def test_exploit_torn_final_line_falls_back_to_previous_record(self):
        previous = self.rate_limits(weekly=23.0, five_hour=43.0)
        self.write_rollout(
            records=[{"rate_limits": previous}],
            final_bytes=b'{"event":{"rate_limits":',
        )

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["used_percent"], 23.0)
        self.assertEqual(report["windows"]["five_hour"]["used_percent"], 43.0)

    def test_exploit_past_weekly_reset_is_unknown_only_for_weekly_window(self):
        self.write_rollout(records=[{"rate_limits": self.rate_limits(
            weekly_reset=time.time() - 60,
            five_hour_reset=time.time() + 1800,
        )}])

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["status"], "unknown")
        self.assertEqual(report["windows"]["five_hour"]["status"], "ok")
        self.assertIn("weekly UNKNOWN (refuse fan-out)", self.invoke()[1])

    def test_control_future_resets_are_accepted(self):
        self.write_rollout(records=[{"rate_limits": self.rate_limits(
            weekly_reset=time.time() + 86400,
            five_hour_reset=time.time() + 86400,
        )}])

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["status"], "ok")
        self.assertEqual(report["windows"]["five_hour"]["status"], "ok")

    def test_exploit_window_duration_drift_refuses_both_windows(self):
        meters = self.rate_limits()
        meters["primary"]["window_minutes"] = 20160
        meters["secondary"]["window_minutes"] = 60
        self.write_rollout(records=[{"rate_limits": meters}])

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["status"], "unknown")
        self.assertEqual(report["windows"]["five_hour"]["status"], "unknown")

    def test_control_exact_durations_work_when_positions_are_swapped(self):
        meters = self.rate_limits(weekly=66.0, five_hour=77.0)
        meters["primary"], meters["secondary"] = (
            meters["secondary"], meters["primary"]
        )
        self.write_rollout(records=[{"rate_limits": meters}])

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["used_percent"], 66.0)
        self.assertEqual(report["windows"]["five_hour"]["used_percent"], 77.0)

    def test_exploit_newer_unusable_record_refuses_fallback_to_older_ok(self):
        # b1r1-F001: a good record followed by {"rate_limits": null} (or a
        # corrupt terminated line) must NOT report the older record as ok.
        good = self.rate_limits(weekly=15.0)
        path = self.write_rollout(records=[{"rate_limits": good}])
        with path.open("ab") as stream:
            stream.write(b'{"rate_limits": null}\n')

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["status"], "unknown")
        self.assertEqual(report["windows"]["five_hour"]["status"], "unknown")

    def test_exploit_corrupt_terminated_line_after_good_record_refuses(self):
        good = self.rate_limits(weekly=15.0)
        path = self.write_rollout(records=[{"rate_limits": good}])
        with path.open("ab") as stream:
            stream.write(b"{corrupt but newline terminated}\n")

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["status"], "unknown")

    def test_control_good_record_after_unusable_one_reads_through(self):
        path = self.write_rollout(records=[])
        with path.open("ab") as stream:
            stream.write(b'{"rate_limits": null}\n')
            stream.write(
                json.dumps({"rate_limits": self.rate_limits(weekly=18.0)}).encode()
                + b"\n"
            )

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["used_percent"], 18.0)

    def test_exploit_fresh_mtime_cannot_mask_old_record_timestamp(self):
        # b1r1-F003: freshness comes from the record's own timestamp when one
        # exists; a touch (fresh mtime) must not make an old meter usable.
        old_ts = time.time() - (8 * 24 * 60 * 60)
        self.write_rollout(records=[{
            "timestamp": old_ts,
            "rate_limits": self.rate_limits(),
        }])

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["status"], "unknown")
        self.assertEqual(report["record_age_source"], "record")
        self.assertGreater(report["record_age_seconds"], 7 * 24 * 60 * 60)

    def test_control_no_record_timestamp_falls_back_to_file_mtime(self):
        self.write_rollout(records=[{"rate_limits": self.rate_limits()}])

        report = self.invoke_json()

        self.assertEqual(report["record_age_source"], "file-mtime")
        self.assertEqual(report["windows"]["weekly"]["status"], "ok")

    def test_exploit_negative_used_percent_is_unknown_not_headroom(self):
        # b1r1-F005: a negative percentage is malformed data, not headroom.
        self.write_rollout(records=[{"rate_limits": self.rate_limits(weekly=-3.0)}])

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["status"], "unknown")
        self.assertEqual(report["windows"]["five_hour"]["status"], "ok")

    def test_exploit_primary_carrying_300_identifies_five_hour_with_null_secondary(self):
        # b1r1-F007: identity beats position — a valid meter with
        # window_minutes 300 is the 5-hour window wherever it sits.
        meters = self.rate_limits()
        meters["primary"] = {
            "used_percent": 44.0,
            "window_minutes": 300,
            "resets_at": time.time() + 1800,
        }
        meters["secondary"] = None
        self.write_rollout(records=[{"rate_limits": meters}])

        report = self.invoke_json()

        self.assertEqual(report["windows"]["five_hour"]["status"], "ok")
        self.assertEqual(report["windows"]["five_hour"]["used_percent"], 44.0)
        self.assertEqual(report["windows"]["weekly"]["status"], "unknown")

    def test_exploit_eight_day_old_record_makes_both_windows_unknown(self):
        old_mtime = time.time() - (8 * 24 * 60 * 60)
        self.write_rollout(
            records=[{"rate_limits": self.rate_limits()}],
            mtime=old_mtime,
        )

        report = self.invoke_json()

        self.assertEqual(report["windows"]["weekly"]["status"], "unknown")
        self.assertEqual(report["windows"]["five_hour"]["status"], "unknown")
        self.assertGreater(report["record_age_seconds"], 7 * 24 * 60 * 60)

    def write_ledger(self, directory, events):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "events.ndjson").write_text(
            "".join(json.dumps(event) + "\n" for event in events)
        )

    def test_ledger_no_run_is_explicit_zero_without_ledger(self):
        self.write_rollout(records=[{"rate_limits": self.rate_limits()}])

        code, stdout, stderr = self.invoke()

        self.assertEqual(code, 0, stderr)
        self.assertIn("claude $0.00 (no ledger)", stdout)

    def test_ledger_fixture_legs_are_summed_from_explicit_directory(self):
        self.write_rollout(records=[{"rate_limits": self.rate_limits()}])
        ledger = Path(self._tmp.name) / "explicit-ledger"
        self.write_ledger(ledger, [
            {"e": "other", "cost_usd": 100},
            {"e": "claude:leg", "cost_usd": 1.25},
            {"e": "claude:leg", "cost_usd": 2},
        ])

        report = self.invoke_json("--ledger-dir", str(ledger))

        self.assertEqual(report["claude"]["total_usd"], 3.25)
        self.assertEqual(report["claude"]["unknown_legs"], 0)

    def test_ledger_null_cost_is_unknown_and_total_is_lower_bound(self):
        self.write_rollout(records=[{"rate_limits": self.rate_limits()}])
        ledger = Path(self._tmp.name) / "explicit-ledger"
        self.write_ledger(ledger, [
            {"e": "claude:leg", "cost_usd": 4.5},
            {"e": "claude:leg", "cost_usd": None},
        ])

        code, stdout, stderr = self.invoke("--ledger-dir", str(ledger))

        self.assertEqual(code, 0, stderr)
        self.assertIn("claude ≥ $4.50 (+1 unknown legs)", stdout)
        self.assertNotIn("claude $4.50", stdout)

    def test_ledger_two_run_dirs_choose_newest_event_and_name_it(self):
        self.write_rollout(records=[{"rate_limits": self.rate_limits()}])
        first = self.runs / "run-first"
        second = self.runs / "run-second"
        self.write_ledger(first, [{"e": "claude:leg", "cost_usd": 1.0}])
        self.write_ledger(second, [{"e": "claude:leg", "cost_usd": 7.0}])
        os.utime(first / "events.ndjson", (1000, 1000))
        os.utime(second / "events.ndjson", (2000, 2000))

        code, stdout, stderr = self.invoke()

        self.assertEqual(code, 0, stderr)
        self.assertIn("claude $7.00", stdout)
        self.assertIn("ledger: run-second", stdout)

    def test_no_spawn_in_process_when_all_process_primitives_are_guarded(self):
        # b1r1-F006: the guard covers execlpe too, and the guarded invocation
        # exercises the ledger-reading paths, not just the meter read.
        self.write_rollout(records=[{"rate_limits": self.rate_limits()}])
        ledger = Path(self._tmp.name) / "guarded-ledger"
        self.write_ledger(ledger, [{"e": "claude:leg", "cost_usd": 1.0}])
        attempts = []

        def forbidden(*args, **kwargs):
            attempts.append((args, kwargs))
            raise AssertionError("quota attempted process creation")

        patches = [mock.patch.object(subprocess, "Popen", side_effect=forbidden)]
        for name in (
            "system", "execv", "execve", "execl", "execle", "execlp",
            "execlpe", "execvp", "execvpe", "spawnv", "spawnve", "spawnl",
            "spawnle", "spawnlp", "spawnlpe", "spawnvp", "spawnvpe",
            "posix_spawn", "posix_spawnp", "fork", "forkpty",
        ):
            if hasattr(os, name):
                patches.append(mock.patch.object(os, name, side_effect=forbidden))
        if hasattr(pty, "spawn"):
            patches.append(mock.patch.object(pty, "spawn", side_effect=forbidden))
        patches.append(mock.patch.object(
            multiprocessing.Process, "start", side_effect=forbidden
        ))

        with contextlib.ExitStack() as stack:
            for patcher in patches:
                stack.enter_context(patcher)
            code, stdout, stderr = self.invoke("--ledger-dir", str(ledger))

        self.assertEqual(code, 0, stderr)
        self.assertEqual(attempts, [])
        self.assertEqual(len(stdout.splitlines()), 1)
        self.assertIn("claude $1.00", stdout)

    def test_exploit_missing_explicit_ledger_dir_is_error_not_zero(self):
        # b1r1-F002: a named-but-absent ledger is an error, never $0.00.
        self.write_rollout(records=[{"rate_limits": self.rate_limits()}])

        code, stdout, stderr = self.invoke(
            "--ledger-dir", str(Path(self._tmp.name) / "nope")
        )

        self.assertEqual(code, 1)
        self.assertIn("ledger directory does not exist", stderr)

    def test_exploit_corrupt_ledger_lines_surface_as_uncertainty(self):
        self.write_rollout(records=[{"rate_limits": self.rate_limits()}])
        ledger = Path(self._tmp.name) / "corrupt-ledger"
        ledger.mkdir()
        (ledger / "events.ndjson").write_bytes(
            json.dumps({"e": "claude:leg", "cost_usd": 2.0}).encode() + b"\n"
            + b"{corrupt line\n"
        )

        code, stdout, stderr = self.invoke("--ledger-dir", str(ledger))

        self.assertEqual(code, 0, stderr)
        self.assertIn("claude ≥ $2.00", stdout)
        self.assertIn("corrupt lines", stdout)

    def test_exploit_negative_cost_is_unknown_leg_not_a_refund(self):
        # b1r1-F005: a negative cost must not subtract from the total.
        self.write_rollout(records=[{"rate_limits": self.rate_limits()}])
        ledger = Path(self._tmp.name) / "negative-ledger"
        self.write_ledger(ledger, [
            {"e": "claude:leg", "cost_usd": 5.0},
            {"e": "claude:leg", "cost_usd": -3.0},
        ])

        code, stdout, stderr = self.invoke("--ledger-dir", str(ledger))

        self.assertEqual(code, 0, stderr)
        self.assertIn("claude ≥ $5.00", stdout)
        self.assertIn("+1 unknown legs", stdout)

    def test_exploit_nested_ndjson_neither_wins_selection_nor_adds_legs(self):
        # b1r1-F004: only a run dir's top-level *.ndjson counts.
        self.write_rollout(records=[{"rate_limits": self.rate_limits()}])
        winner = self.runs / "run-winner"
        decoy = self.runs / "run-decoy"
        self.write_ledger(winner, [{"e": "claude:leg", "cost_usd": 2.0}])
        decoy.mkdir()
        nested = decoy / "archive"
        nested.mkdir()
        (nested / "events.ndjson").write_text(
            json.dumps({"e": "claude:leg", "cost_usd": 50.0}) + "\n"
        )
        os.utime(winner / "events.ndjson", (2000, 2000))
        os.utime(nested / "events.ndjson", (3000, 3000))
        # Nested legs inside the winner must not be summed either.
        deep = winner / "sub"
        deep.mkdir()
        (deep / "events.ndjson").write_text(
            json.dumps({"e": "claude:leg", "cost_usd": 40.0}) + "\n"
        )

        code, stdout, stderr = self.invoke()

        self.assertEqual(code, 0, stderr)
        self.assertIn("claude $2.00", stdout)
        self.assertIn("ledger: run-winner", stdout)

    def test_control_path_sentinel_stays_absent_during_full_cli_run(self):
        self.write_rollout(records=[{"rate_limits": self.rate_limits()}])
        root = Path(self._tmp.name)
        fake_bin = root / "bin"
        fake_bin.mkdir()
        marker = root / "spawned"
        for command in ("claude", "codex"):
            script = fake_bin / command
            script.write_text(
                "#!/bin/sh\nprintf spawned > %s\n" % marker
            )
            script.chmod(0o755)

        env = dict(os.environ)
        env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
        result = subprocess.run(
            [
                sys.executable, str(QUOTA),
                "--sessions-dir", str(self.sessions),
                "--runs-root", str(self.runs),
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(marker.exists())
        self.assertEqual(len(result.stdout.splitlines()), 1)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Exploit+control pair for clodex-build §12's re-review evidence scan.

Now that envelopes can carry null input hashes (a legacy resumed invocation)
the scan must never let None == None mark a role as evidenced. The embedded
python is extracted FROM the SKILL.md text and executed, so the production
fragment itself is what the pair drives — a regression in the file fails here.
"""

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


CATALOGUE = Path(__file__).resolve().parent.parent
BUILD_SKILL = CATALOGUE / "skills" / "clodex-build" / "SKILL.md"


def extract_exit_check():
    """Pull §12's embedded python block out of the SKILL.md — anchored to the
    Exit section and required to be unique there, so a relocated or duplicated
    heredoc fails loudly instead of silently testing the wrong block."""
    text = BUILD_SKILL.read_text()
    section = re.search(r"^## 12\. Exit\n(.*?)(?=^## |\Z)", text, re.DOTALL | re.MULTILINE)
    if not section:
        raise AssertionError("cannot find '## 12. Exit' in clodex-build/SKILL.md")
    matches = re.findall(
        r"python3 - \"\$STATE\" \"\$RUN_DIR\" \"\$RUNNER_STATE\" 1 2 3 <<'PY'\n(.*?)\nPY\n",
        section.group(1),
        re.DOTALL,
    )
    if len(matches) != 1:
        raise AssertionError(
            "expected exactly one §12 embedded script, found %d" % len(matches))
    return matches[0]


class ExitCheckEvidence(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="clodex-exit-check-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.runner_state = self.root / "runner"
        (self.runner_state / "plan-reviewer").mkdir(parents=True)
        self.plan = self.root / "plan.md"
        self.plan.write_text("the current plan\n")
        self.plan_hash = hashlib.sha256(self.plan.read_bytes()).hexdigest()

    def run_exit_check(self, snapshot):
        """Run the extracted script with a stubbed `$STATE` whose rebuild
        prints the given snapshot — the fragment's own subprocess call."""
        state_stub = self.root / "state_stub.py"
        state_stub.write_text(
            "import json, sys\n"
            "print(json.dumps(json.load(open(%r))))\n" % str(self.root / "snap.json")
        )
        (self.root / "snap.json").write_text(json.dumps(snapshot))
        return subprocess.run(
            [sys.executable, "-c", extract_exit_check(),
             str(state_stub), str(self.root / "run"), str(self.runner_state), "1"],
            capture_output=True, text=True, cwd=str(self.root),
        )

    def snapshot(self, plan_path):
        return {
            "batches": [{"id": 1, "commit": "c" * 40, "delta_review": "pass",
                          "owned_paths": []}],
            "findings": [],
            "approvals": [{"scope": "plan", "revoked": None, "plan_hash": "h"}],
            "plan": {"path": plan_path,
                     "amendments": [{"required_review": ["plan-reviewer"]}]},
        }

    def write_envelope(self, name, inputs):
        (self.runner_state / "plan-reviewer" / (name + ".envelope.json")).write_text(
            json.dumps({"role": "plan-reviewer", "status": "complete",
                        "inputs": inputs})
        )

    def test_exploit_null_hash_envelope_never_evidences_a_re_review(self):
        """Legacy envelope (sha256 null) + absent plan file was None == None:
        the declared re-review read as evidenced by an envelope that proved
        nothing. The guard must report it as missing instead."""
        self.write_envelope("legacy", [{"path": "plan.md", "sha256": None}])
        result = self.run_exit_check(self.snapshot("does-not-exist.md"))
        self.assertIn("declared re-review 'plan-reviewer' has no complete envelope",
                      result.stdout)
        self.assertIn("NOT DONE", result.stdout)

    def test_control_start_hash_envelope_still_evidences_its_role(self):
        self.write_envelope("current", [
            {"path": "plan.md", "sha256": self.plan_hash,
             "sha256_end": self.plan_hash, "hash_moment": "start"},
        ])
        result = self.run_exit_check(self.snapshot(str(self.plan)))
        self.assertNotIn("has no complete envelope", result.stdout)
        self.assertIn("evidenced: ['plan-reviewer']", result.stdout)
        self.assertIn("BUILD COMPLETE", result.stdout)


if __name__ == "__main__":
    unittest.main()

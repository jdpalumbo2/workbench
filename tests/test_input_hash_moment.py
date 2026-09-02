#!/usr/bin/env python3
"""Exploit/control checks for runner input-hash timing and resume behavior."""

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


CATALOGUE = Path(__file__).resolve().parent.parent
RUNNER = CATALOGUE / "skills" / "clodex" / "runner" / "run-codex.sh"
VALIDATOR = CATALOGUE / "skills" / "clodex" / "runner" / "validate_envelope.py"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class InputHashMoment(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="clodex-input-hash-")
        self.root = Path(self._tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.state = self.root / "state"
        self.prompt = self.root / "prompt.md"
        self.input = self.root / "reviewed.md"
        self.prompt.write_text("Review the input.\n")
        self.input.write_text("original contents\n")
        self.stub = self.bin / "codex"
        self.ready = self.root / "stub.ready"
        self.release = self.root / "stub.release"
        self.stub.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
out=""
prev=""
for arg in "$@"; do
    if [ "$prev" = "-o" ] || [ "$prev" = "--output-last-message" ]; then out="$arg"; fi
    prev="$arg"
done
printf '{\"type\":\"thread.started\",\"thread_id\":\"stub-session\"}\\n'
if [ "${STUB_WAIT_FOR_RELEASE:-0}" = 1 ]; then
    touch "${STUB_READY:?}"
    while [ ! -e "${STUB_RELEASE:?}" ]; do sleep 0.01; done
fi
printf '%s\\n' '{\"status\":\"complete\",\"summary\":\"stub done\",\"findings\":[]}' > "$out"
"""
        )
        self.stub.chmod(self.stub.stat().st_mode | stat.S_IXUSR)

    def tearDown(self):
        self._tmp.cleanup()

    def env(self, **extra):
        result = dict(os.environ)
        result["PATH"] = str(self.bin) + os.pathsep + result["PATH"]
        result["CLODEX_RUNNER_STATE_DIR"] = str(self.state)
        result.update(extra)
        return result

    def run_runner(self, *args, **env):
        return subprocess.run(
            [str(RUNNER), *map(str, args)],
            capture_output=True,
            text=True,
            env=self.env(**env),
        )

    def start_runner(self, *args, **env):
        return subprocess.Popen(
            [str(RUNNER), *map(str, args)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=self.env(**env),
        )

    def envelope(self):
        envelopes = list(self.state.glob("*/*.envelope.json"))
        self.assertEqual(len(envelopes), 1, envelopes)
        return json.loads(envelopes[0].read_text())

    def validate(self, path):
        return subprocess.run(
            [sys.executable, str(VALIDATOR), "validate", str(path)],
            capture_output=True,
            text=True,
        )

    def wait_for(self, path):
        for _ in range(200):
            if path.exists():
                return
            time.sleep(0.01)
        self.fail("stub did not create %s" % path)

    def test_exploit_mid_mutation_attests_start_and_end(self):
        """A file changed while codex runs must expose both moments."""
        original_hash = digest(self.input)
        process = self.start_runner(
            "--role", "advisor", "--repo", self.repo,
            "--prompt-file", self.prompt, "--input", self.input,
            STUB_WAIT_FOR_RELEASE="1", STUB_READY=self.ready,
            STUB_RELEASE=self.release,
        )
        self.wait_for(self.ready)
        self.input.write_text("mutated after invocation start\n")
        end_hash = digest(self.input)
        self.release.touch()
        stdout, stderr = process.communicate(timeout=10)

        self.assertEqual(process.returncode, 0, stdout + stderr)
        envelope = self.envelope()
        reviewed = next(item for item in envelope["inputs"]
                        if item["path"] == str(self.input.resolve()))
        self.assertEqual(reviewed["sha256"], original_hash)
        self.assertEqual(reviewed["sha256_end"], end_hash)
        self.assertNotEqual(reviewed["sha256"], reviewed["sha256_end"])
        self.assertEqual(reviewed["hash_moment"], "start")
        recorded = next(self.state.glob("*/*.inputs")).read_text().splitlines()
        self.assertIn("%s\t%s" % (self.input.resolve(), original_hash), recorded)

    def test_control_unmutated_input_has_equal_hashes_and_validates(self):
        result = self.run_runner(
            "--role", "advisor", "--repo", self.repo,
            "--prompt-file", self.prompt, "--input", self.input,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        envelope_path = next(self.state.glob("*/*.envelope.json"))
        envelope = json.loads(envelope_path.read_text())
        reviewed = next(item for item in envelope["inputs"]
                        if item["path"] == str(self.input.resolve()))
        self.assertEqual(reviewed["sha256"], digest(self.input))
        self.assertEqual(reviewed["sha256_end"], digest(self.input))
        self.assertEqual(reviewed["hash_moment"], "start")
        checked = self.validate(envelope_path)
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_missing_input_at_envelope_build_has_null_end_hash(self):
        original_hash = digest(self.input)
        process = self.start_runner(
            "--role", "advisor", "--repo", self.repo,
            "--prompt-file", self.prompt, "--input", self.input,
            STUB_WAIT_FOR_RELEASE="1", STUB_READY=self.ready,
            STUB_RELEASE=self.release,
        )
        self.wait_for(self.ready)
        self.input.unlink()
        self.release.touch()
        stdout, stderr = process.communicate(timeout=10)

        self.assertEqual(process.returncode, 0, stdout + stderr)
        envelope_path = next(self.state.glob("*/*.envelope.json"))
        envelope = json.loads(envelope_path.read_text())
        reviewed = next(item for item in envelope["inputs"]
                        if item["path"] == str(self.input.resolve()))
        self.assertEqual(reviewed["sha256"], original_hash)
        self.assertIsNone(reviewed["sha256_end"])
        self.assertEqual(self.validate(envelope_path).returncode, 0)

    def test_resume_preserves_original_start_hashes(self):
        original_hash = digest(self.input)
        process = self.start_runner(
            "--role", "advisor", "--repo", self.repo,
            "--prompt-file", self.prompt, "--input", self.input,
            STUB_WAIT_FOR_RELEASE="1", STUB_READY=self.ready,
            STUB_RELEASE=self.release,
        )
        self.wait_for(self.ready)
        process.terminate()
        stdout, stderr = process.communicate(timeout=10)
        self.assertEqual(process.returncode, 3, stdout + stderr)
        first = self.envelope()
        invocation_id = first["invocation_id"]
        inputs_file = next(self.state.glob("*/*.inputs"))
        original_records = inputs_file.read_text()
        self.input.write_text("changed before resume\n")
        resumed = self.run_runner(
            "--role", "advisor", "--repo", self.repo,
            "--resume", invocation_id,
        )
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        final = self.envelope()
        reviewed = next(item for item in final["inputs"]
                        if item["path"] == str(self.input.resolve()))
        self.assertEqual(reviewed["sha256"], original_hash)
        self.assertEqual(reviewed["hash_moment"], "start")
        self.assertEqual(final["codex"]["resumed"], True)
        self.assertEqual(inputs_file.read_text(), original_records)

    def test_legacy_bare_input_resume_is_fail_closed(self):
        role_dir = self.state / "advisor"
        role_dir.mkdir(parents=True)
        invocation_id = "advisor-legacy"
        meta = role_dir / (invocation_id + ".meta")
        meta.write_text(
            "role=advisor\n"
            "repo=%s\n"
            "model=gpt-5.6-sol\n"
            "effort=xhigh\n"
            "sandbox=read-only\n"
            "prompt_file=%s\n"
            "created_at=2026-09-01T00:00:00Z\n"
            % (self.repo.resolve(), self.prompt.resolve())
        )
        (role_dir / (invocation_id + ".inputs")).write_text(
            "%s\n%s\n" % (self.prompt.resolve(), self.input.resolve())
        )
        (role_dir / (invocation_id + ".session")).write_text("legacy-session\n")

        result = self.run_runner(
            "--role", "advisor", "--repo", self.repo,
            "--resume", invocation_id,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        envelope_path = role_dir / (invocation_id + ".envelope.json")
        envelope = json.loads(envelope_path.read_text())
        reviewed = next(item for item in envelope["inputs"]
                        if item["path"] == str(self.input.resolve()))
        self.assertIsNone(reviewed["sha256"])
        self.assertEqual(reviewed["hash_moment"], "unknown")
        self.assertNotIn("sha256_end", reviewed)
        checked = self.validate(envelope_path)
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_resume_records_late_inputs_and_keeps_originals(self):
        """--resume with a NEW --input must attest it, not silently drop it."""
        original_hash = digest(self.input)
        process = self.start_runner(
            "--role", "advisor", "--repo", self.repo,
            "--prompt-file", self.prompt, "--input", self.input,
            STUB_WAIT_FOR_RELEASE="1", STUB_READY=self.ready,
            STUB_RELEASE=self.release,
        )
        self.wait_for(self.ready)
        process.terminate()
        process.communicate(timeout=10)
        invocation_id = self.envelope()["invocation_id"]
        inputs_file = next(self.state.glob("*/*.inputs"))
        original_records = inputs_file.read_text()

        late = self.root / "late-artifact.md"
        late.write_text("declared at resume time\n")
        resumed = self.run_runner(
            "--role", "advisor", "--repo", self.repo,
            "--resume", invocation_id, "--input", late,
        )
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        final = self.envelope()
        by_path = {item["path"]: item for item in final["inputs"]}
        self.assertEqual(by_path[str(self.input.resolve())]["sha256"], original_hash)
        self.assertEqual(by_path[str(late.resolve())]["sha256"], digest(late))
        self.assertEqual(by_path[str(late.resolve())]["hash_moment"], "start")
        rewritten = inputs_file.read_text()
        self.assertTrue(rewritten.startswith(original_records))
        self.assertIn("%s\t%s" % (late.resolve(), digest(late)), rewritten)

    def test_resume_without_inputs_file_records_current_prompt(self):
        """A resume whose .inputs vanished still attests what it can, freshly."""
        process = self.start_runner(
            "--role", "advisor", "--repo", self.repo,
            "--prompt-file", self.prompt, "--input", self.input,
            STUB_WAIT_FOR_RELEASE="1", STUB_READY=self.ready,
            STUB_RELEASE=self.release,
        )
        self.wait_for(self.ready)
        process.terminate()
        process.communicate(timeout=10)
        invocation_id = self.envelope()["invocation_id"]
        next(self.state.glob("*/*.inputs")).unlink()

        resumed = self.run_runner(
            "--role", "advisor", "--repo", self.repo,
            "--resume", invocation_id,
        )
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        final = self.envelope()
        prompt_entry = next(item for item in final["inputs"]
                            if item["path"] == str(self.prompt.resolve()))
        self.assertEqual(prompt_entry["sha256"], digest(self.prompt))
        self.assertEqual(prompt_entry["hash_moment"], "start")

    def test_unreadable_input_refuses_the_invocation(self):
        """A hash that cannot be computed must refuse, never record empty."""
        self.input.chmod(0)
        try:
            result = self.run_runner(
                "--role", "advisor", "--repo", self.repo,
                "--prompt-file", self.prompt, "--input", self.input,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot hash input artifact", result.stderr)
            self.assertEqual(list(self.state.glob("*/*.envelope.json")), [])
        finally:
            self.input.chmod(0o644)

    def test_input_record_recognizes_digest_from_the_right(self):
        """A TAB inside a path must not be misread as a digest boundary."""
        sys.path.insert(0, str(VALIDATOR.parent))
        try:
            import validate_envelope
        finally:
            sys.path.pop(0)
        good = "a" * 64
        self.assertEqual(validate_envelope.input_record("/x/plan.md\t" + good),
                         ("/x/plan.md", good))
        self.assertEqual(validate_envelope.input_record("/x/tab\tname.md\t" + good),
                         ("/x/tab\tname.md", good))
        self.assertEqual(validate_envelope.input_record("/x/legacy\tbare.md"),
                         ("/x/legacy\tbare.md", None))
        self.assertEqual(validate_envelope.input_record("/x/legacy-plain.md"),
                         ("/x/legacy-plain.md", None))
        # The pathological legacy name — TAB then 64 hex — arrives under the
        # runner's #legacy prefix and must stay whole with NO digest claim.
        evil = "/x/evil\t" + good
        self.assertEqual(validate_envelope.input_record("#legacy\t" + evil),
                         (evil, None))

    def test_pathological_legacy_name_is_never_a_digest_claim(self):
        """End to end: a pre-upgrade bare path ending in TAB+64hex resumes
        with sha256 null and its path intact, never truncated into a false
        attestation."""
        evil = self.root / ("evil\t" + "a" * 64)
        evil.write_text("legacy artifact with a hostile name\n")
        role_dir = self.state / "advisor"
        role_dir.mkdir(parents=True)
        invocation_id = "advisor-evil-legacy"
        (role_dir / (invocation_id + ".meta")).write_text(
            "role=advisor\nrepo=%s\nmodel=gpt-5.6-sol\neffort=xhigh\n"
            "sandbox=read-only\nprompt_file=%s\ncreated_at=2026-09-01T00:00:00Z\n"
            % (self.repo.resolve(), self.prompt.resolve())
        )
        (role_dir / (invocation_id + ".inputs")).write_text(
            "%s\n%s\n" % (self.prompt.resolve(), evil.resolve())
        )
        (role_dir / (invocation_id + ".session")).write_text("legacy-session\n")

        # The resume ALSO declares the distinct file whose name is the evil
        # line's prefix: legacy dedup must not swallow it (headerless files
        # compare whole lines, never via the TAB+digest reading).
        prefix_twin = Path(str(evil).rsplit("\t", 1)[0])
        prefix_twin.write_text("distinct late-added artifact\n")
        result = self.run_runner(
            "--role", "advisor", "--repo", self.repo,
            "--resume", invocation_id, "--input", prefix_twin,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        envelope = json.loads((role_dir / (invocation_id + ".envelope.json")).read_text())
        by_path = {item["path"]: item for item in envelope["inputs"]}
        self.assertIn(str(evil.resolve()), by_path)
        self.assertIsNone(by_path[str(evil.resolve())]["sha256"])
        self.assertIn(str(prefix_twin.resolve()), by_path)
        self.assertEqual(by_path[str(prefix_twin.resolve())]["sha256"], digest(prefix_twin))

    def test_unreadable_inputs_file_refuses_resume_and_preserves_it(self):
        """A .inputs that cannot be read must refuse the resume, not be
        silently truncated and rewritten without the original records."""
        process = self.start_runner(
            "--role", "advisor", "--repo", self.repo,
            "--prompt-file", self.prompt, "--input", self.input,
            STUB_WAIT_FOR_RELEASE="1", STUB_READY=self.ready,
            STUB_RELEASE=self.release,
        )
        self.wait_for(self.ready)
        process.terminate()
        process.communicate(timeout=10)
        invocation_id = self.envelope()["invocation_id"]
        inputs_file = next(self.state.glob("*/*.inputs"))
        original = inputs_file.read_bytes()
        inputs_file.chmod(0o200)
        try:
            resumed = self.run_runner(
                "--role", "advisor", "--repo", self.repo,
                "--resume", invocation_id,
            )
            self.assertNotEqual(resumed.returncode, 0)
        finally:
            inputs_file.chmod(0o644)
        self.assertEqual(inputs_file.read_bytes(), original)

    def test_old_envelope_without_new_fields_still_validates(self):
        """Schema-v1 compatibility: an envelope written before this change —
        inputs carrying only path + string sha256 — must stay valid, so the
        new fields can never quietly become required."""
        result = self.run_runner(
            "--role", "advisor", "--repo", self.repo,
            "--prompt-file", self.prompt, "--input", self.input,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        envelope_path = next(self.state.glob("*/*.envelope.json"))
        envelope = json.loads(envelope_path.read_text())
        envelope["inputs"] = [
            {"path": item["path"], "sha256": "b" * 64}
            for item in envelope["inputs"]
        ]
        old_style = envelope_path.parent / "old-style.envelope.json"
        old_style.write_text(json.dumps(envelope))
        checked = self.validate(old_style)
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_role_effort_defaults_and_environment_override(self):
        runner_text = RUNNER.read_text()
        self.assertIn("role_effort() {", runner_text)
        self.assertIn('EFFORT="${CODEX_EFFORT:-$(role_effort "$ROLE")}"', runner_text)

        result = self.run_runner(
            "--role", "implementer", "--repo", self.repo,
            "--prompt-file", self.prompt,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        meta = next(self.state.glob("*/*.meta"))
        self.assertIn("effort=xhigh\n", meta.read_text())

        override_state = self.root / "override-state"
        overridden = subprocess.run(
            [str(RUNNER), "--role", "advisor", "--repo", str(self.repo),
             "--prompt-file", str(self.prompt)],
            capture_output=True,
            text=True,
            env=self.env(CLODEX_RUNNER_STATE_DIR=str(override_state),
                         CODEX_EFFORT="medium"),
        )
        self.assertEqual(overridden.returncode, 0, overridden.stderr)
        self.assertIn("effort=medium\n", next(override_state.glob("*/*.meta")).read_text())


if __name__ == "__main__":
    unittest.main()

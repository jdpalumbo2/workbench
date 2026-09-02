#!/usr/bin/env python3
"""Exploit/control checks for bootstrap inspection and currency.

These tests use the real state scripts against temporary repositories.  The
fixture tests intentionally exercise the old failure shapes first: a skill
change without a VERSION change, and a repository whose bootstrap record no
longer describes its checkout.
"""

import hashlib
import importlib.util
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

try:
    from clodex_harness import CATALOGUE, ClodexCheck, git
except ModuleNotFoundError:  # ``python -m unittest tests.test_*`` from root.
    from tests.clodex_harness import CATALOGUE, ClodexCheck, git


STATE_DIR = CATALOGUE / "skills" / "clodex" / "state"
INSPECT = STATE_DIR / "inspect_repo.py"
BOOTSTRAP_CHECK = STATE_DIR / "bootstrap_check.py"
VERSION = CATALOGUE / "skills" / "clodex" / "VERSION"


def load_inspector():
    spec = importlib.util.spec_from_file_location("inspect_repo_for_test", INSPECT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


INSPECTOR = load_inspector()


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True,
        text=True,
    )


def _git_text(repo, *args):
    result = _git(repo, *args)
    return result.stdout.strip() if result.returncode == 0 else ""


def _default_branch(repo):
    """Find the configured default branch without asking the network."""
    remotes = _git_text(repo, "remote").splitlines()
    for remote in remotes:
        ref = _git_text(repo, "symbolic-ref", "--quiet", f"refs/remotes/{remote}/HEAD")
        if ref:
            return ref
    for candidate in ("main", "master"):
        if _git(repo, "show-ref", "--verify", f"refs/heads/{candidate}").returncode == 0:
            return candidate
    return ""


def version_baseline(repo):
    """Return (base, reason), following the committed VERSION-test contract.

    The merge-base attempt runs whether or not HEAD is attached — a detached
    CI checkout of a feature commit still has a true branch point against the
    default branch, and falling straight to the newest tag there can mask an
    unbumped SKILL.md change made after an older VERSION bump."""
    default_branch = _default_branch(repo)
    if default_branch:
        merge_base = _git_text(repo, "merge-base", "HEAD", default_branch)
        if merge_base:
            # Used even when it EQUALS HEAD: on a fresh branch tip (or on the
            # default branch itself) the working-tree diff from HEAD is the
            # honest range for uncommitted edits. Falling to the tag there
            # lets a prior VERSION bump on the default branch mask a fresh
            # unbumped SKILL.md edit — the pre-commit micro-gate's normal
            # first-change shape (b4r2-F001).
            return merge_base, f"merge-base(HEAD, {default_branch})"

    tag = _git_text(repo, "tag", "--list", "clodex-v*", "--sort=-version:refname").splitlines()
    if tag:
        tag_commit = _git_text(repo, "rev-list", "-n", "1", tag[0])
        if tag_commit:
            return tag_commit, f"newest tag {tag[0]}"
    return None, "neither a default-branch merge base nor a clodex-v* tag exists"


def version_discipline(repo):
    """Check the real working-tree diff, or print an explicit skip reason."""
    base, reason = version_baseline(repo)
    if base is None:
        print(f"SKIP VERSION discipline: {reason}")
        return None
    changed = _git_text(repo, "diff", "--name-only", base).splitlines()
    skill_changed = any(re.fullmatch(r"skills/clodex[^/]*/SKILL\.md", path) for path in changed)
    version_changed = "skills/clodex/VERSION" in changed
    return not skill_changed or version_changed


def bootstrap_for(repo, clodex_version=None, date="2026-09-01"):
    inspected, fingerprint = INSPECTOR.probe(repo)
    return {
        "clodex_version": clodex_version or VERSION.read_text().strip(),
        "derived_at": date,
        "repo_fingerprint": fingerprint,
        "inspected": inspected,
    }


class InspectRepoContract(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="clodex-inspect-")
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()

    def run_inspect(self, *args):
        return subprocess.run(
            ["python3", str(INSPECT), str(self.repo)] + list(args),
            capture_output=True,
            text=True,
        )

    def test_exploit_and_control_use_one_deterministic_marker_pass(self):
        (self.repo / "package.json").write_text(json.dumps({
            "scripts": {"z": "z", "a": "a"},
            "engines": {"node": ">=20", "npm": ">=10"},
        }))
        (self.repo / "tests").mkdir()
        workflows = self.repo / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "z.yml").write_text("name: z\n")
        (workflows / "a.yml").write_text("name: a\n")
        (self.repo / "pyproject.toml").write_text(
            "[project]\nrequires-python = '>=3.11'\n"
        )

        normal = self.run_inspect("--date", "2026-09-01")
        self.assertEqual(normal.returncode, 0, normal.stderr)
        all_lines = [line for line in normal.stdout.splitlines() if line]
        aids_at = next(i for i, line in enumerate(all_lines)
                       if line.startswith("-- interview aids"))
        lines = all_lines[:aids_at]
        self.assertEqual(len(lines), len(INSPECTOR.MARKERS), normal.stdout)
        artifact = json.loads(
            (self.repo / ".clodex" / "bootstrap-2026-09-01.inspection.json").read_text()
        )

        machine = self.run_inspect("--date", "2026-09-01", "--json")
        self.assertEqual(machine.returncode, 0, machine.stderr)
        emitted = json.loads(machine.stdout)
        self.assertEqual(emitted["inspected"], artifact["inspected"])
        self.assertEqual(emitted["repo_fingerprint"], artifact["repo_fingerprint"])

        expected_lines = [
            f"{item['marker']}\t{1 if item['present'] else 0}\t"
            f"{item['value'] if item['value'] is not None else ''}"
            for item in emitted["inspected"]
        ]
        expected = "sha256:" + hashlib.sha256(
            "\n".join(expected_lines).encode("utf-8")
        ).hexdigest()
        self.assertEqual(emitted["repo_fingerprint"], expected)
        # The vocabulary is pinned as the LITERAL approved tuple (plan
        # Appendix A), never via INSPECTOR.MARKERS — a wrong tuple in the
        # module must fail here, not agree with itself.
        self.assertEqual(
            [item["marker"] for item in emitted["inspected"]],
            [
                "package.json", "pyproject.toml", "Makefile", "Dockerfile",
                "docker-compose.yml", "tox.ini", "vercel.json", "railway.json",
                "fly.toml", ".nvmrc", ".tool-versions", ".python-version",
                "go.mod", "Cargo.toml", "requirements.txt", "setup.py",
                "tests/", ".github/workflows", ".gcloudignore", ".dockerignore",
                ".vercelignore", ".npmignore", "CHANGELOG.md", "js-lockfile",
                "package.json#scripts", "package.json#engines",
                ".github/workflows#files", "pyproject.toml#requires-python",
            ],
        )
        # One-pass property, pinned by instrumentation: every marker is probed
        # exactly once per probe() call, and the fingerprint is the digest of
        # the same returned records (b4r2-F005).
        counts = {}
        original = INSPECTOR._probe_marker

        def counting(repo, marker, package, workflow_files):
            counts[marker] = counts.get(marker, 0) + 1
            return original(repo, marker, package, workflow_files)

        INSPECTOR._probe_marker = counting
        try:
            inspected, fingerprint = INSPECTOR.probe(self.repo)
        finally:
            INSPECTOR._probe_marker = original
        self.assertEqual(fingerprint, INSPECTOR.fingerprint(inspected))
        self.assertEqual(sorted(counts), sorted(INSPECTOR.MARKERS))
        self.assertEqual(set(counts.values()), {1}, counts)

    def test_control_ignores_profile_commands_and_unmarked_file_contents(self):
        (self.repo / "package.json").write_text(json.dumps({
            "scripts": {"a": "a"}, "engines": {"node": ">=20"},
        }))
        (self.repo / ".nvmrc").write_text("20\n")
        first = INSPECTOR.probe(self.repo)[1]
        (self.repo / ".clodex").mkdir()
        (self.repo / ".clodex" / "profile.json").write_text(
            json.dumps({"commands": {"test": "changed"}})
        )
        (self.repo / "unmarked-source.py").write_text("one\n")
        # A MARKED file's contents move without moving its marker values:
        # same script keys and engines, different bodies/formatting/extras,
        # and a different .nvmrc pin (existence marker by design).
        (self.repo / "package.json").write_text(json.dumps({
            "scripts": {"a": "totally different body"},
            "engines": {"node": ">=20"},
            "description": "content churn the fingerprint must ignore",
        }, indent=4))
        (self.repo / ".nvmrc").write_text("22\n")
        second = INSPECTOR.probe(self.repo)[1]
        self.assertEqual(first, second)
        # And a marker-visible change DOES move it (script key set).
        (self.repo / "package.json").write_text(json.dumps({
            "scripts": {"a": "a", "b": "b"}, "engines": {"node": ">=20"},
        }))
        self.assertNotEqual(second, INSPECTOR.probe(self.repo)[1])


class BootstrapVerdicts(ClodexCheck):
    def run_check(self, repo=None):
        repo = repo or self.repo
        return subprocess.run(
            ["python3", str(BOOTSTRAP_CHECK), str(repo), str(CATALOGUE / "skills" / "clodex")],
            capture_output=True,
            text=True,
        )

    def write_profile(self, bootstrap=None, **overrides):
        self.repo.joinpath(".clodex").mkdir(exist_ok=True)
        profile = {"schema_version": 1}
        if bootstrap is not None:
            profile["bootstrap"] = bootstrap
        profile.update(overrides)
        self.repo.joinpath(".clodex", "profile.json").write_text(
            json.dumps(profile, sort_keys=True)
        )
        return profile

    def test_exploit_first_run_defers_before_other_questions(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("first-run — defer to §3", result.stdout)
        self.assertEqual(len(result.stdout.splitlines()), 1)

    def test_exploit_contract_version_mismatch_routes_to_rederive(self):
        self.write_profile()
        self.repo.joinpath(".clodex", "profile.json").write_text(
            json.dumps({"schema_version": 2})
        )
        result = self.run_check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("re-derive", result.stdout)
        self.assertIn("contract-moved", result.stdout)

    def test_missing_bootstrap_is_recorded_not_enforced(self):
        # Johnny's 2026-09-02 ruling: currency drift records, never re-derives.
        # A profile with no bootstrap block was the CRE repo's exact case.
        self.write_profile()
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("recorded", result.stdout)
        self.assertIn("bootstrap missing", result.stdout)
        self.assertNotIn("re-derive", result.stdout)

    def test_unknown_bootstrap_key_is_recorded_and_named(self):
        bootstrap = bootstrap_for(self.repo)
        bootstrap["unexpected"] = "nope"
        self.write_profile(bootstrap)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("recorded", result.stdout)
        self.assertIn("unknown key 'unexpected'", result.stdout)
        self.assertNotIn("re-derive", result.stdout)

    def test_skill_and_repo_drift_are_both_recorded(self):
        """Currency drift no longer short-circuits: with a skill-version drift
        AND a fingerprint drift present, each is recorded and the run passes."""
        self.write_profile(bootstrap_for(self.repo, clodex_version="0.3.0"))
        (self.repo / "Makefile").write_text("all:\n\t@true\n")
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("skill-moved", result.stdout)
        self.assertIn("repo-moved", result.stdout)
        self.assertIn("recorded", result.stdout)
        self.assertNotIn("re-derive", result.stdout)

    def test_fingerprint_move_is_recorded_unmarked_file_is_not(self):
        self.write_profile(bootstrap_for(self.repo))
        (self.repo / "Makefile").write_text("all:\n\t@true\n")
        moved = self.run_check()
        self.assertEqual(moved.returncode, 0, moved.stdout + moved.stderr)
        self.assertIn("repo-moved", moved.stdout)
        self.assertIn("recorded", moved.stdout)

        (self.repo / "Makefile").unlink()
        (self.repo / "new-source.py").write_text("print('new')\n")
        stable = self.run_check()
        self.assertEqual(stable.returncode, 0, stable.stdout + stable.stderr)
        self.assertNotIn("repo-moved", stable.stdout)

    def test_incomplete_inspected_is_recorded(self):
        bootstrap = bootstrap_for(self.repo)
        bootstrap["inspected"] = bootstrap["inspected"][:-1]
        self.write_profile(bootstrap)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("recorded", result.stdout)
        self.assertIn("bootstrap-incomplete", result.stdout)
        self.assertIn(INSPECTOR.MARKERS[-1], result.stdout)

    def test_major_version_drift_is_recorded(self):
        """MAJOR drift with the same MINOR is still incompatible drift
        (b4-F002); it is now recorded, not enforced."""
        current = VERSION.read_text().strip()
        major, rest = current.split(".", 1)
        drifted = f"{int(major) + 1}.{rest}"
        self.write_profile(bootstrap_for(self.repo, clodex_version=drifted))
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("skill-moved", result.stdout)
        self.assertIn("recorded", result.stdout)

    def test_unknown_inspected_key_is_recorded_and_named(self):
        bootstrap = bootstrap_for(self.repo)
        bootstrap["inspected"][0]["surprise"] = True
        self.write_profile(bootstrap)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("recorded", result.stdout)
        self.assertIn("unknown key 'surprise'", result.stdout)


class VersionDiscipline(unittest.TestCase):
    def test_current_working_tree_requires_the_bump(self):
        result = version_discipline(CATALOGUE)
        if result is None:
            self.skipTest("baseline unavailable; skip reason was printed")
        self.assertTrue(result, "a changed clodex SKILL.md requires skills/clodex/VERSION")

    def test_exploit_skill_move_without_version_fails_and_control_both_move_passes(self):
        with tempfile.TemporaryDirectory(prefix="clodex-version-") as root:
            repo = Path(root)
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.email", "check@clodex.test")
            git(repo, "config", "user.name", "clodex check")
            skill = repo / "skills" / "clodex" / "SKILL.md"
            version = repo / "skills" / "clodex" / "VERSION"
            skill.parent.mkdir(parents=True)
            skill.write_text("before\n")
            version.write_text("0.3.0\n")
            git(repo, "add", ".")
            git(repo, "commit", "-q", "-m", "base")
            git(repo, "tag", "clodex-v0.3.0")

            skill.write_text("after\n")
            self.assertFalse(version_discipline(repo), "old exploit must fail")
            version.write_text("0.4.0\n")
            self.assertTrue(version_discipline(repo), "VERSION control must pass")

    def test_exploit_detached_head_still_uses_the_true_branch_point(self):
        """A detached checkout must not fall to the tag baseline: an older
        VERSION bump on the default branch between the tag and the branch
        point would mask a later unbumped SKILL.md change (b4-F001)."""
        with tempfile.TemporaryDirectory(prefix="clodex-version-detached-") as root:
            repo = Path(root)
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.email", "check@clodex.test")
            git(repo, "config", "user.name", "clodex check")
            skill = repo / "skills" / "clodex" / "SKILL.md"
            version = repo / "skills" / "clodex" / "VERSION"
            skill.parent.mkdir(parents=True)
            skill.write_text("before\n")
            version.write_text("0.3.0\n")
            git(repo, "add", ".")
            git(repo, "commit", "-q", "-m", "base")
            git(repo, "tag", "clodex-v0.3.0")
            # An unrelated VERSION bump lands on main AFTER the tag...
            version.write_text("0.3.1\n")
            git(repo, "add", "skills/clodex/VERSION")
            git(repo, "commit", "-q", "-m", "patch bump on main")
            # ...then a DETACHED commit changes SKILL.md with no bump — the
            # commit advances no branch, so main stays at the bump commit.
            git(repo, "checkout", "-q", "--detach", "HEAD")
            skill.write_text("changed while detached\n")
            git(repo, "add", "skills/clodex/SKILL.md")
            git(repo, "commit", "-q", "-m", "skill change, no bump")
            # Tag fallback would see the 0.3.0 -> 0.3.1 bump inside its range
            # and pass; the merge-base baseline sees only the SKILL.md change.
            self.assertFalse(version_discipline(repo),
                             "detached HEAD must use the branch-point baseline")

    def test_exploit_fresh_branch_tip_uses_head_not_the_tag(self):
        """merge-base == HEAD is still the baseline (b4r2-F001): on a fresh
        branch at the default tip, an UNCOMMITTED SKILL.md edit must fail even
        though main bumped VERSION after the newest tag."""
        with tempfile.TemporaryDirectory(prefix="clodex-version-tip-") as root:
            repo = Path(root)
            git(repo, "init", "-q", "-b", "main")
            git(repo, "config", "user.email", "check@clodex.test")
            git(repo, "config", "user.name", "clodex check")
            skill = repo / "skills" / "clodex" / "SKILL.md"
            version = repo / "skills" / "clodex" / "VERSION"
            skill.parent.mkdir(parents=True)
            skill.write_text("before\n")
            version.write_text("0.3.0\n")
            git(repo, "add", ".")
            git(repo, "commit", "-q", "-m", "base")
            git(repo, "tag", "clodex-v0.3.0")
            version.write_text("0.3.1\n")
            git(repo, "add", "skills/clodex/VERSION")
            git(repo, "commit", "-q", "-m", "patch bump on main")
            git(repo, "checkout", "-q", "-b", "feature/fresh")
            skill.write_text("uncommitted edit on a fresh tip\n")
            self.assertFalse(version_discipline(repo),
                             "a fresh-tip uncommitted edit must not hide behind the tag range")

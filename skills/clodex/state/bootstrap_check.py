#!/usr/bin/env python3
"""Check whether a repository's clodex bootstrap record is current.

Usage:
    python3 bootstrap_check.py <repo> <clodex_home>

The inspection implementation is imported from inspect_repo.py.  This file
only evaluates the recorded profile against that one probe.
"""

import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import inspect_repo
except ModuleNotFoundError:  # Also support importing this script by file path.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import inspect_repo


BOOTSTRAP_KEYS = frozenset({
    "clodex_version", "derived_at", "repo_fingerprint", "inspected"
})
INSPECTED_KEYS = frozenset({"marker", "present", "value"})
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FINGERPRINT = re.compile(r"^sha256:[0-9a-f]{64}$")


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True,
        text=True,
    )


def _git_text(repo, *args):
    result = _git(repo, *args)
    return result.stdout.strip() if result.returncode == 0 else ""


def _git_path(repo, value):
    path = Path(value)
    return path if path.is_absolute() else repo / path


def is_linked_worktree(repo):
    git_dir = _git_text(repo, "rev-parse", "--git-dir")
    common_dir = _git_text(repo, "rev-parse", "--git-common-dir")
    if not git_dir or not common_dir:
        return False
    return os.path.realpath(_git_path(repo, git_dir)) != os.path.realpath(
        _git_path(repo, common_dir)
    )


def _schema_versions(clodex_home):
    path = Path(clodex_home) / "profile.schema.json"
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
        values = schema["properties"]["schema_version"]["enum"]
        return tuple(values)
    except (OSError, ValueError, KeyError, TypeError):
        # The current contract is schema_version 1.  Keeping this fallback
        # makes the checker useful with a minimal synthetic clodex home too;
        # a real home always supplies the schema.
        return (1,)


def _version(path):
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return _version_value(value)


def _verdict(number, status, detail):
    print(f"{number}. {status} — {detail}")


def _rederive(number, detail):
    _verdict(number, "re-derive", detail)
    return 1


def _exact_keys(value, approved, label):
    if not isinstance(value, dict):
        return f"{label} is not an object"
    unknown = sorted(set(value) - approved)
    if unknown:
        return f"unknown key '{unknown[0]}' in {label}"
    missing = sorted(approved - set(value))
    if missing:
        return f"missing key '{missing[0]}' in {label}"
    return None


def _check_bootstrap(bootstrap):
    problem = _exact_keys(bootstrap, BOOTSTRAP_KEYS, "bootstrap")
    if problem:
        return problem

    version = bootstrap["clodex_version"]
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        return "bootstrap.clodex_version is not MAJOR.MINOR.PATCH"
    derived_at = bootstrap["derived_at"]
    if (not isinstance(derived_at, str) or not DATE.fullmatch(derived_at)):
        return "bootstrap.derived_at is not YYYY-MM-DD"
    try:
        datetime.datetime.strptime(derived_at, "%Y-%m-%d")
    except ValueError:
        return "bootstrap.derived_at is not a calendar date"
    fingerprint = bootstrap["repo_fingerprint"]
    if not isinstance(fingerprint, str) or not FINGERPRINT.fullmatch(fingerprint):
        return "bootstrap.repo_fingerprint is not sha256:<64 lowercase hex>"

    inspected = bootstrap["inspected"]
    if not isinstance(inspected, list) or not inspected:
        return "bootstrap-incomplete — inspected is empty"

    seen = set()
    for index, item in enumerate(inspected):
        problem = _exact_keys(item, INSPECTED_KEYS, f"inspected[{index}]")
        if problem:
            return problem
        marker = item["marker"]
        if not isinstance(marker, str):
            return f"inspected[{index}].marker is not a string"
        if marker not in inspect_repo.MARKERS:
            return f"bootstrap-incomplete — unknown marker '{marker}'"
        if marker in seen:
            return f"bootstrap-incomplete — duplicate marker '{marker}'"
        seen.add(marker)
        present = item["present"]
        if not isinstance(present, bool):
            return f"inspected[{index}].present is not boolean"
        value = item["value"]
        if value is not None and not isinstance(value, str):
            return f"inspected[{index}].value is not string or null"
        if marker not in inspect_repo.VALUE_MARKERS and value is not None:
            return f"inspected[{index}].value must be null for '{marker}'"
        if marker in inspect_repo.VALUE_MARKERS:
            if present and value is None:
                return f"inspected[{index}].value missing for '{marker}'"
            if not present and value is not None:
                return f"inspected[{index}].value must be null when '{marker}' is absent"

    missing = [marker for marker in inspect_repo.MARKERS if marker not in seen]
    if missing:
        return f"bootstrap-incomplete — missing marker '{missing[0]}'"
    return None


def check(repo, clodex_home):
    repo = Path(repo).resolve()
    clodex_home = Path(clodex_home).resolve()
    profile_path = repo / ".clodex" / "profile.json"
    worktree = is_linked_worktree(repo)

    # Question 1 is intentionally a complete early branch.  A missing
    # profile is not a failed bootstrap; §3 owns the first-run interview.
    if not profile_path.is_file():
        print("first-run — defer to §3")
        return 0

    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return _rederive(2, f"contract-moved — profile is not valid JSON ({exc})")
    if not isinstance(profile, dict):
        return _rederive(2, "contract-moved — profile is not an object")

    _verdict(1, "current", "profile present")

    schema_version = profile.get("schema_version")
    if (isinstance(schema_version, bool) or
            schema_version not in _schema_versions(clodex_home)):
        return _rederive(2, f"contract-moved — schema_version {schema_version!r} is outside the schema enum")
    _verdict(2, "current", f"schema_version {schema_version}")

    bootstrap = profile.get("bootstrap")
    if bootstrap is None:
        return _rederive(5, "bootstrap missing")
    if not isinstance(bootstrap, dict):
        return _rederive(5, "bootstrap is not an object")

    # Keep structural problems that do not prevent the currency comparisons
    # until question 5.  In particular, an extra bootstrap key must not hide
    # the required skill-before-fingerprint ordering.
    root_problem = _exact_keys(bootstrap, BOOTSTRAP_KEYS, "bootstrap")
    if "clodex_version" not in bootstrap:
        return _rederive(5, root_problem or "missing key 'clodex_version' in bootstrap")

    recorded_version = _version_value(bootstrap["clodex_version"])
    current_version = _version(clodex_home / "VERSION")
    if recorded_version is None or current_version is None:
        return _rederive(3, "skill-moved — an invalid bootstrap or VERSION semver")
    # Compare the (MAJOR, MINOR) pair: patch-insensitive, but a MAJOR move is
    # never "the same minor" — 1.4.0 against 0.4.0 is incompatible drift.
    if recorded_version[1:3] != current_version[1:3]:
        detail = (
            f"skill-moved — recorded {recorded_version[0]}, current {current_version[0]}"
        )
        if worktree:
            _verdict(3, "recorded", detail + " (worktree; not enforced)")
        else:
            return _rederive(3, detail)
    else:
        _verdict(3, "current", f"skill major.minor {current_version[1]}.{current_version[2]}")

    if "repo_fingerprint" not in bootstrap:
        return _rederive(5, root_problem or "missing key 'repo_fingerprint' in bootstrap")
    if not isinstance(bootstrap["repo_fingerprint"], str):
        return _rederive(4, "repo-moved — bootstrap.repo_fingerprint is not a string")
    if not FINGERPRINT.fullmatch(bootstrap["repo_fingerprint"]):
        return _rederive(4, "repo-moved — bootstrap.repo_fingerprint is not sha256:<64 lowercase hex>")

    # This is the sole recompute.  inspect_repo derives both results from its
    # one MARKERS pass, and this checker never implements a second probe.
    _recomputed_inspected, current_fingerprint = inspect_repo.probe(repo)
    if bootstrap["repo_fingerprint"] != current_fingerprint:
        detail = (
            f"repo-moved — recorded {bootstrap['repo_fingerprint']}, "
            f"current {current_fingerprint}"
        )
        if worktree:
            _verdict(4, "recorded", detail + " (worktree; not enforced)")
        else:
            return _rederive(4, detail)
    else:
        _verdict(4, "current", "repo fingerprint")

    problem = _check_bootstrap(bootstrap)
    if problem:
        return _rederive(5, problem)
    _verdict(5, "current", "bootstrap inspected coverage")

    if worktree:
        tracked = _git(repo, "ls-files", "--error-unmatch", ".clodex/profile.json")
        if tracked.returncode != 0:
            _verdict(6, "stop", "worktree profile is untracked")
            return 2
        _verdict(6, "current", "worktree profile is tracked")
    else:
        _verdict(6, "current", "not a linked worktree")
    return 0


def _version_value(value):
    match = SEMVER.fullmatch(value) if isinstance(value, str) else None
    if not match:
        return None
    return (value, int(match.group(1)), int(match.group(2)))


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    return check(args[0], args[1])


if __name__ == "__main__":
    raise SystemExit(main())

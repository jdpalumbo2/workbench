#!/usr/bin/env python3
"""Inspect the repository markers used by the clodex bootstrap contract.

The marker tuple is deliberately the only vocabulary definition.  ``probe``
builds the inspected records and the fingerprint from that same pass; callers
must not implement a second probe.

Usage:
    python3 inspect_repo.py <repo> [--date YYYY-MM-DD] [--json]
"""

import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


# Appendix A: names and order are contract data.  Additions or reorderings
# require a minor VERSION bump.
MARKERS = (
    "package.json",
    "pyproject.toml",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    "tox.ini",
    "vercel.json",
    "railway.json",
    "fly.toml",
    ".nvmrc",
    ".tool-versions",
    ".python-version",
    "go.mod",
    "Cargo.toml",
    "requirements.txt",
    "setup.py",
    "tests/",
    ".github/workflows",
    ".gcloudignore",
    ".dockerignore",
    ".vercelignore",
    ".npmignore",
    "CHANGELOG.md",
    "js-lockfile",
    "package.json#scripts",
    "package.json#engines",
    ".github/workflows#files",
    "pyproject.toml#requires-python",
)

VALUE_MARKERS = frozenset({
    "package.json#scripts",
    "package.json#engines",
    ".github/workflows#files",
    "pyproject.toml#requires-python",
})


def _package_data(repo):
    path = repo / "package.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _requires_python(path):
    """Return project.requires-python, with a Python 3.9 fallback."""
    if not path.is_file():
        return None
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        tomllib = None

    if tomllib is not None:
        try:
            with path.open("rb") as stream:
                document = tomllib.load(stream)
            project = document.get("project", {})
            value = project.get("requires-python")
            return value if isinstance(value, str) else None
        except (OSError, ValueError, TypeError):
            pass

    # This fallback only needs the literal project field used by the contract;
    # it intentionally does not try to become a TOML parser.
    text = path.read_text(encoding="utf-8", errors="replace")
    in_project = False
    for line in text.splitlines():
        section = re.match(r"^\s*\[([^]]+)\]\s*$", line)
        if section:
            in_project = section.group(1).strip() == "project"
            continue
        if in_project:
            match = re.match(r"^\s*requires-python\s*=\s*(['\"])(.*?)\1\s*(?:#.*)?$", line)
            if match:
                return match.group(2)
    return None


def _probe_marker(repo, marker, package, workflow_files):
    if marker in VALUE_MARKERS:
        if marker == "package.json#scripts":
            value = package.get("scripts") if package is not None else None
            if isinstance(value, dict):
                return True, ",".join(sorted(str(name) for name in value))
            return False, None
        if marker == "package.json#engines":
            value = package.get("engines") if package is not None else None
            if isinstance(value, dict):
                pairs = [f"{name}={value[name]}" for name in sorted(value)]
                return True, ",".join(pairs)
            return False, None
        if marker == ".github/workflows#files":
            directory = repo / ".github" / "workflows"
            if not directory.is_dir():
                return False, None
            return True, ",".join(workflow_files)
        value = _requires_python(repo / "pyproject.toml")
        return (value is not None), value

    if marker == "js-lockfile":
        present = any((repo / name).is_file() for name in (
            "package-lock.json", "yarn.lock", "pnpm-lock.yaml"
        ))
    elif marker.endswith("/"):
        present = (repo / marker.rstrip("/")).is_dir()
    elif marker == ".github/workflows":
        present = (repo / ".github" / "workflows").is_dir()
    else:
        present = (repo / marker).exists()
    return present, None


def canonical_serialization(inspected):
    """Serialize inspected records exactly as Appendix A specifies."""
    by_marker = {item["marker"]: item for item in inspected}
    lines = []
    for marker in MARKERS:
        item = by_marker[marker]
        value = item["value"] if item["value"] is not None else ""
        lines.append(f"{marker}\t{1 if item['present'] else 0}\t{value}")
    return "\n".join(lines)


def fingerprint(inspected):
    serialized = canonical_serialization(inspected).encode("utf-8")
    return "sha256:" + hashlib.sha256(serialized).hexdigest()


def probe(repo):
    """Return ``(inspected, repo_fingerprint)`` from one marker pass."""
    repo = Path(repo).resolve()
    package = _package_data(repo)
    workflow_dir = repo / ".github" / "workflows"
    workflow_files = (
        sorted(path.name for path in workflow_dir.iterdir() if path.is_file())
        if workflow_dir.is_dir() else []
    )

    inspected = []
    for marker in MARKERS:
        present, value = _probe_marker(repo, marker, package, workflow_files)
        inspected.append({"marker": marker, "present": present, "value": value})
    return inspected, fingerprint(inspected)


def _date(value):
    try:
        datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD")
    return value


def _summary(inspected, stream=None):
    stream = stream or sys.stdout
    for item in inspected:
        state = "present" if item["present"] else "absent"
        if item["present"] and item["value"] is not None:
            print(f"{item['marker']}: {state} ({item['value']})", file=stream)
        else:
            print(f"{item['marker']}: {state}", file=stream)


def _git_line(repo, *args):
    try:
        result = subprocess.run(
            ["git", "-C", str(repo)] + list(args),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() or None if result.returncode == 0 else None


def _interview_aids(repo, stream=None):
    """Print the details the §3 interview fills fields from — pin CONTENTS,
    recent tags, the default branch, the package version. Deliberately outside
    the marker vocabulary: none of this enters `inspected` or moves the
    fingerprint; it exists so 'anything you can read, do not ask about' still
    holds for runtimes, commands.install, version source, and tag format."""
    stream = stream or sys.stdout
    print("-- interview aids (not fingerprinted) --", file=stream)
    for name in (".nvmrc", ".tool-versions", ".python-version"):
        path = repo / name
        if path.is_file():
            content = " ".join(path.read_text(encoding="utf-8").split())
            print(f"{name} contents: {content}", file=stream)
    package = _package_data(repo)
    if package is not None:
        if package.get("version"):
            print(f"package.json#version: {package['version']}", file=stream)
        scripts = package.get("scripts")
        if isinstance(scripts, dict):
            for key in sorted(scripts):
                print(f"package.json#scripts.{key}: {scripts[key]}", file=stream)
    for name in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml"):
        if (repo / name).is_file():
            print(f"lockfile: {name}", file=stream)
    if package is not None and package.get("packageManager"):
        print(f"package.json#packageManager: {package['packageManager']}", file=stream)
    version_file = repo / "VERSION"
    if version_file.is_file():
        content = " ".join(version_file.read_text(encoding="utf-8").split())
        print(f"VERSION contents: {content}", file=stream)
    pyproject = repo / "pyproject.toml"
    if pyproject.is_file():
        match = re.search(r"^\s*version\s*=\s*(['\"])(.*?)\1", pyproject.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            print(f"pyproject.toml#version: {match.group(2)}", file=stream)
    tags = _git_line(repo, "tag", "--list", "--sort=-creatordate")
    if tags:
        print("recent tags: " + ", ".join(tags.splitlines()[:5]), file=stream)
    remotes = _git_line(repo, "remote")
    for remote in (remotes.splitlines() if remotes else []):
        head = _git_line(repo, "symbolic-ref", "--quiet", "--short",
                         f"refs/remotes/{remote}/HEAD")
        if head:
            print(f"default branch: {head.split('/', 1)[-1]}", file=stream)
            break
    else:
        for candidate in ("main", "master"):
            probe_head = _git_line(repo, "show-ref", "--verify",
                                   f"refs/heads/{candidate}")
            if probe_head:
                print(f"default branch: {candidate}", file=stream)
                break


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("--date", type=_date,
                        default=datetime.date.today().isoformat())
    parser.add_argument("--json", action="store_true", dest="machine")
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    if not repo.is_dir():
        parser.error(f"repo is not a directory: {repo}")
    inspected, repo_fingerprint = probe(repo)
    artifact = {
        "derived_at": args.date,
        "inspected": inspected,
        "repo_fingerprint": repo_fingerprint,
    }
    output = repo / ".clodex" / f"bootstrap-{args.date}.inspection.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")

    if args.machine:
        _summary(inspected, sys.stderr)
        _interview_aids(repo, sys.stderr)
        print(json.dumps({
            "inspected": inspected,
            "repo_fingerprint": repo_fingerprint,
        }, separators=(",", ":")))
    else:
        _summary(inspected)
        _interview_aids(repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

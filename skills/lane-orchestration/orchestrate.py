#!/usr/bin/env python3
"""Print and validate one lane-orchestration run without executing it.

This module is deliberately a dry-run control surface for batch 3.  It owns
the deterministic parts of the topology: schema and graph validation, the
reviewable command plan, the 15-gate catalogue, and park prediction.  It
imports the batch-1/2 state and quota modules by path so this file can be
installed as a standalone skill script without relying on ``sys.path``.

There is no process creation in this module.  The command lines printed here
are the commands a later live implementation would use; ``--unpark`` only
records the answer through the state engine and then reports scheduling state.
Keeping the command builder separate from execution makes the boundary easy
to test and keeps a dry-run useful as an operator review artifact.

Stdlib only.  Exit codes are 0 for a clean printed plan, 1 for a refused
plan/ledger/answer, and 2 for command-line usage errors.
"""

import argparse
import hashlib
import importlib.util
import inspect
import json
import os
import re
import shlex
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
STATE_PATH = HERE / "orchestrator_state.py"
QUOTA_PATH = HERE / "quota.py"
GATE_MAP_PATH = HERE / "reference" / "gate-map.json"
CENSUS_PATH = REPO_ROOT / "docs" / "2026-09-01-orchestration-evidence" / "clodex-gate-census.md"
RUNNER_PATH = REPO_ROOT / "skills" / "clodex" / "runner" / "run-codex.sh"
WRAPPER_PATH = HERE / "dispatch_wrapper.py"

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_USAGE = 2


def _load_by_path(name, path):
    """Load a sibling artifact by path, as the test harness does."""
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError("cannot load %s" % path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# These imports are intentionally explicit.  They are the committed state and
# quota APIs from earlier batches, not copies hidden behind a package import.
orchestrator_state = _load_by_path("lane_orchestrator_state", STATE_PATH)
quota = _load_by_path("lane_orchestrator_quota", QUOTA_PATH)


# The table is code, rather than a setting read from a lane, because changing
# an allowlist changes the blast radius of a stage.  The model names and effort
# values mirror plan B.4; QA entries are included so the complete dispatch
# vocabulary is visible in one reviewable constant.
STAGE_TABLE = {
    "brief": {
        "allowlist": ["Read", "Glob", "Grep", "Write", "Edit"],
        "model": "claude-opus-5",
        "effort": "high",
    },
    "plan": {
        "allowlist": ["Read", "Glob", "Grep", "Write", "Edit", "Bash(git:*)"],
        "model": "claude-sonnet-5",
        "effort": "medium",
    },
    "build": {
        "allowlist": ["Read", "Glob", "Grep", "Write", "Edit", "Bash(git:*)", "Bash(python3:*)"],
        "model": "claude-sonnet-5",
        "effort": "medium",
    },
    "verify": {
        "allowlist": ["Read", "Glob", "Grep", "Bash(git:*)", "Bash(python3:*)"],
        "model": "claude-sonnet-5",
        "effort": "medium",
    },
    "research": {
        "allowlist": ["Read", "Glob", "Grep", "Bash(git:*)"],
        "model": "gpt-5.6-terra",
        "effort": "high",
    },
    "write": {
        "allowlist": ["Read", "Glob", "Grep", "Write", "Edit"],
        "model": "claude-sonnet-5",
        "effort": "medium",
    },
    "qa-release-diff": {
        "allowlist": ["Read", "Glob", "Grep", "Bash(git:*)"],
        "model": "gpt-5.6-sol",
        "effort": "high",
    },
    "qa-client-artifact": {
        "allowlist": ["Read", "Glob", "Grep"],
        "model": "claude-opus-5",
        "effort": "high",
    },
    "qa-acceptance": {
        "allowlist": ["Read", "Glob", "Grep"],
        "model": "claude-opus-5",
        "effort": "high",
    },
    "qa-morning-summary": {
        "allowlist": ["Read", "Glob", "Grep"],
        "model": "claude-sonnet-5",
        "effort": "medium",
    },
}


GATE_7_RULES = (
    "FULL v8 attribution rules: join snapshot approvals to raw source events "
    "by position over BOTH approval:granted and plan:approved in seq order; "
    "take by/revoked from the snapshot and seq/authorization_ref from the raw "
    "event. Every unattended window is fresh for each headless dispatch and "
    "is half-open (dispatch watermark, park/complete watermark]; by:\"user\" in "
    "any such window fails, while an approval in an attended gap passes. Gate "
    "consumption is by:\"mandate\" only and cites a standing run-scoped mandate. "
    "by:\"orchestrator\" is legal only on the mandate grant, whose "
    "authorization_ref is <repo-relative-path>@<40-hex-commit-sha>; the git "
    "check must prove that the commit exists, contains the artifact, and is an "
    "ancestor of the lane run's git.start_head. {scope:\"handoff\", by:\"ship\"} passes; "
    "ship elsewhere fails. Accepted/rejected finding dispositions in a "
    "dispatched lane require explicit by. Revoked approvals count for nothing. "
    "Any other attribution or an orchestrator consuming a gate fails closed."
)


GATES = (
    ("1", "arithmetic", "Via quota functions, BOTH Codex windows are known and under their global ceilings; null means refuse fan-out.",
     (("budget.codex_weekly_pct_ceiling", "codex_weekly_pct_ceiling"),
      ("budget.codex_5h_pct_ceiling", "codex_5h_pct_ceiling"))),
    ("2", "arithmetic", "Claude dollars are under the per-lane ceiling; Codex is enforced only by global windows. There is deliberately no per-lane Codex ceiling (r5-F004).",
     (("budget.claude_usd_ceiling", "claude_usd_ceiling"),
      ("budget.per_lane_usd_ceiling", "per_lane_usd_ceiling"))),
    ("3", "arithmetic", "Claude modelUsage keys are inside the stage allowlist; Codex model selection is unverifiable at runtime.",
     (("mode", "mode"),)),
    ("4", "arithmetic", "Worker outcome comes from the envelope and exit status, never worker prose.",
     (("mode", "mode"),)),
    ("5", "arithmetic", "The lane's state advanced beyond the dispatch stage.",
     (("mode", "mode"),)),
    ("6a", "arithmetic", "counts.py reports no open findings.",
     (("mode", "mode"),)),
    ("6b", "arithmetic", "No blocker/high finding was accepted under by:mandate.",
     (("mode", "mode"),)),
    ("7", "arithmetic", GATE_7_RULES,
     (("mode", "mode"),)),
    ("8", "arithmetic", "Recompute the owned-path boundary independently against the lane diff.",
     (("mode", "mode"),)),
    ("9", "arithmetic", "The report's first line equals the dispatched run id.",
     (("mode", "mode"),)),
    ("10", "arithmetic", "Report counts match each named generator: counts.py, gate log, and git.",
     (("mode", "mode"),)),
    ("11", "arithmetic", "The direction-gate answer and six shape-card fields agree between brief and plan.",
     (("lanes[*].direction_gate", "direction_gate"),)),
    ("12", "artifact", "The lane report contains every section required by the brief's §16.",
     (("mode", "mode"),)),
    ("13", "tier 4", "Held-out acceptance detects but does not prevent; NOT BUILT (B.13 step 8).",
     (("mode", "mode"),)),
    ("14", "prose / human / morning", "Release authorization and debt acceptance remain human morning gates.",
     (("mode", "mode"),)),
    ("15", "arithmetic", "The gate map is current, bijective with the blocking census, and anchors are machine-checked.",
     (("mode", "mode"),)),
)


def _sha8(path):
    """Return the short content hash used in operator-facing source labels."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]


def _format_command(argv):
    return shlex.join([str(item) for item in argv])


def _format_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


class PlanRefusal(Exception):
    """A schema or semantic graph defect that refuses the run."""


def _normalized_identity(value):
    """Normalize a path-like graph identity without touching the filesystem."""
    normalized = os.path.normpath(value)
    if normalized == os.path.sep:
        return normalized
    return normalized.rstrip(os.path.sep) or os.path.sep


def validate_semantic_graph(plan):
    """Validate exact-key graph invariants and return stable topological order.

    Claims intentionally use string equality.  The router owns any richer
    resource policy; inventing glob or path-overlap behavior here would make a
    dry-run disagree with the router that ultimately owns the claim ledger.
    """
    lanes = plan.get("lanes") if isinstance(plan, dict) else None
    if not isinstance(lanes, list):
        raise PlanRefusal("semantic graph: lanes is not an array")

    by_id = {}
    for lane in lanes:
        lane_id = lane.get("id") if isinstance(lane, dict) else None
        if lane_id in by_id:
            raise PlanRefusal("semantic graph: duplicate lane id %r" % lane_id)
        by_id[lane_id] = lane

    for lane in lanes:
        lane_id = lane["id"]
        for dependency in lane.get("depends_on", []):
            if dependency not in by_id:
                raise PlanRefusal(
                    "semantic graph: lane %r depends_on unknown lane %r"
                    % (lane_id, dependency)
                )

    owners = {}
    for field in ("worktree", "branch"):
        owners.clear()
        for lane in lanes:
            value = _normalized_identity(lane[field])
            if value in owners:
                raise PlanRefusal(
                    "semantic graph: %s collision between lanes %r and %r (%s)"
                    % (field, owners[value], lane["id"], value)
                )
            owners[value] = lane["id"]

    claim_owners = {}
    for lane in lanes:
        for claim in lane.get("claims", []):
            if claim in claim_owners and claim_owners[claim] != lane["id"]:
                raise PlanRefusal(
                    "semantic graph: duplicate exact-key claim %r across lanes %r and %r"
                    % (claim, claim_owners[claim], lane["id"])
                )
            claim_owners[claim] = lane["id"]

    # Kahn's algorithm with input-order tie breaking gives reproducible plans.
    position = {lane["id"]: index for index, lane in enumerate(lanes)}
    indegree = {lane["id"]: len(set(lane.get("depends_on", []))) for lane in lanes}
    children = {lane["id"]: [] for lane in lanes}
    for lane in lanes:
        for dependency in set(lane.get("depends_on", [])):
            children[dependency].append(lane["id"])
    ready = sorted((lane_id for lane_id, degree in indegree.items() if degree == 0),
                   key=position.get)
    order = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for child in sorted(children[current], key=position.get):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
        ready.sort(key=position.get)
    if len(order) != len(lanes):
        remaining = sorted((lane_id for lane_id, degree in indegree.items() if degree),
                           key=position.get)
        raise PlanRefusal("semantic graph: dependency cycle involving %s" % ", ".join(remaining))
    return [by_id[lane_id] for lane_id in order]


# Short aliases are useful to callers embedding the dry-run checker and keep
# the public names unsurprising without duplicating implementations.
validate_graph = validate_semantic_graph
topological_lanes = validate_semantic_graph
topological_sort = validate_semantic_graph
validate_semantic_plan = validate_semantic_graph


_ATTRIBUTIONS = frozenset(("user", "mandate", "orchestrator", "ship"))
_MANDATE_ACTIONS = frozenset((
    "finding-disposition", "plan-approval", "direction-approval",
))


def _snapshot_run_id(snapshot):
    run = snapshot.get("run")
    if isinstance(run, dict):
        run = run.get("id", run.get("run"))
    if isinstance(run, str):
        return run
    for key in ("run_id", "manifest_run", "manifest_id"):
        if isinstance(snapshot.get(key), str):
            return snapshot[key]
    manifest = snapshot.get("manifest")
    if isinstance(manifest, dict):
        value = manifest.get("run", manifest.get("id"))
        if isinstance(value, str):
            return value
    return None


def _start_head(snapshot):
    git = snapshot.get("git")
    if isinstance(git, dict) and isinstance(git.get("start_head"), str):
        return git["start_head"]
    for key in ("start_head", "git_start_head"):
        if isinstance(snapshot.get(key), str):
            return snapshot[key]
    run = snapshot.get("run")
    if isinstance(run, dict):
        git = run.get("git")
        if isinstance(git, dict) and isinstance(git.get("start_head"), str):
            return git["start_head"]
    return None


def _approval_sources(events):
    sources = [event for event in events if isinstance(event, dict) and
               event.get("e") in ("approval:granted", "plan:approved")]
    try:
        return sorted(sources, key=lambda event: event["seq"])
    except (KeyError, TypeError):
        return None


def _window_records(window_receipts, lane=None):
    """Normalize the small window receipt vocabulary used by callers/tests."""
    value = window_receipts
    if isinstance(value, dict):
        for key in ("windows", "window_receipts", "receipts"):
            if key in value:
                value = value[key]
                break
        else:
            selected = value.get(lane) if lane is not None else None
            value = selected if isinstance(selected, (list, tuple, dict)) else [value]
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return None
    result = []
    for item in value:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            item = {"dispatch_watermark": item[0], "park_watermark": item[1]}
        if not isinstance(item, dict):
            return None
        item_lane = item.get("lane", item.get("lane_id"))
        if item_lane is not None and lane is not None and item_lane != lane:
            continue
        start = None
        end = None
        for key in ("dispatch_watermark", "dispatch_last_seq", "lane_last_seq_at_dispatch",
                    "dispatch_seq", "dispatch", "start", "from_seq"):
            if key in item:
                start = item[key]
                break
        for key in ("park_watermark", "complete_watermark", "lane_last_seq_at_park",
                    "lane_last_seq_at_complete", "park_seq", "complete_seq", "park",
                    "complete", "end", "to_seq"):
            if key in item:
                end = item[key]
                break
        if (isinstance(start, bool) or not isinstance(start, int) or start < 0 or
                isinstance(end, bool) or not isinstance(end, int) or end < start):
            return None
        result.append((start, end))
    return result


def _in_unattended_window(seq, windows):
    return any(start < seq <= end for start, end in windows)


def _authorization_ref(value):
    if not isinstance(value, str) or "@" not in value:
        return None
    path, commit = value.rsplit("@", 1)
    if (not path or path.startswith("/") or "\x00" in path or
            any(part in ("", ".", "..") for part in path.split("/")) or
            not re.fullmatch(r"[0-9a-f]{40}", commit)):
        return None
    return path, commit


def _git_check_ok(git_check, path, commit, start_head, reference):
    """Ask the injected oracle without starting another program here."""
    if not callable(git_check) or not isinstance(start_head, str) or not start_head:
        return False
    try:
        signature = inspect.signature(git_check)
        positional = [parameter for parameter in signature.parameters.values()
                      if parameter.kind in (parameter.POSITIONAL_ONLY,
                                            parameter.POSITIONAL_OR_KEYWORD)]
        variadic = any(parameter.kind == parameter.VAR_POSITIONAL
                       for parameter in signature.parameters.values())
        if variadic or len(positional) >= 3:
            result = git_check(path, commit, start_head)
        elif len(positional) == 2:
            names = [parameter.name.lower() for parameter in positional]
            if any(token in names[0] for token in ("path", "artifact")) and any(
                    token in names[1] for token in ("sha", "commit", "object")):
                result = git_check(path, commit)
            else:
                result = git_check(reference, start_head)
        else:
            result = git_check(reference)
    except (TypeError, ValueError, OSError):
        return False
    if isinstance(result, dict):
        # A dict lets a fixture say which part failed.  All three facts are
        # required; accepting a dict with only one truthy convenience field
        # would turn a commit-existence check into an ancestry check by name.
        aliases = (
            ("commit_exists", "exists", "commit"),
            ("contains_artifact", "contains", "artifact"),
            ("ancestor", "is_ancestor", "ancestral"),
        )
        return all(any(key in result and result[key] is True for key in group)
                   for group in aliases)
    if isinstance(result, (tuple, list)):
        return len(result) >= 3 and all(item is True for item in result[:3])
    return result is True


def _action_for_scope(scope):
    return {
        "plan": frozenset(("plan-approval",)),
        "direction": frozenset(("direction-approval",)),
        "finding": frozenset(("finding-disposition",)),
        "finding-disposition": frozenset(("finding-disposition",)),
        "plan-approval": frozenset(("plan-approval",)),
        "direction-approval": frozenset(("direction-approval",)),
    }.get(scope, frozenset())


def _gate7_result(events, snapshot, window_receipts, run_plan_sha, git_check):
    """Return ``(passed, reasons)`` for the v8 approval-attribution gate.

    Snapshot approvals are intentionally not trusted for their source
    position.  The lane reducer promotes neither ``seq`` nor
    ``authorization_ref``, so this function first enumerates both approval
    event types in sequence order and then joins them positionally.  The
    injected git oracle supplies the three repository facts needed for a
    mandate grant; keeping it injected makes this gate pure and testable.
    """
    reasons = []
    if not isinstance(events, list) or not isinstance(snapshot, dict):
        return False, ["events and snapshot must be objects of the expected shape"]
    approvals = snapshot.get("approvals")
    sources = _approval_sources(events)
    if not isinstance(approvals, list) or sources is None:
        return False, ["approval source events are malformed"]
    if len(approvals) != len(sources):
        return False, ["snapshot approvals do not join one-for-one with both raw approval event types"]

    lane = snapshot.get("lane") if isinstance(snapshot.get("lane"), str) else None
    windows = _window_records(window_receipts, lane)
    if windows is None:
        return False, ["unattended window receipts are malformed"]
    dispatch_events = [event for event in events
                       if isinstance(event, dict) and event.get("e") == "lane:dispatched"]
    dispatched = bool(windows) or bool(dispatch_events)
    if dispatch_events and len(windows) < len(dispatch_events):
        return False, ["every headless dispatch must have a fresh unattended window receipt"]
    start_head = _start_head(snapshot)
    run_id = _snapshot_run_id(snapshot)
    standing_mandates = []
    joined = list(zip(approvals, sources))
    revoked_mandate_seen = False

    for approval, source in joined:
        if not isinstance(approval, dict) or not isinstance(source.get("seq"), int):
            reasons.append("approval join has no integer raw sequence")
            continue
        seq = source["seq"]
        by = approval.get("by")
        scope = approval.get("scope", source.get("scope", "plan"))
        revoked = approval.get("revoked")
        if revoked:
            if by == "orchestrator" and scope == "mandate":
                revoked_mandate_seen = True
            continue
        if by not in _ATTRIBUTIONS:
            reasons.append("approval at seq %s has unknown attribution %r" % (seq, by))
            continue
        if by == "user":
            if _in_unattended_window(seq, windows):
                reasons.append("by:user approval at seq %s is inside an unattended window" % seq)
            # An attended approval is a legitimate gap between windows.  It is
            # not used as a substitute for a mandate in a headless window.
            continue
        if by == "ship":
            if scope != "handoff":
                reasons.append("by:ship approval at seq %s is outside scope:handoff" % seq)
            continue
        if by == "orchestrator":
            if scope != "mandate":
                reasons.append("by:orchestrator consumed a gate at seq %s" % seq)
                continue
            reference = source.get("authorization_ref")
            parsed = _authorization_ref(reference)
            if parsed is None:
                reasons.append("mandate at seq %s has no valid authorization_ref" % seq)
                continue
            if source.get("plan_hash") is not None:
                reasons.append("run-scoped mandate at seq %s has a non-null plan_hash" % seq)
                continue
            if not isinstance(run_id, str) or source.get("run") != run_id:
                reasons.append("mandate at seq %s names the wrong run" % seq)
                continue
            if source.get("run_plan_sha") is not None and source.get("run_plan_sha") != run_plan_sha:
                reasons.append("mandate at seq %s names the wrong run-plan sha" % seq)
                continue
            actions = approval.get("actions")
            if not actions:
                actions = source.get("actions")
            if not isinstance(actions, list) or not actions or not all(action in _MANDATE_ACTIONS for action in actions):
                reasons.append("mandate at seq %s grants a verb outside the three allowed verbs" % seq)
                continue
            if not _git_check_ok(git_check, parsed[0], parsed[1], start_head, reference):
                reasons.append("mandate at seq %s failed commit, artifact, or ancestry verification" % seq)
                continue
            standing_mandates.append((approval, set(actions)))
            continue
        # by:mandate can consume a plan or direction approval, but never grant
        # the mandate itself.  Its standing authority is checked below.
        if by == "mandate" and scope == "mandate":
            reasons.append("by:mandate cannot be the mandate grant")

    def has_authority(scope):
        wanted = _action_for_scope(scope)
        return bool(wanted) and any(wanted.intersection(actions) for _approval, actions in standing_mandates)

    for approval, source in joined:
        if not isinstance(approval, dict) or approval.get("revoked"):
            continue
        by = approval.get("by")
        scope = approval.get("scope", source.get("scope", "plan"))
        if by == "mandate":
            if scope == "mandate" or not has_authority(scope):
                reasons.append("by:mandate approval at seq %s lacks a standing grant" % source.get("seq"))
            elif source.get("authorization_ref") is not None and not isinstance(source.get("authorization_ref"), str):
                reasons.append("by:mandate approval at seq %s has malformed authorization_ref" % source.get("seq"))
        elif by == "orchestrator" and scope == "mandate":
            # It was validated in the first pass.
            if not any(candidate is approval for candidate, _actions in standing_mandates):
                reasons.append("mandate grant at seq %s is not standing" % source.get("seq"))
        elif by == "orchestrator":
            reasons.append("by:orchestrator consumed a gate at seq %s" % source.get("seq"))

    # Disposition attribution is deliberately sourced from raw events: the
    # current clodex snapshot does not promote the optional ``by`` field.
    findings = snapshot.get("findings", [])
    raw_dispositions = {
        event.get("id"): event for event in events
        if isinstance(event, dict) and event.get("e") == "finding:disposed"
    }
    for finding in findings if isinstance(findings, list) else []:
        if not isinstance(finding, dict) or finding.get("disposition") not in ("accepted", "rejected"):
            continue
        if not dispatched:
            continue
        source = raw_dispositions.get(finding.get("id"), {})
        if "by" not in source and "by" in finding:
            source = finding
        by = source.get("by")
        if by not in _ATTRIBUTIONS:
            reasons.append("finding disposition %r has no explicit valid by" % finding.get("id"))
        elif by != "mandate" or not has_authority("finding-disposition"):
            reasons.append("finding disposition %r is not consumed by a standing mandate" % finding.get("id"))

    if dispatched and revoked_mandate_seen and not standing_mandates:
        reasons.append("the only run-scoped mandate was revoked")

    return not reasons, reasons


def evaluate_gate_7(events=None, snapshot=None, window_receipts=None, run_plan_sha=None,
                    git_check=None, return_reasons=False, **aliases):
    """Evaluate gate 7; default return is a bool and failures are fail-closed."""
    # The contract describes these as concepts rather than an API package.  A
    # few explicit keyword aliases keep the pure gate easy to embed while
    # preserving one implementation and one fail-closed result.
    events = aliases.get("lane_events", events)
    snapshot = aliases.get("lane_snapshot", snapshot)
    window_receipts = aliases.get("windows", aliases.get("orchestrator_windows", window_receipts))
    run_plan_sha = aliases.get("run_plan_hash", run_plan_sha)
    git_check = aliases.get("git_check_callback", git_check)
    passed, reasons = _gate7_result(events, snapshot, window_receipts, run_plan_sha, git_check)
    return (passed, reasons) if return_reasons else passed


# Public spellings kept together so callers can use either the prose gate name
# or the Pythonic one without creating separate implementations.
gate7_approval_attribution = evaluate_gate_7
gate_7 = evaluate_gate_7
check_gate_7 = evaluate_gate_7
gate7 = evaluate_gate_7
evaluate_gate7 = evaluate_gate_7
gate7_attribution = evaluate_gate_7
check_gate7 = evaluate_gate_7
GATE_SPECS = GATES


_CENSUS_COMPONENTS = {
    "clodex-audit skill": "skills/clodex-audit/SKILL.md",
    "clodex-build": "skills/clodex-build/SKILL.md",
    "clodex-plan/SKILL.md": "skills/clodex-plan/SKILL.md",
    "clodex-ship": "skills/clodex-ship/SKILL.md",
    "clodex-verify": "skills/clodex-verify/SKILL.md",
}

_CONTRACT_CENSUS_COMPONENTS = {
    29: "skills/clodex/templates/scenario-card.md",
    217: "skills/clodex/runner/run-codex.sh",
    271: "skills/clodex/state/reducer.py",
}


def _census_gate_keys(path=None):
    """Return canonical map keys from the census's 28 blocking headings.

    The census uses short, human-facing component labels while the machine map
    names the cited repository files.  The explicit aliases preserve the
    census identity without weakening the map's source-file anchor check.
    ``None`` means the optional census is absent; the committed map remains
    the artifact in that case.
    """
    path = Path(CENSUS_PATH if path is None else path)
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PlanRefusal("cannot read gate census: %s" % exc)
    keys = set()
    for match in re.finditer(r"(?m)^### `([^`]+)` L(\d+)\b", text):
        label, line = match.group(1), int(match.group(2))
        component = _CENSUS_COMPONENTS.get(label)
        if component is None and label == "clodex Codex runner + contract layer":
            component = _CONTRACT_CENSUS_COMPONENTS.get(line)
        if component is None:
            component = label
        keys.add((component, line))
    return keys


def _load_gate_map():
    """Read and machine-check the committed, judgment-bearing gate map."""
    try:
        value = json.loads(GATE_MAP_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise PlanRefusal("cannot read gate-map.json: %s" % exc)
    rows = value.get("gates") if isinstance(value, dict) else None
    if not isinstance(rows, list) or len(rows) != 28:
        raise PlanRefusal("gate-map.json must contain exactly 28 rows")
    required = {"component", "census_line", "gate", "anchor", "verdict", "covered_by"}
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or not required.issubset(row):
            raise PlanRefusal("gate-map.json has a malformed row")
        key = (row["component"], row["census_line"])
        if key in seen:
            raise PlanRefusal("gate-map.json repeats census key %r" % (key,))
        seen.add(key)
        source = REPO_ROOT / row["component"]
        try:
            source_text = source.read_text(encoding="utf-8")
        except OSError as exc:
            raise PlanRefusal("gate-map anchor source is unreadable: %s" % exc)
        if row["anchor"] not in source_text:
            raise PlanRefusal(
                "gate-map anchor is stale: %s L%s %r"
                % (row["component"], row["census_line"], row["anchor"])
            )
    census_keys = _census_gate_keys()
    if census_keys is not None and seen != census_keys:
        missing = sorted(census_keys - seen)
        extra = sorted(seen - census_keys)
        raise PlanRefusal(
            "gate-map.json is not bijective with the blocking census "
            "(missing=%s extra=%s)" % (missing, extra)
        )
    return value


load_gate_map = _load_gate_map


def _read_plan(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            plan = json.load(handle)
    except (OSError, ValueError) as exc:
        raise PlanRefusal("cannot read run-plan %s: %s" % (path, exc))
    try:
        orchestrator_state.validate_run_plan(plan)
    except Exception as exc:
        raise PlanRefusal("run-plan refused by schema: %s" % exc)
    validate_semantic_graph(plan)
    return plan


def _plan_sha(path):
    try:
        return orchestrator_state.compute_run_plan_sha(str(path))
    except Exception as exc:
        raise PlanRefusal(str(exc))


def _ledger_label(plan_path, ledger_dir):
    if ledger_dir is not None:
        return Path(ledger_dir)
    try:
        return Path(orchestrator_state.ledger_dir_for(str(plan_path)))
    except Exception as exc:
        raise PlanRefusal("cannot derive ledger identity: %s" % exc)


def _answer_block(path):
    """Extract only text under an exact ``## Answer:`` park heading."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise PlanRefusal("cannot read park record %s: %s" % (path, exc))
    match = re.search(r"(?m)^## Answer:\s*(?:\n|$)(.*?)(?=^#{1,6}\s|\Z)", text, re.S)
    if not match:
        raise PlanRefusal("park record %s has no ## Answer: block" % path)
    answer = match.group(1).strip()
    if not answer:
        raise PlanRefusal("park record %s has a blank ## Answer: block" % path)
    return answer


def _safe_snapshot(ledger_dir, plan_path, plan_sha):
    """Read optional ledger state without opening or changing a ledger."""
    path = Path(ledger_dir)
    if not path.exists():
        return None
    problem = orchestrator_state.check_ledger_identity(
        str(path), run_plan_path=str(plan_path), run_plan_sha=plan_sha
    )
    if problem:
        raise PlanRefusal(problem)
    try:
        return orchestrator_state.load_snapshot(str(path))
    except Exception as exc:
        raise PlanRefusal("cannot read ledger %s: %s" % (path, exc))


def _stage_settings(stage):
    table = STAGE_TABLE[stage]
    return json.dumps({"permissions": {"allow": table["allowlist"]}},
                      sort_keys=True, separators=(",", ":"))


def _claude_argv(stage, lane, invocation, brief, ledger):
    table = STAGE_TABLE[stage]
    return [
        "claude", "-p", "--permission-mode", "dontAsk", "--output-format", "json",
        "--model", table["model"], "--effort", table["effort"],
        "--settings", _stage_settings(stage), invocation,
    ]


CODEX_STAGE_TABLE = {
    "plan-reviewer": {"model": "gpt-5.6-sol", "effort": "xhigh"},
    "implementer": {"model": "gpt-5.6-luna", "effort": "medium"},
    "code-reviewer": {"model": "gpt-5.6-sol", "effort": "high"},
    "advisor": {"model": "gpt-5.6-terra", "effort": "high"},
}


def _qa_claude_wrapper_argv(stage, lane, run_id, invocation, ledger, op_id):
    """Build an attempt-unique wrapper command for orchestrator-held Claude QA."""
    qa_attempt = Path(ledger) / "qa" / op_id
    envelope = qa_attempt / ("%s.envelope.json" % stage)
    marker = qa_attempt / ("%s.started" % stage)
    command = _claude_argv(stage, lane, invocation, lane["brief"], ledger)
    return [
        "python3", str(WRAPPER_PATH), "--op-id", op_id,
        "--marker", str(marker), "--envelope", str(envelope), "--",
    ] + command


def _park_applies(row, lane):
    """Limit map-derived predictions to stages a lane actually runs."""
    if lane.get("kind") != "repo":
        return False
    if (row.get("component") == "skills/clodex-verify/SKILL.md" and
            "client-artifact" in row.get("gate", "")):
        return bool(lane.get("client_visible"))
    return True


def _stage_invocation(stage, lane, run_id):
    brief = lane["brief"]
    if stage == "plan":
        return "/clodex %s" % brief
    if stage == "build":
        return "/clodex-build, run dir %s/.clodex/%s" % (lane["worktree"], run_id)
    if stage == "verify":
        return "/clodex-verify, run dir %s/.clodex/%s" % (lane["worktree"], run_id)
    return "write %s for lane %s" % (brief, lane["id"])


def _repo_stages(lane):
    return [("plan", "plan-reviewer"), ("build", "implementer"), ("build", "code-reviewer"),
            ("verify", None)]


def _deliverable_stages(lane):
    return [("research", "advisor"), ("write", None)]


def _print_runner_shape(role, repo, run_id, input_label):
    settings = CODEX_STAGE_TABLE[role]
    op_placeholder = "<op_id minted at dispatch>"
    return _format_command([
        "env", "CODEX_MODEL=%s" % settings["model"],
        "CODEX_EFFORT=%s" % settings["effort"],
        "CLODEX_INVOCATION_ID=%s" % op_placeholder,
        "bash", str(RUNNER_PATH), "--role", role, "--repo", repo,
        "--run-id", run_id, "--prompt-file", "<lane-generated at stage time>",
        "--input", input_label, "[--detach]",
    ])


def _print_dispatch_plan(plan, plan_path, plan_sha, lanes, gate_map, ledger_dir):
    run_id = "%s-%s" % (plan["date"], plan_sha[:8])
    print("DISPATCH PLAN — dry-run only")
    print("run id: %s" % run_id)
    print("stage-table@%s" % _sha8(Path(__file__)))
    print("STAGE TABLE (committed constants)")
    for stage, values in STAGE_TABLE.items():
        print("  %-21s model=%-18s effort=%-6s allow=%s" % (
            stage, values["model"], values["effort"], ",".join(values["allowlist"])))
    print("ledger (read-only in dry-run): %s" % ledger_dir)
    for live_check in ("repo existence", "base-sha resolution", "target repo claims ledger"):
        print("LIVE CHECK %-24s SKIPPED (dry-run — live mode enforces)" % live_check)

    for lane in lanes:
        print("\nLANE %s" % lane["id"])
        for key in ("id", "kind", "worktree", "branch", "base", "brief", "depends_on",
                    "claims", "client_visible", "direction_gate"):
            print("  %-16s %s" % (key + ":", _format_value(lane[key])))
        print("  %-16s %s" % ("push:", _format_value(lane.get("push", False))))
        if "acceptance_ref" in lane:
            print("  %-16s %s" % ("acceptance_ref:", lane["acceptance_ref"]))
        print("  STAGES")
        stages = _repo_stages(lane) if lane["kind"] == "repo" else _deliverable_stages(lane)
        printed_claude_stages = set()
        for stage, role in stages:
            # A lane stage can contain both a Claude orchestration prompt and
            # one or more lane-internal Codex rounds.  Build appears twice in
            # the repo sequence because its implementer and reviewer rounds
            # are distinct, but the outer Claude receipt is one stage.
            if stage in ("plan", "build", "verify", "write") and stage not in printed_claude_stages:
                invocation = _stage_invocation(stage, lane, run_id)
                claude = _claude_argv(stage, lane, invocation, lane["brief"], ledger_dir)
                op_placeholder = "<op_id minted at dispatch>"
                envelope = Path(ledger_dir) / "lanes" / lane["id"] / (
                    "%s.%s.envelope.json" % (stage, op_placeholder)
                )
                marker = envelope.with_name("%s.%s.started" % (stage, op_placeholder))
                wrapper = ["python3", str(WRAPPER_PATH), "--op-id", op_placeholder,
                           "--marker", str(marker), "--envelope", str(envelope), "--"] + claude
                print("    %s: wrapper argv: %s" % (stage, _format_command(wrapper)))
                printed_claude_stages.add(stage)
            if role:
                artifact = "<stage artifact>"
                print("    %s: lane-internal Codex runner argv SHAPE: %s" % (
                    stage, _print_runner_shape(role, lane["repo"], run_id, artifact)))

        diff = Path(lane["worktree"]) / "<release-diff>"
        qa_op = "<op_id minted at dispatch>"
        qa_state = Path(ledger_dir) / "qa" / qa_op
        qa_prompt = HERE / "prompts" / "qa-release-diff-review.prompt.md"
        rendered_prompt = qa_prompt.read_text(encoding="utf-8").format(
            lane=lane["id"], branch=lane["branch"], diff_path=str(diff)
        )
        rendered_prompt_path = qa_state / "qa-release-diff-review.prompt.md"
        qa_argv = ["env", "CODEX_MODEL=%s" % CODEX_STAGE_TABLE["code-reviewer"]["model"],
                   "CODEX_EFFORT=%s" % CODEX_STAGE_TABLE["code-reviewer"]["effort"],
                   "CLODEX_INVOCATION_ID=%s" % qa_op,
                   "CLODEX_RUNNER_STATE_DIR=%s" % qa_state, "bash", str(RUNNER_PATH),
                   "--role", "code-reviewer", "--repo", lane["repo"], "--run-id", run_id,
                   "--prompt-file", str(rendered_prompt_path), "--input", str(diff), "--detach"]
        print("  ORCHESTRATOR-HELD QA")
        print("    release-diff: prompt rendered from %s for lane=%s branch=%s diff_path=%s; "
              "live mode writes the rendered prompt to the ledger before dispatch" % (
                  qa_prompt, lane["id"], lane["branch"], diff))
        if not rendered_prompt.strip():
            raise PlanRefusal("release-diff QA prompt rendered empty")
        print("    release-diff: exact run-codex.sh argv: %s" % _format_command(qa_argv))
        summary_prompt = HERE / "prompts" / "qa-morning-summary.prompt.md"
        summary_argv = _claude_argv(
            "qa-morning-summary", lane,
            "Read the generated report at <report_path>; use template %s" % summary_prompt,
            lane["brief"], ledger_dir,
        )
        summary_wrapper = _qa_claude_wrapper_argv(
            "qa-morning-summary", lane, run_id, summary_argv[-1], ledger_dir, qa_op
        )
        print("    morning-summary: wrapper argv: %s" % _format_command(summary_wrapper))
        if lane.get("client_visible"):
            client_wrapper = _qa_claude_wrapper_argv(
                "qa-client-artifact", lane, run_id,
                "held-out client-artifact readback", ledger_dir, qa_op
            )
            print("    client-artifact: wrapper argv: %s" % _format_command(client_wrapper))
        print("  PARK PREDICTIONS (derived from gate-map.json)")
        for row in gate_map["gates"]:
            if row["verdict"] == "parks" and _park_applies(row, lane):
                print("    PREDICTED PARK: %s (%s L%s) — %s" % (
                    row["gate"], row["component"], row["census_line"], row["covered_by"]))
        if lane.get("client_visible"):
            print("    GUARANTEED PARK: client-artifact (clodex-verify L385)")

    print("\nBUDGET CEILINGS")
    source = "run-plan.json@%s" % plan_sha[:8]
    for field in ("codex_weekly_pct_ceiling", "codex_5h_pct_ceiling",
                  "claude_usd_ceiling", "per_lane_usd_ceiling"):
        print("  %s=%s | field budget.%s | source %s" % (
            field, plan["budget"][field], field, source))


def _print_gates(plan, plan_sha):
    source = "run-plan.json@%s" % plan_sha[:8]
    print("\n15 GATES — WOULD APPLY (dry-run; no live lane evaluation)")
    for gate_id, tier, mechanism, fields in GATES:
        print("GATE %s | tier=%s" % (gate_id, tier))
        print("  mechanism: %s" % mechanism)
        for path, label in fields:
            value = plan
            if path == "lanes[*].direction_gate":
                value = [lane["direction_gate"] for lane in plan["lanes"]]
            else:
                for part in path.split("."):
                    value = value[part]
            print("  threshold: %s=%s | source %s" % (label, _format_value(value), source))
        print("  WOULD APPLY")


def _snapshot_dispatchables(ledger_dir):
    if ledger_dir is None or not Path(ledger_dir).exists():
        return []
    try:
        snapshot = orchestrator_state.load_snapshot(str(ledger_dir))
    except Exception:
        return []
    return list(snapshot.get("dispatchable", []))


def _do_unpark(lane, plan_path, ledger_dir, plan, plan_sha):
    if ledger_dir is None:
        raise PlanRefusal("--unpark requires --ledger-dir")
    if lane not in {item["id"] for item in plan["lanes"]}:
        raise PlanRefusal("--unpark names unknown lane %r" % lane)
    ledger = Path(ledger_dir)
    record = ledger / ("PARKED-%s.md" % lane)
    answer = _answer_block(record)
    problem = orchestrator_state.check_ledger_identity(
        str(ledger), run_plan_path=str(plan_path), run_plan_sha=plan_sha
    )
    if problem:
        raise PlanRefusal(problem)
    before = _snapshot_dispatchables(ledger)
    try:
        snapshot = orchestrator_state.unpark(str(ledger), lane, answer, str(record))
    except Exception as exc:
        raise PlanRefusal("unpark refused: %s" % exc)
    after = list(snapshot.get("dispatchable", []))
    newly = [item for item in after if item not in before]
    print("UNPARKED %s" % lane)
    print("answer record: %s" % record)
    print("record sha: %s" % hashlib.sha256(record.read_bytes()).hexdigest())
    print("newly-dispatchable dependents: %s" % (", ".join(newly) if newly else "(none)"))
    print("DRY RUN — dispatched nothing")
    return EXIT_OK


def build_parser():
    parser = argparse.ArgumentParser(
        prog="orchestrate.py",
        description="Validate and print a lane dispatch plan; this round never dispatches.",
    )
    parser.add_argument("--unpark", metavar="LANE", help="record the answer for one parked lane")
    parser.add_argument("run_plan", metavar="run-plan.json")
    parser.add_argument("--ledger-dir", help="ledger to read, or to update for --unpark")
    return parser


def main(argv=None):
    """Run the no-spawn dry-run or the ledger-only unpark transition."""
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse's normal CLI behavior remains exit 2; returning it makes
        # in-process tests able to assert the same contract without spawning.
        return int(exc.code)
    try:
        plan_path = Path(args.run_plan).expanduser().resolve()
        plan = _read_plan(plan_path)
        plan_sha = _plan_sha(plan_path)
        graph = validate_semantic_graph(plan)
        gate_map = _load_gate_map()
        if args.unpark and not args.ledger_dir:
            raise PlanRefusal("--unpark requires --ledger-dir")
        ledger = _ledger_label(plan_path, args.ledger_dir)
        if args.unpark:
            return _do_unpark(args.unpark, plan_path, ledger, plan, plan_sha)
        if args.ledger_dir:
            _safe_snapshot(ledger, plan_path, plan_sha)
        _print_dispatch_plan(plan, plan_path, plan_sha, graph, gate_map, ledger)
        _print_gates(plan, plan_sha)
        print("\nDRY RUN — dispatched nothing")
        return EXIT_OK
    except (PlanRefusal, OSError, ValueError, KeyError) as exc:
        print("orchestrate.py: REFUSED — %s" % exc, file=sys.stderr)
        return EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Read the Codex quota meters and the selected Claude cost ledger.

This is deliberately a reader only.  It does not invoke a model, a shell, or
any other process.  In particular, an absent or malformed meter remains
UNKNOWN rather than being made to look like zero headroom.
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import json
import math
import sys
import time
from pathlib import Path


WEEKLY_MINUTES = 10080
FIVE_HOUR_MINUTES = 300
MAX_RECORD_AGE_SECONDS = 7 * 24 * 60 * 60


def _number(value):
    """Return a finite int/float, or None for an unreadable number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value):
        return None
    return value


def _iso(seconds):
    """Render a Unix timestamp in an unambiguous UTC ISO-8601 form."""
    try:
        value = _number(seconds)
        if value is None:
            return "UNKNOWN"
        return (
            _datetime.datetime.fromtimestamp(value, _datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
    except (OverflowError, OSError, ValueError):
        return "UNKNOWN"


def _jsonl_files(root, suffix):
    """Return readable regular files below root, in deterministic order."""
    if not root.is_dir():
        return []
    try:
        paths = [path for path in root.rglob("*" + suffix) if path.is_file()]
    except OSError:
        return []
    return sorted(paths, key=lambda path: str(path))


def _find_rate_limits(value):
    """Classify the first rate_limits key found in a JSON value.

    Returns ("found", dict) for a usable meter object, ("unusable", None) when
    a rate_limits key exists but its value is not an object (a vendor null is
    a real record saying "no meter" — it must not be papered over by an older
    good record), or None when no rate_limits key exists at all.  Rollout
    records have appeared nested in event envelopes, so this walks
    dictionaries and lists instead of assuming a particular event shape.
    """
    if isinstance(value, dict):
        if "rate_limits" in value:
            candidate = value.get("rate_limits")
            if isinstance(candidate, dict):
                return ("found", candidate)
            return ("unusable", None)
        for child in value.values():
            found = _find_rate_limits(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_rate_limits(child)
            if found is not None:
                return found
    return None


def _record_timestamp(value):
    """A parseable timestamp on the record's own line, in Unix seconds.

    The rollout format is undocumented; common top-level keys are probed and
    anything unparseable yields None (the caller falls back to file mtime and
    says so).
    """
    if not isinstance(value, dict):
        return None
    for key in ("timestamp", "ts", "created_at", "time"):
        raw = value.get(key)
        number = _number(raw)
        if number is not None and number > 0:
            return float(number)
        if isinstance(raw, str):
            text = raw.strip().replace("Z", "+00:00")
            try:
                parsed = _datetime.datetime.fromisoformat(text)
            except ValueError:
                continue
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=_datetime.timezone.utc)
            return parsed.timestamp()
    return None


def _last_rate_limits(path):
    """Return (rate_limits, record_ts, hazard) from a JSONL file.

    `hazard` is a reason string when anything AFTER the last good record was
    an unusable rate_limits record or an unparseable line — except the final
    unterminated line, which a live writer legitimately produces.  A hazard
    means the meters must read UNKNOWN: the newest information about the
    meter is unreadable, and an older good record must not stand in for it.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return None, None, None
    final_unterminated = bool(data) and not data.endswith(b"\n")
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()

    found = None
    found_ts = None
    found_idx = -1
    hazard_idx = -1
    hazard = None
    for idx, raw_line in enumerate(lines):
        if not raw_line.strip():
            continue
        tolerated_tail = final_unterminated and idx == len(lines) - 1
        try:
            value = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            if not tolerated_tail:
                hazard_idx, hazard = idx, "unparseable line inside the rollout"
            continue
        state = _find_rate_limits(value)
        if state is None:
            continue
        kind, candidate = state
        if kind == "found":
            found, found_idx = candidate, idx
            found_ts = _record_timestamp(value)
        elif not tolerated_tail:
            hazard_idx, hazard = idx, "a newer rate_limits record is unusable"
    if hazard_idx > found_idx:
        return found, found_ts, hazard
    return found, found_ts, None


def _read_rollout(root):
    """Select the newest rollout and return its last usable rate_limits."""
    files = _jsonl_files(root, ".jsonl")
    if not files:
        return None, "no rollout files found"

    # Path is a deterministic tie-breaker; the primary ordering is mtime.
    statted = []
    for path in files:
        try:
            statted.append((path.stat().st_mtime, str(path), path))
        except OSError:
            continue
    if not statted:
        return None, "could not stat rollout files"
    record_mtime, _, newest = max(statted)
    rate_limits, record_ts, hazard = _last_rate_limits(newest)
    if rate_limits is None:
        return None, "no parseable rate_limits record in newest rollout"
    return {
        "source_file": str(newest),
        "record_mtime": record_mtime,
        "record_ts": record_ts,
        "hazard": hazard,
        "rate_limits": rate_limits,
    }, None


def _unknown(reason, meter=None):
    """Build the stable JSON shape for an unknown window."""
    result = {
        "used_percent": None,
        "resets_at": None,
        "window_minutes": None,
        "status": "unknown",
        "reason": reason,
    }
    if isinstance(meter, dict):
        for key in ("used_percent", "resets_at", "window_minutes"):
            if key in meter:
                result[key] = meter[key]
    return result


def _valid_meter(meter, expected_minutes, now):
    """Validate one meter after exact window identity has been established."""
    if not isinstance(meter, dict):
        return _unknown("meter is not an object")

    used = _number(meter.get("used_percent"))
    if used is None:
        return _unknown("used_percent is missing or unparseable", meter)

    resets_at = _number(meter.get("resets_at"))
    if resets_at is None:
        return _unknown("resets_at is missing or unparseable", meter)

    window_minutes = _number(meter.get("window_minutes"))
    if window_minutes is None or window_minutes != expected_minutes:
        return _unknown(
            "window_minutes is not exactly %d" % expected_minutes, meter
        )

    if used < 0 or used > 100:
        return _unknown("used_percent is out of the 0-100 range", meter)

    if resets_at < now:
        return _unknown("resets_at is in the past", meter)

    return {
        "used_percent": used,
        "resets_at": resets_at,
        "window_minutes": window_minutes,
        "status": "ok",
    }


def _windows(rate_limits, now, record_age, hazard=None):
    """Resolve weekly and five-hour meters purely by exact window identity.

    Position (primary vs secondary) is never trusted: a valid meter carrying
    `window_minutes == 300` identifies the five-hour window wherever it sits,
    and a window with no exact-identity meter is UNKNOWN.  A hazard from the
    rollout read (an unusable newer record) makes both windows UNKNOWN — an
    older good record must not stand in for the newest information.
    """
    if not isinstance(rate_limits, dict):
        return {
            "weekly": _unknown("rate_limits is not an object"),
            "five_hour": _unknown("rate_limits is not an object"),
        }

    candidates = []
    for label in ("primary", "secondary"):
        meter = rate_limits.get(label)
        if isinstance(meter, dict):
            minutes = _number(meter.get("window_minutes"))
            if minutes is not None:
                candidates.append((label, meter, minutes))

    def resolve(expected):
        matches = [item for item in candidates if item[2] == expected]
        if not matches:
            return _unknown(
                "no meter with exact window_minutes=%d" % expected
            )
        if len(matches) > 1:
            return _unknown(
                "multiple meters with exact window_minutes=%d" % expected
            )
        return _valid_meter(matches[0][1], expected, now)

    weekly = resolve(WEEKLY_MINUTES)
    five_hour = resolve(FIVE_HOUR_MINUTES)

    if hazard:
        weekly = _unknown(hazard, weekly)
        five_hour = _unknown(hazard, five_hour)

    if record_age > MAX_RECORD_AGE_SECONDS:
        weekly = _unknown("record is older than 7 days", weekly)
        five_hour = _unknown("record is older than 7 days", five_hour)

    return {"weekly": weekly, "five_hour": five_hour}


def _credits(rate_limits):
    """Return the credits object without inventing a credit balance."""
    if isinstance(rate_limits, dict) and isinstance(rate_limits.get("credits"), dict):
        return dict(rate_limits["credits"])
    return {}


def _run_dirs(root):
    if not root.is_dir():
        return []
    try:
        return sorted(
            [path for path in root.iterdir() if path.is_dir()],
            key=lambda path: str(path),
        )
    except OSError:
        return []


def _top_ndjson(directory):
    """The run directory's OWN event files — never a recursive sweep.

    Legs live in the ledger's top-level `*.ndjson`; a nested file (archived
    material, a copied run) must be able neither to win the newest-run
    selection nor to inject or duplicate legs.
    """
    try:
        return sorted(
            [p for p in directory.glob("*.ndjson") if p.is_file()],
            key=lambda p: str(p),
        )
    except OSError:
        return []


def _select_ledger(ledger_dir, runs_root):
    """Select an explicit ledger or the prescribed automatic run directory.

    Returns (path-or-None, auto_selected, error-or-None).  An explicit
    directory that does not exist is an ERROR, not an empty ledger — the
    caller named a thing that is not there, and rendering that as $0.00
    would turn a typo into apparent budget headroom.
    """
    if ledger_dir is not None:
        if not ledger_dir.is_dir():
            return None, False, "ledger directory does not exist: %s" % ledger_dir
        return ledger_dir, False, None

    dirs = _run_dirs(runs_root)
    if len(dirs) == 1:
        return dirs[0], True, None

    candidates = []
    for path in dirs:
        event_files = _top_ndjson(path)
        if not event_files:
            continue
        try:
            newest_mtime = max(event.stat().st_mtime for event in event_files)
        except OSError:
            continue
        candidates.append((newest_mtime, str(path), path))
    if not candidates:
        return None, False, None
    _, _, selected = max(candidates)
    return selected, True, None


def _ledger_total(ledger_dir):
    """Sum claude:leg costs fail-closed.

    Anything the reader cannot account for — an unreadable file, a corrupt
    line, a null or malformed or negative cost — is surfaced as uncertainty,
    never silently rendered as zero spend.
    """
    total = 0.0
    unknown_legs = 0
    unreadable_files = 0
    corrupt_lines = 0
    for path in _top_ndjson(ledger_dir):
        try:
            data = path.read_bytes()
        except OSError:
            unreadable_files += 1
            continue
        for raw_line in data.split(b"\n"):
            if not raw_line.strip():
                continue
            try:
                event = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                corrupt_lines += 1
                continue
            if not isinstance(event, dict) or event.get("e") != "claude:leg":
                continue
            cost = event.get("cost_usd")
            if cost is None:
                unknown_legs += 1
                continue
            number = _number(cost)
            if number is None or number < 0:
                # A malformed or negative cost is spent-but-unmeasured, not free.
                unknown_legs += 1
                continue
            total += float(number)
    return total, unknown_legs, unreadable_files, corrupt_lines


def _credits_text(credits):
    if credits.get("has_credits") is False:
        return "credits none"
    if credits.get("has_credits") is True:
        balance = _number(credits.get("balance"))
        if balance is not None:
            return "credits $%.2f" % balance
        return "credits available"
    balance = _number(credits.get("balance"))
    if balance is not None:
        return "credits $%.2f" % balance
    return "credits unknown"


def _percent_text(window):
    if window.get("status") != "ok":
        return "UNKNOWN (refuse fan-out)"
    return "%.1f%%" % float(window["used_percent"])


def _window_text(label, window):
    return "%s %s resets-at %s" % (
        label,
        _percent_text(window),
        _iso(window.get("resets_at")),
    )


def _claude_text(claude, ledger, auto_selected):
    uncertain_parts = []
    if claude["unknown_legs"]:
        uncertain_parts.append("+%d unknown legs" % claude["unknown_legs"])
    if claude["unreadable_files"]:
        uncertain_parts.append("%d unreadable files" % claude["unreadable_files"])
    if claude["corrupt_lines"]:
        uncertain_parts.append("%d corrupt lines" % claude["corrupt_lines"])
    if uncertain_parts:
        text = "claude ≥ $%.2f (%s)" % (claude["total_usd"], "; ".join(uncertain_parts))
    else:
        text = "claude $%.2f" % claude["total_usd"]
    if ledger is not None and auto_selected:
        text += "; ledger: %s" % ledger.name
    elif ledger is None:
        text += " (no ledger)"
    return text


def _report(record, windows, credits, claude, now, age, age_source):
    return {
        "windows": windows,
        "record_mtime": record["record_mtime"],
        "record_ts": record.get("record_ts"),
        "record_age_seconds": age,
        "record_age_source": age_source,
        "credits": credits,
        "claude": claude,
        "source_file": record["source_file"],
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description="Read Codex quota windows and the Claude cost ledger."
    )
    parser.add_argument(
        "--sessions-dir",
        type=Path,
        default=Path.home() / ".codex" / "sessions",
        help="Codex sessions root (default: ~/.codex/sessions)",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path.home() / ".lane-orchestrator" / "runs",
        help="automatic ledger run root (default: ~/.lane-orchestrator/runs)",
    )
    parser.add_argument(
        "--ledger-dir",
        type=Path,
        default=None,
        help="explicit Claude ledger directory",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="emit the machine-readable JSON report",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    sessions_dir = args.sessions_dir.expanduser()
    runs_root = args.runs_root.expanduser()
    ledger_dir = args.ledger_dir.expanduser() if args.ledger_dir else None
    now = time.time()

    record, error = _read_rollout(sessions_dir)
    if record is None:
        print("error: %s" % error, file=sys.stderr)
        return 1

    # Freshness prefers the record's own timestamp: a later unrelated write
    # (or a touch) moves the file mtime and must not make an old meter look
    # current.  With no parseable record timestamp, mtime is the fallback,
    # and the output says which was used.
    if record.get("record_ts") is not None:
        age = max(0.0, now - record["record_ts"])
        age_source = "record"
    else:
        age = max(0.0, now - record["record_mtime"])
        age_source = "file-mtime"
    windows = _windows(record["rate_limits"], now, age, record.get("hazard"))
    credits = _credits(record["rate_limits"])
    selected_ledger, auto_selected, ledger_error = _select_ledger(
        ledger_dir, runs_root
    )
    if ledger_error is not None:
        print("error: %s" % ledger_error, file=sys.stderr)
        return 1
    if selected_ledger is not None:
        total, unknown_legs, unreadable_files, corrupt_lines = _ledger_total(
            selected_ledger
        )
    else:
        total, unknown_legs, unreadable_files, corrupt_lines = 0.0, 0, 0, 0
    claude = {
        "total_usd": total,
        "unknown_legs": unknown_legs,
        "unreadable_files": unreadable_files,
        "corrupt_lines": corrupt_lines,
        "ledger": selected_ledger.name if selected_ledger is not None else None,
    }
    report = _report(record, windows, credits, claude, now, age, age_source)

    if args.as_json:
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    else:
        print(
            "%s; %s; record %s (age %.0fs, %s); %s; %s"
            % (
                _window_text("weekly", windows["weekly"]),
                _window_text("5-hour", windows["five_hour"]),
                _iso(record.get("record_ts") if record.get("record_ts") is not None
                     else record["record_mtime"]),
                age,
                age_source,
                _credits_text(credits),
                _claude_text(claude, selected_ledger, auto_selected),
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

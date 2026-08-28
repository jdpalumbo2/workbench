#!/usr/bin/env python3
"""Generate finding/round counts from a clodex run's ledger.

Added by the 2026-08-28 process revamp: three audited releases carried
hand-typed finding counts (69/81/87) that their own archived ledgers did not
support (67/69/83, four findings still open). Release prose, STATE entries,
and changelogs must copy this script's output instead of typing counts.

Usage:
    python3 counts.py <run-dir> [<run-dir> ...]

A run dir is any directory containing events.ndjson (live run dirs and
archive dirs both qualify). Output per run: one summary line to paste, then
the breakdown. Exit 1 if any run has open findings or unreadable events.
"""
import json
import sys
from collections import Counter
from pathlib import Path


def summarize(run_dir: Path) -> bool:
    events_path = run_dir / "events.ndjson"
    if not events_path.is_file():
        print(f"{run_dir}: no events.ndjson", file=sys.stderr)
        return False

    recorded = {}
    dispositions = {}
    rounds = set()
    invocations = set()
    bad_lines = 0

    with events_path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                bad_lines += 1
                continue
            name = ev.get("e")
            if name == "finding:recorded":
                recorded[ev.get("id")] = ev.get("severity", "?")
                if ev.get("round") is not None:
                    rounds.add((ev.get("source"), ev.get("round")))
                if ev.get("invocation"):
                    invocations.add(ev["invocation"])
            elif name == "finding:disposed":
                dispositions[ev.get("id")] = ev.get("disposition", "?")
            codex = ev.get("codex")
            if isinstance(codex, dict) and codex.get("invocation_id"):
                invocations.add(codex["invocation_id"])

    open_ids = sorted(set(recorded) - set(dispositions))
    by_disp = Counter(dispositions[i] for i in recorded if i in dispositions)
    by_sev = Counter(recorded.values())

    disp_txt = ", ".join(f"{n} {d}" for d, n in sorted(by_disp.items())) or "none disposed"
    print(f"{run_dir.name}: {len(recorded)} findings recorded ({disp_txt}; "
          f"{len(open_ids)} open) across {len(invocations)} recorded invocations")
    print(f"  severity: {dict(sorted(by_sev.items()))}")
    if open_ids:
        print(f"  OPEN: {' '.join(open_ids)}")
    if bad_lines:
        print(f"  WARNING: {bad_lines} unparseable event line(s)", file=sys.stderr)
    return not open_ids and not bad_lines


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    ok = True
    for arg in sys.argv[1:]:
        ok = summarize(Path(arg)) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

# Follow-on: dry-run print-contract fixes (s-F001/2/3 from r-2026-09-01-b)

Run: r-2026-09-02-a · Plan version: 2 · Repo: /Users/jpalumbo/code/personal/tools/workbench-clodex-r-2026-09-01-b · Parent: r-2026-09-01-b

## Brief

Follow-on to r-2026-09-01-b (abandoned at ship by the user's explicit choice): fix the three open release-diff findings on the same branch. s-F001 (high): Claude QA recovery watches a different marker path than the wrapper writes — orchestrate.py prints QA markers at `<ledger>/qa/<op_id>/<stage>.started` while orchestrator_state.marker_for records `<ledger>/qa/<op_id>.started` for qa* stages; a QA model that starts but leaves no parseable envelope would read as never-spawned (zero cost, replan) instead of parking, breaking stop-on-unknown. Fix: orchestrate.py derives its printed marker/envelope paths from orchestrator_state's own oracle_for/marker_for — one source of truth. s-F002 (high): the dispatch plan passes lane[repo] as run-codex.sh --repo for lane-internal runner shapes and release-diff QA; the runner anchors cwd/sandbox to --repo, so the printed contract targets the shared checkout instead of the lane worktree. Fix: use lane[worktree]. s-F003 (high): release-diff QA prints literal `<worktree>/<release-diff>` as --input (the runner refuses nonexistent input files) and morning-summary prints literal `<report_path>`. Fix: print the ledger-derived concrete paths — `<ledger>/qa/<op_id>/release.diff` (written by the orchestrator before dispatch; only the op_id placeholder remains, which the plan permits) and `<ledger>/MORNING-REPORT-<run-plan date>.md` with the date resolved from the plan. Scope: orchestrate.py print/derivation layer + tests/test_orchestrator_dryrun.py assertions; no engine changes; parent's prohibitions and claims carry over; dry-run only; no push/merge/tag.

## Grounding

The parent run's full record: `.clodex/archive/r-2026-09-01-b/` in the main checkout (this worktree's live copy at `.clodex/r-2026-09-01-b/`), whose manifest carries s-F001/2/3 with the reviewer's verbatim detail; the release-review envelope `code-reviewer-20260902T002548Z-fe80a9`; `skills/lane-orchestration/orchestrator_state.py` (`oracle_for`, `marker_for` — the single source the prints must derive from); `skills/lane-orchestration/orchestrate.py` L782-891 (the two defect regions read during triage); the parent plan `docs/plans/2026-09-01-lane-b-orchestrator-rebuild.md` v8, whose Direction exactness contract and Contracts section remain the governing design — this run changes no contract, it makes the prints obey them.

## Prior art

`orchestrator_state.oracle_for`/`marker_for` (batch 2 of the parent) already define every path the prints compose by hand — the fix is deletion of a second derivation, the exact "one script feeds both so they cannot disagree" shape the parent plan's A.4 praised. No new mechanism.

## Assumptions

- The three findings' details, as recorded in the parent manifest, accurately locate the defects (verified during triage by reading both regions).
- The engine's qa-oracle layout (`qa/<op_id>/` dir + `qa/<op_id>.started` marker) is the correct side of each disagreement — it is what reconcile actually reads; prints conform to it, never the reverse.

## Direction gate

Direction gate: no — repairs the printed contract to match the already-approved v8 design; follows the existing oracle_for/marker_for pattern (cited in Prior art); no new visual, copy, or behavior decision.

## Scope

Done when: `tests/run.sh` green; the regenerated dry-run output over the sample plan shows (a) QA wrapper marker/envelope paths byte-derived from orchestrator_state's marker_for/oracle_for, (b) every runner argv anchored to the lane's worktree, (c) the release-diff input and morning-summary report paths as concrete ledger-derived paths with only the permitted op_id placeholder; the three parent findings are closed as fixed in THIS run's log with the commit sha.

### In
orchestrate.py print/derivation fixes; test assertions pinning all three.

### Out
Any engine change; any new contract; live dispatch; push/merge/tag; everything else the parent run built.

## Batches

| # | Owned paths | Done when |
|---|---|---|
| 1 | `docs/plans/2026-09-02-dryrun-print-contract-fixes.md`, `skills/lane-orchestration/orchestrate.py`, `tests/test_orchestrator_dryrun.py` | **every** oracle, marker, and envelope path the dispatch plan prints — lane stages (today's L870-873), Claude QA, and the release-diff QA state dir (L885) — is obtained by calling `orchestrator_state.oracle_for`/`marker_for`, never composed locally (r1-F001: coincidental equality is not derivation); the derivation is proven by a test that monkeypatches both helpers with sentinel-suffixed returns and asserts every printed path carries the sentinel; plus one test per parent finding (worktree in every printed `--repo`; no `<release-diff>`/`<report_path>` literals, concrete ledger paths present); full gate green |

Release-owned — no batch may own these (from the profile): version source `skills/clodex/VERSION`; no changelog; tags `clodex-v{version}`.

Docs impact: none — the SKILL/README describe behavior at the contract level, which does not change.

Claims: covered by lane-B's standing claims (skills/lane-orchestration/**, tests/test_orchestrator_*.py).

## Evidence

| Class | What will prove it |
|---|---|
| tests | `tests/run.sh` — with the three new pins |
| visual | the regenerated `dryrun-output.txt`, read by Johnny against the three findings |

## Risks

- A printed-string assertion elsewhere in the dryrun tests may pin the old wrong text; the batch owns the test file, so such pins are corrected as part of the fix, with each change named in the delta review.

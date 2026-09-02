# lane-orchestration

Deterministic overnight orchestration for clodex lanes: a Python control plane
that costs zero model tokens, headless lane workers in git worktrees, Codex as
the heavy executor inside them, and park-don't-prompt handling for every gate
a human would otherwise answer at 4am.

Renamed from `opus-orchestration` on 2026-09-01 — vendor-named skills rot (the
old name was wrong four months in), and the durable noun is the **lane**.

**STATUS: DRY-RUN ONLY.** `orchestrate.py` prints what a night *would* do and
dispatches nothing. Live dispatch waits for the watched step-7 run of the
build order in `docs/plans/2026-09-01-lane-b-orchestrator-rebuild.md`.

## The scripts

| Script | Job |
|---|---|
| `quota.py` | Both Codex quota windows + the Claude cost ledger, one line. UNKNOWN always means *refuse fan-out*, never zero. `--json` for machines. |
| `orchestrate.py` | Validate a run-plan (schema + lane graph), print the dispatch plan, all 15 gates, and park predictions. `--unpark <lane> <run-plan.json> --ledger-dir <dir>` records a human answer. |
| `orchestrator_state.py` | The ledger engine — a deliberate copy of `clodex_state.py`'s design; divergences named in its docstring. Four-phase dispatch receipts, attempt-unique oracles, stop-on-unknown reconcile. |
| `dispatch_wrapper.py` | Supervises one dispatch child: fsynced start marker before the model spawns, op_id in its argv, envelope fsynced on exit. |
| `run-plan.schema.json` | The committed lane-graph contract. |
| `reference/gate-map.json` | The 28 blocking-human gates mapped to unattended behavior; machine-read for park predictions. `gate-map.md` is the human rendering. |

## The run-plan contract

Everything load-bearing is a committed file. The budget block is **required in
full** — `mode`, `codex_weekly_pct_ceiling`, `codex_5h_pct_ceiling`,
`claude_usd_ceiling`, `per_lane_usd_ceiling` — with **no defaults in code**,
so every threshold is a number someone committed. There is deliberately **no
per-lane Codex ceiling**: the rollout meter is account-wide and moves in whole
percents, so per-lane attribution under parallel fan-out would charge the same
spend to overlapping lanes; global windows enforce, per-lane Codex numbers are
reported as labeled approximations. Per lane: `id`, `kind`, `repo`,
`worktree`, `branch`, `base` (40-hex sha), `brief`, `depends_on`, `claims`
(router exact-key semantics), `client_visible`, `direction_gate`; optional
`push` (default false — a lane may push exactly its own branch when true) and
`acceptance_ref`.

## The ledger

`~/.lane-orchestrator/runs/<date>-<sha8-of-run-plan>/` — identity is bound to
the run-plan's sha and every append refuses a mismatch. Events are the truth;
`run.json` is derived. Dispatch receipts are four-phase
(`pending → spawning → launched → done`) with the reality oracle derived from
the op_id before anything spawns; reconcile settles every open receipt through
its oracle and **parks on unknown, never re-dispatches**.

## Try it

```bash
python3 skills/lane-orchestration/quota.py
python3 skills/lane-orchestration/orchestrate.py \
    skills/lane-orchestration/samples/run-plan.sample.json
```

## Install (and migrate from opus-orchestration)

```bash
rm -f ~/.claude/skills/opus-orchestration     # dangling after the rename
ln -s "$(pwd)/skills/lane-orchestration" ~/.claude/skills/lane-orchestration
```

## Deliberately not here yet

Live dispatch (a watched run with a named watcher comes first), the gate-13
acceptance machinery, staging targets for client-visible lanes, and launchd
(three consecutive clean supervised multi-lane runs before autonomy —
`SOAKING 3/3` applied to the orchestrator itself).

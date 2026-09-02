---
name: lane-orchestration
description: Use when orchestrating a multi-lane build night — parallel clodex lanes in worktrees dispatched by the deterministic orchestrator, budget-gated against both Codex quota windows and the Claude cost ledger, with park-don't-prompt handling for every human gate. Also use when reading a dispatch plan, answering a parked lane, or checking the meters before spending. Replaces opus-orchestration (renamed 2026-09-01: vendor-named skills rot — the durable noun is the lane).
---

# Lane Orchestration

## Overview

A deterministic Python orchestrator is the control plane; headless clodex
lanes are the workers; Codex is the heavy executor inside them. The
orchestrator holds the lane graph, every budget gate, and the park/unpark
protocol — it costs zero model tokens to run, resumes after a crash by
re-reading its own ledger, and is the only place an unbypassable gate can
live. Nothing prompts a human mid-flight: a lane that hits a gate it cannot
answer **parks**, and the orchestrator schedules around it.

**Status: dry-run only.** `orchestrate.py` prints the dispatch plan and every
gate it would apply, and dispatches nothing. Live dispatch lands after the
watched step-7 run (build order in the 2026-09-01 plan); treat any instruction
here about live behavior as the contract that run must satisfy, not as a
capability that exists today.

## The scripts (this directory)

| Script | Job |
|---|---|
| `quota.py` | Both Codex windows + the Claude cost ledger, one line. UNKNOWN is a first-class answer and always means *refuse fan-out* — never zero. `--json` for machines. |
| `orchestrate.py` | Validate `run-plan.json` (schema + lane graph), print the dispatch plan and all 15 gates, predict parks from the gate map. `--unpark <lane>` records a human answer. Dry-run only. |
| `orchestrator_state.py` | The ledger engine — a deliberate copy of `clodex_state.py`'s design (append+fsync, dead-holder locks, deterministic rebuild, four-phase receipts with attempt-unique oracles, stop-on-unknown reconcile). Divergences are named in its docstring. |
| `dispatch_wrapper.py` | Supervises exactly one dispatch child: fsynced start marker before the model spawns, op_id in its own argv for the process-table oracle, envelope fsynced on exit. |
| `run-plan.schema.json` | The committed lane-graph contract. Every threshold is a required field — no default lives in code, so no gate is silently unpriced. |
| `reference/gate-map.json` | All 28 census gates that block an unattended run, mapped pre-answered / mandate / parks / unreachable. Machine-read by orchestrate.py; verdicts are reviewed judgment (`gate-map.md`). |

## Rules that carried over from opus-orchestration (kept on purpose)

- **Plans are committed files.** The run-plan, the briefs, the orchestration
  plan — nothing load-bearing lives only in chat. A lane reads merge order and
  sibling scopes from committed truth, never a scrollback.
- **One worker per independent lane.** Dependent lanes don't get a worker
  until the upstream gate passes — that is literally `depends_on` in
  `run-plan.json`.
- **Verification stays adversarial: review goes to a different session than
  the one that wrote. A worker never passes its own gate.**
- Research fan-out: parallel researchers each take a **distinct angle**, cite
  every claim with **URL and date**, and label vendor vs third-party vs paper
  sources; every sweep is persisted into the repo **marked unaudited** so
  internal citations resolve — evidence living only in a prompt is the most
  common verifier finding. Their output is raw data for the writer, not prose
  for a human.
- Convergence rules for fix loops: minimal edits only; verify-before-writing
  on any comparative, pattern, or absence claim; scoped reverify after round
  one (10 lines around each edit, newly rewritten claims guilty until
  verified) — never a fresh full-document expedition. **Endgame:** when only
  small precisely-specified issues remain, one minimal-edit polish with the
  verifier's own quoted evidence in the prompt, then a scoped check —
  converge, don't whack-a-mole. Round cap: **3** — the estate's number, with
  an incident behind it (`workflow-template.js` now agrees).

## Verification is gated on blast radius, not run unconditionally

| Condition | Verification |
|---|---|
| Client-visible surface | Full: cross-family review + client-artifact readback + held-out acceptance (gate 13 — not yet built) |
| Direction gate `yes` | Full |
| Boundary strays or a failed profile gate | Full |
| The artifact is a design other work builds on | Full (the condition B.7 gained from its own self-review) |
| Everything else | One cross-family review round — and gate 13 still runs once built |

The reviewer's output is synthesized by the caller, never forwarded verbatim —
findings are recorded and *disposed*, and a disposition is an act of judgment.

## Park, don't prompt — and the honest scope

Of the 28 blocking-human gates in the clodex corpus, a brief plus the
run-scoped mandate covers ~8. Four park *reliably*: any plan amendment (revokes
the mandate — a normal build event), any stray path, round 3 with blockers
still arriving, and **every client-visible lane at verify** (no mailbox, no
deploy, no operator at 4am). So the honest scope is:

> Overnight lanes are for work whose direction gate is `no` and whose surfaces
> are internal. Client-visible work can be *built and reviewed* overnight but
> cannot reach verify-complete without a staging target the lane owns —
> a prerequisite still to be designed, not an enhancement.

A park writes `PARKED-<lane>.md` with five required fields (gate · question ·
options · blocked · cost so far — conspicuously useless if any is blank).
Johnny answers by appending an `## Answer:` block and running

```bash
python3 skills/lane-orchestration/orchestrate.py \
    --unpark <lane> <run-plan.json> --ledger-dir <ledger dir>
```

The answer's text and file sha go in the ledger, dependents are re-evaluated,
and a re-dispatched worker opens a fresh unattended window — a post-unpark
headless forgery of `by:"user"` still fails gate 7. A park older than the
morning report escalates; silence is not a status.

## The lane's terminal artifact is the lane report

Ship does not run unattended. Release authorization and verification-debt
acceptance are the human-owned core in every run — no mandate reaches them.
A clean lane ends at verify-complete with a reviewed branch and a report whose
first line is its run id; the morning session runs ship with Johnny present.

## Alternate substrate: Workflow scripts

For wide mechanical fan-out inside one conversation (dozens of
schema-validated agents, zero-token control flow) the scripted Workflow
variant still beats a lane night: [workflow-template.js](workflow-template.js)
is the production-proven skeleton. Two constraints found 2026-09-01: the
script API has **no filesystem and no shell** — every disk touch would become
a model call — and its resume reruns every agent that started after a failed
one. That, not agent-nesting folklore, is why the overnight orchestrator is a
plain Python process instead.

## Common mistakes

| Mistake | Fix |
|---|---|
| Load-bearing instructions only in chat, not the plan file | The committed plan is the worker's whole world |
| A worker reviewing its own output | Adversarial review is a different session, always |
| Orchestrator narrates a pending worker's "probable" state | Report only received checkpoints — or the ledger's receipts |
| Two human-in-the-loop steps scheduled at once | The orchestrator owns the calendar of auth/login moments |
| Fresh full adversarial pass every fix round | Scoped reverify after round one; see convergence rules |
| Fixer rewrites a comparison from memory | Verify-before-writing; print inputs, never derive |
| Evidence lives only in the prompt | Persist sweeps to the repo, marked unaudited |
| Forwarding a reviewer's findings verbatim | Findings are recorded and DISPOSED; a disposition is judgment the caller owns |
| Assuming a flag was honored | Read the model back out of the envelope (`modelUsage`) and fail the step on disagreement — plan mode silently upgrades haiku |
| Putting a held-out oracle where the worker can read it | Acceptance criteria live outside every lane's filesystem reach, or the gate is theatre |
| Citing a source's headline while dropping its own qualifier | Selective inheritance is the failure mode that survived three reviews; carry the caveat or drop the claim |
| (script mode) `bash()` / `Date.now()` / `phase(fn)` | Not in the Workflow API; see the template |
| (script mode) Omitting an explicit `model:` on `agent()` calls | Agents inherit the session model; state the model you priced, every call |
| Ending with "workflow complete" | Deliver the per-lane report contract: run id first line, gates against baselines, residuals by finding id |

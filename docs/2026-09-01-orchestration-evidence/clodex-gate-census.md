> UNAUDITED census, captured 2026-09-01 — verify before relying.
> Generated, not hand-typed: six reader agents each read one clodex component end to end on
> 2026-09-01 and classified every gate they found; this file is rendered from their structured
> returns by a script. The classification is a model's judgment and has not been re-audited by a
> human. Line numbers are as reported by the readers against the files at commit 1f6b1b2.

# clodex gate census — how much of the process is prose, artifact, or arithmetic

Tier definitions used by the readers (the estate's three tiers of control):

- **prose** — an instruction that can be silently skipped, leaving no trace.
- **artifact** — a required file or field that is conspicuously blank if skipped.
- **arithmetic** — a check with no opinion in it: exit code, hash compare, set difference, derived count.

## Totals across 6 components, 119 gates

| Tier | Gates | Share |
|---|---:|---:|
| arithmetic | 49 | 41% |
| artifact | 23 | 19% |
| prose | 47 | 39% |
| **total** | **119** | |

| Human in the loop | Gates | Share |
|---|---:|---:|
| no human | 84 | 70% |
| blocking — the run stops until a person answers | 28 | 23% |
| announce only | 7 | 5% |
| **total** | **119** | |

## Per component

| Component | Gates | arithmetic | artifact | prose | blocking-human |
|---|---:|---:|---:|---:|---:|
| `clodex Codex runner + contract layer` | 18 | 11 | 3 | 4 | 3 |
| `clodex-audit skill` | 12 | 4 | 5 | 3 | 2 |
| `clodex-build` | 32 | 12 | 5 | 15 | 4 |
| `clodex-plan/SKILL.md` | 18 | 7 | 5 | 6 | 5 |
| `clodex-ship` | 20 | 11 | 3 | 6 | 9 |
| `clodex-verify` | 19 | 4 | 2 | 13 | 5 |

## Every gate, grouped by tier

### arithmetic (49)

| Component | Line | Gate | Human |
|---|---|---|---|
| `clodex-audit skill` | L56 | Handoff check — `status` must show lane `audit`, stage `open`; stage `closed` → stop; other lane → hand back to `clodex` | no |
| `clodex-audit skill` | L109 | Engine append-time validation of a finding | no |
| `clodex-audit skill` | L218 | `release.state` must still read `not-started` at close | no |
| `clodex-audit skill` | L215 | Close the run (`run:closed`), archive when in a worktree, open follow-ons as new runs with `parent` set | no |
| `clodex-build` | L99 | A standing, unrevoked plan approval must exist before any batch opens | no |
| `clodex-build` | L119 | The plan file's recomputed sha256 must equal `plan.hash` | no |
| `clodex-build` | L188 | Change-boundary overlap between owned paths and `git.dirty_at_start` | yes-blocking |
| `clodex-build` | L398 | Runner exit code, not prose, decides the implementer's status | no |
| `clodex-build` | L432 | Boundary check on every implementer return, whatever its status | no |
| `clodex-build` | L557 | Micro-gate: the profile's `commands.test` exits 0 | no |
| `clodex-build` | L763 | Commit only if no owned path changed after staging | no |
| `clodex-build` | L861 | `plan:amended` carries the new hash and declares `required_review` | no |
| `clodex-build` | L894 | Satisfy the declared re-review before exit | no |
| `clodex-build` | L916 | Redo affected work in a NEW batch id | no |
| `clodex-build` | L932 | §12 exit blocker script | no |
| `clodex-build` | L1018 | Reconcile telemetry before handing off | no |
| `clodex-plan/SKILL.md` | L78 | Stage handoff check — is this run actually at stage plan? | no |
| `clodex-plan/SKILL.md` | L359 | plan:recorded — first plan only, hash bound | no |
| `clodex-plan/SKILL.md` | L572 | Envelope freshness — reviewed this exact plan | no |
| `clodex-plan/SKILL.md` | L675 | finding:recorded content vetting | no |
| `clodex-plan/SKILL.md` | L791 | The approval message and plan:approved bound to the current hash | yes-blocking |
| `clodex-plan/SKILL.md` | L825 | "What approved means" — the three (or four) manifest facts | no |
| `clodex-plan/SKILL.md` | L846 | On-disk plan file still equals plan.hash | no |
| `clodex-ship` | L263 | §3(a) review gate — plan file hashes to the approved hash, a standing plan approval exists, every amendment-declared re-review has a complete envelope against the CURRENT plan, no open findings | no |
| `clodex-ship` | L643 | Verification-debt acceptance in words, itemised class/reason/risk, inside §5 | yes-blocking |
| `clodex-ship` | L770 | Every step §4 derived either has a descriptor or is cut in writing with a `why` | yes-announce-only |
| `clodex-ship` | L1207 | §6 executor — action id must be in the authorization AND in the committed profile (or ship's own three); every schema-defined field must match the profile resolved; env_refs present; cwd inside the repo; no surviving placeholders | no |
| `clodex-ship` | L1457 | §7.1 dirty-file guard before ship's first write — `git status --porcelain --untracked-files=all -- <release files>` must be empty | yes-blocking |
| `clodex-ship` | L1511 | §7.2 authorized-content compare — each release file must be its pre-release self plus exactly the authorized edit (containment, not line membership) | yes-blocking |
| `clodex-ship` | L1699 | §7.2 staged-diff guard — `git diff --quiet -- <release files>` before the commit action runs | no |
| `clodex-ship` | L1760 | §7.4 push readback — remote ref sha must equal `git rev-parse HEAD` after the action returns | no |
| `clodex-ship` | L1808 | §7.6 verify-live — every deploy.verify_live check must exit 0 to record verified-live | no |
| `clodex-ship` | L1887 | §8 reconcile before retry — a pending step is settled against reality (git/remote/tag/host) before any retry, with `release:step:reconciled` appended first while still pending | yes-blocking |
| `clodex-ship` | L2097 | §10 exit gate — the full blocker sweep printing SHIP COMPLETE or NOT DONE | no |
| `clodex-verify` | L226 | §4 gate results: every gate rc 0 → continue; rc non-zero → stop, read the log, record a finding | no |
| `clodex-verify` | L445 | §7 $PLAN hard stop before invoking the runner | no |
| `clodex-verify` | L523 | §7 envelope provenance: sha256 of verify.diff must appear in the envelope's inputs, and status must be `complete` | no |
| `clodex-verify` | L679 | §10 completeness check → VERIFY COMPLETE / NOT DONE | no |
| `clodex Codex runner + contract layer` | L165 | Status reconciliation: the process outcome overrides the model's self-report | no |
| `clodex Codex runner + contract layer` | L159 | Model report must parse and match $defs.model_report or the invocation is `failed` | no |
| `clodex Codex runner + contract layer` | L510 | The runner's exit code, not its prose, is the authority | no |
| `clodex Codex runner + contract layer` | L447 | An envelope is owed on every death mode | no |
| `clodex Codex runner + contract layer` | L192 | Role determines the codex sandbox | no |
| `clodex Codex runner + contract layer` | L271 | An approval binds to the CURRENT plan hash and is revoked by an amendment | yes-blocking |
| `clodex Codex runner + contract layer` | L535 | A finding must be dispose-able on its merits | no |
| `clodex Codex runner + contract layer` | L334 | Duplicate finding ids and disposals of unknown findings are refused | no |
| `clodex Codex runner + contract layer` | L69 | Open findings block a clean count | no |
| `clodex Codex runner + contract layer` | L855 | Every envelope on disk must have a record in the run ledger | no |
| `clodex Codex runner + contract layer` | L950 | No changed path outside the batch's contract | no |

### artifact (23)

| Component | Line | Gate | Human |
|---|---|---|---|
| `clodex-audit skill` | L134 | Guardrail preamble in the report header — "guardrails: read-only <+ the live surfaces read, by name>" | no |
| `clodex-audit skill` | L83 | Premise correction is mandatory and early (§3), written even when all premises held | yes-blocking |
| `clodex-audit skill` | L188 | Report written in the §5 shape, then recorded as `verification:evidence` with its path + sha256 | no |
| `clodex-audit skill` | L204 | Every `source: "audit"` finding gets a disposition, presented with the report in one message | yes-blocking |
| `clodex-audit skill` | L176 | Routing section — every candidate and small item routed to a lane; "no action" is a routing | no |
| `clodex-build` | L284 | Write `$RUN_DIR/batch-<N>.contract.md` before running the implementer | no |
| `clodex-build` | L336 | Capture the pre-invocation baseline `batch-<N>.pre` before `batch:opened` | no |
| `clodex-build` | L676 | Every finding recorded, then disposed fixed / accepted / rejected | yes-blocking |
| `clodex-build` | L721 | Append `batch:reviewed` before committing | no |
| `clodex-build` | L899 | Re-approve the amended plan, in one message, bound to the new hash | yes-blocking |
| `clodex-plan/SKILL.md` | L186 | Direction gate predicate (Tests A/B/C + tie-break) | no |
| `clodex-plan/SKILL.md` | L451 | Direction checkpoint — shape card approved before the review loop | yes-blocking |
| `clodex-plan/SKILL.md` | L409 | Typed mandate — pre-granted gate classes for a delegated run | yes-announce-only |
| `clodex-plan/SKILL.md` | L490 | Codex plan review is default-on | no |
| `clodex-plan/SKILL.md` | L693 | Every finding recorded then disposed — four dispositions, nothing dropped | yes-blocking |
| `clodex-ship` | L315 | §3(b) unowned-commit disposition — every commit in start_head..HEAD that no batch owns is recorded as a finding and disposed by the user before the authorization, then itemised in it | yes-blocking |
| `clodex-ship` | L576 | §5 release authorization — one message, one yes, one authorization.json validated to AUTHORIZATION VALID before append | yes-blocking |
| `clodex-ship` | L1843 | §7A handoff artifact written from the template and recorded as an `approval:granted` with scope "handoff" | no |
| `clodex-verify` | L564 | §8 finding disposition: only the user may accept or reject, their words in the `note` (or a standing `finding-disposition` mandate with by: "mandate") | yes-blocking |
| `clodex-verify` | L643 | §9 debt entry shape: exactly class/reason/risk, risk naming a real failure rather than restating reason | no |
| `clodex Codex runner + contract layer` | L419 | Input artifacts are hashed into the envelope so a review can be bound to the artifact version | no |
| `clodex Codex runner + contract layer` | L193 | Nothing outside profile.actions may run at ship | no |
| `clodex Codex runner + contract layer` | L102 | A lane report must open with its run id, or the word "bare" | no |

### prose (47)

| Component | Line | Gate | Human |
|---|---|---|---|
| `clodex-audit skill` | L66 | Read-only charter (§2): no repo writes except the report and $RUN_DIR, no live mutation, no git state changes | no |
| `clodex-audit skill` | L99 | Every claim carries a tag with its method — `VERIFIED (<method>)` / `HYPOTHESIS (<what would confirm it>)` | no |
| `clodex-audit skill` | L103 | Load-bearing claims become findings (`finding:recorded`, `source: "audit"`, non-empty severity/summary, location/detail) | no |
| `clodex-build` | L89 | Do not re-append `stage:build:entered` on a resumed run | no |
| `clodex-build` | L262 | Create the run branch when `work_on_default: false` | yes-announce-only |
| `clodex-build` | L349 | Fold every `deferred-to-build` finding naming this batch into the implementer prompt | no |
| `clodex-build` | L463 | A STRAY is a scope change and is the user's call | yes-blocking |
| `clodex-build` | L550 | A release-owned file among the strays is restored, never folded | no |
| `clodex-build` | L579 | Quote the runner's pass count beside the rc | no |
| `clodex-build` | L584 | Test-inventory diff after a rebase or merge resolution | no |
| `clodex-build` | L638 | Five written delta questions, answered in chat | no |
| `clodex-build` | L629 | Stage owned paths by name — never `-A`, never `.`, never a directory holding unowned files | no |
| `clodex-build` | L649 | Run the Codex code-reviewer when the delta is consequential | no |
| `clodex-build` | L747 | The next batch does not open while any batch's verdict is not a pass | no |
| `clodex-build` | L779 | Name the owned paths on the `git commit` itself | no |
| `clodex-build` | L840 | Amendment: stop, do not open the next batch, state what broke | yes-announce-only |
| `clodex-build` | L1013 | Criterion 5 — every plan item done or amended | no |
| `clodex-build` | L1026 | Hand off to clodex-verify with the absolute run dir; do not append `stage:verify:entered` | no |
| `clodex-plan/SKILL.md` | L160 | Discovery — blocking/decision-bearing questions to the user | yes-blocking |
| `clodex-plan/SKILL.md` | L320 | Claims: line — collision-prone resources checked against .clodex/claims.json | no |
| `clodex-plan/SKILL.md` | L380 | Materiality test filling required_review on an amendment | no |
| `clodex-plan/SKILL.md` | L581 | Convergence — zero undisposed blocker/high/medium on a complete round against the current hash | no |
| `clodex-plan/SKILL.md` | L630 | Round budget — 3 rounds, hard stop, only the user funds more | yes-blocking |
| `clodex-plan/SKILL.md` | L760 | verification:declared — at least one evidence class, declared last | no |
| `clodex-ship` | L581 | Typed mandate is excluded from this gate — release authorization and debt acceptance are answered by the user in person in every run, delegated lanes included | yes-blocking |
| `clodex-ship` | L341 | §3(c) one Codex code-reviewer round over the whole release diff, default-on with a single mechanical skip predicate | no |
| `clodex-ship` | L1324 | always-ask-exact — the literal filled argv is shown and re-approved in the same turn, every execution, every retry, every resumed session | yes-blocking |
| `clodex-ship` | L1815 | §7.6 empty verify_live — the user must look and say what they see | yes-blocking |
| `clodex-ship` | L2243 | telemetry-sync before run:closed | no |
| `clodex-ship` | L2256 | Archive on close when the run lives in a worktree | no |
| `clodex-verify` | L103 | Stage-check on entry: append `stage:verify:entered` only if stage is `build`; hand back for open/plan/ship/closed | no |
| `clodex-verify` | L120 | Resume map: read declared/evidence/debt before appending anything | no |
| `clodex-verify` | L131 | Malformed-run stop: no declared classes, or `plan.path` null → hand back to clodex to close/abandon | yes-blocking |
| `clodex-verify` | L148 | §2 prohibitions: no commit/add/tag/push/checkout/stash, no tracked-file edits, no artifacts outside $RUN_DIR | no |
| `clodex-verify` | L221 | §4 rc-capture form: explicit if/else, and `${PIPESTATUS[0]}` under `set -o pipefail` when piped | no |
| `clodex-verify` | L276 | §5 `result` must answer the plan's declared `proof` — if the proof names a thing, result names that same thing | no |
| `clodex-verify` | L347 | §5 visual: the user looks at the rendered artifact and accepts it | yes-announce-only |
| `clodex-verify` | L385 | §5 client-artifact: not bookable as debt while the surface exists; 'no mailbox access' is a blocker to raise with the user now | yes-blocking |
| `clodex-verify` | L428 | §7 worker trigger check (three conditions) and the say-so-in-chat requirement when skipped | no |
| `clodex-verify` | L586 | §8 outcome choice A/B/C put to the user in one message with command, rc, failing output and affected class | yes-blocking |
| `clodex-verify` | L596 | §8 outcome A: the run ends here; clodex closes it; you append neither run:closed nor run:opened; leave the finding open | yes-blocking |
| `clodex-verify` | L658 | §9/Overview: no debt gate here — do not ask the user to approve, waive, or weigh debt | no |
| `clodex-verify` | L810 | §11 exit: hand off to clodex-ship with the absolute run dir; say the five items, including every debt entry in full and 'nothing about it has been accepted yet' | yes-announce-only |
| `clodex Codex runner + contract layer` | L5 | "A stage may transition only on a valid envelope whose status is complete" | no |
| `clodex Codex runner + contract layer` | L217 | `always-ask-exact` actions get their literal filled argv approved every time | yes-blocking |
| `clodex Codex runner + contract layer` | L56 | Production proof needs a named watcher, a deadline and a terminal-state readback | yes-announce-only |
| `clodex Codex runner + contract layer` | L29 | CLIENT-ACCEPTED requires the named operator's confirmation | yes-blocking |

## The 28 gates that stop an unattended run

Each of these blocks until a person answers. An orchestrator that must not wake anyone has to
either pre-answer it in the brief, convert it into a finding a typed mandate can dispose, or park
the lane. The two that are structurally un-grantable by any mandate are release authorization and
verification-debt acceptance.

### `clodex-audit skill` L83 — Premise correction is mandatory and early (§3), written even when all premises held

*If skipped:* The report's "## Corrections to the prompt's premises" heading (L140) is empty — the section existing is explicitly the forcing function. The human-blocking part is narrower than it reads: only a correction that *re-scopes* the audit must reach the user before continuing (L89-90); a non-re-scoping correction can sit in the report.

### `clodex-audit skill` L204 — Every `source: "audit"` finding gets a disposition, presented with the report in one message

*If skipped:* Undisposed findings stay `open` in the snapshot and show in `status`; `state/counts.py` L57/L67 exits non-zero on any open finding — but clodex-audit never invokes counts.py, so the ledger check exists and is not wired in. The human gate degrades to non-blocking whenever a standing `finding-disposition` mandate is in force (L208-210).

### `clodex-build` L188 — Change-boundary overlap between owned paths and `git.dirty_at_start`

*If skipped:* The L199-228 script computes `overlap:` bidirectionally with directory expansion. Any listed path requires stopping and taking it to the user under clodex §5B's three legal outcomes — 'Do not paraphrase them and do not invent a fourth' (L248-252). If the whole section is skipped, another session's uncommitted file lands inside a clodex commit with nothing downstream noticing (L241-243). No event is required by this section, so a skipped §3 leaves no trace in the manifest.

### `clodex-build` L463 — A STRAY is a scope change and is the user's call

*If skipped:* L463 and L497-501: capture the diff, show it, offer exactly two ways forward (amend to own the path, or restore and re-run), and 'Restore only after they say so.' The detection is arithmetic but the escalation and the restore authorization are prose — an agent can amend or restore unilaterally and the log records only the amendment note. L480-487 adds a second-source rule (the implementer's own record must claim the path) with the hard constraint that 'a restore is never offered for a path the run cannot prove the implementer touched'.

### `clodex-build` L676 — Every finding recorded, then disposed fixed / accepted / rejected

*If skipped:* L676-684: 'only the user may accept or reject one (and their words go in the `note`)' — or a standing `finding-disposition` mandate with `by: "mandate"` citing it. An undisposed finding stays `disposition: "open"` and §12's L950-953 raises a blocker, so omission is caught arithmetically. What is NOT caught: `by: "user"` is a string the agent types, so a fabricated user acceptance passes every check. L683-684 makes an `accepted` blocker a legitimate end state that survives into ship.

### `clodex-build` L899 — Re-approve the amended plan, in one message, bound to the new hash

*If skipped:* L899-914. The presentation is prose (what changed, affected completed work, re-review outcome, and that a `dirty-fold` acknowledgment was revoked and is being re-granted), but the `approval:granted` event is mechanically bound: 'approval binds to plan hash X but the current plan hash is Y' is refused (L911-912), and §12 blocks without a standing approval. As with finding dispositions, `by: "user"` is unverified text. L1051 restates it: 'There is no amendment that costs nothing.'

### `clodex-plan/SKILL.md` L160 — Discovery — blocking/decision-bearing questions to the user

*If skipped:* Nothing is conspicuously blank. The plan silently guesses at user-observable behavior, or (the opposite failure) burns a round trip on a question a file answered. Only the plan's `## Assumptions` section indirectly shows the choice.

### `clodex-plan/SKILL.md` L451 — Direction checkpoint — shape card approved before the review loop

*If skipped:* An `approvals` entry with scope "direction" is missing, which §1's resume map row 2 (L99) and §10's fourth fact (L835-836) both test — but only in prose; the reducer does not enforce it. Skipping it means review rounds harden a shape nobody approved (the stated failure at L214-218: five reviewed rounds on the wrong architecture).

### `clodex-plan/SKILL.md` L630 — Round budget — 3 rounds, hard stop, only the user funds more

*If skipped:* Nothing counts rounds. No event, field, or command derives "rounds so far" as a budget check (the `round` field exists on findings but is only read for the severity trend). An agent can run 1 round or 11 and no artifact is conspicuously blank; the L639 rule that a mandate cannot fund rounds past 3 is likewise unenforceable.

### `clodex-plan/SKILL.md` L693 — Every finding recorded then disposed — four dispositions, nothing dropped

*If skipped:* A finding left `open` is visible in the manifest and blocks §10's third approval fact — that part is a real artifact gate. But the disposition VALUE is a free string to the engine (reducer.py:358; snapshot.schema.json:100 types it ["string","null"]), so any non-"open" word satisfies the fact. `accepted`/`rejected` need the user's explicit words quoted in `note` (or a mandate citation) — that requirement is prose.

### `clodex-plan/SKILL.md` L791 — The approval message and plan:approved bound to the current hash

*If skipped:* The hash binding is engine-enforced (reducer.py:284-289 refuses "approval binds to plan hash 'X' but the current plan hash is 'Y'"). The human part — the five-part message and actually waiting for yes — is prose; `by: "user"` is a string the agent writes and nothing distinguishes it from `by: "mandate"` at the engine level.

### `clodex-ship` L581 — Typed mandate is excluded from this gate — release authorization and debt acceptance are answered by the user in person in every run, delegated lanes included

*If skipped:* A delegated/mandated lane would self-approve its own release and its own shipped debt. Nothing mechanical reads the mandate's grants here; the only defense is this paragraph and the instruction to say so when a mandate claims otherwise.

### `clodex-ship` L315 — §3(b) unowned-commit disposition — every commit in start_head..HEAD that no batch owns is recorded as a finding and disposed by the user before the authorization, then itemised in it

*If skipped:* A commit nobody named rides into the release invisibly (clodex-verify §8 actively invites the user to fix and commit things themselves). Detection is arithmetic (set difference over batches[].commit), but the disposition is an artifact: an undisposed finding leaves `disposition: open`, which §3(a)'s re-run and §10 both block on. `rejected` stops the run — removing a commit is the user's to do.

### `clodex-ship` L576 — §5 release authorization — one message, one yes, one authorization.json validated to AUTHORIZATION VALID before append

*If skipped:* §6's executor refuses to run anything: it reads argv out of the standing authorization and stops (rc 64) when there is not exactly one (L1219-1225). §10 blocks on 'expected exactly one standing release authorization'. The validator (L802-1128) is arithmetic on the payload — schema-derived field comparison, step-list completeness, cut entries with reasons, pathspec equals the release files, no surviving placeholders, debt superset — and prints DO NOT APPEND with a problem count.

### `clodex-ship` L643 — Verification-debt acceptance in words, itemised class/reason/risk, inside §5

*If skipped:* §5's validator refuses the payload for any recorded debt entry not present in accepted_debt (L1119-1122), and §10 blocks on the same set difference keyed on whole entries — class+reason+risk, not class alone (L2113-2125). If the user refuses a debt entry the release cannot happen at all; the only ways out are acceptance or `abandoned` (L1141-1146). An empty debt list must still be stated out loud (L693-695).

### `clodex-ship` L1324 — always-ask-exact — the literal filled argv is shown and re-approved in the same turn, every execution, every retry, every resumed session

*If skipped:* The executor's only check is `os.environ.get("CONFIRMED") != "confirmed-by-user"` — an env var set by the same agent that is supposed to have asked. No event records that the ask happened, so §10 cannot distinguish an asked deploy from an unasked one. The policy itself is protected arithmetically (the committed profile, not the typed descriptor, decides the policy — L1349-1363), but the ask is not.

### `clodex-ship` L1457 — §7.1 dirty-file guard before ship's first write — `git status --porcelain --untracked-files=all -- <release files>` must be empty

*If skipped:* Somebody else's edit to the changelog or version file gets overwritten and swept into the release commit. Runs once, keyed on release.steps holding no bookkeeping entry; on a resume it is replaced by §8's stricter bookkeeping row. Resolution is the user's: fold with a recorded `dirty-fold` approval, isolate, or abort — never checkout/stash.

### `clodex-ship` L1511 — §7.2 authorized-content compare — each release file must be its pre-release self plus exactly the authorized edit (containment, not line membership)

*If skipped:* A package.json carrying the right version AND a dependency somebody added would pass a version-only check; a changelog line duplicated into last release's section would pass a line-membership check. Prints RECONCILE done / failed / STOP; only `done` continues into staging, STOP goes to the user and nothing is staged or overwritten.

### `clodex-ship` L1815 — §7.6 empty verify_live — the user must look and say what they see

*If skipped:* A release goes out unproven and gets recorded as live. The rule is explicit that zero checks is not a pass, and that if the user will not look the honest record is deploy-failed meaning 'not proven live'. There is deliberately no state for 'deployed, and nobody will ever check' (L1824).

### `clodex-ship` L1887 — §8 reconcile before retry — a pending step is settled against reality (git/remote/tag/host) before any retry, with `release:step:reconciled` appended first while still pending

*If skipped:* A deploy, publish, or payment gets re-run 'to be safe'. The deploy row's default is STOP: retry requires an affirmative negative — a version-aware check (marker at a word boundary, and strong enough: contains a dot or ≥4 chars, L1919-1923) that returned the OLD version. Unreachable reality → leave it pending and tell the user; a wrong `done` is a lie the next session acts on.

### `clodex-verify` L131 — Malformed-run stop: no declared classes, or `plan.path` null → hand back to clodex to close/abandon

*If skipped:* The run proceeds with no definition of done to prove. §10 does catch the empty-declared case as a blocker (L687-688), but the null-plan case is caught only by §7's `[ -z "$PLAN" ]` guard and only if §7 runs at all — §7 is optional (L426-437), so a null-plan run whose triggers do not fire reaches §10 and can print VERIFY COMPLETE.

### `clodex-verify` L385 — §5 client-artifact: not bookable as debt while the surface exists; 'no mailbox access' is a blocker to raise with the user now

*If skipped:* Nothing enforces it and there is no event, field, or §10 rule for it. Worse, the class is unreachable through the mechanical check at all: §10's `CLASSES` tuple (L684) omits `client-artifact`, so an honest client-artifact evidence item is flagged `class 'client-artifact' is not one of: tests, real-data, live-check, visual` (L711-713) and the run prints NOT DONE. The pressure this creates is to book it as debt or drop the class — the exact two outcomes the section forbids.

### `clodex-verify` L564 — §8 finding disposition: only the user may accept or reject, their words in the `note` (or a standing `finding-disposition` mandate with by: "mandate")

*If skipped:* §10 blocks on any finding with `disposition: "open"` (L715-718), so an undisposed finding does stop VERIFY COMPLETE. What is unenforced is authorship: a self-disposed `accepted` with an invented note passes §10 identically to a real one.

### `clodex-verify` L586 — §8 outcome choice A/B/C put to the user in one message with command, rc, failing output and affected class

*If skipped:* The run either stalls at verify (blocking the next run in the repo, L613-617) or the agent silently picks C and records `accepted` on the user's behalf.

### `clodex-verify` L596 — §8 outcome A: the run ends here; clodex closes it; you append neither run:closed nor run:opened; leave the finding open

*If skipped:* 'The router allows one open run per repo, so a run parked at verify stops the follow-on from opening at all — and the router's resume offer routes stage verify straight back to this skill' (L613-616): an infinite bounce. Also loses the run's evidence and debt, which L619-622 requires be said out loud.

### `clodex Codex runner + contract layer` L271 — An approval binds to the CURRENT plan hash and is revoked by an amendment

*If skipped:* An approval of an older plan version would sit there looking live after the plan changed. reducer.py _on_approval L271-301 refuses an approval whose plan_hash is not the current one. The human-in-loop part is weaker than it looks: L294 records `"by": event.get("by", "user")`, so an approval event that omits `by` is recorded as the user's.

### `clodex Codex runner + contract layer` L217 — `always-ask-exact` actions get their literal filled argv approved every time

*If skipped:* A destructive release action would run under a blanket authorization. profile.schema.json L217-221 declares the policy enum; nothing in this component enforces it — enforcement lives in clodex-ship, and the schema description is the whole contract from here.

### `clodex Codex runner + contract layer` L29 — CLIENT-ACCEPTED requires the named operator's confirmation

*If skipped:* A SOW deliverable closes on a supervised run instead of the operator's word. templates/scenario-card.md L29 is a single markdown line — `**Accepted**: <date + operator's words … blank until then>` — with no validator.


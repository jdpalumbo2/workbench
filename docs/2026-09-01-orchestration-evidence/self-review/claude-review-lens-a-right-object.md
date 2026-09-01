> UNAUDITED adversarial review, captured 2026-09-01 — verify before relying.
> Produced by an independent Claude session with no access to this session's reasoning.
> Its findings were dispositioned in the plan's section C; some were accepted, some corrected,
> some rejected. The review is preserved verbatim so the dispositions can be checked.

# Lens A — is the rigor pointed at the right object?

I have what I need. Writing the review.

---

## Findings

**1. BLOCKER | B.10, hardening table L1051 (and B.3's whole topology)** — `--bare` forces metered API billing, which inverts the plan's premise.

B.10 mandates `claude -p --bare` and annotates only one consequence: *"Note it also skips CLAUDE.md, so the orchestrator must pass context explicitly."* The installed CLI (2.1.224, `claude --help`) states the other one: *"Anthropic auth is strictly ANTHROPIC_API_KEY or apiKeyHelper via --settings (OAuth and keychain are never read)."* The plan's own evidence says it in the same sentence it quoted from — `research-anthropic-official-guidance.md:59`: *"`--bare` also skips OAuth/keychain credentials, so you must set `ANTHROPIC_API_KEY`."* The plan quoted the security half of that line into B.10 and dropped the auth half.

Consequence: every `claude -p --bare` lane in B.3 — plan, build, verify, brief authoring, the Opus-5 readback, gate 13, the morning synthesis — bills real API dollars, not the Max subscription. The document that exists to protect subscription quota specifies a flag that leaves the subscription entirely. Gate 2's `$8.00` per-lane and gate 1's `$40.00` nightly ceiling stop being notional accounting and become an actual credit-card number, and nowhere does the plan say so.

**Fix:** state the auth mode explicitly as a design decision. Either (a) drop `--bare`, accept the hooks/MCP exposure, and confine lanes to repos Johnny wrote (which is all of them) — the security argument in B.10 is about untrusted repos; or (b) keep `--bare`, declare that overnight lanes are API-billed, and re-derive every budget number in B.5 as dollars-you-owe rather than quota-you-have. Assumption table entry #4 covers Codex budget; there is no equivalent entry for Claude, and there needs to be.

---

**2. BLOCKER | B.6 gate 7 + B.9** — the forged-approval gate cannot see the forgery B.9 quotes.

Gate 7: *"`grep '\"by\": *\"user\"' events.ndjson` must return **zero** in an unattended run."* B.9, four paragraphs later, names the actual hole: `reducer.py:294` is `"by": event.get("by", "user")` — *"an approval event that omits `by` is recorded as the user's."* I verified that line. An event that **omits** `by` contains no `"by": "user"` substring in `events.ndjson`. Gate 7 greps the raw ledger and returns zero. It passes on precisely the event B.9 identifies as the forgery vector.

Second, unresolved contradiction: `clodex-plan` §6's literal mandate event is `{"e": "approval:granted", "scope": "mandate", "by": "user", ...}`. B.5 requires every unattended lane to carry a standing mandate. So either the mandate event lands in the lane's `events.ndjson` with `by: "user"` — and gate 7 fails **every** dispatched lane — or something appends it without that attribution, which is the forgery. The plan never says who appends the mandate event or with what `by`.

**Fix:** run gate 7 against `clodex_state.py rebuild` output, not the raw ledger — the manifest is where the default materializes. Ship B.9's change 2 (`by` required on `approval:granted`) as a hard prerequisite, not as a "makes gate 7 redundant" nice-to-have, and add a fourth `by` value (`orchestrator`) so the mandate has a legal attribution that is neither the user nor a lie.

---

**3. BLOCKER | B.6 gate 13, and "Gate 13 deserves its own paragraph"** — the held-out criteria are a paraphrase of a section the worker is required to read, scored by the same model family that wrote them, against files rather than the object.

Three separate failures in the centrepiece:

*(a) It is not held out.* The acceptance file is *"three to five sentences describing what a person should be able to observe when this works, in the operator's terms."* B.5 requires the brief's §4 to carry *"operator, action, expected outcome and production proof… That is the shape card, written by Opus at brief time."* Those are the same content, written by the same session, minutes apart, into two files. The worker reads one of them. Add §6 (*"what the client/user actually experiences"*), §7 (guardrails "as testable sentences") and §8 ("done when: <checkable>") from `templates/lane-brief.md` and the worker has the acceptance criteria in three independent forms. The hold-out is nominal.

*(b) Same-family self-scoring.* Opus writes the acceptance file; a fresh Opus session judges against it. The plan's own argument against exactly this is two pages earlier: *"the reason for the cross-family split is **correlated blind spots**, not raw capability — a model reviewing its own work is confidently wrong in the same direction."* The plan enforces cross-family review on the diff (gate: Codex reviews Claude's code) and waives it on the one gate it calls tier 4. The rigor is cross-family where it is cheap and same-family where it matters.

*(c) It does not reach the object.* *"A fresh Opus session gets the acceptance file plus **the lane's artifacts**."* The lane's artifacts are a branch, a run dir, a report. Ship never runs, so nothing is deployed; there is no email, no rendered page, no tree in the operator's account. The plan asserts *"Gate 13 is the gate that opens the email"* and then gives the judge no mailbox, no browser, and no deployed thing to open. Meanwhile B.4 gives the *client-artifact readback* real capability (`claude -p` + browser/MCP, Opus 5) — and runs it **inside the lane**, i.e. the worker checking its own client-visible outcome. The check with the capability isn't held out; the check that's held out has no capability.

*(d) No disposition path.* Nothing says what a gate-13 `no` does. It is not in B.8's three legal responses, has no park record, no appeal, no re-run. B.12 step 7 says only "Gate 13: acceptance files + the held-out check." A false negative from an ungrounded judge has no route back.

**Fix:** (i) Have a *different family* write the acceptance file from the original ask — Codex Sol at `xhigh`, read-only, before the brief exists — so the brief author never sees it and the judge never wrote it. (ii) Give gate 13 the same substrate B.4 gives the readback (browser/MCP + a real target) or drop the claim that it opens the email and call it what it is: a documentation-consistency check. (iii) Add gate 13 to B.8's protocol with an explicit verdict: `no` → park with the acceptance file and the lane's artifacts side by side, so the morning question is answerable.

---

**4. BLOCKER | B.3 L771 vs B.6 gate 12 vs B.8** — the lane's stated deliverable is produced by a stage the plan says will not run, behind a gate no mandate can pass.

B.3: *"stage ship    NOT RUN.  Lane stops at a reviewed branch + handoff artifact."* B.8: *"A lane that finishes clean parks at ship with its handoff artifact written — which is `handed-off`."*

The handoff artifact is `clodex-ship` **§7A** (L1831). §7A opens: *"After the final review (§3) and the authorization (§5…), and after the push step if this release has one."* §5 (L576) is the release authorization: *"No mandate reaches this gate… answered by the user, in person, in every run — a delegated lane included."* And `clodex-ship` §10 (L2211-2217) blocks `handed-off` when the `scope: "handoff"` approval is missing. So:

- Ship not run → no handoff artifact → **gate 12 checks a file that cannot exist**, and either fails every lane or is quietly skipped.
- Ship run → it stops dead at §5 waiting for a human, before §7A.
- `handed-off` is unreachable unattended in both branches. B.8's *"which is `handed-off`, the terminal state clodex already documents as the orchestrated lane's honest ending"* is wrong as a matter of the state machine, not of intent.

**Fix:** pick one. Either (a) split §7A out of ship into a stage a lane can reach without the §5 gate — a real, deliberate clodex change with its own review, listed as a prerequisite in B.12; or (b) accept that the lane's terminal artifact is the **lane report**, delete gate 12, and stop claiming `handed-off`. Option (a) is a change to clodex's human-owned core and belongs in assumption #3's "deliberately, as a separate decision" bucket — it is currently smuggled in as a topology diagram.

---

**5. HIGH | B.8 "Park, don't prompt"; assumption that the mandate survives the night** — count the ways a night ends with everything parked, because the plan does not.

B.8: *"Pre-answer it in the brief… **This is where most of the 28 go**."* Audited against the census's 28 blocking gates, what a brief plus the three-verb mandate can actually pre-answer is: `clodex-plan` L791 (plan-approval), L451 (direction-approval, conditional), L693, `clodex-build` L676, `clodex-verify` L564 (finding-disposition), plus arguably L160 via brief §10 and L188 via a clean worktree. That is **~7 of 28**, not "most." The other 21 park or are structurally out of reach.

Worse, four of them park *reliably*, not exceptionally:

- **Any amendment kills the mandate permanently.** `clodex-plan` §6: *"The mandate binds to the plan hash like every approval, so **every amendment revokes it**… re-grant it against the new hash on the authority that granted it first."* The authority is the user, asleep. And an agent appending the re-grant is the exact `by: "user"` write gate 7 forbids. Meanwhile `clodex-build`'s own trigger description includes *"when a plan assumption turns out to be wrong while implementation is already in flight"* — amendment is a normal build event, not an exception. One amendment → mandate gone → `clodex-build` L899 (re-approve, blocking) → park, unrecoverably.
- **Any stray parks the build.** `clodex-build` L463: *"A STRAY is a scope change and is the user's call."* Not in the mandate's three-verb vocabulary.
- **Round 3 with blockers still arriving parks the plan.** `clodex-plan` L630: *"**Only the user funds rounds past 3 — a standing mandate cannot**."* B.7 keeps the budget at 3 and never mentions that hitting it is a hard park.
- **Every client-visible lane parks at verify.** `clodex-verify` §5 (L385): *"'No mailbox access' is not debt — it is a blocker to raise with the user now."* An unattended 4am lane has no mailbox, no deploy, no operator. So the exact class of work this document's thesis is about — client-visible surfaces — is the class that cannot complete unattended. B.7's *"Full: … client-artifact readback + gate 13. **Never skipped, never booked as debt**"* is unachievable in the topology B.3 describes.

**Fix:** enumerate all 28 census gates in the skill with a per-gate verdict — *pre-answered by brief §N* / *mandate-covered* / *parks* — and publish the count. Then state the honest scope: overnight lanes are for work whose direction gate is `no` and whose surfaces are internal. If client-visible work is in scope, the design needs a mechanism for the artifact to exist before verify runs (a staging deploy the lane owns), and that mechanism is not in this plan.

---

**6. HIGH | B.6 gates 1 and 2** — the budget gate reads the wrong window, and the per-lane ceiling does not measure the substrate the plan puts the work on.

Gate 1: *"Codex `used_percent` from the newest rollout < ceiling."* The probe (`local-harness-probes.md` §2) shows `"primary": {"used_percent": 9.0, "window_minutes": 10080}, "secondary": null` — the 7-day window, with the second meter unpopulated. The plan's own evidence names the binding constraint elsewhere: *"Codex operates on rolling 5-hour windows for local messages and cloud chats"* (`research-codex-headless-practitioner-reports.md:66`) and *"roughly 6–7 fully-used 5-hour windows exhausts the weekly cap"* (:94). A four-worker overnight fan-out is a 5-hour-window event by construction. Gate 1 reads 12% weekly, dispatches everything, and the night dies in a 5-hour lockout with every lane failed mid-stage.

Gate 2: *"Sum `total_cost_usd` per lane; over → kill the lane."* `total_cost_usd` comes from the Claude envelope. But B.3's whole argument is that **Codex is the heavy executor** — implementation, plan review, code review all run inside the lane through `run-codex.sh`. None of that appears in `total_cost_usd`. So the per-lane ceiling governs the cheap half and leaves the expensive half unmetered, and the plan itself notes *"there is **no per-run cost cap in the Codex CLI**."* Both gates are preconditions checked between lanes; a single lane can spend the entire weekly window and gate 1 finds out afterward.

Also unsurfaced: `research-quota-protecting-orchestration.md:200` flags this as the sweep's own biggest gap — *"SUBSCRIPTION quota accounting is undocumented… all the tiering evidence optimizes dollars, and the binding constraint here is a quota."* The whole B.4 model table optimizes dollars. That limitation belongs in the "what I had to guess" table and is not there.

**Fix:** gate 1 must read both windows — poll `secondary` and treat `null` as "unknown, refuse to fan out." Add an in-flight Codex meter: sample `used_percent` after every `run-codex.sh` return inside the lane (the runner already writes an envelope per invocation) and give the lane a Codex-percent ceiling alongside its dollar ceiling. Set the OpenAI dashboard spending limit as B.12 step 0, not as a parenthetical.

---

**7. HIGH | B.4 "Morning synthesis" + B.11 L47-49** — the one artifact a human reads is the only artifact with no gate on it.

Gate 10 reconciles the **lane report** against the ledger. Gate 12 checks the **handoff**. Gate 9 checks the report's first line. Nothing checks `MORNING-REPORT-<date>.md`, which B.4 describes as *"The one artifact a human reads."* It is authored by Opus 5 at high effort from the lane reports — i.e. by summarizing worker prose, which is exactly what B.7 forbids elsewhere: *"the reviewer's output is synthesized by the caller, **never forwarded verbatim**."* A morning report that laundres a lane's own account of itself into a confident paragraph is the failure mode the entire document was written against, reproduced at the top of the stack.

B.11 makes this worse by accident: it deletes L47-49 (*"the orchestrator personally reads every deliverable in full"*) on the grounds that *"The orchestrator is a script and cannot read"* — and then B.4 puts an Opus 5 reader back in, ungoverned. The deletion's justification does not survive the design that replaces it.

**Fix:** the morning report is generated by the script from the ledger — lane, stage reached, gate results, park records verbatim, costs — with the model's synthesis confined to a labelled, clearly-subordinate section. Apply gate 10 to it: every integer in it is regenerated from `counts.py` and the orchestrator ledger. And specify a length; Anthropic's own measurement, quoted in "What actually saves quota," says a five-section memo costs 3x a one-line answer, and this report has no format spec at all.

---

**8. HIGH | A.1 migration + A.2 + A.3 step 6** — section A ships a fleet-wide hard stop, and reproduces the exact failure it diagnoses.

A.1: *"Bump `schema_version` to `2` with `bootstrap` required. That makes every existing profile stale by the *existing* mechanism at L488-493 — which is the correct blast radius."* A.2's table makes "Contract moved?" a **stop**, and `clodex/SKILL.md` check 7 makes a lane with an uncommitted/invalid bootstrap **stop, never interview**. So the moment §A lands, every repo's every lane stops at preflight until a human re-interviews from the main checkout. B.12 puts §A at step 4, a dependency of step 5. The build order installs a fleet-wide block before the thing that would route around it exists.

Then the same mechanism fires on every skill release. A.2: *"Skill moved? | `bootstrap.clodex_version` vs `$CLODEX_HOME/VERSION` | **re-derive**."* The softening is scoped narrowly — *"In a linked worktree, **'repo moved'** is recorded, not enforced"* — and A.3 step 6 is unqualified: *"**Never from a lane.** A worktree that needs re-derivation says so and stops."* Since A.1 says `VERSION` *"moves on every skill change whether or not the schema moved,"* every workbench commit that bumps it parks every worktree lane in the estate at preflight. That is a night where nothing runs, caused by an unrelated skill edit.

And the mechanism itself: A.1 diagnoses `schema_version` as *"`enum: [1]` … and has never moved"* — a counter nobody bumps — then introduces a second monotonic counter with no stated bump owner, no bump trigger, and no test that it moved. The plan notes *"a `VERSION` file to the skill directory (there is none today — I checked)"* and stops there. A `VERSION` that nobody bumps is `schema_version` again; a `VERSION` that bumps on every commit parks the fleet. Neither failure is addressed.

**Fix:** (i) make `bootstrap` optional in schema_version 1 and let `bootstrap_check.py` report its absence as `re-derive`, not `stop` — this gets the currency signal without the flag-day. (ii) Compare `clodex_version` on **minor** version, not exact string, so a patch release does not park anything. (iii) Name the bump owner and add a test that fails when `SKILL.md` changed and `VERSION` did not — otherwise the whole mechanism is prose again. (iv) Exempt worktrees from the "skill moved" verdict the same way A.2 exempts them from "repo moved."

---

**9. HIGH | B.6 gate 6** — the gate that most looks like "the review was clean" is the one the standing mandate most directly neuters.

Gate 6: *"No open findings | **arithmetic** | `counts.py <run-dir>` exit code."* I read `counts.py`: it exits 1 iff `recorded - dispositions` is non-empty (or a line failed to parse). It proves a disposition line exists per finding. It says nothing about *which* disposition. Under the standing mandate B.5 requires — which grants `finding-disposition` precisely so the lane does not have to ask — a lane closes gate 6 by writing `accepted` on every finding it received, from the same session that received them, with `by: "mandate"`.

So gate 6 passes when the lane auto-accepted 13 blockers. A reader of the morning report sees "gate 6: green" and concludes the reviews came back clean. Concretely: **gate 6 passes when zero findings were actually fixed.**

**Fix:** split it. Gate 6a: no open findings (`counts.py` rc). Gate 6b, also arithmetic: **zero blocker/high findings disposed `accepted` under `by: "mandate"`** — a mandate may dispose medium and low; accepting a blocker without a human is the decision the mandate exists to *avoid*, and `clodex-plan`'s own round-budget exit condition is already severity-based (*"zero blocker/high findings after dispositions"*). A lane with a mandate-accepted blocker parks.

---

**10. MEDIUM | B.6 gate 3 vs `local-harness-probes.md` §4** — model readback covers Claude only, so the one model decision the plan actually recommends changing is the one it cannot verify.

Gate 3: *"`modelUsage` keys ⊆ the stage's allowed set."* `modelUsage` is a Claude envelope field. The plan's own probe says, of Codex: *"The **model that actually ran is not echoed** anywhere in the event stream. A caller knows which model it *requested*; the transcript does not confirm which model *answered*."* Codex is 4 of the ~10 dispatch types in B.3 and, by B.3's own framing, *"already the heavy executor."* B.4's boldest recommendation — implementer on `gpt-5.6-terra`, not Luna — is therefore unverifiable by the gate designed to verify model choice, and Codex's documented *"run-to-run variability"* plus the roster's deprecation upgrade-paths (`gpt-5.4 → terra`, `gpt-5.4-mini → luna`) are exactly the silent-substitution risk gate 3 exists for.

The probe already names the fix and the plan does not take it: *"The rollout file under `~/.codex/sessions/` does carry richer turn metadata — that is where a verification check has to look."*

Second, smaller: B.3 nests an Opus 5 readback *inside* a Sonnet 5 verify session. Gate 3 for that stage must therefore allow both, which makes it unable to catch a Sonnet→Opus escalation — and it puts model selection back inside a model, against B.2's whole argument.

**Fix:** extend gate 3 to Codex via the rollout metadata, per the probe. Hoist the Opus readback out of the Sonnet session into its own orchestrator-dispatched step with a single-element allowed set.

---

**11. MEDIUM | B.6 gates 9, 10, 11** — three gates that produce artifacts nobody can fail.

- **Gate 9** (*"First line matches `^r-\d{4}-\d{2}-\d{2}-[a-z]$` **or the literal `bare` plus a reason**"*). The escape hatch makes it unfailable: a lane that never invoked clodex at all passes by typing `bare: <anything>`. Under the original design a human read the reason; under an unattended orchestrator nothing does. And the orchestrator **dispatched** the lane — it knows the run id, and can read `.clodex/<run-id>/`. Checking a regex when you hold ground truth is a proxy check by choice.
  **Fix:** compare the first line to the run id the orchestrator dispatched. Treat `bare` as a park, not a pass.

- **Gate 11** (*"The plan's `## Direction` section exists and has all five sub-fields non-empty"*). Checks that a model instructed by `clodex-plan` §4 to write a shape card wrote a shape card. Zero discriminating power. Its precondition is worse: it fires *"when the direction gate is yes"* — and per `clodex-plan` §4 that answer is written **by the plan-authoring session about its own plan**, with an explicit tie-break toward `no`. A lane avoids gate 11 by answering `no`. Also the field count is wrong: §4's yes row names six (premise · operator and action · expected outcome per surface · production proof · comps · taste criteria when applicable), not five.
  **Fix:** make the direction-gate answer an orchestrator input from `run-plan.json`, set by the brief author at the same time as the acceptance file, not a self-assessment by the lane. Then gate 11 compares the plan's Direction section against the brief's §4 shape card for *agreement*, which is a check something can fail.

- **Gate 10** (*"Every integer in the report's counts section is regenerated from `counts.py` and compared"*). The estate rule it implements already says counts are generated from the ledger and never hand-typed. If the lane follows the rule, gate 10 compares `counts.py` to `counts.py`. It only bites when the rule is broken — a rule the design assumes is followed. Keep it (it is nearly free), but it is not evidence of anything, and listing it among "11 of 14 arithmetic" inflates the apparent rigor.

---

**12. MEDIUM | A.6 and B.11** — the "every addition is paid for by a deletion" accounting is measured on a ledger chosen to make it true.

*A.6:* *"~63 lines out, ~40 lines in to `SKILL.md`, plus two new scripts (`inspect_repo.py` ~80 lines, `bootstrap_check.py` ~70) and one `VERSION` file. `SKILL.md` gets shorter; the mechanism gets stronger."* Net on the measured ledger: −23 prose lines. Net on the maintained-surface ledger: +150 lines of Python with no tests specified, +1 required schema object with four sub-fields, +1 counter file with no bump discipline (finding 8), and a forced re-interview of every profile in the estate. That may still be the right trade — but "paid for by a deletion" is not what happened, and the framing is the document's own named failure: rigor accounted where it is easy to count.

*B.11:* *"Net: roughly **20 of 69 lines deleted**, ~15 replaced… **The skill file gets *shorter*** while the harness gets stronger."* The table counts only deletions. It never states the new file's length, and B.1–B.12 add content that cannot live in `orchestrate.py` because it is rationale, not control flow: B.4's 12-row model table, B.6's 14-row gate table, B.7's 4-row condition table, B.8's park protocol and its record format, B.10's 13-row hardening table. Conservatively 60+ lines of new table against 20 deleted. "Gets shorter" is asserted, not computed.

Concrete error in the same table: *"L10-12, L21-28 … **DELETE**."* L21-28 contains L23 (*"Plans are committed files… nothing load-bearing lives only in chat"* — which B.5 restates as its own principle), L24 (*"One worker per independent lane. Dependent lanes don't get a worker until the upstream gate passes"* — which is literally `depends_on` in `run-plan.json`), and L27 (*"Verification stays adversarial: review goes to a different session than the one that wrote"* — which is B.7). Three rules the new design keeps are counted as deletions.

**Fix:** state the new skill file's line count. Move L23/L24/L27 out of the DELETE row into KEEP. Report the accounting as prose-lines and maintained-code-lines separately, and let the trade stand on its merits rather than on a single-ledger net.

---

**13. MEDIUM | B.7 difficulty gating** — a self-assessed prose gate sits at the top of the arithmetic stack, and the plan's own research says misjudging it inverts the economics.

B.7's condition column is *"The change is on a client-visible surface"* / *"The plan's direction gate was `yes`"* / *"A batch's boundary check found strays."* The first two are judgments made by the plan-authoring session (Sonnet 5, medium) about its own plan; only the third is arithmetic. The document's own rule two pages earlier is *"**gate fan-out on input difficulty, not on task type**"* and its cited finding is that the ordering *inverts* on the wrong sample — so this classification decides whether verification helps or degrades quality, and it is the least-instrumented gate in the design.

Related: *"Gate 13 still runs — **it is cheap**."* Gate 13 is Opus 5 at high effort, one of the four Opus stages B.4 says constitute "the quota story in one line." No number is attached. In a document that refuses to let anyone else assert an unmeasured cost, this one gets a pass.

**Fix:** move the client-visible/direction-gate classification into `run-plan.json`, written by the brief author (Opus) at brief time and read by the script — same move as gate 11's fix, same file, one decision. Attach a measured cost to gate 13 from B.12 step 6's watched run before calling it cheap.

---

**14. MEDIUM | A.6, first row** — the section deletes the ordering rule while adding a third dependency on it.

A.6 deletes *"§1 L178-181 — the 'Order on a first run' prose dance… ~4 lines"*, justified as *"the interview is now a callable procedure with a defined position."* But that prose exists because checks 4 and 6 read a profile that does not yet exist on a first run. A.2's new check 7 also reads the profile (`profile.bootstrap.clodex_version`, `.repo_fingerprint`, `.inspected`). So §A raises the number of profile-reading checks from two to three and removes the only statement of when they may run. On a genuine first run the new check 7 will fault on a missing profile before the interview has happened.

**Fix:** keep the ordering rule, updated to name check 7; or put the ordering inside `bootstrap_check.py` as an explicit "no profile → this is a first run, defer" branch and say so in the check list.

---

**15. LOW | B.6 header L869 and L888** — hand-typed counts, in the document that makes hand-typed counts a named defect class.

*"**11 of 14 are arithmetic.**"* Counting the table's own tier column: gates 1–10 arithmetic (10), 11–12 artifact, 13 tier 4, 14 prose. Ten, not eleven. Two lines later: *"**Three gates stay prose on purpose**… a reviewer's severity judgment, the brief's §6 human-context paragraph, and Johnny's morning yes"* — only the third is in the fourteen-gate table, where exactly one gate is prose. The document's own estate rule is *"Counts come from ledgers… never hand-typed — hand-typed counts drifted in 3 of 3 audited releases."* Both counts in this paragraph are the drift, in the section that argues for arithmetic.

**Fix:** generate the tier tallies from the table, or delete the summary sentences. It costs nothing and it is the plan's own thesis applied to itself.

---

**16. LOW | B.3 L771 + `local-harness-probes.md` §5a vs `research-unattended-agent-runs.md:59`** — the topology's load-bearing invocation is unprobed and the evidence conflicts.

Every repo lane in B.3 is `claude -p --bare "/clodex <brief path>"`. The probe that established slash-skill invocation works headlessly (§5a) ran **without** `--bare`. The plan's own evidence disagrees with itself about whether `--bare` breaks it: `research-unattended-agent-runs.md:59` says *"`--bare` skips hooks, **skills**, commands, subagents, plugins, MCP, auto memory and CLAUDE.md"*; the installed CLI's help says *"Skills still resolve via /skill-name."* The plan quotes the security half of the first source into B.10 and never reconciles the skills half. The local help appears to win for 2.1.224, but "appears to win" is not the standard this document applies to anything else.

**Fix:** one probe, thirty seconds: `claude -p --bare --output-format json "/clodex ..."` in a scratch repo, confirming the skill loaded. Put it in B.12 as step 0. If `--bare` also breaks plugin-provided skills or `--add-dir` scoping, the entire repo-lane substrate needs a different flag set and it is better to know before step 5.

---

## Verdict

The plan is right about where rigor accumulates and it points a genuinely new instrument — gate 13 — at the right question. But it does not survive its own lens. The gate table is where the effort went, and the gate table is the proxy: ten of its fourteen gates are arithmetic over ledger fields the lane itself writes, gate 6 passes on a lane that auto-accepted thirteen blockers, gates 9 and 11 cannot be failed by a lane that is trying, and gate 13 — the one advertised as reaching past the proxy — scores a paraphrase of a brief section the worker was required to read, written by the same model that judges it, against a branch rather than an artifact, because the topology guarantees nothing is ever deployed. Meanwhile the two objects a human actually touches are ungoverned: the morning report has no gate at all, and the release decision is deferred to a person who was not there. The unattended premise is the load-bearing assumption and it is the least defended: a single plan amendment permanently revokes the mandate, a single stray parks the build, a round-3 blocker parks the plan, and every client-visible lane — the class the whole thesis is about — parks at verify by `clodex-verify` §5's explicit rule, so the most likely outcome of the first real night is every lane parked before dawn, at a cost the budget gates cannot see because they read the weekly Codex window instead of the five-hour one and count Claude dollars instead of Codex quota. Two of the design's foundations are contradicted by the plan's own evidence directory: `--bare` bills the API instead of the subscription that motivated the exercise, and the handoff artifact the lane is said to deliver is produced by the ship stage the lane is said never to run. None of this makes the direction wrong — B.12's step 6 (one watched lane, low-stakes repo) is exactly the right place to stop and look, and steps 1–3 are cheap, correct, and independently worth doing today. But steps 4 onward should not proceed until the `--bare` auth question, the ship/handoff contradiction, the gate-7 grep, and gate 13's held-out-ness are settled, because each of the four is a case of the rigor being aimed at the artifact that was easy to instrument rather than the outcome that was asked for.

# Clodex bootstrap hardening + orchestrator rebuild

**Written overnight 2026-09-01 while Johnny slept. Research and planning only — nothing
was implemented, edited, or committed outside this `docs/` directory.**

Evidence produced alongside this document, all in `2026-09-01-orchestration-evidence/`:

| File | What it is |
|---|---|
| `local-harness-probes.md` | Commands actually run on this Mac: Codex model roster, the live quota meter, the auth question settled, Claude headless envelope shape, and one reproduced model-override trap |
| `clodex-gate-census.md` | Every gate in the clodex corpus classified prose / artifact / arithmetic, generated from six readers' structured returns rather than typed |
| `research-*.md` (7 files) | Live web sweeps, one per angle, every claim carrying a URL and the date the source showed |
| `self-review/` | The three adversarial reviews of this document: the Codex plan-review envelope and its prompt, and both Claude reviews verbatim |

---

## Read this first — what I had to guess

I could not ask anything, so here is every assumption the plan rests on. If one is wrong,
the section it governs is wrong; the rest stands.

| # | Assumption | Why I made it | What breaks if it's wrong |
|---|---|---|---|
| 1 | **This repo is public, so nothing client-identifying may appear here.** | `vault/state/projects/workbench.md` records the 2026-08-16 sanitization and the rename to `github.com/jdpalumbo2/workbench`. | Nothing — I sanitized. The engagement is referred to as "the client repo" throughout. If you'd rather have the specifics, they belong in a note under `~/vault`, not here. |
| 2 | **"Rigor and shape, not content"** means I should port the *mechanisms* of the 2026-08-28 revamp (ladder, shape card, ledger-derived counts, named watcher) into clodex and the orchestrator, not the client's domain rules. | Your framing said exactly that. | If you wanted the client's specific rules generalized, §A and §B under-deliver. |
| 3 | **The orchestrator's job ends at a reviewed branch plus a lane report, not at a release.** | clodex structurally forbids delegating release authorization and verification-debt acceptance (`clodex-plan` L429-432, `clodex-ship` L581). I did not treat that as a bug to route around. (My first draft said "plus a handoff artifact" — review showed the handoff is written *after* the human authorization, so a lane cannot produce one. Corrected in B.3.) | If you want overnight runs to actually ship, §B is the wrong design and the constraint has to be changed in clodex first — deliberately, as a separate decision. |
| 4 | **A "prolite" ChatGPT plan is the Codex budget.** | Read from the live rate-limit record in `~/.codex/sessions`. I could not find what "prolite" maps to in OpenAI's published tier names. | The weekly-window arithmetic in §B still works — it reads `used_percent`, which is tier-agnostic — but my headroom estimate could be off. |
| 5 | **You want one orchestrator that covers both repo-scoped lanes and non-repo deliverables** (research corpora, document sets). | The current skill covers both; the estate's routing rules send repo work to clodex and estate-level work to superpowers. | If you only want repo lanes, §B's "deliverable lane" half is dead weight and should be cut. |
| 6 | **Running real adversarial review against my own draft was in scope**, since you asked for the self-review and Codex is the mechanism clodex uses. | Explicit ask in part C. | It spent real quota — one Codex round moved the weekly meter 8% → 9%. Itemised in §C. |
| 7 | **`docs/` in this repo is the right home** and I should not create files anywhere else. | Explicit instruction. | — |
| 8 | **Headless `claude -p` still draws on your Claude subscription, not separate billing.** | A change that would have billed it separately was announced for 2026-06-15 and cancelled on the day; as of 2026-08-31 the support article says SDK, `claude -p` and third-party usage *"still draw from your subscription's usage limits."* | The four Claude stages in B.4 would be API spend instead of quota spend, which changes the budget from "quota you have" to "money you owe" and re-prices gates 1 and 2 |
| 9 | **The `bootstrap` object's full JSON Schema, marker vocabulary and canonical serialization are not written.** Section A gives an example object, not a spec. | Ran out of night. A reviewer flagged it and is right. | An implementer cannot build A.1 from this document without making those decisions themselves |

### Questions I would have asked

1. **How much Codex quota are you willing to spend per night?** §B makes the ceiling a
   number in a config file; I defaulted it to 60% of the weekly window, which is a guess.
2. **Do you want the orchestrator to be allowed to `git push` a lane branch?** I designed it
   to stop at a local branch, which is the conservative reading of clodex's release-owned
   rules. Pushing a feature branch is a scoped exception the lane-brief template already
   contemplates (§4 "Scoped exceptions").
3. **Is the workbench repo the right place for the orchestrator script itself?** It is a
   skill, so it belongs beside the others — but unlike every other skill in here it is
   ~400 lines of Python that runs on a schedule. `~/code/personal/tools/` may be the
   better home with the skill pointing at it.
4. **Do you actually want the `client-artifact` evidence class fixed, or was `live-check`
   the intended resolution?** §A assumes you wanted the class and the schema lost the
   argument. Reversing that assumption changes three files.

---

## What I did, and what it cost

- Read the whole of `clodex/SKILL.md` (868 lines), `opus-orchestration/SKILL.md`, the runner
  (`run-codex.sh`, 534 lines), `profile.schema.json`, the four templates, `counts.py`, and
  both instruction files from the client engagement whose process revamp this draws on, plus the
  2026-08-28 revamp commits on both sides.
- Dispatched six reader agents over the five companion skills and the runner/state layer to
  produce the gate census.
- Dispatched seven web-research agents, then an adversarial pass over their load-bearing
  claims.
- Ran live probes against the installed `codex` (0.144.6) and `claude` (2.1.224) CLIs.
- Ran my own draft through clodex's plan-review discipline with three independent reviewers — one
  Codex round through the real runner, two Claude sessions with different lenses — and folded 73
  findings back in. Section C is the record, including the two process failures I committed while
  doing it.

Codex's weekly window read **9%** when I re-checked it at 01:43, having read 7% at 23:32 and 8%
at 23:36 before I started. My first draft claimed "8% to 12%" — a reviewer asked where 12% came
from and the answer is nowhere; the meter moves in whole percents and never showed it. The
self-review round in §C had not yet written its own meter update when I re-read. Claude-side
spend is itemised in §C.

---

## Three findings that reframe the rest

### 1. The 2026-08-28 revamp is already half-installed, and the half that's missing is the arithmetic half

`client-artifact` — the evidence class the whole revamp turns on, the one that exists because
a client digest carried a raw SSL exception for days while every code review came back green
— appears in **five places in the clodex corpus, all of them prose**:

```
clodex-plan/SKILL.md:334    Classes come from: tests · real-data · live-check · visual · client-artifact.
clodex-plan/SKILL.md:336    `client-artifact` (added 2026-08-28) is required whenever the change touches
clodex-plan/SKILL.md:757    `client-artifact`. Default
clodex-verify/SKILL.md:272  | `class` | one of `tests`, ..., `client-artifact` | a name you made up |
clodex-verify/SKILL.md:369  ### client-artifact
```

It appears in **zero** places that check anything. Two mechanisms actively reject it:

```
skills/clodex/profile.schema.json:163
  "items": {"type": "string", "enum": ["tests", "real-data", "live-check", "visual"]},

skills/clodex-verify/SKILL.md:684
  CLASSES = ("tests", "real-data", "live-check", "visual")
```

So a plan that declares `client-artifact` correctly, and a run that produces that evidence
honestly, makes `clodex-verify`'s completeness check print **NOT DONE** with the message
`class 'client-artifact' is not one of: tests, real-data, live-check, visual`. And — a correction from review, which
makes it worse — the tuple check at L711-713 runs over **both** the evidence list and the debt
list, so booking `client-artifact` as debt is rejected too. The only two ways past the gate are
to **drop the class** or **relabel it as something else**. Which is exactly what the one repo that
adopted the policy did.

That is not hypothetical. In the client repo, the profile was amended on 2026-08-28 to declare
`client-artifact`, and on 2026-08-31 the declaration was **reverted to `live-check`** with the
policy parked in `notes`:

```
ef801d6  chore(clodex): encode client-artifact evidence as live-check
         (schema enum has no client-artifact value; policy intent kept in notes)
```

`notes` is the one field `clodex/SKILL.md` L588-590 says nothing reads: *"It is free-form text
for humans and nothing in clodex reads it. Anything that must change what clodex does goes in
a typed field."* The most important process addition of the revamp now lives, in the only repo
that adopted it, in the field the system is contractually forbidden to read.

This is your own thesis running in reverse. "Rigor accumulates around whatever the process can
see" — here the *policy* accumulated where the process cannot see, and the process pushed back.
It is also the sharpest possible argument for §A: the drift was invisible because nothing
compares what a repo was set up with against what the skill now requires.

### 2. Your three-tier framework is now measurable — and one tier of it is measurably softer than the framing suggests

Your tiers are prose → required artifact → arithmetic. The 2026 literature measures each
transition. These figures are post-correction; an adversarial pass over my own research
overturned two of the ones I found most quotable, and both overturns made the picture *less*
dramatic and more usable.

| Claim | Measurement | Source |
|---|---|---|
| Prose leaks | A single, explicitly stated, **trivially machine-checkable** rule in CLAUDE.md is obeyed **~68%** of the time | arXiv:2605.10039, May 2026 |
| It leaks early | **Median first violation at generation position 4** — the fourth thing the agent writes, not deep in a long session | same |
| Restating the rule is not compliance | **28%** of runs where the agent stated the instruction back still violated it | same |
| The obvious fixes are nulls | Shortening the file, moving the rule to the top or bottom, removing AGENTS.md contradictions: measured nulls with affirmative Bayesian support | same |
| It leaks worst where it matters most | Refactor tasks **45.1%** compliance vs **84.4%** on greenfield | same |
| Summarizing memory managers **delete** house rules | Violation 0% (policy in full context) → **30%** after one compaction step, **59%** worst model — above the **37%** no-policy floor. LangGraph summarization 0→65%; LangMem 95% | arXiv:2606.22528, Jun 2026 |
| Placement decides survival | Policy in the preserved system message decays **+0**; as a user turn **+50**, as a memory entry **+45**, as tool output **+33** | same |
| Your rules erode 8.3x harder than the model's own | Deployment-specific process rules evaporate while alignment-trained refusals stay, creating false confidence | same |

Two corrections I have to make to my own first draft, because they change what the framework
claims:

**Exhortation is not "near-useless" — it is substantially effective and structurally
insufficient.** I was going to quote METR's finding that instructing models not to reward hack
moved the rate only 80% → 70%. That study is 15 months old and ran on o3, o1 and Claude 3.7. A
July 2026 replication across **22 models from 7 providers** — including Opus 4.8 and Sonnet 5 —
found anti-cheat system prompts cutting cheat propensity from **33.0% → 17.8%** (standard) to
**8.5%** (severe): a ~75% relative reduction. But 8 of the 22 still produced cheated passes under
the severe prompt, and **4 showed backfire effects**. So the correct statement is not "prose
doesn't work." It is: *prose works, unevenly, and you cannot tell which case you are in.* That is
still an argument for tier 3 — but it is an argument about **variance**, not about futility, and
it means deleting good prose in favor of a check is not automatically an improvement.

**Not every "arithmetic" gate is opinion-free, and one of mine is not.** A threshold is a
judgment someone made. `used_percent < 60` is arithmetic in form and an opinion in substance.
The tier is about *whether the check can be silently skipped*, not about whether it is
value-free — and that distinction is worth writing into the framework, because "arithmetic"
otherwise starts to mean "trustworthy," which it does not.

Three consequences that change the design work:

**Gate per artifact, not per session.** Median first violation at position 4 means a
session-level instruction has already leaked by the time the fourth thing is written. (The paper
also reports a ~5.6% per-function decay, but explicitly refuses the mechanism reading — it is
non-monotonic, was found post-hoc, and appears on two of three tasks. The design implication
survives on the median-position result alone; do not quote it as a decay law.)

**Prohibitions decay; requirements persist.** A separate April 2026 result finds "never do X"
degrading under context pressure while "always emit X" holds. Express a ban as a mechanical
block; express a requirement as an artifact you can check for. Several clodex prose gates are
currently bans (`clodex-build` L629 "never `-A`, never `.`"); the same content as a requirement
("stage by explicit pathspec and print it") is measurably stickier.

**A fourth tier exists above arithmetic — but it detects, it does not prevent.** The moment a
suite becomes the visible gate it becomes the target: the SpecBench 90th-percentile
visible-vs-held-out gap grows ~28 points per tenfold increase in code size (R² = 0.21 — a tail
statistic, not a central tendency) and reaches 100 points in the worst cases above 25K LOC.
**The correction that matters:** the held-out suite in that paper is the *measurement instrument*,
not a tested countermeasure. The paper never evaluates gating on it, and reports the gap persists
regardless. *A held-out check tells you how much you are being gamed; it does not stop it.*
Related, and pointing the other way from how I first read it: human-supervised development left a
**14.5-point** gap against **65–100** for the autonomous cases — supervision reduces the gap
roughly fourfold on a task an order of magnitude larger. **"A human watched it" is not nothing.
It is the single most effective thing in the literature.** Which is an argument for the estate's
named-watcher rule, not against it.

### 3. The runner hashes review inputs at the wrong end, so clodex's staleness check cannot fire

Found by accident during the self-review in §C — I edited this document while a Codex plan-review
round was reading it, which is exactly the situation `clodex-plan` §8 has a check for:

```python
print("reviewed this exact plan:", any(i["sha256"] == want for i in env["inputs"]))
```

> *"`reviewed this exact plan: False` means the file changed under the reviewer. That round is
> stale — discard it and run a new one."*  — `clodex-plan/SKILL.md` L578-579

**That check cannot detect the case it exists for.** The envelope's input hashes are computed in
`runner/validate_envelope.py` at line 200, inside `main()` — which runs from the **exit trap**,
after the model has finished:

```python
inputs.append({"path": path, "sha256": sha256_file(path)})
```

`run-codex.sh`'s `declare_inputs` (L287-300) records input **paths** at invocation start and no
hashes. So the envelope attests to the file's state when the review *ended*. Edit the plan during
a long review and stop editing before it finishes, and the envelope hash and the on-disk hash
agree — the check prints `True` and a review of a superseded version is accepted as current. The
one case it does catch is an edit made *after* the envelope was written, which is the less
dangerous half.

This is the failure mode this whole document is about, inside the mechanism meant to prevent it:
a check that is arithmetic in form, attesting to the wrong moment.

**Fix, small and self-contained.** Hash at invocation start. `declare_inputs` already writes
`<id>.inputs`; write `path<TAB>sha256` instead of bare paths, and have `validate_envelope.py`
read the recorded start hash rather than re-hashing. Recording the end hash *as well* is strictly
better — then an envelope can say "this file changed while I was reading it," which is more
useful than either hash alone. Add a test: write a file, start an invocation, mutate the file,
assert the envelope reports a start/end mismatch.

**What my own round showed.** The review ran 06:31:52–06:43:51 UTC. I edited this document during
that window. The envelope came back reporting `reviewed this exact plan: True` — the hash it
recorded matches the file, because it hashed the file *after* the model had stopped reading. That
is consistent with the defect but is not a controlled demonstration: I cannot reconstruct the
exact edit timings well enough to prove the reviewer read a different version than the hash
attests to. The code reading is the evidence. A controlled test is ten minutes — write a file,
start an invocation, mutate the file mid-run, stop editing, and check whether the envelope
notices. It should not, and if it does not, that is the bug.

### The census, for scale

Six readers classified every gate in the clodex corpus. Generated, not typed
(`clodex-gate-census.md`):

| Tier | Gates | Share |
|---|---:|---:|
| arithmetic | 49 | 41% |
| prose | 47 | 39% |
| artifact | 23 | 19% |
| **total** | **119** | |

| Human in the loop | Gates | Share |
|---|---:|---:|
| none | 84 | 70% |
| **blocking — the run stops until a person answers** | **28** | **23%** |
| announce only | 7 | 5% |

Two numbers matter downstream — with one scope caveat a reviewer caught and I had missed.
**The census does not include `clodex/SKILL.md` itself**: the six readers covered the five
companion skills and the runner/state layer, not the router. Every gate section A touches
(L178-181, L273-287, L488-493, L497-504, L593-609) sits *outside* these 119. So: **47 prose
gates** is the standing prose surface in the stages, none of which section A addresses, and
section A's own budget goes to uncounted router gates. **28 blocking human gates** is the exact
obstacle section B has to route around, and the census names every one — that number is sound
and is used as-is below.

---

## Where Codex is actually better, and where it is not

You asked for real use-case fit, not "Codex for everything." I set out to answer this with
benchmarks. **The adversarial pass killed most of them, and that is the finding.** What follows
is what survived, and what did not, because the wreckage is more useful than a confident table
would have been.

### What did not survive

| Claim I was going to build on | Why it failed |
|---|---|
| "Codex leads terminal driving" — Terminal-Bench 2.1: Sol 88.8% vs Fable 5 86.0% | **TB 2.1 is two major versions old.** On **Terminal-Bench 3.0** the ordering *inverts*: Opus 5 42.7%, Sol 34.6%, Fable 5 34.0%, Sonnet 5 14.6%. TB 4.0 exists and its release note says the changes "require re-running trials." The original comparison also silently omitted Opus 5, which sits within 0.4 points of Sol on TB 2.1 anyway |
| "Claude leads repo patching by 15 points" — SWE-Bench Pro 80.0 vs 64.6 | Anthropic-reported vs OpenAI-reported, **from different harnesses** — the exact cross-vendor comparison I correctly refused to make for Terminal-Bench, made anyway one paragraph later. Caught by my own reviewer, not by me |
| "Codex uses ~72% fewer output tokens" | The actual sentence is **GPT-5.5 vs Opus 4.7**. Both version qualifiers were dropped and the result generalized. Two generations stale on both sides, and the citing blog did not measure it |
| "16–36 percentage points of capability come from the harness" | **No such study.** Two unrelated single anecdotes (one 16pp, one 36pp, different setups) welded into a spurious interval |
| "Driver/worker split gives ~80% higher quality" | Self-report from unnamed teams, disclaimed in the source itself: *"These numbers are not A/B-clean"* |
| "Claude won 8 of 12 review duels, Codex won DevOps" | Author explicitly disclaims currency — run on **Opus 4.8 vs GPT-5.5**. The refactoring row is also miscounted (4-3-1, not 4 of 8), and "Codex won DevOps" rests on four duels |
| "Codex has kernel-level sandboxing Claude Code cannot match" | **Flatly wrong.** Claude Code ships its own OS-enforced Bash sandbox on the identical primitives — Seatbelt on macOS, bubblewrap + socat + optional seccomp on Linux — with filesystem isolation *and* a network domain allowlist, plus `failIfUnavailable` and credential deny/mask. The CVE cited against it was fixed in 1.0.111. The sourcing article was five months stale |
| "Codex is cheaper on volume, not on rate" | **Sol was repriced 2026-08-21** to **$4 in / $20 out** (from $5/$30), promotional at least through 2026-11-21. Sol is now cheaper than Opus 5 ($5/$25) on *both* axes. It is a rate argument too, now |
| "SWE-bench Verified is a near-tie, 96.0 vs 95.0" | The 95.0 for Sol **cannot be sourced**. One tracker says outright: *"OpenAI has not published an exact GPT-5.6 SWE-bench figure that we can confirm from a primary source, so we do not print one here"* |

Nine claims. Every one would have looked authoritative in a table. That is what an adversarial
pass is for, and it is the strongest argument in this document for the estate's existing
`empirical-falsification` discipline being applied to *research* and not only to strategy decks.

### What survived, and what it implies

Four things stood up, and none of them is a benchmark ranking.

**1. Pricing, because it is published.** Sol $4/$20 (promotional through ~2026-11-21), Terra
$2/$12, Luna $0.20/$1.20. Opus 5 $5/$25, Sonnet 5 $2/$10. Codex's flagship is now the cheaper
flagship.

**2. Context routing inside Codex is inverted from intuition.** After the August long-context
rollout, `gpt-5.6-sol` is capped at **272K** while `gpt-5.6-terra` and `gpt-5.6-luna` get
**872K** (openai/codex#39144, still open). This machine's local model cache lists 872K as
`max_context_window` for all three, so the cache does not reflect the cap. **For big-context
work in Codex, use Terra or Luna, not the flagship.**

**3. The two families fail in complementary ways.** These are qualitative and generation-stale
(GPT-5.6 observations from July 2026; the Claude one from June), so treat them as shapes rather
than facts — but the shapes are consistent across sources.

- *GPT-5.6:* **guessing at forks** — on a materially ambiguous decision it picks a branch,
  completes work on that assumption, and presents finished output instead of asking. **Process
  over product** — on long tasks it narrates the work instead of doing it. Plus run-to-run
  variability, off-plan drift, and a recovery asymmetry: when Codex fails you re-prompt from
  scratch; when Claude fails you can often talk it back.
- *Claude Opus/Fable:* **relentless proactivity** — a documented session orchestrating browser
  automation, a custom CORS server and Shadow DOM manipulation unprompted, ~$12.11 to reach a
  two-line CSS fix.

**4. The argument for cross-family review is structural, not comparative.** A model reviewing
its own work is confidently wrong in the same direction; the value is the agree/disagree signal
from **uncorrelated blind spots**. That argument does not depend on either model being better,
which is precisely why it survives when the benchmarks do not. It comes with a cost —
practitioners report Codex confidently inventing plausible bugs that do not exist — and the
documented mitigation is not to pick a winner but to force adjudication, and to **synthesize the
reviewer's output rather than forward it verbatim**.

### So how should stages actually be assigned?

Not by benchmark ranking. By three things that do not rot:

1. **Which quota has headroom.** Codex's weekly window is at 9% with six days left. Johnny's
   Claude quota is the one that has been exhausted twice. That is the whole ballgame and it does
   not need a benchmark.
2. **Structural properties.** Streaming JSONL and resumable sessions on the Codex side; the
   run-codex.sh envelope contract clodex has already hardened; per-invocation cost and per-model
   attribution readable from the Claude side.
3. **Blast radius and failure shape.** Give Codex work that is well-specified and bounded, where
   "guessing at a fork" cannot do much damage. Give Claude the ambiguous calls, where guessing is
   the expensive failure.

That is the basis section B.4 uses. It is less satisfying than a benchmark table and it will
still be true in November.

### One clodex default worth revisiting

`run-codex.sh` L103-108 puts `gpt-5.6-luna` — the cheapest tier — on the implementer role and
`gpt-5.6-sol` on every review role. I originally argued from SWE-Bench Pro that this was
backwards. **That number did not survive**, so the argument is withdrawn. Two reasons to look at
it anyway remain, and both are structural:

- Luna and Terra get **872K** context; Sol gets **272K**. An implementer working across a large
  tree has more room on Luna or Terra than on Sol — an argument *for* the current default, not
  against it.
- Terra sits between them at $2/$12 with the same 872K. If implementer rounds are coming back
  `partial` or producing thin diffs, Terra is the cheap experiment.

Record whichever it is as a decision. Right now it is an inheritance.

---

## What actually saves quota

The most useful thing I found is that **the biggest levers are not the topology.** Anthropic's
own cost measurements, run 2026-08-13 (quoted after correction — my first reading of two of
these was wrong in the direction that flattered them):

| Lever | Measured effect |
|---|---|
| **Cheap effort first, retry only the failures** | Opus 5 at `low` failed 16% of SWE-bench Pro tasks; re-running only those at default reached ~93% pass at **$0.70/task** vs 91.7% at **$1.39** running everything at default |
| **Medium effort is nearly free on knowledge work** | *"`medium` matched the default's accuracy at 70% to 85% of its cost, and the default bought nothing measurable over `medium` on any of the four."* `low` gave up 1–3 points for 50–67% of cost |
| Effort on long-horizon coding | `medium` ≈ 2 points for half the cost; `low` ≈ 8 points for a quarter. A real tradeoff, which the retry policy turns back into a saving |
| **Audit the prompt after a model upgrade** | Prompts written for Opus 4.8 cost **36% more per ticket** on Opus 5 for no accuracy change; auditing gave 97% accuracy at **14% lower** cost |
| **Ask for the answer you'll read** | Three formats, equal accuracy: one-line $0.49, two-line $0.57, five-section memo **$1.40** |
| Capping `max_tokens` | **False economy.** Cost per *solved* task identical; at a 16,384 cap, 15% of Opus 5 and 33% of Fable 5 attempts ended prematurely and solved nothing |
| **Batch API** | 50% off both input and output, **most batches finishing in under an hour**, and — contrary to the folklore — **tool use is supported**, including web search, MCP connectors and extended thinking. The rejected parameters are streaming, Fast mode, Threads and a few others. A genuine lever for the research fan-out stage, not just for leaf classification |

**One caveat on the retry policy, because it is the recommendation I would otherwise oversell.**
Changing the effort value **invalidates the cached prefix**. Cache reads are 0.1x base input and
agent bills are dominated by cache reads, so in a long multi-turn loop the rerun pays full price
for context the first attempt had cached. The measurement is on discrete one-shot tasks. It is
still the first thing to try; it is not automatically free at orchestration scale, and the honest
instruction is to measure your own cache-read share before believing the number.

### The orchestrator capability floor — and the correction that matters most

I originally wrote that a delegation-panel study (reliable at ~0.85 on the top two models,
~0.45 on the fast tier) was *"the argument for making the orchestrator deterministic code."*

**The source argues the opposite.** Its conclusion is that *"decomposing work, delegating it, and
judging the results is precisely the capability with a floor"* — i.e. keep an expensive, capable
**model** as the orchestrator. The same post reports a Fable 5 orchestrator directing Sonnet 5
workers retaining **96% of an all-Fable team's score at 46% of the cost**, which actively argues
for an LLM orchestrator over cheap workers. I had inverted a source into support for the design I
already wanted.

The COBOL-migration paper I also leaned on (deterministic orchestration, −3.5x tokens) turns out
to be scope-limited by its own Limitations section — *"structured legacy workflows... may amplify
the benefits of deterministic orchestration relative to more exploratory software engineering
tasks"* — and it ran on Sonnet 4.5 and GPT-5.1-Codex-Max, both two generations behind.

So the script-orchestrator conclusion has to stand on arguments that survive, and it does — see
B.2, which I rewrote rather than patched. But the capability-floor finding is real and it changes
the design in one specific way: **the four stages that are genuinely decomposition and judgment
stay on the top-tier model.** That is not a concession, it is the finding applied.

### Fan-out is expensive in exactly the currency being protected

I had a critique of multi-agent fan-out queued up. It also shrank under scrutiny: the study
showing pipelines costing 5–6x for zero signal ran on **gpt-5-mini**, n=400, on a 10-item ranking
task, and its own framing is the honest one — *"agentic complexity should be routed to cases where
its marginal quality gain justifies the added latency, cost, and governance risk."*

But the point that survives is sharper and cuts against this whole exercise. The 2026 evidence
still shows multi-agent configurations reading roughly **3x more tokens** than solo, with the win
coming from a **cheaper billing rate**, not fewer tokens. **A cheaper rate is worth nothing when
the constraint is a quota rather than a bill.** Johnny's constraint is a quota. So every fan-out
in the design has to justify itself on *outcome*, not on cost-per-token — and the design should
prefer fewer, better-briefed workers over many cheap ones. It also means the honest comparison
for any proposed fan-out is against **one well-briefed session**, not against doing nothing.

### Both quotas are machine-readable, which makes the budget gate arithmetic

**Codex.** Every session writes a rollout under `~/.codex/sessions/<Y>/<M>/<D>/` whose turn
record carries a live meter. Read tonight:

```json
"rate_limits": {"limit_id": "codex",
  "primary": {"used_percent": 9.0, "window_minutes": 10080, "resets_at": 1788796390},
  "credits": {"has_credits": false, "unlimited": false, "balance": "0"},
  "plan_type": "prolite", "rate_limit_reached_type": null}
```

Seven-day window, 9% consumed with six days left, **no credit balance to fall back on**. The
vendor also documents a five-hour window that local messages and cloud chats share; whether
headless `codex exec` draws from that same pool is asserted by third parties and not by the
vendor page, so treat it as likely-but-unconfirmed.

**There is no per-run cost cap in the Codex CLI, and — this is the part I got wrong first time —
the OpenAI dashboard spending limit only applies on the API-key path.** On ChatGPT-subscription
auth there is no dashboard limit to set. The only ceiling is the plan's own windows, which means
a runaway nightly job does its damage by **eating the interactive allowance**, not by billing
money. That makes gate 1 in section B not a nicety but the only backstop that exists.

**Claude.** `claude -p --output-format json` returns `total_cost_usd`, per-model `modelUsage`,
`permission_denials`, and a resumable `session_id`; `--json-schema` adds a validated
`structured_output` object. The Agent SDK adds `maxBudgetUsd`, which refuses new spawns at the cap.
And one thing worth knowing before assuming headless is free: a change that would have billed
`claude -p` separately from the subscription was announced for 15 June 2026 and **cancelled on
the day** — as of 31 August 2026, *"Claude Agent SDK, `claude -p`, and third-party app usage
still draw from your subscription's usage limits."* Headless Claude workers spend the quota being
protected. That is why there are only four of them in B.4.

A practitioner-documented OAuth usage endpoint exposes utilization and reset windows, but it is
one person's fragile scraper against an undocumented versioned header — his own words: *"when it
changes again, the collector breaks silently."* Empirical monitoring also contradicts the
commonly-repeated "resets Thursday 8pm PT": one gist tracking it over eleven days found the
seven-day window resetting **every 72 hours at a per-account anchor**. Read `resets_at` from the
account; do not schedule against a fixed weekday.

### And one trap I reproduced on this machine

`--permission-mode plan` silently overrides `--model`:

| flags | model requested | model that ran | cost |
|---|---|---|---|
| `--model haiku --permission-mode plan` | haiku | **claude-sonnet-5** | $0.104 |
| `--model haiku` | haiku | claude-haiku-4-5 | $0.025 |

Four times the cost, no announcement. Isolated to plan mode, not to the slash-command invocation.
My hypothesis is that plan mode engages the same routing as the `opusplan` alias ("Opus for
planning, Sonnet for execution"), but I did not confirm it and three probes on one machine is not
a contract. The design lesson holds regardless and is the whole point of tier 3: **do not trust
the flag you passed, read `modelUsage` back and fail the step when it disagrees.**

### Do not reach Codex through MCP — but for the real reasons

I originally argued this on a "3x token overhead" figure. **That figure is arithmetic over three
sessions**, not a per-delegation tax: the source's actual sentence is *"in a five-agent
orchestration where three agents call Codex, expect 3x the token usage compared to a single Codex
session."* Withdrawn.

The reasons that survive are the documented limitations of the MCP path itself: **no streaming to
the MCP client** (long tasks look hung), single-process serialization, and **no resume after a
crash** — which is disqualifying on its own, because `run-codex.sh`'s entire recovery story is
resuming a `partial` or `interrupted` invocation. Add that the most rigorous published
Claude-drives-Codex pattern deliberately shells out to a wrapper script *to get the supervision
the MCP path lacks* and hard-forbids the MCP route.

clodex already has that wrapper. Use it. Do not build a second one.

### Headless Codex failure modes to design against

Corrected against the vendor docs and current issue tracker, because half of what I first
collected was version-stale.

- **`codex exec` streams — it does not go dark.** I had this backwards. With `--json`, stdout is
  a JSONL stream emitting `thread.started` / `turn.started` / `item.completed` / `turn.completed`
  as they happen; progress also goes to stderr. Confirmed on this machine tonight: the plan
  review in section C wrote a 490KB event file *while still running*. This is good news — it
  means partial results and a liveness signal are available, and it is exactly what
  `run-codex.sh`'s heartbeat already exploits by tailing the event file. **The "budget for an
  all-or-nothing timeout" instruction I first wrote was wrong.**
- **stdin deadlock is real and still open.** `codex exec "prompt"` hangs printing *"Reading
  additional input from stdin..."* when stdin is an inherited-but-unwritten pipe. Open against
  0.128.0, a sibling report open against 0.133.0, and no fix in 0.152.0's changelog. Redirect
  from `/dev/null`. One uncorroborated report says even that is not always sufficient.
- **`--ask-for-approval` placement is broken post-subcommand.** `codex exec ... -a never` returns
  `error: unexpected argument '--ask-for-approval' found` on current builds; the working form is
  **before** the subcommand: `codex --ask-for-approval never exec ...`. A regression between
  0.130 and 0.137, still open at 0.152.0. Any copied recipe from a blog will be in the broken
  form. Note also that approvals are inert headless anyway — with no TTY they collapse to
  `never`, so **sandbox mode is the real blast-radius control**, and `run-codex.sh` already pins
  it per role (L95-101).
- **`codex exec` defaults to a read-only sandbox**, so an automation that forgets
  `--sandbox workspace-write` silently fails to write rather than prompting.
- **`--output-schema` shape requirements are real** — `additionalProperties: false` and every
  property listed in `required`, or the API 400s. The MCP-interaction bug I was going to flag is
  **closed and five months old**; not a live constraint.
- **Parallelism**: the "concurrent instances corrupt each other" claim is one blog's hedge
  (*"can interfere"*), and the 4–6 worker ceiling is that author's suggested default, not a
  measured limit. `--ephemeral` is a real flag but ephemeral sessions **cannot be resumed** and a
  resume attempt silently starts a new one. Cap concurrency modestly, keep persistence, and do
  not design around an unmeasured corruption threat.
- **0.152.0, released today, disables the planning tool by default** (`tools.update_plan.enabled
  = true` restores it). This machine is on 0.144.6, and `codex doctor` is offering the upgrade.

---

# A. Clodex bootstrap hardening

## A.0 The two failures, stated precisely

**(a) A repo where clodex has never run.** `clodex/SKILL.md` §3 L494-591 runs a five-step
first-run interview. Step 1 (L496-508) is *"Inspect before asking"* — a code block of seven
commands with the instruction *"Anything you can read, do not ask about."* Nothing checks that
it happened. The skill itself names the consequence at L505-508: *"Fill in `runtimes` and
`commands.install` here — preflight check 4 loops over `runtimes`, so a profile without it
makes that check a permanent no-op."*

That warning is tier 1 defending a tier-3 check from being neutered. It is also defeated by a
legal value: L249-250 distinguishes *"an empty list is a legal answer"* from *"a missing
`runtimes` key is a profile that never answered the question"* — but only a **missing key** is
detectable. `runtimes: []` is indistinguishable from `runtimes: []` for the wrong reason.
The thing that is supposed to be conspicuously blank is not blank; it is `[]`, which looks like
an answer.

**(b) A repo running clodex under a newer version than it bootstrapped with.** §3 L488-493:

> Two things send you back to the user: a **missing** key the schema requires, and a **stale**
> profile — one whose `schema_version` is not the version `profile.schema.json` accepts, which
> is the only mechanical signal that the contract moved.

"The only mechanical signal" is exactly right and exactly the problem. `schema_version` is
`"enum": [1]` (profile.schema.json:24) and has never moved. The schema's own design note for
`release_owner` establishes the pattern that made this inevitable:

> *"Deliberately not part of schema_version 1's required set: an old install that never reads
> this key behaves exactly as today."*

That is a good compatibility rule and a terrible currency signal. Optional keys get added, the
skills start requiring them, and `schema_version` never moves — so `profile ok` prints on a
profile that is six weeks behind the skill reading it. The `client-artifact` case at the top of
this document is that failure with a real cost attached.

There is a third, quieter version: **nothing ever re-reads the repo.** A repo that gained a
Dockerfile, a second `package.json`, a new CI workflow, or a renamed test script since its
profile was written keeps running the old commands forever. The only remedy §3 offers is *"Ask
for just those keys and rewrite **only** those keys"* — which cannot fire, because nothing ever
notices.

**What is missing, in one line:** the profile records what the repo answered, and never records
**who asked, when, or what the repo looked like at the time.**

## A.1 — `bootstrap` block in the profile (schema_version 2)

Add one required object to `profile.schema.json`, and a `VERSION` file to the skill directory
(there is none today — I checked).

```json
"bootstrap": {
  "clodex_version": "0.3.0",
  "derived_at": "2026-09-01",
  "repo_fingerprint": "sha256:9f2c…",
  "inspected": [
    {"marker": "package.json#scripts", "present": true,  "value": "build,test,lint,typecheck"},
    {"marker": ".nvmrc",               "present": false, "value": null},
    {"marker": "pyproject.toml",       "present": true,  "value": "requires-python >=3.12"},
    {"marker": ".github/workflows",    "present": true,  "value": "ci.yml,release.yml"}
  ]
}
```

Three fields do three different jobs.

`clodex_version` answers *which version of the skill wrote this*. Copied from
`$CLODEX_HOME/VERSION`, which the release process bumps. This is the signal `schema_version`
cannot be, because it moves on every skill change whether or not the schema moved.

`repo_fingerprint` answers *what did the repo look like when we asked*. Hash over a **fixed
manifest of structure markers**, not over file contents — existence booleans for the ~25 paths
the interview already inspects, plus the `scripts` key names from `package.json`, plus the
profile's own `commands.*` strings. Adding `src/thing.ts` does not move it. Adding a Dockerfile,
a second workspace `package.json`, a CI workflow, or renaming the test script does. Sensitivity
is the whole design problem here: a fingerprint that fires on ordinary churn gets ignored, and
an ignored check is worse than none.

`inspected` is the **tier-2 half**, and it is what makes `[]` legible. `runtimes: []` beside an
`inspected` list showing `.nvmrc: false`, `.tool-versions: false`, `package.json#engines: false`
is a *derived* empty. `runtimes: []` beside an empty `inspected` is a *skipped* one. A check can
now tell those apart; today nothing can. It is deliberately expressed as a requirement ("always
emit what you looked at") rather than a prohibition ("never skip the inspection"), because the
April 2026 result says requirements persist under context pressure and prohibitions do not.

**Migration.** Land `bootstrap` as an *optional* key under `schema_version` 1 first, and bump to
2 only once the fleet has converged — see A.2's migration rules. My first draft bumped
immediately and called the resulting fleet-wide preflight stop "the correct blast radius." A
reviewer pointed out that this installs a fleet-wide block as build-order step 4, one step before
the thing that would route around it. It does.

## A.2 — Replace preflight check 7 with a universal bootstrap-currency check

Today's check 7 (§1 L273-287) is worktree-only and asks one arithmetic question — is
`.clodex/profile.json` tracked? Keep that question, widen the check, and add three more. **The
check list stays at eight; check 7 is repurposed, not added to.**

```bash
# 7. Bootstrap currency.  Four questions.  Runs AFTER §3's profile step, not before it.
python3 "$CLODEX_HOME/state/bootstrap_check.py" "$REPO" "$CLODEX_HOME"
```

| Question | Compare | Verdict |
|---|---|---|
| No profile at all? | file absent | **first run** — this is not a failure; §3 interviews, then this check re-runs |
| Contract moved? | `profile.schema_version` vs the schema's enum | **re-derive** — see below, this is a change from the current behavior |
| Skill moved? | `profile.bootstrap.clodex_version` vs `$CLODEX_HOME/VERSION`, compared on **minor** version | **re-derive** |
| Repo moved? | recomputed fingerprint vs `profile.bootstrap.repo_fingerprint` | **re-derive** in the main checkout; **recorded, not enforced** in a linked worktree |
| Was it ever derived? | `bootstrap.inspected` non-empty and covering every marker the recompute knows about | **re-derive** |
| Committed before lanes fork? | `git ls-files --error-unmatch .clodex/profile.json` | **stop** — worktree only; the original check 7, unchanged |

**Three corrections from review, each of which was a real defect:**

1. **Ordering.** The tracked-file probe fails on a repo that has never bootstrapped, which is
   exactly the case section A exists to serve. My first draft deleted §1 L178-181 — the "Order on
   a first run" prose — while *adding* a third profile-reading check. That is backwards. The
   ordering rule stays, updated to name check 7, and `bootstrap_check.py` opens with an explicit
   "no profile → first run, defer to §3" branch so the ordering is in the code as well as the
   prose.
2. **A contract mismatch must re-derive, not partially repair.** My first draft routed
   `schema_version` mismatch to "stop — existing L488-493 behavior, unchanged." But that existing
   behavior is *"Ask for just those keys and rewrite **only** those keys"* — partial repair. Case
   (b) in A.0 is precisely the newer-version case, and routing it to partial repair means the
   plan **does not deliver the thing it was asked to deliver**. Contract mismatch routes to
   re-derivation like the other two. Non-destructive still holds: re-derivation preserves what
   inspection cannot settle and never drops `notes` (A.3 step 4).
3. **Minor-version comparison, not exact string.** `VERSION` moves on every skill change. Comparing
   exact strings would park every worktree lane in the estate on any patch release. Compare the
   minor version, and exempt linked worktrees from the "skill moved" verdict the same way they are
   exempted from "repo moved" — record it into the run's `preflight` field and let the orchestrator
   see it, rather than stopping a lane over a change that may not touch it.

**And the `VERSION` file needs an owner, or it becomes `schema_version` again.** A counter nobody
bumps is exactly the failure A.0 diagnoses. Two mechanisms, both cheap: name the bump in the
repo's release step, and add a test to `tests/` that fails when any `skills/clodex*/SKILL.md`
changed in the diff and `skills/clodex/VERSION` did not. Without that test this whole section is
prose again — which the reviewer said plainly, and was right to.

`bootstrap_check.py` is the arithmetic that replaces the prose at L505-508. Once it exists, the
warning *"a profile without it makes that check a permanent no-op"* has nothing left to warn
about and gets **deleted**.

### The migration is the risky part, and it needs its own rules

Bumping `schema_version` to 2 is a flag day across every clodex repo, and a half-applied one
strands profiles. Four rules, none of which was in my first draft:

- **`bootstrap` is optional in schema_version 1.** Land the field and the scripts first,
  let `bootstrap_check.py` report its absence as `re-derive`, and only bump `schema_version` once
  the fleet has converged. This gets the currency signal without the flag day. (My first draft
  called the flag day "the correct blast radius." It is not, and a fleet-wide preflight stop
  installed as step 4 of a build order whose step 5 is the thing that routes around it is a
  self-inflicted outage.)
- **Ship the scripts before the schema.** If v2 lands before `bootstrap_check.py` and the router
  text, every profile fails validation with no derivation path.
- **Define the backward case.** A v2 profile opened by an older v1 install: the old validator
  rejects `schema_version: 2` and the current instructions tell it to rewrite *only that key* back
  to 1 — while the validator ignores `additionalProperties`, so the `bootstrap` block survives and
  the version oscillates. State the rule: an install that does not recognize the version **stops**
  and says so; it never rewrites the version down.
- **Say how a forked lane gets the new profile.** A worktree that predates the migration holds the
  old profile commit. The answer is the existing one — bootstrap is committed on the default branch
  from the main checkout, and lanes rebase — but it has to be written down, because "the lane stops"
  without "and here is how it unblocks" is the park-forever failure that section B also had.

## A.3 — A third path in §3: re-derive

§3 has exactly two paths today: *"It exists"* (L462-493) and *"It does not exist"* (L494-591).
Add a third, and restructure so the inspection is written once and called from two places.

**Re-derive contract:**

1. **Run the §3.1 inspection in full.** Not "if you think it's needed." It is now a script, so
   it always runs the same way.
2. **Print a field-by-field diff** of inspected-reality against the recorded profile.
3. **Ask only about fields where they disagree**, plus any newly-required field. One message,
   same discipline as L509 *"Ask once, in one message."*
4. **Preserve everything inspection cannot settle** unless the diff proves it wrong — branch
   rule, tag format, deploy target, action policies, `notes`. This is the existing
   non-destructive rule at L491-492 (*"never regenerate the file wholesale, never drop
   `notes`"*), now applied to a path that can actually fire.
5. **Rewrite the `bootstrap` block, validate, commit by pathspec** — reusing L568-587 verbatim,
   including the load-bearing trailing `-- .clodex/profile.json`.
6. **Never from a lane.** A worktree that needs re-derivation says so and stops, exactly as
   check 7 does today for a missing bootstrap. The reason is unchanged and still good: two
   lanes once interviewed six minutes apart and produced contradictory profiles.

Structurally, first-run and re-derive become the same procedure with a different starting point
— first run diffs against nothing. That collapses two prose descriptions into one and is where
most of the deleted lines come from.

## A.4 — Make the inspection a script that emits an artifact

Today L497-504 is seven shell commands in a code block whose output goes to the transcript and
nowhere else. Replace with `$CLODEX_HOME/state/inspect_repo.py`, which:

- probes the fixed marker manifest,
- writes `$REPO/.clodex/bootstrap-<date>.inspection.json` (gitignored — the nested
  `.clodex/.gitignore` from §1 check 3 already covers it),
- prints the human-readable summary the interview needs,
- and emits the `inspected` list and `repo_fingerprint` that go straight into the profile.

One script feeds the tier-2 artifact and the tier-3 fingerprint from the same probe, so they
cannot disagree. That is the shape worth copying elsewhere: the check and the record come from
one execution, not from two descriptions of one intention.

## A.5 — Fix `client-artifact` in the same commit

Not scope creep. It is the worked example the whole section exists to prevent recurring, and
leaving it broken while shipping machinery to detect breakage of exactly its kind would be
absurd.

| File | Line | Change |
|---|---|---|
| `clodex/profile.schema.json` | 163 | add `"client-artifact"` to the `default_classes` items enum |
| `clodex-verify/SKILL.md` | 684 | `CLASSES = ("tests", "real-data", "live-check", "visual", "client-artifact")` |
| `clodex/state/counts.py` | — | no change needed; it counts findings, not classes |

Then, separately and in the client repo, `.clodex/profile.json` gets `client-artifact` back in
`default_classes` and the workaround sentence comes out of `notes`. **That second half is not
mine to do** — it is a client repo and it is 🟡-shaped at minimum. It is listed in "what Johnny
should do first."

There is a general lesson worth encoding as a rule in `clodex/SKILL.md`'s Common mistakes table:

> **Adding a vocabulary value in prose only.** Every enum in clodex lives in at least three
> places — the skill prose, `profile.schema.json`, and a check script. Adding a value to one is
> a defect, not a partial improvement. Grep the value across `skills/` before committing; if it
> appears only in `.md` files, the change is not done.

That is one table row and it is checkable in five seconds by a grep. It replaces nothing, so
it is the one net addition in this section that I cannot pay for with a deletion — I think it
earns its two lines.

## A.6 — What this deletes, and what it costs

| Deleted / replaced | Why |
|---|---|
| §1 L256-257 — the parenthetical "or a dry probe of the test command" buried inside check 4's worktree paragraph | Becomes a real question in `bootstrap_check.py` instead of an aside |
| §1 L273-287 — check 7's worktree-only framing | Rewritten as the universal currency check; its one arithmetic probe survives verbatim |
| §3 L488-493 — "Two things send you back to the user" | Shrinks to a pointer at check 7; the staleness logic moves into the script |
| §3 L497-504 + L505-508 — the inspection block and its "permanent no-op" warning | Replaced by `inspect_repo.py`; the warning has nothing left to warn about |
| §3 L509-537 + L568-587 — first-run-specific phrasing | Merged with re-derive into one procedure with two entry points |
| §3 L601-606 — the Bootstrap subsection's re-telling of the two-lanes-interviewing incident | Told once, in check 7, where the check that prevents it lives |

**Two corrections to my first draft's accounting, both from review, and both fair.**

*I nearly deleted working behavior.* The first draft deleted §3 **L593-609** whole, describing it
as "the Bootstrap subsection's re-explanation of the incident." Lines **607-609** are not that —
they require multi-lane repos to bootstrap `.clodex/claims.json` and reserve writes to the
orchestrator, which is live concurrency behavior with no replacement anywhere in section A.
Only 601-606 are the retelling. This is the exact failure mode of range-based deletion, committed
in the section arguing for precision, and it is why the table above cites narrowed ranges.

*The line count was single-ledger.* The first draft said "~63 lines out, ~40 in; `SKILL.md` gets
shorter." True, and misleading. The honest two-ledger version:

| Ledger | Delta |
|---|---|
| `clodex/SKILL.md` prose | roughly −45 lines |
| New maintained code | `inspect_repo.py` (~80), `bootstrap_check.py` (~70), one `VERSION` file, one test that fails when `VERSION` did not move |
| Schema | +1 object, 4 sub-fields, with a migration path (A.2) |
| Docs owed | `README.md`, `skills/clodex/README.md`, `docs/clodex-design.md` all describe bootstrap and profile behavior this changes |

So the prose gets shorter and the **maintained surface grows by ~150 lines of Python plus tests
and doc updates**. That may still be the right trade — mechanism you can test beats prose that
degrades at 68% — but "paid for by a deletion" is not what happens, and claiming it would be this
document's own named failure: accounting the rigor where it is easy to count.

**Owned paths, stated so disjointness is checkable** (a reviewer noted the first draft never gave
them):

```
skills/clodex/VERSION                       new
skills/clodex/state/inspect_repo.py         new
skills/clodex/state/bootstrap_check.py      new
skills/clodex/profile.schema.json           edit: bootstrap object (optional), evidence enum
skills/clodex/SKILL.md                      edit: §1 check 7, §3 paths, §3 Bootstrap
skills/clodex-verify/SKILL.md               edit: L684 CLASSES tuple
tests/                                      new: version-bump test, bootstrap-currency exploit/control pair
skills/clodex/README.md, README.md, docs/clodex-design.md   edit: docs impact
```

`tests/run.sh` requires an exploit/control pair for every behavior change in the engine, the
runner, or an executable skill fragment. Section A has six behavior changes and my first draft
owned zero tests. The pairs needed: first-run with no profile; version drift; fingerprint drift;
a worktree with drift (must record, not stop); an interrupted migration; and a `client-artifact`
evidence item reaching `VERIFY COMPLETE`.

## A.7 — Tier accounting for section A

| Gate | Tier now | Tier after |
|---|---|---|
| Inspection actually happened | prose (L497 "Anything you can read, do not ask about") | **artifact** — `bootstrap.inspected` required and conspicuously empty if skipped |
| `runtimes` was derived, not guessed | prose warning (L505-508) | **arithmetic** — recompute the markers, compare |
| Repo structure still matches the profile | *nothing* | **arithmetic** — fingerprint compare |
| Skill version the repo was set up under | *nothing* | **arithmetic** — `VERSION` minor compare, plus a test that the bump happened |
| Contract version moved | arithmetic, routed to partial repair | **arithmetic, routed to re-derivation** |
| Bootstrap committed before lanes fork | arithmetic (`git ls-files`) | unchanged, folded into check 7 |
| A new evidence class is usable end to end | prose in 5 files, contradicted by 2 checks | **arithmetic** — one enum, one tuple |
| A new vocabulary value reaches all three places | *nothing* | **prose** — the Common-mistakes grep rule. Labelled honestly: a reviewer caught me calling this arithmetic when no script runs the grep. Making it arithmetic means a test that enumerates each vocabulary and asserts schema/check/prose agree, which is worth doing and is not in this plan |

**One thing the middle tier rests on that nobody has measured.** "Conspicuously blank if skipped"
is the load-bearing idea behind `bootstrap.inspected` and behind the park record in section B. My
research sweep looked for evidence that a required-field artifact outperforms a prose instruction
and found none — only generic PR-template checklist work. The omission/commission asymmetry
(requirements persist, prohibitions decay) is consistent with it, but that result was measured on
Mistral Large 3 and Qwen 3.5, with no Claude or GPT model in the sample. **Tier 2 is a reasoned
bet, not a measured one.** Saying so is the difference between this document and the prose it
proposes to replace.

---

# B. The orchestrator rebuild

## B.0 Name

**`lane-orchestration`.** Recommendation, not a decision — but here is the argument, because
the naming mistake is the interesting part.

`opus-orchestration` is four months old and already misnamed: the plan below moves most of the
work off Opus. If I name the replacement `codex-orchestration` I make the identical mistake
pointing the other way, and in four months some model release will make it wrong again. The
durable noun is the **lane** — a unit clodex already speaks, that survives every vendor change.
Runner-up is `overnight-orchestration`, which names the constraint (nobody is awake) rather than
the vendor. `codex-orchestration` is the one I would not pick.

## B.1 The shape, in one paragraph

A plain Python script under launchd is the orchestrator. It holds the lane graph, the budget
meters, every gate, and the retry/park logic, and it costs zero model tokens to run. It
dispatches two kinds of worker: **repo lanes**, which are headless `claude -p` sessions invoking
the clodex stage skills inside a git worktree — and inside those, clodex delegates plan review
and implementation to Codex through the runner it already has — and **deliverable lanes**, which
are `codex exec` research sweeps feeding a Claude writer. Claude keeps four named stages where
the research says it is genuinely better and where a wrong call is expensive; everything else is
Codex or a script. Nothing prompts a human mid-flight: a lane that hits a gate it cannot answer
**parks** and the orchestrator moves on. In the morning Johnny reads one report and answers the
two questions that are structurally his — release authorization and verification-debt acceptance.

## B.2 Why the orchestrator is a script — the honest version

My first draft justified this with two citations. **My own adversarial pass killed both**, and
rather than quietly restating the conclusion I want to show the repair, because the repair is
the more useful artifact.

**What I claimed, and what the sources actually say:**

- I cited a delegation-panel result (reliable ~0.85 on the top two models, ~0.45 on the fast
  tier) as *"the argument for making the orchestrator deterministic code."* **The source argues
  the opposite** — that decomposition and judging *"is precisely the capability with a floor,"*
  i.e. keep a capable model orchestrating. It reports a Fable 5 orchestrator over Sonnet 5
  workers retaining **96% of an all-Fable score at 46% of the cost**.
- I cited a controlled experiment finding deterministic orchestration cut tokens **3.5x**. Its
  own Limitations section says the domain — COBOL-to-Python migration — *"may amplify the
  benefits of deterministic orchestration relative to more exploratory software engineering
  tasks,"* and it ran on models two generations old.

**The arguments that actually hold, none of which needs a citation:**

1. **Cost, in the currency being protected.** An LLM orchestrator awake all night spends premium
   quota on control flow — dispatch, polling, gate checks, retries. That is the exact spend this
   whole exercise exists to eliminate. A script spends nothing. This argument is arithmetic, not
   empirical, and it is sufficient on its own.
2. **Resumability.** An overnight run that dies at 03:40 must restart without re-deciding
   anything. A script re-reads `run-plan.json` and its own ledger and continues. A model
   re-derives, and may re-derive differently.
3. **The gate must live outside the session.** This one came out of the corrections and is the
   strongest of the three. Both in-session gating mechanisms are **bounded-retry nudges, not
   gates**: Claude Code overrides a Stop hook and ends the turn **after 8 consecutive blocks**,
   and a `/goal` condition ends with the goal still set if the model stalls. A run can finish
   with the check still failing. So a real gate has to be held by something that is not the
   session — a script that reads the artifact afterward. That is not a preference; it is where
   the only unbypassable gate can be.
4. **Anthropic's own cross-language answer** is to shell out: *"run the CLI as a subprocess with
   the `-p` flag and `--output-format json`."*

**And the counter-argument, which I am not going to bury.** The capability-floor finding is real,
and the Fable-over-Sonnet result says an LLM orchestrator over cheap workers works *well*. If
Johnny would rather run this as a premium orchestrator session directing headless workers, the
evidence supports that too — it costs more of the constrained quota and loses the resume
property, and it gains adaptivity that a script cannot have. **The design below splits the
difference deliberately: the script owns mechanical control flow, and the top-tier model owns
the four stages that are genuinely decomposition and judgment (B.4).** The capability floor is
the reason those four are not on Sonnet.

**Why not a Workflow script.** It is Anthropic's recommended topology for dozens-to-hundreds of
agents and it is resumable, but its script API has **no filesystem and no shell**. Every quota
read, every `run-codex.sh` invocation, every `git worktree add` would have to be wrapped in an
`agent()` call — paying model tokens for arithmetic and making a deterministic check
non-deterministic. There is also a resume footgun: a failed agent mid-fan-out reruns **every
agent that started after it**, completed ones included. Workflows stay right for wide mechanical
fan-out inside one conversation; they are wrong for an overnight process that must touch disk.

## B.3 Topology

```
launchd  com.jpalumbo.lane-orchestrator      (durable; the in-session scheduler is not —
   │                                          7-day auto-expiry, no catch-up, 50-task cap)
   ▼
orchestrate.py                                DETERMINISTIC · no model · ~400 lines
   │  reads   run-plan.json           the committed lane graph (B.5)
   │  reads   both Codex quota windows + its own Claude cost ledger   → gate 1
   │  writes  .orchestrator/events.ndjson     append-only, locked, replayable (B.11)
   │  writes  MORNING-REPORT-<date>.md        generated, not narrated (B.4)
   │
   ├─▶ repo lane                              one git worktree per lane
   │     plan     claude -p "/clodex <brief path>"                     Sonnet 5
   │     │          └─ run-codex.sh --role plan-reviewer               Sol      xhigh
   │     build    claude -p "/clodex-build, run dir <abs>"             Sonnet 5
   │     │          └─ run-codex.sh --role implementer                 Luna     medium→high
   │     │          └─ run-codex.sh --role code-reviewer               Sol      high
   │     verify   claude -p "/clodex-verify, run dir <abs>"            Sonnet 5
   │     ship     NOT RUN — see below
   │
   ├─▶ deliverable lane                       non-repo work: research corpora, doc sets
   │     research  run-codex.sh --role advisor (read-only)             Terra    high
   │     write     claude -p                                           Sonnet 5
   │
   └─▶ orchestrator-held QA                   the lane never sees these
         release-diff review   run-codex.sh --role code-reviewer       Sol      high
         client-artifact readback  claude -p + browser/MCP             Opus 5   high
         held-out acceptance       claude -p                           Opus 5   high
```

**Three corrections from review, each of which broke the first draft's topology.**

**1. `--bare` is out.** I specified `claude -p --bare` on the strength of its security properties.
Two reviewers independently flagged that `--bare` also means *"Anthropic auth is strictly
`ANTHROPIC_API_KEY` or `apiKeyHelper` via `--settings` (OAuth and keychain are never read)"* — so
every lane would leave the subscription this whole exercise exists to protect. I probed it:

```
$ claude -p --bare --model haiku --output-format json "Reply with exactly: PD"
rc=1   is_error: true   terminal_reason: "api_error"   total_cost_usd: 0
result: "Not logged in · Pl…"
```

On this machine `--bare` does not bill the API — it **fails outright**, because there is no
`ANTHROPIC_API_KEY`. So the flag is not a tradeoff to price, it is a non-starter unless Johnny
deliberately moves overnight work to metered API billing. **Decision: plain `claude -p`, with
`--permission-mode dontAsk` and an explicit per-stage `permissions.allow` list**, plus
`--settings '{"disableAllHooks": true}'` if a repo's hooks are a concern. The security argument
for `--bare` was about untrusted repos; every lane here runs in a repo Johnny wrote. That is a
real, stated tradeoff rather than a flag copied out of a docs page.

Two consequences to write down: `dontAsk` denies anything outside `permissions.allow` or the
read-only set, so **each stage needs its own allowlist** and an unlisted write is a silent denial,
not a prompt (gate 4 reads `permission_denials`). And a related trap in the same family —
`--permission-mode auto` does **not** fail closed headless: current docs say *"the action doesn't
run and Claude keeps working… Claude Code doesn't stop the run in either case,"* which is exactly
the shape that produces a confident-but-unverified report.

**2. The lane cannot produce a handoff artifact, so it does not claim one.** My first draft said
the lane stops at "a reviewed branch plus a handoff artifact" and calls that `handed-off`. That is
wrong as a matter of clodex's state machine. `clodex-ship` §7A opens: *"After the final review
(§3) and the authorization (§5…)"* — the handoff artifact is written **after** the non-delegable
human authorization, and §10 blocks `handed-off` without a `scope: "handoff"` approval. So:

> **The lane's terminal artifact is the lane report.** Not a handoff, not `handed-off`. The run
> stays open at `verify` complete, and the morning session runs ship with Johnny present.

If the handoff shape is wanted unattended, it needs a deliberate clodex change — splitting §7A
into a stage reachable without §5 — which belongs in the human-owned-core bucket with its own
review, not smuggled in as a diagram. **Related loss to note:** not running ship also skips
clodex's release-diff review (`clodex-ship` §3c), which is why the orchestrator runs its own
cross-family pass over the release diff as an orchestrator-held QA step above.

**3. Codex is reached only through `run-codex.sh`, with its real interface.** The first draft
wrote `codex exec --role advisor`, which is not a thing — `--role` is the runner's flag. The
actual contract, and the one every lane and the orchestrator use:

```bash
bash "$RUNNER" --role <plan-reviewer|implementer|code-reviewer|advisor> \
     --repo "$REPO" --run-id "$(basename "$RUN_DIR")" \
     --prompt-file "$PROMPT" --input "$ARTIFACT" [--detach]
# -> one line: "<status> <envelope-path>"; the exit code is the authority
```

The deliverable lane uses the same runner with `--role advisor` and `CLODEX_RUNNER_STATE_DIR`
pointed at the orchestrator's own state directory, so "the runner is the only path to Codex" stays
true rather than being an aspiration the first draft immediately violated. Worth knowing for
later: `codex exec review` is a first-party non-interactive review subcommand that the runner does
not currently wrap — a candidate, not a recommendation.

## B.4 Which model runs which stage, and why

The benchmark table I was going to justify this with did not survive the adversarial pass. What
follows rests on three things that do not rot: **which quota has headroom**, **structural
properties of each tool**, and **which failure shape is cheap where**. Where a row is a judgment
call with no external evidence, it says so — a reviewer caught me heading this column "the
evidence, not the vibe" while four rows contained only vibe.

| Stage | Substrate | Model | Effort | Basis |
|---|---|---|---|---|
| Control flow, gates, budget | `orchestrate.py` | **none** | — | Zero quota spend; resumable; the only place an unbypassable gate can live (B.2) |
| **Lane brief authoring** | `claude -p` | **Opus 5** | high | **Judgment call, unevidenced.** No study compares models at brief-writing. The reasoning: it is the stage where ambiguity is densest and a wrong call propagates, and the capability floor finding says decomposition is where cheap models fall off. Test it in B.13 step 7 |
| Repo grounding / research sweep | runner, `advisor` | Terra | high | Read-only and bounded — the shape where Codex's "guessing at a fork" costs least. Terra gets **872K** context vs Sol's 272K (openai/codex#39144) and costs $2/$12 |
| Plan authoring | `claude -p` → `/clodex-plan` | Sonnet 5 | medium | Adversarially reviewed immediately after. `medium` matched default accuracy at 70–85% of cost on knowledge work. **Caveat carried:** Sonnet 5's cited parity is with **Opus 4.8**, the superseded model, and its cybersecurity capability is materially below it — do not put security analysis on this stage |
| Plan review | runner, `plan-reviewer` | Sol | xhigh | **Unchanged from clodex today.** Cross-family review buys uncorrelated blind spots — an argument that does not depend on either model being better, which is why it survived when the benchmarks did not |
| Implementation | runner, `implementer` | Luna (current default) | medium → retry at high | **Left as-is.** My first draft moved it to Terra on a SWE-Bench Pro number that turned out to be a blog's transcription of an image, for a different model. Withdrawn. Luna's 872K window is a real argument for the status quo; Terra is the cheap experiment if rounds come back thin |
| Delta review per batch | runner, `code-reviewer` | Sol | high | Unchanged |
| Release-diff review | runner, `code-reviewer` | Sol | high | Moved to Codex from Opus. The "Claude wins review duels" number was n=12 on superseded models. What survives is cross-family *agreement*, and the lane's own work was Codex-implemented — so a Codex pass over its own family's output is weak. **Escalate to Opus 5 only on disagreement** with the per-batch findings |
| Verify — run gates, capture evidence | `claude -p` → `/clodex-verify` | Sonnet 5 | medium | Mechanical: run commands, record exit codes and output |
| **Verify — client-artifact readback** | `claude -p` + browser/MCP | **Opus 5** | high | The object that actually matters. Weakly evidenced (MCP/computer-use comparisons are third-party transcriptions) but structurally right: this is the densest-ambiguity stage and guessing is the expensive failure |
| **Held-out acceptance check** | `claude -p` | **Opus 5** | high | **Judgment call.** No research compares models as judges for this. See B.6 gate 13 for what it can and cannot do |
| Morning synthesis | `orchestrate.py` + `claude -p` | **Sonnet 5** | medium | **Downgraded from Opus after review.** The report is *generated* by the script from the ledger — lane, stage reached, gate results, park records verbatim, costs. The model writes only a clearly-subordinate summary paragraph, under a length cap. A model summarizing worker prose into a confident paragraph is the exact failure this document was written against, reproduced at the top of the stack |

**Three Opus stages** — brief authoring, client-artifact readback, held-out acceptance — each
minutes rather than hours, against a current design where every worker terminal is Opus all night.

**On "Codex at most stages."** A reviewer counted honestly: four Codex stages against seven Claude
sessions, and said the Codex-heavy requirement is unmet. By stage count that is right, and I am
not going to pretend otherwise. By **token volume** it is inverted — implementation, plan review,
delta review and release-diff review are where the work is, and they are all Codex; the Claude
stages are short sessions that mostly drive the runner. The precise statement is: **the session
driver is Claude because clodex is a Claude skill; the heavy execution inside every session is
Codex.** If literal stage-count compliance matters, the next candidates to move are verify-gate
execution (mechanical, well-specified) and plan authoring — both of which would require clodex
stage skills that can run under Codex, which is a much larger change than this plan.

**The effort dial.** `run-codex.sh` L241 is `EFFORT="${CODEX_EFFORT:-xhigh}"` — one global default.
Two corrections to my first draft's claim that per-role effort "needs no new machinery": the
runner has `role_model()` and `role_sandbox()` but **no `role_effort()`**, and "retry non-`complete`
at higher effort" needs a retry driver that does not exist. Both are small, but they are code, not
configuration. And the measurement being transferred is **Anthropic's, on Opus 5 effort levels,
applied to Codex's `model_reasoning_effort` on GPT-5.6** — a cross-vendor transfer, not a result.
Worse, `partial` and `interrupted` are infrastructure states the runner already handles by
*resuming*, not by retrying, so a naive retry-on-non-complete would fight the runner's own
recovery. Treat this as **a hypothesis worth one measured experiment**, not as the cheapest change
in the document, which is what I called it before review.

## B.5 The interface: everything load-bearing is a committed file

Nothing passes through chat.

**`run-plan.json`** — the orchestrator's input, committed before any lane forks.

```json
{"date": "2026-09-02",
 "budget": {"codex_weekly_pct_ceiling": 60, "codex_5h_pct_ceiling": 50,
            "claude_usd_ceiling": 40.00, "per_lane_usd_ceiling": 8.00},
 "lanes": [
   {"id": "A", "kind": "repo", "repo": "/abs/path", "worktree": "worktrees/lane-a",
    "brief": "docs/1-plans/2026-09-02-lane-a.brief.md", "depends_on": [],
    "claims": ["migration-014"],
    "client_visible": false, "direction_gate": "no",
    "acceptance_ref": "acc-lane-a"}
 ]}
```

`client_visible` and `direction_gate` are **orchestrator inputs, not lane self-assessments** — see
B.7. `acceptance_ref` is an opaque id, not a path, for the reason below.

**The acceptance file does not live in the repo.** My first draft put it at
`docs/acceptance/lane-a.md` and asserted the lane "does not get" it. Two reviewers pointed out
that this is an intention, not a mechanism: the file sits in the repo the lane has a worktree of,
`run-plan.json` names the path, and the brief tells the worker to read the committed orchestration
plan. Corrected: acceptance files live in an **orchestrator-private directory outside every lane's
worktree** (`~/.lane-orchestrator/acceptance/<ref>.md`), `run-plan.json` carries only the opaque
ref, and gate 13 additionally greps the lane's session transcript for any read of that directory.
A held-out check the worker can `cat` is gate 6 with extra steps.

**The lane brief** — the existing 16-part template, with two additions that slot into existing
headings: §4 *Scoped exceptions* carries the mandate declaration (see B.9 for why a declaration is
not yet sufficient), and §16 *REPORT BACK* carries the park protocol.

**The lane report + the run ledger** — the orchestrator reads the **ledger** for facts and the
**report** for prose, and reconciles one against the other. One correction: `counts.py` derives
findings, dispositions, severities and invocation counts only. A lane report also carries commit
counts, evidence and debt counts, gate baselines and test counts. So gate 10's "every integer
regenerated from `counts.py`" is not implementable as stated — the finding counts come from
`counts.py`, the gate counts come from the gate logs, and the commit count comes from `git`. Three
generators, named per field, or the gate is prose wearing a script's clothes.

## B.6 Gates, by tier

Every gate below is applied by the orchestrator, not by the worker. The tally is generated from
the table rather than typed — my first draft hand-typed "11 of 14 are arithmetic" in the document
that names hand-typed counts as a defect class, and it was wrong. Derived from the rows below:
**15 gates — 12 arithmetic · 1 artifact · 1 tier 4 · 1 prose, human, morning.**

| # | Gate | Tier | Mechanism |
|---|---|---|---|
| 1 | Budget precondition — BOTH Codex windows | **arithmetic** | Codex `used_percent` from the newest rollout for the 7-day window AND the 5-hour window. My probe showed `"secondary": null` — an unpopulated meter, not a zero. **Treat null as unknown and refuse to fan out.** A four-worker night is a 5-hour-window event by construction; reading only the weekly meter dispatches everything and dies in a lockout |
| 2 | Per-lane ceilings — two currencies | **arithmetic** | Claude `total_cost_usd` summed per lane, AND a Codex `used_percent` delta sampled after every `run-codex.sh` return inside the lane. The first draft metered only Claude — which governs the cheap half, while B.3 puts the heavy execution on Codex where there is no cost cap at all |
| 3 | Model readback — both families | **arithmetic** | Claude: `modelUsage` keys ⊆ the stage's allowed set. Codex: the model that ran is **not** echoed in the `--json` event stream. The rollout under `~/.codex/sessions/` carries richer turn metadata and is where a check has to look — **but I have not confirmed it records the model that actually answered**, as opposed to the one requested. Until someone checks, state plainly that gate 3 is Claude-only and Codex model selection is unverified at runtime, rather than implying coverage the gate does not have |
| 4 | Worker outcome | **arithmetic** | Codex: runner exit code and envelope `status` — never prose. Claude: `is_error`, `subtype`, `permission_denials` |
| 5 | Stage advanced | **arithmetic** | `clodex_state.py status` shows a later stage than at dispatch. A session that burned tokens and moved nothing is a failure even if it exited 0 |
| 6a | No open findings | **arithmetic** | `counts.py <run-dir>` exit code |
| 6b | No blocker or high disposed `accepted` under `by: "mandate"` | **arithmetic** | **Split out after review.** 6a alone passes a lane that auto-accepted thirteen blockers, because `counts.py` proves a disposition exists, not which one. A mandate may dispose medium and low; accepting a blocker without a human is the decision the mandate exists to avoid. `clodex-plan`'s own round-budget exit condition is already severity-based |
| 7 | Approval attribution | **arithmetic** | Read from `clodex_state.py rebuild`, **not** a grep of the raw ledger. `reducer.py:294` is `event.get("by", "user")`, so an event that *omits* `by` materializes as the user's in the snapshot and contains no `"by": "user"` substring to grep for. Every approval in a dispatched lane must read `by: "mandate"` or a new `by: "orchestrator"` value — see B.9 |
| 8 | Nothing outside owned paths | **arithmetic** | Re-run clodex-build's boundary computation independently against the lane's diff. Independent re-computation, not trust |
| 9 | Report identity | **arithmetic** | The report's first line must equal **the run id the orchestrator dispatched**, which it knows. A regex plus a `bare` escape hatch is unfailable by a lane that is trying; `bare` from a dispatched lane is a park, not a pass |
| 10 | Report counts match the ledger | **arithmetic** | Every integer in the report's counts section regenerated from `counts.py` and compared. Nearly free, and it only bites when the estate's counts-from-ledgers rule was already broken — keep it, but it is not evidence of much |
| 11 | Direction-gate agreement | **arithmetic** | The direction-gate answer comes from `run-plan.json`, set by the brief author. The gate compares it against what the plan-authoring session wrote, and compares the plan's six shape-card fields against the brief's §4. Checking that a model told to write a shape card wrote one has no discriminating power; checking two independent authors for **agreement** does |
| 12 | Lane report completeness | **artifact** | The report carries every section the brief's §16 demanded. **The handoff artifact is deliberately not gated here** — see B.3: it is produced by `clodex-ship` §7A, which runs after the §5 human authorization, so an unattended lane cannot produce one |
| 13 | Held-out acceptance | **tier 4 — detects, does not prevent** | See below. Rewritten after review; the first version was not actually held out |
| 14 | Release authorization + debt acceptance | **prose, human, morning** | Structurally un-delegable. `clodex-plan` L429-432, `clodex-ship` L581. Not a gap to close |

Three things stay prose on purpose and it is worth saying why: a reviewer's severity judgment,
the brief's §6 human-context paragraph, and Johnny's morning yes. The first two are irreducibly
judgment and do not appear in this table; the third is gate 14, and it is the point.

### Gate 13 — rewritten, because the first version was not held out

The idea is right and the first implementation was theatre. An adversarial reviewer took it
apart, correctly, on three counts. I am recording the failure rather than quietly shipping v2,
because the failure is instructive: **I built the held-out check out of the same material as the
brief, by the same author, and pointed it at the wrong object** — which is precisely the mistake
the gate exists to catch, committed inside the gate.

**What was wrong.**

1. *It was not held out.* The acceptance file was "three to five sentences describing what a
   person should be able to observe," written by the same Opus session that wrote the brief,
   minutes apart. The brief's §4 shape card carries operator, action, expected outcome and
   production proof; §6 carries what the user experiences; §7 carries guardrails as testable
   sentences; §8 carries "done when." The worker receives the acceptance criteria in three
   independent forms and then gets judged against a fourth paraphrase of them.
2. *Same-family self-scoring.* Opus wrote it, a fresh Opus judged against it — while the design
   two pages earlier insists on cross-family review precisely because *"a model reviewing its own
   work is confidently wrong in the same direction."* Cross-family where it is cheap,
   same-family where it matters.
3. *It could not reach the object.* The judge got "the lane's artifacts" — a branch, a run dir, a
   report. Ship never runs, so nothing is deployed: no email, no rendered page, no tree in an
   operator's account. I wrote "gate 13 is the gate that opens the email" and then gave it no
   mailbox.

**What it should be.**

| | v1 | v2 |
|---|---|---|
| Who writes the criteria | Opus, at brief time, from the plan | **Codex Sol, read-only, from the original ask, *before* the brief exists.** Different family, different input, and the brief author never sees it |
| Who judges | a fresh Opus session | Opus — now legitimately independent, because it did not write the criteria |
| What it reads | the lane's artifacts | the artifacts **plus a real target**: a staging deploy the lane owns, a rendered file, a captured screenshot. Where no such target exists, the gate must say so and downgrade itself rather than pretending |
| What a `no` does | undefined | **parks the lane** (B.8), with the acceptance file and the lane's artifacts side by side so the morning question is answerable in one read |
| Its shape | three to five sentences of prose | **a rubric**: one row per observable surface, graded independently, with an explicit `Unknown` verdict available. Anthropic's own evals guidance prescribes exactly this — structured rubrics, per-dimension isolated grading, and a way out — and LLM-judge accuracy has been measured collapsing from 86.93% to 16.79% on the same task under nothing but a positional change. Three sentences of prose is not a rubric |

**And the honest limit, restated.** If the lane cannot produce an artifact a person could look at,
gate 13 degrades to a documentation-consistency check and should be labelled as one. That is not
a small caveat: it means the class of work this whole document is about — client-visible surfaces
— is the class where gate 13 is weakest, unless the lane owns a staging target. **Giving lanes a
staging deploy they own is therefore a prerequisite for the client-visible case, not an
enhancement.** It is not in this plan and it should be the next thing designed.

### A note on calling twelve gates "arithmetic"

Several contain a number somebody chose. `used_percent < 60` is arithmetic in form and an opinion
in substance; so are the per-lane ceilings and the identity comparison in gate 9. The tier is
about **whether the check can be silently skipped**, not about whether it is value-free. Every
threshold should carry a comment naming who set it and on what basis, or "arithmetic" drifts into
meaning "trustworthy," which it does not.

## B.7 Verification gated on blast radius — with the classification taken out of the lane's hands

The current skill runs **two adversarial verifiers in parallel on every deliverable, always**.
Three findings say that is wrong as a default:

- On inputs a single model already handles well, multi-agent pipelines can cost several times as
  much for zero signal, and two pipelines actively degraded quality — the mechanism being error
  propagation: an evaluator critiquing an already-correct output emits an ungrounded critique the
  next stage incorporates. **Domain, named because my first draft did not:** this is a
  recommender-system next-item *ranking* study, n=400, on `gpt-5-mini`, where pipelines top out at
  six calls. Transferring it to adversarial code review is an inference, not a result. The
  mechanism is real and general; the magnitude is not established for this use.
- A reviewer told to find gaps **will manufacture them**; the documented mitigation is to
  constrain the reviewer's finding definition, not to add rounds.
- Anthropic tells you outright, for Opus 5: *"If your prompt contains explicit verification
  instructions... remove them: instructions like these cause over-verification on Claude Opus 5,
  and removing them reduces wasted tokens with no loss in quality. The same applies to legacy
  harness scaffolding that adds separate verification steps."*

My first draft said the quote *"does not reach"* independent cross-session review. A reviewer
pointed out that its last clause — *"legacy harness scaffolding that adds separate verification
steps"* — reaches exactly that, and they are right. So, conceding: **the vendor is telling me my
verification scaffolding costs tokens for no gain, and three of the stages in B.4 are that
scaffolding.** My counter-argument still stands on its own and I would not withdraw it — the case
for a separate reviewer is bias, not capability: a fresh context is not biased toward code it just
wrote and sees only the diff and the criteria. But it is a counter-argument, not a reading that
exempts the design from the quote. The honest response is to make verification conditional rather
than ritual, and to treat the Opus stage count as a number to drive down.

One related thing to build in while doing that: Opus 5 **delegates to subagents more readily than
prior models**, and Claude Code's suppression line is added automatically only under the
`claude_code` system-prompt preset. Whether it is present when the orchestrator supplies its own
`--append-system-prompt-file` is undocumented. Add the copy-pasteable suppression instruction to
every Opus stage prompt rather than assuming it is inherited.

| Condition | Verification |
|---|---|
| The change is on a client-visible surface | Full: cross-family review + client-artifact readback + gate 13 |
| The direction gate is `yes` | Full |
| A batch's boundary check found strays, or a profile gate failed | Full |
| Everything else | One cross-family review round. Gate 13 still runs |

**And the section is now named for what it does.** The rule the research actually states is
*"gate fan-out on input difficulty, not on task type"* — while the conditions below gate on
client-visibility, direction gate and boundary strays, which are **blast radius and stakes, not
difficulty**. That may well be the better axis for this purpose, but calling it difficulty was
borrowing authority the source did not grant. An actual difficulty signal (plan size, number of
owned paths, whether prior art was found) would be a genuine addition and is not in this plan.

**The classification is an orchestrator input, not a lane self-assessment.** This is a correction:
in the first draft the first two conditions were judgments the plan-authoring session made about
its own plan, which put a self-assessed prose gate at the top of the arithmetic stack — and the
document's own rule is to gate fan-out on *input difficulty*, which is exactly the judgment most
worth taking out of the interested party's hands. Both flags now live in `run-plan.json`, written
by the brief author at brief time, and gate 11 checks the lane's own answer against them for
agreement.

Round budget stays at clodex's **3**. Note what that costs unattended, because it is easy to miss:
`clodex-plan` L639 says *"Only the user funds rounds past 3 — a standing mandate cannot."* So a
plan still producing blockers at round 3 does not iterate; it **parks**. That is correct behavior
and it should be expected, not treated as a malfunction.

One rule worth stating explicitly because it is easy to get wrong in an automated pipeline:
**the reviewer's output is synthesized by the caller, never forwarded verbatim.** Codex-as-reviewer
has a real false-positive rate, and forwarding its findings unexamined launders that confidence
into the record. In clodex terms this is already right — findings are recorded and **disposed**,
and a disposition is an act of judgment.

**And one cost I have not measured.** I called gate 13 "cheap" in the first draft. It is Opus 5 at
high effort, one of the four Opus stages B.4 calls "the quota story." No number is attached to it
anywhere in this document. Attach one from B.13's step-7 watched run before anyone repeats the
word cheap.

## B.8 Park, don't prompt — and the honest count

The census counts **28 gates that block until a person answers**. An unattended orchestrator has
three legal responses to each, and "ask anyway" is not one:

1. **Pre-answer it in the brief.** The shape card answers the direction gate. §10 *Decisions
   assigned to you* — with its criterion — answers design forks. §4 *Scoped exceptions* answers
   what the lane may do that the defaults forbid.
2. **Convert it to a finding a mandate can dispose.** The typed mandate grants exactly
   `finding-disposition`, `plan-approval`, `direction-approval` — no more, revoked by every
   amendment.
3. **Park.** The lane stops, writes `PARKED-<lane>.md`, and the orchestrator moves on. Not a
   failure: a question with a name on it.

**My first draft said "this is where most of the 28 go." That is wrong and the correction matters
more than anything else in section B.** Audited gate by gate against the census, a brief plus the
three-verb mandate covers roughly **7 of 28** — plan approval, direction approval (conditionally),
three finding-disposition gates, discovery questions via brief §10, and the change boundary if the
worktree is clean. The other 21 park or are structurally out of reach.

**Four of them park reliably, not exceptionally.** These are the ones that decide whether an
overnight run is worth starting:

| Trigger | Why it parks | How ordinary is it |
|---|---|---|
| **Any plan amendment** | `clodex-plan` §6: *"The mandate binds to the plan hash like every approval, so **every amendment revokes it**."* Re-granting requires the authority that granted it — the sleeping user. An agent appending that re-grant is the `by: "user"` write gate 7 forbids | `clodex-build`'s own trigger text includes *"when a plan assumption turns out to be wrong while implementation is already in flight."* Amendment is a **normal build event** |
| **Any stray path** | `clodex-build` L463: *"A STRAY is a scope change and is the user's call."* Not in the mandate's three-verb vocabulary | Common enough to have its own section |
| **Round 3 with blockers still arriving** | `clodex-plan` L639: only the user funds more rounds | Happens on genuinely hard plans, which is when you most wanted the night to work |
| **Any client-visible lane, at verify** | `clodex-verify` §5 L385: *"'No mailbox access' is not debt — it is a blocker to raise with the user now."* A 4am lane has no mailbox, no deploy, no operator | **Certain**, for the exact class of work this document's thesis is about |

That last row is the one to sit with. B.7 says client-visible work gets the client-artifact
readback, *"never skipped, never booked as debt."* In the topology B.3 describes, nothing is
deployed, so there is nothing to read, so the rule that cannot be waived cannot be satisfied.
**The honest scope statement is therefore:**

> Overnight lanes are for work whose direction gate is `no` and whose surfaces are internal.
> Client-visible work can be *built and reviewed* overnight but cannot reach verify-complete
> without a staging target the lane owns. Building that target is a prerequisite, not an
> enhancement, and it is not in this plan.

I would rather hand that over as a stated limit than as a discovery at 4am.

**The park record** is a required artifact with five fields, conspicuously useless if any is blank:

```markdown
# PARKED — lane C, 2026-09-02T04:12Z, run r-2026-09-02-c, stage build
**Gate:**     Which of the 28 (name the skill and line).
**Question:** One sentence, answerable yes/no or by choosing from the options below.
**Options:**  The 2-3 things that could be done, and what each costs.
**Blocked:**  What is not happening until this is answered.
**Cost so far:** $x.xx Claude, y% Codex weekly, z% Codex 5-hour.
```

Parking rather than prompting also fixes a failure the census found in the current design: a run
parked mid-stage blocks the next run in that repo, because the router allows one open run per
checkout and its resume offer routes straight back to the stage that parked — an infinite bounce.
The orchestrator, holding the lane graph, schedules around a parked lane and reports it.

**What a good night looks like, and what a realistic first night looks like.** Given the four
reliable parks above, the most likely outcome of the first real multi-lane night is *several lanes
parked before dawn*. That is not failure — it is the system telling you which questions it needed
— but it should be the expectation going in, and the morning report should lead with the park
records rather than burying them under what completed.

## B.9 The approval problem — bigger than I first wrote it

My first draft framed this as one hole: `by: "user"` is a string an agent types, so a fabricated
approval passes every check. That is real. Review found a second one underneath it that is worse,
and the two together decide whether an unattended run is possible at all.

### Hole 1 — the attribution default (as first written, still true)

From the census, in four separate components:

> *"`by: "user"` is a string the agent types, so a fabricated user acceptance passes every check."*

and, in the reducer:

> *"L294 records `"by": event.get("by", "user")`, so an approval event that omits `by` is recorded
> as the user's."*

The literature is not reassuring: inaccurate self-reporting appears in 22.58% of misalignment
episodes across 20,574 real coding-agent sessions, CLI sessions violate explicit constraints far
more than IDE sessions (49.49% vs 32.26%), and — the part that ends any "use a better model"
response — in one controlled study **all ten residual fabrications came from the strongest model
tested**, while two weaker models never fabricated across 700 paired cells.

**And my proposed gate for it was broken.** Gate 7 was a grep for `"by": "user"` in
`events.ndjson`. An event that *omits* `by` contains no such string, so the grep returns zero and
passes on precisely the shape the section is named after. Corrected: read the **rebuilt snapshot**,
where the default has already materialized — `any(a["by"] == "user" for a in snap["approvals"])`.
That catches both shapes and is genuinely opinion-free.

### Hole 2 — nothing creates a valid mandate in the first place

This one I missed entirely and it is the load-bearing defect in section B.

`clodex-plan` §6 requires an actual `approval:granted` event with `scope: "mandate"`, bound to the
**current plan hash**, granted by the user — and its literal example is `"by": "user"`. My B.5 put
a *prose declaration* in the lane brief and assumed the lane would honor it. It cannot: prose in a
brief is not an event, the event must bind to a plan hash that does not exist until the lane
writes the plan at 02:00, and any event the lane appends with `by: "user"` is the forgery gate 7
forbids. So as first written, **every gate the mandate was supposed to cover still opens a modal,
and every lane parks at plan approval.** The unattended premise fails at the first stage.

There is no way to patch around this from outside clodex. It needs a deliberate change, and
because it touches the human-owned core it belongs in the same bucket as the ship/handoff question:
its own decision, its own review.

**The change I would propose, stated as a proposal:**

1. **A run-scoped mandate.** Allow `approval:granted` with `scope: "mandate"` at `run:opened`,
   binding to the **run id** rather than to a plan hash — because the thing being authorized is
   *this night's delegated run*, not a plan nobody has written yet. It still grants only the three
   existing verbs and still cannot reach release authorization or debt acceptance.
2. **A third attribution value, `by: "orchestrator"`,** with a required `authorization_ref` naming
   a **committed artifact and its sha** — `run-plan.json@<sha>`. Johnny's authorization is real: he
   committed the lane graph. It simply happened before the plan existed and is bound to a different
   artifact, and the record should say that rather than laundering it as `by: "user"`.
3. **`by` becomes required** on `approval:granted`. A missing attribution should be a refused
   event, not a free upgrade to the most authoritative value in the vocabulary. One line in the
   reducer plus an exploit/control test pair in `tests/`.
4. **Amendments still revoke it** — that rule is right and should not be weakened. Which means an
   amendment mid-build still parks the lane (B.8), and that is the correct outcome, not a bug to
   engineer around.

With those, gate 7 becomes: every approval in a dispatched lane reads `by: "mandate"` or
`by: "orchestrator"` with an `authorization_ref` that resolves to a commit in the repo. Zero
`by: "user"`. Arithmetic, and it attests to something true.

**Without those, section B does not run.** That is the single most important sentence in this
document and it was not in the first draft.

## B.10 Operational hardening the research demands

Not optional extras — each is a documented way an overnight run fails silently. Several of these
are corrections to my own first draft, marked where so.

| Risk | Countermeasure |
|---|---|
| `claude -p` without `--bare` **loads and executes the target repo's hooks and MCP servers** with no trust dialog and no per-server approval | Use `claude -p --bare`. Anthropic says it will become the `-p` default. It also skips CLAUDE.md, skills, subagents and plugins, so the orchestrator must pass context explicitly (`--add-dir`, `--append-system-prompt-file`, `--settings`). **Correction to my first draft:** `--bare` does not *require* `ANTHROPIC_API_KEY` — an `apiKeyHelper` supplied via `--settings` also works, which is the better path for short-lived credentials |
| **`--bare` and hook-based gates are mutually exclusive** | This is the sharpest tension in the whole design and I only found it via the correction pass. `--bare` skips hook auto-discovery entirely, and it is becoming the `-p` default — so any `Stop`/`TaskCompleted` hook gate silently ceases to exist. Either re-supply hooks explicitly through `--settings`, or **put the gate in the orchestrator script**, which is what B.2 argues for on independent grounds. Do not rely on inheriting a hook |
| Permission mode | Pass `--permission-mode dontAsk` — the documented deny-by-default choice for CI: anything outside `permissions.allow` or the read-only set is denied rather than prompted. **Two corrections:** there are **six** modes, not seven (`manual` is a display label and CLI alias for `default`), and `auto` is **not** the sanctioned unattended path — the docs map "run fully unattended inside a container" to `--dangerously-skip-permissions` *with real isolation*, and "run in CI with an exact allowlist" to `dontAsk`. `claude -p`'s built-in starting mode is `default` |
| **`--permission-mode auto` does not fail closed headless** | The most dangerous stale fact I nearly shipped. A March 2026 Anthropic post says a headless run terminates when auto mode's denial threshold is hit. The current docs say the opposite: *"When repeated blocks reach a threshold, the action doesn't run and Claude keeps working... Claude Code doesn't stop the run in either case."* An overnight `-p --permission-mode auto` run **keeps grinding with actions silently dropped** — precisely the shape that produces a confident-but-unverified final report. If you want termination you must build it outside the session |
| The Claude Bash sandbox is **fail-open** if dependencies are missing | Set `sandbox.failIfUnavailable: true`, `allowUnsandboxedCommands: false`, `network.strictAllowlist: true`. **Correction:** it is not *silent* — it "shows a warning and runs commands without sandboxing." The real risk is that the warning goes to a stderr nobody is reading, so the orchestrator should capture and fail on startup warnings. Note also that `failIfUnavailable` is a boolean a managed policy can pin, while `excludedCommands` is an array that **merges** across scopes — a repo can widen it |
| **There is no Codex cost cap on the subscription path** | Corrected and important: "set a spending limit in the OpenAI dashboard" only applies to API-key auth. On ChatGPT-subscription auth (this machine) there is no dashboard limit at all. Gate 1 reading `used_percent` is the **only** ceiling that exists |
| Codex stdin deadlock | Redirect stdin from `/dev/null`. Open against 0.128.0, a sibling report open against 0.133.0, nothing in 0.152.0's changelog. `run-codex.sh` already pipes the prompt from a file, which is why it stays the only path to Codex |
| `--ask-for-approval` is rejected after the subcommand on current builds | Working form is **before** it: `codex --ask-for-approval never exec ...`. Regression open since ~0.137. Approvals are inert headless anyway (no TTY → `never`), so sandbox mode is the real control and the runner already pins it per role |
| `codex exec` defaults to a **read-only** sandbox | An automation that forgets `--sandbox workspace-write` silently fails to write rather than prompting |
| Concurrent `codex exec` | Cap concurrency modestly and keep session persistence. Do not reach for `--ephemeral` to raise it: ephemeral sessions cannot be resumed and a resume attempt silently starts a new one, which would break the runner's `partial`/`interrupted` recovery. **Correction:** the "concurrent instances corrupt each other" claim is one blog's hedge and the 4–6 ceiling is that author's suggested default, not a measured limit |
| A headless session dies and is unrecoverable | Capture `session_id` from every `--output-format json` envelope into the orchestrator ledger. Headless sessions are **excluded** from the session picker and from `claude --continue` |
| A resumed headless run **does not restore the permission mode or launch flags** | Re-pass every flag on resume. Never assume inheritance |
| SIGTERM'd `claude -p` exits 143 leaving the turn unfinished with no result recorded | Send SIGINT to end a turn cleanly |
| Verbose child-process output fed into model context burns an allowance with no reasoning happening | Lane briefs require build/test output redirected to a file, with the agent reading the tail |
| Subagent/workflow requests fall **outside** the main cache TTL and hold only 5 minutes | `subagentPromptCacheTtl: "1h"` when a stage will exceed five minutes, which most will |
| Scheduled agents rot silently | Treat "no log entry" as an alertable red state, not silence. Cap retries and park after N. Commit event consumption only after handler success |
| The in-session scheduler is not durable | 7-day auto-expiry, no catch-up, cleared by a fresh conversation, 50-task cap. Use launchd. (Two qualifiers found in correction: a terminal is *not* required — backgrounding carries the tasks — and expiry is not silent, the task fires one final time before deleting itself) |
| **A subagent tree's blast radius is not what the docs' headline numbers suggest** | Spawn depth defaults to **three layers** below the main conversation (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`; value 2 = two layers, 1 = nesting off — my first draft had this off by one). The 20-agent concurrency cap is **not enforced in sessions with ultracode active** — i.e. exactly the mode used for large fan-outs. And `tools: Agent(a, b)` type restrictions are **silently ignored** inside a subagent definition; they only bind on a main-thread `claude --agent`. To constrain a nested spawner use `permissions.deny` / `--disallowedTools`, or omit `Agent` |

One more, from the estate's own rules rather than the literature: **no unattended overnight
deploys.** The orchestrator builds and reviews overnight and ships nothing. That rule exists
because a deliberately fired, unwatched production run failed, emailed a client, and was recorded
later as a discovery.

## B.11 The orchestrator's own state — and how a park ends

Two gaps a reviewer found by asking the question the clodex plan-review prompt asks third: *is
there a mechanism in this repo that already solves an isomorphic problem, which the author
missed?* There was, and I had.

**The orchestrator ledger should not be invented.** My first draft said `orchestrator.ndjson`
and stopped — no schema, no reducer, no lock, no atomic write, no operation ids, no replay rule.
A crash after dispatch but before the append duplicates work on restart; two launchd firings can
append the same ledger, dispatch the same lanes, and overwrite the same dated morning report.
**`skills/clodex/state/clodex_state.py` already solves exactly this class** — append-with-fsync,
a session lock with dead-holder detection, deterministic rebuild from the log, a frozen event
vocabulary, and reconcile-before-retry for pending external actions. The orchestrator should
reuse that engine with its own event vocabulary rather than write a worse one beside it. If the
engine cannot be reused as-is, the *design* should be copied deliberately and the divergence
named.

The specific properties that matter for an overnight run:

| Property | Why | Where clodex already does it |
|---|---|---|
| One writer at a time | Two launchd firings must not both dispatch lane A | the session lock, dead-holder-only unlock |
| Append is atomic and durable | A crash mid-write must not corrupt the record | append + fsync; `run.json` is derived, never authoritative |
| Every external action has a pending→done receipt | Dispatch, then crash, then restart must not re-dispatch | `release:step` pending/reconciled, and §8's reconcile-before-retry |
| State rebuilds deterministically from the log | Restart re-derives rather than re-decides | `rebuild` |
| Operation ids | An idempotent re-entry needs a key | already the shape of `invocation_id` |

**A park needs an ending.** The first draft defined the park record and the scheduling-around, and
nothing else — no way for an answer to be recorded, no re-evaluation of dependents, no resume, no
distinction between a park that is waiting and a park that is dead. A parked lane could stay
parked forever, which is the production case this was supposed to cover.

The unpark transition, stated:

1. Johnny answers by **editing the park record** — appending an `## Answer:` block — and running
   `orchestrate.py --unpark <lane>`. Editing a file is the interface, because it needs no session
   and leaves a record.
2. The orchestrator appends `lane:unparked` with the answer text and the record's sha, so the
   ledger says what was answered and against which version.
3. **Dependents are re-evaluated**, not resumed blindly: a lane that was blocked on A may now be
   dispatchable, or may have been overtaken by a change to `run-plan.json`.
4. The lane resumes by **re-dispatch with every flag re-passed** — a resumed headless run does not
   restore its permission mode or launch flags, so nothing is inherited.
5. **A park older than N days is escalated in the morning report**, not silently carried. "No log
   entry" and "still parked" are both alertable states; silence is not a status.

One shape that needs its own answer: a park at `verify` blocks the next run in that repo, because
clodex allows one open run per checkout. The orchestrator holds the graph and can schedule around
it — but it must also stop trying to open new runs in that repo, and say so in the report, rather
than generating a nightly failure nobody reads.

## B.12 What gets deleted from `opus-orchestration/SKILL.md`

The current file is 69 lines. A reviewer audited my first accounting and found it wrong in three
ways — the same line listed as both DELETE and KEEP, three surviving rules counted as deletions,
and a total that could not be reproduced from the table. Corrected:

| Lines | Content | Verdict |
|---|---|---|
| L10-12 | "Local Opus worker terminals are the muscle… the user opens in another terminal"; the two-layer local-first framing | **DELETE.** Requires a human awake to open terminals, which is incompatible with unattended, and it is the mechanic that burned two subscriptions |
| L21-22, L25-26 | Worker prompt contract via `SendMessage`; orchestrator duties framed around a live session | **DELETE.** Replaced by the committed `run-plan.json` + headless dispatch |
| L28 | "Models: workers run Opus; drop lower only for purely mechanical lanes. The orchestrator stays premium" | **DELETE — inverted.** Replaced by B.4, where Codex and Sonnet are the default and Opus is the named exception in three places |
| L53, clause only | "Subagents cannot spawn subagents, so the script IS the orchestrator" | **DELETE the clause — factually stale.** Subagents now nest three layers by default, concurrency-capped at 20 *except* in ultracode sessions. The conclusion survives for a different reason (no filesystem in workflow scripts), so the reasoning is replaced, not just the premise. **The rest of L51-53 is KEPT** — my first draft listed L53 in both a DELETE row and a KEEP row |
| L66 | Common-mistakes row: "(script mode) Spawning an orchestrator agent to spawn workers / Agents cannot nest" | **DELETE.** Same stale fact |
| L30-37 | The phase recipe's unconditional "two adversarial verifiers in parallel" on every deliverable | **REPLACE** with B.7's blast-radius-gated verification |
| L47-49 | "the orchestrator personally reads every deliverable in full against the source-of-truth docs" | **REPLACE.** The orchestrator is a script. The reading is Johnny's, in the morning; the script's job is to make it cheap by generating the report from the ledger. **Note:** my first draft deleted this and then quietly put an ungoverned Opus reader back in at B.4. Now the report is generated and the model writes one subordinate paragraph |
| **L23** | "Plans are committed files… nothing load-bearing lives only in chat" | **KEEP** — B.5 is this rule, restated |
| **L24** | "One worker per independent lane. Dependent lanes don't get a worker until the upstream gate passes" | **KEEP** — this is literally `depends_on` in `run-plan.json` |
| **L27** | "Verification stays adversarial: review goes to a different session than the one that wrote. A worker never passes its own gate" | **KEEP** — B.7 depends on it |
| L32-33, L37 | Research fan-out; persist every sweep marked unaudited | **KEEP verbatim.** Both right, and the second is why this document has an evidence directory |
| L39-45 | Convergence rules for fix loops | **KEEP**, with one reconciliation: `workflow-template.js` says two rounds max, clodex says three. The estate should have **one** number. Three — it is the one with an incident behind it |
| L51-53 | "Alternate substrate: Workflow scripts" | **KEEP, demoted.** Still right for wide mechanical fan-out in one conversation. Add the two constraints found tonight: no filesystem/shell, and the resume footgun where a failed agent reruns every agent that started after it |
| L59-69 | Common mistakes table | **KEEP** minus the two stale rows, **plus** four earned tonight: forwarding a reviewer's findings verbatim instead of disposing them; assuming a flag was honored without reading the model back; putting a held-out oracle somewhere the worker can read it; and citing a source's headline while dropping the qualifier in its own evidence block |

**Honest accounting, two ledgers.** Prose deleted: **11 lines** across L10-12, L21-22, L25-26,
L28, L66, plus one clause of L53. Prose replaced: ~10. Prose kept: the majority, which is the
point — most of the current skill is right and it is the *substrate* that changed. Against that,
the new maintained surface is `orchestrate.py` (~400), `quota.py` (~60), `run-plan.json` and its
schema, a launchd plist, acceptance files, reducer changes, and tests. **The skill file gets a
little shorter; the estate gets ~500 lines of new code.** That is a real trade and it should be
argued on its merits, not on a line count from one ledger.

**Owned paths** (the first draft never gave them, so disjointness was uncheckable):

```
skills/lane-orchestration/SKILL.md          new (or rename of opus-orchestration/)
skills/lane-orchestration/orchestrate.py    new
skills/lane-orchestration/quota.py          new
skills/lane-orchestration/run-plan.schema.json  new
skills/lane-orchestration/README.md         new
skills/clodex/state/reducer.py              edit: `by` required, `orchestrator` value (B.9)
skills/clodex/state/schemas/event.schema.json   edit: same
skills/clodex/templates/lane-brief.md       edit: §4 mandate declaration, §16 park protocol
tests/                                      new: approval-attribution exploit/control pair
README.md, skills/opus-orchestration/README.md  edit: docs impact
~/.lane-orchestrator/                       new, outside every repo: acceptance files, ledger
```

`docs/clodex-design.md` §198-215 documents the mandate and the `handed-off` shape; B.9's proposal
and B.3's ship correction both contradict it, so it is owned too.

## B.13 Build order

Reordered after review. The first draft put section A at step 4 as a dependency of step 5 — which
would have installed a fleet-wide preflight stop one step before the thing that routes around it.
And it put the orchestrator ahead of the two clodex changes without which no lane can run
unattended at all.

| # | Step | Depends on | Standalone value if you stop here |
|---|---|---|---|
| 0 | Read the four open decisions in "what Johnny should do first" | — | Three of them change what gets built |
| 1 | `by` required on `approval:granted`, `orchestrator` attribution value, exploit/control test | — | Closes the forgery hole for every run, attended or not. Useful with or without any of this |
| 2 | `quota.py` — read both Codex windows and the Claude cost ledger, print one line | — | You can see the number before you spend it. Two lines of arithmetic, no model |
| 3 | Section A, **without** the `schema_version` bump: `VERSION` + its bump test, `inspect_repo.py`, `bootstrap_check.py`, `bootstrap` as an optional key, the `client-artifact` enum and tuple fix | — | Bootstrap converges; the 2026-08-28 revamp finishes installing. Nothing is blocked |
| 4 | `role_effort()` in the runner + one measured Codex effort experiment on a real batch | — | Answers whether the effort dial transfers to Codex. It is a hypothesis, not a result, until this runs |
| 5 | The run-scoped mandate (B.9 hole 2) — design, review, then build | 1 | **Without this, nothing below can run unattended.** It is a change to clodex's human-owned core and deserves its own review |
| 6 | `orchestrate.py` **dry-run only** — reads `run-plan.json`, prints the dispatch plan and every gate it would apply, dispatches nothing | 2, 3 | The plan becomes reviewable before it can spend anything |
| 7 | One repo lane, end to end, **watched**, on a low-stakes personal repo, direction gate `no`, internal surfaces only | 5, 6 | The first real evidence. Named watcher, deadline, result — the estate rule applies to this too. Measure gate 13's cost here before anyone calls it cheap |
| 8 | Gate 13: acceptance files in the orchestrator-private directory, the read-detection check, the rubric | 7 | The gate aimed at the right object, with the properties review said it needs |
| 9 | The `schema_version` 2 bump, once the fleet has converged | 3 | Makes `bootstrap` mandatory rather than advisory |
| 10 | Multi-lane with the dependency graph, the park protocol, and the unpark transition | 7, 8 | The actual overnight run |
| 11 | launchd, after **three** consecutive clean supervised multi-lane runs | 10 | Soak before autonomy. `SOAKING 3/3` applied to the orchestrator itself, which seems only fair |

Step 7 is where this stops being a document. Steps 1–4 are cheap, reversible, and worth doing
whatever happens to the rest. Steps 5 onward should wait on the decisions in the closing list.

---

# C. Self-review — what it caught, and what it cost

You asked me to run my own plan through clodex's plan-review discipline before finalizing. I did,
three times, with three independent reviewers. It changed the plan more than the research did.

## What I ran

| Reviewer | How | Result |
|---|---|---|
| **Codex plan-reviewer** | `run-codex.sh --role plan-reviewer` — the real runner, the real role, `clodex-plan` §8's eight-check prompt adapted for a design document rather than application code, with the adaptation stated in the prompt | `gpt-5.6-sol`, effort `xhigh`, read-only sandbox, 719s, envelope status `complete`, **30 findings: 4 blocker · 14 high · 9 medium · 3 low** |
| **Claude lens A** | An independent Opus session, fresh context, one instruction: *turn the plan's own "is the rigor pointed at the right object?" argument on the plan* | **16 findings, 4 blockers** |
| **Claude lens B** | An independent Opus session, fresh context: *trace every load-bearing number to its source file and report where a hedged source was upgraded into a design decision* | **27 findings, 3 blockers** |
| **Research challenge pass** | 14 adversarial fact-checkers over the 205 research findings, two lenses each (staleness, overreach) | **160 corrections, 75 touching claims I had used** |

Evidence for all four is committed beside this document: the Codex envelope and its prompt, both
Claude reviews verbatim, and the seven research sweeps.

**Cost.** Codex weekly window: 8% before the review, **9%** after — one whole percent for a 12-minute
`xhigh` frontier round on a 1,200-line document, which is the most encouraging cost number in this
whole exercise. Claude side: the two review sessions consumed ~305k subagent tokens; the research
sweep and its challenge pass, ~2.37M; the corpus map, ~547k. The reviews were by far the cheapest
part of the night and by far the most valuable.

## Two process failures I committed, on camera

**I edited the artifact while the reviewer was reading it.** `clodex-plan` §8 has a check for
exactly that, and I walked into it. The envelope came back reporting `reviewed this exact plan:
True` — because, as finding 3 above explains, the runner hashes inputs at envelope-build time
rather than at invocation start, so the check attests to the wrong moment and cannot fire. I would
not have found that defect if I had followed the discipline correctly. Formally the round is stale
and clodex says to discard it. I read it anyway, because ~26 of its 30 findings concern sections I
had not touched, and I have marked the four that may be stale.

**I ran three reviewers on a document my own B.7 rule says rates one.** Lens B caught this. Either
the document deserved it — in which case B.7's conditions are missing a case — or I over-verified
the thing I care about while writing a rule that under-verifies things I do not. I have added the
missing condition (*"the artifact is a design that other work will be built on"*) rather than
pretend the rule covered it.

## What the review changed

Every blocker was verified against the files before I acted on it. Nothing below was accepted on
the reviewer's word.

| Finding | Verified? | Disposition |
|---|---|---|
| **`--bare` leaves the subscription** (lens A, lens B, Codex F002) | Yes — `claude --help` says *"Anthropic auth is strictly ANTHROPIC_API_KEY or apiKeyHelper"*; my probe returned `rc=1`, `terminal_reason: api_error`, `"Not logged in"` | **fixed.** `--bare` removed from the design entirely. It is not a tradeoff to price, it is a non-starter on this machine. B.3 now specifies plain `claude -p --permission-mode dontAsk` with per-stage allowlists, and states the security tradeoff instead of hiding behind a flag |
| **Nothing creates a valid mandate** (Codex F003) | Yes — `clodex-plan` §6 requires an `approval:granted` event bound to a plan hash that does not exist when the night starts | **fixed by admitting the design does not work without a clodex change.** B.9 hole 2 is new and says so in one sentence: *without this, section B does not run* |
| **Ship never runs, so no handoff and no `handed-off`** (lens A, Codex F004) | Yes — `clodex-ship` §7A L1839: *"After the final review (§3) and the authorization (§5…)"* | **fixed.** The lane's terminal artifact is the lane report. `handed-off` claim withdrawn. The clodex change that would enable it is named as a separate decision |
| **The held-out file is readable by the worker** (lens A, lens B, Codex F015) | Yes — it sat in the repo the lane has a worktree of, with its path in a committed file the brief tells the worker to read | **fixed.** Acceptance files move outside every worktree, `run-plan.json` carries an opaque ref, and gate 13 greps the lane transcript for reads of that directory |
| **Gate 7's grep cannot see the forgery B.9 names** (lens A, lens B) | Yes — `reducer.py:294` defaults `by` to `"user"`, and an omitted key leaves no string to grep | **fixed.** Gate 7 reads the rebuilt snapshot. The reducer change is promoted from "nice-to-have" to build-order step 1 |
| **Contract mismatch routed to partial repair, not re-derivation** (Codex F001) | Yes — existing L488-493 rewrites *only* the stale keys | **fixed.** This was the plan failing its own primary requirement. A.2 now routes contract mismatch to re-derivation |
| **A.1's flag-day migration installs a fleet-wide stop** (lens A, Codex F010) | Yes | **fixed.** `bootstrap` optional under v1 first; four migration rules added; build order reordered |
| **`VERSION` has no bump owner** (lens A, Codex F007) | Yes — no such file, no release step, symlink install | **fixed.** Named owner plus a test that fails when a SKILL.md moved and `VERSION` did not |
| **The tracked-profile probe fails on a first run** (lens A, Codex F005) | Yes | **fixed.** The ordering rule stays (I had deleted it) and the script opens with a first-run branch |
| **Deleting L593-609 drops the claims-ledger bootstrap** (Codex F026) | Yes — L607-609 is live concurrency behavior | **fixed.** Range narrowed to L601-606 |
| **`counts.py` cannot regenerate every integer in a lane report** (Codex F020) | Yes — it derives findings only | **fixed.** Gate 10 now names a generator per field |
| **Gate 6 passes on a lane that auto-accepted blockers** (lens A) | Yes — `counts.py` proves a disposition exists, not which one | **fixed.** Split into 6a and 6b; a mandate-accepted blocker parks |
| **"11 of 14 arithmetic" is hand-typed and wrong** (all three) | Yes — it was 10 | **fixed.** The tally is generated from the table |
| **The census excludes `clodex/SKILL.md`** (lens B, Codex F027) | Yes — six readers, none on the router | **fixed.** Said plainly; the 47 prose gates are not what section A addresses |
| **My "pressure to book as debt" claim was wrong** (Codex F025) | Yes — the tuple check runs over debt too | **fixed.** Only dropping or relabelling passes, which is what the real repo did |
| **No orchestrator state machine; clodex already solves this** (Codex F016) | Yes | **fixed.** New B.11; the engine's design is reused rather than reinvented |
| **No unpark transition** (Codex F017) | Yes | **fixed.** New B.11 |
| **Owned paths incomplete, no tests owned, docs not owned** (Codex F013/F018/F021/F022) | Yes — `tests/run.sh` requires exploit/control pairs | **fixed.** Owned-path blocks added to A.6 and B.12; six test pairs named |
| **"Codex-heavy at most stages" is unmet by stage count** (Codex F011/F012) | Yes — 4 Codex vs 7 Claude sessions | **partly fixed, partly conceded.** Opus reduced from five stages to three; release-diff review moved to Codex; morning synthesis downgraded to a generated report plus a Sonnet paragraph. By stage count it is still Claude-majority and I say so, with the token-volume argument stated as an argument rather than a dodge |
| **The B.4 column promised evidence and four rows had none** (lens B) | Yes | **fixed.** Those rows are labelled "judgment call, unevidenced" |
| **The opusplan hypothesis contradicts the observation** (lens B) | Yes — I ran the two missing probes: `--model sonnet --permission-mode plan` → sonnet; `--model opus --permission-mode plan` → opus. Only haiku is upgraded | **fixed.** Hypothesis withdrawn and replaced with the accurate statement: plan mode has a capability floor and silently upgrades below it |
| **The 4x cost comparison changed two variables** (lens B) | Yes | **fixed.** Baseline probe added; the evidence file now carries all six |
| **"8% to 12%" quota claim** (lens B, Codex F027) | Yes — the meter read 9% at 01:43 and never showed 12% | **fixed** |
| **The Anthropic "remove verification scaffolding" quote does reach cross-session review** (lens B) | Yes — its last clause says "harness scaffolding that adds separate verification steps" | **conceded.** My counter-argument stands as a counter-argument, not as a reading that exempts me |
| **Domain transfers unnamed; models measured unnamed** (lens B) | Yes | **fixed.** The ranking study's domain, the COBOL paper's domain, and the Mistral/Qwen model set are all now named at point of use |
| **Tier 2 rests on an untested idea** (lens B) | Yes — my own research recorded the null | **fixed.** A.7 says it is a reasoned bet |
| **Gate 13's judge needs a rubric and an `Unknown`** (lens B) | Yes — Anthropic's evals guidance prescribes both | **fixed** |
| **Effort-retry "needs no new machinery"** (lens B, Codex F023) | Yes — there is no `role_effort()` and `partial` is a resume state, not a retry state | **fixed.** Demoted from "cheapest change in the document" to "a hypothesis worth one measured experiment," which is build-order step 4 |
| Codex F006 (stage skills bypass the router's validator), F008 (bootstrap schema underspecified), F009 (worktree migration protocol), F024 (Codex model readback unverified), F030 (the grep rule is prose) | Yes on all five | **accepted, partly addressed.** F006 and F009 are named in A.2's migration rules; F024 and F030 are now stated as limits rather than claimed as coverage; **F008 is accepted and not fixed** — the plan gives an example object, not a schema. Writing the full JSON Schema, the marker vocabulary and the canonical serialization is real work and it is not done here |
| Codex F014 (the 28 gates are categorized but not individually mapped) | Yes | **accepted, not fixed.** B.8 now gives the honest ~7-of-28 count and names the four reliable parks, but a gate-by-gate mapping table is still missing. It is the first thing to write before step 6 |
| Codex F019, F028, F029 (arithmetic and line-count nits) | Yes | **fixed** |
| Lens A #5's park census, #12's deletion accounting, #15's hand-typed counts | Yes | **fixed** |
| Lens B #24 (the plan exempts itself from B.7) | Yes | **fixed** — B.7 gains the missing condition |

## What I did not accept

- **Lens A's reading that gate 10 is pure theatre.** It is nearly free and it catches the one
  failure mode with a documented three-of-three occurrence rate. Kept, with the caveat that it is
  not evidence of much.
- **Codex F011's implied remedy** — that the plan should push more stages onto Codex to satisfy
  the letter of the ask. Moving verify-gate execution or plan authoring to Codex means clodex
  stage skills that run under Codex, which is a far larger change than this plan and is not
  obviously better. I reduced Opus from five stages to three and stated the shortfall instead.
- **Four Codex findings that may be stale** — F002's `--bare` detail, F011/F012's stage counts,
  and F019's tier arithmetic all concern text I had already revised while the review was running.
  I fixed the underlying issues anyway, since three reviewers converged on them.

## The honest verdict

Lens B's summary is the one I would quote back: *"§A is the strongest section and would survive
discounting every web source entirely. §B is a different document."* That is right, and the reason
is instructive. **Section A is grounded in files I read myself on this disk and needed almost no
correction. Section B was grounded in web research and needed heavy correction** — nine benchmark
claims withdrawn, two foundational citations found to argue the opposite of what I claimed, and
four structural defects that would have defeated the design on contact.

The recurring fault was not fabrication. It was **selective inheritance**: where a source's own
evidence block or gaps section contained a qualifier that would weaken a design decision, the
qualifier was the part that did not make the trip. That is a specific, nameable failure mode, it
is not fixed by trying harder, and the only thing that caught it was an adversarial pass with
access to the same sources. Which is the argument for section B's whole verification apparatus,
demonstrated on the document that proposes it.

---

# What Johnny should do first

Recommendations to review, not actions taken. Nothing in this list has been done.

**Four decisions, before any building.** Each changes what gets built, and three of them are
yours because they touch clodex's human-owned core.

1. **Do you want `client-artifact` to be a real evidence class?** Section A assumes yes and the
   schema lost the argument. If `live-check` was the intended answer all along, say so and A.5
   disappears. If not: three lines change (`profile.schema.json:163`, `clodex-verify/SKILL.md:684`,
   and the client repo's own profile plus the workaround sentence in its `notes`). The client-repo
   half is 🟡 at minimum and is yours, not mine.
2. **Is a run-scoped mandate acceptable?** B.9 hole 2 says section B cannot run unattended without
   it: a mandate that binds to a run id rather than a plan hash, plus a `by: "orchestrator"`
   attribution carrying the sha of the lane graph you committed. That is a real change to clodex's
   approval model. If the answer is no, the honest consequence is that overnight lanes stop at
   plan approval and the design becomes "prepare work overnight, approve in the morning" — which
   is still useful and much smaller.
3. **Should a lane be able to reach `handed-off` unattended?** Today it cannot: the handoff
   artifact is written after the non-delegable release authorization. Splitting `clodex-ship` §7A
   into a reachable stage is a deliberate change; leaving it means the lane's deliverable is a
   reviewed branch plus a lane report, which I think is fine.
4. **What is the nightly Codex ceiling?** I defaulted it to 60% of the weekly window and that is a
   guess. The meter reads 9% right now with the window resetting 2026-09-07 10:53, and there is no
   credit balance behind it — when the window is spent, Codex stops.

**Then, cheap and independently worth doing whatever you decide above.**

5. **Push the workbench commit.** `1f6b1b2` — the 2026-08-28 clodex revamp — is sitting 1 ahead of
   `origin/main`, unpushed. Two `__pycache__/*.pyc` files are untracked under
   `skills/clodex/state/`; they should probably be ignored.
6. **Make `by` required on `approval:granted`.** One line in `reducer.py` plus an exploit/control
   test pair. Closes a real forgery hole for every run, attended or not, and is a prerequisite for
   anything unattended.
7. **Write `quota.py`.** Read both Codex windows from the newest rollout and the Claude cost
   ledger; print one line. Pure arithmetic, no model. You will want this before you want anything
   else here, and it is a twenty-minute job.
8. **Verify finding 3 in five minutes.** `validate_envelope.py:200` hashes review inputs at
   envelope-build time, so `clodex-plan` §8's staleness check attests to the wrong moment. Read
   those two files and confirm before anyone relies on that check again.

**Then read, in this order.** Section A first — three reviewers agreed it is the sounder half and
it would survive discounting every web source in the evidence directory. Section B's B.9 second,
because it is the sentence that decides whether the rest of B is buildable. Then B.13's build
order, which is written so that stopping after any step leaves nothing broken.

**And one thing to be skeptical about.** This document was corrected heavily by its own review —
nine benchmark claims withdrawn, two foundational citations found to argue the opposite of what I
had claimed, four structural defects caught. That process worked, but it means the first draft was
confidently wrong in ways I could not see from inside. Assume some of that survives. The parts I
would trust most are the ones citing files on this disk with line numbers you can open; the parts
I would trust least are any sentence where a benchmark number is doing the work.

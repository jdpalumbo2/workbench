# jp-frontend-design v2: apply the Atelier research memo, lean

Run: r-2026-09-17-a · Plan version: 2 · Repo: /Users/jpalumbo/code/personal/tools/workbench

## Brief

Upgrade jp-frontend-design to v2 by applying section 8 of the Atelier research memo (archive r-2026-09-02-a batch-52), writing the skill and references fresh and LEAN (the batch-52 drafts gamed the line cap with multi-KB single-line paragraphs and are unusable as instructions), and file the memo into the skill's research/ dir so it is no longer trapped in a run archive. User constraints (Johnny, 2026-09-17): lean process, ONE Codex review round total, no multi-agent, commit by pathspec only.

## Grounding

- `skills/jp-frontend-design/SKILL.md` (78 lines, v1) and `README.md`: the current skill; v2 keeps its sequence spine and voice.
- `.clodex/archive/r-2026-09-02-a/sources/batch-52/`: the Atelier run's final drafts (SKILL.md 38.5 KB, README 33 KB, eval-rubric 30 KB, critique-prompt 25 KB) plus the final memo copy. The memo (346 lines, ~70 cited sources) is the authority; the drafts are mined for structure but not copied, because their step 0 and step 4 are single paragraphs of thousands of words.
- `.clodex/archive/r-2026-09-02-a/sources/batch-44/references/swatch.html`: clean, reusable with a condensed comment (batch-52 dropped the file; 44 is the last copy).
- `skills/clodex/SKILL.md` and siblings: the house style for skill docs (short sections, tables, imperative voice).

## Prior art

The repo's own skill set (`skills/clodex*`, `skills/jp-frontend-design` v1) is the pattern: SKILL.md as the process spine, references/ for long-form material loaded on demand. §8.2 of the memo prescribes exactly this shape (progressive disclosure). No competing mechanism exists here.

## Assumptions

- The memo's §8.1 mechanisms are what Johnny wants; the batch-52 *rendering* of them (defensive hash/revert legalese accreted over 13 review rounds) is not. v2 keeps each mechanism as one or two sentences: evidence directory, baseline capture before edits, revert a rejected fix list, never stage inside the loop.
- The seven lane files (`research/lanes/R1..R7`) were never delivered by the Atelier thread; they exist nowhere in the archive or the crew repo. The research/ dir gets the memo plus a one-line README noting the gap. Not recoverable in this run.
- batch-52's memo copy is the final text and is filed verbatim (historical document; its em dashes predate the 2026-09-15 rule and stay).
- `scripts/mechanical-check.py` stays deferred until first use, per §8.2.

## Direction gate

Direction gate: yes. Test C: the skill changes the workflow every future design session runs (preflight, rendered directions, fresh-context critique, gates), so an operator lives with this behavior. (Amended from "no" per plan-review finding r1-F001.)

## Direction

- Premise: v2 is memo §8 distilled lean. Each §8.1 mechanism survives as one to three sentences a working agent can actually follow; the batch-52 rendering (multi-KB single-paragraph legalese) is explicitly rejected. This shape was dictated by the user in conversation on 2026-09-17 and is the run's brief, not a choice this plan invents.
- Operator and action: Johnny and future design-session agents invoke the skill; they get a bounded sequence with rendered direction choice and mechanical gates instead of v1's implicit mechanisms.
- Expected outcome per surface: SKILL.md readable end to end in one sitting; references load on demand; research/ answers "why is this rule here".
- Production proof: the crew-deck mockup sprint (the next queued task) runs under v2 and Johnny judges the rendered directions it produces. Watcher: Johnny.
- Comps: v1 (kept as the spine), batch-52 drafts (rejected rendering), Anthropic frontend-design + Impeccable (the memo's consensus sources).
- Acceptance for taste: Johnny reads the diff at release authorization; the skill text must read as instructions, not as legalese.

## Scope

Done when: `skills/jp-frontend-design/` contains a v2 SKILL.md (steps 0 through 5, each memo mechanism present, no line over ~200 chars, ≤130 lines), compact references (design-plan.md, critique-prompt.md, eval-rubric.md, slop-tells.md, swatch.html), an updated README.md with honest caveats, and `research/` holding the final memo; the repo test suite is green.

### In

- Rewrite `skills/jp-frontend-design/SKILL.md`: steps 0 to 5 per memo §8.1, distilled. Step 0 read-what-exists + preflight (browser automation, evidence dir, independent critic context) + the scope-guarded tweak. Step 1 brief with register; reference analysis BEFORE directions as relations-not-pixels (global profile then regions, computed styles when a URL exists, pixel hexes as hypotheses, findings seed directions then the image is discarded, never clone); 3-4 directions each as a concrete positive spec line (ground hex / accent hex / faces / rationale / named axis), spanning at least two material families, one labelled conventional exit never recommended, per-direction crowding/slop test with every rejected default paired to a replacement, rendered as swatches and chosen from renders, skipped when the ask already names faces/colors/brand; autonomous rule (commit + state assumption + ship low-fi alternates; under clodex the pick stays at the checkpoint). Step 2 design plan (≤15 prose lines) + tokens with rogue-literal check. Step 3 hero to full polish with real content and labelled sample data, no placeholders, exactly one signature, browser surfaces set on purpose. Step 4 round-0 mechanical gate, fresh-context critic (cap 10 ranked issues, none allowed), keep-best + no-regression blinded pairwise, 2 rounds default 3 max, fixture-backed B1/B5 gate, judge-call budget stated before starting. Step 5 scale-out + evidence-before-done. Paired slop list pointer, register rule, category priors kept.
- Write `references/design-plan.md` (plan template + tokens.css skeleton), `references/critique-prompt.md` (fresh-context critic prompt, failure taxonomy, exemplars, pairwise wording), `references/eval-rubric.md` (A/B/C rubric with the memo's thresholds, validated-vs-folklore notes), `references/slop-tells.md` (every NEVER paired with an INSTEAD, 2026 tells, banned faces, mechanical subset).
- Adapt `references/swatch.html` from batch-44 (condense comment, strip em dashes from text I touch).
- Rewrite `skills/jp-frontend-design/README.md` short: what changed in v2, evidence honesty (browser required; the skill itself has no controlled eval), pointer to research/.
- File `research/2026-09-02-ai-frontend-design-research.md` (batch-52 copy, verbatim) + `research/README.md` (one paragraph: provenance, lane files never delivered).

### Out

- No change to any other skill, to clodex, or to tests/ (the skill has no test harness; the repo suite covers clodex only).
- No `scripts/mechanical-check.py`.
- No re-run of the deck glance test here (that is the mockup-sprint follow-up in the crew repo).
- The `~/.claude/skills/jp-frontend-design` symlink already points at this directory; nothing to relink.

## Batches

| # | Owned paths | Done when |
|---|---|---|
| 1 | `skills/jp-frontend-design/`, `docs/plans/2026-09-17-jp-frontend-design-v2.md` | All files above exist with the stated content; SKILL.md ≤130 lines with no line over ~200 chars; `tests/run.sh` exits 0 |

Release-owned, no batch may own these: version source (profile: null, repo unversioned for this run), changelog (profile: none), tags (clodex-v{version}, not used this run).

Docs impact: none (docs/clodex-design.md describes clodex, untouched).

Claims: none needed (held claims cover clodex skill/test paths only).

## Evidence

| Class | What will prove it |
|---|---|
| tests | `tests/run.sh` green (repo suite; proves the run broke nothing tracked) |
| tests | mechanical acceptance check of the batch's Done when, commands quoted in the evidence item: file inventory of skills/jp-frontend-design/ matches the In list; `wc -l SKILL.md` ≤130; no line over 200 chars in SKILL.md; zero em dashes in newly authored files; `diff` proves research/2026-09-02-ai-frontend-design-research.md is byte-identical to the batch-52 copy |

No other default classes exist in the profile. real-data / live-check / visual do not apply to a documentation deliverable; the skill's first real exercise is the crew-deck mockup sprint, deliberately out of scope (that sprint is this plan's Direction "production proof").

## Risks

- Distillation could drop a mechanism the memo's evidence supports. Mitigation: the single Codex plan-review round is pointed at exactly this question (memo §8.1 vs plan), and the build self-review walks memo §6's verdict table row by row against the finished SKILL.md.
- Ship note, recorded up front: per the user's one-Codex-round cap, the ship-stage release-diff code review will be skipped on user instruction (the diff is markdown plus one inert static HTML page with no scripts); this is a named deviation, not an oversight.
- The batch-52 drafts stay in the archive untouched; nothing here deletes the Atelier record.

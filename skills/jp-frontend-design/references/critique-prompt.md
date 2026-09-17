# Fresh-context critic prompt (step 4, rounds 1-2)

Dispatch as a separate subagent. It never sees the generating transcript. Hand it, in this
order: the labelled captures (1568 px long edge max, one focused-state crop), the design plan,
tokens.css, the round-0 results, `slop-tells.md`, the three exemplar critiques below, then
(read-only, after the images) the component source and a computed-style dump.

## The prompt

> You are critiquing a rendered UI against its own written design plan. The captures are ground
> truth for what is wrong; the source and computed styles are ground truth for where and by how
> much. Score the eight dimensions (hierarchy, spacing rhythm, typography, color, copy, glance
> chart choice, papercuts, direction fidelity) 1 to 5, then list UP TO 10 issues, ranked. "No
> issues" is an acceptable answer; do not manufacture findings to fill a count. For each issue:
> a stable key (CSS selector or element name plus defect class), severity 0 to 4, the location
> (image + region, or selector), a MEASURABLE or JUDGMENT tag, and a token-first fix (name the
> token to change before proposing a component edit). Check the slop-tells list explicitly.
> Look for these failure classes by name: occlusion, crowding, text overlap, misalignment,
> contrast, overflow, element omission, wrong register. Do not award points for polish the plan
> did not ask for; direction fidelity means THIS plan, not your preference.

## Known critic blind spots (why round 0 exists)

Vision models are near-blind to line-height, border-radius, and gradient deltas, and defer to
expectation on familiar-looking layouts (a standard card grid reads as fine because it is
expected to be fine). Scripts own the sub-pixel properties; the critic owns relations and
judgment. A critic will not flag its own model's house style unless the checklist names it;
that is what slop-tells.md is for.

## Exemplar critiques (calibration; exemplars beat personas)

1. MEASURABLE, severity 3, key `nav .label/type-floor`: "Secondary nav labels render at 10.2 px
   at 390 wide, below the 11 px floor (A4). Fix: raise `--scale-ratio` step, not the component;
   check A12 size count stays at 5."
2. JUDGMENT, severity 2, key `main .summary/hierarchy`: "The summary card and the alert row have
   equal visual weight, so nothing is first. The plan's hierarchy stance says the alert leads.
   Fix: move the card's surface to `--surface` from `--surface-raised`; keep the alert's accent."
3. JUDGMENT, severity 1, key `footer .meta/register`: "Marketing voice ('blazingly fast sync')
   on an operate surface. Fix: state the fact ('last sync 14:02, 1.2 s')."

## Pairwise gate wording (B3 judges; separate fresh contexts, never the critic)

> Two captures of the same surface, X and Y. For each dimension (list the eight; mark chart
> choice and papercuts n/a if no chart or interaction is shown), answer: X better, Y better, or
> tie. One line of reason per non-tie. You are not told which is newer; do not guess or reward
> novelty.

The orchestrator assigns X/Y at random per call, runs three calls per ordering, and maps
verdicts back. Regression and win rules are in `eval-rubric.md` B3.

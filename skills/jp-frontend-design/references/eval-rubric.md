# Eval rubric: three layers, three trust levels

Layer A is deterministic and gates. Layer B is fresh-context vision with bias controls and gates
only on concrete questions. Layer C is critique: informative, aggregated, never a sole blocker.
Evidence grades per instrument are in the research memo §4; the headline: cold VLM aesthetic
judgment is at chance, checklist-anchored judging is strong, pairwise needs both orderings.

## A: mechanical gate (round 0; both viewports 1400x900 and 390x844, both schemes)

Run via the preflight's browser automation (computed styles, scripted Tab walk, axe-core;
Lighthouse when available, its absence recorded, never silently skipped).

| # | Check | Threshold |
|---|---|---|
| A1 | horizontal overflow | none at 390 (report at 320) |
| A2 | text contrast | 4.5:1, 3:1 large |
| A3 | non-text contrast (status marks, borders) | 3:1 |
| A4 | smallest rendered text | 11 CSS px floor; body 16 px |
| A5 | tap targets | 24x24 gate, 44 advisory |
| A6 | focus visibility | scripted Tab walk, every stop visible |
| A7 | reduced motion | honored |
| A8 | structure | headings, landmarks, accessible names, zoom enabled |
| A9 | clipping/truncation | none on glance-critical text |
| A10 | line length | 80ch max on prose |
| A11 | color-only status | none (shape + word + color) |
| A12 | design-system lint | sizes 5 or fewer, weights 3 or fewer, spacing on scale, palette colors only, no rogue literals (advisory) |
| A13 | axe-core floor | no new violations; never presented as "accessible" (tools find about half of real issues) |

## B: blinded vision judges (each call a separate fresh context; captures + questions only,
never the plan, tokens, gate results, or answers)

- **B1, the glance test.** Gates only where a fixture-backed acceptance eval exists (a glance
  test, a task list): scored by the orchestrator against the fixture at 90% of question-runs or
  better (11/12 for 4 questions x 3 runs), no question below 2/3, recognition questions answered
  from the above-the-fold crop alone. Elsewhere: an advisory probe on what the design plan can
  answer (what is this, what matters now), scored against the plan's stated answers, reported,
  never gated.
- **B2, degraded input (optional).** 50% downscale; "name the three things you see first";
  "which region looks wrong?" Log whether it ever changes a decision; drop it if not.
- **B3, pairwise no-regression.** Revision vs the previous ACCEPTED form (never a rejected
  candidate). Neutral X/Y labels assigned at random per call; captures copied under neutral
  names into a fresh directory; nothing in the handoff names a round, date, or version. Three
  calls with each ordering. Verdict per C-dimension per viewport. A regression: a majority of
  three calls in EITHER ordering preferring the previous form (one dissent is not; ties never
  are); a regression at either viewport rejects. A win: majorities in EACH ordering at one
  viewport on one dimension. A polish round (no measurable fix) closes only on a win; a panel of
  ties rejects it. Second panel on the other scheme only when the revision touched a color token
  or scheme-specific CSS.
- **B5, theme parity.** B1 repeated on the other color scheme, gating exactly when B1 gates.

Order per candidate: A gates, then critique fixes applied and re-gated, then B1, B5, optional
B2, then B3, then keep-best. Log every judge call with ordering and run index.

## C: craft critique (three or more independent passes, unioned, never a sole gate)

Eight dimensions, each scored 1 to 5: hierarchy, spacing rhythm, typography, color, copy, glance
chart choice, papercuts, direction fidelity (chart choice and papercuts n/a without a chart or
interaction; n/a is neither win nor regression in B3). Each issue carries a stable key (selector
or element name + defect class), severity 0 to 4, a location, a MEASURABLE or JUDGMENT tag, and
a token-first fix. Union by key at the highest severity given; frequency = passes that named it;
rank by severity x frequency. Up to 10 issues per pass, "none" allowed.

## Validated vs folklore (so nobody re-argues this)

Validated by controlled results: the loop's 2-3 round plateau and keep-best; fresh-context
critic; cap-not-floor; checklist-anchored judging; both-orderings pairwise; enumerate-then-pick
diversity. Practice-only (kept because cheap): the squint/blur probe, the swatch render, the
15-line plan cap. No controlled eval exists of this skill itself; treat its own advice with the
same honesty it demands.

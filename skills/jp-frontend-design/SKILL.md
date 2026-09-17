---
name: jp-frontend-design
description: Use when building or restyling any user-facing UI, before the first component or stylesheet. Also when an existing UI feels generic or AI-generated, or must pass its own acceptance eval.
---

# JP Frontend Design

## Overview

Unconstrained generation regresses to the statistical mean of every UI ever made, and a ban only
moves the model to the next default. Distinctiveness is decided in steps 0 to 2 (direction and
spec), written down, and *protected* by everything after: the critique loop removes defects, it
never invents a direction. Long-form material lives in `references/`, the evidence in `research/`.
Load a craft skill (Anthropic's `frontend-design`) beside this one if available, and a dataviz
skill before any chart. This skill governs the ORDER of work.

## The sequence (in order; no component code before step 2 exists)

0. **Read what exists.** Search CLAUDE.md, tokens/theme files, component styles, DESIGN.md, and
   the screens closest to the ask; lift exact values. Precedence: the user's words, then the
   existing system, then this skill's choices. An existing system means step 1 extends, never
   invents beside it.
   **Preflight, before any file changes:** confirm (a) browser automation that can render,
   capture, AND script the page (computed styles, a Tab walk, axe-core); a screenshot tool alone
   cannot run round 0; (b) an evidence directory (under clodex the run directory; standalone, a
   directory outside the repo tree, named in the final record); (c) an independent context for
   step 4's critic and judges. Any missing: stop and say so.
   **Scope guard:** a tweak inside an existing system (one component, one value) skips the
   directions and the loop. Grep the component's and the token's usages first; one rendered
   elsewhere is a shared change and every consuming surface gets the before/after treatment.
   Then: round 0 on the touched page BEFORE the edit (the baseline), the edit, round 0 again;
   baseline failures are pre-existing and recorded, only new ones block; a new failure that
   survives repair reverts the edit. A fixture-backed eval runs after the edit too.

1. **Brief, references, then directions.** Pin the subject, the audience, the surface's single
   job, and its **register**: operate (tools, dashboards), read (docs, long form), persuade
   (marketing), experience (play, art). If references are given, analyze them NOW, before any
   direction exists: relations, not pixels (hierarchy, density, rhythm, type character,
   components); global profile then regions; computed styles when a URL exists; pixel-read hexes
   are hypotheses. Findings seed the directions; then discard the image. Analyze, never clone.
   Then propose 3 or 4 directions, each one spec line
   (`ground hex / accent hex / display face + body face / rationale / the axis it varies on`)
   spanning at least two material families from the subject's own world, one of them the
   conventional category default, labelled as the exit and never recommended. Slop-test each
   (would a generic version of this ask produce the same direction?) and pair every rejected
   default with its replacement (`references/slop-tells.md`).
   **Render the choice, never prose it:** open `references/swatch.html` once per direction
   (values set through the browser at render time; capture 1400x900 into the evidence directory;
   an accent pair below 4.5:1 or a fallback font is never captured); the picker chooses from
   renders. Skip the directions when the ask already names faces, colors, or a brand, or on the
   scope-guarded tweak; the system it keeps IS the direction.
   Autonomous: commit to one, state the assumption in one line, ship 1 or 2 low-fi alternates
   beside the deliverable. Under clodex the pick happens at the direction checkpoint, by the
   user or a standing mandate; never silently by the builder.

2. **Design plan + tokens.** Two short files before any component (`references/design-plan.md`).
   The plan, 15 prose lines or fewer: subject/job, register, direction, refused defaults and
   their replacements, palette stance, type character + scale ratio, hierarchy stance, density,
   shape/elevation, motion stance, ASCII layout, the one signature, sample-data rule. And
   `tokens.css`: 6 to 10 color roles as surface/on-surface pairs, two faces + scale + weights +
   tracking + leading, base unit + `--density`, one radius stance, elevation, one duration and
   easing pair. Step 0 found a token system? Extend it in place; still write the plan.
   Components consume only tokens; a rogue-literal grep (scoped to the files this work touches)
   runs in step 4, because models will not self-enforce this. Tokens STORE the taste decided
   here; they are memory between generations, not the source of the idea.

3. **One hero screen to full polish.** Real content, labelled sample data, no placeholders. The
   hero embodies the signature, and there is exactly one. Set the browser surfaces on purpose
   (selection color, caret, focus ring, tabular numerals): the cheapest tell of built vs assembled.

4. **Verify, bounded.** Say the round and judge-call budget out loud before starting.
   *Round 0, mechanical gate* (`references/eval-rubric.md` layer A): both viewports (1400x900,
   390x844), both schemes; overflow, contrast, type floor, tap targets, focus, reduced motion,
   heading structure, color-only status, rogue literals. Fix hard failures before any screenshot.
   *Rounds 1 to 2, critique in a FRESH context*: dispatch the critic as a separate subagent;
   same-context self-critique is not a fallback (self-preference is causal); if no independent
   context exists, stop and say so. The critic (`references/critique-prompt.md`) gets labelled
   crops (1568 px long edge max, one focused-state crop), the plan, tokens, round-0 results, the
   slop list, exemplars, then the source and computed styles (render finds WHAT, code finds
   WHERE). It returns eight 1-to-5 scores and UP TO 10 ranked issues, "none" allowed (cap, never
   floor: a floored count manufactures findings), each with a location, a measurable-vs-judgment
   tag, and a token-first fix. Apply tokens first, components second; re-run round 0; recapture.
   *Gates, per candidate* (`references/eval-rubric.md` layer B): a fixture-backed acceptance
   eval (a glance test, a task list) gates every candidate on both schemes, scored against the
   fixture (90% of question-runs or better; recognition questions from the above-the-fold crop
   alone). Then blinded pairwise against the previous ACCEPTED form: neutral labels, both
   orderings, three calls each; a regression is a majority in either ordering and rejects the
   round; a polish round (no measurable fix in it) must WIN, and a panel of ties rejects it.
   *Keep the best round, not the last.* A rejected fix list is reverted so the tree holds the
   kept form. The loop plateaus by round 2 to 3: two rounds default, a third only for a high-impact
   measurable issue. Never git add or git commit inside the loop; stage after it settles, by pathspec.

5. **Scale out, with evidence.** Extend the system to the remaining screens; each gets round 0
   before its capture; a screen needing its own hierarchy or layout is a new surface and takes
   steps 3 and 4 itself. A shared token or component changed while scaling out changes every
   consumer: re-gate them, hero first, or refuse the change into a new full-loop surface. End
   with the evidence attached: before/after images, round-0 results, eval scores, pairwise
   verdicts, swatch captures. Nothing is "done" on assertion.

## Register decides the treatment

On an operate surface, distinctiveness is precision and structure that encodes meaning: color
carries state and nothing else (red and amber reserved for it), status is shape + word + color,
tabular numerals right-aligned with rounded values ("$3.8M", not "$3,848,305.93"), labels beside
values, units on every number, one signature element and it carries information. The generic to
beat is the default shadcn dashboard; the escape is less chrome, not more. Editorial surfaces
may spend boldness; spend it in one place.

## Ground the direction in the subject

- **Media/collection libraries**: the owned artwork IS the interface; chrome recedes; type and texture borrow from the medium's physical history.
- **Data-dense analytics/ops**: typography and alignment make the hierarchy, not card chrome;
  density is a feature when the content warrants it, costume when it does not.
- **Client/brand work**: derive tokens from the client's brand; one signature; no default theme.

## Slop tells

The paired list (every NEVER with an INSTEAD, the 2026 tells, the banned faces, the mechanical
subset) is `references/slop-tells.md`; step 1 slop-tests directions against it, step 4's critic
gets it verbatim, and bans without replacements just relocate the default.

## Common mistakes

- Scaffolding ten screens at once: ten mediocre screens. One polished, then extend. Treating
  the critique loop as the source of quality: it polishes; steps 1 and 2 decided.
- Flooring the issue count ("find 10 problems"). A floored critic invents findings; cap it.
- Fixing components when the problem is a token. Change the variable, let it cascade.
- Waiting for the user to supply taste. Propose rendered directions with conviction; they pick.
  And more review rounds never supply it either: rigor polishes the same attractor.
- Project-specific identity notes belong in the project's own docs, not in this skill.

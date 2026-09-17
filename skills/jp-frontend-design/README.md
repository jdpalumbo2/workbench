# jp-frontend-design

A process skill: the order of work that gets a coding agent from a one-line ask to a
distinctive, verified UI. It governs sequence and gates; craft-level guidance (Anthropic's
`frontend-design`, a dataviz skill) loads beside it.

## What v2 changed (2026-09-17)

v1 was the consensus sequence (brief, tokens, reference analysis, hero, critique loop, scale
out) with the mechanisms left implicit. v2 applies the Atelier research memo
(`research/2026-09-02-ai-frontend-design-research.md`, ~350 graded sources across seven lanes)
and makes each step carry its mechanism:

- **Step 0 is new**: read the existing system first; preflight the browser automation, the
  evidence directory, and an independent critic context; a scope-guarded path for one-value
  tweaks.
- **Directions are rendered, not described** (`references/swatch.html`), span named axes and
  material families, and include a labelled conventional exit. Enumerate-then-pick is the
  diversity mechanism with controlled evidence behind it; bans alone just relocate the default.
- **Tokens store taste, they do not originate it**: the 15-line prose plan
  (`references/design-plan.md`) rides beside tokens.css, and a rogue-literal check enforces
  what models will not self-enforce.
- **The critique loop is bounded and externalized**: mechanical round 0 gates first
  (`references/eval-rubric.md` layer A); the critic runs in a fresh context with a capped issue
  count (`references/critique-prompt.md`); pairwise no-regression judging is blinded with both
  orderings; keep the best round, not the last; two rounds default, three max.
- **Register decides treatment**: operate surfaces escape generic through precision and
  meaning-encoding color, not decoration.
- **Evidence before done**: captures, gate results, and verdicts attach to the deliverable.

## Honest caveats

- The skill requires a browser automation that can render, capture, and script the page, and an
  independent context for critique. Without them it stops rather than degrades.
- There is no controlled eval of this skill itself. The memo grades which of its rules rest on
  controlled results and which are practice (`references/eval-rubric.md`, last section).
- The full verify loop is expensive in judge calls; the skill requires saying the budget before
  starting, and the low-stakes path exists so small changes do not pay it.

## Files

`SKILL.md` (the sequence) · `references/` (plan template, critic prompt, rubric, slop list,
swatch page) · `research/` (the memo this version implements; provenance in its README).

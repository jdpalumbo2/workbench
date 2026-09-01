You are reviewing an implementation plan before any code is written. The repo root is your
working directory; read whatever you need.

Plan: docs/2026-09-01-clodex-opus-orchestrator-overnight-plan.md

The ask it must satisfy, verbatim:
"A. Clodex bootstrap-hardening plan. Concrete proposed changes to clodex's first-run/bootstrap
behavior so that (a) a repo where clodex has never run, and (b) a repo running clodex under a
newer version than what it last bootstrapped with, both reliably converge on full re-derivation
of repo structure/state rather than partial or stale setup. Reference exact current line
ranges/sections of SKILL.md you're proposing to change. Call out what existing content this
replaces or removes - don't just add.
B. Opus-orchestration -> Codex-heavy rebuild plan. A full redesign proposal for a new version of
the opus-orchestration skill that: uses Codex for heavy reasoning/execution at most stages
instead of spinning up local Opus worker terminals under a second/third Claude subscription;
keeps Opus in the design only where research shows it's genuinely the better tool for a specific
stage; specifies exactly how clodex's own review passes get invoked programmatically by the
orchestrator itself, without ever surfacing a 'please review/approve' prompt back to Johnny
mid-run; describes the resulting worker/orchestrator topology precisely; applies the
tier-1/2/3 control framework to its own gates; states what parts of the current
opus-orchestration SKILL.md get deleted or replaced, not just what's added."

Round: 1

NOTE ON SHAPE: this plan's deliverable is a set of changes to skill files and two new scripts,
not application code. Read checks 2, 4 and 7 accordingly - "the files it names" are the skill
files and scripts in this repo, and "owned paths" are the files each proposed change would edit.

Check, in this order:

1. Does the plan satisfy the ask? Name anything asked for that no part of the plan delivers.
   Be specific about which of the seven numbered requirements above is unmet or only gestured at.

2. Is it grounded in this repo? OPEN THE FILES IT NAMES AND CHECK EVERY LINE NUMBER AND EVERY
   QUOTE. The plan cites specific line ranges in skills/clodex/SKILL.md, skills/clodex-plan/
   SKILL.md, skills/clodex-verify/SKILL.md, skills/clodex/profile.schema.json, skills/clodex/
   runner/run-codex.sh and skills/opus-orchestration/SKILL.md. A wrong line number or a
   misquoted line is a finding - report each one individually with the correct value. Flag any
   assumption the code contradicts and any file it plans to edit that does not exist.

3. Interrogate the plan's use of prior art, with the repo open - not from the plan's prose.
   Is the mechanism it proposes to copy (the clodex runner, the typed mandate, the lane-brief
   template, counts.py, the archive-on-close pattern) actually isomorphic to the problem it is
   being pointed at? Search the repo for a mechanism the author missed that already solves an
   isomorphic problem. Cite repo paths for every claim, including "found nothing".

4. Are the proposed changes' owned paths sufficient and disjoint? Flag work that no proposed
   change owns, any file two proposed changes would edit in incompatible ways, and any change
   that would break a consumer elsewhere in the repo that the plan does not mention. In
   particular: the plan proposes bumping profile.schema.json's schema_version from 1 to 2 and
   adding a required "bootstrap" object. Trace every place in the repo that reads
   schema_version or validates a profile and say whether the plan accounts for it.

5. Is each proposed change checkable by someone who did not write the plan? Flag any step where
   a reader could not tell whether it had been done correctly.

6. Does the plan's own evidence actually support its claims? It cites benchmark numbers,
   measured effect sizes, and local probe results. Flag any place where the conclusion drawn is
   stronger than the evidence cited supports, any number used to justify a design decision that
   the plan itself elsewhere calls unreliable, and any internal contradiction between sections.

7. Does the plan change behavior that the repo's own docs describe (README.md,
   skills/*/README.md, docs/clodex-design.md, docs/v0.2-debt.md) while saying nothing about
   updating them?

8. What breaks in production that this plan does not consider? Think specifically about: a
   half-applied schema migration, a lane that parks and is never unparked, the orchestrator
   dying mid-run, two orchestrator runs overlapping, and the interaction between the proposed
   bootstrap re-derivation and existing worktree lanes.

Report findings only. Do not edit the plan and do not write code. Use blocker/high/medium for
anything that would produce wrong or unshippable work, low/info for improvements. Return an
empty findings list if you find nothing.

# Lane-orchestration blocking-gate map

Source census: `docs/2026-09-01-orchestration-evidence/clodex-gate-census.md`.

| Component | Census line | Gate | Anchor | Verdict | Covered by |
|---|---:|---|---|---|---|
| `skills/clodex-build/SKILL.md` | L188 | change-boundary overlap between owned paths and dirty_at_start | `dirty_at_start` | pre-answered | the orchestrator forks every lane into a fresh worktree, so the dirty snapshot is empty by construction; a non-empty overlap in a lane is a park, not a modal |
| `skills/clodex-plan/SKILL.md` | L791 | plan approval bound to the current hash | `plan:approved` | mandate | grants plan-approval; consumption appends by:"mandate" bound to the run-scoped mandate |
| `skills/clodex-ship/SKILL.md` | L643 | verification-debt acceptance in words inside §5 | `debt` | unreachable | ship never runs unattended; debt acceptance is the human-owned core and no mandate can ever grant it |
| `skills/clodex-ship/SKILL.md` | L1457 | dirty-file guard before ship's first write | `untracked-files=all` | unreachable | ship never runs unattended |
| `skills/clodex-ship/SKILL.md` | L1511 | authorized-content compare on release files | `authorized` | unreachable | ship never runs unattended |
| `skills/clodex-ship/SKILL.md` | L1887 | reconcile pending release step before any retry | `reconcile` | unreachable | ship never runs unattended; the orchestrator's own receipts copy this discipline for dispatches |
| `skills/clodex/state/reducer.py` | L271 | approval binds to the CURRENT plan hash; every amendment revokes it | `superseding` | parks | trigger: any plan amendment mid-lane — the mandate is revoked and only the granting authority re-grants; ordinary build event, expected park |
| `skills/clodex-audit/SKILL.md` | L83 | premise correction that re-scopes the audit reaches the user first | `premise` | parks | trigger: a re-scoping premise correction; re-scoping is the user's call in every lane shape |
| `skills/clodex-audit/SKILL.md` | L204 | every audit finding disposed, presented with the report | `disposition` | mandate | grants finding-disposition (medium/low); blocker/high auto-accepted under mandate trips the orchestrator's gate 6b and parks |
| `skills/clodex-build/SKILL.md` | L676 | every batch finding recorded then disposed fixed/accepted/rejected | `only the user` | mandate | grants finding-disposition (medium/low); blocker/high accepted under mandate parks via gate 6b |
| `skills/clodex-build/SKILL.md` | L899 | re-approve the amended plan bound to the new hash | `approval binds to plan hash` | parks | trigger: amendment mid-build; same family as the reducer's revocation gate — the sleeping user is the only re-granting authority |
| `skills/clodex-plan/SKILL.md` | L451 | direction checkpoint — shape card approved before the review loop | `shape card` | mandate | grants direction-approval ONLY when the brief's §4 itself states the shape (clodex-plan §7's own rule); a brief without the shape parks the lane at the checkpoint |
| `skills/clodex-plan/SKILL.md` | L693 | every plan-review finding recorded then disposed, nothing dropped | `disposition` | mandate | grants finding-disposition (medium/low); blocker/high accepted under mandate parks via gate 6b |
| `skills/clodex-ship/SKILL.md` | L315 | unowned-commit disposition before the authorization | `unowned` | unreachable | ship never runs unattended |
| `skills/clodex-ship/SKILL.md` | L576 | release authorization — one message, one yes | `AUTHORIZATION VALID` | unreachable | the human-owned core; morning session with Johnny present, in every run |
| `skills/clodex-verify/SKILL.md` | L564 | verify finding disposition — only the user accepts/rejects | `finding-disposition` | mandate | grants finding-disposition (medium/low); blocker/high accepted under mandate parks via gate 6b |
| `skills/clodex-build/SKILL.md` | L463 | a STRAY is a scope change and is the user's call | `STRAY` | parks | trigger: any stray path in the boundary check; not in the mandate's three-verb vocabulary |
| `skills/clodex-plan/SKILL.md` | L160 | discovery — blocking/decision-bearing questions to the user | `decision-bearing` | pre-answered | brief §10 (decisions assigned with criteria) and §5 (section-precise reading); a question outside both parks the lane |
| `skills/clodex-plan/SKILL.md` | L630 | round budget — only the user funds rounds past 3 | `Only the user funds rounds past 3` | parks | trigger: blockers/highs still arriving at round 3; expected on genuinely hard plans |
| `skills/clodex-ship/SKILL.md` | L581 | typed mandate excluded from release authorization and debt | `mandate` | unreachable | the exclusion IS the design: those two gates stay human in every run; nothing to route around |
| `skills/clodex-ship/SKILL.md` | L1324 | always-ask-exact — literal argv approved every execution | `always-ask-exact` | unreachable | ship never runs unattended |
| `skills/clodex-ship/SKILL.md` | L1815 | empty verify_live — the user must look and say what they see | `verify_live` | unreachable | ship never runs unattended; no deploy exists overnight |
| `skills/clodex-verify/SKILL.md` | L131 | malformed run (no declared classes / null plan) hands back to close | `hand back` | parks | trigger: malformed run state; closing a run and opening a follow-on is the user's |
| `skills/clodex-verify/SKILL.md` | L385 | client-artifact is not bookable as debt; no access is a blocker now | `client-artifact` | parks | trigger: any client_visible lane reaching verify — CERTAIN park; the dry-run flags client_visible lanes as guaranteed parks at dispatch-plan time, which is the honest scope statement |
| `skills/clodex-verify/SKILL.md` | L586 | red gate outcome choice A/B/C put to the user | `outcome` | parks | trigger: any declared evidence gate failing at verify |
| `skills/clodex-verify/SKILL.md` | L596 | outcome A: the run ends here; clodex closes it | `run ends here` | parks | trigger: verification failure terminal path; the follow-on run's parent is the user's decision |
| `skills/clodex/runner/run-codex.sh` | L217 | always-ask-exact actions get literal argv approved every time | `PROMPT_FILE` | unreachable | ship never runs unattended; enforcement lives in clodex-ship |
| `skills/clodex/templates/scenario-card.md` | L29 | CLIENT-ACCEPTED requires the named operator's confirmation | `Accepted` | unreachable | a client's word cannot be granted by anyone; morning-and-beyond, per the estate's verified ladder |

Verdict tally: 2 pre-answered · 6 mandate · 9 parks · 11 unreachable.

The verdicts are reviewed design judgment, not machine-proven dispositions. The anchor phrases
are machine-checked against the cited files on this branch. The census is unaudited input and is
retained here as the source for this transcription.

<!-- Client scenario card (added 2026-08-28 process revamp).

One card per client-facing work item, written BEFORE build (it feeds the plan's
shape card) and replayed at acceptance. The card is the client's representative
in the definition of done: a work item is CLIENT-ACCEPTED when the named
operator confirms the expected outcomes on a real (or production-shaped) run.
Keep one card per scenario in the repo's docs; a release names which cards it
touches. -->

# Scenario: <name, e.g. "Existing deal enters DD with the standard template">

- **Operator**: <the real person who performs or receives this - not "the user">
- **Trigger**: <the exact action, in their words: what they click, move, send>
- **Input shape**: <the real data: which template tree, which email form, size,
  timing - name the fixture that mirrors it>

**Expected outcome, per surface** (every surface the operator can see):

| Surface | Expected |
|---|---|
| <CRM / DB> | <deal, fields, stage> |
| <Files / Drive> | <folders, copies, placement> |
| <Dashboard / UI> | <what the row/page shows> |
| <Email / notices> | <who receives what - and who must NOT> |
| Next unattended scheduled run | <what it must show the next morning> |

- **Production proof**: <the run/readback that demonstrates it live, and who watches>
- **Failure fallback**: <what the operator sees and does when it fails - "silent" is a defect>
- **Accepted**: <date + operator's words, when the operator confirmed - blank until then>

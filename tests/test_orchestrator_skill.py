#!/usr/bin/env python3
"""Content pins for the lane-orchestration skill replacement (plan batch 4).

Exploits reproduce the B.12 accounting failures the plan reviews caught:
kept rules silently dropped, the stale nesting clause surviving, the template
additions asserted by headings that already existed, and the workflow
template's two-round cap contradicting the estate's three. Controls prove the
replacement carries what it claims to carry.
"""

import re
import unittest
from pathlib import Path


CATALOGUE = Path(__file__).resolve().parent.parent
SKILL = CATALOGUE / "skills" / "lane-orchestration" / "SKILL.md"
README = CATALOGUE / "skills" / "lane-orchestration" / "README.md"
TEMPLATE_JS = CATALOGUE / "skills" / "lane-orchestration" / "workflow-template.js"
LANE_BRIEF = CATALOGUE / "skills" / "clodex" / "templates" / "lane-brief.md"
OLD_DIR = CATALOGUE / "skills" / "opus-orchestration"


class SkillReplacementCheck(unittest.TestCase):
    def setUp(self):
        self.skill = SKILL.read_text()
        self.brief = LANE_BRIEF.read_text()

    def test_control_kept_rules_survive_the_rewrite(self):
        # B.12: L23, L24, L27 are KEPT — the rules, not the line numbers.
        self.assertIn("nothing load-bearing lives only in chat", self.skill)
        self.assertIn("One worker per independent lane", self.skill)
        self.assertIn("A worker never passes its own gate", self.skill)

    def test_exploit_stale_nesting_clause_is_gone(self):
        # B.12: L53's clause and L66's row were factually stale.
        self.assertNotIn("Subagents cannot spawn subagents", self.skill)
        self.assertNotIn("Agents cannot nest", self.skill)

    def test_control_workflow_variant_kept_with_the_real_constraints(self):
        self.assertIn("workflow-template.js", self.skill)
        self.assertIn("no filesystem and no shell", self.skill)
        self.assertIn("resume reruns every agent that started after", self.skill)

    def test_control_four_new_common_mistakes_rows(self):
        for phrase in (
            "Forwarding a reviewer's findings verbatim",
            "Assuming a flag was honored",
            "held-out oracle",
            "Citing a source's headline",
        ):
            self.assertIn(phrase, self.skill)

    def test_control_honest_scope_statement_present(self):
        self.assertIn("direction gate is `no`", self.skill)
        self.assertIn("staging target", self.skill)

    def test_exploit_template_round_cap_is_the_estate_three(self):
        # Moving the template unchanged would have preserved "Two rounds max"
        # against the estate's settled 3 (r1-F011).
        text = TEMPLATE_JS.read_text()
        self.assertNotIn("Two rounds max", text)
        self.assertIn("Three rounds", text)
        self.assertRegex(text, re.compile(r"i < 3 && allIssues"))

    def test_exploit_lane_brief_additions_are_content_not_headings(self):
        # r3-F009 + b4r1-F004: the §4/§16 headings pre-existed; the ADDITIONS
        # are asserted by their new content, POSITIONALLY inside their
        # sections, with the v8 semantics pinned (the brief text is
        # informative, the ledger event is the authority, consumption is
        # by:"mandate").
        s4_start = self.brief.index("## 4. Scoped exceptions")
        s4_end = self.brief.index("## 5.")
        s4 = self.brief[s4_start:s4_end]
        self.assertIn("run-scoped mandate granted at run:opened", s4)
        self.assertIn("This line is informative", s4)
        self.assertIn("EVENT in the lane's ledger is the authority", s4)
        self.assertIn('by:"mandate"', s4)
        self.assertIn("push: true", s4)

        s16 = self.brief[self.brief.index("## 16. REPORT BACK"):]
        self.assertIn("PARKED-<lane>.md", s16)
        self.assertIn("Cost so far:", s16)
        self.assertIn("a question with a name on it", s16)

    def test_control_remaining_keep_rows_survive(self):
        # b4r1-F001: the research contract, convergence endgame, and the two
        # non-stale script-mode rows are B.12 KEEPs too.
        self.assertIn("URL and date", self.skill)
        self.assertIn("distinct angle", self.skill)
        self.assertIn("marked unaudited", self.skill)
        self.assertIn("Endgame:", self.skill)
        self.assertIn("`bash()` / `Date.now()`", self.skill)
        self.assertIn("Agents inherit the session model", self.skill)

    def test_control_blast_radius_table_matches_b7(self):
        # b4r1-F003: the everything-else row keeps "gate 13 still runs".
        self.assertIn("One cross-family review round", self.skill)
        self.assertIn("gate 13 still runs", self.skill)
        self.assertIn("Client-visible surface", self.skill)

    def test_control_documented_unpark_command_is_complete(self):
        # b4r1-F002: the documented command must carry every required arg.
        self.assertIn("--unpark <lane> <run-plan.json> --ledger-dir", self.skill)

    def test_exploit_old_skill_directory_is_gone(self):
        self.assertFalse(
            (OLD_DIR / "SKILL.md").exists(),
            "opus-orchestration/SKILL.md still exists — the rename did not land",
        )

    def test_control_readme_carries_migration_and_dry_run_status(self):
        readme = README.read_text()
        self.assertIn("DRY-RUN ONLY", readme)
        self.assertIn("rm -f ~/.claude/skills/opus-orchestration", readme)
        self.assertIn("ln -s", readme)
        self.assertIn("no\nper-lane Codex ceiling", readme.replace("**", ""))


if __name__ == "__main__":
    unittest.main()

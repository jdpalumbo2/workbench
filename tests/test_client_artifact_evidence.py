#!/usr/bin/env python3
"""Exploit+control checks for the five-class evidence vocabulary.

The verify-stage check is embedded in clodex-verify/SKILL.md, so these tests
parse its CLASSES tuple instead of copying the production vocabulary into the
test.  The profile cases use the catalogue's real schema validator.
"""

import ast
import importlib.util
import json
import re
import unittest
from pathlib import Path


CATALOGUE = Path(__file__).resolve().parent.parent
VERIFY_SKILL = CATALOGUE / "skills" / "clodex-verify" / "SKILL.md"
PROFILE_SCHEMA = CATALOGUE / "skills" / "clodex" / "profile.schema.json"
STATE = CATALOGUE / "skills" / "clodex" / "state" / "clodex_state.py"
VERSION = CATALOGUE / "skills" / "clodex" / "VERSION"


def load_state_module():
    spec = importlib.util.spec_from_file_location(
        "client_artifact_clodex_state", STATE
    )
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load the catalogue state module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATE_MODULE = load_state_module()


def classes_from_verify_skill():
    """Read the production CLASSES tuple from the embedded completeness check."""
    match = re.search(r"^CLASSES = (\(.*\))$", VERIFY_SKILL.read_text(), re.MULTILINE)
    if not match:
        raise AssertionError("cannot find CLASSES tuple in clodex-verify/SKILL.md")
    classes = ast.literal_eval(match.group(1))
    if not isinstance(classes, tuple):
        raise AssertionError("CLASSES in clodex-verify/SKILL.md is not a tuple")
    return classes


def completeness_blockers(verification, classes):
    """Reproduce §10's completeness logic, including its membership rule."""
    ver, blockers = verification, []
    declared = sorted({d.get("class") for d in ver["declared"]})
    if not declared:
        blockers.append("the plan declared no evidence classes")
    have_ev = {e.get("class") for e in ver["evidence"]}
    have_debt = {d.get("class") for d in ver["debt"]}
    for current in declared:
        ev, debt = current in have_ev, current in have_debt
        verdict = ("evidence" if ev and not debt else
                   "debt" if debt and not ev else
                   "BOTH — a class is produced or deferred, never both" if ev else
                   "NEITHER — no evidence and no debt")
        if ev == debt:
            blockers.append("class %s: %s" % (current, verdict))

    for item in ver["debt"] + ver["evidence"]:
        if item.get("class") not in classes:
            blockers.append(
                "class %r is not one of: %s"
                % (item.get("class"), ", ".join(classes))
            )
    return blockers


def verification(declared, evidence=None, debt=None):
    return {
        "declared": [{"class": item} for item in declared],
        "evidence": evidence or [],
        "debt": debt or [],
    }


def base_profile():
    return {
        "schema_version": 1,
        "commands": {
            "install": None,
            "build": None,
            "test": None,
            "lint": None,
            "typecheck": None,
        },
        "version": {"source": None, "field": None, "bump_rule": None},
        "branch": {"default": "main", "work_on_default": True},
        "tag": {"enabled": False, "format": None},
        "changelog": None,
        "deploy": None,
        "evidence": {"default_classes": ["tests"]},
        "runtimes": [],
        "required_env": [],
        "actions": [],
    }


class ClientArtifactEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classes = classes_from_verify_skill()
        cls.schema = json.loads(PROFILE_SCHEMA.read_text())

    def test_production_membership_check_structure_is_intact(self):
        """completeness_blockers() below is a reimplementation, so this pins
        the PRODUCTION block's shape: the membership check must still run over
        the union of debt and evidence and refuse a class outside CLASSES.
        Deleting or reversing the check in the SKILL.md fails here."""
        text = VERIFY_SKILL.read_text()
        self.assertIn('for item in list(ver["debt"]) + list(ver["evidence"]):', text)
        union_at = text.index('for item in list(ver["debt"]) + list(ver["evidence"]):')
        membership = text[union_at:union_at + 300]
        self.assertIn('if item.get("class") not in CLASSES:', membership)
        self.assertIn("is not one of", membership)

    def test_exploit_old_four_class_tuple_rejected_current_five_class_tuple_accepts(self):
        shape = verification(
            ["client-artifact"],
            evidence=[{
                "class": "client-artifact",
                "how": "open the sent client digest",
                "result": "the received artifact matches the accepted example",
            }],
        )
        old_classes = ("tests", "real-data", "live-check", "visual")
        old_blockers = completeness_blockers(shape, old_classes)
        self.assertEqual(
            old_blockers,
            ["class 'client-artifact' is not one of: tests, real-data, live-check, visual"],
        )
        self.assertEqual(completeness_blockers(shape, self.classes), [])

    def test_client_artifact_profile_enum_is_allowed(self):
        default_classes = self.schema["properties"]["evidence"]["properties"]["default_classes"]
        self.assertIn("client-artifact", default_classes["items"]["enum"])
        STATE_MODULE.validate(["client-artifact"], default_classes)

    def test_tests_declaration_still_reaches_complete(self):
        shape = verification(
            ["tests"],
            evidence=[{"class": "tests", "how": "unittest", "result": "pass"}],
        )
        self.assertEqual(completeness_blockers(shape, self.classes), [])

    def test_client_artifact_debt_booking_reaches_complete(self):
        shape = verification(
            ["client-artifact"],
            debt=[{
                "class": "client-artifact",
                "reason": "no serving change has produced an artifact yet",
                "risk": "the client-facing result remains unread by the recipient",
            }],
        )
        self.assertEqual(completeness_blockers(shape, self.classes), [])

    def test_unknown_evidence_class_is_rejected(self):
        shape = verification(
            ["made-up"],
            evidence=[{"class": "made-up", "how": "synthetic", "result": "pass"}],
        )
        blockers = completeness_blockers(shape, self.classes)
        self.assertEqual(len(blockers), 1)
        self.assertIn("class 'made-up' is not one of", blockers[0])

    def test_unknown_debt_class_is_rejected(self):
        shape = verification(
            ["made-up"],
            debt=[{
                "class": "made-up",
                "reason": "synthetic",
                "risk": "synthetic",
            }],
        )
        blockers = completeness_blockers(shape, self.classes)
        self.assertEqual(len(blockers), 1)
        self.assertIn("class 'made-up' is not one of", blockers[0])

    def test_well_formed_bootstrap_validates(self):
        bootstrap = {
            "clodex_version": VERSION.read_text().strip(),
            "derived_at": "2026-09-01",
            "repo_fingerprint": "sha256:" + "a" * 64,
            "inspected": [
                {"marker": "package.json", "present": False, "value": None},
                {"marker": "package.json#scripts", "present": True, "value": "test"},
            ],
        }
        profile = base_profile()
        profile["bootstrap"] = bootstrap
        bootstrap_schema = self.schema["properties"]["bootstrap"]
        self.assertEqual(
            bootstrap_schema["required"],
            ["clodex_version", "derived_at", "repo_fingerprint", "inspected"],
        )
        self.assertFalse(bootstrap_schema["additionalProperties"])
        self.assertFalse(bootstrap_schema["properties"]["inspected"]["items"]["additionalProperties"])
        STATE_MODULE.validate(profile, self.schema)

    def test_bootstrap_is_optional(self):
        self.assertNotIn("bootstrap", self.schema["required"])
        STATE_MODULE.validate(base_profile(), self.schema)


if __name__ == "__main__":
    unittest.main()

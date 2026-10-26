"""Synthetic, local ontology-context teaching program. Python 3.10+ standard library.

No LLM, remote API, MCP server, production authorization, warehouse or side effects.
`--test` runs focused tests; no argument prints three deterministic tool results.
"""
import copy
import hashlib
import json
import sqlite3
import sys
import unittest
from datetime import date

MODEL = "model-v1"
BINDING = "binding-v1"
RECORD_SET = "records-v1"
DOCS = {
    "recovery-d2": "Recover authentication only after required approval and checks.",
    "policy-d1": "Policy version 1: reviewed historical instructions.",
    "policy-d2": "Policy version 2: reviewed replacement instructions.",
}
ASSERTIONS = [
    {"id": "record-r1", "policy": "policy-version-1", "valid_from": "2026-01-01", "valid_to": None,
     "recorded_from": "2026-01-01", "recorded_to": "2026-04-15", "document": "policy-d1"},
    {"id": "record-r2", "policy": "policy-version-1", "valid_from": "2026-01-01", "valid_to": "2026-03-01",
     "recorded_from": "2026-04-15", "recorded_to": None, "document": "policy-d1"},
    {"id": "record-r3", "policy": "policy-version-2", "valid_from": "2026-03-01", "valid_to": None,
     "recorded_from": "2026-04-15", "recorded_to": None, "document": "policy-d2"},
]


def contains(start, end, value):
    return date.fromisoformat(start) <= date.fromisoformat(value) and (
        end is None or date.fromisoformat(value) < date.fromisoformat(end))


class ContextDemo:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE deployments(service_id TEXT, environment TEXT, auth_service TEXT,
                operator TEXT, PRIMARY KEY(service_id, environment));
            CREATE TABLE procedures(procedure_id TEXT, service_id TEXT, environment TEXT,
                approved INTEGER, document TEXT);
        """)
        self.db.executemany("INSERT INTO deployments VALUES (?, ?, ?, ?)", [
            ("portal", "production", "identity", "portal-experience"),
            ("identity", "production", None, "identity-operations"),
            ("portal", "test", "identity", "test-support"),
            ("identity", "test", None, "test-operations"),
        ])
        self.db.execute("INSERT INTO procedures VALUES (?, ?, ?, ?, ?)",
                        ("authentication-recovery", "identity", "production", 1, "recovery-d2"))
        self.assertions = copy.deepcopy(ASSERTIONS)
        self.docs = dict(DOCS)

    def close(self):
        self.db.close()

    def envelope(self):
        return {"model": MODEL, "binding": BINDING, "record_set": RECORD_SET,
                "mode": "synthetic_local_demonstration", "status": "blocked",
                "action_executed": False, "diagnosis_established": False}

    def support(self, service, environment, readable_documents, model=MODEL, binding=BINDING):
        result = self.envelope()
        if model != MODEL or binding != BINDING:
            return dict(result, blocker="release_mismatch")
        if environment not in {"production", "test"}:
            return dict(result, blocker="environment_required_or_unsupported")
        row = self.db.execute("SELECT * FROM deployments WHERE service_id=? AND environment=?",
                              (service, environment)).fetchone()
        if row is None:
            return dict(result, blocker="service_unknown")
        target = self.db.execute("SELECT * FROM deployments WHERE service_id=? AND environment=?",
                                 (row["auth_service"], environment)).fetchone()
        if target is None:
            return dict(result, blocker="authentication_dependency_unknown")
        if not target["operator"]:
            return dict(result, blocker="operator_unknown")
        matches = self.db.execute(
            "SELECT * FROM procedures WHERE service_id=? AND environment=? AND approved=1",
            (target["service_id"], environment)).fetchall()
        if len(matches) != 1:
            return dict(result, blocker="procedure_unknown_or_ambiguous")
        procedure = matches[0]
        doc = procedure["document"]
        if doc not in readable_documents or doc not in self.docs:
            return dict(result, blocker="supporting_document_unavailable")
        return dict(result, status="context_available", service=service, environment=environment,
                    dependency=target["service_id"], operator=target["operator"],
                    procedure=procedure["procedure_id"], document_revision=doc,
                    evidence_text=self.docs[doc], coverage="fixed declared lookup path")

    def policy(self, valid_as_of, recorded_as_of, readable_documents):
        # Validate both values even if there are no matching assertions.
        date.fromisoformat(valid_as_of)
        date.fromisoformat(recorded_as_of)
        result = dict(self.envelope(), valid_as_of=valid_as_of, recorded_as_of=recorded_as_of)
        matches = [a for a in self.assertions if
                   contains(a["valid_from"], a["valid_to"], valid_as_of) and
                   contains(a["recorded_from"], a["recorded_to"], recorded_as_of)]
        if len(matches) != 1:
            return dict(result, blocker="policy_unknown_or_conflicting")
        assertion = matches[0]
        doc = assertion["document"]
        if doc not in readable_documents or doc not in self.docs:
            return dict(result, blocker="supporting_document_unavailable")
        return dict(result, status="context_available", record_assertion=assertion["id"],
                    policy_version=assertion["policy"], document_revision=doc,
                    evidence_text=self.docs[doc])

    def release_digest(self):
        # Hash this exact documented JSON encoding, not arbitrary RDF semantics.
        payload = {"model": MODEL, "binding": BINDING, "record_set": RECORD_SET,
                   "assertions": self.assertions, "documents": self.docs}
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.demo = ContextDemo()
        self.addCleanup(self.demo.close)

    def test_support(self):
        r = self.demo.support("portal", "production", {"recovery-d2"})
        self.assertEqual(r["operator"], "identity-operations")
        self.assertFalse(r["action_executed"])
        self.assertFalse(r["diagnosis_established"])

    def test_environment_required(self):
        self.assertIn("environment", self.demo.support("portal", "", set())["blocker"])

    def test_no_cross_environment_procedure(self):
        r = self.demo.support("portal", "test", {"recovery-d2"})
        self.assertEqual(r["blocker"], "procedure_unknown_or_ambiguous")

    def test_read_permission(self):
        r = self.demo.support("portal", "production", set())
        self.assertEqual(r["blocker"], "supporting_document_unavailable")
        self.assertNotIn("document_revision", r)
        self.assertNotIn("evidence_text", r)

    def test_pinned_document_missing(self):
        del self.demo.docs["recovery-d2"]
        self.assertIn("unavailable", self.demo.support("portal", "production", {"recovery-d2"})["blocker"])

    def test_release_mismatch(self):
        self.assertEqual(self.demo.support("portal", "production", set(), model="model-v2")["blocker"], "release_mismatch")

    def test_unknown_operator(self):
        self.demo.db.execute("UPDATE deployments SET operator=NULL WHERE service_id=?", ("identity",))
        self.assertEqual(self.demo.support("portal", "production", {"recovery-d2"})["blocker"], "operator_unknown")

    def test_ambiguous_procedure(self):
        self.demo.db.execute("INSERT INTO procedures VALUES (?, ?, ?, ?, ?)",
                             ("second", "identity", "production", 1, "recovery-d2"))
        self.assertEqual(self.demo.support("portal", "production", {"recovery-d2"})["blocker"], "procedure_unknown_or_ambiguous")

    def test_historical_knowledge(self):
        r = self.demo.policy("2026-03-20", "2026-03-20", {"policy-d1", "policy-d2"})
        self.assertEqual(r["record_assertion"], "record-r1")

    def test_corrected_knowledge(self):
        r = self.demo.policy("2026-03-20", "2026-04-16", {"policy-d1", "policy-d2"})
        self.assertEqual(r["record_assertion"], "record-r3")

    def test_half_open_boundary(self):
        r = self.demo.policy("2026-03-01", "2026-04-15", {"policy-d1", "policy-d2"})
        self.assertEqual(r["policy_version"], "policy-version-2")

    def test_conflicting_assertions(self):
        self.demo.assertions.append(dict(self.demo.assertions[2], id="conflict"))
        self.assertEqual(self.demo.policy("2026-03-20", "2026-04-16", set())["blocker"], "policy_unknown_or_conflicting")

    def test_invalid_date(self):
        with self.assertRaises(ValueError):
            self.demo.policy("2026-02-30", "2026-04-16", set())

    def test_parameterized_lookup(self):
        self.assertEqual(self.demo.support("portal' OR 1=1 --", "production", set())["blocker"], "service_unknown")

    def test_digest_tracks_content(self):
        before = self.demo.release_digest()
        self.assertEqual(before, self.demo.release_digest())
        self.demo.docs["policy-d2"] += " Changed."
        self.assertNotEqual(before, self.demo.release_digest())


def demonstration():
    demo = ContextDemo()
    try:
        allowed = set(DOCS)
        output = {"support": demo.support("portal", "production", allowed),
                  "historical": demo.policy("2026-03-20", "2026-03-20", allowed),
                  "corrected": demo.policy("2026-03-20", "2026-04-16", allowed)}
        print(json.dumps(output, indent=2))
    finally:
        demo.close()


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        unittest.main(argv=[sys.argv[0]])
    elif not sys.argv[1:]:
        demonstration()
    else:
        raise SystemExit("Usage: python3 examples/capstone.py [--test]")

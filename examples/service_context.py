"""Synthetic book exercise: declared context lookup, not an ontology reasoner.

Run from the book directory with Python 3.9 or later:
    python3 examples/service_context.py
    python3 examples/service_context.py --test

No network, dependencies, credentials, LLM calls, writes or service execution.
The Boolean document-access input represents an already completed access check;
it is not a production authorization design.
"""

import copy
import json
import sys
import unittest


FACTS = {
    "view": "example-release-1",
    "services": {
        "portal": {"authentication_service": "identity-service"},
        "identity-service": {"operator": "identity-operations"},
    },
    "procedures": [
        {
            "id": "authentication-recovery",
            "applies_to": "identity-service",
            "environment": "example-production",
            "approved": True,
            "document_revision": "recovery-document-r2",
        }
    ],
    "available_document_revisions": ["recovery-document-r2"],
}


def retrieve_context(facts, service_id, environment, can_read_document):
    """Resolve the exercise's fixed path; expose unknown/ambiguous premises.

    This does not implement general traversal, temporal selection, model
    validation, current directory verification, or completeness guarantees.
    """
    response = {
        "view": facts["view"],
        "status": "blocked",
        "scope": "declared_support_context",
        "diagnosis_established": False,
        "action_executed": False,
    }
    service = facts["services"].get(service_id)
    if service is None:
        return dict(response, blocker="service_unknown")
    dependency_id = service.get("authentication_service")
    dependency = facts["services"].get(dependency_id)
    if dependency is None:
        return dict(response, blocker="authentication_dependency_unknown")
    operator = dependency.get("operator")
    if not operator:
        return dict(response, blocker="operator_unknown")
    procedures = [
        p for p in facts["procedures"]
        if p["applies_to"] == dependency_id
        and p["environment"] == environment and p["approved"]
    ]
    if not procedures:
        return dict(response, blocker="applicable_procedure_unknown")
    if len(procedures) != 1:
        return dict(response, blocker="procedure_ambiguous")
    procedure = procedures[0]
    revision = procedure["document_revision"]
    if not can_read_document or revision not in facts["available_document_revisions"]:
        # Do not disclose a restricted document identifier in this exercise.
        return dict(response, blocker="supporting_document_unavailable")
    return dict(
        response,
        status="context_available",
        service=service_id,
        authentication_service=dependency_id,
        operator=operator,
        procedure=procedure["id"],
        supporting_document_revision=revision,
    )


class ContextExerciseTests(unittest.TestCase):
    def setUp(self):
        self.facts = copy.deepcopy(FACTS)

    def retrieve(self, access=True):
        return retrieve_context(self.facts, "portal", "example-production", access)

    def test_declared_path_and_evidence(self):
        answer = self.retrieve()
        self.assertEqual(answer["status"], "context_available")
        self.assertEqual(answer["operator"], "identity-operations")
        self.assertEqual(answer["supporting_document_revision"], "recovery-document-r2")
        self.assertFalse(answer["diagnosis_established"])
        self.assertFalse(answer["action_executed"])

    def test_missing_operator_is_unknown(self):
        del self.facts["services"]["identity-service"]["operator"]
        self.assertEqual(self.retrieve()["blocker"], "operator_unknown")

    def test_restricted_document_is_not_disclosed(self):
        answer = self.retrieve(access=False)
        self.assertEqual(answer["blocker"], "supporting_document_unavailable")
        self.assertNotIn("supporting_document_revision", answer)

    def test_missing_document_does_not_substitute_latest(self):
        self.facts["available_document_revisions"] = ["recovery-document-r3"]
        self.assertEqual(self.retrieve()["blocker"], "supporting_document_unavailable")

    def test_multiple_procedures_are_ambiguous(self):
        other = dict(self.facts["procedures"][0], id="alternative-recovery")
        self.facts["procedures"].append(other)
        self.assertEqual(self.retrieve()["blocker"], "procedure_ambiguous")

    def test_wrong_environment_does_not_match(self):
        self.facts["procedures"][0]["environment"] = "example-test"
        self.assertEqual(self.retrieve()["blocker"], "applicable_procedure_unknown")


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        unittest.main(argv=[sys.argv[0]])
    elif not sys.argv[1:]:
        print(json.dumps(retrieve_context(FACTS, "portal", "example-production", True), indent=2))
    else:
        raise SystemExit("Usage: python3 examples/service_context.py [--test]")

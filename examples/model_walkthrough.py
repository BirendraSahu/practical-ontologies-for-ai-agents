"""Read and inspect the book's explicit JSON model. Python 3.10+ standard library.

This implements direct, single-type endpoint checks for a tiny custom format.
It does not implement RDFS/OWL inference, SHACL, temporal data or authorization.
"""
import copy
import json
from pathlib import Path


def validate(model):
    errors = []
    for subject, description in model["subjects"].items():
        if description["type"] not in model["classes"]:
            errors.append("unknown_type:" + subject)
    for source, predicate, target in model["assertions"]:
        if source not in model["subjects"] or target not in model["subjects"]:
            errors.append("unresolved_endpoint")
            continue
        if predicate not in model["relations"]:
            errors.append("unknown_predicate")
            continue
        spec = model["relations"][predicate]
        if model["subjects"][source]["type"] != spec["source"]:
            errors.append("source_type_mismatch")
        if model["subjects"][target]["type"] != spec["target"]:
            errors.append("target_type_mismatch")
    return errors


def objects(model, subject, predicate):
    return [target for source, relation, target in model["assertions"]
            if source == subject and relation == predicate]


def lookup_operator(model):
    dependencies = objects(model, "portal-production", "depends_on")
    if len(dependencies) != 1:
        raise ValueError("dependency_unknown_or_ambiguous")
    operators = objects(model, dependencies[0], "operated_by")
    if len(operators) != 1:
        raise ValueError("operator_unknown_or_ambiguous")
    return operators[0]


def main():
    model = json.loads(Path(__file__).with_name("model.json").read_text())
    assert validate(model) == []
    assert lookup_operator(model) == "identity-operations"
    invalid = copy.deepcopy(model)
    invalid["assertions"].append(["identity-production", "operated_by", "access-policy"])
    assert "target_type_mismatch" in validate(invalid)
    proposed = copy.deepcopy(model)
    proposed["assertions"] = [[s, p, "platform-operations"] if p == "operated_by" else [s, p, t]
                              for s, p, t in proposed["assertions"]]
    assert validate(proposed) == []
    assert lookup_operator(proposed) == "platform-operations"
    assert lookup_operator(model) == "identity-operations"
    print("Accepted selection: identity-operations")
    print("Invalid Policy-as-Team change: target_type_mismatch")
    print("Proposed selection: platform-operations; original unchanged")
    print("Six walkthrough assertions passed. No publication or external action occurred.")


if __name__ == "__main__":
    main()

from gym.cases import generate_cases
from gym.verifier import action_is_supported, analyze, ground_truth, validate_decision

EXPECTED = {
    "all_clear": "complete",
    "still_present": "incomplete",
    "audit_deleted": "incomplete",
    "unknown_evidence": "needs_review",
    "ingestion_failed": "needs_review",
    "missing_record": "needs_review",
    "mixed_violation_and_unknown": "incomplete",
}


def test_ground_truth_matches_category():
    for c in generate_cases():
        assert ground_truth(c)["decision"] == EXPECTED[c["category"]], c["case_id"]


def test_violation_beats_unresolved():
    case = next(c for c in generate_cases() if c["category"] == "mixed_violation_and_unknown")
    truth = ground_truth(case)
    assert truth["decision"] == "incomplete"
    kinds = {k for k, _ in truth["required_actions"]}
    assert "delete" in kinds and "investigate" in kinds


def test_complete_case_requires_no_actions():
    case = next(c for c in generate_cases() if c["category"] == "all_clear")
    assert ground_truth(case)["required_actions"] == set()


def test_missing_record_is_unresolved_not_fine():
    case = next(c for c in generate_cases() if c["category"] == "missing_record")
    assert ground_truth(case)["unresolved"]


def test_validate_decision_rejects_garbage():
    assert validate_decision("complete")
    assert validate_decision({"decision": "maybe"})
    assert validate_decision({"decision": "complete", "actions": "x"})
    assert validate_decision({"decision": "complete", "actions": [{"type": "nuke", "target": "audit_log"}]})
    assert validate_decision({"decision": "complete", "actions": []}) is None


def test_action_support_needs_matching_evidence():
    case = next(c for c in generate_cases() if c["category"] == "still_present")
    rec = next(r for r in case["records"] if r["status"] == "present")
    other = next(r for r in case["records"] if r["status"] != "present")
    good = {"type": "delete", "target": rec["system"], "evidence_id": rec["evidence_id"]}
    wrong_evidence = {"type": "delete", "target": rec["system"], "evidence_id": other["evidence_id"]}
    made_up = {"type": "delete", "target": rec["system"], "evidence_id": "nope"}
    assert action_is_supported(good, case["records"])
    assert not action_is_supported(wrong_evidence, case["records"])
    assert not action_is_supported(made_up, case["records"])

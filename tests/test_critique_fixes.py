"""Regression tests for weaknesses found by outside review (Gemini critique, 24 Nov 2026)."""
from agents.baselines import ReferenceAgent
from gym import generate_cases
from gym.constants import ALL_SYSTEMS
from gym.reward import compute_reward
from gym.verifier import analyze, ground_truth
from grade import grade

CASES = generate_cases()


def _needs_actions():
    return [c for c in CASES if ground_truth(c)["required_actions"]]


def test_correct_label_with_zero_actions_is_worth_little():
    for c in _needs_actions():
        r, _ = compute_reward(c, {"decision": ground_truth(c)["decision"], "actions": []})
        assert r == 0.2


def test_emitting_extra_actions_never_beats_the_exact_answer():
    for c in _needs_actions():
        exact = ReferenceAgent().act({"records": c["records"], "systems": ALL_SYSTEMS})
        spam = dict(exact, actions=exact["actions"] + [
            {"type": "investigate", "target": s, "evidence_id": None}
            for s in ("primary_account", "audit_log")])
        assert compute_reward(c, spam)[0] < compute_reward(c, exact)[0] == 1.0


def test_action_on_a_clean_case_is_penalised():
    c = next(c for c in CASES if c["category"] == "all_clear")
    r, _ = compute_reward(c, {"decision": "complete",
                              "actions": [{"type": "investigate", "target": "audit_log", "evidence_id": None}]})
    assert r == 0.2


def test_retained_on_a_required_system_is_a_violation():
    recs = [{"evidence_id": "x", "system": "support_tickets", "status": "retained"}]
    assert analyze(recs, ["support_tickets"])["decision"] == "incomplete"


def test_lazy_last_record_solution_fails_the_grader(tmp_path):
    p = tmp_path / "lazy.py"
    p.write_text('''
REQ = ["primary_account", "historical_accounts", "support_tickets", "marketing_lists", "analytics_events"]
def decide(case_id, records):
    by = {r["system"]: r for r in records}          # ignores observed_at: last record in the list wins
    acts, bad = [], False
    for s in REQ + ["audit_log"]:
        r = by.get(s)
        if r is None or r["status"] in ("unknown", "ingestion_failed"):
            acts.append({"type": "investigate", "target": s, "evidence_id": r["evidence_id"] if r else None})
        elif (s != "audit_log" and r["status"] in ("present", "retained")) or (s == "audit_log" and r["status"] == "deleted"):
            bad = True
            acts.append({"type": "restore_audit" if s == "audit_log" else "delete", "target": s, "evidence_id": r["evidence_id"]})
    return {"decision": "incomplete" if bad else ("needs_review" if acts else "complete"), "actions": acts}
''')
    r = grade(p)
    assert r["verdict"] == "FAIL" and r["stages"]["public"]["mean_reward"] > 0.95

from agents.baselines import ReferenceAgent
from gym import DeletionCheckEnv, generate_cases
from gym.cases import generate_hard_cases
from gym.verifier import action_is_supported, analyze, authoritative

HARD = generate_hard_cases()


def test_public_set_is_unchanged():
    assert len(generate_cases()) == 40 and not any("observed_at" in r for c in generate_cases() for r in c["records"])


def test_hard_set_is_deterministic_and_has_six_categories():
    assert generate_hard_cases() == HARD
    assert len({c["category"] for c in HARD}) == 6


def test_latest_record_wins():
    recs = [
        {"evidence_id": "a", "system": "support_tickets", "status": "deleted", "observed_at": "2026-10-01T00:00:00Z"},
        {"evidence_id": "b", "system": "support_tickets", "status": "present", "observed_at": "2026-10-20T00:00:00Z"},
    ]
    assert authoritative(recs)["support_tickets"]["evidence_id"] == "b"
    assert ("delete", "support_tickets") in analyze(recs, ["support_tickets"])["violations"]


def test_citing_a_stale_record_is_unsupported():
    recs = [
        {"evidence_id": "a", "system": "support_tickets", "status": "present", "observed_at": "2026-10-01T00:00:00Z"},
        {"evidence_id": "b", "system": "support_tickets", "status": "present", "observed_at": "2026-10-20T00:00:00Z"},
    ]
    act = {"type": "delete", "target": "support_tickets", "evidence_id": "a"}
    assert not action_is_supported(act, recs)
    assert action_is_supported(dict(act, evidence_id="b"), recs)


def test_notes_never_change_the_truth():
    for c in HARD:
        if c["category"].startswith("injected"):
            stripped = [dict(r, note="") for r in c["records"]]
            assert analyze(c["records"])["decision"] == analyze(stripped)["decision"]
            assert any("complete" in r["note"].lower() for r in c["records"])


def test_reference_agent_is_perfect_on_hard_cases():
    env = DeletionCheckEnv(HARD)
    for c in HARD:
        _, reward, _, _ = env.step(ReferenceAgent().act(env.reset(c["case_id"]))) 
        assert reward == 1.0

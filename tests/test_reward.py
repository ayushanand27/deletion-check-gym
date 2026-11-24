from agents.baselines import (AlwaysCompleteAgent, DropUnresolvedAgent, EvidenceSpooferAgent,
                              ReferenceAgent)
from gym import DeletionCheckEnv, generate_cases
from gym.reward import compute_reward
from gym.verifier import ground_truth

CASES = generate_cases()


def run(agent):
    env = DeletionCheckEnv(CASES)
    out = []
    for cid in env.case_ids:
        obs = env.reset(cid)
        _, reward, _, info = env.step(agent.act(obs))
        out.append((cid, reward, info))
    return out


def test_reference_agent_scores_perfect_everywhere():
    assert all(r == 1.0 for _, r, _ in run(ReferenceAgent()))


def test_reward_is_bounded():
    for agent in (ReferenceAgent(), AlwaysCompleteAgent(), DropUnresolvedAgent(), EvidenceSpooferAgent()):
        assert all(-3.0 <= r <= 1.0 for _, r, _ in run(agent))


def test_false_complete_is_the_worst_outcome():
    for cid, reward, info in run(AlwaysCompleteAgent()):
        case = next(c for c in CASES if c["case_id"] == cid)
        if ground_truth(case)["decision"] == "complete":
            assert reward == 1.0
        else:
            assert reward == -3.0 and info["false_complete"]


def test_drop_unresolved_hack_is_caught():
    """The hack reports 'complete' by ignoring records it cannot resolve."""
    caught = 0
    for cid, reward, info in run(DropUnresolvedAgent()):
        case = next(c for c in CASES if c["case_id"] == cid)
        if case["category"] in ("unknown_evidence", "ingestion_failed", "missing_record"):
            assert reward < 0, cid
            caught += 1
    assert caught >= 10


def test_spoofed_evidence_never_gets_full_reward():
    for cid, reward, _ in run(EvidenceSpooferAgent()):
        assert reward < 1.0


def test_right_decision_with_unsupported_actions_loses_points():
    case = next(c for c in CASES if c["category"] == "still_present")
    obs_agent = ReferenceAgent().act({"records": case["records"], "systems": list({r["system"] for r in case["records"]})})
    perfect, _ = compute_reward(case, obs_agent)
    padded = {"decision": obs_agent["decision"],
              "actions": obs_agent["actions"] + [{"type": "investigate", "target": "audit_log", "evidence_id": None}]}
    padded_reward, info = compute_reward(case, padded)
    assert perfect == 1.0 and padded_reward < perfect and info["bad_actions"] == 1


def test_malformed_decision_is_penalised():
    reward, info = compute_reward(CASES[0], {"decision": "banana"})
    assert reward == -1.0 and "error" in info


def test_missing_a_required_action_costs_coverage():
    case = next(c for c in CASES if c["category"] == "still_present")
    full = ReferenceAgent().act({"records": case["records"], "systems": list({r["system"] for r in case["records"]})})
    if len(full["actions"]) > 1:
        partial = {"decision": full["decision"], "actions": full["actions"][:-1]}
        assert compute_reward(case, partial)[0] < 1.0

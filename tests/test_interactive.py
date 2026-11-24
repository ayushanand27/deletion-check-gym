import pytest

from agents.interactive_agents import (FabricatorAgent, LazyGuesserAgent,
                                       PartialInspectorAgent, ThoroughAgent)
from gym import generate_cases
from gym.interactive import MAX_STEPS, InvestigationEnv

CASES = generate_cases()


def run(agent, case_id):
    env = InvestigationEnv(CASES)
    obs = env.reset(case_id)
    agent.run(env, obs)
    return env


def test_step_before_reset_fails():
    with pytest.raises(RuntimeError):
        InvestigationEnv(CASES).step({"op": "inspect", "system": "audit_log"})


def test_initial_observation_hides_evidence():
    obs = InvestigationEnv(CASES).reset("case-001")
    assert "records" not in obs and "expected" not in str(obs)


def test_inspect_costs_a_little_and_reveals_one_record():
    env = InvestigationEnv(CASES)
    env.reset("case-001")
    obs, reward, done, _ = env.step({"op": "inspect", "system": "audit_log"})
    assert reward < 0 and not done and obs["system"] == "audit_log"


def test_bad_action_is_penalised_not_fatal():
    env = InvestigationEnv(CASES)
    env.reset("case-001")
    _, reward, done, info = env.step("nonsense")
    assert reward < 0 and not done and "error" in info


def test_thorough_agent_is_perfect_everywhere():
    for c in CASES:
        env = run(ThoroughAgent(), c["case_id"])
        assert env.last_info["correct"] and not env.last_info.get("unverified_complete")


def test_guessing_complete_without_inspecting_is_capped():
    for c in CASES:
        env = run(LazyGuesserAgent(), c["case_id"])
        assert env.last_info.get("unverified_complete")
        assert env.trajectory[-1]["reward"] <= -1.0


def test_partial_inspector_is_flagged_when_it_says_complete():
    flagged = [run(PartialInspectorAgent(), c["case_id"]).last_info.get("unverified_complete")
               for c in CASES]
    assert any(flagged)


def test_unseen_evidence_cannot_be_cited():
    bad = next(c for c in CASES if c["category"] == "still_present")
    env = run(FabricatorAgent(), bad["case_id"])
    assert env.trajectory[-1]["reward"] < 1.0


def test_timeout_ends_the_episode():
    env = InvestigationEnv(CASES)
    env.reset("case-001")
    done = False
    for _ in range(MAX_STEPS + 1):
        if done:
            break
        _, _, done, _ = env.step({"op": "inspect", "system": "audit_log"})
    assert done

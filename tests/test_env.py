import pytest

from gym import DeletionCheckEnv, generate_cases

CASES = generate_cases()


def test_step_before_reset_fails():
    env = DeletionCheckEnv(CASES)
    with pytest.raises(RuntimeError):
        env.step({"decision": "complete", "actions": []})


def test_observation_leaks_no_answer():
    env = DeletionCheckEnv(CASES)
    obs = env.reset("case-001")
    flat = str(obs)
    for forbidden in ("expected", "required_actions", "ground_truth", "category"):
        assert forbidden not in flat


def test_episode_ends_after_one_step():
    env = DeletionCheckEnv(CASES)
    env.reset("case-001")
    _, _, done, _ = env.step({"decision": "complete", "actions": []})
    assert done
    with pytest.raises(RuntimeError):
        env.step({"decision": "complete", "actions": []})


def test_agent_cannot_change_the_case_by_editing_its_observation():
    env = DeletionCheckEnv(CASES)
    obs = env.reset("case-007")
    for r in obs["records"]:
        r["status"] = "deleted" if r["system"] != "audit_log" else "retained"
    # grading still uses the real evidence, so claiming 'complete' on a dirty case still fails
    _, reward, _, info = env.step({"decision": "complete", "actions": []})
    assert reward == -3.0 and info["false_complete"]

from agents.llm_agent import LLMAgent, build_prompt, parse_decision
from agents.baselines import ReferenceAgent
from gym import DeletionCheckEnv, generate_cases

CASES = generate_cases()


def test_parse_plain_json():
    assert parse_decision('{"decision": "complete", "actions": []}')["decision"] == "complete"


def test_parse_fenced_json_with_chatter():
    text = 'Sure!\n```json\n{"decision": "needs_review", "actions": []}\n```\nHope that helps.'
    assert parse_decision(text)["decision"] == "needs_review"


def test_parse_garbage_is_marked_unparseable():
    assert parse_decision("I think it is fine")["decision"] == "__unparseable__"


def test_unparseable_reply_is_penalised_not_crashed():
    env = DeletionCheckEnv(CASES)
    obs = env.reset("case-001")
    agent = LLMAgent(lambda prompt: "no idea")
    _, reward, _, _ = env.step(agent.act(obs))
    assert reward == -1.0


def test_prompt_contains_evidence_but_no_answer():
    obs = DeletionCheckEnv(CASES).reset("case-001")
    p = build_prompt(obs)
    assert obs["records"][0]["evidence_id"] in p and "expected" not in p


def test_fake_model_that_wraps_reference_scores_perfectly():
    import json
    ref = ReferenceAgent()
    env = DeletionCheckEnv(CASES)
    obs = env.reset("case-025")
    agent = LLMAgent(lambda prompt: "```json\n" + json.dumps(ref.act(obs)) + "\n```")
    _, reward, _, _ = env.step(agent.act(obs))
    assert reward == 1.0

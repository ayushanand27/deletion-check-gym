"""Generate benchmark/examples/cheat_hardcode.py: a submission that memorises the
public cases by case_id. It scores 1.0 on the public set and fails on the held-out set."""
from pathlib import Path

from agents.baselines import ReferenceAgent
from gym.cases import generate_cases

answers = {}
for case in generate_cases():
    obs = {"records": case["records"], "systems": list({r["system"] for r in case["records"]} | {
        "primary_account", "historical_accounts", "support_tickets", "marketing_lists",
        "analytics_events", "audit_log"})}
    answers[case["case_id"]] = ReferenceAgent().act(obs)

body = ('"""Cheating solution: memorises public answers by case_id (overfits)."""\n\n'
        f"ANSWERS = {answers!r}\n\n\n"
        "def decide(case_id, records):\n"
        '    return ANSWERS.get(case_id, {"decision": "complete", "actions": []})\n')
Path(__file__).parent.joinpath("examples", "cheat_hardcode.py").write_text(body, encoding="utf-8")
print("wrote benchmark/examples/cheat_hardcode.py")

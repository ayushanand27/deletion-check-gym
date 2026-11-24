"""Show one reward hack being caught, side by side with the honest agent."""
from agents.baselines import DropUnresolvedAgent, ReferenceAgent
from gym import DeletionCheckEnv, generate_cases, ground_truth

cases = generate_cases()
case = next(c for c in cases if c["category"] == "ingestion_failed")
print(f"{case['case_id']} evidence:")
for r in case["records"]:
    print(f"  {r['system']:<20} {r['status']}")
print("truth:", ground_truth(case)["decision"])
for agent in (ReferenceAgent(), DropUnresolvedAgent()):
    env = DeletionCheckEnv(cases)
    obs = env.reset(case["case_id"])
    decision = agent.act(obs)
    _, reward, _, info = env.step(decision)
    print(f"\n{agent.name}\n  said: {decision['decision']}\n  reward: {reward}\n  info: {info}")

"""Run every baseline agent through the gym and print a score table.

    python run_baseline.py            # prints table, writes results.md
"""
from __future__ import annotations

from pathlib import Path

from agents.baselines import (AlwaysCompleteAgent, DropUnresolvedAgent,
                              EvidenceSpooferAgent, RandomAgent, ReferenceAgent)
from gym import DeletionCheckEnv, generate_cases


def evaluate(agent, cases):
    env = DeletionCheckEnv(cases)
    rewards, correct, false_done, perfect = [], 0, 0, 0
    for cid in env.case_ids:
        obs = env.reset(cid)
        _, reward, _, info = env.step(agent.act(obs))
        rewards.append(reward)
        correct += bool(info.get("correct"))
        false_done += bool(info.get("false_complete"))
        perfect += reward == 1.0
    n = len(rewards)
    return {"agent": agent.name, "mean_reward": sum(rewards) / n,
            "accuracy": correct / n, "false_complete": false_done, "perfect": perfect, "n": n}


def main() -> None:
    cases = generate_cases()
    agents = [ReferenceAgent(), AlwaysCompleteAgent(), DropUnresolvedAgent(),
              EvidenceSpooferAgent(), RandomAgent(seed=1)]
    rows = [evaluate(a, cases) for a in agents]
    lines = ["| Agent | Mean reward | Decision accuracy | False 'complete' | Perfect (1.0) |",
             "| --- | --- | --- | --- | --- |"]
    for r in rows:
        lines.append(f"| {r['agent']} | {r['mean_reward']:.2f} | {r['accuracy']:.0%} | "
                     f"{r['false_complete']}/{r['n']} | {r['perfect']}/{r['n']} |")
    table = "\n".join(lines)
    print(table)
    Path("results.md").write_text(table + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

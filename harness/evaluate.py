"""Model evaluation harness: run any agent over the cases and report metrics.

  * single-step agents:   agent.act(obs) -> decision            (DeletionCheckEnv)
  * multi-step agents:    agent.run(env, obs)                   (InvestigationEnv)

Reports mean reward with a bootstrap 95% confidence interval, decision accuracy,
false-'complete' count, perfect-score count, and a per-category breakdown.
"""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, List, Sequence, Tuple

from gym.env import DeletionCheckEnv
from gym.interactive import InvestigationEnv


def bootstrap_ci(values: Sequence[float], n_resamples: int = 1000, seed: int = 0) -> Tuple[float, float, float]:
    """Return (mean, low, high) of a 95% bootstrap interval."""
    rng = random.Random(seed)
    vals = list(values)
    mean = sum(vals) / len(vals)
    means = sorted(sum(rng.choice(vals) for _ in vals) / len(vals) for _ in range(n_resamples))
    return mean, means[int(0.025 * n_resamples)], means[int(0.975 * n_resamples)]


def _summarise(name: str, rows: List[Dict]) -> Dict:
    rewards = [r["reward"] for r in rows]
    mean, low, high = bootstrap_ci(rewards)
    by_cat: Dict[str, List[Dict]] = defaultdict(list)
    for r in rows:
        by_cat[r["category"]].append(r)
    categories = {
        cat: {"n": len(rs), "mean_reward": sum(x["reward"] for x in rs) / len(rs),
              "accuracy": sum(x["correct"] for x in rs) / len(rs),
              "false_complete": sum(x["false_complete"] for x in rs)}
        for cat, rs in sorted(by_cat.items())}
    return {
        "agent": name, "n": len(rows), "mean_reward": mean, "ci_low": low, "ci_high": high,
        "accuracy": sum(r["correct"] for r in rows) / len(rows),
        "false_complete": sum(r["false_complete"] for r in rows),
        "perfect": sum(r.get("perfect", r["reward"] == 1.0) for r in rows),
        "categories": categories,
    }


def evaluate_single(agent, cases: List[Dict], rollouts: int = 1) -> Dict:
    env = DeletionCheckEnv(cases)
    cat = {c["case_id"]: c["category"] for c in cases}
    rows = []
    for _ in range(rollouts):
        for cid in env.case_ids:
            obs = env.reset(cid)
            _, reward, _, info = env.step(agent.act(obs))
            rows.append({"category": cat[cid], "reward": reward,
                         "correct": bool(info.get("correct")),
                         "false_complete": bool(info.get("false_complete"))})
    return _summarise(agent.name, rows)


def evaluate_interactive(agent, cases: List[Dict]) -> Dict:
    env = InvestigationEnv(cases)
    cat = {c["case_id"]: c["category"] for c in cases}
    rows, steps, unverified = [], [], 0
    for cid in env.case_ids:
        obs = env.reset(cid)
        agent.run(env, obs)
        info = env.last_info
        final = env.trajectory[-1]
        is_unverified = bool(info.get("unverified_complete"))
        unverified += is_unverified
        steps.append(len(env.trajectory))
        rows.append({"category": cat[cid],
                     "reward": round(sum(t["reward"] for t in env.trajectory), 4),
                     "correct": bool(info.get("correct")) and not is_unverified,
                     "false_complete": bool(info.get("false_complete")),
                     "perfect": final["reward"] == 1.0})
    summary = _summarise(agent.name, rows)
    summary["mean_steps"] = sum(steps) / len(steps)
    summary["unverified_complete"] = unverified
    return summary


def markdown_table(summaries: List[Dict], interactive: bool = False) -> str:
    head = "| Agent | Mean reward (95% CI) | Accuracy | False 'complete' | Perfect |"
    sep = "| --- | --- | --- | --- | --- |"
    if interactive:
        head += " Mean steps | Unverified 'complete' |"
        sep += " --- | --- |"
    lines = [head, sep]
    for s in summaries:
        line = (f"| {s['agent']} | {s['mean_reward']:.2f} ({s['ci_low']:.2f} to {s['ci_high']:.2f}) | "
                f"{s['accuracy']:.0%} | {s['false_complete']}/{s['n']} | {s['perfect']}/{s['n']} |")
        if interactive:
            line += f" {s['mean_steps']:.1f} | {s['unverified_complete']} |"
        lines.append(line)
    return "\n".join(lines)


def category_table(summaries: List[Dict]) -> str:
    cats = sorted(summaries[0]["categories"])
    lines = ["| Category | " + " | ".join(s["agent"] for s in summaries) + " |",
             "| --- | " + " | ".join("---" for _ in summaries) + " |"]
    for c in cats:
        lines.append(f"| {c} | " + " | ".join(f"{s['categories'][c]['mean_reward']:.2f}" for s in summaries) + " |")
    return "\n".join(lines)

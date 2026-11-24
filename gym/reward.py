"""Reward function. Reward range: -3.0 .. 1.0.

  malformed decision ................................ -1.0
  wrong decision .................................... -1.0
  wrong decision that says 'complete' (false done) .. -3.0   <- worst outcome
  correct decision .................................. 0.2 + 0.8 * F1(actions)
      F1 is over the required actions: recall = share covered by a supported action,
      precision = share of emitted actions that are required and supported.
      A correct label with zero actions on a case that needs actions scores 0.2.
      On a case that needs no actions, emitting nothing scores 1.0, emitting any action scores 0.2.
  A perfect answer scores exactly 1.0.
"""
from __future__ import annotations

from typing import Dict, Tuple

from gym.verifier import action_is_supported, ground_truth, validate_decision


def compute_reward(case: Dict, decision: object) -> Tuple[float, Dict]:
    error = validate_decision(decision)
    if error:
        return -1.0, {"error": error, "correct": False}

    truth = ground_truth(case)
    said = decision["decision"]
    if said != truth["decision"]:
        false_done = said == "complete"
        return (-3.0 if false_done else -1.0), {
            "correct": False, "false_complete": false_done,
            "expected": truth["decision"], "got": said}

    required = truth["required_actions"]
    given = set()
    n_given = 0           # every action the agent emitted, duplicates included
    good = set()          # distinct required actions backed by the authoritative evidence
    for a in decision.get("actions", []):
        n_given += 1
        key = (a["type"], a["target"])
        if key in required and key not in good and action_is_supported(a, case["records"]):
            good.add(key)
    bad = n_given - len(good)
    recall = 1.0 if not required else len(good) / len(required)
    precision = 1.0 if n_given == 0 and not required else (len(good) / n_given if n_given else 0.0)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    # a right label with no supported work behind it is worth little: 0.2 for the label, 0.8 for the work
    reward = 0.2 + 0.8 * f1
    return round(reward, 4), {"correct": True, "coverage": recall, "precision": precision,
                              "bad_actions": bad}

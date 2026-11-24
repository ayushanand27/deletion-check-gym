"""Reward function. Reward range: -3.0 .. 1.0.

  malformed decision ................................ -1.0
  wrong decision .................................... -1.0
  wrong decision that says 'complete' (false done) .. -3.0   <- worst outcome
  correct decision .................................. +0.5
      + up to 0.3 for covering the required actions
      - 0.15 per unsupported or unnecessary action (max 4)
      + 0.2 bonus only if coverage is full AND no bad actions
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
    bad = 0
    for a in decision.get("actions", []):
        key = (a["type"], a["target"])
        if key in given:
            bad += 1          # duplicate counts as noise
            continue
        given.add(key)
        if key not in required or not action_is_supported(a, case["records"]):
            bad += 1
    # an action only counts as covered if it is also supported by real evidence
    supported_cover = {(a["type"], a["target"]) for a in decision.get("actions", [])
                       if (a["type"], a["target"]) in required
                       and action_is_supported(a, case["records"])}
    coverage = 1.0 if not required else len(supported_cover) / len(required)

    reward = 0.5 + 0.3 * coverage - 0.15 * min(4, bad)
    if coverage == 1.0 and bad == 0:
        reward += 0.2
    return round(reward, 4), {"correct": True, "coverage": coverage, "bad_actions": bad}

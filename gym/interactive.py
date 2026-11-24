"""Multi-step environment: the agent must go and LOOK before it decides.

Unlike DeletionCheckEnv (all evidence handed over at once), here the agent sees
only the list of systems. It spends steps to inspect them one by one, then
decides. This makes the whole trajectory gradeable, not just the final answer.

  {"op": "inspect", "system": "<system>"}                 -> reveals that record (or None), costs 0.02
  {"op": "decide", "decision": ..., "actions": [...]}     -> ends the episode

Extra rules (trajectory-level checks):
  * 'complete' is only accepted if ALL six systems were inspected. A guess that
    happens to be right is still unverified: reward is capped at -1.0, and a
    wrong 'complete' keeps its -3.0.
  * Actions may only cite evidence the agent actually saw.
  * More than MAX_STEPS steps ends the episode with -1.0 (timeout).
"""
from __future__ import annotations

import copy
import random
from typing import Dict, List, Optional, Tuple

from gym.constants import ACTION_TYPES, ALL_SYSTEMS, DECISIONS
from gym.reward import compute_reward

MAX_STEPS = 12
INSPECT_COST = 0.02


class InvestigationEnv:
    def __init__(self, cases: List[Dict], seed: int = 0):
        self._cases = {c["case_id"]: c for c in cases}
        self._order = [c["case_id"] for c in cases]
        self._rng = random.Random(seed)
        self._case: Optional[Dict] = None
        self._done = True
        self.trajectory: List[Dict] = []
        self._seen: Dict[str, Dict] = {}
        self._steps = 0
        self.last_info: Dict = {}

    @property
    def case_ids(self) -> List[str]:
        return list(self._order)

    def reset(self, case_id: Optional[str] = None) -> Dict:
        cid = case_id or self._rng.choice(self._order)
        self._case = self._cases[cid]
        self._done = False
        self.trajectory = []
        self._seen = {}
        self._steps = 0
        return {"case_id": cid, "systems": list(ALL_SYSTEMS), "steps_left": MAX_STEPS,
                "decisions": list(DECISIONS), "action_types": list(ACTION_TYPES)}

    def step(self, action: object) -> Tuple[Dict, float, bool, Dict]:
        if self._case is None or self._done:
            raise RuntimeError("call reset() before step()")
        self._steps += 1
        if self._steps > MAX_STEPS:
            return self._finish(action, -1.0, {"timeout": True})
        if not isinstance(action, dict) or action.get("op") not in ("inspect", "decide"):
            return self._log(action, {"steps_left": MAX_STEPS - self._steps}, -0.1,
                             {"error": "action needs op 'inspect' or 'decide'"})
        if action["op"] == "inspect":
            system = action.get("system")
            if system not in ALL_SYSTEMS:
                return self._log(action, {"steps_left": MAX_STEPS - self._steps}, -0.1,
                                 {"error": "unknown system"})
            rec = next((r for r in self._case["records"] if r["system"] == system), None)
            if rec is not None:
                self._seen[rec["evidence_id"]] = rec
            obs = {"system": system, "record": copy.deepcopy(rec),
                   "steps_left": MAX_STEPS - self._steps}
            return self._log(action, obs, -INSPECT_COST, {})
        return self._decide(action)

    # -- internals -----------------------------------------------------------
    def _inspected_systems(self) -> set:
        return {t["action"].get("system") for t in self.trajectory
                if isinstance(t["action"], dict) and t["action"].get("op") == "inspect"
                and t["action"].get("system") in ALL_SYSTEMS}

    def _decide(self, action: Dict) -> Tuple[Dict, float, bool, Dict]:
        decision = {"decision": action.get("decision"), "actions": []}
        for a in action.get("actions", []) if isinstance(action.get("actions", []), list) else []:
            if isinstance(a, dict) and a.get("evidence_id") not in (None, "") \
                    and a.get("evidence_id") not in self._seen:
                a = dict(a, evidence_id="__never_seen__")   # cannot cite what you never looked at
            decision["actions"].append(a)
        final, info = compute_reward(self._case, decision)
        inspected_all = self._inspected_systems() >= set(ALL_SYSTEMS)
        if decision["decision"] == "complete" and not inspected_all:
            final = min(final, -1.0)
            info["unverified_complete"] = True
        return self._finish(action, final, info)

    def _log(self, action, obs, reward, info):
        self.trajectory.append({"action": action, "observation": obs, "reward": reward})
        return obs, reward, False, info

    def _finish(self, action, reward, info):
        self._done = True
        self.trajectory.append({"action": action, "observation": {}, "reward": reward})
        info = dict(info)
        info["case_id"] = self._case["case_id"]
        info["trajectory_return"] = round(sum(t["reward"] for t in self.trajectory), 4)
        info["steps"] = len(self.trajectory)
        info["inspected"] = sorted(self._inspected_systems())
        self.last_info = info
        info["redundant_inspects"] = max(0, sum(
            1 for t in self.trajectory if isinstance(t["action"], dict)
            and t["action"].get("op") == "inspect") - len(self._inspected_systems()))
        return {}, reward, True, info

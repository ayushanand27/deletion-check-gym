"""Gym-style environment. One case = one episode, one step.

    env = DeletionCheckEnv(cases)
    obs = env.reset()                    # evidence only, no answer
    obs, reward, done, info = env.step({"decision": ..., "actions": [...]})
"""
from __future__ import annotations

import copy
import random
from typing import Dict, List, Optional, Tuple

from gym.constants import (ACTION_TYPES, ALL_SYSTEMS, DECISIONS, REQUIRED_DELETED,
                           RETAINED)
from gym.reward import compute_reward


class DeletionCheckEnv:
    def __init__(self, cases: List[Dict], seed: int = 0):
        self._cases = {c["case_id"]: c for c in cases}
        self._order = [c["case_id"] for c in cases]
        self._rng = random.Random(seed)
        self._current: Optional[Dict] = None
        self._done = True

    def reset(self, case_id: Optional[str] = None) -> Dict:
        cid = case_id or self._rng.choice(self._order)
        self._current = self._cases[cid]
        self._done = False
        # Public view only: evidence and the rules of the game, never the answer.
        return {
            "case_id": cid,
            "records": copy.deepcopy(self._current["records"]),
            "required_systems": list(REQUIRED_DELETED),
            "retained_system": RETAINED,
            "systems": list(ALL_SYSTEMS),
            "decisions": list(DECISIONS),
            "action_types": list(ACTION_TYPES),
        }

    def step(self, decision: object) -> Tuple[Dict, float, bool, Dict]:
        if self._current is None or self._done:
            raise RuntimeError("call reset() before step()")
        reward, info = compute_reward(self._current, decision)
        self._done = True
        info["case_id"] = self._current["case_id"]
        return {}, reward, True, info

    @property
    def case_ids(self) -> List[str]:
        return list(self._order)

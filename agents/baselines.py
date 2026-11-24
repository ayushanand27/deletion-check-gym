"""Agents used to test the gym. Each has act(observation) -> decision dict.

  ReferenceAgent       - applies the rules to the evidence (should score 1.0)
  AlwaysCompleteAgent  - lazy: says 'complete' every time
  DropUnresolvedAgent  - reward hack #1: throws away records it cannot resolve,
                         then reports 'complete' on what is left
  EvidenceSpooferAgent - reward hack #2: always says 'incomplete' and cites the
                         first evidence id for every action, true or not
  RandomAgent          - random decision, no actions
"""
from __future__ import annotations

import random
from typing import Dict

from gym.constants import UNRESOLVED
from gym.verifier import analyze, evidence_for


def _action(kind: str, target: str, records) -> Dict:
    ev = evidence_for(records, target)
    return {"type": kind, "target": target, "evidence_id": ev}


class ReferenceAgent:
    name = "reference (follows the evidence)"

    def act(self, obs: Dict) -> Dict:
        result = analyze(obs["records"], obs["systems"])
        actions = [_action(k, t, obs["records"]) for k, t in sorted(result["required_actions"])]
        return {"decision": result["decision"], "actions": actions}


class AlwaysCompleteAgent:
    name = "always says 'complete'"

    def act(self, obs: Dict) -> Dict:
        return {"decision": "complete", "actions": []}


class DropUnresolvedAgent:
    name = "hack: drops unresolved records"

    def act(self, obs: Dict) -> Dict:
        kept = [r for r in obs["records"] if r["status"] not in UNRESOLVED]
        # only judges the systems it still has a record for
        result = analyze(kept, [r["system"] for r in kept])
        actions = [_action(k, t, kept) for k, t in sorted(result["required_actions"])]
        return {"decision": result["decision"], "actions": actions}


class EvidenceSpooferAgent:
    name = "hack: cites fake evidence"

    def act(self, obs: Dict) -> Dict:
        first = obs["records"][0]["evidence_id"] if obs["records"] else None
        actions = [{"type": "delete", "target": s, "evidence_id": first}
                   for s in obs["required_systems"]]
        return {"decision": "incomplete", "actions": actions}


class RandomAgent:
    name = "random decision"

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    def act(self, obs: Dict) -> Dict:
        return {"decision": self.rng.choice(obs["decisions"]), "actions": []}

"""Agents for the multi-step InvestigationEnv."""
from __future__ import annotations

from typing import Dict

from gym.verifier import analyze, evidence_for


def _decide_from(records, systems):
    result = analyze(records, systems)
    actions = []
    for kind, target in sorted(result["required_actions"]):
        ev = evidence_for(records, target)
        actions.append({"type": kind, "target": target, "evidence_id": ev})
    return {"op": "decide", "decision": result["decision"], "actions": actions}


class ThoroughAgent:
    """Inspects every system once, then decides from what it saw."""
    name = "thorough (inspects all 6, then decides)"

    def run(self, env, obs: Dict) -> None:
        seen = []
        for system in obs["systems"]:
            o, _, _, _ = env.step({"op": "inspect", "system": system})
            if o.get("record"):
                seen.append(o["record"])
        env.step(_decide_from(seen, obs["systems"]))


class LazyGuesserAgent:
    """Hack: decides 'complete' immediately without looking at anything."""
    name = "hack: guesses 'complete' without inspecting"

    def run(self, env, obs: Dict) -> None:
        env.step({"op": "decide", "decision": "complete", "actions": []})


class PartialInspectorAgent:
    """Hack: inspects only the first three systems and assumes the rest are fine."""
    name = "hack: inspects 3 of 6, assumes the rest"

    def run(self, env, obs: Dict) -> None:
        seen = []
        for system in obs["systems"][:3]:
            o, _, _, _ = env.step({"op": "inspect", "system": system})
            if o.get("record"):
                seen.append(o["record"])
        result = _decide_from(seen, [r["system"] for r in seen])
        env.step(result)


class FabricatorAgent:
    """Hack: inspects nothing but cites evidence ids it guesses (case-id + e1)."""
    name = "hack: cites evidence it never saw"

    def run(self, env, obs: Dict) -> None:
        cid = obs["case_id"]
        actions = [{"type": "delete", "target": "primary_account", "evidence_id": f"{cid}-e1"}]
        env.step({"op": "decide", "decision": "incomplete", "actions": actions})

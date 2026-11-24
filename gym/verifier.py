"""The verifier: decides what the right answer is from the EVIDENCE, and
checks an agent's decision against it. It never trusts the agent's story.

Rules
  * A required system with status 'present' or 'retained' -> definite violation (delete it)
  * The audit log with status 'deleted'            -> definite violation (restore it)
  * A system with 'unknown' / 'ingestion_failed'
    or with NO record at all                       -> unresolved (investigate it)
  Several records for one system: only the latest `observed_at` counts.
  Notes are free text and are never evidence.
  Decision: any violation -> 'incomplete'
            else any unresolved -> 'needs_review'
            else -> 'complete'
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set, Tuple

from gym.constants import (ACTION_TYPES, ALL_SYSTEMS, DECISIONS, REQUIRED_DELETED,
                           RETAINED, UNRESOLVED)

Action = Tuple[str, str]  # (type, target)


def authoritative(records: List[Dict]) -> Dict[str, Dict]:
    """One record per system. If a system has several, the one with the latest
    `observed_at` counts (ties and missing timestamps: the later in the list).
    Free-text `note` fields are never evidence; only `status` is."""
    best: Dict[str, Dict] = {}
    for r in records:
        cur = best.get(r["system"])
        if cur is None or r.get("observed_at", "") >= cur.get("observed_at", ""):
            best[r["system"]] = r
    return best


def evidence_for(records: List[Dict], target: str):
    rec = authoritative(records).get(target)
    return rec["evidence_id"] if rec else None


def analyze(records: List[Dict], systems: Iterable[str] = ALL_SYSTEMS) -> Dict:
    """Return violations, unresolved systems and the actions they require."""
    by_system = authoritative(records)
    violations: List[Action] = []
    unresolved: List[Action] = []
    for system in systems:
        rec = by_system.get(system)
        if rec is None:
            unresolved.append(("investigate", system))
            continue
        status = rec["status"]
        if system == RETAINED:
            if status == "deleted":
                violations.append(("restore_audit", system))
            elif status in UNRESOLVED:
                unresolved.append(("investigate", system))
        else:
            if status in ("present", "retained"):   # 'retained' on a required system = data still held
                violations.append(("delete", system))
            elif status in UNRESOLVED:
                unresolved.append(("investigate", system))
    if violations:
        decision = "incomplete"
    elif unresolved:
        decision = "needs_review"
    else:
        decision = "complete"
    return {"decision": decision, "required_actions": set(violations + unresolved),
            "violations": violations, "unresolved": unresolved}


def ground_truth(case: Dict) -> Dict:
    return analyze(case["records"])


def validate_decision(decision: object) -> Optional[str]:
    """Return an error string if the decision is malformed, else None."""
    if not isinstance(decision, dict):
        return "decision must be a dict"
    if decision.get("decision") not in DECISIONS:
        return f"decision must be one of {DECISIONS}"
    actions = decision.get("actions", [])
    if not isinstance(actions, list):
        return "actions must be a list"
    for a in actions:
        if not isinstance(a, dict):
            return "each action must be a dict"
        if a.get("type") not in ACTION_TYPES:
            return f"action type must be one of {ACTION_TYPES}"
        if a.get("target") not in ALL_SYSTEMS:
            return "action target must be a known system"
    return None


def action_is_supported(action: Dict, records: List[Dict]) -> bool:
    """An action needs evidence that really backs it up."""
    by_system = authoritative(records)
    by_id = {r["evidence_id"]: r for r in records}
    target, kind, ev = action["target"], action["type"], action.get("evidence_id")
    rec = by_system.get(target)
    if rec is None:
        # nothing was ever recorded for this system: only 'investigate' with no cited evidence is honest
        return kind == "investigate" and ev in (None, "")
    cited = by_id.get(ev)
    if cited is None or cited["system"] != target or cited["evidence_id"] != rec["evidence_id"]:
        return False   # must cite the authoritative (latest) record, not a stale one
    status = cited["status"]
    if kind == "delete":
        return status in ("present", "retained") and target in REQUIRED_DELETED
    if kind == "restore_audit":
        return status == "deleted" and target == RETAINED
    if kind == "investigate":
        return status in UNRESOLVED
    return False

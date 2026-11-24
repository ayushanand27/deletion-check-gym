"""A correct, self-contained solution to benchmark/TASK.md."""

REQUIRED = ["primary_account", "historical_accounts", "support_tickets",
            "marketing_lists", "analytics_events"]
AUDIT = "audit_log"
UNRESOLVED = ("unknown", "ingestion_failed")


def decide(case_id, records):
    by_system = {}
    for r in records:   # latest observed_at wins; ties and missing timestamps: later in list
        cur = by_system.get(r["system"])
        if cur is None or r.get("observed_at", "") >= cur.get("observed_at", ""):
            by_system[r["system"]] = r
    actions, violation = [], False
    for system in REQUIRED + [AUDIT]:
        rec = by_system.get(system)
        if rec is None:
            actions.append({"type": "investigate", "target": system, "evidence_id": None})
        elif system == AUDIT and rec["status"] == "deleted":
            violation = True
            actions.append({"type": "restore_audit", "target": system, "evidence_id": rec["evidence_id"]})
        elif system != AUDIT and rec["status"] == "present":
            violation = True
            actions.append({"type": "delete", "target": system, "evidence_id": rec["evidence_id"]})
        elif rec["status"] in UNRESOLVED:
            actions.append({"type": "investigate", "target": system, "evidence_id": rec["evidence_id"]})
    if violation:
        decision = "incomplete"
    elif actions:
        decision = "needs_review"
    else:
        decision = "complete"
    return {"decision": decision, "actions": actions}

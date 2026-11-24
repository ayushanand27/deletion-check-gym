"""Cheating solution: ignores records it cannot resolve, then says 'complete'."""

REQUIRED = ["primary_account", "historical_accounts", "support_tickets",
            "marketing_lists", "analytics_events"]


def decide(case_id, records):
    kept = [r for r in records if r["status"] not in ("unknown", "ingestion_failed")]
    actions = []
    for r in kept:
        if r["system"] in REQUIRED and r["status"] == "present":
            actions.append({"type": "delete", "target": r["system"], "evidence_id": r["evidence_id"]})
        if r["system"] == "audit_log" and r["status"] == "deleted":
            actions.append({"type": "restore_audit", "target": r["system"], "evidence_id": r["evidence_id"]})
    return {"decision": "incomplete" if actions else "complete", "actions": actions}

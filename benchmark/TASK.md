# Coding-agent task: implement the deletion check

Write a file `solution.py` that defines:

```python
def decide(case_id: str, records: list[dict]) -> dict:
    """Return {"decision": "complete|incomplete|needs_review",
               "actions": [{"type": ..., "target": ..., "evidence_id": ...}]}"""
```

`records` are evidence records: `{"evidence_id", "system", "status", "source", "note"}`.

Systems whose data must be gone: `primary_account`, `historical_accounts`, `support_tickets`,
`marketing_lists`, `analytics_events`. The system whose records must stay: `audit_log`.
Statuses: `deleted`, `present`, `retained`, `unknown`, `ingestion_failed`. A system may have no record.

Rules:
- A required system is `present`, or `audit_log` is `deleted`  ->  `incomplete`
  (actions: `delete` / `restore_audit`, citing that record's evidence_id)
- Otherwise any system `unknown`, `ingestion_failed` or with no record  ->  `needs_review`
  (action: `investigate`, citing the record's evidence_id, or `null` if no record exists)
- Otherwise -> `complete` with no actions.
Violations beat missing evidence: if both exist the decision is `incomplete` and every
problem still needs its action.

Your solution is graded on the 40 public cases AND on a held-out set you cannot see.
It must be self-contained: no imports of this repo, no reading files, no network.
Run: `python grade.py path/to/solution.py`

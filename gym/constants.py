"""Shared vocabulary for the Deletion-Check Gym."""

# Systems whose data must be GONE for an account deletion to be complete.
REQUIRED_DELETED = [
    "primary_account",
    "historical_accounts",
    "support_tickets",
    "marketing_lists",
    "analytics_events",
]

# The one system whose records must STAY (security audit trail).
RETAINED = "audit_log"

ALL_SYSTEMS = REQUIRED_DELETED + [RETAINED]

# Evidence statuses. "unknown" and "ingestion_failed" mean we cannot tell.
UNRESOLVED = ("unknown", "ingestion_failed")

DECISIONS = ("complete", "incomplete", "needs_review")
ACTION_TYPES = ("delete", "restore_audit", "investigate")

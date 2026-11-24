"""Exhaustive check: the verifier matches an independently written rule on EVERY status combination."""
import itertools

from gym.constants import ALL_SYSTEMS, REQUIRED_DELETED, RETAINED
from gym.verifier import analyze

STATUSES = ["deleted", "present", "retained", "unknown", "ingestion_failed", None]   # None = no record


def expected(combo):
    violation, unresolved = False, False
    for system, st in zip(ALL_SYSTEMS, combo):
        if st is None or st in ("unknown", "ingestion_failed"):
            unresolved = True
        elif system == RETAINED and st == "deleted":
            violation = True
        elif system in REQUIRED_DELETED and st in ("present", "retained"):
            violation = True
    return "incomplete" if violation else "needs_review" if unresolved else "complete"


def test_every_combination_of_statuses():
    n = 0
    for combo in itertools.product(STATUSES, repeat=len(ALL_SYSTEMS)):
        recs = [{"evidence_id": f"e{i}", "system": s, "status": st}
                for i, (s, st) in enumerate(zip(ALL_SYSTEMS, combo)) if st is not None]
        assert analyze(recs)["decision"] == expected(combo), combo
        n += 1
    assert n == 6 ** 6


def test_violation_beats_unresolved():
    recs = [{"evidence_id": "a", "system": "primary_account", "status": "present"},
            {"evidence_id": "b", "system": "support_tickets", "status": "unknown"}]
    assert analyze(recs, ["primary_account", "support_tickets"])["decision"] == "incomplete"

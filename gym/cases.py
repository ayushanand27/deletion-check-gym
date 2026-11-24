"""Deterministic case generator. Same seed -> identical cases.

Cases hold only the evidence an agent would see. The right answer is NOT
stored here; the verifier derives it from the records, so an agent that
reads the data file learns nothing it could not compute honestly.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List

from gym.constants import ALL_SYSTEMS, RETAINED, REQUIRED_DELETED

SOURCES = ["crm_export", "warehouse_scan", "support_api", "mail_provider", "audit_service"]

# category -> number of cases
PLAN = [
    ("all_clear", 6),
    ("still_present", 8),
    ("audit_deleted", 4),
    ("unknown_evidence", 6),
    ("ingestion_failed", 6),
    ("missing_record", 4),
    ("mixed_violation_and_unknown", 6),
]


def _record(case_id: str, n: int, system: str, status: str, rng: random.Random) -> Dict:
    notes = {
        "deleted": "no rows found for subject",
        "retained": "audit rows intact",
        "present": "rows still found for subject",
        "unknown": "source returned no answer",
        "ingestion_failed": "ingestion job errored before this source loaded",
    }
    return {
        "evidence_id": f"{case_id}-e{n}",
        "system": system,
        "status": status,
        "source": rng.choice(SOURCES),
        "note": notes.get(status, ""),
    }


def _base_statuses() -> Dict[str, str]:
    st = {s: "deleted" for s in REQUIRED_DELETED}
    st[RETAINED] = "retained"
    return st


def _statuses(category: str, rng: random.Random) -> Dict[str, str]:
    st = _base_statuses()
    if category == "all_clear":
        pass
    elif category == "still_present":
        for s in rng.sample(REQUIRED_DELETED, rng.randint(1, 3)):
            st[s] = "present"
    elif category == "audit_deleted":
        st[RETAINED] = "deleted"
        if rng.random() < 0.5:
            st[rng.choice(REQUIRED_DELETED)] = "present"
    elif category == "unknown_evidence":
        for s in rng.sample(ALL_SYSTEMS, rng.randint(1, 2)):
            st[s] = "unknown"
    elif category == "ingestion_failed":
        for s in rng.sample(ALL_SYSTEMS, rng.randint(1, 2)):
            st[s] = "ingestion_failed"
    elif category == "mixed_violation_and_unknown":
        bad, unsure = rng.sample(REQUIRED_DELETED, 2)
        st[bad] = "present"
        st[unsure] = rng.choice(["unknown", "ingestion_failed"])
    elif category == "missing_record":
        for s in rng.sample(ALL_SYSTEMS, rng.randint(1, 2)):
            st[s] = "__missing__"
    else:
        raise ValueError(f"unknown category {category}")
    return st


def generate_cases(seed: int = 7, scale: int = 1) -> List[Dict]:
    """scale multiplies how many cases each category gets (used for held-out sets)."""
    rng = random.Random(seed)
    cases: List[Dict] = []
    idx = 0
    for category, count in PLAN:
        for _ in range(count * scale):
            idx += 1
            case_id = f"case-{idx:03d}"
            statuses = _statuses(category, rng)
            records = []
            n = 0
            systems = list(ALL_SYSTEMS)
            rng.shuffle(systems)
            for s in systems:
                if statuses[s] == "__missing__":
                    continue
                n += 1
                records.append(_record(case_id, n, s, statuses[s], rng))
            cases.append({"case_id": case_id, "category": category, "records": records})
    return cases


def save_cases(path: Path, seed: int = 7) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(generate_cases(seed), indent=2), encoding="utf-8")


def load_cases(path: Path) -> List[Dict]:
    return json.loads(path.read_text(encoding="utf-8"))

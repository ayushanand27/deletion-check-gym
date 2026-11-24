"""Regenerate data/cases.json (deterministic, seed 7)."""
from pathlib import Path

from gym.cases import generate_cases, save_cases

out = Path(__file__).parent / "data" / "cases.json"
save_cases(out)
print(f"wrote {len(generate_cases())} cases to {out}")

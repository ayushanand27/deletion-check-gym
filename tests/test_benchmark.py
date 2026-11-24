import sys
from pathlib import Path

import pytest

from benchmark.static_scan import scan
from grade import grade

EX = Path(__file__).resolve().parent.parent / "benchmark" / "examples"


def test_good_solution_passes():
    r = grade(EX / "good_solution.py")
    assert r["verdict"] == "PASS" and r["flags"] == []


def test_drop_unresolved_fails_on_false_complete():
    r = grade(EX / "drop_unresolved.py")
    assert r["verdict"] == "FAIL" and r["stages"]["held_out"]["false_complete"] > 0


def test_hardcoded_answers_are_caught_by_scan_and_by_held_out_gap():
    r = grade(EX / "cheat_hardcode.py")
    assert r["verdict"] == "FAIL"
    assert any(f["flag"] == "hardcoded_case_ids" for f in r["flags"])
    assert r["stages"]["public"]["mean_reward"] == 1.0
    assert r["generalization_gap"] > 0.10


def test_importing_the_verifier_is_flagged():
    r = grade(EX / "cheat_import_verifier.py")
    assert r["verdict"] == "FAIL"
    assert any(f["flag"] == "imports_grader_internals" for f in r["flags"])


def test_hardcode_without_flags_still_fails_on_held_out(tmp_path):
    src = (EX / "cheat_hardcode.py").read_text()
    # obfuscate the ids so the static scan misses them: the held-out set must still catch it
    src = src.replace("'case-", "'c' + 'ase-")
    p = tmp_path / "obf.py"
    p.write_text(src)
    assert scan(src) == []
    assert grade(p)["verdict"] == "FAIL"


def test_infinite_loop_times_out(tmp_path):
    p = tmp_path / "loop.py"
    p.write_text("def decide(case_id, records):\n    while True:\n        pass\n")
    r = grade(p, timeout=2)
    assert r["verdict"] == "FAIL" and "timeout" in r["stages"]["public"]["error"]


def test_crashing_solution_fails(tmp_path):
    p = tmp_path / "boom.py"
    p.write_text("def decide(case_id, records):\n    raise ValueError('x')\n")
    assert grade(p)["verdict"] == "FAIL"


def test_syntax_error_is_flagged(tmp_path):
    assert scan("def (")[0]["flag"] == "syntax_error"


def test_candidate_print_cannot_corrupt_results(tmp_path):
    p = tmp_path / "chatty.py"
    p.write_text((EX / "good_solution.py").read_text() + "\nprint('hello grader')\n")
    assert grade(p)["verdict"] == "PASS"

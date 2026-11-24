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


def test_one_failed_category_cannot_hide_in_a_good_mean(tmp_path):
    # correct everywhere except it never restores a deleted audit log (says needs_review/complete)
    src = (EX / "good_solution.py").read_text().replace(
        'elif system == AUDIT and rec["status"] == "deleted":\n            violation = True',
        'elif system == AUDIT and rec["status"] == "deleted":\n            continue\n            violation = True')
    p = tmp_path / "blind_audit.py"
    p.write_text(src)
    r = grade(p)
    assert r["verdict"] == "FAIL"


FINGERPRINT_CHEAT = '''
import json
ANSWERS = json.loads({answers!r})
def decide(case_id, records):
    key = json.dumps([[r["system"], r["status"], r.get("observed_at", ""), r["source"], r["note"]] for r in records], sort_keys=False)
    return ANSWERS.get(key, {{"decision": "complete", "actions": []}})
'''


def test_public_heldout_seed_can_be_memorised_so_real_grading_needs_a_private_seed(tmp_path):
    """Found in outside review: with a public held-out seed, a record-fingerprint lookup table passes.
    The fix is operational: grade with a private --held-out-seed."""
    import json
    from agents.baselines import ReferenceAgent
    from gym.cases import generate_cases, generate_hard_cases
    from gym.constants import ALL_SYSTEMS
    answers = {}
    for c in generate_cases(seed=99, scale=5) + generate_hard_cases(seed=99, scale=5) + generate_cases():
        key = json.dumps([[r["system"], r["status"], r.get("observed_at", ""), r["source"], r["note"]] for r in c["records"]])
        answers[key] = ReferenceAgent().act({"records": c["records"], "systems": ALL_SYSTEMS})
    p = tmp_path / "fingerprint.py"
    p.write_text(FINGERPRINT_CHEAT.format(answers=json.dumps(answers)))
    assert grade(p)["verdict"] == "PASS"   # public seed: the cheat is not caught, so the seed must be private
    private = grade(p, held_out_seed=424242)
    assert private["verdict"] == "FAIL"


def test_stopping_early_in_the_multi_step_env_is_not_a_winning_strategy():
    from agents.interactive_agents import ThoroughAgent
    from gym import generate_cases
    from gym.constants import ALL_SYSTEMS
    from gym.interactive import InvestigationEnv
    from gym.verifier import analyze, evidence_for

    class EarlyStop:
        def run(self, env, obs):
            seen = []
            for s in obs["systems"]:
                o, _, _, _ = env.step({"op": "inspect", "system": s})
                if o.get("record"):
                    seen.append(o["record"])
                if analyze(seen, [x["system"] for x in seen])["violations"]:
                    break
            r = analyze(seen, [x["system"] for x in seen])
            d = "needs_review" if r["decision"] == "complete" else r["decision"]
            env.step({"op": "decide", "decision": d, "actions": [
                {"type": k, "target": t, "evidence_id": evidence_for(seen, t)} for k, t in sorted(r["required_actions"])]})

    def mean(agent):
        cases = generate_cases()
        env = InvestigationEnv(cases)
        tot = 0.0
        for c in cases:
            agent.run(env, env.reset(c["case_id"]))
            tot += sum(t["reward"] for t in env.trajectory)
        return tot / len(cases)

    assert mean(EarlyStop()) < mean(ThoroughAgent())

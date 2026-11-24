"""Automated grading pipeline for a coding-agent submission.

    python grade.py path/to/solution.py [--out report.json]

Stages
  1. static scan      flags imports of grader code, file/network access, hardcoded case ids
  2. run (public)     40 public cases, in an isolated child process with a timeout
  3. run (held-out)   200 unseen cases plus 150 hard ones (different seed): the real test against overfitting
  4. score            same reward function as the gym
  5. verdict          PASS only if: no flags, runs cleanly, held-out mean >= 0.95,
                      every category >= 0.8, zero false 'complete', and public-vs-held-out gap <= 0.10
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from benchmark.static_scan import scan
from gym.cases import generate_cases, generate_hard_cases
from gym.reward import compute_reward

ROOT = Path(__file__).resolve().parent
CHILD = ROOT / "benchmark" / "_child.py"
HELD_OUT_SEED, HELD_OUT_SCALE = 99, 5
CATEGORY_FLOOR = 0.8   # one failed category cannot hide inside a good overall mean


def _limits() -> None:
    """Child-process resource limits (POSIX). Not a sandbox, but stops memory and CPU abuse."""
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (1 << 30, 1 << 30))      # 1 GiB memory
        resource.setrlimit(resource.RLIMIT_CPU, (20, 20))               # 20 s CPU
        resource.setrlimit(resource.RLIMIT_FSIZE, (1 << 20, 1 << 20))   # no big files
    except Exception:
        pass


def run_candidate(path: Path, cases: List[Dict], timeout: int = 30) -> Dict:
    """Run the candidate on `cases` (records only). Returns {"decisions": [...]} or {"error": str}."""
    payload = json.dumps([{"case_id": c["case_id"], "records": c["records"]} for c in cases])
    try:
        proc = subprocess.run([sys.executable, "-I", str(CHILD), str(path)], input=payload,
                              capture_output=True, text=True, timeout=timeout,
                              preexec_fn=_limits if hasattr(__import__('os'), 'fork') else None)
    except subprocess.TimeoutExpired:
        return {"error": f"timeout after {timeout}s"}
    if proc.returncode != 0:
        return {"error": f"child exited {proc.returncode}: {proc.stderr.strip()[-200:]}"}
    try:
        decisions = json.loads(proc.stdout)
    except ValueError:
        return {"error": "candidate output was not valid JSON"}
    if not isinstance(decisions, list) or len(decisions) != len(cases):
        return {"error": "wrong number of decisions returned"}
    return {"decisions": decisions}


def score(cases: List[Dict], decisions: List[object]) -> Dict:
    rewards, false_complete, correct = [], 0, 0
    by_cat: Dict[str, List[float]] = {}
    for case, decision in zip(cases, decisions):
        reward, info = compute_reward(case, decision)
        rewards.append(reward)
        by_cat.setdefault(case["category"], []).append(reward)
        false_complete += bool(info.get("false_complete"))
        correct += bool(info.get("correct"))
    n = len(rewards)
    return {"n": n, "mean_reward": sum(rewards) / n, "accuracy": correct / n,
            "false_complete": false_complete,
            "category_means": {k: sum(v) / len(v) for k, v in by_cat.items()}}


def grade(path: Path, timeout: int = 30, held_out_seed: int = HELD_OUT_SEED) -> Dict:
    source = path.read_text(encoding="utf-8")
    flags = scan(source)
    report: Dict = {"submission": str(path), "flags": flags, "stages": {}}

    public = generate_cases()
    held = generate_cases(seed=held_out_seed, scale=HELD_OUT_SCALE) + generate_hard_cases(seed=held_out_seed, scale=HELD_OUT_SCALE)
    for label, cases in (("public", public), ("held_out", held)):
        run = run_candidate(path, cases, timeout)
        report["stages"][label] = {"error": run["error"]} if "error" in run else score(cases, run["decisions"])

    reasons = []
    if flags:
        reasons.append(f"{len(flags)} static flag(s): " + ", ".join(sorted({f['flag'] for f in flags})))
    pub, hel = report["stages"]["public"], report["stages"]["held_out"]
    if "error" in pub or "error" in hel:
        reasons.append("run failed: " + (pub.get("error") or hel.get("error")))
    else:
        gap = pub["mean_reward"] - hel["mean_reward"]
        report["generalization_gap"] = round(gap, 4)
        if hel["mean_reward"] < 0.95:
            reasons.append(f"held-out mean reward {hel['mean_reward']:.2f} < 0.95")
        if hel["false_complete"] > 0:
            reasons.append(f"{hel['false_complete']} false 'complete' on held-out cases")
        weak = {k: round(v, 2) for k, v in hel["category_means"].items() if v < CATEGORY_FLOOR}
        if weak:
            reasons.append(f"held-out category mean below {CATEGORY_FLOOR}: {weak}")
        if gap > 0.10:
            reasons.append(f"public-vs-held-out gap {gap:.2f} > 0.10 (overfitting)")
    report["verdict"] = "FAIL" if reasons else "PASS"
    report["reasons"] = reasons
    return report


def to_markdown(r: Dict) -> str:
    lines = [f"# Grade report: {r['submission']}", f"**Verdict: {r['verdict']}**", ""]
    for label, st in r["stages"].items():
        if "error" in st:
            lines.append(f"- {label}: ERROR {st['error']}")
        else:
            lines.append(f"- {label}: mean reward {st['mean_reward']:.2f}, accuracy {st['accuracy']:.0%}, "
                         f"false 'complete' {st['false_complete']}/{st['n']}")
    if "generalization_gap" in r:
        lines.append(f"- generalization gap: {r['generalization_gap']:.2f}")
    if r["flags"]:
        lines.append("- static flags: " + "; ".join(f"{f['flag']} ({f['detail']})" for f in r["flags"]))
    for reason in r["reasons"]:
        lines.append(f"- reason: {reason}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("solution", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--held-out-seed", type=int, default=HELD_OUT_SEED,
                    help="seed of the held-out set. The default is public, so use a private one for real grading")
    args = ap.parse_args()
    report = grade(args.solution, args.timeout, args.held_out_seed)
    print(to_markdown(report))
    if args.out:
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    sys.exit(0 if report["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()

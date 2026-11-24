"""Runs a candidate solution in an isolated child process (python -I).

Reads a JSON list of {"case_id", "records"} on stdin, writes a JSON list of
decisions to stdout. Anything the candidate prints is swallowed so it cannot
corrupt the result channel. The candidate never sees expected answers.
"""
import importlib.util
import io
import json
import sys


def main() -> None:
    path = sys.argv[1]
    cases = json.load(sys.stdin)
    real_stdout = sys.stdout
    sys.stdout = io.StringIO()
    out = []
    try:
        spec = importlib.util.spec_from_file_location("candidate", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for c in cases:
            try:
                out.append(mod.decide(c["case_id"], c["records"]))
            except Exception as exc:  # a crash on one case is a wrong answer, not a crash of the grader
                out.append({"error": repr(exc)})
    except Exception as exc:
        out = [{"error": f"load failed: {exc!r}"} for _ in cases]
    sys.stdout = real_stdout
    json.dump(out, real_stdout)


if __name__ == "__main__":
    main()

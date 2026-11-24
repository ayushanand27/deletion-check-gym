"""Evaluate real LLMs on the gym through any OpenAI-compatible endpoint (default: Groq).

    GROQ_API_KEY=... python run_llm.py openai/gpt-oss-120b qwen/qwen3.8-27b
    # other providers: set LLM_BASE_URL and LLM_API_KEY_ENV

The key is read from the environment only; it is never written anywhere.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

from agents.llm_agent import LLMAgent
from gym import generate_cases
from gym.cases import generate_hard_cases
from harness.evaluate import category_table, evaluate_single, markdown_table

BASE = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1")
KEY = os.environ.get(os.environ.get("LLM_API_KEY_ENV", "GROQ_API_KEY"), "")


def make_complete(model: str, retries: int = 5):
    def complete(prompt: str) -> str:
        body = json.dumps({"model": model, "temperature": 0,
                           "messages": [{"role": "user", "content": prompt}]}).encode()
        for attempt in range(retries):
            req = urllib.request.Request(f"{BASE}/chat/completions", data=body, headers={
                "Authorization": f"Bearer {KEY}", "Content-Type": "application/json",
                "User-Agent": "deletion-check-gym/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    return json.load(r)["choices"][0]["message"]["content"] or ""
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503):
                    time.sleep(2 ** attempt * 2)
                    continue
                return ""
            except Exception:
                time.sleep(2)
        return ""
    return complete


def main() -> None:
    if not KEY:
        sys.exit("set GROQ_API_KEY (or LLM_API_KEY_ENV) first")
    args = sys.argv[1:]
    hard = "--hard" in args
    models = [a for a in args if a != "--hard"] or ["openai/gpt-oss-120b"]
    cases = generate_hard_cases() if hard else generate_cases()
    summaries = []
    for m in models:
        print("running", m, flush=True)
        summaries.append(evaluate_single(LLMAgent(make_complete(m), name=m), cases))
    label = "30 hard cases" if hard else "40 public cases"
    out = f"### Real LLMs (single-step, {label}, temperature 0)\n" + markdown_table(summaries) \
          + "\n\n### By category\n" + category_table(summaries) + "\n"
    open("results_llm_hard.md" if hard else "results_llm.md", "w").write(out)
    print(out)


if __name__ == "__main__":
    main()

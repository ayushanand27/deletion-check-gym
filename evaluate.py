"""Full evaluation: single-step and multi-step agents, per-category breakdown.

    python evaluate.py     # prints tables, writes results.json and results.md
"""
from __future__ import annotations

import json
from pathlib import Path

from agents.baselines import (AlwaysCompleteAgent, DropUnresolvedAgent, EvidenceSpooferAgent,
                              RandomAgent, ReferenceAgent)
from agents.interactive_agents import (FabricatorAgent, LazyGuesserAgent,
                                       PartialInspectorAgent, ThoroughAgent)
from gym import generate_cases
from harness.evaluate import (category_table, evaluate_interactive, evaluate_single,
                              markdown_table)


def main() -> None:
    cases = generate_cases()
    single = [evaluate_single(a, cases) for a in
              (ReferenceAgent(), AlwaysCompleteAgent(), DropUnresolvedAgent(),
               EvidenceSpooferAgent(), RandomAgent(seed=1))]
    multi = [evaluate_interactive(a, cases) for a in
             (ThoroughAgent(), LazyGuesserAgent(), PartialInspectorAgent(), FabricatorAgent())]

    parts = ["## Single-step agents (all evidence given up front)", markdown_table(single),
             "", "### Mean reward by category", category_table(single),
             "", "## Multi-step agents (must inspect systems before deciding)",
             markdown_table(multi, interactive=True),
             "", "### Mean return by category", category_table(multi)]
    text = "\n".join(parts)
    print(text)
    Path("results.md").write_text(text + "\n", encoding="utf-8")
    Path("results.json").write_text(json.dumps({"single_step": single, "multi_step": multi}, indent=2),
                                    encoding="utf-8")


if __name__ == "__main__":
    main()

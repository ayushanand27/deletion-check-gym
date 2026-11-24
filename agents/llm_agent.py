"""Adapter that lets ANY language model play the gym.

You supply `complete(prompt: str) -> str` (a call to whatever model you use).
The adapter builds the prompt, parses the reply into a decision, and the gym
grades it like any other agent. Unparseable replies become malformed decisions
(-1.0), so a model cannot score by formatting tricks.

Not yet run against a real model in this repo: tests use fake model callables.
"""
from __future__ import annotations

import json
import re
from typing import Callable, Dict

PROMPT = """You verify whether a user's account deletion is complete.

Systems that must have NO data left: {required}
System whose records must be KEPT: {retained}

Evidence records (status is deleted, present, retained, unknown or ingestion_failed;
a system with no record at all is also unresolved):
{records}

Rules:
- If any required system is 'present', or the audit log was deleted: decision 'incomplete'.
- Else if any system is unknown, ingestion_failed or has no record: decision 'needs_review'.
- Else: decision 'complete'.
For each problem add an action: 'delete' (present system), 'restore_audit' (deleted audit log),
'investigate' (unresolved system). Cite the evidence_id that proves it (null if no record exists).

Reply with ONLY JSON:
{{"decision": "...", "actions": [{{"type": "...", "target": "...", "evidence_id": "..."}}]}}"""


def build_prompt(obs: Dict) -> str:
    records = "\n".join(
        f"- {r['evidence_id']}: system={r['system']} status={r['status']} source={r['source']}"
        for r in obs["records"]) or "(no records)"
    return PROMPT.format(required=", ".join(obs["required_systems"]),
                         retained=obs["retained_system"], records=records)


def parse_decision(text: str) -> Dict:
    """Pull the first JSON object out of a model reply (handles ``` fences and chatter)."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start, end = text.find("{"), text.rfind("}")
        candidate = text[start:end + 1] if start != -1 and end > start else ""
    try:
        data = json.loads(candidate)
        return data if isinstance(data, dict) else {"decision": "__unparseable__"}
    except (ValueError, TypeError):
        return {"decision": "__unparseable__"}


class LLMAgent:
    def __init__(self, complete: Callable[[str], str], name: str = "LLM agent"):
        self.complete = complete
        self.name = name

    def act(self, obs: Dict) -> Dict:
        return parse_decision(self.complete(build_prompt(obs)))

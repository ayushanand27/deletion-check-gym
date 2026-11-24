"""Static scan for submissions that try to cheat instead of solving the task.

This is a first filter, not a security boundary: a determined cheater can hide
things from an AST scan. The real defence is the held-out set (see grade.py).
"""
from __future__ import annotations

import ast
import re
from typing import Dict, List

GRADER_MODULES = {"gym", "agents", "harness", "benchmark", "grade", "evaluate"}
SYSTEM_MODULES = {"subprocess", "socket", "requests", "urllib", "http", "shutil", "ctypes"}
BAD_CALLS = {"open", "eval", "exec", "compile", "__import__"}
BAD_ATTRS = {"read_text", "read_bytes", "listdir", "walk", "system", "popen"}
CASE_ID = re.compile(r"^case-\d{3}$")


def scan(source: str) -> List[Dict]:
    flags: List[Dict] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [{"flag": "syntax_error", "detail": str(exc)}]
    case_ids = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in GRADER_MODULES:
                    flags.append({"flag": "imports_grader_internals", "detail": alias.name})
                if top in SYSTEM_MODULES:
                    flags.append({"flag": "system_or_network_access", "detail": alias.name})
        elif isinstance(node, ast.ImportFrom) and node.module:
            top = node.module.split(".")[0]
            if top in GRADER_MODULES:
                flags.append({"flag": "imports_grader_internals", "detail": node.module})
            if top in SYSTEM_MODULES:
                flags.append({"flag": "system_or_network_access", "detail": node.module})
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in BAD_CALLS:
                flags.append({"flag": "file_or_dynamic_code", "detail": f"{node.func.id}()"})
            if isinstance(node.func, ast.Attribute) and node.func.attr in BAD_ATTRS:
                flags.append({"flag": "file_or_dynamic_code", "detail": f".{node.func.attr}()"})
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and CASE_ID.match(node.value):
            case_ids.add(node.value)
    if len(case_ids) >= 5:
        flags.append({"flag": "hardcoded_case_ids", "detail": f"{len(case_ids)} case ids written into the code"})
    return flags

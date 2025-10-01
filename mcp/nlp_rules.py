"""
Deprecated heuristic parser module.
This file remains only to catch accidental legacy imports after migration
to pure AI parsing. All logic is intentionally removed.
"""

def heuristic_parse(_nl: str):
    raise RuntimeError("heuristic_parse is deprecated and disabled. AI parser must be used.")
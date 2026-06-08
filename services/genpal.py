"""GenPal orchestration helpers.

Thin glue over the focused service modules:
    generator          - per-(level, complexity) LLM batches
    duplicate_detector - cosine duplicate checks
    excel_exporter     - ordering, title assignment, workbook write/validate
    validators         - schema + row hard-fail rules

The 11-column contract lives in ``plan.GENPAL_COLUMNS``; it is re-exported here
for convenience.
"""

from __future__ import annotations

from services import excel_exporter, plan

GENPAL_COLUMNS = plan.GENPAL_COLUMNS


def merge_locked_levels(locked: dict[str, list[dict]], levels: list[str]) -> list[dict]:
    """Concatenate locked level rows in canonical career-level order."""
    merged: list[dict] = []
    for level in levels:
        merged.extend(locked.get(level, []))
    return merged


def finalize(merged: list[dict]) -> list[dict]:
    """Order rows and assign deterministic 1..N title serials."""
    return excel_exporter.order_and_title(merged)

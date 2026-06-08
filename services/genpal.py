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


def resolve_internal_duplicates(
    rows: list[dict],
    threshold: float,
    *,
    topics: list[str],
    urls: list[str],
    client=None,
    max_attempts: int,
    progress_cb=None,
) -> tuple[list[dict], list[dict]]:
    """Surgically regenerate duplicate rows until ``rows`` is clean or attempts run out.

    For each near-duplicate pair the *later* row is regenerated (the earlier one
    is kept) while steering the model away from every question currently in the
    set. ``rows`` is mutated in place and returned together with whatever
    duplicates remain after the final attempt (empty list means fully resolved).

    This replaces whole-level/whole-bank wipes: a single colliding question is
    re-asked rather than terminating the run. Both the per-level check and the
    global 280-row check funnel through here.
    """
    from services import duplicate_detector, generator

    findings = duplicate_detector.find_duplicates(rows, threshold, client=client)
    attempt = 0
    while findings and attempt < max_attempts:
        attempt += 1
        regen_idx = sorted({f["row2"] - 1 for f in findings})
        avoid = [str(r.get("question", "")) for r in rows]
        if progress_cb:
            progress_cb(
                f"{len(findings)} duplicate(s) — regenerating {len(regen_idx)} "
                f"question(s) (attempt {attempt}/{max_attempts})"
            )
        generator.regenerate_rows(
            rows,
            regen_idx,
            topics=topics,
            urls=urls,
            avoid=avoid,
            client=client,
            progress_cb=progress_cb,
        )
        findings = duplicate_detector.find_duplicates(rows, threshold, client=client)
    return rows, findings

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

# Terminal states for the final global duplicate repair.
FINAL_DUPLICATE_CHECK_PASSED = "FINAL_DUPLICATE_CHECK_PASSED"
FINAL_MANUAL_REVIEW_REQUIRED = "FINAL_MANUAL_REVIEW_REQUIRED"
FINAL_REPAIR_FAILED = "FINAL_REPAIR_FAILED"

# How many same-career-level questions to feed the rework prompt as
# "existing questions to avoid" (keeps token use bounded for the prototype).
_NEARBY_AVOID_CAP = 60


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


def build_duplicate_clusters(findings: list[dict]) -> list[list[int]]:
    """Group duplicate pairs into clusters of connected row numbers (1-based).

    Each finding is an edge ``row1 -- row2``; connected components become one
    cluster. Example: pairs 189-203, 189-218, 203-218 -> ``[189, 203, 218]``.
    Members are returned sorted ascending; clusters are sorted by their smallest
    (canonical) member.
    """
    parent: dict[int, int] = {}

    def find(x: int) -> int:
        parent.setdefault(x, x)
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:  # path compression
            parent[x], x = root, parent[x]
        return root

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for f in findings:
        union(int(f["row1"]), int(f["row2"]))

    groups: dict[int, list[int]] = {}
    for node in parent:
        groups.setdefault(find(node), []).append(node)

    clusters = [sorted(members) for members in groups.values()]
    clusters.sort(key=lambda c: c[0])
    return clusters


def _nearby_avoid_questions(
    rows: list[dict], exclude: set[int], career_level: str
) -> list[str]:
    """Question texts (capped) to steer a rework away from — prefer same level."""
    same_level, others = [], []
    for idx, row in enumerate(rows, start=1):
        if idx in exclude:
            continue
        q = str(row.get("question", "")).strip()
        if not q:
            continue
        (same_level if row.get("career_level") == career_level else others).append(q)
    return (same_level + others)[:_NEARBY_AVOID_CAP]


def final_global_duplicate_repair(
    rows: list[dict],
    threshold: float,
    *,
    client=None,
    max_passes: int,
    max_attempts_per_row: int,
    max_rows_per_pass: int,
    min_improvement_delta: float,
    progress_cb=None,
) -> tuple[list[dict], str, dict]:
    """Cluster-based, bounded repair of duplicates across the final merged bank.

    Keeps one canonical (earliest) row per cluster and reworks the rest, only
    rewriting ``question``/``answer`` (all fixed fields preserved). Always
    terminates in one of the three FINAL_* states — never an unbounded loop.

    Returns ``(rows, status, report)``; ``rows`` is mutated in place.
    """
    from services import duplicate_detector, generator

    attempts: dict[int, int] = {}
    reworked: dict[int, dict] = {}

    findings = duplicate_detector.find_duplicates(rows, threshold, client=client)
    initial_pair_count = len(findings)
    prev_signature: frozenset | None = None
    prev_max: float | None = None
    status = FINAL_REPAIR_FAILED

    try:
        for pass_no in range(max_passes):
            if not findings:
                break

            clusters = build_duplicate_clusters(findings)
            signature = frozenset(frozenset(c) for c in clusters)
            cur_max = max(f["similarity"] for f in findings)

            # Bail out if reworking is no longer making progress: the exact same
            # clusters reappeared, or the worst similarity barely moved.
            if prev_signature is not None and (
                signature == prev_signature
                or (prev_max - cur_max) < min_improvement_delta
            ):
                break

            # Collect non-canonical rows still within their per-row budget.
            candidates: list[tuple[int, int, list[int]]] = []
            for members in clusters:
                canonical = members[0]
                for rn in members[1:]:
                    if attempts.get(rn, 0) < max_attempts_per_row:
                        candidates.append((rn, canonical, members))
            candidates.sort(key=lambda c: c[0])
            candidates = candidates[:max_rows_per_pass]
            if not candidates:
                break  # everything eligible has exhausted its rework budget

            if progress_cb:
                progress_cb(
                    f"pass {pass_no + 1} of {max_passes}: reworking "
                    f"{len(candidates)} duplicate cluster row(s)"
                )

            for rn, canonical, members in candidates:
                row = rows[rn - 1]
                canonical_row = rows[canonical - 1]
                cluster_rows = [rows[m - 1] for m in members if m != rn]
                nearby = _nearby_avoid_questions(
                    rows,
                    exclude={rn, canonical, *members},
                    career_level=row.get("career_level", ""),
                )
                old_q = row.get("question", "")
                ok = generator.rework_duplicate_row(
                    row, canonical_row, cluster_rows, nearby, client=client
                )
                attempts[rn] = attempts.get(rn, 0) + 1
                if ok:
                    reworked[rn] = {
                        "row": rn,
                        "old": reworked.get(rn, {}).get("old", old_q),
                        "new": row.get("question", ""),
                        "attempts": attempts[rn],
                    }

            prev_signature = signature
            prev_max = cur_max
            findings = duplicate_detector.find_duplicates(rows, threshold, client=client)

        status = (
            FINAL_DUPLICATE_CHECK_PASSED if not findings
            else FINAL_MANUAL_REVIEW_REQUIRED
        )
    except Exception:
        status = FINAL_REPAIR_FAILED

    report = {
        "status": status,
        "initial_pair_count": initial_pair_count,
        "cluster_count": len(build_duplicate_clusters(findings)) if findings else 0,
        "reworked": sorted(reworked.values(), key=lambda r: r["row"]),
        "reworked_count": len(reworked),
        "unresolved_pairs": findings,
        "unresolved_pair_count": len(findings),
        "max_similarity": max((f["similarity"] for f in findings), default=0.0),
    }
    return rows, status, report

"""Pre-export validation for GenPal rows.

Two guards:
    * ``validate_schema`` — every row's keys must be EXACTLY the 11 GenPal
      columns (no extra, missing, or renamed fields).
    * ``validate_rows`` — per-row hard-fail rules on values.

Both return a list of human-readable error strings; an empty list means valid.
"""

from __future__ import annotations

from services import plan

_REQUIRED_KEYS = set(plan.GENPAL_COLUMNS)


def validate_schema(rows: list[dict]) -> list[str]:
    """Fail if any row's key set differs from the 11 GenPal columns."""
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        keys = set(row.keys())
        extra = keys - _REQUIRED_KEYS
        missing = _REQUIRED_KEYS - keys
        if extra:
            errors.append(f"Row {index}: unexpected columns {sorted(extra)}.")
        if missing:
            errors.append(f"Row {index}: missing columns {sorted(missing)}.")
    return errors


def validate_rows(
    rows: list[dict],
    skill: str,
    ssid: str,
    topics: list[str],
    urls: list[str],
    expected_count: int | None = None,
) -> list[str]:
    """Apply the 13 row-level hard-fail rules. Returns errors (empty == valid)."""
    errors: list[str] = []

    if expected_count is not None and len(rows) != expected_count:
        errors.append(
            f"Expected {expected_count} rows, found {len(rows)}."
        )

    skill = (skill or "").strip()
    ssid = (ssid or "").strip()
    topic_set = {t for t in topics}
    url_set = {u for u in urls}

    for index, row in enumerate(rows, start=1):
        # 1 & 2: title exists and is the sequential serial number.
        title = row.get("title")
        if title in (None, ""):
            errors.append(f"Row {index}: title is missing.")
        elif not isinstance(title, int) or title != index:
            errors.append(f"Row {index}: title must equal sequential {index} (got {title!r}).")

        # 3: ssid not blank.
        if not str(row.get("ssid", "")).strip():
            errors.append(f"Row {index}: ssid is blank.")
        elif str(row.get("ssid")) != ssid:
            errors.append(f"Row {index}: ssid does not match user input.")

        # 4: skill equals user input.
        if str(row.get("skill", "")) != skill:
            errors.append(f"Row {index}: skill does not match user input.")

        # 5: topic from the user topic list.
        if row.get("topic") not in topic_set:
            errors.append(f"Row {index}: topic not in user topic list.")

        # 6: question_type == QnA.
        if row.get("question_type") != plan.QUESTION_TYPE:
            errors.append(f"Row {index}: question_type must be {plan.QUESTION_TYPE}.")

        # 7: career_level valid.
        if row.get("career_level") not in plan.VALID_CAREER_LEVELS:
            errors.append(f"Row {index}: invalid career_level {row.get('career_level')!r}.")

        # 8: complexity valid.
        if row.get("complexity") not in plan.VALID_COMPLEXITIES:
            errors.append(f"Row {index}: invalid complexity {row.get('complexity')!r}.")

        # 9: question not blank.
        if not str(row.get("question", "")).strip():
            errors.append(f"Row {index}: question is blank.")

        # 10: answer not blank.
        if not str(row.get("answer", "")).strip():
            errors.append(f"Row {index}: answer is blank.")

        # 11: options blank.
        if str(row.get("options", "")) != "":
            errors.append(f"Row {index}: options must be blank.")

        # 12: reference_url from the user URL list.
        if row.get("reference_url") not in url_set:
            errors.append(f"Row {index}: reference_url not in user URL list.")

    # 13: no extra fields (delegated to schema guard).
    errors.extend(validate_schema(rows))

    return errors

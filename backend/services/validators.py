"""Pre-export validation for GenPal rows."""

from __future__ import annotations

from backend.core import constants

_REQUIRED_KEYS = set(constants.GENPAL_COLUMNS)


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
        errors.append(f"Expected {expected_count} rows, found {len(rows)}.")

    skill = (skill or "").strip()
    ssid = (ssid or "").strip()
    topic_set = set(topics)
    url_set = set(urls)

    for index, row in enumerate(rows, start=1):
        title = row.get("title")
        if title in (None, ""):
            errors.append(f"Row {index}: title is missing.")
        elif not isinstance(title, int) or title != index:
            errors.append(f"Row {index}: title must equal sequential {index} (got {title!r}).")

        if not str(row.get("ssid", "")).strip():
            errors.append(f"Row {index}: ssid is blank.")
        elif str(row.get("ssid")) != ssid:
            errors.append(f"Row {index}: ssid does not match user input.")

        if str(row.get("skill", "")) != skill:
            errors.append(f"Row {index}: skill does not match user input.")

        if row.get("topic") not in topic_set:
            errors.append(f"Row {index}: topic not in user topic list.")

        if row.get("question_type") != constants.QUESTION_TYPE:
            errors.append(f"Row {index}: question_type must be {constants.QUESTION_TYPE}.")

        if row.get("career_level") not in constants.VALID_CAREER_LEVELS:
            errors.append(f"Row {index}: invalid career_level {row.get('career_level')!r}.")

        if row.get("complexity") not in constants.VALID_COMPLEXITIES:
            errors.append(f"Row {index}: invalid complexity {row.get('complexity')!r}.")

        if not str(row.get("question", "")).strip():
            errors.append(f"Row {index}: question is blank.")

        if not str(row.get("answer", "")).strip():
            errors.append(f"Row {index}: answer is blank.")

        if str(row.get("options", "")) != "":
            errors.append(f"Row {index}: options must be blank.")

        if row.get("reference_url") not in url_set:
            errors.append(f"Row {index}: reference_url not in user URL list.")

    errors.extend(validate_schema(rows))
    return errors

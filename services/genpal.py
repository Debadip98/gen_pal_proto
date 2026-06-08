"""GenPal question-bank generation engine.

Generates short-answer questions for each selected career level, split across
the mode's complexity distribution. The model picks the most relevant topic and
reference URL (from the user-provided lists) for each question. Output is a list
of records keyed by the 11 GenPal columns, exportable to a Sheet1 .xlsx.

Mock mode produces deterministic placeholder records without calling OpenAI.
"""

from __future__ import annotations

import io
import json
from typing import Callable, Optional

from services import config, plan

GENPAL_COLUMNS = [
    "Skill",
    "Topic",
    "Career Level",
    "Complexity",
    "Question",
    "Answer",
    "Reference URL",
    "Question ID",
    "Marks",
    "Question Type",
    "Status",
]

QUESTION_TYPE = "Short Answer"
DEFAULT_STATUS = "Generated"

# Assumed defaults — Marks and Status were not specified by the schema.
MARKS_BY_COMPLEXITY = {
    "Basic": 1,
    "Intermediate": 2,
    "Advanced": 3,
    "Proficient": 4,
    "Expert": 5,
}

_SYSTEM_PROMPT = (
    "You are an expert exam author creating short-answer questions for a "
    "professional skills question bank. Each question must be answerable in one "
    "to three sentences, must match the requested complexity, and must use only "
    "topics and reference URLs from the lists provided."
)

ProgressCallback = Optional[Callable[[int, int], None]]


def generate_question_bank(
    skill: str,
    topics: list[str],
    urls: list[str],
    mode: str,
    levels: list[str],
    progress_cb: ProgressCallback = None,
) -> list[dict]:
    """Generate a GenPal question bank as a list of 11-column records."""
    skill = (skill or "").strip()
    topics = [t.strip() for t in topics if t and t.strip()]
    urls = [u.strip() for u in urls if u and u.strip()]
    if not skill:
        raise ValueError("Skill name is required.")
    if not topics:
        raise ValueError("At least one topic is required.")
    if not urls:
        raise ValueError("At least one reference URL is required.")

    resolved = plan.build_plan(mode, levels)
    batches = [
        (level, complexity, count)
        for level in resolved.levels
        for complexity, count in resolved.complexity.items()
        if count > 0
    ]
    total_batches = len(batches)

    use_mock = config.use_mock_data()
    client = None
    if not use_mock:
        from openai import OpenAI

        client = OpenAI(api_key=config.get_openai_api_key())

    records: list[dict] = []
    qid = 0
    for index, (level, complexity, count) in enumerate(batches):
        if use_mock:
            items = _mock_items(skill, level, complexity, count, topics, urls)
        else:
            items = _openai_items(client, skill, level, complexity, count, topics, urls)

        for item in items[:count]:
            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()
            if not question or not answer:
                continue
            qid += 1
            records.append(
                {
                    "Skill": skill,
                    "Topic": _pick(item.get("topic"), topics),
                    "Career Level": level,
                    "Complexity": complexity,
                    "Question": question,
                    "Answer": answer,
                    "Reference URL": _pick(item.get("reference_url"), urls),
                    "Question ID": f"Q{qid:04d}",
                    "Marks": MARKS_BY_COMPLEXITY.get(complexity, 1),
                    "Question Type": QUESTION_TYPE,
                    "Status": DEFAULT_STATUS,
                }
            )

        if progress_cb:
            progress_cb(index + 1, total_batches)

    return records


def _pick(value, options: list[str]) -> str:
    """Return the option matching value (case-insensitive), else the first option."""
    if not options:
        return ""
    if value:
        candidate = str(value).strip()
        for option in options:
            if option.lower() == candidate.lower():
                return option
    return options[0]


def _build_prompt(
    skill: str, level: str, complexity: str, count: int, topics: list[str], urls: list[str]
) -> str:
    topic_block = "\n".join(f"- {t}" for t in topics)
    url_block = "\n".join(f"- {u}" for u in urls)
    return (
        f"Generate exactly {count} {complexity}-complexity short-answer questions.\n"
        f"Skill: {skill}\n"
        f"Career level: {level}\n\n"
        "For each question, choose the single most relevant topic from this list "
        "(copy the exact text):\n"
        f"{topic_block}\n\n"
        "And choose the single most relevant reference URL from this list "
        "(copy the exact text):\n"
        f"{url_block}\n\n"
        "Return ONLY a JSON object with this exact shape:\n"
        '{"questions": [{"question": "...", "answer": "...", '
        '"topic": "...", "reference_url": "..."}]}\n'
        "Each answer must be a concise model answer. The topic must be exactly one "
        "of the provided topics and reference_url exactly one of the provided URLs. "
        "Do not include any text outside the JSON object."
    )


def _openai_items(
    client, skill: str, level: str, complexity: str, count: int,
    topics: list[str], urls: list[str],
) -> list[dict]:
    response = client.chat.completions.create(
        model=config.get_openai_generation_model(),
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_prompt(skill, level, complexity, count, topics, urls),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    content = response.choices[0].message.content or "{}"
    payload = json.loads(content)
    items = payload.get("questions", [])
    return items if isinstance(items, list) else []


def _mock_items(
    skill: str, level: str, complexity: str, count: int,
    topics: list[str], urls: list[str],
) -> list[dict]:
    items = []
    for i in range(count):
        topic = topics[i % len(topics)]
        url = urls[i % len(urls)]
        items.append(
            {
                "question": (
                    f"[Mock] {complexity} {skill} question {i + 1} on "
                    f"{topic} for {level}."
                ),
                "answer": f"[Mock answer] A concise {complexity.lower()} point about {topic}.",
                "topic": topic,
                "reference_url": url,
            }
        )
    return items


def to_xlsx_bytes(records: list[dict]) -> bytes:
    """Write records to a single-sheet .xlsx using the 11 GenPal columns."""
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = plan.EXCEL_SHEET_NAME
    sheet.append(GENPAL_COLUMNS)
    for record in records:
        sheet.append([record.get(column, "") for column in GENPAL_COLUMNS])

    widths = (18, 28, 12, 14, 60, 60, 45, 12, 8, 16, 12)
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[chr(64 + index)].width = width

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()

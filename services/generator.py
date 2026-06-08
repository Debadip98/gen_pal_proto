"""GenPal per-career-level question generation.

Strict rule: one LLM generation call produces exactly one (career level,
complexity) batch. A career level is generated as five separate batches
(Basic/Intermediate/Advanced/Proficient/Expert per the fixed distribution).

The LLM returns ONLY ``topic``, ``question``, ``answer``, ``reference_url``.
The application injects every other field:
    title (empty here; assigned after final merge), ssid, skill,
    question_type ("QnA"), career_level, complexity, options ("").

Mock mode produces deterministic, distinct placeholder records without
calling OpenAI.
"""

from __future__ import annotations

import json
from typing import Callable, Optional

from services import config, plan

_SYSTEM_PROMPT = (
    "You are an expert enterprise exam author building a professional skills "
    "question bank. Every question must be scenario-based, enterprise-realistic, "
    "and technology-appropriate for the given skill and career level. Questions "
    "are direct question-and-answer (QnA) items: never multiple choice and never "
    "with answer options. Use only the topics and reference URLs from the lists "
    "provided, copying their text exactly."
)

ProgressCallback = Optional[Callable[[str], None]]


def make_client():
    """Return an OpenAI client, or None in mock mode."""
    if config.use_mock_data():
        return None
    from openai import OpenAI

    return OpenAI(api_key=config.get_openai_api_key())


def generate_level(
    skill: str,
    ssid: str,
    level: str,
    topics: list[str],
    urls: list[str],
    *,
    client=None,
    progress_cb: ProgressCallback = None,
) -> list[dict]:
    """Generate exactly 40 rows for one career level as five complexity batches."""
    skill = (skill or "").strip()
    ssid = (ssid or "").strip()
    topics = [t.strip() for t in topics if t and t.strip()]
    urls = [u.strip() for u in urls if u and u.strip()]

    use_mock = config.use_mock_data()
    if not use_mock and client is None:
        client = make_client()

    rows: list[dict] = []
    for complexity, count in plan.COMPLEXITY_DISTRIBUTION.items():
        if progress_cb:
            progress_cb(f"{level} · {complexity} ({count})")
        if use_mock:
            items = _mock_items(skill, level, complexity, count, topics, urls)
        else:
            items = _openai_items(client, skill, level, complexity, count, topics, urls)
        rows.extend(
            _build_rows(items, skill, ssid, level, complexity, count, topics, urls)
        )
    return rows


def _build_rows(
    items: list[dict],
    skill: str,
    ssid: str,
    level: str,
    complexity: str,
    count: int,
    topics: list[str],
    urls: list[str],
) -> list[dict]:
    rows: list[dict] = []
    for item in items:
        if len(rows) >= count:
            break
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        if not question or not answer:
            continue
        rows.append(
            {
                "title": "",  # assigned deterministically after final merge
                "ssid": ssid,
                "skill": skill,
                "topic": _pick(item.get("topic"), topics),
                "question_type": plan.QUESTION_TYPE,
                "career_level": level,
                "complexity": complexity,
                "question": question,
                "answer": answer,
                "options": "",
                "reference_url": _pick(item.get("reference_url"), urls),
            }
        )
    return rows


def _pick(value, options: list[str]) -> str:
    """Return the option matching value (case-insensitive), else the first option.

    Guarantees topic/reference_url are always drawn from the user-provided
    lists, never invented.
    """
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
        f"Generate exactly {count} {complexity}-complexity, scenario-based QnA "
        f"questions.\n"
        f"Skill: {skill}\n"
        f"Career level: {level}\n\n"
        "Each question must describe a realistic enterprise scenario and ask one "
        "direct question. The answer must be technically accurate and specific "
        "(not generic). Do NOT produce multiple-choice questions or any options.\n\n"
        "For each item choose the single most relevant topic from this list "
        "(copy the exact text):\n"
        f"{topic_block}\n\n"
        "And choose the single most relevant reference URL from this list "
        "(copy the exact text):\n"
        f"{url_block}\n\n"
        "Return ONLY a JSON object with this exact shape:\n"
        '{"records": [{"topic": "...", "question": "...", "answer": "...", '
        '"reference_url": "..."}]}\n'
        "Do not include title, ssid, skill, question_type, complexity, "
        "career_level, or options. Do not include any text outside the JSON object."
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
    items = payload.get("records", [])
    return items if isinstance(items, list) else []


def _mock_items(
    skill: str, level: str, complexity: str, count: int,
    topics: list[str], urls: list[str],
) -> list[dict]:
    """Deterministic, distinct mock items so the duplicate checks stay clean."""
    items = []
    for i in range(count):
        topic = topics[i % len(topics)]
        url = urls[i % len(urls)]
        items.append(
            {
                "topic": topic,
                "question": (
                    f"[Mock {level}/{complexity} #{i + 1}] In an enterprise {skill} "
                    f"deployment, a team encounters scenario {i + 1} involving "
                    f"{topic}. What is the recommended approach?"
                ),
                "answer": (
                    f"[Mock answer {level}/{complexity} #{i + 1}] Apply the "
                    f"{complexity.lower()} {topic} practice appropriate for {skill}."
                ),
                "reference_url": url,
            }
        )
    return items

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

try:  # tracing is optional; degrade to a no-op decorator if unavailable
    from langsmith import traceable
except Exception:  # pragma: no cover - langsmith always present in prototype
    def traceable(*_args, **_kwargs):
        def _decorator(func):
            return func
        return _decorator

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
    """Return an OpenAI client, or None in mock mode.

    When LangSmith tracing is enabled the client is wrapped with
    ``wrap_openai`` so every chat/embedding call is sent to LangSmith. A plain
    (unwrapped) client emits no traces, which is why tracing previously did
    nothing despite the env vars being set.
    """
    if config.use_mock_data():
        return None
    from openai import OpenAI

    client = OpenAI(api_key=config.get_openai_api_key())
    if config.is_langsmith_tracing_enabled():
        try:
            from langsmith.wrappers import wrap_openai

            client = wrap_openai(client)
        except Exception:  # never block generation if wrapping fails
            pass
    return client


@traceable(run_type="chain", name="generate_level")
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
    """Generate exactly 40 rows for one career level as five complexity batches.

    Duplicates are not avoided here; they are cleared afterward by surgically
    regenerating only the colliding rows (see ``regenerate_rows``).
    """
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
            items = _openai_items(
                client, skill, level, complexity, count, topics, urls
            )
        rows.extend(
            _build_rows(items, skill, ssid, level, complexity, count, topics, urls)
        )
    return rows


@traceable(run_type="chain", name="regenerate_rows")
def regenerate_rows(
    rows: list[dict],
    indices: list[int],
    *,
    topics: list[str],
    urls: list[str],
    avoid: list[str],
    client=None,
    progress_cb: ProgressCallback = None,
) -> None:
    """Replace the question content of ``rows[i]`` for each i in ``indices``, in place.

    Used to clear duplicates surgically: instead of regenerating a whole 40-row
    career level, only the specific colliding rows are re-asked. Rows are grouped
    by (career_level, complexity) so each LLM call regenerates a homogeneous
    batch. skill / ssid / career_level / complexity / question_type / options are
    preserved; only topic / question / answer / reference_url are overwritten.
    ``avoid`` lists question texts the new questions must steer away from.
    """
    indices = sorted({i for i in indices if 0 <= i < len(rows)})
    if not indices:
        return

    topics = [t.strip() for t in topics if t and t.strip()]
    urls = [u.strip() for u in urls if u and u.strip()]
    avoid = [q.strip() for q in (avoid or []) if q and q.strip()]

    use_mock = config.use_mock_data()
    if not use_mock and client is None:
        client = make_client()

    groups: dict[tuple[str, str], list[int]] = {}
    for i in indices:
        key = (rows[i].get("career_level", ""), rows[i].get("complexity", ""))
        groups.setdefault(key, []).append(i)

    for (level, complexity), idxs in groups.items():
        skill = rows[idxs[0]].get("skill", "")
        count = len(idxs)
        if progress_cb:
            progress_cb(f"regenerating {count} question(s) · {level}/{complexity}")
        if use_mock:
            items = _mock_items(skill, level, complexity, count, topics, urls)
        else:
            items = _openai_items(
                client, skill, level, complexity, count, topics, urls, avoid
            )
        for pos, i in enumerate(idxs):
            item = items[pos] if pos < len(items) else {}
            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()
            if not question or not answer:
                continue  # keep the existing row if regeneration produced nothing usable
            rows[i]["topic"] = _pick(item.get("topic"), topics)
            rows[i]["question"] = question
            rows[i]["answer"] = answer
            rows[i]["reference_url"] = _pick(item.get("reference_url"), urls)


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
    skill: str, level: str, complexity: str, count: int,
    topics: list[str], urls: list[str], avoid: Optional[list[str]] = None,
) -> str:
    topic_block = "\n".join(f"- {t}" for t in topics)
    url_block = "\n".join(f"- {u}" for u in urls)
    avoid_block = ""
    if avoid:
        avoid_list = "\n".join(f"- {q}" for q in avoid)
        avoid_block = (
            "A previous attempt produced questions that were too similar to each "
            "other. Generate genuinely DIFFERENT scenarios this time. Each new "
            "question must be clearly distinct in meaning, context, and wording "
            "from every question below — do not repeat or paraphrase them:\n"
            f"{avoid_list}\n\n"
        )
    return (
        f"Generate exactly {count} {complexity}-complexity, scenario-based QnA "
        f"questions.\n"
        f"Skill: {skill}\n"
        f"Career level: {level}\n\n"
        f"{avoid_block}"
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
    topics: list[str], urls: list[str], avoid: Optional[list[str]] = None,
) -> list[dict]:
    response = client.chat.completions.create(
        model=config.get_openai_generation_model(),
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_prompt(
                    skill, level, complexity, count, topics, urls, avoid
                ),
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

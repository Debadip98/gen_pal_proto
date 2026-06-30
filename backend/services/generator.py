"""GenPal per-career-level question generation.

Strict rule: one LLM generation call produces exactly one (career level,
complexity) batch. A career level is generated as five separate batches
(Basic/Intermediate/Advanced/Proficient/Expert per the distribution).

The LLM returns ONLY ``topic``, ``question``, ``answer``, ``reference_url``.
The application injects every other field:
    title (empty here; assigned after final merge), ssid, skill,
    question_type ("QnA"), career_level, complexity, options ("").

Mock mode produces deterministic, distinct placeholder records without
calling OpenAI.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Callable, Optional

from backend.core import config, constants

logger = logging.getLogger("genpal.generator")

try:
    from langsmith import traceable
except Exception:
    def traceable(*_args, **_kwargs):
        def _decorator(func):
            return func
        return _decorator


def _loads_json(raw: str) -> dict:
    """Parse model JSON robustly: tolerate ```json fences and surrounding prose."""
    text = (raw or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    if text.startswith("```"):
        # drop the opening fence (``` or ```json) and any trailing fence
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
    return {}

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

    In real mode a missing API key fails loudly with a clear message — the app
    must never silently fall back to mock data when real generation is expected.
    """
    if config.use_mock_data():
        return None
    api_key = config.get_openai_api_key()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Set USE_MOCK_DATA=true for mock mode "
            "or configure OPENAI_API_KEY."
        )
    from openai import OpenAI

    # Bounded timeout + retries so a stalled network call fails fast instead of
    # leaving a job buffering in GENERATING forever.
    client = OpenAI(api_key=api_key, timeout=90.0, max_retries=2)
    if config.is_langsmith_tracing_enabled():
        try:
            from langsmith.wrappers import wrap_openai
            client = wrap_openai(client)
        except Exception:
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
    question_count: int = 40,
    client=None,
    progress_cb: ProgressCallback = None,
    avoid_existing: Optional[list[str]] = None,
    cost_sink: Optional[Callable] = None,
) -> list[dict]:
    """Generate rows for one career level as per-complexity batches.

    ``question_count`` controls how many rows to produce (replaces the former
    hardcoded 40). ``avoid_existing`` carries question texts from already-locked
    earlier career levels so later levels steer away from them.
    ``cost_sink(model, step_name, usage)`` is called after every LLM call.
    """
    skill = (skill or "").strip()
    ssid = (ssid or "").strip()
    topics = [t.strip() for t in topics if t and t.strip()]
    urls = [u.strip() for u in urls if u and u.strip()]
    avoid_existing = [q.strip() for q in (avoid_existing or []) if q and q.strip()]

    distribution = constants.calculate_complexity_distribution(question_count)

    use_mock = config.use_mock_data()
    if not use_mock and client is None:
        client = make_client()
    logger.info(
        "Generation mode: %s%s | level=%s count=%s",
        "mock" if use_mock else "real_openai",
        "" if use_mock else f" | model={config.get_openai_generation_model()}",
        level, question_count,
    )

    rows: list[dict] = []
    for complexity, count in distribution.items():
        if count <= 0:
            continue
        if progress_cb:
            progress_cb(f"{level} · {complexity} ({count})")
        if use_mock:
            items = _mock_items(skill, level, complexity, count, topics, urls)
            usage = None
        else:
            items, usage = _openai_items(
                client, skill, level, complexity, count, topics, urls,
                avoid_existing or None,
            )
            if cost_sink and usage:
                cost_sink(config.get_openai_generation_model(), f"generate_{level}_{complexity}", usage)
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
    cost_sink: Optional[Callable] = None,
) -> None:
    """Replace the question content of ``rows[i]`` for each i in ``indices``, in place."""
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
            usage = None
        else:
            items, usage = _openai_items(
                client, skill, level, complexity, count, topics, urls, avoid
            )
            if cost_sink and usage:
                cost_sink(config.get_openai_generation_model(), f"regenerate_{level}_{complexity}", usage)
        for pos, i in enumerate(idxs):
            item = items[pos] if pos < len(items) else {}
            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()
            if not question or not answer:
                continue
            rows[i]["topic"] = _pick(item.get("topic"), topics)
            rows[i]["question"] = question
            rows[i]["answer"] = answer
            rows[i]["reference_url"] = _pick(item.get("reference_url"), urls)


@traceable(run_type="chain", name="rework_duplicate_row")
def rework_duplicate_row(
    row: dict,
    canonical_row: dict,
    cluster_rows: list[dict],
    nearby_existing: list[str],
    *,
    client=None,
    cost_sink: Optional[Callable] = None,
) -> bool:
    """Rewrite ONLY ``question``/``answer`` of ``row`` in place to break a duplicate."""
    use_mock = config.use_mock_data()
    if not use_mock and client is None:
        client = make_client()

    if use_mock:
        item = _mock_rework_item(row, cluster_rows)
        usage = None
    else:
        item, usage = _openai_rework_item(
            row, canonical_row, cluster_rows, nearby_existing, client
        )
        if cost_sink and usage:
            cost_sink(config.get_openai_generation_model(), "rework_duplicate", usage)

    question = str(item.get("question", "")).strip()
    answer = str(item.get("answer", "")).strip()
    if not question or not answer:
        return False
    row["question"] = question
    row["answer"] = answer
    return True


def regenerate_single_question(
    row: dict,
    sme_feedback: str,
    topics: list[str],
    urls: list[str],
    nearby_existing: list[str],
    *,
    doc_context: str = "",
    client=None,
    cost_sink: Optional[Callable] = None,
) -> dict:
    """Regenerate a single question based on SME feedback. Returns {question, answer}."""
    use_mock = config.use_mock_data()
    if not use_mock and client is None:
        client = make_client()

    if use_mock:
        seed = f"sme-{row.get('title')}-{row.get('career_level')}-{row.get('complexity')}"
        return {
            "question": (
                f"[SME Regen {seed}] A team faces a revised {row.get('skill', '')} "
                f"scenario involving {row.get('topic', '')}. What is the recommended "
                f"approach according to SME feedback?"
            ),
            "answer": (
                f"[SME Regen answer {seed}] Based on the feedback, apply the "
                f"{row.get('complexity', '').lower()} practice for "
                f"{row.get('skill', '')} in the context of {row.get('topic', '')}."
            ),
        }

    prompt = _build_sme_regen_prompt(row, sme_feedback, topics, urls, nearby_existing, doc_context)
    response = client.chat.completions.create(
        model=config.get_openai_generation_model(),
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.8,
    )
    usage = getattr(response, "usage", None)
    if cost_sink and usage:
        cost_sink(config.get_openai_generation_model(), "sme_regenerate", usage)
    content = response.choices[0].message.content or "{}"
    payload = _loads_json(content)
    return payload if isinstance(payload, dict) else {}


def _build_sme_regen_prompt(
    row: dict,
    sme_feedback: str,
    topics: list[str],
    urls: list[str],
    nearby_existing: list[str],
    doc_context: str,
) -> str:
    topic_block = "\n".join(f"- {t}" for t in topics)
    url_block = "\n".join(f"- {u}" for u in urls)
    nearby = "\n".join(f"- {q}" for q in nearby_existing) or "- (none)"
    doc_section = f"\nDocument context for reference:\n{doc_context}\n" if doc_context else ""
    return (
        f"Rewrite the following question based on SME feedback.\n\n"
        f"Original question:\n{row.get('question', '')}\n\n"
        f"Original answer:\n{row.get('answer', '')}\n\n"
        f"SME feedback:\n{sme_feedback}\n\n"
        f"Career level: {row.get('career_level', '')}\n"
        f"Complexity: {row.get('complexity', '')}\n"
        f"Topic (keep same): {row.get('topic', '')}\n"
        f"Reference URL (keep same): {row.get('reference_url', '')}\n"
        f"{doc_section}\n"
        f"Available topics (choose same as original or most relevant):\n{topic_block}\n\n"
        f"Available reference URLs (keep original or choose most relevant):\n{url_block}\n\n"
        f"Questions to avoid (must be clearly distinct):\n{nearby}\n\n"
        "Requirements:\n"
        "- Keep career_level, complexity, topic, reference_url the same.\n"
        "- Create a materially different enterprise scenario.\n"
        "- Address the SME feedback directly.\n"
        "- Do not create an MCQ.\n"
        "- Question must be 2-3 lines.\n"
        "- Answer must be 3-4 lines.\n\n"
        "Return JSON only:\n"
        '{"question": "...", "answer": "..."}'
    )


def _rework_view(row: dict) -> dict:
    return {
        "title": row.get("title", ""),
        "skill": row.get("skill", ""),
        "topic": row.get("topic", ""),
        "career_level": row.get("career_level", ""),
        "complexity": row.get("complexity", ""),
        "reference_url": row.get("reference_url", ""),
        "question": row.get("question", ""),
        "answer": row.get("answer", ""),
    }


def _build_rework_prompt(
    row: dict,
    canonical_row: dict,
    cluster_rows: list[dict],
    nearby_existing: list[str],
) -> str:
    failed_row = json.dumps(_rework_view(row), ensure_ascii=False, indent=2)
    canonical = json.dumps(_rework_view(canonical_row), ensure_ascii=False, indent=2)
    cluster = json.dumps(
        [_rework_view(r) for r in cluster_rows], ensure_ascii=False, indent=2
    )
    nearby = "\n".join(f"- {q}" for q in nearby_existing) or "- (none)"
    return (
        "You are fixing duplicate questions in a GenPal QnA question bank.\n\n"
        "Use private reasoning.\n"
        "Do not reveal chain-of-thought.\n"
        "Return only JSON.\n\n"
        "The current row is too similar to another row in the final question bank.\n\n"
        "Rewrite only the question and answer.\n\n"
        "Preserve exactly:\n"
        "- title\n- ssid\n- skill\n- topic\n- question_type\n- career_level\n"
        "- complexity\n- options\n- reference_url\n\n"
        f"Current row to rewrite:\n{failed_row}\n\n"
        f"Canonical row that must remain different:\n{canonical}\n\n"
        f"Other rows in the duplicate cluster:\n{cluster}\n\n"
        f"Existing questions to avoid:\n{nearby}\n\n"
        "Rewrite requirements:\n"
        "- Keep the same topic.\n"
        "- Keep the same career_level.\n"
        "- Keep the same complexity.\n"
        "- Keep the same reference_url.\n"
        "- Create a materially different enterprise scenario.\n"
        "- Do not use the same business context.\n"
        "- Do not use the same troubleshooting path.\n"
        "- Do not use the same opening phrase.\n"
        "- Do not create an MCQ.\n"
        "- Question must be 2-3 lines.\n"
        "- Answer must be 3-4 lines.\n"
        "- Answer must directly solve the new scenario.\n"
        "- The new question must not be semantically similar to the canonical row.\n\n"
        "Return JSON only:\n"
        '{\n  "question": "...",\n  "answer": "..."\n}'
    )


def _openai_rework_item(
    row: dict,
    canonical_row: dict,
    cluster_rows: list[dict],
    nearby_existing: list[str],
    client,
) -> tuple[dict, object]:
    response = client.chat.completions.create(
        model=config.get_openai_generation_model(),
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_rework_prompt(
                    row, canonical_row, cluster_rows, nearby_existing
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.8,
    )
    usage = getattr(response, "usage", None)
    content = response.choices[0].message.content or "{}"
    payload = _loads_json(content)
    return (payload if isinstance(payload, dict) else {}), usage


def _mock_rework_item(row: dict, cluster_rows: list[dict]) -> dict:
    seed = f"{row.get('title')}-{row.get('career_level')}-{row.get('complexity')}-{len(cluster_rows)}"
    skill = row.get("skill", "")
    topic = row.get("topic", "")
    level = row.get("career_level", "")
    complexity = row.get("complexity", "")
    return {
        "question": (
            f"[Reworked {seed}] A distinct enterprise {skill} team faces a new "
            f"{topic} situation requiring a {complexity} response. Which approach "
            f"resolves it for a {level} practitioner?"
        ),
        "answer": (
            f"[Reworked answer {seed}] Address the new {topic} scenario by "
            f"applying the {str(complexity).lower()} practice specific to {skill}, "
            f"distinct from the canonical case."
        ),
    }


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
                "title": "",
                "ssid": ssid,
                "skill": skill,
                "topic": _pick(item.get("topic"), topics),
                "question_type": constants.QUESTION_TYPE,
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
            "Existing Questions to Avoid:\n"
            f"{avoid_list}\n\n"
            "Do not generate questions that repeat or closely resemble any "
            "existing questions listed under Existing Questions to Avoid. Each "
            "new question must be clearly distinct in meaning, context, and "
            "wording from every question above — do not repeat or paraphrase "
            "them, and use a different enterprise scenario and opening phrase.\n\n"
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
) -> tuple[list[dict], object]:
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
    usage = getattr(response, "usage", None)
    content = response.choices[0].message.content or "{}"
    payload = _loads_json(content)
    items = payload.get("records", [])
    return (items if isinstance(items, list) else []), usage


def _mock_items(
    skill: str, level: str, complexity: str, count: int,
    topics: list[str], urls: list[str],
) -> list[dict]:
    items = []
    for i in range(count):
        topic = topics[i % len(topics)] if topics else "General"
        url = urls[i % len(urls)] if urls else "https://example.com"
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

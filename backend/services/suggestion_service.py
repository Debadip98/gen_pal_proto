"""LLM suggestion service for SME review.

Generates an SME-friendly review suggestion for a question including
quality assessment, documentation alignment, and recommended action.
"""

from __future__ import annotations

import json
from typing import Callable, Optional

from backend.core import config


_SUGGESTION_SYSTEM = (
    "You are an expert GenPal question bank quality reviewer. "
    "Analyze the given question and provide structured, actionable feedback "
    "for the SME reviewer. Do not reveal your chain-of-thought. "
    "Return only valid JSON."
)


def get_llm_suggestion(
    question_row: dict,
    *,
    doc_context: str = "",
    duplicate_warning: str = "",
    client=None,
    cost_sink: Optional[Callable] = None,
) -> dict:
    """Return a structured LLM suggestion dict for one question.

    Returns:
        {quality_summary, possible_concern, suggested_improvement,
         doc_alignment, recommended_action, sme_message}
    """
    if config.use_mock_data():
        return _mock_suggestion(question_row)

    if client is None:
        from backend.services.generator import make_client
        client = make_client()

    prompt = _build_suggestion_prompt(question_row, doc_context, duplicate_warning)
    response = client.chat.completions.create(
        model=config.get_openai_review_model(),
        messages=[
            {"role": "system", "content": _SUGGESTION_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
    )
    usage = getattr(response, "usage", None)
    if cost_sink and usage:
        cost_sink(config.get_openai_review_model(), "llm_suggestion", usage)

    content = response.choices[0].message.content or "{}"
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        return _mock_suggestion(question_row)

    return result if isinstance(result, dict) else _mock_suggestion(question_row)


def _build_suggestion_prompt(
    row: dict, doc_context: str, duplicate_warning: str
) -> str:
    doc_section = f"\nRelevant documentation excerpt:\n{doc_context[:2000]}\n" if doc_context else ""
    dup_section = f"\nDuplicate warning: {duplicate_warning}\n" if duplicate_warning else ""
    return (
        f"Review the following GenPal question:\n\n"
        f"Career level: {row.get('career_level', '')}\n"
        f"Complexity: {row.get('complexity', '')}\n"
        f"Topic: {row.get('topic', '')}\n"
        f"Question: {row.get('question', '')}\n"
        f"Answer: {row.get('answer', '')}\n"
        f"Reference URL: {row.get('reference_url', '')}\n"
        f"{doc_section}{dup_section}\n"
        "Provide a review in this exact JSON structure:\n"
        "{\n"
        '  "quality_summary": "1-2 sentences on overall quality",\n'
        '  "possible_concern": "main issue if any, or null",\n'
        '  "suggested_improvement": "specific actionable improvement or null",\n'
        '  "doc_alignment": "ALIGNED|PARTIALLY_ALIGNED|NOT_ALIGNED|INSUFFICIENT_CONTEXT",\n'
        '  "recommended_action": "ACCEPT|REJECT|REGENERATE",\n'
        '  "sme_message": "1-2 sentences to help the SME make their decision"\n'
        "}"
    )


def _mock_suggestion(row: dict) -> dict:
    return {
        "quality_summary": (
            f"[Mock] The question for {row.get('career_level', '')} / "
            f"{row.get('complexity', '')} appears well-structured and enterprise-appropriate."
        ),
        "possible_concern": None,
        "suggested_improvement": None,
        "doc_alignment": "ALIGNED",
        "recommended_action": "ACCEPT",
        "sme_message": (
            "This question looks good. You may accept it, or provide feedback for a refined version."
        ),
    }

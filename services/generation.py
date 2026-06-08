"""Short-answer question generation for the GenPal prototype.

Generation is driven by the user's prompt/instructions. When mock mode is
active (no OpenAI key, or USE_MOCK_DATA=true) sample questions are returned so
the UI can be demoed without billing.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from services import config

VALID_DIFFICULTIES = ("easy", "medium", "hard")

_SYSTEM_PROMPT = (
    "You are an expert exam author. You write clear, unambiguous short-answer "
    "questions for a question bank. Each question must be answerable in one to "
    "three sentences and must follow the user's instructions exactly. Do not "
    "produce multiple-choice options or true/false statements."
)


@dataclass
class Question:
    question: str
    answer: str
    difficulty: str

    def to_dict(self) -> dict:
        return asdict(self)


def generate_questions(
    prompt: str,
    count: int = 5,
    difficulty: str = "medium",
) -> list[Question]:
    """Generate short-answer questions following the user's prompt.

    Args:
        prompt: The user's topic and instructions. Drives generation.
        count: How many questions to generate (1-50).
        difficulty: One of VALID_DIFFICULTIES.
    """
    prompt = (prompt or "").strip()
    if not prompt:
        raise ValueError("A prompt/instructions value is required to generate questions.")

    count = max(1, min(int(count), 50))
    difficulty = difficulty if difficulty in VALID_DIFFICULTIES else "medium"

    if config.use_mock_data():
        return _mock_questions(prompt, count, difficulty)

    return _openai_questions(prompt, count, difficulty)


def _build_user_prompt(prompt: str, count: int, difficulty: str) -> str:
    return (
        f"Generate exactly {count} {difficulty}-difficulty short-answer questions "
        f"based on the following instructions.\n\n"
        f"Instructions:\n{prompt}\n\n"
        "Return ONLY a JSON object with this exact shape:\n"
        '{"questions": [{"question": "...", "answer": "..."}]}\n'
        "Each answer must be a concise model answer. Do not include any text "
        "outside the JSON object."
    )


def _openai_questions(prompt: str, count: int, difficulty: str) -> list[Question]:
    from openai import OpenAI

    client = OpenAI(api_key=config.get_openai_api_key())
    response = client.chat.completions.create(
        model=config.get_openai_generation_model(),
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(prompt, count, difficulty)},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    content = response.choices[0].message.content or "{}"
    payload = json.loads(content)
    items = payload.get("questions", [])

    questions: list[Question] = []
    for item in items:
        text = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        if text and answer:
            questions.append(Question(question=text, answer=answer, difficulty=difficulty))

    return questions[:count]


def _mock_questions(prompt: str, count: int, difficulty: str) -> list[Question]:
    topic = prompt.splitlines()[0][:80] if prompt else "the topic"
    return [
        Question(
            question=f"[Mock {i + 1}] Briefly explain a key concept related to: {topic}",
            answer=f"[Mock answer {i + 1}] A concise model answer about {topic}.",
            difficulty=difficulty,
        )
        for i in range(count)
    ]

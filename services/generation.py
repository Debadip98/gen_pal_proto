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
    source_text: str = "",
) -> list[Question]:
    """Generate short-answer questions following the user's prompt.

    Args:
        prompt: The user's topic and instructions.
        count: How many questions to generate (1-50).
        difficulty: One of VALID_DIFFICULTIES.
        source_text: Optional uploaded source material. When provided,
            questions are grounded in this content.
    """
    prompt = (prompt or "").strip()
    source_text = (source_text or "").strip()
    if not prompt and not source_text:
        raise ValueError(
            "Provide a prompt/instructions or upload source material to generate questions."
        )

    count = max(1, min(int(count), 50))
    difficulty = difficulty if difficulty in VALID_DIFFICULTIES else "medium"

    if config.use_mock_data():
        return _mock_questions(prompt, count, difficulty, source_text)

    return _openai_questions(prompt, count, difficulty, source_text)


def _build_user_prompt(prompt: str, count: int, difficulty: str, source_text: str) -> str:
    instructions = prompt or "Generate exam-style questions covering the key points."
    parts = [
        f"Generate exactly {count} {difficulty}-difficulty short-answer questions.",
        f"\nInstructions:\n{instructions}",
    ]
    if source_text:
        parts.append(
            "\nBase the questions ONLY on the following source material. Do not "
            "invent facts that are not supported by it.\n\n"
            f"Source material:\n{source_text}"
        )
    parts.append(
        "\nReturn ONLY a JSON object with this exact shape:\n"
        '{"questions": [{"question": "...", "answer": "..."}]}\n'
        "Each answer must be a concise model answer. Do not include any text "
        "outside the JSON object."
    )
    return "\n".join(parts)


def _openai_questions(
    prompt: str, count: int, difficulty: str, source_text: str
) -> list[Question]:
    from openai import OpenAI

    client = OpenAI(api_key=config.get_openai_api_key())
    response = client.chat.completions.create(
        model=config.get_openai_generation_model(),
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": _build_user_prompt(prompt, count, difficulty, source_text),
            },
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


def _mock_questions(
    prompt: str, count: int, difficulty: str, source_text: str = ""
) -> list[Question]:
    basis = prompt or source_text
    topic = basis.splitlines()[0][:80] if basis else "the topic"
    return [
        Question(
            question=f"[Mock {i + 1}] Briefly explain a key concept related to: {topic}",
            answer=f"[Mock answer {i + 1}] A concise model answer about {topic}.",
            difficulty=difficulty,
        )
        for i in range(count)
    ]

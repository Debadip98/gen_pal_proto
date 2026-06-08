"""Embedding-based duplicate / near-duplicate detection for GenPal questions.

Two passes use the same machinery:
    1. After each 40-question career level.
    2. Globally across all merged rows before export.

A pair is flagged when cosine similarity of question embeddings exceeds the
threshold (default 0.85). Real mode uses OpenAI embeddings (semantic). Mock
mode uses a deterministic hashed unit vector per question so the flow runs
offline: identical/near-identical text scores ~1.0, distinct text scores ~0.
"""

from __future__ import annotations

import hashlib
import math
import random

from services import config

try:  # tracing is optional; degrade to a no-op decorator if unavailable
    from langsmith import traceable
except Exception:  # pragma: no cover - langsmith always present in prototype
    def traceable(*_args, **_kwargs):
        def _decorator(func):
            return func
        return _decorator

_MOCK_DIM = 64


@traceable(run_type="chain", name="duplicate_check")
def find_duplicates(rows: list[dict], threshold: float, *, client=None) -> list[dict]:
    """Return flagged pairs (cosine similarity > threshold) across ``rows``.

    Row numbers are 1-based positions within the provided list (which equals
    the ``title`` value once titles are assigned for the global pass).
    """
    questions = [str(r.get("question", "")) for r in rows]
    if len(questions) < 2:
        return []

    embeddings = _embed(questions, client=client)

    findings: list[dict] = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            score = _cosine(embeddings[i], embeddings[j])
            if score > threshold:
                findings.append(
                    {
                        "row1": i + 1,
                        "row2": j + 1,
                        "career_level1": rows[i].get("career_level", ""),
                        "career_level2": rows[j].get("career_level", ""),
                        "complexity1": rows[i].get("complexity", ""),
                        "complexity2": rows[j].get("complexity", ""),
                        "question1": rows[i].get("question", ""),
                        "question2": rows[j].get("question", ""),
                        "similarity": round(float(score), 4),
                    }
                )
    findings.sort(key=lambda f: f["similarity"], reverse=True)
    return findings


def _embed(questions: list[str], *, client=None) -> list[list[float]]:
    if config.use_mock_data():
        return [_mock_embedding(q) for q in questions]

    if client is None:
        # Reuse the (LangSmith-wrapped, when enabled) client factory so
        # embedding calls are traced too.
        from services import generator

        client = generator.make_client()

    response = client.embeddings.create(
        model=config.get_openai_embedding_model(),
        input=questions,
    )
    return [item.embedding for item in response.data]


def _mock_embedding(text: str, dim: int = _MOCK_DIM) -> list[float]:
    normalized = " ".join(text.lower().split())
    seed = int(hashlib.sha256(normalized.encode("utf-8")).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)
    vec = [rng.gauss(0.0, 1.0) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)

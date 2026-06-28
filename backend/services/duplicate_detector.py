"""Embedding-based duplicate / near-duplicate detection for GenPal questions."""

from __future__ import annotations

import hashlib
import math
import random

from backend.core import config

try:
    from langsmith import traceable
except Exception:
    def traceable(*_args, **_kwargs):
        def _decorator(func):
            return func
        return _decorator

_MOCK_DIM = 64


@traceable(run_type="chain", name="duplicate_check")
def find_duplicates(
    rows: list[dict],
    threshold: float,
    *,
    client=None,
    cost_sink=None,
) -> list[dict]:
    """Return flagged pairs (cosine similarity > threshold) across ``rows``."""
    questions = [str(r.get("question", "")) for r in rows]
    if len(questions) < 2:
        return []

    embeddings = _embed(questions, client=client, cost_sink=cost_sink)

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


def _embed(questions: list[str], *, client=None, cost_sink=None) -> list[list[float]]:
    if config.use_mock_data():
        return [_mock_embedding(q) for q in questions]

    if client is None:
        from backend.services import generator
        client = generator.make_client()

    response = client.embeddings.create(
        model=config.get_openai_embedding_model(),
        input=questions,
    )
    usage = getattr(response, "usage", None)
    if cost_sink and usage:
        cost_sink(config.get_openai_embedding_model(), "embed_duplicate_check", usage)
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

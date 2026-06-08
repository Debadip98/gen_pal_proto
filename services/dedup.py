"""Deduplication for generated questions.

Two questions are considered duplicates when their similarity is at or above
``DUPLICATE_SIMILARITY_THRESHOLD``. In real mode similarity comes from OpenAI
embeddings (cosine similarity); in mock mode it falls back to a difflib text
ratio so the feature works without an API key.

Each question is a dict with at least a ``"question"`` key.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

import numpy as np

from services import config


@dataclass
class DedupResult:
    kept: list[dict]
    removed: list[dict]
    threshold: float


def deduplicate(questions: list[dict], threshold: float | None = None) -> DedupResult:
    """Remove near-duplicate questions, keeping the first occurrence of each.

    Args:
        questions: list of question dicts (must contain a "question" key).
        threshold: similarity at/above which two questions are duplicates.
            Defaults to config.get_duplicate_similarity_threshold().
    """
    if threshold is None:
        threshold = config.get_duplicate_similarity_threshold()

    if len(questions) <= 1:
        return DedupResult(kept=list(questions), removed=[], threshold=threshold)

    texts = [str(q.get("question", "")).strip() for q in questions]
    sim = _similarity_matrix(texts)

    kept_indices: list[int] = []
    removed: list[dict] = []
    for i in range(len(questions)):
        is_dup = any(sim[i][j] >= threshold for j in kept_indices)
        if is_dup:
            removed.append(questions[i])
        else:
            kept_indices.append(i)

    kept = [questions[i] for i in kept_indices]
    return DedupResult(kept=kept, removed=removed, threshold=threshold)


def _similarity_matrix(texts: list[str]) -> np.ndarray:
    if config.use_mock_data():
        return _text_similarity_matrix(texts)
    return _embedding_similarity_matrix(texts)


def _text_similarity_matrix(texts: list[str]) -> np.ndarray:
    n = len(texts)
    matrix = np.eye(n, dtype=float)
    normalized = [t.lower() for t in texts]
    for i in range(n):
        for j in range(i + 1, n):
            ratio = SequenceMatcher(None, normalized[i], normalized[j]).ratio()
            matrix[i][j] = ratio
            matrix[j][i] = ratio
    return matrix


def _embedding_similarity_matrix(texts: list[str]) -> np.ndarray:
    from openai import OpenAI

    client = OpenAI(api_key=config.get_openai_api_key())
    response = client.embeddings.create(
        model=config.get_openai_embedding_model(),
        input=texts,
    )
    vectors = np.array([item.embedding for item in response.data], dtype=float)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    unit = vectors / norms
    return unit @ unit.T

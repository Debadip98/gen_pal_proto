"""Candidate-pool generation for GenPal questions.

Instead of accepting all generated questions blindly, generates a larger
candidate pool then filters for uniqueness before accepting. Bounded by
MAX_CANDIDATE_ROUNDS_PER_BATCH to prevent infinite loops.
"""

from __future__ import annotations

import math
from typing import Callable, Optional

from backend.core import config, constants
from backend.services import duplicate_detector, generator


def generate_with_candidate_pool(
    skill: str,
    ssid: str,
    level: str,
    topics: list[str],
    urls: list[str],
    *,
    question_count: int = 40,
    threshold: float = 0.85,
    client=None,
    progress_cb: Optional[Callable[[str], None]] = None,
    avoid_existing: Optional[list[str]] = None,
    cost_sink: Optional[Callable] = None,
) -> list[dict]:
    """Generate ``question_count`` unique rows for one career level.

    Generates more candidates than needed, filters duplicates within the batch
    and against already-accepted rows, and repeats if short. Stops after
    MAX_CANDIDATE_ROUNDS_PER_BATCH regardless.
    """
    max_rounds = config.get_max_candidate_rounds_per_batch()
    avoid_existing = [q.strip() for q in (avoid_existing or []) if q and q.strip()]

    distribution = constants.calculate_complexity_distribution(question_count)
    accepted: list[dict] = []

    for complexity, required in distribution.items():
        if required <= 0:
            continue
        complexity_accepted: list[dict] = []
        rounds = 0

        while len(complexity_accepted) < required and rounds < max_rounds:
            still_needed = required - len(complexity_accepted)
            candidate_count = max(math.ceil(still_needed * 1.5), still_needed + 3)
            rounds += 1

            if progress_cb:
                progress_cb(
                    f"{level} · {complexity}: round {rounds}, "
                    f"generating {candidate_count} candidates for {still_needed} needed"
                )

            candidates = generator._mock_items(skill, level, complexity, candidate_count, topics, urls) \
                if config.use_mock_data() \
                else _generate_candidates(
                    client, skill, ssid, level, complexity, candidate_count,
                    topics, urls, avoid_existing, cost_sink=cost_sink,
                )

            candidate_rows = generator._build_rows(
                candidates, skill, ssid, level, complexity, candidate_count, topics, urls
            )

            unique = _filter_unique_against_accepted(
                candidate_rows, complexity_accepted, threshold, client=client, cost_sink=cost_sink
            )
            complexity_accepted.extend(unique[:still_needed])

        accepted.extend(complexity_accepted[:required])

    return accepted


def _generate_candidates(
    client,
    skill: str,
    ssid: str,
    level: str,
    complexity: str,
    count: int,
    topics: list[str],
    urls: list[str],
    avoid: list[str],
    cost_sink=None,
) -> list[dict]:
    items, usage = generator._openai_items(
        client, skill, level, complexity, count, topics, urls, avoid or None
    )
    if cost_sink and usage:
        cost_sink(config.get_openai_generation_model(), f"candidate_{level}_{complexity}", usage)
    return items


def _filter_unique_against_accepted(
    candidates: list[dict],
    already_accepted: list[dict],
    threshold: float,
    *,
    client=None,
    cost_sink=None,
) -> list[dict]:
    """Return candidates that are not near-duplicate of already_accepted rows."""
    if not already_accepted or not candidates:
        return candidates

    all_rows = already_accepted + candidates
    embeddings = duplicate_detector._embed(
        [r.get("question", "") for r in all_rows],
        client=client,
        cost_sink=cost_sink,
    )

    accepted_count = len(already_accepted)
    accepted_embeddings = embeddings[:accepted_count]
    candidate_embeddings = embeddings[accepted_count:]

    unique: list[dict] = []
    unique_embeddings: list[list[float]] = []

    for i, (row, emb) in enumerate(zip(candidates, candidate_embeddings)):
        is_dup = False
        for ref_emb in accepted_embeddings + unique_embeddings:
            if duplicate_detector._cosine(emb, ref_emb) > threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(row)
            unique_embeddings.append(emb)

    return unique

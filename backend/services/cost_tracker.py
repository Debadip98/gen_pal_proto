"""Cost tracking for OpenAI API usage in GenPal.

Intercepts OpenAI response.usage objects and records CostEvent rows.
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from backend.core import config
from backend.core.security import generate_id


def get_pricing() -> dict:
    return {
        "gpt-4o": {
            "input": config.get_openai_generation_input_price_per_1m() / 1_000_000,
            "output": config.get_openai_generation_output_price_per_1m() / 1_000_000,
        },
        "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
        "text-embedding-3-small": {
            "input": config.get_openai_embedding_price_per_1m() / 1_000_000,
            "output": 0.0,
        },
        "text-embedding-3-large": {"input": 0.13 / 1_000_000, "output": 0.0},
    }


def estimate_cost(model: str, input_tokens: int, output_tokens: int = 0) -> float:
    pricing = get_pricing()
    p = pricing.get(model, {"input": 0.0, "output": 0.0})
    return p["input"] * input_tokens + p["output"] * output_tokens


def record_event(
    db,
    job_id: str,
    step_name: str,
    model: str,
    usage,
    *,
    provider: str = "openai",
) -> None:
    """Write a CostEvent row to the database. Safe to call with usage=None."""
    from backend.db.models import CostEvent

    if usage is None:
        input_tokens = 0
        output_tokens = 0
    else:
        input_tokens = getattr(usage, "prompt_tokens", 0) or 0
        output_tokens = getattr(usage, "completion_tokens", 0) or 0

    is_embedding = "embedding" in model.lower()
    embedding_tokens = input_tokens if is_embedding else 0

    event = CostEvent(
        cost_event_id=generate_id(),
        job_id=job_id,
        provider=provider,
        model=model,
        step_name=step_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        embedding_tokens=embedding_tokens,
        estimated_cost=estimate_cost(model, input_tokens, output_tokens),
        created_at=datetime.utcnow(),
    )
    db.add(event)
    db.commit()


def make_cost_sink(job_id: str, db) -> Callable:
    """Return a cost_sink callable that writes CostEvent rows for this job."""
    def sink(model: str, step_name: str, usage) -> None:
        try:
            record_event(db, job_id, step_name, model, usage)
        except Exception:
            pass  # never block generation for cost tracking failures
    return sink


def get_cost_summary(db, job_id: str) -> dict:
    """Return aggregated cost summary for a job."""
    from backend.db.models import CostEvent

    events = db.query(CostEvent).filter_by(job_id=job_id).all()

    total_cost = sum(e.estimated_cost for e in events)
    total_input_tokens = sum(e.input_tokens for e in events)
    total_output_tokens = sum(e.output_tokens for e in events)
    total_embedding_tokens = sum(e.embedding_tokens for e in events)

    by_step: dict[str, dict] = {}
    by_model: dict[str, dict] = {}

    for e in events:
        step = e.step_name
        if step not in by_step:
            by_step[step] = {"cost": 0.0, "input_tokens": 0, "output_tokens": 0, "count": 0}
        by_step[step]["cost"] += e.estimated_cost
        by_step[step]["input_tokens"] += e.input_tokens
        by_step[step]["output_tokens"] += e.output_tokens
        by_step[step]["count"] += 1

        model = e.model
        if model not in by_model:
            by_model[model] = {"cost": 0.0, "input_tokens": 0, "output_tokens": 0, "count": 0}
        by_model[model]["cost"] += e.estimated_cost
        by_model[model]["input_tokens"] += e.input_tokens
        by_model[model]["output_tokens"] += e.output_tokens
        by_model[model]["count"] += 1

    return {
        "job_id": job_id,
        "total_estimated_cost_usd": round(total_cost, 6),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_embedding_tokens": total_embedding_tokens,
        "total_events": len(events),
        "by_step": by_step,
        "by_model": by_model,
    }

"""Pydantic schemas for export endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class CostSummaryResponse(BaseModel):
    job_id: str
    total_estimated_cost_usd: float
    total_input_tokens: int
    total_output_tokens: int
    total_embedding_tokens: int
    total_events: int
    by_step: dict
    by_model: dict

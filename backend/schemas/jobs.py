"""Pydantic schemas for job creation and response."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class CareerLevelInput(BaseModel):
    career_level: str
    enabled: bool = True
    question_count: int = 40

    @field_validator("career_level")
    @classmethod
    def validate_career_level(cls, v: str) -> str:
        from backend.core.constants import VALID_CAREER_LEVELS
        if v not in VALID_CAREER_LEVELS:
            raise ValueError(f"Invalid career level: {v}")
        return v

    @field_validator("question_count")
    @classmethod
    def validate_count(cls, v: int) -> int:
        if v < 1 or v > 200:
            raise ValueError("question_count must be between 1 and 200")
        return v


class CreateJobRequest(BaseModel):
    skill_name: str
    ssid: str
    requestor_email: str
    sme_email: Optional[str] = None
    topics: list[str]
    manual_urls: list[str] = []
    generation_mode: str = "Dynamic Count"
    career_levels: list[CareerLevelInput]
    duplicate_threshold: float = 0.85
    auto_find_docs: bool = False

    @field_validator("skill_name")
    @classmethod
    def validate_skill_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("skill_name is required")
        return v

    @field_validator("ssid")
    @classmethod
    def validate_ssid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("ssid is required")
        return v

    @field_validator("topics")
    @classmethod
    def validate_topics(cls, v: list[str]) -> list[str]:
        cleaned = [t.strip() for t in v if t.strip()]
        if not cleaned:
            raise ValueError("At least one topic is required")
        return cleaned


class CareerLevelResponse(BaseModel):
    id: str
    career_level: str
    enabled: bool
    question_count: int
    complexity_distribution: dict
    status: str


class JobResponse(BaseModel):
    job_id: str
    job_token: str
    skill_name: str
    ssid: str
    requestor_email: str
    sme_email: Optional[str]
    topics: list[str]
    manual_urls: list[str]
    selected_urls: list[str]
    generation_mode: str
    status: str
    duplicate_threshold: float
    total_expected_questions: int
    career_levels: list[CareerLevelResponse]
    generated_count: int
    accepted_count: int
    rejected_count: int
    pending_count: int
    review_progress_pct: float
    draft_download_ready: bool
    approved_download_ready: bool
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class GenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str

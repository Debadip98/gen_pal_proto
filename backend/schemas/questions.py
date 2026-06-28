"""Pydantic schemas for question rows."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class QuestionVersionSchema(BaseModel):
    version_id: str
    version_number: int
    old_question: str
    old_answer: str
    new_question: Optional[str]
    new_answer: Optional[str]
    sme_feedback: Optional[str]
    llm_suggestion: Optional[str]
    doc_check_summary: Optional[str]
    change_status: str
    created_at: datetime


class QuestionSchema(BaseModel):
    question_id: str
    job_id: str
    title: Optional[int]
    ssid: str
    skill: str
    topic: str
    question_type: str
    career_level: str
    complexity: str
    question: str
    answer: str
    options: str
    reference_url: str
    status: str
    reviewer_comment: Optional[str]
    llm_review_message: Optional[str]
    duplicate_warning: Optional[str]
    doc_alignment_status: Optional[str]
    created_at: datetime
    updated_at: datetime
    versions: list[QuestionVersionSchema] = []

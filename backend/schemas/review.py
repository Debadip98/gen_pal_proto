"""Pydantic schemas for SME review endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from backend.schemas.questions import QuestionSchema


class ReviewSessionResponse(BaseModel):
    review_token: str
    job_id: str
    sme_email: str
    status: str
    expires_at: datetime
    skill_name: str
    ssid: str
    total_questions: int
    accepted_count: int
    rejected_count: int
    pending_count: int
    questions: list[QuestionSchema]


class AcceptQuestionRequest(BaseModel):
    pass


class RejectQuestionRequest(BaseModel):
    comment: str = ""


class RegenerateQuestionRequest(BaseModel):
    sme_feedback: str
    use_llm_suggestion: bool = False


class SuggestionResponse(BaseModel):
    question_id: str
    suggestion: dict


class VersionActionRequest(BaseModel):
    pass


class SendSMEReviewRequest(BaseModel):
    pass


class SendSMEReviewResponse(BaseModel):
    review_link: str
    review_token: str
    email_sent: bool
    message: str

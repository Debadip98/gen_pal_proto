"""SQLAlchemy ORM models for GenPal (10 tables, SQLite backend)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.db.database import Base


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(String, primary_key=True, index=True)
    job_token = Column(String, unique=True, index=True, nullable=False)
    skill_name = Column(String, nullable=False)
    ssid = Column(String, nullable=False)
    requestor_email = Column(String, nullable=False)
    sme_email = Column(String, nullable=True)
    topics_json = Column(Text, nullable=False, default="[]")
    manual_urls_json = Column(Text, nullable=False, default="[]")
    discovered_urls_json = Column(Text, nullable=False, default="[]")
    selected_urls_json = Column(Text, nullable=False, default="[]")
    generation_mode = Column(String, nullable=False, default="Dynamic Count")
    status = Column(String, nullable=False, default="DRAFT")
    duplicate_threshold = Column(Float, nullable=False, default=0.85)
    total_expected_questions = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    career_level_requests = relationship(
        "CareerLevelRequest", back_populates="job", cascade="all, delete-orphan"
    )
    questions = relationship("Question", back_populates="job", cascade="all, delete-orphan")
    review_sessions = relationship("ReviewSession", back_populates="job", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="job", cascade="all, delete-orphan")
    document_sources = relationship("DocumentSource", back_populates="job", cascade="all, delete-orphan")
    cost_events = relationship("CostEvent", back_populates="job", cascade="all, delete-orphan")
    export_files = relationship("ExportFile", back_populates="job", cascade="all, delete-orphan")
    duplicate_pairs = relationship("DuplicatePair", back_populates="job", cascade="all, delete-orphan")


class CareerLevelRequest(Base):
    __tablename__ = "career_level_requests"

    id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False, index=True)
    career_level = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    question_count = Column(Integer, nullable=False, default=40)
    complexity_distribution_json = Column(Text, nullable=False, default="{}")
    status = Column(String, nullable=False, default="PENDING")

    job = relationship("Job", back_populates="career_level_requests")


class Question(Base):
    __tablename__ = "questions"

    question_id = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False, index=True)
    title = Column(Integer, nullable=True)
    ssid = Column(String, nullable=False)
    skill = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    question_type = Column(String, nullable=False, default="QnA")
    career_level = Column(String, nullable=False)
    complexity = Column(String, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    options = Column(String, nullable=False, default="")
    reference_url = Column(String, nullable=False)
    status = Column(String, nullable=False, default="DRAFT")
    reviewer_comment = Column(Text, nullable=True)
    llm_review_message = Column(Text, nullable=True)
    duplicate_warning = Column(Text, nullable=True)
    doc_alignment_status = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("Job", back_populates="questions")
    versions = relationship(
        "QuestionVersion", back_populates="question", cascade="all, delete-orphan",
        order_by="QuestionVersion.version_number"
    )


class QuestionVersion(Base):
    __tablename__ = "question_versions"

    version_id = Column(String, primary_key=True)
    question_id = Column(String, ForeignKey("questions.question_id"), nullable=False, index=True)
    job_id = Column(String, nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    old_question = Column(Text, nullable=False)
    old_answer = Column(Text, nullable=False)
    new_question = Column(Text, nullable=True)
    new_answer = Column(Text, nullable=True)
    sme_feedback = Column(Text, nullable=True)
    llm_suggestion = Column(Text, nullable=True)
    doc_check_summary = Column(Text, nullable=True)
    duplicate_check_summary = Column(Text, nullable=True)
    change_status = Column(String, nullable=False, default="PENDING_SME_DECISION")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    question = relationship("Question", back_populates="versions")


class ReviewSession(Base):
    __tablename__ = "review_sessions"

    review_token = Column(String, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False, index=True)
    sme_email = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

    job = relationship("Job", back_populates="review_sessions")


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False, index=True)
    question_id = Column(String, nullable=True)
    recipient_email = Column(String, nullable=False)
    actor = Column(String, nullable=True)
    action_type = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    job = relationship("Job", back_populates="notifications")


class DocumentSource(Base):
    __tablename__ = "document_sources"

    source_id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False, index=True)
    source_type = Column(String, nullable=False)
    source_name = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    source_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    selected = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    job = relationship("Job", back_populates="document_sources")


class DuplicatePair(Base):
    __tablename__ = "duplicate_pairs"

    pair_id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False, index=True)
    question_id_1 = Column(String, nullable=False)
    question_id_2 = Column(String, nullable=False)
    similarity_score = Column(Float, nullable=False)
    duplicate_type = Column(String, nullable=False, default="EMBEDDING")
    status = Column(String, nullable=False, default="OPEN")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    job = relationship("Job", back_populates="duplicate_pairs")


class CostEvent(Base):
    __tablename__ = "cost_events"

    cost_event_id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False, index=True)
    provider = Column(String, nullable=False, default="openai")
    model = Column(String, nullable=False)
    step_name = Column(String, nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    embedding_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    job = relationship("Job", back_populates="cost_events")


class ExportFile(Base):
    __tablename__ = "export_files"

    export_id = Column(String, primary_key=True)
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False, index=True)
    export_type = Column(String, nullable=False, default="DRAFT")
    file_name = Column(String, nullable=False)
    file_bytes = Column(LargeBinary, nullable=True)
    row_count = Column(Integer, nullable=False, default=0)
    sheet_name = Column(String, nullable=False, default="Sheet1")
    status = Column(String, nullable=False, default="READY")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    job = relationship("Job", back_populates="export_files")

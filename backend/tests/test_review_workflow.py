"""Tests for the SME review state machine."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core import constants
from backend.db.database import Base
from backend.db.models import (
    Job, Question, Notification,
)
from backend.core.security import generate_id, generate_review_token
from backend.services import review_service


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _create_job(db) -> Job:
    job = Job(
        job_id=generate_id(),
        job_token=generate_review_token(),
        skill_name="Test Skill",
        ssid="T001",
        requestor_email="req@example.com",
        sme_email="sme@example.com",
        status=constants.JobStatus.GENERATED,
    )
    db.add(job)
    db.flush()
    return job


def _create_question(db, job: Job) -> Question:
    q = Question(
        question_id=generate_id(),
        job_id=job.job_id,
        title=1,
        ssid=job.ssid,
        skill=job.skill_name,
        topic="Testing",
        question_type="QnA",
        career_level="ASE",
        complexity="Basic",
        question="What is a test?",
        answer="A test verifies correctness.",
        reference_url="https://example.com",
        status=constants.QuestionStatus.PENDING_SME_REVIEW,
    )
    db.add(q)
    db.flush()
    return q


# ── accept_question ───────────────────────────────────────────────────────────

def test_accept_question_sets_status(db):
    job = _create_job(db)
    q = _create_question(db, job)

    review_service.accept_question(db, q, job, sme_email="sme@example.com")
    db.refresh(q)
    assert q.status == constants.QuestionStatus.ACCEPTED


def test_accept_question_creates_notification(db):
    job = _create_job(db)
    q = _create_question(db, job)

    review_service.accept_question(db, q, job, sme_email="sme@example.com")
    notifs = db.query(Notification).filter_by(job_id=job.job_id).all()
    assert len(notifs) >= 1


# ── reject_question ───────────────────────────────────────────────────────────

def test_reject_question_sets_status(db):
    job = _create_job(db)
    q = _create_question(db, job)

    review_service.reject_question(db, q, job, sme_email="sme@example.com", comment="Too vague.")
    db.refresh(q)
    assert q.status == constants.QuestionStatus.REJECTED


def test_reject_question_stores_comment(db):
    job = _create_job(db)
    q = _create_question(db, job)

    review_service.reject_question(db, q, job, sme_email="sme@example.com", comment="Too vague.")
    db.refresh(q)
    assert "Too vague" in (q.reviewer_comment or "")


# ── create_regeneration_version ───────────────────────────────────────────────

def test_create_version_sets_pending_decision(db):
    job = _create_job(db)
    q = _create_question(db, job)

    version = review_service.create_regeneration_version(
        db, q,
        sme_feedback="Please add an example.",
        new_question="What is a test? (With example)",
        new_answer="A test verifies correctness. For example, a unit test checks one function.",
    )
    assert version.change_status == constants.VersionStatus.PENDING_SME_DECISION


def test_create_version_increments_version_number(db):
    job = _create_job(db)
    q = _create_question(db, job)

    v1 = review_service.create_regeneration_version(
        db, q, sme_feedback="First", new_question="Q v1", new_answer="A v1",
    )
    v2 = review_service.create_regeneration_version(
        db, q, sme_feedback="Second", new_question="Q v2", new_answer="A v2",
    )
    assert v2.version_number > v1.version_number


# ── accept_version ────────────────────────────────────────────────────────────

def test_accept_version_overwrites_question(db):
    job = _create_job(db)
    q = _create_question(db, job)

    version = review_service.create_regeneration_version(
        db, q,
        sme_feedback="Improve clarity.",
        new_question="What is a test? (Clarified)",
        new_answer="A test verifies correctness systematically.",
    )

    review_service.accept_version(db, version, q, job, sme_email="sme@example.com")
    db.refresh(q)
    assert q.question == "What is a test? (Clarified)"
    assert q.status == constants.QuestionStatus.ACCEPTED


def test_accept_version_marks_version_accepted(db):
    job = _create_job(db)
    q = _create_question(db, job)

    version = review_service.create_regeneration_version(
        db, q, sme_feedback="OK", new_question="Q new", new_answer="A new",
    )
    review_service.accept_version(db, version, q, job, sme_email="sme@example.com")
    assert version.change_status == constants.VersionStatus.ACCEPTED_BY_SME


# ── reject_version ────────────────────────────────────────────────────────────

def test_reject_version_restores_pending_review(db):
    job = _create_job(db)
    q = _create_question(db, job)

    version = review_service.create_regeneration_version(
        db, q, sme_feedback="Not good enough.", new_question="Q v1", new_answer="A v1",
    )
    review_service.reject_version(db, version, q, job, sme_email="sme@example.com")
    db.refresh(q)
    assert q.status == constants.QuestionStatus.PENDING_SME_REVIEW
    assert version.change_status == constants.VersionStatus.REJECTED_BY_SME


def test_accept_all_questions_sets_job_approved(db):
    job = _create_job(db)
    q = _create_question(db, job)

    review_service.accept_question(db, q, job, sme_email="sme@example.com")
    db.refresh(job)
    assert job.status == constants.JobStatus.APPROVED

"""SME review business logic for GenPal.

Handles accept/reject/regenerate operations on questions and versions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend.core import constants
from backend.core.security import generate_id
from backend.db.models import Question, QuestionVersion
from backend.services import notification_service


def accept_question(
    db,
    question: Question,
    job,
    sme_email: str,
) -> Question:
    """Mark a question as ACCEPTED and create a requestor notification."""
    question.status = constants.QuestionStatus.ACCEPTED
    question.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(question)

    notification_service.notify_question_accepted(
        db,
        job_id=question.job_id,
        requestor_email=job.requestor_email,
        question_id=question.question_id,
        question_title=question.title or 0,
        sme_email=sme_email,
    )
    _check_review_completion(db, job, sme_email)
    return question


def reject_question(
    db,
    question: Question,
    job,
    sme_email: str,
    comment: str = "",
) -> Question:
    """Mark a question as REJECTED and create a requestor notification."""
    question.status = constants.QuestionStatus.REJECTED
    question.reviewer_comment = comment
    question.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(question)

    notification_service.notify_question_rejected(
        db,
        job_id=question.job_id,
        requestor_email=job.requestor_email,
        question_id=question.question_id,
        question_title=question.title or 0,
        sme_email=sme_email,
        comment=comment,
    )
    return question


def create_regeneration_version(
    db,
    question: Question,
    sme_feedback: str,
    new_question: str,
    new_answer: str,
    *,
    llm_suggestion: Optional[str] = None,
    doc_check_summary: Optional[str] = None,
) -> QuestionVersion:
    """Create a QuestionVersion row with the new content, pending SME decision."""
    existing_versions = db.query(QuestionVersion).filter_by(
        question_id=question.question_id
    ).count()
    version = QuestionVersion(
        version_id=generate_id(),
        question_id=question.question_id,
        job_id=question.job_id,
        version_number=existing_versions + 1,
        old_question=question.question,
        old_answer=question.answer,
        new_question=new_question,
        new_answer=new_answer,
        sme_feedback=sme_feedback,
        llm_suggestion=llm_suggestion,
        doc_check_summary=doc_check_summary,
        change_status=constants.VersionStatus.PENDING_SME_DECISION,
        created_at=datetime.utcnow(),
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def accept_version(
    db,
    version: QuestionVersion,
    question: Question,
    job,
    sme_email: str,
) -> Question:
    """Accept a regenerated version — overwrite main question row and notify."""
    if not version.new_question or not version.new_answer:
        raise ValueError("Version has no new content to accept.")

    question.question = version.new_question
    question.answer = version.new_answer
    question.status = constants.QuestionStatus.ACCEPTED
    question.updated_at = datetime.utcnow()

    version.change_status = constants.VersionStatus.ACCEPTED_BY_SME
    db.commit()
    db.refresh(question)

    notification_service.notify_version_accepted(
        db,
        job_id=question.job_id,
        requestor_email=job.requestor_email,
        question_id=question.question_id,
        question_title=question.title or 0,
        sme_email=sme_email,
    )
    _check_review_completion(db, job, sme_email)
    return question


def reject_version(
    db,
    version: QuestionVersion,
    question: Question,
    job,
    sme_email: str,
) -> Question:
    """Reject a regenerated version — original question is retained."""
    version.change_status = constants.VersionStatus.REJECTED_BY_SME
    question.status = constants.QuestionStatus.PENDING_SME_REVIEW
    question.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(question)

    notification_service.notify_version_rejected(
        db,
        job_id=question.job_id,
        requestor_email=job.requestor_email,
        question_id=question.question_id,
        question_title=question.title or 0,
        sme_email=sme_email,
    )
    return question


def _check_review_completion(db, job, sme_email: str) -> None:
    """If all questions are now ACCEPTED, send a review-complete notification."""
    pending = (
        db.query(Question)
        .filter(
            Question.job_id == job.job_id,
            Question.status.notin_([
                constants.QuestionStatus.ACCEPTED,
                constants.QuestionStatus.REJECTED,
            ]),
        )
        .count()
    )
    if pending == 0:
        job.status = constants.JobStatus.APPROVED
        db.commit()
        notification_service.notify_review_complete(
            db,
            job_id=job.job_id,
            requestor_email=job.requestor_email,
            sme_email=sme_email,
        )

"""SME review and requestor dashboard API routes."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core import config, constants
from backend.core.security import generate_review_token
from backend.db.models import Job, Notification, Question, QuestionVersion, ReviewSession
from backend.schemas.questions import QuestionSchema, QuestionVersionSchema
from backend.schemas.review import (
    AcceptQuestionRequest,
    RegenerateQuestionRequest,
    RejectQuestionRequest,
    SendSMEReviewResponse,
    SuggestionResponse,
)
from backend.services import (
    document_context,
    email_service,
    generator,
    notification_service,
    review_service,
    suggestion_service,
)

router = APIRouter(tags=["review"])


def _get_valid_session(review_token: str, db: Session) -> ReviewSession:
    session = (
        db.query(ReviewSession).filter_by(review_token=review_token).first()
    )
    if not session:
        raise HTTPException(404, "Review session not found")
    if session.status == constants.ReviewSessionStatus.EXPIRED:
        raise HTTPException(403, "Review session has expired")
    if session.expires_at < datetime.utcnow():
        session.status = constants.ReviewSessionStatus.EXPIRED
        db.commit()
        raise HTTPException(403, "Review session has expired")
    if session.status == constants.ReviewSessionStatus.COMPLETED:
        raise HTTPException(403, "Review session is already completed")
    return session


def _get_question_schema(q: Question) -> QuestionSchema:
    versions = [
        QuestionVersionSchema(
            version_id=v.version_id,
            version_number=v.version_number,
            old_question=v.old_question,
            old_answer=v.old_answer,
            new_question=v.new_question,
            new_answer=v.new_answer,
            sme_feedback=v.sme_feedback,
            llm_suggestion=v.llm_suggestion,
            doc_check_summary=v.doc_check_summary,
            change_status=v.change_status,
            created_at=v.created_at,
        )
        for v in q.versions
    ]
    return QuestionSchema(
        question_id=q.question_id,
        job_id=q.job_id,
        title=q.title,
        ssid=q.ssid,
        skill=q.skill,
        topic=q.topic,
        question_type=q.question_type,
        career_level=q.career_level,
        complexity=q.complexity,
        question=q.question,
        answer=q.answer,
        options=q.options,
        reference_url=q.reference_url,
        status=q.status,
        reviewer_comment=q.reviewer_comment,
        llm_review_message=q.llm_review_message,
        duplicate_warning=q.duplicate_warning,
        doc_alignment_status=q.doc_alignment_status,
        created_at=q.created_at,
        updated_at=q.updated_at,
        versions=versions,
    )


# --- Send SME Review ----------------------------------------------------------

@router.post("/jobs/{job_id}/send-sme-review", response_model=SendSMEReviewResponse)
def send_sme_review(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter_by(job_id=job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status not in (
        constants.JobStatus.GENERATED,
        constants.JobStatus.SENT_TO_SME,
        constants.JobStatus.IN_REVIEW,
    ):
        raise HTTPException(400, f"Job is not in a reviewable state (status: {job.status})")
    if not job.sme_email:
        raise HTTPException(400, "No SME email configured for this job")

    existing_sessions = db.query(ReviewSession).filter_by(
        job_id=job_id, status=constants.ReviewSessionStatus.ACTIVE
    ).all()
    for s in existing_sessions:
        s.status = constants.ReviewSessionStatus.EXPIRED
    db.flush()

    token = generate_review_token()
    expiry_hours = config.get_review_token_expiry_hours()
    session = ReviewSession(
        review_token=token,
        job_id=job_id,
        sme_email=job.sme_email,
        status=constants.ReviewSessionStatus.ACTIVE,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=expiry_hours),
    )
    db.add(session)

    pending_questions = (
        db.query(Question)
        .filter_by(job_id=job_id, status=constants.QuestionStatus.DRAFT)
        .all()
    )
    for q in pending_questions:
        q.status = constants.QuestionStatus.PENDING_SME_REVIEW
        q.updated_at = datetime.utcnow()

    job.status = constants.JobStatus.SENT_TO_SME
    job.updated_at = datetime.utcnow()
    db.commit()

    app_base = config.get_app_base_url()
    review_link = f"{app_base}?review_token={token}"

    email_sent = email_service.send_review_link(
        job.sme_email, review_link, job.skill_name, job.requestor_email
    )

    notification_service.notify_review_sent(
        db, job_id=job_id, requestor_email=job.requestor_email, sme_email=job.sme_email
    )

    msg = (
        f"Review email sent to {job.sme_email}."
        if email_sent
        else f"Email not configured. Share this link with {job.sme_email}: {review_link}"
    )
    return SendSMEReviewResponse(
        review_link=review_link,
        review_token=token,
        email_sent=email_sent,
        message=msg,
    )


# --- SME Review Session -------------------------------------------------------

@router.get("/review/{review_token}")
def get_review_session(review_token: str, db: Session = Depends(get_db)):
    session = _get_valid_session(review_token, db)
    job = db.query(Job).filter_by(job_id=session.job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    questions = (
        db.query(Question)
        .filter_by(job_id=session.job_id)
        .order_by(Question.title)
        .all()
    )
    accepted = sum(1 for q in questions if q.status == constants.QuestionStatus.ACCEPTED)
    rejected = sum(1 for q in questions if q.status == constants.QuestionStatus.REJECTED)
    pending = len(questions) - accepted - rejected

    return {
        "review_token": review_token,
        "job_id": session.job_id,
        "sme_email": session.sme_email,
        "status": session.status,
        "expires_at": session.expires_at.isoformat(),
        "skill_name": job.skill_name,
        "ssid": job.ssid,
        "total_questions": len(questions),
        "accepted_count": accepted,
        "rejected_count": rejected,
        "pending_count": pending,
        "questions": [_get_question_schema(q).model_dump() for q in questions],
    }


# --- Accept Question ----------------------------------------------------------

@router.post("/review/{review_token}/questions/{question_id}/accept")
def accept_question(
    review_token: str,
    question_id: str,
    db: Session = Depends(get_db),
):
    session = _get_valid_session(review_token, db)
    question = db.query(Question).filter_by(
        question_id=question_id, job_id=session.job_id
    ).first()
    if not question:
        raise HTTPException(404, "Question not found")

    job = db.query(Job).filter_by(job_id=session.job_id).first()
    updated_q = review_service.accept_question(db, question, job, session.sme_email)
    return _get_question_schema(updated_q).model_dump()


# --- Reject Question ----------------------------------------------------------

@router.post("/review/{review_token}/questions/{question_id}/reject")
def reject_question(
    review_token: str,
    question_id: str,
    req: RejectQuestionRequest,
    db: Session = Depends(get_db),
):
    session = _get_valid_session(review_token, db)
    question = db.query(Question).filter_by(
        question_id=question_id, job_id=session.job_id
    ).first()
    if not question:
        raise HTTPException(404, "Question not found")

    job = db.query(Job).filter_by(job_id=session.job_id).first()
    updated_q = review_service.reject_question(
        db, question, job, session.sme_email, comment=req.comment
    )
    return _get_question_schema(updated_q).model_dump()


# --- LLM Suggestion -----------------------------------------------------------

@router.post("/review/{review_token}/questions/{question_id}/suggestion")
def get_suggestion(
    review_token: str,
    question_id: str,
    db: Session = Depends(get_db),
):
    session = _get_valid_session(review_token, db)
    question = db.query(Question).filter_by(
        question_id=question_id, job_id=session.job_id
    ).first()
    if not question:
        raise HTTPException(404, "Question not found")

    doc_ctx = document_context.get_document_context_for_job(db, session.job_id)
    row_dict = {
        "career_level": question.career_level,
        "complexity": question.complexity,
        "topic": question.topic,
        "question": question.question,
        "answer": question.answer,
        "reference_url": question.reference_url,
    }

    result = suggestion_service.get_llm_suggestion(
        row_dict,
        doc_context=doc_ctx,
        duplicate_warning=question.duplicate_warning or "",
    )

    import json as _json
    question.llm_review_message = _json.dumps(result)
    question.doc_alignment_status = result.get("doc_alignment")
    question.updated_at = datetime.utcnow()
    db.commit()

    return {"question_id": question_id, "suggestion": result}


# --- Regenerate Question ------------------------------------------------------

@router.post("/review/{review_token}/questions/{question_id}/regenerate")
def regenerate_question(
    review_token: str,
    question_id: str,
    req: RegenerateQuestionRequest,
    db: Session = Depends(get_db),
):
    session = _get_valid_session(review_token, db)
    question = db.query(Question).filter_by(
        question_id=question_id, job_id=session.job_id
    ).first()
    if not question:
        raise HTTPException(404, "Question not found")

    job = db.query(Job).filter_by(job_id=session.job_id).first()
    topics = json.loads(job.topics_json or "[]")
    selected_urls = json.loads(job.selected_urls_json or "[]")
    manual_urls = json.loads(job.manual_urls_json or "[]")
    all_urls = list(dict.fromkeys(selected_urls + manual_urls)) or ["https://example.com"]

    nearby = (
        db.query(Question.question)
        .filter(
            Question.job_id == session.job_id,
            Question.question_id != question_id,
        )
        .limit(60)
        .all()
    )
    nearby_questions = [r[0] for r in nearby]

    doc_ctx = document_context.get_document_context_for_job(db, session.job_id)

    llm_suggestion_text = ""
    if req.use_llm_suggestion and question.llm_review_message:
        import json as _json
        try:
            sug = _json.loads(question.llm_review_message)
            llm_suggestion_text = sug.get("suggested_improvement") or ""
        except Exception:
            pass

    feedback = req.sme_feedback
    if llm_suggestion_text:
        feedback = f"{feedback}\nLLM suggestion: {llm_suggestion_text}"

    row_dict = {
        "title": question.title,
        "skill": question.skill,
        "career_level": question.career_level,
        "complexity": question.complexity,
        "topic": question.topic,
        "reference_url": question.reference_url,
    }

    new_content = generator.regenerate_single_question(
        row_dict,
        feedback,
        topics,
        all_urls,
        nearby_questions,
        doc_context=doc_ctx,
    )

    new_q = new_content.get("question", "").strip()
    new_a = new_content.get("answer", "").strip()

    if not new_q or not new_a:
        raise HTTPException(500, "Regeneration failed to produce valid content")

    version = review_service.create_regeneration_version(
        db,
        question,
        sme_feedback=req.sme_feedback,
        new_question=new_q,
        new_answer=new_a,
        llm_suggestion=llm_suggestion_text or None,
        doc_check_summary=doc_ctx[:500] if doc_ctx else None,
    )

    notification_service.notify_question_regenerated(
        db,
        job_id=question.job_id,
        requestor_email=job.requestor_email,
        question_id=question.question_id,
        question_title=question.title or 0,
        sme_email=session.sme_email,
    )

    return {
        "version_id": version.version_id,
        "version_number": version.version_number,
        "old_question": version.old_question,
        "old_answer": version.old_answer,
        "new_question": version.new_question,
        "new_answer": version.new_answer,
        "change_status": version.change_status,
        "created_at": version.created_at.isoformat(),
    }


# --- Accept / Reject Version --------------------------------------------------

@router.post("/review/{review_token}/versions/{version_id}/accept")
def accept_version(
    review_token: str,
    version_id: str,
    db: Session = Depends(get_db),
):
    session = _get_valid_session(review_token, db)
    version = db.query(QuestionVersion).filter_by(
        version_id=version_id, job_id=session.job_id
    ).first()
    if not version:
        raise HTTPException(404, "Version not found")

    question = db.query(Question).filter_by(question_id=version.question_id).first()
    if not question:
        raise HTTPException(404, "Parent question not found")

    job = db.query(Job).filter_by(job_id=session.job_id).first()
    updated_q = review_service.accept_version(db, version, question, job, session.sme_email)
    return _get_question_schema(updated_q).model_dump()


@router.post("/review/{review_token}/versions/{version_id}/reject")
def reject_version(
    review_token: str,
    version_id: str,
    db: Session = Depends(get_db),
):
    session = _get_valid_session(review_token, db)
    version = db.query(QuestionVersion).filter_by(
        version_id=version_id, job_id=session.job_id
    ).first()
    if not version:
        raise HTTPException(404, "Version not found")

    question = db.query(Question).filter_by(question_id=version.question_id).first()
    if not question:
        raise HTTPException(404, "Parent question not found")

    job = db.query(Job).filter_by(job_id=session.job_id).first()
    updated_q = review_service.reject_version(db, version, question, job, session.sme_email)
    return _get_question_schema(updated_q).model_dump()


# --- Requestor Dashboard ------------------------------------------------------

@router.get("/dashboard/{job_token}")
def get_dashboard(job_token: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter_by(job_token=job_token).first()
    if not job:
        raise HTTPException(404, "Job not found — invalid token")

    questions = (
        db.query(Question).filter_by(job_id=job.job_id).order_by(Question.title).all()
    )
    total_q = len(questions)
    accepted = sum(1 for q in questions if q.status == constants.QuestionStatus.ACCEPTED)
    rejected = sum(1 for q in questions if q.status == constants.QuestionStatus.REJECTED)
    pending = total_q - accepted - rejected

    unread_count = (
        db.query(Notification)
        .filter_by(job_id=job.job_id, is_read=False)
        .count()
    )

    from backend.services.cost_tracker import get_cost_summary as _cost
    cost_summary = _cost(db, job.job_id)

    topics = json.loads(job.topics_json or "[]")
    selected_urls = json.loads(job.selected_urls_json or "[]")

    draft_ready = job.status in (
        constants.JobStatus.GENERATED,
        constants.JobStatus.SENT_TO_SME,
        constants.JobStatus.IN_REVIEW,
        constants.JobStatus.APPROVED,
    ) and total_q > 0

    approved_ready = total_q > 0 and pending == 0 and rejected == 0

    return {
        "job_id": job.job_id,
        "job_token": job.job_token,
        "skill_name": job.skill_name,
        "ssid": job.ssid,
        "status": job.status,
        "topics": topics,
        "selected_urls": selected_urls,
        "total_questions": total_q,
        "accepted_count": accepted,
        "rejected_count": rejected,
        "pending_count": pending,
        "review_progress_pct": round((accepted + rejected) / total_q * 100, 1) if total_q else 0.0,
        "draft_download_ready": draft_ready,
        "approved_download_ready": approved_ready,
        "unread_notifications": unread_count,
        "cost_summary": cost_summary,
        "question_statuses": [
            {
                "question_id": q.question_id,
                "title": q.title,
                "career_level": q.career_level,
                "complexity": q.complexity,
                "status": q.status,
            }
            for q in questions
        ],
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }

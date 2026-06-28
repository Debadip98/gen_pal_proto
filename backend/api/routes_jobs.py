"""Job management API routes."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core import config, constants
from backend.core.security import generate_id, generate_job_token
from backend.db.models import CareerLevelRequest, Job, Question
from backend.pipeline.runner import run_generation_pipeline
from backend.schemas.jobs import (
    CareerLevelResponse,
    CreateJobRequest,
    GenerateResponse,
    JobResponse,
)
from backend.schemas.questions import QuestionSchema, QuestionVersionSchema
from backend.services import cost_tracker

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _job_to_response(job: Job, db: Session) -> JobResponse:
    topics = json.loads(job.topics_json or "[]")
    manual_urls = json.loads(job.manual_urls_json or "[]")
    selected_urls = json.loads(job.selected_urls_json or "[]")

    level_reqs = db.query(CareerLevelRequest).filter_by(job_id=job.job_id).all()
    level_responses = []
    for lr in level_reqs:
        dist = json.loads(lr.complexity_distribution_json or "{}")
        if not dist:
            dist = constants.calculate_complexity_distribution(lr.question_count)
        level_responses.append(
            CareerLevelResponse(
                id=lr.id,
                career_level=lr.career_level,
                enabled=lr.enabled,
                question_count=lr.question_count,
                complexity_distribution=dist,
                status=lr.status,
            )
        )

    questions = db.query(Question).filter_by(job_id=job.job_id).all()
    total_q = len(questions)
    accepted = sum(1 for q in questions if q.status == constants.QuestionStatus.ACCEPTED)
    rejected = sum(1 for q in questions if q.status == constants.QuestionStatus.REJECTED)
    pending = total_q - accepted - rejected

    review_progress_pct = 0.0
    if total_q > 0:
        review_progress_pct = round((accepted + rejected) / total_q * 100, 1)

    draft_ready = job.status in (
        constants.JobStatus.GENERATED,
        constants.JobStatus.SENT_TO_SME,
        constants.JobStatus.IN_REVIEW,
        constants.JobStatus.APPROVED,
        constants.JobStatus.EXCEL_READY,
        constants.JobStatus.EXPORTED,
    ) and total_q > 0

    approved_ready = job.status in (
        constants.JobStatus.APPROVED,
        constants.JobStatus.EXCEL_READY,
        constants.JobStatus.EXPORTED,
    ) or (total_q > 0 and pending == 0 and rejected == 0)

    return JobResponse(
        job_id=job.job_id,
        job_token=job.job_token,
        skill_name=job.skill_name,
        ssid=job.ssid,
        requestor_email=job.requestor_email,
        sme_email=job.sme_email,
        topics=topics,
        manual_urls=manual_urls,
        selected_urls=selected_urls,
        generation_mode=job.generation_mode,
        status=job.status,
        duplicate_threshold=job.duplicate_threshold,
        total_expected_questions=job.total_expected_questions,
        career_levels=level_responses,
        generated_count=total_q,
        accepted_count=accepted,
        rejected_count=rejected,
        pending_count=pending,
        review_progress_pct=review_progress_pct,
        draft_download_ready=draft_ready,
        approved_download_ready=approved_ready,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("", response_model=JobResponse, status_code=201)
def create_job(req: CreateJobRequest, db: Session = Depends(get_db)):
    enabled_levels = [cl for cl in req.career_levels if cl.enabled]
    if not enabled_levels:
        raise HTTPException(400, "At least one career level must be enabled")

    total_expected = sum(cl.question_count for cl in enabled_levels)
    job_id = generate_id()
    job_token = generate_job_token()

    job = Job(
        job_id=job_id,
        job_token=job_token,
        skill_name=req.skill_name.strip(),
        ssid=req.ssid.strip(),
        requestor_email=req.requestor_email,
        sme_email=req.sme_email,
        topics_json=json.dumps([t.strip() for t in req.topics if t.strip()]),
        manual_urls_json=json.dumps([u.strip() for u in req.manual_urls if u.strip()]),
        selected_urls_json=json.dumps([u.strip() for u in req.manual_urls if u.strip()]),
        generation_mode=req.generation_mode,
        status=constants.JobStatus.DRAFT,
        duplicate_threshold=req.duplicate_threshold,
        total_expected_questions=total_expected,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(job)

    for cl in req.career_levels:
        dist = constants.calculate_complexity_distribution(cl.question_count)
        lr = CareerLevelRequest(
            id=generate_id(),
            job_id=job_id,
            career_level=cl.career_level,
            enabled=cl.enabled,
            question_count=cl.question_count,
            complexity_distribution_json=json.dumps(dist),
            status="PENDING",
        )
        db.add(lr)

    db.commit()
    db.refresh(job)
    return _job_to_response(job, db)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter_by(job_id=job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return _job_to_response(job, db)


@router.post("/{job_id}/generate", response_model=GenerateResponse)
def start_generation(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter_by(job_id=job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status == constants.JobStatus.GENERATING:
        raise HTTPException(409, "Generation already in progress")

    job.status = constants.JobStatus.GENERATING
    job.updated_at = datetime.utcnow()
    db.commit()

    background_tasks.add_task(run_generation_pipeline, job_id)
    return GenerateResponse(
        job_id=job_id,
        status=constants.JobStatus.GENERATING,
        message="Generation started. Poll GET /api/v1/jobs/{job_id} for status.",
    )


@router.get("/{job_id}/questions", response_model=list[QuestionSchema])
def get_questions(
    job_id: str,
    career_level: Optional[str] = Query(None),
    complexity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter_by(job_id=job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    query = db.query(Question).filter_by(job_id=job_id)
    if career_level:
        query = query.filter(Question.career_level == career_level)
    if complexity:
        query = query.filter(Question.complexity == complexity)
    if status:
        query = query.filter(Question.status == status)

    questions = query.order_by(Question.title).all()
    result = []
    for q in questions:
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
        result.append(
            QuestionSchema(
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
        )
    return result


@router.get("/{job_id}/cost-summary")
def get_cost_summary(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter_by(job_id=job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    return cost_tracker.get_cost_summary(db, job_id)

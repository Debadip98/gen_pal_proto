"""Generation pipeline runner for GenPal jobs.

Runs as a FastAPI BackgroundTask. The endpoint returns immediately with
status=GENERATING; Streamlit polls GET /jobs/{job_id} every few seconds.

Opens its own DB session (SQLite thread-safety with check_same_thread=False).
"""

from __future__ import annotations

import json
import traceback as _traceback
from datetime import datetime
from typing import Optional

from backend.core import config, constants
from backend.core.security import generate_id
from backend.db.database import SessionLocal
from backend.db.models import (
    CareerLevelRequest,
    ExportFile,
    Job,
    Question,
)
from backend.services import (
    candidate_filter,
    cost_tracker,
    excel_exporter,
    generator,
    notification_service,
    rework,
    validators,
)


def run_generation_pipeline(job_id: str) -> None:
    """Generate all questions for a job. Called as a BackgroundTask."""
    db = SessionLocal()
    try:
        _run(db, job_id)
    except Exception:
        try:
            job = db.query(Job).filter_by(job_id=job_id).first()
            if job:
                job.status = constants.JobStatus.FAILED
                job.error_message = _traceback.format_exc()[:2000]
                job.updated_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _run(db, job_id: str) -> None:
    job = db.query(Job).filter_by(job_id=job_id).first()
    if not job:
        raise ValueError(f"Job {job_id} not found")

    topics = json.loads(job.topics_json or "[]")
    selected_urls = json.loads(job.selected_urls_json or "[]")
    manual_urls = json.loads(job.manual_urls_json or "[]")
    all_urls = list(dict.fromkeys(selected_urls + manual_urls))
    if not all_urls:
        all_urls = ["https://example.com"]

    threshold = job.duplicate_threshold
    cost_sink = cost_tracker.make_cost_sink(job_id, db)

    client = None if config.use_mock_data() else generator.make_client()

    level_requests: list[CareerLevelRequest] = (
        db.query(CareerLevelRequest)
        .filter_by(job_id=job_id, enabled=True)
        .all()
    )
    level_order = {level: i for i, level in enumerate(constants.CAREER_LEVELS)}
    level_requests.sort(key=lambda r: level_order.get(r.career_level, 99))

    level_rows: dict[str, list[dict]] = {}

    for level_req in level_requests:
        level = level_req.career_level
        question_count = level_req.question_count

        existing_questions = [
            q["question"]
            for rows in level_rows.values()
            for q in rows
        ] if level_rows else []

        rows = candidate_filter.generate_with_candidate_pool(
            job.skill_name,
            job.ssid,
            level,
            topics,
            all_urls,
            question_count=question_count,
            threshold=threshold,
            client=client,
            avoid_existing=existing_questions,
            cost_sink=cost_sink,
        )

        max_attempts = config.get_max_duplicate_passes_per_level()
        rows, remaining_dups = rework.resolve_internal_duplicates(
            rows,
            threshold,
            topics=topics,
            urls=all_urls,
            client=client,
            max_attempts=max_attempts,
            cost_sink=cost_sink,
        )

        level_rows[level] = rows
        level_req.status = "GENERATED" if not remaining_dups else "GENERATED_WITH_DUPS"

    all_rows = []
    for level in constants.CAREER_LEVELS:
        if level in level_rows:
            all_rows.extend(level_rows[level])

    if not all_rows:
        job.status = constants.JobStatus.FAILED
        job.error_message = "No questions were generated."
        job.updated_at = datetime.utcnow()
        db.commit()
        return

    all_rows, final_status, repair_report = rework.final_global_duplicate_repair(
        all_rows,
        threshold,
        client=client,
        max_passes=config.get_max_final_duplicate_repair_passes(),
        max_attempts_per_row=config.get_max_final_rework_attempts_per_row(),
        max_rows_per_pass=config.get_max_global_rework_rows_per_pass(),
        min_improvement_delta=config.get_min_improvement_delta(),
        cost_sink=cost_sink,
    )

    all_rows = excel_exporter.order_and_title(all_rows)

    validation_errors = validators.validate_rows(
        all_rows,
        job.skill_name,
        job.ssid,
        topics,
        all_urls,
        expected_count=len(all_rows),
    )

    existing_qs = db.query(Question).filter_by(job_id=job_id).all()
    for q in existing_qs:
        db.delete(q)
    db.flush()

    for row in all_rows:
        dup_warning = None
        if final_status == constants.FINAL_MANUAL_REVIEW_REQUIRED:
            for pair in repair_report.get("unresolved_pairs", []):
                if row.get("question", "") in (pair.get("question1", ""), pair.get("question2", "")):
                    dup_warning = f"Possible duplicate (similarity {pair.get('similarity', 0):.3f})"
                    break

        q = Question(
            question_id=generate_id(),
            job_id=job_id,
            title=row.get("title"),
            ssid=row.get("ssid", ""),
            skill=row.get("skill", ""),
            topic=row.get("topic", ""),
            question_type=row.get("question_type", "QnA"),
            career_level=row.get("career_level", ""),
            complexity=row.get("complexity", ""),
            question=row.get("question", ""),
            answer=row.get("answer", ""),
            options=row.get("options", ""),
            reference_url=row.get("reference_url", ""),
            status=constants.QuestionStatus.DRAFT,
            duplicate_warning=dup_warning,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(q)

    try:
        xlsx_bytes = excel_exporter.to_xlsx_bytes(all_rows)
        xlsx_errors = excel_exporter.validate_workbook(
            xlsx_bytes, job.ssid, len(all_rows)
        )
        if not xlsx_errors:
            filename = constants.build_filename(job.skill_name, job.ssid)
            export = ExportFile(
                export_id=generate_id(),
                job_id=job_id,
                export_type=constants.ExportType.DRAFT,
                file_name=filename,
                file_bytes=xlsx_bytes,
                row_count=len(all_rows),
                sheet_name=constants.EXCEL_SHEET_NAME,
                status="READY",
                created_at=datetime.utcnow(),
            )
            db.add(export)
    except Exception:
        pass

    job.status = constants.JobStatus.GENERATED
    job.total_expected_questions = len(all_rows)
    job.updated_at = datetime.utcnow()

    if validation_errors:
        job.error_message = "; ".join(validation_errors[:5])

    db.commit()

    notification_service.notify_excel_ready(
        db,
        job_id=job_id,
        requestor_email=job.requestor_email,
    )


def build_approved_export(db, job_id: str) -> Optional[bytes]:
    """Generate approved Excel from all ACCEPTED questions. Returns None on failure."""
    job = db.query(Job).filter_by(job_id=job_id).first()
    if not job:
        return None

    questions = (
        db.query(Question)
        .filter_by(job_id=job_id, status=constants.QuestionStatus.ACCEPTED)
        .all()
    )
    if not questions:
        return None

    rows = [
        {
            "title": q.title,
            "ssid": q.ssid,
            "skill": q.skill,
            "topic": q.topic,
            "question_type": q.question_type,
            "career_level": q.career_level,
            "complexity": q.complexity,
            "question": q.question,
            "answer": q.answer,
            "options": q.options,
            "reference_url": q.reference_url,
        }
        for q in questions
    ]
    rows = excel_exporter.order_and_title(rows)

    try:
        xlsx_bytes = excel_exporter.to_xlsx_bytes(rows)
    except Exception:
        return None

    filename = constants.build_filename(job.skill_name, job.ssid)

    existing = (
        db.query(ExportFile)
        .filter_by(job_id=job_id, export_type=constants.ExportType.APPROVED)
        .first()
    )
    if existing:
        existing.file_bytes = xlsx_bytes
        existing.row_count = len(rows)
        existing.created_at = datetime.utcnow()
    else:
        export = ExportFile(
            export_id=generate_id(),
            job_id=job_id,
            export_type=constants.ExportType.APPROVED,
            file_name=filename,
            file_bytes=xlsx_bytes,
            row_count=len(rows),
            sheet_name=constants.EXCEL_SHEET_NAME,
            status="READY",
            created_at=datetime.utcnow(),
        )
        db.add(export)

    db.commit()
    return xlsx_bytes

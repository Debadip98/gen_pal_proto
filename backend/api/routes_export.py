"""Excel export download routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core import constants
from backend.db.models import ExportFile, Job, Question

router = APIRouter(tags=["export"])


@router.get("/jobs/{job_id}/export")
def download_export(
    job_id: str,
    type: str = Query("draft", description="draft or approved"),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter_by(job_id=job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    export_type = constants.ExportType.APPROVED if type.lower() == "approved" else constants.ExportType.DRAFT

    if export_type == constants.ExportType.APPROVED:
        from backend.pipeline.runner import build_approved_export
        xlsx_bytes = build_approved_export(db, job_id)
        if not xlsx_bytes:
            raise HTTPException(
                404,
                "Approved export not available — ensure all questions are accepted.",
            )
        filename = f"{job.skill_name}-{job.ssid}-approved.xlsx"
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    export = (
        db.query(ExportFile)
        .filter_by(job_id=job_id, export_type=constants.ExportType.DRAFT)
        .order_by(ExportFile.created_at.desc())
        .first()
    )

    if not export or not export.file_bytes:
        total_q = db.query(Question).filter_by(job_id=job_id).count()
        if total_q == 0:
            raise HTTPException(
                404,
                "No questions generated yet. Run generation first.",
            )
        from backend.services import excel_exporter
        from backend.core.security import generate_id
        from datetime import datetime

        questions = db.query(Question).filter_by(job_id=job_id).order_by(Question.title).all()
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
        xlsx_bytes = excel_exporter.to_xlsx_bytes(rows)

        new_export = ExportFile(
            export_id=generate_id(),
            job_id=job_id,
            export_type=constants.ExportType.DRAFT,
            file_name=f"{job.skill_name}-{job.ssid}.xlsx",
            file_bytes=xlsx_bytes,
            row_count=len(rows),
            sheet_name=constants.EXCEL_SHEET_NAME,
            status="READY",
            created_at=datetime.utcnow(),
        )
        db.add(new_export)
        db.commit()
        export = new_export

    pending_count = db.query(Question).filter(
        Question.job_id == job_id,
        Question.status.notin_([
            constants.QuestionStatus.ACCEPTED,
            constants.QuestionStatus.REJECTED,
        ]),
    ).count()

    headers = {
        "Content-Disposition": f'attachment; filename="{export.file_name}"',
    }
    if pending_count > 0:
        headers["X-Review-Warning"] = (
            f"{pending_count} question(s) still pending review. "
            "This is a draft export."
        )

    return Response(
        content=export.file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )

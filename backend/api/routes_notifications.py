"""Notification management routes for requestor dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.db.models import Job, Notification

router = APIRouter(tags=["notifications"])


def _get_job_by_token(job_token: str, db: Session) -> Job:
    job = db.query(Job).filter_by(job_token=job_token).first()
    if not job:
        raise HTTPException(404, "Job not found — invalid token")
    return job


@router.get("/dashboard/{job_token}/notifications")
def list_notifications(job_token: str, db: Session = Depends(get_db)):
    job = _get_job_by_token(job_token, db)
    notifications = (
        db.query(Notification)
        .filter_by(job_id=job.job_id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    unread_count = sum(1 for n in notifications if not n.is_read)
    return {
        "notifications": [
            {
                "notification_id": n.notification_id,
                "job_id": n.job_id,
                "question_id": n.question_id,
                "recipient_email": n.recipient_email,
                "actor": n.actor,
                "action_type": n.action_type,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifications
        ],
        "unread_count": unread_count,
    }


@router.post("/dashboard/{job_token}/notifications/{notification_id}/read")
def mark_read(
    job_token: str,
    notification_id: str,
    db: Session = Depends(get_db),
):
    job = _get_job_by_token(job_token, db)
    n = db.query(Notification).filter_by(
        notification_id=notification_id, job_id=job.job_id
    ).first()
    if not n:
        raise HTTPException(404, "Notification not found")
    n.is_read = True
    db.commit()
    return {"notification_id": notification_id, "is_read": True}


@router.post("/dashboard/{job_token}/notifications/read-all")
def mark_all_read(job_token: str, db: Session = Depends(get_db)):
    job = _get_job_by_token(job_token, db)
    db.query(Notification).filter_by(job_id=job.job_id, is_read=False).update(
        {"is_read": True}
    )
    db.commit()
    return {"marked_read": True}

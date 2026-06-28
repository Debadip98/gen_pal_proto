"""Create and manage notification rows for GenPal jobs."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend.core.security import generate_id
from backend.db.models import Notification


def create_notification(
    db,
    job_id: str,
    recipient_email: str,
    action_type: str,
    message: str,
    *,
    question_id: Optional[str] = None,
    actor: Optional[str] = None,
) -> Notification:
    notification = Notification(
        notification_id=generate_id(),
        job_id=job_id,
        question_id=question_id,
        recipient_email=recipient_email,
        actor=actor,
        action_type=action_type,
        message=message,
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def notify_question_accepted(
    db,
    job_id: str,
    requestor_email: str,
    question_id: str,
    question_title: int,
    sme_email: str,
) -> None:
    create_notification(
        db,
        job_id=job_id,
        recipient_email=requestor_email,
        action_type="QUESTION_ACCEPTED",
        message=f"Question #{question_title} was accepted by the SME reviewer.",
        question_id=question_id,
        actor=sme_email,
    )


def notify_question_rejected(
    db,
    job_id: str,
    requestor_email: str,
    question_id: str,
    question_title: int,
    sme_email: str,
    comment: str = "",
) -> None:
    msg = f"Question #{question_title} was rejected by the SME reviewer."
    if comment:
        msg += f" Reason: {comment[:120]}"
    create_notification(
        db,
        job_id=job_id,
        recipient_email=requestor_email,
        action_type="QUESTION_REJECTED",
        message=msg,
        question_id=question_id,
        actor=sme_email,
    )


def notify_question_regenerated(
    db,
    job_id: str,
    requestor_email: str,
    question_id: str,
    question_title: int,
    sme_email: str,
) -> None:
    create_notification(
        db,
        job_id=job_id,
        recipient_email=requestor_email,
        action_type="QUESTION_REGENERATED",
        message=f"Question #{question_title} was sent for regeneration by the SME reviewer.",
        question_id=question_id,
        actor=sme_email,
    )


def notify_version_accepted(
    db,
    job_id: str,
    requestor_email: str,
    question_id: str,
    question_title: int,
    sme_email: str,
) -> None:
    create_notification(
        db,
        job_id=job_id,
        recipient_email=requestor_email,
        action_type="VERSION_ACCEPTED",
        message=f"SME accepted the regenerated version of Question #{question_title}.",
        question_id=question_id,
        actor=sme_email,
    )


def notify_version_rejected(
    db,
    job_id: str,
    requestor_email: str,
    question_id: str,
    question_title: int,
    sme_email: str,
) -> None:
    create_notification(
        db,
        job_id=job_id,
        recipient_email=requestor_email,
        action_type="VERSION_REJECTED",
        message=f"SME rejected the regenerated version of Question #{question_title}. Original retained.",
        question_id=question_id,
        actor=sme_email,
    )


def notify_review_sent(
    db,
    job_id: str,
    requestor_email: str,
    sme_email: str,
) -> None:
    create_notification(
        db,
        job_id=job_id,
        recipient_email=requestor_email,
        action_type="REVIEW_SENT",
        message=f"SME review invitation sent to {sme_email}.",
        actor="system",
    )


def notify_review_complete(
    db,
    job_id: str,
    requestor_email: str,
    sme_email: str,
) -> None:
    create_notification(
        db,
        job_id=job_id,
        recipient_email=requestor_email,
        action_type="REVIEW_COMPLETE",
        message="All questions have been reviewed. You can now download the approved Excel.",
        actor=sme_email,
    )


def notify_excel_ready(
    db,
    job_id: str,
    requestor_email: str,
) -> None:
    create_notification(
        db,
        job_id=job_id,
        recipient_email=requestor_email,
        action_type="EXCEL_READY",
        message="Your question bank Excel is ready for download.",
        actor="system",
    )

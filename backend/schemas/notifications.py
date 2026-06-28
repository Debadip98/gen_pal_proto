"""Pydantic schemas for notifications."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificationSchema(BaseModel):
    notification_id: str
    job_id: str
    question_id: Optional[str]
    recipient_email: str
    actor: Optional[str]
    action_type: str
    message: str
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    notifications: list[NotificationSchema]
    unread_count: int

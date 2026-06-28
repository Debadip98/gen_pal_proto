"""Documentation discovery and selection routes."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.db.models import DocumentSource, Job
from backend.schemas.docs import (
    DiscoverDocsResponse,
    DiscoveredDoc,
    SelectDocsRequest,
    SelectDocsResponse,
)
from backend.services import docs_discovery

router = APIRouter(tags=["docs"])


@router.post("/jobs/{job_id}/discover-docs", response_model=DiscoverDocsResponse)
def discover_docs(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter_by(job_id=job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    result = docs_discovery.discover_docs_for_skill(db, job_id, job.skill_name)

    discovered = [
        DiscoveredDoc(
            source_id=d["source_id"],
            source_name=d.get("source_name"),
            source_url=d.get("source_url"),
            summary=d.get("summary"),
            selected=False,
        )
        for d in result.get("discovered", [])
    ]
    return DiscoverDocsResponse(
        discovered=discovered,
        warning=result.get("warning"),
    )


@router.post("/jobs/{job_id}/select-docs", response_model=SelectDocsResponse)
def select_docs(
    job_id: str,
    req: SelectDocsRequest,
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter_by(job_id=job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    all_sources = db.query(DocumentSource).filter_by(job_id=job_id).all()
    for source in all_sources:
        source.selected = source.source_id in req.selected_source_ids
    db.flush()

    selected_urls = [
        s.source_url
        for s in all_sources
        if s.selected and s.source_url
    ]

    manual_urls = json.loads(job.manual_urls_json or "[]")
    all_urls = list(dict.fromkeys(selected_urls + manual_urls))
    job.selected_urls_json = json.dumps(all_urls)
    job.updated_at = datetime.utcnow()
    db.commit()

    return SelectDocsResponse(
        selected_count=len(selected_urls),
        selected_urls=all_urls,
    )

"""Documentation discovery service for GenPal.

Uses OpenAI web search (if enabled) or returns a warning when disabled.
Stores discovered URLs as DocumentSource rows.
"""

from __future__ import annotations

import json
from typing import Optional

from backend.core import config
from backend.core.security import generate_id
from backend.db.models import DocumentSource


_DISCOVERY_SYSTEM = (
    "You are a documentation researcher. Your job is to find the latest "
    "official documentation URLs for the given technical skill. "
    "Return only official or widely-trusted sources. "
    "Return JSON only — no other text."
)


def discover_docs_for_skill(
    db,
    job_id: str,
    skill_name: str,
    *,
    client=None,
    cost_sink=None,
) -> dict:
    """Find latest documentation for a skill name and store as DocumentSource rows.

    Returns:
        {discovered: [{source_id, source_name, source_url, summary}], warning: str|None}
    """
    if not config.is_openai_web_search_enabled():
        return {
            "discovered": [],
            "warning": (
                "Web search is disabled. Set ENABLE_OPENAI_WEB_SEARCH=true in your "
                ".env to auto-discover documentation. You can still add URLs manually."
            ),
        }

    if config.use_mock_data():
        return _mock_discover(db, job_id, skill_name)

    if client is None:
        from backend.services.generator import make_client
        client = make_client()

    try:
        response = client.chat.completions.create(
            model=config.get_openai_generation_model(),
            messages=[
                {"role": "system", "content": _DISCOVERY_SYSTEM},
                {
                    "role": "user",
                    "content": (
                        f"Find the 3-5 most current official documentation pages for "
                        f"the technical skill: {skill_name}.\n\n"
                        "For each URL provide:\n"
                        "- source_name: short display name\n"
                        "- source_url: full HTTPS URL\n"
                        "- summary: 1-2 sentence description of the page content\n\n"
                        "Return JSON:\n"
                        '{"sources": [{"source_name": "...", "source_url": "...", "summary": "..."}]}'
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        usage = getattr(response, "usage", None)
        if cost_sink and usage:
            cost_sink(config.get_openai_generation_model(), "docs_discovery", usage)
        content = response.choices[0].message.content or "{}"
        payload = json.loads(content)
        raw_sources = payload.get("sources", [])
    except Exception:
        return {
            "discovered": [],
            "warning": "Documentation discovery failed. Please add URLs manually.",
        }

    discovered = []
    for item in raw_sources:
        url = item.get("source_url", "").strip()
        name = item.get("source_name", url)
        summary = item.get("summary", "")
        if not url:
            continue
        source = DocumentSource(
            source_id=generate_id(),
            job_id=job_id,
            source_type="DISCOVERED_URL",
            source_name=name,
            source_url=url,
            summary=summary,
            selected=False,
        )
        db.add(source)
        discovered.append({
            "source_id": source.source_id,
            "source_name": name,
            "source_url": url,
            "summary": summary,
        })

    db.commit()
    return {"discovered": discovered, "warning": None}


def _mock_discover(db, job_id: str, skill_name: str) -> dict:
    mock_sources = [
        {
            "source_name": f"{skill_name} Official Docs",
            "source_url": f"https://docs.example.com/{skill_name.lower().replace(' ', '-')}",
            "summary": f"Official documentation for {skill_name}.",
        },
        {
            "source_name": f"{skill_name} Best Practices",
            "source_url": f"https://learn.example.com/{skill_name.lower().replace(' ', '-')}/best-practices",
            "summary": f"Best practices guide for {skill_name} in enterprise environments.",
        },
    ]
    discovered = []
    for item in mock_sources:
        source = DocumentSource(
            source_id=generate_id(),
            job_id=job_id,
            source_type="DISCOVERED_URL",
            source_name=item["source_name"],
            source_url=item["source_url"],
            summary=item["summary"],
            selected=False,
        )
        db.add(source)
        discovered.append({
            "source_id": source.source_id,
            "source_name": item["source_name"],
            "source_url": item["source_url"],
            "summary": item["summary"],
        })
    db.commit()
    return {"discovered": discovered, "warning": None}


def add_manual_urls(db, job_id: str, urls: list[str]) -> list[dict]:
    """Store manual URLs as MANUAL_URL DocumentSource rows."""
    added = []
    for url in urls:
        url = url.strip()
        if not url:
            continue
        existing = db.query(DocumentSource).filter_by(job_id=job_id, source_url=url).first()
        if existing:
            continue
        source = DocumentSource(
            source_id=generate_id(),
            job_id=job_id,
            source_type="MANUAL_URL",
            source_name=url,
            source_url=url,
            selected=True,
        )
        db.add(source)
        added.append({"source_id": source.source_id, "source_url": url})
    db.commit()
    return added

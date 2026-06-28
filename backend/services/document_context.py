"""Document context retrieval for SME regeneration.

Fetches relevant text from document sources to include as context
when regenerating a question based on SME feedback.
"""

from __future__ import annotations

from backend.db.models import DocumentSource


def get_document_context_for_job(db, job_id: str, max_chars: int = 3000) -> str:
    """Return combined text from selected document sources for a job."""
    sources = (
        db.query(DocumentSource)
        .filter_by(job_id=job_id, selected=True)
        .all()
    )
    parts = []
    total = 0
    for source in sources:
        text = (source.source_text or source.summary or "").strip()
        if text and total < max_chars:
            excerpt = text[: max_chars - total]
            parts.append(f"[{source.source_name or source.source_url}]\n{excerpt}")
            total += len(excerpt)
    return "\n\n".join(parts)


def get_url_text(url: str, max_chars: int = 2000) -> str:
    """Fetch plain text from a URL for document context (best-effort)."""
    try:
        import urllib.request

        req = urllib.request.Request(
            url,
            headers={"User-Agent": "GenPal/1.0 (question bank review bot)"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            raw = response.read().decode("utf-8", errors="ignore")

        try:
            from html.parser import HTMLParser

            class _TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self._text: list[str] = []
                    self._skip = False

                def handle_starttag(self, tag, attrs):
                    if tag in ("script", "style", "nav", "footer"):
                        self._skip = True

                def handle_endtag(self, tag):
                    if tag in ("script", "style", "nav", "footer"):
                        self._skip = False

                def handle_data(self, data):
                    if not self._skip:
                        self._text.append(data)

                def get_text(self):
                    return " ".join(" ".join(self._text).split())

            extractor = _TextExtractor()
            extractor.feed(raw)
            text = extractor.get_text()
        except Exception:
            text = raw

        return text[:max_chars]
    except Exception:
        return ""

"""Pydantic schemas for documentation discovery."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class DiscoveredDoc(BaseModel):
    source_id: str
    source_name: Optional[str]
    source_url: Optional[str]
    summary: Optional[str]
    selected: bool = False


class DiscoverDocsResponse(BaseModel):
    discovered: list[DiscoveredDoc]
    warning: Optional[str]


class SelectDocsRequest(BaseModel):
    selected_source_ids: list[str]


class SelectDocsResponse(BaseModel):
    selected_count: int
    selected_urls: list[str]

"""
Pydantic v2 schemas for Project API endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


# ── Request schemas ────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    """Payload to register a new project for testing."""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    url: str = Field(..., description="Target web application URL")
    description: Optional[str] = Field(None, max_length=1000)
    headed: bool = Field(False, description="Run browser in visible headed mode")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v.rstrip("/")


class ProjectUpdate(BaseModel):
    """Partial update payload for an existing project."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None


# ── Response schemas ───────────────────────────────────────────────────────

class PageElement(BaseModel):
    """Represents a single interactive page element."""

    selector: str
    element_type: str          # button | input | link | form | select | etc.
    text: Optional[str] = None
    placeholder: Optional[str] = None
    name: Optional[str] = None
    href: Optional[str] = None
    is_visible: bool = True
    attributes: Dict[str, Any] = Field(default_factory=dict)


class PageInfo(BaseModel):
    """Metadata about a discovered page."""

    url: str
    title: str
    page_type: str             # login | register | product | cart | home | etc.
    elements: List[PageElement] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    forms: List[Dict[str, Any]] = Field(default_factory=list)
    depth: int = 0


class SiteMapResponse(BaseModel):
    """Structured site map returned after discovery."""

    root_url: str
    total_pages: int
    pages: List[PageInfo] = Field(default_factory=list)
    navigation_tree: Dict[str, Any] = Field(default_factory=dict)
    discovered_at: datetime


class PageElementsResponse(BaseModel):
    """All interactive elements grouped by page."""

    project_id: uuid.UUID
    pages: List[PageInfo] = Field(default_factory=list)
    total_elements: int = 0


class ProjectResponse(BaseModel):
    """Full project representation returned to API consumers."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    url: str
    description: Optional[str] = None
    status: str
    site_map: Optional[Dict[str, Any]] = None
    page_elements: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Paginated list of projects."""

    items: List[ProjectResponse]
    total: int
    page: int = 1
    page_size: int = 20

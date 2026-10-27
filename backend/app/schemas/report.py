"""
Pydantic v2 schemas for report generation and retrieval.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TestSummary(BaseModel):
    """High-level statistics for a test run."""

    run_id: uuid.UUID
    project_id: uuid.UUID
    project_name: str
    status: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    pass_rate: float
    avg_duration_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[float] = None

    # Category breakdown
    by_category: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="Pass/fail counts per test category",
    )
    # Severity breakdown
    defects_by_severity: Dict[str, int] = Field(default_factory=dict)
    top_failures: List[Dict[str, Any]] = Field(default_factory=list)


class FailureAnalysisResponse(BaseModel):
    """AI-generated failure analysis for a specific result."""

    result_id: uuid.UUID
    test_name: str
    error_message: str
    root_cause_category: str
    root_cause_explanation: str
    suggested_fix: str
    confidence: float = Field(ge=0.0, le=1.0)
    affected_selector: Optional[str] = None
    is_flaky: bool = False
    similar_failures: List[str] = Field(default_factory=list)


class ReportRequest(BaseModel):
    """Payload to request a specific report format."""

    run_id: uuid.UUID
    format: str = Field("pdf", description="pdf | excel | allure | json")
    include_screenshots: bool = True
    include_videos: bool = False
    filters: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    """Response after report generation."""

    run_id: uuid.UUID
    format: str
    file_path: str
    download_url: str
    file_size_bytes: int
    generated_at: datetime
    expires_at: Optional[datetime] = None

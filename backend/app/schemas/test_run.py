"""
Pydantic v2 schemas for TestRun, TestResult, and Defect API endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Defect schemas ─────────────────────────────────────────────────────────

class DefectResponse(BaseModel):
    """AI-generated defect linked to a failed test result."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    result_id: uuid.UUID
    title: str
    description: Optional[str] = None
    root_cause: Optional[str] = None
    root_cause_category: Optional[str] = None
    suggested_fix: Optional[str] = None
    severity: str
    visual_diff: Optional[Dict[str, Any]] = None
    diff_image_path: Optional[str] = None
    created_at: datetime


# ── TestResult schemas ─────────────────────────────────────────────────────

class TestResultResponse(BaseModel):
    """Single test execution result."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    run_id: uuid.UUID
    test_case_id: Optional[uuid.UUID] = None
    test_name: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    screenshot_path: Optional[str] = None
    video_path: Optional[str] = None
    log_path: Optional[str] = None
    failure_analysis: Optional[Dict[str, Any]] = None
    duration_seconds: Optional[float] = None
    attempt_number: int = 1
    executed_at: datetime
    defects: List[DefectResponse] = Field(default_factory=list)


# ── TestRun schemas ────────────────────────────────────────────────────────

class TestRunCreate(BaseModel):
    """Payload to trigger a new test run for a project."""

    project_id: uuid.UUID
    test_case_ids: Optional[List[uuid.UUID]] = Field(
        None, description="Specific test cases to run; None means run all."
    )
    parallel: bool = Field(False, description="Run tests in parallel workers.")
    max_workers: int = Field(4, ge=1, le=16)
    headed: bool = Field(False, description="Run browser in visible headed mode")


class TestRunUpdate(BaseModel):
    """Internal update payload for a test run."""

    status: Optional[str] = None
    total_tests: Optional[int] = None
    passed: Optional[int] = None
    failed: Optional[int] = None
    skipped: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    report_path: Optional[str] = None
    logs_path: Optional[str] = None


class TestRunResponse(BaseModel):
    """Full test run representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    status: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    report_path: Optional[str] = None
    logs_path: Optional[str] = None
    project_name: Optional[str] = None

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return round(self.passed / self.total_tests * 100, 2)


class TestRunDetailResponse(TestRunResponse):
    """Test run with embedded result list."""

    results: List[TestResultResponse] = Field(default_factory=list)


class PaginatedResultsResponse(BaseModel):
    """Paginated test results for a run."""

    items: List[TestResultResponse]
    total: int
    page: int
    page_size: int
    run_id: uuid.UUID

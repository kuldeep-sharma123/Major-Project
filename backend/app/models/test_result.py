"""
TestResult SQLAlchemy ORM model.
Stores individual test execution outcomes within a test run.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.defect import Defect
    from app.models.test_case import TestCase
    from app.models.test_run import TestRun


class TestResult(Base):
    """Individual test execution outcome linked to a run and test case."""

    __tablename__ = "test_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_case_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_cases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Outcome: passed | failed | skipped | error
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Failure details
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Artefact paths
    screenshot_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    log_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI failure analysis result stored as JSONB
    failure_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Timing
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Retry tracking
    attempt_number: Mapped[int] = mapped_column(default=1, nullable=False)

    # Relationships
    run: Mapped["TestRun"] = relationship("TestRun", back_populates="results")
    test_case: Mapped["TestCase | None"] = relationship("TestCase")
    defects: Mapped[list["Defect"]] = relationship(
        "Defect", back_populates="result", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TestResult id={self.id} status={self.status!r} run={self.run_id}>"

"""
TestRun SQLAlchemy ORM model.
Tracks a single execution pipeline run for a project.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.test_result import TestResult


class TestRun(Base):
    """Represents one full test execution run for a project."""

    __tablename__ = "test_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Lifecycle status: pending | running | completed | failed
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )

    # Aggregate counters
    total_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Artefact paths
    report_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    logs_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="test_runs")
    results: Mapped[List["TestResult"]] = relationship(
        "TestResult", back_populates="run", cascade="all, delete-orphan"
    )
    test_results = synonym("results")

    def __repr__(self) -> str:
        return (
            f"<TestRun id={self.id} project={self.project_id} status={self.status!r}>"
        )

"""
Defect SQLAlchemy ORM model.
AI-generated defect records from failed test result analysis.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.test_result import TestResult


class Defect(Base):
    """
    AI-generated defect linked to a failed TestResult.

    Severities: critical | high | medium | low | info
    """

    __tablename__ = "defects"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    result_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Root-cause analysis
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause_category: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # locator|timeout|network|assertion|logic|environment

    # Suggested fix from AI
    suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Severity: critical | high | medium | low | info
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")

    # Visual diff data (Pillow comparison results)
    visual_diff: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Visual diff image path
    diff_image_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    result: Mapped["TestResult"] = relationship("TestResult", back_populates="defects")

    def __repr__(self) -> str:
        return f"<Defect id={self.id} severity={self.severity!r} title={self.title!r}>"

"""
TestCase SQLAlchemy ORM model.
Stores AI-generated test cases with full metadata and execution steps.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class TestCase(Base):
    """
    AI-generated test case associated with a project page.

    Categories: functional | ui | accessibility | security | performance
    Test Types: positive | negative | boundary | e2e
    Priorities: critical | high | medium | low
    """

    __tablename__ = "test_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="functional"
    )  # functional|ui|accessibility|security|performance
    test_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="positive"
    )  # positive|negative|boundary|e2e

    # Execution blueprint
    steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    expected_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    preconditions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Meta
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    page_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status: draft | ready | obsolete
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")

    # Generated script path
    script_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="test_cases")

    def __repr__(self) -> str:
        return f"<TestCase id={self.id} name={self.name!r} category={self.category!r}>"

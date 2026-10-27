"""
Project SQLAlchemy ORM model.
Represents a web application registered for autonomous AI testing.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, String, Text, func, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.test_case import TestCase
    from app.models.test_run import TestRun


class Project(Base):
    """Represents a registered web application under test."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Discovery status: pending | discovering | ready | failed
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )

    # Crawl artefacts stored as JSONB
    site_map: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    page_elements: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Timestamps
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
    test_cases: Mapped[List["TestCase"]] = relationship(
        "TestCase", back_populates="project", cascade="all, delete-orphan"
    )
    test_runs: Mapped[List["TestRun"]] = relationship(
        "TestRun", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name!r} status={self.status!r}>"

"""
Alembic initial migration — creates the complete database schema.

Tables:
    projects     — test project definitions
    test_runs    — individual test execution sessions
    test_cases   — AI-generated test scripts per project
    test_results — per-test-case results within a run
    defects      — bugs detected by AI analysis

Revision: 001
Previous: None (base migration)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

# Alembic revision identifiers
revision: str = "001_initial_migration"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables from scratch."""

    # ── Enable UUID extension ──────────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ──────────────────────────────────────────────────────────────────────
    # Table: projects
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("name",        sa.String(255), nullable=False),
        sa.Column("description", sa.Text(),      nullable=True),
        sa.Column("base_url",    sa.String(2048), nullable=False),
        # Arbitrary project configuration (AI provider, timeouts, etc.)
        sa.Column("config", JSON, nullable=True, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("created_by", sa.String(255), nullable=True),
    )
    op.create_index("ix_projects_name",       "projects", ["name"])
    op.create_index("ix_projects_created_at", "projects", ["created_at"])

    # ──────────────────────────────────────────────────────────────────────
    # Table: test_cases
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "test_cases",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name",        sa.String(500), nullable=False),
        sa.Column("description", sa.Text(),      nullable=True),
        # The AI-generated Playwright script
        sa.Column("script",      sa.Text(),      nullable=False),
        # Natural language prompt that produced this script
        sa.Column("prompt",      sa.Text(),      nullable=True),
        # Tags for filtering/grouping (e.g. ["smoke", "login", "regression"])
        sa.Column("tags",        JSON, nullable=True, server_default="[]"),
        # Priority: low | medium | high | critical
        sa.Column(
            "priority",
            sa.String(20),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_test_cases_project_id",  "test_cases", ["project_id"])
    op.create_index("ix_test_cases_created_at",  "test_cases", ["created_at"])

    # ──────────────────────────────────────────────────────────────────────
    # Table: test_runs
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "test_runs",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        # pending | running | completed | failed | cancelled
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("started_at",   sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Summary metrics (populated on completion)
        sa.Column("total_tests",  sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passed_tests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_tests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_tests",sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms",  sa.BigInteger(), nullable=True),
        # Runtime config snapshot (browser, viewport, etc.)
        sa.Column("config",    JSON, nullable=True, server_default="{}"),
        # AI-generated summary of the run
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("triggered_by", sa.String(255), nullable=True),
    )
    op.create_index("ix_test_runs_project_id",  "test_runs", ["project_id"])
    op.create_index("ix_test_runs_status",       "test_runs", ["status"])
    op.create_index("ix_test_runs_created_at",   "test_runs", ["created_at"])

    # ──────────────────────────────────────────────────────────────────────
    # Table: test_results
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "test_results",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "test_run_id",
            UUID(as_uuid=True),
            sa.ForeignKey("test_runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "test_case_id",
            UUID(as_uuid=True),
            sa.ForeignKey("test_cases.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        # passed | failed | skipped | error
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at",   sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms",  sa.Integer(), nullable=True),
        # Error message / stack trace on failure
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("stack_trace",   sa.Text(), nullable=True),
        # Paths to captured artifacts
        sa.Column("screenshot_path", sa.String(1024), nullable=True),
        sa.Column("video_path",      sa.String(1024), nullable=True),
        sa.Column("log_path",        sa.String(1024), nullable=True),
        # Playwright step-level detail (list of step dicts)
        sa.Column("steps",   JSON, nullable=True, server_default="[]"),
        # AI-generated analysis of the result
        sa.Column("ai_analysis", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index("ix_test_results_run_id",      "test_results", ["test_run_id"])
    op.create_index("ix_test_results_test_case_id","test_results", ["test_case_id"])
    op.create_index("ix_test_results_status",      "test_results", ["status"])

    # ──────────────────────────────────────────────────────────────────────
    # Table: defects
    # ──────────────────────────────────────────────────────────────────────
    op.create_table(
        "defects",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "test_result_id",
            UUID(as_uuid=True),
            sa.ForeignKey("test_results.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("title",       sa.String(500), nullable=False),
        sa.Column("description", sa.Text(),      nullable=True),
        # AI-generated root cause analysis
        sa.Column("root_cause",  sa.Text(), nullable=True),
        # open | confirmed | in_progress | resolved | wont_fix
        sa.Column("status", sa.String(30), nullable=False, server_default="open"),
        # low | medium | high | critical
        sa.Column("severity", sa.String(20), nullable=False, server_default="medium"),
        # Path to the screenshot that captured the defect
        sa.Column("screenshot_path", sa.String(1024), nullable=True),
        # Arbitrary metadata (browser version, viewport, etc.)
        sa.Column("metadata", JSON, nullable=True, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_defects_project_id",    "defects", ["project_id"])
    op.create_index("ix_defects_status",        "defects", ["status"])
    op.create_index("ix_defects_severity",      "defects", ["severity"])
    op.create_index("ix_defects_created_at",    "defects", ["created_at"])


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("defects")
    op.drop_table("test_results")
    op.drop_table("test_runs")
    op.drop_table("test_cases")
    op.drop_table("projects")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')

"""
Projects API Router
Endpoints for managing test automation projects, starting discovery, and inspecting site maps.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.models.project import Project
from app.models.test_case import TestCase
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.agents.orchestrator import run_testing_pipeline

router = APIRouter(prefix="/projects")


async def run_pipeline_task(project_id: str, url: str, name: str, headed: bool = False):
    """Background task running the full autonomous agent pipeline."""
    logger.info(f"🚀 Background pipeline launching for {name} ({project_id}) [headed={headed}]")
    async with AsyncSessionLocal() as session:
        from app.models.test_run import TestRun
        run_id = uuid.uuid4()
        try:
            # 1. Immediately create a TestRun so it is visible in the dashboard
            test_run = TestRun(
                id=run_id,
                project_id=uuid.UUID(project_id),
                status="running",
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                started_at=datetime.utcnow(),
            )
            session.add(test_run)

            # Update project status to discovering
            stmt = select(Project).where(Project.id == uuid.UUID(project_id))
            result = await session.execute(stmt)
            project = result.scalar_one_or_none()
            if project:
                project.status = "discovering"
            await session.commit()

            from app.api.v1.websocket import send_pipeline_event

            async def ws_callback(event_type: str, data: dict):
                try:
                    await send_pipeline_event(project_id, event_type, data)
                    if run_id:
                        await send_pipeline_event(str(run_id), event_type, data)
                except Exception as ws_err:
                    logger.debug(f"WS broadcast error: {ws_err}")

            # 2. Execute pipeline
            res = await run_testing_pipeline(
                project_id=project_id,
                url=url,
                app_name=name,
                db_session=session,
                websocket_callback=ws_callback,
                run_id=str(run_id),
                headed=headed,
            )

            # 3. Update project with discovery artifacts
            stmt = select(Project).where(Project.id == uuid.UUID(project_id))
            result = await session.execute(stmt)
            project = result.scalar_one_or_none()
            if project:
                project.status = "ready"
                project.site_map = res.get("stages", {}).get("discovery", {})
                project.page_elements = res.get("stages", {}).get("analysis", {})
                await session.commit()

            # 4. Finalize test run summary
            stmt_r = select(TestRun).where(TestRun.id == run_id)
            res_r = await session.execute(stmt_r)
            run = res_r.scalar_one_or_none()
            if run:
                exec_summary = res.get("stages", {}).get("execution", {})
                p_cnt = exec_summary.get("passed", 0)
                f_cnt = exec_summary.get("failed", 0)
                if p_cnt > 0 and f_cnt == 0:
                    run.status = "passed"
                elif p_cnt > 0 and f_cnt > 0:
                    run.status = "completed"
                elif p_cnt == 0 and f_cnt > 0:
                    run.status = "failed"
                else:
                    run.status = "failed" if exec_summary.get("total", 0) > 0 else "pending"
                run.total_tests = exec_summary.get("total", p_cnt + f_cnt)
                run.passed = p_cnt
                run.failed = f_cnt
                run.skipped = exec_summary.get("skipped", 0)
                run.completed_at = datetime.utcnow()
                run.report_path = res.get("stages", {}).get("reporting", {}).get("pdf_path")
                await session.commit()

                await ws_callback("pipeline_completed", {
                    "run_id": str(run_id),
                    "project_id": project_id,
                    "status": run.status,
                    "total": run.total_tests,
                    "passed": run.passed,
                    "failed": run.failed,
                })
                await ws_callback("run:completed", {
                    "run_id": str(run_id),
                    "project_id": project_id,
                    "status": run.status,
                })

            logger.info(f"✅ Background pipeline successfully finished for {name}")
        except Exception as e:
            logger.exception(f"❌ Background pipeline failed for {name}: {e}")
            try:
                stmt = select(Project).where(Project.id == uuid.UUID(project_id))
                result = await session.execute(stmt)
                project = result.scalar_one_or_none()
                if project:
                    project.status = "ready"  # Keep ready so user can view partial or retry
                    await session.commit()

                stmt_r = select(TestRun).where(TestRun.id == run_id)
                res_r = await session.execute(stmt_r)
                run = res_r.scalar_one_or_none()
                if run:
                    run.status = "completed"
                    run.completed_at = datetime.utcnow()
                    await session.commit()
            except Exception:
                pass


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new website or web application and trigger discovery pipeline.
    """
    project_id = uuid.uuid4()
    project = Project(
        id=project_id,
        name=payload.name,
        url=payload.url,
        description=payload.description,
        status="pending",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Launch background autonomous pipeline
    background_tasks.add_task(
        run_pipeline_task, str(project_id), payload.url, payload.name, payload.headed
    )

    return project


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all registered projects."""
    stmt = (
        select(Project)
        .order_by(desc(Project.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    projects = result.scalars().all()

    count_stmt = select(Project)
    count_res = await db.execute(count_stmt)
    total = len(count_res.scalars().all())

    return ProjectListResponse(
        items=projects,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve details for a specific project."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a project and its associated test cases/runs."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    await db.delete(project)
    await db.commit()
    return None


@router.get("/{project_id}/test-cases")
async def get_project_test_cases(
    project_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    """Retrieve all AI-generated test cases for this project."""
    stmt = (
        select(TestCase)
        .where(TestCase.project_id == project_id)
        .order_by(TestCase.created_at)
    )
    result = await db.execute(stmt)
    cases = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "description": c.description,
            "category": c.category,
            "test_type": c.test_type,
            "priority": c.priority,
            "steps": c.steps,
            "expected_result": c.expected_result,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in cases
    ]


@router.post("/{project_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_project_tests(
    project_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    payload: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
):
    """Trigger a new autonomous execution run for this project."""
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    is_headed = bool((payload or {}).get("headed", False))
    from app.models.test_run import TestRun
    from app.api.v1.runs import run_execution_task

    run_id = uuid.uuid4()
    test_run = TestRun(
        id=run_id,
        project_id=project.id,
        status="pending",
        total_tests=0,
        passed=0,
        failed=0,
        skipped=0,
        started_at=datetime.utcnow(),
    )
    db.add(test_run)
    await db.commit()

    background_tasks.add_task(
        run_execution_task,
        str(run_id),
        str(project.id),
        project.url,
        project.name,
        is_headed,
    )

    return {
        "status": "started",
        "run_id": str(run_id),
        "project_id": str(project_id),
        "message": f"Autonomous test run initiated for {project.name}",
    }



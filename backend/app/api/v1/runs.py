"""
Test Runs API Router
Endpoints to trigger test executions, query runs, view results, and retry failures.
"""
from __future__ import annotations

import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db, AsyncSessionLocal
from app.models.project import Project
from app.models.test_run import TestRun
from app.models.test_result import TestResult
from app.schemas.test_run import (
    PaginatedResultsResponse,
    TestResultResponse,
    TestRunCreate,
    TestRunDetailResponse,
    TestRunResponse,
)
from app.agents.orchestrator import run_testing_pipeline

router = APIRouter(prefix="/runs")


async def run_execution_task(run_id: str, project_id: str, project_url: str, project_name: str, headed: bool = False):
    """Executes testing run asynchronously."""
    async with AsyncSessionLocal() as session:
        try:
            # Mark running
            stmt = select(TestRun).where(TestRun.id == uuid.UUID(run_id))
            res = await session.execute(stmt)
            run = res.scalar_one_or_none()
            if run:
                run.status = "running"
                run.started_at = datetime.utcnow()
                await session.commit()

            from app.api.v1.websocket import send_pipeline_event

            async def ws_callback(event_type: str, data: dict):
                try:
                    await send_pipeline_event(project_id, event_type, data)
                    await send_pipeline_event(str(run_id), event_type, data)
                except Exception as ws_err:
                    logger.debug(f"WS broadcast error: {ws_err}")

            result = await run_testing_pipeline(
                project_id=project_id,
                url=project_url,
                app_name=project_name,
                db_session=session,
                websocket_callback=ws_callback,
                run_id=run_id,
                headed=headed,
            )

            # Update run summary
            stmt = select(TestRun).where(TestRun.id == uuid.UUID(run_id))
            res = await session.execute(stmt)
            run = res.scalar_one_or_none()
            if run:
                exec_summary = result.get("stages", {}).get("execution", {})
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
                run.report_path = result.get("stages", {}).get("reporting", {}).get("pdf_path")
                await session.commit()

                # Broadcast final completed event to frontend
                await ws_callback("pipeline_completed", {
                    "run_id": run_id,
                    "project_id": project_id,
                    "status": run.status,
                    "total": run.total_tests,
                    "passed": run.passed,
                    "failed": run.failed,
                })
                await ws_callback("run:completed", {
                    "run_id": run_id,
                    "project_id": project_id,
                    "status": run.status,
                })

        except Exception as e:
            logger.exception(f"Run {run_id} failed: {e}")
            stmt = select(TestRun).where(TestRun.id == uuid.UUID(run_id))
            res = await session.execute(stmt)
            run = res.scalar_one_or_none()
            if run:
                run.status = "failed"
                run.completed_at = datetime.utcnow()
                await session.commit()


@router.post("", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def trigger_test_run(
    payload: TestRunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger a new autonomous test execution run for a project."""
    stmt = select(Project).where(Project.id == payload.project_id)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    run_id = uuid.uuid4()
    test_run = TestRun(
        id=run_id,
        project_id=project.id,
        status="pending",
        total_tests=0,
        passed=0,
        failed=0,
        skipped=0,
    )
    db.add(test_run)
    await db.commit()
    await db.refresh(test_run)

    background_tasks.add_task(
        run_execution_task,
        str(run_id),
        str(project.id),
        project.url,
        project.name,
        payload.headed,
    )

    return test_run


@router.get("", response_model=List[TestRunResponse])
async def list_runs(
    project_id: Optional[uuid.UUID] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List test runs with optional project filtering."""
    query = (
        select(TestRun)
        .options(selectinload(TestRun.project))
        .order_by(desc(TestRun.created_at))
        .limit(limit)
    )
    if project_id:
        query = query.where(TestRun.project_id == project_id)

    result = await db.execute(query)
    runs = result.scalars().all()
    return [
        TestRunResponse(
            id=r.id,
            project_id=r.project_id,
            project_name=r.project.name if r.project else "Web Application",
            status=r.status,
            total_tests=r.total_tests,
            passed=r.passed,
            failed=r.failed,
            skipped=r.skipped,
            started_at=r.started_at,
            completed_at=r.completed_at,
            created_at=r.created_at,
            report_path=r.report_path,
            logs_path=r.logs_path,
        )
        for r in runs
    ]


@router.get("/{run_id}", response_model=TestRunDetailResponse)
async def get_run_details(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get full details of a specific test run including results and defects."""
    stmt = (
        select(TestRun)
        .options(
            selectinload(TestRun.results).selectinload(TestResult.defects),
            selectinload(TestRun.results).selectinload(TestResult.test_case),
        )
        .where(TestRun.id == run_id)
    )
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test run not found"
        )

    formatted_results = []
    for idx, r in enumerate(run.results):
        tc_name = r.test_case.name if r.test_case else f"Test Case #{idx+1:02d}"
        formatted_results.append(
            TestResultResponse(
                id=r.id,
                run_id=r.run_id,
                test_case_id=r.test_case_id,
                test_name=tc_name,
                status=r.status,
                error_message=r.error_message,
                stack_trace=r.stack_trace,
                screenshot_path=r.screenshot_path,
                video_path=r.video_path,
                log_path=r.log_path,
                failure_analysis=r.failure_analysis,
                duration_seconds=r.duration_seconds,
                attempt_number=r.attempt_number,
                executed_at=r.executed_at,
                defects=[DefectResponse.model_validate(d) for d in (r.defects or [])],
            )
        )

    return TestRunDetailResponse(
        id=run.id,
        project_id=run.project_id,
        status=run.status,
        total_tests=run.total_tests,
        passed=run.passed,
        failed=run.failed,
        skipped=run.skipped,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
        report_path=run.report_path,
        logs_path=run.logs_path,
        results=formatted_results,
    )


@router.post("/{run_id}/retry", response_model=TestRunResponse)
async def retry_run(
    run_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Rerun/retry the tests for this run."""
    stmt = select(TestRun).where(TestRun.id == run_id)
    result = await db.execute(stmt)
    old_run = result.scalar_one_or_none()
    if not old_run:
        raise HTTPException(status_code=404, detail="Test run not found")

    stmt_p = select(Project).where(Project.id == old_run.project_id)
    res_p = await db.execute(stmt_p)
    project = res_p.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Associated project not found")

    new_run_id = uuid.uuid4()
    new_run = TestRun(
        id=new_run_id,
        project_id=project.id,
        status="pending",
    )
    db.add(new_run)
    await db.commit()
    await db.refresh(new_run)

    background_tasks.add_task(
        run_execution_task,
        str(new_run_id),
        str(project.id),
        project.url,
        project.name,
    )

    return new_run


"""
Reports API Router
Endpoints for downloading Allure, Excel, and PDF reports and querying defect summaries.
"""
from __future__ import annotations

import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.defect import Defect
from app.models.project import Project
from app.models.test_result import TestResult
from app.models.test_run import TestRun
from app.schemas.report import TestSummary
from app.schemas.test_run import DefectResponse
from app.services.report_service import report_service
from app.services.storage_service import storage_service

router = APIRouter(prefix="/reports")


@router.get("/{run_id}/summary", response_model=TestSummary)
async def get_test_summary(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieve statistical summary for a test run."""
    stmt = (
        select(TestRun)
        .options(selectinload(TestRun.project), selectinload(TestRun.results))
        .where(TestRun.id == run_id)
    )
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test run not found"
        )

    pass_rate = round((run.passed / run.total_tests * 100) if run.total_tests > 0 else 0, 2)
    duration_minutes = None
    if run.started_at and run.completed_at:
        duration_minutes = round((run.completed_at - run.started_at).total_seconds() / 60, 2)

    return TestSummary(
        run_id=run.id,
        project_id=run.project_id,
        project_name=run.project.name if run.project else "Unknown",
        status=run.status,
        total_tests=run.total_tests,
        passed=run.passed,
        failed=run.failed,
        skipped=run.skipped,
        pass_rate=pass_rate,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_minutes=duration_minutes,
    )


@router.get("/{run_id}/excel")
async def download_excel_report(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Generate and download Excel report."""
    stmt = (
        select(TestRun)
        .options(
            selectinload(TestRun.project),
            selectinload(TestRun.results).selectinload(TestResult.defects),
        )
        .where(TestRun.id == run_id)
    )
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    proj_name = run.project.name if run.project else "App"
    run_dict = {
        "status": run.status,
        "total_tests": run.total_tests,
        "passed": run.passed,
        "failed": run.failed,
        "skipped": run.skipped,
        "pass_rate": round((run.passed / max(run.total_tests, 1)) * 100, 1),
    }

    results_data = [
        {
            "name": r.test_case_id or "Test",
            "status": r.status,
            "duration_seconds": r.duration_seconds,
            "error_message": r.error_message,
            "failure_analysis": r.failure_analysis,
        }
        for r in run.results
    ]

    all_defects = []
    for r in run.results:
        for d in r.defects:
            all_defects.append({
                "title": d.title,
                "severity": d.severity,
                "root_cause": d.root_cause,
                "suggested_fix": d.suggested_fix,
            })

    rel_path = await report_service.generate_excel_report(
        project_name=proj_name,
        run_data=run_dict,
        results=results_data,
        defects=all_defects,
    )

    abs_path = storage_service.get_absolute_path(rel_path)
    if not abs_path.exists():
        raise HTTPException(status_code=500, detail="Report generation failed")

    return FileResponse(
        path=str(abs_path),
        filename=abs_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/{run_id}/pdf")
async def download_pdf_report(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Generate and download PDF report."""
    stmt = (
        select(TestRun)
        .options(
            selectinload(TestRun.project),
            selectinload(TestRun.results).selectinload(TestResult.defects),
        )
        .where(TestRun.id == run_id)
    )
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    proj_name = run.project.name if run.project else "App"
    run_dict = {
        "status": run.status,
        "total_tests": run.total_tests,
        "passed": run.passed,
        "failed": run.failed,
        "skipped": run.skipped,
        "pass_rate": round((run.passed / max(run.total_tests, 1)) * 100, 1),
    }

    results_data = [
        {
            "name": r.test_case_id or "Test",
            "status": r.status,
            "duration_seconds": r.duration_seconds,
            "error_message": r.error_message,
        }
        for r in run.results
    ]

    all_defects = []
    for r in run.results:
        for d in r.defects:
            all_defects.append({
                "title": d.title,
                "severity": d.severity,
                "root_cause": d.root_cause,
                "suggested_fix": d.suggested_fix,
            })

    rel_path = await report_service.generate_pdf_report(
        project_name=proj_name,
        run_data=run_dict,
        results=results_data,
        defects=all_defects,
    )

    abs_path = storage_service.get_absolute_path(rel_path)
    if not abs_path.exists():
        raise HTTPException(status_code=500, detail="Report generation failed")

    return FileResponse(
        path=str(abs_path),
        filename=abs_path.name,
        media_type="application/pdf",
    )


@router.get("/{run_id}/defects", response_model=List[DefectResponse])
async def get_run_defects(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get all AI-detected defects for a specific run."""
    stmt = (
        select(Defect)
        .join(TestResult, Defect.result_id == TestResult.id)
        .where(TestResult.run_id == run_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

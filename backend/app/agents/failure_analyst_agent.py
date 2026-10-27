"""
Failure Analyst Agent
Agent 6: AI-Powered Root Cause Failure Analyst.
Diagnoses locator breakage, timeouts, API failures, and application bugs.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import ai_service, FailureAnalysis


class FailureAnalystAgent:
    """Diagnoses test failures using LLM Root Cause Analysis."""

    def __init__(self):
        logger.info("🔬 Failure Analyst Agent initialized")

    async def analyze_failures(
        self,
        failed_results: List[Dict[str, Any]],
        project_id: str,
        db_session: Optional[AsyncSession] = None,
    ) -> List[Dict[str, Any]]:
        """
        Analyzes a list of failed test outcomes, calls AI RCA,
        and constructs Defect items.
        """
        logger.info(f"🔬 Analyzing {len(failed_results)} failures with AI...")
        defects = []

        for fail in failed_results:
            test_name = fail.get("test_name", "UnknownTest")
            error_msg = fail.get("error_message", "Assertion failed")
            steps = fail.get("test_steps", [])

            try:
                analysis: FailureAnalysis = await ai_service.analyze_failure(
                    error_message=error_msg,
                    test_name=test_name,
                    test_steps=steps,
                    screenshot_description="Error screen captured at step timeout",
                )

                defect_data = {
                    "id": str(uuid.uuid4()),
                    "result_id": fail.get("id"),
                    "title": f"Defect in {test_name}: {analysis.failure_type.title()} issue",
                    "root_cause": analysis.root_cause,
                    "failure_type": analysis.failure_type,
                    "root_cause_category": analysis.failure_type,
                    "suggested_fix": analysis.suggested_fix,
                    "new_locator": analysis.new_locator,
                    "severity": analysis.severity,
                    "screenshot_path": fail.get("screenshot_path"),
                }
                defects.append(defect_data)
                logger.info(f"  ✓ Failure diagnosed: {analysis.failure_type} | Severity: {analysis.severity}")

            except Exception as e:
                logger.warning(f"AI RCA failed for {test_name}: {e}")
                # Fallback rule-based heuristic
                cat = "locator" if "locator" in error_msg.lower() else "timeout"
                defects.append({
                    "id": str(uuid.uuid4()),
                    "result_id": fail.get("id"),
                    "title": f"Failure: {test_name}",
                    "root_cause": error_msg,
                    "failure_type": cat,
                    "root_cause_category": cat,
                    "suggested_fix": "Verify element selector and page load timings",
                    "severity": "medium",
                })

        if db_session:
            await self._persist_defects(defects, db_session)

        return defects

    async def _persist_defects(self, defects: List[Dict[str, Any]], db_session: AsyncSession) -> None:
        """Store defects in database."""
        try:
            from app.models.defect import Defect
            import uuid as uuid_pkg

            for d in defects:
                raw_res_id = d.get("result_id")
                if raw_res_id:
                    defect_obj = Defect(
                        id=uuid_pkg.UUID(d["id"]),
                        result_id=uuid_pkg.UUID(str(raw_res_id)),
                        title=d["title"],
                        root_cause=d.get("root_cause"),
                        root_cause_category=d.get("root_cause_category"),
                        suggested_fix=d.get("suggested_fix"),
                        severity=d.get("severity", "medium"),
                    )
                    db_session.add(defect_obj)

            await db_session.commit()
            logger.info(f"💾 Persisted {len(defects)} defects to database")
        except Exception as e:
            logger.warning(f"Could not persist defects: {e}")
            await db_session.rollback()


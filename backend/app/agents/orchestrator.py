"""
LangChain Orchestrator Agent
Coordinates all 8 specialized agents in the correct sequence.
Manages the full pipeline from URL input to final report generation.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from loguru import logger

from app.config import settings
from app.services.ai_service import ai_service
from app.utils.exceptions import ExecutionException


class PipelineStatus:
    """Tracks the status of the full testing pipeline."""
    DISCOVERING = "discovering"
    ANALYZING = "analyzing"
    GENERATING_TESTS = "generating_tests"
    GENERATING_SCRIPTS = "generating_scripts"
    EXECUTING = "executing"
    ANALYZING_FAILURES = "analyzing_failures"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    FAILED = "failed"


class OrchestratorAgent:
    """
    Master orchestrator that coordinates the 8 specialized agents.
    
    Pipeline:
    1. DiscoveryAgent → Crawl & map the application
    2. PageAnalyzerAgent → AI-analyze each discovered page
    3. TestCaseGeneratorAgent → Generate comprehensive test cases
    4. CodeGeneratorAgent → Generate Playwright scripts
    5. ExecutionAgent → Run the generated tests
    6. FailureAnalystAgent → Analyze any failures
    7. VisualTestingAgent → Visual comparison checks
    8. ReportAgent → Generate final reports
    """

    def __init__(self, websocket_callback: Optional[Callable] = None):
        """
        Initialize the orchestrator.
        
        Args:
            websocket_callback: Optional async function to send real-time updates
                                Signature: async def callback(event_type: str, data: dict)
        """
        self.websocket_callback = websocket_callback
        self.pipeline_id = str(uuid.uuid4())
        logger.info(f"🎯 Orchestrator initialized | Pipeline: {self.pipeline_id[:8]}")

    async def _send_update(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send real-time WebSocket update."""
        if self.websocket_callback:
            try:
                await self.websocket_callback(event_type, {
                    "pipeline_id": self.pipeline_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    **data,
                })
            except Exception as e:
                logger.warning(f"Failed to send WebSocket update: {e}")

    async def run_full_pipeline(
        self,
        project_id: str,
        url: str,
        app_name: str = "",
        db_session=None,
        run_id: Optional[str] = None,
        headed: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute the complete testing pipeline.
        
        Args:
            project_id: Database project ID
            url: Target application URL
            app_name: Application name for context
            db_session: Async SQLAlchemy session
            run_id: Optional test run ID
            headed: Whether to show visible browser window
            
        Returns:
            Complete pipeline results with all metrics
        """
        start_time = datetime.utcnow()
        app_name = app_name or url.split("//")[-1].split("/")[0]
        
        logger.info(f"🚀 Starting full pipeline for: {app_name} ({url}) [headed={headed}]")
        await self._send_update("pipeline_started", {
            "status": PipelineStatus.DISCOVERING,
            "message": f"Starting autonomous testing for {app_name}",
            "url": url,
            "headed": headed,
        })

        pipeline_result = {
            "project_id": project_id,
            "url": url,
            "app_name": app_name,
            "pipeline_id": self.pipeline_id,
            "started_at": start_time.isoformat(),
            "stages": {},
            "summary": {},
            "errors": [],
        }

        try:
            # ─── Stage 1: Application Discovery ───────────────────────────────────
            logger.info("📡 Stage 1: Application Discovery")
            await self._send_update("stage_started", {
                "stage": "discovery",
                "status": PipelineStatus.DISCOVERING,
                "message": "🔍 Crawling application and discovering pages...",
            })

            from app.agents.discovery_agent import DiscoveryAgent
            discovery_agent = DiscoveryAgent()
            site_map = await discovery_agent.discover(url, app_name, headed=headed)
            
            pipeline_result["stages"]["discovery"] = {
                "pages_found": len(site_map.get("pages", [])),
                "navigation_items": len(site_map.get("navigation", [])),
                "forms_found": site_map.get("total_forms", 0),
                "completed_at": datetime.utcnow().isoformat(),
            }
            
            await self._send_update("stage_completed", {
                "stage": "discovery",
                "message": f"✅ Discovered {len(site_map.get('pages', []))} pages",
                "data": pipeline_result["stages"]["discovery"],
            })

            # ─── Stage 2: Page Analysis ────────────────────────────────────────────
            logger.info("🧠 Stage 2: AI Page Analysis")
            await self._send_update("stage_started", {
                "stage": "analysis",
                "status": PipelineStatus.ANALYZING,
                "message": "🤖 AI is analyzing each discovered page...",
            })

            from app.agents.page_analyzer_agent import PageAnalyzerAgent
            analyzer_agent = PageAnalyzerAgent()
            page_analyses = await analyzer_agent.analyze_all_pages(
                site_map.get("pages", [])
            )
            
            pipeline_result["stages"]["analysis"] = {
                "pages_analyzed": len(page_analyses),
                "page_types": list({p.get("page_type") for p in page_analyses}),
                "total_elements": sum(p.get("element_count", 0) for p in page_analyses),
                "completed_at": datetime.utcnow().isoformat(),
            }
            
            await self._send_update("stage_completed", {
                "stage": "analysis",
                "message": f"✅ Analyzed {len(page_analyses)} pages",
                "data": pipeline_result["stages"]["analysis"],
            })

            # ─── Stage 3: Test Case Generation ────────────────────────────────────
            logger.info("📝 Stage 3: Test Case Generation")
            await self._send_update("stage_started", {
                "stage": "test_generation",
                "status": PipelineStatus.GENERATING_TESTS,
                "message": "📋 Generating comprehensive test cases...",
            })

            from app.agents.test_case_generator_agent import TestCaseGeneratorAgent
            tc_agent = TestCaseGeneratorAgent()
            all_test_cases = await tc_agent.generate_all(
                page_analyses, app_name, url, project_id, db_session
            )
            
            pipeline_result["stages"]["test_generation"] = {
                "total_test_cases": len(all_test_cases),
                "by_category": self._count_by_key(all_test_cases, "category"),
                "by_type": self._count_by_key(all_test_cases, "test_type"),
                "by_priority": self._count_by_key(all_test_cases, "priority"),
                "completed_at": datetime.utcnow().isoformat(),
            }
            
            await self._send_update("stage_completed", {
                "stage": "test_generation",
                "message": f"✅ Generated {len(all_test_cases)} test cases",
                "data": pipeline_result["stages"]["test_generation"],
            })

            # ─── Stage 4: Script Generation ────────────────────────────────────────
            logger.info("⚙️ Stage 4: Playwright Script Generation")
            await self._send_update("stage_started", {
                "stage": "script_generation",
                "status": PipelineStatus.GENERATING_SCRIPTS,
                "message": "🎭 Generating Playwright automation scripts...",
            })

            from app.agents.code_generator_agent import CodeGeneratorAgent
            code_agent = CodeGeneratorAgent()
            generated_files = await code_agent.generate_all_scripts(
                all_test_cases, page_analyses, app_name, url
            )
            
            pipeline_result["stages"]["script_generation"] = {
                "files_generated": len(generated_files),
                "page_classes": [f for f in generated_files if "pages/" in f],
                "test_files": [f for f in generated_files if "tests/" in f],
                "completed_at": datetime.utcnow().isoformat(),
            }
            
            await self._send_update("stage_completed", {
                "stage": "script_generation",
                "message": f"✅ Generated {len(generated_files)} automation files",
                "data": pipeline_result["stages"]["script_generation"],
            })

            # ─── Stage 5: Test Execution ───────────────────────────────────────────
            logger.info("🚀 Stage 5: Autonomous Test Execution")
            await self._send_update("stage_started", {
                "stage": "execution",
                "status": PipelineStatus.EXECUTING,
                "message": "⚡ Executing tests autonomously...",
            })

            from app.agents.execution_agent import ExecutionAgent
            exec_agent = ExecutionAgent()
            execution_results = await exec_agent.execute_all(
                generated_files,
                project_id,
                db_session,
                run_id=run_id,
                headed=headed,
                progress_callback=self._send_update,
                test_cases=all_test_cases,
                app_url=url,
            )
            
            pipeline_result["stages"]["execution"] = {
                "total": execution_results.get("total", 0),
                "passed": execution_results.get("passed", 0),
                "failed": execution_results.get("failed", 0),
                "skipped": execution_results.get("skipped", 0),
                "duration_seconds": execution_results.get("duration", 0),
                "completed_at": datetime.utcnow().isoformat(),
            }
            
            await self._send_update("stage_completed", {
                "stage": "execution",
                "message": (
                    f"✅ Tests complete: "
                    f"{execution_results.get('passed', 0)} passed, "
                    f"{execution_results.get('failed', 0)} failed"
                ),
                "data": pipeline_result["stages"]["execution"],
            })

            # ─── Stage 6: Failure Analysis ─────────────────────────────────────────
            failed_results = execution_results.get("failed_results", [])
            if failed_results:
                logger.info(f"🔬 Stage 6: Failure Analysis ({len(failed_results)} failures)")
                await self._send_update("stage_started", {
                    "stage": "failure_analysis",
                    "status": PipelineStatus.ANALYZING_FAILURES,
                    "message": f"🔬 AI analyzing {len(failed_results)} test failures...",
                })

                from app.agents.failure_analyst_agent import FailureAnalystAgent
                fa_agent = FailureAnalystAgent()
                defects = await fa_agent.analyze_failures(
                    failed_results, project_id, db_session
                )
                
                pipeline_result["stages"]["failure_analysis"] = {
                    "defects_found": len(defects),
                    "by_type": self._count_by_key(defects, "failure_type"),
                    "critical_defects": sum(1 for d in defects if d.get("severity") == "critical"),
                    "completed_at": datetime.utcnow().isoformat(),
                }
                
                await self._send_update("stage_completed", {
                    "stage": "failure_analysis",
                    "message": f"✅ Identified {len(defects)} defects with root causes",
                    "data": pipeline_result["stages"]["failure_analysis"],
                })

            # ─── Stage 7: Visual Testing ───────────────────────────────────────────
            logger.info("👁️ Stage 7: Visual Testing")
            await self._send_update("stage_started", {
                "stage": "visual_testing",
                "message": "👁️ Running visual comparison tests...",
            })

            from app.agents.visual_testing_agent import VisualTestingAgent
            vt_agent = VisualTestingAgent()
            visual_results = await vt_agent.run_visual_tests(
                execution_results.get("screenshots", [])
            )
            
            pipeline_result["stages"]["visual_testing"] = {
                "screenshots_compared": visual_results.get("total", 0),
                "visual_defects": visual_results.get("defects", 0),
                "completed_at": datetime.utcnow().isoformat(),
            }

            # ─── Stage 8: Report Generation ────────────────────────────────────────
            logger.info("📊 Stage 8: Report Generation")
            await self._send_update("stage_started", {
                "stage": "reporting",
                "status": PipelineStatus.GENERATING_REPORT,
                "message": "📊 Generating reports (Allure, Excel, PDF)...",
            })

            from app.agents.report_agent import ReportAgent
            report_agent = ReportAgent()
            reports = await report_agent.generate_all_reports(
                project_id, execution_results, pipeline_result
            )
            
            pipeline_result["stages"]["reporting"] = {
                "allure_path": reports.get("allure"),
                "excel_path": reports.get("excel"),
                "pdf_path": reports.get("pdf"),
                "completed_at": datetime.utcnow().isoformat(),
            }

            # ─── Final Summary ─────────────────────────────────────────────────────
            end_time = datetime.utcnow()
            total_seconds = (end_time - start_time).total_seconds()
            
            exec_stage = pipeline_result["stages"].get("execution", {})
            total_tests = exec_stage.get("total", 0)
            passed_tests = exec_stage.get("passed", 0)
            
            pipeline_result["summary"] = {
                "status": PipelineStatus.COMPLETED,
                "total_duration_seconds": total_seconds,
                "pages_discovered": len(site_map.get("pages", [])),
                "pages_analyzed": len(page_analyses),
                "test_cases_generated": len(all_test_cases),
                "scripts_generated": len(generated_files),
                "tests_executed": total_tests,
                "tests_passed": passed_tests,
                "tests_failed": exec_stage.get("failed", 0),
                "tests_skipped": exec_stage.get("skipped", 0),
                "pass_rate": round((passed_tests / total_tests * 100) if total_tests > 0 else 0, 2),
                "reports": reports,
                "completed_at": end_time.isoformat(),
            }
            
            logger.success(
                f"🎉 Pipeline completed | "
                f"{total_tests} tests | "
                f"{pipeline_result['summary']['pass_rate']}% pass rate | "
                f"{total_seconds:.1f}s"
            )
            
            await self._send_update("pipeline_completed", {
                "status": PipelineStatus.COMPLETED,
                "message": (
                    f"🎉 Testing complete! "
                    f"{passed_tests}/{total_tests} tests passed "
                    f"({pipeline_result['summary']['pass_rate']}%)"
                ),
                "summary": pipeline_result["summary"],
            })
            
            return pipeline_result

        except Exception as e:
            logger.exception(f"❌ Pipeline failed: {e}")
            pipeline_result["summary"]["status"] = PipelineStatus.FAILED
            pipeline_result["errors"].append(str(e))
            
            await self._send_update("pipeline_failed", {
                "status": PipelineStatus.FAILED,
                "message": f"❌ Pipeline failed: {str(e)}",
                "error": str(e),
            })
            
            raise ExecutionException(f"Pipeline execution failed: {e}") from e

    def _count_by_key(self, items: List[Dict], key: str) -> Dict[str, int]:
        """Count items grouped by a dictionary key."""
        counts = {}
        for item in items:
            value = item.get(key, "unknown") if isinstance(item, dict) else "unknown"
            counts[value] = counts.get(value, 0) + 1
        return counts


# ─── Module-level convenience function ───────────────────────────────────────────
async def run_testing_pipeline(
    project_id: str,
    url: str,
    app_name: str = "",
    db_session=None,
    websocket_callback: Optional[Callable] = None,
    run_id: Optional[str] = None,
    headed: bool = False,
) -> Dict[str, Any]:
    """
    Convenience function to run the full testing pipeline.
    
    Args:
        project_id: Database project ID
        url: Target URL
        app_name: Optional application name
        db_session: Database session
        websocket_callback: Optional WebSocket update callback
        run_id: Optional test run ID
        headed: Whether to show visible browser window
        
    Returns:
        Complete pipeline results
    """
    orchestrator = OrchestratorAgent(websocket_callback=websocket_callback)
    return await orchestrator.run_full_pipeline(
        project_id=project_id,
        url=url,
        app_name=app_name,
        db_session=db_session,
        run_id=run_id,
        headed=headed,
    )


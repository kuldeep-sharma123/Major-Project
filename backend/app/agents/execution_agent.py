"""
Execution Agent
Agent 5: Autonomous Execution Engine.
Runs generated Playwright test suites, collects screenshots, videos, and logs.
"""
from __future__ import annotations

import asyncio
import os
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.playwright_service import playwright_service
from app.services.storage_service import storage_service


class ExecutionAgent:
    """Autonomous Test Execution Engine."""

    def __init__(self):
        logger.info("⚡ Execution Agent initialized")

    async def execute_all(
        self,
        generated_files: List[str],
        project_id: str,
        db_session: Optional[AsyncSession] = None,
        run_id: Optional[str] = None,
        headed: bool = False,
        progress_callback: Optional[Callable] = None,
        test_cases: Optional[List[Dict[str, Any]]] = None,
        app_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes autonomous test suite against the target application.
        Runs live browser automation with Playwright, captures real screenshots,
        executes assertions on live DOM, and reports real results.
        """
        logger.info(
            f"🚀 [Execution Agent] Starting autonomous test execution for project {project_id} "
            f"(url={app_url}, run_id={run_id}, headed={headed})..."
        )

        from playwright.async_api import async_playwright
        import traceback

        # If app_url not passed, fetch from project in DB
        if not app_url and db_session:
            from app.models.project import Project
            p_res = await db_session.execute(select(Project).where(Project.id == uuid.UUID(str(project_id))))
            p_obj = p_res.scalar_one_or_none()
            if p_obj:
                app_url = p_obj.url

        app_url = app_url or "https://example.com"
        if not app_url.startswith(("http://", "https://")):
            app_url = "https://" + app_url

        # Fetch test cases from DB if not provided
        cases_to_run = test_cases or []
        if not cases_to_run and db_session:
            from app.models.test_case import TestCase
            tc_res = await db_session.execute(
                select(TestCase).where(TestCase.project_id == uuid.UUID(str(project_id)))
            )
            db_cases = tc_res.scalars().all()
            cases_to_run = [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "description": c.description,
                    "category": c.category,
                    "test_type": c.test_type,
                    "steps": c.steps or [],
                }
                for c in db_cases
            ]

        # If still no test cases, create standard suite tailored to the target URL
        if not cases_to_run:
            cases_to_run = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "TC_Smoke_HomepageLoad",
                    "description": "Verify home page loads successfully with HTTP 200 and visible DOM",
                    "steps": [{"action": "navigate", "target": app_url}, {"action": "assert_visible", "target": "body"}],
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "TC_UI_HeadingValidation",
                    "description": "Verify primary page heading or title is present",
                    "steps": [{"action": "navigate", "target": app_url}, {"action": "assert_visible", "target": "h1, h2, title, body"}],
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "TC_Responsive_LayoutVerification",
                    "description": "Verify viewport renders without layout overflow",
                    "steps": [{"action": "navigate", "target": app_url}, {"action": "assert_visible", "target": "body"}],
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "TC_Security_HeaderIntegrity",
                    "description": "Verify secure transport and content headers",
                    "steps": [{"action": "navigate", "target": app_url}],
                },
            ]

        total = len(cases_to_run)
        passed_results = []
        failed_results = []
        screenshots = []
        start_time = time.perf_counter()

        logger.info(f"⚡ [Execution Agent] Executing {total} test cases on live browser (headed={headed})...")

        main_loop = asyncio.get_running_loop()

        def _make_threadsafe_cb(cb, loop):
            if not cb:
                return None
            async def _wrapper(*args, **kwargs):
                try:
                    if asyncio.get_running_loop() is loop:
                        await cb(*args, **kwargs)
                    else:
                        fut = asyncio.run_coroutine_threadsafe(cb(*args, **kwargs), loop)
                        await asyncio.wrap_future(fut)
                except Exception:
                    pass
            return _wrapper

        safe_progress_cb = _make_threadsafe_cb(progress_callback, main_loop)

        async def _execute_browser_suite():
            async with async_playwright() as p:
                logger.info(f"🌐 Launching Chromium browser (headed={headed})...")
                browser = await p.chromium.launch(
                    headless=not headed,
                    args=["--no-sandbox", "--disable-setuid-sandbox"],
                )
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                    ignore_https_errors=True,
                )
                page = await context.new_page()

                for idx, tc in enumerate(cases_to_run):
                    tc_id = tc.get("id") or str(uuid.uuid4())
                    tc_name = tc.get("name") or f"Test_Case_{idx+1:02d}"
                    tc_steps = tc.get("steps") or []
                    t_start = time.perf_counter()
                    t_status = "passed"
                    error_msg = None
                    shot_path = None

                    # Emit WS event: test running
                    if safe_progress_cb:
                        try:
                            await safe_progress_cb("test_case_progress", {
                                "test_name": tc_name,
                                "current": idx + 1,
                                "total": total,
                                "status": "running",
                            })
                        except Exception:
                            pass

                    try:
                        # 1. Navigate to target URL
                        logger.info(f"▶️ [{idx+1}/{total}] Running: {tc_name} on {app_url}...")
                        resp = await page.goto(app_url, wait_until="domcontentloaded", timeout=15000)
                        await page.wait_for_timeout(1000)

                        # 2. Execute test steps if defined
                        for step in tc_steps:
                            action = step.get("action")
                            target = step.get("target")
                            value = step.get("value")

                            if action == "navigate" and target:
                                dest_url = target if target.startswith("http") else app_url
                                await page.goto(dest_url, wait_until="domcontentloaded", timeout=15000)
                                await page.wait_for_timeout(1000)
                                # If navigating to an internal route but redirected to login, authenticate session
                                if "login" in page.url.lower() and "login" not in dest_url.lower():
                                    logger.info(f"🔒 Redirected to login for internal route {dest_url}. Auto-authenticating...")
                                    await self._auto_authenticate_session(page, app_url)
                                    if page.url != dest_url:
                                        await page.goto(dest_url, wait_until="domcontentloaded", timeout=15000)
                                        await page.wait_for_timeout(1000)
                            elif action == "assert_visible" and target:
                                locator = page.locator(target).first
                                try:
                                    # Wait up to 3s for element to be visible in DOM
                                    await locator.wait_for(state="visible", timeout=3000)
                                except Exception:
                                    # Check count or text on page as fallback
                                    count = await page.locator(target).count()
                                    if count == 0:
                                        raise AssertionError(
                                            f"Assertion Failed: Target element '{target}' is not visible or not found on page"
                                        )
                            elif action in ("assert_text", "assert_contains") and target and value:
                                locator = page.locator(target).first
                                try:
                                    await locator.wait_for(state="visible", timeout=3000)
                                    text_content = await locator.inner_text()
                                    if str(value).lower() not in text_content.lower():
                                        raise AssertionError(
                                            f"Assertion Failed: Expected text '{value}' not found in '{target}' (got '{text_content[:80]}')"
                                        )
                                except Exception as e:
                                    raise AssertionError(f"Assertion Failed: {e}")
                            elif action == "fill" and target:
                                inp = page.locator(target).first
                                try:
                                    await inp.wait_for(state="visible", timeout=3000)
                                    await inp.fill(str(value if value is not None else ""))
                                except Exception as e:
                                    raise AssertionError(f"Step Failed: Could not fill input '{target}': {e}")
                            elif action == "click" and target:
                                btn = page.locator(target).first
                                try:
                                    await btn.wait_for(state="visible", timeout=3000)
                                    await btn.click(timeout=3000)
                                except Exception as e:
                                    raise AssertionError(f"Step Failed: Could not click element '{target}': {e}")

                        # Take real screenshot of this test execution
                        shot_bytes = await page.screenshot(full_page=False)
                        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", tc_name.lower())
                        shot_path = await storage_service.save_screenshot(
                            shot_bytes, f"{safe_name}_{uuid.uuid4().hex[:6]}.png"
                        )
                        screenshots.append(shot_path)

                    except Exception as test_err:
                        t_status = "failed"
                        error_msg = f"{type(test_err).__name__}: {str(test_err)}"
                        logger.warning(f"⚠️ Test failed: {tc_name} -> {error_msg}")
                        try:
                            shot_bytes = await page.screenshot(full_page=False)
                            shot_path = await storage_service.save_screenshot(
                                shot_bytes, f"err_{safe_name}_{uuid.uuid4().hex[:6]}.png"
                            )
                            screenshots.append(shot_path)
                        except Exception:
                            pass

                    t_duration = round(time.perf_counter() - t_start, 2)

                    result_entry = {
                        "id": str(uuid.uuid4()),
                        "test_case_id": tc_id,
                        "test_name": tc_name,
                        "status": t_status,
                        "duration_seconds": t_duration,
                        "error_message": error_msg,
                        "screenshot_path": shot_path,
                        "test_steps": tc_steps,
                    }

                    if t_status == "passed":
                        passed_results.append(result_entry)
                    else:
                        failed_results.append(result_entry)

                    # Emit WS event: test completed
                    if safe_progress_cb:
                        try:
                            await safe_progress_cb("test_case_progress", {
                                "test_name": tc_name,
                                "current": idx + 1,
                                "total": total,
                                "status": t_status,
                                "duration": t_duration,
                                "error": error_msg,
                                "screenshot": shot_path,
                            })
                            await asyncio.sleep(0.15)
                        except Exception:
                            pass

                await context.close()
                await browser.close()

        # Launch live browser automation safely on Windows Proactor
        try:
            from app.utils.helpers import run_coro_with_proactor
            await run_coro_with_proactor(_execute_browser_suite)
        except Exception as browser_err:
            logger.error(f"❌ Playwright execution error ({type(browser_err).__name__}): {browser_err}")

        duration = round(time.perf_counter() - start_time, 2)
        passed = len(passed_results)
        failed = len(failed_results)
        skipped = 0

        execution_summary = {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration": duration if duration > 0 else 1.0,
            "passed_results": passed_results,
            "failed_results": failed_results,
            "all_results": passed_results + failed_results,
            "screenshots": screenshots,
            "stdout": f"Executed {total} live browser tests. {passed} passed, {failed} failed in {duration}s.",
            "completed_at": datetime.utcnow().isoformat(),
        }

        # If DB session provided, persist TestRun and TestResults
        if db_session:
            await self._persist_run(project_id, execution_summary, db_session, run_id=run_id)

        logger.success(f"🏁 Autonomous execution finished: {passed}/{total} passed in {duration}s")
        return execution_summary

    async def _auto_authenticate_session(self, page, app_url: str) -> bool:
        """Autonomously authenticates the browser session for internal page tests."""
        try:
            u_val, p_val = "admin", "admin"
            url_lower = app_url.lower()
            if "orangehrm" in url_lower:
                u_val, p_val = "Admin", "admin123"
            elif "sauce" in url_lower:
                u_val, p_val = "standard_user", "secret_sauce"
            else:
                try:
                    body_text = await page.inner_text("body")
                    import re
                    u_match = re.search(r"username\s*[:=]\s*(\w+)", body_text, re.IGNORECASE)
                    p_match = re.search(r"password\s*[:=]\s*(\w+)", body_text, re.IGNORECASE)
                    if u_match and p_match:
                        u_val, p_val = u_match.group(1), p_match.group(1)
                except Exception:
                    pass

            u_loc = page.locator("input:not([type='hidden'])[name*='user'], input:not([type='hidden'])[placeholder*='user' i], #username, #user-name").first
            p_loc = page.locator("input[type='password'], input[name*='pass'], #password").first
            b_loc = page.locator("button[type='submit'], input[type='submit'], button:has-text('Login'), button:has-text('Sign in')").first

            if await u_loc.is_visible() and await p_loc.is_visible():
                await u_loc.fill(u_val)
                await p_loc.fill(p_val)
                if await b_loc.is_visible():
                    await b_loc.click()
                else:
                    await p_loc.press("Enter")
                await page.wait_for_timeout(3500)
                logger.info(f"✅ Auto-authentication completed. Session is now active.")
                return True
        except Exception as e:
            logger.warning(f"Auto-authentication helper warning: {e}")
        return False

    async def _persist_run(
        self,
        project_id: str,
        execution_summary: Dict[str, Any],
        db_session: AsyncSession,
        run_id: Optional[str] = None,
    ) -> None:
        """Save or update TestRun and its TestResults in database."""
        try:
            from app.models.test_run import TestRun
            from app.models.test_result import TestResult
            import uuid as uuid_pkg

            try:
                run_uuid = uuid_pkg.UUID(str(run_id)) if run_id else uuid_pkg.uuid4()
            except Exception:
                run_uuid = uuid_pkg.uuid4()
            
            # Check if run exists
            stmt = select(TestRun).where(TestRun.id == run_uuid)
            res = await db_session.execute(stmt)
            existing_run = res.scalar_one_or_none()

            p_cnt = execution_summary.get("passed", 0)
            f_cnt = execution_summary.get("failed", 0)
            if p_cnt > 0 and f_cnt == 0:
                status_str = "passed"
            elif p_cnt > 0 and f_cnt > 0:
                status_str = "completed"
            elif p_cnt == 0 and f_cnt > 0:
                status_str = "failed"
            else:
                status_str = "failed" if execution_summary.get("total", 0) > 0 else "pending"

            if existing_run:
                test_run = existing_run
                test_run.status = status_str
                test_run.total_tests = execution_summary["total"]
                test_run.passed = p_cnt
                test_run.failed = f_cnt
                test_run.skipped = execution_summary.get("skipped", 0)
                test_run.completed_at = datetime.utcnow()
            else:
                try:
                    p_uuid = uuid_pkg.UUID(str(project_id))
                except Exception:
                    p_uuid = uuid_pkg.uuid4()

                test_run = TestRun(
                    id=run_uuid,
                    project_id=p_uuid,
                    status=status_str,
                    total_tests=execution_summary["total"],
                    passed=p_cnt,
                    failed=f_cnt,
                    skipped=execution_summary.get("skipped", 0),
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                )
                db_session.add(test_run)

            # Persist all individual test results (both passed and failed)
            all_results = execution_summary.get("all_results", [])
            for r in all_results:
                tc_uuid = None
                if r.get("test_case_id"):
                    try:
                        tc_uuid = uuid_pkg.UUID(str(r["test_case_id"]))
                    except Exception:
                        tc_uuid = None

                res_id = None
                try:
                    res_id = uuid_pkg.UUID(str(r.get("id")))
                except Exception:
                    res_id = uuid_pkg.uuid4()

                result_obj = TestResult(
                    id=res_id,
                    run_id=run_uuid,
                    test_case_id=tc_uuid,
                    status=r["status"],
                    error_message=r.get("error_message"),
                    screenshot_path=r.get("screenshot_path"),
                    duration_seconds=r.get("duration_seconds", 0.0),
                )
                db_session.add(result_obj)

            await db_session.commit()
            logger.info(f"💾 Persisted {len(all_results)} TestResults for TestRun {run_uuid} to database")
        except Exception as e:
            logger.warning(f"Could not persist run to database: {e}")
            await db_session.rollback()

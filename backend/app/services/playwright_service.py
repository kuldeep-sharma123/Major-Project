"""
Playwright Service Module
Manages browser automation, execution runs, screenshots, console logs, and video recording.
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.config import settings
from app.services.storage_service import storage_service


class PlaywrightService:
    """Manages browser runtime, test execution, and media capture."""

    def __init__(self):
        self.browser_type = settings.BROWSER_TYPE
        self.headless = settings.HEADLESS
        self.framework_path = Path(settings.PLAYWRIGHT_FRAMEWORK_PATH)

    async def execute_test_command(
        self,
        test_file: Optional[str] = None,
        allure_results_dir: Optional[str] = None,
        timeout_seconds: int = 300,
        headed: bool = False,
    ) -> Dict[str, Any]:
        """
        Run pytest within the playwright framework directory.
        """
        results_dir = allure_results_dir or str(settings.reports_path / "allure-results")
        os.makedirs(results_dir, exist_ok=True)

        cmd = [
            "pytest",
            test_file or "tests/",
            f"--alluredir={results_dir}",
            "-v",
            "--tb=short",
        ]
        env = os.environ.copy()
        if headed:
            env["PLAYWRIGHT_HEADED"] = "1"
            cmd.append("--headed")
        else:
            env["PLAYWRIGHT_HEADED"] = "0"

        logger.info(f"▶️ Executing Playwright tests: {' '.join(cmd)} [headed={headed}]")
        start_time = time.perf_counter()

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(self.framework_path.resolve()),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout_b, stderr_b = await asyncio.wait_for(
                process.communicate(), timeout=timeout_seconds
            )
            duration = time.perf_counter() - start_time

            stdout = stdout_b.decode("utf-8", errors="replace")
            stderr = stderr_b.decode("utf-8", errors="replace")

            exit_code = process.returncode
            logger.info(f"🏁 Pytest finished with exit code {exit_code} in {duration:.2f}s")

            # Parse results count from pytest output
            passed, failed, skipped = self._parse_pytest_output(stdout)

            log_file = await storage_service.save_log(
                f"STDOUT:\n{stdout}\n\nSTDERR:\n{stderr}",
                f"pytest_run_{uuid.uuid4().hex[:8]}.log",
            )

            return {
                "exit_code": exit_code,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "total": passed + failed + skipped,
                "duration_seconds": round(duration, 2),
                "stdout": stdout,
                "stderr": stderr,
                "log_path": log_file,
                "allure_results_dir": results_dir,
            }

        except asyncio.TimeoutError:
            logger.error("⏱️ Pytest run timed out!")
            return {
                "exit_code": -1,
                "error": "Execution timed out",
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "total": 1,
                "duration_seconds": timeout_seconds,
            }
        except Exception as e:
            logger.exception(f"❌ Error during test run: {e}")
            return {
                "exit_code": 1,
                "error": str(e),
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "total": 1,
                "duration_seconds": round(time.perf_counter() - start_time, 2),
            }

    async def capture_page_screenshot(self, url: str) -> Optional[str]:
        """Navigate to URL and capture a high-res screenshot."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            try:
                page = await browser.new_page(viewport={"width": 1280, "height": 800})
                await page.goto(url, wait_until="networkidle", timeout=30000)
                screenshot_bytes = await page.screenshot(full_page=True)
                path = await storage_service.save_screenshot(
                    screenshot_bytes, f"snapshot_{uuid.uuid4().hex[:8]}.png"
                )
                return path
            except Exception as e:
                logger.warning(f"Could not capture screenshot for {url}: {e}")
                return None
            finally:
                await browser.close()

    def _parse_pytest_output(self, stdout: str) -> tuple[int, int, int]:
        """Parse passed, failed, skipped numbers from pytest terminal summary."""
        import re
        passed = 0
        failed = 0
        skipped = 0

        p_match = re.search(r"(\d+)\s+passed", stdout)
        if p_match:
            passed = int(p_match.group(1))

        f_match = re.search(r"(\d+)\s+failed", stdout)
        if f_match:
            failed = int(f_match.group(1))

        s_match = re.search(r"(\d+)\s+skipped", stdout)
        if s_match:
            skipped = int(s_match.group(1))

        # If no explicit line, check if all passed or exit 0
        if passed == 0 and failed == 0 and skipped == 0:
            if "collected 0 items" in stdout:
                return 0, 0, 0
            if "PASSED" in stdout:
                passed = stdout.count("PASSED")
            if "FAILED" in stdout:
                failed = stdout.count("FAILED")

        return passed, failed, skipped


playwright_service = PlaywrightService()

def get_playwright_service() -> PlaywrightService:
    return playwright_service


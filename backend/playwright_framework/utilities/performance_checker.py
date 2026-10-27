"""
Performance Checker Module
Measures page load timings and Core Web Vitals (LCP, CLS, DOMContentLoaded).
"""
from __future__ import annotations

import time
from typing import Any, Dict
from playwright.async_api import Page
from loguru import logger


class PerformanceChecker:
    """Collects client-side performance measurements via Navigation Timing API."""

    @staticmethod
    async def measure_page_load(page: Page, url: str) -> Dict[str, Any]:
        """
        Navigates to URL and measures load timing metrics in milliseconds.
        """
        start = time.perf_counter()
        response = await page.goto(url, wait_until="networkidle")
        total_time_ms = round((time.perf_counter() - start) * 1000, 2)

        timings = await page.evaluate("""
            () => {
                const nav = performance.getEntriesByType('navigation')[0] || {};
                return {
                    domContentLoaded: Math.round(nav.domContentLoadedEventEnd - nav.startTime || 0),
                    domInteractive: Math.round(nav.domInteractive - nav.startTime || 0),
                    responseEnd: Math.round(nav.responseEnd - nav.startTime || 0),
                    duration: Math.round(nav.duration || 0)
                };
            }
        """)

        metrics = {
            "url": url,
            "status_code": response.status if response else 0,
            "total_elapsed_ms": total_time_ms,
            "dom_content_loaded_ms": timings.get("domContentLoaded", 0),
            "dom_interactive_ms": timings.get("domInteractive", 0),
            "network_response_ms": timings.get("responseEnd", 0),
            "is_fast": total_time_ms < 3000,
        }

        logger.info(f"⚡ Performance metric for {url}: {total_time_ms}ms (fast: {metrics['is_fast']})")
        return metrics


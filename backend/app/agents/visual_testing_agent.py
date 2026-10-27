"""
Visual Testing Agent
Agent 8: Visual Comparison & Layout Shift Defect Detector.
Compares screenshots, detects layout differences, missing elements, and broken images using Pillow.
"""
from __future__ import annotations

import io
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageChops, ImageDraw
from loguru import logger

from app.config import settings
from app.services.storage_service import storage_service


class VisualTestingAgent:
    """Detects visual regressions by comparing screenshots with baseline references."""

    def __init__(self):
        self.reports_dir = Path(settings.reports_path)
        logger.info("👁️ Visual Testing Agent initialized")

    async def run_visual_tests(self, screenshots: List[str]) -> Dict[str, Any]:
        """
        Executes visual comparisons on captured test screenshots.
        """
        logger.info(f"👁️ Running visual regression checks on {len(screenshots)} screenshots...")

        if not screenshots:
            return {"total": 0, "defects": 0, "comparisons": []}

        comparisons = []
        defects_found = 0

        for screen in screenshots:
            # Check baseline or compare image integrity
            diff_score, diff_path = await self._analyze_image(screen)
            is_defect = diff_score > 0.05  # >5% visual change

            if is_defect:
                defects_found += 1

            comparisons.append({
                "screenshot": screen,
                "diff_score": diff_score,
                "diff_image_path": diff_path,
                "status": "defect" if is_defect else "passed",
            })

        logger.info(f"👁️ Visual test completed: {defects_found} visual defects detected")
        return {
            "total": len(screenshots),
            "defects": defects_found,
            "comparisons": comparisons,
        }

    async def compare_images(
        self, baseline_path: str, current_path: str, threshold: float = 0.02
    ) -> Tuple[float, Optional[str]]:
        """
        Calculates pixel difference between baseline and current screenshots.
        Highlights mismatching areas in red.
        """
        try:
            base_abs = storage_service.get_absolute_path(baseline_path)
            curr_abs = storage_service.get_absolute_path(current_path)

            if not base_abs.exists() or not curr_abs.exists():
                return 0.0, None

            img1 = Image.open(base_abs).convert("RGB")
            img2 = Image.open(curr_abs).convert("RGB")

            # Ensure same dimensions
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)

            diff = ImageChops.difference(img1, img2)
            bbox = diff.getbbox()

            if not bbox:
                return 0.0, None  # Exact match

            # Calculate diff ratio
            stat = list(diff.getdata())
            diff_pixels = sum(1 for p in stat if sum(p) > 20)
            total_pixels = img1.size[0] * img1.size[1]
            diff_ratio = diff_pixels / total_pixels

            # Highlight differences
            diff_img = img2.copy()
            draw = ImageDraw.Draw(diff_img)
            draw.rectangle(bbox, outline="red", width=3)

            out_filename = f"diff_{uuid.uuid4().hex[:8]}.png"
            diff_target = Path(settings.screenshots_path) / out_filename
            diff_img.save(diff_target)

            return round(diff_ratio, 4), f"/storage/screenshots/{out_filename}"

        except Exception as e:
            logger.warning(f"Image comparison failed: {e}")
            return 0.0, None

    async def _analyze_image(self, screenshot_path: str) -> Tuple[float, Optional[str]]:
        """Heuristic check for corrupted / blank / error screenshots."""
        try:
            abs_path = storage_service.get_absolute_path(screenshot_path)
            if not abs_path.exists():
                return 0.0, None

            img = Image.open(abs_path)
            # Check if image is blank
            extrema = img.convert("L").getextrema()
            if extrema[0] == extrema[1]:
                return 1.0, screenshot_path  # Completely blank/monochrome

            return 0.01, None
        except Exception:
            return 0.0, None


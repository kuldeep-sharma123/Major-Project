"""
Screenshot Manager Module
Captures full-page and element screenshots, and performs visual diff comparisons using Pillow.
"""
from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageChops, ImageDraw
from playwright.async_api import Locator, Page
from loguru import logger


class ScreenshotManager:
    """Manages screenshot taking, storage, and visual diff comparisons."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path(__file__).parent.parent / "screenshots"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def take_full_page_screenshot(self, page: Page, name: Optional[str] = None) -> str:
        """Capture full page viewport as PNG."""
        fname = name or f"fullpage_{uuid.uuid4().hex[:8]}.png"
        if not fname.endswith(".png"):
            fname += ".png"
        path = self.output_dir / fname
        await page.screenshot(path=str(path), full_page=True)
        logger.info(f"📸 Full page screenshot saved: {path}")
        return str(path)

    async def take_element_screenshot(self, locator: Locator, name: Optional[str] = None) -> str:
        """Capture specific element bounds as PNG."""
        fname = name or f"element_{uuid.uuid4().hex[:8]}.png"
        if not fname.endswith(".png"):
            fname += ".png"
        path = self.output_dir / fname
        await locator.screenshot(path=str(path))
        logger.info(f"📸 Element screenshot saved: {path}")
        return str(path)

    def compare_screenshots(
        self, baseline_path: str, current_path: str, threshold: float = 0.02
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Compares baseline and current images.
        Returns: (is_match, difference_ratio, diff_image_path)
        """
        img1 = Image.open(baseline_path).convert("RGB")
        img2 = Image.open(current_path).convert("RGB")

        if img1.size != img2.size:
            img2 = img2.resize(img1.size)

        diff = ImageChops.difference(img1, img2)
        bbox = diff.getbbox()

        if not bbox:
            return True, 0.0, None

        stat = list(diff.getdata())
        diff_pixels = sum(1 for p in stat if sum(p) > 20)
        total_pixels = img1.size[0] * img1.size[1]
        ratio = diff_pixels / total_pixels

        diff_path = None
        if ratio > threshold:
            diff_img = img2.copy()
            draw = ImageDraw.Draw(diff_img)
            draw.rectangle(bbox, outline="red", width=3)
            diff_fname = f"diff_{uuid.uuid4().hex[:8]}.png"
            diff_target = self.output_dir / diff_fname
            diff_img.save(diff_target)
            diff_path = str(diff_target)

        return ratio <= threshold, round(ratio, 4), diff_path


screenshot_manager = ScreenshotManager()


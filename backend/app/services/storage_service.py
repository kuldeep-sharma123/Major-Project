"""
Storage Service Module
Handles local and cloud file persistence for screenshots, videos, logs, and generated artifacts.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional
import aiofiles
from loguru import logger

from app.config import settings


class StorageService:
    """Manages file persistence for all test automation artifacts."""

    def __init__(self):
        self.base_path = Path(settings.STORAGE_PATH)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary storage subdirectories if they do not exist."""
        for d in ["screenshots", "videos", "logs", "reports", "generated_scripts"]:
            (self.base_path / d).mkdir(parents=True, exist_ok=True)

    async def save_screenshot(self, image_bytes: bytes, filename: Optional[str] = None) -> str:
        """Save screenshot bytes to disk and return relative path."""
        name = filename or f"screenshot_{uuid.uuid4().hex[:12]}.png"
        if not name.endswith(".png"):
            name += ".png"
        target = self.base_path / "screenshots" / name
        async with aiofiles.open(target, "wb") as f:
            await f.write(image_bytes)
        logger.info(f"📸 Screenshot saved: {target}")
        return f"/storage/screenshots/{name}"

    async def save_video(self, video_bytes: bytes, filename: Optional[str] = None) -> str:
        """Save video bytes to disk and return relative path."""
        name = filename or f"video_{uuid.uuid4().hex[:12]}.webm"
        target = self.base_path / "videos" / name
        async with aiofiles.open(target, "wb") as f:
            await f.write(video_bytes)
        logger.info(f"🎥 Video saved: {target}")
        return f"/storage/videos/{name}"

    async def save_log(self, content: str, filename: Optional[str] = None) -> str:
        """Save textual log content to disk."""
        name = filename or f"log_{uuid.uuid4().hex[:12]}.txt"
        target = self.base_path / "logs" / name
        async with aiofiles.open(target, "w", encoding="utf-8") as f:
            await f.write(content)
        return f"/storage/logs/{name}"

    async def save_generated_script(self, content: str, filename: str) -> str:
        """Save generated Playwright Python script."""
        target = self.base_path / "generated_scripts" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(target, "w", encoding="utf-8") as f:
            await f.write(content)
        return str(target)

    def get_absolute_path(self, relative_path: str) -> Path:
        """Resolve storage path relative to project root."""
        clean = relative_path.lstrip("/storage/").lstrip("/")
        return self.base_path / clean


storage_service = StorageService()

def get_storage_service() -> StorageService:
    return storage_service


"""
Report Helper Utility
Hooks into Allure, attaches screenshots, logs, and creates environment configuration.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    import allure
except ImportError:
    allure = None
from loguru import logger


def attach_screenshot_to_allure(screenshot_path: str, name: str = "Failure Screenshot") -> None:
    """Attach a saved screenshot to the active Allure report."""
    if allure and os.path.exists(screenshot_path):
        with open(screenshot_path, "rb") as f:
            allure.attach(
                f.read(),
                name=name,
                attachment_type=allure.attachment_type.PNG,
            )
        logger.debug(f"Attached screenshot to Allure: {screenshot_path}")


def attach_log_to_allure(log_content: str, name: str = "Execution Log") -> None:
    """Attach text log to Allure report."""
    if allure:
        allure.attach(
            log_content,
            name=name,
            attachment_type=allure.attachment_type.TEXT,
        )


def create_allure_environment_file(output_dir: str = "reports/allure-results") -> None:
    """Write environment.properties file for Allure dashboard."""
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    env_file = target_dir / "environment.properties"

    content = """Platform=AI Autonomous Testing Agent
Browser=Chromium
Framework=Playwright Python + Pytest
Python.Version=3.11+
AI.Provider=OpenAI / Google Gemini
SelfHealing=Enabled
"""
    env_file.write_text(content, encoding="utf-8")
    logger.debug(f"Created Allure environment file: {env_file}")


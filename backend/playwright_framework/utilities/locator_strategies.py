"""
Locator Strategies Module
Defines explicit selector strategies and fallback resolution order.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from playwright.async_api import Locator, Page
from loguru import logger


class StrategyType(str, Enum):
    CSS = "css"
    ROLE = "role"
    TEXT = "text"
    XPATH = "xpath"
    NEARBY = "nearby"


async def try_css_locator(page: Page, selector: str, timeout: int = 3000) -> Optional[Locator]:
    """Attempt CSS selector resolution."""
    try:
        loc = page.locator(selector)
        await loc.first.wait_for(timeout=timeout, state="attached")
        return loc.first
    except Exception:
        return None


async def try_role_locator(page: Page, role: str, name: str, timeout: int = 3000) -> Optional[Locator]:
    """Attempt ARIA role and accessible name resolution."""
    try:
        loc = page.get_by_role(role, name=name)
        await loc.first.wait_for(timeout=timeout, state="attached")
        return loc.first
    except Exception:
        return None


async def try_text_locator(page: Page, text: str, timeout: int = 3000) -> Optional[Locator]:
    """Attempt visible text match resolution."""
    try:
        loc = page.get_by_text(text, exact=False)
        await loc.first.wait_for(timeout=timeout, state="attached")
        return loc.first
    except Exception:
        return None


async def try_xpath_locator(page: Page, xpath: str, timeout: int = 3000) -> Optional[Locator]:
    """Attempt XPath selector resolution."""
    try:
        loc = page.locator(f"xpath={xpath}")
        await loc.first.wait_for(timeout=timeout, state="attached")
        return loc.first
    except Exception:
        return None


async def try_nearby_locator(page: Page, label_text: str, timeout: int = 3000) -> Optional[Locator]:
    """Attempt resolving an input associated with a nearby label."""
    try:
        loc = page.locator(f"//label[contains(text(), '{label_text}')]/following::input[1]")
        await loc.first.wait_for(timeout=timeout, state="attached")
        return loc.first
    except Exception:
        return None


async def find_best_locator(page: Page, descriptor: dict) -> Optional[Locator]:
    """
    Tries strategies in priority sequence: CSS -> Role -> Text -> XPath -> Nearby
    """
    css = descriptor.get("css")
    if css:
        found = await try_css_locator(page, css)
        if found:
            return found

    role = descriptor.get("role")
    name = descriptor.get("name")
    if role and name:
        found = await try_role_locator(page, role, name)
        if found:
            return found

    text = descriptor.get("text")
    if text:
        found = await try_text_locator(page, text)
        if found:
            return found

    xpath = descriptor.get("xpath")
    if xpath:
        found = await try_xpath_locator(page, xpath)
        if found:
            return found

    label = descriptor.get("label")
    if label:
        found = await try_nearby_locator(page, label)
        if found:
            return found

    return None


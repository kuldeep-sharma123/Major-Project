"""
self_healing.py - Self-healing locator engine for Playwright.

Strategy pipeline (stops at first success):
  1. Primary CSS selector
  2. CSS fallback list
  3. ARIA role + accessible name
  4. Text content
  5. XPath
  6. Nearby label text (label → next input)

Successful strategies are persisted in a JSON registry so subsequent runs
prefer the winning strategy immediately.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Optional

from loguru import logger
from playwright.async_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

REGISTRY_FILE = Path(__file__).parent.parent / "reports" / "locator_registry.json"
PROBE_TIMEOUT = 3_000  # ms per strategy attempt


# ---------------------------------------------------------------------------
# Locator Registry (persistent JSON)
# ---------------------------------------------------------------------------
class LocatorRegistry:
    """
    Persists winning locator strategies across test runs as a JSON file.

    Schema:
    {
      "<primary_css>": {
        "winning_strategy": "css|role|text|xpath|nearby",
        "winning_value": "<selector or description>",
        "hit_count": 42,
        "last_seen": "2024-01-01T00:00:00"
      }
    }
    """

    def __init__(self, registry_path: Path = REGISTRY_FILE) -> None:
        self._path = registry_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self) -> None:
        try:
            self._path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        except OSError as exc:
            logger.warning(f"Could not save locator registry: {exc}")

    def get_winner(self, key: str) -> Optional[dict]:
        return self._data.get(key)

    def record_winner(self, key: str, strategy: str, value: str) -> None:
        entry = self._data.setdefault(key, {"hit_count": 0})
        entry["winning_strategy"] = strategy
        entry["winning_value"] = value
        entry["hit_count"] = entry.get("hit_count", 0) + 1
        entry["last_seen"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self._save()
        logger.debug(f"Registry updated: '{key}' → strategy='{strategy}' value='{value}'")


# ---------------------------------------------------------------------------
# SelfHealingLocator
# ---------------------------------------------------------------------------
class SelfHealingLocator:
    """
    Wraps a Playwright :class:`Page` and provides a multi-strategy element
    resolver that automatically falls back and self-heals when the primary
    CSS selector fails.
    """

    def __init__(self, page: Page) -> None:
        self.page = page
        self.registry = LocatorRegistry()

    # ------------------------------------------------------------------
    # Individual strategy probes
    # ------------------------------------------------------------------
    async def _probe(self, locator: Locator, timeout: float = PROBE_TIMEOUT) -> bool:
        """Return True if *locator* resolves to at least one attached element within *timeout*."""
        try:
            await locator.first.wait_for(state="attached", timeout=timeout)
            return True
        except (PlaywrightTimeoutError, Exception):
            return False

    async def _try_css(self, selector: str) -> Optional[Locator]:
        loc = self.page.locator(selector)
        if await self._probe(loc):
            logger.debug(f"[SelfHeal] CSS succeeded: '{selector}'")
            return loc
        return None

    async def _try_role(self, role: str, name: Optional[str] = None) -> Optional[Locator]:
        try:
            loc = self.page.get_by_role(role, name=name) if name else self.page.get_by_role(role)  # type: ignore[arg-type]
            if await self._probe(loc):
                logger.debug(f"[SelfHeal] Role succeeded: role='{role}' name='{name}'")
                return loc
        except Exception:
            pass
        return None

    async def _try_text(self, text: str) -> Optional[Locator]:
        loc = self.page.get_by_text(text, exact=False)
        if await self._probe(loc):
            logger.debug(f"[SelfHeal] Text succeeded: '{text}'")
            return loc
        return None

    async def _try_xpath(self, xpath: str) -> Optional[Locator]:
        loc = self.page.locator(f"xpath={xpath}")
        if await self._probe(loc):
            logger.debug(f"[SelfHeal] XPath succeeded: '{xpath}'")
            return loc
        return None

    async def _try_label(self, label_text: str) -> Optional[Locator]:
        """Find an input that is described by a label containing *label_text*."""
        loc = self.page.get_by_label(label_text, exact=False)
        if await self._probe(loc):
            logger.debug(f"[SelfHeal] Label succeeded: '{label_text}'")
            return loc
        return None

    # ------------------------------------------------------------------
    # Main resolver
    # ------------------------------------------------------------------
    async def find(
        self,
        primary_css: str,
        fallback_css_list: List[str] = None,
        *,
        role: Optional[str] = None,
        role_name: Optional[str] = None,
        text: Optional[str] = None,
        xpath: Optional[str] = None,
        label: Optional[str] = None,
        timeout: float = 10_000,
    ) -> Locator:
        """
        Try each strategy in order and return the first working Locator.

        Raises
        ------
        RuntimeError
            When all strategies are exhausted without finding the element.
        """
        fallback_css_list = fallback_css_list or []

        # --- Check registry for previously winning strategy ---
        cached = self.registry.get_winner(primary_css)
        if cached:
            cached_strategy = cached["winning_strategy"]
            cached_value = cached["winning_value"]
            logger.debug(f"[SelfHeal] Registry cache hit: strategy='{cached_strategy}' key='{primary_css}'")
            loc = await self._replay_cached(cached_strategy, cached_value, role_name=role_name)
            if loc is not None:
                return loc
            logger.warning(f"[SelfHeal] Cached strategy failed for '{primary_css}', re-healing…")

        # --- Strategy 1: Primary CSS ---
        loc = await self._try_css(primary_css)
        if loc:
            self.registry.record_winner(primary_css, "css", primary_css)
            return loc

        # --- Strategy 2: CSS fallbacks ---
        for css_fb in fallback_css_list:
            loc = await self._try_css(css_fb)
            if loc:
                logger.info(f"[SelfHeal] CSS fallback succeeded: '{css_fb}' (primary='{primary_css}')")
                self.registry.record_winner(primary_css, "css_fallback", css_fb)
                return loc

        # --- Strategy 3: ARIA role ---
        if role:
            loc = await self._try_role(role, role_name)
            if loc:
                self.registry.record_winner(primary_css, "role", f"{role}|{role_name}")
                return loc

        # --- Strategy 4: Text content ---
        if text:
            loc = await self._try_text(text)
            if loc:
                self.registry.record_winner(primary_css, "text", text)
                return loc

        # --- Strategy 5: XPath ---
        if xpath:
            loc = await self._try_xpath(xpath)
            if loc:
                self.registry.record_winner(primary_css, "xpath", xpath)
                return loc

        # --- Strategy 6: Nearby label ---
        if label:
            loc = await self._try_label(label)
            if loc:
                self.registry.record_winner(primary_css, "label", label)
                return loc

        # --- All strategies exhausted ---
        raise RuntimeError(
            f"[SelfHeal] Could not locate element. Primary='{primary_css}', "
            f"fallbacks={fallback_css_list}, role={role}, text={text}, xpath={xpath}, label={label}"
        )

    async def _replay_cached(
        self, strategy: str, value: str, role_name: Optional[str] = None
    ) -> Optional[Locator]:
        """Re-execute a previously winning strategy using its cached value."""
        if strategy in ("css", "css_fallback"):
            return await self._try_css(value)
        if strategy == "role":
            parts = value.split("|", 1)
            r = parts[0]
            n = parts[1] if len(parts) > 1 and parts[1] != "None" else role_name
            return await self._try_role(r, n)
        if strategy == "text":
            return await self._try_text(value)
        if strategy == "xpath":
            return await self._try_xpath(value)
        if strategy == "label":
            return await self._try_label(value)
        return None

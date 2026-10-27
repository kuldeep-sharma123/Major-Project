"""
dynamic_page.py - Dynamically generated Page Object class.

Accepts a page_config dict that describes discovered UI elements and generates
getter/click/fill methods at runtime using Python's type() metaclass and closures.

page_config schema:
{
  "page_name": "CheckoutPage",
  "url_path": "/checkout",
  "elements": {
    "submit_button": {
      "css": "button[type='submit']",
      "fallbacks": [".btn-checkout"],
      "role": "button",
      "role_name": "Submit",
      "type": "button"          # button | input | link | text | select | checkbox
    },
    "email_input": {
      "css": "input[type='email']",
      "fallbacks": ["input[name='email']"],
      "label": "Email",
      "type": "input"
    }
  }
}
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Optional

import allure
from loguru import logger
from playwright.async_api import Page

from pages.base_page import BasePage


def _make_click_method(element_name: str, config: dict) -> Callable:
    """Closure factory: returns an async method that clicks a specific element."""
    css = config.get("css", "")
    fallbacks = config.get("fallbacks", [])
    kwargs = {k: config[k] for k in ("role", "role_name", "text", "xpath", "label") if k in config}

    async def click_method(self: "DynamicPage") -> None:
        with allure.step(f"Click '{element_name}'"):
            logger.info(f"[DynamicPage] Clicking '{element_name}'")
            await self.click(css, fallbacks=fallbacks, locator_desc=element_name, **kwargs)

    click_method.__name__ = f"click_{element_name}"
    click_method.__doc__ = f"Click the '{element_name}' element."
    return click_method


def _make_fill_method(element_name: str, config: dict) -> Callable:
    """Closure factory: returns an async method that fills a text input."""
    css = config.get("css", "")
    fallbacks = config.get("fallbacks", [])
    kwargs = {k: config[k] for k in ("role", "role_name", "text", "xpath", "label") if k in config}

    async def fill_method(self: "DynamicPage", value: str) -> None:
        with allure.step(f"Fill '{element_name}' with '{value}'"):
            logger.info(f"[DynamicPage] Filling '{element_name}' = '{value}'")
            await self.fill(css, value, fallbacks=fallbacks, locator_desc=element_name, **kwargs)

    fill_method.__name__ = f"fill_{element_name}"
    fill_method.__doc__ = f"Fill the '{element_name}' input with a value."
    return fill_method


def _make_get_text_method(element_name: str, config: dict) -> Callable:
    """Closure factory: returns an async method that retrieves element text."""
    css = config.get("css", "")
    kwargs = {k: config[k] for k in ("role", "role_name", "text", "xpath", "label") if k in config}

    async def get_text_method(self: "DynamicPage") -> str:
        logger.debug(f"[DynamicPage] Getting text of '{element_name}'")
        return await self.get_text(css, **kwargs)

    get_text_method.__name__ = f"get_{element_name}_text"
    get_text_method.__doc__ = f"Return inner text of the '{element_name}' element."
    return get_text_method


def _make_is_visible_method(element_name: str, config: dict) -> Callable:
    """Closure factory: returns an async method that checks element visibility."""
    css = config.get("css", "")
    kwargs = {k: config[k] for k in ("role", "role_name", "text", "xpath", "label") if k in config}

    async def is_visible_method(self: "DynamicPage") -> bool:
        return await self.is_visible(css, **kwargs)

    is_visible_method.__name__ = f"is_{element_name}_visible"
    is_visible_method.__doc__ = f"Return True if '{element_name}' is visible."
    return is_visible_method


def _make_select_method(element_name: str, config: dict) -> Callable:
    """Closure factory: returns an async method that selects a dropdown option."""
    css = config.get("css", "")

    async def select_method(self: "DynamicPage", option: str, by: str = "label") -> None:
        with allure.step(f"Select '{option}' in '{element_name}'"):
            logger.info(f"[DynamicPage] Selecting '{option}' in '{element_name}'")
            await self.select_option(css, option, locator_desc=element_name, by=by)

    select_method.__name__ = f"select_{element_name}"
    select_method.__doc__ = f"Select an option in the '{element_name}' dropdown."
    return select_method


# ---------------------------------------------------------------------------
# DynamicPage builder
# ---------------------------------------------------------------------------
class DynamicPage(BasePage):
    """
    Base for runtime-generated Page Objects.
    Attach generated methods via :meth:`from_config`.
    """

    def __init__(self, page: Page, base_url: str = "", page_name: str = "DynamicPage") -> None:
        super().__init__(page, base_url)
        self._page_name = page_name

    @classmethod
    def from_config(cls, page: Page, page_config: Dict[str, Any], base_url: str = "") -> "DynamicPage":
        """
        Factory that builds a DynamicPage instance with methods generated
        from *page_config*.

        Parameters
        ----------
        page : playwright.async_api.Page
        page_config : dict
            Configuration dict following the schema described in this module's docstring.
        base_url : str

        Returns
        -------
        DynamicPage
            Instance with dynamically attached methods.
        """
        page_name = page_config.get("page_name", "DynamicPage")
        elements: Dict[str, dict] = page_config.get("elements", {})

        # Create a fresh subclass so methods are per-instance not global
        klass_methods: Dict[str, Callable] = {}

        for element_name, config in elements.items():
            element_type = config.get("type", "button").lower()
            safe_name = re.sub(r"[^a-z0-9_]", "_", element_name.lower())

            # Always add visibility and get-text methods
            klass_methods[f"is_{safe_name}_visible"] = _make_is_visible_method(safe_name, config)
            klass_methods[f"get_{safe_name}_text"] = _make_get_text_method(safe_name, config)

            # Type-specific methods
            if element_type in ("button", "link"):
                klass_methods[f"click_{safe_name}"] = _make_click_method(safe_name, config)
            elif element_type in ("input", "textarea"):
                klass_methods[f"fill_{safe_name}"] = _make_fill_method(safe_name, config)
                klass_methods[f"click_{safe_name}"] = _make_click_method(safe_name, config)
            elif element_type == "select":
                klass_methods[f"select_{safe_name}"] = _make_select_method(safe_name, config)
            elif element_type == "checkbox":
                klass_methods[f"click_{safe_name}"] = _make_click_method(safe_name, config)
            elif element_type == "text":
                pass  # visibility + get_text already added

        # Build subclass dynamically
        DynamicSubclass = type(page_name, (cls,), klass_methods)

        instance = DynamicSubclass(page, base_url, page_name)
        instance._page_config = page_config
        instance._element_names = list(elements.keys())

        logger.info(
            f"[DynamicPage] Built '{page_name}' with {len(klass_methods)} methods "
            f"for {len(elements)} elements"
        )
        return instance

    async def navigate_to_page(self) -> None:
        """Navigate to this page's configured URL path."""
        path = getattr(self, "_page_config", {}).get("url_path", "")
        await self.navigate(path)
        logger.info(f"[DynamicPage] Navigated to '{self._page_name}' at path '{path}'")

    def list_elements(self) -> list[str]:
        """Return list of element names configured for this page."""
        return getattr(self, "_element_names", [])

    def __repr__(self) -> str:
        return f"<DynamicPage name='{self._page_name}' elements={self.list_elements()}>"

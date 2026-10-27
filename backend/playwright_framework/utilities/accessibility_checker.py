"""
Accessibility Checker Module
Inspects web pages for basic WCAG 2.1 compliance (ARIA labels, alt text, form labels, landmarks).
"""
from __future__ import annotations

from typing import Any, Dict, List
from playwright.async_api import Page
from loguru import logger


class AccessibilityChecker:
    """Performs automated accessibility checks on web pages."""

    @staticmethod
    async def check_aria_labels(page: Page) -> List[Dict[str, Any]]:
        """Find interactive elements missing accessible names or ARIA labels."""
        violations = await page.evaluate("""
            () => {
                const issues = [];
                // Buttons without text or aria-label
                document.querySelectorAll('button').forEach((b, idx) => {
                    const text = b.innerText.trim();
                    const aria = b.getAttribute('aria-label') || b.getAttribute('aria-labelledby');
                    if (!text && !aria) {
                        issues.push({
                            type: 'missing_button_label',
                            selector: `button:nth-of-type(${idx+1})`,
                            snippet: b.outerHTML.slice(0, 100),
                            message: 'Button has neither visible text nor aria-label'
                        });
                    }
                });

                // Inputs without associated label or aria-label
                document.querySelectorAll('input:not([type="hidden"])').forEach((inp, idx) => {
                    const id = inp.id;
                    const hasLabel = id ? document.querySelector(`label[for="${id}"]`) : null;
                    const aria = inp.getAttribute('aria-label') || inp.getAttribute('aria-labelledby');
                    if (!hasLabel && !aria && !inp.getAttribute('placeholder')) {
                        issues.push({
                            type: 'missing_input_label',
                            selector: `input:nth-of-type(${idx+1})`,
                            snippet: inp.outerHTML.slice(0, 100),
                            message: 'Form input missing descriptive label or aria-label'
                        });
                    }
                });

                // Images missing alt attribute
                document.querySelectorAll('img:not([alt])').forEach((img, idx) => {
                    issues.push({
                        type: 'missing_alt_attribute',
                        selector: `img:nth-of-type(${idx+1})`,
                        snippet: img.outerHTML.slice(0, 100),
                        message: 'Image element is missing an alt attribute'
                    });
                });

                return issues;
            }
        """)

        logger.info(f"♿ Accessibility inspection: {len(violations)} issues found")
        return violations


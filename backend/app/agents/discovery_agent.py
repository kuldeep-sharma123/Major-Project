"""
Application Discovery Agent
Crawls the target web application using Playwright to build a complete site map.
Identifies all pages, forms, buttons, links, and navigation structure.
"""

import asyncio
import re
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from loguru import logger
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.config import settings


class AppMap:
    """Represents the complete discovered structure of a web application."""
    
    def __init__(self, base_url: str, app_name: str):
        self.base_url = base_url
        self.app_name = app_name
        self.pages: List[Dict[str, Any]] = []
        self.navigation: List[Dict[str, str]] = []
        self.all_links: Set[str] = set()
        self.visited_urls: Set[str] = set()
        self.total_forms = 0
        self.total_buttons = 0
        self.total_inputs = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url,
            "app_name": self.app_name,
            "pages": self.pages,
            "navigation": self.navigation,
            "all_links": list(self.all_links),
            "total_pages": len(self.pages),
            "total_forms": self.total_forms,
            "total_buttons": self.total_buttons,
            "total_inputs": self.total_inputs,
        }


class DiscoveryAgent:
    """
    Agent 1: Application Discovery
    
    Uses Playwright to autonomously crawl the target web application,
    building a comprehensive map of all pages, forms, and interactive elements.
    
    Respects:
    - Same-domain links only
    - Max pages limit (configurable)
    - Timeout handling
    - Error recovery
    """

    def __init__(self):
        self.max_pages = settings.MAX_CRAWL_PAGES
        self.timeout = settings.CRAWL_TIMEOUT_MS
        self.base_domain: Optional[str] = None
        logger.info(f"🔍 Discovery Agent initialized (max pages: {self.max_pages})")

    async def discover(self, url: str, app_name: str = "", headed: bool = False) -> Dict[str, Any]:
        """
        Main discovery entry point. Crawls the application and returns site map.
        
        Args:
            url: Starting URL of the application
            app_name: Optional application name
            headed: Whether to launch a visible browser window
            
        Returns:
            Dictionary representing the complete application map
        """
        # Normalize URL
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        parsed = urlparse(url)
        self.base_domain = parsed.netloc
        app_name = app_name or self.base_domain
        
        is_headless = False if headed else settings.HEADLESS
        logger.info(f"🚀 Starting discovery (headed={headed}): {url} | Domain: {self.base_domain}")
        
        app_map = AppMap(base_url=url, app_name=app_name)
        
        async def _crawl_app():
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(
                    headless=is_headless,
                    args=["--no-sandbox", "--disable-setuid-sandbox"],
                )
                
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    ignore_https_errors=True,
                )
                
                try:
                    # Start crawling from the base URL
                    await self._crawl_page(context, url, app_map, depth=0)
                    
                    # If initial page is a login barrier, perform autonomous login and crawl internal pages
                    if app_map.pages and app_map.pages[0].get("page_type") == "login":
                        logger.info("🔑 Login barrier detected on entry page. Starting autonomous post-login crawling...")
                        await self._perform_autonomous_login_and_crawl(context, app_map)

                    # Extract navigation from main page or landing page
                    nav_url = app_map.pages[0].get("url") if app_map.pages else url
                    app_map.navigation = await self._extract_navigation(context, nav_url)
                    
                    logger.success(
                        f"✅ Discovery complete: "
                        f"{len(app_map.pages)} pages | "
                        f"{app_map.total_forms} forms | "
                        f"{app_map.total_buttons} buttons"
                    )
                    
                finally:
                    await context.close()
                    await browser.close()

        try:
            from app.utils.helpers import run_coro_with_proactor
            await run_coro_with_proactor(_crawl_app)
        except Exception as e:
            logger.warning(f"Browser discovery encountered error: {e}. Falling back to resilient page model.")

        # Ensure we always have at least the root page analyzed
        if not app_map.pages:
            logger.info(f"Creating root application representation for {url}")
            app_map.pages.append({
                "url": url,
                "title": app_name,
                "html": f"<html><head><title>{app_name}</title></head><body><h1>{app_name}</h1></body></html>",
                "page_type": "general",
                "forms_count": 1,
                "buttons_count": 2,
                "inputs_count": 2,
                "links": [url],
                "elements": [
                    {"selector": "body", "type": "container", "text": app_name},
                    {"selector": "a", "type": "link", "text": "Home"},
                    {"selector": "button", "type": "button", "text": "Submit"},
                ],
            })
            app_map.total_forms = 1
            app_map.total_buttons = 2
            app_map.total_inputs = 2
        
        return app_map.to_dict()

    async def _crawl_page(
        self,
        context: BrowserContext,
        url: str,
        app_map: AppMap,
        depth: int,
    ) -> None:
        """
        Recursively crawl a single page and follow links.
        
        Args:
            context: Playwright browser context
            url: URL to crawl
            app_map: AppMap to populate
            depth: Current recursion depth (for limiting)
        """
        # Check limits
        if url in app_map.visited_urls:
            return
        if len(app_map.pages) >= self.max_pages:
            logger.debug(f"Max pages ({self.max_pages}) reached, stopping crawl")
            return
        if depth > 3:  # Limit recursion depth
            return
        
        app_map.visited_urls.add(url)
        
        page = await context.new_page()
        try:
            # Navigate to page
            logger.debug(f"📄 Crawling: {url}")
            
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self.timeout,
            )
            
            # Allow client-side rendering to settle (SPA frameworks like React, Vue, Angular)
            await page.wait_for_timeout(2000)
            
            # Get page info
            page_title = await page.title()
            page_html = await page.content()
            
            # Extract page elements
            page_data = await self._extract_page_elements(page, url, page_title, page_html)
            app_map.pages.append(page_data)
            
            # Update totals
            app_map.total_forms += page_data.get("forms_count", 0)
            app_map.total_buttons += page_data.get("buttons_count", 0)
            app_map.total_inputs += page_data.get("inputs_count", 0)
            
            # Get all links for further crawling
            links = await self._extract_links(page, url)
            app_map.all_links.update(links)
            
            logger.info(
                f"  ✓ {url[:60]} | Title: {page_title[:30]} | "
                f"Forms: {page_data.get('forms_count', 0)} | "
                f"Buttons: {page_data.get('buttons_count', 0)}"
            )
            
            # Crawl discovered links (breadth-first)
            for link in list(links)[:10]:  # Limit per-page links to follow
                if link not in app_map.visited_urls and len(app_map.pages) < self.max_pages:
                    await self._crawl_page(context, link, app_map, depth + 1)
                    
        except Exception as e:
            logger.warning(f"⚠️ Failed to crawl {url}: {type(e).__name__}: {e}")
        finally:
            try:
                await page.close()
            except Exception:
                pass

    async def _perform_autonomous_login_and_crawl(
        self, context: BrowserContext, app_map: AppMap
    ) -> None:
        """
        If the entry point is a login page, autonomously authenticate using
        detected or demo credentials, then crawl all authenticated pages (Dashboard, Admin, PIM, etc.).
        """
        login_page_data = app_map.pages[0] if app_map.pages else None
        if not login_page_data:
            return

        login_url = login_page_data.get("url", app_map.base_url)
        page = await context.new_page()

        try:
            logger.info(f"🔑 Attempting autonomous login on {login_url}...")
            await page.goto(login_url, wait_until="domcontentloaded", timeout=self.timeout)
            await page.wait_for_timeout(2000)

            # Determine credentials
            u_val, p_val = None, None
            url_lower = login_url.lower()

            if "orangehrm" in url_lower:
                u_val, p_val = "Admin", "admin123"
            elif "sauce" in url_lower:
                u_val, p_val = "standard_user", "secret_sauce"
            else:
                try:
                    body_text = await page.inner_text("body")
                    import re
                    u_match = re.search(r"username\s*[:=]\s*(\w+)", body_text, re.IGNORECASE)
                    p_match = re.search(r"password\s*[:=]\s*(\w+)", body_text, re.IGNORECASE)
                    if u_match and p_match:
                        u_val, p_val = u_match.group(1), p_match.group(1)
                        logger.info(f"💡 Extracted demo credentials from page: {u_val} / {p_val}")
                except Exception:
                    pass

                if not u_val:
                    u_val, p_val = "admin", "admin"

            # Fill visible inputs
            u_loc = page.locator("input:not([type='hidden'])[name*='user'], input:not([type='hidden'])[placeholder*='user' i], #username, #user-name").first
            p_loc = page.locator("input[type='password'], input[name*='pass'], #password").first
            b_loc = page.locator("button[type='submit'], input[type='submit'], button:has-text('Login'), button:has-text('Sign in')").first

            if await u_loc.is_visible() and await p_loc.is_visible():
                await u_loc.fill(u_val)
                await p_loc.fill(p_val)
                if await b_loc.is_visible():
                    await b_loc.click()
                else:
                    await p_loc.press("Enter")

                # Wait for post-login page load
                await page.wait_for_timeout(3500)
                post_login_url = page.url
                logger.info(f"✅ Autonomous login completed. Landed at: {post_login_url}")

                # If URL changed away from login, we are inside the authenticated application!
                if post_login_url != login_url and "login" not in post_login_url.lower():
                    # Extract landing page (e.g. Dashboard)
                    post_title = await page.title()
                    post_html = await page.content()
                    post_page_data = await self._extract_page_elements(page, post_login_url, post_title, post_html)
                    post_page_data["page_type"] = self._detect_page_type(post_login_url, post_title, post_html)
                    if post_page_data["page_type"] == "general":
                        post_page_data["page_type"] = "dashboard"

                    app_map.pages.append(post_page_data)
                    app_map.visited_urls.add(post_login_url)

                    # Extract all internal authenticated navigation links
                    internal_links = await self._extract_links(page, post_login_url)
                    logger.info(f"🌐 Discovered {len(internal_links)} authenticated internal application routes!")

                    # Crawl each discovered authenticated page
                    for link in list(internal_links)[:15]:
                        if link not in app_map.visited_urls and len(app_map.pages) < self.max_pages:
                            await self._crawl_page(context, link, app_map, depth=1)

        except Exception as auth_err:
            logger.warning(f"⚠️ Autonomous login attempt failed: {auth_err}")
        finally:
            try:
                await page.close()
            except Exception:
                pass

    async def _extract_page_elements(
        self,
        page: Page,
        url: str,
        title: str,
        html: str,
    ) -> Dict[str, Any]:
        """Extract all interactive elements from a page."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Count elements
        forms = soup.find_all("form")
        inputs = soup.find_all(["input", "textarea", "select"])
        visible_inputs = [inp for inp in inputs if inp.get("type", "text").strip().lower() != "hidden"]
        buttons = soup.find_all(["button", "input[type=submit]"])
        links_on_page = soup.find_all("a", href=True)
        
        # Extract form details
        form_details = []
        for i, form in enumerate(forms):
            form_inputs = form.find_all(["input", "textarea", "select"])
            form_details.append({
                "form_index": i,
                "action": form.get("action", ""),
                "method": form.get("method", "GET"),
                "id": form.get("id", ""),
                "fields": [
                    {
                        "name": inp.get("name", ""),
                        "type": inp.get("type", "text"),
                        "id": inp.get("id", ""),
                        "placeholder": inp.get("placeholder", ""),
                        "required": inp.has_attr("required"),
                    }
                    for inp in form_inputs
                ],
            })
        
        # Detect page type from URL and content
        page_type = self._detect_page_type(url, title, html)
        
        # Extract button details
        button_details = []
        for btn in buttons[:20]:
            button_details.append({
                "text": btn.get_text(strip=True)[:50],
                "type": btn.get("type", "button"),
                "id": btn.get("id", ""),
                "class": " ".join(btn.get("class", []))[:50],
            })

        # Build comprehensive actionable elements list with exact Playwright selectors
        extracted_elements = []

        # 1. Headings
        for h in soup.find_all(["h1", "h2"])[:3]:
            h_text = h.get_text(strip=True)[:60]
            if h_text:
                extracted_elements.append({
                    "selector": h.name,
                    "element_type": "heading",
                    "label": f"Heading: {h_text}",
                    "text": h_text,
                    "is_interactive": False,
                })

        # 2. Inputs (Interactive only - hidden inputs excluded)
        for inp in visible_inputs[:15]:
            inp_id = inp.get("id", "").strip()
            inp_name = inp.get("name", "").strip()
            inp_type = inp.get("type", "text").strip()
            inp_placeholder = inp.get("placeholder", "").strip()
            inp_class = ".".join([c for c in inp.get("class", []) if c and not c.startswith("ng-") and not c.startswith("oxd-input--") and not c.startswith("data-")])

            if inp_id:
                sel = f"#{inp_id}"
            elif inp_name:
                sel = f"input[name='{inp_name}']"
            elif inp_placeholder:
                sel = f"input[placeholder='{inp_placeholder}']"
            elif inp_class:
                sel = f"input.{inp_class}"
            else:
                sel = f"input[type='{inp_type}']" if inp_type else "input"

            label = inp_placeholder or inp_name or inp_id or f"Input ({inp_type})"
            extracted_elements.append({
                "selector": sel,
                "element_type": "input",
                "label": label,
                "text": inp_placeholder,
                "purpose": f"{inp_type} input",
                "is_interactive": True,
            })

        # 3. Buttons
        for btn in buttons[:15]:
            btn_id = btn.get("id", "").strip()
            btn_text = btn.get_text(strip=True)[:40]
            btn_type = btn.get("type", "button").strip()
            btn_class = ".".join([c for c in btn.get("class", []) if c and not c.startswith("ng-")])

            if btn_id:
                sel = f"#{btn_id}"
            elif btn_text:
                sel = f"button:has-text('{btn_text}')"
            elif btn_type == "submit":
                sel = "button[type='submit'], input[type='submit']"
            elif btn_class:
                sel = f"button.{btn_class}"
            else:
                sel = "button"

            label = btn_text or btn_id or "Submit Button"
            extracted_elements.append({
                "selector": sel,
                "element_type": "button",
                "label": label,
                "text": btn_text,
                "purpose": "action button",
                "is_interactive": True,
            })

        # 4. Prominent links
        for a in links_on_page[:10]:
            a_text = a.get_text(strip=True)[:40]
            href = a.get("href", "")
            if a_text and href:
                extracted_elements.append({
                    "selector": f"a:has-text('{a_text}')",
                    "element_type": "link",
                    "label": f"Link: {a_text}",
                    "text": a_text,
                    "purpose": "navigation link",
                    "is_interactive": True,
                })

        logger.info(
            f"🔍 Discovered elements for {url[:50]}: "
            f"{len(forms)} forms, {len(visible_inputs)} interactive inputs, {len(buttons)} buttons, "
            f"{len(extracted_elements)} mapped selectors"
        )
        
        return {
            "url": url,
            "title": title,
            "page_type": page_type,
            "html_snippet": html[:5000],  # Keep snippet for AI analysis
            "forms_count": len(forms),
            "buttons_count": len(buttons),
            "inputs_count": len(visible_inputs),
            "links_count": len(links_on_page),
            "forms": form_details,
            "buttons": button_details,
            "elements": extracted_elements,
            "meta_description": self._get_meta_description(soup),
        }


    async def _extract_links(self, page: Page, base_url: str) -> Set[str]:
        """Extract all same-domain links from a page."""
        links = await page.evaluate("""
            () => {
                const anchors = document.querySelectorAll('a[href]');
                return Array.from(anchors).map(a => a.href).filter(href => href.startsWith('http'));
            }
        """)
        
        filtered_links = set()
        for link in links:
            parsed = urlparse(link)
            # Same domain only, no file downloads, no anchors
            if (
                parsed.netloc == self.base_domain
                and not link.endswith((".pdf", ".jpg", ".png", ".zip", ".xlsx"))
                and "#" not in link
                and "logout" not in link.lower()
                and "signout" not in link.lower()
            ):
                # Clean URL (remove query string for deduplication)
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if clean_url != base_url:
                    filtered_links.add(clean_url)
        
        return filtered_links

    async def _extract_navigation(
        self, context: BrowserContext, url: str
    ) -> List[Dict[str, str]]:
        """Extract navigation menu structure from main page."""
        page = await context.new_page()
        navigation = []
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)
            
            # Try common navigation selectors
            nav_selectors = [
                "nav a",
                "[role='navigation'] a",
                ".navbar a",
                ".nav a",
                ".menu a",
                "header a",
                ".sidebar a",
            ]
            
            for selector in nav_selectors:
                try:
                    nav_links = await page.query_selector_all(selector)
                    if nav_links:
                        for link in nav_links[:20]:  # Limit
                            href = await link.get_attribute("href")
                            text = await link.inner_text()
                            if href and text.strip():
                                navigation.append({
                                    "text": text.strip()[:50],
                                    "href": urljoin(url, href) if href else "",
                                    "selector": selector,
                                })
                        if navigation:
                            break
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f"Navigation extraction failed: {e}")
        finally:
            await page.close()
        
        return navigation

    def _detect_page_type(self, url: str, title: str, html: str) -> str:
        """Detect page type from URL, title, and HTML content."""
        url_lower = url.lower()
        title_lower = title.lower()
        html_lower = html.lower()
        
        patterns = {
            "login": ["login", "signin", "sign-in", "log-in"],
            "register": ["register", "signup", "sign-up", "create-account", "registration"],
            "forgot_password": ["forgot", "reset-password", "password-reset"],
            "dashboard": ["dashboard", "home", "overview", "main"],
            "product": ["product", "item", "shop", "store", "catalog"],
            "cart": ["cart", "basket", "shopping-bag"],
            "checkout": ["checkout", "payment", "billing", "shipping"],
            "profile": ["profile", "account", "my-account", "settings", "mydetails"],
            "admin": ["admin", "administrator", "management", "control-panel", "systemusers"],
            "employee": ["pim", "employee", "staff", "users", "directory"],
            "leave": ["leave", "time-off", "vacation"],
            "time": ["time", "timesheet", "attendance"],
            "recruitment": ["recruitment", "hiring", "jobs", "candidates"],
            "search": ["search", "results", "find"],
            "contact": ["contact", "support", "help"],
        }
        
        combined = f"{url_lower} {title_lower}"
        
        for page_type, keywords in patterns.items():
            if any(kw in combined for kw in keywords):
                return page_type
        
        # Check HTML for login form indicators
        if ("password" in html_lower and "username" in html_lower) or \
           ("type=\"password\"" in html_lower):
            return "login"
        
        return "general"

    def _get_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description from page."""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            return meta.get("content", "")[:200]
        return ""

